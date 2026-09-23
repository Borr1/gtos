# G12 OTI5 OTR061 Source Hash Noleak Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Confirms source-hash and no-leak boundaries for the combined audit scope.
- Keeps broker actual-R, account history, live result labels, and paid/API sources closed.

```json
{
  "artifact_family": "G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT",
  "audit_verdict": "PASS_SOURCE_HASH_AND_NOLEAK_FOR_QUARANTINED_SCOPE",
  "forbidden_surface_diff_scope": {
    "allowed_written_directory": "research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit",
    "live_trading_surface_edits_allowed": false,
    "mt5_order_behavior_allowed": false,
    "paid_api_databento_allowed": false
  },
  "generated_at_utc": "2026-05-07T09:59:44Z",
  "hashed_evidence_files": [
    {
      "bytes": 219241,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_RESULT_LEDGER_2026-05-07.json",
      "sha256": "b49369d55d080206528f0068fa44dd7c8b86618cd3675b11aa814c93dc3a169f"
    },
    {
      "bytes": 2069,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_METHOD_FREEZE_2026-05-07.json",
      "sha256": "1070c7fb034c191b5aaef3a39640a09dddebdf182acbdae985b6fcb24e8dddb4"
    },
    {
      "bytes": 25276,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
      "sha256": "9999f727c7e6fe4235e2975d89e8fa49cb6b04965544cf8220ba7556b36a7200"
    },
    {
      "bytes": 9650,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
      "sha256": "bad5d01825ff094f4e7db50a8d821e474d4462cdba3f8fb5fbf20af7f17a29dc"
    },
    {
      "bytes": 950,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_2026-05-07.json",
      "sha256": "b5f8ca82c3e3e549e6c4f768fe88ed7750c27fb73a4467f23c4874f2bd2accfd"
    },
    {
      "bytes": 1323,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
      "sha256": "17c5c428913cb731e8793e9ac8f87d0474fd65f64d90686f47e1dec10afdea13"
    },
    {
      "bytes": 6455,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_COMPLETION_AUDIT_2026-05-07.json",
      "sha256": "8013d5e2fabe34ab93455359690dc55fca2df7c2e930baa4332337a11b2ea126"
    },
    {
      "bytes": 181544,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti5_g6_cusum_changepoint_quarantined_results\\OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
      "sha256": "22c71896a12735def2ce065167ab12f779e7aaad92412ab23288d52bbc07a0a6"
    },
    {
      "bytes": 1965,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.json",
      "sha256": "236d424940182f7509a2677a30e6799a4011c35cf61fd8ece97b5823670a36da"
    },
    {
      "bytes": 8151,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
      "sha256": "d5a67175ab1da11941d29440e4b490b12648a3da60cd5c0bc45d4ebec7e7bc01"
    },
    {
      "bytes": 26482,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json",
      "sha256": "363652d3bba49d3335adba038f1649944d1908c35701fded2746635bcc253da1"
    },
    {
      "bytes": 248722,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json",
      "sha256": "0f8c79e1f58ffed286d8ce823c96bc28d38dca586a6a4fcc4cee84ac5a1f5eb8"
    },
    {
      "bytes": 7144,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_COMPLETION_AUDIT_2026-05-07.json",
      "sha256": "eda7311fd5ef06853b91f5dd19fbd54aac787c1145d2274f39648ccedad22868"
    },
    {
      "bytes": 1584013,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
      "sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
    },
    {
      "bytes": 13170,
      "path": ".context\\LIVE_STATE.md",
      "sha256": "6833ded6bf1ddeec45bacba9dddafdf571d131bd010e1ab670374c4de0aaba23"
    },
    {
      "bytes": 25348,
      "path": ".context\\02_session_handoffs\\SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235"
    },
    {
      "bytes": 11078,
      "path": ".context\\00_core\\quick_reference_card.md",
      "sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd"
    },
    {
      "bytes": 11400,
      "path": ".context\\00_core\\research_operating_doctrine.md",
      "sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe"
    },
    {
      "bytes": 395854,
      "path": ".context\\00_core\\research_current_state.md",
      "sha256": "1b895df3e5d7702d7b58fe8e97ce7ded769be3d891b7591eeb5f278fd43eff00"
    },
    {
      "bytes": 4988,
      "path": ".context\\00_core\\goal_session_research_discipline.md",
      "sha256": "cf4aeedd800ddd8f81abb7158cdc1686801a2df132fefeab5ad33fd343df1e36"
    },
    {
      "bytes": 4218,
      "path": ".context\\00_core\\local_heavy_data_inventory.md",
      "sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0"
    },
    {
      "bytes": 5908,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
      "sha256": "64019a2f70f8c2b165ba5fffe0b0e22186f3b9a4b47ccc936626af50a251c084"
    },
    {
      "bytes": 9841,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_otx_g6_post_audit\\G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json",
      "sha256": "bb0f5428ef5e9e3de376caa9ecd0544ca0d891842fa8f0dcac3f800d1deb6f2c"
    },
    {
      "bytes": 1207034,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
      "sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224"
    },
    {
      "bytes": 11704,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_oti5_otr061_post_audit\\G12_OTI5_OTR061_POST_AUDIT_GOAL_PROMPT_2026-05-07.md",
      "sha256": "54aa37ec677ce1a192faad4f548b939301817f44ded783936f4322cae006fe44"
    }
  ],
  "live_effect": false,
  "noleak_review": {
    "oti5_blocked_packet_outcomes_opened": false,
    "oti5_broker_actual_r_opened": false,
    "oti5_forbidden_input_key_hit_count": 0,
    "oti5_live_trade_results_opened": false,
    "oti5_row_forbidden_key_hits_excluding_allowed_synthetic_r": [],
    "otr061_account_history_accessed": false,
    "otr061_broker_actual_r_accessed": false,
    "otr061_live_order_state_accessed": false,
    "otr061_result_label_key_hits": []
  },
  "oti5_source_hash_review": {
    "all_consumed_files_hashed": true,
    "feature_asof_failures": [],
    "material_source_hash_failure_count": 0,
    "missing_loaded_table_audit_note": "One OTI5 report table lacks an expected hash reference, but material_source_hash_failure_count=0 and no row-level consumed path/source hash failure is present; not a G12 rejection basis for quarantined discovery.",
    "source_gate_pass": true,
    "tick_expected_hash_missing_loaded_tables": [
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-04.parquet"
    ],
    "tick_files_rehashed_count": 15
  },
  "otr061_source_hash_review": {
    "all_used_files_hashed": true,
    "current_parquet_hash_matches_expected": true,
    "missing_hash_rows": [],
    "parquet_rows_direct": 89391,
    "recovered_parquet_current_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
    "recovered_parquet_expected_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
  },
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
