# Source Materialization Opportunity Ledger

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "artifact_family": "SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY",
  "field_status_rows_inspected": 257,
  "generated_at_utc": "2026-05-13T01:20:09Z",
  "hash_status_counts": {
    "HASHED_NOW": 11932,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 180,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 491,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 421
  },
  "live_effect": false,
  "local_root_probe": [
    {
      "exists": true,
      "readable": true,
      "root": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
      "sample_count": 8,
      "samples": [
        "GBPJPY",
        "GBPUSD",
        "NAS100",
        "README.md",
        "US30_cash",
        "USDJPY",
        "XAGUSD",
        "XAUUSD"
      ]
    },
    {
      "exists": true,
      "readable": true,
      "root": "C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots",
      "sample_count": 7,
      "samples": [
        "sierra_6b_to_gbpusd_pilot_20260504",
        "sierra_6j_to_usdjpy_pilot_20260504",
        "sierra_first_wave_bounded_conversion_20260504",
        "sierra_nq_to_nas100_pilot_20260504",
        "sierra_si_to_xagusd_pilot_20260504",
        "sierra_xauusd_scid_to_xauusd_pilot_20260504",
        "sierra_ym_to_us30_cash_pilot_20260504"
      ]
    },
    {
      "exists": true,
      "readable": true,
      "root": "C:/Users/MSI/Documents/ai-trading-agent/data/sierrachart_exports",
      "sample_count": 3,
      "samples": [
        "NQM26-CME_2026-04-15_1300_1400_scid.csv",
        "pre_cua_scid_inventory_2026-05-03.json",
        "scid_inventory_2026-05-03.json"
      ]
    },
    {
      "exists": true,
      "readable": true,
      "root": "C:/Users/MSI/Documents/ai-trading-agent/data/external",
      "sample_count": 5,
      "samples": [
        "features",
        "normalized",
        "raw",
        "status",
        "validation"
      ]
    },
    {
      "exists": true,
      "readable": true,
      "root": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
      "sample_count": 10,
      "samples": [
        ".contaminated_backup",
        ".d1_bias_lag_state.15480.tmp",
        ".d1_bias_lag_state.json",
        ".displacement_state.json",
        ".dumb_baseline_state.GBPJPY.json",
        ".dumb_baseline_state.GBPUSD.json",
        ".dumb_baseline_state.json",
        ".dumb_baseline_state.NAS100.json",
        ".dumb_baseline_state.US30_cash.json",
        ".dumb_baseline_state.USDJPY.json"
      ]
    },
    {
      "exists": true,
      "readable": true,
      "root": "C:/SierraChart/Data",
      "sample_count": 10,
      "samples": [
        "2TargetsWithBEStop.twconfig",
        "2TargetsWithCommonStop.twconfig",
        "6AM26-CME.scid",
        "6BM26-CME.scid",
        "6CM26-CME.scid",
        "6EM26-CME.scid",
        "6JM26-CME.scid",
        "6SM26-CME.scid",
        "AAPL.scid",
        "AMZN-NQTV.scid"
      ]
    },
    {
      "exists": true,
      "readable": true,
      "root": "C:/tmp",
      "sample_count": 10,
      "samples": [
        "a2_test",
        "all_fills.csv",
        "cascade_full_template.txt",
        "debug_wilcoxon.log",
        "debug_wilcoxon2.log",
        "dumb_baseline_sanity",
        "g0_fpb_sealed_0.pyc",
        "g0_fpb_sealed_1.pyc",
        "g0_fpb_sealed_2.pyc",
        "g12_scid_impl_audit_tmp_codex"
      ]
    }
  ],
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
  "opportunities": [
    {
      "inventory_rows_available": 750,
      "materialization_action": "Build source-control LTF parser that emits as-of path descriptors, bars-present flags, source pointer/hash fields, timezone/session convention, and gap flags.",
      "opportunity_id": "LTF_MARKET_DATA_ASOF_MATERIALIZATION",
      "route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
      "same_evidence_class_closure": "Reduced to exact parser builder prompt; no result labels opened.",
      "source_inventory_categories": [
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE",
        "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
        "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT"
      ],
      "unblocks_status": "SOURCE_EXISTS_NEEDS_PARSER"
    },
    {
      "inventory_rows_available": 5171,
      "materialization_action": "Build G12-ready proxy contracts for source family, contract/month, calendar, roll/inverse policy, source hash/as-of, and explicit non-equivalence to broker CFD truth.",
      "opportunity_id": "ORDERFLOW_PROXY_CONTEXT_CONTRACTS",
      "proxy_rows_context_only": 7,
      "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
      "same_evidence_class_closure": "Reduced to exact proxy contract prompt; no broker-native CFD truth claims opened.",
      "source_family_rows": [
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
      "source_inventory_categories": [
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
      ],
      "unblocks_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "inventory_rows_available": 6172,
      "materialization_action": "Search explicit source-safe logs for historical proof; if absent, create prospective capture contracts for intended entry/stop/target/framework fields with verifier fixtures.",
      "opportunity_id": "PROSPECTIVE_NON_GENERATABLE_CAPTURE",
      "route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
      "same_evidence_class_closure": "Classified as non-generatable from price/proxy alone; next prompt owns source-safe recovery or future capture.",
      "source_inventory_categories": [
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT",
        "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE"
      ],
      "unblocks_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE"
    },
    {
      "inventory_rows_available": 6202,
      "materialization_action": "Freeze baseline seed, duplicate policy, denominator ownership, and no-outcome controls as packet metadata before any result gate.",
      "opportunity_id": "BASELINE_CONTROL_PACKET_ASSIGNMENT",
      "route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
      "same_evidence_class_closure": "Reduced to exact baseline/control prompt.",
      "source_inventory_categories": [
        "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT",
        "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT"
      ],
      "unblocks_status": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS"
    },
    {
      "inventory_rows_available": 912,
      "materialization_action": "Create exact no-commit hash/export manifest and owner approval text for raw parse scope without committing raw market blobs.",
      "opportunity_id": "NO_COMMIT_HASH_AND_EXPORT_MANIFESTS",
      "route_id": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE",
      "same_evidence_class_closure": "Reduced to exact access/export prompt.",
      "source_inventory_categories": [
        "HASH_DEFERRED_LARGE_SUPPORTING_FILE",
        "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE"
      ],
      "unblocks_status": "HASH_OR_ACCESS_REQUIREMENT"
    }
  ],
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_equivalence_rows_inspected": 7,
  "requirement_rows_inspected": 8,
  "route_id": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS",
  "schema_version": "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1",
  "searched_roots_from_card_fields": [
    "C:/SierraChart/Data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/external",
    "C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots",
    "C:/Users/MSI/Documents/ai-trading-agent/data/sierrachart_exports",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_READY_8_ROUTE_LEDGER_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_FAIL_CLOSED_MISSING_FIELD_LEDGER_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_2026-05-12.json"
  ],
  "searched_roots_from_card_fields_count": 14,
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
  "source_family_rows_inspected": 4,
  "source_inventory_count": 13024,
  "source_status_rows_inspected": 17,
  "validation_safe": false
}
```
