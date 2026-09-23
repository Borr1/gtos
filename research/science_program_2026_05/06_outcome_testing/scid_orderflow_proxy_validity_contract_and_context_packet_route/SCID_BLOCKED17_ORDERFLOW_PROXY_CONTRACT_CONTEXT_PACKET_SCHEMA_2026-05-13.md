# Context Packet Schema

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

```json
{
  "allowed_output": "Context/control packet fields only. No result scoring, validation, promotion, broker truth, or live decision effect.",
  "artifact_family": "CONTEXT_PACKET_SCHEMA",
  "asof_policy": "All source event times used for derived context must be <= decision_asof_utc; publication_or_capture_asof_utc must be recorded and staleness-flagged.",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY",
  "fail_closed_if_missing": [
    "source_family",
    "source_family_contract_id",
    "proxy_mapping_version",
    "proxy_instrument",
    "contract_root",
    "contract_month",
    "publication_or_capture_asof_utc",
    "source_hash_or_deferral_id",
    "parser_version",
    "non_equivalence_label",
    "duplicate_denominator_key"
  ],
  "forbidden_fields": [
    "broker account balance/equity",
    "broker order ticket",
    "broker deal id",
    "broker position id",
    "account-history realized label",
    "post-outcome path label",
    "R/PnL/win-rate/expectancy/performance field",
    "validation or promotion flag"
  ],
  "generated_at_utc": "2026-05-13T02:48:20Z",
  "join_key_policy": "Join only by frozen candidate_input_row_id/card_id/decision_asof_utc plus duplicate_denominator_key; never expand denominators or mix expansion rows.",
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
  "packet_schema_id": "scid_blocked17_orderflow_proxy_context_packet_v1",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_fields": [
    "packet_schema_version",
    "card_id",
    "candidate_input_row_id",
    "decision_asof_utc",
    "candidate_symbol",
    "source_family",
    "source_family_contract_id",
    "proxy_mapping_version",
    "proxy_instrument",
    "contract_root",
    "contract_month",
    "roll_rule_id",
    "session_calendar_id",
    "timezone_policy",
    "inverse_price_policy",
    "publication_or_capture_asof_utc",
    "source_file_pointer_or_vendor_cache_id",
    "source_hash_or_deferral_id",
    "parser_version",
    "derived_feature_schema_version",
    "non_equivalence_label",
    "staleness_status",
    "gap_or_sparse_quality_flags",
    "duplicate_denominator_key",
    "allowed_use_context_control_only",
    "invalid_context_flags"
  ],
  "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
  "schema_version": "scid_blocked17_orderflow_proxy_contract_v1",
  "source_family_contract_ids": [
    "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
    "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
    "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
    "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
  ],
  "validation_safe": false
}
```
