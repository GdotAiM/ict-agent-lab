"""Month-7 Slice 4: manipulation template as a separate field.

Does not overwrite ict_weekly_profile.
Does not set OSOK or swing_ticket.
"""

from __future__ import annotations

from ftn.os.m7_contracts import ManipulationTemplate, Month7State, MANIPULATION_TEMPLATES
from ftn.os.m7_profile import derive_month7_profile, read_week_path


_POOL = {
    "liquidity_pool",
    "old_high_retest",
    "old_low_retest",
    "bullish_order_block",
    "bearish_order_block",
}


def _explicit_pool(raw: dict) -> str:
    ev = raw.get("evidence") or {}
    p = ev.get("week_path") or raw.get("week_path") or {}
    pool = (p.get("pool") or p.get("template_mechanism") or "").lower()
    return pool if pool in _POOL else ""


def classify_template(profile_name: str, path: dict, explicit_pool: str) -> tuple[str, str]:
    if profile_name == "none":
        return "none", "no_weekly_profile"
    pool = explicit_pool
    if not pool:
        if path.get("ran_htf_discount_on") or path.get("ran_htf_premium_on"):
            pool = "liquidity_pool"
        else:
            return "none", "no_template_mechanism"
    family = {
        "classic_tuesday_low_of_week": "classic_tuesday_low",
        "classic_tuesday_high_of_week": "classic_tuesday_high",
        "wednesday_low_of_week": "wednesday_low",
        "wednesday_high_of_week": "wednesday_high",
    }.get(profile_name)
    if not family:
        # later profiles: template name may equal profile name if in glossary
        if profile_name in MANIPULATION_TEMPLATES:
            return profile_name, "profile_as_template_family"
        return "none", "no_template_family"
    suffix = {
        "liquidity_pool": "liquidity_pool",
        "old_high_retest": "old_high_retest",
        "old_low_retest": "old_low_retest",
        "bullish_order_block": "bullish_order_block",
        "bearish_order_block": "bearish_order_block",
    }[pool]
    # reject mismatched OB side
    if family.endswith("low") and suffix == "bearish_order_block":
        return "none", "ob_side_mismatch"
    if family.endswith("high") and suffix == "bullish_order_block":
        return "none", "ob_side_mismatch"
    if family.endswith("low") and suffix == "old_low_retest":
        suffix = "old_high_retest"
    if family.endswith("high") and suffix == "old_high_retest":
        suffix = "old_low_retest"
    name = f"{family}_{suffix}"
    if name not in MANIPULATION_TEMPLATES:
        return "none", "not_in_glossary"
    return name, "path_mechanism"


def derive_month7_template(raw: dict) -> Month7State:
    base = derive_month7_profile(raw)
    name, why = classify_template(
        base.ict_weekly_profile.name,
        read_week_path(raw),
        _explicit_pool(raw),
    )
    tf = "weekly"
    return Month7State(
        dealing_range=base.dealing_range,
        ict_weekly_profile=base.ict_weekly_profile,
        manipulation_template=ManipulationTemplate(name=name, pool_tf=tf if name != "none" else "none", origin="ict_source"),
        ipda_window=base.ipda_window,
        lrlr=base.lrlr,
        intraweek_contrary=base.intraweek_contrary,
        osok_opportunity=base.osok_opportunity,
        swing_ticket=None,
        ict_guidance=base.ict_guidance,
    )
