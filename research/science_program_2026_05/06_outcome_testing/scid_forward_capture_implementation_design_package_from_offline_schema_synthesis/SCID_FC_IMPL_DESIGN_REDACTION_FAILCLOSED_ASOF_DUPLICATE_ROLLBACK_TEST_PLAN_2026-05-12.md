# Redaction Failclosed Asof Duplicate Rollback Test Plan

Route: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS`
Evidence class: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`

```json
{
  "artifact_type": "redaction_failclosed_asof_duplicate_rollback_test_plan",
  "fail_closed_triggers": [
    "missing required group field",
    "invalid enum",
    "stale or post-decision as-of timestamp",
    "source hash absent for required source-backed fields",
    "forbidden broker/account/order/deal/position/ticket identifier",
    "forbidden result/performance metric",
    "duplicate candidate id with changed denominator key",
    "raw orderflow/depth/blob payload"
  ],
  "forbidden_fields": [
    "account",
    "account_id",
    "login",
    "order_id",
    "deal_id",
    "position_id",
    "ticket",
    "pending_ticket",
    "mt5_order_ticket",
    "trade_state_ticket",
    "broker_fill_state",
    "actual_r",
    "synthetic_path_r",
    "slippage_price",
    "pnl",
    "win_loss",
    "expectancy",
    "target_hit",
    "stop_hit"
  ],
  "generated_at_utc": "2026-05-12T05:29:30Z",
  "rollback": [
    "Disable future SCID writer through existing forward-capture logger gate or scoped revert",
    "Restart affected orchestrators only after owner approval",
    "Do not delete historical rows; quarantine invalid schema outputs for G12 audit",
    "Run proposed rollout verifier before reopening any capture stream"
  ],
  "route_id": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "runtime_vs_parser_policy": {
    "research_parser": "fail-closed; invalid rows are not accepted as SCID source evidence",
    "runtime_writer": "fail-open for trading behavior, log/quarantine invalid SCID row"
  },
  "safe_flags": {
    "ai_api_call_opened": false,
    "broker_or_account_evidence_opened": false,
    "canary_or_selector_change_opened": false,
    "config_change_opened": false,
    "evidence_class": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
    "execution_logic_change_opened": false,
    "live_effect": false,
    "outcome_review_opened": false,
    "paid_vendor_call_opened": false,
    "performance_claim_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "prompt_change_opened": false,
    "raw_blob_capture_opened": false,
    "result_scoring_opened": false,
    "risk_logic_change_opened": false,
    "validation_safe": false
  },
  "schema_version": "scid_forward_source_capture_v1",
  "test_matrix": [
    "valid synthetic row per group",
    "missing required field per group",
    "forbidden broker identifier",
    "forbidden result/performance metric",
    "stale as-of timestamp",
    "duplicate denominator drift",
    "LTF unavailable source",
    "orderflow unavailable local/cache source"
  ]
}
```
