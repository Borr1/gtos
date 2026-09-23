# V100 Pre-Replay Brief - Passive-Fallback Displacement Repair

Generated: 2026-07-03T10:25Z

## Current Replay Evidence

- V92 hostile baseline `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 51 trades, +29.35570236 net R, +33.93212860 gross/final R, W/L/F 37/14/0, 62 expired unfilled.
- V97 hostile comparator `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 47 trades, +13.89627731 net R, +18.23890670 gross/final R, W/L/F 23/24/0, 51 expired unfilled. Same-window V97 added 19 trades for +0.99594545R and removed 23 V92 trades for +13.53876156R.
- V98 hostile router-floor repair `BROAD_LIVE_AS_IF_REPLAY_SOURCE_BOUND_ROUTER_FLOOR_REPAIR_V98_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 44 trades, +18.09434583 net R, +22.26187127 gross/final R, W/L/F 23/21/0, 6 expired unfilled. V98 improved V97 by +4.19806852R but remained -11.26135653R below V92.
- V99 hostile passive-limit queue repair `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_LIMIT_QUEUE_REPAIR_V99_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 45 trades, +13.25940200 net R, +17.37183705 gross/final R, W/L/F 22/23/0, 19 expired unfilled. V99 added 25 trades for +3.11036779R but removed 24 V98 trades for +7.94531162R.
- No broad replay is currently running. The only matching process at preflight was a Chronicle memory helper, not a replay/verifier.

## Same-Window Denominator Discipline

- V92 hostile selected-window axes: package 1101, candidate 894, scorecard/order 39, filled 25, actual executable R +17.76833767.
- V97 hostile selected-window axes: package 1101, candidate 894, scorecard/order 29, filled 18, actual executable R +13.48984606.
- V98 hostile selected-window axes: package 1101, candidate 894, scorecard/order 27, filled 25, actual executable R +17.16997641. V98 used skip-tick/source-bound denominator repair, so denominator totals are diagnostic and not directly comparable to non-skip-tick V92/V97 totals.
- V99 hostile selected-window axes: package 1101, candidate 894, scorecard/order 27, order-present 46, filled 21, actual executable R +11.30935650.
- This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

## Incorporated Subagent Findings

- Goodall: incorporated. V99 degraded passive rows filled 23 trades for +2.85524977R with lower average transfer quality; V98 removed positives were stronger. Passive terminal orders reserved scarce risk and same-symbol state.
- Ramanujan: incorporated. `finalizer_pre_order_materialization_preflight` marks degraded passive-queue rows, but finalizer ranking did not subordinate them. Add rank class/extra-slot fields and demote unless transfer dominance is proven.
- Einstein: incorporated. V99 scorecard supply remained present; removed V98 positives were mostly V99 missed rows, not missing evidence. Primary cause is earlier passive terminal-order reservation before stronger later package rows.

## Root Mismatch Map

- source-bound -> candidate: not current choke; V92/V97/V98/V99 all generate 894/1101 axes.
- candidate -> selector/scheduler: partially fixed; scorecards remain 288, but materialization/ranking churn displaces stronger transfers.
- scheduler -> risk/finalizer: current choke. Weaker fallback-degraded passive rows reserve scarce daily risk and same-symbol pending state before stronger rows.
- risk -> order/fillability: partially fixed. Broker cost authority remains enforced; passive queue is valid, but fallback-degraded queue needs causal transfer dominance before consuming scarce state.
- lifecycle/fill/exit: still open after V100. If V100 restores stronger transfers but remains below V92, next likely leak is same-symbol replacement quality or exit/stop geometry.
- ledger/verifier: diagnostic fields need to preserve degraded transfer score, min floor, rank class, and rank penalty.

## Patch Batch

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: propagate passive degraded transfer floor into scheduler/runtime config, compute predecision degraded transfer score, block weak degraded fallback rows below configured floor, persist rank fields, and demote degraded rows in `finalizer_admission_rank_fields` unless transfer dominance is allowed.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`: repaired profile already sets `replay_order_fillability_policy_v1_passive_limit_fallback_envelope_min_degraded_transfer_score = 0.55` and disables accepted-risk-spend double counting in repaired profile.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: focused preflight/rank tests.
- `tests/test_broad_replay_repair_config.py`: repaired-profile config propagation test.

Patch classification: correctness and performance repair, not an outcome-fitted loss bucket. It uses expected net R, probability, limit fillability, source completeness, broker-cost status, package authority, and finalizer transfer dominance only.

## Expected Measurable Effect

- Candidate -> scorecard should stay near 25006 candidate rows and 288 scorecard rows for the hostile bucket.
- Scorecard/order transfer should reduce weak degraded passive terminal-order churn versus V99; order rows may fall from 66 if weak passive queue rows are correctly blocked or demoted.
- Order -> fill transfer should preserve genuinely strong passive opportunities while reducing expired-unfilled rows and daily-budget missed rows.
- Added transfers versus V98 should be more selective; removed V98 positive R should shrink versus V99.
- Missed positive R may rise if weak fallback rows are blocked, but missed negative R should not improve only by suppressing all trades. The diagnostic is added-vs-removed net transfer and retained stronger positives.
- Cost-refused/source-gap execution must remain zero.
- Risk-reduced/full-risk distribution should remain provenance-preserved; no broker/live/final authority is granted.

## Replay Success Criteria

- Helped: V100 net R improves over V99 and preferably V98, V99 degraded-passive displacement shrinks, removed V98 positives shrink, expired-unfilled/daily-budget missed pressure falls, and added transfers are net positive without suppressing all opportunity.
- Failed: V100 blocks too many valid passive opportunities, trade count collapses without a quality improvement, or added-vs-removed transfer remains worse than V98.
- Exposes next flaw: V100 restores materialization but headline remains below V92 because same-symbol replacement or exit/stop geometry dominates losses.
