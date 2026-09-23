# G12 NOFILL Readonly Tick Recovery Next Route Recommendation

Route: `G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "next_route_recommendation",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "full_prompt": "Build `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`.\n\nScope: source/control only. Inputs: this G12 audit, target NOFILL tick recovery route, `C:\\SierraChart\\Data\\XAUUSD.scid`, and the exact remaining requests OWNER-TICK-0020 and OWNER-TICK-0021. Parse the SCID file read-only, hash the raw source, compute row counts for each requested UTC day and each candidate timestamp, and compare fields against the MT5 bid/ask tick contract. Do not score results, do not inspect broker/account/order/history/deal/position values, do not call paid/API/Databento routes, do not change prompts/config/risk/permissions/safety/selector/canary/live behavior, and do not commit raw SCID-derived exports. If SCID satisfies an approved alternate-source contract, emit a source-hashed alternate packet for G12 audit; if it does not, emit exact field-mismatch blockers plus owner/manual export instructions. Run a route verifier and focused tests. Terminal flags: NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
  "generated_at_utc": "2026-05-10T10:17:25Z",
  "live_effect": false,
  "non_passive_next_route": true,
  "one_line_starter": "/goal Build an alternate-source XAUUSD 2026-04-15/16 source-control route from C:\\SierraChart\\Data\\XAUUSD.scid only; do mandatory preflight; stay market-data source-control only with no validation/result/live surfaces; parse and hash SCID coverage for OWNER-TICK-0020 and OWNER-TICK-0021 candidate windows, compare against the MT5 bid/ask tick field contract, either emit a source-hashed alternate-source packet or exact field-mismatch blocker, run verifier/focused tests, and close with NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
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
  "owner_manual_export_fallback": {
    "action": "Provide or authorize source-safe XAUUSD tick exports for 2026-04-15 and 2026-04-16.",
    "required_fields": [
      "ask",
      "bid",
      "broker_symbol",
      "flags",
      "last",
      "source_symbol",
      "time_msc",
      "time_utc",
      "volume"
    ],
    "required_files": [
      "data/ticks/XAUUSD/2026-04-15.parquet",
      "data/ticks/XAUUSD/2026-04-16.parquet"
    ],
    "required_hashing": "SHA256, size, schema, min/max timestamp, field availability, and candidate-window row count.",
    "required_window_utc": "00:00:00Z through 23:59:59.999999Z for each source date"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recommended_route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "remaining_route_status": "ACCEPT_EXACT_REMAINING_MT5_TICK_REQUESTS_AFTER_SOURCE_SAFE_SEARCH_AND_READONLY_EXTRACTION",
  "route_id": "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT",
  "route_type": "alternate_source_recovery_route",
  "schema_version": "g12_nofill_readonly_tick_recovery_export_source_control_audit_v1",
  "terminal_decision": "ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE",
  "validation_safe": false,
  "why_this_route": "The exact MT5 bid/ask tick export requests remain unrecovered, but local same-market Sierra SCID rows cover both UTC dates and rule out a market-closed explanation. The next route should determine whether SCID can serve a source-control alternate packet or must remain a field-mismatch blocker."
}
```
