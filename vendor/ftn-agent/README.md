# FTN Agent — Filling The Numbers

Paper-first ICT orchestration agent in the same company style as
[GdotAiM/mint-agent](https://github.com/GdotAiM/mint-agent).

FTN runs the Month-09 *Filling The Numbers* workflow:

1. Daily prep (HTF context + four measurement families)
2. Pre-session filter (bias + four-level count)
3. Kill-zone watch (London / NY AM)
4. Setup gate (raid → displacement → MSS → PD-array retrace)
5. Management (scale after four numbers; leave a runner)
6. Close-of-day journal

**It does not invent live edges and does not place live orders.**
Default mode is `paper`. Live requires dual unlock (`live_enabled: true` **and**
`FTN_LIVE=1`) and is still refused by the stub.

## Desk (HERMES-style frontend)

Vanilla HTML/CSS/JS — no npm. Same dark-terminal language as
[hermes-desk](https://github.com/GdotAiM/hermes-desk).

```bash
cd ftn-agent/desk
python3 -m http.server 8766 --bind 127.0.0.1
# open http://127.0.0.1:8766
```

Overlays: 0-GMT pivots, CBDR, Asian, Flout, four-number count, PD arrays.
Paper ticket modal hands off to MINT — it does not route a broker.

## Quick start

```bash
cd ftn-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python3 -m ftn run --symbol EURUSD --fixture fixtures/sample_eurusd.json
python3 -m ftn prep --symbol EURUSD --fixture fixtures/sample_eurusd.json
cat dispatch/out/latest.json
pytest
```

## Layout

```
AGENT.md                 # Charter (paste into Claude Code / Cursor)
AGENTS.md                # Coding-agent operating rules
config.yaml              # Paper/live locks, sessions, risk caps
src/ftn/
  engine/                # Pivots, CBDR, Asian, Flout, PD-array overlap
  workflow/              # Six-stage orchestrator
  adapters/              # Paper stub (no live broker)
  journal/               # Decision template
```

## Safety (inherited from MINT)

- Paper default
- Dual unlock for live — stub still refuses live
- No secrets in git
- Tickets ≠ orders
- Caps cannot rise without a human

## License

MIT
