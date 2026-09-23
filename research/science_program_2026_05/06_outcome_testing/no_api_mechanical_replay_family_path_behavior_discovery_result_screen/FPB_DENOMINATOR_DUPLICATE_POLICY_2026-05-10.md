# Denominator Duplicate Policy

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "accepted_duplicate_candidate_keys": 687275,
  "accepted_raw_candidate_attempts": 13540033,
  "accepted_unique_nonduplicate_candidate_path_label_denominator": 12852758,
  "artifact_family": "denominator_duplicate_policy",
  "changes_live_trading_behavior": false,
  "counts_match_accepted_headline": true,
  "credentials_touched": false,
  "duplicate_key_policy": "candidate duplicate key is symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256 per accepted substrate; duplicates are excluded from family/path-label denominators.",
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "frozen_before_family_comparisons": true,
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
  "path_label_duplicate_policy": "one discovery path label is closed for each unique nonduplicate candidate; duplicate path keys remain zero under the accepted scanner contract.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recomputed_duplicate_candidate_keys": 687275,
  "recomputed_path_label_count": 12852758,
  "recomputed_raw_candidate_attempts": 13540033,
  "recomputed_unique_nonduplicate_denominator": 12852758,
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "validation_safe": false
}
```
