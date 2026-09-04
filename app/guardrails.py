from app.products import products


# Merchant-configured safety policies
MAX_TRANSACTION_AMOUNT = 5000
MAX_ITEM_QUANTITY = 5


def validate_product(product_id: int, quantity: int):

    # Rule 1: Quantity must be valid
    if quantity <= 0:
        return {
            "allowed": False,
            "reason": "Quantity must be greater than zero"
        }

    # Rule 2: Maximum quantity per product
    if quantity > MAX_ITEM_QUANTITY:
        return {
            "allowed": False,
            "reason": (
                f"Maximum allowed quantity per product is "
                f"{MAX_ITEM_QUANTITY}"
            )
        }

    # Find product
    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    # Rule 3: Product must exist
    if product is None:
        return {
            "allowed": False,
            "reason": "Product not found"
        }

    # Rule 4: Inventory must be sufficient
    if quantity > product["stock"]:
        return {
            "allowed": False,
            "reason": (
                f"Insufficient inventory. "
                f"Only {product['stock']} units available"
            )
        }

    # Calculate transaction amount
    total = product["price"] * quantity

    # Rule 5: Maximum transaction amount
    if total > MAX_TRANSACTION_AMOUNT:
        return {
            "allowed": False,
            "reason": (
                f"Transaction exceeds automated spending limit "
                f"of ₹{MAX_TRANSACTION_AMOUNT}"
            )
        }

    # Everything passed
    return {
        "allowed": True,
        "reason": "All guardrail checks passed",
        "product": product,
        "quantity": quantity,
        "total": total
    }