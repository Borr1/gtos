# Denominator Noleak Safe Flag Audit

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "artifact_family": "DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT",
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY",
  "excluded_blocked15_card_count": 15,
  "excluded_blocked15_card_ids": [
    "ADV-004",
    "ADV-005",
    "BEH-002",
    "BEH-003",
    "BEH-004",
    "BEH-005",
    "EXE-002",
    "EXE-004",
    "GEO-001",
    "GEO-005",
    "HAZ-002",
    "MAC-002",
    "MAC-005",
    "UNC-002",
    "UNC-003"
  ],
  "expansion_candidate_ids_outside_denominator": [
    "EXP-DENOM-001",
    "EXP-MISS-001",
    "EXP-POI-001",
    "EXP-LTF-001",
    "EXP-PROXY-001",
    "EXP-LIFE-001",
    "EXP-CAL-001",
    "EXP-ADV-001"
  ],
  "failures": [],
  "forbidden_sources_excluded_count": 67,
  "g12_source_inventory_count": 13024,
  "g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
  "generated_at_utc": "2026-05-13T01:20:09Z",
  "included_card_count": 17,
  "included_card_ids": [
    "ADV-002",
    "EXE-001",
    "EXE-003",
    "EXE-005",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "HAZ-003",
    "HAZ-004",
    "MAC-003",
    "MIC-001",
    "MIC-002",
    "MIC-003",
    "MIC-004",
    "MIC-005",
    "UNC-001",
    "UNC-005"
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
  "raw_market_blob_commits_added": 0,
  "ready_8_excluded_card_ids": [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004"
  ],
  "route_id": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS",
  "schema_version": "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1",
  "target_source_inventory_count": 13024,
  "validation_safe": false
}
```
