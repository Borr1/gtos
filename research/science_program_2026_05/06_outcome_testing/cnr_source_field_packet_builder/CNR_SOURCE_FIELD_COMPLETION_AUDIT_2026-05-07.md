# CNR Source Field Completion Audit - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_SOURCE_FIELD_COMPLETION_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "duplicate_summary": {
    "by_packet": {
      "OTG0-PKT-060": {
        "countable_rows": 400,
        "rows": 1600,
        "unique_denominator_keys": 400,
        "unique_primary_duplicate_groups": 20
      },
      "OTG0-PKT-061": {
        "countable_rows": 160,
        "rows": 1020,
        "unique_denominator_keys": 160,
        "unique_primary_duplicate_groups": 8
      },
      "OTG0-PKT-062": {
        "countable_rows": 380,
        "rows": 1720,
        "unique_denominator_keys": 380,
        "unique_primary_duplicate_groups": 19
      },
      "OTG0-PKT-063": {
        "countable_rows": 420,
        "rows": 1720,
        "unique_denominator_keys": 420,
        "unique_primary_duplicate_groups": 21
      },
      "OTG0-PKT-066": {
        "countable_rows": 120,
        "rows": 140,
        "unique_denominator_keys": 120,
        "unique_primary_duplicate_groups": 6
      }
    },
    "duplicate_context_rows": 4720,
    "duplicate_policy": "one countable row per duplicate_group_id per packet/timing_model_family/target_model_family",
    "stability_status": "PASS_DUPLICATE_DENOMINATOR_STABLE",
    "total_rows": 6200,
    "unique_denominator_keys": 1480
  },
  "forbidden_scan_summary": {
    "forbidden_tokens": [
      "synthetic_path_r",
      "synthetic_r",
      "broker_actual_r",
      "account_history",
      "live_trade_result",
      "live_trade_results",
      "target_hit_timestamp",
      "stop_hit_timestamp",
      "post_entry_mfe",
      "post_entry_mae",
      "mfe",
      "mae",
      "result_status",
      "result_ledger",
      "hit_sl",
      "hit_tp1",
      "first_touch_times",
      "path_label",
      "later_path_label",
      "continuation_resolution_status",
      "outcome_status",
      "synthetic_path"
    ],
    "hit_count": 0,
    "hits": [],
    "scan_status": "PASS",
    "truncated": false
  },
  "generated_at_utc": "2026-05-07T16:38:18Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "objective_restated": "Build source-hashed input-only CNR timing source-field packet artifacts or exact blockers for future G12/G0 audit without opening outcomes or touching live trading behavior.",
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_summary": {
    "blocked_rows": 6098,
    "packet_blocker_counts": {
      "OTG0-PKT-060": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1574,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 26
      },
      "OTG0-PKT-061": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1012,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 8
      },
      "OTG0-PKT-062": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1688,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 32
      },
      "OTG0-PKT-063": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1688,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 32
      },
      "OTG0-PKT-066": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 136,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 4
      }
    },
    "quote_extracted_rows": 2368,
    "ready_input_only_rows": 102,
    "ready_scope_note": "Rows are input-only source-field packets. Ready means source fields are present for G12/G0 audit, not outcome scoring or validation.",
    "row_count": 6200,
    "target_status_counts": {
      "CNR_T0_ORIGINAL_TP1": {
        "BOUND_INPUT_ONLY_ORIGINAL_TP1": 1550
      },
      "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
        "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET": 1550
      },
      "CNR_T2_ASOF_STRUCTURAL_LEVEL": {
        "BLOCKED_STRUCTURED_ASOF_LEVEL_SOURCE_NOT_BOUND": 1550
      },
      "CNR_T3_TIMEBOX_TERMINAL": {
        "BLOCKED_TERMINAL_TIMEBOX_POLICY_NOT_BOUND": 1550
      }
    },
    "timing_status_counts": {
      "CNR_E0_DECISION_CLOSE_MARKET": {
        "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 56,
        "QUOTE_EXTRACTED_SOURCE_HASHED": 1184
      },
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": {
        "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 56,
        "QUOTE_EXTRACTED_SOURCE_HASHED": 1184
      },
      "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK": {
        "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 1240
      },
      "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW": {
        "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 1240
      },
      "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER": {
        "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 1240
      }
    }
  },
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": {
        "branch": "main",
        "git_status_short": "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied\nwarning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied\n M pipeline_state/shadow_observer_state.json\n M research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.json\n M research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md\n M research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.json\n M research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md\n M research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.json\n M research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md\n M research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.json\n M research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md\n M shadow_logs/candidate_features_log.jsonl\n M shadow_logs/context_control_ledger.jsonl\n M shadow_logs/cusum_candidate_rate_daily.csv\n M shadow_logs/d1_bias_lag.jsonl\n M shadow_logs/direction_emission_xau_audit.jsonl\n M shadow_logs/displacement_events.jsonl\n M shadow_logs/dumb_baseline_hypotheticals.jsonl\n M shadow_logs/fvg_ob_confluence.jsonl\n M shadow_logs/heartbeat_flatten_events.jsonl\n M shadow_logs/liquidity_distance_log.jsonl\n M shadow_logs/notification_queue_dead_zone_status.jsonl\n M shadow_logs/ob_continuation_daily.csv\n M shadow_logs/pending_limit_lifecycle.jsonl\n M shadow_logs/prefill_delivery_path.jsonl\n M shadow_logs/proximity_shadow_log.jsonl\n M shadow_logs/regime_classifications.jsonl\n M shadow_logs/session_volatility_sweep_status.jsonl\n M shadow_logs/shadow_observer_status.jsonl\n M shadow_logs/sl_beyond_ob_decisions.jsonl\n M shadow_logs/storage_retention_status.jsonl\n M shadow_logs/strategy_follow_candidates.jsonl\n M shadow_logs/strategy_follow_evaluations.jsonl\n M shadow_logs/structure_detector_divergences.jsonl\n M shadow_logs/touch_count_gate_decisions.jsonl\n M shadow_logs/v2b_forward_pairs.jsonl",
        "head": "39727b159ff064844d2f03a1fe7c1c7eebff343b",
        "latest_handoff_read": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        "live_state_regenerated": true,
        "research_current_state_fresh_in_live_state": true
      },
      "requirement": "mandatory GTOS preflight",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR_2026-05-07.json",
      "requirement": "context anchor for compaction resilience",
      "status": "PASS"
    },
    {
      "evidence": "source_hash_manifest includes all preregistration JSON control inputs",
      "requirement": "read controlling preregistration inputs",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW_2026-05-07.json",
      "requirement": "search approved local/heavy/source roots",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
      "requirement": "build input-only packet rows or exact blockers",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_2026-05-07.json",
      "requirement": "source hash consumed files",
      "status": "PASS"
    },
    {
      "evidence": "builder excludes result/quarantine directories and does not compute R; anti-boxing review discloses quarantined broad-search output not used",
      "requirement": "do not score outcomes/open result quarantine dirs",
      "status": "PASS_WITH_CAUTION"
    },
    {
      "evidence": "all generated artifacts carry required flags",
      "requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
      "status": "PASS"
    },
    {
      "evidence": "builder writes only lane artifacts; final git diff must confirm",
      "requirement": "no forbidden live-surface edits",
      "status": "PENDING_FINAL_DIFF_CHECK"
    },
    {
      "evidence": "verify/test scripts added in same lane",
      "requirement": "verification scripts/tests practical",
      "status": "PENDING_RUN"
    }
  ],
  "sample_floor_summary": {
    "current_unique_primary_duplicate_groups": 74,
    "duplicate_report_ref": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
    "expansion_status": "LOCAL_TICK_QUOTE_EXTRACTION_ATTEMPTED_FOR_ALL_SOURCE_RECORDS; remaining blockers are source-field/schema blockers, not worktree absence",
    "ready_unique_primary_duplicate_groups": 30,
    "sample_floor_policy": {
      "aggregate_descriptive": ">=30 unique duplicate groups",
      "single_packet": "single-row result-or-impossibility can be audited by G12/G0 only after input packet audit",
      "validation_dossier": ">=50 unique duplicate groups with DSR/PBO/effective-N computable or explicitly not_computable"
    },
    "searched_root_count": 9,
    "searched_roots": [
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 120,
        "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent",
        "search_status": "SEARCHED",
        "truncated": true
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 120,
        "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing",
        "search_status": "SEARCHED",
        "truncated": true
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 120,
        "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
        "search_status": "SEARCHED",
        "truncated": true
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 62,
        "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
        "search_status": "SEARCHED",
        "truncated": false
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 69,
        "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external",
        "search_status": "SEARCHED",
        "truncated": false
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 6,
        "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
        "search_status": "SEARCHED",
        "truncated": false
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 120,
        "root": "C:\\tmp",
        "search_status": "SEARCHED",
        "truncated": true
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 120,
        "root": "C:\\Users\\MSI\\Documents",
        "search_status": "SEARCHED",
        "truncated": true
      },
      {
        "denied_or_walk_errors": [],
        "exists": true,
        "result_count_returned": 14,
        "root": "C:\\SierraChart\\Data",
        "search_status": "SEARCHED",
        "truncated": false
      }
    ],
    "small_n_handling": "small n blocks validation claims only; packet build/search/extraction continued across approved roots"
  },
  "stop_condition_status": "ACHIEVED_INPUT_ONLY_PACKETS_WITH_EXACT_SOURCE_BLOCKERS_PENDING_EXTERNAL_VERIFICATION_COMMANDS",
  "validation_safe": false
}
```
