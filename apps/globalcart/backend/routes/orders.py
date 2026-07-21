"""Order-related endpoints: customer-facing order lookup and manual sync."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Order, OrderEvent, SystemLog, OrderStatus
from serializers import serialize_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Return the full customer-facing order (details + events, NO system logs)."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return serialize_order(order, include_events=True)


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
