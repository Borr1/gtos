# OTB0 Packet Builder Requirements - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**Outcome/result columns allowed in primary packets:** `false`

## Builder Lanes

| Lane | Packet class | Packets | Required output contract |
| --- | --- | --- | --- |
| OTB1 | lifecycle/no-fill | 10 | one packet-specific frozen input file per experiment, setup_id_or_candidate_id, decision_asof_utc, source_capture_utc, pending_created_utc_if_applicable, lifecycle_event_id, lifecycle_state, fill_or_no_fill_state, cancel_expiry_or_wrong_side_reason, duplicate_group_id, source_hash, source_symbol, label family separation: no broker_actual_r/synthetic_path_r/win_loss/outcome_r in primary lifecycle rows, stable lifecycle taxonomy for filled, still_pending, cancelled, expired, wrong_side, tick_missing, same_bar_or_path_ambiguity, unresolved |
| OTB2 | synthetic replay | 16 | one packet-specific frozen input file per experiment, ordered_path_source_id, path_start_utc, path_end_utc, source_hash, duplicate_group_id, decision_asof_utc, entry_sl_tp_or_level_packet, cost_model_version, same_bar_ambiguity_policy, broker_actual_r_absent_from_primary_metric=true, source hashes and no-leak feature whitelist, local OHLC/path-log regeneration manifest when default V2/V3 event logs are absent |

## Universal Packet Fields From OTG0

| Field |
| --- |
| experiment_id |
| hypothesis_id |
| frozen_at_utc |
| outcome_review_opened=false |
| promotion_verdict=NO_PROMOTION_VERDICT |
| metric |
| null |
| alternative |
| sample_floor |
| duplicate_policy |
| label_separation_policy |
| source_contract_or_blocker_refs |
| result_quarantine_path |

## OTB1 Lifecycle Packets

| Packet | Experiment | Current verdict | Blockers |
| --- | --- | --- | --- |
| OTG0-PKT-011 | G10-EXP-PREFILL-003 | BLOCKED_WITH_EXACT_FIELDS | No packet-specific row file exists., Existing prefill/pending logs are source evidence, not exact OTL1 packet rows., Missing or non-normalized fields: setup_id_or_candidate_id, decision_asof_utc, source_capture_utc, lifecycle_event_id, fill_or_no_fill_state, cancel_expiry_or_wrong_side_reason, duplicate_group_id., Missing source_hash, source_symbol, ordered prefill candles/ticks, pending/native broker state, spread/tick at arm/trigger, and most trade_id joins., Historical coverage has 0 broker lifecycle rows and 0 original POI-bound rows. |
| OTG0-PKT-016 | EXP-G11-FRICTION-GATE-007 | BLOCKED_WITH_EXACT_FIELDS | No registered source contract in frozen packet., G11 no_leak_fields contain forbidden future/outcome names: future_return, actual_r, post_entry_path, trade_result., Need concrete friction source cache, as-of feature whitelist, duplicate group, lifecycle denominator, and exact packet fields. |
| OTG0-PKT-017 | EXP-G11-OBSERVER-EXPANSION-006 | BLOCKED_WITH_EXACT_FIELDS | No registered source contract in frozen packet., G11 no_leak_fields contain forbidden outcome/post-signal names: actual_r, win_loss, post_signal_path, tp_sl_hit., Existing shadow_observer_status rows are observer status, not lifecycle packets, and lack exact session/side/as-of/source-capture/lifecycle/duplicate fields. |
| OTG0-PKT-025 | EXP-G2-GARCH-LIFECYCLE-002 | BLOCKED_WITH_EXACT_FIELDS | No registered source contract in frozen packet., No candidate lifecycle packet joined to realized-vol and vol-of-vol as-of fields., Need realized_vol_*_asof fields, lifecycle fields, duplicate_group_id, and source/as-of proof. |
| OTG0-PKT-029 | EXP-G2-SURVIVAL-PATH-006 | BLOCKED_WITH_EXACT_FIELDS | No registered source contract in frozen packet., Current lifecycle logs have partial aliases but no normalized cause-specific survival packet., Need event-time and censoring fields, pending_created_utc_if_applicable, lifecycle_event_id, fill_or_no_fill_state, cancel_expiry_or_wrong_side_reason, duplicate_group_id, and source-capture proof. |
| OTG0-PKT-045 | EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003 | BLOCKED_WITH_EXACT_FIELDS | No registered source contract in frozen packet., Need XAUUSD footprint/absorption source contract, predecision flow fields, source hash/symbol, POI bounds, lifecycle truth, and broker actual-R separation. |
| OTG0-PKT-055 | EXP-G5-NEWS-005 | BLOCKED_WITH_EXACT_FIELDS | Source contract path data/news/forexfactory_calendar.json is absent; configured data/news_calendar.json exists., Unresolved LIT-G5-FOMC-001, LIT-G5-FOMC-DECAY-001, and LIT-G5-NEWS-001 refs remain., Need event/source cache timestamps, event IDs/window classes, stale-calendar rule, matched-control duplicate groups, and exact lifecycle rows. |
| OTG0-PKT-059 | EXP-G5-XG7-MACRO-ATTN-009 | BLOCKED_WITH_EXACT_FIELDS | Same G5 calendar path mismatch and unresolved LIT-G5 refs as OTG0-PKT-055., Need G7 macro labels committed before outcome review and a canonical G5/G7 interaction denominator., Need event/month clustering, duplicate_group_id, and exact lifecycle packet rows. |
| OTG0-PKT-071 | EXP-G7-FOMC-ATTN-003 | BLOCKED_WITH_EXACT_FIELDS | Fed/FOMC cached HTML exists, but parser, stale-source tests, frozen event-window labels, and no-lookahead checks are missing., G5 local calendar source path mismatch also affects this packet., Need event_id, event_time_utc, event_source_cache_time_utc, window_class, source_capture_utc, exact lifecycle labels, and duplicate/event-cluster IDs. |
| OTG0-PKT-079 | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001 | BLOCKED_WITH_EXACT_FIELDS | Cboe raw CSVs exist, but publication-as-of, parser/cache hashes, legal review, and no-lookahead tests are unresolved., Current lifecycle rows are not normalized to exact OTL1 schema and do not expose duplicate_group_id., Shares hypothesis family HYP-G8-VIX1D9D-STRESS-002 with EXP-G8-VIX1D9D-STRESS-002; denominator policy must prevent duplicate route counting. |

## OTB2 Synthetic Packets

| Packet | Experiment | Current decision | Blocking fields |
| --- | --- | --- | --- |
| OTG0-PKT-013 | G10-EXP-RISKBANK-005 | BLOCKED_WITH_EXACT_FIELDS | ordered_path_source_id, path_start_utc, path_end_utc, source_hash, duplicate_group_id, decision_asof_utc, cost_model_version, entry_sl_tp_or_level_packet |
| OTG0-PKT-031 | EXP-G3-DC-OVERSHOOT-002 | BLOCKED_WITH_EXACT_FIELDS | dc_overshoot_ratio_at_decision_packet, decision_asof_utc, ordered_path_source_id, duplicate_group_id, source_hash, cost_model_version, same_bar_ambiguity_policy |
| OTG0-PKT-032 | EXP-G3-DC-SWING-001 | BLOCKED_WITH_EXACT_FIELDS | dc_threshold_grid_packet, dc_event_count_at_decision, dc_event_rate_lookback_only, duplicate_group_id, source_hash, ordered_path_source_id |
| OTG0-PKT-036 | EXP-G3-TDA-007 | BLOCKED_WITH_EXACT_FIELDS | embedding_window_end_at_decision, persistence_summary_packet, path_start_utc, path_end_utc, source_hash, duplicate_group_id |
| OTG0-PKT-044 | EXP-G4-STOP-CASCADE-MOMENTUM-006 | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, sweep_cascade_packet, entry_sl_tp_or_level_packet, matched_group_id_or_duplicate_group_id, source_hash, ordered_path_source_id |
| OTG0-PKT-049 | EXP-G4G6-CASCADE-GENERIC-010 | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, g4_g6_matched_packet, source_valid_flow_depth_fields, matched_group_id, source_symbol, source_hash |
| OTG0-PKT-052 | EXP-G5-AMH-004 | BLOCKED_WITH_EXACT_FIELDS | unresolved_source_refs, monthly_decay_packet, month_closed_timestamp_utc, next_month_path_label_boundary, source_hash, duplicate_group_id, sample_floor_effective_n |
| OTG0-PKT-053 | EXP-G5-CROWD-001 | BLOCKED_WITH_EXACT_FIELDS | google_trends_extractor_cache, source_publication_timestamp_utc, query_protocol_hash, crowding_proxy_value_asof, duplicate_group_id, ordered_path_source_id |
| OTG0-PKT-056 | EXP-G5-PRED-003 | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, stress_proxy_packet, g4_source_valid_stress_source, matched_baseline_packet, source_hash, duplicate_cluster_key |
| OTG0-PKT-060 | G6-EXP-001-OB-VS-GENERIC-RETRACE | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, ob_vs_generic_packet, generic_retrace_comparator, entry_sl_tp_or_level_packet, duplicate_setup_id, source_hash |
| OTG0-PKT-062 | G6-EXP-003-OPENING-DRIVE-CONTINUATION | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, opening_drive_packet, frozen_range_definition, path_start_utc, path_end_utc, cost_model_version, duplicate_breakout_key |
| OTG0-PKT-063 | G6-EXP-004-EXHAUSTION-CHANGEPOINT | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, exhaustion_changepoint_packet, threshold_freeze, ordered_path_source_id, duplicate_impulse_key, source_hash, cost_model_version |
| OTG0-PKT-066 | G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE | BLOCKED_WITH_EXACT_FIELDS | registered_source_contracts, round_number_band_packet, ob_bounds, liquidity_sweep_asof_fields, ordered_path_source_id, duplicate_ob_zone_key, source_hash |
| OTG0-PKT-069 | EXP-G7-CROSSASSET-STRESS-008 | BLOCKED_WITH_EXACT_FIELDS | fred_dxy_parser_cache_asof_proof, stress_state_packet, source_cache_time_utc, stress_state_timestamp_utc, source_hash, ordered_path_source_id, duplicate_stress_episode_key |
| OTG0-PKT-074 | EXP-G7-LBMA-FIX-004 | BLOCKED_WITH_EXACT_FIELDS | lbma_parser_timestamp_test, fix_window_packet, source_hash, timezone_rule, matched_non_fix_controls, ordered_path_source_id, duplicate_setup_fix_key |
| OTG0-PKT-075 | EXP-G7-USD-REALRATE-001 | BLOCKED_WITH_EXACT_FIELDS | fred_dxy_validation_ready_cache, usd_realrate_state_packet, source_hash, publication_or_close_time_rule, ordered_path_source_id, duplicate_day_setup_key, same_day_daily_close_leakage_test |

## Non-Negotiable Builder Rules

1. Builders create frozen input packets only, not result files.
2. Builders must not create or write under `research/science_program_2026_05/06_outcome_testing/quarantine/`.
3. Builders must not read or report R/result values.
4. Builders must make duplicate grouping, source hash, source capture time, and no-leak whitelist machine-checkable before any later result lane starts.
5. Broker actual-R, synthetic path-R, and lifecycle/no-fill labels remain physically separate.
