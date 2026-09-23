# Git Lfs Storage Audit

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "artifact_family": "git_lfs_storage_materialization_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-10T21:10:26+00:00",
  "git_lfs_fsck_returncode": 0,
  "git_lfs_fsck_stderr": "",
  "git_lfs_fsck_stdout": "Git LFS fsck OK",
  "git_lfs_ls_files_contains_large_artifacts": true,
  "issues": [],
  "large_jsonl_records": [
    {
      "head_blob_is_lfs_pointer": true,
      "head_blob_size": 134,
      "local_lfs_object_exists": true,
      "local_lfs_object_size": 205437302,
      "local_materialized_for_jsonl_parsing": true,
      "local_worktree_sha256": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
      "local_worktree_size": 205437302,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl",
      "pointer_matches_local_lfs_object_size": true,
      "pointer_matches_local_worktree": true,
      "pointer_oid": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
      "pointer_size": 205437302,
      "repo_path": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_engine_from_source_universe/NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl"
    },
    {
      "head_blob_is_lfs_pointer": true,
      "head_blob_size": 134,
      "local_lfs_object_exists": true,
      "local_lfs_object_size": 170589802,
      "local_materialized_for_jsonl_parsing": true,
      "local_worktree_sha256": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
      "local_worktree_size": 170589802,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl",
      "pointer_matches_local_lfs_object_size": true,
      "pointer_matches_local_worktree": true,
      "pointer_oid": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
      "pointer_size": 170589802,
      "repo_path": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_engine_from_source_universe/NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl"
    }
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
  "raw_blob_violations_over_100mb": [],
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "status": "PASS",
  "validation_safe": false
}
```
