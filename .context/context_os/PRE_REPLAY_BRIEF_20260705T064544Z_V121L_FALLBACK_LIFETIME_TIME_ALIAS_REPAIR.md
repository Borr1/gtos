# V121L Pre-Replay Brief - Fallback Lifetime and Time Alias Repair

Generated: 2026-07-05T06:45:44Z

This is a bounded repair proof for the V121K hostile five-day window. It does not prove global source-bound reservoir conversion and must not be compared directly to the 1.249M global source-bound R reservoir.

## Latest Completed Replay

V121K prefix: `BROAD_LIVE_AS_IF_REPLAY_V121K_HOSTILE_5D_ORDER_TRUTH_TRANSFER_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

- Window: 2026-05-13..2026-05-17
- Candidates / scorecards / order events / terminal orders / trades / missed: 24093 / 288 / 10 / 3 / 1 / 24086
- Net/gross/final R: -1.09653986 / -1.0 / -1.0
- Cash PnL / risk cash / risk pct: -1096.53986 / 1000.0 / 1.0
- W/L/F: 0/1/0
- Broker/live/final: false / false / false
- Trade: XAGUSD LONG, off_configured_session, passive_queue_confirmed, stopped before target.

## Baseline Comparison

Same-window comparison against prior baselines:

| Baseline | Trades Delta | Net R Delta | Added Trades / R | Removed Trades / R | Key Read |
| --- | ---: | ---: | ---: | ---: | --- |
| V89D | -55 | -35.9417444 | 1 / -1.09653986 | 56 / +34.84520454 | V121K removed net-positive transfer. |
| V90 | -50 | -29.93855143 | 1 / -1.09653986 | 51 / +28.84201157 | V121K added one losing transfer. |
| V92 | -50 | -30.45224222 | 1 / -1.09653986 | 51 / +29.35570236 | Scorecards stayed 288, orders/fills collapsed. |

This shows V121K was a truth/transfer regression versus V92, not a solved system.

## Current Dirty / Active Code Changes

Patch batch in:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Active route/context dirt exists from prior checkpoints and is not part of this proof unless explicitly updated by the replay.

## Incorporated Findings

- Carson: incorporated. V121K had 16832+ candidates in-progress, only a tiny number final-selected, and order/trade rows had canonical time fields but missing old aliases. V121L patches ledger time alias normalization.
- Descartes: incorporated. Selected V121J/V121K orders were correctly expired when entries never touched; the remaining blocker is conversion/finalizer/order transfer rather than declaring missing evidence.
- Copernicus/Fable plan: incorporated for B2. Current code still clamped fallback to expiry; V121L changes it to latest usable time before expiry or explicit exhausted-window blocker.

## Mismatch Classes

- Source-bound -> candidate: same-window transfer remains bounded; do not use global source-bound R as denominator for this five-day proof.
- Candidate -> scorecard: V121K preserved 288 scorecards versus V92.
- Scorecard -> scheduler/risk/order: transfer collapsed after scorecard, with final blockers concentrated in marketable_guard, headroom, fill_realism, package_authority, and stop_hazard.
- Order -> lifecycle/fill: 10 order events became only 3 terminal orders and 1 fill.
- Fill -> exit: only filled path lost -1.09653986R.
- Ledger: order/trade rows need stable `decision_time`, `asof_utc`, `entry_time`, and `exit_time` aliases for parity tooling.

## V121K Top Blockers

Scorecard transfer:

- marketable_guard: 104 rows
- headroom: 45 rows
- fill_realism: 58 rows
- package_authority: 51 rows
- stop_hazard: 19 rows
- risk_basis_missing: 2 rows
- selector_materialization / lifecycle_expiry / daily_lockout: 1 row each

Missed opportunity:

- cost refused diagnostic: 19889 rows, -3864.23778154R
- router-refusal open-reduced not allowed: 1636 rows, -38.32422267R
- numeric disagreement open-reduced disabled: 746 rows, -24.54211672R
- marketable guard: 210 rows, -73.4754329R
- stop hazard: 224 rows, -31.5134136R
- ordered tick required: 283 rows, 0R
- passive-limit too close: 51 rows, -0.04390671R

## Patch Batch

V121L repairs:

- Correctness: guarded-market fallback can no longer execute at expiry; it clamps to `expiry - 1 minute` or emits `fallback_window_exhausted_by_expiry`.
- Ledger truth: package replay rows now preserve `decision_time` / `asof_utc` / `entry_time` / `exit_time` aliases from canonical UTC fields without overwriting existing values.
- Diagnostic: high candidate fill probability can score the high-fill wait-ceiling diagnostic when order fillability is missing, but missing order fillability remains non-executable.
- Correctness: `risk_authority_bound_and_headroom_available` is now treated as an admitted success reason, not a headroom final blocker; true `risk_headroom_zero` remains a blocker.
- Correctness: passive-limit fallback envelope uses the same lifetime helper as guarded-market execution, propagating clamp/exhaustion fields into risk/order ledgers.

Focused verification:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "preserves_replay_time_aliases or clamps_inside_order_lifetime or guarded_market_fallback_decision_requires_no_broker_boundary or guarded_market_fallback_applied_oracle_uses_fallback_fill_status or high_fill_blocked_unfilled_probe_scores_counterfactual_diagnostic or rejects_missing_order_fillability_even_with_high_candidate_fill" -q`
- Result: 8 passed, 501 deselected, 1 unrelated pytest config warning.

## Proof Command

Run the same hostile five-day repaired-only window because the patch affects order/fallback transfer and ledger truth across the same comparator window:

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 \
  --end 2026-05-17 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V121L_FALLBACK_LIFETIME_TIME_ALIAS_REPAIR_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --skip-tick-source \
  --compact-missed-ledger
```

## Expected Measurable Effects

- Candidate -> scorecard: expected roughly unchanged at 288 in the same window.
- Scorecard -> order: fallback rows should no longer use expiry itself as fallback time.
- Order -> fill: valid fallback fills must occur strictly before expiry; exhausted windows should remain non-executable.
- Missed positive/negative R: may reclassify as explicit fallback-window exhaustion or high-fill diagnostic proxy.
- Trade count and net R: may improve, worsen, or stay flat; the useful proof is whether transfer truth is cleaner and no invalid fallback-at-expiry path remains.
- Cost-refused/source-gap execution: must remain zero executable refused/source-gap fills.
- Risk distribution: preserve full/reduced risk provenance and raw/effective selector action split.

## Helped / Failed / Next-Flaw Criteria

Helped if:

- `fallback_window_exhausted_by_expiry` appears where fallback had no usable lifetime, and no fallback decision time equals expiry.
- passive-limit fallback envelope rows use `passive_limit_fallback_envelope_window_exhausted_by_expiry` instead of the stale delay-reaches-expiry blocker and expose unclamped/latest-usable/clamped fields.
- order/trade rows carry `decision_time`, `asof_utc`, `entry_time`, and `exit_time` aliases when canonical fields exist.
- headroom blockers split true `risk_headroom_zero` from admitted `risk_authority_bound_and_headroom_available` rows.
- cost-refused/source-gap rows remain non-executable.
- added/removed transfers are explained by order/fillability truth, not by blanket trade suppression.

Failed if:

- old fallback-at-expiry behavior remains;
- scorecard/order/trade transfer collapses further without exact blocker reclassification;
- broker/live/final changes from false;
- positive R comes only from suppressing opportunity.

Next deeper flaw if V121L is truth-clean but still undertransfers:

- repair the next highest-leverage order/fillability/risk finalizer leak shown by V121L ledgers, likely marketable_guard/headroom/fill_realism reallocation or scheduler finalizer authority, not another cost-only patch.
