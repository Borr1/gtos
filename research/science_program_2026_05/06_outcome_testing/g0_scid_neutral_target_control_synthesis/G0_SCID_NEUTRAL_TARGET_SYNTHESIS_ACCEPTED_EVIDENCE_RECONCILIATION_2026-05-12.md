# Accepted Evidence Reconciliation

- **route_id:** `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS`
- **evidence_class:** `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_only_as": "source-safe neutral future-behavior control evidence; no strategy result meaning",
  "artifact_family": "accepted_evidence_reconciliation",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY",
  "exact_reconciliation_checks": [
    {
      "actual": "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY",
      "check_id": "g12_terminal_decision",
      "expected": "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY",
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "candidate_rows",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 2432,
      "check_id": "sealed_rows",
      "expected": 2432,
      "status": "PASS"
    },
    {
      "actual": 582,
      "check_id": "stress_rows",
      "expected": 582,
      "status": "PASS"
    },
    {
      "actual": 24112,
      "check_id": "terminal_statuses",
      "expected": 24112,
      "status": "PASS"
    },
    {
      "actual": 20292,
      "check_id": "computable_rows",
      "expected": 20292,
      "status": "PASS"
    },
    {
      "actual": 3820,
      "check_id": "fail_closed_not_computable_rows",
      "expected": 3820,
      "status": "PASS"
    },
    {
      "actual": 9,
      "check_id": "bounded_scid_segments_rehashed",
      "expected": 9,
      "status": "PASS"
    },
    {
      "actual": 0,
      "check_id": "target_row_hash_mismatches",
      "expected": 0,
      "status": "PASS"
    },
    {
      "actual": 0,
      "check_id": "target_value_mismatches",
      "expected": 0,
      "status": "PASS"
    },
    {
      "actual": 24112,
      "check_id": "terminal_grid_recomputed_unique_keys",
      "expected": 24112,
      "status": "PASS"
    },
    {
      "actual": 0,
      "check_id": "terminal_grid_duplicate_keys",
      "expected": 0,
      "status": "PASS"
    },
    {
      "actual": 7,
      "check_id": "denominator_groups",
      "expected": 7,
      "status": "PASS"
    }
  ],
  "g12_review_pass_map": {
    "accepted_scid_segment_rehash": true,
    "aggregate_matrix": true,
    "denominator": true,
    "dirty_raw_live_surface": true,
    "noleak": true,
    "not_computable": true,
    "prerequisite_acceptance": true,
    "row_target_recomputation": true,
    "saturation": true,
    "source_hash_input_binding": true,
    "terminal_grid": true
  },
  "g12_terminal_boundary": "CONTROL_EVIDENCE_ONLY_NOT_STRATEGY_PERFORMANCE",
  "generated_at_utc": "2026-05-11T22:53:11Z",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS",
  "row_result_recomputation_summary": {
    "horizon_counts": {
      "1": 5828,
      "4": 5531,
      "16": 4834,
      "32": 4099
    },
    "partition_counts_with_repeated_family_horizon_rows": {
      "SEALED_VALIDATION_CANDIDATE_DESIGN": 16322,
      "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": 3970
    },
    "row_results_loaded": 20292,
    "target_family_counts": {
      "neutral_close_to_close_return_m15_horizons_v1": 10837,
      "neutral_high_low_excursion_m15_horizons_v1": 9455
    },
    "terminal_status_counts": {
      "COMPUTABLE": 20292
    }
  },
  "schema_version": "g0_scid_neutral_target_control_synthesis_v1",
  "terminal_decision_from_g12": "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false
}
```
