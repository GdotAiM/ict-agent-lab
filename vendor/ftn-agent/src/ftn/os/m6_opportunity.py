"""Month-6 Slice 7: swing_opportunity flag.

MD assembled is optional. No persist. No M9 candidate.
"""

from __future__ import annotations

from ftn.os.m6_contracts import Month6State, SwingOpportunity
from ftn.os.m6_md import derive_month6_md


def classify_opportunity(st: Month6State) -> SwingOpportunity:
    if st.market_selection.state != "suitable":
        return SwingOpportunity(flag=False, reason="market_unsuitable")
    if st.swing_family == "none":
        return SwingOpportunity(flag=False, reason="no_swing_family")
    if not st.risk_frame.stop_reference or not st.risk_frame.target_reference:
        return SwingOpportunity(flag=False, reason="no_risk_frame")
    extra = ""
    if st.million_dollar_swing.state == "assembled":
        extra = "+md_assembled"
    return SwingOpportunity(flag=True, reason="suitable_family_risk" + extra)


def derive_month6(raw: dict) -> Month6State:
    base = derive_month6_md(raw)
    opp = classify_opportunity(base)
    return Month6State(
        market_selection=base.market_selection,
        htf_draw=base.htf_draw,
        swing_family=base.swing_family,
        sequential_pattern=base.sequential_pattern,
        supporting_evidence=base.supporting_evidence,
        risk_frame=base.risk_frame,
        million_dollar_swing=base.million_dollar_swing,
        swing_opportunity=opp,
    )
