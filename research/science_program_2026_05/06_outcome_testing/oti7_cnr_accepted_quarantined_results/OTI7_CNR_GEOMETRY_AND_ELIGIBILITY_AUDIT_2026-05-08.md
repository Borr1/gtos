# OTI7 CNR Geometry And Eligibility Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "geometry_and_eligibility_audit",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "eligibility_gate_order": [
    "accepted_ready_row_only",
    "blocked_row_exclusion",
    "source_hash_and_quote_recompute",
    "source_packet_geometry_present",
    "pre_entry_target_already_passed_check",
    "stop_target_geometry_check",
    "ordered_tick_terminal_scoring"
  ],
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "missing_geometry_count": 8,
  "missing_geometry_rows": [
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "row_number": 1601
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "row_number": 1605
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "row_number": 2521
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "row_number": 2525
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "row_number": 2541
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "row_number": 2545
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "row_number": 2561
    },
    {
      "packet_id": "OTG0-PKT-061",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "row_number": 2565
    }
  ],
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "quote_timestamp_mismatch_count": 0,
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "status_counts": {
    "SCORED_STOP_FIRST": 64,
    "SCORED_TARGET_FIRST": 12,
    "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
    "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18
  },
  "stop_invalid_count": 18,
  "stop_invalid_rows": [
    {
      "executable_entry_price": 75.678,
      "original_stop_loss": 74.378,
      "original_take_profit_1": 73.36,
      "record_id": "OTG0-PKT-060|XAGUSD_2026-05-06T07:15:00+00:00",
      "row_number": 1501,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.678,
      "original_stop_loss": 74.378,
      "original_take_profit_1": 73.36,
      "record_id": "OTG0-PKT-060|XAGUSD_2026-05-06T07:15:00+00:00",
      "row_number": 1505,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.888,
      "original_stop_loss": 74.107,
      "original_take_profit_1": 71.895,
      "record_id": "OTG0-PKT-060|XAGUSD_2026-05-06T07:30:00+00:00",
      "row_number": 1541,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.888,
      "original_stop_loss": 74.107,
      "original_take_profit_1": 71.895,
      "record_id": "OTG0-PKT-060|XAGUSD_2026-05-06T07:30:00+00:00",
      "row_number": 1545,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.992,
      "original_stop_loss": 74.249,
      "original_take_profit_1": 73.554,
      "record_id": "OTG0-PKT-060|XAGUSD_2026-05-06T08:45:00+00:00",
      "row_number": 1581,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.992,
      "original_stop_loss": 74.249,
      "original_take_profit_1": 73.554,
      "record_id": "OTG0-PKT-060|XAGUSD_2026-05-06T08:45:00+00:00",
      "row_number": 1585,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.678,
      "original_stop_loss": 74.378,
      "original_take_profit_1": 73.36,
      "record_id": "OTG0-PKT-062|XAGUSD_2026-05-06T07:15:00+00:00",
      "row_number": 4181,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.678,
      "original_stop_loss": 74.378,
      "original_take_profit_1": 73.36,
      "record_id": "OTG0-PKT-062|XAGUSD_2026-05-06T07:15:00+00:00",
      "row_number": 4185,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.888,
      "original_stop_loss": 74.107,
      "original_take_profit_1": 71.895,
      "record_id": "OTG0-PKT-062|XAGUSD_2026-05-06T07:30:00+00:00",
      "row_number": 4241,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.888,
      "original_stop_loss": 74.107,
      "original_take_profit_1": 71.895,
      "record_id": "OTG0-PKT-062|XAGUSD_2026-05-06T07:30:00+00:00",
      "row_number": 4245,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.992,
      "original_stop_loss": 74.249,
      "original_take_profit_1": 73.554,
      "record_id": "OTG0-PKT-062|XAGUSD_2026-05-06T08:45:00+00:00",
      "row_number": 4301,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.992,
      "original_stop_loss": 74.249,
      "original_take_profit_1": 73.554,
      "record_id": "OTG0-PKT-062|XAGUSD_2026-05-06T08:45:00+00:00",
      "row_number": 4305,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.678,
      "original_stop_loss": 74.378,
      "original_take_profit_1": 73.36,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T07:15:00+00:00",
      "row_number": 5901,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.678,
      "original_stop_loss": 74.378,
      "original_take_profit_1": 73.36,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T07:15:00+00:00",
      "row_number": 5905,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.888,
      "original_stop_loss": 74.107,
      "original_take_profit_1": 71.895,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T07:30:00+00:00",
      "row_number": 5961,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.888,
      "original_stop_loss": 74.107,
      "original_take_profit_1": 71.895,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T07:30:00+00:00",
      "row_number": 5965,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.992,
      "original_stop_loss": 74.249,
      "original_take_profit_1": 73.554,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T08:45:00+00:00",
      "row_number": 6021,
      "side": "SHORT"
    },
    {
      "executable_entry_price": 75.992,
      "original_stop_loss": 74.249,
      "original_take_profit_1": 73.554,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T08:45:00+00:00",
      "row_number": 6025,
      "side": "SHORT"
    }
  ],
  "target_already_passed_count": 0,
  "target_already_passed_rows": [],
  "validation_safe": false
}
```
