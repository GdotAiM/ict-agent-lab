
"""Calendar → focus pair. ICT: med/high in London or NY KZ. Else watchlist. Else idle."""

from __future__ import annotations

KZ = {"london", "ny", "ny_am", "ny_pm", "london_close"}
IMPACT = {"medium", "high"}


def pick_focus(calendar: list, watchlist: list, fallback: str | None = None) -> dict:
    events = []
    for ev in calendar or []:
        impact = str(ev.get("impact", "")).lower()
        kz = str(ev.get("killzone", "")).lower()
        if impact in IMPACT and kz in KZ and ev.get("pair"):
            events.append(ev)
    if events:
        pair = events[0]["pair"]
        return {"focus_pair": pair, "source": "calendar", "event": events[0], "idle": False}
    if watchlist:
        return {"focus_pair": watchlist[0], "source": "watchlist", "event": None, "idle": False}
    return {"focus_pair": fallback, "source": "idle", "event": None, "idle": True}
