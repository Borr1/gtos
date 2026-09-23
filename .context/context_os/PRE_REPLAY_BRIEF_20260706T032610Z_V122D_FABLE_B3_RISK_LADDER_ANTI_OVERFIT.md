# V122D Fable B3 Anti-Overfit Pre-Replay Brief

Generated: `2026-07-06T03:26:10Z`

## 1. Latest Completed Replay
- Latest broad replay: `BROAD_LIVE_AS_IF_REPLAY_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR_20260513_20260517`.
- Window: `2026-05-13..2026-05-17`, hostile bounded bucket, not full-reservoir proof.
- Trades: `45`; net/gross/final R: `21.82482975` / `25.17869106` / `25.17869106`; W/L/F `27/18/0`.
- Latest B3 proof: `BROAD_LIVE_AS_IF_REPLAY_V122C_FABLE_B3_RISK_LADDER_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`.
- V122C one-day June 3 numbers: `14` trades, net/gross/final R `-1.8242459` / `-0.74330096` / `-0.74330096`, cash PnL `-1563.10136496`, W/L/F `5/9/0`, candidates `6603`, scorecard `96`, orders `32`, missed `6586`.

This next smoke proves or disproves B3 structural generalization only. It does not prove full-reservoir conversion.

## 2. Running Processes
No broad replay, verifier, pytest, or compile process is running. Context OS sidecars are running.

## 3. Baselines
- V122B vs V122C on June 3: behavior-neutral; all headline/candidate/order/scorecard/missed deltas `0`.
- V122C B3 checks: executed REFUSED `0`, executed source-gap `0`, live/final true `0`, full-risk signing bad rows `0`, scorecard/missed/order/trade missing ladders all `0`.
- V122C risk tiers: scorecard diagnostic `96`; missed diagnostic `6586`; orders full `8`, reduced `22`, diagnostic `2`; trades full `3`, reduced `11`.

## 4. Dirty Files / Active Changes
Active B3 route-owned changes:
- `src/components/selector_v4.py`
- `src/research/reduced_risk_action_reason_contract.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_selector_v4.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- Fable matrix and current root/pre-replay artifacts under `.context/context_os/`.
- V122C replay artifacts under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`.

There are many unrelated/pre-existing dirty files and deleted historical science ledgers. Do not revert them.

## 5. Subagent Findings
Fable is incorporated as the controlling B0-B8 plan. Prior subagent findings are incorporated where disk evidence exists in the matrix.

## 6. Mismatch Classes
- Source-bound -> candidate: unchanged by B3.
- Candidate -> selector: focused B3 configured-action semantics closed.
- Selector -> scheduler: B2 remains closed.
- Scheduler -> risk: V122C closed missing scorecard/missed ladder fields on June 3.
- Risk -> order: V122C preserved order/trade tier distribution and full-risk signing truth on June 3.
- Order -> lifecycle -> fill: B4 after B3.
- Ledger/verifier: full route verifier after B3 artifacts are complete.

## 7. Fixed / Partial / Open
- DONE: B0, B1, B2.
- PARTIAL: B3 focused patch and June-3 proof are done; anti-overfit proof is open.
- PARTIAL: B4/B5.
- OPEN: B6/B7/B8.

## 8. Highest-Leverage Same-Root Batch
Continue B3 with one structural anti-overfit proof on `2026-06-11`, a non-May, non-June-3 objective slice named in the Fable plan.

## 9. Files / Components
- Replay harness: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- Risk ladder code under `src/research_infra/v4_timewarp_simulated_live_research_loop.py`

## 10. Patch Types
No new code patch before this proof. This is targeted structural validation of the B3 correctness/proof repair.

## 11. Expected Measurable Effect Before Replay
- Candidate -> scorecard transfer: measured for the selected day, no direct expected change.
- Scorecard -> order transfer: measured for the selected day, no direct expected change.
- Order -> fill transfer: measured for the selected day, no direct expected change.
- Missed positive/negative R: attribution should carry diagnostic ladder causes.
- Trade count/net R/W-L: no expectation of positivity; only structural risk-ladder generalization.
- Cost-refused/source-gap execution: must remain `0`.
- Risk distribution: scorecard/missed/order/trade rows must carry explicit full/reduced/diagnostic ladder tiers and causes.

## 12. Proof Criteria
V122D helps if the anti-overfit day completes and preserves B3 truth:
- zero missing risk ladders on scorecard/missed/order/trade;
- zero executed REFUSED/source-gap rows;
- zero live/final true rows;
- full-risk rows have no missing signing conditions;
- reduced/diagnostic rows carry causes.

V122D fails if these truth surfaces regress, if the run is only partial, or if full-risk appears without signing conditions.
