"""SQLAlchemy models for the GlobalCart Order Management System."""
import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from database import Base


class OrderStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    HELD = "HELD"
    PENDING = "PENDING"


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"


class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    status = Column(SAEnum(OrderStatus), nullable=False, default=OrderStatus.PROCESSING)
    payment_status = Column(
        SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING
    )
    total_amount = Column(Float, nullable=False, default=0.0)
    items = Column(Text, nullable=False, default="[]")  # JSON-encoded list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship(
        "OrderEvent",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderEvent.timestamp",
    )
    logs = relationship(
        "SystemLog",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="SystemLog.timestamp",
    )


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    actor = Column(String, nullable=False, default="system")

    order = relationship("Order", back_populates="events")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(SAEnum(LogLevel), nullable=False, default=LogLevel.INFO)
    message = Column(Text, nullable=False)
    internal_code = Column(String, nullable=True)

    order = relationship("Order", back_populates="logs")
