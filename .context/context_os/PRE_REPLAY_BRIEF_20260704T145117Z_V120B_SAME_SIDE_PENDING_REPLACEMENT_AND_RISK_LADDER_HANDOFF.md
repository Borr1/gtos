# Pre-Replay Brief - 2026-07-04T14:51Z - V120B Same-Side Pending Replacement And Risk-Ladder Handoff

Scope: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain closed. Local replay/package evaluation keeps full 82-sleeve authority. This is a hostile five-day repair proof, not a full-reservoir transfer claim.

## 1. Latest Completed Replay

`BROAD_LIVE_AS_IF_REPLAY_V119C_PASSIVE_DISTANCE_QUEUE_RELEASE_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- window: `2026-05-13..2026-05-17`
- scorecard rows: `288`
- order/trade rows: `16 / 5`
- trade net R: `-5.50984356`
- W/L/F: `0 / 5 / 0`
- missed rows: `2761`
- interpretation: V119C improved order-transfer truth versus V119B, but exposed unsafe same-side pending BTCUSD LONG stacking.

## 2. Running Replay State

No broad replay was running when this brief was written. Focused compile/tests passed. Next action is the V120B hostile five-day same-config repaired-only replay unless a process-state check shows another run has started.

## 3. Baselines

- V119B same-window prior: scorecards `288`, order/trade `4 / 1`, net R `-1.10389662`, missed rows `2767`.
- V119C same-window latest: scorecards `288`, order/trade `16 / 5`, net R `-5.50984356`, missed rows `2761`.
- V119C delta: `+12` orders, `+4` trades, `-4.40594694R` net R. This was a truth repair regression, not a policy win.
- V89D/V90/V92 remain historical route baselines for broad behavior; this brief uses V119B/V119C as the same-code-line local denominator for this patch.

## 4. Dirty Files / Active Changes

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T145117Z_V120B_SAME_SIDE_PENDING_REPLACEMENT_AND_RISK_LADDER_HANDOFF.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260704T145117Z_V120B_SAME_SIDE_PENDING_REPLACEMENT_AND_RISK_LADDER_HANDOFF.md`

## 5. Subagent Findings

- Dirac: incorporated. V119C filled BTCUSD LONG same-side pending rows as `same_direction_scale_in`; patch routes same-side pending exposure to `replace_pending`.
- Nash: partially incorporated. Finalizer ladder fields can be lost in order materialization; patch preserves finalized ladder/full-risk fields. Scheduler stale-ladder recompute after fallback priority reset remains open if replay shows ladder drift.
- Dalton: incorporated. Same-side pending helper test and verifier fatal were added.

## 6. Mismatch Classes

- source-bound -> candidate: partially fixed; measure same-window transfer only.
- candidate -> selector: partially fixed; raw/effective selector truth remains monitored.
- selector -> scheduler: partially fixed; scheduler stale-ladder refresh remains possible.
- scheduler -> risk: current batch fixes same-side pending replacement action resolution.
- risk -> order: current batch fixes finalized ladder propagation into emitted order risk authority.
- order -> lifecycle: current batch makes filled same-side pending duplicates without replacement authority verifier-fatal.
- lifecycle -> fill: open; V120B must show whether stacked fills vanish or become committed replacements/expiries.
- fill -> exit: open; if replacement truth is clean and still loses, next root is stop/exit geometry.
- ledger: current batch adds deterministic verifier scan for the unsafe V119C class.

## 7. Fixed / Partial / Open

Fixed in this batch:

- same-side pending context no longer grants scale-in authority;
- same-side pending replacement reconstruction no longer returns `{}`;
- runtime risk finalizer ladder is finalized after guards and copied into orders;
- missing dynamic-budget quality values serialize as `null`, not crash;
- verifier now scans filled same-side pending duplicates.

Partially fixed:

- signed risk-expression ladder is preserved into orders, but scheduler stale-ladder recompute after fallback priority reset is still open.

Open:

- whether replacement truth improves or reduces fill transfer;
- stop/exit behavior for any remaining BTCUSD fills;
- same-window source-bound transfer after this patch.

## 8. Highest-Leverage Same-Root Batch

Batch: same-symbol lifecycle truth plus risk-expression handoff.

Reason: V119C’s four added BTCUSD losing fills were not just bad trades; they were accepted while same-side pending exposure was already visible. That makes the order/lifecycle path incorrect before exit tuning.

## 9. Files / Components

- runtime loop: lifecycle resolver, source-required override, pending replacement diagnostic, dynamic-budget serializer, finalizer-to-order risk handoff;
- tests: runtime lifecycle/risk tests and verifier tests;
- verifier: same-side pending duplicate lifecycle authority scan and result integration.

## 10. Patch Type

- same-side pending replacement: correctness repair;
- final risk ladder propagation: correctness and diagnostic repair;
- missing-quality serializer: truth serializer repair;
- verifier scan: verifier repair.

## 11. Expected Measurable Effect

- candidate -> scorecard transfer: unchanged expected.
- scorecard -> order transfer: order count may decrease from V119C `16` if stacked pending rows are no longer admitted as independent scale-ins.
- order -> fill transfer: fill count should drop from V119C `5` unless replacements are causally admitted.
- missed positive R: may increase if invalid stacked fills become missed/expired diagnostic rows.
- missed negative R: should capture blocked invalid negative paths separately.
- trade count: likely lower than `5`; not a positive-by-suppression claim unless replacement/expiry reasons are causal and explicit.
- net/gross/final R: can improve by removing invalid stacked losers, but success is primarily lifecycle truth plus verifier clean.
- W/L/F: stacked BTCUSD losers should not remain as four independent scale-in losses.
- cost-refused/source-gap execution: must remain `0`.
- risk-reduced/full-risk distribution: finalized ladder fields should be present on emitted rows; full/reduced should be reportable separately.

## 12. Replay Result Meaning

Helped:

- V120B has zero filled same-side pending rows without replace-pending authority;
- verifier same-side pending lifecycle scan bad counts are zero;
- BTCUSD pending stack is replaced, expired, or filled only through committed replacement authority;
- risk ladder fields are present in order/trade rows.

Failed:

- any filled same-side pending duplicate remains `same_direction_scale_in`;
- verifier reports `broad_live_as_if_same_side_pending_lifecycle_authority_bad`;
- replacement rows lose finalizer/order risk ladder fields.

Exposes next flaw:

- lifecycle truth is clean but replay remains negative. Then patch the largest remaining bucket from V120B ledgers, likely stop/exit geometry, scheduler runtime-ineligible rows, or scheduler risk-expression stale-ladder drift.
