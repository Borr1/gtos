# Synthetic Fixture Manifest

```json
{
  "artifact_family": "synthetic_fixture_manifest",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "coverage": {
    "duplicate_key_drift_fail_closed": true,
    "forbidden_broker_field_fail_closed": true,
    "hash_mismatch_fail_closed": true,
    "missing_bounds_fail_closed": true,
    "raw_market_blob_attempt_fail_closed": true,
    "source_bar_after_asof_fail_closed": true,
    "stale_asof_fail_closed": true,
    "valid_fvg": true,
    "valid_non_ob_geometry": true,
    "valid_ob": true
  },
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY",
  "fixture_count": 10,
  "fixture_rows": [
    {
      "expected_issue_codes": [],
      "expected_status": "PASS",
      "fixture_id": "valid_adv005_ob_valid",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/valid_adv005_ob_valid.json",
      "sha256": "3dd389c5afde7f473ed3fd693c7558e28a963c0f9807f0fcd7de3049bfecc24a"
    },
    {
      "expected_issue_codes": [],
      "expected_status": "PASS",
      "fixture_id": "valid_beh003_fvg_valid",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/valid_beh003_fvg_valid.json",
      "sha256": "914d14dc3aa5faebad7affd0301a7871ed5dc7bb69b4ef7a5d32bf18c7a5c36d"
    },
    {
      "expected_issue_codes": [],
      "expected_status": "PASS",
      "fixture_id": "valid_geo001_geometry_other_valid",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/valid_geo001_geometry_other_valid.json",
      "sha256": "c8ecc6a5425f628475c5434b0a8d23e8da1ddd387f6987907295ecb305aa965b"
    },
    {
      "expected_issue_codes": [
        "missing_poi_bounds"
      ],
      "expected_status": "FAIL",
      "fixture_id": "missing_bounds_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/missing_bounds_fail_closed.json",
      "sha256": "3d98bb225591eb8abebad6448b83f50cef40f451d2932cc204648b201d57c625"
    },
    {
      "expected_issue_codes": [
        "source_after_decision_asof"
      ],
      "expected_status": "FAIL",
      "fixture_id": "stale_asof_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/stale_asof_fail_closed.json",
      "sha256": "cb5b279c2f3a03d613fda8f1910f4dca13db1a44d1b962be84b59b7e88ce8d32"
    },
    {
      "expected_issue_codes": [
        "source_bar_after_decision_asof",
        "mso_snapshot_hash_mismatch"
      ],
      "expected_status": "FAIL",
      "fixture_id": "late_source_bar_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/late_source_bar_fail_closed.json",
      "sha256": "cbb47997759417bea9df2bc4fd8924d1e66cd5ce341721a647e9bb984315ae2d"
    },
    {
      "expected_issue_codes": [
        "forbidden_key"
      ],
      "expected_status": "FAIL",
      "fixture_id": "forbidden_broker_field_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/forbidden_broker_field_fail_closed.json",
      "sha256": "f71066bce4fcf1b3735b6b051e32f7588bef2c77376ff9216d454511644ec3b4"
    },
    {
      "expected_issue_codes": [
        "mso_snapshot_hash_mismatch"
      ],
      "expected_status": "FAIL",
      "fixture_id": "hash_mismatch_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/hash_mismatch_fail_closed.json",
      "sha256": "2919483c490bc81167c988be5c92909bf6e42d57a1091069b9eba357ec9a7ed1"
    },
    {
      "expected_issue_codes": [
        "forbidden_key"
      ],
      "expected_status": "FAIL",
      "fixture_id": "raw_blob_attempt_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/raw_blob_attempt_fail_closed.json",
      "sha256": "62f1dca4389adef2a5f3a78207c02a0f8603180a81c24776818a0559209bd929"
    },
    {
      "expected_issue_codes": [],
      "expected_status": "MIXED",
      "fixture_id": "duplicate_denominator_mismatch_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair/fixtures/duplicate_denominator_mismatch_fail_closed.jsonl",
      "sha256": "9158da369e7022bb42ddad0f2a81951000c5ee953dd0cfea644f186aa66fe5f7"
    }
  ],
  "generated_at_utc": "2026-05-13T03:45:00Z",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
  "schema_version": "scid_blocked15_poi_bounds_capture_contract_v1",
  "validation_safe": false
}
```
