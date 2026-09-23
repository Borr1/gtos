# V113C Transfer/Risk/Fillability Trace-Tightened Pre-Replay Brief

Generated: 2026-07-04T05:26:00Z

## Current State

- V113, V113 skip-tick, and V113B skip-tick summaries are interrupted tombstones and remain excluded from behavioral proof.
- The V113B run was intentionally stopped before proof because Lagrange found a same-root trace drift: raw fill-floor failures were being exported by timewarp as canonical scheduler-option authority failures even when scheduler had route-resolved them.
- No broker/live/final authority is enabled. Local replay/package evaluation remains full authority.

## Patch Batch Now Included

- Scheduler authority repair: `src/research/moonshot_scheduler_v4_best_trade_allocator.py` now derives `resolved_package_fill_floor_failures` and `unresolved_package_fill_floor_failures`; authority, signed invalidation, and replay reduce-risk failures use unresolved failures.
- Scheduler diagnostics: raw, resolved, unresolved, and authority failure lists are emitted separately.
- Timewarp trace repair: `src/research_infra/v4_timewarp_simulated_live_research_loop.py` now uses unresolved/authority failures for canonical `package_fill_floor_authority_failures` and preserves raw/resolved/unresolved side fields.
- Tests passed before replay:
  - `python3 -m py_compile` on scheduler/timewarp and touched tests.
  - `test_passive_limit_route_resolution_clears_only_resolved_fill_floor_failures`
  - `test_open_reduced_guarded_route_resolves_passive_limit_fill_floor_without_relaxing_raw_failure`
  - `test_open_reduced_passive_limit_queue_route_bypasses_execution_authority_floor`
  - `test_scheduler_option_trace_reports_unresolved_fill_floor_failures_not_raw`
  - `test_scheduler_missed_attribution_carries_source_required_and_veto_diagnostics`

## Same-Window Baseline Contract

- V111 same-window baseline must be filtered from the 19-day V111 ledgers to `2026-06-03`, not compared as a full 19-day run.
- Sartre sanity slice for V111 June 3: 28 trades, -4.91291701 net R, W/L/F 3/25/0, 58 orders, 1 expired order, 22 guarded-fallback-applied trades.
- Use `decision_time_utc[:10]` as primary date filter, with fallback date keys only if needed.
- Use `canonical_replay_candidate_instance_key` as stable trade key; fallback to `candidate_id@@decision_time_utc`. Do not synthesize symbol/side-only keys.

## V113C Proof Prefix

`BROAD_LIVE_AS_IF_REPLAY_V113C_TRANSFER_RISK_EXPRESSION_FILLABILITY_TRACE_TIGHTENED_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

The suffix is a source-loading stall label, not a live-readiness claim. A valid proof requires completed summary status `broad_live_as_if_replay_materialized_broker_live_closed`, date_start/date_end `2026-06-03`, live broker false, broker mutation false, final selection false, and trade/order/missed/candidate-index/scorecard ledgers present for the same prefix.

## Success/Failure Criteria

- Helped: zero executed REFUSED/source-gap rows, zero disabled off-config fallback fills, raw/effective selector action preserved, session_open_range_break candidate-index rows retained, unresolved fill-floor trace fields no longer show route-resolved failures as authority blockers, and V113C improves or exactly explains the V111 June 3 transfer without suppressing all opportunity.
- Failed: trade set remains negative/disjoint with removed winners and no causal predecision blocker, canonical failure fields still show raw resolved fill-floor failures, or improvement comes only from blocking opportunity.
