# Historical OHLC GTOS Replay Cost-Sensitivity Split

Generated UTC: `2026-05-16T03:08:55Z`

This packet splits changed, gradient-sensitive, unfilled, and same-M15 ambiguous cost-sensitivity signatures into immediate work routes.

## Counts

- `ambiguity_signature_rows`: `2847`
- `bucket_rows`: `112`
- `changed_signature_rows`: `5258`
- `gradient_requirement_rows`: `320`
- `question_rows`: `3`
- `signature_input_rows`: `61312`
- `source_manifest_rows`: `4`
- `unfilled_split_rows`: `7824`

## Immediate Work

- Aggregate changed signatures by route/entry/target-stop family.
- Search exact spread/slippage source for gradient-sensitive rows or build conservative stress bounds.
- Join unfilled and ambiguity signatures to M1/tick/no-fill reconstruction routes.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
