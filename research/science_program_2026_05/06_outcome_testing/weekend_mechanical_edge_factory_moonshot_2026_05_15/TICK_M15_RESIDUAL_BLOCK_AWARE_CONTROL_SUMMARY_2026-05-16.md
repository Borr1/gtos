# Tick M15 Residual Block-Aware Controls

Generated UTC: `2026-05-15T16:27:56Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: row reconstruction and block-aware diagnostics only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `residual_input_rows`: `18`
- `row_reconstruction_rows`: `10403`
- `flagged_descriptor_references`: `785`
- `unique_flagged_bars`: `448`
- `duplicate_flagged_references`: `337`
- `block_control_rows`: `72`
- `axis_stress_rows`: `621`
- `aggregate_concentration_rows`: `243`
- `source_join_missing_rows`: `0`

## Block-Control Buckets

- `BLOCK_CONTROL_RESIDUAL_LOW_TAIL`: `17`
- `BLOCK_CONTROL_WEAKENED`: `55`

## Boundary

- Every residual-denominator row is reconstructed and source-joined where possible.
- Block-aware controls preserve date, month, source-file, or UTC-hour flagged counts before rotating inside each block.
- Cross-descriptor duplicate bars are explicit; descriptor references must not be treated as independent trade opportunities.
