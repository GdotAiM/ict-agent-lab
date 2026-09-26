
"""DXY relationship to the focus pair. Context, not an automatic idle."""

from __future__ import annotations

DOLLAR_BULL = ("USDJPY", "USDCHF", "USDCAD", "USDTRY")
DOLLAR_BEAR = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "XAUUSD", "EURGBP")


def _state(block: dict | None) -> str:
    if not block:
        return "unclear"
    dt = (block.get("daytrade_iof") or {})
    st = block.get("state")
    if st in {"bullish", "bearish"}:
        return st
    return dt.get("daily") or "unclear"


def dxy_relationship(pair: str, pair_iof: str, dxy_block: dict | None) -> str:
    if not dxy_block:
        return "unavailable"
    dxy = _state(dxy_block)
    if dxy == "unclear" or pair_iof not in {"bullish", "bearish"}:
        return "neutral"
    p = (pair or "").upper()
    if p in DOLLAR_BEAR or p.startswith("EUR") or p.startswith("GBP") or p.startswith("XAU"):
        return "supportive" if dxy != pair_iof else "contradictory"
    if p in DOLLAR_BULL or p.startswith("USD"):
        return "supportive" if dxy == pair_iof else "contradictory"
    return "neutral"
