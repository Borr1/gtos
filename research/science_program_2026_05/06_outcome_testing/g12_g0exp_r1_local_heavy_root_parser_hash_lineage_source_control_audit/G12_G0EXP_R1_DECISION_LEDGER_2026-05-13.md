# G12 G0EXP R1 Decision Ledger

- **route_id:** `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT`
- **evidence_class:** `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

- Terminal decision: `ACCEPT_AS_G12_G0EXP_R1_SOURCE_CONTROL_AUDIT_WITH_SAME_CLASS_HASH_REPAIR`.

```json
{
  "artifact_family": "decision_ledger",
  "assigned_family_audit": {
    "all_assigned_families_reduced_to_closed_or_exact": true,
    "assigned_family_count": 4,
    "assigned_family_status_rows": [
      {
        "access_status": "CLOSED_OR_EXACT_BY_ROOT_ROWS",
        "as_of_status": "CLOSED_SOURCE_CONTROL_ONLY_NO_OUTCOME_ASOF",
        "candidate_family": "local_heavy_data_root_coverage_and_hash_deferral_controls",
        "candidate_id": "R4-EXP-ROOT-001",
        "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER_2026-05-13.json",
        "no_leak_status": "PASS_METADATA_ONLY_NO_RAW_CONTENT_NO_RESULT_SCORING",
        "parser_status": "NOT_PRIMARY_PARSER_FAMILY",
        "source_status": "CLOSED_WITH_ROOT_METADATA_COVERAGE",
        "stop_condition": "Closed by source-root coverage plus hash deferral records for raw/heavy files."
      },
      {
        "access_status": "NO_RUNTIME_ACCESS_REQUIRED",
        "as_of_status": "CLOSED_FOR_SOURCE_CONTROL_LINEAGE_ONLY",
        "candidate_family": "parser_version_shape_fingerprint_and_schema_drift_controls",
        "candidate_id": "R4-EXP-PARSER-001",
        "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX_2026-05-13.json",
        "no_leak_status": "PASS_CONTROL_FILE_SHAPES_ONLY_NO_OUTCOME_OPENING",
        "parser_status": "CLOSED_PARSER_CODE_HASH_AND_SHAPE_FINGERPRINTS",
        "source_status": "CLOSED_WITH_HASHED_PARSER_FILES_AND_SCHEMA_SHAPES",
        "stop_condition": "Closed with 120 parser/control files and 120 schema shapes."
      },
      {
        "access_status": "NO_RUNTIME_ACCESS_REQUIRED",
        "as_of_status": "CLOSED_FOR_FUTURE_DENOMINATOR_PREREQUISITE_ONLY",
        "candidate_family": "hash_integrity_placebo_controls",
        "candidate_id": "EXP-ADV-001",
        "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER_2026-05-13.json",
        "no_leak_status": "PASS_MISSING_HASH_STRATA_ARE_CONTROL_FLAGS_NOT_RESULTS",
        "parser_status": "CLOSED_BY_PARSER_HASH_REQUIREMENT",
        "source_status": "CLOSED_WITH_HASH_COMPLETENESS_AND_DEFERRAL_STRATA",
        "stop_condition": "Closed as a future placebo/control family: missing hash remains fail-closed until exact source hash exists."
      },
      {
        "access_status": "NO_RUNTIME_ACCESS_REQUIRED",
        "as_of_status": "CLOSED_HEAD_AND_INPUT_HASH_BOUND",
        "candidate_family": "source_control_commit_route_and_artifact_lineage_controls",
        "candidate_id": "R4-EXP-CODEHIST-001",
        "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF_2026-05-13.json",
        "no_leak_status": "PASS_LINEAGE_ONLY_NO_RESULT_OR_LIVE_SURFACE",
        "parser_status": "CLOSED_BY_ROUTE_SCRIPT_HASHES",
        "source_status": "CLOSED_WITH_GIT_LINEAGE_AND_OUTPUT_BINDING",
        "stop_condition": "Closed with upstream input hashes, route script hashes, generated artifact hashes, and git lineage."
      }
    ],
    "root_absence_exact_requirements": []
  },
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "decision_summary": "R1 is accepted as G12 source/control evidence after repairing the stale G12 prompt hash in the R1 manifest/lineage. The packet remains source-control only and cannot open results, validation, promotion, or live behavior.",
  "evidence_class": "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T04:47:59Z",
  "live_effect": false,
  "no_raw_blob_audit": {
    "audit_status": "PASS_NO_RAW_MARKET_BLOB_COMMIT_BY_THIS_ROUTE",
    "no_forbidden_live_surface_in_scope": true,
    "raw_market_blob_artifact_count": 0,
    "raw_market_blob_paths_in_manifest": []
  },
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
  "parser_fingerprint_audit": {
    "missing_required_fingerprint_field_count": 0,
    "parser_drift_policy": "Any future denominator-entry packet must bind parser_code_hash, shape_fingerprint, schema key-set fingerprint, producer file path, and lineage commit before outcome/result opening.",
    "parser_file_count": 120,
    "schema_shape_file_count": 120
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "quarantine_audit": {
    "accepted_40_count_recomputed_from_upstream": 40,
    "adjacent_overflow_count": 6,
    "adjacent_overflow_entered_accepted_40": [],
    "r1_new_denominator_rows_added": 0,
    "result_or_validation_opened": false
  },
  "remaining_exact_source_access_export_capture_requirements": [],
  "route_id": "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT",
  "safe_flag_audit": {
    "safe_flag_failures": [],
    "safe_flag_file_count": 26
  },
  "same_class_repair_closed": true,
  "schema_version": "g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_v1",
  "terminal_decision": "ACCEPT_AS_G12_G0EXP_R1_SOURCE_CONTROL_AUDIT_WITH_SAME_CLASS_HASH_REPAIR",
  "validation_safe": false
}
```
