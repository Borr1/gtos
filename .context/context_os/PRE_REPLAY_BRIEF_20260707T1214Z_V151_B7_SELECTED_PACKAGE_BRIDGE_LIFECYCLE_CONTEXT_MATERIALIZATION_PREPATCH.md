# V151 B7 Selected-Package Bridge Lifecycle Context Materialization Prepatch Brief

Generated UTC: 2026-07-07T12:14:09Z

This brief selects the next Fable B7 same-root batch after completed V150
targeted replay. It authorizes code/config/test repair only; no broad replay is
authorized before focused proof.

## 1. Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, terminal orders `6`, trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`, expected cost `0.25079769R`, cash PnL `+211.19447407`, risk cash `750.42443587`, risk pct sum `0.75`, W/L/F `3/0/0`.
- Orders: `3` filled, `3` expired unfilled. Trade frequency: `0.6` per day.
- Broker/live/final: broker mutation false, live broker authority false, final selection false.

## 2. Running Process State

No broad replay is authorized. V150 replay and deterministic parsers completed.
Before any new replay, recheck process state and avoid duplicates.

## 3. Baseline Comparison

- V150 vs V149/V148/V147/V144: trade delta `0`, net delta `0`.
- V150 vs V146: trade delta `+1`, net delta `+0.29090804R`, added `1`, removed `0`.
- V89D/V90/V92 hostile May references remain non-denominator-equivalent to this June 1-5 five-symbol proof slice.

## 4. Dirty Files And Active Code Changes

Active checkpoint files include:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- this V151 prepatch brief and the matching V151 root-cause map.

Pre-existing unrelated dirty files and old deleted raw science ledgers remain
outside this checkpoint scope.

## 5. Subagent Findings

- Fable plan/audit: incorporated as dependency control surface.
- Kepler/Archimedes/Curie V148: incorporated; behavior-neutral vs V147.
- Socrates/Hilbert V150: incorporated; focused tests passed, but targeted replay did not reach the repaired consumer path.
- No finding is rejected; V150 result demotes the consumer-path hypothesis from next replay target to covered regression while selecting the upstream bridge/lifecycle context leak.

## 6. Mismatch Classes

- Source-bound -> candidate: partial. `829/1101` source axes generate candidates, but selected-package row-bound source is missing for `79` executable axes.
- Candidate -> selector: partial. Selector reject calibration remains a smaller open class (`6` axes).
- Selector -> scheduler: partial. Scheduler/reallocation remains open (`64+7` axes), but V151 first fixes missing bridge/lifecycle context that blocks interpretation.
- Scheduler -> risk -> order: V150 consumer repairs have focused coverage but no replay effect yet.
- Order -> lifecycle/fill: lifecycle-label context is missing for candidate-namespace materialized axes (`21` axes) and many selected-package bridge axes (`455+28` broader classification rows).
- Fill -> exit: unchanged.
- Ledger/verifier: parity artifacts are deterministic but currently classify the next leak as bridge/lifecycle materialization.

## 7. Fixed / Partial / Open

- B0: DONE.
- B1: DONE.
- B2: DONE.
- B3: DONE WITH LABEL.
- B4: DONE WITH LABEL.
- B5: DONE.
- B6: DONE WITH LABEL.
- B7: PARTIAL. V150 targeted proof completed but behavior-neutral; V151 selected-package bridge/lifecycle context materialization is next.
- B8: OPEN. Broker/live/final remain false.

## 8. Highest-Leverage Same-Root Batch

V151 B7 same-root batch:

1. Materialize row-bound selected-package replay candidate or decision-window source before labeling executable axes as missing.
2. Materialize lifecycle-label context for candidate-namespace axes before counting them as selected-package source gaps.
3. Preserve the distinction between true non-executable source gaps and executable replay candidates that only lack bridge/lifecycle context.
4. Keep broker-cost REFUSED/source-gap rows non-executable and scoreable/missed only.

## 9. Affected Files And Patch Types

- `run_selected_package_replay_bridge.py`: correctness/diagnostic producer repair.
- `build_source_bound_execution_parity.py`: correctness/diagnostic consumer and bucket-label repair.
- `v4_timewarp_simulated_live_research_loop.py`: only if replay rows need to carry the bridge/lifecycle context into candidate/order/missed ledgers.
- Focused tests: parity/bridge tests first; timewarp tests only if consumer fields change.

## 10. Focused Proof Required Before Replay

- Compile touched Python modules.
- Run focused tests for bridge/parity classification.
- Rebuild source-bound parity for V150 or a fixture prefix; targeted replay only if a runtime consumer changes.

## 11. Expected Measurable Effect Before Replay

- Candidate -> scorecard transfer: unchanged unless runtime consumer is patched.
- Scorecard -> order transfer: unchanged unless runtime consumer is patched.
- Missed positive/negative R: should reclassify, not disappear.
- Parity buckets expected to shrink:
  - `executable_axis_missing_row_bound_selected_package_replay_candidate_or_decision_window`: `79`.
  - `executable_axis_candidate_namespace_materialized_no_lifecycle_label_context`: `21`.
- Trade count/R/W-L/F: expected neutral before runtime replay.
- Cost-refused/source-gap execution: must remain zero.

## 12. Success / Failure Criteria

Helped:

- The `79` and `21` priority buckets shrink or become exact non-executable source-gap labels with source evidence.
- No executable axis loses candidate/source provenance.
- No REFUSED/source-gap/off-authority row becomes executable.

Failed:

- The repair only adds helper fields with no consumer/verifier/test.
- Parity bucket counts stay identical after focused rebuild.
- Runtime replay is launched before producer, consumer, and tests are wired.
