
"""Session clocks → protraction stage and PIP20 window."""

from __future__ import annotations


def _hhmm(clock: str | None) -> tuple[int, int] | None:
    if not clock:
        return None
    parts = str(clock).strip().split(":")
    try:
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return None


def session_clocks(session: str | None, clock: str | None = None) -> dict:
    session = (session or "").lower()
    hm = _hhmm(clock)
    stage = "none"
    window = None

    if hm:
        h, m = hm
        minutes = h * 60 + m
        if minutes == 0:
            stage = "gmt_0000"
        elif minutes == 20 * 60 + 20 or (h == 8 and m == 20):
            stage = "cme_0820"
        elif h == 10 and m == 0:
            stage = "london_close_1000"
        elif h == 0 and m == 0:
            stage = "ny_midnight"
        elif 19 * 60 <= minutes or minutes <= 15:
            stage = "ny_midnight"

        if 19 * 60 <= minutes or minutes <= 5:
            window = "asia_ny_stops"
        elif 7 * 60 <= minutes <= 10 * 60:
            window = "ny_expansion"

    if stage == "none":
        if session in {"london"}:
            stage = "gmt_0000"
        elif session in {"ny", "ny_am"}:
            stage = "cme_0820"
        elif session in {"london_close", "lc"}:
            stage = "london_close_1000"
        elif session in {"asia"}:
            stage = "ny_midnight"

    if window is None:
        if session in {"asia", "asia_ny_stops"}:
            window = "asia_ny_stops"
        elif session in {"ny", "ny_am", "ny_expansion"}:
            window = "ny_expansion"

    return {"protraction_stage": stage, "pip20_window": window, "source": "clocks"}
