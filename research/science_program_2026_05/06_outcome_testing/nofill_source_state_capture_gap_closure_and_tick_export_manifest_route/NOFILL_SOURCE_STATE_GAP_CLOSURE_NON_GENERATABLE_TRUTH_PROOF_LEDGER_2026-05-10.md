# Nofill Source State Gap Closure Non Generatable Truth Proof Ledger 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

- row_count: `37`

## Machine Payload

```json
{
  "all_rows_price_tick_bar_backfill_possible": false,
  "artifact_family": "non_generatable_historical_truth_proof_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T08:33:44Z",
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
  "proof_rule": "Historical GTOS source-state truth requires contemporaneous source-safe GTOS logs. Market data can support future path/coverage fields, but cannot reconstruct missing pending intent, lifecycle group, write-clock, ticket redaction, order observability, or native order-type truth.",
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "row_count": 37,
  "rows_count": 37,
  "rows_sample": [
    {
      "action_required_codes": [
        "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP"
      ],
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "decision_time_utc": "2026-04-14T01:15:05.006410+00:00",
      "existing_source_safe_evidence_found": false,
      "final_state_status": "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
      "forward_capture_fields_required": [
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "capture_latency_ms",
        "capture_clock_source_status",
        "capture_clock_skew_ms",
        "capture_clock_skew_status",
        "pending_order_mode_source_safe",
        "pending_order_mode_status",
        "broker_pending_order_created_status",
        "native_pending_order_type_source_safe",
        "native_pending_order_type_status",
        "pending_intent_created_utc",
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "cancel_expiry_utc",
        "cancel_expiry_reason_status",
        "entry_touch_first_utc",
        "side_aware_entry_touch_status",
        "terminal_area_touch_status",
        "terminal_area_first_touch_utc",
        "protective_area_touch_status",
        "protective_area_first_touch_utc",
        "event_order_resolution_method",
        "same_tick_same_bar_ambiguity_status"
      ],
      "missing_historical_truth": [
        "pending_lifecycle_group_id",
        "pending_intent_persisted_at_decision_time",
        "source_safe_order_observability_state",
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "native_pending_order_type_source_safe",
        "final_lifecycle_state_source_safe",
        "cancel_expiry_reason_status"
      ],
      "negative_evidence": {
        "market_data_catalog_status": "NOT_RECOVERED_IN_ACTIVE_WORKTREE_CATALOG",
        "market_data_tick_match_count": 0,
        "market_data_tick_matches": [],
        "pending_lifecycle_audit_evidence": {
          "action_required_codes": [
            "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP"
          ],
          "final_state": "PENDING_LIFECYCLE_GROUP_MISSING",
          "final_state_status": "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
          "join_backfill_row_count": 0,
          "lifecycle_row_count": 0,
          "manual_backfill_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP",
          "no_leak_status": "POST_DECISION_PENDING_LIFECYCLE_AUDIT_NO_DECISION_FEATURE",
          "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
          "row_key": "trade_record|GBPJPY_2026-04-14T01:15:05.006410+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "pending_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
      "price_tick_bar_backfill_possible": false,
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "why_non_generatable": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "action_required_codes": [
        "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP"
      ],
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "decision_time_utc": "2026-04-14T15:30:05.012815+00:00",
      "existing_source_safe_evidence_found": false,
      "final_state_status": "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
      "forward_capture_fields_required": [
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "capture_latency_ms",
        "capture_clock_source_status",
        "capture_clock_skew_ms",
        "capture_clock_skew_status",
        "pending_order_mode_source_safe",
        "pending_order_mode_status",
        "broker_pending_order_created_status",
        "native_pending_order_type_source_safe",
        "native_pending_order_type_status",
        "pending_intent_created_utc",
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "cancel_expiry_utc",
        "cancel_expiry_reason_status",
        "entry_touch_first_utc",
        "side_aware_entry_touch_status",
        "terminal_area_touch_status",
        "terminal_area_first_touch_utc",
        "protective_area_touch_status",
        "protective_area_first_touch_utc",
        "event_order_resolution_method",
        "same_tick_same_bar_ambiguity_status"
      ],
      "missing_historical_truth": [
        "pending_lifecycle_group_id",
        "pending_intent_persisted_at_decision_time",
        "source_safe_order_observability_state",
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "native_pending_order_type_source_safe",
        "final_lifecycle_state_source_safe",
        "cancel_expiry_reason_status"
      ],
      "negative_evidence": {
        "market_data_catalog_status": "NOT_RECOVERED_IN_ACTIVE_WORKTREE_CATALOG",
        "market_data_tick_match_count": 0,
        "market_data_tick_matches": [],
        "pending_lifecycle_audit_evidence": {
          "action_required_codes": [
            "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP"
          ],
          "final_state": "PENDING_LIFECYCLE_GROUP_MISSING",
          "final_state_status": "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
          "join_backfill_row_count": 0,
          "lifecycle_row_count": 0,
          "manual_backfill_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP",
          "no_leak_status": "POST_DECISION_PENDING_LIFECYCLE_AUDIT_NO_DECISION_FEATURE",
          "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
          "row_key": "trade_record|GBPJPY_2026-04-14T15:30:05.012815+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "pending_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
      "price_tick_bar_backfill_possible": false,
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "why_non_generatable": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "action_required_codes": [
        "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP"
      ],
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "decision_time_utc": "2026-04-15T00:30:05.011237+00:00",
      "existing_source_safe_evidence_found": false,
      "final_state_status": "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
      "forward_capture_fields_required": [
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "capture_latency_ms",
        "capture_clock_source_status",
        "capture_clock_skew_ms",
        "capture_clock_skew_status",
        "pending_order_mode_source_safe",
        "pending_order_mode_status",
        "broker_pending_order_created_status",
        "native_pending_order_type_source_safe",
        "native_pending_order_type_status",
        "pending_intent_created_utc",
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "cancel_expiry_utc",
        "cancel_expiry_reason_status",
        "entry_touch_first_utc",
        "side_aware_entry_touch_status",
        "terminal_area_touch_status",
        "terminal_area_first_touch_utc",
        "protective_area_touch_status",
        "protective_area_first_touch_utc",
        "event_order_resolution_method",
        "same_tick_same_bar_ambiguity_status"
      ],
      "missing_historical_truth": [
        "pending_lifecycle_group_id",
        "pending_intent_persisted_at_decision_time",
        "source_safe_order_observability_state",
        "capture_write_started_at_utc",
        "capture_write_completed_at_utc",
        "native_pending_order_type_source_safe",
        "final_lifecycle_state_source_safe",
        "cancel_expiry_reason_status"
      ],
      "negative_evidence": {
        "market_data_catalog_status": "NOT_RECOVERED_IN_ACTIVE_WORKTREE_CATALOG",
        "market_data_tick_match_count": 0,
        "market_data_tick_matches": [],
        "pending_lifecycle_audit_evidence": {
          "action_required_codes": [
            "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP"
          ],
          "final_state": "PENDING_LIFECYCLE_GROUP_MISSING",
          "final_state_status": "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
          "join_backfill_row_count": 0,
          "lifecycle_row_count": 0,
          "manual_backfill_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP",
          "no_leak_status": "POST_DECISION_PENDING_LIFECYCLE_AUDIT_NO_DECISION_FEATURE",
          "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
          "row_key": "trade_record|GBPJPY_2026-04-15T00:30:05.011237+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "pending_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
      "price_tick_bar_backfill_possible": false,
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "why_non_generatable": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    }
  ],
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "validation_safe": false
}
```
