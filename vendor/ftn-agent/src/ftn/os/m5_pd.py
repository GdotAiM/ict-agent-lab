"""Month-5 Slice 6: HTF PD identity.

Stores nearest premium/discount ids. Does not encode scan order.
Does not set position_opportunity.
"""

from __future__ import annotations

from ftn.os.m5_contracts import HtfPd, Month5State, PositionOpportunity
from ftn.os.m5_confirm import derive_month5_confirm


def read_htf_pd(raw: dict) -> HtfPd:
    ev = raw.get("evidence") or {}
    m5 = raw.get("month5") or raw.get("ict_position") or {}
    pd = ev.get("htf_pd") or m5.get("htf_pd") or raw.get("htf_pd") or {}
    tf = pd.get("dealing_range_tf") or "none"
    if tf not in ("monthly", "weekly", "daily", "none"):
        tf = "none"
    return HtfPd(
        dealing_range_tf=tf,
        equilibrium=pd.get("equilibrium"),
        nearest_premium_id=pd.get("nearest_premium_id"),
        nearest_discount_id=pd.get("nearest_discount_id") or raw.get("origin_pd_array"),
        origin="ict_source",
    )


def derive_month5_pd(raw: dict) -> Month5State:
    base = derive_month5_confirm(raw)
    return Month5State(
        quarterly_shift=base.quarterly_shift,
        ipda_window=base.ipda_window,
        open_float=base.open_float,
        open_float_pools=base.open_float_pools,
        institutional_swing=base.institutional_swing,
        confirming=base.confirming,
        htf_pd=read_htf_pd(raw),
        setup_progression=base.setup_progression,
        entry_technique=base.entry_technique,
        position_management=base.position_management,
        position_opportunity=PositionOpportunity(flag=False, reason="slice6_pd_only"),
    )
