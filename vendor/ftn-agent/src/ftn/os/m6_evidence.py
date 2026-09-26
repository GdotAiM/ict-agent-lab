"""Month-6 Slice 3: required vs confirming evidence flags.

Does not mint million_dollar_swing or swing_opportunity.
Does not name swing_family / sequential_pattern.
"""

from __future__ import annotations

from ftn.os.m6_contracts import (
    Month6State,
    SequentialPattern,
    SupportingEvidence,
    SwingOpportunity,
)
from ftn.os.m6_env import derive_month6_env


def _block(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    m6 = raw.get("month6") or raw.get("ict_swing") or {}
    return ev.get("supporting_evidence") or m6.get("supporting_evidence") or ev


def read_supporting(raw: dict) -> SupportingEvidence:
    b = _block(raw)
    if not isinstance(b, dict):
        b = {}
    origin = raw.get("origin_pd_array")
    inst = raw.get("pair_institutional") or {}
    sp = inst.get("sponsorship") or {}
    htf = bool(b.get("htf_trend"))
    if not htf and (sp.get("monthly") in {"bullish", "bearish"} or sp.get("weekly") in {"bullish", "bearish"}):
        htf = True
    iof = bool(b.get("institutional_order_flow"))
    if not iof and inst.get("state") in {"bullish", "bearish"}:
        iof = True
    pd = bool(b.get("pd_arrays"))
    if not pd and origin:
        pd = True
    return SupportingEvidence(
        htf_trend=htf,
        institutional_order_flow=iof,
        pd_arrays=pd,
        seasonal_tendency=bool(b.get("seasonal_tendency")),
        interest_rates=bool(b.get("interest_rates")),
        cot=bool(b.get("cot")),
        intermarket=bool(b.get("intermarket")),
    )


def derive_month6_evidence(raw: dict) -> Month6State:
    base = derive_month6_env(raw)
    return Month6State(
        market_selection=base.market_selection,
        htf_draw=base.htf_draw,
        swing_family="none",
        sequential_pattern=SequentialPattern(),
        supporting_evidence=read_supporting(raw),
        million_dollar_swing=base.million_dollar_swing,
        swing_opportunity=SwingOpportunity(flag=False, reason="slice3_flags_only"),
    )
