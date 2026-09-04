from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from app.products import products
from app.guardrails import validate_product
from app.ai_agent import generate_upsell_message
from app.order_service import create_order_service
from app.database import get_db
from app.cart import cart

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent Interface"]
)

class AgentCheckoutRequest(BaseModel):
    product_id: int
    quantity: int
    idempotency_key: str

@router.get("/manifest")
def get_agent_manifest():
    return {
        "merchant": {
            "name": "MerchantOS Demo Store",
            "description": "AI-native merchant commerce platform",
            "currency": "INR"
        },

        "capabilities": [
            "product_catalog",
            "product_search",
            "agent_checkout"
        ],

        "endpoints": {
            "catalog": "/agent/catalog",
            "search": "/agent/search",
            "checkout": "/agent/checkout"
        },

        "version": "1.0"
    }

@router.get("/catalog")
def get_agent_catalog():

    agent_catalog = []

    for product in products:

        structured_product = {
            "@context": "https://schema.org/",
            "@type": "Product",

            "name": product["name"],
            "description": product["description"],
            "category": product["category"],

            "identifier": f"merchantos-product-{product['id']}",

            "offers": {
                "@type": "Offer",
                "price": product["price"],
                "priceCurrency": product["currency"],
                "availability": (
                    "https://schema.org/InStock"
                    if product["stock"] > 0
                    else "https://schema.org/OutOfStock"
                )
            },

            "inventory": {
                "quantity": product["stock"]
            }
        }

        agent_catalog.append(structured_product)

    return {
        "@context": "https://schema.org/",
        "@type": "ItemList",

        "merchant": "MerchantOS Demo Store",

        "total_products": len(agent_catalog),

        "products": agent_catalog
    }

@router.get("/search")
def search_products(
    query: str = Query(default=""),
    max_price: int | None = Query(default=None)
):

    results = []

    query = query.lower().strip()

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
            results.append(product)

    return {
        "query": query,
        "max_price": max_price,
        "result_count": len(results),
        "products": results
    }

@router.get("/validate")
def validate_agent_purchase(
    product_id: int,
    quantity: int
):

    result = validate_product(
        product_id,
        quantity
    )

    return {
        "product_id": product_id,
        "quantity": quantity,
        "guardrail_decision": result
    }

@router.get("/upsell")
def get_upsell_recommendation():

    # No items in cart
    if not cart:
        return {
            "message": "Cart is empty",
            "recommendations": []
        }

    cart_product_ids = {
        item["product_id"]
        for item in cart
    }

    recommendations = []

    for product in products:

        # Don't recommend products already in cart
        if product["id"] in cart_product_ids:
            continue

        # Don't recommend out-of-stock products
        if product["stock"] <= 0:
            continue

        # Check whether product complements something in the cart
        for item in cart:

            cart_product = next(
                (
                    p for p in products
                    if p["id"] == item["product_id"]
                ),
                None
            )

            if cart_product is None:
                continue

            # Electronics + Electronics
            if (
                cart_product["category"] == "Electronics"
                and product["category"] == "Electronics"
            ):
                reason = (
                    f"{product['name']} complements the "
                    f"{cart_product['name']} in your purchase."
                )

                recommendations.append({
                    "product_id": product["id"],
                    "name": product["name"],
                    "description": product["description"],
                    "price": product["price"],
                    "currency": product["currency"],
                    "stock": product["stock"],
                    "reason": reason
                })

                break

            # Electronics + Accessories
            if (
                cart_product["category"] == "Electronics"
                and product["category"] == "Accessories"
            ):
                reason = (
                    f"{product['name']} can complement your "
                    f"{cart_product['name']} and improve your setup."
                )

                recommendations.append({
                    "product_id": product["id"],
                    "name": product["name"],
                    "description": product["description"],
                    "price": product["price"],
                    "currency": product["currency"],
                    "stock": product["stock"],
                    "reason": reason
                })

                break

    return {
        "message": "Upsell recommendations generated",
        "cart_items": len(cart),
        "recommendations": recommendations
    }

@router.get("/ai-upsell")
def ai_upsell():

    # Generate the normal deterministic recommendations first
    cart_items = []

    # Use the current cart

    for item in cart:
        product = next(
            (
                p for p in products
                if p["id"] == item["product_id"]
            ),
            None
        )

        if product:
            cart_items.append({
                "product_id": product["id"],
                "name": product["name"],
                "quantity": item["quantity"],
                "unit_price": product["price"]
            })

    if not cart_items:
        return {
            "message": "Cart is empty",
            "recommendation": None
        }

    # Generate candidate recommendations
    recommendations = []

    cart_product_ids = {
        item["product_id"]
        for item in cart_items
    }

    for product in products:

        if product["id"] in cart_product_ids:
            continue

        if product["stock"] <= 0:
            continue

        recommendations.append({
            "product_id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "price": product["price"],
            "currency": product["currency"],
            "stock": product["stock"],
            "reason": (
                f"{product['name']} can complement "
                f"your current purchase."
            )
        })

    if not recommendations:
        return {
            "message": "No recommendations available",
            "recommendation": None
        }

    # Ask Gemini to choose/explain the best recommendation
    ai_message = generate_upsell_message(
        cart_items,
        recommendations
    )

    return {
        "message": "AI upsell recommendation generated",
        "cart_items": cart_items,
        "recommendation": ai_message
    }
    
@router.post("/checkout")
def agent_checkout(
    request: AgentCheckoutRequest,
    db = Depends(get_db)
):

    try:

        result = create_order_service(
            product_id=request.product_id,
            quantity=request.quantity,
            idempotency_key=request.idempotency_key,
            db=db
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    order = result["order"]

    return {
        "message": (
            "Existing order returned"
            if result["duplicate"]
            else "Agent checkout successful"
        ),

        "order": {
            "order_id": order.id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status,
            "idempotency_key": order.idempotency_key
        }
    }