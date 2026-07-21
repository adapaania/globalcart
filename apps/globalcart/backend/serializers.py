"""Shared serialization helpers for the GlobalCart API responses."""
import json

from models import Order, OrderEvent, SystemLog


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
