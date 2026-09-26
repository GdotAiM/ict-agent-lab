
"""Narrow CONSO. Consumes frozen MarketState only."""

from __future__ import annotations

from ftn.os.contracts import Candidate, MarketState


def evaluate_conso(state: MarketState) -> dict:
    ctx = state.context
    ev = ctx.evidence or {}
    box = ev.get("box")
    iof = ctx.pair_institutional.state
    raid = ev.get("raid") or {}
    raid_taken = bool(raid.get("taken"))
    raid_px = raid.get("price")
    play = None
    target = None

    if not box or iof == "unclear":
        cand = Candidate("CONSO", "ineligible", False, "box_null" if not box else "iof_unclear", "ict_source")
        return {"candidate": cand, "play": None, "target": None, "eligibility": {"box": bool(box), "iof": iof}}

    high, low = box.get("high"), box.get("low")
    eq = None
    if high is not None and low is not None:
        eq = (high + low) / 2

    # fade: raid of the IOF-opposed edge
    fade_edge = None
    if iof == "bullish":
        fade_edge = low
    elif iof == "bearish":
        fade_edge = high

    at_fade = (
        raid_taken
        and fade_edge is not None
        and raid_px is not None
        and abs(float(raid_px) - float(fade_edge)) < 1e-6
    )
    displacement_inside = bool(ev.get("displacement_inside_box"))
    left_box = bool(ev.get("left_box"))

    if at_fade:
        play, target = "fade_edge", "eq"
    elif displacement_inside:
        play, target = "expansion_inside", "opposite_side"
    elif left_box:
        play, target = "breakout_use", "next_pd_or_ftn"
    else:
        play = None

    eligible = play is not None
    cand = Candidate(
        "CONSO",
        "unevaluated" if eligible else "ineligible",
        eligible,
        play or "box_present_no_play",
        "ict_source",
    )
    return {
        "candidate": cand,
        "play": play,
        "target": target,
        "eq": eq,
        "eligibility": {
            "box": True,
            "iof": iof,
            "at_fade_edge": at_fade,
            "displacement_inside": displacement_inside,
            "left_box": left_box,
        },
        "evidence": {"box": box, "raid": raid, "fingerprint": state.fingerprint},
    }
