from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Order
from app.payment.state_machine import PaymentState, transition
from app.payment.recovery import recover_payment
from app.audit import create_audit_log
from app.razorpay_client import client


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


class RecoveryRequest(BaseModel):
    gateway_status: str

class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/initiate/{order_id}")
def initiate_payment(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Payment already completed
    if order.payment_status == PaymentState.PAID.value:
        raise HTTPException(
            status_code=400,
            detail="Payment is already completed"
        )

    # Payment already initiated
    # Don't create another Razorpay order
    if (
        order.payment_status == PaymentState.INITIATED.value
        and order.razorpay_order_id
    ):
        return {
            "message": "Payment already initiated",
            "order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "amount": int(order.total_amount * 100),
            "currency": order.currency,
            "payment_status": order.payment_status,
            "payment_attempts": order.payment_attempts
        }

    # Only NOT_STARTED payments can be initiated
    try:
        current_state = PaymentState(order.payment_status)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid payment state: {order.payment_status}"
        )

    if current_state != PaymentState.NOT_STARTED:
        raise HTTPException(
            status_code=400,
            detail=f"Payment cannot be initiated from state: {current_state.value}"
        )

    # Create Razorpay Test Mode order
    data = {
        "amount": int(order.total_amount * 100),
        "currency": order.currency,
        "receipt": f"mos_{order.id}_{int(datetime.utcnow().timestamp())}",
        "notes": {
            "merchant_order_id": str(order.id)
        }
    }

    try:
        razorpay_order = client.order.create(data=data)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Razorpay order creation failed: {str(error)}"
        )

    # Move payment state:
    # NOT_STARTED → INITIATED
    try:
        new_state = transition(
            current_state,
            PaymentState.INITIATED
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    order.payment_status = new_state.value
    order.razorpay_order_id = razorpay_order["id"]
    order.payment_attempts += 1

    db.commit()
    db.refresh(order)

    # Audit the payment initiation
    create_audit_log(
        db=db,
        event_type="PAYMENT_INITIATED",
        actor_type="SYSTEM",
        actor_id="payment-engine",
        action="INITIATE_PAYMENT",
        status="INITIATED",
        reason="Razorpay Test Mode order created",
        product_id=order.product_id,
        quantity=order.quantity,
        amount=order.total_amount,
        idempotency_key=order.idempotency_key
    )

    return {
        "message": "Payment initiated successfully",
        "order_id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "amount": razorpay_order["amount"],
        "currency": razorpay_order["currency"],
        "payment_status": order.payment_status,
        "payment_attempts": order.payment_attempts
    }

@router.post("/verify")
def verify_payment(
    request: PaymentVerificationRequest,
    db: Session = Depends(get_db)
):
    # 1. Find our local order using Razorpay Order ID
    order = (
        db.query(Order)
        .filter(Order.razorpay_order_id == request.razorpay_order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Razorpay order not found"
        )

    # 2. Prevent duplicate verification
    if order.payment_status == PaymentState.PAID.value:
        return {
            "message": "Payment already verified",
            "order_id": order.id,
            "payment_status": order.payment_status,
            "payment_id": order.payment_id
        }

    # 3. Payment must be in a state where verification makes sense
    if order.payment_status not in [
        PaymentState.INITIATED.value,
        PaymentState.UNKNOWN.value
    ]:
        raise HTTPException(
            status_code=400,
            detail=f"Payment cannot be verified from state: {order.payment_status}"
        )

    # 4. Verify Razorpay signature
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": request.razorpay_order_id,
            "razorpay_payment_id": request.razorpay_payment_id,
            "razorpay_signature": request.razorpay_signature
        })

    except Exception:
        create_audit_log(
            db=db,
            event_type="PAYMENT_VERIFICATION",
            actor_type="SYSTEM",
            actor_id="payment-verifier",
            action="VERIFY_PAYMENT",
            status="REJECTED",
            reason="Invalid Razorpay payment signature",
            product_id=order.product_id,
            quantity=order.quantity,
            amount=order.total_amount,
            idempotency_key=order.idempotency_key
        )

        raise HTTPException(
            status_code=400,
            detail="Payment signature verification failed"
        )

    # 5. Signature is valid → move payment to PAID
    try:
        new_state = transition(
            PaymentState(order.payment_status),
            PaymentState.PAID
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    order.payment_status = new_state.value
    order.payment_id = request.razorpay_payment_id
    # Reduce inventory after successful payment
    from app.products import products

    for product in products:
        if product["id"] == order.product_id:
            product["stock"] -= order.quantity
            break

    # Payment successfully verified → confirm the order
    order.status = "PAID"

    db.commit()
    db.refresh(order)

    # 6. Record successful verification
    create_audit_log(
        db=db,
        event_type="PAYMENT_VERIFICATION",
        actor_type="SYSTEM",
        actor_id="payment-verifier",
        action="VERIFY_PAYMENT",
        status="PAID",
        reason="Razorpay payment signature verified successfully",
        product_id=order.product_id,
        quantity=order.quantity,
        amount=order.total_amount,
        idempotency_key=order.idempotency_key
    )

    return {
        "message": "Payment verified successfully",
        "order_id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_payment_id": order.payment_id,
        "payment_status": order.payment_status,
        "amount": order.total_amount,
        "currency": order.currency
    }

@router.post("/recover/{order_id}")
def recover_order_payment(
    order_id: int,
    request: RecoveryRequest,
    db: Session = Depends(get_db)
):

    # 1. Find order
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # 2. Validate gateway status
    allowed_statuses = {
        "paid",
        "failed",
        "not_found",
        "unknown"
    }

    if request.gateway_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid gateway status"
        )

    # 3. Convert database state to PaymentState
    try:
        current_state = PaymentState(order.payment_status)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid payment state in database: {order.payment_status}"
        )

    # 4. Recovery engine decides the next state
    try:
        new_state = recover_payment(
            current_state,
            request.gateway_status
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # 5. Validate state transition
    try:
        transition(current_state, new_state)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid payment transition: "
                f"{current_state} → {new_state}"
            )
        )

    # 6. Update database
    order.payment_status = new_state.value
    order.payment_attempts += 1

    # Keep order status consistent with payment state
    if new_state == PaymentState.PAID:
        order.status = "PAID"

    elif new_state == PaymentState.FAILED:
        order.status = "PAYMENT_FAILED"

    elif new_state == PaymentState.UNKNOWN:
        order.status = "PAYMENT_UNKNOWN"

    elif new_state == PaymentState.INITIATED:
        order.status = "PENDING"

    db.commit()
    db.refresh(order)

    # 7. Create audit record
    create_audit_log(
        db=db,
        event_type="PAYMENT_RECOVERY",
        actor_type="SYSTEM",
        actor_id="recovery-engine",
        action="RECOVER_PAYMENT",
        status=new_state.value,
        reason=f"Gateway status: {request.gateway_status}",
        product_id=order.product_id,
        quantity=order.quantity,
        amount=order.total_amount,
        idempotency_key=order.idempotency_key
    )

    return {
        "message": "Payment recovery completed",
        "order_id": order.id,
        "previous_state": current_state.value,
        "gateway_status": request.gateway_status,
        "new_state": new_state.value,
        "payment_attempts": order.payment_attempts
    }