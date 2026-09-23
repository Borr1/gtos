# Nofill Source State Gap Closure G0 Blocker Ingestion Reconciliation 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "artifact_family": "g0_blocker_ingestion_reconciliation",
  "blocker_candidate_ids": [
    "GBPJPY_2026-04-14T01:15:05.006410+00:00",
    "GBPJPY_2026-04-14T15:30:05.012815+00:00",
    "GBPJPY_2026-04-15T00:30:05.011237+00:00",
    "GBPJPY_2026-04-15T13:15:57.164919+00:00",
    "GBPJPY_2026-04-16T00:16:00.503237+00:00",
    "GBPJPY_2026-04-22T08:00:05.028587+00:00",
    "GBPJPY_2026-04-23T07:16:14.138817+00:00",
    "GBPJPY_2026-04-28T09:00:05.010558+00:00",
    "GBPUSD_2026-04-14T07:30:05.011677+00:00",
    "GBPUSD_2026-04-14T14:00:57.743957+00:00",
    "GBPUSD_2026-04-15T07:30:05.010905+00:00",
    "GBPUSD_2026-04-15T13:16:01.327115+00:00",
    "GBPUSD_2026-04-17T08:00:59.541491+00:00",
    "GBPUSD_2026-04-17T14:15:05.012317+00:00",
    "GBPUSD_2026-04-20T07:45:05.020140+00:00",
    "GBPUSD_2026-04-20T15:31:14.730975+00:00",
    "GBPUSD_2026-04-21T11:30:05.011826+00:00",
    "GBPUSD_2026-04-22T07:16:12.155934+00:00",
    "NAS100_2026-04-29T15:00:05.012307+00:00",
    "NAS100_2026-05-01T08:15:00+00:00",
    "US30_cash_2026-04-14T08:16:00.983581+00:00",
    "US30_cash_2026-04-16T13:45:56.810509+00:00",
    "USDJPY_2026-04-15T02:45:05.009485+00:00",
    "USDJPY_2026-04-15T13:15:57.398922+00:00",
    "USDJPY_2026-04-16T15:00:05.011292+00:00",
    "USDJPY_2026-04-21T13:45:05.018194+00:00",
    "USDJPY_2026-04-22T00:30:05.018068+00:00",
    "USDJPY_2026-04-22T15:15:05.016051+00:00",
    "USDJPY_2026-04-23T08:45:05.012266+00:00",
    "USDJPY_2026-04-24T00:16:10.771453+00:00",
    "XAGUSD_2026-05-01T08:30:00+00:00",
    "XAUUSD_2026-04-15T14:15:05.007998+00:00",
    "XAUUSD_2026-04-16T09:30:05.013547+00:00",
    "XAUUSD_2026-04-16T13:16:01.126537+00:00",
    "XAUUSD_2026-04-17T13:30:05.007149+00:00",
    "XAUUSD_2026-05-01T08:15:00+00:00",
    "XAUUSD_2026-05-01T15:45:00+00:00"
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "g0_catalog_implications": {
    "blockers_with_local_tick_catalog_match": 6,
    "blockers_with_non_generatable_source_state_gap": 37,
    "blockers_without_local_tick_catalog_match": 31,
    "implication": "Catalog refresh changes no blocker into an admitted row because every blocker still has a pending-lifecycle/source-state truth gap. Recovered or recoverable ticks are useful only after source-state truth exists or prospective capture creates new rows."
  },
  "g0_completion_can_mark_goal_complete": true,
  "g0_next_route_selected": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
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
  "reconciled_counts": {
    "admitted_rows": 2,
    "blocker_rows": 37,
    "duplicate_denominators": "2/2/2",
    "reject_rows": 9,
    "repaired_packet_hash": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
  },
  "reject_candidate_ids": [
    "GBPJPY_2026-05-04T03:00:00+00:00",
    "GBPJPY_2026-05-06T02:30:00+00:00",
    "NAS100_2026-05-03T16:15:00+00:00",
    "NAS100_2026-05-04T07:15:00+00:00",
    "NAS100_2026-05-05T07:15:00+00:00",
    "NAS100_2026-05-06T07:15:00+00:00",
    "NAS100_2026-05-07T07:15:00+00:00",
    "XAUUSD_2026-05-04T07:15:00+00:00",
    "XAUUSD_2026-05-05T08:15:00+00:00"
  ],
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "source_g0_route": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW",
  "source_g0_terminal_decision": "ACCEPT_WITH_EXACT_SOURCE_EXPANSION_OR_CATALOG_REFRESH_FOLLOWUPS",
  "validation_safe": false
}
```
