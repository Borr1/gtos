# Exact Requirement Rows

```json
{
  "artifact_family": "exact_requirement_rows",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-13T04:47:27Z",
  "live_effect": false,
  "may_open_outcomes_or_results_in_this_route": false,
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
  "route_id": "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT",
  "rows": [
    {
      "accepted_field_names": [
        "candidate_input_row_id",
        "candidate_id",
        "source_candidate_id"
      ],
      "future_fail_closed_if_missing": "MISSING_CANDIDATE_ID",
      "requirement": "candidate id",
      "requirement_row_id": "ADV002-REQ-CANDIDATE-ID",
      "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY"
    },
    {
      "accepted_field_names": [
        "duplicate_proxy_denominator_key",
        "duplicate_key",
        "nofill_duplicate_key"
      ],
      "future_fail_closed_if_missing": "MISSING_DUPLICATE_KEY",
      "requirement": "duplicate key",
      "requirement_row_id": "ADV002-REQ-DUPLICATE-KEY",
      "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY"
    },
    {
      "accepted_field_names": [
        "source_hash",
        "source_sha256",
        "row_hash",
        "source_file_sha256"
      ],
      "future_fail_closed_if_missing": "MISSING_SOURCE_HASH",
      "requirement": "source hash / row hash",
      "requirement_row_id": "ADV002-REQ-SOURCE-HASH",
      "status": "ACCEPTED_AFTER_MANIFEST_HASH_REPAIR"
    },
    {
      "accepted_field_names": [
        "group_membership_version",
        "group_membership_manifest_sha256",
        "duplicate_group_id",
        "canonical_economic_group"
      ],
      "exact_next_requirement": "future packet must emit group_membership_version and group_membership_manifest_sha256 or G12 must reject denominator entry",
      "future_fail_closed_if_missing": "MISSING_GROUP_MEMBERSHIP_VERSION",
      "requirement": "group membership version",
      "requirement_row_id": "ADV002-REQ-GROUP-MEMBERSHIP",
      "status": "ACCEPTED_AS_EXACT_FUTURE_FAIL_CLOSED_REQUIREMENT"
    },
    {
      "accepted_field_names": [
        "collision_policy",
        "canonical_counting_row_id",
        "noncanonical_projection_policy"
      ],
      "future_fail_closed_if_missing": "MISSING_COLLISION_POLICY",
      "requirement": "collision policy",
      "requirement_row_id": "ADV002-REQ-COLLISION-POLICY",
      "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY"
    },
    {
      "accepted_field_names": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_hash",
        "row_hash",
        "group_membership_version",
        "group_membership_manifest_sha256",
        "canonical_counting_row_id",
        "collision_policy",
        "canonical_economic_group",
        "symbol",
        "session",
        "timeframe",
        "decision_asof_utc",
        "source_observed_asof_utc",
        "source_identifier"
      ],
      "future_fail_closed_if_missing": "FORBIDDEN_FIELD_PRESENT",
      "requirement": "as-of/no-leak allowlist and denylist",
      "requirement_row_id": "ADV002-REQ-ASOF-NOLEAK",
      "status": "ACCEPTED_SOURCE_CONTROL_DESIGN_READY"
    },
    {
      "accepted_field_names": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_hash",
        "row_hash",
        "group_membership_version",
        "group_membership_manifest_sha256",
        "canonical_counting_row_id",
        "collision_policy",
        "decision_asof_utc",
        "source_observed_asof_utc"
      ],
      "future_fail_closed_if_missing": "route back to source-control repair before denominator entry",
      "requirement": "future candidate/control capture rows",
      "requirement_row_id": "ADV002-REQ-CAPTURE-ROWS",
      "status": "FUTURE_PACKET_REQUIREMENT_ONLY_NO_RESULTS_OPENED"
    }
  ],
  "true_remaining_requirements_are_exact": true,
  "vague_blockers": [],
  "validation_safe": false
}
```
