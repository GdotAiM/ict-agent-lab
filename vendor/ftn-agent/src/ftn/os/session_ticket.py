
"""Hermes governance: one entry ticket per session per pair."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ftn.os.contracts import DayContext, SessionTicket

ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "dispatch" / "out"


def _key(ctx: DayContext) -> str:
    session = (ctx.evidence or {}).get("session") or "unknown"
    return f"session_{ctx.date}_{ctx.symbol}_{session}.json"


def path_for(ctx: DayContext) -> Path:
    STORE.mkdir(parents=True, exist_ok=True)
    return STORE / _key(ctx)


def load_ticket(ctx: DayContext) -> SessionTicket | None:
    p = path_for(ctx)
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    return SessionTicket(
        id=raw["id"],
        kind=raw["kind"],
        module=raw["module"],
        session=raw["session"],
    )


def attach_ticket(ctx: DayContext) -> DayContext:
    existing = load_ticket(ctx)
    if existing is None:
        return ctx
    return replace(ctx, session_ticket=existing)


def persist_ticket(ctx: DayContext, module: str, kind: str = "paper_entry") -> SessionTicket:
    session = (ctx.evidence or {}).get("session") or "unknown"
    ticket = SessionTicket(
        id=f"{ctx.date}-{ctx.symbol}-{session}-{module}",
        kind=kind,
        module=module,
        session=session,
    )
    path_for(ctx).write_text(
        json.dumps(
            {"id": ticket.id, "kind": ticket.kind, "module": ticket.module, "session": ticket.session},
            indent=2,
        )
        + "\n"
    )
    return ticket
