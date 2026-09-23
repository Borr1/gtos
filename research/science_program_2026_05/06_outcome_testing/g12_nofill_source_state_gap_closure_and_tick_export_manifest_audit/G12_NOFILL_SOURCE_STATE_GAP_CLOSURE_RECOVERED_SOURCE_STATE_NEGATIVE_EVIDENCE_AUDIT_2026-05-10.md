# G12 Nofill Source State Gap Closure Recovered Source State Negative Evidence Audit 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`
- recovered_source_state_count: `0`

```json
{
  "artifact_family": "recovered_source_state_negative_evidence_audit",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:13:22Z",
  "live_effect": false,
  "negative_evidence_ids_match_blocker_ids": true,
  "negative_evidence_ids_match_proof_ids": true,
  "negative_evidence_row_count": 37,
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
  "recovered_source_state_count": 0,
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "rows": [
    {
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-16",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-22",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-23",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPJPY_2026-04-28T09:00:05.010558+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-28",
      "symbol": "GBPJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-14",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-14",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-17",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-17",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-20",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-20",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-21",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-22",
      "symbol": "GBPUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "NAS100_2026-04-29T15:00:05.012307+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-29",
      "symbol": "NAS100",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "NAS100_2026-05-01T08:15:00+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-05-01",
      "symbol": "NAS100",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-14",
      "symbol": "US30_cash",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-16",
      "symbol": "US30_cash",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-16",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-21",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-22",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-22",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-23",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-24",
      "symbol": "USDJPY",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAGUSD_2026-05-01T08:30:00+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-05-01",
      "symbol": "XAGUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-15",
      "symbol": "XAUUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-16",
      "symbol": "XAUUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-16",
      "symbol": "XAUUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-04-17",
      "symbol": "XAUUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAUUSD_2026-05-01T08:15:00+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-05-01",
      "symbol": "XAUUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    },
    {
      "candidate_id": "XAUUSD_2026-05-01T15:45:00+00:00",
      "existing_source_safe_evidence_found": false,
      "source_date": "2026-05-01",
      "symbol": "XAUUSD",
      "why_not_recovered": "Price, ticks, and bars can show market movement, but they cannot recreate whether GTOS persisted a pending intent, the lifecycle group id, source-safe order observability, write-clock timestamps, ticket redaction status, native pending type, or final lifecycle state at decision time. Those facts require an existing source-safe log row or future capture."
    }
  ],
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "validation_safe": false
}
```
