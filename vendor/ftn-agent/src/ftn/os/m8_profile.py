
"""Month-8 Slice 3: ICT London profile from post-00:00 NY path + IOF.

Ideal CBDR + bearish IOF alone must not name a profile.
"""

from __future__ import annotations

from ftn.os.m8_contracts import Month8State, LondonProfile
from ftn.os.m8_detect import derive_month8_measures
from ftn.os.m8_project import project_daily_extreme
from ftn.os.m8_htf import annotate_htf_overlap


def _iof(raw: dict) -> str:
    inst = raw.get("pair_institutional") or {}
    return inst.get("state") or (inst.get("daytrade_iof") or {}).get("daily") or "unclear"


def read_path(raw: dict) -> dict:
    ev = raw.get("evidence") or {}
    path = ev.get("path_after_anchor") or raw.get("path_after_anchor") or {}
    return {
        "anchor": path.get("anchor") or "00:00",
        "first_move": path.get("first_move"),  # up | down | none
        "window": path.get("window") or "",
        "higher_high_vs_asian_or_cbdr": bool(path.get("higher_high_vs_asian_or_cbdr")),
        "lower_low_vs_asian_or_cbdr": bool(path.get("lower_low_vs_asian_or_cbdr")),
        "move_started_by_0200": path.get("move_started_by_0200"),
    }


def classify_london_profile(iof: str, path: dict, gate_allowed: bool) -> tuple[str, str]:
    if not gate_allowed:
        return "none", "london_not_allowed"
    first = path.get("first_move")
    if not first or first == "none":
        return "none", "no_post_anchor_path"
    early = path.get("move_started_by_0200")
    if early is None:
        early = path.get("window") in {"00:00-02:00", "00:00-02:00 NY"}
    if iof == "bearish" and first == "up":
        if path.get("higher_high_vs_asian_or_cbdr") and early:
            return "normal_protraction_sell", "post_anchor_rally_then_iof"
        if path.get("higher_high_vs_asian_or_cbdr") and not early:
            return "delayed_protraction_sell", "late_protraction_then_iof"
        return "none", "insufficient_range_take"
    if iof == "bullish" and first == "down":
        if path.get("lower_low_vs_asian_or_cbdr") and early:
            return "normal_protraction_buy", "post_anchor_decline_then_iof"
        if path.get("lower_low_vs_asian_or_cbdr") and not early:
            return "delayed_protraction_buy", "late_protraction_then_iof"
        return "none", "insufficient_range_take"
    return "none", "path_does_not_match_iof"


def derive_month8_profile(raw: dict) -> Month8State:
    base = derive_month8_measures(raw)
    path = read_path(raw)
    iof = _iof(raw)
    profile, why = classify_london_profile(iof, path, base.london_session_gate.allowed)
    proj = project_daily_extreme(base.cbdr, iof)
    # frozen replace via constructor
    return Month8State(
        ict_true_day=base.ict_true_day,
        cbdr=base.cbdr,
        asian_height_pips=base.asian_height_pips,
        london_session_gate=base.london_session_gate,
        ict_london_profile=profile,  # type: ignore[arg-type]
        daily_extreme_projection=proj,
        daytrade_opportunity=profile != "none" and base.london_session_gate.allowed,
        htf_entry_overlap=annotate_htf_overlap(raw),
        ict_guidance=base.ict_guidance,
    )
