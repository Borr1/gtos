# Historical OHLC GTOS Replay Exact-Spread Path-Control Packet

Generated UTC: `2026-05-16T03:29:58Z`

This packet recomputes M15 path controls for gradient-sensitive signatures where exact MT5 reference spread exists, and preserves unavailable exact-spread rows as stress-only controls.

## Counts

- `bucket_rows`: `28`
- `exact_descriptor_delta_rows`: `63`
- `exact_gradient_input_rows`: `63`
- `exact_path_control_rows`: `63`
- `gradient_input_rows`: `320`
- `question_rows`: `3`
- `source_manifest_rows`: `6`
- `spread_stress_input_rows`: `320`
- `unavailable_gradient_rows`: `257`
- `unavailable_stress_rows`: `257`

## Descriptor Delta Status

- `EXACT_DIFFERS_FROM_LOW_AND_HIGH_PROXY_DESCRIPTOR`: `9`
- `EXACT_MATCHES_HIGH_STATIC_PROXY_DESCRIPTOR`: `42`
- `EXACT_MATCHES_LOW_PROXY_DESCRIPTOR`: `12`

## Immediate Work

- Split exact descriptor deltas by route/entry/target-stop and execution-friction role.
- Probe unfilled retest-limit families with MT5 tick/M1 touch reconstruction.
- Join exact-spread path controls to same-M15 ambiguity and no-fill geometry controls.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
