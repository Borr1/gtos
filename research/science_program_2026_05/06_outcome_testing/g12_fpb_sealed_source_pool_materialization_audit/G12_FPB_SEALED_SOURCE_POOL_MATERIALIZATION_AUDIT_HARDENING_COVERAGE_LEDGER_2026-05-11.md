# Hardening Coverage Ledger

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `hardening_coverage_ledger`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "all_required_controls_covered": true,
  "artifact_family": "hardening_coverage_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-11T09:43:01Z",
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
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "rows": [
    {
      "audit_output": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_COMPLETION_AUDIT_2026-05-11.json",
      "required_control": "proof-or-impossibility, no-speed-shortcut, same-evidence-class continuation",
      "source_control": "goal_session_research_discipline",
      "status": "COVERED"
    },
    {
      "audit_output": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_SCID_SOURCE_HASH_COVERAGE_AUDIT_2026-05-11.json",
      "required_control": "worktree absence is not data absence; hash consumed source files",
      "source_control": "local_heavy_data_inventory",
      "status": "COVERED"
    },
    {
      "audit_output": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_DISCOVERY_EXCLUSION_AUDIT_2026-05-11.json",
      "required_control": "discovery rows excluded and sealed source use gated before validation",
      "source_control": "historical_sealed_validation_protocol",
      "status": "COVERED"
    },
    {
      "audit_output": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_SCID_SOURCE_HASH_COVERAGE_AUDIT_2026-05-11.json",
      "required_control": "all 9 SCID files are rehashed, not sampled",
      "source_control": "no_speed_shortcut",
      "status": "COVERED"
    },
    {
      "audit_output": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_REPAIR_BLOCKER_LEDGER_2026-05-11.json",
      "required_control": "local Sierra files read directly; no owner/export blocker needed for accepted nine",
      "source_control": "owner_access_pursuit",
      "status": "COVERED"
    },
    {
      "audit_output": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_NOLEAK_DIRTY_STATE_AUDIT_2026-05-11.json",
      "required_control": "safe flags, no live surface, duplicate, baseline, and gate audits",
      "source_control": "hostile_audit_controls",
      "status": "COVERED"
    }
  ],
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "validation_safe": false
}
```
