from app.payment.state_machine import PaymentState
from app.payment.recovery import recover_payment


print("================================")
print("MerchantOS Recovery Engine")
print("================================")


print("\nTEST 1: UNKNOWN → PAID")

result = recover_payment(
    PaymentState.UNKNOWN,
    "paid"
)

print("Recovered state:", result)


print("\nTEST 2: UNKNOWN → FAILED")

result = recover_payment(
    PaymentState.UNKNOWN,
    "failed"
)

print("Recovered state:", result)


print("\nTEST 3: UNKNOWN → SAFE RETRY")

result = recover_payment(
    PaymentState.UNKNOWN,
    "not_found"
)

print("Recovered state:", result)


print("\nTEST 4: UNKNOWN → UNKNOWN")

result = recover_payment(
    PaymentState.UNKNOWN,
    "unknown"
)

print("Recovered state:", result)