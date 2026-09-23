# Source Inventory Hash Deferral Audit

```json
{
  "artifact_family": "source_inventory_hash_deferral_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "deferred_without_reason_count": 0,
  "deferred_without_reason_samples": [],
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "expected_hash_status_counts": {
    "HASHED_NOW": 361,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 126,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 3,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 354
  },
  "expected_source_categories": [
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
    "LOCAL_OHLCV_LTF_OR_M15_CSV_SOURCE",
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
    "OTHER_RELEVANT_SOURCE_METADATA",
    "PATH_CONTEXT_SHADOW_SOURCE",
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
    "SESSION_VOLATILITY_CONTEXT_SOURCE",
    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE",
    "SIERRA_DEPTH_MARKET_DEPTH_SOURCE",
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
    "SIERRA_SOURCE_CONTROL_LEDGER_OR_PARSER",
    "SOURCE_CONTROL_SUPPORTING_ARTIFACT"
  ],
  "forbidden_broker_account_order_history_deal_position_sources_consumed": 0,
  "generated_at_utc": "2026-05-12T07:45:56Z",
  "hash_drift_rebound_repair_count": 19,
  "hash_drift_rebound_repair_samples": [
    {
      "builder_sha256": "18bafd0d4195584c110e4849825342ac887ec6cebd31d70c7d07eb3ff7ea8e1e",
      "g12_rebound_sha256": "3d9db327015192e2bc415411fe8fab8d6be061d53197364f3dda63414341e822",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/databento_live_trigger_decisions.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "a5d1eaa7c37d3ff66d982bb19e4de021979ece8eb2165e3900912fb638e7f009",
      "g12_rebound_sha256": "37b0f0f51e35de6a3bea7cf53e66832a76b6a9b7fe9c4d8e0d15f0d074d02013",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/nas100_orderflow_adverse_selection_status.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "48b8aa6b4861134e80ca324f461823adafc593b21bb1cac6172b3bf58bcb61a3",
      "g12_rebound_sha256": "4ca64880213020ae614cd53835803953b0b30a6e5b3d3f93159aca6112d3e7a9",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/orderflow_primitives_status.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "3e2540846b4093c302633617cd2a711f720aa01c083b31d8a740f0c347b5452b",
      "g12_rebound_sha256": "c6a5b98ba31d66ac3542941cd61afde0c1a8613092b8a8521016293cdc87ba4d",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/sierra_confluence_source_status.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "706275d7ae8c1bc16a997e7c65d5438d2b462c4efc947dfdf006ea8a3b1a42aa",
      "g12_rebound_sha256": "97be507117d6275d94091f3cdf1ead232aab15e88514dd6fcb2716ff2209e2a9",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/sierra_depth_enrichment_status.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "182c648a9826d51ddb081d914e6ec49cc6da0d945f6bda3578a71d74cc1582a4",
      "g12_rebound_sha256": "9baa0e1b29ec56ffc6e89f88150cddf7e5963f578effbfbd87bf0c21da341b84",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/sierra_depth_feature_snapshots.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "d35fdce73f61d6d7f50eaf4e994a38262de51541cf115f1ac91dd98bb2b41b54",
      "g12_rebound_sha256": "34bf50536698e67f5afb600d5f20062365ccfd8f03561bdb4df755e7cb01ea76",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/candidate_ltf_path_order.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "bc6d16545eb15356118a45214a13d4c78f9be591521889b2d7b6b8f2228a1a15",
      "g12_rebound_sha256": "78cd13b53c0491fdcb848ff0594468982fb61c8995f89f0ea9bbda6a2ae53211",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/candidate_path_contract_audit.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "f5e70d88b59ddef52dac9f77532956072c1567e8bcaa0c60970e8a0b08d9dd7a",
      "g12_rebound_sha256": "a7ec01f91ff7a0521f90be0425f37c74b40dc3752d0e967c4c6525711264b520",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/prefill_delivery_path.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "1eb428e68723ac315003a0324b4c8a40d8cafbf618355455f7056d116c0fbca2",
      "g12_rebound_sha256": "15f1e663867b291426d62235e400353f2de15858246804d13edb895406f8eaf8",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/prefill_delivery_path_resolutions.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "f1b8d346b942d1d6f5f0a12e5d954e270b4d4b4ce9be953c9cba1cdd4eb25174",
      "g12_rebound_sha256": "1d17e137888deaaa5d94ba30dc8807c1fc747b1b66700b7ede2bf01ef80a44b2",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/proxy_blocker_status.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "43b893873409e92334ad3a830a13f47e61afe9929893cd4ee799326a6b3a92e9",
      "g12_rebound_sha256": "cd3f922c03e59439b0c1c434c92e9dd1f3a6f6662dc62b208435efe94b282ca5",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs/sierra_proxy_registry_status.jsonl",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "f59b3ff9a543c3a8b5880e90ff752ba5188080cb854c3411706335623e953d33",
      "g12_rebound_sha256": "9c746cb7e099edc4b27df4b7d83255f6c07f5e3913d6d9b3d4a2f5d9ff4a6af8",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/GBPJPY/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "736c62545d3c5be07c45698c2b4c296c6e01c25e5a2100d7c7459b2555bef344",
      "g12_rebound_sha256": "9e37f6d87bbe71bd38f417bf460c1e3f4b27abec17baa4c44b209d01629d9165",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/GBPUSD/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "97bd66bc3694975c21cd85c572c683ad27a20925b2b906000e260dc66c46ab1a",
      "g12_rebound_sha256": "64dab0b2673ee15ab9c0856f3a06ad29d176c0f1f22b549f1d6a3a24afbfed3a",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/NAS100/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "5941dd6d20f7bc7bca5dcb7a54c9d08c2344ae8519b7a815bc925e7674e7898e",
      "g12_rebound_sha256": "2197afd0e0f0d913f2cdbd057c66876e228bc2b6c2143e9accfae4efe24fda6a",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/US30_cash/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "8119d76d3f775df42bd36c5aa3c03c1535b0bd1d84444eff245cf22d70234f78",
      "g12_rebound_sha256": "55c4e6105a02a2e4141cf42efb05b6c6b0add10e2161e583bb35e8b22f69c395",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/USDJPY/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "b2c1721022df56fc5efc1cc5c17d9c9dc03b82bc861c03531d1d3cda9942c52a",
      "g12_rebound_sha256": "b36a644e466155a4ac3a8e1baafd50fef5d6eb4dc39b32e0f1b406010203c8fd",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/XAGUSD/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    },
    {
      "builder_sha256": "e140fb27e539a88e1b1c6bcd93b3e10317c6262160fce690f0a9ef30796bd67e",
      "g12_rebound_sha256": "5308583430322fc8c0142eb445b2324faf21b1db0ea69cebd604e40783c90f00",
      "path": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks/XAUUSD/.state.json",
      "repair_class": "MUTABLE_EXTERNAL_CONTEXT_SOURCE_REBOUND_IN_G12"
    }
  ],
  "hash_mismatch_count": 0,
  "hash_mismatch_samples": [],
  "hash_status_counts_recomputed": {
    "HASHED_NOW": 361,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 126,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 3,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 354
  },
  "live_effect": false,
  "missing_files_with_hash_count": 0,
  "missing_files_with_hash_samples": [],
  "missing_hash_or_deferral_count": 0,
  "missing_hash_or_deferral_samples": [],
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
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "source_category_counts_recomputed": {
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE": 93,
    "LOCAL_OHLCV_LTF_OR_M15_CSV_SOURCE": 48,
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 205,
    "OTHER_RELEVANT_SOURCE_METADATA": 53,
    "PATH_CONTEXT_SHADOW_SOURCE": 15,
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 9,
    "SESSION_VOLATILITY_CONTEXT_SOURCE": 7,
    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 150,
    "SIERRA_DEPTH_MARKET_DEPTH_SOURCE": 152,
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE": 33,
    "SIERRA_SOURCE_CONTROL_LEDGER_OR_PARSER": 59,
    "SOURCE_CONTROL_SUPPORTING_ARTIFACT": 20
  },
  "source_inventory_count_recomputed": 844,
  "source_inventory_hash_deferral_ok": true,
  "validation_safe": false
}
```
