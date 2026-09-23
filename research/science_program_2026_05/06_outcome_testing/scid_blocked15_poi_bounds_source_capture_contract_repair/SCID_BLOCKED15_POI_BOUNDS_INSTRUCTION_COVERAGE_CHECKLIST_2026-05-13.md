# Instruction Coverage Checklist

```json
{
  "all_required_items_covered": true,
  "artifact_family": "instruction_coverage_checklist",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
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
  "rows": [
    {
      "covered": true,
      "evidence": "LIVE_STATE and core doctrine files read before route build.",
      "requirement": "mandatory_preflight"
    },
    {
      "covered": true,
      "evidence": "Route inputs are disk paths and generated ledgers.",
      "requirement": "no_chat_or_compaction_memory"
    },
    {
      "covered": true,
      "evidence": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY",
      "requirement": "evidence_class_only"
    },
    {
      "covered": true,
      "evidence": [
        "validation",
        "results",
        "R/PnL/win-rate/expectancy/performance",
        "promotion",
        "AI/API",
        "paid vendor access",
        "broker account/order/history/deal/position evidence",
        "raw market blob commit",
        "live restart",
        "live behavior",
        "trading/risk/safety/prompt-decision changes"
      ],
      "requirement": "forbidden_surfaces_closed"
    },
    {
      "covered": true,
      "evidence": [
        "ADV-005",
        "BEH-002",
        "BEH-003",
        "BEH-005",
        "GEO-001"
      ],
      "requirement": "target_cards_covered"
    },
    {
      "covered": true,
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/SCID_BLOCKED15_POI_BOUNDS_SOURCE_LOGGER_CONTRACT_2026-05-13.json",
      "requirement": "source_logger_contract"
    },
    {
      "covered": true,
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/SCID_BLOCKED15_POI_BOUNDS_MSO_SNAPSHOT_HASH_SOURCE_BAR_SCHEMA_2026-05-13.json",
      "requirement": "mso_snapshot_hash_and_source_bar_schema"
    },
    {
      "covered": true,
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/SCID_BLOCKED15_POI_BOUNDS_SYNTHETIC_FIXTURE_MANIFEST_2026-05-13.json",
      "requirement": "synthetic_no_leak_redaction_fixtures"
    },
    {
      "covered": true,
      "evidence": "route verifier and focused pytest",
      "requirement": "parser_asof_hash_redaction_tests"
    },
    {
      "covered": true,
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/SCID_BLOCKED15_POI_BOUNDS_SATURATION_SELF_REDTEAM_LEDGER_2026-05-13.json",
      "requirement": "saturation_self_redteam"
    },
    {
      "covered": true,
      "evidence": [
        "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/SCID_BLOCKED15_POI_BOUNDS_NEXT_G12_REPAIR_AUDIT_PROMPT_2026-05-13.md",
        "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/SCID_BLOCKED15_POI_BOUNDS_NEXT_G12_REPAIR_AUDIT_STARTER_2026-05-13.txt"
      ],
      "requirement": "next_g12_prompt_starter"
    },
    {
      "covered": true,
      "evidence": {
        "live_effect": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "requirement": "safe_flags"
    }
  ],
  "schema_version": "scid_blocked15_poi_bounds_capture_contract_v1",
  "validation_safe": false
}
```
