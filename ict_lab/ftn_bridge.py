"""Glue between the Strands agent and the vendored FTN package (vendor/ftn-agent).

FTN's code is used unchanged. The bridge:
- puts vendor/ftn-agent/src on sys.path;
- refuses to run unless FTN's config says mode=paper and live_enabled=false,
  and never touches ftn.adapters (no broker/quote calls);
- only accepts fixtures from FTN's own fixtures/ dir (by name) or an inline
  OHLC pack validated with FtnInputPack;
- redirects FTN's dispatch/journal writes to a temp dir (the runtime code dir
  may be read-only and we don't want artefacts in the vendored tree);
- validates every result with Pydantic (ict_lab.ftn_models).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

from .ftn_models import FtnBriefing, FtnInputPack, FtnWorkflowResult
from .models import validation_error_json

FTN_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "ftn-agent"
FTN_FIXTURES = FTN_ROOT / "fixtures"
_MAX_MD = 6000


class FtnRefused(Exception):
    """Raised when a charter law would be violated."""


def _ensure_path() -> None:
    src = str(FTN_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _work_root() -> Path:
    root = Path(os.environ.get("FTN_LAB_WORKDIR", Path(tempfile.gettempdir()) / "ftn_lab"))
    tpl_dst = root / "src" / "ftn" / "journal" / "_TEMPLATE_DECISION.md"
    if not tpl_dst.exists():
        tpl_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FTN_ROOT / "src" / "ftn" / "journal" / "_TEMPLATE_DECISION.md", tpl_dst)
    return root


# FTN modules that write artefacts under <repo>/dispatch/out (module globals).
_OUTPUT_GLOBALS = [
    ("ftn.os.handoff", "OUT"),
    ("ftn.os.mint_draft", "OUT"),
    ("ftn.os.m7_swing", "STORE"),
    ("ftn.os.session_ticket", "STORE"),
]


@contextmanager
def _redirect_outputs(work: Path):
    """Temporarily point FTN's dispatch/journal writes at ``work`` (FTN code unchanged)."""
    import importlib

    import ftn.journal.write as journal_write

    saved = [(journal_write, "repo_root", journal_write.repo_root)]
    journal_write.repo_root = lambda: work
    out = work / "dispatch" / "out"
    for mod_name, attr in _OUTPUT_GLOBALS:
        mod = importlib.import_module(mod_name)
        saved.append((mod, attr, getattr(mod, attr)))
        setattr(mod, attr, out)
    try:
        yield out
    finally:
        for mod, attr, value in saved:
            setattr(mod, attr, value)


def check_charter() -> dict:
    """Load FTN config and enforce PAPER-only. Returns the config dict."""
    _ensure_path()
    from ftn.config_load import load_config  # noqa: WPS433

    cfg = load_config()
    if cfg.get("mode") != "paper":
        raise FtnRefused(f"FTN config mode is {cfg.get('mode')!r}; the lab only runs mode=paper.")
    if cfg.get("live_enabled"):
        raise FtnRefused("FTN config has live_enabled=true; the lab refuses to run live.")
    if os.environ.get("FTN_LIVE", "").strip() == "1":
        raise FtnRefused("FTN_LIVE=1 is set; the lab refuses to run with the live unlock present.")
    return cfg


def list_fixtures(workflow_only: bool = False) -> list[str]:
    names = sorted(p.stem for p in FTN_FIXTURES.glob("*.json") if not p.stem.endswith(".expected"))
    if workflow_only:
        keep = []
        for n in names:
            try:
                data = json.loads((FTN_FIXTURES / f"{n}.json").read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and {"previous_day", "cbdr", "asian", "flout"} <= set(data):
                keep.append(n)
        return keep
    return names


def resolve_fixture(name: str) -> Path:
    """Map a fixture *name* (e.g. sample_eurusd) to a file inside FTN's fixtures dir."""
    stem = (name or "").strip()
    stem = stem[:-5] if stem.endswith(".json") else stem
    stem = stem.rsplit("/", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", stem):
        raise ValueError(f"invalid fixture name: {name!r}")
    path = (FTN_FIXTURES / f"{stem}.json").resolve()
    if path.parent != FTN_FIXTURES.resolve() or not path.is_file():
        raise ValueError(f"unknown fixture {name!r}; available: {', '.join(list_fixtures())}")
    return path


def run_ftn_workflow(fixture: Optional[str] = "sample_eurusd", bias: str = "auto",
                     price: Optional[float] = None, pack: Optional[dict] = None,
                     stage: str = "all") -> FtnWorkflowResult:
    """Run PREP→FILTER→WATCH→GATE→MANAGE→JOURNAL and return a validated result."""
    check_charter()
    if bias not in ("auto", "bullish", "bearish"):
        raise ValueError("bias must be auto, bullish or bearish")
    if stage not in ("all", "prep"):
        raise ValueError("stage must be 'all' or 'prep'")

    work = _work_root()
    if pack is not None:
        validated = FtnInputPack.model_validate(pack)
        tmp = work / "inputs"
        tmp.mkdir(parents=True, exist_ok=True)
        fx_path = tmp / f"inline_{validated.symbol}.json"
        fx_path.write_text(validated.model_dump_json(), encoding="utf-8")
        symbol = validated.symbol
    else:
        fx_path = resolve_fixture(fixture or "sample_eurusd")
        raw = json.loads(fx_path.read_text(encoding="utf-8"))
        FtnInputPack.model_validate(raw)  # clear error if the fixture isn't a workflow pack
        symbol = raw.get("symbol", "EURUSD")

    from ftn.engine.levels import build_families
    from ftn.engine.ohlc import load_bars
    from ftn.workflow import orchestrator

    with _redirect_outputs(work) as out_dir:
        payload = orchestrator.run_workflow(
            symbol=symbol, fixture=fx_path, bias=bias, price=price,
            stage=stage, out_dir=out_dir,
        )

    families = build_families(load_bars(fx_path, symbol))
    journal_md = None
    if payload.get("journal_path"):
        journal_md = Path(payload["journal_path"]).read_text(encoding="utf-8")

    ticket = payload["ticket"]
    return FtnWorkflowResult.model_validate({
        **payload,
        "measurements": {k: families[k] for k in ("pivots", "cbdr", "asian", "flout")},
        "no_trade": not ticket.get("actionable_for_mint", False),
        "orders_placed": 0,
        "journal_markdown": journal_md,
    })


def _plain(obj: Any) -> Any:
    return asdict(obj) if is_dataclass(obj) else obj


def ftn_briefing(fixture: str = "integration_m1_m9_eurusd") -> FtnBriefing:
    """Month-9 DTR briefing + candidate log from an FTN evidence fixture (read-only)."""
    check_charter()
    from ftn.os.briefing import brief_from_fixture

    path = resolve_fixture(fixture)
    with _redirect_outputs(_work_root()):
        state, cands, md, _ftn = brief_from_fixture(path)
    ctx = getattr(state, "context", None)
    return FtnBriefing(
        fixture=path.stem,
        date=getattr(ctx, "date", None),
        symbol=getattr(ctx, "symbol", None),
        candidates=[_plain(c) for c in cands],
        briefing_markdown=md[:_MAX_MD],
        truncated=len(md) > _MAX_MD,
    )


# -- JSON wrappers used by the Strands tools ------------------------------------------

def _guard(fn, model_name: str) -> str:
    try:
        return fn().model_dump_json(exclude_none=True)
    except FtnRefused as exc:
        return json.dumps({"error": f"FTN refused (charter): {exc}"})
    except ValidationError as exc:
        return validation_error_json(exc.title, exc)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        return json.dumps({"error": f"{model_name}: {exc}"})


def ftn_workflow_json(fixture: Optional[str] = "sample_eurusd", bias: str = "auto",
                      price: Optional[float] = None, pack_json: Optional[str] = None) -> str:
    def run():
        pack = json.loads(pack_json) if pack_json else None
        return run_ftn_workflow(fixture=fixture, bias=bias, price=price, pack=pack)
    return _guard(run, "FtnWorkflowResult")


def ftn_briefing_json(fixture: str = "integration_m1_m9_eurusd") -> str:
    return _guard(lambda: ftn_briefing(fixture), "FtnBriefing")
