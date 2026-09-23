# Nofill Source State Gap Closure Active Pursuit Ladder Ledger 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

- row_count: `37`

## Machine Payload

```json
{
  "all_terminal_statuses_allowed": true,
  "allowed_terminal_statuses": [
    "CONTAMINATION_EMBARGO_EXCLUDED",
    "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE",
    "OWNER_EXPORT_REQUIRED",
    "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED",
    "RECOVERED_SOURCE_STATE_EXISTING_LOG",
    "REJECT_FORBIDDEN_EVIDENCE_CLASS",
    "SOURCE_CONTRACT_FIXTURE_ONLY"
  ],
  "artifact_family": "row_level_active_pursuit_ladder_ledger",
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
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "row_count": 37,
  "rows_count": 37,
  "rows_sample": [
    {
      "active_pursuit_ladder": [
        {
          "action": "searched_existing_source_safe_logs_artifacts_and_catalog_roots",
          "evidence": {
            "active_catalog_missing_window_evidence": {
              "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
              "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
              "exact_next_action": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
              "local_catalog_status": "source_state_not_reconstructable_from_catalog_presence",
              "roots_searched": [
                "current_worktree_data_root",
                "current_worktree_tick_root",
                "current_worktree_shadow_logs",
                "current_worktree_exports",
                "current_worktree_external_data",
                "current_worktree_science_routes",
                "absolute_main_data_root",
                "absolute_main_tick_root",
                "absolute_main_shadow_logs",
                "absolute_main_exports",
                "absolute_main_external_data",
                "prior_worktree_root",
                "sierra_chart_root",
                "sierra_chart_data_root",
                "sierra_chart_depth_root",
                "owner_documents_candidate_root"
              ],
              "source_date": "2026-04-14",
              "source_family": "pending_lifecycle_or_order_observability_truth",
              "source_requirement_type": "non_generatable_historical_gtos_source_state",
              "supporting_catalog_row_ids": [],
              "symbol": "GBPJPY",
              "timeframe": "not_applicable",
              "window_id": "MW-SOURCESTATE-0001"
            },
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
            "source_families_searched": [
              "mt5_tick_parquet",
              "pending_lifecycle_or_order_observability_truth",
              "source_control_route_artifacts"
            ]
          },
          "status": "completed",
          "step": 1
        },
        {
          "action": "build_recovered_source_state_manifest_if_truth_found",
          "evidence": "No blocker row has source-safe pending lifecycle group/write-clock/order-observability truth sufficient for recovery.",
          "status": "negative_evidence_ledgered",
          "step": 2
        },
        {
          "action": "pursue_recoverable_market_data_without_forbidden_surfaces",
          "evidence": "Tick dependency is exact and source-control-only; no account/order/history/deal/position values are used.",
          "status": "specified",
          "step": 3
        },
        {
          "action": "create_exact_owner_export_request_when_local_catalog_has_no tick",
          "evidence": {
            "fields": [
              "time_utc",
              "time_msc",
              "bid",
              "ask",
              "last",
              "volume",
              "flags",
              "source_symbol",
              "broker_symbol",
              "source_file_sha256"
            ],
            "required": true,
            "source_date": "2026-04-14",
            "symbol": "GBPJPY",
            "timeframe": "TICK",
            "window_end_utc": "2026-04-14T23:59:59.999999Z",
            "window_start_utc": "2026-04-14T00:00:00Z"
          },
          "status": "exact_request_created",
          "step": 4
        },
        {
          "action": "prove_non_generatable_historical_source_state_and_map_forward_capture_fields",
          "evidence": {
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
          "status": "proven_and_mapped",
          "step": 5
        },
        {
          "action": "handle_contamination_or_embargo",
          "evidence": {
            "admission_reasons": [
              "candidate_registry_l2_final_state_not_joined_status_only",
              "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-14",
              "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
              "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
              "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
            ],
            "clean_denominator_status": "not_contamination_blocked"
          },
          "status": "not_applicable",
          "step": 6
        }
      ],
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "contamination_or_embargo_blocked": false,
      "decision_time_utc": "2026-04-14T01:15:05.006410+00:00",
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0001",
      "source_date": "2026-04-14",
      "source_row_identity_preserved": true,
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED",
      "terminal_status_allowed": true
    },
    {
      "active_pursuit_ladder": [
        {
          "action": "searched_existing_source_safe_logs_artifacts_and_catalog_roots",
          "evidence": {
            "active_catalog_missing_window_evidence": {
              "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
              "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
              "exact_next_action": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
              "local_catalog_status": "source_state_not_reconstructable_from_catalog_presence",
              "roots_searched": [
                "current_worktree_data_root",
                "current_worktree_tick_root",
                "current_worktree_shadow_logs",
                "current_worktree_exports",
                "current_worktree_external_data",
                "current_worktree_science_routes",
                "absolute_main_data_root",
                "absolute_main_tick_root",
                "absolute_main_shadow_logs",
                "absolute_main_exports",
                "absolute_main_external_data",
                "prior_worktree_root",
                "sierra_chart_root",
                "sierra_chart_data_root",
                "sierra_chart_depth_root",
                "owner_documents_candidate_root"
              ],
              "source_date": "2026-04-14",
              "source_family": "pending_lifecycle_or_order_observability_truth",
              "source_requirement_type": "non_generatable_historical_gtos_source_state",
              "supporting_catalog_row_ids": [],
              "symbol": "GBPJPY",
              "timeframe": "not_applicable",
              "window_id": "MW-SOURCESTATE-0002"
            },
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
            "source_families_searched": [
              "mt5_tick_parquet",
              "pending_lifecycle_or_order_observability_truth",
              "source_control_route_artifacts"
            ]
          },
          "status": "completed",
          "step": 1
        },
        {
          "action": "build_recovered_source_state_manifest_if_truth_found",
          "evidence": "No blocker row has source-safe pending lifecycle group/write-clock/order-observability truth sufficient for recovery.",
          "status": "negative_evidence_ledgered",
          "step": 2
        },
        {
          "action": "pursue_recoverable_market_data_without_forbidden_surfaces",
          "evidence": "Tick dependency is exact and source-control-only; no account/order/history/deal/position values are used.",
          "status": "specified",
          "step": 3
        },
        {
          "action": "create_exact_owner_export_request_when_local_catalog_has_no tick",
          "evidence": {
            "fields": [
              "time_utc",
              "time_msc",
              "bid",
              "ask",
              "last",
              "volume",
              "flags",
              "source_symbol",
              "broker_symbol",
              "source_file_sha256"
            ],
            "required": true,
            "source_date": "2026-04-14",
            "symbol": "GBPJPY",
            "timeframe": "TICK",
            "window_end_utc": "2026-04-14T23:59:59.999999Z",
            "window_start_utc": "2026-04-14T00:00:00Z"
          },
          "status": "exact_request_created",
          "step": 4
        },
        {
          "action": "prove_non_generatable_historical_source_state_and_map_forward_capture_fields",
          "evidence": {
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
          "status": "proven_and_mapped",
          "step": 5
        },
        {
          "action": "handle_contamination_or_embargo",
          "evidence": {
            "admission_reasons": [
              "candidate_registry_l2_final_state_not_joined_status_only",
              "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-14",
              "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
              "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
              "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
            ],
            "clean_denominator_status": "not_contamination_blocked"
          },
          "status": "not_applicable",
          "step": 6
        }
      ],
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "contamination_or_embargo_blocked": false,
      "decision_time_utc": "2026-04-14T15:30:05.012815+00:00",
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0002",
      "source_date": "2026-04-14",
      "source_row_identity_preserved": true,
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED",
      "terminal_status_allowed": true
    },
    {
      "active_pursuit_ladder": [
        {
          "action": "searched_existing_source_safe_logs_artifacts_and_catalog_roots",
          "evidence": {
            "active_catalog_missing_window_evidence": {
              "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
              "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
              "exact_next_action": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
              "local_catalog_status": "source_state_not_reconstructable_from_catalog_presence",
              "roots_searched": [
                "current_worktree_data_root",
                "current_worktree_tick_root",
                "current_worktree_shadow_logs",
                "current_worktree_exports",
                "current_worktree_external_data",
                "current_worktree_science_routes",
                "absolute_main_data_root",
                "absolute_main_tick_root",
                "absolute_main_shadow_logs",
                "absolute_main_exports",
                "absolute_main_external_data",
                "prior_worktree_root",
                "sierra_chart_root",
                "sierra_chart_data_root",
                "sierra_chart_depth_root",
                "owner_documents_candidate_root"
              ],
              "source_date": "2026-04-15",
              "source_family": "pending_lifecycle_or_order_observability_truth",
              "source_requirement_type": "non_generatable_historical_gtos_source_state",
              "supporting_catalog_row_ids": [],
              "symbol": "GBPJPY",
              "timeframe": "not_applicable",
              "window_id": "MW-SOURCESTATE-0003"
            },
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
            "source_families_searched": [
              "mt5_tick_parquet",
              "pending_lifecycle_or_order_observability_truth",
              "source_control_route_artifacts"
            ]
          },
          "status": "completed",
          "step": 1
        },
        {
          "action": "build_recovered_source_state_manifest_if_truth_found",
          "evidence": "No blocker row has source-safe pending lifecycle group/write-clock/order-observability truth sufficient for recovery.",
          "status": "negative_evidence_ledgered",
          "step": 2
        },
        {
          "action": "pursue_recoverable_market_data_without_forbidden_surfaces",
          "evidence": "Tick dependency is exact and source-control-only; no account/order/history/deal/position values are used.",
          "status": "specified",
          "step": 3
        },
        {
          "action": "create_exact_owner_export_request_when_local_catalog_has_no tick",
          "evidence": {
            "fields": [
              "time_utc",
              "time_msc",
              "bid",
              "ask",
              "last",
              "volume",
              "flags",
              "source_symbol",
              "broker_symbol",
              "source_file_sha256"
            ],
            "required": true,
            "source_date": "2026-04-15",
            "symbol": "GBPJPY",
            "timeframe": "TICK",
            "window_end_utc": "2026-04-15T23:59:59.999999Z",
            "window_start_utc": "2026-04-15T00:00:00Z"
          },
          "status": "exact_request_created",
          "step": 4
        },
        {
          "action": "prove_non_generatable_historical_source_state_and_map_forward_capture_fields",
          "evidence": {
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
          },
          "status": "proven_and_mapped",
          "step": 5
        },
        {
          "action": "handle_contamination_or_embargo",
          "evidence": {
            "admission_reasons": [
              "candidate_registry_l2_final_state_not_joined_status_only",
              "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-15",
              "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
              "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
              "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
            ],
            "clean_denominator_status": "not_contamination_blocked"
          },
          "status": "not_applicable",
          "step": 6
        }
      ],
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "contamination_or_embargo_blocked": false,
      "decision_time_utc": "2026-04-15T00:30:05.011237+00:00",
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0003",
      "source_date": "2026-04-15",
      "source_row_identity_preserved": true,
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED",
      "terminal_status_allowed": true
    }
  ],
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "terminal_status_counts": {
    "CONTAMINATION_EMBARGO_EXCLUDED": 17,
    "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE": 1,
    "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED": 19
  },
  "validation_safe": false
}
```
