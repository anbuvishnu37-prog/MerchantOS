from app.payment.state_machine import (
    PaymentState,
    transition
)


print("Test 1: NOT_STARTED → INITIATED")

result = transition(
    PaymentState.NOT_STARTED,
    PaymentState.INITIATED
)

print("Result:", result)


print("\nTest 2: INITIATED → PAID")

result = transition(
    PaymentState.INITIATED,
    PaymentState.PAID
)

print("Result:", result)


print("\nTest 3: INITIATED → UNKNOWN")

result = transition(
    PaymentState.INITIATED,
    PaymentState.UNKNOWN
)

print("Result:", result)


print("\nTest 4: PAID → INITIATED")

try:

    result = transition(
        PaymentState.PAID,
        PaymentState.INITIATED
    )

    print("Result:", result)

except ValueError as error:

    print("Correctly rejected:", error)