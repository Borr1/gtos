# V186 B7 Pre-Replay Brief - Explicit Close/Reverse Lifecycle Root Authority

Generated UTC: 2026-07-08T12:09:00Z.

## Control State

- Fable batch: B7 runtime transfer, `B7_explicit_package_close_reverse_lifecycle_root_authority_parity`.
- Latest completed replay baseline: `BROAD_LIVE_AS_IF_REPLAY_V185_B7_PRE_SCHEDULER_LIFECYCLE_FLOOR_PARITY_20260604_20260605_XAUUSD_TARGETED`.
- Broker mutation, live broker authority, and final selection remain false.
- Replay scope: bounded XAUUSD 2026-06-04..2026-06-05 targeted slice. This proves or rejects this local repair only; it is not full-reservoir conversion evidence.

## V185 Baseline

- Candidates / scorecards / order rows / trades / missed / buckets: `1130 / 184 / 17 / 8 / 1121 / 31`.
- W/L/F: `5/3/0`.
- Net/gross/final R: `0.50779951 / 1.12248313 / 1.12248313`.
- Cash PnL / risk cash / risk pct: `114.93888574 / 4858.62127863 / 4.875`.
- Expected cost R: `0.61468362`.
- Executed broker-cost REFUSED/source-gap rows: `0 / 0`.
- V185 moved `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00` from pre-scheduler lifecycle floor blocked to `scheduler_option_materialized`, `scheduler_rank=1`, `scheduler_score=0.19`.
- New blocker: lifecycle root authority still blocks the row with `close_reverse_authority_not_allowed,close_reverse_release_context_missing` despite valid signed package new-entry authority targeting `close_and_reverse`, broker-cost PASSED status, source completeness, package/order executable authority, and replay opposite-open exposure context.

## Patch Batch

Files changed:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Repair type:

- behavior-changing correctness repair;
- producer/consumer repair in the scheduler close/reverse lifecycle-root authority contract;
- does not loosen broker-cost REFUSED, source-gap, unsigned, unfillable, or off-authority rows;
- keeps broker/live/final false.

Root fix:

- scheduler now reads replay opposite-open IDs and risk from `same_symbol_replay_exposure_context`;
- explicit package executable materialization rows with valid signed close/reverse authority can use materialization floors instead of generic close/reverse floors;
- the same authority can convert replay-context opposite-open risk into close/reverse release risk, preserving the release ID for lifecycle root and downstream exposure mutation;
- emitted proof fields include explicit close/reverse materialization allowed/applies/floors, release source, context-release applied, broker-cost passed, and source-complete status.

Focused proof already passed:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'current_package_order_authority_supersedes_stale_nested_false_inputs or explicit_package_close_reverse_uses_context_release_and_materialization_floors or order_executable_package_authority_releases_zero_requested_risk_basis or explicit_order_authority_soft_failures_release_without_top_level_order_field or raw_reject_open_reduced_order_execution' -q --tb=short`

## Expected Replay Effect

- Candidate count should remain near `1130`; no candidate-generation narrowing is expected.
- Candidate -> scorecard/order transfer may increase only for exact signed explicit package close/reverse rows.
- The 17:45 row should no longer be blocked by `package_lifecycle_root_authority_not_allowed:close_reverse_authority_not_allowed,close_reverse_release_context_missing`.
- If the row transfers, scorecard/order/trade count may increase and missed positive R should drop by about the row's current `0.29090804R` opportunity proxy, unless a downstream order/fill/exit blocker is exposed.
- Executed broker-cost REFUSED/source-gap rows must remain `0 / 0`.
- Improvement must be classified as better scheduler lifecycle-root conversion and risk/release authority, not broad trade blocking.

## Pass / Fail Criteria

Helped:

- the 17:45 row reaches scorecard/order/trade or exposes a new exact downstream blocker after lifecycle-root authority parity;
- added/removed trades are attributed by exact candidate instance key;
- V186 does not execute REFUSED/source-gap rows and does not collapse opportunity to look positive.

Failed:

- the 17:45 row remains blocked by `package_lifecycle_root_authority_not_allowed`;
- trade/order transfer collapses without a terminal-source explanation;
- REFUSED/source-gap rows execute;
- the patch admits broad mixed/negative missing-authority or runtime-ineligible buckets.

## Planned Targeted Replay

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-04 \
  --end 2026-06-05 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD \
  --max-candidates-per-symbol-window 0 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V186_B7_EXPLICIT_CLOSE_REVERSE_LIFECYCLE_ROOT_AUTHORITY_20260604_20260605_XAUUSD_TARGETED
```
