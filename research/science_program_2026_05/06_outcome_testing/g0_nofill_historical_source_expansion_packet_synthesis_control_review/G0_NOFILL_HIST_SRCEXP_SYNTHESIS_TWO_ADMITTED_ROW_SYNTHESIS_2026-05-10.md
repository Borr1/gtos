# G0 NOFILL Historical Source Expansion Two Admitted Row Synthesis

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Summary

The two admitted rows are source/control packet rows only and do not support validation.

## Machine Payload

```json
{
  "admitted_row_count": 2,
  "artifact_family": "two_admitted_row_source_control_synthesis",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T07:53:15Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW",
  "rows": [
    {
      "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
      "decision_time_utc": "2026-05-08T15:45:00+00:00",
      "entry_touch_spread_status": "ENTRY_TOUCH_NOT_OBSERVED_SOURCE_SAFE",
      "field_count": 55,
      "future_logger_field_count": 20,
      "missing_source_state_fields": [
        "cancel_expiry_utc",
        "capture_clock_skew_ms",
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "native_pending_order_type_source_safe",
        "regime_context_status",
        "session_tag"
      ],
      "native_pending_order_type_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "parser_code_hash": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
      "pending_order_mode_status": "PENDING_ORDER_MODE_CAPTURED_SOURCE_SAFE",
      "protective_area_touch_status": "PROTECTIVE_AREA_NOT_TOUCHED_SOURCE_SAFE",
      "safe_flags": {
        "live_effect": false,
        "opens_result_scoring": false,
        "opens_validation": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "source_artifact_hash": "53a5b700c2044a9c424259e3aa44f7b350837a1efd9ccc7b2ad16b5eecc74358",
      "source_date": "2026-05-08",
      "source_files_sha256": {
        "candidate_ltf_path_order": "0ed23ea479b2a98a98021a67c838c7b27f9c0a2ee280193cefa25d8a01ed208f",
        "candidate_registry_audit": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
        "pending_limit_lifecycle": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
        "pending_limit_lifecycle_audit": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
        "tick_parquet": "5ba5af2f5b1a9561397ecd0adf397fd4eeba942fe9c218f066c74288436b9e31"
      },
      "source_symbol": "NDX100",
      "symbol": "NAS100",
      "terminal_area_touch_status": "TERMINAL_AREA_TOUCHED_SOURCE_SAFE"
    },
    {
      "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
      "decision_time_utc": "2026-05-08T13:45:00+00:00",
      "entry_touch_spread_status": "ENTRY_TOUCH_NOT_OBSERVED_SOURCE_SAFE",
      "field_count": 55,
      "future_logger_field_count": 20,
      "missing_source_state_fields": [
        "cancel_expiry_utc",
        "capture_clock_skew_ms",
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "native_pending_order_type_source_safe",
        "regime_context_status",
        "session_tag"
      ],
      "native_pending_order_type_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "parser_code_hash": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
      "pending_order_mode_status": "PENDING_ORDER_MODE_CAPTURED_SOURCE_SAFE",
      "protective_area_touch_status": "PROTECTIVE_AREA_NOT_TOUCHED_SOURCE_SAFE",
      "safe_flags": {
        "live_effect": false,
        "opens_result_scoring": false,
        "opens_validation": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "source_artifact_hash": "dd55c753d9c544558741795303ccdb5a54a0e1cda8177a22d61f952ef8d0a698",
      "source_date": "2026-05-08",
      "source_files_sha256": {
        "candidate_ltf_path_order": "0ed23ea479b2a98a98021a67c838c7b27f9c0a2ee280193cefa25d8a01ed208f",
        "candidate_registry_audit": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
        "pending_limit_lifecycle": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
        "pending_limit_lifecycle_audit": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
        "tick_parquet": "bfed917d099ba990458319e4c607e405e3a53de458be13d9dc893be011fc4cd6"
      },
      "source_symbol": "US30",
      "symbol": "US30_cash",
      "terminal_area_touch_status": "TERMINAL_AREA_TOUCHED_SOURCE_SAFE"
    }
  ],
  "schema_version": "g0_nofill_historical_source_expansion_packet_synthesis_control_review_v1",
  "source_control_interpretation": [
    "Both rows show source-bound NOFILL-style terminal-area touch status without limit-touch status in the packet contract.",
    "Both rows carry safe redactions for execution/slippage/order-ticket fields.",
    "Both rows leave validation, result scoring, cost labels, and broker outcomes closed.",
    "n=2 is a source-control packet seed, not a validation denominator."
  ],
  "summary": "The two admitted rows are source/control packet rows only and do not support validation.",
  "validation_safe": false,
  "validation_sufficiency": {
    "reason": "Two rows cannot clear sample floor, duplicate concentration, symbol/session/regime split, no-leak validation, or result/cost accounting gates.",
    "sufficient_for_validation": false
  }
}
```
