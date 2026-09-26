"""Charter Slice 1 contracts. Parse only. No detectors.

Supporting lecture notes are per recognized PAM (not aggregate),
so overlapping PAM recognition remains valid without shared mutable notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
PamId = Literal[
    "pam1", "pam2", "pam3", "pam4", "pam5", "pam6",
    "pam7", "pam8", "pam9", "pam10", "pam11", "pam12", "none",
]
Horizon = Literal[
    "intraday_scalp", "short_term", "swing", "position", "day",
    "universal", "monthly_target", "osok", "none",
]

PRES = set(Pres.__args__)
PAM_IDS = set(PamId.__args__) - {"none"}
HORIZONS = set(Horizon.__args__)

# Glossary convenience map (annotation only; does not mint recognition)
_HORIZON_OF: dict[str, Horizon] = {
    "pam1": "intraday_scalp",
    "pam12": "intraday_scalp",
    "pam2": "short_term",
    "pam3": "swing",
    "pam10": "swing",
    "pam4": "position",
    "pam5": "day",
    "pam11": "day",
    "pam6": "universal",
    "pam7": "universal",
    "pam8": "monthly_target",
    "pam9": "osok",
}


@dataclass(frozen=True)
class CharterRecognition:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class PamEntry:
    """One recognized (or listed) PAM with per-model supporting notes."""

    pam_id: PamId = "none"
    horizon: Horizon = "none"
    primary_lecture_note: Pres = "none"
    amplified_note: Pres = "none"
    trade_plan_note: Pres = "none"
    algorithmic_theory_note: Pres = "none"


@dataclass(frozen=True)
class CharterState:
    identified_pam: Pres = "none"
    recognized_pams: tuple = ()  # tuple[PamEntry, ...]
    model13_bridge: Pres = "none"
    charter_recognition: CharterRecognition = field(default_factory=CharterRecognition)


def _one(v, allowed):
    return v if v in allowed else "none"


def _entry(item: dict) -> PamEntry:
    pid = _one(item.get("pam_id"), PAM_IDS | {"none"})
    hz = _one(item.get("horizon"), HORIZONS)
    if hz == "none" and pid in _HORIZON_OF:
        hz = _HORIZON_OF[pid]
    return PamEntry(
        pam_id=pid,  # type: ignore[arg-type]
        horizon=hz,  # type: ignore[arg-type]
        primary_lecture_note=_one(item.get("primary_lecture_note"), PRES),
        amplified_note=_one(item.get("amplified_note"), PRES),
        trade_plan_note=_one(item.get("trade_plan_note"), PRES),
        algorithmic_theory_note=_one(item.get("algorithmic_theory_note"), PRES),
    )


def parse_charter(raw: dict) -> CharterState | None:
    block = raw.get("charter") or raw.get("ict_charter")
    if not block:
        return None
    cr = block.get("charter_recognition") or {}
    if isinstance(cr, bool):
        cr = {"flag": cr}
    entries = []
    for item in block.get("recognized_pams") or ():
        if isinstance(item, str):
            item = {"pam_id": item}
        if isinstance(item, dict):
            e = _entry(item)
            if e.pam_id != "none":
                entries.append(e)
    return CharterState(
        identified_pam=_one(block.get("identified_pam"), PRES),
        recognized_pams=tuple(entries),
        model13_bridge=_one(block.get("model13_bridge"), PRES),
        charter_recognition=CharterRecognition(
            flag=bool(cr.get("flag", False)),
            reason=cr.get("reason") or "provided_state",
        ),
    )
