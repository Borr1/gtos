# OTI4 G6 Opening-Drive Duplicate Denominator Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`

```json
{
  "artifact_family": "OTI4_G6_OPENING_DRIVE_DUPLICATE_DENOMINATOR_REPORT",
  "denominator_inflation_factor_raw_over_unique": 4.526316,
  "denominator_policy": "Use unique duplicate_group_id/duplicate_breakout_key, never raw records, for any future countable opening-drive denominator.",
  "duplicate_group_reuse_count": 12,
  "group_rows": [
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|GBPJPY|2026-05-04|tokyo|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-04T02:15:00+00:00",
      "last_decision_asof_utc": "2026-05-04T03:00:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 3,
      "sessions": [
        "tokyo"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "GBPJPY"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|GBPJPY|2026-05-06|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-06T07:30:00+00:00",
      "last_decision_asof_utc": "2026-05-06T07:45:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF",
        "same_bar_terminal_order_uncertainty_flagged"
      ],
      "raw_child_rows": 2,
      "sessions": [
        "london"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "GBPJPY"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|GBPJPY|2026-05-06|tokyo|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-06T02:30:00+00:00",
      "last_decision_asof_utc": "2026-05-06T02:30:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "tokyo"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "GBPJPY"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|NAS100|2026-05-03|ny|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-03T16:15:00+00:00",
      "last_decision_asof_utc": "2026-05-03T16:15:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "ny"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "NAS100"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|NAS100|2026-05-04|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-04T10:30:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 2,
      "sessions": [
        "london"
      ],
      "sides": [
        "LONG",
        "SHORT"
      ],
      "symbols": [
        "NAS100"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|NAS100|2026-05-04|ny|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-04T13:15:00+00:00",
      "last_decision_asof_utc": "2026-05-04T17:00:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 12,
      "sessions": [
        "ny"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "NAS100"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|NAS100|2026-05-05|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-05T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-05T07:15:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "london"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "NAS100"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|NAS100|2026-05-06|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "london"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "NAS100"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|US30_cash|2026-05-06|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-06T09:15:00+00:00",
      "last_decision_asof_utc": "2026-05-06T09:15:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "london"
      ],
      "sides": [
        "LONG"
      ],
      "symbols": [
        "US30_cash"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|USDJPY|2026-05-05|tokyo|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-05T00:45:00+00:00",
      "last_decision_asof_utc": "2026-05-05T00:45:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "tokyo"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "USDJPY"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAGUSD|2026-05-04|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-04T10:30:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 14,
      "sessions": [
        "london"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAGUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAGUSD|2026-05-04|ny|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-04T13:15:00+00:00",
      "last_decision_asof_utc": "2026-05-04T17:00:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 16,
      "sessions": [
        "ny"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAGUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAGUSD|2026-05-05|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-05T07:30:00+00:00",
      "last_decision_asof_utc": "2026-05-05T10:30:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 11,
      "sessions": [
        "london"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAGUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAGUSD|2026-05-05|ny|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-05T14:15:00+00:00",
      "last_decision_asof_utc": "2026-05-05T17:00:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 10,
      "sessions": [
        "ny"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAGUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAGUSD|2026-05-06|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-06T08:45:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF",
        "same_bar_terminal_order_uncertainty_flagged"
      ],
      "raw_child_rows": 3,
      "sessions": [
        "london"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAGUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAUUSD|2026-05-03|ny|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-03T16:15:00+00:00",
      "last_decision_asof_utc": "2026-05-03T16:30:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 2,
      "sessions": [
        "ny"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAUUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAUUSD|2026-05-04|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 1,
      "sessions": [
        "london"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAUUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAUUSD|2026-05-05|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-05T08:00:00+00:00",
      "last_decision_asof_utc": "2026-05-05T08:15:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF"
      ],
      "raw_child_rows": 2,
      "sessions": [
        "london"
      ],
      "sides": [
        "SHORT"
      ],
      "symbols": [
        "XAUUSD"
      ]
    },
    {
      "countable_prereg_opening_drive_unit": false,
      "duplicate_group_id": "G6_OPENING_DRIVE|XAUUSD|2026-05-06|london|NO_BREAKOUT_ASOF",
      "first_decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "last_decision_asof_utc": "2026-05-06T08:00:00+00:00",
      "not_computable_reasons": [
        "decision_asof_after_ohlc_source_last_timestamp",
        "duplicate_breakout_key_declares_NO_BREAKOUT_ASOF",
        "missing_prereg_opening_drive_field_breakout_close_time",
        "missing_prereg_opening_drive_field_breakout_side",
        "missing_prereg_opening_drive_field_range_high",
        "missing_prereg_opening_drive_field_range_low",
        "no_ohlc_bars_for_frozen_range_window",
        "no_ohlc_bars_for_path_window",
        "opening_drive_packet_status_SOURCE_BLOCKED_NO_RANGE_BARS_ASOF",
        "same_bar_terminal_order_uncertainty_flagged"
      ],
      "raw_child_rows": 2,
      "sessions": [
        "london"
      ],
      "sides": [
        "LONG",
        "SHORT"
      ],
      "symbols": [
        "XAUUSD"
      ]
    }
  ],
  "max_records_per_duplicate_group": 16,
  "outcome_review_opened": false,
  "prereg_countable_unique_groups": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_record_count": 86,
  "unique_duplicate_group_count": 19,
  "validation_safe": false
}
```
