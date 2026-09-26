
"""LTF MSS / displacement after a named raid. Execution confirm only."""

from __future__ import annotations


def detect_mss(bars: list[dict], raid: dict, lookback: int = 4) -> dict:
    if not bars or not raid.get("taken") or not raid.get("level"):
        return {"mss": False, "displacement": False, "source": "detector"}
    level = raid["level"]
    raid_px = float(raid["price"])
    idx = None
    for i, b in enumerate(bars):
        if level in {"pdl", "week_so_far_low", "itl"} and float(b["l"]) <= raid_px:
            idx = i
            break
        if level in {"pdh", "week_so_far_high", "ith"} and float(b["h"]) >= raid_px:
            idx = i
            break
    if idx is None:
        return {"mss": False, "displacement": False, "source": "detector", "reason": "raid_bar_not_found"}

    prior = bars[max(0, idx - lookback):idx]
    after = bars[idx + 1:]
    ranges = [float(b["h"]) - float(b["l"]) for b in bars]
    med = sorted(ranges)[len(ranges) // 2] if ranges else 0.0

    displacement = False
    mss = False
    if level in {"pdl", "week_so_far_low", "itl"}:
        swing = max((float(b["h"]) for b in prior), default=None)
        for b in after:
            rng = float(b["h"]) - float(b["l"])
            if med and rng >= 1.4 * med:
                displacement = True
            if swing is not None and float(b["c"]) > swing:
                mss = True
    else:
        swing = min((float(b["l"]) for b in prior), default=None)
        for b in after:
            rng = float(b["h"]) - float(b["l"])
            if med and rng >= 1.4 * med:
                displacement = True
            if swing is not None and float(b["c"]) < swing:
                mss = True

    return {
        "mss": mss,
        "displacement": displacement,
        "source": "detector",
        "raid_bar_index": idx,
        "swing": swing if prior else None,
    }
