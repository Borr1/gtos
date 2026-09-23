# Pre-Replay Brief - 2026-07-04T13:20Z - V118 Order-Exec Authority Split

Scope: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full across the 82-sleeve package. This is a bounded repair proof, not a global reservoir claim.

## Latest Completed Replay

Latest completed replay remains:

`BROAD_LIVE_AS_IF_REPLAY_V117_B4_FILL_REALISM_SOURCE_SLICE_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- window: `2026-05-13..2026-05-17`
- profile: `repaired_package_conversion_v3`
- scorecards / order rows / order events: `288 / 3 / 6`
- filled trades: `1`
- net R: `-1.10389662`
- gross / final R: `-1.0 / -1.0`
- cash PnL / risk cash: `-110.389662 / 100.0`
- W/L/F: `0/1/0`
- missed rows / scoreable missed rows: `2643 / 966`
- missed +R / -R / net: `216.44200363 / -1801.09783238 / -1584.65582875`

V117 is a hostile five-day repair slice. It does not prove or disprove total million-R reservoir transfer.

## Running Process State

No broad replay is running. No pytest is running. Rawls and Hegel were read, incorporated, and closed.

Decision: run a one-day V118 smoke first because this batch changes authority propagation and false-executable veto semantics. Do not start the five-day replay until the one-day contract proves clean.

## Baseline Comparison

Same-window comparison anchors:

- V92 hostile five-day: `51 trades, +29.35570236R`
- V106 same window: `83 trades, +32.57834226R`, `288` scorecards, `91` order rows, `185` order events
- V117 same window: `1 trade, -1.10389662R`, `288` scorecards, `3` order rows, `6` order events
- V117 delta vs V106: `-82` trades, `-33.68223888R`
- V110B broad 19-day: `95 trades, +22.80442652R`
- V111 broad 19-day: `45 trades, -4.19333138R`

## Dirty Files And Active Changes

Active checkpoint files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T132039Z_V118_ORDER_EXEC_AUTHORITY_SPLIT.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260704T132039Z_V118_ORDER_EXEC_AUTHORITY_SPLIT.md`

Do not stage unrelated dirty files or `.context/LIVE_STATE.md`.

## Incorporated Subagent Findings

- Rawls: incorporated. Added scorecard/finalizer package-authority propagation including prefixed order-executable fields.
- Hegel: incorporated. Added scheduler/verifier tests and fatal verifier handling for false order-executable filled rows.
- Godel: deferred. Source loader offset/day-index performance repair remains useful for broad runs but is not the current correctness blocker.
- Hilbert: incorporated in V117/V118. Signed package authority is now separated from fill/order executability.

## Known Mismatch Classes

- source-bound -> candidate: V117 generated `808/1101` axes; not the current dominant leak.
- candidate -> selector: raw/materialized action and reason are separated.
- selector -> scheduler: signed authority truth remains separate from order/fillability truth.
- scheduler -> risk: requested-risk source uses explicit row/nested ladder fields, not final approved risk inference.
- risk -> order: explicit `package_replay_order_executable_candidate_use_allowed=false` is preserved as a veto and not overwritten by package admission success.
- order -> lifecycle -> fill: false order-executable rows must stay scoreable/missed and never become filled trades.
- fill -> exit: not changed in this batch.
- ledger/verifier: top-level scorecard aliases and selected-package order/trade false-exec scans are patched.

## Same-Root Batch To Prove

Batch: `V118_ORDER_EXEC_AUTHORITY_SPLIT`.

Patch type:

- correctness repair: preserve signed authority vs order-executable authority split;
- ledger repair: propagate split fields into scorecard/finalizer aliases;
- verifier repair: fatal if false order-executable rows fill.

Expected measurable effect before replay:

- candidate -> scorecard transfer: unchanged or improved only through preserved authority fields.
- scorecard -> order transfer: may improve from V117 if valid authority rows were previously erased.
- order -> fill transfer: must not improve by executing rows marked order-executable false.
- missed positive/negative R: should be attributed to explicit order/fillability reasons instead of missing authority.
- trade count / net R / W/L: not required to improve in the one-day proof.
- cost-refused/source-gap execution: must remain zero.
- risk-reduced/full-risk distribution: must remain reported with provenance.

Pass criteria:

- `python3 -m py_compile` remains clean.
- Scheduler tests remain `209 passed`; verifier tests remain `80 passed`.
- No filled order/trade has `package_replay_order_executable_candidate_use_allowed=false`.
- Valid signed authority rows can remain scoreable while order-executable false blocks fills.
- Scorecard/top-level and finalizer aliases carry the new fields.
- Broker/live/final remain false.

Fail criteria:

- explicit false order-executable rows fill;
- signed authority is erased only because fillability/order viability failed;
- scorecard/order rows lose the new authority fields;
- the smoke is interpreted as full reservoir proof.
