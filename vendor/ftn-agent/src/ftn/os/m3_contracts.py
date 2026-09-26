"""Month-3 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Dir = Literal["bullish", "bearish", "unclear", "none"]
Tf = Literal["monthly", "weekly", "daily", "h4", "none"]
Trap = Literal["trendline_phantom", "head_shoulders", "none"]
Ant = Literal["present", "none"]

DIRS = set(Dir.__args__)
TFS = set(Tf.__args__)
TRAPS = set(Trap.__args__)
ANTS = set(Ant.__args__)


@dataclass(frozen=True)
class NextSetup:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month3State:
    selected_timeframe: Tf = "none"
    institutional_order_flow: Dir = "none"
    institutional_sponsorship: Dir = "none"
    institutional_structure: Dir = "none"
    macro_to_micro: str = "none"
    trap_pattern: Trap = "none"
    anticipated_setup: Ant = "none"
    next_setup: NextSetup = field(default_factory=NextSetup)


def _dir(v) -> Dir:
    return v if v in DIRS else "none"


def parse_month3(raw: dict) -> Month3State | None:
    block = raw.get("month3") or raw.get("ict_next")
    if not block:
        return None
    tf = block.get("selected_timeframe") or "none"
    if tf not in TFS:
        tf = "none"
    trap = block.get("trap_pattern") or "none"
    if trap not in TRAPS:
        trap = "none"
    ant = block.get("anticipated_setup") or "none"
    if ant not in ANTS:
        ant = "none"
    mm = block.get("macro_to_micro") or "none"
    if mm not in ("present", "none"):
        mm = "none"
    ns = block.get("next_setup") or {}
    if isinstance(ns, bool):
        ns = {"flag": ns}
    return Month3State(
        selected_timeframe=tf,
        institutional_order_flow=_dir(block.get("institutional_order_flow")),
        institutional_sponsorship=_dir(block.get("institutional_sponsorship")),
        institutional_structure=_dir(block.get("institutional_structure")),
        macro_to_micro=mm,
        trap_pattern=trap,
        anticipated_setup=ant,
        next_setup=NextSetup(
            flag=bool(ns.get("flag", False)),
            reason=ns.get("reason") or "provided_state",
        ),
    )
