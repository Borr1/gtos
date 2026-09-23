# OTI4 Opening-Drive Source Hash Asof Duplicate Audit

- Generated at UTC: `2026-05-08T14:58:23Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`
- Live effect: `false`

- Verifies source hashes, as-of constraints, and duplicate-key contract revision.

```json
{
  "all_rows_have_proof_or_exact_blocker": true,
  "artifact_family": "OTI4_OPENING_DRIVE_SOURCE_HASH_ASOF_DUPLICATE_AUDIT",
  "asof_failure_count_for_source_corrected_rows": 0,
  "duplicate_policy": "future result lanes must use source_contract_key or exact blocker status, not stale NO_BREAKOUT_ASOF duplicate groups",
  "exact_blocker_counts": {
    "BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE": 12,
    "BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE": 6,
    "BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION": 8,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3
  },
  "forbidden_sources_read": [],
  "generated_at_utc": "2026-05-08T14:58:23Z",
  "lane_id": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
  "live_effect": false,
  "original_duplicate_group_count": 17,
  "outcome_review_opened": false,
  "parser_version": "oti4_opening_drive_tick_mid_m1_source_contract_v1_2026_05_08",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proof_status_counts": {
    "EXACT_IMPOSSIBILITY_OR_SOURCE_BLOCKER": 11,
    "SOURCE_HASHED_RANGE_BREAKOUT_ASOF_PROOF": 69
  },
  "result_labels_assigned": 0,
  "row_count": 80,
  "row_route_decision_counts": {
    "CONTRACT_REVISED_EXCLUDE_BREAKOUT_SIDE_MISMATCH": 12,
    "CONTRACT_REVISED_EXCLUDE_DECISION_BEFORE_FROZEN_RANGE_CLOSE": 8,
    "CONTRACT_REVISED_EXCLUDE_NO_BREAKOUT_ASOF": 6,
    "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT": 51,
    "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY": 3
  },
  "source_contract_id": "OTI4_OPENING_DRIVE_TICK_RANGE_BREAKOUT_SOURCE_CONTRACT_V1",
  "source_corrected_contract_key_count": 16,
  "source_hash_mismatch_count": 0,
  "source_hash_record_count": 30,
  "validation_safe": false
}
```
