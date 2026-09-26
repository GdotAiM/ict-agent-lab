
"""MINT paper draft. Tickets ≠ orders. No broker call."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "dispatch" / "out"

SIDE = {
    "REV": None,  # filled from sentiment/iof
}


def draft_from_handoff(handoff: dict) -> dict | None:
    selected = next((c for c in handoff.get("candidates") or [] if c.get("state") == "selected"), None)
    if not selected:
        return None
    ms = handoff.get("market_state") or {}
    iof = ((ms.get("institutional") or {}).get("state"))
    sent = ((ms.get("sentiment") or {}).get("direction"))
    module = selected["module"]
    if module == "REV":
        side = "buy" if iof == "bullish" else "sell" if iof == "bearish" else None
    elif module in {"BB", "PIP20"}:
        side = "buy" if iof == "bullish" else "sell"
    elif module == "CONSO":
        side = "buy" if iof == "bullish" else "sell"
    else:
        side = None
    ticket = handoff.get("session_ticket") or {}
    return {
        "kind": "mint_paper_draft",
        "mode": "paper",
        "actionable_for_mint": False,
        "requires": ["RISK", "allowlist", "human_ack"],
        "from": "ftn-agent",
        "to": "mint-agent",
        "symbol": handoff.get("symbol"),
        "date": handoff.get("date"),
        "session": handoff.get("session"),
        "side": side,
        "module": module,
        "reason": selected.get("reason"),
        "origin": selected.get("origin"),
        "fingerprint": handoff.get("fingerprint"),
        "session_ticket_id": ticket.get("id"),
        "contrary": handoff.get("contrary"),
        "ftn_objectives": (handoff.get("ftn_annotation") or {}).get("four") or [],
        "notes": "Draft only. mint-agent must not route until dual unlock + RISK.",
    }


def write_draft(handoff: dict) -> Path | None:
    draft = draft_from_handoff(handoff)
    if not draft:
        return None
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"mint_draft_{handoff.get('date')}_{handoff.get('symbol')}.json"
    blob = json.dumps(draft, indent=2) + "\n"
    try:
        path.write_text(blob)
    except OSError:
        pass
    latest = OUT / "mint_draft_latest.json"
    try:
        latest.write_text(blob)
        return latest
    except OSError:
        return path
