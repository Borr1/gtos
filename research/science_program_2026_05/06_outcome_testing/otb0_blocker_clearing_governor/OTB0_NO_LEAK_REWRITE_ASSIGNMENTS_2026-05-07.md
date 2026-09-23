# OTB0 No-Leak Rewrite Assignments - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

## Rewrite Assignments

| Hypothesis | Forbidden current fields | Rewrite to as-of whitelist | Move forbidden fields to |
| --- | --- | --- | --- |
| HYP-G11-PROVENANCE-GATE-001 | outcome_r, win_loss, future_price, post_entry_path, trade_result | source_id_asof, source_contract_version_asof, source_hash_asof, parser_version_asof, feature_publication_asof_utc, source_cache_time_utc, validation_safe_flag_asof_metadata_only | blocker_text_or_label_separation_policy |
| HYP-G11-COVERAGE-GATE-002 | actual_r, trade_outcome, future_return, post_signal_continuation | coverage_manifest_id, instrument_enabled_asof, source_available_asof, session_calendar_asof, source_missingness_rate_asof, coverage_window_end_utc | blocker_text_or_label_separation_policy |
| HYP-G11-SOURCE-TRANSFER-003 | actual_r, take_profit_hit, stop_loss_hit, post_entry_path | source_symbol, target_symbol, proxy_map_version_asof, roll_contract_asof, lead_lag_window_predeclared, transfer_alignment_score_asof | blocker_text_or_label_separation_policy |
| HYP-G11-PUBLIC-LAG-004 | post_release_revision, future_release_value, actual_r, trade_outcome | release_id, source_publication_timestamp_utc, source_cache_time_utc, vintage_date_asof, revision_state_asof, stale_source_age_minutes_asof | blocker_text_or_label_separation_policy |
| HYP-G11-OPTIONS-VOL-005 | future_vol_index, post_event_outcome, actual_r, trade_result | vol_source_id, vol_index_symbol, observation_date, publication_asof_utc, source_cache_hash, license_state_asof, parser_version_asof | blocker_text_or_label_separation_policy |
| HYP-G11-OBSERVER-EXPANSION-006 | actual_r, win_loss, post_signal_path, tp_sl_hit | observer_symbol, observer_enabled_asof, trading_enabled_false_asof, session_window_asof, source_freshness_age_asof, observer_blocker_flag_asof | blocker_text_or_label_separation_policy |
| HYP-G11-FRICTION-GATE-007 | future_return, actual_r, post_entry_path, trade_result | spread_at_decision, spread_atr_ratio_at_decision, tick_value_asof, contract_spec_version_asof, commission_schedule_asof, min_stop_distance_asof | blocker_text_or_label_separation_policy |
| HYP-G11G4-SOURCE-GATED-ORDERFLOW-008 | actual_r, trade_result, post_entry_path, future_orderflow | orderflow_source_id, dataset_schema_asof, source_symbol, proxy_map_version_asof, license_state_asof, source_capture_utc, feature_window_end_utc_lte_decision_time | blocker_text_or_label_separation_policy |

## Rewrite Rules

1. Do not silently reinterpret forbidden outcome/future fields as safe features.
2. Keep forbidden fields only in blocker/test-method/label-separation text, never in `no_leak_fields`.
3. Do not set `validation_safe=true`.
4. Do not set `outcome_review_opened=true`.
5. Submit rewritten rows to later G12 blocker-clearing audit before any outcome lane opens.
