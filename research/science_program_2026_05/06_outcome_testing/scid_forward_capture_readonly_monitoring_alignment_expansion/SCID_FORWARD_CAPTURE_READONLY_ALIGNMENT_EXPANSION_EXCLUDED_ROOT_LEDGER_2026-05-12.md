# Excluded Root Ledger

- **route_id:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION`
- **evidence_class:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "excluded_root_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "dynamic_file_exclusion_count": 11,
  "dynamic_file_exclusions": [
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
  "evidence_class": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY",
  "exclusion_policy": "Excluded roots/files are not blockers; they are hard-boundary no-leak exclusions for this read-only shape route.",
  "generated_at_utc": "2026-05-12T05:26:39Z",
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
  "route_id": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
  "schema_version": "scid_forward_capture_readonly_alignment_expansion_v1",
  "static_excluded_roots": [
    {
      "exists": true,
      "path": "data",
      "reason": "raw market/history/tick blobs excluded by route boundary"
    },
    {
      "exists": true,
      "path": "data/ticks",
      "reason": "raw tick parquet/blob content excluded"
    },
    {
      "exists": true,
      "path": "knowledge_base/trade_records",
      "reason": "trade/broker record evidence excluded"
    },
    {
      "exists": true,
      "path": "prompts",
      "reason": "production prompt surface excluded from changes and not needed for shape map"
    },
    {
      "exists": true,
      "path": "config",
      "reason": "risk/config/live behavior surface excluded"
    },
    {
      "exists": true,
      "path": "src/components/execution.py",
      "reason": "execution/live behavior surface excluded"
    },
    {
      "exists": true,
      "path": "src/components/permissions.py",
      "reason": "safety/live decision surface excluded"
    },
    {
      "exists": true,
      "path": "scripts/canary_test.py",
      "reason": "canary selector/evaluation surface excluded"
    }
  ],
  "validation_safe": false
}
```
