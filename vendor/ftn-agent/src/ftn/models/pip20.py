
"""Narrow PIP20. Consumes frozen MarketState only."""

from __future__ import annotations

from ftn.os.contracts import Candidate, MarketState

ASIA_SESSIONS = {"asia", "asia_ny_stops"}
NY_SESSIONS = {"ny", "ny_am", "ny_expansion"}


def evaluate_pip20(state: MarketState) -> dict:
    ctx = state.context
    ev = ctx.evidence or {}
    profile = ctx.profile
    iof = ctx.pair_institutional.state
    raid = ev.get("raid") or {}
    raid_taken = bool(raid.get("taken"))
    session = ev.get("session") or ""
    window = ev.get("pip20_window")
    if window not in {"asia_ny_stops", "ny_expansion"}:
        if session in ASIA_SESSIONS:
            window = "asia_ny_stops"
        elif session in NY_SESSIONS:
            window = "ny_expansion"
        else:
            window = None

    adr = ctx.adr5 or {}
    remaining = adr.get("remaining")
    adr_ok = remaining is None or float(remaining) >= 20
    profile_ok = profile not in {"unclear", "consolidation", "reversal_watch"}
    iof_ok = iof in {"bullish", "bearish"}

    eligible = bool(profile_ok and iof_ok and window and raid_taken and adr_ok)

    if not profile_ok:
        cand = Candidate("PIP20", "ineligible", False, f"profile={profile}", "hermes_interpretation")
    elif not window:
        cand = Candidate("PIP20", "ineligible", False, "no_pip20_window", "ict_source")
    elif not raid_taken:
        cand = Candidate("PIP20", "ineligible", False, "no_raid_in_window", "ict_source")
    elif not adr_ok:
        cand = Candidate("PIP20", "ineligible", False, "adr_remaining_lt_20", "hermes_interpretation")
    elif eligible:
        cand = Candidate("PIP20", "unevaluated", True, f"window={window}", "ict_source")
    else:
        cand = Candidate("PIP20", "ineligible", False, "missing_iof_or_context", "ict_source")

    return {
        "candidate": cand,
        "window": window,
        "objective_pips": 20,
        "stop_pips": 20,
        "eligibility": {
            "profile_ok": profile_ok,
            "iof_ok": iof_ok,
            "window": window,
            "raid_taken": raid_taken,
            "adr_remaining": remaining,
        },
        "evidence": {"session": session, "raid": raid, "fingerprint": state.fingerprint},
    }
