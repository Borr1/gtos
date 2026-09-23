# Safe Flag Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `safe_flag_audit`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "safe_flag_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "failures": [],
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
      "artifact": "completion",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "native_scid",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "csv_triage",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "selected_source",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "source_asof",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "duplicate",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "baseline",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "hardening",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "saturation",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "noleak_dirty",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "manifest",
      "failures": [],
      "status": "PASS"
    },
    {
      "artifact": "verification",
      "failures": [],
      "status": "SKIP_NON_PACKET_VERIFIER_RESULT"
    }
  ],
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "status": "PASS",
  "validation_safe": false
}
```
