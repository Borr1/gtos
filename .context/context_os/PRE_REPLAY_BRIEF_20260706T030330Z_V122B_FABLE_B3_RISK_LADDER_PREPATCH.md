# V122B Fable B3 Pre-Replay Brief

Generated: `2026-07-06T03:03:30Z`

## 1. Latest Completed Replay
- Latest broad replay: `BROAD_LIVE_AS_IF_REPLAY_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR_20260513_20260517`.
- Window: `2026-05-13..2026-05-17`, hostile bounded bucket, not full-reservoir proof.
- Trades: `45`; net/gross/final R: `21.82482975` / `25.17869106` / `25.17869106`.
- Cash PnL: `12465.17720161`; W/L/F `27/18/0`.
- Exact-window denominator: source-bound R `407295.6072920759`; package axes `1101`; candidate axes `886`; scorecard/order axes `33`; filled axes `29`; actual executable R `21.29589138`.
- Latest focused Fable proof: `BROAD_LIVE_AS_IF_REPLAY_V122B_FABLE_B2_PRIORITY_CONTEXT_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`.
- V122B one-day June 3 proof numbers: `14` trades, net/gross/final R `-1.8242459` / `-0.74330096` / `-0.74330096`, cash PnL `-1563.10136496`, W/L/F `5/9/0`, `15` orders, `1` expired, `6603` candidates, `96` scorecard rows, `6586` missed rows.

This smoke proves local B2 correctness only. It does not prove total source-bound reservoir conversion.

## 2. Running Processes
No broad replay, verifier, pytest, or compile process is running. Context OS sidecars are running.

## 3. Baselines
- V89D hostile five-day: `56` trades, `+34.84520454R`, W/L/F `41/15/0`.
- V90 hostile five-day: `51` trades, `+28.84201157R`, W/L/F `37/14/0`.
- V92 hostile five-day: `51` trades, `+29.35570236R`, W/L/F `37/14/0`.
- V121AG hostile five-day: `45` trades, `+21.82482975R`, W/L/F `27/18/0`.
- V121AG vs V92: `-6` trades and `-7.53087261R`; added V121AG trades `40/+19.48176809R`; removed V92 trades `46/+27.37534711R`; common trade delta `+0.36270641R`.
- V122B vs V122 B1 one-day June 3: behavior-neutral; all headline deltas `0`.

## 4. Dirty Files / Active Changes
Active B0-B2 route-owned changes include:
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260706.md`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- V122/V122B focused proof artifacts under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`
- refreshed route verifier artifacts from B1.

There are many unrelated/pre-existing dirty files and deleted historical science ledgers. Do not revert them.

## 5. Subagent Findings
- Fable: incorporated as the controlling B0-B8 plan and audit.
- Prior subagents: incorporated where disk evidence exists in the V122 matrix. Remaining prior-agent claims are durable recall only, not authority unless backed by current files/tests/artifacts.

## 6. Mismatch Classes
- Source-bound -> candidate: partial; exact-window axes are visible but not fully converted. Broad/full-reservoir claims wait for B7.
- Candidate -> selector: B1 provenance closed; B3 still needs off-configured configured-action semantics and risk admission causes.
- Selector -> scheduler: B2 priority context closed; reduced rows are not demoted until eligible primary trade competitor context is known.
- Scheduler -> risk: open next; risk ladder must make full/reduced/diagnostic signed and causal.
- Risk -> order: open next; risk provenance must survive into scorecard/order/trade/missed ledgers.
- Order -> lifecycle -> fill: B4 after B3.
- Fill -> exit: later; do not tune exits before B3/B4 truth surfaces.
- Ledger/verifier: B5 after B3 proof artifacts.

## 7. Fixed / Partial / Open
- DONE: B0 truth audit baseline.
- DONE: B1 raw/effective provenance and R identity focused proof.
- DONE: B2 fillability/reallocation priority context and executable-surface truth.
- PARTIAL: B3 risk-expression ladder and loss-bucket demotion.
- PARTIAL: B4 fill realism and B5 verifier precision.
- OPEN: B6 broker-cost calibration audit, B7 proof ladder, B8 live path.

## 8. Highest-Leverage Same-Root Batch
Selected batch: `B3 risk-expression ladder and loss-bucket demotion`.

Reason: with B1/B2 closed, the next root mismatch is whether the system expresses conviction correctly. V122B still has risk decisions `open-reduced-risk=9`, `reduce-risk=2`, `trade=4`; B3 must prove that full risk is reachable only for signed, broker-cost-passed, source-complete, fillable, top-ranked package candidates and that reduced/diagnostic rows preserve exact causal demotion.

## 9. Files / Components
- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_selector_v4.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`

## 10. Patch Types
- B3 selector off-configured action semantics: correctness repair.
- B3 risk ladder producer/consumer propagation: correctness and behavior repair.
- B3 ledger/verifier additions: diagnostic/proof repair with no intended standalone behavior change.

## 11. Expected Measurable Effect Before Replay
- Candidate -> scorecard transfer: unchanged unless off-configured action semantics expose newly valid package authority.
- Scorecard -> order transfer: may increase for valid signed full-risk rows and may decrease for invalid diagnostic rows.
- Order -> fill transfer: should not be changed directly by B3.
- Missed positive/negative R: attribution should improve; no positive-by-suppression accepted.
- Trade count: may change only through corrected risk authority.
- Net/gross/final R and W/L/F: behavior-changing only if corrected risk expression changes executable authority.
- Cost-refused/source-gap execution: must remain `0`.
- Risk distribution: full-risk vs reduced-risk must be separated and causally attributed.

## 12. Proof Criteria
B3 helps if:
- Focused selector/scheduler/timewarp/verifier tests pass.
- `py_compile` passes for touched modules.
- Ledger rows expose raw selector action, effective selector action, risk ladder tier, tier causes, final risk pct, full-risk allowed/applied, broker-cost/source-complete/fillability/top-ranked conditions, and downstream trade/order/missed provenance.
- A one-day targeted proof shows no executed REFUSED/source-gap rows, no live/final rows, and full/reduced risk distribution is explainable from predecision causes.

B3 fails if:
- Off-configured open-reduced authority collapses to reduce-risk without explicit configured-action contract.
- Full-risk rows execute without signed package authority, broker-cost pass, source completeness, fillability resolution, and top-ranked/scheduler authority.
- Reduced/diagnostic rows lose demotion causes before order/trade/missed ledgers.
- Positive behavior comes only from suppressing opportunity.
