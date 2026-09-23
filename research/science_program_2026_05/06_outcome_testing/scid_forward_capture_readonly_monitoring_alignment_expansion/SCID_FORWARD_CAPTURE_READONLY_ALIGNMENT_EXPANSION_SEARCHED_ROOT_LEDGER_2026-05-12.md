# Searched Root Ledger

- **route_id:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION`
- **evidence_class:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "searched_root_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY",
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
  "parsed_shape_file_count": 2551,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
  "schema_version": "scid_forward_capture_readonly_alignment_expansion_v1",
  "searched_root_count": 18,
  "searched_roots": [
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 337,
      "files_seen": 337,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "current_scid_source_control_route_artifacts",
      "root_path": ".",
      "scope": "current_routes",
      "why_allowed": "SCID source/control route JSON, JSONL, verifier, and tests; validation/result route names excluded."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "current_program_control_json_artifacts",
      "root_path": "research/science_program_2026_05/00_control",
      "scope": "program_control",
      "why_allowed": "program-control schemas and registries; JSON shapes only."
    },
    {
      "exists": true,
      "files_excluded": 10,
      "files_parsed_for_shape": 83,
      "files_seen": 94,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "shadow_logs_shape_only_non_forbidden_families",
      "root_path": "shadow_logs",
      "scope": "shadow_logs",
      "why_allowed": "shadow-log key sets only; broker/account/result/performance file families excluded by filename."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 4,
      "files_seen": 5,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "pipeline_state_schema_shapes",
      "root_path": "pipeline_state",
      "scope": "pipeline_state",
      "why_allowed": "pipeline-state JSON key shapes only; no values copied."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 84,
      "files_seen": 84,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "research_infra_keyword_shapes",
      "root_path": "src/research_infra",
      "scope": "research_infra",
      "why_allowed": "research-infra source keyword shapes only; no producer modification."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 45,
      "files_seen": 45,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "focused_tests_keyword_shapes",
      "root_path": "tests",
      "scope": "tests",
      "why_allowed": "test keyword/key-shape evidence only."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 340,
      "files_seen": 340,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
      "root_path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN",
      "scope": "external_routes",
      "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_program_control_shapes::SCID_IMPL_DESIGN",
      "root_path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN",
      "scope": "external_control",
      "why_allowed": "absolute local root program-control JSON shapes; no raw blobs."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 460,
      "files_seen": 460,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
      "root_path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS",
      "scope": "external_routes",
      "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_program_control_shapes::SCID_SYNTH_HARNESS",
      "root_path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS",
      "scope": "external_control",
      "why_allowed": "absolute local root program-control JSON shapes; no raw blobs."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 337,
      "files_seen": 337,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
      "root_path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION",
      "scope": "external_routes",
      "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_program_control_shapes::SCID_LTF_OF_EXPANSION",
      "root_path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION",
      "scope": "external_control",
      "why_allowed": "absolute local root program-control JSON shapes; no raw blobs."
    },
    {
      "exists": true,
      "files_excluded": 1,
      "files_parsed_for_shape": 357,
      "files_seen": 358,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
      "root_path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY",
      "scope": "external_routes",
      "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_program_control_shapes::SCID_NOAPI_HYP_FACTORY",
      "root_path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY",
      "scope": "external_control",
      "why_allowed": "absolute local root program-control JSON shapes; no raw blobs."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 27,
      "files_seen": 27,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_scid_route_artifact_shapes::NOAPIMECHREPLAY",
      "root_path": "C:/tmp/gtos_otb/NOAPIMECHREPLAY",
      "scope": "external_routes",
      "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "prior_worktree_program_control_shapes::NOAPIMECHREPLAY",
      "root_path": "C:/tmp/gtos_otb/NOAPIMECHREPLAY",
      "scope": "external_control",
      "why_allowed": "absolute local root program-control JSON shapes; no raw blobs."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 337,
      "files_seen": 337,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
      "root_path": "C:/Users/MSI/Documents/ai-trading-agent",
      "scope": "external_routes",
      "why_allowed": "absolute local root route-artifact key shapes; no raw blobs or result/validation routes."
    },
    {
      "exists": true,
      "files_excluded": 0,
      "files_parsed_for_shape": 20,
      "files_seen": 20,
      "parse_error_count": 0,
      "parse_errors": [],
      "root_label": "original_local_repo_program_control_shapes::ai-trading-agent",
      "root_path": "C:/Users/MSI/Documents/ai-trading-agent",
      "scope": "external_control",
      "why_allowed": "absolute local root program-control JSON shapes; no raw blobs."
    }
  ],
  "validation_safe": false
}
```
