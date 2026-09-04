from app.database import SessionLocal
from app.order_service import create_order_service


db = SessionLocal()

try:

    result = create_order_service(
        product_id=2,
        quantity=1,
        idempotency_key="ai-service-test-001",
        db=db
    )

    order = result["order"]

    print("Order service test successful!")
    print("Order ID:", order.id)
    print("Product ID:", order.product_id)
    print("Quantity:", order.quantity)
    print("Total:", order.total_amount)
    print("Status:", order.status)

finally:
    db.close()