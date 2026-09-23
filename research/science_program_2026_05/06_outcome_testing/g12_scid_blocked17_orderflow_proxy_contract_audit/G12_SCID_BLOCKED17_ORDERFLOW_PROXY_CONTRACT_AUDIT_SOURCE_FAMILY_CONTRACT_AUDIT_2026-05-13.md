# Source Family Contract Audit

```json
{
  "artifact_family": "SOURCE_FAMILY_CONTRACT_AUDIT",
  "changes_live_trading_behavior": false,
  "contract_count": 4,
  "contract_rows": [
    {
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "checks": {
        "broker_native_cfd_truth_disallowed": true,
        "contract_id_present": true,
        "exact_access_requirement_present": true,
        "invalid_context_blocks_broker_truth": true,
        "invalid_context_blocks_hash_or_non_equivalence_gap": true,
        "invalid_context_blocks_result_claims": true,
        "may_score_results_now_false": true,
        "parser_acceptance_criteria_present": true,
        "roll_session_asof_rule_present": true,
        "source_family_present": true,
        "staleness_policy_present": true,
        "upstream_proxy_boundary_present": true
      },
      "contract_id": "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_EXACT_RAW_PARSE_SCOPE_REQUIRED",
      "exact_access_requirement_if_unresolved": "Run a no-commit Sierra .depth window inventory/parser job for declared contract/date windows; record path, size, mtime, sha256 or accepted hash deferral; do not commit raw .depth.",
      "source_family": "sierra_depth_market_depth",
      "upstream_source_count": 152
    },
    {
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "checks": {
        "broker_native_cfd_truth_disallowed": true,
        "contract_id_present": true,
        "exact_access_requirement_present": true,
        "invalid_context_blocks_broker_truth": true,
        "invalid_context_blocks_hash_or_non_equivalence_gap": true,
        "invalid_context_blocks_result_claims": true,
        "may_score_results_now_false": true,
        "parser_acceptance_criteria_present": true,
        "roll_session_asof_rule_present": true,
        "source_family_present": true,
        "staleness_policy_present": true,
        "upstream_proxy_boundary_present": true
      },
      "contract_id": "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_EXACT_SCID_PARSE_REQUIREMENT",
      "exact_access_requirement_if_unresolved": "Run a no-commit SCID parser over declared symbol/windows; attach parser version, scale proof, path, size, mtime, and hash/deferral id.",
      "source_family": "sierra_scid_footprint_bid_ask_volume",
      "upstream_source_count": 33
    },
    {
      "availability_status": "SOURCE_CONTROL_ARTIFACTS_AVAILABLE_NO_NEW_API_CALL_OPENED",
      "checks": {
        "broker_native_cfd_truth_disallowed": true,
        "contract_id_present": true,
        "exact_access_requirement_present": true,
        "invalid_context_blocks_broker_truth": true,
        "invalid_context_blocks_hash_or_non_equivalence_gap": true,
        "invalid_context_blocks_result_claims": true,
        "may_score_results_now_false": true,
        "parser_acceptance_criteria_present": true,
        "roll_session_asof_rule_present": true,
        "source_family_present": true,
        "staleness_policy_present": true,
        "upstream_proxy_boundary_present": true
      },
      "contract_id": "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_CACHED_ONLY_NEW_PULL_BLOCKED",
      "exact_access_requirement_if_unresolved": "For a missing window, write a pre-call manifest with dataset, schema, symbol, UTC window, expected fields, expected cost/free-credit status, no-leak policy, and owner approval requirement before any fetch.",
      "source_family": "databento_cached_or_declared_orderflow_artifacts",
      "upstream_source_count": 207
    },
    {
      "availability_status": "AVAILABLE_CONTEXT_ONLY_WITH_NON_EQUIVALENCE_LEDGER_REQUIRED",
      "checks": {
        "broker_native_cfd_truth_disallowed": true,
        "contract_id_present": true,
        "exact_access_requirement_present": true,
        "invalid_context_blocks_broker_truth": true,
        "invalid_context_blocks_hash_or_non_equivalence_gap": true,
        "invalid_context_blocks_result_claims": true,
        "may_score_results_now_false": true,
        "parser_acceptance_criteria_present": true,
        "roll_session_asof_rule_present": true,
        "source_family_present": true,
        "staleness_policy_present": true,
        "upstream_proxy_boundary_present": true
      },
      "contract_id": "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_FAIL_CLOSED_MAPPING_REQUIRED",
      "exact_access_requirement_if_unresolved": "Materialize the mapping registry row from committed source-control artifacts or append a prospective proxy-mapping capture requirement; do not infer mapping from price correlation.",
      "source_family": "proxy_mapping_registry_and_blocker_logs",
      "upstream_source_count": 51
    }
  ],
  "credentials_touched": false,
  "evidence_class": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_ONLY",
  "failure_count": 0,
  "failures": [],
  "generated_at_utc": "2026-05-13T04:50:06Z",
  "global_rules": [
    "Every packet row must carry source_family, source_file_pointer_or_vendor_cache_id, source_hash or accepted deferral id, proxy_mapping_version, contract root/month or same-market root, publication_or_capture_asof_utc, parser_version, and non_equivalence_label.",
    "Every proxy row is context/control only until a separate G12/G0 route accepts transfer/equivalence and a separate result lane explicitly opens scoring.",
    "Parser must fail closed on missing contract, roll, session calendar, timezone, inverse-price policy, source hash/deferral, or non-equivalence label.",
    "No raw .depth/.scid/vendor market blob may be committed by this route."
  ],
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_requirement_surface_count": 72,
  "route_id": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT",
  "schema_version": "g12_scid_blocked17_orderflow_proxy_contract_audit_v1",
  "source_family_total_upstream_source_count": 443,
  "validation_safe": false
}
```
