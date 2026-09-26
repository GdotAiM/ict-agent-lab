"""Month-12 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
PRES = set(Pres.__args__)


@dataclass(frozen=True)
class TopDown:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month12State:
    long_term_note: Pres = "none"
    intermediate_term_note: Pres = "none"
    short_term_note: Pres = "none"
    intraday_note: Pres = "none"
    identified_top_down: Pres = "none"
    top_down: TopDown = field(default_factory=TopDown)


def _one(v, allowed):
    return v if v in allowed else "none"


def parse_month12(raw: dict) -> Month12State | None:
    block = raw.get("month12") or raw.get("ict_top_down")
    if not block:
        return None
    td = block.get("top_down") or {}
    if isinstance(td, bool):
        td = {"flag": td}
    return Month12State(
        long_term_note=_one(block.get("long_term_note"), PRES),
        intermediate_term_note=_one(block.get("intermediate_term_note"), PRES),
        short_term_note=_one(block.get("short_term_note"), PRES),
        intraday_note=_one(block.get("intraday_note"), PRES),
        identified_top_down=_one(block.get("identified_top_down"), PRES),
        top_down=TopDown(
            flag=bool(td.get("flag", False)),
            reason=td.get("reason") or "provided_state",
        ),
    )
