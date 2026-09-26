"""Pure-Python ICT research tools (wrapped as Strands tools in main.py).

These tools do arithmetic and structuring only. They make no claims about
whether any trading idea works -- that is what the research is for.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from pydantic import ValidationError

from .models import MeasurementWindow, ResearchHypothesis, RiskReward, validation_error_json


# -- Risk / reward -------------------------------------------------------------------

def compute_risk_reward(entry: float, stop_loss: float, target: float,
                        direction: Optional[str] = None) -> RiskReward:
    """Return a validated RiskReward. Raises ValueError/ValidationError on bad input."""
    for name, v in (("entry", entry), ("stop_loss", stop_loss), ("target", target)):
        if v is None or float(v) <= 0:
            raise ValueError(f"{name} must be a positive price")
    entry, stop_loss, target = float(entry), float(stop_loss), float(target)
    if entry == stop_loss:
        raise ValueError("stop_loss cannot equal entry (risk would be zero)")

    if direction is None or str(direction).strip() == "":
        direction = "long" if stop_loss < entry else "short"
    direction = str(direction).strip().lower()
    direction = {"buy": "long", "sell": "short"}.get(direction, direction)
    if direction not in ("long", "short"):
        raise ValueError("direction must be 'long' or 'short'")

    if direction == "long" and stop_loss > entry:
        raise ValueError("for a long trade the stop_loss must be below entry")
    if direction == "short" and stop_loss < entry:
        raise ValueError("for a short trade the stop_loss must be above entry")
    if direction == "long" and target <= entry:
        raise ValueError("for a long trade the target must be above entry")
    if direction == "short" and target >= entry:
        raise ValueError("for a short trade the target must be below entry")

    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    return RiskReward(
        direction=direction, entry=entry, stop_loss=stop_loss, target=target,
        risk=round(risk, 6), reward=round(reward, 6), r_multiple=round(reward / risk, 2),
    )


def risk_reward_json(entry: float, stop_loss: float, target: float,
                     direction: Optional[str] = None) -> str:
    try:
        return compute_risk_reward(entry, stop_loss, target, direction).model_dump_json()
    except ValidationError as exc:
        return validation_error_json(RiskReward, exc)
    except (TypeError, ValueError) as exc:
        return json.dumps({"error": f"RiskReward: {exc}"})


# -- Research hypothesis -------------------------------------------------------------

# Symbols recognised in questions (extend freely; user-editable).
KNOWN_INSTRUMENTS = [
    "MNQ", "MES", "NQ", "ES", "YM", "RTY", "CL", "GC", "SI", "ZN", "ZB",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "DXY", "BTC", "ETH", "SPY", "QQQ",
]

TIMEZONE_ALIASES = {
    r"\bny\b|new york|\bet\b|\best\b|\bedt\b": "America/New_York",
    r"london|\bgmt\b|\bbst\b": "Europe/London",
    r"tokyo|\bjst\b": "Asia/Tokyo",
    r"johannesburg|\bsast\b": "Africa/Johannesburg",
    r"\butc\b": "UTC",
}

# Reference levels -> plain-language description used in the observable condition.
REFERENCE_LEVELS = {
    "midnight open": "the opening price of the 00:00 (New York time) candle for that day",
    "fvg": "the boundaries of the fair value gap (FVG) defined in the question",
    "fair value gap": "the boundaries of the fair value gap (FVG) defined in the question",
    "previous day high": "the prior session's high",
    "previous day low": "the prior session's low",
}

_WINDOW = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|–|to)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
    re.IGNORECASE,
)


def _to_24h(hour: int, minute: int, ampm: Optional[str]) -> str:
    if ampm:
        ampm = ampm.lower()
        if hour == 12:
            hour = 0
        if ampm == "pm":
            hour += 12
    return f"{hour:02d}:{minute:02d}"


def parse_window(question: str) -> Optional[tuple[str, str]]:
    """Find a same-day time range such as '10-11am' or '9:30 to 10:00 am'."""
    m = _WINDOW.search(question)
    if not m:
        return None
    h1, m1, ap1, h2, m2, ap2 = m.groups()
    ap1 = ap1 or ap2  # "10-11am" -> both am
    start = _to_24h(int(h1), int(m1 or 0), ap1)
    end = _to_24h(int(h2), int(m2 or 0), ap2)
    return start, end


def detect_instrument(question: str) -> Optional[str]:
    tokens = re.findall(r"[A-Za-z]{2,6}", question)
    upper = {t.upper() for t in tokens if t.isupper()}
    for sym in KNOWN_INSTRUMENTS:
        if sym in upper:
            return sym
    return None


def detect_timezone(question: str) -> Optional[str]:
    q = question.lower()
    for pattern, tz in TIMEZONE_ALIASES.items():
        if re.search(pattern, q):
            return tz
    return None


def build_hypothesis(question: str, *, hypothesis: Optional[str] = None,
                     instrument: Optional[str] = None,
                     observable_condition: Optional[str] = None,
                     invalidation_condition: Optional[str] = None,
                     window_start: Optional[str] = None, window_end: Optional[str] = None,
                     timezone: Optional[str] = None,
                     required_evidence: Optional[list[str]] = None) -> ResearchHypothesis:
    """Build a validated ResearchHypothesis. Explicit args override parsed defaults."""
    question = (question or "").strip()
    instrument = instrument or detect_instrument(question)
    if not instrument:
        raise ValueError("could not detect an instrument; pass instrument explicitly (e.g. NQ)")
    parsed = parse_window(question)
    window_start = window_start or (parsed[0] if parsed else None)
    window_end = window_end or (parsed[1] if parsed else None)
    if not (window_start and window_end):
        raise ValueError("could not detect a time window; pass window_start/window_end as HH:MM")
    timezone = timezone or detect_timezone(question) or "America/New_York"

    q = question.lower()
    level = next((desc for key, desc in REFERENCE_LEVELS.items() if key in q), None)
    level_text = level or "the reference level named in the question"
    label = "Silver Bullet window" if "silver bullet" in q else None
    window_text = f"{window_start}-{window_end} {timezone}"

    hypothesis = hypothesis or (
        f"On {instrument}, price trades to {level_text} during the {window_text} window "
        f"on more sessions than it does in a comparable baseline window."
    )
    observable_condition = observable_condition or (
        f"Within {window_text}, at least one {instrument} price print touches or crosses "
        f"{level_text} (touch rule and tolerance defined by the user before testing)."
    )
    invalidation_condition = invalidation_condition or (
        f"Over the agreed sample, the touch rate inside {window_text} is not higher than the "
        f"baseline window's touch rate by the pre-agreed margin, or the result does not hold "
        f"out of sample."
    )
    required_evidence = required_evidence or [
        f"Intraday {instrument} OHLC data (e.g. 1-minute) with timestamps converted to {timezone}",
        f"The value of {level_text} for each session in the sample",
        f"Per-session flag: condition met inside {window_text} (yes/no)",
        "Same flag for a baseline window of equal length on the same sessions",
        "Sample definition (date range, session filters, excluded days) fixed before testing",
        "Touch-rate comparison with counts, plus an out-of-sample check",
    ]
    return ResearchHypothesis(
        question=question,
        hypothesis=hypothesis,
        instrument=instrument.upper(),
        observable_condition=observable_condition,
        invalidation_condition=invalidation_condition,
        measurement_window=MeasurementWindow(
            start=window_start, end=window_end, timezone=timezone, label=label,
        ),
        required_evidence=required_evidence,
    )


def hypothesis_json(question: str, **overrides) -> str:
    try:
        return build_hypothesis(question, **overrides).model_dump_json(exclude_none=True)
    except ValidationError as exc:
        return validation_error_json(ResearchHypothesis, exc)
    except (TypeError, ValueError) as exc:
        return json.dumps({"error": f"ResearchHypothesis: {exc}"})
