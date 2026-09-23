# No Leak Duplicate Purge Embargo Source Hash Rules

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "no_leak_duplicate_purge_embargo_source_hash_rules",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_rules": [
    "Primary denominator is nofill_duplicate_key_sha256 or its source-safe equivalent.",
    "Secondary concentration denominator is duplicate_group_id_sha256 or its source-safe equivalent.",
    "Row-level counts are descriptive only until duplicate denominators are recomputed."
  ],
  "forbidden_status_only_fields": [
    "cost_testing_gate_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "mt5_order_ticket_redaction_status",
    "raw_ticket_field_present_status",
    "slippage_label_status",
    "slippage_value_redaction_status"
  ],
  "generated_at_utc": "2026-05-10T04:31:04Z",
  "live_effect": false,
  "no_leak_rules": [
    "Do not open result, cost, slippage, execution quality, broker actual-R, account history, order, deal, or position values.",
    "Use only as-of fields available at or before decision/capture timestamp; otherwise emit fail-closed missing status.",
    "Keep source/control rows separate from validation/result rows in filenames, schema, and prompt language.",
    "Reject any row whose hidden label appears in source fields, parser diagnostics, row ID, or status vocabulary."
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "purge_embargo_rules": [
    "Purge packet row ID, source row ID, source inventory ID, nofill duplicate key, and duplicate group overlap.",
    "Globally contaminated source dates from accepted G12: ['2026-04-17', '2026-04-20', '2026-04-30', '2026-05-01', '2026-05-03', '2026-05-04', '2026-05-05', '2026-05-06'].",
    "Apply at least one-day same-symbol/source-lane embargo around contaminated source dates before source expansion.",
    "G12 may tighten the embargo if source-lane timestamps show same-event leakage."
  ],
  "route_id": "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW",
  "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1",
  "source_hash_rules": [
    "Hash every raw tick/shadow/Sierra/source artifact consumed.",
    "Hash parser code and route builder code.",
    "Record path, size, mtime when available, sha256, parser version, and source contract ID.",
    "Never rely on local-heavy metadata alone as validation-safe evidence."
  ],
  "validation_safe": false
}
```
