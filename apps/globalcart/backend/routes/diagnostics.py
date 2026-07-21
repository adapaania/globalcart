"""Diagnostics endpoint: internal system logs, error codes, and recommended actions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Order
from serializers import serialize_log

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


def recommend_action(order: Order, logs):
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


@router.get("/{order_id}")
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

    return {
        "order_id": order.order_id,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "payment_status": order.payment_status.value
        if hasattr(order.payment_status, "value")
        else order.payment_status,
        "system_logs": logs,
        "error_codes": error_codes,
        "recommended_action": recommend_action(order, logs),
    }
