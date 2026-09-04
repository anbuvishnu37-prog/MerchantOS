from app.products import products
from app.guardrails import validate_product
from app.models import Order
from app.audit import create_audit_log


def create_order_service(
    product_id: int,
    quantity: int,
    idempotency_key: str,
    db
):
    # 1. Check idempotency
    existing_order = (
        db.query(Order)
        .filter(
            Order.idempotency_key == idempotency_key
        )
        .first()
    )

    if existing_order:
        return {
            "duplicate": True,
            "order": existing_order
        }

    # 2. Run guardrails
    validation = validate_product(
        product_id,
        quantity
    )

    if not validation["allowed"]:

        create_audit_log(
            db=db,
            event_type="AGENT_TRANSACTION",
            actor_type="BUYER_AGENT",
            actor_id="demo-agent-001",
            action="CREATE_ORDER",
            status="REJECTED",
            reason=validation["reason"],
            product_id=product_id,
            quantity=quantity,
            amount=0,
            idempotency_key=idempotency_key
        )

        db.commit()

        raise ValueError(validation["reason"])

    # 3. Get authoritative product information
    product = validation["product"]
    total = validation["total"]

    # 4. Create persistent order
    order = Order(
        product_id=product["id"],
        quantity=quantity,
        unit_price=product["price"],
        total_amount=total,
        currency=product["currency"],
        status="PENDING",
        idempotency_key=idempotency_key
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # 5. Audit successful order
    create_audit_log(
        db=db,
        event_type="AGENT_TRANSACTION",
        actor_type="BUYER_AGENT",
        actor_id="demo-agent-001",
        action="CREATE_ORDER",
        status="APPROVED",
        reason="Order passed guardrail validation",
        product_id=product["id"],
        quantity=quantity,
        amount=total,
        idempotency_key=idempotency_key
    )

    return {
        "duplicate": False,
        "order": order,
        "product": product
    }
    