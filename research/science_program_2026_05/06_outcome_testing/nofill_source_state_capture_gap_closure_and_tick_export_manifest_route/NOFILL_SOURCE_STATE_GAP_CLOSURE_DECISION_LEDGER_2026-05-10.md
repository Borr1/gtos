# Nofill Source State Gap Closure Decision Ledger 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

- terminal_decision: `ACCEPT_AS_SOURCE_STATE_GAP_CLOSURE_AND_EXPORT_MANIFEST`

## Machine Payload

```json
{
  "accepted_upstream_counts": {
    "admitted_source_bound_rows": 2,
    "blocked_rows": 37,
    "duplicate_denominators": "2/2/2",
    "rejected_rows": 9,
    "repaired_packet_hash": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
  },
  "artifact_family": "decision_ledger",
  "blocker_action_class_counts": {
    "CLEAN_DENOMINATOR_EXCLUDED_BY_CONTAMINATION_OR_EMBARGO": 17,
    "LOCAL_TICK_SOURCE_PRESENT_BUT_NOT_SUFFICIENT": 6,
    "NON_GENERATABLE_HISTORICAL_GTOS_SOURCE_STATE_FORWARD_CAPTURE_REQUIRED": 37,
    "RECOVERABLE_MARKET_DATA_BY_APPROVED_READONLY_EXTRACTION_OR_OWNER_EXPORT": 31
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_summary": "The route freezes exact source-state gap closure, tick/export requests, owner actions, and forward-capture requirements. It does not admit more rows, validate outcomes, or change live behavior.",
  "generated_at_utc": "2026-05-10T08:33:44Z",
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
  "required_fact_preservation": {
    "blockers_require_non_generatable_historical_gtos_source_state": 37,
    "contamination_embargo_blockers": 17,
    "source_state_recovered_count": 0,
    "tick_export_dependent_blockers": 31
  },
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "route_status": "historical_rows_blocked_until_exact_owner_export_or_forward_capture_requirements_are_executed_in_future_routes",
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "terminal_decision": "ACCEPT_AS_SOURCE_STATE_GAP_CLOSURE_AND_EXPORT_MANIFEST",
  "terminal_status_counts": {
    "CONTAMINATION_EMBARGO_EXCLUDED": 17,
    "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE": 1,
    "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED": 19
  },
  "validation_safe": false
}
```
