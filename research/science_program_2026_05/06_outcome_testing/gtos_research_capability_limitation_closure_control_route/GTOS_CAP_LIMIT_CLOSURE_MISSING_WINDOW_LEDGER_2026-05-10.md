# GTOS Capability Limitation Missing Window Ledger

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "missing_window_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_next_action_rule": "Each missing market-data window routes to approved acquisition or owner export; each missing historical GTOS state routes to source-safe logs or forward capture requirement.",
  "generated_at_utc": "2026-05-10T06:33:15Z",
  "live_effect": false,
  "market_data_missing_windows": [
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPJPY 2026-04-14 through approved read-only market-data route.",
      "source_date": "2026-04-14",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPJPY 2026-04-15 through approved read-only market-data route.",
      "source_date": "2026-04-15",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPJPY 2026-04-16 through approved read-only market-data route.",
      "source_date": "2026-04-16",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPJPY 2026-04-22 through approved read-only market-data route.",
      "source_date": "2026-04-22",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPJPY 2026-04-23 through approved read-only market-data route.",
      "source_date": "2026-04-23",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPUSD 2026-04-14 through approved read-only market-data route.",
      "source_date": "2026-04-14",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPUSD 2026-04-15 through approved read-only market-data route.",
      "source_date": "2026-04-15",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPUSD 2026-04-17 through approved read-only market-data route.",
      "source_date": "2026-04-17",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPUSD 2026-04-20 through approved read-only market-data route.",
      "source_date": "2026-04-20",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPUSD 2026-04-21 through approved read-only market-data route.",
      "source_date": "2026-04-21",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for GBPUSD 2026-04-22 through approved read-only market-data route.",
      "source_date": "2026-04-22",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for US30_cash 2026-04-14 through approved read-only market-data route.",
      "source_date": "2026-04-14",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "US30_cash"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for US30_cash 2026-04-16 through approved read-only market-data route.",
      "source_date": "2026-04-16",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "US30_cash"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for USDJPY 2026-04-15 through approved read-only market-data route.",
      "source_date": "2026-04-15",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for USDJPY 2026-04-16 through approved read-only market-data route.",
      "source_date": "2026-04-16",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for USDJPY 2026-04-21 through approved read-only market-data route.",
      "source_date": "2026-04-21",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for USDJPY 2026-04-22 through approved read-only market-data route.",
      "source_date": "2026-04-22",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for USDJPY 2026-04-23 through approved read-only market-data route.",
      "source_date": "2026-04-23",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for USDJPY 2026-04-24 through approved read-only market-data route.",
      "source_date": "2026-04-24",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "USDJPY"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for XAUUSD 2026-04-15 through approved read-only market-data route.",
      "source_date": "2026-04-15",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for XAUUSD 2026-04-16 through approved read-only market-data route.",
      "source_date": "2026-04-16",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD"
    },
    {
      "blocker_class": "recoverable_market_data_absence",
      "exact_source_requirement": "Obtain or export local tick parquet for XAUUSD 2026-04-17 through approved read-only market-data route.",
      "source_date": "2026-04-17",
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "XAUUSD"
    }
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
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "source_state_missing_examples": [
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-14",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-14",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-15",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-15",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-16",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-22",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-23",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPJPY_2026-04-28T09:00:05.010558+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-28",
      "symbol": "GBPJPY"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-14",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-14",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-15",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-15",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-17",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-17",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-20",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-20",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-21",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-22",
      "symbol": "GBPUSD"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "NAS100_2026-04-29T15:00:05.012307+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-04-29",
      "symbol": "NAS100"
    },
    {
      "blocker_class": "non_generatable_historical_source_state_absence",
      "candidate_id": "NAS100_2026-05-01T08:15:00+00:00",
      "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "source_date": "2026-05-01",
      "symbol": "NAS100"
    }
  ],
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
