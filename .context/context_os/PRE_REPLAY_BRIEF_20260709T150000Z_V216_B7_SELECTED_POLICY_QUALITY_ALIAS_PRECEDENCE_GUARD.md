# Pre-Replay Brief - V216 B7 Selected-Policy Quality Alias Precedence Guard

Generated UTC: 2026-07-09T15:00:00Z.

## Control Surface

- Fable batch: B7 full proof ladder, targeted transfer-composition correctness repair.
- Broker/live/final boundary: broker mutation disabled, live broker authority false, final selection false.
- Replay authority: local replay/package authority full.
- Scope: bounded two-day proof slice only, not a full-reservoir transfer claim.
- Current process state before replay: V215 completed; no duplicate V216 replay is active.

## Latest Completed Replay

Latest completed targeted proof:
`BROAD_LIVE_AS_IF_REPLAY_V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

- Scope: 2026-05-13..2026-05-14, XAUUSD/USDCAD/USDJPY, repaired profile only.
- Candidate/scorecard/order/trade/missed/bucket rows: 1651 / 192 / 8 / 3 / 1647 / 92.
- W/L/F: 3 / 0 / 0.
- Net/gross/final R: +1.10761535 / +1.35101129 / +1.35101129.
- Cash PnL: +277.0648589.
- Risk cash: 750.86709783.
- Expected cost R: 0.24339594.
- V215 versus V214 delta: trade count -10, net R +2.86933957, gross/final R +1.87308262, cash PnL +405.7672548.
- V215 removed 11 V214 trades totaling -2.08087572R and restored one V213 trade totaling +0.78846385R.
- V215 missed rows carry 29 `finite_selected_policy_reallocation_quality_score_below_floor` override-blocked reasons.
- Executed REFUSED/source-gap rows: 0 / 0.

Interpretation: V215 repaired the V214 negative cohort for this slice, but Descartes found a real production hole not covered by the first V215 tests: a finite negative `selected_policy_executable_quality_reallocation_score` could still be masked by older nonnegative aliases.

## Incorporated Subagent Findings

- Descartes: INCORPORATED. The selected-policy quality gate now resolves the explicit selected-policy executable reallocation-quality score before older `risk_admitted_scheduler_reallocation_score`, `replacement_reallocation_quality_score`, and `selected_scheduler_replacement_reallocation_quality_score` fallbacks.
- Descartes: INCORPORATED. Added `test_selected_policy_gate_prefers_explicit_reallocation_score_over_stale_aliases`.
- Descartes: INCORPORATED. Fixed `test_risk_finalizer_blocks_non_original_signed_micro_rescue_when_soft_transfer_fails` so it reaches the risk-finalizer micro-rescue path and passes.
- Descartes: DEFERRED TO NEXT ROUTE BINDING. Route verifier should add a fatal finite-negative selected-policy reallocation-quality check under signed soft-transfer reliance after V216 artifacts exist.

## Current Patch Batch

Batch:
`V216_B7_SELECTED_POLICY_QUALITY_ALIAS_PRECEDENCE_GUARD`.

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260709.md`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T150000Z_V216_B7_SELECTED_POLICY_QUALITY_ALIAS_PRECEDENCE_GUARD.md`

Patch types:

- Correctness repair: explicit selected-policy executable reallocation-quality score is authoritative over older scheduler/replacement aliases.
- Test repair: focused tests cover conflicting alias precedence and non-original signed micro-rescue blocking.

Focused proof already run:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py` passed.
- Focused signed/selected-policy/micro-rescue pytest cluster: 9 passed, 605 deselected, 1 warning.

## Expected V216 Effects

- Candidate -> scorecard transfer: expected equal to V215.
- Scorecard -> order -> fill transfer: expected equal to V215 unless the replay has an unobserved conflicting alias row.
- Executed finite-negative selected-policy quality rows: must be 0.
- Alias-conflict execution rows: must be 0.
- Missed rows: if any conflicting alias exists, it must be blocked with `selected_policy_reallocation_quality_score`.
- Cost/source execution: executed REFUSED/source-gap rows must remain 0 / 0.
- Broker/live/final: must remain false.

Artifact scan before this replay found no actual V214/V215 conflicting-alias rows, so the expected behavior is neutral versus V215. V216 is still required because production code changed after V215.

## V216 Replay Command

Run only the targeted proof slice:

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 \
  --end 2026-05-14 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD USDCAD USDJPY \
  --compact-missed-ledger \
  --gc-between-chunks \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V216_B7_SELECTED_POLICY_QUALITY_ALIAS_PRECEDENCE_GUARD_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY
```

Broker/live/final remain closed regardless of V216 result.
