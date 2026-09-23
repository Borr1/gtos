# Paid Access Free Blocker Ledger

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

```json
{
  "all_remainders_exact": true,
  "artifact_family": "PAID_ACCESS_FREE_BLOCKER_LEDGER",
  "blocker_count": 6,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY",
  "generated_at_utc": "2026-05-13T02:48:20Z",
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
  "paid_vendor_access_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_dependency_surface_count": 72,
  "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
  "rows": [
    {
      "ai_or_api_required_now": false,
      "blocker_id": "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1_ACCESS_OR_PARSER_REQUIREMENT",
      "exact_requirement": "Run a no-commit Sierra .depth window inventory/parser job for declared contract/date windows; record path, size, mtime, sha256 or accepted hash deferral; do not commit raw .depth.",
      "owner_or_future_route_action": "G12 audit may accept the contract as source-control; parser/materialization remains a separate no-commit source-control route if raw windows are needed.",
      "paid_access_required_now": false,
      "raw_blob_commit_required_now": false,
      "source_family": "sierra_depth_market_depth",
      "status": "CONTRACT_ATTACHED_EXACT_RAW_PARSE_SCOPE_REQUIRED"
    },
    {
      "ai_or_api_required_now": false,
      "blocker_id": "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1_ACCESS_OR_PARSER_REQUIREMENT",
      "exact_requirement": "Run a no-commit SCID parser over declared symbol/windows; attach parser version, scale proof, path, size, mtime, and hash/deferral id.",
      "owner_or_future_route_action": "G12 audit may accept the contract as source-control; parser/materialization remains a separate no-commit source-control route if raw windows are needed.",
      "paid_access_required_now": false,
      "raw_blob_commit_required_now": false,
      "source_family": "sierra_scid_footprint_bid_ask_volume",
      "status": "CONTRACT_ATTACHED_EXACT_SCID_PARSE_REQUIREMENT"
    },
    {
      "ai_or_api_required_now": false,
      "blocker_id": "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1_ACCESS_OR_PARSER_REQUIREMENT",
      "exact_requirement": "For a missing window, write a pre-call manifest with dataset, schema, symbol, UTC window, expected fields, expected cost/free-credit status, no-leak policy, and owner approval requirement before any fetch.",
      "owner_or_future_route_action": "G12 audit may accept the contract as source-control; parser/materialization remains a separate no-commit source-control route if raw windows are needed.",
      "paid_access_required_now": false,
      "raw_blob_commit_required_now": false,
      "source_family": "databento_cached_or_declared_orderflow_artifacts",
      "status": "CONTRACT_ATTACHED_CACHED_ONLY_NEW_PULL_BLOCKED"
    },
    {
      "ai_or_api_required_now": false,
      "blocker_id": "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1_ACCESS_OR_PARSER_REQUIREMENT",
      "exact_requirement": "Materialize the mapping registry row from committed source-control artifacts or append a prospective proxy-mapping capture requirement; do not infer mapping from price correlation.",
      "owner_or_future_route_action": "G12 audit may accept the contract as source-control; parser/materialization remains a separate no-commit source-control route if raw windows are needed.",
      "paid_access_required_now": false,
      "raw_blob_commit_required_now": false,
      "source_family": "proxy_mapping_registry_and_blocker_logs",
      "status": "CONTRACT_ATTACHED_FAIL_CLOSED_MAPPING_REQUIRED"
    },
    {
      "ai_or_api_required_now": false,
      "blocker_id": "PROXY_TRANSFER_VALIDATION_NOT_OPENED",
      "exact_requirement": "Separate future G12/G0 result or transfer-validation gate must freeze proxy-transfer hypothesis, denominator, source hashes, and result permissions before any interpretation beyond context/control.",
      "owner_or_future_route_action": "Do not open in this route.",
      "paid_access_required_now": false,
      "raw_blob_commit_required_now": false,
      "source_family": "all_proxy_families",
      "status": "SEPARATE_EVIDENCE_CLASS_REQUIRED"
    },
    {
      "ai_or_api_required_now": false,
      "blocker_id": "BROKER_NATIVE_CFD_TRUTH_FORBIDDEN",
      "exact_requirement": "Broker-native CFD truth would require an explicitly authorized broker/source lane and cannot be inferred from futures, Sierra, Databento, or proxy mapping rows.",
      "owner_or_future_route_action": "Do not request or consume broker account/order/history/deal/position evidence in this lane.",
      "paid_access_required_now": false,
      "raw_blob_commit_required_now": false,
      "source_family": "all_proxy_families",
      "status": "HARD_FORBIDDEN_IN_THIS_LANE"
    }
  ],
  "schema_version": "scid_blocked17_orderflow_proxy_contract_v1",
  "vague_blocker_wording_present": false,
  "validation_safe": false
}
```
