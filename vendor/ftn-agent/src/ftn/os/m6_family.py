"""Month-6 Slice 4: swing_family + sequential pattern from M/W/D alignment.

Does not set swing_opportunity.
Does not assemble Million-Dollar gates.
"""

from __future__ import annotations

from ftn.os.m6_contracts import (
    Month6State,
    SequentialPattern,
    SwingOpportunity,
)
from ftn.os.m6_evidence import derive_month6_evidence


def _mw_d(raw: dict) -> tuple[str, str, str]:
    inst = raw.get("pair_institutional") or {}
    sp = inst.get("sponsorship") or {}
    return (
        sp.get("monthly") or "unclear",
        sp.get("weekly") or "unclear",
        sp.get("daily") or "unclear",
    )


def classify_sequence(m: str, w: str, d: str) -> tuple[str, str]:
    """Returns (swing_family, sequential_pattern name). unclear != correcting."""
    if m == "bullish":
        if w == "bullish" and d == "bullish":
            return "bull", "mwd_all_bullish"
        if w == "bullish" and d == "bearish":
            return "bull", "mw_bullish_daily_correcting"
        if w == "bearish":
            return "bull", "m_bullish_wd_correcting"
        return "none", "none"
    if m == "bearish":
        if w == "bearish" and d == "bearish":
            return "bear", "mwd_all_bearish"
        if w == "bearish" and d == "bullish":
            return "bear", "mw_bearish_daily_correcting"
        if w == "bullish":
            return "bear", "m_bearish_wd_correcting"
        return "none", "none"
    return "none", "none"


def derive_month6_family(raw: dict) -> Month6State:
    base = derive_month6_evidence(raw)
    fam, seq = classify_sequence(*_mw_d(raw))
    return Month6State(
        market_selection=base.market_selection,
        htf_draw=base.htf_draw,
        swing_family=fam,
        sequential_pattern=SequentialPattern(
            name=seq,
            state="watching" if seq != "none" else "none",
            origin="ict_source",
        ),
        supporting_evidence=base.supporting_evidence,
        million_dollar_swing=base.million_dollar_swing,
        swing_opportunity=SwingOpportunity(flag=False, reason="slice4_family_only"),
    )
