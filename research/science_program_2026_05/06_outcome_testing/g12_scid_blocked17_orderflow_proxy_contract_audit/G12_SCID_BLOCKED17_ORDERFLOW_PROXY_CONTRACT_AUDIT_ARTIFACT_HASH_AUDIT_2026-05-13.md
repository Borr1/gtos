# Artifact Hash Audit

```json
{
  "artifact_family": "ARTIFACT_HASH_AUDIT",
  "changes_live_trading_behavior": false,
  "classification_counts": {
    "PROMPT_HASH_MANIFEST_DRIFT_REPAIRED_BY_CURRENT_AUDIT_REHASH": 1,
    "RAW_BYTE_HASH_MATCH": 23,
    "TEXT_EOL_EQUIVALENT_LF_HASH_MATCH": 5
  },
  "credentials_touched": false,
  "evidence_class": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T04:50:06Z",
  "live_effect": false,
  "manifest_self_hash_policy": "target output manifest excludes itself; audit binds its current hash separately",
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
  "route_id": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT",
  "row_count_recomputed": 29,
  "same_g12_repairs_closed": [
    {
      "current_sha256": "4affec0b8cabf9bd28698295d6fa5e081853fb0600372390ffdac2694e9f5cb4",
      "current_size_bytes": 4528,
      "old_manifest_sha256": "f68bd35ebcac1bf606dea114f3ba3353acf853e45306e1e1aa4aa0382374df91",
      "old_manifest_size_bytes": 3155,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-13.md",
      "repair_status": "CLOSED_IN_G12_AUDIT_REHASH_PROJECTION"
    }
  ],
  "schema_version": "g12_scid_blocked17_orderflow_proxy_contract_audit_v1",
  "strict_failure_count": 0,
  "strict_failures": [],
  "target_focused_tests_ok": true,
  "target_focused_tests_summary": "..... [100%]; 5 passed in 0.60s",
  "target_manifest_artifact_count": 29,
  "target_manifest_current_sha256": "2c81ccb12efd575965fa1b8fdcb759a5dd0c4019356a72206400f0634c087d78",
  "target_manifest_path": "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_OUTPUT_MANIFEST_2026-05-13.json",
  "target_verifier_ok": true,
  "text_eol_equivalent_row_count": 5,
  "text_eol_equivalent_rows": [
    {
      "crlf_count": 16,
      "lf_normalized_sha256": "ff5103215726e6b0c5ff49c571d70783400c4d0b3c3f8a6e6d52c444228b56c3",
      "manifest_sha256": "ff5103215726e6b0c5ff49c571d70783400c4d0b3c3f8a6e6d52c444228b56c3",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_FOCUSED_TEST_RESULT_2026-05-13.json"
    },
    {
      "crlf_count": 14,
      "lf_normalized_sha256": "f6e5b97cf8e0d1760a7ccb6dd467c2953f76c000e86de0aa714c49167b170c4b",
      "manifest_sha256": "f6e5b97cf8e0d1760a7ccb6dd467c2953f76c000e86de0aa714c49167b170c4b",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_FOCUSED_TEST_RESULT_2026-05-13.md"
    },
    {
      "crlf_count": 1176,
      "lf_normalized_sha256": "982d58e0b68d5095b331e6d7da5b892571612b4b983f8e909eee68cf4d38d88c",
      "manifest_sha256": "982d58e0b68d5095b331e6d7da5b892571612b4b983f8e909eee68cf4d38d88c",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/build_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py"
    },
    {
      "crlf_count": 127,
      "lf_normalized_sha256": "f500a38df1746a8a191eda4b58861fbadb369e1bbdd1bbd2446120655665a424",
      "manifest_sha256": "f500a38df1746a8a191eda4b58861fbadb369e1bbdd1bbd2446120655665a424",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/test_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py"
    },
    {
      "crlf_count": 306,
      "lf_normalized_sha256": "6ec60069d0300cfe9a19a83205d94b765c51942ab6d7ee1da682efc4db868588",
      "manifest_sha256": "6ec60069d0300cfe9a19a83205d94b765c51942ab6d7ee1da682efc4db868588",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/verify_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py"
    }
  ],
  "validation_safe": false
}
```
