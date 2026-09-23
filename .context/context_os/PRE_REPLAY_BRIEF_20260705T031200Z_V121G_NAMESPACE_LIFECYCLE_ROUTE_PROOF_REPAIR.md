# V121G Pre-Replay Brief - Namespace, Lifecycle, Route Proof Repair

Generated: 2026-07-05T03:12:00Z

This is a bounded one-day repair proof, not total reservoir conversion proof. The replay window is 2026-05-15 only, full-grid, repaired profile, broker/live/final closed.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121F_AUTHORITY_PROJECTION_PARITY_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Candidates / scorecards / order rows / simulated orders / accepted pending / trades / missed: 8174 / 96 / 12 / 6 / 6 / 1 / 8168
- Net R / gross R / final R / cash PnL: -1.03400946 / -1.0 / -1.0 / -1034.00946
- W/L/F: 0/1/0
- Expired unfilled: 5
- Risk cash / risk pct sum: 1000.0 / 1.0
- Broker/live/final: false / false / false

## Baseline Delta

- V121E: 15 simulated orders, 15 accepted pending, 14 expired, 1 filled trade, net R -1.03402526, cash PnL -562.25123512, risk pct sum 0.54375.
- V121F: 6 simulated orders, 6 accepted pending, 5 expired, 1 filled trade, net R -1.03400946, cash PnL -1034.00946, risk pct sum 1.0.
- Interpretation: V121F removed optimistic order materialization, but still leaves diagnostic-only rows in lifecycle/risk counters.

## Incorporated Subagent Findings

- Parfit: open probability namespace collision. Scheduler signed authority uses generic `fill_probability` as execution fillability while selector quality treats generic `fill_probability` as entry quality.
- Harvey: open diagnostic lifecycle leak. Diagnostic-only fill rows are blocked in transfer fields but still bind pending lifecycle and accepted-risk counters.
- Harvey: open fallback geometry leak. A guarded fallback thesis-geometry unusable reason can still pass through passive queue availability.
- Hegel: open route proof selection leak. V121F artifacts are materialized, but active root-map/manifest selection still points at older prefixes.

## Patch Batch

Correctness repairs:
- make signed authority generic `fill_probability` entry-quality only and keep order fillability under `execution_fill_probability`, `limit_fillability_probability`, and `predecision_limit_fillability_probability`;
- make selector quality contract fail when `fill_probability` provenance is limit/execution fillability;
- prevent diagnostic-only fill rows from reserving risk, pending order state, or expiry lifecycle events;
- make thesis-geometry unusable fallback non-degradable even when passive queue is available.

Route/proof repairs:
- update active `CURRENT_ROOT_CAUSE_MAP.json` to V121G;
- build current parity artifacts after replay;
- run route builder/verifier against current-prefix selection.

## Expected Measurable Effects

- Candidate -> scorecard: should remain 8174 -> 96 unless selector quality provenance exposes more source-required rows.
- Scorecard -> order: should drop for diagnostic-only rows that previously materialized pending orders.
- Order -> fill: true fills should remain bounded to executable rows only.
- Missed positive/negative R: may increase or become more explicit because diagnostic opportunities move to missed/non-executable instead of lifecycle.
- Trade count and net R: may remain one trade around -1.034R; no positive-by-suppression claim is accepted.
- Cost-refused/source-gap execution: must remain zero.
- Risk distribution: diagnostic-only rows must not inflate accepted-risk or pending lifecycle counts.

## Replay Command

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-15 \
  --end 2026-05-15 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V121G_NAMESPACE_LIFECYCLE_ROUTE_PROOF_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --skip-tick-source \
  --compact-missed-ledger
```

## Success / Failure Criteria

Helped:
- diagnostic-only orders no longer appear as accepted pending or expiry lifecycle rows;
- fallback thesis-geometry unusable + passive queue returns contract unmet;
- signed authority payload and selector quality contract keep entry-quality and execution fillability separate;
- selected route prefix advances to V121G/V121F artifacts for parity/verifier proof.

Failed:
- diagnostic-only fill realism still binds pending lifecycle;
- generic `fill_probability` still carries execution fillability;
- passive queue still overrides thesis-geometry fallback unusability;
- verifier selects an older broad prefix.

