"""Month-5 Slice 8: position_opportunity.

Generic flag. Confirming evidence is not required.
Does not persist. Does not write session_ticket.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m5_contracts import Month5State, PositionOpportunity
from ftn.os.m5_setup import derive_month5_setup


def classify_opportunity(st: Month5State) -> PositionOpportunity:
    qs = st.quarterly_shift.state == "in_progress"
    ipda = st.ipda_window.days in (20, 40, 60)
    if not (qs or ipda):
        return PositionOpportunity(False, "no_quarterly_or_ipda")
    of_ = st.open_float.buy_side == "present" or st.open_float.sell_side == "present"
    pools = bool(st.open_float_pools.pool_ids)
    swing = st.institutional_swing.kind in ("breaker_swing_point", "failure_swing")
    if not (of_ or pools or swing):
        return PositionOpportunity(False, "no_float_pool_or_swing")
    if st.htf_pd.dealing_range_tf not in ("monthly", "weekly", "daily"):
        return PositionOpportunity(False, "no_htf_pd_range")
    return PositionOpportunity(True, "quarterly_or_ipda_plus_float_and_pd")


def derive_month5(raw: dict) -> Month5State:
    base = derive_month5_setup(raw)
    return replace(base, position_opportunity=classify_opportunity(base))
