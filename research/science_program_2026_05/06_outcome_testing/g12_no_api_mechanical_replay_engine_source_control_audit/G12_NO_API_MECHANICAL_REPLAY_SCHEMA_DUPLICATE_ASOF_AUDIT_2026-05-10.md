# Schema Duplicate Asof Audit

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "artifact_family": "schema_duplicate_asof_projection_audit",
  "candidate_duplicate_key": "symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_key_uses_source_safe_fields_only": true,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-10T21:10:22+00:00",
  "issues": [],
  "live_effect": false,
  "no_lookahead_rules": [
    "mechanical family definitions are static in this artifact before scanning OHLC rows",
    "swing-based events require confirmed swings after two right-side bars have closed",
    "candidate rows use only bars closed at or before decision_time_utc",
    "path-label rows are separate discovery labels and never decision inputs",
    "historical GTOS AI intent remains projection-only unless source-logged prompt/input/output/gate/lifecycle truth exists"
  ],
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
  "path_label_policy": {
    "forbidden_label_claims": [
      "PnL",
      "broker actual outcome",
      "win-rate",
      "expectancy",
      "validation result"
    ],
    "label_family": "DISCOVERY_PATH_LABEL_ONLY"
  },
  "projection_boundary": {
    "all_candidate_rows_projection_only": true,
    "historical_pending_lifecycle_truth_inferred_from_price": false,
    "original_gtos_ai_intent_claimed": false
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "source_duplicate_key": "source_family|symbol|timeframe|source_sha256",
  "status": "PASS",
  "validation_safe": false
}
```
