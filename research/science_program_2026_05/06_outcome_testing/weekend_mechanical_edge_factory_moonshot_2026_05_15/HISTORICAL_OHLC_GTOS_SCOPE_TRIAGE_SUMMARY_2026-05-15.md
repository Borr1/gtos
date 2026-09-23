# Historical OHLC GTOS Scope Triage

Generated UTC: `2026-05-15T15:34:55Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE`

GTOS scope triage only. This is not sealed validation, R/PnL, expectancy, fillability, live-readiness, or a promotion verdict.

## Counts

- `input_cluster_resilient_rows`: `20`
- `triage_rows`: `20`
- `immediate_replay_queue_rows`: `6`
- `source_transfer_queue_rows`: `5`

## Scope Buckets

- `CONFIGURED_BACKTEST_ONLY_OUTSIDE_SESSION`: `1`
- `CONFIGURED_BACKTEST_ONLY_SOURCE_TRANSFER_CANDIDATE`: `2`
- `CURRENT_SYMBOL_OUTSIDE_CONFIGURED_SESSION`: `3`
- `GTOS_IMMEDIATE_REPLAY_CANDIDATE`: `6`
- `OUT_OF_SCOPE_SYMBOL_DIAGNOSTIC`: `2`
- `OUT_OF_SCOPE_SYMBOL_OR_OFF_SESSION_DIAGNOSTIC`: `6`

## Boundary

- Immediate replay queue rows are research candidates only.
- Current-symbol off-session rows are not live-trade candidates.
- Backtest-only configured symbols require source-transfer proof before reuse.
