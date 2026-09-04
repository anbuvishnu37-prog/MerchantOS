from app.ai_agent import ask_merchantos_ai


question = """
I want to buy 1 Wireless Mouse.
Please place the order for me.
"""


response = ask_merchantos_ai(question)

print("MerchantOS AI response:")
print(response)