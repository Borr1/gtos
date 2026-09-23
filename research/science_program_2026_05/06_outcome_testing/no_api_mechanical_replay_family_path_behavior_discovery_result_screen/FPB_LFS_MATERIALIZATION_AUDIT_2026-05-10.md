# LFS Materialization Audit

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "all_lfs_checks_pass": true,
  "artifact_family": "lfs_materialization_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "generated_at_utc": "2026-05-11T04:20:56+00:00",
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
  "policy": "Accepted compact JSONL artifacts must be LFS pointers in HEAD and materialized locally before any parsing; this route does not add new raw JSONL row blobs.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "rows": [
    {
      "artifact": "candidate_compact_rows",
      "expected_lfs_oid": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
      "expected_lfs_size": 205437302,
      "head_blob_size": 134,
      "head_is_lfs_pointer": true,
      "head_lfs_oid": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
      "head_lfs_size": 205437302,
      "local_exists": true,
      "local_materialized_jsonl": true,
      "local_sha256": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
      "local_size": 205437302,
      "passes": true,
      "path": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_engine_from_source_universe/NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl"
    },
    {
      "artifact": "path_label_compact_rows",
      "expected_lfs_oid": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
      "expected_lfs_size": 170589802,
      "head_blob_size": 134,
      "head_is_lfs_pointer": true,
      "head_lfs_oid": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
      "head_lfs_size": 170589802,
      "local_exists": true,
      "local_materialized_jsonl": true,
      "local_sha256": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
      "local_size": 170589802,
      "passes": true,
      "path": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_engine_from_source_universe/NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl"
    }
  ],
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "validation_safe": false
}
```
