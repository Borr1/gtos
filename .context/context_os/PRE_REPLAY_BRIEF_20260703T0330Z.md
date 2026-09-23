# Pre-Replay Brief - 2026-07-03T03:30Z

Scope: denominator-to-deployment ultimate-system replay repair in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full. This brief supersedes the 2026-07-02T22:01Z brief for the next patch batch.

## 1. Latest Completed Replay

Latest completed broad proof remains:

`BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- candidates: `25,006`
- scorecards: `288`
- terminal orders: `119`
- filled trades: `51`
- missed rows: `24,887`
- net R: `+29.35570236`
- gross/final R: `+33.93212860`
- cash PnL: `+6228.63096022`
- W/L/F: `37/14/0`
- broker/live/final: `false/false/false`

Latest completed targeted projection smoke:

`BROAD_LIVE_AS_IF_REPLAY_CANONICAL_CONTEXT_PROJECTION_REPAIR_V94_20260513_REPAIRED_ONLY_COMPACT_SMOKE`

- date: `2026-05-13`
- candidate-index rows: `8,864`
- scorecards: `96`
- order ledger rows: `110`
- terminal orders: `55`
- filled trades: `16`
- missed rows: `8,809`
- net R: `+6.77427007`
- gross/final R: `+8.23945742`
- expected cost R: `1.46518735`
- cash PnL: `+2565.01995828`
- W/L/F: `9/7/0`
- broker/live/final: `false/false/false`
- missed scoreable R: `+593.60435707` positive, `-2970.33466290` negative, `-2376.73030583` total

## 2. Running Replay

No broad replay, route builder, verifier, pytest, or py_compile process is running.

Decision: do not start a duplicate broad replay. Patch the two current V94 truth-contract failures, then run focused tests and another targeted one-day smoke before any broad rerun.

## 3. Baseline Comparison

| Run | Scope | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Boundary |
|---|---|---:|---:|---:|---:|---:|---|
| V89D | 2026-05-13..17 fullgrid | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 | broad comparator |
| V90 | 2026-05-13..17 fullgrid | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 | broad comparator |
| V92 | 2026-05-13..17 fullgrid | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 | latest broad proof |
| V94 | 2026-05-13 one-day smoke | 16 | +6.77427007 | +8.23945742 | +2565.01995828 | 9/7/0 | targeted projection proof, not broad replacement |

## 4. Dirty Files And Active Code Changes

Active route/code changes include:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_denominator_to_deployment_execution.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_denominator_to_deployment_verifier.py`

Context updates include this brief, `CURRENT_ROOT_CAUSE_MAP.json`, the continuation directive, and `current_repo_reading_order.md`.

Do not stage unrelated historical science JSONL deletions, stale partial artifacts, or `.context/LIVE_STATE.md`.

## 5. Subagent Findings

- Halley: incorporated. Verifier had selected stale V12 and confused scheduler mismatch/context producer gaps. Current manifest now points V94; stale-prefix and scheduler-mismatch noise are resolved.
- Turing: incorporated. Producer coverage was partial; candidate/order/trade/missed rows needed selected scheduler context/replacement aliases and candidate-instance identity. V94 verifies context-envelope projection clean.
- Confucius: incorporated. Compact candidate and missed ledgers dropped context/replacement fields; route harness compaction now preserves those surfaces.
- Banach/Averroes/Aquinas: running sidecar review of the current V94 authority and stop-hazard verifier failures; their findings will be folded in before final verification.

## 6. Known Mismatch Classes

- source-bound -> candidate: V94 parity maps `853/1101` source axes to candidates; `248/1101` remain not generated or non-executable by exact labels.
- candidate -> selector: open selector/admission leaks remain (`229` selector reject source-axis labels), but current verifier blocker is not selector admission.
- selector -> scheduler: current V94 has `101` candidate-generated-not-scheduler-selected axis labels; later behavioral repair lane.
- scheduler -> risk: risk is still heavily reduced; current patch does not change sizing policy.
- risk -> order: REFUSED/source-gap broker-cost rows remain non-executable and must stay so.
- order -> lifecycle/fill: V94 has `6` order-accepted-not-filled axis labels; later fillability/lifecycle lane.
- fill -> exit: two M1 proxy profit-harvest rows are incorrectly promoted to terminal/headline/final-R authority despite lacking ordered-tick truth.
- ledger truth: five candidate-index rows report stop-hazard status/action capped while `risk_cap_applied` remains false.

## 7. Fixed / Partial / Open

Fixed by V94:

- candidate context envelope scan is clean;
- source-bound parity stream scan is clean;
- adaptive disabled-axis scan is clean;
- lifecycle root flat truth scan is clean;
- cost authority scan is clean;
- scheduler parity mismatch counts are empty.

Open:

- `broad_live_as_if_selected_policy_replay_authority_leak`: 2 order rows and 2 trade rows where M1 proxy profit-harvest still claims headline/terminal/final-R authority.
- `broad_quality_parity_candidate_index_contract_bad`: 5 candidate-index rows with `predecision_stop_hazard_guard_capped_without_risk_cap`.

## 8. Highest-Leverage Same-Root Batch

Patch batch:

`replay_truth_authority_normalization_batch`

Reason: both remaining verifier blockers are the same root class: replay ledgers still let diagnostic/proxy or stale field values override the canonical replay truth contract.

## 9. Affected Files / Components

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: profit-harvest replay authority and stop-hazard projection normalization.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: direct helper tests for authority/projection truth.
- `tests/test_broad_replay_repair_config.py` or verifier tests if compact path needs explicit coverage.

## 10. Patch Classification

- Profit-harvest M1 proxy demotion: correctness repair. M1 path evidence may remain diagnostic but cannot set terminal/headline/final-R authority without ordered-tick truth.
- Stop-hazard capped normalization: correctness and ledger-truth repair. A capped stop-hazard guard with cap pct/action must emit `risk_cap_applied=true`.
- No performance repair is intended in this batch. If headline R changes, it is expected to come from removing false terminal authority, not from opportunity suppression.

## 11. Expected Measurable Effect Before Replay

- candidate -> scorecard transfer: no intended count change.
- scorecard -> order transfer: no intended count change.
- order -> fill transfer: no intended count change.
- missed positive R / negative R: no intended suppression or admission change.
- trade count: likely unchanged in targeted smoke unless false profit-harvest terminal authority had altered terminal trade inclusion.
- net/gross/final R: may move if the two M1 proxy profit-harvest rows were affecting headline final R; that movement is a truth correction, not a performance claim.
- W/L/F: may move only if terminal close reason/final-R authority changes.
- cost-refused/source-gap execution: must remain zero.
- risk-reduced/full-risk distribution: no intended change.

## 12. Proof Criteria

Helped:

- focused tests pass;
- V95 targeted smoke has zero selected-policy replay authority leaks;
- V95 candidate index has zero stop-hazard capped-without-risk-cap rows;
- context envelope, source-bound parity, cost authority, adaptive axis, and lifecycle scans remain clean.

Failed:

- M1 proxy rows still claim headline/terminal/final-R authority;
- capped stop-hazard rows still emit `risk_cap_applied=false`;
- any REFUSED/source-gap broker-cost candidate becomes executable;
- projection fixes remove opportunity rather than preserving diagnostic/missed accounting.

Exposes next flaw:

- V95 verifier becomes clean but transfer remains limited. Next patch should move to the highest material behavioral leak from V95 parity/flow: selector admission, scheduler ranking/reallocation, risk sizing, order/fillability, lifecycle, or exit geometry.
