# Context Anchor

Route: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS`
Evidence class: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`

```json
{
  "accepted_candidate_boundary": 3014,
  "accepted_capture_groups": [
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source"
  ],
  "artifact_type": "context_anchor",
  "control_inputs": [
    {
      "name": "accepted_g12_decision",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json",
      "required_status": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
    },
    {
      "name": "accepted_g12_schema_contract",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json",
      "required_status": "ten accepted capture groups, 3014 candidate-row coverage expectation, duplicate-key policy accepted"
    },
    {
      "name": "accepted_offline_schema_package",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_ACCEPTED_G12_G0_HANDOFF_RECONCILIATION_2026-05-12.json",
      "required_status": "schema version scid_forward_source_capture_v1 accepted for future source capture"
    },
    {
      "name": "g0_synthesis_route_bundle",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
      "required_status": "rank 1 route is implementation design package; live_wiring_ready=false"
    },
    {
      "name": "g0_future_source_capture_gate",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_FUTURE_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER_2026-05-12.json",
      "required_status": "design/test-harness/read-only alignment allowed; live wiring requires owner approval"
    }
  ],
  "generated_at_utc": "2026-05-12T05:29:30Z",
  "non_goals": [
    "No production code changes in this route",
    "No live logger wiring in this route",
    "No validation, outcome review, scoring, R, win rate, expectancy, or promotion verdict",
    "No broker/account/API/paid-vendor/raw-blob evidence opening"
  ],
  "preserved_flags": {
    "NO_PROMOTION_VERDICT": true,
    "live_effect_false": true,
    "outcome_review_opened_false": true,
    "validation_safe_false": true
  },
  "route_id": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "safe_flags": {
    "ai_api_call_opened": false,
    "broker_or_account_evidence_opened": false,
    "canary_or_selector_change_opened": false,
    "config_change_opened": false,
    "evidence_class": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
    "execution_logic_change_opened": false,
    "live_effect": false,
    "outcome_review_opened": false,
    "paid_vendor_call_opened": false,
    "performance_claim_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "prompt_change_opened": false,
    "raw_blob_capture_opened": false,
    "result_scoring_opened": false,
    "risk_logic_change_opened": false,
    "validation_safe": false
  },
  "schema_version": "scid_forward_source_capture_v1",
  "terminal_boundary": "DESIGN_ONLY_NO_LIVE_WIRING"
}
```
