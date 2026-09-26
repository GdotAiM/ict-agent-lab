"""Month-3 Slice 2: labeled institutional context.

Does not derive next_setup.
Does not write pair_institutional.
Does not inspect raw month4–9.
"""

from __future__ import annotations

from ftn.os.m3_contracts import Month3State, NextSetup, _dir


def _block(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    m3 = raw.get("month3") or raw.get("ict_next") or {}
    return ev, m3


def derive_month3_context(raw: dict) -> Month3State:
    ev, m3 = _block(raw)
    src = ev.get("month3") or ev or m3
    tf = src.get("selected_timeframe") or m3.get("selected_timeframe") or "none"
    if tf not in ("monthly", "weekly", "daily", "h4"):
        tf = "none"
    ant = src.get("anticipated_setup") or m3.get("anticipated_setup") or "none"
    if ant != "present":
        ant = "none"
    trap = src.get("trap_pattern") or m3.get("trap_pattern") or "none"
    if trap not in ("trendline_phantom", "head_shoulders"):
        trap = "none"
    mm = src.get("macro_to_micro") or m3.get("macro_to_micro") or "none"
    if mm != "present":
        mm = "none"
    return Month3State(
        selected_timeframe=tf,
        institutional_order_flow=_dir(src.get("institutional_order_flow") or m3.get("institutional_order_flow")),
        institutional_sponsorship=_dir(src.get("institutional_sponsorship") or m3.get("institutional_sponsorship")),
        institutional_structure=_dir(src.get("institutional_structure") or m3.get("institutional_structure")),
        macro_to_micro=mm,
        trap_pattern=trap,
        anticipated_setup=ant,
        next_setup=NextSetup(flag=False, reason="slice2_context_only"),
    )
