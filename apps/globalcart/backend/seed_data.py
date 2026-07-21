"""Seed the GlobalCart database with the support scenarios.

Can be run standalone (``python seed_data.py``) or imported and called
via ``seed_database(db)`` from the FastAPI startup hook.
"""
import json
from datetime import datetime, timedelta

from database import SessionLocal, engine, Base
from models import (
    Order,
    OrderEvent,
    SystemLog,
    OrderStatus,
    PaymentStatus,
    LogLevel,
)


def _dt(base, **kwargs):
    return base + timedelta(**kwargs)


def seed_database(db):
    """Populate the database with the four demo orders and related data."""
    now = datetime.utcnow()

    # ------------------------------------------------------------------
    # GC-1001 — Normal delivered order, all green
    # ------------------------------------------------------------------
    base1 = now - timedelta(days=6)
    order1 = Order(
        order_id="GC-1001",
        customer_name="Alice Johnson",
        customer_email="alice.johnson@example.com",
        status=OrderStatus.DELIVERED,
        payment_status=PaymentStatus.SUCCESS,
        total_amount=149.99,
        items=json.dumps(
            [
                {"sku": "PROD-101", "name": "Wireless Headphones", "qty": 1, "price": 99.99},
                {"sku": "PROD-205", "name": "USB-C Charging Cable", "qty": 2, "price": 25.00},
            ]
        ),
        created_at=base1,
        updated_at=_dt(base1, days=3),
    )
    order1.events = [
        OrderEvent(order_id="GC-1001", timestamp=base1, event_type="ORDER_PLACED",
                   description="Order placed by customer.", actor="customer"),
        OrderEvent(order_id="GC-1001", timestamp=_dt(base1, minutes=2), event_type="PAYMENT_CAPTURED",
                   description="Payment of $149.99 captured successfully.", actor="payment-gateway"),
        OrderEvent(order_id="GC-1001", timestamp=_dt(base1, hours=5), event_type="ORDER_PROCESSING",
                   description="Order sent to warehouse for fulfillment.", actor="system"),
        OrderEvent(order_id="GC-1001", timestamp=_dt(base1, days=1), event_type="SHIPPED",
                   description="Package handed to carrier. Tracking: 1Z-GC-1001.", actor="warehouse"),
        OrderEvent(order_id="GC-1001", timestamp=_dt(base1, days=3), event_type="DELIVERED",
                   description="Package delivered and signed for.", actor="carrier"),
    ]
    order1.logs = [
        SystemLog(order_id="GC-1001", timestamp=base1, level=LogLevel.INFO,
                  message="Order intake validation passed.", internal_code="OK_INTAKE"),
        SystemLog(order_id="GC-1001", timestamp=_dt(base1, days=1), level=LogLevel.INFO,
                  message="Fulfillment completed without incident.", internal_code="OK_FULFILL"),
    ]

    # ------------------------------------------------------------------
    # GC-1042 — Payment SUCCESS, stuck in PROCESSING, warehouse timeout
    # ------------------------------------------------------------------
    base2 = now - timedelta(days=2)
    order2 = Order(
        order_id="GC-1042",
        customer_name="Bob Martinez",
        customer_email="bob.martinez@example.com",
        status=OrderStatus.PROCESSING,
        payment_status=PaymentStatus.SUCCESS,
        total_amount=329.50,
        items=json.dumps(
            [
                {"sku": "PROD-330", "name": "Mechanical Keyboard", "qty": 1, "price": 129.50},
                {"sku": "PROD-412", "name": "4K Monitor", "qty": 1, "price": 200.00},
            ]
        ),
        created_at=base2,
        updated_at=_dt(base2, hours=6),
    )
    order2.events = [
        OrderEvent(order_id="GC-1042", timestamp=base2, event_type="ORDER_PLACED",
                   description="Order placed by customer.", actor="customer"),
        OrderEvent(order_id="GC-1042", timestamp=_dt(base2, minutes=1), event_type="PAYMENT_CAPTURED",
                   description="Payment of $329.50 captured successfully.", actor="payment-gateway"),
        OrderEvent(order_id="GC-1042", timestamp=_dt(base2, hours=1), event_type="ORDER_PROCESSING",
                   description="Order queued for warehouse fulfillment.", actor="system"),
        OrderEvent(order_id="GC-1042", timestamp=_dt(base2, hours=6), event_type="FULFILLMENT_RETRY",
                   description="Fulfillment attempt failed; awaiting retry.", actor="system"),
    ]
    order2.logs = [
        SystemLog(order_id="GC-1042", timestamp=base2, level=LogLevel.INFO,
                  message="Order intake validation passed.", internal_code="OK_INTAKE"),
        SystemLog(order_id="GC-1042", timestamp=_dt(base2, minutes=1), level=LogLevel.INFO,
                  message="Payment captured and reconciled.", internal_code="OK_PAYMENT"),
        SystemLog(order_id="GC-1042", timestamp=_dt(base2, hours=6), level=LogLevel.ERROR,
                  message="Validation_Error: Warehouse_API_Timeout while dispatching fulfillment request.",
                  internal_code="Validation_Error: Warehouse_API_Timeout"),
    ]

    # ------------------------------------------------------------------
    # GC-2020 — HELD, high-value $5,200, manual verification required
    # ------------------------------------------------------------------
    base3 = now - timedelta(days=1)
    order3 = Order(
        order_id="GC-2020",
        customer_name="Catherine Lee",
        customer_email="catherine.lee@example.com",
        status=OrderStatus.HELD,
        payment_status=PaymentStatus.SUCCESS,
        total_amount=5200.00,
        items=json.dumps(
            [
                {"sku": "PROD-900", "name": "Professional Camera Kit", "qty": 1, "price": 4200.00},
                {"sku": "PROD-901", "name": "Telephoto Lens", "qty": 1, "price": 1000.00},
            ]
        ),
        created_at=base3,
        updated_at=_dt(base3, hours=2),
    )
    order3.events = [
        OrderEvent(order_id="GC-2020", timestamp=base3, event_type="ORDER_PLACED",
                   description="Order placed by customer.", actor="customer"),
        OrderEvent(order_id="GC-2020", timestamp=_dt(base3, minutes=2), event_type="PAYMENT_CAPTURED",
                   description="Payment of $5,200.00 captured successfully.", actor="payment-gateway"),
        OrderEvent(order_id="GC-2020", timestamp=_dt(base3, hours=1), event_type="FRAUD_REVIEW",
                   description="Order flagged for high-value manual review.", actor="risk-engine"),
        OrderEvent(order_id="GC-2020", timestamp=_dt(base3, hours=2), event_type="ORDER_HELD",
                   description="Order placed on hold pending financial verification.", actor="system"),
    ]
    order3.logs = [
        SystemLog(order_id="GC-2020", timestamp=base3, level=LogLevel.INFO,
                  message="Order intake validation passed.", internal_code="OK_INTAKE"),
        SystemLog(order_id="GC-2020", timestamp=_dt(base3, hours=2), level=LogLevel.WARN,
                  message="HIGH_VALUE_ORDER: Manual financial verification required before fulfillment.",
                  internal_code="HIGH_VALUE_ORDER"),
    ]

    # ------------------------------------------------------------------
    # GC-3030 — PENDING, SKU out of stock
    # ------------------------------------------------------------------
    base4 = now - timedelta(hours=10)
    order4 = Order(
        order_id="GC-3030",
        customer_name="David Kim",
        customer_email="david.kim@example.com",
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        total_amount=89.00,
        items=json.dumps(
            [
                {"sku": "PROD-887", "name": "Limited Edition Sneakers", "qty": 1, "price": 89.00},
            ]
        ),
        created_at=base4,
        updated_at=_dt(base4, hours=1),
    )
    order4.events = [
        OrderEvent(order_id="GC-3030", timestamp=base4, event_type="ORDER_PLACED",
                   description="Order placed by customer.", actor="customer"),
        OrderEvent(order_id="GC-3030", timestamp=_dt(base4, minutes=5), event_type="PAYMENT_AUTHORIZED",
                   description="Payment authorized, awaiting capture on fulfillment.", actor="payment-gateway"),
        OrderEvent(order_id="GC-3030", timestamp=_dt(base4, hours=1), event_type="INVENTORY_CHECK",
                   description="Inventory check failed for one or more items.", actor="system"),
    ]
    order4.logs = [
        SystemLog(order_id="GC-3030", timestamp=base4, level=LogLevel.INFO,
                  message="Order intake validation passed.", internal_code="OK_INTAKE"),
        SystemLog(order_id="GC-3030", timestamp=_dt(base4, hours=1), level=LogLevel.ERROR,
                  message="SKU_OUT_OF_STOCK: Item PROD-887 unavailable in all fulfillment centers.",
                  internal_code="SKU_OUT_OF_STOCK: Item PROD-887 unavailable"),
    ]

    db.add_all([order1, order2, order3, order4])
    db.commit()


def run():
    """Create tables and seed from a standalone invocation."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Order).count()
        if existing > 0:
            print(f"Database already has {existing} orders. Skipping seed.")
            return
        seed_database(db)
        print("Seeded database with demo orders: GC-1001, GC-1042, GC-2020, GC-3030")
    finally:
        db.close()


if __name__ == "__main__":
    run()
