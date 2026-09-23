# Orderflow Depth Proxy Source Contract Access Readiness Matrix

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_schema_groups_covered": [
    "orderflow/proxy"
  ],
  "artifact_family": "ORDERFLOW_DEPTH_PROXY_SOURCE_CONTRACT_ACCESS_READINESS_MATRIX",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:37:18Z",
  "live_effect": false,
  "matrix_scope": "orderflow/depth/proxy contracts and readiness only; all proxy evidence context-only",
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
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "rows": [
    {
      "access_readiness": "READY_FOR_NO_COMMIT_WINDOW_EXTRACTION_AFTER_OWNER_APPROVES_RAW_PARSE_SCOPE",
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "capture_group": "orderflow/proxy",
      "hash_policy": "Large external raw files hash-deferred; path/size/mtime and existing parser specs hashed.",
      "parser_requirement": "Sierra depth parser with record-size/endian proof, contract/date binding, and as-of cut.",
      "proxy_boundary": "Depth is futures/exchange ladder context, not broker-native CFD queue truth.",
      "schema_fields_unlocked": [
        "best_bid_ask_depth",
        "depth_imbalance",
        "ladder_voids",
        "absorption_proxy"
      ],
      "source_count": 152,
      "source_family": "sierra_depth_market_depth",
      "source_inventory_categories": [
        "SIERRA_DEPTH_MARKET_DEPTH_SOURCE"
      ]
    },
    {
      "access_readiness": "READY_FOR_CONTRACT_WINDOW_EXTRACTION_AFTER_HASH_OR_EXPORT_GATE",
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "capture_group": "orderflow/proxy",
      "hash_policy": "Large raw SCID hash deferred unless no-commit hash job approved.",
      "parser_requirement": "SCID parser must separate same-market CFD-like symbols from futures proxy roots.",
      "proxy_boundary": "Footprint context is source-transfer context only unless same-market source is explicitly registered.",
      "schema_fields_unlocked": [
        "bid_volume",
        "ask_volume",
        "delta",
        "volume_profile",
        "aggression_proxy"
      ],
      "source_count": 33,
      "source_family": "sierra_scid_footprint_bid_ask_volume",
      "source_inventory_categories": [
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
      ]
    },
    {
      "access_readiness": "CACHED_SOURCE_CONTROL_ONLY_READY_NEW_PULL_BLOCKED",
      "availability_status": "SOURCE_CONTROL_ARTIFACTS_AVAILABLE_NO_NEW_API_CALL_OPENED",
      "capture_group": "orderflow/proxy",
      "hash_policy": "Committed JSON/MD/PY artifacts hashed; raw vendor blobs absent or hash-deferred.",
      "parser_requirement": "Only cached/artifact paths may be referenced; any new Databento call needs a pre-call budget/free-credit manifest and owner approval.",
      "proxy_boundary": "Databento futures depth/trades are not broker-native CFD execution/account truth.",
      "schema_fields_unlocked": [
        "mbo_event_count",
        "mbp_depth_features",
        "cost_cap_status",
        "dataset_symbol_map"
      ],
      "source_count": 207,
      "source_family": "databento_cached_or_declared_orderflow_artifacts",
      "source_inventory_categories": [
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL"
      ]
    },
    {
      "access_readiness": "READY_FOR_CONTEXT_CONTRACTS_NOT_FOR_VALIDATION",
      "availability_status": "AVAILABLE_CONTEXT_ONLY_WITH_NON_EQUIVALENCE_LEDGER_REQUIRED",
      "capture_group": "orderflow/proxy",
      "hash_policy": "Source-control rows hash-bound where small; runtime logs metadata-manifested.",
      "parser_requirement": "Registry parser must fail closed if proxy mapping lacks source, contract, roll, timezone, or inverse-price policy.",
      "proxy_boundary": "All proxy rows remain context-only and not broker-native CFD truth until separate transfer validation exists.",
      "schema_fields_unlocked": [
        "proxy_group",
        "contract_root",
        "basis_caveat",
        "inverse_contract_flag",
        "blocked_mapping_reason"
      ],
      "source_count": 51,
      "source_family": "proxy_mapping_registry_and_blocker_logs",
      "source_inventory_categories": [
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL"
      ]
    }
  ],
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "validation_safe": false
}
```
