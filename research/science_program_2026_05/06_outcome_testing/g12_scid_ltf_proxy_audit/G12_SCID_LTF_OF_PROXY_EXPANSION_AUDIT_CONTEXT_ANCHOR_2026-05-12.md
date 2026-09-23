# Context Anchor

```json
{
  "anti_boxing_checks_pursued": [
    "Did the audit penalize valid LTF/orderflow/proxy context just because it is not OB-only? No.",
    "Did the audit require validation/R/PnL/win-rate in a lane where absence is required? No.",
    "Did the audit distinguish futures/proxy context from broker-native CFD/account/order truth? Yes.",
    "Did the audit treat absolute local roots and prior worktrees as valid searched sources? Yes."
  ],
  "artifact_family": "context_anchor",
  "builder_artifacts_read": {
    "approval_gates": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_APPROVAL_GATE_LEDGER_2026-05-12.json",
    "asof_noleak": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-12.json",
    "candidate_coverage": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CANDIDATE_COVERAGE_MATRIX_2026-05-12.json",
    "closeout": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "completion": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.json",
    "decision": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_DECISION_LEDGER_2026-05-12.json",
    "inventory": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SOURCE_INVENTORY_HASH_MANIFEST_2026-05-12.json",
    "ladder": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ACQUISITION_LADDER_2026-05-12.json",
    "ltf_matrix": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
    "manifest": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json",
    "orderflow_matrix": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
    "proxy_validity": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
    "reconciliation": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json",
    "verification_result": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json"
  },
  "candidate_input_rows_path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
  "changes_live_trading_behavior": false,
  "controlling_prompt_sha256": "ef90b47e287e2da52e269417a870eef1af7af6343ce9b5674e037c8cd02b9e7d",
  "credentials_touched": false,
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T07:45:55Z",
  "input_route": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis",
  "lane_posture": "G12 audit: adversarial but fair. Accept auditable source/control doors when proxy/context labels and no-leak boundaries are exact; reject or repair only concrete source, field, root, hash, proxy-label, scoped-diff, verifier, or evidence-class failures.",
  "live_effect": false,
  "mandatory_context_files_read_after_preflight": [
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_current_state.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
  ],
  "objective_restatement": "Independently audit the source/control-only LTF/orderflow/proxy expansion route from disk, recomputing row boundaries, ten capture groups, inventories, source search, hash/deferral policy, matrices, proxy validity, approval gates, no-leak scope, verifier/test evidence, and forbidden-surface absence.",
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
  "proof_or_impossibility_stop_condition": "Accept only if every prompt requirement recomputes cleanly; otherwise emit exact file/field/source/root/hash/proxy/no-leak/scoped-diff/test failures.",
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "validation_safe": false
}
```
