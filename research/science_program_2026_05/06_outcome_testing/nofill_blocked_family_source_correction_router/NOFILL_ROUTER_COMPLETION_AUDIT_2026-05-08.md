# NOFILL Router Completion Audit

Generated: 2026-05-08T14:27:01Z

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Route all 246 G12-blocked no-fill categorical rows to exact source-correction, contract-revision, access/source request, or impossibility decisions without opening result/performance/live lanes.

## Prompt-To-Artifact Checklist

| requirement | status | evidence |
| --- | --- | --- |
| mandatory_gtos_preflight | PASS_RECORDED | NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.json |
| split_246_blocked_rows_by_family | PASS | NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.json |
| route_every_blocked_row | PASS | NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json |
| search_local_heavy_data_and_prior_artifacts | PASS | NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json |
| request_access_if_needed | PASS | NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.json |
| write_next_prompt_packs_only_for_source_safe_or_contract_revision_lanes | PASS | ['OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md', 'OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md', 'OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md', 'OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md', 'OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md'] |
| record_failure_learning | PASS | NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json |
| preserve_no_promotion_and_false_flags | PASS | verify_nofill_blocked_family_source_correction_router_2026_05_08.py |
| no_live_trading_surface_changes | PASS | git diff/name-only scope check |

## Verification Evidence

{
  "access_request_rows": 7,
  "command_checks": [
    {
      "command": "python -m py_compile C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\build_nofill_blocked_family_source_correction_router_2026_05_08.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\verify_nofill_blocked_family_source_correction_router_2026_05_08.py C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\test_nofill_blocked_family_source_correction_router_2026_05_08.py",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "python -m pytest C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\test_nofill_blocked_family_source_correction_router_2026_05_08.py -q",
      "returncode": 0,
      "stderr": "",
      "stdout": "....                                                                     [100%]\n============================== warnings summary ===============================\n..\\..\\AppData\\Roaming\\Python\\Python313\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\MSI\\AppData\\Roaming\\Python\\Python313\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_cache\\v\\cache\\nodeids: [WinError 5] Access is denied: 'C:\\\\Users\\\\MSI\\\\Documents\\\\ai-trading-agent\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n4 passed, 1 warning in 0.11s"
    }
  ],
  "diff_scope_check": {
    "changed_files": [
      ".context/00_core/research_current_state.md",
      ".context/LIVE_STATE.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_GOAL_PROMPT_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_COMPLETION_AUDIT_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_COMPLETION_AUDIT_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_NEXT_PROMPT_PACK_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/build_nofill_blocked_family_source_correction_router_2026_05_08.py",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/test_nofill_blocked_family_source_correction_router_2026_05_08.py",
      "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/verify_nofill_blocked_family_source_correction_router_2026_05_08.py"
    ],
    "checked_scope": "committed_diff_HEAD_parent",
    "forbidden_changed_files": [],
    "status": "PASS",
    "workspace_changed_path_count_observed": 185,
    "workspace_changed_paths_observed_sample": [
      ".context/05_operations/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.md",
      "knowledge_base/index/trade_record_inventory_index_2026-05-05.json",
      "pipeline_state/live_monitoring_maintenance_state.json",
      "pipeline_state/shadow_observer_state.json",
      "pipeline_state/sierra_depth_enrichment_checkpoint.json",
      "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json",
      "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
      "research/operations/AI_MARKET_MONITORING_OBSERVATIONS_2026-05-08.md",
      "research/operations/GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-08_0812UTC.md",
      "research/operations/GTOS_MONITORING_SELF_SUSTAINING_FIX_2026-05-08.md",
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
      "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json",
      "research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md",
      "research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.json",
      "research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md",
      "research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.json",
      "research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md",
      "research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json",
      "research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md",
      "research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.json",
      "research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md",
      "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json",
      "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md",
      "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json",
      "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md",
      "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json",
      "research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md",
      "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json",
      "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md",
      "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.json",
      "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md",
      "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json",
      "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md",
      "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.json",
      "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.md",
      "research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.json",
      "research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md",
      "research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.json",
      "research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md",
      "research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.json",
      "research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md",
      "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json",
      "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md",
      "research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.json",
      "research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md",
      "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json",
      "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md",
      "research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.json",
      "research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md",
      "research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.json",
      "research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md",
      "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json",
      "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md",
      "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.json",
      "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md",
      "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.json",
      "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md",
      "research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.json",
      "research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.json",
      "research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.json",
      "research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md",
      "research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.json",
      "research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md",
      "research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json",
      "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.json",
      "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md",
      "research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.json",
      "research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.json",
      "research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md"
    ]
  },
  "generated_files_checked_for_flags": [
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_COMPLETION_AUDIT_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_COMPLETION_AUDIT_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_NEXT_PROMPT_PACK_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md"
  ],
  "issues": [],
  "json_files_parsed": [
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_COMPLETION_AUDIT_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json"
  ],
  "no_promotion_flags": {
    "live_effect": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": false
  },
  "oti3_missing_tick_dates": [
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-17.parquet",
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-20.parquet"
  ],
  "route_rows": 246,
  "source_counts": {
    "blocked_rows": 246,
    "blocker_code_counts": {
      "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
      "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
      "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
      "BLOCK_RESULT_MISSING_SOURCE": 80,
      "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 1,
      "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1
    },
    "blocker_tuple_counts": {
      "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
      "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
      "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
      "BLOCK_RESULT_MISSING_SOURCE": 80,
      "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED+BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1
    },
    "eligible_rows": 52,
    "total_rows": 298
  },
  "verification_status": "PASS",
  "verified_at_utc": "2026-05-08T14:27:01Z"
}

## Status

`PASS_VERIFIED_COMPLETE`; `can_mark_goal_complete=true`.
