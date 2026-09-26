"""Month-7 Slice 2: dealing range + IPDA from labeled arrays.

Does not name ict_weekly_profile.
"""

from __future__ import annotations

from ftn.os.m7_contracts import (
    DealingRange,
    IctWeeklyProfile,
    IntraweekContrary,
    IpdaWindow,
    Lrlr,
    ManipulationTemplate,
    Month7State,
    OsokOpportunity,
    parse_month7,
)


def _tf_from_id(aid: str | None) -> str:
    if not aid:
        return "none"
    a = aid.upper()
    if a.startswith("M_") or a.startswith("MN") or "MONTH" in a:
        return "monthly"
    if a.startswith("W_") or "WEEK" in a:
        return "weekly"
    if a.startswith("D_") or a.startswith("PD"):
        return "daily"
    if a.startswith("H4") or a.startswith("4H"):
        return "h4"
    return "none"


def _direction(raw: dict) -> str:
    inst = raw.get("pair_institutional") or {}
    return (
        (inst.get("sponsorship") or {}).get("weekly")
        or inst.get("state")
        or "unclear"
    )


def labeled_dealing_range(raw: dict) -> DealingRange:
    m7 = raw.get("month7") or raw.get("ict_week") or {}
    explicit = m7.get("dealing_range") or raw.get("dealing_range") or {}
    frm = explicit.get("from_array_id")
    to = explicit.get("to_array_id")
    if not frm:
        # labeled HTF: origin is the from-array when weekly/monthly
        origin = raw.get("origin_pd_array")
        if origin and _tf_from_id(origin) in {"monthly", "weekly"}:
            frm = origin
    if not to:
        targets = list(raw.get("opposing_target_arrays") or [])
        to = targets[0] if targets else None
    if not frm and not to:
        return DealingRange()
    direction = explicit.get("direction") or _direction(raw)
    if direction not in {"bullish", "bearish", "unclear"}:
        direction = "unclear"
    return DealingRange(
        from_array_id=frm,
        from_tf=explicit.get("from_tf") or _tf_from_id(frm),
        to_array_id=to,
        to_tf=explicit.get("to_tf") or _tf_from_id(to),
        direction=direction,
        origin="ict_source",
    )


def labeled_ipda(raw: dict) -> IpdaWindow:
    m7 = raw.get("month7") or raw.get("ict_week") or {}
    block = m7.get("ipda_window") if isinstance(m7.get("ipda_window"), dict) else {}
    days = block.get("days") if block else m7.get("ipda_window")
    if days is None:
        days = raw.get("ipda_days")
    if days not in (20, 40, 60):
        days = None
    return IpdaWindow(days=days, origin="ict_source")


def derive_month7_range(raw: dict) -> Month7State:
    """Fill dealing range + IPDA. Leave profile/template/OSOK as none unless already parsed provided state — then strip profile."""
    base = parse_month7(raw) or Month7State()
    return Month7State(
        dealing_range=labeled_dealing_range(raw),
        ict_weekly_profile=IctWeeklyProfile(),
        manipulation_template=ManipulationTemplate(),
        ipda_window=labeled_ipda(raw),
        lrlr=Lrlr(),
        intraweek_contrary=IntraweekContrary(),
        osok_opportunity=OsokOpportunity(),
        swing_ticket=None,
        ict_guidance=base.ict_guidance,
    )
