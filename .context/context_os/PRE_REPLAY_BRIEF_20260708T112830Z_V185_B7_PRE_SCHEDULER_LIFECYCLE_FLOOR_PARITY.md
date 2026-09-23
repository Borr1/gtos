# V185 B7 Pre-Replay Brief - Pre-Scheduler Lifecycle Floor Parity

Generated UTC: 2026-07-08T11:28:30Z.

## Control State

- Fable batch: B7 runtime transfer, `B7_pre_scheduler_lifecycle_resolver_source_bound_floor_parity`.
- Latest completed replay baseline: `BROAD_LIVE_AS_IF_REPLAY_V184_B7_CLOSE_REVERSE_ROUTER_REFUSAL_RISK_PARITY_20260604_20260605_XAUUSD_TARGETED`.
- Broker mutation, live broker authority, and final selection remain false.
- Replay scope: bounded XAUUSD 2026-06-04..2026-06-05 targeted slice. This proves or rejects this local repair only; it is not full-reservoir conversion evidence.

## V184 Baseline

- Candidates / scorecards / order events / terminal orders / trades / missed / buckets: `1130 / 184 / 17 / 9 / 8 / 1121 / 31`.
- W/L/F: `5/3/0`.
- Net/gross/final R: `0.50779951 / 1.12248313 / 1.12248313`.
- Cash PnL / risk cash / risk pct: `114.93888574 / 4858.62127863 / 4.875`.
- Expected cost R: `0.61468362`.
- Executed broker-cost REFUSED/source-gap rows: `0 / 0`.
- Main exposed bug: `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00` is package-executable, cost PASSED, and source-complete in candidate/packet sidecar, but is final-blocked before scheduler ranking by generic close/reverse lifecycle floors.

## Patch Batch

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Repair type:

- behavior-changing correctness repair;
- producer/consumer repair, not a report-only helper;
- does not loosen broker-cost REFUSED, source-gap, unresolved fill-floor, or off-authority rows;
- keeps broker/live/final false.

Root fix:

- `replay_lifecycle_action_resolver_detail()` now recognizes explicit source-bound package materialization for open-reduced replay rows;
- signed source-bound/open-reduced close/reverse rows can consume the same source-bound/router lifecycle floor family before scheduler ranking;
- proof fields identify `lifecycle_router_refusal_floor_applies`, `explicit_source_bound_package_materialized`, `source_bound_package_materializer`, and raw-selector promotion contract status.

Focused proof already passed:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'replay_lifecycle_explicit_source_bound_close_reverse_uses_router_lifecycle_floors or replay_lifecycle_source_bound_fill_floor_opposite_side_derives_signed_authority or runtime_close_reverse_uses_router_refusal_lifecycle_floors_for_signed_package_rows' -q --tb=short`

## Expected Replay Effect

- Candidate count should remain near `1130`; no candidate-generation narrowing is expected.
- Scorecard/order transfer may increase for exact signed source-bound/open-reduced lifecycle rows.
- The 17:45 Aristotle row should either become scheduler-rankable/order-present/traded, or move to a new exact downstream blocker after pre-scheduler lifecycle floor parity.
- Missed positive R should drop if that row transfers; missed negative R may move only for rows matching the same causal contract.
- Executed broker-cost REFUSED/source-gap rows must remain `0 / 0`.
- Improvement must be classified as better lifecycle-to-scheduler conversion, not broad trade blocking.

## Pass / Fail Criteria

Helped:

- the 17:45 row is no longer blocked by `package_lifecycle_action_resolution_required:expected_net_r_below_floor` before scheduler ranking;
- added/removed trades are attributed by exact candidate instance key;
- V185 does not execute REFUSED/source-gap rows and does not collapse opportunity to look positive.

Failed:

- the 17:45 row remains final-blocked by the same generic close/reverse floor;
- scorecard/order transfer collapses without a terminal-source explanation;
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
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V185_B7_PRE_SCHEDULER_LIFECYCLE_FLOOR_PARITY_20260604_20260605_XAUUSD_TARGETED
```
