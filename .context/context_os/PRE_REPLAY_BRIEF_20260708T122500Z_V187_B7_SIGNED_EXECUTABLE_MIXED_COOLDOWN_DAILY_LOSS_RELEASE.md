# V187 B7 Pre-Replay Brief - Signed Executable Mixed Cooldown/Daily-Loss Release

Generated UTC: 2026-07-08T12:25:00Z.

## Control State

- Fable batch: B7 runtime transfer, `B7_signed_executable_mixed_cooldown_daily_loss_release_parity`.
- Latest completed replay baseline: `BROAD_LIVE_AS_IF_REPLAY_V186_B7_EXPLICIT_CLOSE_REVERSE_LIFECYCLE_ROOT_AUTHORITY_20260604_20260605_XAUUSD_TARGETED`.
- Broker mutation, live broker authority, and final selection remain false.
- Replay scope: bounded XAUUSD 2026-06-04..2026-06-05 targeted slice. This proves or rejects this local repair only; it is not full-reservoir conversion evidence.

## V186 Baseline

- Candidates / scorecards / order rows / trades / missed / buckets: `1130 / 184 / 17 / 8 / 1121 / 31`.
- W/L/F: `5/3/0`.
- Net/gross/final R: `0.50779951 / 1.12248313 / 1.12248313`.
- Cash PnL / risk cash / risk pct: `114.93888574 / 4858.62127863 / 4.875`.
- Expected cost R: `0.61468362`.
- Executed broker-cost REFUSED/source-gap rows: `0 / 0`.
- V186 fixed lifecycle root for `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`: scheduler rank `1`, scheduler score `2.618938145`, close/reverse authority allowed, release kind `opposite_open_close_reverse`, release risk `0.5`.
- New blocker: runtime risk rejects the same row with `recent_same_symbol_closed_trade_cooldown`; cooldown release reason is `cooldown_release_reason_not_allowed:same_symbol_daily_loss_lockout_after_closed_trade`.

## Patch Batch

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Repair type:

- behavior-changing correctness repair;
- risk-authority consumer repair, not a report-only helper;
- does not disable recent cooldown or same-symbol daily-loss lockout globally;
- keeps broker/live/final false.

Root fix:

- signed-executable daily-loss release now treats a conflict set as compatible when it contains daily-loss lockout plus recent same-symbol/same-cluster cooldown reasons;
- broad package-quality daily-loss release remains closed;
- unsigned, low-quality, broker-cost-refused, source-gap, and non-compatible conflict sets remain blocked;
- proof fields now surface `daily_loss_lockout_conflict_present`, `daily_loss_specialized_release_reason_compatible`, and compatible release reasons.

Focused proof already passed:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'package_cooldown_release_uses_raw_selector_promotion_contract_for_signed_executable_daily_loss_lockout or signed_open_reduced_package_releases_same_symbol_cooldown_floor_mismatch or risk_finalizer_primary_probe_alias_fields_preserve_cooldown_release_contract or runtime_risk_authority_blocks_same_symbol_after_recent_trade' -q --tb=short`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'explicit_package_close_reverse_uses_context_release_and_materialization_floors or current_package_order_authority_supersedes_stale_nested_false_inputs' -q --tb=short`

## Expected Replay Effect

- Candidate count should remain near `1130`; no candidate-generation narrowing is expected.
- The 17:45 row should no longer be blocked by `recent_same_symbol_closed_trade_cooldown` when the signed-executable release quality still passes.
- If the row transfers, scorecard/order/trade count may increase and missed positive R should drop by about the row's current `0.29090804R` opportunity proxy, unless a downstream order/fill/exit blocker is exposed.
- Executed broker-cost REFUSED/source-gap rows must remain `0 / 0`.
- Improvement must be classified as better risk/cooldown release authority, not broad trade blocking.

## Pass / Fail Criteria

Helped:

- the 17:45 row reaches scorecard/order/trade or exposes a new exact downstream blocker after cooldown release parity;
- V187 does not execute REFUSED/source-gap rows and does not collapse opportunity to look positive;
- any added/removed trades are attributed by exact candidate instance key.

Failed:

- the 17:45 row remains blocked by `recent_same_symbol_closed_trade_cooldown` or `same_symbol_daily_loss_lockout_after_closed_trade`;
- REFUSED/source-gap rows execute;
- trade/order transfer collapses without a terminal-source explanation.

## Planned Targeted Replay

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-04 \
  --end 2026-06-05 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD \
  --max-candidates-per-symbol-window 0 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V187_B7_SIGNED_EXECUTABLE_MIXED_COOLDOWN_DAILY_LOSS_RELEASE_20260604_20260605_XAUUSD_TARGETED
```
