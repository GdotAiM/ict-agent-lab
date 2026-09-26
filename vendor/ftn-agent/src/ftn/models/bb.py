
"""Narrow BB. Consumes frozen MarketState only."""

from __future__ import annotations

from ftn.os.contracts import Candidate, MarketState

PROTRACTIONS = ("ny_midnight", "cme_0820", "london_close_1000", "gmt_0000")


def evaluate_bb(state: MarketState) -> dict:
    ctx = state.context
    ev = ctx.evidence or {}
    iof = ctx.pair_institutional.state
    sent = ctx.sentiment.direction
    judas = ctx.sentiment.judas_side
    raid = ev.get("raid") or {}
    raid_taken = bool(raid.get("taken"))
    session = ev.get("session") or ""
    stage = ev.get("protraction_stage") or "none"
    if stage not in PROTRACTIONS and session == "london":
        stage = "gmt_0000"

    side = None
    if iof == "bullish" and sent in {"bullish", "unclear"}:
        side = "buy"
    elif iof == "bearish" and sent in {"bearish", "unclear"}:
        side = "sell"

    # offset = soup in the IOF direction (bullish + sell-side/low raid)
    engine = None
    if ev.get("bb_engine") in {"offset", "reacc"}:
        engine = ev.get("bb_engine")
    elif raid_taken and side == "buy" and judas == "sell_side":
        engine = "offset"
    elif raid_taken and side == "sell" and judas == "buy_side":
        engine = "offset"
    elif (not raid_taken) and ev.get("ote") and side:
        engine = "reacc"

    waiting = bool(side and judas not in {None, "none"} and not raid_taken and engine is None)
    eligible = engine is not None

    if eligible:
        cand = Candidate("BB", "unevaluated", True, f"engine={engine}", "ict_source")
    elif waiting:
        cand = Candidate("BB", "unevaluated", False, "waiting_judas_completion", "ict_source")
    else:
        cand = Candidate("BB", "ineligible", False, "missing_iof_or_judas_or_engine", "ict_source")

    return {
        "candidate": cand,
        "engine": engine,
        "side": side,
        "protraction_stage": stage,
        "eligibility": {
            "iof": iof,
            "sentiment": sent,
            "judas": judas,
            "raid_taken": raid_taken,
            "engine": engine,
            "waiting_judas": waiting,
        },
        "evidence": {"raid": raid, "session": session, "fingerprint": state.fingerprint},
    }
