# Historical OHLC GTOS Replay Cost-Sensitivity Family Spread Packet

Generated UTC: `2026-05-16T03:21:59Z`

This packet aggregates changed cost-sensitive signatures by route/entry/target-stop family, probes read-only MT5 ticks for every gradient-sensitive reference window, and emits stress-bound rows for every gradient row.

## Counts

- `ambiguity_input_rows`: `2847`
- `bucket_rows`: `31`
- `changed_input_rows`: `5258`
- `exact_source_window_rows`: `68`
- `family_aggregate_rows`: `384`
- `gradient_exact_spread_rows`: `320`
- `gradient_input_rows`: `320`
- `question_rows`: `3`
- `source_manifest_rows`: `8`
- `spread_stress_bound_rows`: `320`
- `unfilled_input_rows`: `7824`
- `unfilled_recon_route_rows`: `192`

## Exact Spread Buckets

- `EXACT_SPREAD_ABOVE_STATIC_PROXY_SUPRA_STATIC_STRESS_REQUIRED`: `51`
- `EXACT_SPREAD_UNAVAILABLE_STRESS_PAIR_ONLY`: `257`
- `EXACT_SPREAD_WITHIN_MEDIAN_PROXY_BOUND_NONSTATIC_DESCRIPTOR`: `12`

## Immediate Work

- Re-run exact-cost path controls for gradient-sensitive rows using the extracted spread brackets.
- Probe cost-invariant unfilled retest-limit families with MT5 tick/M1 touch reconstruction.
- Join exact-spread and unfilled reconstruction to same-M15 ambiguity and no-fill geometry controls.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
