# MT5 Tick Contract Field Comparison Audit

Route: `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
Terminal posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "mt5_tick_contract_field_comparison_audit",
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
      "mt5_equivalence_status": "UTC timestamp exists but is Sierra source-native, not MT5 broker-native",
      "mt5_tick_contract_meaning": "UTC timestamp attached to the MT5 tick row",
      "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
      "satisfies_mt5_tick_contract_field": true,
      "scid_evidence": "SCID DTDateTime microsecond timestamp"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "time_msc",
      "mt5_equivalence_status": "not MT5-native time_msc; conversion would be source timestamp proxy",
      "mt5_tick_contract_meaning": "MT5 millisecond broker tick timestamp",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID timestamp can be converted to milliseconds"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "bid",
      "mt5_equivalence_status": "open/high/low/close and bid_volume cannot be substituted for bid quote",
      "mt5_tick_contract_meaning": "bid quote price",
      "presence_status": "ABSENT",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID has OHLC price fields and bid_volume, not bid quote price"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "ask",
      "mt5_equivalence_status": "open/high/low/close and ask_volume cannot be substituted for ask quote",
      "mt5_tick_contract_meaning": "ask quote price",
      "presence_status": "ABSENT",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID has OHLC price fields and ask_volume, not ask quote price"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "last",
      "mt5_equivalence_status": "SCID close can be a market-activity price proxy but not MT5 last field proof",
      "mt5_tick_contract_meaning": "MT5 tick last price field",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID close is a source-native record close price"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "volume",
      "mt5_equivalence_status": "SCID record volume is source-native footprint volume, not MT5 tick volume proof",
      "mt5_tick_contract_meaning": "MT5 tick volume field",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "SCID total_volume plus bid_volume and ask_volume"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "flags",
      "mt5_equivalence_status": "absent",
      "mt5_tick_contract_meaning": "MT5 tick flags bitmask",
      "presence_status": "ABSENT",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "No SCID field carries MT5 tick flags"
    },
    {
      "blocker_class": "NONE_FOR_METADATA_VALUE",
      "field": "source_symbol",
      "mt5_equivalence_status": "source metadata derivable, not row-native",
      "mt5_tick_contract_meaning": "source symbol metadata for the tick file",
      "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
      "satisfies_mt5_tick_contract_field": true,
      "scid_evidence": "Derivable from XAUUSD.scid filename and owner request"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "broker_symbol",
      "mt5_equivalence_status": "same text symbol does not prove MT5 broker_symbol lineage",
      "mt5_tick_contract_meaning": "MT5 broker symbol used for the tick export",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY",
      "satisfies_mt5_tick_contract_field": false,
      "scid_evidence": "Filename says XAUUSD, but SCID source is Sierra and not MT5 broker export"
    },
    {
      "blocker_class": "NONE_FOR_SOURCE_HASH_VALUE",
      "field": "source_file_sha256",
      "mt5_equivalence_status": "hash exists for SCID source, not for missing MT5 parquet",
      "mt5_tick_contract_meaning": "SHA256 of the consumed source file",
      "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
      "satisfies_mt5_tick_contract_field": true,
      "scid_evidence": "Raw SCID SHA256 is computed for this route"
    }
  ],
  "generated_at_utc": "2026-05-10T10:47:40Z",
  "hard_absent_fields": [
    "bid",
    "ask",
    "flags"
  ],
  "live_effect": false,
  "mt5_tick_contract_blocker_summary": "SCID proves same-market source activity but lacks bid quote, ask quote, and MT5 flags; several other fields are source-native proxies rather than MT5-native tick fields.",
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
  "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "schema_version": "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1",
  "validation_safe": false
}
```
