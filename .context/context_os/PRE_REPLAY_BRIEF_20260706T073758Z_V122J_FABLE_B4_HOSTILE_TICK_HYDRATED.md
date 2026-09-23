# Pre-Replay Brief: V122J Fable B4 Hostile Tick-Hydrated Proof

Status: current control surface before the next replay. This is a bounded hostile five-day B4 proof, not full-reservoir transfer proof.

## 1. Latest Completed Replay

Latest completed replay prefix: `BROAD_LIVE_AS_IF_REPLAY_V122I_FABLE_B4_HOSTILE_5D_FILL_REALISM_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`.

Window: `2026-05-13..2026-05-17`. Profile: `repaired_package_conversion_v3`. Broker/live/final all false.

Numbers:
- candidates `23995`
- scorecard rows `288`
- summary order rows `115`
- filled trades `46`
- missed rows `23949`
- source universe rows `328`
- net R `+21.81176337`
- gross/final R `+25.21689165 / +25.21689165`
- cash PnL `$12599.05654101`
- risk cash `$27001.41545856`
- risk pct sum `25.3875`
- W/L/F `27/19/0`
- full/reduced fills `16/30`
- trade fill realism: `source_safe_immediate_marketable=43`, `passive_queue_confirmed=3`
- executable REFUSED/source-gap/M15-proxy/first-touch/live/final rows: all `0`

This smoke proves local hostile B4 behavior before full May tick hydration. It does not prove total reservoir conversion.

## 2. Running Processes

No broad replay is running. The May 13-18 tick export finished and the manifest was written after a `--reuse-existing` manifest rerun.

The initial export failed only at final provenance assembly because the command used stale scope `ordered_price_path_ticks_not_broker_lifecycle_truth`. The accepted scope is `ordered_price_path_only_not_broker_order_lifecycle_truth`. The exporter is patched and tested to reject this before MT5 initialization next time.

## 3. Baseline Comparison

V89D same-window baseline: `56` trades, `+34.84520454R` net, W/L/F `41/15/0`.

V90 same-window baseline: `51` trades, `+28.84201157R` net, W/L/F `37/14/0`.

V92 same-window baseline: `51` trades, `+29.35570236R` net, gross/final `+33.9321286`, cash PnL `$6228.63096022`, W/L/F `37/14/0`.

V121AG same-window baseline: `45` trades, `+21.82482975R` net, gross/final `+25.17869106`, cash PnL `$12465.17720161`, W/L/F `27/18/0`.

V122I versus V121AG: trades `+1`, net R `-0.01306638`, gross/final `+0.03820059`, cash PnL `+$133.8793394`, W/L delta `0/+1`; added `2` trades for `-1.09384428R`, removed `1` trade for `-1.0807779R`.

V122I versus V92: trades `-5`, net R `-7.54393899`, gross/final `-8.71523695`, cash PnL `+$6370.42558079`, W/L delta `-10/+5`; added `42` trades for `+18.38792381R`, removed `47` trades for `+26.29456921R`.

## 4. Dirty Files And Active Code Changes

Current active changes for this checkpoint:
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260706.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260706T073758Z_V122J_FABLE_B4_HOSTILE_TICK_HYDRATED_PREREPLAY.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260706T073758Z_V122J_FABLE_B4_HOSTILE_TICK_HYDRATED.md`
- `scripts/export_mt5_research_ticks.py`
- `tests/test_mt5_research_export_symbol_defaults.py`

There are many older unrelated dirty files in the worktree; do not stage or revert them as part of this checkpoint.

## 5. Subagent Findings

Rawls: older B4 tick-enabled replay command/readiness finding incorporated. Key points now applied: no `--skip-tick-source`, fresh Python replay process, parse exact summary/ledger fields.

Avicenna: older tick visibility finding incorporated. Key points now applied or previously committed: resolver-compatible FTMO mappings, lazy hash validation, actual first/last tick coverage, and manifest acceptance boundaries.

Aquinas: incorporated. It confirms V122I passes executable hostile fill-realism safety but B4 remains partial. It also flags a B5 comparison-binding gap: the V122I parity summary exists, but V121AG/V92 comparisons report `axis_transfer_delta_status=not_computed_missing_candidate_parity_summary`.

Laplace: incorporated. It confirms the V122I tick manifest has `24` symbols, `9,941,602` rows, resolver-compatible source truth scope, and all required resolver acceptance fields. It also confirms no blocking code patch is required before V122J; the remaining reuse-existing full-path test is non-blocking.

## 6. Known Mismatch Classes

Source-bound -> candidate: V122I generated `886/1101` exact-window axes. The global `1.249M R` diagnostic reservoir is not the denominator for this five-day proof.

Candidate -> selector: B1/B3 raw/effective selector and risk ladder provenance are closed on focused proof slices.

Selector -> scheduler: B2 reallocation/fillability truth is closed with label, but V122I still has a `B2_B3_scheduler_risk_reallocation_or_admission` missed bucket of `712` rows, `431` scoreable, `-86.67444635R` scoreable net.

Scheduler -> risk: V122I expresses risk with `16` full-risk and `30` reduced-risk fills. Continue reporting full/reduced separately.

Risk -> order: cost-refused/source-gap rows are non-executable and scoreable/missed. B6 remains open; do not loosen REFUSED.

Order -> fill: executable fills are realism-passing in V122I, but `source_gap=16585` and `ordered_tick_required_source_gap=2952` missed rows require the hydrated V122J rerun.

Fill -> exit: V122I stress/MC stays positive. Exit quality is downstream after B4/B6 proof.

Ledger/verifier: B5 is closed with label; V122J must preserve zero authority leaks.

Comparison proof: B5 is reopened to partial for parity-summary binding. V122J can run, but post-run comparisons must bind the V122J parity summary before axis-transfer deltas are used as proof.

## 7. Fixed / Partial / Open

Fixed:
- B0 truth baseline.
- B1 provenance truth.
- B2 fillability/reallocation truth with label.
- B3 risk ladder with label.
- B5 verifier/comparison precision with label.
- B4 exporter resumability and provenance fail-fast.

Partial:
- B4 fill-simulation realism. V122I executable truth is clean, but full May tick hydration was not available for that replay.

Open:
- B6 broker-cost calibration cell audit.
- B7 full proof ladder.
- B8 live path.

## 8. Highest-Leverage Same-Root Batch

Current batch: B4 fill-simulation/source realism.

Same-root repair/proof: rerun the hostile five-day proof after full 24-symbol ordered-tick hydration to distinguish missing-source artifacts from real non-executable diagnostic rows.

## 9. Files/Components Affected

Code/test changed:
- `scripts/export_mt5_research_ticks.py`: provenance validation now happens before MT5 initialization/export.
- `tests/test_mt5_research_export_symbol_defaults.py`: regression proves bad owner-authorized scope fails before MT5 initialization.

Replay artifacts expected:
- V122J broad replay summary/order/trade/missed/source/oracle ledgers.
- V122J B4 blocker classification.
- V122J flow diagnostic summary/dossier.
- V122J source-bound parity summary/ledger and leakage plan.
- V122J comparisons against V121AG and V92.

## 10. Patch Type

Exporter change: correctness/infrastructure repair. It should be behavior-neutral for valid replay inputs.

V122J replay: behavior measurement after source hydration, not policy tuning.

## 11. Expected Measurable Effect

Candidate -> scorecard: should stay near V122I (`23995 -> 288`) unless tick source changes materialization unexpectedly.

Scorecard -> order: source-gap/order-tick-required blockers should fall if they were missing-source artifacts.

Order -> fill: fills may increase, decrease, or reclassify. Any added executable fill must be realism-passing.

Missed positive R: must remain visible by exact reason. No positive-by-suppression accepted.

Missed negative R: must remain visible by exact reason. No hidden diagnostic loss bucket accepted.

Trade count: may move from V122I `46`; any movement must be explained by source binding or exact downstream blocker.

Net/gross/final R: may improve or worsen; delta must be attributed to tick-hydrated source binding, not hand-tuned suppression.

W/L/F: must be reported.

Cost-refused/source-gap execution: must stay `0`.

Risk-reduced/full-risk distribution: report full and reduced separately; V122I baseline is `16/30`.

## 12. Prove / Fail / Expose Criteria

Helped: source-gap/order-tick-required diagnostics collapse or become exact non-executable labels; executable fills remain realism-passing; V121AG/V92 deltas are attributable.

Failed: valid ordered ticks exist but replay still emits generic source-gap for matching rows; M15/first-touch diagnostic paths execute; any broker/live/final leak appears.

Exposed next flaw: if B4 source gaps close and scoreable missed R remains dominated by cost refusal, proceed to B6 broker-cost calibration audit. If scheduler/risk or order-geometry buckets dominate after source closure, patch those exact same-root chains before B6.
