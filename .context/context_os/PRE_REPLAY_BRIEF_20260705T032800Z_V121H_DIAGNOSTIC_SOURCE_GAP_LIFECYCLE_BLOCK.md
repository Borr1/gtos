# V121H Pre-Replay Brief - Diagnostic Source-Gap Lifecycle Block

Generated: 2026-07-05T03:28:00Z

This remains the same one-day bounded repair proof. It is not total reservoir conversion proof.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121G_NAMESPACE_LIFECYCLE_ROUTE_PROOF_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Candidates / scorecards / order rows / simulated orders / accepted pending / trades / missed: 8174 / 96 / 11 / 6 / 5 / 1 / 8168
- Net R / gross R / final R / cash PnL: -1.03400946 / -1.0 / -1.0 / -1034.00946
- W/L/F: 0/1/0
- Expired unfilled: 4

## Newly Exposed Same-Root Leak

V121G blocked the ordered-tick diagnostic row from pending lifecycle, but four `postdecision_ordered_path_source_gap_or_entry_not_touched` diagnostic rows still emitted accepted-pending rows and four expiry rows. These rows already carry `diagnostic_fill_only=True`, `fill_realism_executable=False`, and `package_execution_result_scope=diagnostic_counterfactual_only` after normalization, but the lifecycle gate ran before that normalization and only checked the ordered-tick event-queue flag.

## Patch

Treat any fill-realism row with `fill_realism_executable is False` and a non-empty, non-`not_filled` `fill_realism_class` as diagnostic-lifecycle-blocked before pending state, accepted-risk counters, or expiry queueing.

## Expected Measurable Effect

- accepted pending should drop from 5 to 1;
- expired unfilled should drop from 4 to 0;
- order rows should drop diagnostic pending/expiry materialization and retain only diagnostic order events plus the true filled trade lifecycle;
- net R should remain around -1.03400946 unless lifecycle counters were changing candidate admission later in the day;
- no broker/live/final authority.

