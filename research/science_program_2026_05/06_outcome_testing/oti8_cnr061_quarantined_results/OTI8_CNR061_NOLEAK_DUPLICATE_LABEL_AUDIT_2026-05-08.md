# OTI8 CNR061 No-Leak Duplicate Label Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT",
  "blocked_exclusion": {
    "accepted_rows": 8,
    "blocked_rows": 94,
    "blocked_rows_expected": 94,
    "countable_blocked_rows": 12,
    "countable_overlap": {
      "duplicate_denominator_key_overlap": [],
      "duplicate_group_id_overlap": [],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "raw_overlap_disclosed": {
      "duplicate_denominator_key_overlap": [
        "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1",
        "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1"
      ],
      "duplicate_group_id_overlap": [
        "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471"
      ],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "status": "PASS_EXACT_8_ACCEPTED_94_BLOCKED_UNDER_SOURCE_HASH_AND_COUNTABLE_DUPLICATE_POLICY"
  },
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "duplicate_policy": {
    "countable_blocked_overlap": {
      "duplicate_denominator_key_overlap": [],
      "duplicate_group_id_overlap": [],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "countable_overlap_status": "PASS_ZERO_COUNTABLE_BLOCKED_OVERLAP",
    "countable_policy": "Use CNR/G12 countable_denominator_row from source rows: one countable primary row per packet/duplicate_group/timing_model/target_model; duplicate-context rows are retained row-level but excluded from countable aggregate.",
    "do_not_join_on_duplicate_group_alone": true,
    "raw_duplicate_overlap_disclosure": {
      "duplicate_denominator_key_overlap": [
        "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1",
        "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1"
      ],
      "duplicate_group_id_overlap": [
        "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471"
      ],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "row_level_all_eight_reported": true
  },
  "forbidden_input_key_hits": [],
  "g12_duplicate_summary": {
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
  "generated_at_utc": "2026-05-08T05:11:01Z",
  "label_family_separation": {
    "accepted_input_label_family": "INPUT_ONLY_GEOMETRY_QUOTE_PATH_HORIZON_NO_RESULTS",
    "broker_actual_r_opened": false,
    "hidden_path_labels_opened": false,
    "result_label_family": "QUARANTINED_SYNTHETIC_ORDERED_TICK_PATH_R_DISCOVERY_ONLY",
    "synthetic_path_r_is_not_broker_actual_r": true
  },
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "no_leak_status": "PASS",
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
