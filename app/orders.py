from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.products import products
from app.guardrails import validate_product
from app.database import get_db
from app.models import Order
from app.audit import create_audit_log
from app.order_service import create_order_service


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


class OrderRequest(BaseModel):
    product_id: int
    quantity: int


@router.post("/")
def create_order(
    request: OrderRequest,
    idempotency_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):

    # 1. Idempotency key is required
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required"
        )

    # 2. Create order through order service
    try:
        result = create_order_service(
            product_id=request.product_id,
            quantity=request.quantity,
            idempotency_key=idempotency_key,
            db=db
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # 3. Handle duplicate request
    if result["duplicate"]:

        existing_order = result["order"]

        return {
            "message": "Duplicate request detected",
            "order": {
                "order_id": existing_order.id,
                "product_id": existing_order.product_id,
                "quantity": existing_order.quantity,
                "unit_price": existing_order.unit_price,
                "total_amount": existing_order.total_amount,
                "currency": existing_order.currency,
                "status": existing_order.status,
                "idempotency_key": existing_order.idempotency_key
            }
        }

    # 4. Get newly created order
    order = result["order"]
    product = result["product"]

    # 5. Return response
    return {
        "message": "Order created successfully",
        "order": {
            "order_id": order.id,
            "product_id": order.product_id,
            "product_name": product["name"],
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status,
            "idempotency_key": order.idempotency_key
        }
    }

@router.get("/{order_id}")
def get_order_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return {
        "order_id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "total_amount": order.total_amount,
        "currency": order.currency,

        "order_status": order.status,

        "payment": {
            "status": order.payment_status,
            "attempts": order.payment_attempts,
            "payment_id": order.payment_id,
            "razorpay_order_id": order.razorpay_order_id
        },

        "idempotency_key": order.idempotency_key,
        "created_at": order.created_at
    }