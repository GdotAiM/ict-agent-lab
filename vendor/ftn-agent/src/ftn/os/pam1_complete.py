"""PAM1 model-instance completeness annotation.

Describes how complete labeled PAM1 evidence is.
Does not infer PAM1 from Core.
Does not mint Charter recognition.
Does not create tickets.
"""

from __future__ import annotations

from dataclasses import dataclass

from ftn.os.pam1_evidence import Pam1Evidence, parse_pam1_evidence

REQUIRED = (
    "direction",
    "ipda",
    "institutional_sponsorship",
    "liquidity_objective",
    "ny_execution_window",
    "ote",
    "directional_link",
)
CONFIRMING = (
    "liquidity_raid",
    "displacement",
    "market_structure_shift",
    "institutional_reference",
)


@dataclass(frozen=True)
class Pam1Completeness:
    required_present: tuple = ()
    required_missing: tuple = ()
    confirming_present: tuple = ()
    confirming_missing: tuple = ()
    required_complete: bool = False
    # descriptive only — never a recognition or ticket signal
    reason: str = "unevaluated"


def annotate_pam1_completeness(ev: Pam1Evidence | None) -> Pam1Completeness | None:
    if ev is None:
        return None
    req_ok, req_miss = [], []
    # direction
    (req_ok if ev.direction in ("bullish", "bearish") else req_miss).append("direction")
    (req_ok if ev.ipda.present == "present" else req_miss).append("ipda")
    (req_ok if ev.institutional_sponsorship == "present" else req_miss).append(
        "institutional_sponsorship"
    )
    (req_ok if ev.liquidity_objective.present == "present" else req_miss).append(
        "liquidity_objective"
    )
    (req_ok if ev.ny_execution_window == "present" else req_miss).append("ny_execution_window")
    (req_ok if ev.ote.present == "present" else req_miss).append("ote")
    (req_ok if ev.directional_link == "present" else req_miss).append("directional_link")

    conf_ok, conf_miss = [], []
    c = ev.confirming
    for name, val in (
        ("liquidity_raid", c.liquidity_raid),
        ("displacement", c.displacement),
        ("market_structure_shift", c.market_structure_shift),
        ("institutional_reference", c.institutional_reference),
    ):
        (conf_ok if val == "present" else conf_miss).append(name)

    complete = len(req_miss) == 0
    return Pam1Completeness(
        required_present=tuple(req_ok),
        required_missing=tuple(req_miss),
        confirming_present=tuple(conf_ok),
        confirming_missing=tuple(conf_miss),
        required_complete=complete,
        reason="required_complete" if complete else "required_incomplete",
    )


def derive_pam1_completeness(raw: dict) -> Pam1Completeness | None:
    return annotate_pam1_completeness(parse_pam1_evidence(raw))
