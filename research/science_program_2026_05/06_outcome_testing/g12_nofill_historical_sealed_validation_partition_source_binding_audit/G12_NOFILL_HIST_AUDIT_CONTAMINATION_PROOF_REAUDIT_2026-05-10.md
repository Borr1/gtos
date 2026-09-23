# Contamination Proof Reaudit

Route: `G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT`
Target route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "contamination_proof_reaudit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "all_rows_have_contamination_or_control_reason": true,
    "all_rows_use_nonsealed_partition_classes": true,
    "proof_counts_match_row_family_counts": true,
    "proof_marks_all_rows_contaminated": true,
    "proof_row_count_matches_rows": true,
    "sealed_escape_rule_present": true
  },
  "contaminated_row_count_recomputed": 298,
  "contamination_counts_by_terminal_family_recomputed": {
    "accepted": 225,
    "reject": 65,
    "source_control": 4,
    "source_impossible": 4
  },
  "contamination_reason_counts": {
    "accepted CAT V3 categorical input label already assigned": 225,
    "duplicate key/group membership already inspected": 225,
    "exact source-impossibility decision already accepted": 4,
    "excluded before denominator movement": 65,
    "non-denominator row consumed by source repair/control route": 4,
    "reject overlap against accepted duplicate keys/groups already audited": 65,
    "reject reason already assigned": 65,
    "requires unavailable broker-native quote-event sequence source": 4,
    "row was included in source-control/count-packet/G12/G0 synthesis chain": 225,
    "source-control decision already made": 4
  },
  "credentials_touched": false,
  "live_effect": false,
  "nonsealed_partition_class_violations": [],
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
  "primary_partition_counts_recomputed": {
    "CONTAMINATED_DISCOVERY_DEVELOPMENT_INPUT_CONTROL": 225,
    "CONTAMINATED_REJECT_EXCLUSION_PROOF": 65,
    "CONTAMINATED_SOURCE_IMPOSSIBILITY_NON_DENOMINATOR": 4,
    "DEVELOPMENT_SOURCE_CONTROL_NON_DENOMINATOR": 4
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rows_without_contamination_or_control_reason": [],
  "sealed_escape_rule": "No row sharing packet_row_id, source_row_id, nofill_duplicate_key, duplicate_group_id, symbol/session/date/source_lane exact tuple, or one-day embargo overlap with these rows can be admitted as sealed validation without a new G12 source-control audit.",
  "target_route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
  "validation_safe": false
}
```
