# OTI3 USDJPY Completion Audit - 2026-05-08

```json
{
  "artifact_family": "OTI3_USDJPY_COMPLETION_AUDIT",
  "can_mark_goal_complete": true,
  "completion_status": "PASS_VERIFIED",
  "forbidden_surfaces": {
    "account_history_accessed": false,
    "broker_actual_r_accessed": false,
    "live_trade_result_accessed": false,
    "mt5_account_calls": 0,
    "mt5_history_calls": 0,
    "mt5_order_calls": 0,
    "mt5_position_calls": 0,
    "order_send_calls": 0,
    "paid_api_or_databento_calls": 0
  },
  "generated_at_utc": "2026-05-08T14:57:32Z",
  "lane_id": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
  "live_effect": false,
  "next_unblockers": {
    "entry_first_rows": "Route to a separate fill/path categorical contract if those rows should be classified beyond no-fill closure.",
    "missing_tick_rows": "No remaining rows if extraction succeeds; otherwise exact USDJPY bid/ask tick source is required for the listed dates.",
    "protective_first_rows": "No rows observed unless verifier artifacts show otherwise; if present, define a separate protective-before-entry no-fill category before labeling."
  },
  "no_r_performance_scoring": true,
  "objective_restatement": "Resolve 69 USDJPY price-only no-fill rows to source-hashed quote/tick categorical lifecycle evidence or exact blockers under a conservative parser contract.",
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": "generate_live_state ran; LIVE_STATE, latest handoff, quick reference, doctrine, research_current_state, goal_session_research_discipline, local_heavy_data_inventory, prompt pack, router context/ledgers were read.",
      "requirement": "mandatory_gtos_preflight",
      "status": "PASS"
    },
    {
      "evidence": "rows=69 decisions=69",
      "requirement": "row_universe_69",
      "status": "PASS"
    },
    {
      "evidence": "eligible=58 blocked=11 remaining_access=[]",
      "requirement": "quote_tick_sources_or_exact_blockers",
      "status": "PASS"
    },
    {
      "evidence": "Only USDJPY 2026-04-17 and 2026-04-20 are eligible for MT5 copy_ticks_range extraction; no other date uses MT5 extraction.",
      "requirement": "approved_missing_date_route_only",
      "status": "PASS"
    },
    {
      "evidence": "Extraction ledger records initialize/copy_ticks_range/shutdown only; account/history/order/position/order_send counters are false/zero.",
      "requirement": "no_account_history_order_calls",
      "status": "PASS"
    },
    {
      "evidence": "PASS",
      "requirement": "source_hashes_required",
      "status": "PASS"
    },
    {
      "evidence": "duplicate_keys=[] asof_violations=[]",
      "requirement": "duplicate_and_asof_checks",
      "status": "PASS"
    },
    {
      "evidence": "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
      "requirement": "flags_preserved",
      "status": "PASS"
    },
    {
      "evidence": "forbidden_hits=0",
      "requirement": "no_r_performance_or_live_labels",
      "status": "PASS"
    },
    {
      "evidence": {
        "changed_files": [
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_RECORDS_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.md",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_VERIFICATION_2026-05-08.json",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/__init__.py",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/build_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08.py",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/test_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08.py",
          "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/verify_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08.py"
        ],
        "check_scope": "latest committed lane diff",
        "live_surface_files": [],
        "status": "PASS",
        "workspace_changed_path_count": 191,
        "workspace_changed_path_sample": [
          ".context/05_operations/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.md",
          ".context/LIVE_STATE.md",
          "knowledge_base/index/trade_record_inventory_index_2026-05-05.json",
          "pipeline_state/shadow_observer_state.json",
          "pipeline_state/sierra_depth_enrichment_checkpoint.json",
          "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json",
          "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
          "research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.json",
          "research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md",
          "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json",
          "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md",
          "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json",
          "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.md",
          "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.json",
          "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md",
          "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.json",
          "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md",
          "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json",
          "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md",
          "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json"
        ]
      },
      "requirement": "no_live_trading_surface_change",
      "status": "PASS"
    }
  ],
  "repo_head": "9cad99c83bc12bf84a569ac82d579aa6ee978dc9",
  "row_outcome": {
    "blocked_exact": 11,
    "categorical_label_counts": {
      "nofill_terminal_before_entry": 58
    },
    "exact_blocker_counts": {
      "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 7,
      "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 4
    },
    "quote_tick_categorical_contract_evidence": 58,
    "total_rows": 69
  },
  "schema_version": "oti3_usdjpy_price_only_quote_or_tick_contract_v1",
  "scope": "source_correction_or_contract_revision_only",
  "source_search_conclusion": "quote_tick_sources_present_for_all_needed_dates",
  "validation_safe": false,
  "verification": {
    "artifact_family": "OTI3_USDJPY_VERIFICATION",
    "can_mark_goal_complete": true,
    "forbidden_hits": [],
    "hash_mismatches": [],
    "issues": [],
    "live_effect": false,
    "live_surface_diff_check": {
      "changed_files": [
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_RECORDS_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_VERIFICATION_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/__init__.py",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/build_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08.py",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/test_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08.py",
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/verify_oti3_usdjpy_price_only_quote_or_tick_contract_2026_05_08.py"
      ],
      "check_scope": "latest committed lane diff",
      "live_surface_files": [],
      "status": "PASS",
      "workspace_changed_path_count": 191,
      "workspace_changed_path_sample": [
        ".context/05_operations/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.md",
        ".context/LIVE_STATE.md",
        "knowledge_base/index/trade_record_inventory_index_2026-05-05.json",
        "pipeline_state/shadow_observer_state.json",
        "pipeline_state/sierra_depth_enrichment_checkpoint.json",
        "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json",
        "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
        "research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.json",
        "research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md",
        "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json",
        "research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md",
        "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.json",
        "research/program_control/LIVE_SHADOW_OPPORTUNITY_SUMMARY_2026-05-04.md",
        "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.json",
        "research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md",
        "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.json",
        "research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md",
        "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json",
        "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md",
        "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json"
      ]
    },
    "missing_hash_paths": [],
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "row_counts": {
      "blocked_exact": 11,
      "eligible_contract_evidence": 58,
      "total": 69
    },
    "source_hash_modes": {
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\USDJPY_M1.csv": "working_tree_file",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet": "working_tree_file",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_categorical_result_packet\\NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_categorical_result_packet\\NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_closure_source_packet\\NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_result_contract_design\\NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_result_contract_design\\NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_2026-05-08.json": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet": "working_tree_file",
      "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet": "working_tree_file"
    },
    "summary_counts": {
      "blocked_exact_rows": 11,
      "categorical_label_counts": {
        "nofill_terminal_before_entry": 58
      },
      "eligible_contract_evidence_rows": 58,
      "exact_blocker_counts": {
        "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 7,
        "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 4
      }
    },
    "validation_safe": false,
    "verification_status": "PASS"
  }
}
```
