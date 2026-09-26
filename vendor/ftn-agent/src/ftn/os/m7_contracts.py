"""Month-7 Slice 1 contracts. No detectors.

Glossary frozen from Slice 0 (lessons 2–3).
Hermes profile ≠ ict_weekly_profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

Tf = Literal["monthly", "weekly", "daily", "h4", "none"]
Dir = Literal["bullish", "bearish", "unclear"]
LrlrState = Literal["low", "high", "unclear"]
Contrary = Literal["watch", "confirmed", "none"]
ProfState = Literal["watching", "invalidated", "none"]

WEEKLY_PROFILES = (
    "classic_tuesday_low_of_week",
    "classic_tuesday_high_of_week",
    "wednesday_low_of_week",
    "wednesday_high_of_week",
    "consolidation_thursday_reversal_bullish",
    "consolidation_thursday_reversal_bearish",
    "consolidation_midweek_rally",
    "consolidation_midweek_decline",
    "seek_and_destroy_bullish_friday",
    "seek_and_destroy_bearish_friday",
    "wednesday_weekly_reversal_bullish",
    "wednesday_weekly_reversal_bearish",
    "none",
)

# Lesson 3 mechanisms — not weekly profiles
MANIPULATION_TEMPLATES = (
    "classic_tuesday_low_liquidity_pool",
    "classic_tuesday_low_old_high_retest",
    "classic_tuesday_low_bullish_order_block",
    "classic_tuesday_high_liquidity_pool",
    "classic_tuesday_high_old_low_retest",
    "classic_tuesday_high_bearish_order_block",
    "wednesday_low_liquidity_pool",
    "wednesday_low_old_high_retest",
    "wednesday_low_bullish_order_block",
    "wednesday_high_liquidity_pool",
    "wednesday_high_old_low_retest",
    "wednesday_high_bearish_order_block",
    "consolidation_midweek_rally",
    "consolidation_midweek_decline",
    "consolidation_thursday_reversal_bullish",
    "consolidation_thursday_reversal_bearish",
    "seek_and_destroy_bullish_friday",
    "seek_and_destroy_bearish_friday",
    "wednesday_weekly_reversal_bullish",
    "wednesday_weekly_reversal_bearish",
    "none",
)


@dataclass(frozen=True)
class DealingRange:
    from_array_id: Optional[str] = None
    from_tf: Tf = "none"
    to_array_id: Optional[str] = None
    to_tf: Tf = "none"
    direction: Dir = "unclear"
    origin: str = "ict_source"


@dataclass(frozen=True)
class IctWeeklyProfile:
    name: str = "none"
    state: ProfState = "none"
    origin: str = "ict_source"


@dataclass(frozen=True)
class ManipulationTemplate:
    name: str = "none"
    pool_tf: Tf = "none"
    origin: str = "ict_source"


@dataclass(frozen=True)
class IpdaWindow:
    days: Optional[int] = None  # 20 | 40 | 60 | None
    origin: str = "ict_source"


@dataclass(frozen=True)
class Lrlr:
    state: LrlrState = "unclear"
    origin: str = "ict_source"


@dataclass(frozen=True)
class IntraweekContrary:
    state: Contrary = "none"
    origin: str = "ict_source"


@dataclass(frozen=True)
class OsokOpportunity:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class SwingTicket:
    """Hermes governance. Paper weekly horizon. Not session_ticket."""

    id: str = ""
    kind: str = "paper_swing"
    module: str = "OSOK"
    opened: str = ""
    status: str = "none"  # open | closed | none
    origin: str = "hermes_governance"


@dataclass(frozen=True)
class Month7State:
    dealing_range: DealingRange = field(default_factory=DealingRange)
    ict_weekly_profile: IctWeeklyProfile = field(default_factory=IctWeeklyProfile)
    manipulation_template: ManipulationTemplate = field(default_factory=ManipulationTemplate)
    ipda_window: IpdaWindow = field(default_factory=IpdaWindow)
    lrlr: Lrlr = field(default_factory=Lrlr)
    intraweek_contrary: IntraweekContrary = field(default_factory=IntraweekContrary)
    osok_opportunity: OsokOpportunity = field(default_factory=OsokOpportunity)
    swing_ticket: Optional[SwingTicket] = None
    ict_guidance: dict = field(
        default_factory=lambda: {
            "weekly_extreme_mon_wed": "often ~70-76%",
            "note": "guidance not hermes_governance",
        }
    )


def _norm_profile(name: str | None) -> str:
    n = name or "none"
    return n if n in WEEKLY_PROFILES else "none"


def _norm_template(name: str | None) -> str:
    n = name or "none"
    return n if n in MANIPULATION_TEMPLATES else "none"


def parse_month7(raw: dict) -> Month7State | None:
    block = raw.get("month7") or raw.get("ict_week")
    if not block:
        return None
    dr = block.get("dealing_range") or {}
    wp = block.get("ict_weekly_profile") or {}
    if isinstance(wp, str):
        wp = {"name": wp}
    tm = block.get("manipulation_template") or {}
    if isinstance(tm, str):
        tm = {"name": tm}
    ip = block.get("ipda_window") or {}
    if isinstance(ip, int):
        ip = {"days": ip}
    lr = block.get("lrlr") or {}
    if isinstance(lr, str):
        lr = {"state": lr}
    ct = block.get("intraweek_contrary") or {}
    if isinstance(ct, str):
        ct = {"state": ct}
    oo = block.get("osok_opportunity") or {}
    if isinstance(oo, bool):
        oo = {"flag": oo}
    sw = block.get("swing_ticket")
    ticket = None
    if isinstance(sw, dict) and sw.get("id"):
        ticket = SwingTicket(
            id=str(sw.get("id") or ""),
            kind=sw.get("kind") or "paper_swing",
            module=sw.get("module") or "OSOK",
            opened=sw.get("opened") or "",
            status=sw.get("status") or "none",
            origin=sw.get("origin") or "hermes_governance",
        )
    days = ip.get("days")
    if days not in (20, 40, 60, None):
        days = None
    return Month7State(
        dealing_range=DealingRange(
            from_array_id=dr.get("from_array_id"),
            from_tf=dr.get("from_tf") or "none",
            to_array_id=dr.get("to_array_id"),
            to_tf=dr.get("to_tf") or "none",
            direction=dr.get("direction") or "unclear",
            origin=dr.get("origin") or "ict_source",
        ),
        ict_weekly_profile=IctWeeklyProfile(
            name=_norm_profile(wp.get("name")),
            state=wp.get("state") or ("watching" if wp.get("name") and wp.get("name") != "none" else "none"),
            origin=wp.get("origin") or "ict_source",
        ),
        manipulation_template=ManipulationTemplate(
            name=_norm_template(tm.get("name")),
            pool_tf=tm.get("pool_tf") or "none",
            origin=tm.get("origin") or "ict_source",
        ),
        ipda_window=IpdaWindow(days=days, origin=ip.get("origin") or "ict_source"),
        lrlr=Lrlr(state=lr.get("state") or "unclear", origin=lr.get("origin") or "ict_source"),
        intraweek_contrary=IntraweekContrary(
            state=ct.get("state") or "none",
            origin=ct.get("origin") or "ict_source",
        ),
        osok_opportunity=OsokOpportunity(
            flag=bool(oo.get("flag", False)),
            reason=oo.get("reason") or "provided_state",
        ),
        swing_ticket=ticket,
        ict_guidance=block.get("ict_guidance")
        or {
            "weekly_extreme_mon_wed": "often ~70-76%",
            "note": "guidance not hermes_governance",
        },
    )
