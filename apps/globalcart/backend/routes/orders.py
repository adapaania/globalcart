"""Order-related endpoints: lookup, create, update, delete, and manual sync."""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Order, OrderEvent, SystemLog, OrderStatus, PaymentStatus
from serializers import serialize_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


# --- Pydantic schemas ---------------------------------------------------------

class OrderItem(BaseModel):
    sku: Optional[str] = ""
    name: Optional[str] = ""
    qty: Optional[float] = 1
    price: Optional[float] = 0.0


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_email: str = Field(..., min_length=1)
    total_amount: float = 0.0
    status: OrderStatus = OrderStatus.PROCESSING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    items: List[OrderItem] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    items: Optional[List[OrderItem]] = None


# --- Helpers ------------------------------------------------------------------

def _next_order_id(db: Session) -> str:
    """Generate the next GC-XXXX id, incremented from the max existing number."""
    max_num = 1000
    for (oid,) in db.query(Order.order_id).all():
        if oid and oid.startswith("GC-"):
            try:
                n = int(oid.split("-", 1)[1])
                if n > max_num:
                    max_num = n
            except (ValueError, IndexError):
                continue
    return f"GC-{max_num + 1:04d}"


# --- Routes -------------------------------------------------------------------

@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Return the full customer-facing order (details + events, NO system logs)."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return serialize_order(order, include_events=True)


@router.post("")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order with an auto-generated GC-XXXX id."""
    order_id = _next_order_id(db)
    now = datetime.utcnow()
    order = Order(
        order_id=order_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        status=payload.status,
        payment_status=payload.payment_status,
        total_amount=payload.total_amount,
        items=json.dumps([i.model_dump() for i in payload.items]),
        created_at=now,
        updated_at=now,
    )
    db.add(order)
    db.flush()  # ensure order row exists before adding the FK event
    event = OrderEvent(
        order_id=order.order_id,
        timestamp=now,
        event_type="ORDER_CREATED",
        description="Order created via support console.",
        actor="support_agent",
    )
    db.add(event)
    db.commit()
    db.refresh(order)
    return serialize_order(order, include_events=True)


@router.patch("/{order_id}")
def update_order(order_id: str, payload: OrderUpdate, db: Session = Depends(get_db)):
    """Partially update an order. Records an ORDER_UPDATED timeline event."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")

    changes = []

    if payload.customer_name is not None and payload.customer_name != order.customer_name:
        changes.append(f"customer_name → '{payload.customer_name}'")
        order.customer_name = payload.customer_name

    if payload.customer_email is not None and payload.customer_email != order.customer_email:
        changes.append(f"customer_email → '{payload.customer_email}'")
        order.customer_email = payload.customer_email

    if payload.total_amount is not None and payload.total_amount != order.total_amount:
        changes.append(f"total_amount → {payload.total_amount}")
        order.total_amount = payload.total_amount

    if payload.status is not None:
        cur = order.status.value if hasattr(order.status, "value") else order.status
        if payload.status.value != cur:
            changes.append(f"status {cur} → {payload.status.value}")
            order.status = payload.status

    if payload.payment_status is not None:
        cur = (
            order.payment_status.value
            if hasattr(order.payment_status, "value")
            else order.payment_status
        )
        if payload.payment_status.value != cur:
            changes.append(f"payment_status {cur} → {payload.payment_status.value}")
            order.payment_status = payload.payment_status

    if payload.items is not None:
        order.items = json.dumps([i.model_dump() for i in payload.items])
        changes.append("items updated")

    if changes:
        now = datetime.utcnow()
        order.updated_at = now
        event = OrderEvent(
            order_id=order.order_id,
            timestamp=now,
            event_type="ORDER_UPDATED",
            description="Order updated by support agent: " + "; ".join(changes) + ".",
            actor="support_agent",
        )
        db.add(event)
        db.commit()
        db.refresh(order)

    return serialize_order(order, include_events=True)


@router.delete("/{order_id}")
def delete_order(order_id: str, db: Session = Depends(get_db)):
    """Delete an order and all of its events and logs."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    db.delete(order)  # cascade removes related events and logs
    db.commit()
    return {"deleted": True, "order_id": order_id}


@router.post("/{order_id}/sync")
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
