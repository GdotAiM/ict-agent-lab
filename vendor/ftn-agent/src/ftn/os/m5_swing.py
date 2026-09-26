"""Month-5 Slice 4: institutional swing point.

breaker_swing_point | failure_swing | none
turtle_soup / breaker_block are entry annotations only.
Does not set position_opportunity.
"""

from __future__ import annotations

from ftn.os.m5_contracts import InstitutionalSwing, Month5State, PositionOpportunity
from ftn.os.m5_float import derive_month5_float


def read_swing(raw: dict) -> InstitutionalSwing:
    ev = raw.get("evidence") or {}
    m5 = raw.get("month5") or raw.get("ict_position") or {}
    sw = ev.get("institutional_swing") or m5.get("institutional_swing") or raw.get("institutional_swing") or {}
    if isinstance(sw, str):
        sw = {"kind": sw}
    kind = sw.get("kind") or "none"
    if kind not in ("breaker_swing_point", "failure_swing"):
        kind = "none"
    entry = sw.get("entry_annotation") or "none"
    if entry not in ("turtle_soup", "breaker_block"):
        entry = "none"
    return InstitutionalSwing(kind=kind, entry_annotation=entry, origin="ict_source")


def derive_month5_swing(raw: dict) -> Month5State:
    base = derive_month5_float(raw)
    return Month5State(
        quarterly_shift=base.quarterly_shift,
        ipda_window=base.ipda_window,
        open_float=base.open_float,
        open_float_pools=base.open_float_pools,
        institutional_swing=read_swing(raw),
        confirming=base.confirming,
        htf_pd=base.htf_pd,
        position_opportunity=PositionOpportunity(flag=False, reason="slice4_swing_only"),
    )
