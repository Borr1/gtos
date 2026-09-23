# LTF Source Contract Availability Matrix

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_schema_groups_covered": [
    "LTF",
    "baseline-control"
  ],
  "artifact_family": "LTF_SOURCE_CONTRACT_AVAILABILITY_MATRIX",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:37:18Z",
  "live_effect": false,
  "matrix_scope": "source/control contracts only; no LTF result scoring or validation opened",
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
      "approval_gate": "None for source-control reference; future live wiring separate.",
      "availability_status": "CLOSED_AS_M15_BASELINE_ONLY_NOT_LOWER_THAN_DECISION_INTERVAL",
      "capture_group": "LTF",
      "hash_policy": "Already hash-bound by accepted candidate rows and upstream manifests.",
      "parser_requirement": "Use accepted SCID as-of bar parser; no target/result fields.",
      "schema_fields_unlocked": [
        "decision_asof_utc",
        "bar_window_start_utc",
        "bar_window_end_utc",
        "included_bar_hashes"
      ],
      "source_count": 3014,
      "source_family": "accepted_scid_m15_source_control_bars",
      "source_inventory_categories": [
        "SCID_ASOF_CANDIDATE_INPUT_ROWS"
      ]
    },
    {
      "approval_gate": "No raw commit; if new exports are needed, owner Sierra export approval required.",
      "availability_status": "AVAILABLE_SOURCE_CONTROL_FILES_EXIST",
      "capture_group": "LTF",
      "hash_policy": "Small committed CSV/manifest files hashed where under route limit; larger raw roots deferred by manifest metadata.",
      "parser_requirement": "CSV parser must bind alias, timeframe, timestamp convention, and source manifest before joining.",
      "schema_fields_unlocked": [
        "ltf_bar_count",
        "ltf_path_order",
        "ltf_high_low_sequence",
        "ltf_gap_or_missing_bar_flags"
      ],
      "source_count": 150,
      "source_family": "sierra_converted_m1_m5_m15_ohlcv_roots",
      "source_inventory_categories": [
        "SIERRA_CONVERTED_LTF_OHLCV_SOURCE"
      ]
    },
    {
      "approval_gate": "Owner approval required to copy/export or consume raw parquet into a new packet; broker account evidence remains forbidden.",
      "availability_status": "AVAILABLE_IN_ABSOLUTE_PRIOR_ROOT_NOT_CURRENT_WORKTREE",
      "capture_group": "LTF",
      "hash_policy": "Raw parquet hash deferred unless dedicated no-commit hash job is approved; path/size/mtime manifested now.",
      "parser_requirement": "Read-only parquet parser with symbol/date/as-of window; no account/order/deal/position columns.",
      "schema_fields_unlocked": [
        "bid_ask_spread",
        "tick_count",
        "micro_path_order",
        "quote_gap_flags"
      ],
      "source_count": 93,
      "source_family": "prior_production_mt5_tick_parquet_market_context",
      "source_inventory_categories": [
        "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE"
      ]
    },
    {
      "approval_gate": "No raw commit. Dedicated source-hash/extract window job or owner export approval before row materialization.",
      "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
      "capture_group": "LTF",
      "hash_policy": "Large external raw files hash-deferred; metadata and existing source-control inventories hash-bound.",
      "parser_requirement": "SCID binary parser/header proof; bind contract root and inverse/point-value policy before join.",
      "schema_fields_unlocked": [
        "trade_price",
        "bid_volume",
        "ask_volume",
        "volume_profile_bin",
        "footprint_delta"
      ],
      "source_count": 33,
      "source_family": "sierra_scid_time_and_sales",
      "source_inventory_categories": [
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
      ]
    },
    {
      "approval_gate": "Historical rows without exact candidate/duplicate binding remain unavailable; future capture contract required.",
      "availability_status": "AVAILABLE_FOR_FORWARD_OR_CURRENT_SYSTEM_CONTEXT_NOT_HISTORICAL_INTENT_TRUTH",
      "capture_group": "LTF",
      "hash_policy": "Source-control/log metadata hashed or deferred by size; no raw/live dirt committed.",
      "parser_requirement": "JSONL parser must require candidate_input_row_id or duplicate-key binding; weak symbol-time joins stay fail-closed.",
      "schema_fields_unlocked": [
        "candidate_ltf_path_order",
        "prefill_delivery_path",
        "candidate_path_contract_status"
      ],
      "source_count": 18,
      "source_family": "path_context_shadow_logs",
      "source_inventory_categories": [
        "PATH_CONTEXT_SHADOW_SOURCE"
      ]
    },
    {
      "approval_gate": "None for source-control context; future schema wiring is separate.",
      "availability_status": "AVAILABLE_CONTEXT_ONLY",
      "capture_group": "baseline-control",
      "hash_policy": "Small CSV/JSONL status artifacts hash-bound or metadata-manifested.",
      "parser_requirement": "Join by symbol/session/as-of timestamp only; never by post-outcome state.",
      "schema_fields_unlocked": [
        "session_volatility_bucket",
        "sweep_status",
        "session_context_flags"
      ],
      "source_count": 7,
      "source_family": "session_volatility_context_logs",
      "source_inventory_categories": [
        "SESSION_VOLATILITY_CONTEXT_SOURCE"
      ]
    }
  ],
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "validation_safe": false
}
```
