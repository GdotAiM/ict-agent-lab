"""Month-1 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
Side = Literal["premium", "equilibrium", "discount", "none"]

PRES = set(Pres.__args__)
SIDES = set(Side.__args__)


@dataclass(frozen=True)
class SetupElements:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month1State:
    identified_setup_elements: Pres = "none"
    dealing_range_side: Side = "none"
    conditioning_note: Pres = "none"
    focus_note: Pres = "none"
    fair_valuation_note: Pres = "none"
    liquidity_run_note: Pres = "none"
    impulse_note: Pres = "none"
    protraction_note: Pres = "none"
    setup_elements: SetupElements = field(default_factory=SetupElements)


def _pres(v) -> Pres:
    return v if v in PRES else "none"


def parse_month1(raw: dict) -> Month1State | None:
    block = raw.get("month1") or raw.get("ict_foundation")
    if not block:
        return None
    side = block.get("dealing_range_side") or "none"
    if side not in SIDES:
        side = "none"
    se = block.get("setup_elements") or {}
    if isinstance(se, bool):
        se = {"flag": se}
    return Month1State(
        identified_setup_elements=_pres(block.get("identified_setup_elements")),
        dealing_range_side=side,
        conditioning_note=_pres(block.get("conditioning_note")),
        focus_note=_pres(block.get("focus_note")),
        fair_valuation_note=_pres(block.get("fair_valuation_note")),
        liquidity_run_note=_pres(block.get("liquidity_run_note")),
        impulse_note=_pres(block.get("impulse_note")),
        protraction_note=_pres(block.get("protraction_note")),
        setup_elements=SetupElements(
            flag=bool(se.get("flag", False)),
            reason=se.get("reason") or "provided_state",
        ),
    )
