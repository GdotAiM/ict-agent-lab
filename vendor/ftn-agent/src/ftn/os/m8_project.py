
"""Month-8 Slice 5: daily extreme projection from CBDR standard deviations.

Bearish IOF → project the day's HIGH above CBDR.
Bullish IOF → project the day's LOW below CBDR.
Selected level is context, not an entry.
"""

from __future__ import annotations

from ftn.os.m8_contracts import CbdrState, DailyExtremeProjection


def _height(cbdr: CbdrState) -> float | None:
    if cbdr.body_high is not None and cbdr.body_low is not None:
        return float(cbdr.body_high) - float(cbdr.body_low)
    if cbdr.height_pips is not None:
        return float(cbdr.height_pips) / 10000.0
    return None


def project_daily_extreme(cbdr: CbdrState, iof: str) -> DailyExtremeProjection:
    h = _height(cbdr)
    if h is None or h <= 0:
        return DailyExtremeProjection()
    if iof == "bearish":
        base = cbdr.body_high if cbdr.body_high is not None else None
        if base is None and cbdr.wick_high is not None:
            base = cbdr.wick_high
        if base is None:
            return DailyExtremeProjection()
        levels = tuple({"sd": n, "price": round(base + n * h, 5)} for n in (1, 2, 3))
        return DailyExtremeProjection(
            draw="high",
            sd_levels=levels,
            source_range="cbdr_bodies",
            selected_level=levels[0]["price"],
            basis=("bearish_iof", "sell_day_projects_high"),
            origin="ict_source",
        )
    if iof == "bullish":
        base = cbdr.body_low if cbdr.body_low is not None else None
        if base is None and cbdr.wick_low is not None:
            base = cbdr.wick_low
        if base is None:
            return DailyExtremeProjection()
        levels = tuple({"sd": n, "price": round(base - n * h, 5)} for n in (1, 2, 3))
        return DailyExtremeProjection(
            draw="low",
            sd_levels=levels,
            source_range="cbdr_bodies",
            selected_level=levels[0]["price"],
            basis=("bullish_iof", "buy_day_projects_low"),
            origin="ict_source",
        )
    return DailyExtremeProjection()
