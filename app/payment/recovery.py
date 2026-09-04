from app.payment.state_machine import PaymentState


def recover_payment(
    current_state: PaymentState,
    gateway_status: str
) -> PaymentState:

    print("Recovery Engine activated")

    # -----------------------------------------
    # 1. Payment already confirmed
    # -----------------------------------------

    if gateway_status == "paid":

        print("Gateway confirms payment was successful")

        return PaymentState.PAID


    # -----------------------------------------
    # 2. Gateway confirms payment failed
    # -----------------------------------------

    if gateway_status == "failed":

        print("Gateway confirms payment failed")

        return PaymentState.FAILED


    # -----------------------------------------
    # 3. Gateway has no record of transaction
    # -----------------------------------------

    if gateway_status == "not_found":

        print(
            "Gateway has no record of payment."
        )

        print(
            "Transaction is safe to retry."
        )

        return PaymentState.INITIATED


    # -----------------------------------------
    # 4. Gateway still cannot confirm
    # -----------------------------------------

    if gateway_status == "unknown":

        print(
            "Gateway status still unknown."
        )

        print(
            "DO NOT retry automatically."
        )

        return PaymentState.UNKNOWN


    raise ValueError(
        f"Unknown gateway status: {gateway_status}"
    )