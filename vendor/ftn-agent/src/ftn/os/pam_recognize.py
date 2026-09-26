"""Charter Slice 3: charter_recognition derivation.

identified_pam == present AND ≥1 valid pam_id in recognized_pams
    → charter_recognition true
otherwise false.

Does not rank PAMs. Does not create tickets. Does not mutate Core.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.pam_context import derive_charter_context
from ftn.os.pam_contracts import CharterRecognition, CharterState


def classify_charter_recognition(st: CharterState) -> CharterRecognition:
    valid = [e for e in st.recognized_pams if e.pam_id != "none"]
    if st.identified_pam == "present" and valid:
        return CharterRecognition(True, "identified_pam_with_named_pam")
    if st.identified_pam != "present":
        return CharterRecognition(False, "no_identified_pam")
    return CharterRecognition(False, "no_named_pam")


def derive_charter(raw: dict) -> CharterState:
    base = derive_charter_context(raw)
    return replace(base, charter_recognition=classify_charter_recognition(base))
