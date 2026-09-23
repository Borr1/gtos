# Mt5 Field Blocker Reaudit

```json
{
  "artifact_family": "mt5_field_blocker_reaudit",
  "blocker_summary": "SCID carries source-native timestamp, OHLC, total volume, bid volume, and ask volume. It does not carry MT5 bid quote, ask quote, or flags; time_msc, last, volume, and broker_symbol remain proxy-only.",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "derivable_without_leakage_fields": [
    "time_utc",
    "source_symbol",
    "source_file_sha256"
  ],
  "field_rows": [
    {
      "blocker_class": "NONE_FOR_TIMESTAMP_VALUE",
      "field": "time_utc",
      "mt5_equivalence_status": "timestamp value exists, but source lineage is Sierra-native rather than MT5 broker-native",
      "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
      "satisfies_mt5_tick_contract_field": true,
      "scid_evidence": "SCID DTDateTime microsecond timestamp"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "time_msc",
      "mt5_equivalence_status": "not MT5-native time_msc; conversion would be a source timestamp proxy",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID timestamp can be converted to milliseconds"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "bid",
      "mt5_equivalence_status": "OHLC or bid_volume cannot be substituted for MT5 bid quote",
      "presence_status": "ABSENT",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID has OHLC price fields and bid_volume, not bid quote price"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "ask",
      "mt5_equivalence_status": "OHLC or ask_volume cannot be substituted for MT5 ask quote",
      "presence_status": "ABSENT",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID has OHLC price fields and ask_volume, not ask quote price"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "last",
      "mt5_equivalence_status": "market-activity proxy only; not MT5 last field proof",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID close is a source-native record close price"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "volume",
      "mt5_equivalence_status": "source-native footprint volume, not MT5 tick volume proof",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID total_volume plus bid_volume and ask_volume"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "flags",
      "mt5_equivalence_status": "absent",
      "presence_status": "ABSENT",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "No SCID field carries MT5 tick flags"
    },
    {
      "blocker_class": "NONE_FOR_METADATA_VALUE",
      "field": "source_symbol",
      "mt5_equivalence_status": "source metadata only",
      "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
      "satisfies_mt5_tick_contract_field": true,
      "scid_evidence": "Derivable from XAUUSD.scid filename and owner request"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "broker_symbol",
      "mt5_equivalence_status": "same text symbol does not prove MT5 broker_symbol lineage",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "Filename says XAUUSD but source is Sierra, not MT5 broker export"
    },
    {
      "blocker_class": "NONE_FOR_SOURCE_HASH_VALUE",
      "field": "source_file_sha256",
      "mt5_equivalence_status": "hash exists for SCID source, not for missing MT5 parquet",
      "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
      "satisfies_mt5_tick_contract_field": true,
      "scid_evidence": "Raw SCID SHA256 is computed by this audit"
    }
  ],
  "generated_at_utc": "2026-05-10T11:13:20Z",
  "hard_absent_fields": [
    "bid",
    "ask",
    "flags"
  ],
  "live_effect": false,
  "mt5_tick_contract_satisfied": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_only_non_equivalent_fields": [
    "time_msc",
    "last",
    "volume",
    "broker_symbol"
  ],
  "required_mt5_tick_fields": [
    "time_utc",
    "time_msc",
    "bid",
    "ask",
    "last",
    "volume",
    "flags",
    "source_symbol",
    "broker_symbol",
    "source_file_sha256"
  ],
  "route_id": "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_v1",
  "substitution_check": {
    "mt5_spread_or_cost_proof_opened": false,
    "scid_bid_ask_volume_substituted_for_mt5_bid_or_ask_quotes": false,
    "scid_ohlc_substituted_for_mt5_bid_or_ask": false
  },
  "target_route_comparison": {
    "comparison_status": "MATCH",
    "mismatches": []
  },
  "target_route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "validation_safe": false
}
```
