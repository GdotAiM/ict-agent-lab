
"""Named-extreme raid from bars vs levels already on context."""

from __future__ import annotations

NAMED_KEYS = ("pdh", "pdl", "week_so_far_high", "week_so_far_low", "ith", "itl")


def detect_raid(bars: list[dict], named: dict, buffer: float = 0.0) -> dict:
    if not bars or not named:
        return {"level": None, "price": None, "taken": False, "source": "detector"}
    hh = max(float(b["h"]) for b in bars)
    ll = min(float(b["l"]) for b in bars)
    hits = []
    for key in NAMED_KEYS:
        px = named.get(key)
        if px is None:
            continue
        px = float(px)
        if key.endswith("high") or key == "pdh" or key == "ith":
            if hh >= px - buffer:
                hits.append((key, px, hh - px))
        else:
            if ll <= px + buffer:
                hits.append((key, px, px - ll))
    if not hits:
        return {"level": None, "price": None, "taken": False, "source": "detector"}
    # deepest pierce first
    hits.sort(key=lambda x: x[2], reverse=True)
    level, price, _ = hits[0]
    return {"level": level, "price": price, "taken": True, "source": "detector", "also": [h[0] for h in hits[1:]]}
