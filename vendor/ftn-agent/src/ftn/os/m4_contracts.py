"""Month-4 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ArrayKind = Literal[
    "orderblock",
    "mitigation_block",
    "breaker_block",
    "rejection_block",
    "reclaimed_orderblock",
    "propulsion_block",
    "vacuum_block",
    "liquidity_void",
    "liquidity_pool",
    "fvg",
    "none",
]
Polarity = Literal["bullish", "bearish", "none"]
PatternNote = Literal["divergence_phantom", "double_bottom", "double_top", "none"]
Tf = Literal["monthly", "weekly", "daily", "h4", "none"]

KINDS = set(ArrayKind.__args__)
POL = set(Polarity.__args__)
PAT = set(PatternNote.__args__)
TFS = set(Tf.__args__)


@dataclass(frozen=True)
class PdArray:
    id: str = "none"
    kind: ArrayKind = "none"
    polarity: Polarity = "none"
    timeframe: Tf = "none"


@dataclass(frozen=True)
class ArrayOpportunity:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month4State:
    arrays: tuple = ()
    pattern_note: PatternNote = "none"
    interest_rate_effects: bool = False
    array_opportunity: ArrayOpportunity = field(default_factory=ArrayOpportunity)


def _one_array(item) -> PdArray:
    if isinstance(item, str):
        item = {"kind": item}
    kind = item.get("kind") or "none"
    if kind not in KINDS:
        kind = "none"
    pol = item.get("polarity") or "none"
    if pol not in POL:
        pol = "none"
    tf = item.get("timeframe") or "none"
    if tf not in TFS:
        tf = "none"
    return PdArray(
        id=item.get("id") or "none",
        kind=kind,
        polarity=pol,
        timeframe=tf,
    )


def parse_month4(raw: dict) -> Month4State | None:
    block = raw.get("month4") or raw.get("ict_arrays")
    if not block:
        return None
    items = block.get("arrays") or ()
    if isinstance(items, dict):
        items = [items]
    note = block.get("pattern_note") or "none"
    if note not in PAT:
        note = "none"
    opp = block.get("array_opportunity") or {}
    if isinstance(opp, bool):
        opp = {"flag": opp}
    return Month4State(
        arrays=tuple(_one_array(x) for x in items),
        pattern_note=note,
        interest_rate_effects=bool(block.get("interest_rate_effects")),
        array_opportunity=ArrayOpportunity(
            flag=bool(opp.get("flag", False)),
            reason=opp.get("reason") or "provided_state",
        ),
    )
