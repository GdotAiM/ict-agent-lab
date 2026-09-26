"""Month-11 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
Family = Literal["commodity", "fx", "stock", "bond", "none"]

PRES = set(Pres.__args__)
FAMILIES = set(Family.__args__)


@dataclass(frozen=True)
class MegaTrade:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month11State:
    mega_trade_family: Family = "none"
    identified_mega_trade: Pres = "none"
    quarterly_shift_overlap: Pres = "none"
    seasonal_overlap: Pres = "none"
    relative_strength_note: Pres = "none"
    mega_trade: MegaTrade = field(default_factory=MegaTrade)


def _one(v, allowed):
    return v if v in allowed else "none"


def parse_month11(raw: dict) -> Month11State | None:
    block = raw.get("month11") or raw.get("ict_mega")
    if not block:
        return None
    mt = block.get("mega_trade") or {}
    if isinstance(mt, bool):
        mt = {"flag": mt}
    return Month11State(
        mega_trade_family=_one(block.get("mega_trade_family"), FAMILIES),
        identified_mega_trade=_one(block.get("identified_mega_trade"), PRES),
        quarterly_shift_overlap=_one(block.get("quarterly_shift_overlap"), PRES),
        seasonal_overlap=_one(block.get("seasonal_overlap"), PRES),
        relative_strength_note=_one(block.get("relative_strength_note"), PRES),
        mega_trade=MegaTrade(
            flag=bool(mt.get("flag", False)),
            reason=mt.get("reason") or "provided_state",
        ),
    )
