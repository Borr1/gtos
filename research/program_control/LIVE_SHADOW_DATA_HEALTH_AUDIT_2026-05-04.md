# Live Shadow Data Health Audit - 2026-05-04

**Schema:** `live_shadow_data_health_audit_v1`
**Generated:** `2026-06-01T19:18:10.753156+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This read-only audit checks cross-log candidate coverage, identity consistency, latest path alignment, path-label geometry sanity, pending-lifecycle joins, mechanical strategy coverage, opportunity-level duplicate counting, Sierra/Databento confluence and source/feature interpretation, lane expectation modes, critical null/empty fields, and explicit source-capture limitations.

## Counts

- Latest candidates: `506`
- Logs inspected: `24`
- Raw rows inspected: `231530`
- Issues: `2065`
- Candidate final outcomes: `{'REJECTED_L2': 125, 'LIMIT_PLACED': 17, 'REJECTED_GATE1_SAFETY': 42, 'REJECTED_GATE3_CIRCUIT_BREAKER': 56, 'REJECTED_GATE0_5_TRADING_ENABLED': 21, 'SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC': 235, 'LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN': 9, 'LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE': 1}`
- Latest path labels: `{'entry_touched_then_reached_tp1': 84, 'continued_without_entry_touch_to_tp_area': 80, 'entry_touched_tp_and_sl_m15_ambiguous': 201, 'went_through_entry_and_continued_to_sl': 79, 'entry_touched_unresolved': 12}`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 0 |
| `SERIOUS` | 2065 |
| `MODERATE` | 0 |
| `LOW` | 0 |

## Coverage

| Log | Covered candidates | Missing | Asof mismatches |
|---|---:|---:|---:|
| `v2b_forward_pairs.jsonl` | 506 | 0 | 0 |
| `prefill_delivery_path.jsonl` | 506 | 0 | 0 |
| `fvg_ob_confluence.jsonl` | 506 | 0 | 0 |
| `context_control_ledger.jsonl` | 506 | 0 | 0 |
| `live_structural_strategy_metadata.jsonl` | 404 | 102 | 0 |
| `databento_live_trigger_decisions.jsonl` | 404 | 102 | 0 |
| `sierra_confluence_source_status.jsonl` | 404 | 102 | 0 |
| `sierra_depth_feature_snapshots.jsonl` | 506 | 0 | 0 |
| `account_truth_reconciliation_status.jsonl` | 404 | 102 | 0 |
| `candidate_path_follow.jsonl` | 456 | 50 | 0 |
| `live_candidate_opportunity_clusters.jsonl` | 404 | 102 | 170 |
| `live_candidate_strategy_rollups.jsonl` | 404 | 102 | 170 |
| `v2b_forward_pair_resolutions.jsonl` | 492 | 14 | 239 |
| `prefill_delivery_path_resolutions.jsonl` | 492 | 14 | 239 |
| `fvg_ob_confluence_resolutions.jsonl` | 492 | 14 | 239 |
| `missed_opportunity_shadow.jsonl` | 404 | 102 | 170 |
| `candidate_ltf_path_order.jsonl` | 506 | 0 | 0 |

## Opportunity Counting

- Status counts: `{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 80, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 160, 'BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP': 164}`
- Algorithm versions: `{'active_setup_lifecycle_tolerance_v1': 404}`
- Unique opportunity IDs: `244`

## All-Row Identity Health

- Candidate-scoped rows checked: `231004`
- Orphan dependent rows by log: `{'pending_limit_lifecycle_join_backfill.jsonl': ['broadorigin_106777432745ee99599b8e76', 'broadorigin_eeb936474f606b9bebd2f4d5', 'broadorigin_c8cb84aaaddd60a9c6903d55', 'broadorigin_c70f73c1e55558004baea072', 'broadorigin_d294ad9e69a5bbc99465eba3', 'broadorigin_4d4218ca588cc46127193e8c', 'broadorigin_00f02f67485d48a04dde0666', 'broadorigin_91549cb78ebe2250488c44e0', 'broadorigin_d294ad9e69a5bbc99465eba3', 'broadorigin_00f02f67485d48a04dde0666', 'broadorigin_91549cb78ebe2250488c44e0', 'broadorigin_a58abd079e78a49fc3ed7a2a', 'broadorigin_95e1f4f841a261722b80a4c7', 'broadorigin_2f1fcbb7f16270cd2090f5ee']}`
- Candidate identity variant conflicts: `{}`

## Mechanical Strategy Health

- Latest strategy row counts per candidate: `{16: 207, 24: 249}`
- Missing mechanical rows by candidate: `{}`
- Outcome mismatches: `[]`

## Path Geometry Health

- Checked latest path rows: `456`
- Mismatches: `[]`

## Pending Lifecycle Health

- LIMIT_PLACED candidates: `['XAUUSD_2026-05-04T07:15:00+00:00', 'NAS100_2026-05-04T07:15:00+00:00', 'GBPJPY_2026-05-04T03:00:00+00:00', 'NAS100_2026-05-05T07:15:00+00:00', 'XAUUSD_2026-05-05T08:15:00+00:00', 'NAS100_2026-05-03T16:15:00+00:00', 'GBPJPY_2026-05-06T02:30:00+00:00', 'NAS100_2026-05-06T07:15:00+00:00', 'NAS100_2026-05-07T07:15:00+00:00', 'US30_cash_2026-05-08T13:45:00+00:00', 'NAS100_2026-05-08T15:45:00+00:00', 'GBPJPY_2026-05-11T07:30:00+00:00', 'US30_cash_2026-05-11T08:15:00+00:00', 'NAS100_2026-05-11T09:15:00+00:00', 'NAS100_2026-05-12T07:15:00+00:00', 'XAGUSD_2026-05-12T09:00:00+00:00', 'US30_cash_2026-05-12T09:30:00+00:00', 'BTCUSD_2026-06-01T12:00:00Z', 'ETHUSD_2026-06-01T12:00:00Z', 'EURJPY_2026-06-01T13:15:00Z', 'NAS100_2026-06-01T13:15:00Z', 'UKOIL_cash_2026-06-01T13:15:00Z', 'US30_cash_2026-06-01T13:15:00Z', 'USDJPY_2026-06-01T13:00:00Z', 'USOIL_cash_2026-06-01T13:15:00Z', 'GBPJPY_2026-06-01T16:45:00Z', 'NAS100_2026-06-01T17:15:00Z']`
- Missing lifecycle joins: `['BTCUSD_2026-06-01T12:00:00Z', 'ETHUSD_2026-06-01T12:00:00Z', 'EURJPY_2026-06-01T13:15:00Z', 'NAS100_2026-06-01T13:15:00Z', 'UKOIL_cash_2026-06-01T13:15:00Z', 'US30_cash_2026-06-01T13:15:00Z', 'USDJPY_2026-06-01T13:00:00Z', 'USOIL_cash_2026-06-01T13:15:00Z', 'GBPJPY_2026-06-01T16:45:00Z', 'NAS100_2026-06-01T17:15:00Z']`
- Unexpected joins: `[]`
- Trade ID mismatches: `[]`

## Source / Feature Interpretation

- Mismatches: `[]`

## External Confluence

- Sierra statuses: `{'FEATURES_EXTRACTED': 21, 'NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL': 244, 'LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED': 170, 'LOCAL_DEPTH_FILE_MISSING': 71}`
- Databento statuses: `{'NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE': 506}`
- Paid fetch attempted count: `0`

## Trade Record Candidate Coverage

- Trade-record candidates seen: `313`
- Matched candidate shadow rows: `299`
- Missing candidate shadow rows: `['ETHUSD_2026-06-01T18:00:00Z', 'EURGBP_2026-06-01T17:45:00Z', 'GBPJPY_2026-06-01T17:45:00Z', 'GBPJPY_2026-06-01T19:00:00Z', 'NAS100_2026-06-01T17:45:00Z', 'NAS100_2026-06-01T18:00:00Z', 'US30_cash_2026-06-01T18:45:00Z', 'US30_cash_2026-06-01T19:00:00Z']`
- Value mismatches: `[]`
- Documented candidate-id collisions: `[{'candidate_id': 'GBPJPY_2026-06-01T17:15:00Z', 'source_files': ['knowledge_base\\trade_records\\GBPJPY\\2026-06-01_moonshot_h17_18_1715_broadorigin_468d5a3cb120682b5a4da7a0.json', 'knowledge_base\\trade_records\\GBPJPY\\2026-06-01_moonshot_h17_18_1715_broadorigin_63ba2335b9cd056f3a7986e5.json'], 'reason': 'multiple trade-record files share one M15 candidate_id; exact source_file shadow row required for value comparison'}, {'candidate_id': 'GBPJPY_2026-06-01T18:00:00Z', 'source_files': ['knowledge_base\\trade_records\\GBPJPY\\2026-06-01_moonshot_h17_18_1800_broadorigin_9d573c2761fa8d6beb46cd3d.json', 'knowledge_base\\trade_records\\GBPJPY\\2026-06-01_moonshot_h17_18_1800_broadorigin_f386e7733430913d912d512b.json'], 'reason': 'multiple trade-record files share one M15 candidate_id; exact source_file shadow row required for value comparison'}, {'candidate_id': 'JP225_2026-06-01T17:30:00Z', 'source_files': ['knowledge_base\\trade_records\\JP225\\2026-06-01_moonshot_h17_18_1730_broadorigin_79fbe5d3912dcbf399809c23.json', 'knowledge_base\\trade_records\\JP225\\2026-06-01_moonshot_h17_18_1730_broadorigin_c9f363852200533007f2c7d7.json'], 'reason': 'multiple trade-record files share one M15 candidate_id; exact source_file shadow row required for value comparison'}]`

## Documented Limitations

- Source-not-captured fields: `{}`
- Legacy source-not-captured fields: `{'cost_aware_min_r_fields': 190, 'standalone_fvg_entry_geometry': 190, 'swing_protected_lock_level': 190}`
- Affected strategies: `{'FVG_OB_CONFLUENCE_OB_AFTER_FVG': 207, 'V2_STRUCT_COMPOSITE_ANY': 404, 'V2_STRUCT_FVG_MID_EDGE': 404, 'V2_STRUCT_SWING_PROTECTED': 404, 'V3_FVG_ONLY_RESCUE_RISK_BANK': 404, 'V3_FVG_THEN_OB_TAIL_RISK_BANK': 404, 'V3_OB_LOCK_COST_AWARE_MIN_R': 404, 'V3_OB_LOCK_PULLBACK_RISK_BANK': 404}`
- Unresolved score statuses: `{}`
- Legacy unresolved score statuses: `{}`
- Backfill rule: Do not synthesize SOURCE_NOT_CAPTURED fields from later candles. Backfill only from original decision-time rows/files that contain the exact value.

## Null Field Health

- Allowed null counts: `{'account_truth_reconciliation_status.jsonl.asof_latest_candle_utc': 404, 'account_truth_reconciliation_status.jsonl.source_symbol': 207, 'account_truth_reconciliation_status.jsonl.trade_id': 387, 'candidate_ltf_path_order.jsonl.mt5_read_error': 456, 'candidate_ltf_path_order.jsonl.sl_first_touch_utc': 226, 'candidate_ltf_path_order.jsonl.source_symbol': 207, 'candidate_ltf_path_order.jsonl.trade_id': 479, 'candidate_ltf_path_order.jsonl.entry_first_touch_utc': 130, 'candidate_ltf_path_order.jsonl.terminal_event_r': 35, 'candidate_ltf_path_order.jsonl.tp1_first_touch_utc': 141, 'candidate_ltf_path_order.jsonl.terminal_event_utc': 12, 'candidate_path_follow.jsonl.mt5_read_error': 456, 'candidate_path_follow.jsonl.trade_id': 431, 'context_control_ledger.jsonl.regime': 506, 'context_control_ledger.jsonl.source_hash': 506, 'context_control_ledger.jsonl.source_symbol': 207, 'context_control_ledger.jsonl.trade_id': 479, 'databento_live_trigger_decisions.jsonl.asof_latest_candle_utc': 404, 'databento_live_trigger_decisions.jsonl.source_symbol': 207, 'databento_live_trigger_decisions.jsonl.trade_id': 387, 'fvg_ob_confluence.jsonl.lower_timeframe_available': 506, 'fvg_ob_confluence.jsonl.regime': 506, 'fvg_ob_confluence.jsonl.source_hash': 506, 'fvg_ob_confluence.jsonl.source_symbol': 207, 'fvg_ob_confluence.jsonl.touch_count': 506, 'fvg_ob_confluence.jsonl.trade_id': 479, 'fvg_ob_confluence_resolutions.jsonl.trade_id': 467, 'live_candidate_opportunity_clusters.jsonl.overlapping_active_symbol_opportunity_ids': 211, 'live_candidate_opportunity_clusters.jsonl.trade_id': 387, 'live_candidate_opportunity_clusters.jsonl.opportunity_terminal_event_utc': 107, 'live_candidate_opportunity_clusters.jsonl.opportunity_entry_first_touch_utc': 76, 'live_candidate_opportunity_clusters.jsonl.asof_latest_candle_utc': 27, 'live_candidate_strategy_rollups.jsonl.overlapping_active_symbol_opportunity_ids': 211, 'live_candidate_strategy_rollups.jsonl.trade_id': 387, 'live_candidate_strategy_rollups.jsonl.opportunity_entry_first_touch_utc': 76, 'live_candidate_strategy_rollups.jsonl.asof_latest_candle_utc': 27, 'live_structural_strategy_metadata.jsonl.asof_latest_candle_utc': 404, 'live_structural_strategy_metadata.jsonl.source_symbol': 207, 'live_structural_strategy_metadata.jsonl.trade_id': 387, 'missed_opportunity_shadow.jsonl.trade_id': 387, 'pending_limit_lifecycle_join_backfill.jsonl.source_symbol': 9, 'prefill_delivery_path.jsonl.fill_delay_seconds': 506, 'prefill_delivery_path.jsonl.fill_happened': 506, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_cancel': 506, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_fill': 506, 'prefill_delivery_path.jsonl.pre_fill_candles': 506, 'prefill_delivery_path.jsonl.pre_fill_ticks_summary': 506, 'prefill_delivery_path.jsonl.regime': 506, 'prefill_delivery_path.jsonl.reversal_leg_timing': 506, 'prefill_delivery_path.jsonl.source_hash': 506, 'prefill_delivery_path.jsonl.source_symbol': 207, 'prefill_delivery_path.jsonl.trade_id': 479, 'prefill_delivery_path_resolutions.jsonl.trade_id': 467, 'sierra_confluence_source_status.jsonl.asof_latest_candle_utc': 404, 'sierra_confluence_source_status.jsonl.source_symbol': 207, 'sierra_confluence_source_status.jsonl.trade_id': 387, 'sierra_confluence_source_status.jsonl.sierra_futures_symbol': 162, 'sierra_confluence_source_status.jsonl.sierra_source_symbol': 162, 'sierra_depth_feature_snapshots.jsonl.depth_path': 244, 'sierra_depth_feature_snapshots.jsonl.sierra_futures_symbol': 244, 'sierra_depth_feature_snapshots.jsonl.sierra_source_symbol': 244, 'strategy_follow_candidates.jsonl.regime': 506, 'strategy_follow_candidates.jsonl.source_hash': 506, 'strategy_follow_candidates.jsonl.source_symbol': 207, 'strategy_follow_candidates.jsonl.trade_id': 479, 'v2b_forward_pair_resolutions.jsonl.trade_id': 467, 'v2b_forward_pairs.jsonl.lower_timeframe_available': 506, 'v2b_forward_pairs.jsonl.regime': 506, 'v2b_forward_pairs.jsonl.source_hash': 506, 'v2b_forward_pairs.jsonl.source_symbol': 207, 'v2b_forward_pairs.jsonl.trade_id': 479, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_path_order_label': 496, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_event_utc': 17136, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_order_ambiguity': 8752, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_outcome_status': 8752, 'live_mechanical_strategy_shadow_outcomes.jsonl.strategy_proxy_r': 6675, 'live_mechanical_strategy_shadow_outcomes.jsonl.trade_id': 125200, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_candidate_id': 90}`
- Unexpected null counts: `{'account_truth_reconciliation_status.jsonl.source_component': 197, 'candidate_ltf_path_order.jsonl.tp1_first_touch_bar_ohlc': 125, 'candidate_ltf_path_order.jsonl.sl_first_touch_bar_ohlc': 102, 'candidate_ltf_path_order.jsonl.terminal_event_bar_ohlc': 62, 'candidate_ltf_path_order.jsonl.asof_latest_candle_utc': 50, 'candidate_ltf_path_order.jsonl.entry_first_touch_bar_ohlc': 50, 'candidate_ltf_path_order.jsonl.m1_source_first_bar_utc': 50, 'candidate_ltf_path_order.jsonl.m1_source_last_bar_utc': 50, 'candidate_ltf_path_order.jsonl.m1_source_sha256': 50, 'candidate_ltf_path_order.jsonl.m1_spread_max': 50, 'candidate_ltf_path_order.jsonl.m1_spread_mean': 50, 'candidate_ltf_path_order.jsonl.m1_spread_min': 50, 'candidate_ltf_path_order.jsonl.terminal_event_r': 50, 'candidate_ltf_path_order.jsonl.terminal_event_utc': 50, 'candidate_path_follow.jsonl.sl_first_touch_utc': 176, 'candidate_path_follow.jsonl.entry_first_touch_utc': 80, 'candidate_path_follow.jsonl.tp1_first_touch_utc': 91, 'context_control_ledger.jsonl.source_component': 299, 'databento_live_trigger_decisions.jsonl.source_component': 197, 'fvg_ob_confluence.jsonl.fvg_bounds': 307, 'fvg_ob_confluence.jsonl.sequencing': 310, 'fvg_ob_confluence.jsonl.ob_bounds': 302, 'fvg_ob_confluence.jsonl.composite_arbitration': 299, 'fvg_ob_confluence.jsonl.disagreement_reason': 299, 'fvg_ob_confluence.jsonl.poi_quality': 299, 'fvg_ob_confluence_resolutions.jsonl.source_component': 492, 'fvg_ob_confluence_resolutions.jsonl.asof_latest_candle_utc': 46, 'fvg_ob_confluence_resolutions.jsonl.bars_elapsed': 46, 'fvg_ob_confluence_resolutions.jsonl.hit_sl': 46, 'fvg_ob_confluence_resolutions.jsonl.hit_tp1': 46, 'fvg_ob_confluence_resolutions.jsonl.path_label': 46, 'fvg_ob_confluence_resolutions.jsonl.path_outcome_status': 46, 'fvg_ob_confluence_resolutions.jsonl.touched_entry': 46, 'live_candidate_opportunity_clusters.jsonl.source_component': 404, 'live_candidate_opportunity_clusters.jsonl.candidate_path_label': 27, 'live_candidate_opportunity_clusters.jsonl.nearest_distance_to_entry_r': 27, 'live_candidate_strategy_rollups.jsonl.candidate_path_label': 27, 'live_candidate_strategy_rollups.jsonl.latest_follow_asof_utc': 27, 'live_candidate_strategy_rollups.jsonl.mechanical_dependency_signature': 27, 'live_candidate_strategy_rollups.jsonl.nearest_distance_to_entry_r': 27, 'live_structural_strategy_metadata.jsonl.latest_ltf_asof_utc': 27, 'live_structural_strategy_metadata.jsonl.latest_path_asof_utc': 27, 'missed_opportunity_shadow.jsonl.source_component': 404, 'missed_opportunity_shadow.jsonl.asof_latest_candle_utc': 27, 'missed_opportunity_shadow.jsonl.limit_entry_path_label': 27, 'missed_opportunity_shadow.jsonl.nearest_distance_to_entry_r': 27, 'pending_limit_lifecycle_join_backfill.jsonl.asof_latest_candle_utc': 4, 'pending_limit_lifecycle_join_backfill.jsonl.candidate_id_backfilled': 21, 'pending_limit_lifecycle_join_backfill.jsonl.decision_time_utc_backfilled': 21, 'pending_limit_lifecycle_join_backfill.jsonl.framework': 21, 'pending_limit_lifecycle_join_backfill.jsonl.decision_time_utc': 11, 'pending_limit_lifecycle_join_backfill.jsonl.source_component': 11, 'prefill_delivery_path.jsonl.source_component': 299, 'prefill_delivery_path_resolutions.jsonl.source_component': 492, 'prefill_delivery_path_resolutions.jsonl.asof_latest_candle_utc': 46, 'prefill_delivery_path_resolutions.jsonl.bars_elapsed': 46, 'prefill_delivery_path_resolutions.jsonl.hit_sl': 46, 'prefill_delivery_path_resolutions.jsonl.hit_tp1': 46, 'prefill_delivery_path_resolutions.jsonl.path_label': 46, 'prefill_delivery_path_resolutions.jsonl.path_outcome_status': 46, 'prefill_delivery_path_resolutions.jsonl.touched_entry': 46, 'sierra_confluence_source_status.jsonl.source_component': 197, 'sierra_depth_feature_snapshots.jsonl.depth_file_mtime_utc': 315, 'sierra_depth_feature_snapshots.jsonl.depth_file_size_bytes': 315, 'strategy_follow_candidates.jsonl.mt5_order_ticket': 430, 'strategy_follow_candidates.jsonl.native_pending_order_type': 430, 'strategy_follow_candidates.jsonl.broker_pending_order_created': 409, 'strategy_follow_candidates.jsonl.pending_order_mode': 409, 'v2b_forward_pair_resolutions.jsonl.source_component': 492, 'v2b_forward_pair_resolutions.jsonl.asof_latest_candle_utc': 46, 'v2b_forward_pair_resolutions.jsonl.bars_elapsed': 46, 'v2b_forward_pair_resolutions.jsonl.hit_sl': 46, 'v2b_forward_pair_resolutions.jsonl.hit_tp1': 46, 'v2b_forward_pair_resolutions.jsonl.path_label': 46, 'v2b_forward_pair_resolutions.jsonl.path_outcome_status': 46, 'v2b_forward_pair_resolutions.jsonl.touched_entry': 46, 'v2b_forward_pairs.jsonl.source_component': 299, 'live_mechanical_strategy_shadow_outcomes.jsonl.branch_decision': 40166, 'live_mechanical_strategy_shadow_outcomes.jsonl.decision_evidence': 40166, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_real_volume_count': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_real_volume_max': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_real_volume_mean': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_real_volume_min': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_real_volume_source_status': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_spread_count': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_spread_max': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_spread_mean': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_spread_min': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_spread_source_status': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_tick_volume_count': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_tick_volume_max': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_tick_volume_mean': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_tick_volume_min': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.m15_tick_volume_source_status': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.nearest_abs_distance_to_entry': 98832, 'live_mechanical_strategy_shadow_outcomes.jsonl.opportunity_proxy_r_reference': 22557, 'live_mechanical_strategy_shadow_outcomes.jsonl.preserved_candidate_path_proxy_r': 6481, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_current_claim_proxy_r_reference': 2533, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_match_price': 3385, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_match_time_utc': 3385, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_match_timeframe': 3385, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_match_type': 3385, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_stop_distance_price': 3385, 'live_mechanical_strategy_shadow_outcomes.jsonl.standalone_fvg_matching_gap_timeframes': 12284, 'live_mechanical_strategy_shadow_outcomes.jsonl.standalone_fvg_poi_matching_gap_timeframes': 14108, 'live_mechanical_strategy_shadow_outcomes.jsonl.structural_duplicate_proxy_reference_r': 1581, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_hypothetical_proxy_reference_r': 507, 'live_mechanical_strategy_shadow_outcomes.jsonl.strategy_proxy_r': 27977, 'live_mechanical_strategy_shadow_outcomes.jsonl.swing_protected_type_mismatches': 4554, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_entry_touch_spread_unit': 488, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_entry_touch_spread_value_source_safe': 488, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_protective_area_first_touch_utc': 446, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_terminal_area_first_touch_utc': 67, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_avoid_non_saved_proxy_r_reference': 316, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_avoid_saved_proxy_interval_status': 405, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_avoid_saved_proxy_r_interval_high': 405, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_avoid_saved_proxy_r_interval_low': 405, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_unresolved_horizon_mae_r_reference': 520, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_unresolved_horizon_mfe_r_reference': 520, 'live_mechanical_strategy_shadow_outcomes.jsonl.missed_opportunity_audit': 3039, 'live_mechanical_strategy_shadow_outcomes.jsonl.opportunity_preservation_status': 3039, 'live_mechanical_strategy_shadow_outcomes.jsonl.underlying_intelligence_preserved': 3039, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_median_depth10_imbalance': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_median_max_ask_wall': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_median_max_bid_wall': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_median_near_far_ratio': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_median_total_depth10': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_sample_count': 1091, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_thin_depth10_rate': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_feature_row_key': 1091, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_missing_field': 1254, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_pre60_median_depth10_imbalance': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_pre60_median_total_depth10': 1155, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_event15_depth_record_count': 227, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_path_proxy_r': 227, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_path_proxy_r_basis': 227, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_pre60_depth_record_count': 227, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_record_count': 227, 'live_mechanical_strategy_shadow_outcomes.jsonl.depth_thinness_window_presence_status': 227, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_checked_candle_time_utc': 18, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_decision_spread_unit': 1, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_decision_spread_value_source_safe': 1, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_avoid_saved_proxy_r': 407, 'live_mechanical_strategy_shadow_outcomes.jsonl.gbpjpy_long_adverse_current_claim_proxy_r_reference': 170, 'live_mechanical_strategy_shadow_outcomes.jsonl.standalone_fvg_current_claim_proxy_r_reference': 184, 'live_mechanical_strategy_shadow_outcomes.jsonl.standalone_fvg_poi_price_level': 2948, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_fill_first_touch_utc': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_outcome_status': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_proxy_r': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_shifted_entry_price': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_shifted_target_r': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_source_files': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_terminal_event_utc': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.entry_offset_050r_tick_replay_status': 1474, 'live_mechanical_strategy_shadow_outcomes.jsonl.moonshot_selected_action_source_capture_created_at_utc': 10318}`
- Critical null counts: `{}`
- Allowed null policy: Allowed nulls are explicit non-decision or source-identity fields such as trade_id/source_symbol/regime/source_hash, plus point-in-time rows that intentionally have no asof_latest_candle_utc.

## Lane Expectations

- Row counts by mode: `{'candidate_driven_point_in_time': 9254, 'candidate_driven_path_aligned': 65504, 'candidate_registry': 506, 'candidate_path_aligned_strategy_rows': 154992, 'source_driven_lifecycle_join': 817, 'event_waiting_exit_management': 0, 'approval_blocked_event_triggered_paid_data': 0, 'source_driven_readiness_status': 214, 'source_driven_preregistration_status': 149, 'source_driven_observer_hardening_status': 94}`
- Staleness policy: `{'candidate_registry': 'candidate rows are event/candidate driven and must have dependent coverage when present', 'candidate_driven_point_in_time': 'one latest row per candidate or explicit source/status blocker', 'candidate_driven_path_aligned': 'latest asof must align to candidate_path_follow when candidate paths advance', 'source_driven_lifecycle_join': 'freshness follows source lifecycle events, not wall-clock churn', 'source_driven_readiness_status': 'freshness follows upstream evidence signatures, not wall-clock churn', 'source_driven_preregistration_status': 'freshness follows preregistration/source-status signatures, not wall-clock churn', 'source_driven_observer_hardening_status': 'freshness follows observer source/status signatures and stale-status transitions', 'event_waiting_exit_management': 'empty is valid only with no filled trade/trigger status', 'approval_blocked_event_triggered_paid_data': 'no paid live rows until approved trigger policy is active'}`

## Issues

| Severity | Code | Log | Candidate | Message |
|---|---|---|---|---|
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T11:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `BTCUSD_2026-06-01T12:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `ETHUSD_2026-06-01T12:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDCAD_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `BTCUSD_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `BTCUSD_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `BTCUSD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `BTCUSD_2026-06-01T15:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `BTCUSD_2026-06-01T16:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `CHFJPY_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `CHFJPY_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `CHFJPY_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `CHFJPY_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `CHFJPY_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `CHFJPY_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `ETHUSD_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `ETHUSD_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `ETHUSD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `ETHUSD_2026-06-01T15:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T15:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T16:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T16:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T15:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURJPY_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURJPY_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURJPY_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURJPY_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURJPY_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `JP225_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T15:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T14:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T15:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `US30_cash_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDCAD_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDCAD_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDCAD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDCAD_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDJPY_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T14:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T15:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `XAUUSD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `XAUUSD_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `XAUUSD_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T16:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T17:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T17:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `EURGBP_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T16:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `GBPJPY_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T17:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `NAS100_2026-06-01T17:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `UKOIL_cash_2026-06-01T17:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDCAD_2026-06-01T17:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USOIL_cash_2026-06-01T17:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T11:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `BTCUSD_2026-06-01T12:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `ETHUSD_2026-06-01T12:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDCAD_2026-06-01T11:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `BTCUSD_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `BTCUSD_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `BTCUSD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `BTCUSD_2026-06-01T15:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `BTCUSD_2026-06-01T16:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `CHFJPY_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `CHFJPY_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `CHFJPY_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `CHFJPY_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `CHFJPY_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `CHFJPY_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `ETHUSD_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `ETHUSD_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `ETHUSD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `ETHUSD_2026-06-01T15:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T15:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T16:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T16:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T15:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURJPY_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURJPY_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURJPY_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURJPY_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURJPY_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T13:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T14:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `JP225_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T15:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T14:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T15:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `US30_cash_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDCAD_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDCAD_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDCAD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDCAD_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDJPY_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T12:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T13:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T13:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T14:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T15:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USOIL_cash_2026-06-01T15:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `XAUUSD_2026-06-01T13:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `XAUUSD_2026-06-01T14:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `XAUUSD_2026-06-01T14:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T16:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T17:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T17:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `EURGBP_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T16:45:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `GBPJPY_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T17:15:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `NAS100_2026-06-01T17:00:00Z` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `UKOIL_cash_2026-06-01T17:30:00Z` | candidate has no latest row in dependent shadow log |

Only first 200 issues shown; JSON contains all `2065` issues.
