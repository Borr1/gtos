# Pre-Replay Brief - 2026-07-02T22:01:48Z

Scope: denominator-to-deployment ultimate-system replay repair in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full. This brief is the required checkpoint before the next patch or replay.

## 1. Latest Completed Replay

Newest completed broad run on disk:

`BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

Summary:

- status: `broad_live_as_if_replay_materialized_broker_live_closed`
- candidates: `25,006`
- scorecards: `288`
- order ledger rows: `239`
- terminal orders: `119`
- filled trades: `51`
- missed rows: `24,887`
- net R: `+29.35570236`
- gross/final R: `+33.9321286`
- expected cost R: `4.57642624`
- cash PnL: `+6228.63096022`
- risk cash: `10284.37194876`
- risk pct: `9.87218988`
- W/L/F: `37/14/0`
- broker/live/final: `false/false/false`

## 2. Running Replay

No broad replay, pytest, py_compile, or build process is currently running.

`BROAD_LIVE_AS_IF_REPLAY_REPLACEMENT_REALLOCATION_QUALITY_REPAIR_V93_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID` is an interrupted partial, not final proof. It wrote complete-looking row counts and a partial summary, but no final summary. Treat it as salvage evidence only.

Decision: do not resume or duplicate V93. Parse it for row-level truth, patch the exposed producer-side gaps, then run focused tests/projection smoke before any broad rerun.

## 3. Baseline Comparison

| Run | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Delta vs V89D Net R |
|---|---:|---:|---:|---:|---:|---:|
| V89D stop-hazard attribution fullgrid | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 | baseline |
| V90 transfer-rank lifecycle authority | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 | -6.00319297 |
| V92 lifecycle truth adaptive-axis | 51 | +29.35570236 | +33.9321286 | +6228.63096022 | 37/14/0 | -5.48950218 |
| V93 replacement/reallocation quality partial | 51 | +29.35570236 | +33.9321286 | +6228.63096022 | 37/14/0 | -5.48950218 |

Interpretation: V93 did not move behavior versus V92 in the salvage rows. The scheduler replacement-quality patch may be correct internally, but the replay ledgers do not yet expose enough canonical context/replacement-quality projection to prove or debug the next behavioral decision path.

## 4. Dirty Files And Active Changes

Active route/code files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/components/selector_v4.py`
- `src/research/reduced_risk_action_reason_contract.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- route tests in `tests/test_broad_replay_repair_config.py`, `tests/test_denominator_to_deployment_verifier.py`, `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`, `tests/test_selector_v4.py`, `tests/test_timewarp_scheduler_materialization.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`

Other dirty surfaces:

- Context OS files are dirty from earlier context infrastructure work.
- Older large historical science-program JSONL files are deleted in the worktree.
- `.codex_run_logs/` and several partial broad replay artifacts are untracked.

Staging boundary: do not stage unrelated historical deletions, `.context/LIVE_STATE.md`, stale partial artifacts, or context-infrastructure work with the next route repair unless that checkpoint explicitly owns them.

## 5. Subagent Findings

- Chandrasekhar the 2nd: incorporated. Finding was post-gate replacement/reallocation ordering; scheduler now has hard-gated replacement/reallocation quality scoring and tests. V93 shows no behavior change, so the next question is whether the fields are visible and instance-bound downstream.
- Pascal the 2nd: incorporated for verifier hardening. Verifier checks now cover stale prefix, lifecycle missed truth, selected bridge canonical key, REFUSED/source-gap non-execution, adaptive disabled axis, and context envelope presence. Producer-side rows now need to satisfy those checks.
- Boole the 2nd: partially incorporated and promoted to next batch. Finding was missing canonical context envelope and candidate-ID keyed selected maps. V93 confirms this remains open: scorecards and missed rows are context-sparse and replacement quality is not top-level.
- Earlier agents: mixed. Cost authority, lifecycle action resolution, stale finalizer-surface protection, same-cluster slot truth, adaptive axis split, stop hazard, and replacement churn patches were applied where current evidence supported them. Remaining deferred items are behavioral lanes after producer truth projection.

## 6. Mismatch Classes

- source-bound -> candidate: the large source-bound reservoir is visible but still compresses heavily before scorecard/order/fill; full transfer accounting remains open.
- candidate -> selector: skipped/not-risk-bearing rows need exact context envelopes and causal miss reasons before any gate opening.
- selector -> scheduler: scheduler receives quality fields, but selected package/context identity must be instance-keyed, not bare candidate-ID keyed.
- scheduler -> risk: replacement/reallocation quality exists internally but is invisible top-level in V93 scorecard/order/trade/missed rows.
- risk -> order: broker-cost REFUSED/source-gap rows remain non-executable; this is correct and must stay true.
- order -> lifecycle: pending replacement/lifecycle release attribution improved, but only five V93 scorecard rows had lifecycle-root release candidates.
- lifecycle -> fill: latest completed transfer is 119 terminal orders -> 51 fills; fillability behavior remains a later performance lane.
- fill -> exit: filled loss remains dominated by stop paths, but exit changes need causal predecision evidence and not close-reason overfit.
- ledger truth: top-level fields can disagree with nested selected scheduler truth, causing parity/verifier drift.

## 7. Fixed / Partial / Open

Fixed:

- Broker-calibrated replay cost authority is primary; old synthetic cost is diagnostic fallback only.
- REFUSED/source-gap broker-cost rows do not execute in latest completed evidence.
- Scheduler replacement/reallocation quality comparator is implemented internally.
- V89D/V90/V92 selected-set churn is quantified.
- Verifier is hardened against stale prefix and major truth leaks.

Partially fixed:

- Candidate instance identity exists in many paths, but selected maps and missed attribution are not canonical everywhere.
- Missed-opportunity accounting is scoreable, but context and rank/replacement attribution remain sparse.
- Risk reallocation exists, but all V92 orders/trades are still open-reduced-risk.

Open/newly exposed:

- V93 scorecard top-level `same_symbol_replay_exposure_context`: `109/288`.
- V93 scorecard nested `selected_scheduler_same_symbol_replay_exposure_context`: `236/288`.
- V93 missed top-level `same_symbol_replay_exposure_context`: `4107/24887`.
- V93 top-level `replacement_reallocation_quality_score`: `0` rows across scorecard/order/trade/missed.
- V93 top-level `selected_scheduler_replacement_reallocation_quality_score`: `0` rows across scorecard/order/trade/missed.
- `selected_scheduler_options_by_candidate_id` exists on scorecards; `selected_scheduler_options_by_candidate_instance_key` is absent.

## 8. Next Same-Root Batch

Patch batch:

`canonical_replay_context_envelope_and_instance_projection_batch`

Reason: The current root leak is not another broad replay. It is the producer-side truth envelope: selected scheduler context/replacement quality and instance identity exist in nested/internal surfaces but do not consistently reach scorecard/missed/order/trade rows as canonical top-level replay truth.

## 9. Affected Files / Components

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: canonical context envelope helper, selected instance-key map, missed attribution, scorecard/order/trade/missed projection.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`: bridge compact fields should preserve timeframe/context envelope where relevant.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: verifier already mostly hardened; may need exact producer-field assertions after patch.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: producer helper/materialization tests.
- `tests/test_broad_replay_repair_config.py`: compact/bridge projection tests.
- `tests/test_denominator_to_deployment_verifier.py`: verifier invariant tests if producer fields change.

## 10. Patch Classification

- Correctness repair: canonical context envelope; instance-key selected map; exact selected/missed attribution before candidate-ID fallback.
- Diagnostic/ledger repair: top-level projection of same-symbol context and replacement/reallocation quality; source/status field for synthesized-empty context.
- Performance repair: none expected directly in this batch. This is a prerequisite for the next behavioral repair.

## 11. Expected Measurable Effect

- candidate -> scorecard transfer: row count should remain `25006 -> 288`; top-level selected context coverage should rise from `109/288` to all rows where selected/pre-risk scheduler context exists, currently `236/288`.
- scorecard -> order transfer: no count change expected; latest completed baseline is `288 -> 119` terminal orders.
- order -> fill transfer: no count change expected; latest completed baseline is `119 -> 51`.
- missed positive R: do not suppress; V92 diagnostic positive missed sum is `+2054.54396823R` over `2721` rows.
- missed negative R: do not blindly admit; V92 diagnostic negative missed sum is `-7914.65328589R` over `4773` rows.
- trade count: no headline change expected from projection-only patch.
- net/gross/final R: no headline change expected; baseline is `+29.35570236 / +33.9321286 / +33.9321286`.
- W/L/F: no headline change expected; baseline is `37/14/0`.
- cost-refused/source-gap execution: must remain zero executed REFUSED/source-gap rows.
- risk-reduced/full-risk distribution: no immediate change expected; V92 order/trade decisions are all `open-reduced-risk`, which remains an open calibration/performance lane.

## 12. Success / Failure Criteria

Helped:

- Focused tests and a targeted projection/materialization smoke show canonical context envelope present where source exists.
- `selected_scheduler_options_by_candidate_instance_key` is emitted and used before candidate-ID fallback.
- Replacement/reallocation quality is visible in selected top-level scorecard/order/trade/missed rows when applicable.
- Verifier scans pass.
- REFUSED/source-gap broker-cost rows remain non-executable.

Failed:

- Top-level context/replacement fields remain sparse when nested source exists.
- Canonical bridge/join keys mismatch `(candidate_id, decision_time)`.
- Candidate-ID fallback still controls selected attribution when `decision_time_utc` exists.
- Any cost-refused/source-gap row becomes executable.

Exposes next deeper flaw:

- Projection is complete but V92/V93 trade sequence and R remain unchanged. Then the next batch should be behavioral: selector admission, scheduler allocation, risk sizing, order/fillability, lifecycle, or exit, ranked by newly visible transfer/leak data.

Replay rule:

Run focused tests and targeted projection/materialization smoke first. Do not start a new broad replay just because this patch lands. Run broad replay only after the producer truth fields are verified or after a behavioral patch changes global decisions.
