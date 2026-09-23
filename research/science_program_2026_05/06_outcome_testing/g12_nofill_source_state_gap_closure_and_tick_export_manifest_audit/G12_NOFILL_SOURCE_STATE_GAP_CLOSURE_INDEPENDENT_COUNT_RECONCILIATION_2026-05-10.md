# G12 Nofill Source State Gap Closure Independent Count Reconciliation 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`

```json
{
  "artifact_family": "independent_count_reconciliation",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "expected_counts": {
    "admitted_source_bound_rows": 2,
    "blocked_rows": 37,
    "contamination_embargo_rows": 17,
    "duplicate_denominators": "2/2/2",
    "field_closure_rows": 55,
    "recovered_source_state_count": 0,
    "rejected_rows": 9,
    "tick_export_rows": 31
  },
  "generated_at_utc": "2026-05-10T09:13:22Z",
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recomputed_counts": {
    "admitted_source_bound_rows_from_g0_row_ledger": 2,
    "blocker_rows_from_active_pursuit_rows": 37,
    "blocker_rows_from_g0_blocker_ids": 37,
    "blocker_rows_from_taxonomy_rows": 37,
    "contamination_embargo_rows": 17,
    "duplicate_denominators_from_g0_duplicate_review": "2/2/2",
    "duplicate_denominators_from_packet_duplicate_ledger": "2/2/2",
    "field_closure_rows": 55,
    "recovered_source_state_count": 0,
    "reject_rows_from_g0_reject_rows": 9,
    "reject_rows_from_target_g0_reject_ids": 9,
    "tick_export_rows": 31
  },
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "row_level_sources_used": [
    "research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_TWO_ADMITTED_ROW_SYNTHESIS_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_REJECT_LEARNING_LEDGER_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_PURSUIT_LADDER_LEDGER_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_CONTAMINATION_EMBARGO_HANDLING_LEDGER_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_55_FIELD_CLOSURE_LEDGER_2026-05-10.json"
  ],
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "validation_safe": false
}
```
