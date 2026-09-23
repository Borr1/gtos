# Tick M15 Primitive Factory

Generated UTC: `2026-05-15T15:54:59Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: descriptor factory only. No edge, R/PnL, validation, live-readiness, or promotion verdict.

## Counts

- Source parquet files consumed: `114`
- M15 event rows: `8977`
- Baseline rows: `28`
- Flag summary rows: `140`
- Primitive-flagged rows: `2040`
- Current-day partial event rows: `448`
- Read error rows: `0`

## Flag Families

- `ABSORPTION_PROXY_CVD_DIVERGENCE_DELTA_P75`: `635` flagged descriptor rows
- `DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION`: `457` flagged descriptor rows
- `SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION`: `963` flagged descriptor rows
- `TICK_RANGE_EXPANSION_P95_SAME_SYMBOL_SESSION`: `458` flagged descriptor rows
- `TICK_VELOCITY_BURST_P95_SAME_SYMBOL_SESSION`: `457` flagged descriptor rows

## Boundary

- Flags are same-symbol/session percentile descriptors, not signals.
- No target outcome was attached.
- Current-day partial rows are labelled and must be excluded from sealed evidence.
