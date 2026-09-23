# Shadow Log Schema Gap Repair - 2026-05-06

Quarantined path-source-incomplete rows written during the MT5 IPC outage. Rows were removed from path/outcome logs instead of backfilled with false touch flags, because no M15 bars means no path observation.

```json
{
  "created_at_utc": "2026-05-06T11:31:10.919201+00:00",
  "reason": "Quarantine path-source-incomplete rows written during MT5 IPC outage; do not fabricate touch/TP/SL booleans.",
  "schema_version": "shadow_log_schema_gap_repair_v1",
  "targets": {
    "candidate_path_follow.jsonl": {
      "bad_json_passthrough_rows": 0,
      "kept_rows": 1789,
      "quarantine_path": "research\\operations\\shadow_log_schema_gap_repair_2026-05-06\\candidate_path_follow.jsonl.quarantine.jsonl",
      "quarantined_rows": 5
    },
    "live_mechanical_strategy_shadow_outcomes.jsonl": {
      "bad_json_passthrough_rows": 0,
      "kept_rows": 39938,
      "quarantine_path": "research\\operations\\shadow_log_schema_gap_repair_2026-05-06\\live_mechanical_strategy_shadow_outcomes.jsonl.quarantine.jsonl",
      "quarantined_rows": 64
    }
  }
}
```
