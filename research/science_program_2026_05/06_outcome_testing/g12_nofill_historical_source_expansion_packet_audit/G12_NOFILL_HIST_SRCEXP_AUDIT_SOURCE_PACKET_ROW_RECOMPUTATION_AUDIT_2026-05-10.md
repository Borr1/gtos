# Source Packet Row Recomputaton Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "source_packet_row_recomputation_audit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "all_rows_have_55_fields": true,
    "all_rows_have_future20_fields": true,
    "all_rows_validate_against_runtime_contract": true,
    "all_safe_flags_closed": true,
    "expected_rows_match": true,
    "no_forbidden_keys": true,
    "packet_row_count_is_2": true,
    "packet_sha_matches_manifest": true
  },
  "credentials_touched": false,
  "expected_rows": [
    {
      "decision_time_utc": "2026-05-08T15:45:00Z",
      "symbol": "NAS100"
    },
    {
      "decision_time_utc": "2026-05-08T13:45:00Z",
      "symbol": "US30_cash"
    }
  ],
  "generated_at_utc": "2026-05-10T05:28:55Z",
  "live_effect": false,
  "observed_rows": [
    {
      "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
      "decision_time_utc": "2026-05-08T15:45:00Z",
      "field_count": 55,
      "forbidden_key_hits": [],
      "future20_field_count": 20,
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "promotion_verdict": "NO_PROMOTION_VERDICT",
      "safe_flags_closed": true,
      "source_control_only_status": "SOURCE_PACKET_CONTROL_ONLY_SAMPLE_FLOOR_NOT_VALIDATION",
      "source_date": "2026-05-08",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "NAS100",
      "validation_contract_issues": [],
      "validation_contract_ok": true
    },
    {
      "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
      "decision_time_utc": "2026-05-08T13:45:00Z",
      "field_count": 55,
      "forbidden_key_hits": [],
      "future20_field_count": 20,
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "promotion_verdict": "NO_PROMOTION_VERDICT",
      "safe_flags_closed": true,
      "source_control_only_status": "SOURCE_PACKET_CONTROL_ONLY_SAMPLE_FLOOR_NOT_VALIDATION",
      "source_date": "2026-05-08",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "US30_cash",
      "validation_contract_issues": [],
      "validation_contract_ok": true
    }
  ],
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
  "packet_path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl",
  "packet_row_count_recomputed": 2,
  "packet_sha256_manifest": "2c8dd8ff4b3e660bea7978a22a84e309ce98f3d95d9db0221fd13957481aa480",
  "packet_sha256_recomputed": "2c8dd8ff4b3e660bea7978a22a84e309ce98f3d95d9db0221fd13957481aa480",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
