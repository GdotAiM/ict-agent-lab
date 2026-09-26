
"""Williams %R(10) on 15m. ICT-source input, not the sentiment engine."""

from __future__ import annotations


def williams_r(bars: list[dict], period: int = 10) -> dict:
    if not bars or len(bars) < period:
        return {"value": None, "state": "unavailable", "period": period, "timeframe": "m15"}
    window = bars[-period:]
    hh = max(float(b["h"]) for b in window)
    ll = min(float(b["l"]) for b in window)
    close = float(window[-1]["c"])
    width = hh - ll
    if width <= 0:
        return {"value": None, "state": "unavailable", "period": period, "timeframe": "m15"}
    value = (hh - close) / width * -100.0
    if value <= -80:
        state = "bullish"
    elif value >= -20:
        state = "bearish"
    else:
        state = "neutral"
    return {
        "value": round(value, 2),
        "state": state,
        "period": period,
        "timeframe": "m15",
        "hh": hh,
        "ll": ll,
        "close": close,
    }
