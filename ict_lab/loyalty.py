"""Reference (pure Python) loyalty maths -- same rules as the Code Interpreter snippet.

Used as the fallback when the Code Interpreter is unavailable and in unit tests.
"""
from __future__ import annotations

EARN_RATES = {"standard": 1, "device": 2, "fresh": 5}
TIER_RATES = {"Silver": 0.00, "Gold": 0.10, "Platinum": 0.15}
POINTS_PER_DOLLAR = 100
REDEEM_BLOCK = 500


def normalize_tier(tier: str) -> str:
    t = (tier or "").strip().capitalize()
    if t not in TIER_RATES:
        raise ValueError(f"Unknown tier '{tier}'. Use Silver, Gold or Platinum.")
    return t


def normalize_category(category: str) -> str:
    c = (category or "standard").strip().lower()
    if c not in EARN_RATES:
        raise ValueError(f"Unknown product_category '{category}'. Use standard, device or fresh.")
    return c


def compute_loyalty_discount(loyalty_points: int, tier: str, order_total: float,
                             product_category: str = "standard") -> dict:
    if order_total <= 0:
        raise ValueError("order_total must be greater than 0")
    if loyalty_points < 0:
        raise ValueError("loyalty_points cannot be negative")
    tier = normalize_tier(tier)
    product_category = normalize_category(product_category)

    max_redeemable = int(order_total * 0.5 * POINTS_PER_DOLLAR) // REDEEM_BLOCK * REDEEM_BLOCK
    points_redeemed = min((loyalty_points // REDEEM_BLOCK) * REDEEM_BLOCK, max_redeemable)
    points_value = points_redeemed / POINTS_PER_DOLLAR
    subtotal = order_total - points_value
    rate = TIER_RATES[tier]
    tier_discount = subtotal * rate
    final_total = subtotal - tier_discount
    points_earned = int(order_total * EARN_RATES[product_category])
    return {
        "points_redeemed": points_redeemed,
        "points_value": round(points_value, 2),
        "tier": tier,
        "tier_discount_pct": round(rate * 100, 2),
        "tier_discount": round(tier_discount, 2),
        "original_total": order_total,
        "final_total": round(final_total, 2),
        "total_savings": round(order_total - final_total, 2),
        "points_earned": points_earned,
        "remaining_points": loyalty_points - points_redeemed + points_earned,
    }
