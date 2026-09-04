from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from app.database import Base


class Order(Base):

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, nullable=False)

    quantity = Column(Integer, nullable=False)

    unit_price = Column(Float, nullable=False)

    total_amount = Column(Float, nullable=False)

    currency = Column(String, default="INR")

    status = Column(
        String,
        default="PENDING"
    )

    payment_status = Column(
        String,
        default="NOT_STARTED"
    )

    payment_attempts = Column(
        Integer,
        default=0
    )

    payment_id = Column(
        String,
        nullable=True
    )
    razorpay_order_id = Column(String, nullable=True)

    idempotency_key = Column(
        String,
        unique=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )