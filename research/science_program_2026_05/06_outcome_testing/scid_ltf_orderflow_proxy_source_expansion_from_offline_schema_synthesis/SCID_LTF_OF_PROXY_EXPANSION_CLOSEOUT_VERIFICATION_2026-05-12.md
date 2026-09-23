# Closeout Verification

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "CLOSEOUT_VERIFICATION",
  "builder_completed": true,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "focused_pytest": {
    "command": "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
    "observed_result": "6 passed",
    "status": "PASSED"
  },
  "generated_at_utc": "2026-05-12T05:37:18Z",
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
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "scoped_git_status": {
    "no_scoped_forbidden_live_surface": true,
    "no_scoped_raw_market_blob": true,
    "returncode": 0,
    "scoped_entries": [],
    "stderr": [
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied"
    ],
    "unrelated_dirty_entry_count": 0
  },
  "standalone_verifier": {
    "command": "python research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
    "observed_result": "ok=true",
    "status": "PASSED"
  },
  "terminal_decision": "BUILT_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_G12_AUDIT_REQUIRED",
  "validation_safe": false
}
```
