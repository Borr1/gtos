# V121J Pre-Replay Brief - Order Taxonomy And Runtime Release Truth

Generated: 2026-07-05T05:09:28Z

This is a bounded one-day repair proof for 2026-05-15. It proves or disproves a truth/materialization batch only. It must not be compared directly to the global 1.249M/286k/237k R reservoir.

## 1. Latest Completed Replay

Latest completed prefix: `BROAD_LIVE_AS_IF_REPLAY_V121I_SCHEDULER_REALLOCATION_ORDER_BRIDGE_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

- Window: 2026-05-15..2026-05-15
- Candidates / scorecards / orders / oracle rows / trades / missed: 8174 / 96 / 2 / 2 / 0 / 8172
- Net R / gross R / final R / cash PnL / risk cash: 0 / 0 / 0 / 0 / 0
- W/L/F: 0/0/0
- Scoreable missed rows / scoreable diagnostic opportunity R: 1476 / -1158.8468346R
- Broker sends: 0
- Broker/live/final: false / false / false

V121I versus V121H same-window: orders 9 -> 2, trades 1 -> 0, missed 8166 -> 8172, net R -1.03400946 -> 0. That is truth-positive because the invalid loser was removed, but it is not performance proof because no trades filled.

## 2. Active Process State

No broad replay, denominator builder, pytest, py_compile, or stale git helper is running in this repo. Do not duplicate a run.

## 3. Baselines

V89D/V90/V92 are hostile five-day comparators, not same-denominator proof for this one-day smoke.

| Run | Window | Trades | Orders | Scorecards | Missed | Net R | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | 243 | 288 | 24885 | +34.84520454 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | 233 | 288 | 24890 | +28.84201157 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | 239 | 288 | 24887 | +29.35570236 | 37/14/0 |
| V121H | 2026-05-15 | 1 | 9 | 96 | 8166 | -1.03400946 | 0/1/0 |
| V121I | 2026-05-15 | 0 | 2 | 96 | 8172 | 0 | 0/0/0 |

## 4. Dirty Files / Active Code Changes

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Other pre-existing dirty files remain in the route/control surface and are not reverted.

## 5. Subagent / Audit Findings

- Fable: incorporated. Current patch stays in B2/B3 truth/materialization and does not open live.
- Avicenna: incorporated. V121I’s highest current leak is order materialization/authority, especially order-executable missing and cost-passed rows without execution-bound paths.
- Arendt: incorporated. The two V121I selected orders had available M1 paths and no entry touch; classify as normal unfilled orders, not source gaps.
- Boole: incorporated. Raw pending replacement release diagnostics could still leak into scheduler/risk headroom; runtime-only release arithmetic is now patched.
- Parfit: incorporated. Entry-quality fill probability and execution/fillability probability stay separate and correctly namespaced.
- Harvey: partially incorporated. Diagnostic lifecycle rows are no longer binding; runtime replacement release arithmetic is completed in this batch.

## 6. Mismatch Classes

- Source-bound -> candidate: same-window transfer is bounded; do not compare to global reservoir.
- Candidate -> selector: entry-quality fill and execution fillability remain separate.
- Selector -> scheduler: package authority failures are explicit skip reasons, not generic selector collapse.
- Scheduler -> risk: replacement release only creates headroom after runtime replacement applies and matches runtime pending IDs.
- Risk -> order: cost-refused/source-gap/explicit false rows remain non-executable but scoreable/missed.
- Order -> lifecycle: entry not touched on available path is accepted unfilled truth, not missing evidence.
- Lifecycle -> fill: diagnostic counterfactual fills stay non-executable.
- Fill -> exit: no V121I fills, so exit cannot be judged from this slice.
- Ledger: raw diagnostic release values are preserved separately from runtime executable release values.

## 7. Fixed / Partial / Open

Fixed:

- candidate quality preserves the `ultimate_candidate_package.` namespace when package entry-quality becomes generic fill probability;
- generic fill probability is not backfilled from limit/execution fillability;
- selector skip reasons preserve package open-reduced authority failures;
- entry-not-touched with available M1/tick path becomes `not_filled` even if pre-stamped `source_gap`;
- scheduler `_unused_pending_release` credits only runtime release IDs after runtime replacement applies;
- scheduler and risk authority preserve raw release values while using matched explicit runtime release IDs for executable headroom;
- missed-opportunity attribution uses package order transfer status and final blocker fields before generic authority-missing or cost-passed/no-bound buckets, including row-normalization repair after transfer fields are attached.

Partial:

- order materialization taxonomy must be proven by V121J replay;
- runtime release leak is strict-runtime unit-tested but needs replay evidence for headroom/reallocation impact;
- generic missed blocker collapse is attribution and normalization unit-tested but needs replay evidence that `1337 + 235` misleading buckets move into exact final-blocker reasons;
- V121I still leaves order-executable missing and execution-bound path gaps.

Open:

- V121I missed diagnostics: 1337 `package_replay_order_executable_authority_missing`, 235 `cost_passed_broker_authority_without_execution_bound_order_path`;
- no filled trades means no exit/profit-harvest conclusion;
- if V121J remains zero-trade, the next root batch is selected/order materialization authority, not more source-gap taxonomy.

## 8. Highest-Leverage Same-Root Batch

Batch: order taxonomy and runtime replacement release truth.

Affected files/components:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Patch types:

- correctness: fill taxonomy, runtime-only replacement release, source namespace;
- performance: valid unfilled orders can remain lifecycle-visible instead of diagnostic-only; headroom is no longer flattered by raw release diagnostics;
- diagnostic/ledger: raw release values and runtime release values are separate.

## 9. Expected Effects Before Replay

- Candidate -> scorecard: likely unchanged.
- Scorecard -> order: selected entry-not-touched rows should stop being source-gap diagnostic rows.
- Order -> fill: may remain 0 if entries were never touched.
- Missed positive R: may move to unfilled/expired opportunity buckets; must be reported separately.
- Missed negative R: must remain counted.
- Trade count: may remain 0.
- Net/gross/final R and W/L/F: may remain 0/0/0 if no entries touch.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk: report separately; do not promote all reduced-risk rows.

## 10. Replay Command

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-15 \
  --end 2026-05-15 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V121J_ORDER_TAXONOMY_RUNTIME_RELEASE_TRUTH_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --skip-tick-source \
  --compact-missed-ledger
```

## 11. Success / Failure Criteria

Helped:

- V121I selected XAUUSD/BTCUSD entry-not-touched rows become normal `not_filled` lifecycle/order truth instead of diagnostic `source_gap`;
- executed REFUSED/source-gap/explicit false rows remain zero;
- pending replacement headroom uses matched explicit runtime IDs only and ledgers raw values separately;
- generic order-executable missing and cost-passed/no-bound missed buckets collapse into exact final blockers where transfer status exists;
- candidate/scorecard/order/fill/missed deltas are stage-attributed.

Failed:

- selected rows still die as `postdecision_ordered_path_source_gap_or_entry_not_touched`;
- raw diagnostic replacement release still changes headroom when runtime replacement did not apply;
- headline improvement comes only from fewer trades and more unexplained missed positive R;
- the one-day smoke is treated as global reservoir proof.
