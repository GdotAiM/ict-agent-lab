"""Month-2 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
Guide = Literal["10_percent", "none"]
Psych = Literal["no_fear_of_losing", "none"]
Trap = Literal["false_flag", "false_breakout", "none"]

PRES = set(Pres.__args__)
GUIDES = set(Guide.__args__)
PSYCHS = set(Psych.__args__)
TRAPS = set(Trap.__args__)


@dataclass(frozen=True)
class LowRiskFrame:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month2State:
    small_account_posture: Pres = "none"
    identified_low_risk_frame: Pres = "none"
    identified_high_reward_context: Pres = "none"
    monthly_return_guidance: Guide = "none"
    psychology_note: Psych = "none"
    loss_mitigation_note: Pres = "none"
    trap_pattern: Trap = "none"
    low_risk_frame: LowRiskFrame = field(default_factory=LowRiskFrame)


def _pres(v) -> Pres:
    return v if v in PRES else "none"


def parse_month2(raw: dict) -> Month2State | None:
    block = raw.get("month2") or raw.get("ict_risk")
    if not block:
        return None
    guide = block.get("monthly_return_guidance") or "none"
    if guide not in GUIDES:
        guide = "none"
    psych = block.get("psychology_note") or "none"
    if psych not in PSYCHS:
        psych = "none"
    trap = block.get("trap_pattern") or "none"
    if trap not in TRAPS:
        trap = "none"
    fr = block.get("low_risk_frame") or {}
    if isinstance(fr, bool):
        fr = {"flag": fr}
    return Month2State(
        small_account_posture=_pres(block.get("small_account_posture")),
        identified_low_risk_frame=_pres(block.get("identified_low_risk_frame")),
        identified_high_reward_context=_pres(block.get("identified_high_reward_context")),
        monthly_return_guidance=guide,
        psychology_note=psych,
        loss_mitigation_note=_pres(block.get("loss_mitigation_note")),
        trap_pattern=trap,
        low_risk_frame=LowRiskFrame(
            flag=bool(fr.get("flag", False)),
            reason=fr.get("reason") or "provided_state",
        ),
    )
