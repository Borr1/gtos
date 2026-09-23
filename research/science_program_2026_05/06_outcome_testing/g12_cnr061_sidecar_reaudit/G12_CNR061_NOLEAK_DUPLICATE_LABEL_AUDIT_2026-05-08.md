# G12 CNR061 Noleak Duplicate Label Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- `audit_status`: `PASS`

```json
{
  "artifact_family": "G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT",
  "audit_status": "PASS",
  "duplicate_group_join_ambiguity": [
    {
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471",
      "join_status": "AMBIGUOUS_IF_USED_ALONE_USE_RECORD_ID_PLUS_ROW_HASH",
      "otx_records_in_group": 11,
      "sidecar_rows": 2
    },
    {
      "duplicate_group_id": "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222",
      "join_status": "AMBIGUOUS_IF_USED_ALONE_USE_RECORD_ID_PLUS_ROW_HASH",
      "otx_records_in_group": 3,
      "sidecar_rows": 6
    }
  ],
  "duplicate_group_only_join_decision": {
    "decision": "REJECT_DUPLICATE_GROUP_ONLY_JOIN_AS_INSUFFICIENT_FOR_ROW_ACCEPTANCE",
    "reason": "The two duplicate groups contain multiple OTX records and multiple sidecar timing rows; G12 acceptance uses source_row_sha256 plus record_id, not duplicate_group_id alone."
  },
  "duplicate_summary": {
    "duplicate_denominator_key_counts": {
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 1,
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 1,
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3
    },
    "duplicate_group_counts": {
      "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471": 2,
      "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
    },
    "record_id_counts": {
      "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00": 2,
      "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00": 2,
      "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00": 2,
      "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00": 2
    },
    "sidecar_row_count": 8,
    "unique_duplicate_denominator_key_count": 4,
    "unique_duplicate_group_count": 2,
    "unique_record_id_count": 4,
    "unique_sidecar_row_hashes": 8
  },
  "forbidden_packet_row_key_hits": [],
  "forbidden_packet_row_scan_status": "PASS_NO_FORBIDDEN_RESULT_LABEL_KEYS",
  "future_denominator_policy": "The 8 rows are accepted only as input packet rows. A future quarantined result lane must freeze whether denominators are row-level timing-family rows, record-level rows, or duplicate-group-collapsed rows before reading outcomes.",
  "generated_at_utc": "2026-05-08T04:41:16Z",
  "label_boundary": {
    "accepted_label_family": "INPUT_ONLY_GEOMETRY_QUOTE_PATH_HORIZON_NO_RESULTS",
    "blocked_packet_outcomes_opened": false,
    "future_quarantined_result_lane_required_before_any_scoring": true,
    "realized_or_hidden_result_labels_read": false,
    "result_scoring_performed": false
  },
  "live_effect": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_cnr061_sidecar_reaudit_v1",
  "upstream_noleak_evidence": {
    "cnr_matrix_forbidden_scan_status": "PASS_INPUT_MATRIX_HAS_NO_FORBIDDEN_OUTCOME_KEYS",
    "g12_cnr_source_field_scan_status": null,
    "sidecar_noleak_forbidden_status": "PASS"
  },
  "validation_safe": false
}
```
