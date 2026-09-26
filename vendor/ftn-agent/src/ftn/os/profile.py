
"""Profile is hermes_interpretation, not an ICT enum."""

from __future__ import annotations


def derive_profile(raw: dict) -> str:
    ev = raw.get("evidence") or {}
    if ev.get("box"):
        return "consolidation"
    raid = ev.get("raid") or {}
    named = raid.get("level") in {
        "pdh", "pdl", "week_so_far_high", "week_so_far_low", "ith", "itl",
    }
    if raid.get("taken") and named and (ev.get("htf_pd_at_raid") or raw.get("origin_pd_array")):
        return "reversal_watch"
    if ev.get("pip20_window") or ev.get("session") in {"ny_am", "asia"}:
        return "continuation"
    if ev.get("left_box"):
        return "expansion"
    return "unclear"
