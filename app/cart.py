from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.products import products


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


class CartItem(BaseModel):
    product_id: int
    quantity: int


cart = []


@router.post("/add")
def add_to_cart(item: CartItem):

    # Find product
    product = next(
        (p for p in products if p["id"] == item.product_id),
        None
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Validate quantity
    if item.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # Validate inventory
    if item.quantity > product["stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product['stock']} units available"
        )

    # Check if product already exists in cart
    for cart_item in cart:

        if cart_item["product_id"] == item.product_id:

            new_quantity = cart_item["quantity"] + item.quantity

            if new_quantity > product["stock"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {product['stock']} units available"
                )

            cart_item["quantity"] = new_quantity

            return {
                "message": "Cart updated",
                "cart": cart
            }

    # Add new item
    cart.append({
        "product_id": item.product_id,
        "quantity": item.quantity
    })

    return {
        "message": "Product added to cart",
        "cart": cart
    }


@router.get("/")
def get_cart():

    cart_details = []
    total = 0

    for item in cart:

        product = next(
            p for p in products
            if p["id"] == item["product_id"]
        )

        subtotal = product["price"] * item["quantity"]

        cart_details.append({
            "product_id": product["id"],
            "name": product["name"],
            "quantity": item["quantity"],
            "unit_price": product["price"],
            "subtotal": subtotal
        })

        total += subtotal

    return {
        "items": cart_details,
        "total": total,
        "currency": "INR"
    }