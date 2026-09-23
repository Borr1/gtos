# G12 Nofill Source State Gap Closure Owner Export Request Grouping Audit 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`
- tick_export_dependent_blocker_count: `31`
- grouped_market_data_request_count: `22`

```json
{
  "actual_symbol_set": [
    "GBPJPY",
    "GBPUSD",
    "US30_cash",
    "USDJPY",
    "XAUUSD"
  ],
  "artifact_family": "owner_export_request_grouping_audit",
  "audit_status": "PASS",
  "candidate_coverage_ok": true,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_candidate_coverage": [],
  "expected_symbol_set": [
    "GBPJPY",
    "GBPUSD",
    "US30_cash",
    "USDJPY",
    "XAUUSD"
  ],
  "extra_request_candidate_coverage": [],
  "generated_at_utc": "2026-05-10T09:13:22Z",
  "grouped_market_data_request_count": 22,
  "live_effect": false,
  "missing_tick_candidate_coverage": [],
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
  "request_rows": [
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-14T01:15:05.006410+00:00",
        "GBPJPY_2026-04-14T15:30:05.012815+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0001",
      "source_date": "2026-04-14",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-15T00:30:05.011237+00:00",
        "GBPJPY_2026-04-15T13:15:57.164919+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0002",
      "source_date": "2026-04-15",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-16T00:16:00.503237+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0003",
      "source_date": "2026-04-16",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-22T08:00:05.028587+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0004",
      "source_date": "2026-04-22",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-23T07:16:14.138817+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0005",
      "source_date": "2026-04-23",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "window_end_utc": "2026-04-23T23:59:59.999999Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-14T07:30:05.011677+00:00",
        "GBPUSD_2026-04-14T14:00:57.743957+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0006",
      "source_date": "2026-04-14",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-15T07:30:05.010905+00:00",
        "GBPUSD_2026-04-15T13:16:01.327115+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0007",
      "source_date": "2026-04-15",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-17T08:00:59.541491+00:00",
        "GBPUSD_2026-04-17T14:15:05.012317+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0008",
      "source_date": "2026-04-17",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "window_end_utc": "2026-04-17T23:59:59.999999Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-20T07:45:05.020140+00:00",
        "GBPUSD_2026-04-20T15:31:14.730975+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0009",
      "source_date": "2026-04-20",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "window_end_utc": "2026-04-20T23:59:59.999999Z",
      "window_start_utc": "2026-04-20T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-21T11:30:05.011826+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0010",
      "source_date": "2026-04-21",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "window_end_utc": "2026-04-21T23:59:59.999999Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-22T07:16:12.155934+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0011",
      "source_date": "2026-04-22",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "US30_cash_2026-04-14T08:16:00.983581+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0012",
      "source_date": "2026-04-14",
      "source_symbol": "US30_or_US30_cash_broker_alias",
      "symbol": "US30_cash",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "US30_cash_2026-04-16T13:45:56.810509+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0013",
      "source_date": "2026-04-16",
      "source_symbol": "US30_or_US30_cash_broker_alias",
      "symbol": "US30_cash",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-15T02:45:05.009485+00:00",
        "USDJPY_2026-04-15T13:15:57.398922+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0014",
      "source_date": "2026-04-15",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-16T15:00:05.011292+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0015",
      "source_date": "2026-04-16",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-21T13:45:05.018194+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0016",
      "source_date": "2026-04-21",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "window_end_utc": "2026-04-21T23:59:59.999999Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-22T00:30:05.018068+00:00",
        "USDJPY_2026-04-22T15:15:05.016051+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0017",
      "source_date": "2026-04-22",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-23T08:45:05.012266+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0018",
      "source_date": "2026-04-23",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "window_end_utc": "2026-04-23T23:59:59.999999Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-24T00:16:10.771453+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0019",
      "source_date": "2026-04-24",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "window_end_utc": "2026-04-24T23:59:59.999999Z",
      "window_start_utc": "2026-04-24T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "XAUUSD_2026-04-15T14:15:05.007998+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0020",
      "source_date": "2026-04-15",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "XAUUSD_2026-04-16T09:30:05.013547+00:00",
        "XAUUSD_2026-04-16T13:16:01.126537+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0021",
      "source_date": "2026-04-16",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "audit_status": "PASS",
      "candidate_ids": [
        "XAUUSD_2026-04-17T13:30:05.007149+00:00"
      ],
      "checks": {
        "candidate_ids_in_tick_manifest": true,
        "candidate_ids_present": true,
        "forbidden_account_order_history_constraint_present": true,
        "market_data_only_constraint_present": true,
        "owner_request_id_present": true,
        "required_fields_exact": true,
        "target_hash_requires_sha": true,
        "target_path_present": true,
        "window_present": true
      },
      "owner_request_id": "OWNER-TICK-0022",
      "source_date": "2026-04-17",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "window_end_utc": "2026-04-17T23:59:59.999999Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    }
  ],
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "symbol_request_counts": {
    "GBPJPY": 5,
    "GBPUSD": 6,
    "US30_cash": 2,
    "USDJPY": 6,
    "XAUUSD": 3
  },
  "tick_export_dependent_blocker_count": 31,
  "validation_safe": false
}
```
