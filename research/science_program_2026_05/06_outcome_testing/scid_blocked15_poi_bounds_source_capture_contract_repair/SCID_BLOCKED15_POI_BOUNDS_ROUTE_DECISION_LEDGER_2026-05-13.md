# Route Decision Ledger

```json
{
  "artifact_family": "route_decision_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "decisions": [
    {
      "decision": "EXHAUSTED_NO_ACCEPTED_DENOMINATOR_POI_SOURCE_ROWS",
      "evidence": [
        "research/science_program_2026_05/06_outcome_testing/g12_scid_future_capture_blocked15_source_state_materialization_audit/G12_SCID_FC_BLOCKED15_AUDIT_PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/G0_SCID_BLOCKED_UNBLOCKING_SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER_2026-05-12.json",
        "shadow_logs/scid_forward_source_capture.jsonl"
      ],
      "next_requirement": "prospective capture contract",
      "route": "existing_mso_or_scid_source_artifact_recovery"
    },
    {
      "decision": "FORBIDDEN",
      "evidence": "Would infer historical POI intent/source-state from later price movement.",
      "next_requirement": "do not use; fail closed",
      "route": "price_path_reconstruction"
    },
    {
      "decision": "REPAIRED_WITH_V2_CONTRACT",
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_poi_type_bounds_source.schema.json",
      "next_requirement": "G12 audit must compare v1 compatibility and v2 exactness.",
      "route": "offline_schema_v1_extension"
    },
    {
      "decision": "BUILT",
      "evidence": "synthetic fixtures in route fixtures directory",
      "next_requirement": "focused pytest and verifier must pass",
      "route": "synthetic_parser_fixture_route"
    },
    {
      "decision": "NOT_OPENED_FOR_THIS_GOAL",
      "evidence": "forbidden surface: live restart/live behavior",
      "next_requirement": "future owner-approved implementation route only",
      "route": "live_logger_or_restart_route"
    }
  ],
  "evidence_class": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY",
  "generated_at_utc": "2026-05-13T03:45:00Z",
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
  "route_id": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
  "schema_version": "scid_blocked15_poi_bounds_capture_contract_v1",
  "validation_safe": false
}
```
