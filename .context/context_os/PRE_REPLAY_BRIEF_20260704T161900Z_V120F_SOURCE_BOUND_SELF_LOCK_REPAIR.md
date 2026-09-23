# V120F Source-Bound Self-Lock Repair Pre-Replay Brief

Broker/live/final remain closed. Local replay/package authority remains full.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V120E_DERIVED_RAW_REJECT_PROMOTION_CONTRACT_20260515_REPAIRED_ONLY_FULLGRID`
- Window: `2026-05-15..2026-05-15`
- Result: 8174 candidates, 96 scorecards, 26 orders, 6 trades, 8161 missed rows.
- Trade result: 2/4/0 W/L/F, net `-0.83245370R`, gross/final `-0.27252862R`.
- Authority result: cost REFUSED/source-gap executions stayed zero.

## Same-Window Baselines

- V92 May-15: 84 orders, 16 trades, 7/9/0 W/L/F, net `-2.23790002R`.
- V120D May-15: 8174 candidates, 96 scorecards, 0 orders, 0 trades.
- V120E restored order/fill transfer versus V120D but remains a bounded one-day proof slice, not a full-reservoir claim.

## Current Evidence

Subagents Mencius, Heisenberg, Ptolemy, Cicero, Locke, and Euler are incorporated.

- Mencius: candidate generation is not the dominant leak; executable package candidates existed but did not become orders in V120D.
- Heisenberg: order authority dies between package replay candidate authority and scheduler order-executable transfer.
- Ptolemy: `risk_basis_missing` mostly masks specific blockers because risk packets are present.
- Cicero: stale explicit false source-bound self-lock can override current source-bound/effective admission evidence.
- Locke: signed source-bound authority can reconstitute dropped boolean aliases when signature/hash/key/predecision identity match; this is bounded authority, not blanket risk release.
- Euler: V120E restored 26 orders and 6 trades, but 3 of 6 filled trades still carried `ordered_tick_required_for_adverse_before_profit_sequence` source gaps through M1/passive-queue path truth. These must be scoreable missed/diagnostic rows, not executable fills.

The highest-leverage remaining row-level leak is a stale self-lock:

- Candidate key `broadorigin_6c01911903bb3ca9bce3ceab@@2026-05-15T00:15:00+00:00` has source-bound aliases true, effective admission count `1.0`, effective selector action `open-reduced-risk`, broker cost PASSED, source completeness `1.0`, and signed authority status valid in the candidate-index surface.
- It still carries `package_replay_executable_candidate_use_allowed=false` with reason `source_bound_package_replay_not_allowed`.
- That false value is treated as authoritative instead of being re-derived through the current source-bound/effective-admission/broker-cost/quality gates.

The same-root truth batch also includes a path-source authority leak:

- M1 queue-realism can prove a passive entry touch, but it cannot prove adverse-before-profit sequence ordering when the oracle emits `ordered_tick_required_for_adverse_before_profit_sequence`.
- V120E allowed those rows to remain filled executable trades if the oracle had already stamped `fill_realism_class=passive_queue_confirmed`.
- V120F demotes those rows to `diagnostic_counterfactual_only` while preserving the original diagnostic fill fields for missed-opportunity accounting.

## Patch Batch

Files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Patch types:

- Correctness: make stale explicit false `source_bound_package_replay_not_allowed` re-derivable through current source-bound and broker-cost gates.
- Correctness: do not let explicit false admission override a valid effective admission count after source-bound execution authority is true.
- Correctness: allow bounded signed source-bound authority to reconstitute dropped boolean aliases only when signature/hash/key/predecision identity match.
- Diagnostic correctness: keep `risk_basis_missing` only when risk basis is truly absent, not when a more specific package/stop/fill/lifecycle blocker exists.
- Correctness: keep ordered-tick-required M1/passive-queue rows non-executable while preserving diagnostic fill/missed opportunity fields.

## Expected Effect

- Candidate -> scorecard count: unchanged.
- Scorecard/order -> fill: valid source-bound rows should no longer die only on stale source-bound self-lock; ordered-tick-required source-gap rows should stop appearing as executable fills.
- Missed positive and negative R: both may move because this restores opportunity rather than suppressing it.
- Cost REFUSED/source-gap execution: must remain zero; executed rows with `ordered_tick_required_for_adverse_before_profit_sequence` must become zero.
- Risk-basis rows: should fall or become specific blockers.

Helped if V120F shows fewer stale `source_bound_package_replay_not_allowed` blockers, zero refused-cost executions, zero ordered-tick-required source-gap executions, and more exact blocker attribution. Failed if rows execute without source-bound evidence, cost pass, effective materialization proof, or ordered-tick truth where required, or if the dominant blocker remains the same stale self-lock.
