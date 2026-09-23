# G12 OTI8 CNR061 Duplicate Label Methodology Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI8_CNR061_DUPLICATE_LABEL_METHODOLOGY_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "blocked_row_exclusion": {
    "accepted_rows": 8,
    "blocked_rows": 94,
    "blocked_rows_expected": 94,
    "countable_blocked_overlap": {
      "duplicate_denominator_key_overlap": [],
      "duplicate_group_id_overlap": [],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "countable_blocked_rows": 12,
    "g12_blocked_audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
    "raw_blocked_overlap_disclosed": {
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
    "status": "PASS_EXACT_8_ACCEPTED_94_BLOCKED_AND_ZERO_COUNTABLE_OVERLAP"
  },
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
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
  "generated_at_utc": "2026-05-08T05:43:40Z",
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
  "method_freeze_before_scoring_evidence": {
    "builder_path": "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/build_oti8_cnr061_quarantined_results_2026_05_08.py",
    "method_comment_line": 564,
    "method_freeze_artifact": "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_METHOD_FREEZE_2026-05-08.json",
    "method_freeze_status": "PASS_METHOD_FROZEN",
    "result_ledger_references_method_freeze_artifact": "OTI8_CNR061_METHOD_FREEZE_2026-05-08.json",
    "status": "PASS_METHOD_DECLARED_AND_BUILDER_ORDER_CONFIRMED",
    "terminal_score_call_line": 606
  },
  "methodology_noncomputability": {
    "dsr": {
      "reason": "Eight row-level discovery-only rows collapse to four countable timing-family rows and two duplicate groups; no validation vector or promotion test exists.",
      "status": "not_computable"
    },
    "effective_n": {
      "countable_rows": 4,
      "duplicate_groups": 2,
      "resolved_countable_rows": 2,
      "row_level_rows": 8,
      "status": "tiny_n_discovery_only_not_validation"
    },
    "pbo": {
      "reason": "No model family selection or train/test split is being evaluated; this is one frozen quarantined packet.",
      "status": "not_computable"
    },
    "sample_floor": {
      "current_duplicate_groups": 2,
      "current_row_level_n": 8,
      "required_future_floor": "future CNR target/timing validation needs a separately preregistered sample floor; this packet cannot validate.",
      "sample_floor_pass": false
    },
    "statistical_verdict": "NOT_VALIDATION_NOT_PROMOTION_DSR_PBO_NOT_COMPUTABLE",
    "status": "PASS_NOT_COMPUTABLE_AND_NOT_VALIDATION"
  },
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_oti8_cnr061_post_result_audit_v1",
  "validation_safe": false
}
```
