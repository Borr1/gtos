# Compact Cap Diagnostics

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "artifact_family": "compact_cap_diagnostics",
  "changes_live_trading_behavior": false,
  "compact_candidate_rows_suppressed_by_artifact_cap": 12732758,
  "compact_candidate_rows_written": 120000,
  "compact_path_label_rows_suppressed_by_artifact_cap": 12732758,
  "compact_path_label_rows_written": 120000,
  "compact_rows_policy": "Compact rows are schema/parser sanity evidence only and are not decisive ranking evidence because this route builds full-population aggregate counters.",
  "credentials_touched": false,
  "decisive_ranking_uses_compact_sample": false,
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "full_stream_aggregate_used_for_route_priority": true,
  "g0_compact_sample_scope_note": "The compact artifacts are materialized LFS rows capped at 120000 rows each. These cross-tabs are compact-sample-only and must not be treated as full-stream family label distributions.",
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "validation_safe": false
}
```
