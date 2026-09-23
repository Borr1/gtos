# Sierra SCID M15 Primitive Factory

Generated UTC: `2026-05-15T17:21:01Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: primitive descriptors only. No target movement, strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `input_m15_bar_rows`: `250133`
- `primitive_event_rows`: `250133`
- `baseline_rows`: `120`
- `flag_summary_rows`: `1667`
- `question_rows`: `28`
- `source_symbols`: `30`
- `session_buckets`: `4`
- `bars_with_any_flag`: `152788`

## Flag Counts

- `abs_delta_p90`: `25270`
- `ask_volume_dominant_p80`: `50775`
- `bid_volume_dominant_p20`: `51210`
- `body_p90`: `26368`
- `close_near_high_range_p80`: `12985`
- `close_near_low_range_p80`: `13125`
- `lower_wick_rejection_range_p80`: `4025`
- `num_trades_p90`: `25199`
- `post_source_gap_first_bar`: `21991`
- `price_delta_divergence_active`: `6725`
- `range_p90`: `26208`
- `range_p95`: `13060`
- `upper_wick_rejection_range_p80`: `4305`
- `volume_p90`: `25100`

## Next Same-Resource Work

- Build same-symbol/session/horizon target movement controls from the Sierra M15 bar ledger.
- Add neighbor-placebo and source-gap controls before interpreting any primitive as residual.
- Compare Sierra futures proxy primitive families against existing Route C tick primitives.
