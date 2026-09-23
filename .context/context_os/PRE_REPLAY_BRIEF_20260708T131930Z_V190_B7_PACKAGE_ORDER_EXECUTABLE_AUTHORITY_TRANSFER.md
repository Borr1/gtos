# V190 B7 Package Order-Executable Authority Transfer Pre-Replay Brief

Generated: 2026-07-08T13:19:30Z

## Scope

This is a bounded B7 truth/proof repair for the XAUUSD 2026-06-04..2026-06-05
targeted replay slice. It is not a broad behavioral proof and must not be
compared directly to the global source-bound reservoir.

## Latest Completed Run

Latest completed prefix:
`BROAD_LIVE_AS_IF_REPLAY_V189_B7_RISK_EXPRESSION_NAMESPACE_PARITY_20260604_20260605_XAUUSD_TARGETED`.

V189 numbers:

- Candidates: 1130
- Scorecards: 184
- Orders: 28
- Trades: 12
- Missed rows: 1116
- Buckets: 34
- Net/gross/final R: `2.29004187 / 3.19764809 / 3.19764809`
- Cash PnL: `1362.61375829`
- Risk cash / risk pct: `7369.13533739 / 7.375`
- W/L/F: `9 / 3 / 0`
- Executed broker-cost REFUSED/source-gap rows: `0 / 0`
- Full-risk public label violations: `0`

## Active Process State

No broad replay process was running before this patch. Multiple Context OS MCP
stdio helper processes were active; they are not replay/build processes.

## Current Same-Root Evidence

Dalton found the remaining high-leverage B7 truth gap:
`package_replay_order_executable_authority_missing` on `230` missed rows with
`+161.00852628` expected-net R.

V189 row inspection showed that representative rows already carried
`package_replay_order_executable_candidate_use_allowed=false` at top level, but
the missed proof namespace still emitted
`missed_package_replay_order_executable_candidate_use_allowed=null` and a
generic `package_replay_order_executable_authority_missing` reason. The concrete
pre-order blocker existed as `scheduler_materialization_skip_reason`, e.g.
`selector_reduce_risk_not_new_entry_authority`.

This is a consumer/emission truth mismatch, not an execution promotion.

## Patch Batch

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness/proof repair.
- Expected behavior: neutral for candidates, scorecards, orders, fills, trades,
  R, cash PnL, and W/L/F.
- Expected ledger effect: generic missing-order-authority missed rows split into
  explicit false order-authority/final-blocker rows where authority is already
  present or nested under scheduler score components.

Producer/consumer/proof contract:

- Producer: scheduler score components and final row top-level package order
  authority fields.
- Consumer: `scheduler_missed_opportunity_attribution_fields` and
  `normalize_package_new_entry_authority_ledger_row`.
- Ledger/proof surface: missed opportunity ledger fields prefixed
  `missed_package_replay_order_executable_*`.
- Focused verifier: targeted pytest cases for nested scheduler authority and
  V189-style false authority sync.

Focused proof already run:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'nested_scheduler_order_authority_false or syncs_false_order_authority or missed_opportunity_attribution_missing_order_authority_is_not_executable or normalize_package_row_repairs_missed_authority_missing_with_final_blocker or normalize_package_row_repairs_missed_cost_passed_with_final_blocker' -q --tb=short`: `5 passed, 587 deselected, 1 warning`.

## Replay Success Criteria

Run the smallest targeted proof slice with the same window/profile as V189.

Helped:

- Trade/order/candidate counts and net/gross/final R remain unchanged or any
  change is explained by deterministic row-truth changes.
- Executed broker-cost REFUSED/source-gap rows remain `0 / 0`.
- `missed_package_replay_order_executable_candidate_use_allowed=null` decreases
  for rows with explicit false package-order authority.
- Generic `package_replay_order_executable_authority_missing` decreases or is
  reclassified under concrete pre-order blockers such as
  `selector_reduce_risk_not_new_entry_authority`.
- Cost-refused/source-gap rows remain diagnostic and non-executable.

Failed:

- Any REFUSED/source-gap candidate becomes executable/fillable.
- Behavior changes without a corresponding execution-authority truth reason.
- Generic missing-order-authority remains dominant on rows that already carry
  explicit false authority.

Exposed next flaw:

- If generic missing remains only where no top-level or nested authority exists,
  the next B7 blocker is upstream producer materialization.
- If generic missing is replaced by selector-materialization blockers, the next
  batch should address the underlying selector/scheduler policy path only after
  the proof namespace is honest.

