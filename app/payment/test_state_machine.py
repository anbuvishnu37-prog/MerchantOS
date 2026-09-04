from app.payment.state_machine import PaymentState, can_transition, transition


def test_not_started_to_initiated():
    assert can_transition(
        PaymentState.NOT_STARTED,
        PaymentState.INITIATED
    )


def test_initiated_to_paid():
    assert can_transition(
        PaymentState.INITIATED,
        PaymentState.PAID
    )


def test_initiated_to_failed():
    assert can_transition(
        PaymentState.INITIATED,
        PaymentState.FAILED
    )


def test_initiated_to_unknown():
    assert can_transition(
        PaymentState.INITIATED,
        PaymentState.UNKNOWN
    )


def test_paid_cannot_transition():
    assert not can_transition(
        PaymentState.PAID,
        PaymentState.FAILED
    )


def test_transition_returns_new_state():
    assert transition(
        PaymentState.INITIATED,
        PaymentState.PAID
    ) == PaymentState.PAID