
"""Origin / target PD arrays from a finite HTF list. 20-day list, 40 if spent."""

from __future__ import annotations


def _mid(arr: dict) -> float:
    return (float(arr["low"]) + float(arr["high"])) / 2.0


def select_origin_targets(arrays: list, last: float, iof: str, max_n: int = 20) -> dict:
    arrays = list(arrays or [])[:max_n]
    if last is None or iof not in {"bullish", "bearish"}:
        return {"origin": None, "targets": [], "source": "detector"}
    below = [a for a in arrays if float(a.get("high", 0)) <= last]
    above = [a for a in arrays if float(a.get("low", 0)) >= last]
    if iof == "bullish":
        origin = max(below, key=_mid, default=None)
        targets = sorted(above, key=_mid)
    else:
        origin = min(above, key=_mid, default=None)
        targets = sorted(below, key=_mid, reverse=True)
    # spent: nothing below/above in-direction → extend caller list to 40
    return {
        "origin": origin.get("id") if origin else None,
        "targets": [a.get("id") for a in targets if a.get("id")],
        "source": "detector",
        "lookback": len(arrays),
    }
