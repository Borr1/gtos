# CNR061 Source Join Map - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- `conclusion`: `PROVEN_FOR_8_G12_READY_ROWS; NON_READY_OTX_OTR_ROWS_RECORDED_IN_BLOCKER_LEDGER`

```json
{
  "artifact_family": "CNR061_SOURCE_JOIN_MAP",
  "conclusion": "PROVEN_FOR_8_G12_READY_ROWS; NON_READY_OTX_OTR_ROWS_RECORDED_IN_BLOCKER_LEDGER",
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
  "generated_at_utc": "2026-05-08T04:11:39Z",
  "join_attempts": [
    {
      "ambiguous_rows": 0,
      "match_widths": {
        "1": 8
      },
      "matched_rows": 8,
      "missing_rows": 0,
      "name": "g12_ready_to_cnr_matrix_by_source_row_sha256",
      "source_rows": 8
    },
    {
      "ambiguous_rows": 0,
      "match_widths": {
        "1": 8
      },
      "matched_rows": 8,
      "missing_rows": 0,
      "name": "g12_ready_to_cnr_source_by_row_sha256",
      "source_rows": 8
    },
    {
      "ambiguous_rows": 0,
      "match_widths": {
        "1": 8
      },
      "matched_rows": 8,
      "missing_rows": 0,
      "name": "g12_ready_to_otx_by_record_id",
      "source_rows": 8
    },
    {
      "ambiguous_rows": 0,
      "match_widths": {
        "1": 8
      },
      "matched_rows": 8,
      "missing_rows": 0,
      "name": "g12_ready_to_g6_input_packet_by_record_id",
      "source_rows": 8
    },
    {
      "matched_records": 51,
      "missing_records": 0,
      "name": "otx_all_to_cnr_e0e1_t0_by_record_id",
      "source_records": 51
    },
    {
      "matched_records": 4,
      "missing_records": 47,
      "name": "otx_all_to_g12_ready_by_record_id",
      "source_records": 51
    },
    {
      "matched_records": 1,
      "missing_records": 0,
      "name": "otr061_to_cnr_e0e1_t0_by_record_id",
      "source_records": 1
    },
    {
      "matched_records": 0,
      "missing_records": 1,
      "name": "otr061_to_g12_ready_by_record_id",
      "source_records": 1
    }
  ],
  "join_failures": [],
  "live_effect": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "cnr061_geometry_horizon_sidecar_v1",
  "source_counts": {
    "cnr_geometry_matrix_pkt061_rows": 8,
    "cnr_source_field_pkt061_e0e1_t0_rows": 102,
    "cnr_source_field_pkt061_e0e1_t0_unique_record_ids": 51,
    "cnr_source_field_pkt061_rows_all_timing_targets": 1020,
    "g12_ready_pkt061_rows": 8,
    "g12_ready_pkt061_unique_record_ids": 4,
    "otr061_recovered_rows": 1,
    "otx_pkt061_proposal_rows": 51,
    "otx_pkt061_rows_with_decision_quote": 50,
    "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": 0,
    "otx_pkt061_rows_with_ordered_path": 50,
    "sidecar_ready_rows": 8,
    "sidecar_unique_record_ids": 4
  },
  "validation_safe": false
}
```
