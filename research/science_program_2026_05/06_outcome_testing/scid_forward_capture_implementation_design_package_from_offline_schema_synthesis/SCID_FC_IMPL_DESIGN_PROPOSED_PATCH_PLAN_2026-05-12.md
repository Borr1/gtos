# Proposed Patch Plan

Route: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS`
Evidence class: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`

```json
{
  "artifact_type": "proposed_patch_plan",
  "function_contracts": [
    "build_scid_forward_source_capture_row(candidate_packet, group_context) -> dict",
    "validate_scid_forward_source_capture_row(row, duplicate_key_registry=None) -> ValidationResult",
    "record_scid_forward_capture_group(row, *, path=SCID_FORWARD_SOURCE_CAPTURE_PATH) -> bool",
    "record_scid_forward_capture_lifecycle_event(lifecycle_event, candidate_context) -> bool"
  ],
  "generated_at_utc": "2026-05-12T05:29:30Z",
  "no_live_assertions": [
    "This route makes no production code changes.",
    "Future runtime writer must be additive and fail-open for trading behavior.",
    "Future parser/validator must be fail-closed for accepted research rows.",
    "Future rollout cannot change prompt/config/risk/safety/execution/canary/selector behavior."
  ],
  "patch_artifacts": [
    {
      "applies_now": false,
      "artifact": "PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
      "path": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
      "requires_g12_review_before_apply": true,
      "requires_owner_approval": true
    },
    {
      "applies_now": false,
      "artifact": "PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md",
      "path": "proposed_patches/PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md",
      "requires_g12_review_before_apply": true,
      "requires_owner_approval": true
    },
    {
      "applies_now": false,
      "artifact": "PROPOSED_PATCH_003_TESTS_AND_VERIFIERS_2026-05-12.patch.md",
      "path": "proposed_patches/PROPOSED_PATCH_003_TESTS_AND_VERIFIERS_2026-05-12.patch.md",
      "requires_g12_review_before_apply": true,
      "requires_owner_approval": true
    }
  ],
  "proposal_status": "DESIGN_ONLY_NOT_APPLIED",
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
  "schema_version": "scid_forward_source_capture_v1"
}
```
