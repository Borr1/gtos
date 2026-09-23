# Owner Approval Restart Rollback Gate Dossier

Route: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS`
Evidence class: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`

```json
{
  "artifact_type": "owner_approval_restart_rollback_gate_dossier",
  "gates": [
    {
      "gate": "G12_DESIGN_AUDIT",
      "pass_condition": "G12 accepts this design package as control evidence only with no live/result boundary breach.",
      "required_before": "Any production patch is applied"
    },
    {
      "gate": "OWNER_APPROVAL_TO_EDIT_RUNTIME",
      "pass_condition": "Owner explicitly approves additive SCID capture wiring and restart window.",
      "required_before": "Any edit to src/, tests/, or scripts/ outside this research route"
    },
    {
      "gate": "FOCUSED_TESTS",
      "pass_condition": "Adapter, redaction, duplicate, as-of, unavailable-source, and no-decision-effect tests pass.",
      "required_before": "Future merge"
    },
    {
      "gate": "RESTART_POLICY",
      "pass_condition": "Affected orchestrators restarted after merge; first rows checked for schema/redaction/fail-closed status.",
      "required_before": "Future live monitoring"
    },
    {
      "gate": "ROLLBACK_POLICY",
      "pass_condition": "Scoped revert or logger-disable path documented; historical rows quarantined, not deleted.",
      "required_before": "Future rollout"
    }
  ],
  "generated_at_utc": "2026-05-12T05:29:30Z",
  "monitoring_after_future_rollout": [
    "new shadow_logs/scid_forward_source_capture.jsonl exists",
    "schema_version equals scid_forward_source_capture_v1",
    "all ten groups appear only from source-safe contexts",
    "forbidden fields absent",
    "unavailable sources fail closed",
    "no trading decision-path output diffs"
  ],
  "owner_approval_required_for_live_wiring": true,
  "restart_now": false,
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
