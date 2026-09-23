# Nofill Source State Gap Closure Contamination Embargo Handling Ledger 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

- contamination_embargo_blocker_count: `17`

## Machine Payload

```json
{
  "artifact_family": "contamination_embargo_blocker_handling_ledger",
  "changes_live_trading_behavior": false,
  "contamination_embargo_blocker_count": 17,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T08:33:44Z",
  "live_effect": false,
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
  "permanent_clean_denominator_exclusion_status": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "rows_count": 17,
  "rows_sample": [
    {
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=GBPJPY/2026-04-16",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "clean_denominator_status": "permanent_exclusion_for_current_packet",
      "contamination_row_id": "CONTAM-0001",
      "future_clean_eligibility": "only_if_separate_independent_clean_source_generation_proof_is_accepted",
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "reusable_only_as": [
        "source_contract_fixture",
        "forensics_control",
        "stress_control"
      ],
      "source_date": "2026-04-16",
      "symbol": "GBPJPY"
    },
    {
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-17",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "clean_denominator_status": "permanent_exclusion_for_current_packet",
      "contamination_row_id": "CONTAM-0002",
      "future_clean_eligibility": "only_if_separate_independent_clean_source_generation_proof_is_accepted",
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "reusable_only_as": [
        "source_contract_fixture",
        "forensics_control",
        "stress_control"
      ],
      "source_date": "2026-04-17",
      "symbol": "GBPUSD"
    },
    {
      "admission_reasons": [
        "candidate_registry_l2_final_state_not_joined_status_only",
        "source_date_contaminated_by_parent_g12=2026-04-17",
        "one_day_embargo_overlap_with_contaminated_date=2026-04-17",
        "local_tick_parquet_missing_for_symbol_date=GBPUSD/2026-04-17",
        "pending_lifecycle_audit_status=PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        "action_required_codes=LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP",
        "final_state_not_admissible_nofill_source_status=PENDING_LIFECYCLE_GROUP_MISSING"
      ],
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "clean_denominator_status": "permanent_exclusion_for_current_packet",
      "contamination_row_id": "CONTAM-0003",
      "future_clean_eligibility": "only_if_separate_independent_clean_source_generation_proof_is_accepted",
      "handling_status": "CONTAMINATION_EMBARGO_EXCLUDED",
      "reusable_only_as": [
        "source_contract_fixture",
        "forensics_control",
        "stress_control"
      ],
      "source_date": "2026-04-17",
      "symbol": "GBPUSD"
    }
  ],
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "validation_safe": false
}
```
