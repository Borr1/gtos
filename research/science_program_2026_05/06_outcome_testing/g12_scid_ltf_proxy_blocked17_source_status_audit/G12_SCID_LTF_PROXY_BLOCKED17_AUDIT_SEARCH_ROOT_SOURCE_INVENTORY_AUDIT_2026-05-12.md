# Search Root Source Inventory Audit

```json
{
  "artifact_family": "SEARCH_ROOT_SOURCE_INVENTORY_AUDIT",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY",
  "failures": [],
  "forbidden_sources_excluded_count": 67,
  "generated_at_utc": "2026-05-12T18:00:40Z",
  "hash_status_counts": {
    "HASHED_NOW": 11932,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 180,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 491,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 421
  },
  "live_effect": false,
  "missing_required_categories": [],
  "missing_required_roots": [],
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
  "required_categories_present": [
    "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT",
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
  ],
  "required_roots_present": [
    "absolute_external_source_cache",
    "absolute_production_data_tree",
    "absolute_production_tick_root",
    "current_route_and_source_control_artifacts",
    "current_worktree_data_tree",
    "current_worktree_shadow_source_status_logs",
    "prior_gtos_worktrees",
    "sierrachart_data_root"
  ],
  "root_rows": [
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 4309,
      "forbidden_sources_excluded": 0,
      "ladder_step": 1,
      "negative_hit": false,
      "parse_failures": [],
      "path": "research/science_program_2026_05/06_outcome_testing",
      "patterns": [
        "*.json",
        "*.jsonl",
        "*.md",
        "*.py"
      ],
      "positive_source_categories": {
        "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT": 60,
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 2,
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 4226
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Accepted SCID source-control, prior LTF/proxy, G12 audit, strategy-field, and offline schema ledgers.",
      "root_id": "current_route_and_source_control_artifacts",
      "sources_selected": 4288,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 109,
      "forbidden_sources_excluded": 4,
      "ladder_step": 2,
      "negative_hit": false,
      "parse_failures": [],
      "path": "shadow_logs",
      "patterns": [
        "*.jsonl",
        "*.csv"
      ],
      "positive_source_categories": {
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 3,
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 102
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Source-status and path shadow logs only, excluding broker/result/account/order evidence.",
      "root_id": "current_worktree_shadow_source_status_logs",
      "sources_selected": 105,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 338,
      "forbidden_sources_excluded": 1,
      "ladder_step": 3,
      "negative_hit": false,
      "parse_failures": [],
      "path": "data",
      "patterns": [
        "*.csv",
        "*.json",
        "*.jsonl",
        "*.parquet",
        "*.zst",
        "*.scid"
      ],
      "positive_source_categories": {
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 211,
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 126
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Worktree data/source-cache discovery. Raw market blobs are metadata only.",
      "root_id": "current_worktree_data_tree",
      "sources_selected": 337,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 1161,
      "forbidden_sources_excluded": 4,
      "ladder_step": 4,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data",
      "patterns": [
        "*.csv",
        "*.json",
        "*.jsonl",
        "*.parquet",
        "*.zst",
        "*.scid"
      ],
      "positive_source_categories": {
        "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE": 93,
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 226,
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 385,
        "OTHER_RELEVANT_SOURCE_METADATA": 327,
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 126
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Primary local-heavy production data root from local_heavy_data_inventory.md.",
      "root_id": "absolute_production_data_tree",
      "sources_selected": 1157,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 94,
      "forbidden_sources_excluded": 0,
      "ladder_step": 5,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
      "patterns": [
        "*.parquet",
        "*.json",
        "*.md"
      ],
      "positive_source_categories": {
        "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE": 93,
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 1
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "MT5 tick parquet market-context captures by symbol/date, not account/order evidence.",
      "root_id": "absolute_production_tick_root",
      "sources_selected": 94,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 570,
      "forbidden_sources_excluded": 2,
      "ladder_step": 6,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/external",
      "patterns": [
        "*.json",
        "*.jsonl",
        "*.zst",
        "*.csv",
        "*.txt"
      ],
      "positive_source_categories": {
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 226,
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 340,
        "OTHER_RELEVANT_SOURCE_METADATA": 2
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "External feature/source/vendor/status/cache artifacts.",
      "root_id": "absolute_external_source_cache",
      "sources_selected": 568,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 3,
      "forbidden_sources_excluded": 0,
      "ladder_step": 7,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/sierrachart_exports",
      "patterns": [
        "*.csv",
        "*.json"
      ],
      "positive_source_categories": {
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 2,
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 1
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Sierra exported or converted source files.",
      "root_id": "absolute_sierra_converted_exports",
      "sources_selected": 3,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 132,
      "forbidden_sources_excluded": 0,
      "ladder_step": 8,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots",
      "patterns": [
        "*.csv",
        "*.json"
      ],
      "positive_source_categories": {
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 7,
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 125
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Sierra OHLCV root exports for LTF path source status.",
      "root_id": "absolute_sierra_ohlcv_roots",
      "sources_selected": 132,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 123,
      "forbidden_sources_excluded": 4,
      "ladder_step": 9,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
      "patterns": [
        "*.jsonl",
        "*.csv"
      ],
      "positive_source_categories": {
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 3,
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 77,
        "OTHER_RELEVANT_SOURCE_METADATA": 3,
        "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE": 30,
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 6
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Production shadow logs for source status only, excluding result/account/order evidence.",
      "root_id": "absolute_production_shadow_logs",
      "sources_selected": 119,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 88,
      "forbidden_sources_excluded": 0,
      "ladder_step": 10,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/Users/MSI/Documents/ai-trading-agent/exports",
      "patterns": [
        "*.csv",
        "*.json",
        "*.jsonl",
        "*.txt"
      ],
      "positive_source_categories": {
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 31,
        "OTHER_RELEVANT_SOURCE_METADATA": 57
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Owner/export cache discovery if present.",
      "root_id": "absolute_exports_root",
      "sources_selected": 88,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 185,
      "forbidden_sources_excluded": 0,
      "ladder_step": 11,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/SierraChart/Data",
      "patterns": [
        "*.scid",
        "*.depth",
        "*.csv"
      ],
      "positive_source_categories": {
        "OTHER_RELEVANT_SOURCE_METADATA": 152,
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE": 33
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Sierra local .scid/depth/time-and-sales source-status discovery.",
      "root_id": "sierrachart_data_root",
      "sources_selected": 185,
      "status": "SEARCHED"
    },
    {
      "access_requirement": null,
      "exists": true,
      "files_seen": 6000,
      "forbidden_sources_excluded": 52,
      "ladder_step": 12,
      "negative_hit": false,
      "parse_failures": [],
      "path": "C:/tmp/gtos_otb",
      "patterns": [
        "*.json",
        "*.jsonl",
        "*.md",
        "*.py",
        "*.csv"
      ],
      "positive_source_categories": {
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 133,
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 5299,
        "OTHER_RELEVANT_SOURCE_METADATA": 390,
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 126
      },
      "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs.",
      "purpose": "Prior worktree/source-status route discovery; not canonical without hashes.",
      "root_id": "prior_gtos_worktrees",
      "sources_selected": 5948,
      "status": "SEARCHED"
    }
  ],
  "route_id": "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT",
  "schema_version": "g12_scid_ltf_proxy_blocked17_source_status_audit_v1",
  "searched_root_count": 12,
  "source_category_counts": {
    "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT": 60,
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE": 186,
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 593,
    "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 6142,
    "OTHER_RELEVANT_SOURCE_METADATA": 931,
    "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE": 30,
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 4545,
    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 504,
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE": 33
  },
  "source_inventory_count": 13024,
  "validation_safe": false
}
```
