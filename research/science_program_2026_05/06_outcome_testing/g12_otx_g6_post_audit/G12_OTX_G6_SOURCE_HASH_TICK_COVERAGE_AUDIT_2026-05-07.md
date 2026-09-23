# G12 Otx G6 Source Hash Tick Coverage Audit

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "artifact_family": "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT",
  "coverage_summary_by_packet": {
    "OTG0-PKT-060": {
      "decision_quote_status": {
        "DECISION_QUOTE_FOUND_ASOF": 76,
        "DECISION_QUOTE_NOT_FOUND_WITHIN_5M": 4
      },
      "packet_specific_status": {
        "NOT_CLEARED_BY_TICK_DATA": 80
      },
      "path_status": {
        "ORDERED_TICK_PATH_AVAILABLE": 79,
        "ORDERED_TICK_PATH_EMPTY_OR_MISSING": 1
      },
      "records": 80
    },
    "OTG0-PKT-061": {
      "decision_quote_status": {
        "DECISION_QUOTE_FOUND_ASOF": 50,
        "DECISION_QUOTE_NOT_FOUND_WITHIN_5M": 1
      },
      "packet_specific_status": {
        "ORDERED_TICK_PATH_AVAILABLE": 50,
        "ORDERED_TICK_PATH_EMPTY_OR_MISSING": 1
      },
      "path_status": {
        "ORDERED_TICK_PATH_AVAILABLE": 50,
        "ORDERED_TICK_PATH_EMPTY_OR_MISSING": 1
      },
      "records": 51
    },
    "OTG0-PKT-062": {
      "decision_quote_status": {
        "DECISION_QUOTE_FOUND_ASOF": 81,
        "DECISION_QUOTE_NOT_FOUND_WITHIN_5M": 5
      },
      "packet_specific_status": {
        "ASOF_OPENING_RANGE_BREAKOUT_READY": 73,
        "RANGE_NOT_COMPLETE_ASOF_DECISION": 9,
        "RANGE_TICK_WINDOW_EMPTY_OR_MISSING": 4
      },
      "path_status": {
        "ORDERED_TICK_PATH_AVAILABLE": 84,
        "ORDERED_TICK_PATH_EMPTY_OR_MISSING": 2
      },
      "records": 86
    },
    "OTG0-PKT-063": {
      "decision_quote_status": {
        "DECISION_QUOTE_FOUND_ASOF": 81,
        "DECISION_QUOTE_NOT_FOUND_WITHIN_5M": 5
      },
      "packet_specific_status": {
        "INSUFFICIENT_PREDECISION_M1_BARS": 5,
        "PREREGISTERED_TICK_CUSUM_FEATURE_READY": 81
      },
      "path_status": {
        "ORDERED_TICK_PATH_AVAILABLE": 84,
        "ORDERED_TICK_PATH_EMPTY_OR_MISSING": 2
      },
      "records": 86
    },
    "OTG0-PKT-066": {
      "decision_quote_status": {
        "DECISION_QUOTE_FOUND_ASOF": 3,
        "DECISION_QUOTE_NOT_FOUND_WITHIN_5M": 4
      },
      "packet_specific_status": {
        "STRUCTURED_SWEEP_FIELDS_READY": 7
      },
      "path_status": {
        "ORDERED_TICK_PATH_AVAILABLE": 5,
        "ORDERED_TICK_PATH_EMPTY_OR_MISSING": 2
      },
      "records": 7
    }
  },
  "critical_xau_2026_05_06": {
    "columns": [
      "ts_utc",
      "ts_msc",
      "bid",
      "ask",
      "last",
      "volume",
      "flags",
      "inferred_aggressor"
    ],
    "exists": true,
    "max_ts_utc": "2026-05-06T23:59:59.392000+00:00",
    "min_ts_utc": "2026-05-06T17:16:17.131000+00:00",
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
    "row_count": 108541,
    "sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
    "windows": [
      {
        "end_utc": "2026-05-06T07:15:00Z",
        "first_ts_utc": null,
        "last_ts_utc": null,
        "row_count": 0,
        "start_utc": "2026-05-06T07:10:00Z"
      },
      {
        "end_utc": "2026-05-06T11:15:00Z",
        "first_ts_utc": null,
        "last_ts_utc": null,
        "row_count": 0,
        "start_utc": "2026-05-06T07:15:00Z"
      },
      {
        "end_utc": "2026-05-06T08:00:00Z",
        "first_ts_utc": null,
        "last_ts_utc": null,
        "row_count": 0,
        "start_utc": "2026-05-06T07:55:00Z"
      }
    ]
  },
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "live_effect": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "source_hash_recheck": {
    "context_churn_mismatches": [
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\.context\\00_core\\research_current_state.md",
        "current_sha256": "e3c64ccd6591035cb4495e97440a7901ec66401575ef51cd53b358d725133627",
        "exists_current": true,
        "listed_path": ".context/00_core/research_current_state.md",
        "otx_sha256": "0c579b66e0c482b6bc4a1093eb282114221169591698e4c300e5900dcbda2b2f",
        "purpose": "controlling_input",
        "sha256_matches_otx": false
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\.context\\LIVE_STATE.md",
        "current_sha256": "58fccc34140c4a8101b0ba07b63a7a6d1ca38c473ce68ca90432ceff1f712622",
        "exists_current": true,
        "listed_path": ".context/LIVE_STATE.md",
        "otx_sha256": "e76bf0b8e3f589689b9b45cf5f39eb2281c9158e9281b194c723eba510eb053a",
        "purpose": "controlling_input",
        "sha256_matches_otx": false
      }
    ],
    "context_hash_mismatch_expected_after_preflight_or_docs_refresh": true,
    "current_rehash_rows": [
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\.context\\00_core\\goal_session_research_discipline.md",
        "current_sha256": "6bd423b74126a1494001684c3c1cc7e50e607cd18c187a1f769ef63ee1734ada",
        "exists_current": true,
        "listed_path": ".context/00_core/goal_session_research_discipline.md",
        "otx_sha256": "6bd423b74126a1494001684c3c1cc7e50e607cd18c187a1f769ef63ee1734ada",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\.context\\00_core\\research_current_state.md",
        "current_sha256": "e3c64ccd6591035cb4495e97440a7901ec66401575ef51cd53b358d725133627",
        "exists_current": true,
        "listed_path": ".context/00_core/research_current_state.md",
        "otx_sha256": "0c579b66e0c482b6bc4a1093eb282114221169591698e4c300e5900dcbda2b2f",
        "purpose": "controlling_input",
        "sha256_matches_otx": false
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\.context\\LIVE_STATE.md",
        "current_sha256": "58fccc34140c4a8101b0ba07b63a7a6d1ca38c473ce68ca90432ceff1f712622",
        "exists_current": true,
        "listed_path": ".context/LIVE_STATE.md",
        "otx_sha256": "e76bf0b8e3f589689b9b45cf5f39eb2281c9158e9281b194c723eba510eb053a",
        "purpose": "controlling_input",
        "sha256_matches_otx": false
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
        "current_sha256": "64019a2f70f8c2b165ba5fffe0b0e22186f3b9a4b47ccc936626af50a251c084",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
        "otx_sha256": "64019a2f70f8c2b165ba5fffe0b0e22186f3b9a4b47ccc936626af50a251c084",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
        "current_sha256": "14c595be104f632b9c0c659a5c2c2d85e50057862324bc2c6f4e317d95d6ea39",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
        "otx_sha256": "14c595be104f632b9c0c659a5c2c2d85e50057862324bc2c6f4e317d95d6ea39",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md",
        "current_sha256": "1fd18655acc0b8bede984d2e7f71b0bec5c312440c0f396cbd1faa897fb40a4b",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md",
        "otx_sha256": "1fd18655acc0b8bede984d2e7f71b0bec5c312440c0f396cbd1faa897fb40a4b",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
        "current_sha256": "d66c8aab004283afe4291dd5f9194797d689466301f67708ecd30ed7d2283fa7",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
        "otx_sha256": "d66c8aab004283afe4291dd5f9194797d689466301f67708ecd30ed7d2283fa7",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.md",
        "current_sha256": "adf5ee0bf090406e3752da740894434a3c64c68568882f54b008e2e1ce403c7c",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.md",
        "otx_sha256": "adf5ee0bf090406e3752da740894434a3c64c68568882f54b008e2e1ce403c7c",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.json",
        "current_sha256": "a98e75794c2414593175741c2cc021841160af4fef64f4c96ae672b52fe34c4e",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.json",
        "otx_sha256": "a98e75794c2414593175741c2cc021841160af4fef64f4c96ae672b52fe34c4e",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.md",
        "current_sha256": "9297bfd1c4202150818f505e23844a3bd39119d6af872b07135c231d3c70d14e",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.md",
        "otx_sha256": "9297bfd1c4202150818f505e23844a3bd39119d6af872b07135c231d3c70d14e",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
        "current_sha256": "3bb8116518f2f23b83fa2e15b42aaeef92a3e2d0c5804477087dbe6f4b13827b",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
        "otx_sha256": "3bb8116518f2f23b83fa2e15b42aaeef92a3e2d0c5804477087dbe6f4b13827b",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_2026-05-07.md",
        "current_sha256": "a11d58624b60b45949afba38b569f1729b48d170d31766fd85cc2a225d6bd09a",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_2026-05-07.md",
        "otx_sha256": "a11d58624b60b45949afba38b569f1729b48d170d31766fd85cc2a225d6bd09a",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\g12_g3_g6_packet_builder_audit\\G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_2026-05-07.json",
        "current_sha256": "11125f6a10f4d02ba41c52645693733643d2c53841bd65a7df1e166a2b3f4f16",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_2026-05-07.json",
        "otx_sha256": "11125f6a10f4d02ba41c52645693733643d2c53841bd65a7df1e166a2b3f4f16",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_METHOD_FREEZE_2026-05-07.md",
        "current_sha256": "6b3d5388edec93e1320fbb84bdeee048ce51cce10ad16be19505143cac6fb219",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results/OTI4_METHOD_FREEZE_2026-05-07.md",
        "otx_sha256": "6b3d5388edec93e1320fbb84bdeee048ce51cce10ad16be19505143cac6fb219",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_BLOCKER_AND_AMBIGUITY_LEDGER_2026-05-07.md",
        "current_sha256": "3c5ba88dea8f7167277fc7027e3d118d870ccce2b3635d5741c18efef6a06e7a",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results/OTI4_BLOCKER_AND_AMBIGUITY_LEDGER_2026-05-07.md",
        "otx_sha256": "3c5ba88dea8f7167277fc7027e3d118d870ccce2b3635d5741c18efef6a06e7a",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\oti4_g6_opening_drive_quarantined_results\\OTI4_COMPLETION_AUDIT_2026-05-07.md",
        "current_sha256": "13dc958db4233bd33c608562ae75d562adf173e9d47f7fa4beb94bf0ee3238ae",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results/OTI4_COMPLETION_AUDIT_2026-05-07.md",
        "otx_sha256": "13dc958db4233bd33c608562ae75d562adf173e9d47f7fa4beb94bf0ee3238ae",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.md",
        "current_sha256": "c9a03e79bb388524b7dfcd290b1f0f7b882a6bd0e7dcafa98348567dce597514",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb6_g6_blocker_clearing_proof_pack/OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.md",
        "otx_sha256": "c9a03e79bb388524b7dfcd290b1f0f7b882a6bd0e7dcafa98348567dce597514",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROOF_MATRIX_2026-05-07.md",
        "current_sha256": "56f6baec11d78a38204dab5732a737d3cf159fc8ba4abf52b3217ab08c7dacac",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb6_g6_blocker_clearing_proof_pack/OTB6_G6_PROOF_MATRIX_2026-05-07.md",
        "otx_sha256": "56f6baec11d78a38204dab5732a737d3cf159fc8ba4abf52b3217ab08c7dacac",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_LOCAL_DATA_AVAILABILITY_2026-05-07.md",
        "current_sha256": "a5b221cbfdd090413021c9c1e56cb2a5a92c5a554a8ffc5c7da60461fd44d5b5",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb6_g6_blocker_clearing_proof_pack/OTB6_G6_LOCAL_DATA_AVAILABILITY_2026-05-07.md",
        "otx_sha256": "a5b221cbfdd090413021c9c1e56cb2a5a92c5a554a8ffc5c7da60461fd44d5b5",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb6_g6_blocker_clearing_proof_pack\\OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.md",
        "current_sha256": "6a3ff31450d8ce63d8a57a58d83a1f76a0f03e73f1d6a9cf1c5b11ca45830123",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb6_g6_blocker_clearing_proof_pack/OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.md",
        "otx_sha256": "6a3ff31450d8ce63d8a57a58d83a1f76a0f03e73f1d6a9cf1c5b11ca45830123",
        "purpose": "controlling_input",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "current_sha256": "b682ba1377af7ac11721be068f91cf78e546d7f88a0865332432cffd6704bd1c",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "otx_sha256": "b682ba1377af7ac11721be068f91cf78e546d7f88a0865332432cffd6704bd1c",
        "purpose": "frozen_target_packet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "current_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
        "otx_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
        "purpose": "frozen_target_packet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
        "current_sha256": "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
        "otx_sha256": "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080",
        "purpose": "frozen_target_packet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
        "current_sha256": "0064500e34b9880ddd8b1db1f84035c63cdf2433e80f05c9c27e5fbc92b3e828",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
        "otx_sha256": "0064500e34b9880ddd8b1db1f84035c63cdf2433e80f05c9c27e5fbc92b3e828",
        "purpose": "frozen_target_packet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\tmp\\gtos_otb\\G12OTX\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
        "current_sha256": "4a2fc13bd16855cea11df01c9781bca9dc79176356cb9966b7f5d315f6904714",
        "exists_current": true,
        "listed_path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
        "otx_sha256": "4a2fc13bd16855cea11df01c9781bca9dc79176356cb9966b7f5d315f6904714",
        "purpose": "frozen_target_packet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
        "current_sha256": "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
        "otx_sha256": "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
        "current_sha256": "fa2b64a91ed38e54c7a1b57683e5a7991a86db8a9c9b37a72b312e7fc39d5c02",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
        "otx_sha256": "fa2b64a91ed38e54c7a1b57683e5a7991a86db8a9c9b37a72b312e7fc39d5c02",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
        "current_sha256": "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
        "otx_sha256": "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-03.parquet",
        "current_sha256": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-03.parquet",
        "otx_sha256": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
        "current_sha256": "7b2f89ecbbbc59124fc56c7b9e504d7b41e299f7bd950fc54821e8f18a7fa478",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
        "otx_sha256": "7b2f89ecbbbc59124fc56c7b9e504d7b41e299f7bd950fc54821e8f18a7fa478",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
        "current_sha256": "13357b7bc6b4d02690ab7055b611b431c6e2ce2a77c36df791f347cf7fcaed35",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
        "otx_sha256": "13357b7bc6b4d02690ab7055b611b431c6e2ce2a77c36df791f347cf7fcaed35",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-06.parquet",
        "current_sha256": "41896f6984bcba5ef3ba5ae656303e5968c5a5ed26acda58f439aa45bee45ad4",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-06.parquet",
        "otx_sha256": "41896f6984bcba5ef3ba5ae656303e5968c5a5ed26acda58f439aa45bee45ad4",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-06.parquet",
        "current_sha256": "eb90e21f12aef7564a6f2995fc8a051eb27a61057326e3c5ccf4b5c3132f69fb",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-06.parquet",
        "otx_sha256": "eb90e21f12aef7564a6f2995fc8a051eb27a61057326e3c5ccf4b5c3132f69fb",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-04.parquet",
        "current_sha256": "424c3d9ee4279fd8c258b061f335a25b32b74e88dab8f71abb12016126f50338",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-04.parquet",
        "otx_sha256": "424c3d9ee4279fd8c258b061f335a25b32b74e88dab8f71abb12016126f50338",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-05.parquet",
        "current_sha256": "7316926c90065e3f0d8c3c8b49d38544a82dd82cc0536cc35d415e93c82dad76",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-05.parquet",
        "otx_sha256": "7316926c90065e3f0d8c3c8b49d38544a82dd82cc0536cc35d415e93c82dad76",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-06.parquet",
        "current_sha256": "b00d0d06697b1da4c2f2f14f63dd4730fd4ad6d9ce331199a1975b7744d9114d",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-06.parquet",
        "otx_sha256": "b00d0d06697b1da4c2f2f14f63dd4730fd4ad6d9ce331199a1975b7744d9114d",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
        "current_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
        "otx_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
        "current_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
        "otx_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
        "current_sha256": "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
        "otx_sha256": "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-03.parquet",
        "current_sha256": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-03.parquet",
        "otx_sha256": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-04.parquet",
        "current_sha256": "1186ffbcdba2bb028fd39ebada82dce9c1d342a318b9e3cc65e823b2b280f09f",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-04.parquet",
        "otx_sha256": "1186ffbcdba2bb028fd39ebada82dce9c1d342a318b9e3cc65e823b2b280f09f",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
        "current_sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
        "otx_sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      },
      {
        "current_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
        "current_sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
        "exists_current": true,
        "listed_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
        "otx_sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
        "purpose": "read_only_external_tick_parquet",
        "sha256_matches_otx": true
      }
    ],
    "material_source_mismatches": [],
    "otx_source_file_count": 43
  },
  "source_hash_verdict": "PASS_CURRENT_REHASH_EXCEPT_EXPECTED_CONTEXT_CHURN",
  "tick_coverage_verdict": "PARTIAL_COVERAGE_CONFIRMED_ABSOLUTE_MAIN_PATH_INSPECTED",
  "tick_root_absolute_required_by_prompt": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
  "tick_root_exists": true,
  "validation_safe": false,
  "worktree_data_ticks_parquet_files": []
}
```
