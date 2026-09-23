# Live Shadow Data Health Audit - 2026-05-04

**Schema:** `live_shadow_data_health_audit_v1`
**Generated:** `2026-05-05T01:02:23.054163+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This read-only audit checks cross-log candidate coverage, identity consistency, latest path alignment, path-label geometry sanity, pending-lifecycle joins, mechanical strategy coverage, opportunity-level duplicate counting, Sierra/Databento confluence and source/feature interpretation, lane expectation modes, critical null/empty fields, and explicit source-capture limitations.

## Counts

- Latest candidates: `49`
- Logs inspected: `20`
- Raw rows inspected: `31617`
- Issues: `13`
- Candidate final outcomes: `{'REJECTED_L2': 30, 'LIMIT_PLACED': 3, 'REJECTED_GATE1_SAFETY': 16}`
- Latest path labels: `{'entry_touched_then_reached_tp1': 5, 'continued_without_entry_touch_to_tp_area': 38, 'entry_touched_tp_and_sl_m15_ambiguous': 2, 'went_through_entry_and_continued_to_sl': 3}`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 0 |
| `SERIOUS` | 13 |
| `MODERATE` | 0 |
| `LOW` | 0 |

## Coverage

| Log | Covered candidates | Missing | Asof mismatches |
|---|---:|---:|---:|
| `v2b_forward_pairs.jsonl` | 49 | 0 | 0 |
| `prefill_delivery_path.jsonl` | 49 | 0 | 0 |
| `fvg_ob_confluence.jsonl` | 49 | 0 | 0 |
| `context_control_ledger.jsonl` | 49 | 0 | 0 |
| `live_structural_strategy_metadata.jsonl` | 48 | 1 | 0 |
| `databento_live_trigger_decisions.jsonl` | 48 | 1 | 0 |
| `sierra_confluence_source_status.jsonl` | 48 | 1 | 0 |
| `sierra_depth_feature_snapshots.jsonl` | 48 | 1 | 0 |
| `account_truth_reconciliation_status.jsonl` | 48 | 1 | 0 |
| `candidate_path_follow.jsonl` | 48 | 1 | 0 |
| `live_candidate_opportunity_clusters.jsonl` | 48 | 1 | 0 |
| `live_candidate_strategy_rollups.jsonl` | 48 | 1 | 0 |
| `v2b_forward_pair_resolutions.jsonl` | 48 | 1 | 0 |
| `prefill_delivery_path_resolutions.jsonl` | 48 | 1 | 0 |
| `fvg_ob_confluence_resolutions.jsonl` | 48 | 1 | 0 |
| `missed_opportunity_shadow.jsonl` | 48 | 1 | 0 |
| `candidate_ltf_path_order.jsonl` | 48 | 1 | 0 |

## Opportunity Counting

- Status counts: `{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 7, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 39, 'BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP': 2}`
- Algorithm versions: `{'active_setup_lifecycle_tolerance_v1': 48}`
- Unique opportunity IDs: `9`

## All-Row Identity Health

- Candidate-scoped rows checked: `31608`
- Orphan dependent rows by log: `{}`
- Candidate identity variant conflicts: `{}`

## Mechanical Strategy Health

- Latest strategy row counts per candidate: `{16: 48}`
- Missing mechanical rows by candidate: `{}`
- Outcome mismatches: `[]`

## Path Geometry Health

- Checked latest path rows: `48`
- Mismatches: `[]`

## Pending Lifecycle Health

- LIMIT_PLACED candidates: `['XAUUSD_2026-05-04T07:15:00+00:00', 'NAS100_2026-05-04T07:15:00+00:00', 'GBPJPY_2026-05-04T03:00:00+00:00']`
- Missing lifecycle joins: `[]`
- Unexpected joins: `[]`
- Trade ID mismatches: `[]`

## Source / Feature Interpretation

- Mismatches: `[]`

## External Confluence

- Sierra statuses: `{'FEATURES_EXTRACTED': 21, 'NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL': 3, 'LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED': 25}`
- Databento statuses: `{'NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE': 49}`
- Paid fetch attempted count: `0`

## Trade Record Candidate Coverage

- Trade-record candidates seen: `49`
- Matched candidate shadow rows: `49`
- Missing candidate shadow rows: `[]`
- Value mismatches: `[]`

## Documented Limitations

- Source-not-captured fields: `{'cost_aware_min_r_fields': 48, 'fvg_lock_state': 48, 'post_lock_reentry_state': 48, 'standalone_fvg_entry_geometry': 48, 'structural_lock_event_time_price': 48, 'swing_protected_lock_level': 48}`
- Affected strategies: `{'FVG_OB_CONFLUENCE_OB_AFTER_FVG': 48, 'V2_STRUCT_COMPOSITE_ANY': 48, 'V2_STRUCT_FVG_MID_EDGE': 48, 'V2_STRUCT_SWING_PROTECTED': 48, 'V3_FVG_ONLY_RESCUE_RISK_BANK': 48, 'V3_FVG_THEN_OB_TAIL_RISK_BANK': 48, 'V3_OB_LOCK_COST_AWARE_MIN_R': 48, 'V3_OB_LOCK_PULLBACK_RISK_BANK': 48}`
- Unresolved score statuses: `{'MISSING_REQUIRED_LIVE_METADATA': 384}`
- Backfill rule: Do not synthesize SOURCE_NOT_CAPTURED fields from later candles. Backfill only from original decision-time rows/files that contain the exact value.

## Null Field Health

- Allowed null counts: `{'account_truth_reconciliation_status.jsonl.asof_latest_candle_utc': 48, 'account_truth_reconciliation_status.jsonl.source_symbol': 48, 'account_truth_reconciliation_status.jsonl.trade_id': 45, 'candidate_ltf_path_order.jsonl.mt5_read_error': 48, 'candidate_ltf_path_order.jsonl.sl_first_touch_utc': 43, 'candidate_ltf_path_order.jsonl.source_symbol': 48, 'candidate_ltf_path_order.jsonl.trade_id': 45, 'candidate_ltf_path_order.jsonl.entry_first_touch_utc': 38, 'candidate_ltf_path_order.jsonl.terminal_event_r': 1, 'candidate_ltf_path_order.jsonl.tp1_first_touch_utc': 3, 'candidate_path_follow.jsonl.mt5_read_error': 48, 'candidate_path_follow.jsonl.trade_id': 45, 'context_control_ledger.jsonl.regime': 49, 'context_control_ledger.jsonl.source_hash': 49, 'context_control_ledger.jsonl.source_symbol': 49, 'context_control_ledger.jsonl.trade_id': 46, 'databento_live_trigger_decisions.jsonl.asof_latest_candle_utc': 48, 'databento_live_trigger_decisions.jsonl.source_symbol': 48, 'databento_live_trigger_decisions.jsonl.trade_id': 45, 'fvg_ob_confluence.jsonl.lower_timeframe_available': 49, 'fvg_ob_confluence.jsonl.regime': 49, 'fvg_ob_confluence.jsonl.source_hash': 49, 'fvg_ob_confluence.jsonl.source_symbol': 49, 'fvg_ob_confluence.jsonl.touch_count': 49, 'fvg_ob_confluence.jsonl.trade_id': 46, 'fvg_ob_confluence_resolutions.jsonl.source_symbol': 48, 'fvg_ob_confluence_resolutions.jsonl.trade_id': 45, 'live_candidate_opportunity_clusters.jsonl.overlapping_active_symbol_opportunity_ids': 35, 'live_candidate_opportunity_clusters.jsonl.source_symbol': 48, 'live_candidate_opportunity_clusters.jsonl.trade_id': 45, 'live_candidate_opportunity_clusters.jsonl.opportunity_entry_first_touch_utc': 33, 'live_candidate_opportunity_clusters.jsonl.opportunity_terminal_event_utc': 34, 'live_candidate_strategy_rollups.jsonl.overlapping_active_symbol_opportunity_ids': 35, 'live_candidate_strategy_rollups.jsonl.source_symbol': 48, 'live_candidate_strategy_rollups.jsonl.trade_id': 45, 'live_candidate_strategy_rollups.jsonl.opportunity_entry_first_touch_utc': 33, 'live_structural_strategy_metadata.jsonl.asof_latest_candle_utc': 48, 'live_structural_strategy_metadata.jsonl.source_symbol': 48, 'live_structural_strategy_metadata.jsonl.trade_id': 45, 'missed_opportunity_shadow.jsonl.source_symbol': 48, 'missed_opportunity_shadow.jsonl.trade_id': 45, 'pending_limit_lifecycle_join_backfill.jsonl.source_symbol': 3, 'prefill_delivery_path.jsonl.fill_delay_seconds': 49, 'prefill_delivery_path.jsonl.fill_happened': 49, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_cancel': 49, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_fill': 49, 'prefill_delivery_path.jsonl.pre_fill_candles': 49, 'prefill_delivery_path.jsonl.pre_fill_ticks_summary': 49, 'prefill_delivery_path.jsonl.regime': 49, 'prefill_delivery_path.jsonl.reversal_leg_timing': 49, 'prefill_delivery_path.jsonl.source_hash': 49, 'prefill_delivery_path.jsonl.source_symbol': 49, 'prefill_delivery_path.jsonl.trade_id': 46, 'prefill_delivery_path_resolutions.jsonl.source_symbol': 48, 'prefill_delivery_path_resolutions.jsonl.trade_id': 45, 'sierra_confluence_source_status.jsonl.asof_latest_candle_utc': 48, 'sierra_confluence_source_status.jsonl.source_symbol': 48, 'sierra_confluence_source_status.jsonl.trade_id': 45, 'sierra_confluence_source_status.jsonl.sierra_futures_symbol': 3, 'sierra_confluence_source_status.jsonl.sierra_source_symbol': 3, 'sierra_depth_feature_snapshots.jsonl.depth_path': 3, 'sierra_depth_feature_snapshots.jsonl.sierra_futures_symbol': 3, 'sierra_depth_feature_snapshots.jsonl.sierra_source_symbol': 3, 'strategy_follow_candidates.jsonl.regime': 49, 'strategy_follow_candidates.jsonl.source_hash': 49, 'strategy_follow_candidates.jsonl.source_symbol': 49, 'strategy_follow_candidates.jsonl.trade_id': 46, 'v2b_forward_pair_resolutions.jsonl.source_symbol': 48, 'v2b_forward_pair_resolutions.jsonl.trade_id': 45, 'v2b_forward_pairs.jsonl.lower_timeframe_available': 49, 'v2b_forward_pairs.jsonl.regime': 49, 'v2b_forward_pairs.jsonl.source_hash': 49, 'v2b_forward_pairs.jsonl.source_symbol': 49, 'v2b_forward_pairs.jsonl.trade_id': 46, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_path_order_label': 112, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_event_utc': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_order_ambiguity': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_outcome_status': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.strategy_proxy_r': 186, 'live_mechanical_strategy_shadow_outcomes.jsonl.trade_id': 13392, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_candidate_id': 86}`
- Unexpected null counts: `{'sierra_depth_feature_snapshots.jsonl.depth_file_mtime_utc': 3, 'sierra_depth_feature_snapshots.jsonl.depth_file_size_bytes': 3}`
- Critical null counts: `{}`
- Allowed null policy: Allowed nulls are explicit non-decision or source-identity fields such as trade_id/source_symbol/regime/source_hash, plus point-in-time rows that intentionally have no asof_latest_candle_utc.

## Lane Expectations

- Row counts by mode: `{'candidate_driven_point_in_time': 547, 'candidate_driven_path_aligned': 7271, 'candidate_registry': 49, 'candidate_path_aligned_strategy_rows': 23642, 'source_driven_lifecycle_join': 108, 'event_waiting_exit_management': 0, 'approval_blocked_event_triggered_paid_data': 0, 'approval_blocked_target_refresh': 0}`
- Staleness policy: `{'candidate_registry': 'candidate rows are event/candidate driven and must have dependent coverage when present', 'candidate_driven_point_in_time': 'one latest row per candidate or explicit source/status blocker', 'candidate_driven_path_aligned': 'latest asof must align to candidate_path_follow when candidate paths advance', 'source_driven_lifecycle_join': 'freshness follows source lifecycle events, not wall-clock churn', 'event_waiting_exit_management': 'empty is valid only with no filled trade/trigger status', 'approval_blocked_event_triggered_paid_data': 'no paid live rows until approved trigger policy is active', 'approval_blocked_target_refresh': 'no inference rows until target refresh and owner approval'}`

## Issues

| Severity | Code | Log | Candidate | Message |
|---|---|---|---|---|
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_structural_strategy_metadata.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `databento_live_trigger_decisions.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `sierra_confluence_source_status.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `sierra_depth_feature_snapshots.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `account_truth_reconciliation_status.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `candidate_path_follow.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_candidate_opportunity_clusters.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `live_candidate_strategy_rollups.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `v2b_forward_pair_resolutions.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `prefill_delivery_path_resolutions.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `fvg_ob_confluence_resolutions.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `missed_opportunity_shadow.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
| `SERIOUS` | `MISSING_CANDIDATE_COVERAGE` | `candidate_ltf_path_order.jsonl` | `USDJPY_2026-05-05T00:45:00+00:00` | candidate has no latest row in dependent shadow log |
