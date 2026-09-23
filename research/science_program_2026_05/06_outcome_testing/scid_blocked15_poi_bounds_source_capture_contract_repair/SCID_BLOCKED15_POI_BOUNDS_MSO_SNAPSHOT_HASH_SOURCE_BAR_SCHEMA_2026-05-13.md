# MSO Snapshot Hash Source Bar Schema

```json
{
  "artifact_family": "mso_snapshot_hash_source_bar_schema",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY",
  "generated_at_utc": "2026-05-13T03:45:00Z",
  "hash_policy": {
    "mso_snapshot_hash": "sha256(canonical mso_snapshot_commitment)",
    "source_bar_set_hash": "sha256(canonical source_bar_refs)",
    "source_hash": "sha256(canonical row without source_hash)"
  },
  "live_effect": false,
  "mso_snapshot_commitment_schema": {
    "detected_poi_refs": [
      {
        "poi_detection_asof_utc": "date-time <= decision_asof_utc",
        "poi_detection_code_hash": "sha256",
        "poi_detection_rule_version": "string",
        "poi_id": "string",
        "poi_lower_bound": "number or null",
        "poi_mechanism_family": [
          "ob_zone",
          "fvg_gap",
          "breaker_zone",
          "swing_boundary",
          "liquidity_sweep_zone",
          "round_number_band",
          "volume_profile_zone",
          "geometry_envelope",
          "macro_calendar_context_zone",
          "other_source_bound_poi",
          "none"
        ],
        "poi_source_bar_ids": "array of source_bar_ref.source_bar_id",
        "poi_source_timeframe": "string",
        "poi_subtype": "string or null",
        "poi_type_enum_ob_fvg_breaker_swing_other_none": [
          "ob",
          "fvg",
          "breaker",
          "swing",
          "other",
          "none"
        ],
        "poi_upper_bound": "number or null"
      }
    ],
    "market_state_builder_version": "string",
    "market_state_input_hash": "sha256",
    "mso_snapshot_asof_utc": "date-time <= decision_asof_utc",
    "mso_snapshot_schema_version": "SCID_POI_BOUNDS_MSO_SNAPSHOT_COMMITMENT_V1",
    "selected_poi_id": "string or null; null allowed only with POI_BOUNDS_NO_POI_SOURCE_SAFE",
    "source_bar_refs": [
      {
        "bar_end_exclusive_utc": "date-time <= decision_asof_utc",
        "bar_open_utc": "date-time",
        "payload_redaction_state": "HASH_ONLY_NO_RAW_MARKET_BLOB",
        "source_bar_hash": "sha256 over external/source-local bar payload, not raw payload committed here",
        "source_bar_id": "string; stable source-local id",
        "source_file_pointer_or_cache_id": "string; no raw blob commit",
        "source_instrument": "string",
        "source_timeframe": "string"
      }
    ]
  },
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
  "raw_market_blob_policy": "Only source pointers and hashes are committed in this route; raw OHLC/tick/depth blobs are forbidden.",
  "route_id": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
  "schema_version": "scid_blocked15_poi_bounds_capture_contract_v1",
  "source_bar_ref_schema": {
    "bar_end_exclusive_utc": "date-time <= decision_asof_utc",
    "bar_open_utc": "date-time",
    "payload_redaction_state": "HASH_ONLY_NO_RAW_MARKET_BLOB",
    "source_bar_hash": "sha256 over external/source-local bar payload, not raw payload committed here",
    "source_bar_id": "string; stable source-local id",
    "source_file_pointer_or_cache_id": "string; no raw blob commit",
    "source_instrument": "string",
    "source_timeframe": "string"
  },
  "validation_safe": false
}
```
