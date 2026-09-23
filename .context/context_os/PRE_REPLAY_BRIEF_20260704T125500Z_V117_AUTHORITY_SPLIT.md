# Pre-Replay Brief - 2026-07-04T12:55Z - V117 Authority Split

Scope: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full across the 82-sleeve surface. This checkpoint is a same-root correctness repair, not a live claim.

## 1. Latest Completed Replay

Latest completed replay:

`BROAD_LIVE_AS_IF_REPLAY_V117_B4_FILL_REALISM_SOURCE_SLICE_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- window: `2026-05-13..2026-05-17`
- profile: `repaired_package_conversion_v3`
- scorecards: `288`
- candidate rows in split profile: `2646`
- orders / order events: `3 / 6`
- filled trades: `1`
- net R: `-1.10389662`
- gross / final R: `-1.0 / -1.0`
- cash PnL / risk cash: `-110.389662 / 100.0`
- W/L/F: `0/1/0`
- missed rows / scoreable missed rows: `2643 / 966`
- scoreable missed +R / -R / net: `216.44200363 / -1801.09783238 / -1584.65582875`

This five-day hostile bucket proves B4 fill-realism and authority-transfer behavior only for this exact window. It does not prove total reservoir conversion.

## 2. Running Process State

No broad replay is running. Two read-only sidecar explorers are active:

- Rawls: scorecard/finalizer propagation audit for the new authority split.
- Hegel: verifier/test coverage audit for non-executable split rows.

Decision: do not start a broad replay until the current scheduler authority split plus any concrete propagation/verifier findings are integrated.

## 3. Baseline Comparison

Same-window V106 comparison:

- V106 prefix: `BROAD_LIVE_AS_IF_REPLAY_V106_SELECTOR_FULL_TRADE_RELEASE_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
- V106 trades / net R: `83 / +32.57834226`
- V106 scorecards / orders / order events: `288 / 91 / 185`
- V117 added trades / R: `1 / -1.10389662`
- V117 removed V106 trades / R: `83 / +32.57834226`
- V117 delta: `-82` trades, `-33.68223888R`

Reference baselines: V92 hostile five-day `51 trades, +29.35570236R`; V110B broad 19-day `95 trades, +22.80442652R`; V111 broad 19-day `45 trades, -4.19333138R`.

## 4. Current Dirty Files And Active Code Changes

Relevant active files in this checkpoint:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T125500Z_V117_AUTHORITY_SPLIT.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260704T125500Z_V117_AUTHORITY_SPLIT.md`
- route comparison artifact `BROAD_LIVE_AS_IF_REPLAY_V117_B4_FILL_REALISM_SOURCE_SLICE_20260513_20260517_V106_COMPARISON.json`

Do not stage unrelated historical deletions, unrelated Context OS infrastructure changes, or `.context/LIVE_STATE.md`.

## 5. Subagent Findings

- Godel: deferred. Source loader still scans from CSV start per exact window; repair later with OHLC offset/day index. Not the current highest-leverage correctness blocker.
- Hilbert: incorporated. V117 finalizer probes are row-bound/materialized, but package-new-entry authority survives only on the 3 executable-finalized rows because fill-floor/order viability is folded into signing validity.
- Rawls: pending. Expected to confirm whether new split fields propagate into scorecard/order/trade/missed rows.
- Hegel: pending. Expected to confirm verifier/test assertions needed for the split.

## 6. Known Mismatch Chain

- source-bound -> candidate: mostly alive in V117, `808/1101` axes generated.
- candidate -> selector: partially fixed; open-reduced/reject distribution visible.
- selector -> scheduler: current patch preserves raw/materialized selector reasons and keeps row-bound package signing valid.
- scheduler -> risk: current patch propagates explicit requested-risk sources without inferring from final approved risk.
- risk -> order: current patch separates package signing from `package_replay_order_executable_candidate_use_allowed`.
- order -> lifecycle/fill: B4 fill-realism remains active; optimistic/non-executable rows must remain scoreable missed, not executable fills.
- fill -> exit: still open after authority-transfer proof.
- ledger/verifier: pending sidecar audit for split fields and fatal scans.

## 7. Fixed, Partial, Open

Fixed in this patch:

- `package_new_entry_authority_valid` no longer means "fillable"; it means signed predecision package identity/authority is valid.
- Fill-floor/order non-executability now uses `package_replay_order_executable_candidate_use_allowed=false` with explicit reason.
- Lifecycle `replace_pending` and `close_and_reverse` are not over-blocked by new-position fill-floor failures.
- Synthetic `candidate:<n>` identities still fail signing.
- Row-bound `broadorigin_*@@decision_time` identities remain signable.
- Focused scheduler tests: `208 passed`.

Open:

- Scorecard/order/trade/missed propagation of the new split fields must be confirmed.
- Verifier may need a fatal scan for executable rows with `package_replay_order_executable_candidate_use_allowed=false`.
- A targeted V117-style smoke must prove scorecard/order-present axes recover without executing fill-floor-refused rows.
- Full/reduced risk distribution still requires replay proof.

## 8. Highest-Leverage Same-Root Batch

Complete the V117 package authority split across:

- scheduler option generation;
- scorecard/finalizer aliasing;
- verifier fatal scans;
- targeted replay proof.

This is a correctness repair. It may not improve headline R immediately; the expected improvement is truthful conversion accounting and recovery of package-authority presence without letting non-executable rows fill.

## 9. Expected Measurable Effect Before Replay

- candidate -> scorecard transfer: unchanged from V117.
- scorecard -> order-present axes: should increase from V117's `5` only if valid authority rows are no longer erased.
- order -> fill transfer: should not increase through fill-floor non-executable rows.
- missed positive/negative R: should move from "missing authority" into explicit non-executable fill-floor/order reasons.
- trade count: may remain low if B4 realism honestly blocks fills.
- net/gross/final R: improvement is not required for this proof; incorrect execution is a failure.
- W/L/F: no positive-by-suppression accepted.
- cost-refused/source-gap execution: must remain `0`.
- risk-reduced/full-risk distribution: should report explicit requested-risk source and remain honest.

## 10. Replay Pass/Fail Criteria

Pass:

- no executable row has `package_replay_order_executable_candidate_use_allowed=false`;
- fill-floor/order failures keep `package_new_entry_authority_valid=true` when identity/signature is valid;
- top-level scorecard/package authority fields are present for row-bound finalizer probes;
- synthetic candidate IDs remain non-signable;
- candidate/scorecard/order/fill transfer is reported same-window against V106/V117 only;
- broker/live/final remain false.

Fail:

- package authority is still erased on row-bound probes;
- fill-floor failures execute as filled trades;
- V117 recovers orders by bypassing broker-cost or source-gap authority;
- lifecycle replacement/close-reverse paths are blocked by new-position-only fill-floor logic;
- the smoke is interpreted as total reservoir proof.
