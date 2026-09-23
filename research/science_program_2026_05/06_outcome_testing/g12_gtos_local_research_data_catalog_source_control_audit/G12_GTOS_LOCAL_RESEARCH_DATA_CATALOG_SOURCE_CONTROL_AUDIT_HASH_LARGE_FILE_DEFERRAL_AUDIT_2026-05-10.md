# Hash Large File Deferral Audit

Route: `G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "hash_large_file_deferral_audit",
  "audit_passed": true,
  "catalog_hashed_file_count": 1076,
  "catalog_large_file_deferral_count": 124,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_followup_for_missing_persisted_hash_rows": "Do not cite the 46 persisted prior_worktree_root hash rows as current files; rerun the target builder in the consuming worktree to refresh the bounded catalog before source use.",
  "generated_at_utc": "2026-05-10T07:24:26Z",
  "live_effect": false,
  "manifest_hashed_file_count": 1076,
  "manifest_large_file_deferral_count": 124,
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
  "persisted_hash_rows_currently_missing": 46,
  "persisted_hash_rows_currently_missing_samples": [
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
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT",
  "runtime_recomputed_hashed_file_count": 1076,
  "runtime_recomputed_hashes_verified": 1076,
  "runtime_recomputed_large_file_deferral_count": 124,
  "schema_version": "g12_gtos_local_research_data_catalog_source_control_audit_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
  "validation_safe": false
}
```
