# V121F Pre-Replay Brief - Authority Projection Parity Repair

Generated: 2026-07-05T02:43:45Z

This is a bounded one-day repair proof, not total reservoir conversion proof.
The replay window is 2026-05-15 only, full-grid, repaired profile, broker/live/final closed.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121E_ORDER_FILLABILITY_EXECUTION_AUTHORITY_SPLIT_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Profile: `repaired_package_conversion_v3`
- Candidates / scorecards / order events / accepted pending / trades / missed: 8174 / 96 / 30 / 15 / 1 / 8159
- Net R / gross R / final R / cash PnL: -1.03402526 / -1.0 / -1.0 / -562.25123512
- W/L/F: 0/1/0
- Expired unfilled: 14
- Missed positive / negative net R: 377.96759776 / -1535.48823833
- Missed counterfactual positive / negative rows: 326 / 1148
- Risk decisions on accepted orders: trade 5, open-reduced-risk 10
- Broker/live/final: false / false / false

## Baseline Comparisons

- V121E vs V121C: added minus removed net R = 2.76872074, added transfer net positive = false, removed transfer net positive = false.
- V121E vs V121D: added minus removed net R = 2.76872074, added transfer net positive = false, removed transfer net positive = false.
- This smoke proves local authority/projection repair only. It does not prove the million-R reservoir transferred.

## Current Patch Batch

Correctness repairs:
- Broker-cost floor selector reason no longer opens reduced risk unless explicit package authority allows it.
- Scheduler risk ladder distinguishes raw selector origin from signed materialized reduced origin.
- Full-risk ladder rows downgrade unless signed authority, broker cost, source completeness, fill-floor resolution, and full-risk applied/allowed are all true.
- Diagnostic fill rows become non-executable transfer rows with `diagnostic_counterfactual_only`.
- Fallback thesis-geometry failures block; they no longer degrade to passive-limit queue release.

Diagnostic/ledger repairs:
- Missed rows use `same_symbol_replay_exposure_ledger_fields(...)`.
- Order rows carry fill-realism fields and diagnostic scope.
- Source-bound parity relabels raw selector rejects with downstream fields as downstream materialization leaks.

## Refreshed Parity Result

- Prefix: `SOURCE_BOUND_TO_EXECUTED_PARITY_V121E_ORDER_FILLABILITY_EXECUTION_AUTHORITY_SPLIT_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Parity rows / source member axes: 7003 / 1101
- Bad pure selector-reject rows with scheduler option present: 0
- New explicit downstream materialized selector-reject rows: 4368
- Top labels:
  - `candidate_generated_selector_reject_downstream_execution_materialized:missed_count`: 3912
  - `candidate_generated_selector_reject_downstream_execution_materialized:scheduler_option_present_count`: 456

## Failed Partial Attempt

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121F_AUTHORITY_PROJECTION_PARITY_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Status: failed partial, not behavioral evidence.
- Artifact written before failure: `BROAD_LIVE_AS_IF_REPLAY_V121F_AUTHORITY_PROJECTION_PARITY_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS_SOURCE_UNIVERSE_LEDGER.jsonl`
- Failure: `run_campaign` referenced `scheduler_limits` during candidate namespace backfill before defining it at campaign scope.
- Repair before rerun: `run_campaign` now initializes `scheduler_limits = scheduler_config(config)` once during campaign setup.

## Expected Measurable Effects

- Candidate -> scorecard: should stay comparable to V121E unless diagnostic demotion affects materialization.
- Scorecard -> order: may drop if prior orders were diagnostic-fill or geometry-breach authority leaks.
- Order -> fill: may drop; diagnostic fill authority must not fill executable trades.
- Missed positive R: may increase if former optimistic fills become missed diagnostics.
- Missed negative R: may also increase; this is acceptable if it exposes honest non-executable opportunity.
- Trade count: may remain 1 or decrease; no positive-by-suppression claim accepted.
- Net/gross/final R: may worsen or improve; correctness gates are primary for V121F.
- Cost-refused/source-gap execution: must remain 0.
- Risk distribution: full-risk rows must have complete signing fields, reduced rows must carry causes.

## Replay Command

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-15 \
  --end 2026-05-15 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V121F_AUTHORITY_PROJECTION_PARITY_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --skip-tick-source \
  --compact-missed-ledger
```

## Success / Failure Criteria

Helped:
- Verifier authority leaks above drop materially or to zero.
- Diagnostic fill rows no longer appear executable.
- Geometry-breach degraded releases disappear.
- Missed same-symbol context missing rows drop materially or to zero.
- Trade/R deltas are explainable by authority truth, not opportunity suppression.

Failed:
- REFUSED/source-gap rows execute.
- Full-risk rows still miss signing fields.
- Diagnostic fill rows bind as executable order/trade transfer.
- Geometry-breach fallback still releases passive queue.
- Replay becomes positive only by collapsing opportunity without explaining missed positive R.

Next deeper flaw exposed:
- If authority leaks clear but R remains negative, inspect top V121F losing bucket first, then targeted 5-day hostile and non-May regime proofs before policy tuning.
