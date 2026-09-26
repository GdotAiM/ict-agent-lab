
"""Candidate logger — frozen MarketState only. Does not load *.expected.json."""

from __future__ import annotations

from ftn.models.bb import evaluate_bb
from ftn.models.conso import evaluate_conso
from ftn.models.pip20 import evaluate_pip20
from ftn.models.rev import evaluate_rev
from ftn.os.contracts import Candidate, MarketState


def evaluate_candidates(state: MarketState) -> tuple[Candidate, ...]:
    rev = evaluate_rev(state)["candidate"]
    conso = evaluate_conso(state)["candidate"]
    bb = evaluate_bb(state)["candidate"]
    pip = evaluate_pip20(state)["candidate"]

    if rev.state == "selected" and conso.eligible:
        conso = Candidate("CONSO", "suppressed", True, "REV_preemption", "hermes_governance")

    # PIP20 is the stricter offset subset; if both eligible, suppress BB for the ticket
    if pip.eligible and bb.eligible and rev.state != "selected" and not rev.eligible:
        bb = Candidate("BB", "suppressed", True, "PIP20_stricter_offset", "hermes_governance")

    if rev.eligible:
        if bb.state != "suppressed":
            bb = Candidate("BB", "invalidated", False, "named_extreme_plus_htf_array", "hermes_governance")
        if pip.eligible:
            pip = Candidate("PIP20", "invalidated", False, "named_extreme_plus_htf_array", "hermes_governance")

    ftn = Candidate("FTN", "annotate", False, "objectives_only", "hermes_governance")
    return (rev, conso, pip, bb, ftn)
