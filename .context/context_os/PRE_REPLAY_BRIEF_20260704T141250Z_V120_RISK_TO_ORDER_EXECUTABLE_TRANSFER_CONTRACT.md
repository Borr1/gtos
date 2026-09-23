# V120 Risk-To-Order Executable Transfer Contract Pre-Replay Brief

Generated: 2026-07-04T14:12:50Z

Broker/live/final remain closed. Local replay/package evaluation has full authority. This brief is for a code patch and targeted replay proof, not a live claim.

## Latest Completed Replay

Latest completed prefix: `BROAD_LIVE_AS_IF_REPLAY_V119_ORDER_EXEC_AUTHORITY_SPLIT_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

Window: `2026-05-13..2026-05-17`

Status: `broad_live_as_if_replay_materialized_broker_live_closed`

Numbers: 288 scorecards, 2 headline orders, 4 order ledger rows, 1 trade, net R `-1.10389662`, gross/final R `-1.0/-1.0`, cash PnL `-110.389662`, W/L/F `0/1/0`, missed `+224.65585079R / -1851.47117197R / -1626.81532118R`.

Authority cleanliness: executed cost-refused rows `0`, executed source-gap rows `0`, executed false-order-exec rows `0`.

## Active Processes

No broad replay, pytest, or py_compile process was active in the bounded process scan. Do not start a duplicate broad replay.

## Baseline Comparison

Same hostile 5-day window:

| Run | Trades | Order Ledger Rows | Net R | Gross R | Final R | Cash PnL | W/L/F |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 56 | 243 | 34.84520454 | 39.93441037 | 39.93441037 | 8178.90660707 | 41/15/0 |
| V90 | 51 | 233 | 28.84201157 | 33.36349114 | 33.36349114 | 6371.80465431 | 37/14/0 |
| V92 | 51 | 239 | 29.35570236 | 33.9321286 | 33.9321286 | 6228.63096022 | 37/14/0 |
| V119 | 1 | 4 | -1.10389662 | -1.0 | -1.0 | -110.389662 | 0/1/0 |

V119 is cleaner authority proof than earlier versions, but transfer collapsed. Do not compare this 5-day slice to the global million-R reservoir without same-window normalization.

## Dirty Files And Active Changes

Current scoped dirty code/test files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`

Current scoped route-control files:

- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T134917Z_V118C_UNSIGNED_PACKAGE_PROBE_TRUTH.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260704T134917Z_V118C_UNSIGNED_PACKAGE_PROBE_TRUTH.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T141250Z_V120_RISK_TO_ORDER_EXECUTABLE_TRANSFER_CONTRACT.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260704T141250Z_V120_RISK_TO_ORDER_EXECUTABLE_TRANSFER_CONTRACT.md`

## Subagent Findings

Hubble: incorporated. V118C proved unsigned/no-final-selection probes become explicit false, but one-day order-executable true probes still produced zero orders.

Averroes: incorporated. V119 root batch is risk-to-order executable transfer, not exit tuning: 27 missed order-executable rows, zero risk basis, no reallocation, stale risk-expression tiering.

Socrates: partially incorporated. Verifier catches false executable filled rows and cost/source-gap execution. Missing direct verifier coverage for `scorecard_reported_*` source alias/funnel proof.

Pasteur and Hilbert: pending. They are auditing scheduler reallocation and runtime risk/order final disposition. Incorporate before replay.

## Mismatch Map

Source-bound -> candidate: partially fixed. Same-window package rows create scorecards; full-reservoir claims still need exact-window normalization.

Candidate -> selector: partially fixed. Raw reject and effective open-reduced-risk are separated.

Selector -> scheduler: open. Order-executable package probes can enter scheduler with zero risk and disappear as generic veto/zero-trade.

Scheduler -> risk: open. V119 order-executable missed rows show `selected_cell_risk_pct=0.0`, `scheduler_approved_risk_pct=0.0`, and `sizing_haircut_reason=risk_pct_basis_missing`.

Risk -> order: open. 28 scorecards and 27 missed rows are order-executable true, but only 4 order events and 1 fill appear.

Order -> lifecycle/fill: partially fixed. Executed rows are authority-clean, but expired/unfilled and missed lifecycle dispositions are not yet complete enough.

Fill -> exit: deferred. V119 has only one clean fill; exit/stop geometry should be judged after the transfer path produces enough clean fills.

Ledger/verifier: partially fixed. Filled-row authority is covered; scorecard-to-order final disposition and reported source alias need stronger assertions.

## V120 Patch Batch

Patch the same-root chain:

1. Scheduler final order-executable disposition.
2. Zero-risk risk-basis release or explicit terminal blocker for package order-executable candidates.
3. Reallocation after guard/headroom/daily-lockout veto, when same-window next-best candidates are valid.
4. Risk-expression ladder finalization after scheduler/risk/order guards.
5. Scorecard/order/missed transfer funnel fields and verifier assertions.

Affected files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`

Patch types:

- Correctness: final disposition and reallocation.
- Correctness: risk-basis release for causal signed package authority.
- Diagnostic/proof: transfer funnel and scorecard reported authority source.

## Expected Effect

Candidate -> scorecard transfer should remain at least V119-level; no top-N narrowing.

Scorecard -> order transfer must become explainable: order-executable true rows either bind to order/trade or receive a final blocker.

Order -> fill transfer may rise if valid rows are unlocked; expired/fill realism remains honest.

Missed positive/negative R should be reclassified from opaque risk-basis holes into final blockers or executed rows, not suppressed.

Trade count may rise. Net R may improve or worsen; correctness is primary for this batch.

Cost-refused/source-gap/false-order-exec execution must remain zero.

Full-risk vs reduced-risk vs diagnostic must be reported separately after replay.

## Replay Criteria

Run targeted proof first, not a broad replay by reflex. A one-day V120 May 13 smoke is sufficient if it exercises the order-executable transfer rows. Then run the 5-day hostile bucket if the targeted proof is green.

Success: every order-executable true row has final disposition, reallocation is measurable when top candidates are blocked, no false executable/cost/source-gap execution appears, and risk-expression tier reflects final controls.

Failure: order-executable rows still disappear as generic zero-trade/risk-basis missing, or positivity comes only from suppressing opportunity.
