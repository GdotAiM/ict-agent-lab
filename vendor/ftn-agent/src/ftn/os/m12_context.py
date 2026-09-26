"""Month-12 Slice 2: labeled top-down context.

Does not derive top_down.
Does not write pair_institutional or session_ticket.
Does not inspect raw month1–11.
"""

from __future__ import annotations

from ftn.os.m12_contracts import Month12State, PRES, TopDown, _one


def _block(raw: dict):
    ev = raw.get("evidence") or {}
    m12 = raw.get("month12") or raw.get("ict_top_down") or {}
    return ev, m12


def derive_month12_context(raw: dict) -> Month12State:
    ev, m12 = _block(raw)
    src = ev.get("month12") or ev or m12
    return Month12State(
        long_term_note=_one(src.get("long_term_note") or m12.get("long_term_note"), PRES),
        intermediate_term_note=_one(
            src.get("intermediate_term_note") or m12.get("intermediate_term_note"), PRES
        ),
        short_term_note=_one(src.get("short_term_note") or m12.get("short_term_note"), PRES),
        intraday_note=_one(src.get("intraday_note") or m12.get("intraday_note"), PRES),
        identified_top_down=_one(
            src.get("identified_top_down") or m12.get("identified_top_down"), PRES
        ),
        top_down=TopDown(flag=False, reason="slice2_context_only"),
    )
