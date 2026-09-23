# V147 B7 Transfer Recovery Pre-Replay Brief

Generated UTC: 2026-07-07T08:05:00Z

This brief is the control surface before the next patch or replay. No broad
replay is authorized from this brief. The next action is a focused B7 transfer
recovery patch and focused tests.

## V147 Targeted Replay Result

Updated UTC: 2026-07-07T08:45:00Z.

Targeted replay completed:

`BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`

Result:

- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`,
  `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Candidate rows: 6633.
- Scorecard rows: 480.
- Order event rows: 13; simulated order rows: 6.
- Filled trades: 3.
- Missed rows: 6627.
- Net R: `+0.84449709`.
- Gross/final R: `+1.09529478 / +1.09529478`.
- Cash PnL: `+84.46094125`.
- W/L/F: `3/0/0`.
- Broker-calibrated execution cost: `0.25079769R`.
- Risk: all fills are still `open-reduced-risk`; risk pct sum `0.3`, risk cash
  `300.06790974`.
- Stress/MC: extra-cost +0.05R/trade `+0.69449709R`, +0.10R/trade
  `+0.54449709R`, +0.20R/trade `+0.24449709R`; MC 200 iterations, total net
  `+0.84449709R`, worst max drawdown `0.0R`.
- Invalid execution: REFUSED cost `0`, source-gap `0`, unresolved fill-floor
  order/trade `0/0`, live/final `0`.

Comparison:

- V147 versus V146: added one trade, removed none, net delta `+0.29090804R`.
  The added trade is
  `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`,
  XAUUSD LONG, `moonshot_h17_18`, `ob_retest`, `+0.29090804R`.
- V147 versus V144: same three filled trade keys and same net `+0.84449709R`,
  but V147 keeps V146's cleaner unresolved-fill-floor authority surface:
  order event rows `13` versus V144 `15`, simulated orders `6` versus V144 `7`,
  expired unfilled `3` versus V144 `4`.

Interpretation:

- The V147 patch helped by better conversion, not by suppressing opportunity:
  candidates and scorecards stayed flat, one valid winner was recovered, and no
  trade was removed.
- This is still a bounded five-symbol/five-day local transfer proof. It does not
  prove B7.4 19-day transfer, B7.5 extended history, or B8 live readiness.
- Next action is verification/audit/commit for the V147 checkpoint, not another
  replay. The next B7 patch after commit should target the remaining blocker
  classes shown by the V147 flow artifacts.

## V147 Focused Patch Update

Updated UTC: 2026-07-07T08:18:54Z.

Patch landed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: source-bound
  router-refusal materialization default fill floor changed from `0.80` to
  `0.55`, and the materialization limit fallback now uses the source-bound
  constants instead of the stricter positive-predecision defaults.
- `src/components/selector_v4.py`: source-bound router-refusal selector release
  fallback fill floor changed from `0.80` to `0.55`.
- `run_broad_live_as_if_replay_harness.py`: repaired profile now forwards
  scheduler and ultimate-package source-bound router-refusal materialization
  fill floors at `0.55`.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: added a
  `62cb`-class materialize-scheduler-window proof for execution fillability
  `0.551338888` passing the selected-policy floor while preserving signed
  open-reduced authority and no live broker authority.
- `tests/test_broad_replay_repair_config.py`: repaired-profile expectations now
  require the `0.55` source-bound router-refusal materialization fill floor.

Focused proof passed:

- py_compile on touched code/tests.
- repaired profile config test: 1 passed.
- source-bound router-refusal materialization tests: 4 passed.
- adjacent signed/namespace timewarp tests: 4 passed.
- scheduler guard tests: 3 passed.

This is behavior-changing. The next authorized run is the smallest same-window
targeted proof, not a broad replay:

`BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`

Expected effect before replay:

- More source-bound router-refusal rows with broker-cost pass, source-complete
  package admission, positive predecision edge, and execution fillability at or
  above `0.55` can become signed open-reduced scheduler-rankable rows.
- Candidate/scorecard rows should not collapse.
- REFUSED/source-gap/unresolved-fill-floor/live/final execution counts must stay
  zero.
- If new orders/fills appear, they must be separated from suppression effects and
  compared to V146 and V144.

## 1. Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Candidate rows: 6633.
- Scorecard rows: 480.
- Order rows: 10.
- Filled trades: 2.
- Missed rows: 6628.
- Net R: `+0.55358905`.
- Gross/final R: `+0.72340378 / +0.72340378`.
- Cash PnL: `+55.36532564`.
- W/L/F: `2/0/0`.
- Executed REFUSED/source-gap/live/final rows: 0.
- Unresolved fill-floor order/trade rows: 0/0.
- Interpretation: bounded local repair proof only; not full-reservoir conversion proof.

## 2. Running Replay

No broad replay, targeted replay, pytest, py_compile, route builder, or route
verifier process is running in the current process scan.

## 3. Baseline Comparison

- V146 vs V145 targeted: trade delta `-1`, net R delta `+0.37023550`; removed
  unresolved-fill-floor rows `b8a...14:30` (`-1.10446455R`) and
  `bf1a...07:30` (`+1.12241840R`), restored `e59c...18:15`
  (`+0.38818935R`).
- V146 vs V144 targeted: trade delta `-1`, net R delta `-0.29090804`; removed
  valid V144 winner `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`.
- V128 full five-day reference: 55 trades, `+1.12099062R`, 38/17/0, 35191
  candidates, 212 order rows, 55 fills.
- V104 same-window comparator: 46 trades, `+14.73101491R`; V128 still has 0
  common V104 canonical trade keys and trails V104 by `-13.61002429R`.

## 4. Dirty Files And Active Changes

Current route-scoped dirty files before the V147 patch:

- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`
  updated with current V146 matrix and selected V147 batch.
- `.context/context_os/PRE_REPLAY_BRIEF_20260707T0805Z_V147_B7_TRANSFER_RECOVERY.md`
  added by this brief.

Existing unrelated dirty files remain outside this patch scope, including older
context files and unrelated repo dirt reported by `LIVE_STATE`.

## 5. Subagent Findings

- Kant: incorporated. V146 did not newly drop `62cb`; V145 dropped it before
  order/trade. The row is source-bound/cost-passed and appears in finalizer
  probes, but router-refusal open-reduced materialization is not granted:
  `source_bound_open_reduced_materialization_allowed=false`, origin family not
  allowed, execution fill probability `0.551338888` below materialization floor
  `0.8`.
- Tesla: incorporated. Highest B7 recoverable class is scheduler/reallocation
  ranking (`69` axes, missed R `+166.58235496 / -401.05522433`). Repair must
  rank/reallocate only cost-passed, source-complete, fillable positive-transfer
  candidates, not admit all.
- Heisenberg: incorporated. V146 has no missed rows that are already
  order-executable; the mismatch is earlier in package authority, fill-floor
  quality, finalizer fill-realism, lifecycle authority, and pending replacement
  gates. Add verifier/tests for explicit blocker classes and terminal risk
  release.

## 6. Mismatch Classes

- Source-bound -> candidate: partial. V128 broad generates 888/1101 axes but
  only 33 reach scorecard/order presence and 23 fill.
- Candidate -> selector: partial. Router-refusal/source-bound materialization
  can leave valid rows diagnostic instead of scheduler-rankable.
- Selector -> scheduler: partial. Cost-passed/source-complete/fillable rows can
  be non-selected or non-order-executable without enough transfer-blocker proof.
- Scheduler -> risk: partial. Ladder truth exists, but V146 fills are still all
  open-reduced-risk and allocation/headroom effects remain B7-open.
- Risk -> order: V146 unresolved fill-floor execution leak is fixed; remaining
  blockers are package authority, fill-realism, selector materialization,
  marketable guard, lifecycle authority, and cost authority.
- Order -> lifecycle/fill: partial. Pending accepted orders terminalize in V146,
  but verifier coverage should require terminal risk release and exact expiry or
  cancel reasons.
- Fill -> exit: open. Exit/stop damage remains a later B7 blocker after transfer
  proof; do not tune exits from a corrupted transfer path.
- Ledger/verifier: green at V146, but V147 should add exact blocker/terminal
  proof scans if new fields are introduced.

## 7. Fixed / Partial / Open

- Fixed: B0-B6 truth contracts as recorded in
  `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`.
- Fixed in V146: unresolved fill-floor order/trade authority leak.
- Partial: B7 transfer recovery, especially source-bound/router-refusal
  materialization, scheduler reallocation, order-executable blocker proof, and
  lifecycle terminal proof.
- Open: B7.4 broad 19-day, B7.5 extended history, B8 live path.

## 8. Highest-Leverage Same-Root Batch

V147 B7 transfer recovery:

1. Repair signed router-refusal/source-bound materialization so rows like
   `62cb...17:45` can become scheduler-rankable only under signed/cost/fillable
   authority.
2. Preserve scoreable diagnostics for unresolved fill-floor, REFUSED cost, and
   source-gap rows; do not execute them.
3. Add exact blocker-class proof for cost-passed/source-complete/fillable rows
   that remain non-order-executable.
4. Add terminal lifecycle/risk-release proof for pending accepted rows.

## 9. Affected Files

- `src/components/selector_v4.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_selector_v4.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_timewarp_scheduler_materialization.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_denominator_to_deployment_verifier.py`

## 10. Patch Type

- Correctness repair: signed materialization/rankability and lifecycle terminal
  truth.
- Diagnostic/ledger repair: exact blocker proof for cost-passed/source-complete
  fillable missed rows.
- Performance repair: only if the transfer path converts valid candidates
  without executing REFUSED/source-gap/unresolved-fill-floor rows.

## 11. Expected Measurable Effect

- Candidate -> scorecard transfer: no collapse; candidate rows stay visible.
- Scorecard -> order transfer: valid signed/cost-passed/fillable rows may move
  from missed/probe to scheduler-rankable/order-eligible, but only with exact
  authority.
- Order -> fill transfer: no REFUSED/source-gap/unresolved-fill-floor execution.
- Missed positive R: should fall only by valid conversion or exact
  non-executable classification.
- Missed negative R: remains visible; no positive-by-suppression.
- Trade count: can move either direction, but added/removed keys must be causal.
- Net/gross/final R and W/L/F: can move either direction; correctness is judged
  by transfer proof and no authority regressions.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: must remain reported separately.

## 12. Proof Criteria

Helped:

- `62cb...17:45` or the same root class becomes rankable/order-eligible with
  signed/cost/fill/lifecycle authority, or receives a precise non-executable
  blocker that explains why V144 was wrong.
- Every cost-passed/source-complete/fillable missed row has an explicit
  blocker-class/reason.
- Pending accepted rows terminalize with risk release.
- Route verifier remains green.

Failed:

- Improvement comes only from trade collapse.
- Any REFUSED/source-gap/unresolved-fill-floor/live/final row executes.
- Candidate/scorecard rows collapse without causal blocker proof.
- `62cb...17:45` remains unexplained.
