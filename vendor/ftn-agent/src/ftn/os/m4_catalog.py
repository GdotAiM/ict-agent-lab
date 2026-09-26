"""Month-4 Slice 2: labeled PD-array catalog.

Does not invent kinds.
Does not derive array_opportunity.
Does not inspect raw month5/6/7.
"""

from __future__ import annotations

from ftn.os.m4_contracts import (
    ArrayOpportunity,
    Month4State,
    PatternNote,
    _one_array,
)


def _block(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    m4 = raw.get("month4") or raw.get("ict_arrays") or {}
    return ev, m4


def read_arrays(raw: dict) -> tuple:
    ev, m4 = _block(raw)
    items = ev.get("arrays") or m4.get("arrays") or raw.get("arrays") or ()
    if isinstance(items, dict):
        items = [items]
    return tuple(_one_array(x) for x in items)


def read_note(raw: dict) -> PatternNote:
    ev, m4 = _block(raw)
    note = ev.get("pattern_note") or m4.get("pattern_note") or raw.get("pattern_note") or "none"
    if note not in ("divergence_phantom", "double_bottom", "double_top"):
        return "none"
    return note


def read_rates(raw: dict) -> bool:
    ev, m4 = _block(raw)
    c = ev.get("confirming") or m4 or ev
    return bool(c.get("interest_rate_effects") or m4.get("interest_rate_effects"))


def derive_month4_catalog(raw: dict) -> Month4State:
    return Month4State(
        arrays=read_arrays(raw),
        pattern_note=read_note(raw),
        interest_rate_effects=read_rates(raw),
        array_opportunity=ArrayOpportunity(flag=False, reason="slice2_catalog_only"),
    )
