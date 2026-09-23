# V150 B7 Signed Action, Finalizer Route, And Immediate-Preflight Consumer Repair Pre-Replay Brief

Generated UTC: 2026-07-07T11:41:17Z

This brief advances the Fable execution matrix after completed V149 artifacts and
focused V150 proof. It authorizes only the same bounded
2026-06-01..2026-06-05 targeted proof slice, not a broad replay.

## 1. Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, simulated orders `6`, trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`, cash PnL `+211.19447407`, risk cash `750.42443587`, risk pct sum `0.75`, W/L/F `3/0/0`.
- Invalid execution counts: executed REFUSED cost `0`, executed source-gap `0`, unresolved-fill-floor order/trade `0/0`, live/final authority rows `0`.
- Interpretation: V149 is behavior-identical to V148/V147 at trade identity and R, but shifted the next visible leak into consumer mismatch buckets. This remains a bounded local B7 proof, not a full-reservoir transfer claim.

## 2. Running Process State

No broad replay, targeted replay, verifier, py_compile, pytest, route builder, or
route verifier process is running at brief creation.

## 3. Baseline Comparison

- V89D hostile fullgrid 2026-05-13..17: 56 trades, `+34.84520454R`, cash `+8178.90660707`, W/L/F `41/15/0`.
- V90 hostile fullgrid 2026-05-13..17: 51 trades, `+28.84201157R`, cash `+6371.80465431`, W/L/F `37/14/0`.
- V92 hostile fullgrid 2026-05-13..17: 51 trades, `+29.35570236R`, cash `+6228.63096022`, W/L/F `37/14/0`.
- These are hostile/stress references, not denominator-equivalent to the current June 1-5 five-symbol targeted proof.
- V149 vs V148: trade delta `0`, net delta `0`, added `0`, removed `0`.
- V149 vs V147: trade delta `0`, net delta `0`.
- V149 vs V146: trade delta `+1`, net delta `+0.29090804R`, added `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, removed `0`.
- V149 vs V144: trade delta `0`, net delta `0`.

## 4. Dirty Files And Active Code Changes

Active V150 patch files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1141Z_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260707T1141Z_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR.md`

Pre-existing unrelated dirty files and old deleted raw science ledgers remain
outside this checkpoint scope.

## 5. Subagent Findings Incorporated

- Fable plan/audit: incorporated as dependency control surface. B0-B6 remain done or done-with-label; B7 remains partial; B8 remains open.
- Kepler/Archimedes/Curie: incorporated in V148. V148 focused proof passed but targeted replay was behavior-neutral versus V147.
- Socrates: incorporated in V150. Immediate-marketable route production was correct, but `marketable_limit_immediate_fill_candidate()` consumed raw `route_session=off_configured_session`, causing routed rows to fall into `passive_limit_too_close_predecision_guard`.
- Hilbert: incorporated in V150. Runtime risk authority could still derive release/sizing from raw reject before signed/materialized package action. A direct risk-authority regression now proves raw reject is preserved while effective signed open-reduced action releases positive replay risk.

## 6. Mismatch Classes

- Source-bound -> candidate: partial. Candidate surface remains visible, but high-R rows still leak before order.
- Candidate -> selector: partial but improved. Raw selector reject is preserved separately from signed/materialized package action.
- Selector -> scheduler: patched in V148. Producer-side raw/effective split is not the main current leak.
- Scheduler -> risk: current V150 patch. `reduced_selector_action_for_authority_surfaces()` now consumes signed/materialized package action with authority, and finalizer action resolution includes package authority action before calling runtime risk authority.
- Risk -> order: current V150 patch. Runtime risk proof now preserves raw reject and effective open-reduced separately while releasing package replay risk only for signed executable rows.
- Order -> lifecycle/fill: current V150 patch at preflight. Immediate-marketable route execution uses concrete execution session authority before applying passive-limit-too-close.
- Fill -> exit: unchanged.
- Ledger/verifier: focused tests cover producer/consumer/proof surfaces. Broader verifier scans remain pending after targeted replay.

## 7. Fixed / Partial / Open

- B0: DONE.
- B1: DONE.
- B2: DONE.
- B3: DONE WITH LABEL.
- B4: DONE WITH LABEL.
- B5: DONE.
- B6: DONE WITH LABEL.
- B7: PARTIAL. V150 focused proof passed for signed-action, finalizer-route, runtime-risk, and immediate-preflight consumer parity; targeted replay still needed.
- B8: OPEN. Broker/live/final remain false.

## 8. Highest-Leverage Same-Root Batch

V150 B7 same-root batch:

1. Do not let raw reject override signed/materialized package open-reduced action in risk release/sizing.
2. Do not let stale flattened guard-blocked fields outrank finalizer immediate-marketable route truth.
3. Do not let immediate-marketable routed rows leak into passive-limit-too-close preflight because raw route provenance says off-configured.
4. Keep raw-only off-configured rows, REFUSED cost, source-gap cost, invalid signed authority, and nonpreselected net-negative variants non-executable.

## 9. Affected Files And Patch Types

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: correctness/performance transfer repair.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: focused verifier coverage for signed action projection, final blocker precedence, immediate-fill authority, preflight routing, and runtime-risk raw/effective action split.
- Matrix/root-cause/cursor files: diagnostic control surface only.

## 10. Focused Proof Already Run

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Exact timewarp pytest with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`: `12 passed, 1 warning`.

## 11. Expected Measurable Effect Before Replay

- Candidate -> scorecard transfer: expected unchanged near `6633 -> 480`.
- Scorecard -> order transfer: may increase only for signed, cost-passed, source-complete, concrete-session package rows.
- Order -> fill transfer: immediate-marketable contracted rows should either order/fill or move to a downstream causal blocker, not `passive_limit_too_close_predecision_guard`.
- Missed positive R: should decrease or be reclassified from V149 preselected buckets:
  - generic `risk_finalizer_rejected_preselected_candidate`: `12` rows, `+2.29904221R` net proxy.
  - marketable guard blocked: `7` rows, `+3.90723626R` net proxy.
  - passive-too-close preflight: `10` rows, `+0.35693456R` net proxy.
- Missed negative R: must remain visible and scoreable; nonpreselected variants are net negative and must not be globally opened.
- Trade count and R: can move either direction; any added/removed keys must be causal and compared to V149/V148/V147/V146/V144.
- Cost-refused/source-gap/unresolved-fill-floor execution: must remain zero.
- Risk distribution: full-risk vs reduced-risk remains separately reported; this patch is not a global risk-promotion.

## 12. Replay Success / Failure Criteria

Helped:

- V149 preselected consumer-mismatch buckets shrink or reclassify to later true blockers.
- Added rows are signed, cost-passed, source-complete, fillable package rows with concrete execution session.
- Existing V149 valid trades are not removed without causal predecision reason.
- Invalid execution counts stay zero.

Failed:

- Improvement comes only from trade collapse.
- Any REFUSED, source-gap, unresolved-fill-floor, live, final, or raw-only off-authority row executes.
- Rows with `package_marketable_limit_entry_routed_to_immediate_marketable_limit` still block on `passive_limit_too_close_predecision_guard`.
- Rows with raw `reject`, signed/materialized risk-bearing action, cost passed, source complete, fillable/order-executable status, and positive scheduler risk still produce `final_approved_risk_pct=0` with pass-like risk reasons.
- Candidate/scorecard rows collapse without causal blocker proof.
