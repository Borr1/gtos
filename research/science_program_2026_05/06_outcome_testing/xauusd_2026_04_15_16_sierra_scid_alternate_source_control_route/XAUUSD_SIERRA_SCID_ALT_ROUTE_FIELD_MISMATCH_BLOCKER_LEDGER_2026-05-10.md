# Field Mismatch Blocker Ledger

Route: `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
Terminal posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "field_mismatch_blocker_ledger",
  "blocker_rows": [
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "time_msc",
      "manual_export_required": true,
      "mt5_equivalence_status": "not MT5-native time_msc; conversion would be source timestamp proxy",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "bid",
      "manual_export_required": true,
      "mt5_equivalence_status": "open/high/low/close and bid_volume cannot be substituted for bid quote",
      "presence_status": "ABSENT"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "ask",
      "manual_export_required": true,
      "mt5_equivalence_status": "open/high/low/close and ask_volume cannot be substituted for ask quote",
      "presence_status": "ABSENT"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "last",
      "manual_export_required": true,
      "mt5_equivalence_status": "SCID close can be a market-activity price proxy but not MT5 last field proof",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "volume",
      "manual_export_required": true,
      "mt5_equivalence_status": "SCID record volume is source-native footprint volume, not MT5 tick volume proof",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY"
    },
    {
      "blocker_class": "HARD_FIELD_ABSENT",
      "field": "flags",
      "manual_export_required": true,
      "mt5_equivalence_status": "absent",
      "presence_status": "ABSENT"
    },
    {
      "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
      "field": "broker_symbol",
      "manual_export_required": true,
      "mt5_equivalence_status": "same text symbol does not prove MT5 broker_symbol lineage",
      "presence_status": "DERIVABLE_ONLY_AS_PROXY"
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_blocker_summary": "SCID has timestamped OHLC and bid/ask volume, but it does not contain bid quote price, ask quote price, or MT5 flags. SCID close/volume/broker-symbol/time_msc substitutions would be proxies and cannot close the MT5 tick export requests.",
  "generated_at_utc": "2026-05-10T10:47:40Z",
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
  "owner_tick_requests_remain_open": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_only_non_equivalent_fields": [
    "time_msc",
    "last",
    "volume",
    "broker_symbol"
  ],
  "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "schema_version": "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1",
  "terminal_blocker_status": "MT5_BID_ASK_TICK_CONTRACT_NOT_SATISFIED_BY_SCID",
  "validation_safe": false
}
```
