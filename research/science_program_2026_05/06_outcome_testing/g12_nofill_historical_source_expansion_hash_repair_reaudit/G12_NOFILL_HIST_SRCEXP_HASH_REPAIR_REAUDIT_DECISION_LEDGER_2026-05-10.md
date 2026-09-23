# Decision Ledger

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "admitted_packet_row_count": 2,
  "artifact_family": "decision_ledger",
  "blocked_candidate_count": 37,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_reasons": [
    "The three prior parser/verifier hash blockers were recomputed from disk and match the repaired target manifest.",
    "Packet parser_code_hash fields bind the current accepted target builder hash.",
    "The repaired packet SHA matches target and repair manifests.",
    "Packet semantics remain exactly two admitted rows, 37 blockers, 9 rejects, and duplicate denominators 2/2/2.",
    "Target, repair, and new G12 verification lanes remain source/control only with validation closed."
  ],
  "duplicate_denominators": "2/2/2",
  "generated_at_utc": "2026-05-10T06:17:09Z",
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
  "rejected_candidate_count": 9,
  "remaining_exact_repair_blocker_count": 0,
  "remaining_exact_repair_blockers": [],
  "route_id": "G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT",
  "terminal_decision": "ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT",
  "validation_safe": false
}
```
