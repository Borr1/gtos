# Pre-Replay Brief — V121P_RISK_TIER_TRUTH_AND_STOP_HAZARD_CAP_RELEASE

Generated: `2026-07-05T10:45:30Z`

Broker/live/final remain `false/false/false`. This is a one-day targeted repair proof, not full reservoir conversion proof.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121O_STRICT_SIGNED_AUTHORITY_BINDING_REPAIR_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-13..2026-05-17`
- Rows: candidates `25006`, scorecards `288`, orders `60`, trades `18`
- R: net `3.52136577`, gross `4.863274051`, final `4.863274051`, cash `882.08385266`
- W/L/F: `9/9/0`
- Missed: positive `10258.561325262`, negative `-15390.740150662`, cost-passed diagnostic `3333.676002946`
- Cost refused/source-gap executions: `0/0`

## Same-Window Baseline

- V89D: `34.84520454R / 56 trades`
- V90: `28.84201157R / 51 trades`
- V92: `29.35570236R / 51 trades`
- V121M: `4.39334958R / 21 trades`
- V121O: `3.52136577R / 18 trades`

V121O vs V92 removed `49` trades worth `30.39299679R`. Top blockers: `[['ordered_tick_required_for_adverse_before_profit_sequence_not_satisfied', 22, 18.56968073], ['predecision_stop_hazard_guard', 11, 9.79504711], ['scheduler_materialization_skipped_selector_reduce_risk_open_reduced_not_executable:numeric_disagreement_open_reduced_risk_disabled_by_config', 6, 2.32270429], ['scheduler_materialization_skipped_selector_not_risk_bearing_package_open_reduced_authority_not_allowed:admission_quality_dynamic_router_refused_candidate_use', 5, -1.41032935]]`. Ordered-tick blockers are not judged as policy failure because V121O was launched with `--skip-tick-source`.

## Patch Batch

- Risk-tier truth: final `trade_bound` + `full-risk` rows no longer keep stale reduced scheduler causes. In-memory renormalization changes V121O trade ladder from `18 reduced` to `13 full / 5 reduced`.
- Stop-hazard release: repaired profile changes `predecision_stop_hazard_guard_action` from `block` to `cap`, preserving a causal predecision guard while allowing signed opportunities to execute at capped risk.
- Adjacent authority helper: `replay_order_cost_authority_block_reason` tolerates `config=None` and classifies instead of crashing.

## Success Criteria

- No live broker/final authority.
- Cost REFUSED/source-gap executed remains zero.
- Risk ladder rows materialize full/reduced distribution truth instead of all reduced.
- Stop-hazard-blocked V121O/V92-overlap rows on 2026-05-14 become capped executable rows or receive a later explicit blocker.
- Improvement must come from better risk expression and guard-to-cap conversion, not from suppressing opportunity.

## Replay

Run prefix: `BROAD_LIVE_AS_IF_REPLAY_V121P_RISK_TIER_TRUTH_STOP_HAZARD_CAP_20260514_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
Window: `2026-05-14..2026-05-14`
Profile: `repaired_package_conversion_v3`
Tick mode: `--skip-tick-source` for comparability with V121O; do not interpret ordered-tick source gaps as global non-executable proof.
