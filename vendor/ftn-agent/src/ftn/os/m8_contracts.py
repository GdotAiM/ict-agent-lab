
"""Month-8 contracts. ICT day-trade layer on Market State. No detectors here."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

CbdrClass = Literal["ideal", "expanded", "wide", "unknown"]
LondonProfile = Literal[
    "normal_protraction_buy",
    "normal_protraction_sell",
    "delayed_protraction_buy",
    "delayed_protraction_sell",
    "none",
]
Draw = Literal["high", "low", "none"]


@dataclass(frozen=True)
class IctTrueDay:
    """ICT day != broker/MT4 midnight. All windows are New York local."""

    clock: str = "America/New_York"
    day_anchor: str = "00:00"
    asian: tuple = ("20:00", "00:00")
    london_kz: tuple = ("01:00", "05:00")
    london_close: tuple = ("10:00", "12:00")
    ny_am: tuple = ("07:00", "10:00")
    cbdr_window: tuple = ("14:00", "20:00")
    origin: str = "ict_source"


@dataclass(frozen=True)
class CbdrState:
    height_pips: Optional[float] = None
    body_height_pips: Optional[float] = None
    wick_high: Optional[float] = None
    wick_low: Optional[float] = None
    body_high: Optional[float] = None
    body_low: Optional[float] = None
    classification: CbdrClass = "unknown"
    daytrade_classic: bool = False  # True only when classification == ideal (<40)
    origin: str = "ict_source"


@dataclass(frozen=True)
class LondonGate:
    allowed: bool = False
    reason: Optional[str] = None  # wide_cbdr | poor_consolidation | adr_spent | news | none
    origin: str = "ict_source"


@dataclass(frozen=True)
class DailyExtremeProjection:
    draw: Draw = "none"
    sd_levels: tuple = ()
    source_range: str = "cbdr"
    selected_level: Optional[float] = None
    basis: tuple = ()
    origin: str = "ict_source"


@dataclass(frozen=True)
class HtfOverlap:
    present: bool = False
    array_id: Optional[str] = None
    timeframe: Optional[str] = None
    relationship: Optional[str] = None
    origin: str = "ict_source"


@dataclass(frozen=True)
class Month8State:
    """ICT day-trade layer. Distinct from Hermes `profile`."""

    ict_true_day: IctTrueDay = field(default_factory=IctTrueDay)
    cbdr: CbdrState = field(default_factory=CbdrState)
    asian_height_pips: Optional[float] = None
    london_session_gate: LondonGate = field(default_factory=LondonGate)
    ict_london_profile: LondonProfile = "none"
    daily_extreme_projection: DailyExtremeProjection = field(default_factory=DailyExtremeProjection)
    daytrade_opportunity: bool = False
    htf_entry_overlap: HtfOverlap = field(default_factory=HtfOverlap)
    ict_guidance: dict = field(
        default_factory=lambda: {
            "approx_setups_per_day": 2,
            "adr_capture_pct": "65-75",
            "note": "guidance not hermes_governance",
        }
    )


def classify_cbdr(height_pips: float | None) -> str:
    if height_pips is None:
        return "unknown"
    if height_pips < 40:
        return "ideal"
    if height_pips < 50:
        return "expanded"
    return "wide"


def parse_month8(raw: dict | None) -> Month8State | None:
    if not raw:
        return None
    block = raw.get("month8") or raw.get("ict_day")
    if not block:
        return None
    cb = block.get("cbdr") or {}
    height = cb.get("height_pips")
    cls = cb.get("classification") or classify_cbdr(height)
    gate = block.get("london_session_gate") or {}
    proj = block.get("daily_extreme_projection") or {}
    ov = block.get("htf_entry_overlap") or {}
    return Month8State(
        cbdr=CbdrState(
            height_pips=height,
            body_height_pips=cb.get("body_height_pips"),
            wick_high=cb.get("wick_high"),
            wick_low=cb.get("wick_low"),
            body_high=cb.get("body_high"),
            body_low=cb.get("body_low"),
            classification=cls,
            daytrade_classic=cls == "ideal",
        ),
        asian_height_pips=block.get("asian_height_pips"),
        london_session_gate=LondonGate(
            allowed=bool(gate.get("allowed", False)),
            reason=gate.get("reason"),
        ),
        ict_london_profile=block.get("ict_london_profile") or "none",
        daily_extreme_projection=DailyExtremeProjection(
            draw=proj.get("draw") or "none",
            sd_levels=tuple(proj.get("sd_levels") or ()),
            source_range=proj.get("source_range") or "cbdr",
            selected_level=proj.get("selected_level"),
            basis=tuple(proj.get("basis") or ()),
        ),
        daytrade_opportunity=bool(block.get("daytrade_opportunity", False)),
        htf_entry_overlap=HtfOverlap(
            present=bool(ov.get("present", False)),
            array_id=ov.get("array_id"),
            timeframe=ov.get("timeframe"),
            relationship=ov.get("relationship"),
        ),
    )
