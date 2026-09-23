# Closeout Verification

- **route_id:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "closeout_verification",
  "changes_live_trading_behavior": false,
  "closeout_metadata_refreshed_at_utc": "2026-05-12T04:25:54Z",
  "context_refresh_commit": "cade19b4 docs: refresh state after scid offline schema g0 synthesis",
  "credentials_touched": false,
  "evidence_class": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY",
  "final_live_state_refresh": {
    "complete": true,
    "generated_at_utc": "2026-05-12 04:21:49 UTC",
    "head": "cade19b4 docs: refresh state after scid offline schema g0 synthesis",
    "research_context_fresh": true
  },
  "final_live_state_refresh_complete": true,
  "focused_pytest": {
    "command": "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/test_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
    "observed_result": "6 passed",
    "status": "PASSED"
  },
  "generated_at_utc": "2026-05-12T04:18:03Z",
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
  "planned_commands": [
    "python research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/build_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
    "python research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/verify_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
    "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/test_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
    "python scripts/generate_live_state.py"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "research_artifact_commit": "b81b8772 research: synthesize scid offline schema g0 routes",
  "route_artifact_dir": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control",
  "route_id": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL",
  "schema_version": "g0_scid_forward_capture_offline_schema_synthesis_v1",
  "scoped_commits": {
    "complete": true,
    "context_refresh_commit": "cade19b4 docs: refresh state after scid offline schema g0 synthesis",
    "research_artifact_commit": "b81b8772 research: synthesize scid offline schema g0 routes",
    "scope": "new G0 route artifacts, five prompt packs, and research context/live-state refresh only"
  },
  "scoped_commits_complete": true,
  "scoped_git_status": {
    "entries": [
      {
        "path": "context/LIVE_STATE.md",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "M "
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
        "path": "scripts/_live_monitor_iter.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/backfill_account_pnl_truth_reconciliation.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/backfill_broker_actual_r_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/build_daily_monitoring_checklist.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/close_live_shadow_capture_gaps.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/run_live_monitoring_maintenance.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/verify_shadow_log_integrity.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "scripts/watchdog.ps1",
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
        "path": "src/components/edge_monitor.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/components/mt5_daemon_runtime.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/components/orchestrator.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/components/tick_capture.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/research_infra/decision_layer_diagnostics_join.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/research_infra/exit_management_no_event_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/research_infra/live_shadow_gap_closure.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/research_infra/opportunity_lifecycle_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/research_infra/pending_limit_lifecycle_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "src/research_infra/v2_structural_selector_readiness.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_decision_layer_diagnostics_join.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_exit_management_no_event_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_live_shadow_gap_closure.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_mt5_daemon_runtime.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_opportunity_lifecycle_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_orchestrator.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_pending_limit_lifecycle_audit.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_tick_capture.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_v2_structural_selector_readiness.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "tests/test_verify_shadow_log_integrity.py",
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
        "path": "research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.json",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.md",
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
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "scripts/analyze_missed_fill_opportunities.py",
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
      },
      {
        "path": "src/research_infra/missed_fill_opportunity_study.py",
        "scoped": false,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "tests/test_missed_fill_opportunity_study.py",
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
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      }
    ],
    "stderr": [
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied"
    ]
  },
  "scoped_git_status_at_build": {
    "no_scoped_forbidden_live_surface": true,
    "no_scoped_raw_market_blob": true,
    "returncode": 0,
    "scoped_entries": [
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": "??"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/",
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
    "unrelated_dirty_entry_count": 211
  },
  "selected_prompt_packs": {
    "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES": {
      "one_line_starter": "/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, 3,014 candidate coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    },
    "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE": {
      "one_line_starter": "/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, 3,014 candidate coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    },
    "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION": {
      "one_line_starter": "/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, 3,014 candidate coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    },
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": {
      "one_line_starter": "/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, 3,014 candidate coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    },
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS": {
      "one_line_starter": "/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, 3,014 candidate coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    }
  },
  "standalone_verifier": {
    "failure_count": 0,
    "ok": true,
    "status": "PASSED"
  },
  "status": "STANDALONE_VERIFIER_FOCUSED_PYTEST_SCOPED_COMMITS_AND_FINAL_LIVE_STATE_REFRESH_PASSED",
  "syntax_parse": {
    "failures": [],
    "method": "ast_parse_no_bytecode",
    "ok": true
  },
  "terminal_decision": "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE",
  "validation_safe": false
}
```
