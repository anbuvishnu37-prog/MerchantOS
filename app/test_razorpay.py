from app.razorpay_client import client

data = {
    "amount": 79900,
    "currency": "INR",
    "receipt": "mos_test_001",
    "notes": {
        "purpose": "MerchantOS Razorpay integration test"
    }
}

order = client.order.create(data=data)

print("Razorpay Test Order created successfully")
print("Razorpay Order ID:", order["id"])
print("Amount:", order["amount"])
print("Currency:", order["currency"])
print("Status:", order["status"])