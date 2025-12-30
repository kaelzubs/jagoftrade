"""
Shipping calculation module for the drop-shipping application.
Supports multiple shipping methods based on weight, destination, and cart value.
"""

from decimal import Decimal
from django.conf import settings


# Shipping method definitions
SHIPPING_METHODS = {
    "standard": {
        "name": "Standard Shipping",
        "base_cost": Decimal("500.00"),  # NGN
        "per_kg_cost": Decimal("100.00"),
        "est_days": (5, 10),
    },
    "express": {
        "name": "Express Shipping",
        "base_cost": Decimal("1000.00"),
        "per_kg_cost": Decimal("150.00"),
        "est_days": (2, 3),
    },
    "economy": {
        "name": "Economy Shipping",
        "base_cost": Decimal("300.00"),
        "per_kg_cost": Decimal("50.00"),
        "est_days": (7, 14),
    },
}

# Regional shipping surcharges (state-based in Nigeria)
# Add more states as needed
REGIONAL_SURCHARGES = {
    "lagos": Decimal("0.0"),  # No surcharge for Lagos (base location)
    "kano": Decimal("200.00"),
    "abuja": Decimal("100.00"),
    "rivers": Decimal("250.00"),
    "ogun": Decimal("50.00"),
    "oyo": Decimal("100.00"),
    "kwara": Decimal("150.00"),
    "enugu": Decimal("300.00"),
    "anambra": Decimal("250.00"),
    "imo": Decimal("250.00"),
    "abia": Decimal("250.00"),
    "calabar": Decimal("350.00"),
    "gombe": Decimal("200.00"),
    "bauchi": Decimal("200.00"),
    "kaduna": Decimal("150.00"),
    "katsina": Decimal("250.00"),
    "zamfara": Decimal("300.00"),
    "kebbi": Decimal("300.00"),
    "niger": Decimal("150.00"),
    "nasarawa": Decimal("100.00"),
    "plateau": Decimal("200.00"),
    "taraba": Decimal("250.00"),
    "adamawa": Decimal("250.00"),
    "yobe": Decimal("250.00"),
    "borno": Decimal("300.00"),
    "jigawa": Decimal("200.00"),
    "akwa_ibom": Decimal("300.00"),
    "cross_river": Decimal("300.00"),
    "ebonyi": Decimal("250.00"),
    "edo": Decimal("200.00"),
    "delta": Decimal("250.00"),
    "bayelsa": Decimal("300.00"),
    "ekiti": Decimal("150.00"),
    "osun": Decimal("100.00"),
}


def calculate_weight(cart_items):
    """
    Calculate total weight of items in cart.
    cart_items should be an iterable of dicts with 'product' and 'quantity' keys.
    """
    total_weight = Decimal("0")
    for item in cart_items:
        product = item.get("product")
        quantity = item.get("quantity", 1)
        if product and hasattr(product, "weight") and product.weight:
            total_weight += Decimal(str(product.weight)) * quantity
    return total_weight


def get_regional_surcharge(state):
    """
    Get surcharge for a given state (case-insensitive).
    Returns 0 if state not found (defaults to standard rate).
    """
    if not state:
        return Decimal("0")
    state_lower = str(state).lower().strip().replace(" ", "_")
    return REGIONAL_SURCHARGES.get(state_lower, Decimal("100.00"))


def calculate_shipping(cart_items, shipping_method="standard", destination_state=None, cart_subtotal=Decimal("0")):
    """
    Calculate shipping cost dynamically.

    Args:
        cart_items: list of cart item dicts with 'product' and 'quantity'
        shipping_method: one of 'standard', 'express', 'economy'
        destination_state: customer's state (used for surcharge)
        cart_subtotal: subtotal of the cart (Decimal)

    Returns:
        dict with keys: cost, method_name, est_days, breakdown (for transparency)
    """
    if shipping_method not in SHIPPING_METHODS:
        shipping_method = "standard"

    method_config = SHIPPING_METHODS[shipping_method]
    total_weight = calculate_weight(cart_items)

    # Calculate base shipping cost (base + weight-based)
    base_cost = method_config["base_cost"]
    weight_cost = method_config["per_kg_cost"] * total_weight
    subtotal_cost = base_cost + weight_cost

    # Apply regional surcharge
    regional_surcharge = get_regional_surcharge(destination_state)

    # Check for free shipping threshold
    free_shipping_threshold = getattr(settings, "SHIPPING_FREE_THRESHOLD", Decimal("10000.00"))
    if cart_subtotal >= free_shipping_threshold and shipping_method == "standard":
        total_shipping_cost = Decimal("0")
        discount_reason = f"Free shipping for orders >= ₦{free_shipping_threshold}"
    else:
        total_shipping_cost = subtotal_cost + regional_surcharge
        discount_reason = None

    return {
        "cost": total_shipping_cost,
        "method": shipping_method,
        "method_name": method_config["name"],
        "est_days": method_config["est_days"],
        "total_weight": total_weight,
        "breakdown": {
            "base": base_cost,
            "weight_cost": weight_cost,
            "regional_surcharge": regional_surcharge,
            "subtotal": subtotal_cost,
            "free_shipping_applied": discount_reason,
        },
    }


def get_all_shipping_options(cart_items, destination_state=None, cart_subtotal=Decimal("0")):
    """
    Return all available shipping options with their costs for customer selection.
    Useful for checkout page to allow user to pick a method.
    """
    options = []
    for method_key in SHIPPING_METHODS.keys():
        option = calculate_shipping(cart_items, method_key, destination_state, cart_subtotal)
        options.append(option)
    return options
