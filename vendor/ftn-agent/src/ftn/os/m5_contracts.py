"""Month-5 Slice 1 contracts. No detectors.

Glossary: Slice 0 signed. PD hierarchy stored as identity, not scan order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

QsState = Literal["in_progress", "none", "unclear"]
Lookback = Literal[3, 4, "none"]
Side = Literal["present", "absent", "unclear"]
SwingKind = Literal["breaker_swing_point", "failure_swing", "none"]
EntryAnn = Literal["turtle_soup", "breaker_block", "none"]
Season = Literal["bullish", "bearish", "ideal", "none"]
EntryTech = Literal["stop", "limit", "none"]
IpdaDays = Literal[20, 40, 60, "none"]


@dataclass(frozen=True)
class QuarterlyShift:
    state: QsState = "unclear"
    lookback_months: Lookback = "none"
    direction: str = "unclear"
    origin: str = "ict_source"


@dataclass(frozen=True)
class IpdaWindow:
    days: IpdaDays = "none"
    high: Optional[str] = None
    low: Optional[str] = None
    origin: str = "ict_source"


@dataclass(frozen=True)
class OpenFloat:
    buy_side: Side = "unclear"
    sell_side: Side = "unclear"
    origin: str = "ict_source"


@dataclass(frozen=True)
class OpenFloatPools:
    pool_ids: tuple = ()
    origin: str = "ict_source"


@dataclass(frozen=True)
class InstitutionalSwing:
    kind: SwingKind = "none"
    entry_annotation: EntryAnn = "none"
    origin: str = "ict_source"


@dataclass(frozen=True)
class ConfirmingEvidence:
    ten_year_notes: bool = False
    ten_year_yields: bool = False
    interest_rate_differentials: bool = False
    intermarket: bool = False
    seasonal_tendency: Season = "none"


@dataclass(frozen=True)
class HtfPd:
    dealing_range_tf: str = "none"
    equilibrium: Optional[str] = None
    nearest_premium_id: Optional[str] = None
    nearest_discount_id: Optional[str] = None
    origin: str = "ict_source"


@dataclass(frozen=True)
class PositionOpportunity:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month5State:
    quarterly_shift: QuarterlyShift = field(default_factory=QuarterlyShift)
    ipda_window: IpdaWindow = field(default_factory=IpdaWindow)
    open_float: OpenFloat = field(default_factory=OpenFloat)
    open_float_pools: OpenFloatPools = field(default_factory=OpenFloatPools)
    institutional_swing: InstitutionalSwing = field(default_factory=InstitutionalSwing)
    confirming: ConfirmingEvidence = field(default_factory=ConfirmingEvidence)
    htf_pd: HtfPd = field(default_factory=HtfPd)
    setup_progression: str = "none"
    entry_technique: EntryTech = "none"
    position_management: str = "none"
    position_opportunity: PositionOpportunity = field(default_factory=PositionOpportunity)


def parse_month5(raw: dict) -> Month5State | None:
    block = raw.get("month5") or raw.get("ict_position")
    if not block:
        return None
    qs = block.get("quarterly_shift") or {}
    if isinstance(qs, str):
        qs = {"state": qs}
    ip = block.get("ipda_window") or {}
    if isinstance(ip, int):
        ip = {"days": ip}
    of_ = block.get("open_float") or {}
    pools = block.get("open_float_pools") or {}
    if isinstance(pools, list):
        pools = {"pool_ids": pools}
    sw = block.get("institutional_swing") or {}
    if isinstance(sw, str):
        sw = {"kind": sw}
    cf = block.get("confirming") or {}
    pd = block.get("htf_pd") or {}
    opp = block.get("position_opportunity") or {}
    if isinstance(opp, bool):
        opp = {"flag": opp}
    kind = sw.get("kind") or "none"
    if kind not in ("breaker_swing_point", "failure_swing", "none"):
        kind = "none"
    days = ip.get("days", "none")
    if days not in (20, 40, 60, "none"):
        days = "none"
    return Month5State(
        quarterly_shift=QuarterlyShift(
            state=qs.get("state") if qs.get("state") in ("in_progress", "none", "unclear") else "unclear",
            lookback_months=qs.get("lookback_months") if qs.get("lookback_months") in (3, 4, "none") else "none",
            direction=qs.get("direction") or "unclear",
            origin=qs.get("origin") or "ict_source",
        ),
        ipda_window=IpdaWindow(
            days=days,
            high=ip.get("high"),
            low=ip.get("low"),
            origin=ip.get("origin") or "ict_source",
        ),
        open_float=OpenFloat(
            buy_side=of_.get("buy_side") if of_.get("buy_side") in ("present", "absent", "unclear") else "unclear",
            sell_side=of_.get("sell_side") if of_.get("sell_side") in ("present", "absent", "unclear") else "unclear",
        ),
        open_float_pools=OpenFloatPools(pool_ids=tuple(pools.get("pool_ids") or ())),
        institutional_swing=InstitutionalSwing(
            kind=kind,
            entry_annotation=sw.get("entry_annotation") if sw.get("entry_annotation") in ("turtle_soup", "breaker_block", "none") else "none",
        ),
        confirming=ConfirmingEvidence(
            ten_year_notes=bool(cf.get("ten_year_notes")),
            ten_year_yields=bool(cf.get("ten_year_yields")),
            interest_rate_differentials=bool(cf.get("interest_rate_differentials")),
            intermarket=bool(cf.get("intermarket")),
            seasonal_tendency=cf.get("seasonal_tendency") if cf.get("seasonal_tendency") in ("bullish", "bearish", "ideal", "none") else "none",
        ),
        htf_pd=HtfPd(
            dealing_range_tf=pd.get("dealing_range_tf") or "none",
            equilibrium=pd.get("equilibrium"),
            nearest_premium_id=pd.get("nearest_premium_id"),
            nearest_discount_id=pd.get("nearest_discount_id"),
        ),
        setup_progression=block.get("setup_progression") or "none",
        entry_technique=block.get("entry_technique") if block.get("entry_technique") in ("stop", "limit", "none") else "none",
        position_management=block.get("position_management") or "none",
        position_opportunity=PositionOpportunity(
            flag=bool(opp.get("flag", False)),
            reason=opp.get("reason") or "provided_state",
        ),
    )
