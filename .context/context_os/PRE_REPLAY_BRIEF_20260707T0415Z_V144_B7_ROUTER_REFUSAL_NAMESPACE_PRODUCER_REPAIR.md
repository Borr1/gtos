# Pre-Replay Brief - V144 B7 Router-Refusal Namespace Producer Repair

Generated UTC: 2026-07-07T04:15:00Z

This is a same-scope rerun after V143 failed the focused producer proof. It is
not a broad replay and not a full reservoir claim.

## Latest Completed Replay

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V143_B7_UNSIGNED_ROUTER_REFUSAL_EXECUTABLE_AUTHORITY_CONTRACT_20260601_20260605_TARGETED`

- Scope: 2026-06-01..2026-06-05.
- Symbols: `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`.
- Profile: `repaired_package_conversion_v3`.
- Candidate rows: 6633.
- Scorecard rows: 480.
- Order rows: 15.
- Trade rows: 3.
- Missed rows: 6626.
- Packet sidecar rows: 7120.
- Net R: +0.84449709.
- Gross/final R: +1.09529478 / +1.09529478.
- Cash PnL: +84.46094125.
- W/L/F: 3/0/0.
- Trade-key delta versus V142: 3 common, 0 added, 0 removed.
- Executed REFUSED rows: 0.
- Executed source-gap rows: 0.

## V143 Failure

V143 did not reduce the unsigned router-refusal executable-authority predicate:

- Candidate: 1980.
- Missed: 1980.
- Packet sidecar: 1905.
- Scorecard: 0.
- Order: 0.
- Trade: 0.
- Total: 5865.

The failed proof showed the original repair was verifier/order-trade facing, not
producer-facing. The root producer leak was `ledger_namespace_alias_fields()`,
which still copied stale executable aliases for source-bound router-refusal
materialization rows with invalid or missing signed new-entry authority.

## Current Patch

Behavior-changing correctness repair:

- Keep source-bound and admission diagnostic fields available for scoreability.
- Demote `package_replay_candidate_use_allowed`,
  `package_replay_executable_candidate_use_allowed`, and
  `replay_candidate_use_allowed_now` when the row is
  `source_bound_router_refusal_open_reduced_materialized_for_replay` and lacks
  valid signed new-entry authority.
- Keep those aliases executable when valid signed authority, matching hash, and
  source-bound instance key are present.

Files changed in this sub-batch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`
- `.context/context_os/PRE_REPLAY_BRIEF_20260707T0415Z_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR.md`

Focused checks passed:

- py_compile for touched runtime/test file.
- Focused pytest: 2 passed.

## Planned Replay

Prefix:

`BROAD_LIVE_AS_IF_REPLAY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED`

Command:

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-01 \
  --end 2026-06-05 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD XAGUSD USDCAD USDJPY UKOIL_cash \
  --max-candidates-per-symbol-window 0 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED
```

## Success Criteria

- Unsigned router-refusal executable-authority predicate rows are zero in every
  V144 ledger.
- Executed REFUSED/source-gap rows remain zero.
- Broker mutation, live broker authority, and final selection remain false.
- The same-scope candidate -> scorecard -> order -> fill counts are reported.
- Any R, cash, or trade-key delta versus V143 is attributed to namespace
  demotion, signed authority, route/fillability, lifecycle, cost/source gap, or
  exit behavior.

## Failure Criteria

- Any unsigned router-refusal executable-authority predicate row remains.
- Any REFUSED/source-gap row executes.
- Any live/final/broker claim opens.
- The result improves only by hiding candidate/missed opportunity rather than
  converting or correctly classifying it.
