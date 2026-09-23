# G12 Otx G6 Completion Audit

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "artifact_family": "G12_OTX_G6_COMPLETION_AUDIT",
  "artifact_files": [
    "G12_OTX_G6_BLOCKER_ACTION_MAP_2026-05-07",
    "G12_OTX_G6_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07",
    "G12_OTX_G6_LEAKAGE_NOLEAK_AUDIT_2026-05-07",
    "G12_OTX_G6_METHOD_STATS_AUDIT_2026-05-07",
    "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07",
    "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07",
    "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07"
  ],
  "can_mark_goal_complete": true,
  "freshness_record": {
    "current_head_seen": "1436d4d1 docs: refresh research state for g12 otx prompt",
    "latest_research_relevant_commit": "087feb5c research: harden g12 otx g6 prompt",
    "live_state_status": "FRESH"
  },
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "head_at_audit": "1436d4d15cb4517e97294a1ab62447c283f2aa44",
  "live_effect": false,
  "objective_restated": "Run the G12 post-audit of OTX G6 tick-aware resolution and decide OTG0-PKT-060/061/062/063/066 with proof-or-impossibility evidence while preserving research-only NO_PROMOTION_VERDICT boundaries.",
  "outcome_review_opened": false,
  "per_packet_saturation_ledger": [
    {
      "evidence_found": {
        "otb6_generic_comparator_ready_rows": 80,
        "otb6_unique_matched_control_groups": 20,
        "otx_ordered_tick_path_ready_rows": 79,
        "otx_quote_ready_rows": 76
      },
      "negative_evidence": [
        "No local artifact contains a populated mechanical_ob_bounds_asof_v1 packet row for OTG0-PKT-060.",
        "Hits for market_state_row_hash/touch_sequence/ob_id are contracts or unrelated geometry docs, not source-row artifacts with H1 OB id, bounds, creation UTC, impulse BOS UTC, mitigation state, and touch sequence.",
        "Shadow logs were limited to source/provenance filename discovery; result-bearing shadow rows were not consumed."
      ],
      "next_exact_action": "Prospective mechanical_ob_bounds_asof_v1 capture with market_state source path/hash, row hash, H1 OB id, ob_low/high/mid, OB creation UTC, impulse BOS UTC, mitigation state, and touch_sequence for every row.",
      "packet_id": "OTG0-PKT-060",
      "paths_searched": [
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_otb_rebuild_reaudit",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution",
        ".context",
        "src"
      ],
      "terminal_g12_decision": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS"
    },
    {
      "evidence_found": {
        "absolute_tick_file": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
        "absolute_tick_file_min_ts_utc": "2026-05-06T17:16:17.131000+00:00",
        "blocked_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
        "decision_quote_window_rows": 0,
        "ordered_tick_path_ready_rows": 50,
        "quote_ready_rows": 50
      },
      "negative_evidence": [],
      "next_exact_action": "Recover or recapture XAUUSD ticks covering at least 2026-05-06 07:10-11:15 UTC, hash the source parquet, and rebuild continuation_no_retrace_decision_price_path_v1 before any CNR result lane.",
      "packet_id": "OTG0-PKT-061",
      "paths_searched": [
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_otb_rebuild_reaudit",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution",
        ".context",
        "src"
      ],
      "terminal_g12_decision": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE"
    },
    {
      "evidence_found": {
        "countable_discovery_rows": 9,
        "duplicate_policy": "one countable primary unique breakout per duplicate_breakout_key_otx",
        "mean_synthetic_r_resolved_only": -0.5,
        "raw_rows": 86,
        "resolved_synthetic_r_rows": 5
      },
      "negative_evidence": [],
      "next_exact_action": "Only a future source-complete opening-drive lane with >=200 unique breakout groups and a separate G12 result audit may make any validation-style claim.",
      "packet_id": "OTG0-PKT-062",
      "paths_searched": [
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_otb_rebuild_reaudit",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution",
        ".context",
        "src"
      ],
      "terminal_g12_decision": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS"
    },
    {
      "evidence_found": {
        "excluded_record_ids": [
          "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
          "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00"
        ],
        "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
        "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
        "required_status": "PREREGISTERED_TICK_CUSUM_FEATURE_READY",
        "source_ready_rows": 81
      },
      "negative_evidence": [],
      "next_exact_action": "Run a separate quarantined CUSUM result audit using only the frozen 81-row source-ready subset, preserving duplicate-group policy and no broker actual-R.",
      "packet_id": "OTG0-PKT-063",
      "paths_searched": [
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_otb_rebuild_reaudit",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution",
        ".context",
        "src"
      ],
      "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS"
    },
    {
      "evidence_found": {
        "accepted_record_ids": [
          "OTG0-PKT-066|XAUUSD_2026-05-04T07:15:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-05T08:00:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-05T08:15:00+00:00"
        ],
        "excluded_record_ids": [
          "OTG0-PKT-066|XAUUSD_2026-05-03T16:15:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-03T16:30:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-06T07:15:00+00:00",
          "OTG0-PKT-066|XAUUSD_2026-05-06T08:00:00+00:00"
        ],
        "required_feature_asof_lte_decision": true,
        "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
        "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
        "required_sweep_status": "STRUCTURED_SWEEP_FIELDS_READY",
        "sample_floor": 150,
        "source_ready_rows": 3
      },
      "negative_evidence": [],
      "next_exact_action": "Collect or rebuild enough source-ready XAU OB-zone/round-number sweep rows to reach the 150-row floor before scoring beyond parser dry-run.",
      "packet_id": "OTG0-PKT-066",
      "paths_searched": [
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_otb_rebuild_reaudit",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution",
        ".context",
        "src"
      ],
      "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": "scripts/generate_live_state.py was run and .context/LIVE_STATE.md read; freshness FRESH at research commit 087feb5c.",
      "requirement": "mandatory_preflight_live_state",
      "status": "PASS"
    },
    {
      "evidence": "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md read.",
      "requirement": "latest_handoff_read",
      "status": "PASS"
    },
    {
      "evidence": ".context/00_core/quick_reference_card.md read.",
      "requirement": "quick_reference_read",
      "status": "PASS"
    },
    {
      "evidence": ".context/00_core/research_operating_doctrine.md read.",
      "requirement": "research_doctrine_read",
      "status": "PASS"
    },
    {
      "evidence": ".context/00_core/research_current_state.md read.",
      "requirement": "research_current_state_read",
      "status": "PASS"
    },
    {
      "evidence": ".context/00_core/goal_session_research_discipline.md read.",
      "requirement": "goal_session_discipline_read",
      "status": "PASS"
    },
    {
      "evidence": "G12_OTX_G6_POST_AUDIT_GOAL_PROMPT_2026-05-07.md read from disk after preflight.",
      "requirement": "controlling_prompt_read_from_disk",
      "status": "PASS"
    },
    {
      "evidence": "LIVE_STATE research context status was FRESH; git log -20 and OTX/prompt commits inspected.",
      "requirement": "context_freshness_contract",
      "status": "PASS"
    },
    {
      "evidence": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks inspected; XAUUSD 2026-05-06 parquet min timestamp and missing 07:15/08:00 windows recorded.",
      "requirement": "absolute_tick_path_inspected",
      "status": "PASS"
    },
    {
      "evidence": "All required OTX JSON, JSONL, builder, and test files were inspected or verified.",
      "requirement": "otx_required_files_read",
      "status": "PASS"
    },
    {
      "evidence": "G12 G3/G6, OTI4, OTB6, OTB2R G6, G12 OTB rebuild, OTG0 manifest, and control rules inspected.",
      "requirement": "prior_context_read",
      "status": "PASS"
    },
    {
      "evidence": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS",
      "requirement": "otg0_pkt_060_decided",
      "status": "PASS"
    },
    {
      "evidence": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE",
      "requirement": "otg0_pkt_061_decided",
      "status": "PASS"
    },
    {
      "evidence": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS",
      "requirement": "otg0_pkt_062_decided",
      "status": "PASS"
    },
    {
      "evidence": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS",
      "requirement": "otg0_pkt_063_decided",
      "status": "PASS"
    },
    {
      "evidence": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS",
      "requirement": "otg0_pkt_066_decided",
      "status": "PASS"
    },
    {
      "evidence": "All generated JSON uses NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
      "requirement": "no_promotion_flags_preserved",
      "status": "PASS"
    },
    {
      "evidence": "Generated files live under g12_otx_g6_post_audit except optional context closeout handled separately; no src/prompts/config/canary/MT5/live-order files changed.",
      "requirement": "forbidden_surfaces_untouched",
      "status": "PASS"
    },
    {
      "evidence": {
        "builder": "python -B -m py_compile build_g12_otx_g6_post_audit_2026_05_07.py",
        "g12_pytest": "python -B -m pytest -q test_g12_otx_g6_post_audit_2026_05_07.py",
        "otx_py_compile": "python -B -m py_compile ../otx_g6_tick_aware_end_to_end_resolution/build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py",
        "otx_pytest": "python -B -m pytest -q ../otx_g6_tick_aware_end_to_end_resolution/test_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py"
      },
      "requirement": "verification_commands",
      "status": "PASS"
    }
  ],
  "validation_safe": false
}
```
