# No Leak Forbidden Surface Safe Flag Audit

```json
{
  "artifact_family": "no_leak_forbidden_surface_safe_flag_audit",
  "benign_forbidden_reference_count": 289,
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY",
  "failures": [],
  "forbidden_surface_summary": {
    "no_ai_api": true,
    "no_broker_account_order_history_deal_position_evidence": true,
    "no_live_restart": true,
    "no_paid_vendor": true,
    "no_promotion": true,
    "no_prompt_config_risk_safety_execution_canary_selector_live_behavior_change": true,
    "no_r_pnl_win_rate_expectancy_performance_claim": true,
    "no_raw_market_blob_commit": true,
    "no_registry_edit": true,
    "no_remote_push": true,
    "no_validation_or_result_scoring": true
  },
  "generated_at_utc": "2026-05-12T13:39:28Z",
  "live_effect": false,
  "ok": true,
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
  "payload_safe_flag_rows": [
    {
      "input": "completion_audit",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "verification_result",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "output_manifest",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "source_field_mapping_matrix",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "per_card_terminal_status_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "replay_input_packet_design_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "blocked_card_dependency_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "same_evidence_class_blocker_pursuit_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "partition_forward_capture_dependency_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "expansion_candidate_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "negative_evidence_anti_boxing_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "saturation_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    },
    {
      "input": "saturation_self_redteam_anti_ceiling_ledger",
      "row_failures": [],
      "safe_flags_ok": true
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT",
  "schema_version": "g12_scid_noapi_40card_prereg_replay_input_design_audit_v1",
  "scoped_git_status": {
    "entries": [
      {
        "path": ".context/LIVE_STATE.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "knowledge_base/index/trade_record_inventory_index_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "knowledge_base/monitoring/edge_monitor_state.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "pipeline_state/live_monitoring_maintenance_state.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "pipeline_state/shadow_observer_state.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "pipeline_state/sierra_depth_enrichment_checkpoint.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_VERIFICATION_RESULT_2026-05-11.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/account_pnl_truth_reconciliation.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/account_truth_reconciliation_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/broker_actual_r_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_features_log.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_ltf_path_order.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_path_contract_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_path_follow.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_registry_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/context_control_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/context_control_ledger.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/cusum_candidate_rate_daily.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/d1_bias_lag.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/daily_pnl.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/daily_pnl_history.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/databento_live_trigger_decisions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/decision_layer_diagnostics_join.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/direction_emission_xau_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/displacement_events.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/dumb_baseline_hypotheticals.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/es_mes_preregistration_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/exit_management_shadow_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/external_source_blocker_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/fvg_ob_confluence.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/fvg_ob_confluence_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/fvg_ob_confluence_resolutions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/gbpjpy_proxy_gap_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/heartbeat_flatten_events.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/j46_j49_exit_comparator_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/j46_j49_shadow_outcomes.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/liquidity_distance_log.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_candidate_opportunity_clusters.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_candidate_strategy_rollups.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_monitor.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_monitor_alerts.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_monitoring_maintenance_runs.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_structural_strategy_metadata.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/mechanical_context_diagnostics_join.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/missed_opportunity_shadow.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/ml_shadow_predictions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/ml_shadow_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/nas100_orderflow_adverse_selection_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/notification_queue_dead_zone_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/ob_continuation_daily.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/opportunity_lifecycle_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/orderflow_primitives_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/pending_limit_lifecycle.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/prefill_delivery_path.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/prefill_delivery_path_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/prefill_delivery_path_resolutions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/proximity_shadow_log.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/proxy_blocker_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/regime_classifications.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/regime_decay_outcome_join.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/s79_side_aware_risk_context.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/session_volatility_log.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/session_volatility_sweep_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/shadow_observer_hardening_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/shadow_observer_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_confluence_source_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_depth_enrichment_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_proxy_registry_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sl_beyond_ob_decisions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/slippage.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/storage_retention_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/strategy_follow_candidates.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/strategy_follow_evaluations.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/structure_detector_divergences.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/structure_detector_divergences_2026-04-26.jsonl.gz",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " D"
      },
      {
        "path": "shadow_logs/structure_detector_divergences_2026-04-27.jsonl.gz",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " D"
      },
      {
        "path": "shadow_logs/sweep_divergence_log.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/touch_count_gate_decisions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/trade_index_lifecycle_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2_structural_selector_readiness.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2b_forward_pair_resolution_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2b_forward_pair_resolutions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2b_forward_pairs.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/xauusd_same_market_extension_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "data/account_history/mt5_deals_2026-04-27_2026-05-11.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/archive/",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/live_intelligence/",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LIVE_MECHANICAL_STRATEGY_SHADOW_OUTCOMES_DEDUP_MANIFEST_20260512_003422.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LIVE_MECHANICAL_STRATEGY_SHADOW_OUTCOMES_PRE_DEDUP_20260512_003422.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LTO019_DERIVED_LOG_REPAIR_20260512_073108.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LTO019_decision_layer_diagnostics_join_pre_repair_20260512_073108.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/ML_SHADOW_PREDICTIONS_POINTER_HEADER_PRE_REPAIR_20260512_073616.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/ML_SHADOW_PREDICTIONS_POINTER_HEADER_REPAIR_20260512_073616.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/nofill_forward_source_capture.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/operator_market_intelligence.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/source_diagnostic_intelligence.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/time_in_trade.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      }
    ],
    "no_scoped_forbidden_live_surface": true,
    "no_scoped_raw_market_blob": true,
    "returncode": 0,
    "scoped_entries": [
      {
        "path": ".context/LIVE_STATE.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      }
    ],
    "stderr": [
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied"
    ],
    "unscoped_entries": [
      {
        "path": "knowledge_base/index/trade_record_inventory_index_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "knowledge_base/monitoring/edge_monitor_state.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "pipeline_state/live_monitoring_maintenance_state.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "pipeline_state/shadow_observer_state.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "pipeline_state/sierra_depth_enrichment_checkpoint.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_VERIFICATION_RESULT_2026-05-11.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/account_pnl_truth_reconciliation.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/account_truth_reconciliation_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/broker_actual_r_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_features_log.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_ltf_path_order.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_path_contract_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_path_follow.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/candidate_registry_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/context_control_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/context_control_ledger.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/cusum_candidate_rate_daily.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/d1_bias_lag.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/daily_pnl.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/daily_pnl_history.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/databento_live_trigger_decisions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/decision_layer_diagnostics_join.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/direction_emission_xau_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/displacement_events.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/dumb_baseline_hypotheticals.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/es_mes_preregistration_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/exit_management_shadow_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/external_source_blocker_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/fvg_ob_confluence.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/fvg_ob_confluence_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/fvg_ob_confluence_resolutions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/gbpjpy_proxy_gap_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/heartbeat_flatten_events.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/j46_j49_exit_comparator_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/j46_j49_shadow_outcomes.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/liquidity_distance_log.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_candidate_opportunity_clusters.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_candidate_strategy_rollups.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_monitor.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_monitor_alerts.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_monitoring_maintenance_runs.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/live_structural_strategy_metadata.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/mechanical_context_diagnostics_join.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/missed_opportunity_shadow.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/ml_shadow_predictions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/ml_shadow_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/nas100_orderflow_adverse_selection_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/notification_queue_dead_zone_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/ob_continuation_daily.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/opportunity_lifecycle_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/orderflow_primitives_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/pending_limit_lifecycle.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/prefill_delivery_path.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/prefill_delivery_path_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/prefill_delivery_path_resolutions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/proximity_shadow_log.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/proxy_blocker_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/regime_classifications.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/regime_decay_outcome_join.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/s79_side_aware_risk_context.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/session_volatility_log.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/session_volatility_sweep_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/shadow_observer_hardening_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/shadow_observer_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_confluence_source_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_depth_enrichment_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sierra_proxy_registry_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/sl_beyond_ob_decisions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/slippage.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/storage_retention_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/strategy_follow_candidates.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/strategy_follow_evaluations.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/structure_detector_divergences.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/structure_detector_divergences_2026-04-26.jsonl.gz",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " D"
      },
      {
        "path": "shadow_logs/structure_detector_divergences_2026-04-27.jsonl.gz",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " D"
      },
      {
        "path": "shadow_logs/sweep_divergence_log.csv",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/touch_count_gate_decisions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/trade_index_lifecycle_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2_structural_selector_readiness.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2b_forward_pair_resolution_audit.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2b_forward_pair_resolutions.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/v2b_forward_pairs.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "shadow_logs/xauusd_same_market_extension_status.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "data/account_history/mt5_deals_2026-04-27_2026-05-11.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/archive/",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/live_intelligence/",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LIVE_MECHANICAL_STRATEGY_SHADOW_OUTCOMES_DEDUP_MANIFEST_20260512_003422.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LIVE_MECHANICAL_STRATEGY_SHADOW_OUTCOMES_PRE_DEDUP_20260512_003422.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LTO019_DERIVED_LOG_REPAIR_20260512_073108.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/LTO019_decision_layer_diagnostics_join_pre_repair_20260512_073108.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/ML_SHADOW_PREDICTIONS_POINTER_HEADER_PRE_REPAIR_20260512_073616.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/ML_SHADOW_PREDICTIONS_POINTER_HEADER_REPAIR_20260512_073616.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/nofill_forward_source_capture.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/operator_market_intelligence.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/source_diagnostic_intelligence.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "shadow_logs/time_in_trade.jsonl",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      }
    ],
    "unscoped_entry_count": 179
  },
  "suspicious_forbidden_reference_count": 0,
  "suspicious_forbidden_references": [],
  "target_evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
  "target_route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "validation_safe": false
}
```
