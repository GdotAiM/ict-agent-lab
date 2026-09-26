
"""1H/15m consolidation box from compression. Narrow detector."""

from __future__ import annotations


def detect_box(bars: list[dict], prev_range: dict | None = None, window: int = 8) -> dict | None:
    if not bars or len(bars) < window:
        return None
    sl = bars[-window:]
    hh = max(float(b["h"]) for b in sl)
    ll = min(float(b["l"]) for b in sl)
    width = hh - ll
    if width <= 0:
        return None
    pd = None
    if prev_range and prev_range.get("high") is not None:
        pd = float(prev_range["high"]) - float(prev_range["low"])
    med = sorted(float(b["h"]) - float(b["l"]) for b in sl)[window // 2]
    tight_vs_day = pd is not None and width <= 0.45 * pd
    tight_vs_bars = med > 0 and width <= 2.2 * med * 2  # weak fallback; prefer day
    if not (tight_vs_day or (pd is None and width <= 8 * med)):
        return None
    return {"high": hh, "low": ll, "eq": (hh + ll) / 2.0, "source": "detector", "window": window}
