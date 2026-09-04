from app.payment.state_machine import PaymentState


def simulate_payment(scenario: str) -> PaymentState:

    if scenario == "success":

        print("Payment gateway: Payment successful")

        return PaymentState.PAID


    elif scenario == "failure":

        print("Payment gateway: Payment rejected")

        return PaymentState.FAILED


    elif scenario == "timeout":

        print("Payment gateway: Network timeout")

        return PaymentState.UNKNOWN


    else:

        raise ValueError(
            f"Unknown payment scenario: {scenario}"
        )