"""Month-5 Slice 5: confirming evidence.

10Y notes / yields / differentials / intermarket / seasonal.
Does not set position_opportunity.
"""

from __future__ import annotations

from ftn.os.m5_contracts import ConfirmingEvidence, Month5State, PositionOpportunity
from ftn.os.m5_swing import derive_month5_swing


def read_confirming(raw: dict) -> ConfirmingEvidence:
    ev = raw.get("evidence") or {}
    m5 = raw.get("month5") or raw.get("ict_position") or {}
    c = ev.get("confirming") or m5.get("confirming") or raw.get("confirming") or {}
    season = c.get("seasonal_tendency") or "none"
    if season not in ("bullish", "bearish", "ideal", "none"):
        season = "none"
    return ConfirmingEvidence(
        ten_year_notes=bool(c.get("ten_year_notes")),
        ten_year_yields=bool(c.get("ten_year_yields")),
        interest_rate_differentials=bool(c.get("interest_rate_differentials")),
        intermarket=bool(c.get("intermarket")),
        seasonal_tendency=season,
    )


def derive_month5_confirm(raw: dict) -> Month5State:
    base = derive_month5_swing(raw)
    return Month5State(
        quarterly_shift=base.quarterly_shift,
        ipda_window=base.ipda_window,
        open_float=base.open_float,
        open_float_pools=base.open_float_pools,
        institutional_swing=base.institutional_swing,
        confirming=read_confirming(raw),
        htf_pd=base.htf_pd,
        position_opportunity=PositionOpportunity(flag=False, reason="slice5_confirm_only"),
    )
