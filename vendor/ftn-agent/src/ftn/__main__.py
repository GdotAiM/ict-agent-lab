
"""python -m ftn"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ftn.workflow.orchestrator import run_workflow
from ftn.os.briefing import brief_from_fixture


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="FTN / Month-9 OS — paper-first.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--symbol", default="EURUSD")
        sp.add_argument("--fixture", type=Path, default=None)
        sp.add_argument("--bias", choices=["bullish", "bearish", "auto"], default="auto")
        sp.add_argument("--price", type=float, default=None)
        sp.add_argument("--out", type=Path, default=None)

    run = sub.add_parser("run", help="Run FTN PREP→JOURNAL workflow")
    add_common(run)
    prep = sub.add_parser("prep", help="Daily prep only")
    add_common(prep)
    br = sub.add_parser("brief", help="Month-9 DTR briefing + candidate log")
    br.add_argument("--fixture", type=Path, required=True)
    br.add_argument("--out", type=Path, default=None)
    lp = sub.add_parser("live-probe", help="Probe live DATA adapters (quotes only; orders refused)")
    lp.add_argument("--symbol", default="EURUSD")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "live-probe":
        from ftn.adapters.live import fetch_quote, fetch_calendar, refuse_live_orders, live_data_allowed
        from ftn.config_load import load_config
        cfg = {}
        try:
            cfg = load_config()
        except Exception:
            pass
        payload = {
            "data_allowed": live_data_allowed(cfg),
            "quote": fetch_quote(args.symbol, cfg),
            "calendar": fetch_calendar(cfg),
            "orders": refuse_live_orders(),
        }
        print(json.dumps(payload, indent=2))
        return 0
    if args.command == "brief":
        state, cands, md, ftn = brief_from_fixture(args.fixture)
        out = args.out or Path("dispatch/journal") / f"{state.context.date}_{state.context.symbol}_BRIEFING.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        print(md)
        print(f"\n# wrote {out}", file=sys.stderr)
        return 0
    stage = "all" if args.command == "run" else "prep"
    result = run_workflow(
        symbol=args.symbol,
        fixture=args.fixture,
        bias=args.bias,
        price=args.price,
        stage=stage,
        out_dir=args.out,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
