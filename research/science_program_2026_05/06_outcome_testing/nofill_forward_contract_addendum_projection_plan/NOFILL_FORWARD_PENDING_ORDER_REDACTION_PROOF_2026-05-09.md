# NOFILL Forward Pending Order Redaction Proof 2026-05-09

- route_id: `NOFILL_FORWARD_CONTRACT_ADDENDUM_PROJECTION_PLAN`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Proof

The dry-run fixture intentionally includes raw ticket/order/fill/result-shaped fields: `mt5_order_ticket`, `pending_ticket`, `trade_state_ticket`, `order_send_attempted`, `order_send_success`, `broker_fill_state`, `fill_time_utc`, `slippage_price`, `actual_r`, and `synthetic_path_r`.

The source-safe projection emits only addendum status fields. It does not emit raw ticket values, ticket hashes, order-send booleans, fill state, account/order-history fields, slippage value, actual R, synthetic R, win-rate, or expectancy.

Projection leak issues: `[]`.

## Projected Status Output

- `broker_pending_order_created_status`: `NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED`
- `capture_clock_skew_ms`: `None`
- `capture_clock_skew_status`: `CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY`
- `capture_clock_source_status`: `SYSTEM_UTC_SOURCE`
- `capture_latency_ms`: `None`
- `capture_observed_at_utc`: `2026-05-09T10:00:00+00:00`
- `capture_timestamp_derivation_rule`: `DERIVED_FROM_SOURCE_CREATED_AT`
- `capture_write_completed_at_utc`: `None`
- `capture_write_started_at_utc`: `None`
- `cost_testing_gate_status`: `COST_TESTING_NOT_OPENED`
- `decision_spread_status`: `CAPTURED_SOURCE_SAFE`
- `decision_spread_unit`: `SOURCE_NATIVE`
- `decision_spread_value_source_safe`: `16.0`
- `entry_touch_spread_status`: `SOURCE_FIELD_MISSING`
- `entry_touch_spread_value_source_safe`: `None`
- `execution_quality_label_status`: `NOT_OPENED_FOR_SOURCE_CONTROL`
- `execution_quality_value_redaction_status`: `RAW_EXECUTION_FIELD_PRESENT_REDACTED`
- `mt5_order_ticket_redaction_status`: `SOURCE_TICKET_VALUE_REDACTED`
- `native_pending_order_type_source_safe`: `BUY_LIMIT`
- `native_pending_order_type_status`: `CAPTURED_SOURCE_SAFE`
- `pending_order_mode_source_safe`: `INTERNAL_CANDLE_POLLED_INTENT`
- `pending_order_mode_status`: `CAPTURED_DIRECT`
- `raw_ticket_field_present_status`: `RAW_TICKET_VALUE_PRESENT_REDACTED`
- `slippage_label_status`: `NOT_OPENED_FOR_SOURCE_CONTROL`
- `slippage_value_redaction_status`: `RAW_SLIPPAGE_VALUE_PRESENT_REDACTED`
- `spread_source_hash`: `f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49`

## Required Verifier Behavior

- Fail if any output key equals a forbidden raw field name.
- Fail if any raw ticket value appears in output keys or values.
- Fail if `slippage_label_status` or `execution_quality_label_status` differs from `NOT_OPENED_FOR_SOURCE_CONTROL`.
- Fail if `validation_safe`, `outcome_review_opened`, or `live_effect` is true.
