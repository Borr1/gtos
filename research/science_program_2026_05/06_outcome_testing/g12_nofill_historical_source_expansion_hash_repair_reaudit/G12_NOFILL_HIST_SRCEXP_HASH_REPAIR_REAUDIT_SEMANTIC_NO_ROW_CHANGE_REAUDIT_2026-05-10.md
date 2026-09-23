# Semantic No Row Change Reaudit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "semantic_no_row_change_reaudit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "admission_counts_match_expected": true,
    "all_packet_safe_flags_closed": true,
    "duplicate_denominators_still_2_2_2": true,
    "no_forbidden_result_cost_keys_in_packet": true,
    "output_manifest_counts_match_expected": true,
    "repair_semantic_counts_unchanged": true,
    "repair_semantic_ledger_proves_hash_only_change": true,
    "target_packet_has_exact_two_rows": true,
    "target_row_identities_match_expected": true
  },
  "credentials_touched": false,
  "duplicate_denominators": {
    "primary_unique_count": 2,
    "row_level_count": 2,
    "secondary_unique_count": 2
  },
  "expected_row_identities": [
    {
      "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
      "decision_time_utc": "2026-05-08T15:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "symbol": "NAS100"
    },
    {
      "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
      "decision_time_utc": "2026-05-08T13:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "symbol": "US30_cash"
    }
  ],
  "generated_at_utc": "2026-05-10T06:17:01Z",
  "live_effect": false,
  "observed_row_identities": [
    {
      "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
      "decision_time_utc": "2026-05-08T15:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "symbol": "NAS100"
    },
    {
      "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
      "decision_time_utc": "2026-05-08T13:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "symbol": "US30_cash"
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "remaining_blockers": [],
  "repair_semantic_ledger_core": {
    "after_packet_sha256": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
    "before_packet_sha256": "2c8dd8ff4b3e660bea7978a22a84e309ce98f3d95d9db0221fd13957481aa480",
    "only_hash_derived_fields_changed": true,
    "semantic_counts_unchanged": true,
    "semantic_rows_unchanged_excluding_hash_fields": true
  },
  "repair_semantic_ledger_path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_packet_parser_hash_repair_rebuild\\NOFILL_HIST_SRCEXP_HASH_REPAIR_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_2026-05-10.json",
  "status_counts": {
    "ADMITTED_SOURCE_PACKET_ROW": 2,
    "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT": 37,
    "REJECTED_ONE_DAY_EMBARGO_OVERLAP": 9
  },
  "target_admission_counts": {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "candidate_count_considered": 48,
    "rejected_candidate_count": 9
  },
  "target_output_manifest_counts": {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "rejected_candidate_count": 9
  },
  "validation_safe": false
}
```
