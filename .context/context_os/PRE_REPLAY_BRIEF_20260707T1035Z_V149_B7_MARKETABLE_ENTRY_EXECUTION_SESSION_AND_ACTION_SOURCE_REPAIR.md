# V149 B7 Marketable-Entry Execution Session And Action Source Repair Pre-Replay Brief

Generated UTC: 2026-07-07T10:35:51Z

This brief advances the Fable execution matrix after completed V148 artifacts. It authorizes only the same bounded 2026-06-01..2026-06-05 targeted proof slice, not a broad replay.

## 1. Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, simulated orders `6`, trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`, cash PnL `+211.19447407`, risk cash `750.42443587`, risk pct sum `0.75`, W/L/F `3/0/0`.
- Invalid execution counts: executed REFUSED cost `0`, executed source-gap `0`, unresolved-fill-floor order/trade `0/0`, live/final authority rows `0`.
- Interpretation: V148 is behavior-identical to V147 at trade identity and R. It is a bounded local B7 proof, not a full-reservoir transfer claim.

## 2. Running Process State

No broad replay, targeted replay, verifier, py_compile, pytest, route builder, or route verifier process is running.

## 3. Baseline Comparison

- V89D hostile fullgrid 2026-05-13..17: 56 trades, `+34.84520454R`, cash `+8178.90660707`, W/L/F `41/15/0`.
- V90 hostile fullgrid 2026-05-13..17: 51 trades, `+28.84201157R`, cash `+6371.80465431`, W/L/F `37/14/0`.
- V92 hostile fullgrid 2026-05-13..17: 51 trades, `+29.35570236R`, cash `+6228.63096022`, W/L/F `37/14/0`.
- These are required hostile/stress references, not denominator-equivalent to the current June 1-5 five-symbol targeted proof.
- V148 vs V147: trade delta `0`, net delta `0`, added `0`, removed `0`.
- V148 vs V146: trade delta `+1`, net delta `+0.29090804R`, added `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, removed `0`.
- V148 vs V144: trade delta `0`, net delta `0`.

## 4. Dirty Files And Active Code Changes

Active V149 patch files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1035Z_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260707T1035Z_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR.md`

Pre-existing unrelated dirty files and old deleted raw science ledgers remain outside this checkpoint scope.

## 5. Subagent Findings Incorporated

- Fable plan/audit: incorporated as dependency control surface. B0-B6 remain done or done-with-label; B7 remains partial; B8 remains open.
- Prior Kepler/Archimedes/Curie findings: incorporated in V148. V148 focused proof passed but the targeted replay was behavior-neutral versus V147.
- Current disk evidence: incorporated. V148 missed rows show `22` preselected `package_marketable_limit_entry_guard_blocked` rows with broker cost passed, source complete, mostly fillable, and `+4.36251202R` opportunity proxy. The guard route shows concrete `route_session_applied`/`authority_session` but was blocked by raw off-configured provenance and by reading raw selector action instead of signed/materialized package action.

## 6. Mismatch Classes

- Source-bound -> candidate: partial. Candidate surface remains visible, but high-R rows still leak before order.
- Candidate -> selector: partial. Raw selector reject can coexist with signed/materialized open-reduced package authority for local replay.
- Selector -> scheduler: patched earlier for V148 self-lock; behavior-neutral versus V147.
- Scheduler -> risk/order: current V149 patch. The marketable-entry guard now records raw selector action separately but consumes effective/materialized/signed package action for immediate-limit authority, and concrete execution session beats raw route provenance for execution-session validation.
- Order -> lifecycle/fill: unchanged. Released rows still must pass order policy, lifecycle, fill realism, cost, and no-broker authority checks.
- Fill -> exit: unchanged.
- Ledger/verifier: route now records `selector_action_source`, `raw_selector_action_for_immediate_marketable_limit`, `concrete_execution_session_for_immediate_marketable_limit`, and `raw_off_configured_session_requires_explicit_authority`.

## 7. Fixed / Partial / Open

- B0: DONE.
- B1: DONE.
- B2: DONE.
- B3: DONE WITH LABEL.
- B4: DONE WITH LABEL.
- B5: DONE.
- B6: DONE WITH LABEL.
- B7: PARTIAL. V149 focused proof passed for the marketable-entry execution namespace and action-source repair; targeted replay still needed.
- B8: OPEN. Broker/live/final remain false.

## 8. Highest-Leverage Same-Root Batch

V149 B7 same-root batch:

1. Do not let raw `route_session=off_configured_session` override a concrete execution namespace session from `route_session_applied` or `authority_session`.
2. Do not let raw selector reject override signed/materialized/effective package open-reduced action in the marketable-entry immediate-limit guard.
3. Keep raw-only off-configured rows blocked unless explicit off-session authority exists.
4. Preserve raw and effective action/session provenance in the route ledger.

## 9. Affected Files And Patch Types

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: correctness/performance transfer repair.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: focused verifier coverage for concrete-session release, raw-reject/effective-open-reduced release, and raw-only off-configured blocking.
- Matrix/root-cause/cursor files: diagnostic control surface only.

## 10. Focused Proof Already Run

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "marketable_open_reduced_raw_off_configured or package_marketable_entry_guard_routes_open_reduced_as_immediate_marketable_limit_when_package_authorized or package_marketable_entry_guard_keeps_low_quality_market_entry_blocked or package_marketable_entry_guard_blocks_missing_cost_source_authority" -q`: `4 passed, 567 deselected`.

## 11. Expected Measurable Effect Before Replay

- Candidate -> scorecard transfer: expected unchanged near `6633 -> 480`.
- Scorecard -> order transfer: the `risk_finalizer_rejected_preselected_candidate:package_marketable_limit_entry_guard_blocked` class should shrink from `22` rows if downstream order/lifecycle accepts the release.
- Order -> fill transfer: some of the `19` fillable preselected guard-blocked rows may become order/fill candidates; raw-only or nonpreselected rows must remain blocked unless they independently pass signed authority.
- Missed positive R: should decrease from valid conversion or become reclassified to downstream order/lifecycle blocker; no missed rows should disappear without reason.
- Missed negative R: must remain visible and scoreable; nonpreselected guard-blocked rows are net negative and must not be globally opened.
- Trade count and R: can move either direction; any added/removed keys must be causal and compared to V148/V147/V146/V144.
- Cost-refused/source-gap/unresolved-fill-floor execution: must remain zero.
- Risk distribution: full-risk vs reduced-risk remains separately reported; this patch is not a global risk-promotion.

## 12. Replay Success / Failure Criteria

Helped:

- The preselected package-marketable guard-blocked class shrinks, or its false action/session blocker subreasons shrink materially.
- Added rows are signed, cost-passed, source-complete, fillable package rows with concrete execution session.
- Existing V148 valid trades are not removed without causal predecision reason.
- Invalid execution counts stay zero.

Failed:

- Improvement comes only from trade collapse.
- Any REFUSED, source-gap, unresolved-fill-floor, live, final, or off-authority row executes.
- The guard-blocked class still shows `raw_off_configured_session_requires_explicit_off_session_authority` or `immediate_marketable_limit_requires_trade_selector_action` for rows with concrete execution session and signed effective package action.
- Candidate/scorecard rows collapse without causal blocker proof.
