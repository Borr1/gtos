# Acquisition Manifest Example

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "acquisition_request_manifest_example",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "live_effect": false,
  "market_data_request_count": 22,
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
  "request_count": 42,
  "requests": [
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPJPY 2026-04-14 through approved read-only market-data route.",
      "request_id": "ACQ-0001",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPJPY 2026-04-15 through approved read-only market-data route.",
      "request_id": "ACQ-0002",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPJPY 2026-04-16 through approved read-only market-data route.",
      "request_id": "ACQ-0003",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-16T23:59:59Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPJPY 2026-04-22 through approved read-only market-data route.",
      "request_id": "ACQ-0004",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-22T23:59:59Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPJPY 2026-04-23 through approved read-only market-data route.",
      "request_id": "ACQ-0005",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-23T23:59:59Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPUSD 2026-04-14 through approved read-only market-data route.",
      "request_id": "ACQ-0006",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPUSD 2026-04-15 through approved read-only market-data route.",
      "request_id": "ACQ-0007",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPUSD 2026-04-17 through approved read-only market-data route.",
      "request_id": "ACQ-0008",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-17T23:59:59Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPUSD 2026-04-20 through approved read-only market-data route.",
      "request_id": "ACQ-0009",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-20T23:59:59Z",
      "window_start_utc": "2026-04-20T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPUSD 2026-04-21 through approved read-only market-data route.",
      "request_id": "ACQ-0010",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-21T23:59:59Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for GBPUSD 2026-04-22 through approved read-only market-data route.",
      "request_id": "ACQ-0011",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "GBPUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-22T23:59:59Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for US30_cash 2026-04-14 through approved read-only market-data route.",
      "request_id": "ACQ-0012",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "US30_cash",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for US30_cash 2026-04-16 through approved read-only market-data route.",
      "request_id": "ACQ-0013",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "US30_cash",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-16T23:59:59Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for USDJPY 2026-04-15 through approved read-only market-data route.",
      "request_id": "ACQ-0014",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "USDJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for USDJPY 2026-04-16 through approved read-only market-data route.",
      "request_id": "ACQ-0015",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "USDJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-16T23:59:59Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for USDJPY 2026-04-21 through approved read-only market-data route.",
      "request_id": "ACQ-0016",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "USDJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-21T23:59:59Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for USDJPY 2026-04-22 through approved read-only market-data route.",
      "request_id": "ACQ-0017",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "USDJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-22T23:59:59Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for USDJPY 2026-04-23 through approved read-only market-data route.",
      "request_id": "ACQ-0018",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "USDJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-23T23:59:59Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for USDJPY 2026-04-24 through approved read-only market-data route.",
      "request_id": "ACQ-0019",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "USDJPY",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-24T23:59:59Z",
      "window_start_utc": "2026-04-24T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for XAUUSD 2026-04-15 through approved read-only market-data route.",
      "request_id": "ACQ-0020",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "XAUUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for XAUUSD 2026-04-16 through approved read-only market-data route.",
      "request_id": "ACQ-0021",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "XAUUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-16T23:59:59Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "approval_required": true,
      "approved_route": "read_only_market_data_export_or_owner_export_manifest",
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "hash_policy": "sha256_after_export_before_use",
      "no_leak_constraints": [
        "no_account_order_deal_history_position_values",
        "no_broker_actual_r",
        "no_result_scoring"
      ],
      "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
      "owner_action_required": "Obtain or export local tick parquet for XAUUSD 2026-04-17 through approved read-only market-data route.",
      "request_id": "ACQ-0022",
      "requested_fields": [
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "source_requirement_type": "recoverable_market_data",
      "symbol": "XAUUSD",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-17T23:59:59Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0023",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0024",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0025",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0026",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0027",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-16T23:59:59Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0028",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-22T23:59:59Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0029",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-23T23:59:59Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0030",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPJPY",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-28T23:59:59Z",
      "window_start_utc": "2026-04-28T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0031",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0032",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-14T23:59:59Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0033",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0034",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-15T23:59:59Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0035",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-17T23:59:59Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0036",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-17T23:59:59Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0037",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-20T23:59:59Z",
      "window_start_utc": "2026-04-20T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0038",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-20T23:59:59Z",
      "window_start_utc": "2026-04-20T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0039",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-21T23:59:59Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0040",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "GBPUSD",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-22T23:59:59Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0041",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "NAS100",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-04-29T23:59:59Z",
      "window_start_utc": "2026-04-29T00:00:00Z"
    },
    {
      "approval_required": false,
      "approved_route": "prospective_forward_capture_requirement",
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "cost_cap_usd": 0,
      "execution_status": "not_executed_manifest_only",
      "forbidden_fields": [
        "broker_actual_r",
        "account_history_deal_link",
        "native_order_ticket"
      ],
      "hash_policy": "source_hash_required_after_future_capture",
      "no_leak_constraints": [
        "do_not_infer_historical_source_state_from_price",
        "do_not_convert_projection_to_historical_truth"
      ],
      "output_path": "future_forward_capture_contract_not_historical_backfill",
      "owner_action_required": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
      "request_id": "ACQ-0042",
      "requested_fields": [
        "pending_intent_id",
        "lifecycle_group_id",
        "write_clock_utc",
        "source_lane",
        "final_lifecycle_state"
      ],
      "source_requirement_type": "non_generatable_historical_gtos_source_state",
      "symbol": "NAS100",
      "timeframe": "not_applicable",
      "window_end_utc": "2026-05-01T23:59:59Z",
      "window_start_utc": "2026-05-01T00:00:00Z"
    }
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "source_state_capture_requirement_count": 20,
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
