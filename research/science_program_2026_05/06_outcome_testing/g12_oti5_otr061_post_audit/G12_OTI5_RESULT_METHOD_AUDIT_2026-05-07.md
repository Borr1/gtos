# G12 OTI5 Result Method Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Verifies the frozen subset, duplicate denominator, label-family separation, source-hash controls, and non-computable validation statistics.
- The negative OTI5 result is accepted only as quarantined discovery evidence.

```json
{
  "artifact_family": "G12_OTI5_RESULT_METHOD_AUDIT",
  "artifact_hashes": {
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_COMPLETION_AUDIT_2026-05-07.json": "8013d5e2fabe34ab93455359690dc55fca2df7c2e930baa4332337a11b2ea126",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json": "bad5d01825ff094f4e7db50a8d821e474d4462cdba3f8fb5fbf20af7f17a29dc",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_2026-05-07.json": "b5f8ca82c3e3e549e6c4f768fe88ed7750c27fb73a4467f23c4874f2bd2accfd",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json": "17c5c428913cb731e8793e9ac8f87d0474fd65f64d90686f47e1dec10afdea13",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_METHOD_FREEZE_2026-05-07.json": "1070c7fb034c191b5aaef3a39640a09dddebdf182acbdae985b6fcb24e8dddb4",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_RESULT_LEDGER_2026-05-07.json": "b49369d55d080206528f0068fa44dd7c8b86618cd3675b11aa814c93dc3a169f",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl": "22c71896a12735def2ce065167ab12f779e7aaad92412ab23288d52bbc07a0a6",
    "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json": "9999f727c7e6fe4235e2975d89e8fa49cb6b04965544cf8220ba7556b36a7200"
  },
  "audit_verdict": "PASS_ACCEPT_DISCOVERY_ONLY_CONTROLS_SOUND",
  "control_gates": {
    "all_consumed_files_hashed": true,
    "blocked_packet_outcomes_opened": false,
    "broker_actual_r_opened": false,
    "duplicate_denominator_policy_verdict": "PASS_DUPLICATE_DENOMINATOR_FROZEN_BEFORE_SCORING",
    "duplicate_primary_selection_rule": "Sort by decision_asof_utc, then record_id; keep rank 1 as countable primary.",
    "forbidden_input_key_hit_count": 0,
    "label_family_gate_pass": true,
    "live_trade_results_opened": false,
    "local_heavy_data_inventory_enforced": true,
    "material_source_hash_failure_count": 0,
    "source_gate_pass": true
  },
  "cusum_partition_metrics_primary_rows": {
    "failure_rate_reduction_has_changepoint_vs_no_changepoint": 0.14285714,
    "has_changepoint_count_gt_0": {
      "failure_rate_resolved_terminal": 0.85714286,
      "mean_synthetic_r_resolved_only": -0.64285714,
      "median_synthetic_r_resolved_only": -1.0,
      "no_entry_rows": 6,
      "record_count": 13,
      "resolved_synthetic_r_rows": 7,
      "terminal_status_counts": {
        "ENTRY_TOUCHED_THEN_SL": 6,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 6
      },
      "total_synthetic_r_resolved_only": -4.5,
      "win_rate_resolved_terminal": 0.14285714
    },
    "interpretation_boundary": "Descriptive quarantined discovery partition only; no threshold selection, validation, or promotion claim.",
    "mean_r_delta_has_changepoint_vs_no_changepoint": 0.35714286,
    "no_changepoint_count_eq_0": {
      "failure_rate_resolved_terminal": 1.0,
      "mean_synthetic_r_resolved_only": -1.0,
      "median_synthetic_r_resolved_only": -1.0,
      "no_entry_rows": 2,
      "record_count": 4,
      "resolved_synthetic_r_rows": 2,
      "terminal_status_counts": {
        "ENTRY_TOUCHED_THEN_SL": 2,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 2
      },
      "total_synthetic_r_resolved_only": -2.0,
      "win_rate_resolved_terminal": 0.0
    }
  },
  "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
  "frozen_subset": {
    "excluded_ids_match_duplicate_report": true,
    "excluded_record_ids": [
      "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00"
    ],
    "raw_rows": 86,
    "source_ready_rows": 81
  },
  "generated_at_utc": "2026-05-07T09:59:27Z",
  "live_effect": false,
  "methodology_terminal_review": {
    "hidden_validation_route": "NO_HONEST_ROUTE_FROM_CURRENT_FILES",
    "reason": "Only 17 duplicate-primary groups and 9 resolved synthetic rows exist; there is no unseen fold matrix, no broker actual-R opening, no train/test variant matrix, and the lane is explicitly discovery-only.",
    "sample_floor_review": {
      "broker_actual_r_floor": 100,
      "broker_actual_r_opened": false,
      "current_countable_synthetic_groups": 17,
      "status": "BELOW_SAMPLE_FLOOR_DISCOVERY_ONLY",
      "synthetic_row_floor": 300
    },
    "statistical_verdict": "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR"
  },
  "metric_summary": {
    "failure_rate_resolved_terminal": 0.88888889,
    "mean_synthetic_r_resolved_only": -0.72222222,
    "median_synthetic_r_resolved_only": -1.0,
    "no_entry_rows": 8,
    "record_count": 17,
    "resolved_synthetic_r_rows": 9,
    "terminal_status_counts": {
      "ENTRY_TOUCHED_THEN_SL": 8,
      "ENTRY_TOUCHED_THEN_TP1": 1,
      "NO_ENTRY_TOUCH_NO_R_SCORED": 8
    },
    "total_synthetic_r_resolved_only": -6.5,
    "win_rate_resolved_terminal": 0.11111111
  },
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-063",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
  "validation_safe": false,
  "verified_claims": [
    {
      "claim": "raw_total_packet_rows",
      "expected": 86,
      "observed": 86,
      "status": "PASS"
    },
    {
      "claim": "source_ready_rows",
      "expected": 81,
      "observed": 81,
      "status": "PASS"
    },
    {
      "claim": "g12_blocked_rows_excluded",
      "expected": 5,
      "observed": 5,
      "status": "PASS"
    },
    {
      "claim": "unique_duplicate_groups",
      "expected": 17,
      "observed": 17,
      "status": "PASS"
    },
    {
      "claim": "duplicate_primary_rows",
      "expected": 17,
      "observed": 17,
      "status": "PASS"
    },
    {
      "claim": "resolved_synthetic_tick_r_rows",
      "expected": 9,
      "observed": 9,
      "status": "PASS"
    },
    {
      "claim": "terminal_sl_count",
      "expected": 8,
      "observed": 8,
      "status": "PASS"
    },
    {
      "claim": "terminal_tp1_count",
      "expected": 1,
      "observed": 1,
      "status": "PASS"
    },
    {
      "claim": "terminal_no_entry_count",
      "expected": 8,
      "observed": 8,
      "status": "PASS"
    },
    {
      "claim": "mean_resolved_synthetic_r",
      "expected": -0.72222222,
      "observed": -0.72222222,
      "status": "PASS"
    },
    {
      "claim": "dsr_status",
      "expected": "not_computable",
      "observed": "not_computable",
      "status": "PASS"
    },
    {
      "claim": "pbo_status",
      "expected": "not_computable",
      "observed": "not_computable",
      "status": "PASS"
    },
    {
      "claim": "effective_n_status",
      "expected": "not_computable_for_validation",
      "observed": "not_computable_for_validation",
      "status": "PASS"
    }
  ]
}
```
