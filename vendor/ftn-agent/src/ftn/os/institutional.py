
"""Daytrade IOF state from TF evidence. Monthly/weekly never vote."""

from __future__ import annotations

from ftn.os.contracts import DaytradeIof, InstitutionalContext, TfBias


def derive_daytrade(daily: str, h4: str, m60: str) -> tuple[str, str, tuple]:
    notes = []
    if daily == "unclear":
        return "unclear", "unclear", tuple(notes)
    if daily == h4:
        if m60 == daily or m60 == "unclear":
            return daily, "aligned", tuple(notes)
        notes.append("m60_countertrend")
        return daily, "qualified", tuple(notes)
    if h4 == "unclear":
        return daily, "qualified", tuple(notes)
    return "unclear", "conflicted", tuple(notes)


def build_institutional(raw: dict) -> InstitutionalContext:
    block = raw.get("pair_institutional") or raw.get("institutional") or {}
    sp = block.get("sponsorship") or {}
    dt = block.get("daytrade_iof") or {}
    daily = dt.get("daily", "unclear")
    h4 = dt.get("h4", "unclear")
    m60 = dt.get("m60", "unclear")
    state, conf, notes = derive_daytrade(daily, h4, m60)
    return InstitutionalContext(
        sponsorship=TfBias(
            monthly=sp.get("monthly", "not_scored"),
            weekly=sp.get("weekly", "not_scored"),
            daily=sp.get("daily", "unclear"),
            h4=sp.get("h4", "unclear"),
        ),
        daytrade_iof=DaytradeIof(daily=daily, h4=h4, m60=m60),
        state=state,
        confidence=conf,
        notes=notes,
    )
