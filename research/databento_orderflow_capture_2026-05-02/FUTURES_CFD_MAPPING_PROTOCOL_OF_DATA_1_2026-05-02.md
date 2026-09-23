# OF-DATA-1 Protocol - Futures To CFD Mapping

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Objective

Determine whether CME futures data from Databento can act as a reliable signal
source for GTOS MT5 CFD execution symbols before we spend credits on deeper
footprint/depth/orderflow studies.

This protocol answers one question first:

> Does futures price movement transfer cleanly enough to the CFD symbol to make
> event-window orderflow research valid?

It does not test profitability, trade rules, or production behavior.

## Registered Pairs

Primary mappings:

| Futures source | GTOS/MT5 target | Reason |
|---|---|---|
| `GC.v.0` | `XAUUSD` | COMEX gold futures is the closest centralized auction proxy for gold |
| `NQ.v.0` | `NAS100` | E-mini Nasdaq futures is the closest centralized auction proxy |
| `YM.v.0` | `US30_cash` | E-mini Dow futures is the closest direct Dow proxy |

Comparator mapping:

| Futures source | GTOS/MT5 target | Reason |
|---|---|---|
| `ES.v.0` | `US30_cash` | S&P futures may proxy broader US equity index risk but raw levels are not comparable |

## Data Inputs

Databento:

- Dataset: `GLBX.MDP3`
- First schema: `trades`
- Symbols: continuous front-month futures (`*.v.0`)
- Start with event windows, not full-history pulls

MT5:

- Existing `data/historical_2026/{SYMBOL}_M1.csv`
- Treat timestamps as UTC, matching the existing GTOS historical loader convention
- Later extension: local tick parquet for sub-minute spread/slippage diagnostics

Timestamp correction:

- If the diagnostic lead/lag scan shows a stable offset, rerun with an explicit MT5 timestamp shift.
- Initial 2026-04-24 diagnostic found a stable `+180 minute` broker-time offset; for UTC alignment use `--mt5-time-shift-minutes -180`.
- This correction is research-local and does not change the production/live data path.

## Metrics

For every pair:

- futures minutes
- MT5 minutes
- aligned minutes
- close basis mean/std/min/max
- 95th percentile absolute basis z-score
- one-minute return correlation at zero lag
- lead/lag return correlation for `[-5, +5]` minutes
- best absolute lead/lag correlation
- beta of MT5 returns versus futures returns
- directional agreement
- futures volume and trade-count coverage

Positive lag means futures leads MT5 by that many one-minute bars.

## Interpretation Rules

Green transfer candidate:

- enough aligned minutes for the window
- high zero-lag or futures-leading return correlation
- stable basis for same-scale pairs (`GC->XAUUSD`, `NQ->NAS100`, `YM->US30_cash`)
- direction agreement materially above 50%

Yellow transfer candidate:

- returns align but raw basis is unstable
- use event concurrence instead of direct level mapping

Red transfer candidate:

- weak return correlation
- inconsistent lead/lag
- low directional agreement
- insufficient aligned minutes

## Credit Discipline

Do not fetch full-depth/full-history data for this stage.

First fetch level:

- `trades` only
- one day or targeted kill-zone/event windows
- explicit cost cap

Escalate to `mbp-1`, `mbp-10`, or `mbo` only after trades-level transfer is acceptable.

## Ambiguity Ledger

Known ambiguities:

- MT5 broker prices can diverge from exchange futures during illiquid/news moments.
- MT5 historical CSV timestamps may be broker-server time, not UTC.
- Continuous futures roll behavior must be audited around roll dates.
- Raw basis is meaningful for same-underlying mappings but not for `ES->US30_cash`.
- A one-day diagnostic cannot prove durable transfer.
- Databento trade side is not yet treated as a validated orderflow trigger.

## Acceptance Before OF-DATA-2

Before pulling larger depth windows:

- At least one report exists for each primary pair.
- The report includes costs, coverage, correlation, basis, lead/lag, ambiguity, and next steps.
- Weak mappings are either dropped or restricted to event-concurrence only.
- `NO_PROMOTION_VERDICT` remains.
