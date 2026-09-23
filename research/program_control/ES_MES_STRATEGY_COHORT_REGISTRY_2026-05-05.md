# ES/MES Strategy-Cohort Registry - 2026-05-05

**Status:** `ES_MES_STRATEGY_COHORT_PREREGISTERED_SOURCE_STATUS_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Question

Can ES/MES provide preregistered equity-index context/control evidence, and later a separate strategy cohort if event ids and scoring rules are frozen before outcomes?

## Source Mapping

| File symbol | Source symbol | Evidence class | Allowed use |
|---|---|---|---|
| `SPX_ES` | `ESM26-CME` | `FUTURES_PROXY_TRANSFER` | S&P futures proxy/context source; not broker execution truth |
| `SPX_MES` | `MESM26-CME` | `FUTURES_PROXY_TRANSFER` | Micro S&P futures proxy/context source; not broker execution truth |
| `NAS100_US30_CONTEXT` | `ES/MES` | `CROSS_INSTRUMENT_CONTEXT` | same-session equity-index context only |

## Session Windows

| Window | UTC | Reason |
|---|---|---|
| `NY_INDEX_CONTEXT` | `13:30-16:00` | aligns US30 NY context window; this is a research slice, not an exchange-hours claim |
| `NY_BROAD_EQUITY_CONTEXT` | `13:00-17:00` | aligns broad GTOS NY decision context for future as-of joins |
| `LONDON_INDEX_CONTEXT` | `08:00-10:30` | aligns US30 London context window for cross-index diagnostics |

## No-Lookahead Rules

- Any future feature row must use source events with timestamp <= decision_time_utc/asof_cutoff_utc.
- Registry/status rows must not contain TP/SL hits, realized R, synthetic path labels, or replay lift.
- Outcome files stay closed until event ids, source files, hashes, session windows, and scoring spec are frozen.
- ES/MES evidence must remain labeled as transfer/context evidence, not broker actual-R.

## Boundary

- Allowed use: `['equity-index context/control around NAS100 and US30 diagnostics', 'future standalone ES/MES strategy cohort only after a separate frozen event registry exists']`
- Disallowed use: `['direct broker-truth validation for NAS100 or US30', 'promotion dossier input before broker/source/cost/lifecycle floors are met', 'outcome mining from existing converted ES/MES rows']`
- Opened outcome slices: `[]`
