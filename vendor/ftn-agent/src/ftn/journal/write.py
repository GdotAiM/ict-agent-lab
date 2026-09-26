from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ftn.config_load import repo_root


def write_journal(payload: dict[str, Any]) -> Path:
    t = payload["ticket"]
    tpl = (repo_root() / "src" / "ftn" / "journal" / "_TEMPLATE_DECISION.md").read_text(
        encoding="utf-8"
    )
    levels = "\n".join(
        f"- L{lv['index']} `{lv['name']}` @ {lv['price']:.5f}" for lv in t.get("four_levels", [])
    ) or "- none"
    conf = t.get("pd_confluence") or []
    confluence = (
        "\n".join(f"- {h.get('name')} × {h.get('pd_array')} ({h.get('kind')})" for h in conf)
        or "- none"
    )
    reasons = t.get("no_trade_reasons") or []
    reason_txt = "\n".join(f"- {r}" for r in reasons) or "- none (candidate)"
    setup = t.get("setup") or {}
    setup_txt = "\n".join(f"- {k}: {v}" for k, v in setup.items()) or "- missing"
    body = (
        tpl.replace("{{DATE}}", payload["scanned_at"])
        .replace("{{SYMBOL}}", str(t.get("symbol")))
        .replace("{{BIAS}}", str(t.get("bias")))
        .replace("{{KIND}}", str(t.get("kind")))
        .replace("{{FAMILY}}", str(t.get("family")))
        .replace("{{LEVELS}}", levels)
        .replace("{{CONFLUENCE}}", confluence)
        .replace("{{SETUP}}", setup_txt)
        .replace("{{REASONS}}", reason_txt)
    )
    out = repo_root() / "dispatch" / "journal"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{payload['scanned_at']}_DECISION.md"
    path.write_text(body, encoding="utf-8")
    return path
