# Live Shadow Data Health Audit - 2026-05-04

**Schema:** `live_shadow_data_health_audit_v1`
**Generated:** `2026-05-05T21:17:29.349395+00:00`
**Status:** `OK_WITH_DOCUMENTED_LIMITATIONS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This read-only audit checks cross-log candidate coverage, identity consistency, latest path alignment, path-label geometry sanity, pending-lifecycle joins, mechanical strategy coverage, opportunity-level duplicate counting, Sierra/Databento confluence and source/feature interpretation, lane expectation modes, critical null/empty fields, and explicit source-capture limitations.

## Counts

- Latest candidates: `76`
- Logs inspected: `24`
- Raw rows inspected: `49509`
- Issues: `0`
- Candidate final outcomes: `{'REJECTED_L2': 51, 'LIMIT_PLACED': 6, 'REJECTED_GATE1_SAFETY': 17, 'REJECTED_GATE3_CIRCUIT_BREAKER': 2}`
- Latest path labels: `{'entry_touched_then_reached_tp1': 5, 'continued_without_entry_touch_to_tp_area': 62, 'entry_touched_tp_and_sl_m15_ambiguous': 2, 'went_through_entry_and_continued_to_sl': 4, 'entry_touched_unresolved': 3}`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 0 |
| `SERIOUS` | 0 |
| `MODERATE` | 0 |
| `LOW` | 0 |

## Coverage

| Log | Covered candidates | Missing | Asof mismatches |
|---|---:|---:|---:|
| `v2b_forward_pairs.jsonl` | 76 | 0 | 0 |
| `prefill_delivery_path.jsonl` | 76 | 0 | 0 |
| `fvg_ob_confluence.jsonl` | 76 | 0 | 0 |
| `context_control_ledger.jsonl` | 76 | 0 | 0 |
| `live_structural_strategy_metadata.jsonl` | 76 | 0 | 0 |
| `databento_live_trigger_decisions.jsonl` | 76 | 0 | 0 |
| `sierra_confluence_source_status.jsonl` | 76 | 0 | 0 |
| `sierra_depth_feature_snapshots.jsonl` | 76 | 0 | 0 |
| `account_truth_reconciliation_status.jsonl` | 76 | 0 | 0 |
| `candidate_path_follow.jsonl` | 76 | 0 | 0 |
| `live_candidate_opportunity_clusters.jsonl` | 76 | 0 | 0 |
| `live_candidate_strategy_rollups.jsonl` | 76 | 0 | 0 |
| `v2b_forward_pair_resolutions.jsonl` | 76 | 0 | 0 |
| `prefill_delivery_path_resolutions.jsonl` | 76 | 0 | 0 |
| `fvg_ob_confluence_resolutions.jsonl` | 76 | 0 | 0 |
| `missed_opportunity_shadow.jsonl` | 76 | 0 | 0 |
| `candidate_ltf_path_order.jsonl` | 76 | 0 | 0 |

## Opportunity Counting

- Status counts: `{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 12, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 63, 'BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP': 1}`
- Algorithm versions: `{'active_setup_lifecycle_tolerance_v1': 76}`
- Unique opportunity IDs: `13`

## All-Row Identity Health

- Candidate-scoped rows checked: `49375`
- Orphan dependent rows by log: `{}`
- Candidate identity variant conflicts: `{}`

## Mechanical Strategy Health

- Latest strategy row counts per candidate: `{16: 76}`
- Missing mechanical rows by candidate: `{}`
- Outcome mismatches: `[]`

## Path Geometry Health

- Checked latest path rows: `76`
- Mismatches: `[]`

## Pending Lifecycle Health

- LIMIT_PLACED candidates: `['XAUUSD_2026-05-04T07:15:00+00:00', 'NAS100_2026-05-04T07:15:00+00:00', 'GBPJPY_2026-05-04T03:00:00+00:00', 'NAS100_2026-05-05T07:15:00+00:00', 'XAUUSD_2026-05-05T08:15:00+00:00', 'NAS100_2026-05-03T16:15:00+00:00']`
- Missing lifecycle joins: `[]`
- Unexpected joins: `[]`
- Trade ID mismatches: `[]`

## Source / Feature Interpretation

- Mismatches: `[]`

## External Confluence

- Sierra statuses: `{'FEATURES_EXTRACTED': 21, 'NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL': 3, 'LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED': 52}`
- Databento statuses: `{'NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE': 76}`
- Paid fetch attempted count: `0`

## Trade Record Candidate Coverage

- Trade-record candidates seen: `78`
- Matched candidate shadow rows: `76`
- Missing candidate shadow rows: `[]`
- Value mismatches: `[]`
- Documented candidate-id collisions: `[{'candidate_id': 'XAUUSD_2026-05-03T16:30:00+00:00', 'source_files': ['knowledge_base\\trade_records\\XAUUSD\\2026-05-03_ny_1630.json', 'knowledge_base\\trade_records\\XAUUSD\\2026-05-03_ny_1645.json', 'knowledge_base\\trade_records\\XAUUSD\\2026-05-03_ny_1700.json'], 'reason': 'multiple trade-record files share one M15 candidate_id; exact source_file shadow row required for value comparison'}]`

## Documented Limitations

- Source-not-captured fields: `{'cost_aware_min_r_fields': 76, 'fvg_lock_state': 76, 'post_lock_reentry_state': 76, 'standalone_fvg_entry_geometry': 76, 'structural_lock_event_time_price': 76, 'swing_protected_lock_level': 76}`
- Affected strategies: `{'FVG_OB_CONFLUENCE_OB_AFTER_FVG': 76, 'V2_STRUCT_COMPOSITE_ANY': 76, 'V2_STRUCT_FVG_MID_EDGE': 76, 'V2_STRUCT_SWING_PROTECTED': 76, 'V3_FVG_ONLY_RESCUE_RISK_BANK': 76, 'V3_FVG_THEN_OB_TAIL_RISK_BANK': 76, 'V3_OB_LOCK_COST_AWARE_MIN_R': 76, 'V3_OB_LOCK_PULLBACK_RISK_BANK': 76}`
- Unresolved score statuses: `{'MISSING_REQUIRED_LIVE_METADATA': 608}`
- Backfill rule: Do not synthesize SOURCE_NOT_CAPTURED fields from later candles. Backfill only from original decision-time rows/files that contain the exact value.

## Null Field Health

- Allowed null counts: `{'account_truth_reconciliation_status.jsonl.asof_latest_candle_utc': 76, 'account_truth_reconciliation_status.jsonl.source_symbol': 76, 'account_truth_reconciliation_status.jsonl.trade_id': 70, 'candidate_ltf_path_order.jsonl.entry_first_touch_utc': 72, 'candidate_ltf_path_order.jsonl.sl_first_touch_utc': 75, 'candidate_ltf_path_order.jsonl.source_symbol': 76, 'candidate_ltf_path_order.jsonl.tp1_first_touch_utc': 56, 'candidate_ltf_path_order.jsonl.trade_id': 70, 'candidate_ltf_path_order.jsonl.mt5_read_error': 24, 'candidate_ltf_path_order.jsonl.terminal_event_r': 3, 'candidate_ltf_path_order.jsonl.terminal_event_utc': 3, 'candidate_path_follow.jsonl.mt5_read_error': 76, 'candidate_path_follow.jsonl.trade_id': 70, 'context_control_ledger.jsonl.regime': 76, 'context_control_ledger.jsonl.source_hash': 76, 'context_control_ledger.jsonl.source_symbol': 76, 'context_control_ledger.jsonl.trade_id': 70, 'databento_live_trigger_decisions.jsonl.asof_latest_candle_utc': 76, 'databento_live_trigger_decisions.jsonl.source_symbol': 76, 'databento_live_trigger_decisions.jsonl.trade_id': 70, 'fvg_ob_confluence.jsonl.lower_timeframe_available': 76, 'fvg_ob_confluence.jsonl.regime': 76, 'fvg_ob_confluence.jsonl.source_hash': 76, 'fvg_ob_confluence.jsonl.source_symbol': 76, 'fvg_ob_confluence.jsonl.touch_count': 76, 'fvg_ob_confluence.jsonl.trade_id': 70, 'fvg_ob_confluence_resolutions.jsonl.source_symbol': 76, 'fvg_ob_confluence_resolutions.jsonl.trade_id': 70, 'live_candidate_opportunity_clusters.jsonl.opportunity_entry_first_touch_utc': 72, 'live_candidate_opportunity_clusters.jsonl.opportunity_terminal_event_utc': 75, 'live_candidate_opportunity_clusters.jsonl.overlapping_active_symbol_opportunity_ids': 75, 'live_candidate_opportunity_clusters.jsonl.source_symbol': 76, 'live_candidate_opportunity_clusters.jsonl.trade_id': 70, 'live_candidate_strategy_rollups.jsonl.opportunity_entry_first_touch_utc': 72, 'live_candidate_strategy_rollups.jsonl.overlapping_active_symbol_opportunity_ids': 75, 'live_candidate_strategy_rollups.jsonl.source_symbol': 76, 'live_candidate_strategy_rollups.jsonl.trade_id': 70, 'live_structural_strategy_metadata.jsonl.asof_latest_candle_utc': 76, 'live_structural_strategy_metadata.jsonl.source_symbol': 76, 'live_structural_strategy_metadata.jsonl.trade_id': 70, 'missed_opportunity_shadow.jsonl.source_symbol': 76, 'missed_opportunity_shadow.jsonl.trade_id': 70, 'pending_limit_lifecycle_join_backfill.jsonl.source_symbol': 6, 'prefill_delivery_path.jsonl.fill_delay_seconds': 76, 'prefill_delivery_path.jsonl.fill_happened': 76, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_cancel': 76, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_fill': 76, 'prefill_delivery_path.jsonl.pre_fill_candles': 76, 'prefill_delivery_path.jsonl.pre_fill_ticks_summary': 76, 'prefill_delivery_path.jsonl.regime': 76, 'prefill_delivery_path.jsonl.reversal_leg_timing': 76, 'prefill_delivery_path.jsonl.source_hash': 76, 'prefill_delivery_path.jsonl.source_symbol': 76, 'prefill_delivery_path.jsonl.trade_id': 70, 'prefill_delivery_path_resolutions.jsonl.source_symbol': 76, 'prefill_delivery_path_resolutions.jsonl.trade_id': 70, 'sierra_confluence_source_status.jsonl.asof_latest_candle_utc': 76, 'sierra_confluence_source_status.jsonl.source_symbol': 76, 'sierra_confluence_source_status.jsonl.trade_id': 70, 'sierra_confluence_source_status.jsonl.sierra_futures_symbol': 3, 'sierra_confluence_source_status.jsonl.sierra_source_symbol': 3, 'sierra_depth_feature_snapshots.jsonl.depth_path': 3, 'sierra_depth_feature_snapshots.jsonl.sierra_futures_symbol': 3, 'sierra_depth_feature_snapshots.jsonl.sierra_source_symbol': 3, 'strategy_follow_candidates.jsonl.regime': 76, 'strategy_follow_candidates.jsonl.source_hash': 76, 'strategy_follow_candidates.jsonl.source_symbol': 76, 'strategy_follow_candidates.jsonl.trade_id': 70, 'v2b_forward_pair_resolutions.jsonl.source_symbol': 76, 'v2b_forward_pair_resolutions.jsonl.trade_id': 70, 'v2b_forward_pairs.jsonl.lower_timeframe_available': 76, 'v2b_forward_pairs.jsonl.regime': 76, 'v2b_forward_pairs.jsonl.source_hash': 76, 'v2b_forward_pairs.jsonl.source_symbol': 76, 'v2b_forward_pairs.jsonl.trade_id': 70, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_path_order_label': 112, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_event_utc': 10518, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_order_ambiguity': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_outcome_status': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.strategy_proxy_r': 291, 'live_mechanical_strategy_shadow_outcomes.jsonl.trade_id': 21904, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_candidate_id': 90}`
- Unexpected null counts: `{'candidate_ltf_path_order.jsonl.terminal_event_r': 52, 'candidate_ltf_path_order.jsonl.terminal_event_utc': 52, 'candidate_path_follow.jsonl.sl_first_touch_utc': 70, 'candidate_path_follow.jsonl.entry_first_touch_utc': 62, 'candidate_path_follow.jsonl.tp1_first_touch_utc': 7, 'sierra_depth_feature_snapshots.jsonl.depth_file_mtime_utc': 3, 'sierra_depth_feature_snapshots.jsonl.depth_file_size_bytes': 3, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_event_utc': 10, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_checked_candle_time_utc': 2}`
- Critical null counts: `{}`
- Allowed null policy: Allowed nulls are explicit non-decision or source-identity fields such as trade_id/source_symbol/regime/source_hash, plus point-in-time rows that intentionally have no asof_latest_candle_utc.

## Lane Expectations

- Row counts by mode: `{'candidate_driven_point_in_time': 849, 'candidate_driven_path_aligned': 13370, 'candidate_registry': 76, 'candidate_path_aligned_strategy_rows': 34900, 'source_driven_lifecycle_join': 189, 'event_waiting_exit_management': 0, 'approval_blocked_event_triggered_paid_data': 0, 'source_driven_readiness_status': 52, 'source_driven_preregistration_status': 36, 'source_driven_observer_hardening_status': 37}`
- Staleness policy: `{'candidate_registry': 'candidate rows are event/candidate driven and must have dependent coverage when present', 'candidate_driven_point_in_time': 'one latest row per candidate or explicit source/status blocker', 'candidate_driven_path_aligned': 'latest asof must align to candidate_path_follow when candidate paths advance', 'source_driven_lifecycle_join': 'freshness follows source lifecycle events, not wall-clock churn', 'source_driven_readiness_status': 'freshness follows upstream evidence signatures, not wall-clock churn', 'source_driven_preregistration_status': 'freshness follows preregistration/source-status signatures, not wall-clock churn', 'source_driven_observer_hardening_status': 'freshness follows observer source/status signatures and stale-status transitions', 'event_waiting_exit_management': 'empty is valid only with no filled trade/trigger status', 'approval_blocked_event_triggered_paid_data': 'no paid live rows until approved trigger policy is active'}`

## Issues

No cross-log data-health issues found. Documented limitations remain explicit and non-fabricated.
