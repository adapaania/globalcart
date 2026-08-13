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


class EventIn(BaseModel):
    timestamp: Optional[datetime] = None
    event_type: str
    description: Optional[str] = ""
    actor: Optional[str] = "system"


class LogIn(BaseModel):
    timestamp: Optional[datetime] = None
    level: str = "INFO"
    message: str
    internal_code: Optional[str] = ""


class OrderPushItem(BaseModel):
    """A single record in a bulk push. If ``order_id`` matches an existing
    order it is updated (upsert); otherwise a new order is created."""
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    items: Optional[List[OrderItem]] = None
    events: Optional[List[EventIn]] = None
    logs: Optional[List[LogIn]] = None


class OrderPush(BaseModel):
    orders: List[OrderPushItem] = Field(..., min_length=1)


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

@router.get("")
def list_orders(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all orders with optional filtering by status and payment_status.
    
    Query params:
    - status: filter by order status (PROCESSING, SHIPPED, DELIVERED, HELD, PENDING)
    - payment_status: filter by payment status (SUCCESS, PENDING, FAILED)
    - limit: max results per page (default 100)
    - offset: pagination offset (default 0)
    """
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(orders),
        "orders": [serialize_order(order, include_events=False) for order in orders],
    }


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


@router.post("/push")
def push_orders(payload: OrderPush, db: Session = Depends(get_db)):
    """Bulk data-ingest / upsert endpoint.

    Accepts a batch of order records and, for each one:
      * **Updates** the order if its ``order_id`` already exists (any provided
        fields are overwritten; ``events`` and ``logs`` are appended).
      * **Creates** a new order otherwise — using the supplied ``order_id`` if
        given and free, else an auto-generated ``GC-XXXX`` id.

    This lets an external system push and modify GlobalCart data in one call.
    Returns a summary listing which ids were created vs updated.
    """
    now = datetime.utcnow()
    created: List[str] = []
    updated: List[str] = []
    results = []

    for item in payload.orders:
        order = None
        if item.order_id:
            order = db.query(Order).filter(Order.order_id == item.order_id).first()

        if order is None:
            # --- create ---
            new_id = item.order_id or _next_order_id(db)
            order = Order(
                order_id=new_id,
                customer_name=item.customer_name or "Unknown",
                customer_email=item.customer_email or "",
                status=item.status or OrderStatus.PROCESSING,
                payment_status=item.payment_status or PaymentStatus.PENDING,
                total_amount=item.total_amount or 0.0,
                items=json.dumps([i.model_dump() for i in (item.items or [])]),
                created_at=now,
                updated_at=now,
            )
            db.add(order)
            db.flush()
            db.add(OrderEvent(
                order_id=order.order_id,
                timestamp=now,
                event_type="ORDER_CREATED",
                description="Order created via bulk push.",
                actor="push_api",
            ))
            created.append(order.order_id)
        else:
            # --- update / upsert ---
            if item.customer_name is not None:
                order.customer_name = item.customer_name
            if item.customer_email is not None:
                order.customer_email = item.customer_email
            if item.total_amount is not None:
                order.total_amount = item.total_amount
            if item.status is not None:
                order.status = item.status
            if item.payment_status is not None:
                order.payment_status = item.payment_status
            if item.items is not None:
                order.items = json.dumps([i.model_dump() for i in item.items])
            order.updated_at = now
            db.add(OrderEvent(
                order_id=order.order_id,
                timestamp=now,
                event_type="ORDER_UPDATED",
                description="Order updated via bulk push.",
                actor="push_api",
            ))
            updated.append(order.order_id)

        # append any supplied events
        for ev in (item.events or []):
            db.add(OrderEvent(
                order_id=order.order_id,
                timestamp=ev.timestamp or now,
                event_type=ev.event_type,
                description=ev.description or "",
                actor=ev.actor or "system",
            ))
        # append any supplied system logs
        for lg in (item.logs or []):
            db.add(SystemLog(
                order_id=order.order_id,
                timestamp=lg.timestamp or now,
                level=lg.level,
                message=lg.message,
                internal_code=lg.internal_code or "",
            ))

        db.flush()
        results.append(order.order_id)

    db.commit()

    # re-serialize the affected orders
    orders_out = []
    for oid in results:
        o = db.query(Order).filter(Order.order_id == oid).first()
        if o:
            orders_out.append(serialize_order(o, include_events=True))

    return {
        "pushed": len(results),
        "created": created,
        "updated": updated,
        "orders": orders_out,
    }


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
