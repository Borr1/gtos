# Catalog Row Count Schema Audit

Route: `G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "catalog_row_count_schema_audit",
  "audit_passed": true,
  "catalog_sensitive_path_row_count": 0,
  "catalog_sensitive_path_rows": [],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "expected_counts": {
    "acquisition_requests": 42,
    "catalog_rows": 1200,
    "large_file_deferrals": 124,
    "negative_search_rows": 4,
    "non_generatable_source_state_gaps": 20,
    "positive_search_rows": 2,
    "recoverable_market_data_windows": 22,
    "search_queries": 6,
    "small_hash_rows": 1076
  },
  "expected_counts_reconciled": true,
  "generated_at_utc": "2026-05-10T07:24:26Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "persisted_catalog_row_count": 1200,
  "persisted_hash_recompute": {
    "bad_size_deferrals": [],
    "hash_mismatches": [],
    "missing_deferrals": [],
    "missing_hash_rows": [
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\README.md",
        "catalog_row_id": "LCAT-001070",
        "recorded_sha256": "4034c8a7f9eac366256e7850dd597b699538731a5fc23a6f2932cd415aa6c090",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\RED_TEAM_100_PERCENT.md",
        "catalog_row_id": "LCAT-001071",
        "recorded_sha256": "9277da81c85664a1142e18f05ccc1c49b1b08f88b5ebafeb4c4883d64fcb2f82",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\TP_INVERSION_BUG_REPORT.md",
        "catalog_row_id": "LCAT-001072",
        "recorded_sha256": "0cc6638e9da994bd3bc4c6caba4c5420281a59680dd0cc87c9a99110fdd3a65c",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\ULTRAPLAN_APR9_2026.md",
        "catalog_row_id": "LCAT-001073",
        "recorded_sha256": "265aec8a0357ec260a944e8ce835acff676c6019849f90a33990ebe0e1fed5bb",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_F2.1_REPORT.md",
        "catalog_row_id": "LCAT-001074",
        "recorded_sha256": "47651750d0135e6c1eabe4a28fdc34cba4f75de621f91b2e9340fa7beb2a195a",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_R1_REPORT.md",
        "catalog_row_id": "LCAT-001075",
        "recorded_sha256": "c065835fba41af1310bc689f154338d9c07179c35e39085e51daeaf21f12565a",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_R2_REPORT.md",
        "catalog_row_id": "LCAT-001076",
        "recorded_sha256": "e4dc7aaa0b10fef9336c10bcc54b371491d44da2b32ba729f8eec13c4737ca98",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_R3_REPORT.md",
        "catalog_row_id": "LCAT-001077",
        "recorded_sha256": "c21f1175c65e19be76bc7852db90e9ee9cb6990414f6f98e914037d0c1e731e3",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_R4_REPORT.md",
        "catalog_row_id": "LCAT-001078",
        "recorded_sha256": "9fdd908676800f304e35d30783e5833934e9b3751ceadeb057fc21b708eba1cc",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_R5_REPORT.md",
        "catalog_row_id": "LCAT-001079",
        "recorded_sha256": "9ef0fd20e9d46c66a75ef064e05985c0f69abbc41494ef3a2f2dbad72f711446",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE1_R6_REPORT.md",
        "catalog_row_id": "LCAT-001080",
        "recorded_sha256": "615fe9850a284d62038adb1563a77ce089f8d0ff63b9a10f0f34193f963eaa21",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE2_F2_SWEEP_REPORT.md",
        "catalog_row_id": "LCAT-001081",
        "recorded_sha256": "14c825a4066376eef48f9898e0a1a4af7dc723c3913c0bf83f1cfeebdb6a879c",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\WAVE2_F3_SYNTHESIS_REPORT.md",
        "catalog_row_id": "LCAT-001082",
        "recorded_sha256": "fee66d495d97c376ab560541635f70c5fe6e83fbb760ab92d6fe6454a64acaa8",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\XAUUSD_M1.csv",
        "catalog_row_id": "LCAT-001083",
        "recorded_sha256": "e76034fc472b62bcb4968c40aea8e5f94b318d96b6ebaad6e3324be96847b79b",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\XAUUSD_M5.csv",
        "catalog_row_id": "LCAT-001084",
        "recorded_sha256": "358ae52806decee2967d301c006449144c3a6d8dd991c997512955f1c3b43d61",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\_f3_aggregator.py",
        "catalog_row_id": "LCAT-001085",
        "recorded_sha256": "8b1b33f07785a07abe8731ffcf1556dbb991ea277e64aaec21a21a56aa0f0b62",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\quick_reference_card.md",
        "catalog_row_id": "LCAT-001086",
        "recorded_sha256": "0a5e7db08d43c3ae0ffa32e5d70165c53b32b8422c3720d65c47f3179748bf89",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\r_multiple_analysis.md",
        "catalog_row_id": "LCAT-001087",
        "recorded_sha256": "8ef0f41a154d26e4a41a3ac64c23c5fca546e7204d4ea9bed0bab6da0b3839f3",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\reasoning_text_mining.md",
        "catalog_row_id": "LCAT-001088",
        "recorded_sha256": "036f3e9bb8b91291edfd10cc6441cde765c69c63498b94c2578f6e5ebf95985b",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\regime_tagging.py",
        "catalog_row_id": "LCAT-001089",
        "recorded_sha256": "00292b74913c555fd53f0d95ad8898c5e786f407647aae9ca8dd8567d9777a60",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\regime_tagging_results.md",
        "catalog_row_id": "LCAT-001090",
        "recorded_sha256": "e8bed26310e4baa8d46086095eb2b0a69021ad3b5a569cecd99ccca4c5f30724",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\requirements.txt",
        "catalog_row_id": "LCAT-001091",
        "recorded_sha256": "ff6cc2a63d657ee5f0b79a8ec55a47e7aef018df4f7c0feae3fb7a0f71308df7",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\run_agent.py",
        "catalog_row_id": "LCAT-001092",
        "recorded_sha256": "92d0cb559c5cf85a3b86368fe45c5088ff5d0869f4eb283eb27a80dfaea58b70",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\run_comprehensive_tests.py",
        "catalog_row_id": "LCAT-001093",
        "recorded_sha256": "0267415c20942333304b0fbbdac44133183a35eda12e6fcad4206ef9cba2091b",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\session_engineering_report.md",
        "catalog_row_id": "LCAT-001094",
        "recorded_sha256": "3aaeda017451df2db02ad5a6fd448d23dd0e021bf394b5d4cc78979b194f6c47",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\signal_activation_audit.md",
        "catalog_row_id": "LCAT-001095",
        "recorded_sha256": "f5b0e3bc54b358310c6e9be48d450fcc745cc3001e403f900cdeb88e6c74ba94",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\skills-lock.json",
        "catalog_row_id": "LCAT-001096",
        "recorded_sha256": "50a054221fd4de8c4e435f77cba58e9db7619522bc810f24eed4e474ccd3482b",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\test_a_momentum_baseline_results.md",
        "catalog_row_id": "LCAT-001097",
        "recorded_sha256": "35dbd48f4fca2ca787bdd79c42c4bc3392b7cb99bc4f744d1add96ae86945e79",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\test_a_rerun_real_bos_results.md",
        "catalog_row_id": "LCAT-001098",
        "recorded_sha256": "96b5aeb5a2c54b90f209f86fa8cb5e391cfb1399b98a94b47f2bc6108cb8ad58",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\CNR061GEOM\\test_b_results.md",
        "catalog_row_id": "LCAT-001099",
        "recorded_sha256": "0f9d98df80125432dc7410c864aedd85b08ea887840e841adc7b87b830565036",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.agents\\skills\\youtube-transcript\\SKILL.md",
        "catalog_row_id": "LCAT-001185",
        "recorded_sha256": "df92ca595baca73cefab145d82680a7949e9ca471cb894df2a614848b2f04b83",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.claude\\skills\\codebase-verify.md",
        "catalog_row_id": "LCAT-001186",
        "recorded_sha256": "d5385a425b24926d3ad27e88f5a764b8b6c5137d4e6f60d1a86fb28b34e46092",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.claude\\skills\\kb-cross-reference.md",
        "catalog_row_id": "LCAT-001187",
        "recorded_sha256": "b3aa82db2be6944f8a35eea4b3a6aee18e461888cff516e7bc9ee6e6ec49a880",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.claude\\skills\\red-team-checklist.md",
        "catalog_row_id": "LCAT-001188",
        "recorded_sha256": "0b175b6325c0a80d236ba4f77049e4963224ca8a46e043af7f80e42a3ccec5b3",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.claude\\skills\\statistical-testing.md",
        "catalog_row_id": "LCAT-001189",
        "recorded_sha256": "1e6503e363bade6955c6961c6487574428d749946aeda4422bbbf9b627476637",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_READING_ORDER.md",
        "catalog_row_id": "LCAT-001190",
        "recorded_sha256": "2ec3964df18b42c89059de7cac803d96d9c30e9d330439000695cd444e0fecfc",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\LIVE_STATE.md",
        "catalog_row_id": "LCAT-001191",
        "recorded_sha256": "5a7e9e14235fcc8456ae66195eac13bbb2b11417536a65ffe1070952a452ed2c",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\SESSION_43_PAUSE_SNAPSHOT.md",
        "catalog_row_id": "LCAT-001192",
        "recorded_sha256": "fc2096dedd49ef266e0544cc7a822d0c7d2bfab86e0d0196fa18e676f4e0a5db",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\architecture.md",
        "catalog_row_id": "LCAT-001193",
        "recorded_sha256": "09eea96a9a7fe5ab8981421a8507ad0c98642dc1acac1f0050b57c0b31fcce08",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\goal_session_research_discipline.md",
        "catalog_row_id": "LCAT-001194",
        "recorded_sha256": "02f1e0b5e8d18eaf6fec657b4ace9169096d83a778e68cf311f8004de7ae198c",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\local_heavy_data_inventory.md",
        "catalog_row_id": "LCAT-001195",
        "recorded_sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\master_roadmap.md",
        "catalog_row_id": "LCAT-001196",
        "recorded_sha256": "049dbf4d38159d4639cacf9231245b9422da998b2bf44d73783a6f38ef435d43",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\pre_lock_final_review.md",
        "catalog_row_id": "LCAT-001197",
        "recorded_sha256": "86245d137ecff092238c122cd491cc5928cc67c598410e1c1d0686f923955694",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\quick_reference_card.md",
        "catalog_row_id": "LCAT-001198",
        "recorded_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\research_current_state.md",
        "catalog_row_id": "LCAT-001199",
        "recorded_sha256": "0dc4a6170930b446c6d3d9195506a8af2869b4de70e90262c9c7f1aa796123b6",
        "root_id": "prior_worktree_root"
      },
      {
        "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.context\\00_core\\research_operating_doctrine.md",
        "catalog_row_id": "LCAT-001200",
        "recorded_sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe",
        "root_id": "prior_worktree_root"
      }
    ],
    "persisted_large_deferral_bad_size_count": 0,
    "persisted_large_deferral_missing_count": 0,
    "persisted_large_deferral_stat_checked": 124,
    "persisted_large_file_deferrals": 124,
    "persisted_small_hash_mismatch_count": 0,
    "persisted_small_hash_missing_count": 46,
    "persisted_small_hash_rows": 1076,
    "persisted_small_hashes_recomputed_currently": 1030
  },
  "persisted_hash_status_counts": {
    "deferred_large_file_requires_dedicated_hash_manifest": 124,
    "sha256_complete": 1076
  },
  "persisted_large_file_deferral_rows": 124,
  "persisted_small_hash_rows": 1076,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_fields_count": 21,
  "route_id": "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT",
  "row_field_missing": [],
  "row_field_missing_count": 0,
  "runtime_recomputed_catalog_row_count": 1200,
  "runtime_recomputed_large_file_deferrals": 124,
  "runtime_recomputed_small_hash_rows": 1076,
  "safe_flag_issue_count": 0,
  "safe_flag_issues": [],
  "schema_version": "g12_gtos_local_research_data_catalog_source_control_audit_v1",
  "source_control_only_row_count": 1200,
  "target_catalog_path": "research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_2026-05-10.jsonl",
  "terminal_decision": "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
  "validation_safe": false,
  "weak_large_file_consumption_count": 0,
  "weak_large_file_consumption_rows": []
}
```
