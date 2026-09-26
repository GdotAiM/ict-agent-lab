"""Month-6 Slice 5: descriptive risk frame.

No sizing. No dollar risk. No opportunity. No MD assembly.
"""

from __future__ import annotations

from ftn.os.m6_contracts import Month6State, RiskFrame, SwingOpportunity
from ftn.os.m6_family import derive_month6_family


def read_risk(raw: dict) -> RiskFrame:
    m6 = raw.get("month6") or raw.get("ict_swing") or {}
    labeled = m6.get("risk_frame") or raw.get("risk_frame") or {}
    stop = labeled.get("stop_reference") or raw.get("origin_pd_array")
    targets = raw.get("opposing_target_arrays") or []
    target = labeled.get("target_reference") or (targets[0] if targets else None)
    frame = labeled.get("reward_frame")
    if not frame and stop and target:
        inst = raw.get("pair_institutional") or {}
        sp = inst.get("sponsorship") or {}
        if sp.get("monthly") == "bullish" or inst.get("state") == "bullish":
            frame = "discount_to_premium"
        elif sp.get("monthly") == "bearish" or inst.get("state") == "bearish":
            frame = "premium_to_discount"
    return RiskFrame(
        stop_reference=stop,
        target_reference=target,
        reward_frame=frame,
        origin="ict_source",
    )


def derive_month6_risk(raw: dict) -> Month6State:
    base = derive_month6_family(raw)
    return Month6State(
        market_selection=base.market_selection,
        htf_draw=base.htf_draw,
        swing_family=base.swing_family,
        sequential_pattern=base.sequential_pattern,
        supporting_evidence=base.supporting_evidence,
        risk_frame=read_risk(raw),
        million_dollar_swing=base.million_dollar_swing,
        swing_opportunity=SwingOpportunity(flag=False, reason="slice5_risk_only"),
    )
