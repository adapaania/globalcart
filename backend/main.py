"""FastAPI application for the GlobalCart Order Management System."""
import json
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db, SessionLocal
from models import Order, OrderEvent, SystemLog, OrderStatus
from seed_data import seed_database

app = FastAPI(title="GlobalCart Order Management System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create tables and seed the database if it is empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Order).count() == 0:
            seed_database(db)
            print("[startup] Database seeded with demo orders.")
        else:
            print("[startup] Database already contains orders; skipping seed.")
    finally:
        db.close()


# ----------------------------------------------------------------------
# Serializers
# ----------------------------------------------------------------------
def serialize_event(event: OrderEvent):
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "event_type": event.event_type,
        "description": event.description,
        "actor": event.actor,
    }


def serialize_log(log: SystemLog):
    return {
        "id": log.id,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "level": log.level.value if hasattr(log.level, "value") else log.level,
        "message": log.message,
        "internal_code": log.internal_code,
    }


def serialize_order(order: Order, include_events: bool = True):
    try:
        items = json.loads(order.items) if order.items else []
    except (ValueError, TypeError):
        items = []
    data = {
        "order_id": order.order_id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "payment_status": order.payment_status.value
        if hasattr(order.payment_status, "value")
        else order.payment_status,
        "total_amount": order.total_amount,
        "items": items,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }
    if include_events:
        data["events"] = [serialize_event(e) for e in order.events]
    return data


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Return the full customer-facing order (details + events, NO system logs)."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return serialize_order(order, include_events=True)


@app.get("/api/diagnostics/{order_id}")
def get_diagnostics(order_id: str, db: Session = Depends(get_db)):
    """Return internal state: system logs, error codes, and a recommended action."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")

    logs = [serialize_log(l) for l in order.logs]
    error_codes = [
        l["internal_code"]
        for l in logs
        if l["level"] in ("ERROR", "WARN") and l["internal_code"]
    ]

    recommended_action = _recommend_action(order, logs)

    return {
        "order_id": order.order_id,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "payment_status": order.payment_status.value
        if hasattr(order.payment_status, "value")
        else order.payment_status,
        "system_logs": logs,
        "error_codes": error_codes,
        "recommended_action": recommended_action,
    }


def _recommend_action(order: Order, logs):
    """Derive a recommended remediation action from logs and status."""
    codes = " ".join(
        (l["internal_code"] or "") + " " + (l["message"] or "") for l in logs
    ).lower()

    status = order.status.value if hasattr(order.status, "value") else order.status

    if "warehouse_api_timeout" in codes:
        return (
            "Warehouse API timed out during fulfillment. Trigger a manual sync "
            "(POST /api/orders/{}/sync) to re-dispatch the order to the warehouse.".format(order.order_id)
        )
    if "high_value_order" in codes:
        return (
            "Order is on hold for high-value manual financial verification. "
            "Escalate to the finance team to verify and release the hold."
        )
    if "sku_out_of_stock" in codes:
        return (
            "One or more SKUs are out of stock. Restock the item or offer the "
            "customer a substitute/refund before the order can proceed."
        )
    if status == "PROCESSING":
        return "Order is processing. If stuck, trigger a manual sync to advance it."
    return "No action required. Order is healthy."


@app.post("/api/orders/{order_id}/sync")
def sync_order(order_id: str, db: Session = Depends(get_db)):
    """Simulate a manual sync. Moves a stuck PROCESSING order to SHIPPED."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")

    status = order.status.value if hasattr(order.status, "value") else order.status

    if status == OrderStatus.PROCESSING.value:
        order.status = OrderStatus.SHIPPED
        order.updated_at = datetime.utcnow()
        event = OrderEvent(
            order_id=order.order_id,
            timestamp=datetime.utcnow(),
            event_type="MANUAL_SYNC",
            description="Manual sync triggered by agent. Order re-dispatched and marked SHIPPED.",
            actor="agent",
        )
        log = SystemLog(
            order_id=order.order_id,
            timestamp=datetime.utcnow(),
            level="INFO",
            message="Manual sync succeeded. Warehouse dispatch confirmed.",
            internal_code="OK_MANUAL_SYNC",
        )
        db.add(event)
        db.add(log)
        db.commit()
        db.refresh(order)
        return {
            "synced": True,
            "message": "Order was stuck in PROCESSING and has been advanced to SHIPPED.",
            "order": serialize_order(order, include_events=True),
        }

    db.refresh(order)
    return {
        "synced": False,
        "message": f"No sync action needed. Order status is '{status}'.",
        "order": serialize_order(order, include_events=True),
    }
