"""Month-5 Slice 7: setup progression + entry technique + position management.

Annotations only. Does not set position_opportunity.
"""

from __future__ import annotations

from ftn.os.m5_contracts import Month5State, PositionOpportunity
from ftn.os.m5_pd import derive_month5_pd


def _ann(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    m5 = raw.get("month5") or raw.get("ict_position") or {}
    return ev.get("setup") or m5 or ev


def derive_month5_setup(raw: dict) -> Month5State:
    base = derive_month5_pd(raw)
    a = _ann(raw)
    prog = a.get("setup_progression") or raw.get("setup_progression") or "none"
    if prog not in ("watching", "none"):
        prog = "none"
    tech = a.get("entry_technique") or raw.get("entry_technique") or "none"
    if tech not in ("stop", "limit"):
        tech = "none"
    mgmt = a.get("position_management") or raw.get("position_management") or "none"
    if mgmt not in ("annotated", "none"):
        mgmt = "none"
    return Month5State(
        quarterly_shift=base.quarterly_shift,
        ipda_window=base.ipda_window,
        open_float=base.open_float,
        open_float_pools=base.open_float_pools,
        institutional_swing=base.institutional_swing,
        confirming=base.confirming,
        htf_pd=base.htf_pd,
        setup_progression=prog,
        entry_technique=tech,
        position_management=mgmt,
        position_opportunity=PositionOpportunity(flag=False, reason="slice7_setup_only"),
    )
