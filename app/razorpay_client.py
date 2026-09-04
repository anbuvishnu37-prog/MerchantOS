import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not KEY_ID or not KEY_SECRET:
    raise ValueError("Razorpay credentials not found in .env")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))