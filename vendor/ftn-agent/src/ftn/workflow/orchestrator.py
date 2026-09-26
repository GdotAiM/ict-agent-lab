from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ftn.config_load import load_config, repo_root
from ftn.engine.levels import atr_pips, build_families, count_four, detect_bias, overlap_pd
from ftn.engine.ohlc import load_bars
from ftn.journal.write import write_journal


STAGES = ["PREP", "FILTER", "WATCH", "GATE", "MANAGE", "JOURNAL"]


def run_workflow(
    *,
    symbol: str,
    fixture: Path | None,
    bias: str,
    price: float | None,
    stage: str = "all",
    out_dir: Path | None = None,
) -> dict[str, Any]:
    cfg = load_config()
    pack = load_bars(fixture, symbol)
    families = build_families(pack)
    last = price if price is not None else pack.get("last", pack["previous_day"]["close"])
    direction = detect_bias(pack, bias)
    pip = float(pack.get("pip", 0.0001))
    vol = atr_pips(pack, pip)
    compressed = vol < float(cfg.get("min_atr_pips", 20))

    counts = {
        fam: count_four(families, bias=direction, price=last, family=fam)
        for fam in ("pivots", "cbdr", "asian", "flout")
    }
    # pick the family with a full 4-count nearest to last price
    chosen_name, chosen = max(
        counts.items(),
        key=lambda kv: (len(kv[1]), -abs(kv[1][0]["price"] - last) if kv[1] else 0),
    )
    tol = float(cfg.get("overlap_tolerance_pips", 8)) * pip
    hits = overlap_pd(chosen, pack.get("pd_arrays", []), tol)

    setup = pack.get("setup", {})
    gate_ok = bool(
        setup.get("liquidity_raid")
        and setup.get("displacement")
        and setup.get("mss")
        and setup.get("pd_retrace")
        and setup.get("killzone") in ("london", "ny_am")
    )

    no_trade_reasons: list[str] = []
    if compressed and cfg.get("compress_blocks_trade", True):
        no_trade_reasons.append("compressed_atr")
    if cfg.get("require_pd_overlap", True) and not hits:
        no_trade_reasons.append("no_pd_array_overlap")
    if not gate_ok:
        no_trade_reasons.append("setup_gate_incomplete")
    if cfg.get("mode") != "paper":
        no_trade_reasons.append("non_paper_mode_refused")

    actionable = len(no_trade_reasons) == 0
    ticket = {
        "kind": "entry_candidate" if actionable else "no_trade",
        "actionable_for_mint": actionable,
        "symbol": pack.get("symbol", symbol),
        "bias": direction,
        "price": last,
        "family": chosen_name,
        "four_levels": chosen,
        "all_families": counts,
        "pd_confluence": hits,
        "volatility_atr_pips": vol,
        "compressed": compressed,
        "setup": setup,
        "gate_ok": gate_ok,
        "no_trade_reasons": no_trade_reasons,
        "management": {
            "scale_out_after_levels": cfg.get("scale_out_after_levels", 4),
            "runner_pct": cfg.get("runner_pct", 0.25),
            "note": "Pivots/ranges are targets. Entry remains PD-array after MSS.",
        },
        "mode": cfg.get("mode"),
        "live_enabled": cfg.get("live_enabled"),
    }

    payload = {
        "ok": True,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "stage": stage,
        "stages": STAGES if stage == "all" else ["PREP"],
        "ticket": ticket,
        "note": "No orders placed. Ticket still needs MINT allowlist + RISK + human paper ack.",
    }

    out = out_dir or (repo_root() / "dispatch" / "out")
    out.mkdir(parents=True, exist_ok=True)
    stamp = payload["scanned_at"]
    path = out / f"ftn_{stamp}.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    (out / "latest.json").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload["dispatch_path"] = str(path)

    if stage == "all":
        jpath = write_journal(payload)
        payload["journal_path"] = str(jpath)

    return payload
