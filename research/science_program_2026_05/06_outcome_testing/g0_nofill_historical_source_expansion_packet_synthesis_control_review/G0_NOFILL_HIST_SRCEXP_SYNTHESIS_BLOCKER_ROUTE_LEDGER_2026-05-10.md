# G0 NOFILL Historical Source Expansion 37 Blocker Route Ledger

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Summary

All 37 blockers have exact route classes, catalog evidence, and next actions.

## Machine Payload

```json
{
  "action_class_counts": {
    "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO": 17,
    "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT": 6,
    "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED": 37,
    "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT": 31
  },
  "artifact_family": "thirty_seven_blocker_route_ledger",
  "blocked_row_count": 37,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T07:53:15Z",
  "generic_blocker_terms_absent": true,
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
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "catalog_search_evidence": {
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
      "decision_time_utc": "2026-04-14T01:15:05.006410+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-14; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-14T01:15:05.006410+00:00",
        "market_data_window": "2026-04-14T00:00:00Z/2026-04-14T23:59:59Z",
        "source_date": "2026-04-14"
      },
      "source_date": "2026-04-14",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "catalog_search_evidence": {
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
      "decision_time_utc": "2026-04-14T15:30:05.012815+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-14; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-14T15:30:05.012815+00:00",
        "market_data_window": "2026-04-14T00:00:00Z/2026-04-14T23:59:59Z",
        "source_date": "2026-04-14"
      },
      "source_date": "2026-04-14",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "catalog_search_evidence": {
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
      "decision_time_utc": "2026-04-15T00:30:05.011237+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T00:30:05.011237+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPJPY_2026-04-15T13:15:57.164919+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-15T13:15:57.164919+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T13:15:57.164919+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPJPY_2026-04-16T00:16:00.503237+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-16T00:16:00.503237+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-16; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-16T00:16:00.503237+00:00",
        "market_data_window": "2026-04-16T00:00:00Z/2026-04-16T23:59:59Z",
        "source_date": "2026-04-16"
      },
      "source_date": "2026-04-16",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPJPY_2026-04-22T08:00:05.028587+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-22T08:00:05.028587+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-22; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-22T08:00:05.028587+00:00",
        "market_data_window": "2026-04-22T00:00:00Z/2026-04-22T23:59:59Z",
        "source_date": "2026-04-22"
      },
      "source_date": "2026-04-22",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-23",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPJPY_2026-04-23T07:16:14.138817+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-23T07:16:14.138817+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPJPY 2026-04-23; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-23T07:16:14.138817+00:00",
        "market_data_window": "2026-04-23T00:00:00Z/2026-04-23T23:59:59Z",
        "source_date": "2026-04-23"
      },
      "source_date": "2026-04-23",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPJPY_2026-04-28T09:00:05.010558+00:00",
      "catalog_search_evidence": {
        "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE",
        "market_data_tick_match_count": 1,
        "market_data_tick_matches": [
          {
            "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
            "catalog_row_id": "LCAT-000636",
            "hash_status": "sha256_complete",
            "repo_relative_path": "outside_current_worktree",
            "root_id": "absolute_main_tick_root",
            "sha256": "5d88d8dd5522cc2811ee0be7e40a9506cb447ffb216ba895f8007d4078840e03",
            "size_bytes": 3882626,
            "source_family": "mt5_tick_parquet"
          }
        ],
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
          "row_key": "trade_record|GBPJPY_2026-04-28T09:00:05.010558+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-28T09:00:05.010558+00:00",
      "exact_next_action": "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-28T09:00:05.010558+00:00",
        "market_data_window": "2026-04-28T00:00:00Z/2026-04-28T23:59:59Z",
        "source_date": "2026-04-28"
      },
      "source_date": "2026-04-28",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY",
      "terminal_route_class": "SOURCE_STATE_NON_GENERATABLE_ONLY",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-14T07:30:05.011677+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-14T07:30:05.011677+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-14; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-14T07:30:05.011677+00:00",
        "market_data_window": "2026-04-14T00:00:00Z/2026-04-14T23:59:59Z",
        "source_date": "2026-04-14"
      },
      "source_date": "2026-04-14",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-14T14:00:57.743957+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-14T14:00:57.743957+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-14; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-14T14:00:57.743957+00:00",
        "market_data_window": "2026-04-14T00:00:00Z/2026-04-14T23:59:59Z",
        "source_date": "2026-04-14"
      },
      "source_date": "2026-04-14",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-15T07:30:05.010905+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-15T07:30:05.010905+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T07:30:05.010905+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-15T13:16:01.327115+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-15T13:16:01.327115+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T13:16:01.327115+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-17",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-17T08:00:59.541491+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-17T08:00:59.541491+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-17; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-17T08:00:59.541491+00:00",
        "market_data_window": "2026-04-17T00:00:00Z/2026-04-17T23:59:59Z",
        "source_date": "2026-04-17"
      },
      "source_date": "2026-04-17",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-17",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-17T14:15:05.012317+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-17T14:15:05.012317+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-17; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-17T14:15:05.012317+00:00",
        "market_data_window": "2026-04-17T00:00:00Z/2026-04-17T23:59:59Z",
        "source_date": "2026-04-17"
      },
      "source_date": "2026-04-17",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-20",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-20",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-20",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-20T07:45:05.020140+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-20T07:45:05.020140+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-20; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-20T07:45:05.020140+00:00",
        "market_data_window": "2026-04-20T00:00:00Z/2026-04-20T23:59:59Z",
        "source_date": "2026-04-20"
      },
      "source_date": "2026-04-20",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-20",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-20",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-20",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-20T15:31:14.730975+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-20T15:31:14.730975+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-20; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-20T15:31:14.730975+00:00",
        "market_data_window": "2026-04-20T00:00:00Z/2026-04-20T23:59:59Z",
        "source_date": "2026-04-20"
      },
      "source_date": "2026-04-20",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-20",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-21",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-21T11:30:05.011826+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-21T11:30:05.011826+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-21; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-21T11:30:05.011826+00:00",
        "market_data_window": "2026-04-21T00:00:00Z/2026-04-21T23:59:59Z",
        "source_date": "2026-04-21"
      },
      "source_date": "2026-04-21",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|GBPUSD_2026-04-22T07:16:12.155934+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-22T07:16:12.155934+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for GBPUSD 2026-04-22; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "GBPUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-22T07:16:12.155934+00:00",
        "market_data_window": "2026-04-22T00:00:00Z/2026-04-22T23:59:59Z",
        "source_date": "2026-04-22"
      },
      "source_date": "2026-04-22",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-30",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "NAS100_2026-04-29T15:00:05.012307+00:00",
      "catalog_search_evidence": {
        "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE",
        "market_data_tick_match_count": 1,
        "market_data_tick_matches": [
          {
            "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-04-29.parquet",
            "catalog_row_id": "LCAT-000660",
            "hash_status": "deferred_large_file_requires_dedicated_hash_manifest",
            "repo_relative_path": "outside_current_worktree",
            "root_id": "absolute_main_tick_root",
            "sha256": null,
            "size_bytes": 14176528,
            "source_family": "mt5_tick_parquet"
          }
        ],
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
          "row_key": "trade_record|NAS100_2026-04-29T15:00:05.012307+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-29T15:00:05.012307+00:00",
      "exact_next_action": "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "NAS100"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-29T15:00:05.012307+00:00",
        "market_data_window": "2026-04-29T00:00:00Z/2026-04-29T23:59:59Z",
        "source_date": "2026-04-29"
      },
      "source_date": "2026-04-29",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "NAS100",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-05-01",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-30",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "NAS100_2026-05-01T08:15:00+00:00",
      "catalog_search_evidence": {
        "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE",
        "market_data_tick_match_count": 1,
        "market_data_tick_matches": [
          {
            "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-01.parquet",
            "catalog_row_id": "LCAT-000662",
            "hash_status": "deferred_large_file_requires_dedicated_hash_manifest",
            "repo_relative_path": "outside_current_worktree",
            "root_id": "absolute_main_tick_root",
            "sha256": null,
            "size_bytes": 11914727,
            "source_family": "mt5_tick_parquet"
          }
        ],
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
          "row_key": "trade_record|NAS100_2026-05-01T08:15:00+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-05-01T08:15:00+00:00",
      "exact_next_action": "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "NAS100"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-05-01T08:15:00+00:00",
        "market_data_window": "2026-05-01T00:00:00Z/2026-05-01T23:59:59Z",
        "source_date": "2026-05-01"
      },
      "source_date": "2026-05-01",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "NAS100",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=US30_cash/2026-04-14",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|US30_cash_2026-04-14T08:16:00.983581+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-14T08:16:00.983581+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for US30_cash 2026-04-14; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "US30_cash"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-14T08:16:00.983581+00:00",
        "market_data_window": "2026-04-14T00:00:00Z/2026-04-14T23:59:59Z",
        "source_date": "2026-04-14"
      },
      "source_date": "2026-04-14",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "US30_cash",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=US30_cash/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|US30_cash_2026-04-16T13:45:56.810509+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-16T13:45:56.810509+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for US30_cash 2026-04-16; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "US30_cash"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-16T13:45:56.810509+00:00",
        "market_data_window": "2026-04-16T00:00:00Z/2026-04-16T23:59:59Z",
        "source_date": "2026-04-16"
      },
      "source_date": "2026-04-16",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "US30_cash",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-15T02:45:05.009485+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-15T02:45:05.009485+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T02:45:05.009485+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-15T13:15:57.398922+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-15T13:15:57.398922+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T13:15:57.398922+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-16T15:00:05.011292+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-16T15:00:05.011292+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-16; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-16T15:00:05.011292+00:00",
        "market_data_window": "2026-04-16T00:00:00Z/2026-04-16T23:59:59Z",
        "source_date": "2026-04-16"
      },
      "source_date": "2026-04-16",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-20",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-21",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-21T13:45:05.018194+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-21T13:45:05.018194+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-21; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-21T13:45:05.018194+00:00",
        "market_data_window": "2026-04-21T00:00:00Z/2026-04-21T23:59:59Z",
        "source_date": "2026-04-21"
      },
      "source_date": "2026-04-21",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-22T00:30:05.018068+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-22T00:30:05.018068+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-22; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-22T00:30:05.018068+00:00",
        "market_data_window": "2026-04-22T00:00:00Z/2026-04-22T23:59:59Z",
        "source_date": "2026-04-22"
      },
      "source_date": "2026-04-22",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-22",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-22T15:15:05.016051+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-22T15:15:05.016051+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-22; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-22T15:15:05.016051+00:00",
        "market_data_window": "2026-04-22T00:00:00Z/2026-04-22T23:59:59Z",
        "source_date": "2026-04-22"
      },
      "source_date": "2026-04-22",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-23",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-23T08:45:05.012266+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-23T08:45:05.012266+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-23; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-23T08:45:05.012266+00:00",
        "market_data_window": "2026-04-23T00:00:00Z/2026-04-23T23:59:59Z",
        "source_date": "2026-04-23"
      },
      "source_date": "2026-04-23",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=USDJPY/2026-04-24",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|USDJPY_2026-04-24T00:16:10.771453+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-24T00:16:10.771453+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for USDJPY 2026-04-24; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "USDJPY"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-24T00:16:10.771453+00:00",
        "market_data_window": "2026-04-24T00:00:00Z/2026-04-24T23:59:59Z",
        "source_date": "2026-04-24"
      },
      "source_date": "2026-04-24",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-05-01",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-30",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAGUSD_2026-05-01T08:30:00+00:00",
      "catalog_search_evidence": {
        "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE",
        "market_data_tick_match_count": 1,
        "market_data_tick_matches": [
          {
            "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-01.parquet",
            "catalog_row_id": "LCAT-000696",
            "hash_status": "sha256_complete",
            "repo_relative_path": "outside_current_worktree",
            "root_id": "absolute_main_tick_root",
            "sha256": "e980bdafeaa5b8a6e8baad0efaf3b812a4966e0b7b225135f2e50b5bef67b31d",
            "size_bytes": 2847558,
            "source_family": "mt5_tick_parquet"
          }
        ],
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
          "row_key": "trade_record|XAGUSD_2026-05-01T08:30:00+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-05-01T08:30:00+00:00",
      "exact_next_action": "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAGUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-05-01T08:30:00+00:00",
        "market_data_window": "2026-05-01T00:00:00Z/2026-05-01T23:59:59Z",
        "source_date": "2026-05-01"
      },
      "source_date": "2026-05-01",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAGUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-15",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|XAUUSD_2026-04-15T14:15:05.007998+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-15T14:15:05.007998+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for XAUUSD 2026-04-15; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAUUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-15T14:15:05.007998+00:00",
        "market_data_window": "2026-04-15T00:00:00Z/2026-04-15T23:59:59Z",
        "source_date": "2026-04-15"
      },
      "source_date": "2026-04-15",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD",
      "terminal_route_class": "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|XAUUSD_2026-04-16T09:30:05.013547+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-16T09:30:05.013547+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for XAUUSD 2026-04-16; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAUUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-16T09:30:05.013547+00:00",
        "market_data_window": "2026-04-16T00:00:00Z/2026-04-16T23:59:59Z",
        "source_date": "2026-04-16"
      },
      "source_date": "2026-04-16",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|XAUUSD_2026-04-16T13:16:01.126537+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-16T13:16:01.126537+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for XAUUSD 2026-04-16; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAUUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-16T13:16:01.126537+00:00",
        "market_data_window": "2026-04-16T00:00:00Z/2026-04-16T23:59:59Z",
        "source_date": "2026-04-16"
      },
      "source_date": "2026-04-16",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-17",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=XAUUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
      "catalog_search_evidence": {
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
          "row_key": "trade_record|XAUUSD_2026-04-17T13:30:05.007149+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-04-17T13:30:05.007149+00:00",
      "exact_next_action": "Create an approved read-only tick export/extraction or owner-export request for XAUUSD 2026-04-17; hash the parquet before any packet rebuild. Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAUUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-04-17T13:30:05.007149+00:00",
        "market_data_window": "2026-04-17T00:00:00Z/2026-04-17T23:59:59Z",
        "source_date": "2026-04-17"
      },
      "source_date": "2026-04-17",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-05-01",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-30",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAUUSD_2026-05-01T08:15:00+00:00",
      "catalog_search_evidence": {
        "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE",
        "market_data_tick_match_count": 1,
        "market_data_tick_matches": [
          {
            "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-01.parquet",
            "catalog_row_id": "LCAT-000707",
            "hash_status": "sha256_complete",
            "repo_relative_path": "outside_current_worktree",
            "root_id": "absolute_main_tick_root",
            "sha256": "ed0773d4ded22a853c0aa40d6ee5503d37fb27f95c5958977ef129c82a837ae0",
            "size_bytes": 7322672,
            "source_family": "mt5_tick_parquet"
          }
        ],
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
          "row_key": "trade_record|XAUUSD_2026-05-01T08:15:00+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-05-01T08:15:00+00:00",
      "exact_next_action": "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAUUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-05-01T08:15:00+00:00",
        "market_data_window": "2026-05-01T00:00:00Z/2026-05-01T23:59:59Z",
        "source_date": "2026-05-01"
      },
      "source_date": "2026-05-01",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    },
    {
      "action_classes": [
        "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT",
        "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED",
        "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO"
      ],
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-05-01",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-30",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
      "can_enter_clean_source_packet_now": false,
      "candidate_id": "XAUUSD_2026-05-01T15:45:00+00:00",
      "catalog_search_evidence": {
        "market_data_catalog_status": "RECOVERED_LOCAL_SOURCE",
        "market_data_tick_match_count": 1,
        "market_data_tick_matches": [
          {
            "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-01.parquet",
            "catalog_row_id": "LCAT-000707",
            "hash_status": "sha256_complete",
            "repo_relative_path": "outside_current_worktree",
            "root_id": "absolute_main_tick_root",
            "sha256": "ed0773d4ded22a853c0aa40d6ee5503d37fb27f95c5958977ef129c82a837ae0",
            "size_bytes": 7322672,
            "source_family": "mt5_tick_parquet"
          }
        ],
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
          "row_key": "trade_record|XAUUSD_2026-05-01T15:45:00+00:00|pending_limit_lifecycle_audit_v1",
          "schema_version": "pending_limit_lifecycle_audit_v1",
          "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        },
        "pending_lifecycle_audit_row_found": true,
        "source_state_catalog_applicability": "NOT_APPLICABLE_TO_NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE",
        "source_state_catalog_reason": "Catalog file presence can locate logs, but cannot create the missing pending lifecycle group, write-clock, persisted intent, or order-observability truth after the fact."
      },
      "decision_time_utc": "2026-05-01T15:45:00+00:00",
      "exact_next_action": "Do not infer lifecycle truth from price. Search only existing source-safe pending lifecycle group, persisted intent, write-clock, and order-observability logs; current audit evidence reduces the row to forward capture requirements. Keep excluded from clean denominators unless a separate future G12 source-control audit proves independent source generation and embargo separation.",
      "roots_consulted": [
        "absolute_main_data_root",
        "absolute_main_exports",
        "absolute_main_external_data",
        "absolute_main_shadow_logs",
        "absolute_main_tick_root",
        "current_worktree_data_root",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "current_worktree_shadow_logs",
        "current_worktree_tick_root",
        "owner_documents_candidate_root",
        "prior_worktree_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "sierra_chart_root"
      ],
      "searched_symbols": [
        "XAUUSD"
      ],
      "searched_time_window": {
        "decision_time_utc": "2026-05-01T15:45:00+00:00",
        "market_data_window": "2026-05-01T00:00:00Z/2026-05-01T23:59:59Z",
        "source_date": "2026-05-01"
      },
      "source_date": "2026-05-01",
      "source_families_searched": [
        "mt5_tick_parquet",
        "pending_lifecycle_or_order_observability_truth",
        "source_control_route_artifacts"
      ],
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD",
      "terminal_route_class": "SOURCE_STATE_AND_CONTAMINATION_BLOCKED",
      "validation_safe": false
    }
  ],
  "schema_version": "g0_nofill_historical_source_expansion_packet_synthesis_control_review_v1",
  "source_dates": [
    "2026-04-14",
    "2026-04-15",
    "2026-04-16",
    "2026-04-17",
    "2026-04-20",
    "2026-04-21",
    "2026-04-22",
    "2026-04-23",
    "2026-04-24",
    "2026-04-28",
    "2026-04-29",
    "2026-05-01"
  ],
  "summary": "All 37 blockers have exact route classes, catalog evidence, and next actions.",
  "symbols": [
    "GBPJPY",
    "GBPUSD",
    "NAS100",
    "US30_cash",
    "USDJPY",
    "XAGUSD",
    "XAUUSD"
  ],
  "terminal_route_class_counts": {
    "MARKET_DATA_RECOVERABLE_BUT_SOURCE_STATE_NON_GENERATABLE": 19,
    "SOURCE_STATE_AND_CONTAMINATION_BLOCKED": 17,
    "SOURCE_STATE_NON_GENERATABLE_ONLY": 1
  },
  "validation_safe": false
}
```
