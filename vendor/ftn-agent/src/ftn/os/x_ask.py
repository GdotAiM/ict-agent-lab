
"""Hermes X investigator helper. Reads handoff only. Never writes Market State."""

from __future__ import annotations

import json
from pathlib import Path


def load_handoff(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def why_selected(handoff: dict) -> dict:
    selected = [c for c in handoff.get("candidates") or [] if c.get("state") == "selected"]
    suppressed = [c for c in handoff.get("candidates") or [] if c.get("state") == "suppressed"]
    invalidated = [c for c in handoff.get("candidates") or [] if c.get("state") == "invalidated"]
    pick = selected[0] if selected else None
    ms = handoff.get("market_state") or {}
    return {
        "fingerprint": handoff.get("fingerprint"),
        "selected": pick,
        "because": {
            "sentiment": (ms.get("sentiment") or {}).get("direction"),
            "profile": ms.get("profile"),
            "origin": ms.get("origin_pd_array"),
            "iof": ((ms.get("institutional") or {}).get("state")),
            "contrary": handoff.get("contrary"),
        },
        "suppressed": suppressed,
        "invalidated": invalidated,
        "session_ticket": handoff.get("session_ticket"),
        "rule": "X may cite this pack. X must not edit DayContext or candidates.py.",
    }


def render_claim_md(ans: dict) -> str:
    pick = ans.get("selected") or {}
    b = ans.get("because") or {}
    lines = [
        f"# Why {pick.get('module', 'NO-TRADE')} — investigation pack",
        "",
        f"- Fingerprint: `{ans.get('fingerprint')}`",
        f"- Selected: `{pick.get('module')}` ({pick.get('reason')}) origin=`{pick.get('origin')}`",
        f"- Sentiment: {b.get('sentiment')}  Profile: {b.get('profile')}  IOF: {b.get('iof')}",
        f"- Origin PD: `{b.get('origin')}`",
        f"- Contrary: {b.get('contrary')}",
        f"- Session ticket: `{((ans.get('session_ticket') or {}).get('id'))}`",
        "",
        "## Suppressed",
        "",
    ]
    if ans.get("suppressed"):
        for c in ans["suppressed"]:
            lines.append(f"- {c['module']}: {c['reason']}")
    else:
        lines.append("- none")
    lines += ["", "## Invalidated", ""]
    if ans.get("invalidated"):
        for c in ans["invalidated"]:
            lines.append(f"- {c['module']}: {c['reason']}")
    else:
        lines.append("- none")
    lines += [
        "",
        "## Hermes X rule",
        "",
        "File this as a claim in hermes-x/investigations. Do not write Market State.",
        "",
    ]
    return "\n".join(lines)
