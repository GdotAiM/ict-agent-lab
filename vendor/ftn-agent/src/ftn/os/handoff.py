"""DayContext handoff transport.

Kernel writes; consumers (Hermes-X, Desk) must not write Market State.
handoff.v1 is transport only — not a second domain model.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ftn.os.contracts import MarketState

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "dispatch" / "out"

SCHEMA_VERSION = "1"
KIND_V1 = "day_context_handoff"
# Legacy label retained in notes only — do not emit as primary kind.
LEGACY_KIND = "month9_handoff"


def _opt_asdict(obj):
    if obj is None:
        return None
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj


def build_handoff(state: MarketState, candidates, ftn: dict) -> dict:
    """Serialize DayContext snapshot for read-only consumers.

    schemaVersion + kind identify the transport contract.
    PAM1 evidence/completeness are intelligence projections, not orders.
    Forbidden signal fields (BUY/SELL/confidence/rank/broker) are never written.
    """
    c = state.context
    ticket = asdict(c.session_ticket) if c.session_ticket else None
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": KIND_V1,
        "producer": "ftn-agent",
        "consumer": "hermes-x|hermes-desk",
        "mode": "paper",
        "fingerprint": state.fingerprint,
        "symbol": c.symbol,
        "date": c.date,
        "session": (c.evidence or {}).get("session"),
        "market_state": {
            "sentiment": asdict(c.sentiment),
            "institutional": asdict(c.pair_institutional),
            "dxy": c.dxy,
            "profile": c.profile,
            "origin_pd_array": c.origin_pd_array,
            "opposing_target_arrays": list(c.opposing_target_arrays),
            "opens": c.opens,
            "scenarios": c.scenarios,
            "month1": asdict(c.month1) if c.month1 else None,
            "month2": asdict(c.month2) if c.month2 else None,
            "month3": asdict(c.month3) if c.month3 else None,
            "month4": asdict(c.month4) if c.month4 else None,
            "month5": asdict(c.month5) if c.month5 else None,
            "month6": asdict(c.month6) if c.month6 else None,
            "month7": asdict(c.month7) if c.month7 else None,
            "month8": asdict(c.month8) if c.month8 else None,
            "month10": asdict(c.month10) if c.month10 else None,
            "month11": asdict(c.month11) if c.month11 else None,
            "month12": asdict(c.month12) if c.month12 else None,
            "charter": asdict(c.charter) if c.charter else None,
            "pam1_evidence": _opt_asdict(getattr(c, "pam1_evidence", None)),
            "pam1_completeness": _opt_asdict(getattr(c, "pam1_completeness", None)),
        },
        "candidates": [
            {
                "module": x.module,
                "state": x.state,
                "eligible": x.eligible,
                "reason": x.reason,
                "origin": x.origin,
            }
            for x in candidates
        ],
        "ftn_annotation": {
            "family": ftn.get("family"),
            "bias": ftn.get("bias"),
            "four": ftn.get("four") or [],
        },
        "session_ticket": ticket,
        "contrary": (c.scenarios or {}).get("contrary"),
        "notes": [
            "Transport only: DayContext snapshot for research projection.",
            "Consumers must not mutate Market State or invent ICT rules.",
            "PAM recognition and completeness are not execution instructions.",
            f"Legacy kind was '{LEGACY_KIND}'; primary kind is '{KIND_V1}'.",
            "Forbidden as signal fields: trade direction recommendation, model ranking, broker command.",
        ],
    }


def write_handoff(state: MarketState, candidates, ftn: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = build_handoff(state, candidates, ftn)
    blob = json.dumps(payload, indent=2, default=str) + "\n"
    path = OUT / f"handoff_{c_date(state)}.json"
    latest = OUT / "handoff_latest.json"
    written = None
    for dest in (path, latest):
        try:
            dest.write_text(blob)
            written = dest
        except OSError:
            continue
    return written


def c_date(state: MarketState) -> str:
    ev = (state.context.evidence or {}).get("session") or "unknown"
    return f"{state.context.date}_{state.context.symbol}_{ev}"
