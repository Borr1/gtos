# NOFILL Read-Only Tick Recovery Ladder Ledger

Route: `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary
- `tick_export_dependent_blocker_count`: `31`
- `grouped_request_count`: `22`
- `recovered_grouped_request_count`: `20`
- `remaining_owner_export_request_count`: `2`
- `recovered_candidate_row_count`: `28`
- `remaining_candidate_row_count`: `3`
- `contamination_embargo_excluded_row_count`: `12`

## Machine Payload

```json
{
  "artifact_family": "row_window_recovery_ladder_ledger",
  "candidate_rows": [
    {
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "candidate_utc": "2026-04-14T01:15:05.006410Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0001",
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-14.parquet",
      "source_sha256": "5bd866e1fc74b8d2f3c0f1e8ba53ffef2d1a399e07c19f1acd970e1c1fe0a4e2",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "candidate_utc": "2026-04-14T15:30:05.012815Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0001",
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-14.parquet",
      "source_sha256": "5bd866e1fc74b8d2f3c0f1e8ba53ffef2d1a399e07c19f1acd970e1c1fe0a4e2",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "candidate_utc": "2026-04-15T00:30:05.011237Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0002",
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-15.parquet",
      "source_sha256": "183795c2900e538726a1ea2fbad4146cd200591dbc572bf3f9853df6e456e66d",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
      "candidate_utc": "2026-04-15T13:15:57.164919Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0002",
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-15.parquet",
      "source_sha256": "183795c2900e538726a1ea2fbad4146cd200591dbc572bf3f9853df6e456e66d",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "candidate_utc": "2026-04-16T00:16:00.503237Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0003",
      "source_date": "2026-04-16",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-16.parquet",
      "source_sha256": "19152faa2713eff446d6ced13694c1ba206e6035496480237b4dbf2708f727f7",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
      "candidate_utc": "2026-04-22T08:00:05.028587Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0004",
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-22.parquet",
      "source_sha256": "69080040b37c652eefec2ffded50239c0cb608225eab23029d23f94b3fc2b379",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
      "candidate_utc": "2026-04-23T07:16:14.138817Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0005",
      "source_date": "2026-04-23",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-23.parquet",
      "source_sha256": "8fb92e5674382c0265062249b073b7e36805a53a9fc07bedd4d6ee83c0d9784a",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
      "candidate_utc": "2026-04-14T07:30:05.011677Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0006",
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-14.parquet",
      "source_sha256": "0f917392030134ca9fa443abdec1207e5d80542b5e0b9d6b3a3ba59aa191e412",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
      "candidate_utc": "2026-04-14T14:00:57.743957Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0006",
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-14.parquet",
      "source_sha256": "0f917392030134ca9fa443abdec1207e5d80542b5e0b9d6b3a3ba59aa191e412",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
      "candidate_utc": "2026-04-15T07:30:05.010905Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0007",
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-15.parquet",
      "source_sha256": "7b4df6cc830b0f94d1c80c32782a19d176d96c2a5f9a2b4d280899746e8d8dfb",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
      "candidate_utc": "2026-04-15T13:16:01.327115Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0007",
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-15.parquet",
      "source_sha256": "7b4df6cc830b0f94d1c80c32782a19d176d96c2a5f9a2b4d280899746e8d8dfb",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "candidate_utc": "2026-04-17T08:00:59.541491Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0008",
      "source_date": "2026-04-17",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-17.parquet",
      "source_sha256": "a0dbedf4f42333595f614b9eacaabf1d24b0f1d55c790d971fc50adcfc3d8d12",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "candidate_utc": "2026-04-17T14:15:05.012317Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0008",
      "source_date": "2026-04-17",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-17.parquet",
      "source_sha256": "a0dbedf4f42333595f614b9eacaabf1d24b0f1d55c790d971fc50adcfc3d8d12",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "candidate_utc": "2026-04-20T07:45:05.020140Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0009",
      "source_date": "2026-04-20",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-20.parquet",
      "source_sha256": "2dcf9ea0d4d33f5f09a7bd8427251fc9f5282fbca52861bb9a808be1c4328f8a",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "candidate_utc": "2026-04-20T15:31:14.730975Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0009",
      "source_date": "2026-04-20",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-20.parquet",
      "source_sha256": "2dcf9ea0d4d33f5f09a7bd8427251fc9f5282fbca52861bb9a808be1c4328f8a",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "candidate_utc": "2026-04-21T11:30:05.011826Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0010",
      "source_date": "2026-04-21",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-21.parquet",
      "source_sha256": "b3b9349ae45bbf63669ab6957f08608b41dbc5e79901586a4f2635439cdd3822",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
      "candidate_utc": "2026-04-22T07:16:12.155934Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0011",
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-22.parquet",
      "source_sha256": "c28e753536fd2ef40fec68ec70f8024176985ab34b4202dd962059df81f696d2",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
      "candidate_utc": "2026-04-14T08:16:00.983581Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0012",
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-14.parquet",
      "source_sha256": "89231640fafef98b7e6e01a8c7e76413986b4874b5de8d64bdf0b553f7941588",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "US30_cash",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
      "candidate_utc": "2026-04-16T13:45:56.810509Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0013",
      "source_date": "2026-04-16",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-16.parquet",
      "source_sha256": "205c20d976f85a2031cfcd62db900295d2a665f021c48cdb9c8c140761d70c39",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "US30_cash",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
      "candidate_utc": "2026-04-15T02:45:05.009485Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0014",
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-15.parquet",
      "source_sha256": "bf6196c9332e94adf576becb743e77848844b59ebf4ba1126029232224df8e30",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
      "candidate_utc": "2026-04-15T13:15:57.398922Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0014",
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-15.parquet",
      "source_sha256": "bf6196c9332e94adf576becb743e77848844b59ebf4ba1126029232224df8e30",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
      "candidate_utc": "2026-04-16T15:00:05.011292Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0015",
      "source_date": "2026-04-16",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-16.parquet",
      "source_sha256": "3dcadb200e61a1f486303a49716eccb3446f91503e27e42cf681ad62853b407d",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
      "candidate_utc": "2026-04-21T13:45:05.018194Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0016",
      "source_date": "2026-04-21",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-21.parquet",
      "source_sha256": "98493eaa5b2ef1f1d5b15c1296770b7c2979f48ac44896764d0ea4fbc9eabb9e",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
      "candidate_utc": "2026-04-22T00:30:05.018068Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0017",
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-22.parquet",
      "source_sha256": "a5a839f79272c505c3fc87f2a10ff08d48e82f5d6519dea4cc9efb2ec119508d",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
      "candidate_utc": "2026-04-22T15:15:05.016051Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0017",
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-22.parquet",
      "source_sha256": "a5a839f79272c505c3fc87f2a10ff08d48e82f5d6519dea4cc9efb2ec119508d",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
      "candidate_utc": "2026-04-23T08:45:05.012266Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0018",
      "source_date": "2026-04-23",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-23.parquet",
      "source_sha256": "4c1b7ee014d33eb4d6a5f886b68e44224080fa433bf278be1e7b2d9852e67010",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
      "candidate_utc": "2026-04-24T00:16:10.771453Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0019",
      "source_date": "2026-04-24",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-24.parquet",
      "source_sha256": "96ee076771334c44ea29560d2ddd2cb02563750147be045b58b96d71ae827479",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERED_SOURCE_HASHED_STILL_SOURCE_STATE_BLOCKED"
    },
    {
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "candidate_utc": "2026-04-15T14:15:05.007998Z",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "coverage_status": "not_covered",
      "market_data_recovery_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "owner_request_id": "OWNER-TICK-0020",
      "source_date": "2026-04-15",
      "source_path": null,
      "source_sha256": null,
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "XAUUSD",
      "terminal_status": "OWNER_EXPORT_REQUIRED_AFTER_RECOVERY_LADDER"
    },
    {
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "candidate_utc": "2026-04-16T09:30:05.013547Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "not_covered",
      "market_data_recovery_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "owner_request_id": "OWNER-TICK-0021",
      "source_date": "2026-04-16",
      "source_path": null,
      "source_sha256": null,
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "XAUUSD",
      "terminal_status": "OWNER_EXPORT_REQUIRED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "candidate_utc": "2026-04-16T13:16:01.126537Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "not_covered",
      "market_data_recovery_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "owner_request_id": "OWNER-TICK-0021",
      "source_date": "2026-04-16",
      "source_path": null,
      "source_sha256": null,
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "XAUUSD",
      "terminal_status": "OWNER_EXPORT_REQUIRED_CONTAMINATION_EXCLUDED"
    },
    {
      "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
      "candidate_utc": "2026-04-17T13:30:05.007149Z",
      "clean_packet_use_status": "excluded_until_independent_clean_source_proof",
      "contamination_or_embargo_blocked": true,
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "market_data_recovery_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "owner_request_id": "OWNER-TICK-0022",
      "source_date": "2026-04-17",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/XAUUSD/2026-04-17.parquet",
      "source_sha256": "8c5ffc921bb811f78bdd16e43553d7a7650a6b1c862a70f18d23eebc42f9b0db",
      "source_state_boundary": "ticks_do_not_admit_candidate_without_pending_lifecycle_write_clock_order_observability_truth",
      "symbol": "XAUUSD",
      "terminal_status": "RECOVERED_SOURCE_HASHED_CONTAMINATION_EXCLUDED"
    }
  ],
  "changes_live_trading_behavior": false,
  "contamination_embargo_excluded_row_count": 12,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:46:57Z",
  "grouped_request_count": 22,
  "grouped_rows": [
    {
      "candidate_ids": [
        "GBPJPY_2026-04-14T01:15:05.006410+00:00",
        "GBPJPY_2026-04-14T15:30:05.012815+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-14T23:59:58.740000Z",
      "min_timestamp_utc": "2026-04-14T00:00:02.941000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0001",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 222024,
      "size_bytes": 3691827,
      "source_date": "2026-04-14",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-14.parquet",
      "source_sha256": "5bd866e1fc74b8d2f3c0f1e8ba53ffef2d1a399e07c19f1acd970e1c1fe0a4e2",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
            "candidate_utc": "2026-04-14T01:15:05.006410Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
            "candidate_utc": "2026-04-14T15:30:05.012815Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 2.941,
        "last_tick_before_window_end_seconds": 1.259999,
        "row_count_inside_requested_utc_window": 222024
      },
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-15T00:30:05.011237+00:00",
        "GBPJPY_2026-04-15T13:15:57.164919+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-15T23:59:58.060000Z",
      "min_timestamp_utc": "2026-04-15T00:00:03.841000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0002",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 239538,
      "size_bytes": 3923919,
      "source_date": "2026-04-15",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-15.parquet",
      "source_sha256": "183795c2900e538726a1ea2fbad4146cd200591dbc572bf3f9853df6e456e66d",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
            "candidate_utc": "2026-04-15T00:30:05.011237Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
            "candidate_utc": "2026-04-15T13:15:57.164919Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 3.841,
        "last_tick_before_window_end_seconds": 1.939999,
        "row_count_inside_requested_utc_window": 239538
      },
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-16T00:16:00.503237+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-16T23:59:58.496000Z",
      "min_timestamp_utc": "2026-04-16T00:00:01.347000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0003",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 236959,
      "size_bytes": 3851820,
      "source_date": "2026-04-16",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-16.parquet",
      "source_sha256": "19152faa2713eff446d6ced13694c1ba206e6035496480237b4dbf2708f727f7",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
            "candidate_utc": "2026-04-16T00:16:00.503237Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 1.347,
        "last_tick_before_window_end_seconds": 1.503999,
        "row_count_inside_requested_utc_window": 236959
      },
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-22T08:00:05.028587+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-22T23:59:58.514000Z",
      "min_timestamp_utc": "2026-04-22T00:00:09.411000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0004",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 250615,
      "size_bytes": 4019231,
      "source_date": "2026-04-22",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-22.parquet",
      "source_sha256": "69080040b37c652eefec2ffded50239c0cb608225eab23029d23f94b3fc2b379",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
            "candidate_utc": "2026-04-22T08:00:05.028587Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 9.411,
        "last_tick_before_window_end_seconds": 1.485999,
        "row_count_inside_requested_utc_window": 250615
      },
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-23T07:16:14.138817+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-23T23:59:58.735000Z",
      "min_timestamp_utc": "2026-04-23T00:00:04.798000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0005",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 305039,
      "size_bytes": 4684456,
      "source_date": "2026-04-23",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-23.parquet",
      "source_sha256": "8fb92e5674382c0265062249b073b7e36805a53a9fc07bedd4d6ee83c0d9784a",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
            "candidate_utc": "2026-04-23T07:16:14.138817Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 4.798,
        "last_tick_before_window_end_seconds": 1.264999,
        "row_count_inside_requested_utc_window": 305039
      },
      "window_end_utc": "2026-04-23T23:59:59.999999Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-14T07:30:05.011677+00:00",
        "GBPUSD_2026-04-14T14:00:57.743957+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-14T23:59:58.289000Z",
      "min_timestamp_utc": "2026-04-14T00:00:02.878000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0006",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 140383,
      "size_bytes": 2566997,
      "source_date": "2026-04-14",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-14.parquet",
      "source_sha256": "0f917392030134ca9fa443abdec1207e5d80542b5e0b9d6b3a3ba59aa191e412",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
            "candidate_utc": "2026-04-14T07:30:05.011677Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
            "candidate_utc": "2026-04-14T14:00:57.743957Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 2.878,
        "last_tick_before_window_end_seconds": 1.710999,
        "row_count_inside_requested_utc_window": 140383
      },
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-15T07:30:05.010905+00:00",
        "GBPUSD_2026-04-15T13:16:01.327115+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-15T23:59:57.944000Z",
      "min_timestamp_utc": "2026-04-15T00:00:03.761000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0007",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 152421,
      "size_bytes": 2722667,
      "source_date": "2026-04-15",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-15.parquet",
      "source_sha256": "7b4df6cc830b0f94d1c80c32782a19d176d96c2a5f9a2b4d280899746e8d8dfb",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
            "candidate_utc": "2026-04-15T07:30:05.010905Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
            "candidate_utc": "2026-04-15T13:16:01.327115Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 3.761,
        "last_tick_before_window_end_seconds": 2.055999,
        "row_count_inside_requested_utc_window": 152421
      },
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-17T08:00:59.541491+00:00",
        "GBPUSD_2026-04-17T14:15:05.012317+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-17T23:59:41.473000Z",
      "min_timestamp_utc": "2026-04-17T00:00:09.834000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0008",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 178942,
      "size_bytes": 3049533,
      "source_date": "2026-04-17",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-17.parquet",
      "source_sha256": "a0dbedf4f42333595f614b9eacaabf1d24b0f1d55c790d971fc50adcfc3d8d12",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
            "candidate_utc": "2026-04-17T08:00:59.541491Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
            "candidate_utc": "2026-04-17T14:15:05.012317Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 9.834,
        "last_tick_before_window_end_seconds": 18.526999,
        "row_count_inside_requested_utc_window": 178942
      },
      "window_end_utc": "2026-04-17T23:59:59.999999Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-20T07:45:05.020140+00:00",
        "GBPUSD_2026-04-20T15:31:14.730975+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-20T23:59:58.559000Z",
      "min_timestamp_utc": "2026-04-20T00:00:07.487000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0009",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 179015,
      "size_bytes": 3059435,
      "source_date": "2026-04-20",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-20.parquet",
      "source_sha256": "2dcf9ea0d4d33f5f09a7bd8427251fc9f5282fbca52861bb9a808be1c4328f8a",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
            "candidate_utc": "2026-04-20T07:45:05.020140Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
            "candidate_utc": "2026-04-20T15:31:14.730975Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 7.487,
        "last_tick_before_window_end_seconds": 1.440999,
        "row_count_inside_requested_utc_window": 179015
      },
      "window_end_utc": "2026-04-20T23:59:59.999999Z",
      "window_start_utc": "2026-04-20T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-21T11:30:05.011826+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-21T23:59:58.549000Z",
      "min_timestamp_utc": "2026-04-21T00:00:06.807000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0010",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 184174,
      "size_bytes": 3104581,
      "source_date": "2026-04-21",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-21.parquet",
      "source_sha256": "b3b9349ae45bbf63669ab6957f08608b41dbc5e79901586a4f2635439cdd3822",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
            "candidate_utc": "2026-04-21T11:30:05.011826Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 6.807,
        "last_tick_before_window_end_seconds": 1.450999,
        "row_count_inside_requested_utc_window": 184174
      },
      "window_end_utc": "2026-04-21T23:59:59.999999Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-22T07:16:12.155934+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-22T23:59:58.269000Z",
      "min_timestamp_utc": "2026-04-22T00:00:09.344000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0011",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 163415,
      "size_bytes": 2869040,
      "source_date": "2026-04-22",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-22.parquet",
      "source_sha256": "c28e753536fd2ef40fec68ec70f8024176985ab34b4202dd962059df81f696d2",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
            "candidate_utc": "2026-04-22T07:16:12.155934Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 9.344,
        "last_tick_before_window_end_seconds": 1.730999,
        "row_count_inside_requested_utc_window": 163415
      },
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "candidate_ids": [
        "US30_cash_2026-04-14T08:16:00.983581+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-14T23:57:49.824000Z",
      "min_timestamp_utc": "2026-04-14T01:01:00.262000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0012",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 189608,
      "size_bytes": 3363965,
      "source_date": "2026-04-14",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-14.parquet",
      "source_sha256": "89231640fafef98b7e6e01a8c7e76413986b4874b5de8d64bdf0b553f7941588",
      "source_symbol": "US30_or_US30_cash_broker_alias",
      "symbol": "US30_cash",
      "symbol_compatibility": {
        "basis": "existing repo MT5 research export mapping uses US30_cash:US30",
        "broker_symbol": "US30",
        "requested_symbol": "US30_cash",
        "status": "compatible_broker_alias_for_market_data_only"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
            "candidate_utc": "2026-04-14T08:16:00.983581Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 3660.262,
        "last_tick_before_window_end_seconds": 130.175999,
        "row_count_inside_requested_utc_window": 189608
      },
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_ids": [
        "US30_cash_2026-04-16T13:45:56.810509+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-16T23:57:54.481000Z",
      "min_timestamp_utc": "2026-04-16T01:01:00.265000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0013",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 181824,
      "size_bytes": 3227975,
      "source_date": "2026-04-16",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-16.parquet",
      "source_sha256": "205c20d976f85a2031cfcd62db900295d2a665f021c48cdb9c8c140761d70c39",
      "source_symbol": "US30_or_US30_cash_broker_alias",
      "symbol": "US30_cash",
      "symbol_compatibility": {
        "basis": "existing repo MT5 research export mapping uses US30_cash:US30",
        "broker_symbol": "US30",
        "requested_symbol": "US30_cash",
        "status": "compatible_broker_alias_for_market_data_only"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
            "candidate_utc": "2026-04-16T13:45:56.810509Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 3660.265,
        "last_tick_before_window_end_seconds": 125.518999,
        "row_count_inside_requested_utc_window": 181824
      },
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-15T02:45:05.009485+00:00",
        "USDJPY_2026-04-15T13:15:57.398922+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-15T23:59:58.041000Z",
      "min_timestamp_utc": "2026-04-15T00:00:03.797000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0014",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 117046,
      "size_bytes": 2243297,
      "source_date": "2026-04-15",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-15.parquet",
      "source_sha256": "bf6196c9332e94adf576becb743e77848844b59ebf4ba1126029232224df8e30",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
            "candidate_utc": "2026-04-15T02:45:05.009485Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
            "candidate_utc": "2026-04-15T13:15:57.398922Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 3.797,
        "last_tick_before_window_end_seconds": 1.958999,
        "row_count_inside_requested_utc_window": 117046
      },
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-16T15:00:05.011292+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-16T23:59:57.446000Z",
      "min_timestamp_utc": "2026-04-16T00:00:01.335000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0015",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 114833,
      "size_bytes": 2203620,
      "source_date": "2026-04-16",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-16.parquet",
      "source_sha256": "3dcadb200e61a1f486303a49716eccb3446f91503e27e42cf681ad62853b407d",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
            "candidate_utc": "2026-04-16T15:00:05.011292Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 1.335,
        "last_tick_before_window_end_seconds": 2.553999,
        "row_count_inside_requested_utc_window": 114833
      },
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-21T13:45:05.018194+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-21T23:59:57.778000Z",
      "min_timestamp_utc": "2026-04-21T00:00:07.055000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0016",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 126514,
      "size_bytes": 2367705,
      "source_date": "2026-04-21",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-21.parquet",
      "source_sha256": "98493eaa5b2ef1f1d5b15c1296770b7c2979f48ac44896764d0ea4fbc9eabb9e",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
            "candidate_utc": "2026-04-21T13:45:05.018194Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 7.055,
        "last_tick_before_window_end_seconds": 2.221999,
        "row_count_inside_requested_utc_window": 126514
      },
      "window_end_utc": "2026-04-21T23:59:59.999999Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-22T00:30:05.018068+00:00",
        "USDJPY_2026-04-22T15:15:05.016051+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-22T23:59:58.465000Z",
      "min_timestamp_utc": "2026-04-22T00:00:09.373000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0017",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 115085,
      "size_bytes": 2175673,
      "source_date": "2026-04-22",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-22.parquet",
      "source_sha256": "a5a839f79272c505c3fc87f2a10ff08d48e82f5d6519dea4cc9efb2ec119508d",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
            "candidate_utc": "2026-04-22T00:30:05.018068Z",
            "inside_source_span": true
          },
          {
            "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
            "candidate_utc": "2026-04-22T15:15:05.016051Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 9.373,
        "last_tick_before_window_end_seconds": 1.534999,
        "row_count_inside_requested_utc_window": 115085
      },
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-23T08:45:05.012266+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-23T23:59:58.374000Z",
      "min_timestamp_utc": "2026-04-23T00:00:04.775000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0018",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 150006,
      "size_bytes": 2711362,
      "source_date": "2026-04-23",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-23.parquet",
      "source_sha256": "4c1b7ee014d33eb4d6a5f886b68e44224080fa433bf278be1e7b2d9852e67010",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
            "candidate_utc": "2026-04-23T08:45:05.012266Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 4.775,
        "last_tick_before_window_end_seconds": 1.625999,
        "row_count_inside_requested_utc_window": 150006
      },
      "window_end_utc": "2026-04-23T23:59:59.999999Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-24T00:16:10.771453+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-24T23:59:43.751000Z",
      "min_timestamp_utc": "2026-04-24T00:00:06.045000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0019",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 125100,
      "size_bytes": 2345690,
      "source_date": "2026-04-24",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-24.parquet",
      "source_sha256": "96ee076771334c44ea29560d2ddd2cb02563750147be045b58b96d71ae827479",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
            "candidate_utc": "2026-04-24T00:16:10.771453Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 6.045,
        "last_tick_before_window_end_seconds": 16.248999,
        "row_count_inside_requested_utc_window": 125100
      },
      "window_end_utc": "2026-04-24T23:59:59.999999Z",
      "window_start_utc": "2026-04-24T00:00:00Z"
    },
    {
      "candidate_ids": [
        "XAUUSD_2026-04-15T14:15:05.007998+00:00"
      ],
      "coverage_status": "not_covered",
      "last_error": "(1, 'Success')",
      "owner_export_still_required_for_market_data": true,
      "owner_request_id": "OWNER-TICK-0020",
      "read_only_extraction_status": "NO_TICKS_EXPORTED",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "NO_TICKS_EXPORTED",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 0,
      "source_date": "2026-04-15",
      "source_path": null,
      "source_sha256": null,
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "symbol_compatibility": {
        "broker_symbol": "XAUUSD",
        "requested_symbol": "XAUUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "XAUUSD_2026-04-16T09:30:05.013547+00:00",
        "XAUUSD_2026-04-16T13:16:01.126537+00:00"
      ],
      "coverage_status": "not_covered",
      "last_error": "(1, 'Success')",
      "owner_export_still_required_for_market_data": true,
      "owner_request_id": "OWNER-TICK-0021",
      "read_only_extraction_status": "NO_TICKS_EXPORTED",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "NO_TICKS_EXPORTED",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 0,
      "source_date": "2026-04-16",
      "source_path": null,
      "source_sha256": null,
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "symbol_compatibility": {
        "broker_symbol": "XAUUSD",
        "requested_symbol": "XAUUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "XAUUSD_2026-04-17T13:30:05.007149+00:00"
      ],
      "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
      "field_availability": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "max_timestamp_utc": "2026-04-17T23:59:58.919000Z",
      "min_timestamp_utc": "2026-04-17T01:00:00.749000Z",
      "owner_export_still_required_for_market_data": false,
      "owner_request_id": "OWNER-TICK-0022",
      "recovery_ladder_steps": [
        {
          "status": "not_recovered_in_catalog_search",
          "step": "accepted_active_catalog"
        },
        {
          "status": "no_pre_existing_tick_file_match",
          "step": "targeted_current_absolute_prior_owner_documents_search"
        },
        {
          "status": "not_applicable_to_mt5_bid_ask_tick_schema",
          "step": "sierra_vendor_cache"
        },
        {
          "status": "EXPORTED_MARKET_DATA_ONLY_TICKS",
          "step": "read_only_mt5_market_data_extraction"
        }
      ],
      "row_count": 602353,
      "size_bytes": 8603256,
      "source_date": "2026-04-17",
      "source_file_sha256_field_status": "recorded_in_source_hash_manifest",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/XAUUSD/2026-04-17.parquet",
      "source_sha256": "8c5ffc921bb811f78bdd16e43553d7a7650a6b1c862a70f18d23eebc42f9b0db",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "symbol_compatibility": {
        "broker_symbol": "XAUUSD",
        "requested_symbol": "XAUUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage": {
        "candidate_times_inside_source_span": [
          {
            "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
            "candidate_utc": "2026-04-17T13:30:05.007149Z",
            "inside_source_span": true
          }
        ],
        "coverage_status": "partial_day_span_covers_all_candidate_timestamps",
        "first_tick_after_window_start_seconds": 3600.749,
        "last_tick_before_window_end_seconds": 1.080999,
        "row_count_inside_requested_utc_window": 602353
      },
      "window_end_utc": "2026-04-17T23:59:59.999999Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
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
  "recovered_candidate_row_count": 28,
  "recovered_grouped_request_count": 20,
  "remaining_candidate_row_count": 3,
  "remaining_owner_export_request_count": 2,
  "route_id": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
  "schema_version": "nofill_readonly_tick_recovery_export_source_control_route_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS",
  "tick_export_dependent_blocker_count": 31,
  "validation_safe": false
}
```
