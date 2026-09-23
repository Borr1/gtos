# G12 Otx G6 Result Acceptance Review

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "acceptance_verdict": "ACCEPT_PACKET_062_AS_QUARANTINED_DISCOVERY_ONLY_NO_VALIDATION",
  "artifact_family": "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW",
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "label_family_review": {
    "broker_actual_r_inspected": false,
    "result_source_policy": "tick_recomputed_only_no_broker_actual_r_no_hidden_path_labels",
    "synthetic_path_r_used_only_as_quarantined_discovery": true
  },
  "live_effect": false,
  "outcome_review_opened": false,
  "packet_062_decision": {
    "accepted_evidence": {
      "countable_discovery_rows": 9,
      "duplicate_policy": "one countable primary unique breakout per duplicate_breakout_key_otx",
      "mean_synthetic_r_resolved_only": -0.5,
      "raw_rows": 86,
      "resolved_synthetic_r_rows": 5
    },
    "blocked_from_promotion_by": [
      "sample floor not met",
      "DSR/PBO/effective-N not computable",
      "same-dataset discovery quarantine",
      "synthetic path-R is not broker actual-R"
    ],
    "decision_reason": "G12 accepts OTX's OTI4B ledger only as tick-recomputed quarantined discovery evidence. It is below sample floor, uses synthetic path-R only, keeps broker actual-R closed, and has explicit duplicate/row exclusions.",
    "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
    "future_unblocker": "Only a future source-complete opening-drive lane with >=200 unique breakout groups and a separate G12 result audit may make any validation-style claim.",
    "packet_id": "OTG0-PKT-062",
    "row_exclusion_evidence": {
      "NOT_COUNTABLE_OPENING_DRIVE_FILTER_FAILED": 77
    },
    "terminal_g12_decision": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "same_bar_or_same_tick_policy": {
    "accepted_policy": "same tick TP and SL is ambiguous and synthetic_r is null; no same-bar guess is accepted.",
    "otx_same_tick_ambiguous_rows": 0
  },
  "source_hash_review": {
    "all_used_files_hashed": true,
    "result_rows_policy": "Rows cite tick-recomputed source policy; source files are in OTX source hash ledger."
  },
  "terminal_result_status_counts": {
    "ENTRY_TOUCHED_THEN_SL": 4,
    "ENTRY_TOUCHED_THEN_TP1": 1,
    "NOT_COUNTABLE_OPENING_DRIVE_FILTER_FAILED": 77,
    "NO_ENTRY_TOUCH_NO_R_SCORED": 4
  },
  "validation_safe": false
}
```
