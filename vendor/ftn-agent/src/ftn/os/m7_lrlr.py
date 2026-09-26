"""Month-7 Slice 5: LRLR state.

High resistance may later gate OSOK (Slice 6).
Must never write Month-8 london_session_gate.
"""

from __future__ import annotations

from ftn.os.m7_contracts import Lrlr, Month7State
from ftn.os.m7_template import derive_month7_template


def read_lrlr(raw: dict) -> Lrlr:
    ev = raw.get("evidence") or {}
    path = ev.get("week_path") or raw.get("week_path") or {}
    m7 = raw.get("month7") or {}
    src = path.get("lrlr") or ev.get("lrlr") or m7.get("lrlr") or raw.get("lrlr")
    if isinstance(src, dict):
        state = src.get("state")
        origin = src.get("origin") or "ict_source"
    else:
        state = src
        origin = "ict_source"
    if state not in {"low", "high", "unclear"}:
        state = "unclear"
    return Lrlr(state=state, origin=origin)


def derive_month7_lrlr(raw: dict) -> Month7State:
    base = derive_month7_template(raw)
    return Month7State(
        dealing_range=base.dealing_range,
        ict_weekly_profile=base.ict_weekly_profile,
        manipulation_template=base.manipulation_template,
        ipda_window=base.ipda_window,
        lrlr=read_lrlr(raw),
        intraweek_contrary=base.intraweek_contrary,
        osok_opportunity=base.osok_opportunity,  # still false until Slice 6
        swing_ticket=None,
        ict_guidance=base.ict_guidance,
    )
