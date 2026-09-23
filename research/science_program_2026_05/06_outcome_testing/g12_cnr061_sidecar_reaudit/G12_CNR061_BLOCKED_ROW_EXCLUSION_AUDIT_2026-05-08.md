# G12 CNR061 Blocked Row Exclusion Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- `audit_status`: `PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED`

```json
{
  "artifact_family": "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT",
  "audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
  "blocked_by_pre_entry_target_already_passed_check": {
    "NOT_COMPUTED_QUOTE_BLOCKED": 2,
    "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING": 92
  },
  "blocked_by_quote_source_status": {
    "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 2,
    "QUOTE_EXTRACTED_SOURCE_HASHED": 92
  },
  "blocked_by_symbol": {
    "US30_cash": 2,
    "USDJPY": 2,
    "XAGUSD": 88,
    "XAUUSD": 2
  },
  "blocked_summary": {
    "blocked_e0e1_t0_rows": 94,
    "by_pre_entry_target_already_passed_check": {
      "NOT_COMPUTED_QUOTE_BLOCKED": 2,
      "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING": 92
    },
    "by_quote_source_status": {
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 2,
      "QUOTE_EXTRACTED_SOURCE_HASHED": 92
    },
    "by_symbol": {
      "US30_cash": 2,
      "USDJPY": 2,
      "XAGUSD": 88,
      "XAUUSD": 2
    },
    "otr061_recovered_rows_not_ready": 2
  },
  "exclusion_counts": {
    "accepted_plus_blocked": 102,
    "accepted_sidecar_rows": 8,
    "accepted_source_hashes": 8,
    "accepted_unique_record_ids": 4,
    "blocked_rows": 94,
    "blocked_source_hashes": 94,
    "blocked_unique_record_ids": 47,
    "cnr_source_e0e1_t0_rows": 102,
    "source_hash_union": 102
  },
  "generated_at_utc": "2026-05-08T04:41:16Z",
  "live_effect": false,
  "otr061_recovery_block_status": {
    "all_otr061_rows_have_source_hashed_quote_status": true,
    "all_otr061_rows_target_already_passed": true,
    "blocked_record_ids": [
      "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
    ],
    "matched_otr061_rows_in_blocked_set": 2,
    "otr061_rows": [
      {
        "minimum_unblocker": "input-only invalid-clearing policy for market-entry rows where the source-hashed executable quote is already past original TP1",
        "otr061_recovery_join_status": "MATCHED_OTR061_RECOVERY_RECORD",
        "pre_entry_target_already_passed_check": "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING",
        "quote_source_status": "QUOTE_EXTRACTED_SOURCE_HASHED",
        "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "minimum_unblocker": "input-only invalid-clearing policy for market-entry rows where the source-hashed executable quote is already past original TP1",
        "otr061_recovery_join_status": "MATCHED_OTR061_RECOVERY_RECORD",
        "pre_entry_target_already_passed_check": "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING",
        "quote_source_status": "QUOTE_EXTRACTED_SOURCE_HASHED",
        "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      }
    ],
    "reason": "TARGET_ALREADY_PASSED_INPUT_GATE_NOT_MISSING_TICK_EVIDENCE"
  },
  "outcome_review_opened": false,
  "overlap_checks": {
    "accepted_blocked_record_id_overlap": [],
    "accepted_blocked_source_hash_overlap": [],
    "cnr_source_hashes_missing_from_union": [],
    "union_hashes_not_in_cnr_source": []
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_cnr061_sidecar_reaudit_v1",
  "validation_safe": false
}
```
