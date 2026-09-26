"""Month-7 Slice 3: ICT weekly profile from week-to-date path + HTF bias.

Range + bias alone must not name a profile.
Does not set OSOK or swing_ticket.
"""

from __future__ import annotations

from ftn.os.m7_contracts import IctWeeklyProfile, Month7State
from ftn.os.m7_range import derive_month7_range


def _bias(raw: dict) -> str:
    inst = raw.get("pair_institutional") or {}
    return (inst.get("sponsorship") or {}).get("weekly") or inst.get("state") or "unclear"


def read_week_path(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    p = ev.get("week_path") or raw.get("week_path") or {}
    return {
        "extreme_low_day": (p.get("extreme_low_day") or "").lower(),
        "extreme_high_day": (p.get("extreme_high_day") or "").lower(),
        "ran_htf_discount_on": (p.get("ran_htf_discount_on") or "").lower(),
        "ran_htf_premium_on": (p.get("ran_htf_premium_on") or "").lower(),
        "monday_hovered_above_discount": bool(p.get("monday_hovered_above_discount")),
        "monday_hovered_below_premium": bool(p.get("monday_hovered_below_premium")),
    }


def classify_weekly_profile(bias: str, path: dict) -> tuple[str, str]:
    if not any(path.values()):
        return "none", "no_week_path"
    low = path.get("extreme_low_day")
    high = path.get("extreme_high_day")
    if bias == "bullish":
        if low == "tuesday" and path.get("ran_htf_discount_on") == "tuesday":
            return "classic_tuesday_low_of_week", "tue_low_into_htf_discount"
        if low == "wednesday" and path.get("ran_htf_discount_on") == "wednesday":
            return "wednesday_low_of_week", "wed_low_into_htf_discount"
        return "none", "bullish_path_insufficient"
    if bias == "bearish":
        if high == "tuesday" and path.get("ran_htf_premium_on") == "tuesday":
            return "classic_tuesday_high_of_week", "tue_high_into_htf_premium"
        if high == "wednesday" and path.get("ran_htf_premium_on") == "wednesday":
            return "wednesday_high_of_week", "wed_high_into_htf_premium"
        return "none", "bearish_path_insufficient"
    return "none", "bias_unclear"


def derive_month7_profile(raw: dict) -> Month7State:
    base = derive_month7_range(raw)
    name, why = classify_weekly_profile(_bias(raw), read_week_path(raw))
    state = "watching" if name != "none" else "none"
    return Month7State(
        dealing_range=base.dealing_range,
        ict_weekly_profile=IctWeeklyProfile(name=name, state=state, origin="ict_source"),
        manipulation_template=base.manipulation_template,
        ipda_window=base.ipda_window,
        lrlr=base.lrlr,
        intraweek_contrary=base.intraweek_contrary,
        osok_opportunity=base.osok_opportunity,
        swing_ticket=None,
        ict_guidance=base.ict_guidance,
    )
