# Decision Ledger

```json
{
  "accepted_evidence_class": "SAME_MARKET_SCID_MARKET_ACTIVITY_CONTEXT_ONLY",
  "artifact_family": "decision_ledger",
  "changes_live_trading_behavior": false,
  "closes_owner_tick_requests": false,
  "context_only_packet_boundary": "Accepted only to prove same-market Sierra source coverage and record-level activity context around the two requested UTC days and three candidate timestamps.",
  "credentials_touched": false,
  "decision_status": "PASS",
  "exact_remaining_owner_requests": [
    {
      "owner_request_id": "OWNER-TICK-0020",
      "required_fields": [
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
      "target_path_template": "data/ticks/XAUUSD/2026-04-15.parquet"
    },
    {
      "owner_request_id": "OWNER-TICK-0021",
      "required_fields": [
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
      "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet"
    }
  ],
  "generated_at_utc": "2026-05-10T11:13:20Z",
  "live_effect": false,
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
  "owner_manual_mt5_export_still_required": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repair_prompt_if_needed": null,
  "repair_required": false,
  "route_id": "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_v1",
  "source_hashed_alternate_packet_accepted": true,
  "target_route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "target_route_terminal_decision": "ACCEPT_AS_SOURCE_HASHED_SCID_CONTEXT_PACKET_WITH_EXACT_MT5_FIELD_BLOCKERS",
  "terminal_decision": "ACCEPT_TARGET_ROUTE_AS_SOURCE_HASHED_SCID_CONTEXT_ONLY_WITH_MT5_TICK_BLOCKERS_OPEN",
  "two_dates_open_ended_drag_closed_for_scid_evidence_class": true,
  "validation_safe": false
}
```
