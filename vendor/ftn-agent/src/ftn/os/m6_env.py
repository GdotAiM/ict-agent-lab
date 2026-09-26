"""Month-6 Slice 2: market suitability + HTF draw from labeled sponsorship.

Does not name swing_family or sequential_pattern.
Does not assemble Million-Dollar gates.
"""

from __future__ import annotations

from ftn.os.m6_contracts import (
    MarketSelection,
    Month6State,
    SequentialPattern,
    SwingOpportunity,
)


def _sponsorship(raw: dict) -> dict:
    inst = raw.get("pair_institutional") or {}
    return inst.get("sponsorship") or {}


def labeled_suitability(raw: dict) -> MarketSelection:
    m6 = raw.get("month6") or raw.get("ict_swing") or {}
    sel = m6.get("market_selection") or raw.get("market_selection") or {}
    if isinstance(sel, str):
        state = sel
    else:
        state = sel.get("state")
    if state in {"suitable", "unsuitable", "unclear"}:
        return MarketSelection(state=state, origin="ict_source")
    # labeled HTF sponsorship: monthly or weekly present → suitable for research
    sp = _sponsorship(raw)
    monthly = sp.get("monthly")
    weekly = sp.get("weekly")
    if monthly in {"bullish", "bearish"} or weekly in {"bullish", "bearish"}:
        return MarketSelection(state="suitable", origin="ict_source")
    if raw.get("origin_pd_array"):
        return MarketSelection(state="suitable", origin="hermes_interpretation")
    return MarketSelection(state="unclear", origin="ict_source")


def htf_draw(raw: dict) -> str:
    """Monthly sponsorship first, else weekly. Not a sequential family."""
    sp = _sponsorship(raw)
    for key in ("monthly", "weekly"):
        v = sp.get(key)
        if v in {"bullish", "bearish"}:
            return v
    inst = raw.get("pair_institutional") or {}
    st = inst.get("state")
    if st in {"bullish", "bearish"}:
        return st
    return "unclear"


def derive_month6_env(raw: dict) -> Month6State:
    return Month6State(
        market_selection=labeled_suitability(raw),
        htf_draw=htf_draw(raw),
        swing_family="none",
        sequential_pattern=SequentialPattern(),
        swing_opportunity=SwingOpportunity(flag=False, reason="slice2_env_only"),
    )
