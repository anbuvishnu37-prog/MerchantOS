from app.payment.simulator import simulate_payment


print("================================")
print("MerchantOS Payment Simulator")
print("================================")


print("\nTEST 1: SUCCESS")

result = simulate_payment("success")

print("Final state:", result)


print("\nTEST 2: FAILURE")

result = simulate_payment("failure")

print("Final state:", result)


print("\nTEST 3: NETWORK TIMEOUT")

result = simulate_payment("timeout")

print("Final state:", result)