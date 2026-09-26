
"""Month-8 Slice 6: HTF overlap annotation.

Marks when the day-trade idea sits on an HTF PD array.
Never changes size, caps, candidate priority, or session tickets.
"""

from __future__ import annotations

from ftn.os.m8_contracts import HtfOverlap


def annotate_htf_overlap(raw: dict) -> HtfOverlap:
    origin = raw.get("origin_pd_array")
    if not origin:
        daily = (((raw.get("pd_matrix") or {}).get("htf") or {}).get("daily") or [])
        if daily:
            first = daily[0]
            origin = first.get("id") if isinstance(first, dict) else None
    if not origin:
        return HtfOverlap()
    # relationship is always seed_only — lecture 8, signed essence
    tf = "daily"
    if isinstance(origin, str) and origin.startswith("W_"):
        tf = "weekly"
    elif isinstance(origin, str) and origin.startswith("M_"):
        tf = "monthly"
    return HtfOverlap(
        present=True,
        array_id=str(origin),
        timeframe=tf,
        relationship="seed_only",
        origin="ict_source",
    )
