# ICT glossary (user-editable, optional)

> **Status: personal working notes — edit freely.** Definitions are kept generic on
> purpose and are *not* verified trading facts. Times and rules below are
> placeholders reflecting how I currently describe these concepts; confirm them
> against your own sources before using them in research. Nothing here is
> financial advice. This file is **not** ingested into the Knowledge Base.

| Term | Working definition (edit me) |
|------|------------------------------|
| **Killzone** | A recurring intraday time window (defined in a specific timezone, usually New York time) that the research treats as a period of interest. Record the exact start/end you use. |
| **Silver Bullet window** | A specific one-hour intraday window used in ICT-style research. The lab's example uses **10:00–11:00 America/New_York**; add other windows you use here. |
| **Midnight open** | The opening price of the 00:00 candle in the chosen timezone (the lab assumes America/New_York) for a given day, used as a reference level. |
| **FVG (fair value gap)** | A price range left between candles where, by your chosen definition (e.g. a three-candle pattern), the wicks do not overlap. Write down the exact rule you test. |
| **Displacement** | A strong directional move by your own measurable definition (e.g. candle range vs. recent average). |
| **Liquidity (buy-side / sell-side)** | Price areas above highs / below lows the research treats as targets. Define the swing rule you use. |
| **R multiple** | Reward ÷ risk for a trade idea, where risk = \|entry − stop\| and reward = \|target − entry\|. Computed by `calculate_risk_reward`. |

## Risk rules (template — fill in your own)

- Max risk per idea: `____` % of account (or `____` points).
- Minimum R multiple to consider an idea: `____` R.
- Stop must be on the correct side of entry for the direction (enforced by the tool).
- Every hypothesis needs a written invalidation condition *before* looking at results.
