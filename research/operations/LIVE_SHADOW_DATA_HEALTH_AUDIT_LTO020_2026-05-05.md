# Live Shadow Data Health Audit - 2026-05-04

**Schema:** `live_shadow_data_health_audit_v1`
**Generated:** `2026-05-05T04:26:12.194124+00:00`
**Status:** `OK_WITH_DOCUMENTED_LIMITATIONS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This read-only audit checks cross-log candidate coverage, identity consistency, latest path alignment, path-label geometry sanity, pending-lifecycle joins, mechanical strategy coverage, opportunity-level duplicate counting, Sierra/Databento confluence and source/feature interpretation, lane expectation modes, critical null/empty fields, and explicit source-capture limitations.

## Counts

- Latest candidates: `49`
- Logs inspected: `20`
- Raw rows inspected: `33557`
- Issues: `0`
- Candidate final outcomes: `{'REJECTED_L2': 30, 'LIMIT_PLACED': 3, 'REJECTED_GATE1_SAFETY': 16}`
- Latest path labels: `{'entry_touched_then_reached_tp1': 5, 'continued_without_entry_touch_to_tp_area': 39, 'entry_touched_tp_and_sl_m15_ambiguous': 2, 'went_through_entry_and_continued_to_sl': 3}`

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
| `v2b_forward_pairs.jsonl` | 49 | 0 | 0 |
| `prefill_delivery_path.jsonl` | 49 | 0 | 0 |
| `fvg_ob_confluence.jsonl` | 49 | 0 | 0 |
| `context_control_ledger.jsonl` | 49 | 0 | 0 |
| `live_structural_strategy_metadata.jsonl` | 49 | 0 | 0 |
| `databento_live_trigger_decisions.jsonl` | 49 | 0 | 0 |
| `sierra_confluence_source_status.jsonl` | 49 | 0 | 0 |
| `sierra_depth_feature_snapshots.jsonl` | 49 | 0 | 0 |
| `account_truth_reconciliation_status.jsonl` | 49 | 0 | 0 |
| `candidate_path_follow.jsonl` | 49 | 0 | 0 |
| `live_candidate_opportunity_clusters.jsonl` | 49 | 0 | 0 |
| `live_candidate_strategy_rollups.jsonl` | 49 | 0 | 0 |
| `v2b_forward_pair_resolutions.jsonl` | 49 | 0 | 0 |
| `prefill_delivery_path_resolutions.jsonl` | 49 | 0 | 0 |
| `fvg_ob_confluence_resolutions.jsonl` | 49 | 0 | 0 |
| `missed_opportunity_shadow.jsonl` | 49 | 0 | 0 |
| `candidate_ltf_path_order.jsonl` | 49 | 0 | 0 |

## Opportunity Counting

- Status counts: `{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 9, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 40}`
- Algorithm versions: `{'active_setup_lifecycle_tolerance_v1': 49}`
- Unique opportunity IDs: `9`

## All-Row Identity Health

- Candidate-scoped rows checked: `33548`
- Orphan dependent rows by log: `{}`
- Candidate identity variant conflicts: `{}`

## Mechanical Strategy Health

- Latest strategy row counts per candidate: `{16: 49}`
- Missing mechanical rows by candidate: `{}`
- Outcome mismatches: `[]`

## Path Geometry Health

- Checked latest path rows: `49`
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

- Source-not-captured fields: `{'cost_aware_min_r_fields': 49, 'fvg_lock_state': 49, 'post_lock_reentry_state': 49, 'standalone_fvg_entry_geometry': 49, 'structural_lock_event_time_price': 49, 'swing_protected_lock_level': 49}`
- Affected strategies: `{'FVG_OB_CONFLUENCE_OB_AFTER_FVG': 49, 'V2_STRUCT_COMPOSITE_ANY': 49, 'V2_STRUCT_FVG_MID_EDGE': 49, 'V2_STRUCT_SWING_PROTECTED': 49, 'V3_FVG_ONLY_RESCUE_RISK_BANK': 49, 'V3_FVG_THEN_OB_TAIL_RISK_BANK': 49, 'V3_OB_LOCK_COST_AWARE_MIN_R': 49, 'V3_OB_LOCK_PULLBACK_RISK_BANK': 49}`
- Unresolved score statuses: `{'MISSING_REQUIRED_LIVE_METADATA': 392}`
- Backfill rule: Do not synthesize SOURCE_NOT_CAPTURED fields from later candles. Backfill only from original decision-time rows/files that contain the exact value.

## Null Field Health

- Allowed null counts: `{'account_truth_reconciliation_status.jsonl.asof_latest_candle_utc': 49, 'account_truth_reconciliation_status.jsonl.source_symbol': 49, 'account_truth_reconciliation_status.jsonl.trade_id': 46, 'candidate_ltf_path_order.jsonl.entry_first_touch_utc': 49, 'candidate_ltf_path_order.jsonl.sl_first_touch_utc': 49, 'candidate_ltf_path_order.jsonl.source_symbol': 49, 'candidate_ltf_path_order.jsonl.tp1_first_touch_utc': 31, 'candidate_ltf_path_order.jsonl.trade_id': 46, 'candidate_ltf_path_order.jsonl.mt5_read_error': 18, 'candidate_path_follow.jsonl.mt5_read_error': 49, 'candidate_path_follow.jsonl.trade_id': 46, 'context_control_ledger.jsonl.regime': 49, 'context_control_ledger.jsonl.source_hash': 49, 'context_control_ledger.jsonl.source_symbol': 49, 'context_control_ledger.jsonl.trade_id': 46, 'databento_live_trigger_decisions.jsonl.asof_latest_candle_utc': 49, 'databento_live_trigger_decisions.jsonl.source_symbol': 49, 'databento_live_trigger_decisions.jsonl.trade_id': 46, 'fvg_ob_confluence.jsonl.lower_timeframe_available': 49, 'fvg_ob_confluence.jsonl.regime': 49, 'fvg_ob_confluence.jsonl.source_hash': 49, 'fvg_ob_confluence.jsonl.source_symbol': 49, 'fvg_ob_confluence.jsonl.touch_count': 49, 'fvg_ob_confluence.jsonl.trade_id': 46, 'fvg_ob_confluence_resolutions.jsonl.source_symbol': 49, 'fvg_ob_confluence_resolutions.jsonl.trade_id': 46, 'live_candidate_opportunity_clusters.jsonl.opportunity_entry_first_touch_utc': 49, 'live_candidate_opportunity_clusters.jsonl.opportunity_terminal_event_utc': 49, 'live_candidate_opportunity_clusters.jsonl.overlapping_active_symbol_opportunity_ids': 49, 'live_candidate_opportunity_clusters.jsonl.source_symbol': 49, 'live_candidate_opportunity_clusters.jsonl.trade_id': 46, 'live_candidate_strategy_rollups.jsonl.opportunity_entry_first_touch_utc': 49, 'live_candidate_strategy_rollups.jsonl.overlapping_active_symbol_opportunity_ids': 49, 'live_candidate_strategy_rollups.jsonl.source_symbol': 49, 'live_candidate_strategy_rollups.jsonl.trade_id': 46, 'live_structural_strategy_metadata.jsonl.asof_latest_candle_utc': 49, 'live_structural_strategy_metadata.jsonl.source_symbol': 49, 'live_structural_strategy_metadata.jsonl.trade_id': 46, 'missed_opportunity_shadow.jsonl.source_symbol': 49, 'missed_opportunity_shadow.jsonl.trade_id': 46, 'pending_limit_lifecycle_join_backfill.jsonl.source_symbol': 3, 'prefill_delivery_path.jsonl.fill_delay_seconds': 49, 'prefill_delivery_path.jsonl.fill_happened': 49, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_cancel': 49, 'prefill_delivery_path.jsonl.fvg_ob_swing_state_at_fill': 49, 'prefill_delivery_path.jsonl.pre_fill_candles': 49, 'prefill_delivery_path.jsonl.pre_fill_ticks_summary': 49, 'prefill_delivery_path.jsonl.regime': 49, 'prefill_delivery_path.jsonl.reversal_leg_timing': 49, 'prefill_delivery_path.jsonl.source_hash': 49, 'prefill_delivery_path.jsonl.source_symbol': 49, 'prefill_delivery_path.jsonl.trade_id': 46, 'prefill_delivery_path_resolutions.jsonl.source_symbol': 49, 'prefill_delivery_path_resolutions.jsonl.trade_id': 46, 'sierra_confluence_source_status.jsonl.asof_latest_candle_utc': 49, 'sierra_confluence_source_status.jsonl.source_symbol': 49, 'sierra_confluence_source_status.jsonl.trade_id': 46, 'sierra_confluence_source_status.jsonl.sierra_futures_symbol': 3, 'sierra_confluence_source_status.jsonl.sierra_source_symbol': 3, 'sierra_depth_feature_snapshots.jsonl.depth_path': 3, 'sierra_depth_feature_snapshots.jsonl.sierra_futures_symbol': 3, 'sierra_depth_feature_snapshots.jsonl.sierra_source_symbol': 3, 'strategy_follow_candidates.jsonl.regime': 49, 'strategy_follow_candidates.jsonl.source_hash': 49, 'strategy_follow_candidates.jsonl.source_symbol': 49, 'strategy_follow_candidates.jsonl.trade_id': 46, 'v2b_forward_pair_resolutions.jsonl.source_symbol': 49, 'v2b_forward_pair_resolutions.jsonl.trade_id': 46, 'v2b_forward_pairs.jsonl.lower_timeframe_available': 49, 'v2b_forward_pairs.jsonl.regime': 49, 'v2b_forward_pairs.jsonl.source_hash': 49, 'v2b_forward_pairs.jsonl.source_symbol': 49, 'v2b_forward_pairs.jsonl.trade_id': 46, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_path_order_label': 112, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_event_utc': 8859, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_order_ambiguity': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_outcome_status': 8368, 'live_mechanical_strategy_shadow_outcomes.jsonl.strategy_proxy_r': 189, 'live_mechanical_strategy_shadow_outcomes.jsonl.trade_id': 14144, 'live_mechanical_strategy_shadow_outcomes.jsonl.pending_lifecycle_candidate_id': 86}`
- Unexpected null counts: `{'candidate_ltf_path_order.jsonl.terminal_event_r': 31, 'candidate_ltf_path_order.jsonl.terminal_event_utc': 31, 'candidate_path_follow.jsonl.entry_first_touch_utc': 29, 'candidate_path_follow.jsonl.sl_first_touch_utc': 29, 'sierra_depth_feature_snapshots.jsonl.depth_file_mtime_utc': 3, 'sierra_depth_feature_snapshots.jsonl.depth_file_size_bytes': 3, 'live_mechanical_strategy_shadow_outcomes.jsonl.ltf_terminal_event_utc': 5}`
- Critical null counts: `{}`
- Allowed null policy: Allowed nulls are explicit non-decision or source-identity fields such as trade_id/source_symbol/regime/source_hash, plus point-in-time rows that intentionally have no asof_latest_candle_utc.

## Lane Expectations

- Row counts by mode: `{'candidate_driven_point_in_time': 573, 'candidate_driven_path_aligned': 7935, 'candidate_registry': 49, 'candidate_path_aligned_strategy_rows': 24890, 'source_driven_lifecycle_join': 110, 'event_waiting_exit_management': 0, 'approval_blocked_event_triggered_paid_data': 0, 'target_refresh_approved_pending_ml_shadow': 0}`
- Staleness policy: `{'candidate_registry': 'candidate rows are event/candidate driven and must have dependent coverage when present', 'candidate_driven_point_in_time': 'one latest row per candidate or explicit source/status blocker', 'candidate_driven_path_aligned': 'latest asof must align to candidate_path_follow when candidate paths advance', 'source_driven_lifecycle_join': 'freshness follows source lifecycle events, not wall-clock churn', 'event_waiting_exit_management': 'empty is valid only with no filled trade/trigger status', 'approval_blocked_event_triggered_paid_data': 'no paid live rows until approved trigger policy is active', 'target_refresh_approved_pending_ml_shadow': 'no inference rows until target refresh, feature bundle, model artifact, and tests are ready'}`

## Issues

No cross-log data-health issues found. Documented limitations remain explicit and non-fabricated.
