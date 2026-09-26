"""Month-2 Slice 2: labeled risk-frame context.

Does not derive low_risk_frame.
Does not write M6 RiskFrame.
Does not inspect raw month3–9.
"""

from __future__ import annotations

from ftn.os.m2_contracts import LowRiskFrame, Month2State, _pres


def _block(raw: dict):
    ev = raw.get("evidence") or {}
    m2 = raw.get("month2") or raw.get("ict_risk") or {}
    return ev, m2


def derive_month2_context(raw: dict) -> Month2State:
    ev, m2 = _block(raw)
    src = ev.get("month2") or ev or m2
    guide = src.get("monthly_return_guidance") or m2.get("monthly_return_guidance") or "none"
    if guide != "10_percent":
        guide = "none"
    psych = src.get("psychology_note") or m2.get("psychology_note") or "none"
    if psych != "no_fear_of_losing":
        psych = "none"
    trap = src.get("trap_pattern") or m2.get("trap_pattern") or "none"
    if trap not in ("false_flag", "false_breakout"):
        trap = "none"
    return Month2State(
        small_account_posture=_pres(src.get("small_account_posture") or m2.get("small_account_posture")),
        identified_low_risk_frame=_pres(src.get("identified_low_risk_frame") or m2.get("identified_low_risk_frame")),
        identified_high_reward_context=_pres(src.get("identified_high_reward_context") or m2.get("identified_high_reward_context")),
        monthly_return_guidance=guide,
        psychology_note=psych,
        loss_mitigation_note=_pres(src.get("loss_mitigation_note") or m2.get("loss_mitigation_note")),
        trap_pattern=trap,
        low_risk_frame=LowRiskFrame(flag=False, reason="slice2_context_only"),
    )
