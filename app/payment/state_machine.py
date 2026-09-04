from enum import Enum


class PaymentState(str, Enum):

    NOT_STARTED = "NOT_STARTED"

    INITIATED = "INITIATED"

    PAID = "PAID"

    FAILED = "FAILED"

    UNKNOWN = "UNKNOWN"


ALLOWED_TRANSITIONS = {

    PaymentState.NOT_STARTED: [
        PaymentState.INITIATED
    ],

    PaymentState.INITIATED: [
        PaymentState.PAID,
        PaymentState.FAILED,
        PaymentState.UNKNOWN
    ],

    PaymentState.UNKNOWN: [
        PaymentState.PAID,
        PaymentState.FAILED,
        PaymentState.INITIATED
    ],

    PaymentState.PAID: [],

    PaymentState.FAILED: []
}


def can_transition(
    current_state: PaymentState,
    new_state: PaymentState
) -> bool:

    return new_state in ALLOWED_TRANSITIONS.get(
        current_state,
        []
    )


def transition(
    current_state: PaymentState,
    new_state: PaymentState
) -> PaymentState:

    if not can_transition(
        current_state,
        new_state
    ):

        raise ValueError(
            f"Invalid payment transition: "
            f"{current_state} → {new_state}"
        )

    return new_state