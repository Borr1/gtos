# Forbidden Field Key-Shape Exclusion Ledger

- **route_id:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION`
- **evidence_class:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "forbidden_field_key_shape_exclusion_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY",
  "forbidden_file_exclusion_count": 11,
  "forbidden_file_exclusions": [
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/account_pnl_truth_reconciliation.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/account_truth_reconciliation_status.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/broker_actual_r_audit.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/daily_pnl_history.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/equity_read_anomalies.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/j46_j49_shadow_outcomes.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/regime_decay_outcome_join.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/slippage.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "shadow_log_forbidden_broker_account_result_performance_family_excluded",
      "path": "shadow_logs/trade_index_lifecycle_audit.jsonl",
      "root_label": "shadow_logs_shape_only_non_forbidden_families"
    },
    {
      "exclusion_reason": "validation_result_or_neutral_target_route_excluded",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.json",
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY"
    }
  ],
  "forbidden_key_category_counts": {
    "broker_account_order_deal_position": 5032,
    "credential_or_api": 1916,
    "post_outcome_or_validation": 11697,
    "result_performance_outcome": 8772
  },
  "forbidden_key_examples": [
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G10_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G10_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G10_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "validation_safe",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "validation_safe_blockers",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "validation_safe_blockers[]",
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].validation_safe",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].validation_safe_blockers",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].validation_safe_blockers[]",
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "broker_account_order_deal_position"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "forbidden_surface_check.mt5_changed",
      "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "tests_run[].result",
      "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "validation_safe",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "validation_safe_blockers",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "validation_safe_blockers[]",
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G5_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G5_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G5_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G7_MACRO_CROSS_ASSET_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G7_MACRO_CROSS_ASSET_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G7_MACRO_CROSS_ASSET_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "sources[].promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "sources[].validation_safe",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "sources[].validation_safe_blockers",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "sources[].validation_safe_blockers[]",
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_GOAL_STATUS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].promotion_verdict",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].validation_safe",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].validation_safe_blockers",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "rows[].validation_safe_blockers[]",
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "cd2_reconciliation.accepted_master_prereg_rows[].promotion_verdict",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "cd2_reconciliation.blocked_cd2_master_actions[].promotion_verdict",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "broker_account_order_deal_position"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "cd2_reconciliation.mt5_calls",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "cd2_reconciliation.promotion_verdict",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "cd2_reconciliation.source_policy.validation_safe_true_allowed",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "cd2_reconciliation.source_policy.validation_safe_true_rows_after_reconciliation",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "files_written[]",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "broker_account_order_deal_position"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "forbidden_surface_check.mt5_changed",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "tests_run[].result",
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "goal_status_rows[].files_written",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "goal_status_rows[].files_written[]",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "goal_status_rows[].promotion_verdict",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "broker_account_order_deal_position"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "mt5_calls",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "orchestration_plan.promotion_boundary",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "promotion_verdict",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "registries.experiment_preregistry.promotion_verdict",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "registries.hypothesis_registry.promotion_verdict",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "registries.mechanism_registry.promotion_verdict",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "result_performance_outcome"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.experiment_prereg_v1.field_notes.outcome_review_opened",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.experiment_prereg_v1.promotion_boundary",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.goal_status_v1.field_notes.promotion_verdict",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.goal_status_v1.promotion_boundary",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.science_hypothesis_v1.field_notes.promotion_blockers",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.science_hypothesis_v1.promotion_boundary",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.science_mechanism_v1.promotion_boundary",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    },
    {
      "categories": [
        "post_outcome_or_validation"
      ],
      "disposition": "EXCLUDED_FROM_SOURCE_CONTROL_ROW_SHAPE_MATCH",
      "key_path": "schema_contracts.source_contract_v2.field_notes.validation_safe",
      "path": "research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.json",
      "root_label": "current_program_control_json_artifacts"
    }
  ],
  "generated_at_utc": "2026-05-12T05:26:39Z",
  "leak_policy": "Forbidden key shapes were recorded only as key names/categories and excluded from source/control coverage; no raw values were copied.",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result": "PASS_FORBIDDEN_KEY_SHAPES_EXCLUDED_FROM_COVERAGE",
  "route_id": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
  "schema_version": "scid_forward_capture_readonly_alignment_expansion_v1",
  "validation_safe": false
}
```
