"""Month-7 Slice 6: OSOK opportunity + intraweek contrary.

High LRLR refuses OSOK. Does not mint swing_ticket.
Does not touch M8 London.
"""

from __future__ import annotations

from ftn.os.m7_contracts import IntraweekContrary, Month7State, OsokOpportunity
from ftn.os.m7_lrlr import derive_month7_lrlr


def read_contrary(raw: dict) -> IntraweekContrary:
    ev = raw.get("evidence") or {}
    path = ev.get("week_path") or raw.get("week_path") or {}
    m7 = raw.get("month7") or {}
    src = path.get("contrary") or ev.get("intraweek_contrary") or m7.get("intraweek_contrary")
    if isinstance(src, dict):
        state = src.get("state")
        origin = src.get("origin") or "ict_source"
    else:
        state = src
        origin = "ict_source"
    if state not in {"watch", "confirmed", "none"}:
        state = "none"
    return IntraweekContrary(state=state, origin=origin)


def classify_osok(st: Month7State) -> OsokOpportunity:
    if st.ict_weekly_profile.name == "none":
        return OsokOpportunity(flag=False, reason="no_weekly_profile")
    if st.lrlr.state == "high":
        return OsokOpportunity(flag=False, reason="lrlr_high")
    if st.lrlr.state != "low":
        return OsokOpportunity(flag=False, reason="lrlr_not_low")
    if st.intraweek_contrary.state == "confirmed":
        return OsokOpportunity(flag=False, reason="intraweek_contrary_confirmed")
    if not st.dealing_range.from_array_id or not st.dealing_range.to_array_id:
        return OsokOpportunity(flag=False, reason="no_dealing_range")
    return OsokOpportunity(flag=True, reason="profile_plus_lrlr_low")


def derive_month7_osok(raw: dict) -> Month7State:
    base = derive_month7_lrlr(raw)
    contrary = read_contrary(raw)
    tmp = Month7State(
        dealing_range=base.dealing_range,
        ict_weekly_profile=base.ict_weekly_profile,
        manipulation_template=base.manipulation_template,
        ipda_window=base.ipda_window,
        lrlr=base.lrlr,
        intraweek_contrary=contrary,
        osok_opportunity=base.osok_opportunity,
        swing_ticket=None,
        ict_guidance=base.ict_guidance,
    )
    osok = classify_osok(tmp)
    return Month7State(
        dealing_range=tmp.dealing_range,
        ict_weekly_profile=tmp.ict_weekly_profile,
        manipulation_template=tmp.manipulation_template,
        ipda_window=tmp.ipda_window,
        lrlr=tmp.lrlr,
        intraweek_contrary=tmp.intraweek_contrary,
        osok_opportunity=osok,
        swing_ticket=None,
        ict_guidance=tmp.ict_guidance,
    )
