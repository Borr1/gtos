# V122C Fable B3 Pre-Replay Brief

Generated: `2026-07-06T03:18:36Z`

## 1. Latest Completed Replay
- Latest broad replay: `BROAD_LIVE_AS_IF_REPLAY_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR_20260513_20260517`.
- Window: `2026-05-13..2026-05-17`, hostile bounded bucket, not full-reservoir proof.
- Trades: `45`; net/gross/final R: `21.82482975` / `25.17869106` / `25.17869106`.
- Cash PnL: `12465.17720161`; W/L/F `27/18/0`.
- Exact-window denominator: source-bound R `407295.6072920759`; package axes `1101`; candidate axes `886`; scorecard/order axes `33`; filled axes `29`; actual executable R `21.29589138`.
- Latest focused Fable proof: `BROAD_LIVE_AS_IF_REPLAY_V122B_FABLE_B2_PRIORITY_CONTEXT_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`.
- V122B one-day June 3 numbers: `14` trades, net/gross/final R `-1.8242459` / `-0.74330096` / `-0.74330096`, cash PnL `-1563.10136496`, W/L/F `5/9/0`, `15` orders, `1` expired, `6603` candidates, `96` scorecard rows, `6586` missed rows.

This smoke will prove or disprove the local B3 repair only. It does not prove total source-bound reservoir conversion.

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
Active B3 route-owned changes:
- `src/components/selector_v4.py`
- `src/research/reduced_risk_action_reason_contract.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_selector_v4.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260706.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260706T031836Z_V122C_FABLE_B3_RISK_LADDER_PREREPLAY.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260706T031836Z_V122C_FABLE_B3_RISK_LADDER.md`

There are many unrelated/pre-existing dirty files and deleted historical science ledgers. Do not revert them.

## 5. Subagent Findings
- Fable: incorporated as the controlling B0-B8 plan and audit.
- Prior subagents: incorporated where disk evidence exists in the matrix. Remaining prior-agent claims are durable recall only, not authority unless backed by current files/tests/artifacts.

## 6. Mismatch Classes
- Source-bound -> candidate: partial; B3 does not alter generation.
- Candidate -> selector: B3 focused patch closes configured off-session/dynamic-router open-reduced semantics.
- Selector -> scheduler: B2 remains closed; B3 did not change scheduler ranking.
- Scheduler -> risk: B3 focused patch closes stranded prefixed scorecard/finalizer ladder surfaces.
- Risk -> order: projection scan shows order/trade tier distributions are preserved while scorecard/missed missing ladder rows close.
- Order -> lifecycle -> fill: B4 after B3.
- Fill -> exit: later.
- Ledger/verifier: B3 focused verifier checks pass; full route verifier should run after V122C artifacts exist.

## 7. Fixed / Partial / Open
- DONE: B0 truth audit baseline.
- DONE: B1 raw/effective provenance and R identity focused proof.
- DONE: B2 fillability/reallocation priority context and executable-surface truth.
- PARTIAL: B3 risk-expression ladder and loss-bucket demotion; focused code/tests/projection are green, replay proof open.
- PARTIAL: B4 fill realism and B5 verifier precision.
- OPEN: B6 broker-cost calibration audit, B7 proof ladder, B8 live path.

## 8. Highest-Leverage Same-Root Batch
Selected batch remains `B3 risk-expression ladder and loss-bucket demotion`.

The same-root patch already made:
- configured off-session and dynamic-router open-reduced reasons executable in selector semantics;
- scorecard/finalizer prefixed ladders consumable by top-level risk ladder normalization;
- no-probe/non-materialized missed rows explicit diagnostic ladder rows instead of blank provenance.

## 9. Files / Components
- `src/components/selector_v4.py`
- `src/research/reduced_risk_action_reason_contract.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_selector_v4.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`

## 10. Patch Types
- Selector configured-action semantics: correctness repair.
- Risk ladder prefixed-surface consumer repair: diagnostic/proof repair with no intended standalone trade suppression.
- Missed/scorecard diagnostic ladder synthesis: diagnostic/proof repair.

## 11. Expected Measurable Effect Before Replay
- Candidate -> scorecard transfer: expected unchanged.
- Scorecard -> order transfer: expected unchanged unless selector configured-action semantics expose valid authority.
- Order -> fill transfer: expected unchanged.
- Missed positive/negative R: attribution should improve; no positive-by-suppression accepted.
- Trade count: expected unchanged or small semantic-action delta only.
- Net/gross/final R and W/L/F: expected unchanged or small semantic-action delta only.
- Cost-refused/source-gap execution: must remain `0`.
- Risk distribution: scorecard/missed/order/trade rows must carry explicit full/reduced/diagnostic ladder tiers and causes.

Projection scan on existing V122B artifacts with the new normalizer:
- Scorecard ladder missing rows: `24 -> 0`.
- Missed-opportunity ladder missing rows: `4289 -> 0`.
- Order ladder missing rows: `0 -> 0`, tiers remain diagnostic `2`, full `8`, reduced `22`.
- Trade ladder missing rows: `0 -> 0`, tiers remain full `3`, reduced `11`.

## 12. Proof Criteria
V122C helps if:
- Focused selector/scheduler/timewarp/verifier tests stay green.
- `py_compile` stays green for touched modules.
- One-day replay rows show zero missing risk ladder fields on scorecard/missed/order/trade surfaces.
- Full-risk rows satisfy signing conditions; reduced/diagnostic rows carry causes.
- Executed REFUSED/source-gap rows remain `0`.
- Live/broker mutation and final-selection true rows remain `0`.

V122C fails if:
- Full-risk rows execute without signed package authority, broker-cost pass, source completeness, fillability resolution, and full-risk allowed/applied.
- Reduced/diagnostic rows lose demotion causes before order/trade/missed ledgers.
- Improvement comes only from suppressing opportunity.
- The run is interrupted and only partial artifacts exist.
