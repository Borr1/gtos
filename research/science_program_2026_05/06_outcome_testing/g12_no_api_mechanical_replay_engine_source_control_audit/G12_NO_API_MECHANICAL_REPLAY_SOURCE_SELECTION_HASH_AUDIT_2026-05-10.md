# Source Selection Hash Audit

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "all_large_file_hashes_have_sha256_and_size": true,
  "artifact_family": "source_selection_hash_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "excluded_source_slice_count": 3135,
  "generated_at_utc": "2026-05-10T21:10:08+00:00",
  "issues": [],
  "large_file_hash_resolution_count": 18,
  "large_file_hash_resolution_ids": [
    "SRC-00324",
    "SRC-02171",
    "SRC-02172",
    "SRC-02173",
    "SRC-02174",
    "SRC-02176",
    "SRC-02177",
    "SRC-02178",
    "SRC-02179",
    "SRC-02180",
    "SRC-02181",
    "SRC-02182",
    "SRC-02183",
    "SRC-02184",
    "SRC-02185",
    "SRC-02190",
    "SRC-02191",
    "SRC-02408"
  ],
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "selected_by_source_family": {
    "LOCAL_OHLCV_CSV": 273,
    "SIERRA_DERIVED_OHLCV_EXPORT": 92
  },
  "selected_by_symbol_count": 38,
  "selected_by_timeframe": {
    "H1": 94,
    "H4": 52,
    "M1": 60,
    "M15": 101,
    "M5": 58
  },
  "selected_source_count": 365,
  "source_universe_rows_consumed": 3500,
  "status": "PASS",
  "validation_safe": false
}
```
