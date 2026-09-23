# Historical OHLC Challenger Frontier

Generated UTC: `2026-05-16T02:00:35Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Historical OHLC challenger frontier routing only. This packet preserves screened discovery/control rows and converts them into source-safe next work; it is not validation, R/PnL, expectancy, live-readiness, or a promotion verdict.

## Counts

- `control_queue_input_rows`: `477`
- `placebo_input_rows`: `477`
- `survivor_input_rows`: `44`
- `concentration_audit_input_rows`: `44`
- `gtos_triage_input_rows`: `20`
- `gtos_contract_input_rows`: `6`
- `frontier_route_rows`: `477`
- `frontier_action_rows`: `1437`
- `frontier_family_rows`: `30`
- `bucket_rows`: `86`
- `question_rows`: `477`

## Frontier Status Counts

- `OHLC_FRONTIER_CLUSTER_WEIGHTED_SIGN_FRAGILE_SPLIT_REQUIRED`: `6`
- `OHLC_FRONTIER_CONTROL_COVERAGE_EXPANSION_REQUIRED`: `18`
- `OHLC_FRONTIER_DUPLICATE_CLUSTER_HEAVY_DEDUP_REQUIRED`: `6`
- `OHLC_FRONTIER_GTOS_REPLAY_CONTRACT_READY_SOURCE_REPLAY_AND_COST_FILL`: `6`
- `OHLC_FRONTIER_KILLED_BY_NEIGHBOR_OR_PERMUTED_PLACEBO`: `415`
- `OHLC_FRONTIER_RESILIENT_CROSS_MARKET_DIAGNOSTIC_OR_TRANSFER_REQUIRED`: `12`
- `OHLC_FRONTIER_SOURCE_TRANSFER_MECHANISM_IMPORT_READY`: `2`
- `OHLC_FRONTIER_TIME_SPLIT_SIGN_FRAGILE_REGIME_SPLIT_REQUIRED`: `12`

## Immediate Work

- Replay/source-plan GTOS contracts with entry geometry and cost/fill models.
- Split time-fragile, duplicate-heavy, and cluster-weighted fragile routes.
- Preserve failed placebo routes as negative controls and inverse/avoid candidates.
- Continue no-fill entry geometry challenger work from the parallel explorer route.
