# NOFILL Forward No-Leak Field Policy 2026-05-09

- route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- schema_version: `nofill_cat_v3_forward_lifecycle_capture_contract_v1`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Allowed Source Classes

- `decision_time_candidate_safe_projection`
- `pending_limit_lifecycle_source_safe_projection`
- `candidate_path_follow_source_projection`
- `candidate_ltf_path_order_source_projection`
- `tick_parquet_readonly_manifest`
- `lower_tf_ohlc_readonly_manifest`
- `source_control_rebuild_artifact`
- `source_contract_artifact`
- `parser_hash_manifest`

## Forbidden Substitutes

These names may appear in this document only as forbidden terms. They must not appear as accepted schema field names or source values:

- `account_history`
- `actual_r`
- `broker_actual_r`
- `broker_fill_state`
- `databento_payload`
- `expectancy`
- `live_order_state`
- `mt5_deal_id`
- `mt5_order_ticket`
- `order_send_attempted`
- `order_send_success`
- `paid_api_result`
- `r_multiple`
- `r_value`
- `synthetic_path_r`
- `win_rate`

## Closed Labels

`future_result_label_status` must stay `NOT_OPENED`. `broker_actual_r_status`, `hidden_path_label_status`, and `live_account_order_label_status` must stay `FORBIDDEN`. The route fails if any artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.

## Raw Log Handling

Existing logs can contain useful source evidence and forbidden execution-shaped fields in the same row. Any future builder must use an allowlist projection. Raw `pending_limit_lifecycle`, `candidate_ltf_path_order`, or `strategy_follow_candidates` rows are not contract-safe inputs by themselves.
