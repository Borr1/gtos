# Historical OHLC GTOS Replay Contract

Generated UTC: `2026-05-15T15:37:43Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT`

Frozen replay/source contract only. It freezes discovery candidates for future source-safe replay and does not validate edge, R/PnL, expectancy, fillability, live-readiness, or promotion.

## Counts

- `input_immediate_replay_rows`: `6`
- `contract_rows`: `6`
- `cluster_binding_rows`: `588`
- `blocker_rows`: `30`

## Symbols

- `GBPJPY`: `5`
- `XAUUSD`: `1`

## Boundary

- These contracts freeze candidate definitions; they do not prove an edge.
- Existing discovery rows are contaminated for validation of these frozen rules.
- Entry geometry and cost/fill modeling remain open blockers.
