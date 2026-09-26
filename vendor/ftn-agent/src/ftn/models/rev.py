
"""Slice 4 — narrow REV. Consumes frozen MarketState only."""

from __future__ import annotations

from ftn.os.contracts import Candidate, MarketState

NAMED = {"pdh", "pdl", "week_so_far_high", "week_so_far_low", "ith", "itl"}


def evaluate_rev(state: MarketState) -> dict:
    ctx = state.context
    ev = ctx.evidence or {}
    raid = ev.get("raid") or {}
    named = set((ctx.ranges or {}).get("named_extremes") or {})
    raid_taken = bool(raid.get("taken"))
    level = raid.get("level")
    raid_named = level in named or level in NAMED
    htf = ev.get("htf_pd_at_raid") or ctx.origin_pd_array
    session_exception = ev.get("session") in {"ny_am", "london_close"} and bool(htf)
    iof_ok = ctx.pair_institutional.state != "unclear"
    mss = bool(ev.get("mss"))

    eligibility = {
        "named_extreme_raid": raid_taken and raid_named,
        "htf_pd_at_or_around_raid": bool(htf),
        "contextual_exception": bool(session_exception),
        "institutional_context_clear": iof_ok,
    }
    eligible = eligibility["named_extreme_raid"] and (
        eligibility["htf_pd_at_or_around_raid"] or eligibility["contextual_exception"]
    ) and eligibility["institutional_context_clear"]

    execution = {"mss_or_displacement": mss, "confirmed": eligible and mss}

    if execution["confirmed"]:
        cand = Candidate("REV", "selected", True, "named_extreme_raid+htf_pd+mss", "hermes_interpretation")
    elif eligible:
        cand = Candidate("REV", "unevaluated", True, "eligible_waiting_mss", "ict_source")
    else:
        cand = Candidate("REV", "ineligible", False, "no_named_extreme_plus_htf_context", "ict_source")

    return {
        "candidate": cand,
        "eligibility": eligibility,
        "execution": execution,
        "evidence": {
            "raid": raid,
            "htf_pd": htf,
            "session": ev.get("session"),
            "mss": mss,
            "fingerprint": state.fingerprint,
        },
    }
