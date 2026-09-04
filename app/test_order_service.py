from app.database import SessionLocal
from app.order_service import create_order_service
import uuid


def test_create_order_service():

    db = SessionLocal()

    try:

        result = create_order_service(
            product_id=2,
            quantity=1,
            idempotency_key=f"ai-service-test-{uuid.uuid4()}",
            db=db
        )

        order = result["order"]

        assert result["duplicate"] is False
        assert order.product_id == 2
        assert order.quantity == 1
        assert order.total_amount == 799
        assert order.status == "PENDING"

    finally:
        db.close()