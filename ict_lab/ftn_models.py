"""Pydantic v2 models for FTN (Filling The Numbers) workflow outputs.

FTN's own contracts (ftn.os.contracts) are frozen dataclasses for the Month-9
briefing path; run_workflow() returns plain dicts. These models mirror that
ticket shape and enforce the FTN charter's hard laws on every result:
PAPER only, live disabled, no orders.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

FAMILIES = ("pivots", "cbdr", "asian", "flout")
STAGES = ["PREP", "FILTER", "WATCH", "GATE", "MANAGE", "JOURNAL"]
KNOWN_NO_TRADE = {
    "compressed_atr", "no_pd_array_overlap", "setup_gate_incomplete", "non_paper_mode_refused",
}


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow")


# -- Inputs -------------------------------------------------------------------------

class _Range(_Base):
    high: float
    low: float

    @model_validator(mode="after")
    def _hl(self):
        if self.high <= self.low:
            raise ValueError("high must be greater than low")
        return self


class PreviousDay(_Range):
    close: float

    @model_validator(mode="after")
    def _close_inside(self):
        if not (self.low <= self.close <= self.high):
            raise ValueError("close must be within [low, high]")
        return self


class PdArrayIn(_Base):
    id: str
    kind: str
    low: float
    high: float


class FtnSetup(_Base):
    killzone: Optional[str] = None
    liquidity_raid: bool = False
    displacement: bool = False
    mss: bool = False
    pd_retrace: bool = False


class FtnInputPack(_Base):
    """The OHLC pack run_workflow() consumes (same shape as fixtures/sample_eurusd.json)."""
    symbol: str = Field(min_length=3)
    pip: float = Field(gt=0)
    htf_bias: Literal["bullish", "bearish"] = "bullish"
    last: Optional[float] = Field(default=None, gt=0)
    atr: Optional[float] = Field(default=None, gt=0)
    previous_day: PreviousDay
    swings: dict = Field(default_factory=dict)
    cbdr: _Range
    asian: _Range
    flout: _Range
    pd_arrays: list[PdArrayIn] = Field(default_factory=list)
    setup: FtnSetup = Field(default_factory=FtnSetup)


# -- Outputs ------------------------------------------------------------------------

class FtnLevel(_Base):
    index: int = Field(ge=1, le=4)
    name: str
    price: float


class FtnConfluenceHit(FtnLevel):
    pd_array: str
    kind: Optional[str] = None


class FtnManagement(_Base):
    scale_out_after_levels: int = Field(ge=1)
    runner_pct: float = Field(ge=0, le=1)
    note: str


class FtnTicket(_Base):
    kind: Literal["entry_candidate", "no_trade"]
    actionable_for_mint: bool
    symbol: str
    bias: Literal["bullish", "bearish"]
    price: float
    family: Literal["pivots", "cbdr", "asian", "flout"]
    four_levels: list[FtnLevel] = Field(max_length=4)
    all_families: dict[str, list[FtnLevel]]
    pd_confluence: list[FtnConfluenceHit]
    volatility_atr_pips: float = Field(ge=0)
    compressed: bool
    gate_ok: bool
    no_trade_reasons: list[str]
    management: FtnManagement
    # Charter hard laws: PAPER only, live never enabled.
    mode: Literal["paper"]
    live_enabled: Literal[False]

    @model_validator(mode="after")
    def _consistency(self):
        if set(self.all_families) != set(FAMILIES):
            raise ValueError(f"all_families must contain exactly {FAMILIES}")
        unknown = set(self.no_trade_reasons) - KNOWN_NO_TRADE
        if unknown:
            raise ValueError(f"unknown no_trade_reasons: {sorted(unknown)}")
        if self.actionable_for_mint != (not self.no_trade_reasons):
            raise ValueError("actionable_for_mint must be True iff there are no no_trade_reasons")
        if (self.kind == "entry_candidate") != self.actionable_for_mint:
            raise ValueError("kind must be entry_candidate iff actionable_for_mint")
        if self.compressed and "compressed_atr" not in self.no_trade_reasons:
            raise ValueError("compressed session must be filtered as NO-TRADE")
        if not self.pd_confluence and "no_pd_array_overlap" not in self.no_trade_reasons:
            raise ValueError("no PD-array overlap must be filtered as NO-TRADE")
        if not self.gate_ok and "setup_gate_incomplete" not in self.no_trade_reasons:
            raise ValueError("incomplete setup gate must be filtered as NO-TRADE")
        return self


class FtnWorkflowResult(BaseModel):
    """What the agent sees: measurements, NO-TRADE filter, confluence, paper ticket."""
    model_config = ConfigDict(extra="ignore")
    ok: Literal[True]
    stage: Literal["all", "prep"]
    stages: list[str]
    scanned_at: str
    ticket: FtnTicket
    measurements: dict  # four measurement families (pivots / cbdr / asian / flout)
    no_trade: bool
    orders_placed: Literal[0] = 0
    note: str
    journal_markdown: Optional[str] = None


class FtnCandidate(_Base):
    module: str
    state: str
    eligible: bool
    reason: Optional[str] = None
    origin: Optional[str] = None


class FtnBriefing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fixture: str
    date: Optional[str] = None
    symbol: Optional[str] = None
    mode: Literal["paper"] = "paper"
    candidates: list[FtnCandidate]
    briefing_markdown: str
    truncated: bool = False
