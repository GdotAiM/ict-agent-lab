"""Month-6 Slice 1 contracts. No detectors.

Glossary: Slice 0 signed with six Million-Dollar gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

SwingFamily = Literal["bull", "bear", "none"]
Suit = Literal["suitable", "unsuitable", "unclear"]
MdState = Literal["assembled", "incomplete", "none"]
SeqState = Literal["watching", "none"]

BULL_SEQUENCES = (
    "mwd_all_bullish",
    "mw_bullish_daily_correcting",
    "m_bullish_wd_correcting",
)
BEAR_SEQUENCES = (
    "mwd_all_bearish",
    "mw_bearish_daily_correcting",
    "m_bearish_wd_correcting",
)
SEQUENCES = BULL_SEQUENCES + BEAR_SEQUENCES + ("none",)

MD_GATES = (
    "seasonal_tendency",
    "major_market_analysis",
    "intermarket_analysis",
    "top_down_analysis",
    "setup",
    "management",
)

REQUIRED_EVIDENCE = ("htf_trend", "institutional_order_flow", "pd_arrays")
CONFIRMING_EVIDENCE = ("seasonal_tendency", "interest_rates", "cot", "intermarket")


@dataclass(frozen=True)
class MarketSelection:
    state: Suit = "unclear"
    origin: str = "ict_source"


@dataclass(frozen=True)
class SequentialPattern:
    name: str = "none"
    state: SeqState = "none"
    origin: str = "ict_source"


@dataclass(frozen=True)
class SupportingEvidence:
    htf_trend: bool = False
    institutional_order_flow: bool = False
    pd_arrays: bool = False
    seasonal_tendency: bool = False
    interest_rates: bool = False
    cot: bool = False
    intermarket: bool = False


@dataclass(frozen=True)
class RiskFrame:
    stop_reference: Optional[str] = None
    target_reference: Optional[str] = None
    reward_frame: Optional[str] = None
    origin: str = "ict_source"


@dataclass(frozen=True)
class MillionDollarSwing:
    state: MdState = "none"
    missing: tuple = ()
    origin: str = "ict_source"


@dataclass(frozen=True)
class SwingOpportunity:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month6State:
    market_selection: MarketSelection = field(default_factory=MarketSelection)
    htf_draw: str = "unclear"  # bullish | bearish | unclear; not swing_family
    swing_family: SwingFamily = "none"
    sequential_pattern: SequentialPattern = field(default_factory=SequentialPattern)
    supporting_evidence: SupportingEvidence = field(default_factory=SupportingEvidence)
    risk_frame: RiskFrame = field(default_factory=RiskFrame)
    million_dollar_swing: MillionDollarSwing = field(default_factory=MillionDollarSwing)
    swing_opportunity: SwingOpportunity = field(default_factory=SwingOpportunity)


def _seq(name: str | None) -> str:
    n = name or "none"
    return n if n in SEQUENCES else "none"


def parse_month6(raw: dict) -> Month6State | None:
    block = raw.get("month6") or raw.get("ict_swing")
    if not block:
        return None
    sel = block.get("market_selection") or {}
    if isinstance(sel, str):
        sel = {"state": sel}
    seq = block.get("sequential_pattern") or {}
    if isinstance(seq, str):
        seq = {"name": seq}
    ev = block.get("supporting_evidence") or {}
    rf = block.get("risk_frame") or {}
    md = block.get("million_dollar_swing") or {}
    if isinstance(md, str):
        md = {"state": md}
    so = block.get("swing_opportunity") or {}
    if isinstance(so, bool):
        so = {"flag": so}
    fam = block.get("swing_family") or "none"
    if fam not in ("bull", "bear", "none"):
        fam = "none"
    miss = tuple(md.get("missing") or ())
    st = md.get("state") or "none"
    if st not in ("assembled", "incomplete", "none"):
        st = "none"
    suit = sel.get("state") or "unclear"
    if suit not in ("suitable", "unsuitable", "unclear"):
        suit = "unclear"
    return Month6State(
        market_selection=MarketSelection(state=suit, origin=sel.get("origin") or "ict_source"),
        htf_draw=block.get("htf_draw") if block.get("htf_draw") in ("bullish", "bearish", "unclear") else "unclear",
        swing_family=fam,
        sequential_pattern=SequentialPattern(
            name=_seq(seq.get("name")),
            state=seq.get("state") or ("watching" if seq.get("name") and seq.get("name") != "none" else "none"),
            origin=seq.get("origin") or "ict_source",
        ),
        supporting_evidence=SupportingEvidence(
            htf_trend=bool(ev.get("htf_trend")),
            institutional_order_flow=bool(ev.get("institutional_order_flow")),
            pd_arrays=bool(ev.get("pd_arrays")),
            seasonal_tendency=bool(ev.get("seasonal_tendency")),
            interest_rates=bool(ev.get("interest_rates")),
            cot=bool(ev.get("cot")),
            intermarket=bool(ev.get("intermarket")),
        ),
        risk_frame=RiskFrame(
            stop_reference=rf.get("stop_reference"),
            target_reference=rf.get("target_reference"),
            reward_frame=rf.get("reward_frame"),
            origin=rf.get("origin") or "ict_source",
        ),
        million_dollar_swing=MillionDollarSwing(
            state=st,
            missing=miss,
            origin=md.get("origin") or "ict_source",
        ),
        swing_opportunity=SwingOpportunity(
            flag=bool(so.get("flag", False)),
            reason=so.get("reason") or "provided_state",
        ),
    )
