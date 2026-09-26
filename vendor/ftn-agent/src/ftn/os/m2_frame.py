"""Month-2 Slice 3: low_risk_frame derivation.

identified_low_risk_frame == present
AND identified_high_reward_context == present.
Posture / guidance / psychology / traps do not mint the flag.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m2_context import derive_month2_context
from ftn.os.m2_contracts import LowRiskFrame, Month2State


def classify_low_risk_frame(st: Month2State) -> LowRiskFrame:
    if (
        st.identified_low_risk_frame == "present"
        and st.identified_high_reward_context == "present"
    ):
        return LowRiskFrame(True, "identified_low_and_high_reward")
    return LowRiskFrame(False, "missing_identified_frame")


def derive_month2(raw: dict) -> Month2State:
    base = derive_month2_context(raw)
    return replace(base, low_risk_frame=classify_low_risk_frame(base))
