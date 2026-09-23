# SCID As-Of Completion Audit

- Route: `SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL`
- Evidence class: `SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "summary": {
    "bar_row_count": 7567,
    "can_mark_route_packet_materialized": true,
    "candidate_input_row_count": 3014,
    "live_effect": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "remaining_blockers": [],
    "validation_safe": false
  }
}
```

## Payload

```json
{
  "artifact_family": "completion_audit",
  "changes_live_trading_behavior": false,
  "completion_checks": {
    "all_9_segments_rehash_before_consumption": true,
    "all_required_artifacts_exist": true,
    "bars_source_bounded_asof_safe": true,
    "both_warnings_repaired": true,
    "candidate_rows_input_only": true,
    "discovery_exclusions_and_baselines_preserved": true,
    "duplicate_proxy_denominator_controlled": true,
    "g12_contract_decision_accepted_with_two_warnings": true,
    "live_surface_not_in_scope": true,
    "next_g12_prompt_exists": true,
    "raw_market_blobs_not_in_scope": true,
    "safe_flags_closed": true
  },
  "credentials_touched": false,
  "dirty_scope_audit": {
    "checks": {
      "no_forbidden_live_surface_paths_in_scope": true,
      "no_raw_market_blobs_in_scope": true
    },
    "forbidden_live_surface_paths_in_scope": [],
    "raw_market_blob_paths_in_scope": [],
    "scoped_route_or_prompt_paths": [
      "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-11.md",
      "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/"
    ],
    "unrelated_workspace_dirt_recorded_only": [
      "M .context/LIVE_STATE.md",
      "M knowledge_base/index/trade_record_inventory_index_2026-05-05.json",
      "M knowledge_base/monitoring/edge_monitor_state.json",
      "M pipeline_state/live_monitoring_maintenance_state.json",
      "M pipeline_state/sierra_depth_enrichment_checkpoint.json",
      "M research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json",
      "M research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
      "M research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json",
      "M research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md",
      "M research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json",
      "M research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.md",
      "M research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.json",
      "M research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md",
      "M research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.json",
      "M research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md",
      "M research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json",
      "M research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md",
      "M research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json",
      "M research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md",
      "M research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.json",
      "M research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md",
      "M research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.json",
      "M research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md",
      "M research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json",
      "M research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md",
      "M research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.json",
      "M research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md",
      "M research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json",
      "M research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md",
      "M research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json",
      "M research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md",
      "M research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json",
      "M research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md",
      "M research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json",
      "M research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md",
      "M research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.json",
      "M research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md",
      "M research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json",
      "M research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md",
      "M research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.json",
      "M research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.md",
      "M research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.json",
      "M research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md",
      "M research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.json",
      "M research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md",
      "M research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.json",
      "M research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md",
      "M research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json",
      "M research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md",
      "M research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.json",
      "M research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md",
      "M research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json",
      "M research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md",
      "M research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.json",
      "M research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md",
      "M research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.json",
      "M research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md",
      "M research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json",
      "M research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md",
      "M research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.json",
      "M research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md",
      "M research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.json",
      "M research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md",
      "M research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.json",
      "M research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json",
      "M research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.json",
      "M research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md",
      "M research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.json",
      "M research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md",
      "M research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json",
      "M research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.json",
      "M research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md",
      "M research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.json",
      "M research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.json",
      "M research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md",
      "M research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.json",
      "M research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md",
      "M research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.json",
      "M research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md",
      "M research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json",
      "M research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.md",
      "M research/science_program_2026_05/04_goal_prompts/G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md",
      "M scripts/_live_monitor_iter.py",
      "M shadow_logs/account_pnl_truth_reconciliation.jsonl",
      "M shadow_logs/account_truth_reconciliation_status.jsonl",
      "M shadow_logs/broker_actual_r_audit.jsonl",
      "M shadow_logs/candidate_features_log.jsonl",
      "M shadow_logs/candidate_ltf_path_order.jsonl",
      "M shadow_logs/candidate_path_contract_audit.jsonl",
      "M shadow_logs/candidate_path_follow.jsonl",
      "M shadow_logs/candidate_registry_audit.jsonl",
      "M shadow_logs/context_control_audit.jsonl",
      "M shadow_logs/context_control_ledger.jsonl",
      "M shadow_logs/cusum_candidate_rate_daily.csv",
      "M shadow_logs/daily_pnl.json",
      "M shadow_logs/daily_pnl_history.jsonl",
      "M shadow_logs/databento_live_trigger_decisions.jsonl",
      "M shadow_logs/decision_layer_diagnostics_join.jsonl",
      "M shadow_logs/direction_emission_xau_audit.jsonl",
      "M shadow_logs/displacement_events.jsonl",
      "M shadow_logs/dumb_baseline_hypotheticals.jsonl",
      "M shadow_logs/es_mes_preregistration_status.jsonl",
      "M shadow_logs/exit_management_shadow_status.jsonl",
      "M shadow_logs/external_source_blocker_status.jsonl",
      "M shadow_logs/fvg_ob_confluence.jsonl",
      "M shadow_logs/fvg_ob_confluence_audit.jsonl",
      "M shadow_logs/fvg_ob_confluence_resolutions.jsonl",
      "M shadow_logs/gbpjpy_proxy_gap_status.jsonl",
      "M shadow_logs/heartbeat_flatten_events.jsonl",
      "M shadow_logs/j46_j49_exit_comparator_audit.jsonl",
      "M shadow_logs/j46_j49_shadow_outcomes.jsonl",
      "M shad
... truncated in markdown; see matching JSON artifact ...
```
