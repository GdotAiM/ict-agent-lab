"""Memory hygiene helpers.

Long-term memory is for *identity and preferences* only. Numbers that the
agent calculated or looked up (prices, totals, discounts, refund amounts,
order status) go stale, so they are redacted before a turn is saved.
"""
from __future__ import annotations

import re

# Header prepended to retrieved memories so the model knows how to treat them.
CONTEXT_HEADER = (
    "Customer Context (from long-term memory -- identity and preferences ONLY; "
    "may be stale; never use it for prices, totals, discounts, refund amounts "
    "or order status):"
)

REDACTED = "[amount omitted]"

# $150, $1,234.56, $ 95, USD 12.50, 12.50 USD
_MONEY = re.compile(
    r"(?:\$\s?\d[\d,]*(?:\.\d+)?)|(?:\bUSD\s?\d[\d,]*(?:\.\d+)?)|(?:\b\d[\d,]*(?:\.\d+)?\s?USD\b)",
    re.IGNORECASE,
)


def redact_amounts(text: str) -> str:
    """Replace money amounts in ``text`` with a placeholder."""
    if not text:
        return text
    return _MONEY.sub(REDACTED, text)
