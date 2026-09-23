# G12 Otx G6 Blocker Action Map

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "artifact_family": "G12_OTX_G6_BLOCKER_ACTION_MAP",
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "live_effect": false,
  "outcome_review_opened": false,
  "packet_actions": [
    {
      "blocked_from_promotion_by": [],
      "frozen_allowed_subset": null,
      "next_exact_action": "Prospective mechanical_ob_bounds_asof_v1 capture with market_state source path/hash, row hash, H1 OB id, ob_low/high/mid, OB creation UTC, impulse BOS UTC, mitigation state, and touch_sequence for every row.",
      "packet_id": "OTG0-PKT-060",
      "terminal_g12_decision": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS"
    },
    {
      "blocked_from_promotion_by": [],
      "frozen_allowed_subset": null,
      "next_exact_action": "Recover or recapture XAUUSD ticks covering at least 2026-05-06 07:10-11:15 UTC, hash the source parquet, and rebuild continuation_no_retrace_decision_price_path_v1 before any CNR result lane.",
      "packet_id": "OTG0-PKT-061",
      "terminal_g12_decision": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE"
    },
    {
      "blocked_from_promotion_by": [
        "sample floor not met",
        "DSR/PBO/effective-N not computable",
        "same-dataset discovery quarantine",
        "synthetic path-R is not broker actual-R"
      ],
      "frozen_allowed_subset": null,
      "next_exact_action": "Only a future source-complete opening-drive lane with >=200 unique breakout groups and a separate G12 result audit may make any validation-style claim.",
      "packet_id": "OTG0-PKT-062",
      "terminal_g12_decision": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS"
    },
    {
      "blocked_from_promotion_by": [
        "future lane not yet run",
        "synthetic/path result labels still closed",
        "sample floor and DSR/PBO/effective-N not yet established"
      ],
      "frozen_allowed_subset": {
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
      "next_exact_action": "Run a separate quarantined CUSUM result audit using only the frozen 81-row source-ready subset, preserving duplicate-group policy and no broker actual-R.",
      "packet_id": "OTG0-PKT-063",
      "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS"
    },
    {
      "blocked_from_promotion_by": [
        "only three current source-ready rows",
        "sample floor 150 XAU OB-retouch rows not met",
        "future synthetic/path result labels still closed"
      ],
      "frozen_allowed_subset": {
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
      "next_exact_action": "Collect or rebuild enough source-ready XAU OB-zone/round-number sweep rows to reach the 150-row floor before scoring beyond parser dry-run.",
      "packet_id": "OTG0-PKT-066",
      "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "saturation_search_evidence": {
    "git_head": "1436d4d15cb4517e97294a1ab62447c283f2aa44",
    "git_log_oneline_20": [
      "1436d4d1 docs: refresh research state for g12 otx prompt",
      "087feb5c research: harden g12 otx g6 prompt",
      "7cc67ed0 research: add g12 otx g6 post audit prompt",
      "c55c7c69 docs: refresh research state for otx g6",
      "b9ba0f8b research: add otx g6 tick-aware resolution",
      "b81d087d docs: record tick-aware g6 followup context",
      "b131f111 research: stabilize oti otb artifact hygiene",
      "8228a0e4 docs: refresh research state after oti otb merges",
      "707c1610 merge: integrate otb6 g6 blocker proof pack",
      "bd38bbd4 merge: integrate oti4 g6 opening-drive audit",
      "2f6bfc12 docs: refresh research state after oti3 g3 audit",
      "b4ff6484 research: add oti3 g3 geometry quarantined audit",
      "3b04f0bd docs: refresh research state after otb6 stabilization",
      "af47d8a3 research: stabilize otb6 g6 proof pack tests",
      "83cee9e9 docs: refresh research state after otb6 g6 proof pack",
      "da34eda1 research: add otb6 g6 blocker proof pack",
      "45b1deea docs: refresh research state after oti4 audit",
      "95f66617 research: add oti4 g6 opening drive audit",
      "ca22d1c7 docs: refresh research state after g3 g6 audit",
      "8add0011 research: audit g3 g6 packet builders"
    ],
    "negative_evidence": [
      "No local artifact contains a populated mechanical_ob_bounds_asof_v1 packet row for OTG0-PKT-060.",
      "Hits for market_state_row_hash/touch_sequence/ob_id are contracts or unrelated geometry docs, not source-row artifacts with H1 OB id, bounds, creation UTC, impulse BOS UTC, mitigation state, and touch sequence.",
      "Shadow logs were limited to source/provenance filename discovery; result-bearing shadow rows were not consumed."
    ],
    "otx_commit_files": [
      "b9ba0f8b research: add otx g6 tick-aware resolution",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_ADVERSARIAL_SELF_REVIEW_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_ADVERSARIAL_SELF_REVIEW_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_ARTIFACT_MANIFEST_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_COMPLETION_AUDIT_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_COMPLETION_AUDIT_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_OTI4B_QUARANTINED_RESULT_ROWS_2026-05-07.jsonl",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py",
      "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/test_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py"
    ],
    "patterns": [
      "mechanical_ob_bounds_asof_v1",
      "market_state_row_hash",
      "touch_sequence",
      "ob_id",
      "XAUUSD_2026-05-06T07:15:00+00:00",
      "XAUUSD_2026-05-06T08:00:00+00:00"
    ],
    "positive_hits_by_pattern": {
      "XAUUSD_2026-05-06T07:15:00+00:00": [
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\OTB2R_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\OTB2R_G6_SOURCE_HASH_AUDIT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\OTB2R_G6_SOURCE_HASH_AUDIT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_RESULT_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_OTI4B_QUARANTINED_RESULT_ROWS_2026-05-07.jsonl",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md"
      ],
      "XAUUSD_2026-05-06T08:00:00+00:00": [
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\OTB2R_G6_SOURCE_HASH_AUDIT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_RESULT_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_OTI4B_QUARANTINED_RESULT_ROWS_2026-05-07.jsonl",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md"
      ],
      "market_state_row_hash": [
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\build_otb6_g6_blocker_clearing_proof_pack_2026_05_07.py"
      ],
      "mechanical_ob_bounds_asof_v1": [
        ".context\\00_core\\research_current_state.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\build_otb6_g6_blocker_clearing_proof_pack_2026_05_07.py",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_ADVERSARIAL_SELF_REVIEW_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_ADVERSARIAL_SELF_REVIEW_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py"
      ],
      "ob_id": [
        ".context\\05_operations\\GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_1000UTC.md",
        ".context\\05_operations\\GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_1015UTC.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\build_otb6_g6_blocker_clearing_proof_pack_2026_05_07.py",
        "src\\components\\touch_count_gate_logger.py",
        "src\\research_infra\\decision_layer_diagnostics_join.py",
        "src\\research_infra\\ob_zone_test.py"
      ],
      "touch_sequence": [
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\build_g12_g3_g6_packet_builder_audit_2026_05_07.py",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\build_otb6_g6_blocker_clearing_proof_pack_2026_05_07.py",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_NO_LEAK_AND_STRICTER_FORMULATION_REPORT_2026-05-07.json",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_NO_LEAK_AND_STRICTER_FORMULATION_REPORT_2026-05-07.md",
        "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\build_oti4_g6_opening_drive_quarantined_results_2026_05_07.py"
      ]
    },
    "prompt_hardening_commit_files": [
      "087feb5c research: harden g12 otx g6 prompt",
      "research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_POST_AUDIT_GOAL_PROMPT_2026-05-07.md"
    ],
    "searched_roots": [
      "research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit",
      "research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results",
      "research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack",
      "research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets",
      "research\\science_program_2026_05\\06_outcome_testing\\g12_otb_rebuild_reaudit",
      "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution",
      ".context",
      "src"
    ],
    "shadow_logs_source_provenance_filename_inventory": [
      "shadow_logs\\candidate_features_log.jsonl",
      "shadow_logs\\candidate_ltf_path_order.jsonl",
      "shadow_logs\\candidate_mso_snapshot_joins.jsonl",
      "shadow_logs\\candidate_path_contract_audit.jsonl",
      "shadow_logs\\candidate_path_follow.jsonl",
      "shadow_logs\\candidate_registry_audit.jsonl",
      "shadow_logs\\context_control_audit.jsonl",
      "shadow_logs\\context_control_ledger.jsonl",
      "shadow_logs\\continuation_no_retrace_candidates.jsonl",
      "shadow_logs\\cusum_candidate_rate_daily.csv",
      "shadow_logs\\external_source_blocker_status.jsonl",
      "shadow_logs\\live_candidate_opportunity_clusters.jsonl",
      "shadow_logs\\live_candidate_strategy_rollups.jsonl",
      "shadow_logs\\mechanical_context_diagnostics_join.jsonl",
      "shadow_logs\\prefill_delivery_path.jsonl",
      "shadow_logs\\prefill_delivery_path_audit.jsonl",
      "shadow_logs\\prefill_delivery_path_resolutions.jsonl",
      "shadow_logs\\s79_side_aware_risk_context.jsonl",
      "shadow_logs\\shadow_observer_tick_enrichment.jsonl",
      "shadow_logs\\sierra_confluence_source_status.jsonl",
      "shadow_logs\\sierra_depth_feature_snapshots.jsonl",
      "shadow_logs\\sierra_proxy_registry_status.jsonl",
      "shadow_logs\\strategy_follow_candidates.jsonl"
    ]
  },
  "validation_safe": false,
  "verdict": "ALL_PACKET_NEXT_ACTIONS_EXACT"
}
```
