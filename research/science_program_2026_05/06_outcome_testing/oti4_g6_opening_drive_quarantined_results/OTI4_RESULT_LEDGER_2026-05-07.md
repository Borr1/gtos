# OTI4 G6 Opening-Drive Result Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`  
**Validation safe:** `False`  
**Outcome review opened:** `False`

## Summary

| item | value |
| --- | --- |
| raw records | 86 |
| unique duplicate groups | 19 |
| prereg countable unique groups | 0 |
| sample floor | 200 |
| result status | NOT_COMPUTABLE |
| computed continuation expectancy R | None |
| computed countable n | 0 |

## Not Computable Reason Counts

| reason | rows |
| --- | --- |
| decision_asof_after_ohlc_source_last_timestamp | 86 |
| duplicate_breakout_key_declares_NO_BREAKOUT_ASOF | 86 |
| missing_prereg_opening_drive_field_breakout_close_time | 86 |
| missing_prereg_opening_drive_field_breakout_side | 86 |
| missing_prereg_opening_drive_field_range_high | 86 |
| missing_prereg_opening_drive_field_range_low | 86 |
| no_ohlc_bars_for_frozen_range_window | 86 |
| no_ohlc_bars_for_path_window | 86 |
| opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF | 86 |
| same_bar_terminal_order_uncertainty_flagged | 6 |

## Quarantine Note

No prereg-compatible opening-drive continuation outcome was computed. Every row is source-blocked or noncountable, and raw path labels, broker actual-R, blocked outcomes, and live trade results were not opened.
