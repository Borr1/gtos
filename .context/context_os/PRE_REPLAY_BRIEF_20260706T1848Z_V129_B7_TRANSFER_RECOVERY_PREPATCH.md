# V129 B7 Transfer Recovery Prepatch Brief

Generated UTC: 2026-07-06T18:48Z

Purpose: select the next B7 same-root patch batch before any new replay. This brief uses current disk/process evidence after commit `6a6fe2a6b4c2cad984a42dad22c91513aec5572c` and the Fable B0-B8 matrix.

## Process State

- No broad replay, route builder, route verifier, pytest, py_compile, or harness process was running at process check.
- Three B7 read-only explorers returned and were closed: Meitner, Boyle, Hypatia.
- Broker/live/final remain false. Local replay/package authority remains full.

## Latest Completed Replay

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`

Window: 2026-06-01..2026-06-05

- Candidates: 35191
- Scorecard rows: 480
- Order rows: 212
- Filled trades: 55
- Missed rows: 35085
- Net R: +1.12099062
- Gross/final R: +6.22739670 / +6.22739670
- Cash PnL: +3007.28429755
- Risk cash: 24524.77867515
- Risk pct sum: 24.25
- W/L/F: 38/17/0
- Full/reduced fills: 22/33
- Fill realism: ordered_tick_entry_touch 53, source_safe_immediate_marketable 2
- Executed REFUSED/source-gap/live/final rows: 0/0/0
- Same-window source-bound R: 531411.6867472403
- Package axes: 1101
- Candidate-generated axes: 888
- Scorecard/order-present axes: 33
- Filled axes: 23
- Axis-attributed executable R: -1.06981543

## Baseline Comparison

- V127B same window: 109 trades, -7.50803319R, source_safe_immediate_marketable fills 71, axis-attributed executable R -22.3190414.
- V128 vs V127B: trade delta -54, net R delta +8.62902381; added 32 trades for +0.24238086R, removed 86 trades for -8.38664295R, common 23.
- V104 same window: 46 trades, +14.73101491R, axis-attributed executable R +13.36917856.
- V128 vs V104: trade delta +9, net R delta -13.61002429; added 55 trades for +1.12099062R, removed 46 trades for +14.73101491R, common 0.
- V89D/V90/V92 are May hostile comparators only, not direct V128 window denominators: V89D +34.84520454R / 56 trades, V90 +28.84201157R / 51 trades, V92 +29.35570236R / 51 trades.

## Fable Batch State

- B0 DONE: truth instrumentation baseline.
- B1 DONE: provenance truth contract.
- B2 DONE: fillability and reallocation truth chain.
- B3 DONE WITH LABEL: risk-expression ladder and loss-bucket demotion.
- B4 DONE WITH LABEL: fill-simulation realism.
- B5 DONE: verifier and comparison precision.
- B6 DONE WITH LABEL: broker-cost calibration audit.
- B7 PARTIAL: proof ladder is verifier-green but transfer remains weak.
- B8 OPEN: live path remains closed until B7/B8 gates pass.

## Subagent Findings

- Meitner incorporated into this batch: scheduler soft guard and reallocation are collapsed into terminal vetoes. Dominant labels are `candidate_generated_not_scheduler_selected` 250 axes and `candidate_generated_selector_reduce_risk_not_scheduler_selected` 41 axes, with combined scheduler reallocation leakage about 292 axes / 477831.4401036222 source-bound R. Cost-refused rows must remain terminal.
- Boyle incorporated into this batch: all 46 V104 filled keys exist in V128 candidate/missed ledgers but 0 reach scorecard/order/trade. Of those, 23 are broker-cost REFUSED non-executable, 12 are materialization guard, 9 are scheduler/reallocation, and 2 are selector reduce-risk authority/materialization. The cost-passed direct recovery class is 11 keys for +4.60376235R in V104.
- Hypatia incorporated into this batch: selected_policy_replay:stop_loss has 13 ordered-tick fills for -14.31653698R. They pass source/completeness/expected-net provenance but show predecision executable-quality weakness through limit fillability, stop-hazard geometry, and reallocation quality. The fix must use causal predecision fields, not close_reason or net_r.

## Root Mismatch Classes

- source-bound -> candidate: PARTIAL. 888/1101 axes generate candidates, but only 33 reach scorecard/order and 23 fill.
- candidate -> selector -> scheduler: OPEN. Soft scheduler/materialization vetoes and reduce-risk runtime-ineligible paths terminate before reallocation.
- scheduler -> risk: PARTIAL. Full/reduced provenance is visible, but reduced/runtime-ineligible paths still affect allocation and recovery.
- risk -> order -> fill: FIXED WITH WATCH. V128 removed unauthorized immediate-marketability transfer without executed REFUSED/source-gap rows.
- fill -> exit: OPEN. Selected-policy stop-loss admission is provenance-calibrated but not executable-quality gated.
- ledger/verifier: FIXED WITH WATCH. V128 verifier is green; next fields must have producer, consumer, proof surface, and tests.

## Selected Same-Root Batch

Batch: V129 B7 transfer recovery.

Files expected:
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_timewarp_scheduler_materialization.py` if missed attribution needs a focused materialization surface
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py` if route verifier needs a fatal count or classification assertion

Patch requirements:
- Split scheduler hard terminal vetoes from reallocation-soft guard vetoes.
- Cost-refused/source-gap/stale authority rows remain terminal and non-executable.
- Cost-passed, source-bound, signed-authority soft-guard candidates become scoreable reallocation-pool candidates, not immediate broker orders.
- Timewarp finalizer consumes only bound scheduler reallocation-pool options and rejects terminal veto pool candidates.
- Preserve terminal-vs-soft labels into ledgers and missed rows.
- Add selected-policy executable-quality admission using predecision limit fillability, stop-hazard geometry, pressure, source boundary, and reallocation quality; do not use outcome fields.
- Add a V104 removed-key recovery classification surface if it can be produced from deterministic existing fields without hand labels.

Patch type: correctness and behavior-changing.

Expected measurable effect before replay:
- Candidate -> scorecard transfer should improve for cost-passed authority-valid soft-guard candidates.
- Scorecard -> order transfer should recover some of the 11 V104 cost-passed scheduler/reduce-risk keys.
- Order -> fill truth must keep ordered-tick/source-safe realism and zero REFUSED/source-gap execution.
- Missed positive R should fall only by recovered transfer, not by dropping accounting.
- Missed negative R may rise if bad selected-policy transfers are blocked and retained as missed.
- Trade count is not success by itself.
- Net/gross/final R should improve or expose the next deeper transfer/exit flaw.
- Full/reduced distribution must remain signed and causal.

Smallest proof after patch:
- Focused scheduler and timewarp tests first.
- If focused tests pass, run route verifier/audits and a targeted same-window V129 proof slice before any broad replay.
- Success means cost-passed soft-guard/reduce-risk candidates can reallocate while REFUSED/source-gap rows stay non-executable, and selected-policy executable-quality rows are blocked/demoted with causal predecision labels.
