# OTI8 CNR061 Completion Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

**Verification status:** `PASS`  
**Can mark goal complete:** `true`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI8_CNR061_COMPLETION_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "can_mark_goal_complete": true,
  "canary_calls": 0,
  "concrete_success_criteria": [
    "Build quarantined package over exactly 8 G12-accepted sidecar row hashes.",
    "Exclude 94 blocked rows and freeze countable duplicate denominator policy before terminal scoring.",
    "Score only source-hashed executable quote plus ordered tick path evidence.",
    "Write method/source/no-leak/duplicate/label/methodology/forensics/next-lane/completion artifacts.",
    "Run verifier/tests and preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
  ],
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "generated_at_utc": "2026-05-08T05:11:01Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "objective_restated": "Run OTI8_CNR061_QUARANTINED_RESULT_LANE for OTG0-PKT-061 using only the 8 G12-accepted CNR061 sidecar rows and no broker/account/live/hidden labels.",
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": "LIVE_STATE regenerated; required core docs and latest handoff read and hashed.",
      "requirement": "mandatory_gtos_preflight",
      "status": "PASS"
    },
    {
      "evidence": "OTI8_CNR061_CONTEXT_ANCHOR_2026-05-08.json records HEAD, branch, worktree, runtime dirt, controlling prompt, routes, and searched roots.",
      "requirement": "context_anchor_before_scoring",
      "status": "PASS"
    },
    {
      "evidence": "All present prompt-listed CNR061/CNR/OTX/OTR061 artifacts consumed or hashed; stale missing source-field matrix recorded with replacement.",
      "requirement": "controlling_inputs_read",
      "status": "PASS"
    },
    {
      "evidence": "OTI8_CNR061_METHOD_FREEZE_2026-05-08.json freezes cohort, quote side, terminal order, R scoring, horizon, and duplicate policy before terminal scoring in the builder flow.",
      "requirement": "method_freeze_before_label_review",
      "status": "PASS"
    },
    {
      "evidence": "8 accepted sidecar rows matched G12 decision/readiness ledgers.",
      "requirement": "exact_8_accepted_rows",
      "status": "PASS"
    },
    {
      "evidence": "94 blocked source rows excluded; source row hash and record overlap zero; countable duplicate key/group overlap zero.",
      "requirement": "exact_94_blocked_rows_excluded",
      "status": "PASS_WITH_RAW_DUPLICATE_CONTEXT_OVERLAP_DISCLOSED"
    },
    {
      "evidence": "sidecar/source row hash failures=0; required source missing=0",
      "requirement": "source_hash_recompute",
      "status": "PASS"
    },
    {
      "evidence": "forbidden input key hits=0",
      "requirement": "no_leak_forbidden_key_scan",
      "status": "PASS"
    },
    {
      "evidence": "Result rows are quarantined synthetic ordered-tick path R only; broker actual-R/account/live/hidden path labels unopened.",
      "requirement": "label_family_separation",
      "status": "PASS"
    },
    {
      "evidence": "Countable blocked overlap zero; raw duplicate group overlap intentionally not used for identity.",
      "requirement": "duplicate_denominator_audit",
      "status": "PASS_WITH_RAW_DUPLICATE_CONTEXT_OVERLAP_DISCLOSED"
    },
    {
      "evidence": "OTI8_CNR061_RESULT_LEDGER_2026-05-08.json and row-level JSONL written.",
      "requirement": "row_level_and_countable_results",
      "status": "PASS"
    },
    {
      "evidence": "DSR/PBO/effective-N reported as not computable/tiny-n discovery-only.",
      "requirement": "methodology_report",
      "status": "PASS"
    },
    {
      "evidence": "Resolved tiny-residual target and unresolved May 5 path anatomy recorded.",
      "requirement": "failure_forensics",
      "status": "PASS"
    },
    {
      "evidence": "OTI8_CNR061_G12_POST_RESULT_PROMPT_PACK_2026-05-08.md written.",
      "requirement": "next_lane_prompt",
      "status": "PASS"
    },
    {
      "evidence": "git diff live-surface scan at build time.",
      "requirement": "no_live_surface_changes",
      "status": "PASS"
    }
  ],
  "validation_safe": false,
  "verification_observed_at_utc": "2026-05-08T05:43:40Z",
  "verification_results_observed": {
    "builder_invariant_recompute": {
      "accepted_rows": 8,
      "blocked_rows": 94,
      "countable_blocked_rows": 12,
      "countable_overlap": {
        "duplicate_denominator_key_overlap": [],
        "duplicate_group_id_overlap": []
      },
      "sidecar_hash_failures": [],
      "source_hash_failures": [],
      "status": "PASS"
    },
    "focused_pytest": {
      "command": "C:\\Python313\\python.exe -B -m pytest -p no:cacheprovider C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti8_cnr061_quarantined_results\\test_oti8_cnr061_quarantined_results_2026_05_08.py -q",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": "......                                                                   [100%]\n6 passed in 1.45s"
    },
    "forbidden_live_surface_diff_scan": {
      "changed_live_surface_files": [],
      "command": "git diff --name-only -- src prompts config scripts/canary run_agent.py start_all.bat",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": ""
    },
    "generated_json_jsonl_parse": {
      "parsed_json_count": 10,
      "parsed_json_files": [
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_BLOCKER_AND_NEXT_ACTION_LEDGER_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_COMPLETION_AUDIT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_CONTEXT_ANCHOR_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_METHOD_FREEZE_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT_2026-05-08.json"
      ],
      "parsed_jsonl": [
        {
          "path": "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
          "rows": 8
        }
      ],
      "status": "PASS"
    },
    "generated_quarantine_flag_scan": {
      "forbidden_true_flag_hits": [],
      "missing_or_wrong_promotion_verdict": [],
      "status": "PASS"
    },
    "input_no_leak_duplicate_label_audit": {
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
      "forbidden_input_key_hits": [],
      "no_leak_status": "PASS",
      "status": "PASS"
    },
    "py_compile": {
      "command": "C:\\Python313\\python.exe -B -m py_compile C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti8_cnr061_quarantined_results\\build_oti8_cnr061_quarantined_results_2026_05_08.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti8_cnr061_quarantined_results\\verify_oti8_cnr061_quarantined_results_2026_05_08.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\oti8_cnr061_quarantined_results\\test_oti8_cnr061_quarantined_results_2026_05_08.py",
      "returncode": 0,
      "status": "PASS",
      "stderr_tail": "",
      "stdout_tail": ""
    }
  },
  "verification_status": "PASS"
}
```
