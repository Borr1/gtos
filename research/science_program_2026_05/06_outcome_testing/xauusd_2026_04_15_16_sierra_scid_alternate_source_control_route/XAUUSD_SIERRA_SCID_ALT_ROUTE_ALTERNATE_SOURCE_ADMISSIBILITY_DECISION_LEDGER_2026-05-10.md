# Alternate Source Admissibility Decision Ledger

Route: `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
Terminal posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "admissibility_boundary": "Use this packet only to prove same-market Sierra source coverage and record-level price/volume context. Do not use it as MT5 bid/ask tick recovery, spread/cost proof, lifecycle truth, outcome labels, or validation input.",
  "artifact_family": "alternate_source_admissibility_decision_ledger",
  "changes_live_trading_behavior": false,
  "closes_owner_tick_requests": false,
  "credentials_touched": false,
  "decision": "ADMISSIBLE_AS_SCID_MARKET_ACTIVITY_CONTEXT_ONLY_WITH_MT5_TICK_CONTRACT_BLOCKERS",
  "generated_at_utc": "2026-05-10T10:47:40Z",
  "hard_blocker_fields": [
    "bid",
    "ask",
    "flags"
  ],
  "live_effect": false,
  "mt5_tick_contract_satisfied": false,
  "mt5_tick_recovery_equivalent": false,
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
  "owner_manual_mt5_tick_export_still_required": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_only_fields": [
    "time_msc",
    "last",
    "volume",
    "broker_symbol"
  ],
  "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "schema_version": "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1",
  "scid_context_contract": {
    "contract_id": "same_market_sierra_scid_footprint_context_v1",
    "evidence_class": "SAME_MARKET_SCID_MARKET_ACTIVITY_CONTEXT_ONLY",
    "explicit_non_equivalence": [
      "not MT5 bid/ask tick recovery",
      "not broker quote spread evidence",
      "not source-state truth",
      "not validation or result evidence"
    ],
    "required_fields": [
      "raw_scid_sha256",
      "scid_header",
      "full_day_row_count",
      "candidate_nearest_records",
      "timestamp_utc",
      "open",
      "high",
      "low",
      "close",
      "num_trades",
      "total_volume",
      "bid_volume",
      "ask_volume"
    ]
  },
  "scid_context_contract_satisfied": true,
  "source_hashed_alternate_packet_should_be_emitted": true,
  "validation_safe": false
}
```
