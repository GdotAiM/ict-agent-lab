"""Month-7 Slice 7: paper swing_ticket persistence.

Weekly horizon. Not session_ticket. Not an M9 candidate.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ftn.os.m7_contracts import Month7State, SwingTicket
from ftn.os.m7_osok import derive_month7_osok

ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "dispatch" / "out"


def _week_id(d: str) -> str:
    try:
        iso = date.fromisoformat(d).isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    except ValueError:
        return d


def path_for(symbol: str, d: str) -> Path:
    STORE.mkdir(parents=True, exist_ok=True)
    return STORE / f"swing_{_week_id(d)}_{symbol}.json"


def load_swing(symbol: str, d: str) -> SwingTicket | None:
    p = path_for(symbol, d)
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    return SwingTicket(
        id=raw.get("id") or "",
        kind=raw.get("kind") or "paper_swing",
        module=raw.get("module") or "OSOK",
        opened=raw.get("opened") or "",
        status=raw.get("status") or "open",
        origin=raw.get("origin") or "hermes_governance",
    )


def persist_swing(symbol: str, d: str, existing: SwingTicket | None = None) -> SwingTicket:
    if existing and existing.status == "open":
        return existing
    week = _week_id(d)
    ticket = SwingTicket(
        id=f"{week}-{symbol}-OSOK",
        kind="paper_swing",
        module="OSOK",
        opened=d,
        status="open",
        origin="hermes_governance",
    )
    path_for(symbol, d).write_text(
        json.dumps(
            {
                "id": ticket.id,
                "kind": ticket.kind,
                "module": ticket.module,
                "opened": ticket.opened,
                "status": ticket.status,
                "origin": ticket.origin,
            },
            indent=2,
        )
        + "\n"
    )
    return ticket


def derive_month7_swing(raw: dict, persist: bool = True) -> Month7State:
    base = derive_month7_osok(raw)
    symbol = raw.get("symbol") or raw.get("focus_pair") or ""
    d = raw.get("date") or ""
    existing = load_swing(symbol, d)
    ticket = existing
    if persist and base.osok_opportunity.flag and existing is None:
        ticket = persist_swing(symbol, d)
    elif persist and existing and existing.status == "open":
        ticket = existing
    elif not base.osok_opportunity.flag:
        ticket = existing  # do not close here; lifecycle later
        if existing is None:
            ticket = None
    return Month7State(
        dealing_range=base.dealing_range,
        ict_weekly_profile=base.ict_weekly_profile,
        manipulation_template=base.manipulation_template,
        ipda_window=base.ipda_window,
        lrlr=base.lrlr,
        intraweek_contrary=base.intraweek_contrary,
        osok_opportunity=base.osok_opportunity,
        swing_ticket=ticket,
        ict_guidance=base.ict_guidance,
    )
