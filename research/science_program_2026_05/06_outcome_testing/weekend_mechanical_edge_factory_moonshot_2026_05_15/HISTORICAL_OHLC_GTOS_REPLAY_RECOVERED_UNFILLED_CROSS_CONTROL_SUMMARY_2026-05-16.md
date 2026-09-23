# Historical OHLC GTOS Replay Recovered-Unfilled Cross-Control Join

Generated UTC: `2026-05-16T03:55:15Z`

This packet joins recovered unfilled path controls with exact-spread/stress controls and no-fill geometry branch context.

## Counts

- `bucket_rows`: `49`
- `exact_context_rows`: `320`
- `exact_descriptor_delta_input_rows`: `63`
- `exact_unavailable_stress_input_rows`: `257`
- `family_join_rows`: `266`
- `nofill_ambiguity_branch_input_rows`: `400`
- `nofill_context_rows`: `400`
- `nofill_repair_branch_input_rows`: `400`
- `question_rows`: `5`
- `recovered_entry_input_rows`: `51`
- `recovered_signature_input_rows`: `816`
- `signature_join_rows`: `816`
- `source_manifest_rows`: `7`

## Family Status

- `EXACT_DELTA_AND_UNAVAILABLE_STRESS_ONLY_FAMILY`: `27`
- `EXACT_DELTA_ONLY_FAMILY`: `17`
- `RECOVERED_ONLY_FAMILY`: `59`
- `RECOVERED_WITH_EXACT_DELTA_AND_UNAVAILABLE_STRESS_FAMILY`: `6`
- `RECOVERED_WITH_EXACT_DELTA_FAMILY`: `9`
- `RECOVERED_WITH_UNAVAILABLE_STRESS_FAMILY`: `54`
- `UNAVAILABLE_STRESS_ONLY_FAMILY`: `94`

## Immediate Work

- Split exact-differs rows by route/entry/target-stop and spread interval mechanics.
- Stress recovered fill-bar order-unresolved rows with M1/tick ordering where available.
- Convert confirmed no-fill signatures into execution-friction/fillability branch controls.
- Build cost/fill/path family synthesis preserving all family rows.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
