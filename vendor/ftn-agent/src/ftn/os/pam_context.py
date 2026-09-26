"""Charter Slice 2: labeled PAM context ingest.

Does not derive charter_recognition.
Does not inspect or mutate Core M1–M12.
Does not create candidates or session tickets.
"""

from __future__ import annotations

from ftn.os.pam_contracts import (
    PRES,
    CharterRecognition,
    CharterState,
    PamEntry,
    _entry,
    _one,
)


def _block(raw: dict):
    ev = raw.get("evidence") or {}
    ch = raw.get("charter") or raw.get("ict_charter") or {}
    return ev, ch


def derive_charter_context(raw: dict) -> CharterState:
    ev, ch = _block(raw)
    src = ev.get("charter") or ev or ch
    entries = []
    for item in src.get("recognized_pams") or ch.get("recognized_pams") or ():
        if isinstance(item, str):
            item = {"pam_id": item}
        if isinstance(item, dict):
            e = _entry(item)
            if e.pam_id != "none":
                entries.append(e)
    return CharterState(
        identified_pam=_one(
            src.get("identified_pam") or ch.get("identified_pam"), PRES
        ),
        recognized_pams=tuple(entries),
        model13_bridge=_one(
            src.get("model13_bridge") or ch.get("model13_bridge"), PRES
        ),
        charter_recognition=CharterRecognition(
            flag=False, reason="slice2_context_only"
        ),
    )
