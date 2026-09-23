# Pre-Replay Brief - V143 B7 Unsigned Router-Refusal Executable Authority Contract

Generated UTC: 2026-07-07T03:48:00Z

This is a targeted B7 proof, not a broad reservoir claim. It reuses the V142
bounded scope so the patch delta is attributable.

## Current Process State

- No broad replay, route builder, route verifier, pytest, or py_compile process is running.
- Stale GUI/git diff helpers were terminated before this brief.
- Context OS MCP stdio servers are present and are not replay processes.

## Dependency State

- Fable sequence loaded from `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_IMPLEMENTATION_SEQUENCE_20260705.md`.
- Fable audit loaded from `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_ROOT_CAUSE_AUDIT_20260705.md`.
- Current matrix: `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`.
- B0-B6 remain DONE or DONE WITH LABEL.
- B7 remains PARTIAL.
- B8 remains OPEN and blocked by B7.

## Latest Completed Replay

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V142_B7_MISSED_NAMESPACE_EXECUTABLE_AUTHORITY_DEMOTION_20260601_20260605_TARGETED`

- Scope: 2026-06-01..2026-06-05.
- Symbols: `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`.
- Profile: `repaired_package_conversion_v3`.
- Candidate authority: `uncapped_full_authority`.
- Bounded smoke: true.
- Candidate rows: 6633.
- Scorecard rows: 480.
- Order ledger rows: 15.
- Trade rows: 3.
- Missed rows: 6626.
- Packet sidecar rows: 7120.
- Headline net R: +0.84449709.
- Headline gross R: +1.09529478.
- Headline final R: +1.09529478.
- Cash PnL: +211.19447407.
- W/L/F: 3/0/0.
- Order status counts: pending_accepted 7, expired_unfilled 4, filled 3, terminal_lifecycle_position_state_mutation_deferred 1.
- Missed cost dispositions: cost_authority_not_primary_miss_reason 3341, scoreable_missed_cost_refused_non_executable_diagnostic 3285.
- Executable missed scoreable net R: 0.0.

## Baseline Comparison

- V128 full five-day B7 reference: 35191 candidates, 480 scorecards, 212 order rows, 55 fills, net R +1.12099062, gross/final R +6.22739670 / +6.22739670, cash PnL +3007.28429755, W/L/F 38/17/0.
- V142 targeted proof slice: 6633 candidates, 480 scorecards, 15 order rows, 3 fills, net R +0.84449709, gross/final R +1.09529478 / +1.09529478, cash PnL +211.19447407, W/L/F 3/0/0.
- V143 must be compared to V142 for this proof because the scope is the same; V128 is a broader 24-symbol reference and not the direct denominator.

## Current Patch Batch

Batch: B7 transfer recovery, unsigned router-refusal executable authority contract.

Patch type:

- Correctness repair: selected bridge/router-refusal executable authority must be signed and source-bound, not inferred from raw bool aliases.
- Verifier repair: candidate/missed/packet/order/trade scans must flag unsigned router-refusal executable aliases.
- Behavior impact expectation: neutral to mildly behavior-changing. Invalid router-refusal executable flags should demote to diagnostic/missed, while properly signed selected-bridge authority remains usable.

Changed files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `.context/context_os/B7_UNSIGNED_ROUTER_REFUSAL_AUTHORITY_PRE_REPLAY_AUDIT_20260707.json`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`

Focused checks passed before replay:

- py_compile passed for all touched Python modules/tests.
- Scheduler focused tests: 5 passed.
- Timewarp focused tests: 7 passed.
- Verifier focused tests: 4 passed.

## Pre-Replay Audit

Audit artifact: `.context/context_os/B7_UNSIGNED_ROUTER_REFUSAL_AUTHORITY_PRE_REPLAY_AUDIT_20260707.json`

V142 unsigned router-refusal executable-authority predicate counts:

- Candidate ledger: 1980 / 6633 rows.
- Missed ledger: 1980 / 6626 rows.
- Packet sidecar ledger: 1905 / 7120 rows.
- Scorecard ledger: 0 / 480 rows.
- Order ledger: 0 / 15 rows.
- Trade ledger: 0 / 3 rows.
- Total predicate rows: 5865.

The V142 leak is therefore not an already-filled trade leak. It is a candidate,
missed, and packet executable-authority namespace leak that can distort B7
transfer analysis and future materialization if left open.

## Targeted Replay

Planned prefix:

`BROAD_LIVE_AS_IF_REPLAY_V143_B7_UNSIGNED_ROUTER_REFUSAL_EXECUTABLE_AUTHORITY_CONTRACT_20260601_20260605_TARGETED`

Planned command:

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-01 \
  --end 2026-06-05 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD XAGUSD USDCAD USDJPY UKOIL_cash \
  --max-candidates-per-symbol-window 0 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V143_B7_UNSIGNED_ROUTER_REFUSAL_EXECUTABLE_AUTHORITY_CONTRACT_20260601_20260605_TARGETED
```

## Success Criteria

- Unsigned router-refusal executable-authority predicate rows: 0 in candidate, missed, packet sidecar, scorecard, order, and trade ledgers.
- Executed REFUSED/source-gap rows: 0.
- Broker mutation, live broker authority, and final selection remain false.
- Candidate -> scorecard -> order -> fill counts remain explicit; a lower trade count is not a win by itself.
- Added/removed trades versus V142 must be attributed to signed authority, route/fillability, lifecycle, cost/source gap, or exit behavior.
- Missed positive and negative R remain scoreable/diagnostic; opportunity is not suppressed to make headline R look better.
- If net R worsens, accept only if the truth repair exposes the next B7 transfer blocker.

## Failure Criteria

- Any unsigned router-refusal executable-authority row remains in an executable ledger.
- Any REFUSED/source-gap row executes.
- Any broker/live/final claim opens.
- Positive result comes from collapse of candidate/order/fill opportunity without causal attribution.
- New B0-B6 truth contracts regress.
