# V122 Fable B0/B1 Pre-Replay Brief

Generated: `2026-07-05T22:53:54Z`

## 1. Latest Completed Replay
- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR_20260513_20260517`.
- Window: `2026-05-13..2026-05-17`, bounded hostile bucket, not full-reservoir proof.
- Trades: `45`; net/gross/final R: `21.82482975` / `25.17869106` / `25.17869106`.
- Cash PnL: `12465.17720161`; risk cash `26023.79295971`; risk pct sum `24.5125`.
- W/L/F: `27/18/0`.
- Exact-window denominator: source-bound R `407295.6072920759`; package axes `1101`; candidate axes `886`; scorecard/order axes `33`; filled axes `29`; actual executable R `21.29589138`.

## 2. Running Processes
No broad replay is running. The read-only MT5 tick probe completed and wrote:
`research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/mt5_tick_probes/tick_availability/v121ah_may_tick_gap_probe_20260705T224825Z.json`.

That probe is not a replay result. It proves the bridge can provide sampled May 2026 ordered-tick windows for later B2/B4 fillability and fill-realism work.

## 3. Baselines
- V121AG vs V121AF: trade delta `+1`, net R delta `+1.56450959`; added `2` trades `+1.29477854R`; removed `1` trade `-0.26973105R`.
- V121AG vs V92: V92 had `51` trades, `+29.35570236R`, W/L/F `37/14/0`. V121AG is `-6` trades and `-7.53087261R`; added `40` V121AG trades for `+19.48176809R`; removed `46` V92 trades for `+27.37534711R`; common trade delta `+0.36270641R`.
- V89D/V90 are historical comparators and are not rerun in this checkpoint. They remain baseline names for the B7 proof ladder, not proof denominators for this B0/B1 patch.

## 4. Dirty Files / Active Changes
Active route-owned dirty files include timewarp, selector, scheduler allocator, route builders/verifiers/harness files, and focused tests. The Fable implementation sequence and root-cause audit were saved under `.context/context_os/fable_ultimate_plan/`.

Local B1 patch completed in this main session:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: terminal lifecycle account rows now pass `final_r`, `net_proxy_r`, `gross_r`, and `expected_cost_r` to `account_row()`.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: terminal lifecycle account row now asserts public `final_r` remains gross/final while `net_proxy_r` remains net.

## 5. Subagent Findings
- Kant the 2nd: incorporated. Cost-refused and negative-EV diagnostics were over-counted as downstream selector materialization.
- Copernicus the 2nd: incorporated. Current loss bucket does not justify stop geometry tuning; positive selected-policy diagnostics require ordered-tick authority.
- Nietzsche the 2nd: incorporated. V121AG vs V92 is a downstream transfer regression, concentrated in order/fillability, scheduler/reallocation, and risk expression.
- Gibbs the 2nd: running. B0 provenance audit script/output ownership.
- Noether the 2nd: running. B1 selector raw/effective action contract ownership.
- Hilbert the 2nd: running. B1 scheduler metadata raw/effective action contract ownership.

## 6. Mismatch Classes
- Source-bound -> candidate: partial. V121AG generated `886/1101` exact-window axes; candidate rows are unchanged vs V92.
- Candidate -> selector: open. Fable A1/B1 shows raw/effective selector action semantics are fragmented and structural full-risk selection is not yet expressible.
- Selector -> scheduler: open. B1 must preserve raw origin while writing materialized/effective action separately.
- Scheduler -> risk: partial. Timewarp risk authority already reads `scheduler_materialization_original_selector_action`; selector/scheduler workers are closing remaining paths.
- Risk -> order/fill/lifecycle: open next batch. B2/B3 handle fill-floor, reallocation, fallback/expiry, and risk ladder once B1 provenance is trustworthy.
- Fill -> exit: deferred. Do not tune exits/stops from the current bucket until ordered-tick/fill-realism authority is materialized.
- Ledger/verifier: partial. Terminal lifecycle account-row gross/net identity is patched locally; B0 and later B5 verifier precision remain.

## 7. Fixed / Partial / Open
- Fixed in prior checkpoints: cost-refused non-executable classification, source-gap missed accounting, effective stop-hazard cap truth, V121AG parity artifact refresh, route verifier green for V121AG.
- Fixed in this checkpoint: terminal lifecycle account-row helper receives gross/net/cost truth directly.
- Partial: selector/scheduler raw/effective action preservation, B0 audit script, provenance collapse baseline.
- Open: B2 fillability/reallocation chain, B3 risk-expression ladder and bucket demotion, B4 fill realism, B5 verifier precision, B6 broker-cost calibration audit, B7 proof ladder, B8 live path.

## 8. Highest-Leverage Same-Root Batch
Active batch: `V122_FABLE_B0_B1_PROVENANCE_TRUTH`.

Reason: Fable's audit shows proof and behavior are both distorted if raw selector action, effective/materialized selector action, risk authority, and R identity remain fragmented. This batch must land before interpreting B2/B3 replay results.

## 9. Files / Components
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/audit_provenance_and_flags_v114.py`
- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_selector_v4.py`
- `tests/test_timewarp_scheduler_materialization.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

## 10. Patch Types
- B0: diagnostic baseline artifact, no behavior change.
- B1: correctness repair plus ledger/provenance repair, intended behavior-neutral except where previous provenance/accounting truth was wrong.

## 11. Expected Measurable Effect Before Replay
- Candidate -> scorecard transfer: unchanged for B1.
- Scorecard -> order transfer: unchanged for B1.
- Order -> fill transfer: unchanged for B1.
- Missed positive/negative R: unchanged for B1, but attribution should become trustworthy.
- Trade count and W/L/F: unchanged for B1 targeted proof; any movement means an unintended behavior change leaked.
- Net/gross/final R: no trade-set change expected; gross/net identity drift should go to zero in B0/B1 scans.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: measured more honestly but not policy-changed until B3.

## 12. Proof Criteria
B0/B1 helped if:
- B0 audit outputs materialize and record provenance-collapse/R-identity/fallback-expiry/raw-failure/cost-refusal baselines.
- Unit tests for selector, scheduler materialization, timewarp R identity, and B0 script pass.
- `py_compile` passes for touched modules.
- No broad replay is started until B0/B1 truth checks are green.

B0/B1 failed if:
- A focused B1 proof changes trade set or R without an intentional behavior patch.
- Raw selector origin still collapses to materialized action in scheduler/risk/order/trade surfaces.
- Any account/trade row still cannot satisfy `gross_r - expected_cost_r == net_proxy_r` when all fields are present.
