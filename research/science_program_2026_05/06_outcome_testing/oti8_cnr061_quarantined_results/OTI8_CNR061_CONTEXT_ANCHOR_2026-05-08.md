# OTI8 CNR061 Context Anchor - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "active_question_stack": [
    "Can the exact 8 G12-accepted source-hashed CNR061 rows be scored without opening blocked rows?",
    "Do raw duplicate overlaps invalidate scoring, or are they duplicate-context rows excluded by countable policy?",
    "Did CNR_T0 original TP1 resolve before stop within the fixed ordered tick horizon?",
    "What does the tiny-n result teach without promotion or rescue?"
  ],
  "api_calls": 0,
  "artifact_family": "OTI8_CNR061_CONTEXT_ANCHOR",
  "blocked_packet_outcome_source_read": false,
  "branch": "oti8-cnr061-quarantined-results",
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "controlling_prompt_path": "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-08.md",
  "current_head": "fcad01fe15b2a2bb6166f10f213dac50e64cc5d0",
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "generated_at_utc": "2026-05-08T05:11:01Z",
  "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "read_inputs": [
    "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-08.md",
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_SOURCE_HASH_JOIN_AUDIT_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_NEXT_LANE_PROMPT_PACK_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl",
    "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_JOIN_MAP_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
    "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
    "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_COMPLETION_AUDIT_2026-05-07.json"
  ],
  "route_decision_ledger": [
    {
      "decision": "USE_ACCEPTED_8_SIDE CAR_ROWS_ONLY",
      "reason": "G12_CNR061 accepted exactly 8 input-only rows for a future quarantined result audit."
    },
    {
      "decision": "USE_SOURCE_HASHED_TICK_PATHS",
      "reason": "Rows carry executable quote and ordered_path_packet with source parquet hashes."
    },
    {
      "decision": "FREEZE_COUNTABLE_DUPLICATE_POLICY_BEFORE_SCORING",
      "reason": "Raw blocked duplicate groups overlap accepted groups; G12 policy rejects duplicate_group-only joins and countable blocked overlap is zero."
    },
    {
      "decision": "DO_NOT_USE_BROKER_ACTUAL_R_OR_HIDDEN_PATH_LABELS",
      "reason": "Prompt forbids broker/account/live/hidden result labels; scoring reads only bid/ask ticks."
    }
  ],
  "runtime_dirt_at_anchor": "M .context/LIVE_STATE.md\n?? research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/build_oti8_cnr061_quarantined_results_2026_05_08.py\n?? research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/test_oti8_cnr061_quarantined_results_2026_05_08.py\n?? research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/verify_oti8_cnr061_quarantined_results_2026_05_08.py",
  "searched_root_ledger": [
    {
      "purpose": "worktree artifacts and prompt-listed upstream files",
      "root": "C:\\tmp\\gtos_otb\\OTI8CNR061",
      "status": "SEARCHED"
    },
    {
      "purpose": "absolute local heavy tick source paths declared by accepted sidecar rows",
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "status": "FOUND_XAGUSD_2026_05_04_AND_2026_05_05"
    },
    {
      "purpose": "prompt-named CNR source field row matrix replacement search",
      "root": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder",
      "status": "FOUND_CNR_SOURCE_FIELD_PACKET_ROWS_2026_05_07_JSONL_PROMPT_2026_05_08_MATRIX_NAME_ABSENT"
    }
  ],
  "validation_safe": false,
  "worktree_path": "C:\\tmp\\gtos_otb\\OTI8CNR061"
}
```
