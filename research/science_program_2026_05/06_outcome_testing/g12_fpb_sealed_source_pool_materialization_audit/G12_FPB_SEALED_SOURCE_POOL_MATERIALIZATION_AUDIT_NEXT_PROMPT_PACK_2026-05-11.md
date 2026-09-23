# Next Prompt Pack

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `next_prompt_pack`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "next_prompt_pack",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_basis": "REPAIR_BLOCKED_SOURCE_POOL_PACKET",
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "full_prompt": {
    "goal": "Repair the append-mutable native Sierra SCID source-hash drift by freezing immutable source evidence before any SCID-to-as-of or validation route.",
    "must_include": [
      "all 9 current recomputed SCID hashes and stale packet hashes",
      "immutable full-file copy policy or bounded eligible-segment hash policy",
      "audit timestamp and coverage end freeze",
      "eligible_segment_start_utc hard floor preserved",
      "all 365 selected discovery hashes still excluded",
      "four adversarial baseline preservation",
      "builder/verifier/focused tests"
    ],
    "must_not_include": [
      "validation execution",
      "path-label generation",
      "result scoring",
      "promotion",
      "AI/API calls",
      "broker account/order/history/deal/position reads",
      "live behavior changes"
    ]
  },
  "generated_at_utc": "2026-05-11T09:43:01Z",
  "live_effect": false,
  "next_route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "one_line_starter": "/goal Build FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR from the G12 FPB sealed source-pool audit repair-blocker ledger; do mandatory GTOS preflight first; stay source-control only with no validation execution, replay/path-label/result scoring, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, credentials, remotes, live behavior, or prompt/config/risk/safety changes; repair the 9 append-mutable Sierra SCID source candidates by producing immutable snapshot hashes or bounded eligible-segment hashes, refreshed coverage windows, source/as-of/no-leak metadata, duplicate decisions, partition assignments, and a rerunnable verifier/focused test pack; preserve all 365 discovery-source exclusions and the four adversarial baselines; emit JSON+MD repair packet, G12 rerun prompt, completion audit, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
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
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "validation_safe": false
}
```
