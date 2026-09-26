"""Month-6 Slice 6: Million-Dollar composite (six gates).

Does not set swing_opportunity true by itself.
Does not persist a ticket.
"""

from __future__ import annotations

from ftn.os.m6_contracts import MD_GATES, MillionDollarSwing, Month6State, SwingOpportunity
from ftn.os.m6_risk import derive_month6_risk


def _md_block(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    m6 = raw.get("month6") or raw.get("ict_swing") or {}
    return ev.get("million_dollar") or ev.get("md_gates") or m6.get("million_dollar_swing") or {}


def _present(raw: dict, base) -> dict:
    b = _md_block(raw)
    ev = base.supporting_evidence
    gates = {
        "seasonal_tendency": bool(ev.seasonal_tendency or b.get("seasonal_tendency")),
        "major_market_analysis": bool(b.get("major_market_analysis")),
        "intermarket_analysis": bool(ev.intermarket or b.get("intermarket_analysis")),
        "top_down_analysis": bool(
            b.get("top_down_analysis")
            or (raw.get("evidence") or {}).get("top_down_analysis")
            or raw.get("ipda_days")
        ),
        "setup": bool(
            b.get("setup")
            or (
                base.swing_family in {"bull", "bear"}
                and base.risk_frame.stop_reference
                and base.risk_frame.target_reference
            )
        ),
        "management": bool(b.get("management")),
    }
    return gates


def assemble_md(raw: dict, base) -> MillionDollarSwing:
    if base.swing_family == "none":
        return MillionDollarSwing(state="none", missing=(), origin="ict_source")
    gates = _present(raw, base)
    missing = tuple(g for g in MD_GATES if not gates[g])
    if not missing:
        return MillionDollarSwing(state="assembled", missing=(), origin="ict_source")
    return MillionDollarSwing(state="incomplete", missing=missing, origin="ict_source")


def derive_month6_md(raw: dict) -> Month6State:
    base = derive_month6_risk(raw)
    md = assemble_md(raw, base)
    return Month6State(
        market_selection=base.market_selection,
        htf_draw=base.htf_draw,
        swing_family=base.swing_family,
        sequential_pattern=base.sequential_pattern,
        supporting_evidence=base.supporting_evidence,
        risk_frame=base.risk_frame,
        million_dollar_swing=md,
        swing_opportunity=SwingOpportunity(flag=False, reason="slice6_md_only"),
    )
