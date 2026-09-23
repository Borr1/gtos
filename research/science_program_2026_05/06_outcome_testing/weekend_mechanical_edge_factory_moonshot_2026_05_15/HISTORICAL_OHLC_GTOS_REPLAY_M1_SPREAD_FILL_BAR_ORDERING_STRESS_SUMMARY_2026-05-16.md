# Historical OHLC GTOS Replay M1 Spread Fill-Bar Ordering Stress

Generated UTC: `2026-05-16T04:43:48Z`

Historical OHLC GTOS replay M1 spread fill-bar ordering stress only. This packet preserves the full upstream M1 spread-adjusted signature denominator, splits rows whose original m1_first_touch_status has fill-bar order-unresolved target/stop touches into optimistic and conservative M1 interval statuses, and uses MT5 M1 bars read-only where row fields alone cannot evaluate the conservative next-bar path. It makes no validation, R/PnL, win-rate, expectancy, live-readiness, promotion, or live behavior-change claim.

## Counts

- `input_signature_rows`: `2256`
- `input_cost_model_rows`: `141`
- `output_signature_rows`: `2256`
- `family_rows`: `480`
- `bucket_rows`: `44`
- `question_rows`: `6`
- `fill_bar_order_unresolved_rows`: `176`
- `conservative_target_after_fill_bar_rows`: `164`
- `conservative_no_touch_after_fill_bar_rows`: `0`
- `conservative_stop_after_fill_bar_rows`: `0`
- `conservative_same_m1_ambiguous_after_fill_bar_rows`: `0`
- `conservative_source_fail_closed_rows`: `12`
- `source_manifest_rows`: `5`

## Conservative First-Touch Status

- `CONSERVATIVE_CARRIED_NO_TARGET_OR_STOP_TOUCH_WITHIN_M1_REPLAY_HORIZON`: `536`
- `CONSERVATIVE_CARRIED_TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY`: `1544`
- `CONSERVATIVE_TARGET_TOUCH_FIRST_OR_ONLY_AFTER_FILL_BAR`: `164`
- `MT5_M1_NO_NEXT_BAR_IN_ORIGINAL_REPLAY_WINDOW_FAIL_CLOSED`: `12`

## Interval Status

- `INTERVAL_NOT_APPLICABLE_NON_FILL_BAR_ORDER_STATUS_CARRIED`: `2080`
- `INTERVAL_OPTIMISTIC_TARGET_TO_CONSERVATIVE_SOURCE_FAIL_CLOSED`: `12`
- `INTERVAL_OPTIMISTIC_TARGET_TO_CONSERVATIVE_TARGET`: `164`

## Verifier

- `ok`: `True`
- `signature_rows_preserve_full_denominator`: `True`
- `fill_bar_unresolved_rows_preserved`: `True`
- `all_signature_rows_have_safe_flags`: `True`
- `all_family_rows_have_safe_flags`: `True`
- `source_manifest_all_files_hashed`: `True`
- `no_output_manifest_or_sprint_ledger_write`: `True`

## Next Unresolved Questions

- `OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-001`: How many upstream signatures required fill-bar ordering stress? (`row_count=176`)
- `OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-002`: How many optimistic fill-bar target touches remain target-first after excluding the fill bar? (`row_count=164`)
- `OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-003`: How many optimistic fill-bar target touches become no-touch under the conservative next-bar path? (`row_count=0`)
- `OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-004`: How many optimistic fill-bar target touches become stop-first under the conservative next-bar path? (`row_count=0`)
- `OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-005`: How many conservative next-bar paths remain same-M1-bar target/stop ambiguous? (`row_count=0`)
- `OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-006`: How many fill-bar stress rows failed closed due missing next-bar M1 source? (`row_count=12`)

This branch-local fill-bar ordering stress packet does not complete the weekend moonshot objective and does not close tick-level ordering uncertainty.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
