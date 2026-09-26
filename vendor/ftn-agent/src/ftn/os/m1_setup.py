"""Month-1 Slice 3: setup_elements derivation.

identified_setup_elements == present → flag true.
Dealing-range side / notes do not mint the flag.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m1_context import derive_month1_context
from ftn.os.m1_contracts import Month1State, SetupElements


def classify_setup_elements(st: Month1State) -> SetupElements:
    if st.identified_setup_elements == "present":
        return SetupElements(True, "identified_setup_elements")
    return SetupElements(False, "no_identified_setup_elements")


def derive_month1(raw: dict) -> Month1State:
    base = derive_month1_context(raw)
    return replace(base, setup_elements=classify_setup_elements(base))
