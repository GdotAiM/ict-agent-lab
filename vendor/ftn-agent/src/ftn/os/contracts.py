
"""v2.1 contracts. No scoring. No winner selection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Literal, Optional


Bias = Literal["bullish", "bearish", "unclear", "not_scored"]
Conf = Literal["aligned", "qualified", "conflicted", "unclear"]
Rel = Literal["supportive", "neutral", "contradictory", "unavailable"]
Profile = Literal[
    "expansion", "consolidation", "reversal_watch", "continuation", "unclear"
]
Origin = Literal[
    "ict_source", "hermes_interpretation", "hermes_governance", "hermes_empirical"
]
CandState = Literal[
    "selected", "suppressed", "invalidated", "ineligible", "annotate", "unevaluated"
]


def _freeze(obj: Any) -> Any:
    if is_dataclass(obj):
        return tuple((k, _freeze(getattr(obj, k))) for k in obj.__dataclass_fields__)
    if isinstance(obj, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in obj.items()))
    if isinstance(obj, list):
        return tuple(_freeze(v) for v in obj)
    return obj


@dataclass(frozen=True)
class TfBias:
    monthly: Bias = "not_scored"
    weekly: Bias = "not_scored"
    daily: Bias = "unclear"
    h4: Bias = "unclear"


@dataclass(frozen=True)
class DaytradeIof:
    daily: Bias = "unclear"
    h4: Bias = "unclear"
    m60: Bias = "unclear"


@dataclass(frozen=True)
class InstitutionalContext:
    sponsorship: TfBias = field(default_factory=TfBias)
    daytrade_iof: DaytradeIof = field(default_factory=DaytradeIof)
    state: Bias = "unclear"
    confidence: Conf = "unclear"
    notes: tuple = ()


@dataclass(frozen=True)
class WilliamsR:
    name: str = "williams_r"
    period: int = 10
    timeframe: str = "m15"
    value: Optional[float] = None
    state: str = "unavailable"


@dataclass(frozen=True)
class Probe:
    preferred_side: str = "either"
    observed_side: str = "none"


@dataclass(frozen=True)
class Sentiment:
    direction: Bias = "unclear"
    expected_delivery: str = "unclear"
    indicator: WilliamsR = field(default_factory=WilliamsR)
    reference_open: str = "gmt0"
    asian_range: dict = field(default_factory=dict)
    liquidity_probe: Probe = field(default_factory=Probe)
    judas_side: str = "none"
    reaction: dict = field(default_factory=lambda: {"pd_array_reaction": "none"})
    basis: tuple = ()


@dataclass(frozen=True)
class PdArray:
    id: str
    kind: str
    tf: str
    low: float
    high: float


@dataclass(frozen=True)
class PdMatrix:
    htf: dict = field(default_factory=dict)
    ltf: dict = field(default_factory=dict)
    confluences: tuple = ()


@dataclass(frozen=True)
class SessionTicket:
    id: str
    kind: str
    module: str
    session: str


@dataclass(frozen=True)
class DayContext:
    date: str
    symbol: str
    timezone: str = "America/New_York"
    last: Optional[float] = None
    calendar: tuple = ()
    watchlist: tuple = ()
    focus_pair: str = ""
    dxy: dict = field(default_factory=dict)
    pair_institutional: InstitutionalContext = field(default_factory=InstitutionalContext)
    origin_pd_array: Optional[str] = None
    opposing_target_arrays: tuple = ()
    opens: dict = field(default_factory=dict)
    ranges: dict = field(default_factory=dict)
    adr5: dict = field(default_factory=dict)
    pd_matrix: PdMatrix = field(default_factory=PdMatrix)
    sentiment: Sentiment = field(default_factory=Sentiment)
    profile: Profile = "unclear"
    scenarios: dict = field(default_factory=dict)
    session_ticket: Optional[SessionTicket] = None
    evidence: dict = field(default_factory=dict)
    month8: object = None  # Month8State | None; optional ICT day-trade layer
    month7: object = None  # Month7State | None; optional ICT weekly layer
    month6: object = None  # Month6State | None; optional ICT swing layer
    month5: object = None  # Month5State | None; optional ICT position layer
    month4: object = None  # Month4State | None; optional ICT PD-array catalog
    month3: object = None  # Month3State | None; optional ICT next-setup layer
    month2: object = None  # Month2State | None; optional ICT risk-frame layer
    month1: object = None  # Month1State | None; optional ICT foundation layer
    month10: object = None  # Month10State | None; optional ICT multi-asset layer
    month11: object = None  # Month11State | None; optional ICT mega-trade layer
    month12: object = None  # Month12State | None; optional ICT top-down layer
    charter: object = None  # CharterState | None; optional ICT Charter PAM layer
    pam1_evidence: object = None  # Pam1Evidence | None; read-only model-instance context
    pam1_completeness: object = None  # Pam1Completeness | None; descriptive only


@dataclass(frozen=True)
class Candidate:
    module: str
    state: CandState = "unevaluated"
    eligible: bool = False
    reason: str = ""
    origin: Origin = "hermes_interpretation"


@dataclass(frozen=True)
class MarketState:
    """Frozen snapshot. Models read this; they do not write it."""

    context: DayContext
    fingerprint: str = ""


def freeze_market_state(ctx: DayContext) -> MarketState:
    blob = json.dumps(asdict(ctx), sort_keys=True, default=str)
    fp = str(abs(hash(blob)))
    return MarketState(context=ctx, fingerprint=fp)


def _inst(d: dict | None) -> InstitutionalContext:
    d = d or {}
    sp = d.get("sponsorship") or {}
    dt = d.get("daytrade_iof") or {}
    return InstitutionalContext(
        sponsorship=TfBias(
            monthly=sp.get("monthly", "not_scored"),
            weekly=sp.get("weekly", "not_scored"),
            daily=sp.get("daily", "unclear"),
            h4=sp.get("h4", "unclear"),
        ),
        daytrade_iof=DaytradeIof(
            daily=dt.get("daily", "unclear"),
            h4=dt.get("h4", "unclear"),
            m60=dt.get("m60", "unclear"),
        ),
        state=d.get("state", "unclear"),
        confidence=d.get("confidence", "unclear"),
        notes=tuple(d.get("notes") or ()),
    )


def _sent(d: dict | None) -> Sentiment:
    d = d or {}
    ind = d.get("indicator") or {}
    pr = d.get("liquidity_probe") or {}
    return Sentiment(
        direction=d.get("direction", "unclear"),
        expected_delivery=d.get("expected_delivery", "unclear"),
        indicator=WilliamsR(
            value=ind.get("value"),
            state=ind.get("state", "unavailable"),
        ),
        reference_open=d.get("reference_open", "gmt0"),
        asian_range=d.get("asian_range") or {},
        liquidity_probe=Probe(
            preferred_side=pr.get("preferred_side", "either"),
            observed_side=pr.get("observed_side", "none"),
        ),
        judas_side=d.get("judas_side", "none"),
        reaction=d.get("reaction") or {"pd_array_reaction": "none"},
        basis=tuple(d.get("basis") or ()),
    )


def _pdm(d: dict | None) -> PdMatrix:
    d = d or {}
    return PdMatrix(
        htf=d.get("htf") or {},
        ltf=d.get("ltf") or {},
        confluences=tuple(d.get("confluences") or ()),
    )


def _month8(raw: dict):
    from ftn.os.m8_contracts import parse_month8
    return parse_month8(raw)


def _month7(raw: dict):
    from ftn.os.m7_contracts import parse_month7
    return parse_month7(raw)


def _month6(raw: dict):
    from ftn.os.m6_contracts import parse_month6
    return parse_month6(raw)

def _month5(raw: dict):
    from ftn.os.m5_contracts import parse_month5
    return parse_month5(raw)

def _month4(raw: dict):
    from ftn.os.m4_contracts import parse_month4
    return parse_month4(raw)

def _month3(raw: dict):
    from ftn.os.m3_contracts import parse_month3
    return parse_month3(raw)

def _month2(raw: dict):
    from ftn.os.m2_contracts import parse_month2
    return parse_month2(raw)

def _month1(raw: dict):
    from ftn.os.m1_contracts import parse_month1
    return parse_month1(raw)

def _month10(raw: dict):
    from ftn.os.m10_contracts import parse_month10
    return parse_month10(raw)

def _month11(raw: dict):
    from ftn.os.m11_contracts import parse_month11
    return parse_month11(raw)

def _month12(raw: dict):
    from ftn.os.m12_contracts import parse_month12
    return parse_month12(raw)

def _charter(raw: dict):
    from ftn.os.pam_contracts import parse_charter
    return parse_charter(raw)

def _pam1_evidence(raw: dict):
    from ftn.os.pam1_evidence import parse_pam1_evidence
    return parse_pam1_evidence(raw)

def _pam1_completeness(raw: dict):
    from ftn.os.pam1_complete import derive_pam1_completeness
    return derive_pam1_completeness(raw)


def load_day_context(path: str | Path) -> DayContext:
    raw = json.loads(Path(path).read_text())
    if "expected_winner" in raw or "pick" in raw:
        raise ValueError("fixture must not name a winning model")
    pair_ic = _inst(raw.get("pair_institutional") or raw.get("institutional"))
    return DayContext(
        date=raw["date"],
        symbol=raw["symbol"],
        timezone=raw.get("timezone", "America/New_York"),
        last=raw.get("last"),
        calendar=tuple(raw.get("calendar") or ()),
        watchlist=tuple(raw.get("watchlist") or ()),
        focus_pair=raw.get("focus_pair") or raw["symbol"],
        dxy=raw.get("dxy") or {},
        pair_institutional=pair_ic,
        origin_pd_array=raw.get("origin_pd_array"),
        opposing_target_arrays=tuple(raw.get("opposing_target_arrays") or ()),
        opens=raw.get("opens") or {},
        ranges=raw.get("ranges") or {},
        adr5=raw.get("adr5") or {},
        pd_matrix=_pdm(raw.get("pd_matrix")),
        sentiment=_sent(raw.get("sentiment")),
        profile=raw.get("profile", "unclear"),
        scenarios=raw.get("scenarios") or {},
        evidence=raw.get("evidence") or {},
        month8=_month8(raw),
        month7=_month7(raw),
        month6=_month6(raw),
        month5=_month5(raw),
        month4=_month4(raw),
        month3=_month3(raw),
        month2=_month2(raw),
        month1=_month1(raw),
        month10=_month10(raw),
        month11=_month11(raw),
        month12=_month12(raw),
        charter=_charter(raw),
        pam1_evidence=_pam1_evidence(raw),
        pam1_completeness=_pam1_completeness(raw),
    )


def context_to_dict(ctx: DayContext) -> dict:
    return asdict(ctx)
