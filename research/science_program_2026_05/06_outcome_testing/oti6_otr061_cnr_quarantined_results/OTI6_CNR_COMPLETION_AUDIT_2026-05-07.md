# OTI6 CNR Completion Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

**Terminal status:** `RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION`  
**Verification status:** `PASS`  
**Can mark goal complete:** `True`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI6_CNR_COMPLETION_AUDIT",
  "broker_actual_r_accessed": false,
  "can_mark_goal_complete": true,
  "canary_calls": 0,
  "concrete_success_criteria": [
    "verify OTG0-PKT-061/G12/OTR061/prereg claims from files",
    "recompute recovered parquet SHA256 and tick coverage",
    "recover original GTOS geometry from source-hashed candidate row",
    "apply CNR_E0 executable market-entry geometry before R scoring",
    "emit terminal result-or-impossibility forensics without forcing a win/loss",
    "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false"
  ],
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "generated_at_utc": "2026-05-07T10:23:43Z",
  "git_head_at_build": "e8747e13f16045154d81e60503d7a12835314452",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_surface_diff_review_at_build": {
    "changed_files_at_build_time": [
      ".context/LIVE_STATE.md"
    ],
    "forbidden_live_surface_changed_files": [],
    "status": "PASS"
  },
  "mt5_order_calls": 0,
  "objective_restated": "Run the OTI6 quarantined result lane for one frozen OTR061 recovered XAUUSD tick packet and determine whether CNR_E0 can be R-scored under preregistered geometry.",
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
      "requirement": "objective_terminal_status",
      "status": "PASS"
    },
    {
      "evidence": ".context/LIVE_STATE.md regenerated and hashed in source report.",
      "requirement": "mandatory_live_state_regenerated_and_read",
      "status": "PASS"
    },
    {
      "evidence": "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md hashed in source report.",
      "requirement": "latest_handoff_read",
      "status": "PASS"
    },
    {
      "evidence": "quick_reference_card.md hashed in source report.",
      "requirement": "quick_reference_read",
      "status": "PASS"
    },
    {
      "evidence": "research_operating_doctrine.md hashed in source report.",
      "requirement": "research_doctrine_read",
      "status": "PASS"
    },
    {
      "evidence": "research_current_state.md hashed in source report.",
      "requirement": "research_current_state_read",
      "status": "PASS"
    },
    {
      "evidence": "goal_session_research_discipline.md hashed in source report.",
      "requirement": "goal_discipline_read",
      "status": "PASS"
    },
    {
      "evidence": "local_heavy_data_inventory.md hashed and local recovered parquet rechecked.",
      "requirement": "local_heavy_data_inventory_read",
      "status": "PASS"
    },
    {
      "evidence": "PASS",
      "requirement": "all_controlling_inputs_read_and_hashed",
      "status": "PASS"
    },
    {
      "evidence": {
        "columns": [
          "ts_utc",
          "time",
          "bid",
          "ask",
          "last",
          "volume",
          "time_msc",
          "flags",
          "volume_real",
          "mt5_symbol"
        ],
        "decision_quote": {
          "ask": 4648.29,
          "bid": 4647.65,
          "decision_rows_lte_071500": 875,
          "executable_decision_price_long_ask": 4648.29,
          "quote_timestamp_utc": "2026-05-06T07:14:59.889000Z"
        },
        "expected_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
        "first_ask": 4646.56,
        "first_bid": 4645.91,
        "first_tick_utc": "2026-05-06T07:10:01.820000Z",
        "last_ask": 4680.59,
        "last_bid": 4680.02,
        "last_tick_utc": "2026-05-06T11:15:59.763000Z",
        "ordered_path": {
          "first_ask": 4648.31,
          "first_bid": 4647.67,
          "first_timestamp_utc": "2026-05-06T07:15:00.634000Z",
          "last_ask": 4680.18,
          "last_bid": 4679.63,
          "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
          "path_end_utc": "2026-05-06T11:15:00Z",
          "path_start_utc": "2026-05-06T07:15:00Z",
          "post_horizon_first_timestamp_utc": "2026-05-06T11:15:00.335000Z",
          "row_count": 88060
        },
        "path": "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
        "required_source_window": {
          "first_timestamp_utc": "2026-05-06T07:10:01.820000Z",
          "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
          "row_count": 88935,
          "window_end_utc": "2026-05-06T11:15:00Z",
          "window_start_utc": "2026-05-06T07:10:00Z"
        },
        "row_count": 89391,
        "sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
        "sha256_matches_expected": true
      },
      "requirement": "otr061_g12_claims_recomputed",
      "status": "PASS"
    },
    {
      "evidence": "shadow_logs/continuation_no_retrace_candidates.jsonl:50",
      "requirement": "original_geometry_recovered_from_source_line",
      "status": "PASS"
    },
    {
      "evidence": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
      "requirement": "cnr_e0_geometry_applied_before_r_scoring",
      "status": "PASS"
    },
    {
      "evidence": "4648.29 > 4582.77",
      "requirement": "long_ask_already_beyond_original_tp1_verified",
      "status": "PASS"
    },
    {
      "evidence": "PREREGISTERED_GEOMETRY_INVALID_TARGET_ALREADY_PASSED_AT_DECISION",
      "requirement": "result_or_impossibility_forensics_written",
      "status": "PASS"
    },
    {
      "evidence": {
        "forbidden_true_flag_hits": [],
        "promotion_verdict_missing_or_wrong": [],
        "status": "PASS"
      },
      "requirement": "no_promotion_flags_preserved",
      "status": "PASS"
    },
    {
      "evidence": "No broker actual-R, account history, live trade results, live order state, blocked-packet outcomes, paid/API/Databento, or MT5 order calls opened.",
      "requirement": "no_forbidden_result_or_live_sources_read",
      "status": "PASS"
    },
    {
      "evidence": {
        "changed_files_at_build_time": [
          ".context/LIVE_STATE.md"
        ],
        "forbidden_live_surface_changed_files": [],
        "status": "PASS"
      },
      "requirement": "forbidden_live_surface_diff_absent_at_build",
      "status": "PASS"
    },
    {
      "evidence": "NOT_VALIDATION_NOT_COMPUTABLE_GEOMETRY_IMPOSSIBLE_SINGLE_RECORD",
      "requirement": "dsr_pbo_effective_n_reported",
      "status": "PASS"
    }
  ],
  "required_artifacts_written": [
    "OTI6_CNR_COMPLETION_AUDIT_2026-05-07.json",
    "OTI6_CNR_COMPLETION_AUDIT_2026-05-07.md",
    "OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.json",
    "OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.md",
    "OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.json",
    "OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.md",
    "OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
    "OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md",
    "OTI6_CNR_METHOD_FREEZE_2026-05-07.json",
    "OTI6_CNR_METHOD_FREEZE_2026-05-07.md",
    "OTI6_CNR_RESULT_LEDGER_2026-05-07.json",
    "OTI6_CNR_RESULT_LEDGER_2026-05-07.md",
    "OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.json",
    "OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.md",
    "OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md",
    "build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
    "test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
    "verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py"
  ],
  "safety_scan_at_build": {
    "forbidden_true_flag_hits": [],
    "promotion_verdict_missing_or_wrong": [],
    "status": "PASS"
  },
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
  "validation_safe": false,
  "verification_commands_required_after_build": [
    "JSON parse all generated OTI6 JSON artifacts",
    "python -B -m py_compile build_oti6_otr061_cnr_quarantined_results_2026_05_07.py test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
    "python -B -m pytest -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/test_oti6_otr061_cnr_quarantined_results_2026_05_07.py -q",
    "focused OTR061/G12 control tests",
    "scan generated outputs for NO_PROMOTION_VERDICT and forbidden true safety flags",
    "git diff forbidden live-surface scan"
  ],
  "verification_observed_at_utc": "2026-05-07T10:31:25Z",
  "verification_results_observed": {
    "focused_oti6_pytest": {
      "command": "C:\\Python313\\python.exe -B -m pytest -p no:cacheprovider C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\test_oti6_otr061_cnr_quarantined_results_2026_05_07.py -q",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": ".......                                                                  [100%]\n7 passed in 1.14s"
    },
    "focused_otr061_g12_pytest": {
      "command": "C:\\Python313\\python.exe -B -m pytest -p no:cacheprovider C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\test_otr061_xau_tick_recovery_2026_05_07.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\test_g12_oti5_otr061_post_audit_2026_05_07.py -q",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": "...............                                                          [100%]\n15 passed in 0.64s"
    },
    "forbidden_live_surface_diff_scan": {
      "changed_live_surface_files": [],
      "command": "git diff --name-only -- src prompts config scripts run_agent.py start_all.bat",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": ""
    },
    "forbidden_true_flag_scan": {
      "forbidden_true_flag_hits": [],
      "status": "PASS"
    },
    "generated_json_parse": {
      "parsed_count": 8,
      "parsed_files": [
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_COMPLETION_AUDIT_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHOD_FREEZE_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json"
      ],
      "status": "PASS"
    },
    "no_promotion_verdict_scan": {
      "missing_no_promotion_verdict_files": [],
      "status": "PASS"
    },
    "py_compile": {
      "command": "C:\\Python313\\python.exe -B -m py_compile C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\build_oti6_otr061_cnr_quarantined_results_2026_05_07.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti6_otr061_cnr_quarantined_results\\test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": ""
    }
  },
  "verification_status": "PASS"
}
```
