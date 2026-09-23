# V121I Pre-Replay Brief - Scheduler Reallocation And Order Bridge

Generated: 2026-07-05T04:30:34Z

This is a bounded one-day repair proof for 2026-05-15. It does not prove total reservoir conversion and must not be compared directly to the global 1.249M/286k/237k R reservoir.

## 1. Latest Completed Replay

Latest completed prefix: `BROAD_LIVE_AS_IF_REPLAY_V121H_DIAGNOSTIC_SOURCE_GAP_LIFECYCLE_BLOCK_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

- Window: 2026-05-15..2026-05-15
- Candidates / scorecards / order rows / simulated orders / accepted pending / trades / missed: 8174 / 96 / 9 / 8 / 1 / 1 / 8166
- Net R / gross R / final R / cash PnL: -1.03400946 / -1.0 / -1.0 / -1034.00946
- W/L/F: 0/1/0
- Expired unfilled: 0

## 2. Active Process State

No broad replay, denominator builder, pytest, or py_compile process is running. Do not duplicate a run.

## 3. Baselines

These are context comparators, not same-denominator proof for this one-day smoke.

| Run | Window | Trades | Orders | Scorecards | Missed | Net R | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | 243 | 288 | 24885 | +34.84520454 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | 233 | 288 | 24890 | +28.84201157 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | 239 | 288 | 24887 | +29.35570236 | 37/14/0 |
| V121H | 2026-05-15 | 1 | 9 | 96 | 8166 | -1.03400946 | 0/1/0 |

V92 five-day same-window source-bound context: `218870.181480028R`, `894` candidate axes, `39` scorecard/order axes, `25` filled axes, `+17.76833767R` executable R. V121I is only a same-day truth slice.

## 4. Dirty Files / Active Changes

- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260705T043034Z_V121I_SCHEDULER_REALLOCATION_ORDER_BRIDGE.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260705T043034Z_V121I_SCHEDULER_REALLOCATION_ORDER_BRIDGE.md`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `src/components/selector_v4.py`
- `src/components/ultimate_candidate_package.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_selector_v4.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

## 5. Subagent / Audit Findings

- Fable: incorporated. Current patch follows the saved B2/B3 truth-chain sequence, not live activation.
- Turing: incorporated. Router-refusal package replay materialization uses role disposition `admission_candidate`, not a narrow origin-family allowlist.
- Popper: incorporated. Entry-quality fill and execution-fill authority are split; router-refusal fill-floor false remains a hard order veto.
- Carver: incorporated. Scheduler/risk reallocation probes need signed source-bound soft guard authority and their own reallocation quality score.
- Current focused tests: incorporated. Valid scheduler-selected trade rows with package execution true but missing the newer order-executable mirror were blocked as authority missing.

## 6. Mismatch Classes

- Source-bound -> candidate: V121H generated 851/1101 axes and reached only 2 scorecard/order axes.
- Candidate -> selector: entry-quality fill and execution limit-fillability must stay separate.
- Selector -> scheduler: raw selector action and materialized/effective replay action must stay separate.
- Scheduler -> risk: soft guard vetoes were treated as hard reallocation failures.
- Risk -> order: missing order-executable mirror blocked valid scheduler-selected trade rows.
- Order -> lifecycle: diagnostic source-gap/fill-realism rows must not bind pending lifecycle.
- Lifecycle -> fill: filled versus missed rows need exact delay/skip/expire/fill reasons.
- Fill -> exit: V121H’s one filled XAUUSD short is a real loser; no exit repair is claimed here.
- Ledger: false package-executable rows that materialize are now verifier-fatal.

## 7. Fixed / Partial / Open

Fixed:
- execution fill probability is carried separately from entry-quality fill probability;
- false router-refusal fill-floor reasons are hard order vetoes;
- scheduler emits reallocation score, eligibility, hard failures, and guard penalty provenance;
- finalizer uses reallocation quality score for reallocation quality gates;
- finalizer derives missing order-executable mirror only for valid scheduler-selected `trade` rows with package execution true and broker-cost preflight passed.

Partial:
- source-bound transfer is still locally low until replay proves changed transfer;
- risk ladder distribution still needs replay proof;
- global reservoir transfer is not measured by this one-day smoke.

Open:
- parse missed-positive and missed-negative R after V121I;
- if local repair passes, run hostile five-day and then a non-May regime.

## 8. Highest-Leverage Same-Root Batch

Batch: scheduler reallocation and selected-package order bridge.

Affected files/components:
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: scheduler hard gates and reallocation score/provenance.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: finalizer soft-probe, quality gate score, order bridge, nested fillability rank source.
- `src/components/selector_v4.py` and `src/components/ultimate_candidate_package.py`: selector/package execution-fill parity already in patch set.
- verifier and tests listed above.

Patch types:
- correctness: signed source-bound soft guard route and order-executable bridge;
- performance: reallocation candidates can compete instead of going flat;
- diagnostic/ledger: exact provenance fields and verifier false-materialization check.

## 9. Expected Effects Before Replay

- Candidate -> scorecard: unchanged or improves if router-refusal role bridge was the blocker.
- Scorecard -> order: valid scheduler-selected package trade rows should stop failing only because the order-executable mirror is missing.
- Order -> fill: may increase if authority-missing was the local blocker; false/refused/source-gap rows must remain zero-executed.
- Missed positive R: should move from generic scheduler/risk/order authority missing into exact guard/reallocation/order-fill reasons.
- Missed negative R: may also move; this is not a suppress-to-win patch.
- Trade count: should not collapse to zero; any added trade must be classified net positive or net negative.
- Net/gross/final R and W/L/F: may improve or worsen; correctness is exact transfer and no hard-veto leak.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk: report distribution separately from replay ledgers.

## 10. Replay Command

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-15 \
  --end 2026-05-15 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V121I_SCHEDULER_REALLOCATION_ORDER_BRIDGE_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --skip-tick-source \
  --compact-missed-ledger
```

## 11. Success / Failure Criteria

Helped:
- `risk_admitted_scheduler_reallocation_score` appears on eligible scheduler/finalizer probes;
- `package_replay_order_executable_authority_missing` drops for valid selected trade rows;
- added/removed trades and missed R are stage-attributed;
- executed REFUSED/source-gap/explicit false rows remain zero.

Failed:
- rows still die at `option_not_runtime_eligible` or `scheduler_score` despite signed source-bound reallocation score;
- explicit false package rows materialize;
- headline improvement comes only from fewer trades and more unexplained missed positive R;
- the one-day smoke is mistaken for full-reservoir proof.

