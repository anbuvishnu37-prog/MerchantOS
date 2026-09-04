from fastapi import APIRouter

from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from datetime import datetime

from app.database import Base, SessionLocal
router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    event_type = Column(
        String,
        nullable=False
    )

    actor_type = Column(
        String,
        nullable=False
    )

    actor_id = Column(
        String,
        nullable=True
    )

    action = Column(
        String,
        nullable=False
    )

    product_id = Column(
        Integer,
        nullable=True
    )

    quantity = Column(
        Integer,
        nullable=True
    )

    amount = Column(
        Float,
        nullable=True
    )

    status = Column(
        String,
        nullable=False
    )

    reason = Column(
        Text,
        nullable=True
    )

    idempotency_key = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

def create_audit_log(
    db,
    event_type,
    actor_type,
    actor_id,
    action,
    status,
    reason=None,
    product_id=None,
    quantity=None,
    amount=None,
    idempotency_key=None
):

    log = AuditLog(

        event_type=event_type,

        actor_type=actor_type,

        actor_id=actor_id,

        action=action,

        status=status,

        reason=reason,

        product_id=product_id,

        quantity=quantity,

        amount=amount,

        idempotency_key=idempotency_key
    )

    db.add(log)

    db.commit()

    db.refresh(log)

    return log

@router.get("/logs")
def get_audit_logs():

    db = SessionLocal()

    try:

        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .all()
        )

        return [
            {
                "id": log.id,
                "event_type": log.event_type,
                "actor_type": log.actor_type,
                "actor_id": log.actor_id,
                "action": log.action,
                "product_id": log.product_id,
                "quantity": log.quantity,
                "amount": log.amount,
                "status": log.status,
                "reason": log.reason,
                "idempotency_key": log.idempotency_key,
                "created_at": log.created_at
            }

            for log in logs
        ]

    finally:

        db.close()
        
    