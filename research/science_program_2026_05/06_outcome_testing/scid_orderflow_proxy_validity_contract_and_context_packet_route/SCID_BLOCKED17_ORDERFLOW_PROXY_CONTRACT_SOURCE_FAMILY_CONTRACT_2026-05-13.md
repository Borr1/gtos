# Source Family Contract

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

```json
{
  "artifact_family": "SOURCE_FAMILY_CONTRACT",
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "contract_count": 4,
  "contract_global_rules": [
    "Every packet row must carry source_family, source_file_pointer_or_vendor_cache_id, source_hash or accepted deferral id, proxy_mapping_version, contract root/month or same-market root, publication_or_capture_asof_utc, parser_version, and non_equivalence_label.",
    "Every proxy row is context/control only until a separate G12/G0 route accepts transfer/equivalence and a separate result lane explicitly opens scoring.",
    "Parser must fail closed on missing contract, roll, session calendar, timezone, inverse-price policy, source hash/deferral, or non-equivalence label.",
    "No raw .depth/.scid/vendor market blob may be committed by this route."
  ],
  "contracts": [
    {
      "access_readiness": "READY_FOR_NO_COMMIT_WINDOW_EXTRACTION_AFTER_OWNER_APPROVES_RAW_PARSE_SCOPE",
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "broker_native_cfd_truth_claim_allowed": false,
      "contract_id": "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_EXACT_RAW_PARSE_SCOPE_REQUIRED",
      "exact_access_requirement_if_unresolved": "Run a no-commit Sierra .depth window inventory/parser job for declared contract/date windows; record path, size, mtime, sha256 or accepted hash deferral; do not commit raw .depth.",
      "invalid_contexts": [
        "broker-native CFD truth claim",
        "broker account/order/history/deal/position evidence",
        "result scoring, validation, promotion, or performance interpretation",
        "post-decision or post-cancel source selection",
        "source pointer without hash or G12-accepted hash deferral",
        "missing non-equivalence label",
        "broker fill queue or broker spread truth",
        "continuous-contract heatmap used as exact contract depth",
        "Sunday/holiday depth sample interpreted as active-session state without flags"
      ],
      "local_metadata_observations": [
        {
          "counts_by_suffix": {
            ".depth": 165,
            ".scid": 33
          },
          "exists": true,
          "path": "C:/SierraChart",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": true,
          "root_id": "sierra_root"
        },
        {
          "counts_by_suffix": {
            ".depth": 0,
            ".scid": 33
          },
          "exists": true,
          "path": "C:/SierraChart/Data",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": false,
          "root_id": "sierra_data"
        },
        {
          "counts_by_suffix": {
            ".depth": 165
          },
          "exists": true,
          "path": "C:/SierraChart/Data/MarketDepthData",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": false,
          "root_id": "sierra_market_depth"
        }
      ],
      "may_score_results_now": false,
      "parser_acceptance_criteria": [
        "record-size and endian proof",
        "contract root and contract month parsed from file name",
        "exchange date and UTC conversion rule frozen",
        "records selected only where source event time <= decision_asof_utc",
        "clear-book-only, closed-market, gap, and stale-depth flags emitted",
        "path, size, mtime, and sha256 or G12-accepted hash-deferral id attached"
      ],
      "roll_session_asof_rule": "Use exact active contract/date files, not continuous futures. Bind exchange session calendar, feed delay label, and UTC conversion before any candidate join.",
      "schema_fields_unlocked_context_only": [
        "best_bid_ask_depth",
        "depth_imbalance",
        "ladder_voids",
        "absorption_proxy"
      ],
      "source_family": "sierra_depth_market_depth",
      "source_inventory_categories": [
        "SIERRA_DEPTH_MARKET_DEPTH_SOURCE"
      ],
      "source_scope": "Sierra .depth market depth files under local Sierra roots; first-wave depth inventory is source-status evidence only.",
      "staleness_policy": "Fail closed when the latest usable depth update before decision_asof_utc is older than the route-declared threshold, when the file is clear-book-only for the active window, or when the file was still being written without a no-change completion check.",
      "upstream_hash_policy": "Large external raw files hash-deferred; path/size/mtime and existing parser specs hashed.",
      "upstream_parser_requirement": "Sierra depth parser with record-size/endian proof, contract/date binding, and as-of cut.",
      "upstream_proxy_boundary": "Depth is futures/exchange ladder context, not broker-native CFD queue truth.",
      "upstream_source_count": 152,
      "useful_contexts": [
        "depth availability status",
        "queue/depth context features",
        "liquidity void or absorption proxy context",
        "parser fixture and future context packet fields"
      ]
    },
    {
      "access_readiness": "READY_FOR_CONTRACT_WINDOW_EXTRACTION_AFTER_HASH_OR_EXPORT_GATE",
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "broker_native_cfd_truth_claim_allowed": false,
      "contract_id": "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_EXACT_SCID_PARSE_REQUIREMENT",
      "exact_access_requirement_if_unresolved": "Run a no-commit SCID parser over declared symbol/windows; attach parser version, scale proof, path, size, mtime, and hash/deferral id.",
      "invalid_contexts": [
        "broker-native CFD truth claim",
        "broker account/order/history/deal/position evidence",
        "result scoring, validation, promotion, or performance interpretation",
        "post-decision or post-cancel source selection",
        "source pointer without hash or G12-accepted hash deferral",
        "missing non-equivalence label",
        "centralized spot FX or broker CFD volume truth",
        "same-market indicative quote data treated as broker execution truth"
      ],
      "local_metadata_observations": [
        {
          "counts_by_suffix": {
            ".depth": 165,
            ".scid": 33
          },
          "exists": true,
          "path": "C:/SierraChart",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": true,
          "root_id": "sierra_root"
        },
        {
          "counts_by_suffix": {
            ".depth": 0,
            ".scid": 33
          },
          "exists": true,
          "path": "C:/SierraChart/Data",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": false,
          "root_id": "sierra_data"
        },
        {
          "counts_by_suffix": {
            ".depth": 165
          },
          "exists": true,
          "path": "C:/SierraChart/Data/MarketDepthData",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": false,
          "root_id": "sierra_market_depth"
        }
      ],
      "may_score_results_now": false,
      "parser_acceptance_criteria": [
        "SCID timestamp and price scaling decoded by versioned parser",
        "bid/ask/volume fields separated from derived features",
        "same-market symbols separated from futures proxy symbols",
        "source event time <= decision_asof_utc",
        "sparse/thin symbol warnings emitted",
        "path, size, mtime, and sha256 or accepted hash deferral attached"
      ],
      "roll_session_asof_rule": "Bind symbol root and contract month when futures; bind same-market source label when non-futures. Use UTC and exchange/session calendar, not local wall-clock labels.",
      "schema_fields_unlocked_context_only": [
        "bid_volume",
        "ask_volume",
        "delta",
        "volume_profile",
        "aggression_proxy"
      ],
      "source_family": "sierra_scid_footprint_bid_ask_volume",
      "source_inventory_categories": [
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
      ],
      "source_scope": "Sierra .scid intraday files and same-market/futures roots; source-status evidence only until parser G12 accepts field semantics.",
      "staleness_policy": "Fail closed when no SCID bar/tick exists inside the declared pre-decision window, when sparse-symbol quality flags are action-required, or when parser scale/version is unknown.",
      "upstream_hash_policy": "Large raw SCID hash deferred unless no-commit hash job approved.",
      "upstream_parser_requirement": "SCID parser must separate same-market CFD-like symbols from futures proxy roots.",
      "upstream_proxy_boundary": "Footprint context is source-transfer context only unless same-market source is explicitly registered.",
      "upstream_source_count": 33,
      "useful_contexts": [
        "bid/ask volume context",
        "delta and volume-profile context",
        "aggression proxy context",
        "same-market availability status where registered"
      ]
    },
    {
      "access_readiness": "CACHED_SOURCE_CONTROL_ONLY_READY_NEW_PULL_BLOCKED",
      "availability_status": "SOURCE_CONTROL_ARTIFACTS_AVAILABLE_NO_NEW_API_CALL_OPENED",
      "broker_native_cfd_truth_claim_allowed": false,
      "contract_id": "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_CACHED_ONLY_NEW_PULL_BLOCKED",
      "exact_access_requirement_if_unresolved": "For a missing window, write a pre-call manifest with dataset, schema, symbol, UTC window, expected fields, expected cost/free-credit status, no-leak policy, and owner approval requirement before any fetch.",
      "invalid_contexts": [
        "broker-native CFD truth claim",
        "broker account/order/history/deal/position evidence",
        "result scoring, validation, promotion, or performance interpretation",
        "post-decision or post-cancel source selection",
        "source pointer without hash or G12-accepted hash deferral",
        "missing non-equivalence label",
        "new Databento call without owner-approved pre-call manifest",
        "vendor futures depth/trades used as broker account or CFD execution truth"
      ],
      "local_metadata_observations": [
        {
          "counts_by_suffix": {
            ".csv": 0,
            ".depth": 0,
            ".json": 294,
            ".parquet": 0,
            ".scid": 0
          },
          "exists": true,
          "path": "C:/Users/MSI/Documents/ai-trading-agent/data/external",
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": true,
          "root_id": "absolute_external_source_cache"
        }
      ],
      "may_score_results_now": false,
      "parser_acceptance_criteria": [
        "dataset, schema, symbol, window, and source cache path present",
        "cost/free-credit status present for any future fetch",
        "source artifact hash attached",
        "records selected only where source event time <= decision_asof_utc",
        "MBO/MBP/trades schema family explicitly labeled"
      ],
      "roll_session_asof_rule": "Use declared Databento dataset symbol and futures contract month or continuous symbol mapping; freeze the mapping before joins.",
      "schema_fields_unlocked_context_only": [
        "mbo_event_count",
        "mbp_depth_features",
        "cost_cap_status",
        "dataset_symbol_map"
      ],
      "source_family": "databento_cached_or_declared_orderflow_artifacts",
      "source_inventory_categories": [
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL"
      ],
      "source_scope": "Committed Databento/orderflow artifacts and declared request manifests only; no new paid/API pull is opened here.",
      "staleness_policy": "Fail closed when the cached artifact lacks window, schema, source hash, or created_at/source as-of metadata; request rows alone are not market data.",
      "upstream_hash_policy": "Committed JSON/MD/PY artifacts hashed; raw vendor blobs absent or hash-deferred.",
      "upstream_parser_requirement": "Only cached/artifact paths may be referenced; any new Databento call needs a pre-call budget/free-credit manifest and owner approval.",
      "upstream_proxy_boundary": "Databento futures depth/trades are not broker-native CFD execution/account truth.",
      "upstream_source_count": 207,
      "useful_contexts": [
        "cached MBP/MBO/trades source-control fields",
        "dataset symbol mapping context",
        "cost-cap and request-manifest status",
        "future stratified proxy parity packet inputs"
      ]
    },
    {
      "access_readiness": "READY_FOR_CONTEXT_CONTRACTS_NOT_FOR_VALIDATION",
      "availability_status": "AVAILABLE_CONTEXT_ONLY_WITH_NON_EQUIVALENCE_LEDGER_REQUIRED",
      "broker_native_cfd_truth_claim_allowed": false,
      "contract_id": "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1",
      "contract_status": "CONTRACT_ATTACHED_FAIL_CLOSED_MAPPING_REQUIRED",
      "exact_access_requirement_if_unresolved": "Materialize the mapping registry row from committed source-control artifacts or append a prospective proxy-mapping capture requirement; do not infer mapping from price correlation.",
      "invalid_contexts": [
        "broker-native CFD truth claim",
        "broker account/order/history/deal/position evidence",
        "result scoring, validation, promotion, or performance interpretation",
        "post-decision or post-cancel source selection",
        "source pointer without hash or G12-accepted hash deferral",
        "missing non-equivalence label",
        "proxy transfer accepted from price correlation alone",
        "mapping row used without current contract month and non-equivalence caveat"
      ],
      "local_metadata_observations": [
        {
          "counts_by_suffix": {
            ".jsonl": 99
          },
          "exists": true,
          "path": "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
          "proxy_related_logs": [
            "gbpjpy_proxy_gap_status.jsonl",
            "proxy_blocker_status.jsonl",
            "sierra_proxy_registry_status.jsonl"
          ],
          "raw_blob_committed": false,
          "raw_content_read": false,
          "recursive_count": false,
          "root_id": "absolute_shadow_logs"
        }
      ],
      "may_score_results_now": false,
      "parser_acceptance_criteria": [
        "source symbol and proxy symbol present",
        "contract root/month or same-market root present",
        "roll rule and session calendar present",
        "timezone and inverse-price policy present where applicable",
        "non-equivalence label present",
        "mapping version and source hash attached"
      ],
      "roll_session_asof_rule": "Fail closed unless mapping version, roll calendar, exchange session calendar, and inverse-price convention are frozen before use.",
      "schema_fields_unlocked_context_only": [
        "proxy_group",
        "contract_root",
        "basis_caveat",
        "inverse_contract_flag",
        "blocked_mapping_reason"
      ],
      "source_family": "proxy_mapping_registry_and_blocker_logs",
      "source_inventory_categories": [
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL"
      ],
      "source_scope": "Committed proxy mapping rows, proxy blocker/status logs, and source-control registries; not market data by itself.",
      "staleness_policy": "Fail closed when mapping source timestamp predates a contract roll, when registry rows conflict, or when source-status logs are action-required/stale.",
      "upstream_hash_policy": "Source-control rows hash-bound where small; runtime logs metadata-manifested.",
      "upstream_parser_requirement": "Registry parser must fail closed if proxy mapping lacks source, contract, roll, timezone, or inverse-price policy.",
      "upstream_proxy_boundary": "All proxy rows remain context-only and not broker-native CFD truth until separate transfer validation exists.",
      "upstream_source_count": 51,
      "useful_contexts": [
        "proxy eligibility flags",
        "inverse-contract flags",
        "basis caveats",
        "blocked mapping reasons"
      ]
    }
  ],
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_requirement_surface_count": 72,
  "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
  "schema_version": "scid_blocked17_orderflow_proxy_contract_v1",
  "source_family_total_upstream_source_count": 443,
  "validation_safe": false
}
```
