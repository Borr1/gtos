# Historical OHLC Primitive Factory

Generated UTC: `2026-05-15T15:18:51Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `HISTORICAL_OHLC_DISCOVERY_ONLY`

This factory converts M15 candles into primitive movement descriptors for hypothesis generation only. It is not sealed validation or strategy performance.

## Counts

- `m15_csv_files`: `24`
- `baseline_rows`: `726843`
- `primitive_event_rows`: `550552`
- `primitive_summary_rows`: `2565`
- `family_summary_rows`: `108`
- `baseline_summary_rows`: `285`
- `hypothesis_rows`: `5`

## Required Next Controls

- freeze any candidate primitive before outcome scoring in a separate route
- same-symbol/session/horizon generic movement baseline
- neighbor-window and shuffled-label controls
- duplicate/event clustering and concentration
- purged/embargoed split for learned thresholds
- cost/fill model before strategy projection

## Primitive Counts

- `RANGE_COMPRESSION`: `93342`
- `LOWER_WICK_EXHAUSTION`: `84534`
- `UPPER_WICK_EXHAUSTION`: `76895`
- `RANGE_EXPANSION_DOWN`: `53461`
- `CLOSE_BREAKOUT_UP_16`: `52461`
- `SWEEP_HIGH_CLOSE_BACK_INSIDE_16`: `52435`
- `RANGE_EXPANSION_UP`: `52227`
- `SWEEP_LOW_CLOSE_BACK_INSIDE_16`: `43543`
- `CLOSE_BREAKOUT_DOWN_16`: `41654`
