# Searched And Excluded Root Recomputation Audit

- route_id: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT`
- evidence_class: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY`
- terminal_decision: `n/a`
- status: `PASS`

```json
{
  "absolute_or_prior_worktree_roots": [
    {
      "files_parsed_for_shape": 340,
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
      "root_path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN"
    },
    {
      "files_parsed_for_shape": 20,
      "root_label": "prior_worktree_program_control_shapes::SCID_IMPL_DESIGN",
      "root_path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN"
    },
    {
      "files_parsed_for_shape": 460,
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
      "root_path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS"
    },
    {
      "files_parsed_for_shape": 20,
      "root_label": "prior_worktree_program_control_shapes::SCID_SYNTH_HARNESS",
      "root_path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS"
    },
    {
      "files_parsed_for_shape": 337,
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
      "root_path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION"
    },
    {
      "files_parsed_for_shape": 20,
      "root_label": "prior_worktree_program_control_shapes::SCID_LTF_OF_EXPANSION",
      "root_path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION"
    },
    {
      "files_parsed_for_shape": 357,
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
      "root_path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY"
    },
    {
      "files_parsed_for_shape": 20,
      "root_label": "prior_worktree_program_control_shapes::SCID_NOAPI_HYP_FACTORY",
      "root_path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY"
    },
    {
      "files_parsed_for_shape": 27,
      "root_label": "prior_worktree_scid_route_artifact_shapes::NOAPIMECHREPLAY",
      "root_path": "C:/tmp/gtos_otb/NOAPIMECHREPLAY"
    },
    {
      "files_parsed_for_shape": 20,
      "root_label": "prior_worktree_program_control_shapes::NOAPIMECHREPLAY",
      "root_path": "C:/tmp/gtos_otb/NOAPIMECHREPLAY"
    },
    {
      "files_parsed_for_shape": 337,
      "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
      "root_path": "C:/Users/MSI/Documents/ai-trading-agent"
    },
    {
      "files_parsed_for_shape": 20,
      "root_label": "original_local_repo_program_control_shapes::ai-trading-agent",
      "root_path": "C:/Users/MSI/Documents/ai-trading-agent"
    }
  ],
  "artifact_family": "searched_excluded_root_recomputation_audit",
  "dynamic_exclusion_count": 11,
  "dynamic_exclusions_match_forbidden_ledger": true,
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY",
  "failures": [],
  "forbidden_file_exclusion_count": 11,
  "generated_at_utc": "2026-05-12T07:34:30Z",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "parsed_shape_file_count_reported": 2551,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recomputed_from_root_rows": {
    "external_or_prior_root_count_from_rows": 12,
    "files_excluded_from_rows": 11,
    "files_seen_from_rows": 2564,
    "parse_error_count_from_rows": 0,
    "parsed_shape_file_count_from_rows": 2551,
    "searched_root_count_from_rows": 18
  },
  "root_scope_boundary": "Excluded roots/files are accepted no-leak boundaries, not blockers, unless a required target route or allowed source/control root is missing.",
  "route_id": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT",
  "searched_more_than_accepted_twelve_targets": true,
  "searched_root_count_reported": 18,
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
  "status": "PASS",
  "validation_safe": false
}
```
