# Historical OHLC GTOS Branch Source-Repair Feasibility

Generated UTC: 2026-05-16T06:53:45Z

## Boundary

Historical OHLC GTOS branch source-repair feasibility packet only. Rows preserve all 386 branches and classify current exact-spread/source feasibility, proxy fallbacks, and same-resource next actions. Exact broker R/PnL, strategy expectancy, win-rate, validation, live-readiness, promotion, and live behavior change are not claimed.

## Counts

- matrix_branch_input_rows: 386
- matrix_source_input_rows: 386
- exact_spread_delta_input_rows: 63
- exact_spread_unavailable_input_rows: 257
- branch_feasibility_rows: 386
- action_rows: 386
- exact_spread_route_rows: 386
- bucket_rows: 25
- question_rows: 4
- source_manifest_rows: 5

## Feasibility Distribution

- CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED: 16
- EXACT_SPREAD_RECOMPUTED_FROM_CURRENT_SOURCE: 59
- EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY: 138
- PROVENANCE_ONLY_NO_SINGLE_SOURCE_REPAIR: 2
- ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_REPLAY_AVAILABLE: 171
