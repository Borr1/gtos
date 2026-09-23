# Decision Ledger

```json
{
  "accepted_evidence_class_only": true,
  "artifact_family": "DECISION_LEDGER",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "decision_checks": [
    {
      "check": "source_status",
      "passed": true
    },
    {
      "check": "parser_hash_asof",
      "passed": true
    },
    {
      "check": "missing_exact",
      "passed": true
    },
    {
      "check": "denominator_noleak",
      "passed": true
    },
    {
      "check": "saturation",
      "passed": true
    }
  ],
  "evidence_class": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_ONLY",
  "exact_downstream_requirements": [
    {
      "access_or_owner_requirement": "None for existing local files; owner approval only if a new Sierra export/copy is requested.",
      "affected_field": "ltf_source_hash",
      "affected_source_family": "sierra_converted_m1_m5_m15_ohlcv_roots",
      "exact_action": "For any large un-hashed CSV selected by a future packet, run a no-commit sha256 job and record path,size,mtime,sha256,parser_id before G12 acceptance.",
      "forbidden_boundary": "Do not commit raw CSV blobs or open result fields.",
      "g12_audit_status": "EXACT_DOWNSTREAM_REQUIREMENT_PRESERVED",
      "requirement_id": "REQ-LTF-HASH-001",
      "source_file_count": 150,
      "status": "EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED"
    },
    {
      "access_or_owner_requirement": "None for read-only metadata from existing local files; separate owner approval if a route wants to copy/export raw parquet into a packet.",
      "affected_field": "ltf_source_hash",
      "affected_source_family": "prior_production_mt5_tick_parquet_market_context",
      "exact_action": "For any large parquet selected by a future packet, run a no-commit sha256 job or accepted hash-deferral audit and record path,size,mtime,sha256-or-deferral,parser_id.",
      "forbidden_boundary": "Exclude account/order/history/deal/position fields and do not commit raw parquet blobs.",
      "g12_audit_status": "EXACT_DOWNSTREAM_REQUIREMENT_PRESERVED",
      "requirement_id": "REQ-LTF-HASH-002",
      "source_file_count": 93,
      "status": "EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED"
    },
    {
      "access_or_owner_requirement": "None.",
      "affected_field": "decision_minus_window_start_utc",
      "affected_source_family": "all_ltf_source_families",
      "exact_action": "Card-level packet builder must copy candidate bar_window_start_utc or register a card-specific source-control window_start before parsing LTF rows; missing value fails closed.",
      "forbidden_boundary": "Do not infer the window from target/result/path outcome fields.",
      "g12_audit_status": "EXACT_DOWNSTREAM_REQUIREMENT_PRESERVED",
      "requirement_id": "REQ-LTF-WINDOW-003",
      "source_file_count": null,
      "status": "EXACT_PACKET_FIELD_REQUIREMENT_ATTACHED"
    },
    {
      "access_or_owner_requirement": "None for audit. Any future raw-source extraction remains separately owner/access gated.",
      "affected_field": "all SOURCE_EXISTS_NEEDS_PARSER rows",
      "affected_source_family": "blocked17_ltf_asof_attachment_matrix",
      "exact_action": "Run research/science_program_2026_05/04_goal_prompts/G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_GOAL_PROMPT_2026-05-13.md to independently audit denominator, parser binding, source hash/as-of requirements, fail-closed states, and safe flags before any result gate.",
      "forbidden_boundary": "G12 audit remains source-status/control evidence only.",
      "g12_audit_status": "CLOSED_BY_THIS_AUDIT",
      "requirement_id": "REQ-G12-AUDIT-004",
      "source_file_count": 78,
      "status": "EXACT_G12_REPAIR_AUDIT_REQUIREMENT_ATTACHED"
    }
  ],
  "fair_audit_policy": "Absence of result/performance validation is not a blocker in this parser/hash/as-of source-control lane; only denominator, parser, hash, as-of, manifest, no-leak, or forbidden-surface failures can reject the packet.",
  "generated_at_utc": "2026-05-13T04:46:17Z",
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
  "route_id": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT",
  "schema_version": "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_v1",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false
}
```
