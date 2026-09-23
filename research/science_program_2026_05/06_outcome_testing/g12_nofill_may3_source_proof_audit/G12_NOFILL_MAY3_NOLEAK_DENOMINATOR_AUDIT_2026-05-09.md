# G12 NOFILL May 3 No-Leak Denominator Audit - 2026-05-09

Generated: `2026-05-09T03:38:51Z`

Decision: `PASS_NO_LABEL_DENOMINATOR_RESULT_VALIDATION_PROMOTION_MOVEMENT`

## May 3 Boundary

```json
{
  "noleak_violations": 0,
  "reject_total_preserved_outside_labels_denominators": 65,
  "result_labels_assigned": 0,
  "rows_moved_into_accepted_denominator": 0,
  "targeted_row_count": 3
}
```

## NOFILL CAT V2 Boundary

```json
{
  "accepted_rows": 225,
  "blocked_exact_rows": 8,
  "duplicate_posture": {
    "accepted_rows": 225,
    "accepted_unique_nofill_duplicate_keys": 182,
    "oti5_canonical_rows_accepted_for_rebuild": 3,
    "oti5_noncanonical_rows_rejected_from_denominator": 39
  },
  "g12_blocker_review_status": "PASS",
  "g12_v2_noleak_status": "PASS",
  "pending_duplicate_review_status": "PASS",
  "pending_noleak_review_status": "PASS",
  "reject_ledger_rows": 65,
  "rejected_rows": 65,
  "row_count": 298
}
```

## Other Row Boundary

```json
{
  "cnr061_noleak_status": "PASS",
  "cnr_next_noleak_status": "ACCEPT_AS_RESEARCH_CONTROL_NOLEAK_DUPLICATE_SAMPLE_BOUNDARY",
  "cnr_t3_blocked_94_status": {
    "blocked_audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
    "blocked_overlap_with_accepted": [],
    "blocked_rows": 94,
    "note": "The 94 blocked rows are verified only as excluded; no blocked-row terminal labels or performance were computed by G12.",
    "packet_hashes_from_accepted_manifest": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "packet_rows_from_blocked_set": [],
    "status": "PASS"
  },
  "g12_blocked_cnr061_rows_status": {
    "audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
    "blocked_rows": 94,
    "live_effect": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "source": "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json",
    "validation_safe": false
  },
  "six_t3_rows_status": {
    "decision": "ACCEPT_LIFECYCLE_EVIDENCE_ONLY",
    "live_effect": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "row_count": 6,
    "source": "G12_CNR061_LIFECYCLE_PACKET_AUDIT_2026-05-08.json",
    "validation_safe": false
  }
}
```

## Forbidden Field/Flag Scan

```json
{
  "files_scanned": [
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_may3_opening_range_market_closure_or_source_proof\\NOFILL_MAY3_SOURCE_PROOF_PACKET_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_may3_opening_range_market_closure_or_source_proof\\NOFILL_MAY3_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_may3_opening_range_market_closure_or_source_proof\\NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_may3_opening_range_market_closure_or_source_proof\\NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_lifecycle_categorical_result_packet_v2_rebuild\\NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_lifecycle_categorical_result_packet_v2_rebuild\\NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_categorical_result_packet_v2_audit\\G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_categorical_result_packet_v2_audit\\G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json",
    "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_cat_v2_pending_source_contract_audit\\G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json"
  ],
  "forbidden_result_or_account_key_hits": [],
  "status": "PASS",
  "unsafe_true_flag_hits": []
}
```

Conclusion: the `65` rejects, six T3/CNR061 lifecycle rows, G12-blocked CNR061 rows, and all rows outside the three May 3 source-control targets remain outside this lane's labels, denominators, result use, validation use, promotion use, and live effect.
