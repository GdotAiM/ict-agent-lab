"""Month-5 Slice 3: Open Float + OF liquidity pools.

Two fields. Does not name institutional swing.
Does not set position_opportunity.
"""

from __future__ import annotations

from ftn.os.m5_contracts import (
    Month5State,
    OpenFloat,
    OpenFloatPools,
    PositionOpportunity,
)
from ftn.os.m5_env import derive_month5_env


def _block(raw: dict) -> tuple:
    ev = raw.get("evidence") or {}
    m5 = raw.get("month5") or raw.get("ict_position") or {}
    return ev, m5


def read_open_float(raw: dict) -> OpenFloat:
    ev, m5 = _block(raw)
    of_ = ev.get("open_float") or m5.get("open_float") or raw.get("open_float") or {}
    buy = of_.get("buy_side")
    sell = of_.get("sell_side")
    if buy not in ("present", "absent", "unclear"):
        buy = "unclear"
    if sell not in ("present", "absent", "unclear"):
        sell = "unclear"
    return OpenFloat(buy_side=buy, sell_side=sell, origin="ict_source")


def read_pools(raw: dict) -> OpenFloatPools:
    ev, m5 = _block(raw)
    pools = ev.get("open_float_pools") or m5.get("open_float_pools") or raw.get("open_float_pools") or {}
    if isinstance(pools, list):
        ids = pools
    else:
        ids = pools.get("pool_ids") or ()
    return OpenFloatPools(pool_ids=tuple(ids), origin="ict_source")


def derive_month5_float(raw: dict) -> Month5State:
    base = derive_month5_env(raw)
    return Month5State(
        quarterly_shift=base.quarterly_shift,
        ipda_window=base.ipda_window,
        open_float=read_open_float(raw),
        open_float_pools=read_pools(raw),
        position_opportunity=PositionOpportunity(flag=False, reason="slice3_float_only"),
    )
