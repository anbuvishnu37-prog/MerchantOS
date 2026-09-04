import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.products import products
from app.guardrails import validate_product
from app.order_service import create_order_service
from app.database import SessionLocal


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")


client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=30000
    )
)


# ============================================================
# PRODUCT SEARCH TOOL
# ============================================================

def search_products_tool(
    query: str,
    max_price: int | None = None
):
    """
    Search the MerchantOS product catalog.
    """

    query = query.lower().strip()

    results = []

    for product in products:

        matches_query = (
            query == ""
            or query in product["name"].lower()
            or query in product["description"].lower()
            or query in product["category"].lower()
        )

        matches_price = (
            max_price is None
            or product["price"] <= max_price
        )

        if matches_query and matches_price:

            results.append({
                "product_id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "category": product["category"],
                "price": product["price"],
                "currency": product["currency"],
                "stock": product["stock"]
            })

    return {
        "query": query,
        "max_price": max_price,
        "result_count": len(results),
        "products": results
    }


# ============================================================
# PURCHASE VALIDATION TOOL
# ============================================================

def validate_purchase_tool(
    product_id: int,
    quantity: int
):
    """
    Validate a proposed purchase using MerchantOS guardrails.
    """

    result = validate_product(
        product_id,
        quantity
    )

    return result


# ============================================================
# ORDER CREATION TOOL
# ============================================================

def create_order_tool(
    product_id: int,
    quantity: int,
    idempotency_key: str
):
    """
    Create a MerchantOS order through the authoritative
    order service.
    """

    db = SessionLocal()

    try:

        result = create_order_service(
            product_id=product_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            db=db
        )

        order = result["order"]

        if result["duplicate"]:

            return {
                "success": True,
                "duplicate": True,
                "message": "This order request was already processed.",
                "order_id": order.id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "total_amount": order.total_amount,
                "currency": order.currency,
                "status": order.status
            }

        return {
            "success": True,
            "duplicate": False,
            "message": "Order created successfully.",
            "order_id": order.id,
            "product_id": order.product_id,
            "product_name": result["product"]["name"],
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status
        }

    except ValueError as error:

        return {
            "success": False,
            "message": str(error)
        }

    finally:
        db.close()


# ============================================================
# MAIN AI AGENT
# ============================================================

def ask_merchantos_ai(user_message: str):

    message = user_message.lower().strip()

    # ========================================================
    # PURCHASE REQUEST: WIRELESS MOUSE
    # ========================================================

    if "wireless mouse" in message and (
        "buy" in message
        or "purchase" in message
        or "order" in message
        or "place the order" in message
    ):

        # Determine quantity
        quantity = 1

        if "10" in message:
            quantity = 10
        elif "5" in message:
            quantity = 5
        elif "4" in message:
            quantity = 4
        elif "3" in message:
            quantity = 3
        elif "2" in message:
            quantity = 2

        product_id = 2

        # ----------------------------------------------------
        # SAFETY VALIDATION
        # ----------------------------------------------------

        validation = validate_purchase_tool(
            product_id=product_id,
            quantity=quantity
        )

        if not validation["allowed"]:

            return (
                "Purchase not allowed.\n\n"
                f"Reason: {validation['reason']}\n"
                "Product: Wireless Mouse\n"
                f"Requested quantity: {quantity}\n"
                "Maximum allowed quantity: 5"
            )

        # ----------------------------------------------------
        # CREATE ORDER
        # ----------------------------------------------------

        import uuid

        idempotency_key = f"ai-order-{uuid.uuid4()}"

        order_result = create_order_tool(
            product_id=product_id,
            quantity=quantity,
            idempotency_key=idempotency_key
        )

        if not order_result["success"]:

            return (
                "I could not complete the order.\n\n"
                f"Reason: {order_result['message']}"
            )

        # ----------------------------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------------------------

        return (
            "Order placed successfully!\n\n"
            f"Order ID: {order_result['order_id']}\n"
            f"Product: {order_result['product_name']}\n"
            f"Quantity: {order_result['quantity']}\n"
            f"Unit Price: ₹{order_result['unit_price']}\n"
            f"Total Amount: ₹{order_result['total_amount']}\n"
            f"Status: {order_result['status']}"
        )

    # ========================================================
    # NORMAL AI CONVERSATION
    # ========================================================

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are the MerchantOS AI commerce assistant. "
                    "Help customers understand products, shopping "
                    "and recommendations. "
                    "Never invent product information, prices, "
                    "stock, discounts, or orders."
                ),
                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                ),
                max_output_tokens=200
            )
        )

        return response.text

    except Exception as error:

        print(f"Gemini unavailable: {error}")

        return (
            "MerchantOS AI is temporarily unavailable. "
            "However, MerchantOS transaction safety and order "
            "processing remain operational."
        )
def generate_upsell_message(
    cart_items,
    recommendations
):

    cart_text = "\n".join(
        f"- {item['name']} × {item['quantity']} "
        f"(₹{item['unit_price']})"
        for item in cart_items
    )

    recommendation_text = "\n".join(
        f"- {item['name']} — ₹{item['price']}: "
        f"{item['reason']}"
        for item in recommendations
    )

    prompt = f"""
You are the AI commerce assistant for MerchantOS.

Customer cart:

{cart_text}

Candidate recommendations:

{recommendation_text}

Choose the most useful recommendation.

Explain briefly why it complements the customer's purchase.

Do not invent products, prices, discounts, features, or availability.

Keep the response below 50 words.
"""

    response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="low"
        ),
        max_output_tokens=100
    )
)

    return response.text