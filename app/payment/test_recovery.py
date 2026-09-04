from app.payment.state_machine import PaymentState
from app.payment.recovery import recover_payment


def test_recovery_paid():
    result = recover_payment(
        PaymentState.INITIATED,
        "paid"
    )
    assert result == PaymentState.PAID


def test_recovery_failed():
    result = recover_payment(
        PaymentState.INITIATED,
        "failed"
    )
    assert result == PaymentState.FAILED


def test_recovery_not_found():
    result = recover_payment(
        PaymentState.INITIATED,
        "not_found"
    )
    assert result == PaymentState.INITIATED


def test_recovery_unknown():
    result = recover_payment(
        PaymentState.INITIATED,
        "unknown"
    )
    assert result == PaymentState.UNKNOWN


def test_recovery_invalid_status():
    try:
        recover_payment(
            PaymentState.INITIATED,
            "invalid"
        )
        assert False
    except ValueError:
        assert True