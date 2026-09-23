# G12 OTI6 CNR Source Hash Noleak Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "all_consumed_files_hashed": true,
  "all_required_files_exist": true,
  "api_calls": 0,
  "artifact_family": "G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT",
  "audit_verdict": "PASS_SOURCE_HASH_AND_NOLEAK_BOUNDARIES_PRESERVED",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "forbidden_reads_or_calls": {
    "account_history_accessed": false,
    "api_calls": 0,
    "blocked_packet_outcome_source_read": false,
    "broker_actual_r_accessed": false,
    "databento_calls": 0,
    "live_order_state_accessed": false,
    "live_trade_results_accessed": false,
    "mt5_order_calls": 0,
    "paid_data_calls": 0
  },
  "generated_at_utc": "2026-05-07T10:47:40Z",
  "git_head_at_build": "16713c77 docs: refresh research state for g12 oti6 prompt",
  "input_file_hashes": [
    {
      "exists": true,
      "path": ".context/LIVE_STATE.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "3c43d48ab316f5d1bfe7f59b85ab6f21df331637a7e6ff445b01cfcc316ec5c4",
      "size_bytes": 13216
    },
    {
      "exists": true,
      "path": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
      "size_bytes": 25348
    },
    {
      "exists": true,
      "path": ".context/00_core/quick_reference_card.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
      "size_bytes": 11078
    },
    {
      "exists": true,
      "path": ".context/00_core/research_operating_doctrine.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe",
      "size_bytes": 11400
    },
    {
      "exists": true,
      "path": ".context/00_core/research_current_state.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "b63fbff68536d711afe07b5b1b6ae7ef8d871ba5bb056e940b2bf42a4b3d6c93",
      "size_bytes": 405125
    },
    {
      "exists": true,
      "path": ".context/00_core/goal_session_research_discipline.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "77517255976f997421fc1063eb49557e8c3f65cee81d70edb7d345937ca2ed07",
      "size_bytes": 4999
    },
    {
      "exists": true,
      "path": ".context/00_core/local_heavy_data_inventory.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0",
      "size_bytes": 4218
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti6_cnr_post_audit/G12_OTI6_CNR_POST_AUDIT_GOAL_PROMPT_2026-05-07.md",
      "required": true,
      "role": "mandatory_preflight_or_control_context",
      "sha256": "016040c19224f3e2a1963c4b1a154a5fb1b4e548e1a4584adfaf3895719a6654",
      "size_bytes": 8121
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHOD_FREEZE_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "5e4292f49a55837326320cc86ef2939a2f704580482fce985a004fa39ca4d3c2",
      "size_bytes": 2075
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "efc3dd9f188014163b64f2911a27b08d6dc149556c3966aa795470c0cb6baf55",
      "size_bytes": 2559
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "9a63e3dfe676a68d75b901dceb27217aeb2778b15161f41211789e3c85d37485",
      "size_bytes": 13112
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "5b54a4f8db36ded4ff7e22b11edb89907ad564b4022ce73c738a770d75c37a51",
      "size_bytes": 2638
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "15a16e27f5ff36c1004f7b4a5be3da8ae25b90beb35e4ec3c19f0912163fc7dd",
      "size_bytes": 6319
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "474dd90aa92d3c6ffd200649df3848157decb1a1be71e3edeedeead6c9ca2606",
      "size_bytes": 2284
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "e74fe23e2ede47d7dd893fb9140bcd801e6ad12d9076a4fd3657061ce3408e4b",
      "size_bytes": 1785
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_COMPLETION_AUDIT_2026-05-07.json",
      "required": true,
      "role": "oti6_machine_checkable_input",
      "sha256": "781682daf2f46be8928de6be4d371e99b03ac5618a41143e767cc8e7756ca1e5",
      "size_bytes": 13054
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHOD_FREEZE_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "694abe45ee3621ba14e461c61823bbd88ff5f6958b12e57d42437689047a1d95",
      "size_bytes": 2277
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "0e9b3233adcdbf3de5a63479ed02255a9cf1017ef443227fbca8eff752145f24",
      "size_bytes": 2976
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "af2a15eb6ec8f5c65ffa9b777108c94a97bae5102417be9acedbb6b383d0201f",
      "size_bytes": 13328
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "f5db72b0a45f27b3030813ea7ceb484b499e0ebfa9c9427fd12c96946e26a6d7",
      "size_bytes": 2857
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "6de8f5d27306f5198e6b5059245b72fe4972079ce9a2e3eb16746466e6b4a278",
      "size_bytes": 6537
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "e74201c68bb519c11f853f4d278864c078a265f1b4c0c7175ae64841f5efd66e",
      "size_bytes": 2689
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "915198cb35dd5afa6780593444980c7abe96847c61c80460188b1ff475a4b829",
      "size_bytes": 2012
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_COMPLETION_AUDIT_2026-05-07.md",
      "required": true,
      "role": "oti6_human_readable_input",
      "sha256": "581423c72166d4e6ed5f1c62916a603b893902e2fac6899b12837c33000e5928",
      "size_bytes": 13446
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "bcb354240d38f484c1610a2fa2eced76f5b9b732029f80611f03b8a49e952b7a",
      "size_bytes": 3546
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "3de2d8b35d272705df241a4bbc38ab2534273b5e4b6e4d6bdccc4353182e3b21",
      "size_bytes": 8319
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.md",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "ed78067acc8976209e4ee1721daa686d464026ce6a4dbac0b5343e001dbaf235",
      "size_bytes": 3976
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.md",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "3e81f25820e2a94f67274cf06f41052db4a9e96c6ec856e73ead38fab4edc1ff",
      "size_bytes": 8700
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "d5a67175ab1da11941d29440e4b490b12648a3da60cd5c0bc45d4ebec7e7bc01",
      "size_bytes": 8151
    },
    {
      "exists": true,
      "path": "research/program_control/CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "ca0a14e03cd5cc12896aa330947bcf6a08ef9f17b87b311b85165f915e895869",
      "size_bytes": 4839
    },
    {
      "exists": true,
      "path": "research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "989a8bdffe7460fc95c00c0bc15cf7f4ea6251a43008bcacb30559c2f92364c4",
      "size_bytes": 1601
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
      "required": true,
      "role": "upstream_control_input",
      "sha256": "64019a2f70f8c2b165ba5fffe0b0e22186f3b9a4b47ccc936626af50a251c084",
      "size_bytes": 5908
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
      "required": true,
      "role": "oti6_builder_verifier_test_input",
      "sha256": "b74893e4c0494cf24606f10bf5ba3ad5f11569477028ad01ec366a1e272b2829",
      "size_bytes": 37872
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
      "required": true,
      "role": "oti6_builder_verifier_test_input",
      "sha256": "6a64afbd3325cf6f42137709437c7b897983e247fa098483a636e4339d8b9443",
      "size_bytes": 7169
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
      "required": true,
      "role": "oti6_builder_verifier_test_input",
      "sha256": "00fece6656fcba7563a03ede98d5db77fbb542523ff7e3f1d1b9919d744d2478",
      "size_bytes": 7658
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
      "required": true,
      "role": "source_hashed_recovered_tick_file",
      "sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
      "size_bytes": 1584013
    }
  ],
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "missing_required_files": [],
  "mt5_order_calls": 0,
  "no_leak_review": {
    "blocked_packet_outcomes_opened": false,
    "broker_actual_r_opened": false,
    "candidate_no_leak_status": "DECISION_TIME_CONTINUATION_NO_RETRACE_CANDIDATE_NO_OUTCOME_FIELDS",
    "forbidden_source_review": {
      "account_history_accessed": false,
      "blocked_packet_outcome_source_read": false,
      "broker_actual_r_accessed": false,
      "live_order_state_accessed": false,
      "paid_or_api_or_databento_called": false,
      "resolution_log_used_only_as_permitted_lifecycle_context": true
    },
    "label_family_gate_status": "PASS",
    "live_trade_results_opened": false,
    "post_decision_context_not_used_for_cnr_e0_scoring": true
  },
  "order_calls": 0,
  "oti6_source_gate_review": {
    "all_consumed_files_hashed": true,
    "hash_failures": [],
    "local_heavy_data_inventory_enforced": true,
    "missing_required_files": [],
    "source_gate_status": "PASS"
  },
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "parquet_hash_review": {
    "expected_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
    "matches_oti6_expected": true,
    "oti6_reported_sha256_matches_expected": true,
    "recomputed_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
    "upstream_g12_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
