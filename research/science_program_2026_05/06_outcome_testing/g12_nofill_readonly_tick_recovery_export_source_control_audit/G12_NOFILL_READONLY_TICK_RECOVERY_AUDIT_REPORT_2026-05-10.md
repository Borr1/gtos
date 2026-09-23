# G12 NOFILL Readonly Tick Recovery Audit Report

Route: `G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "audit_report",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "count_summary": {
    "g12_grouped_candidate_total": 31,
    "g12_grouped_request_rows": 22,
    "owner_action_remaining_requests": 2,
    "recovered_absent_absent_windows": 2,
    "recovered_absent_recovered_windows": 20,
    "source_manifest_rows": 20,
    "target_candidate_rows": 31,
    "target_clean_candidate_rows": 19,
    "target_contamination_embargo_excluded_rows": 12,
    "target_grouped_rows": 22,
    "target_recovered_candidate_rows": 28,
    "target_recovered_grouped_rows": 20,
    "target_remaining_candidate_rows": 3,
    "target_remaining_grouped_rows": 2,
    "upstream_owner_market_data_export_requests": 22,
    "upstream_tick_export_rows": 31,
    "upstream_unique_export_requests": 22
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T10:17:25Z",
  "headline_findings": [
    "Target JSON artifacts parse and preserve NO_PROMOTION_VERDICT with safe flags false.",
    "Counts recompute to 31 tick/export-dependent rows, 22 grouped requests, 20 recovered grouped sources, 28 recovered candidate rows, 2 remaining owner/export requests, 3 remaining candidate rows, and 12 contamination/embargo exclusions.",
    "All 20 recovered ignored parquet sources were rehashed locally and covered their requested UTC candidate windows.",
    "The remaining exact MT5 bid/ask tick requests are XAUUSD 2026-04-15 and XAUUSD 2026-04-16; read-only MT5 extraction returned zero ticks with exact symbol selection, full UTC-day boundaries, and success last_error.",
    "Local Sierra XAUUSD.scid has same-market rows on both remaining dates, so market closure is ruled out; it is not admitted as recovered MT5 tick source because it does not satisfy the target bid/ask tick field contract.",
    "No raw tick parquet/CSV files are tracked or staged, and no validation/result/live surfaces were opened.",
    "Next route is active: parse and hash Sierra XAUUSD.scid as alternate-source control evidence or freeze exact field-mismatch blockers plus owner export instructions."
  ],
  "live_effect": false,
  "next_route_summary": {
    "one_line_starter": "/goal Build an alternate-source XAUUSD 2026-04-15/16 source-control route from C:\\SierraChart\\Data\\XAUUSD.scid only; do mandatory preflight; stay market-data source-control only with no validation/result/live surfaces; parse and hash SCID coverage for OWNER-TICK-0020 and OWNER-TICK-0021 candidate windows, compare against the MT5 bid/ask tick field contract, either emit a source-hashed alternate-source packet or exact field-mismatch blocker, run verifier/focused tests, and close with NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
    "recommended_route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE"
  },
  "noleak_summary": {
    "audit_status": "PASS",
    "forbidden_live_surface_paths": [],
    "raw_tick_or_csv_files_not_tracked_or_staged": true
  },
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
  "remaining_request_summary": {
    "recovery_ladder_exhaustion_status": "ACCEPT_EXACT_REMAINING_MT5_TICK_REQUESTS_AFTER_SOURCE_SAFE_SEARCH_AND_READONLY_EXTRACTION",
    "remaining": [
      "XAUUSD|2026-04-15",
      "XAUUSD|2026-04-16"
    ],
    "sierra_scid_window_rows_present": true
  },
  "route_id": "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_nofill_readonly_tick_recovery_export_source_control_audit_v1",
  "source_hash_window_summary": {
    "hash_mismatch_count": 0,
    "recovered_source_file_count": 20,
    "rehashed_local_source_file_count": 20,
    "window_or_schema_failure_count": 0
  },
  "terminal_decision": "ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE",
  "validation_safe": false
}
```
