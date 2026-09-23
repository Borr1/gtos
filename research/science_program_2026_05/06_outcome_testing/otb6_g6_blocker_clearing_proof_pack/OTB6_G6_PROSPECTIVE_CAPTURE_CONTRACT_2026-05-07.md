# OTB6 G6 Prospective Capture Contract

Promotion verdict: `NO_PROMOTION_VERDICT`

All contracts are shadow-only and input-only. They require file hashes, row hashes, and `feature_asof_utc <= decision_asof_utc` before any label or scoring lane opens.

## OTG0-PKT-060

- Schema: `mechanical_ob_bounds_asof_v1`
- Required fields: `candidate_id`, `setup_id`, `packet_id`, `experiment_id`, `symbol`, `decision_asof_utc`, `source_capture_utc`, `source_path`, `source_sha256`, `row_hash`, `feature_asof_utc_lte_decision_asof_utc`, `duplicate_group_id`, `no_result_fields_assertion`, `market_state_source_path`, `market_state_source_sha256`, `market_state_row_hash`, `timeframe`, `ob_id`, `ob_low`, `ob_high`, `ob_mid`, `ob_created_utc`, `impulse_bos_utc`, `mitigation_state`, `touch_sequence`, `poi_price_level`, `selected_ob_reason`, `matched_control_group_id`

## OTG0-PKT-061

- Schema: `continuation_no_retrace_decision_price_path_v1`
- Required fields: `candidate_id`, `setup_id`, `packet_id`, `experiment_id`, `symbol`, `decision_asof_utc`, `source_capture_utc`, `source_path`, `source_sha256`, `row_hash`, `feature_asof_utc_lte_decision_asof_utc`, `duplicate_group_id`, `no_result_fields_assertion`, `entry_model_id`, `decision_quote_time_msc`, `decision_bid`, `decision_ask`, `decision_mid`, `spread`, `decision_price_model`, `slippage_model_id`, `ordered_path_source_id`, `path_source_type`, `path_source_path`, `path_source_sha256`, `path_first_timestamp_utc`, `path_last_timestamp_utc`, `path_row_count`, `path_start_utc`, `path_end_utc`

## OTG0-PKT-063

- Schema: `g6_changepoint_feature_v1`
- Required fields: `candidate_id`, `setup_id`, `packet_id`, `experiment_id`, `symbol`, `decision_asof_utc`, `source_capture_utc`, `source_path`, `source_sha256`, `row_hash`, `feature_asof_utc_lte_decision_asof_utc`, `duplicate_group_id`, `no_result_fields_assertion`, `changepoint_model_id`, `changepoint_model_version`, `parser_source_path`, `parser_sha256`, `threshold_freeze_id`, `input_ohlc_source_path`, `input_ohlc_source_sha256`, `window_start_utc`, `window_end_utc`, `changepoint_count`, `last_changepoint_utc`, `distance_from_last_changepoint_bars`, `changepoint_score`

## OTG0-PKT-066

- Schema: `xau_liquidity_sweep_ob_round_join_v1`
- Required fields: `candidate_id`, `setup_id`, `packet_id`, `experiment_id`, `symbol`, `decision_asof_utc`, `source_capture_utc`, `source_path`, `source_sha256`, `row_hash`, `feature_asof_utc_lte_decision_asof_utc`, `duplicate_group_id`, `no_result_fields_assertion`, `ob_zone_key`, `ob_low`, `ob_high`, `ob_mid`, `round_number_model_id`, `nearest_50_level`, `nearest_100_level`, `inside_50_band_10usd`, `inside_100_band_15usd`, `sweep_type`, `sweep_level`, `sweep_direction`, `sweep_detected_utc`, `sweep_source_timeframe`, `liquidity_pool_id`, `join_status`
