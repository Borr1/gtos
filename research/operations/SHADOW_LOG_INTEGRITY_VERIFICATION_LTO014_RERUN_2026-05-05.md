# Shadow Log Integrity Verification - 2026-05-04

**Schema:** `shadow_log_integrity_verification_v1`
**Generated:** `2026-05-05T01:09:11.737439+00:00`
**Overall status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

- JSONL files inspected: `70`
- JSONL rows inspected: `57648`
- Known-schema JSONL files: `47`
- CSV shadow files inspected: `4`
- Documented waiting lanes: `4`
- Candidate/MSO join health: `OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS`
- Candidate registry audit health: `OK_WITH_DOCUMENTED_REGISTRY_LIMITATIONS`
- Candidate path contract health: `OK_WITH_DOCUMENTED_PATH_LIMITATIONS`
- Opportunity lifecycle audit health: `ACTION_REQUIRED`
- Pending-limit lifecycle audit health: `OK_WITH_DOCUMENTED_PENDING_LIFECYCLE_LIMITATIONS`
- V2b forward-pair resolution audit health: `OK_WITH_DOCUMENTED_V2B_LIMITATIONS`
- Pre-fill delivery path audit health: `OK_WITH_DOCUMENTED_PREFILL_LIMITATIONS`
- FVG/OB confluence audit health: `OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS`
- Context/control audit health: `OK_WITH_DOCUMENTED_CONTEXT_CONTROL_LIMITATIONS`
- Broker actual-R audit health: `OK_WITH_DOCUMENTED_ACCOUNTING_LIMITATIONS`
- Account/PnL truth health: `OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS`
- Trade-index lifecycle health: `ACTION_REQUIRED`
- Issues: `49`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 0 |
| `SERIOUS` | 49 |
| `MODERATE` | 0 |
| `LOW` | 0 |

## Known Forward/Shadow Logs

| Log | Rows | Latest UTC | Schemas | Status |
|---|---:|---|---|---|
| `account_pnl_truth_reconciliation.jsonl` | 15 | `2026-05-04T22:58:26.680526+00:00` | `{'account_pnl_truth_reconciliation_v1': 15}` | `OK` |
| `account_truth_reconciliation_status.jsonl` | 49 | `2026-05-05T01:03:08.317118+00:00` | `{'account_truth_reconciliation_status_v1': 49}` | `OK` |
| `broker_actual_r_audit.jsonl` | 56 | `2026-05-05T01:07:32.203605+00:00` | `{'broker_actual_r_audit_v1': 56}` | `OK` |
| `candidate_ltf_path_order.jsonl` | 958 | `2026-05-05T01:02:55.428276+00:00` | `{'candidate_ltf_path_order_v1': 958}` | `OK` |
| `candidate_mso_snapshot_joins.jsonl` | 49 | `2026-05-05T01:05:40.755092+00:00` | `{'candidate_mso_snapshot_join_v1': 49}` | `OK` |
| `candidate_path_contract_audit.jsonl` | 77 | `2026-05-05T01:03:17.640055+00:00` | `{'candidate_path_contract_audit_v1': 77}` | `OK` |
| `candidate_path_follow.jsonl` | 954 | `2026-05-05T01:02:55.052894+00:00` | `{'candidate_path_follow_v1': 954}` | `OK` |
| `candidate_registry_audit.jsonl` | 49 | `2026-05-05T01:05:40.953706+00:00` | `{'candidate_registry_audit_v1': 49}` | `OK` |
| `context_control_audit.jsonl` | 77 | `2026-05-05T01:07:32.010620+00:00` | `{'context_control_audit_v1': 77}` | `OK` |
| `context_control_ledger.jsonl` | 49 | `2026-05-05T00:45:25.844667+00:00` | `{'context_control_forward_v1': 49}` | `OK` |
| `d1_bias_lag.jsonl` | 372 | `None` | `{}` | `OK` |
| `d1_bias_lag_recovery.jsonl` | 3 | `2026-05-04T08:03:31.297974+00:00` | `{'d1_bias_lag_recovery_v1': 3}` | `OK` |
| `databento_live_budget_ledger.jsonl` | 4 | `2026-05-04T23:37:15.740424+00:00` | `{'databento_live_budget_ledger_v1': 4}` | `OK` |
| `databento_live_confluence.jsonl` | 3 | `2026-05-04T23:37:15.739771+00:00` | `{'databento_live_confluence_v1': 3}` | `OK` |
| `databento_live_trigger_decisions.jsonl` | 70 | `2026-05-05T01:03:04.904221+00:00` | `{'databento_live_trigger_decision_v1': 70}` | `OK` |
| `external_source_blocker_status.jsonl` | 186 | `2026-05-05T01:03:08.343293+00:00` | `{'external_source_blocker_status_v1': 186}` | `OK` |
| `fvg_ob_confluence.jsonl` | 49 | `2026-05-05T00:45:25.843377+00:00` | `{'fvg_ob_confluence_forward_v1': 49}` | `OK` |
| `fvg_ob_confluence_audit.jsonl` | 97 | `2026-05-05T01:07:22.065225+00:00` | `{'fvg_ob_confluence_audit_v1': 97}` | `OK` |
| `fvg_ob_confluence_resolutions.jsonl` | 958 | `2026-05-05T01:03:01.396090+00:00` | `{'fvg_ob_confluence_resolution_v1': 958}` | `OK` |
| `gbpjpy_proxy_gap_status.jsonl` | 9 | `2026-05-05T01:08:23.488652+00:00` | `{'gbpjpy_orderflow_proxy_gap_status_v1': 9}` | `OK` |
| `live_candidate_opportunity_clusters.jsonl` | 833 | `2026-05-05T01:03:03.671688+00:00` | `{'live_candidate_opportunity_cluster_v1': 833}` | `OK` |
| `live_candidate_strategy_rollups.jsonl` | 1019 | `2026-05-05T01:03:05.171416+00:00` | `{'live_candidate_strategy_rollup_v1': 1019}` | `OK` |
| `live_mechanical_strategy_shadow_outcomes.jsonl` | 24426 | `2026-05-05T01:02:58.074721+00:00` | `{'live_mechanical_strategy_shadow_outcome_v1': 24426}` | `OK` |
| `live_structural_strategy_metadata.jsonl` | 49 | `2026-05-05T01:02:58.728248+00:00` | `{'live_structural_strategy_metadata_v1': 49}` | `OK` |
| `missed_opportunity_shadow.jsonl` | 958 | `2026-05-05T01:03:02.644592+00:00` | `{'missed_opportunity_shadow_v1': 958}` | `OK` |
| `ml_shadow_status.jsonl` | 31 | `2026-05-05T01:03:08.343249+00:00` | `{'ml_shadow_status_v1': 31}` | `OK` |
| `nas100_orderflow_adverse_selection_status.jsonl` | 2 | `2026-05-05T01:07:48.691130+00:00` | `{'nas100_orderflow_adverse_selection_status_v1': 2}` | `OK` |
| `opportunity_lifecycle_audit.jsonl` | 77 | `2026-05-05T01:05:41.052963+00:00` | `{'opportunity_lifecycle_audit_v1': 77}` | `ISSUES` |
| `pending_limit_lifecycle.jsonl` | 62 | `2026-05-05T00:00:05.158160+00:00` | `{'pending_limit_lifecycle_v1': 62}` | `OK` |
| `pending_limit_lifecycle_audit.jsonl` | 41 | `2026-05-05T01:05:41.142830+00:00` | `{'pending_limit_lifecycle_audit_v1': 41}` | `OK` |
| `pending_limit_lifecycle_join_backfill.jsonl` | 110 | `2026-05-05T01:02:58.633768+00:00` | `{'pending_limit_lifecycle_join_backfill_v1': 110}` | `OK` |
| `prefill_delivery_path.jsonl` | 49 | `2026-05-05T00:45:25.841096+00:00` | `{'prefill_delivery_path_v1': 49}` | `OK` |
| `prefill_delivery_path_audit.jsonl` | 97 | `2026-05-05T01:07:22.141066+00:00` | `{'prefill_delivery_path_audit_v1': 97}` | `OK` |
| `prefill_delivery_path_resolutions.jsonl` | 989 | `2026-05-05T01:03:00.094160+00:00` | `{'prefill_delivery_path_resolution_v1': 989}` | `OK` |
| `proxy_blocker_status.jsonl` | 31 | `2026-05-05T01:03:08.343221+00:00` | `{'proxy_blocker_status_v1': 31}` | `OK` |
| `shadow_observer_status.jsonl` | 455 | `2026-05-05T01:05:23.444456+00:00` | `{'shadow_observer_status_v1': 455}` | `OK` |
| `shadow_observer_tick_enrichment.jsonl` | 31 | `2026-05-04T15:17:06.433237+00:00` | `{'shadow_observer_tick_enrichment_v1': 31}` | `OK` |
| `sierra_confluence_source_status.jsonl` | 49 | `2026-05-05T01:03:05.141348+00:00` | `{'sierra_confluence_source_status_v1': 49}` | `OK` |
| `sierra_depth_enrichment_status.jsonl` | 3 | `2026-05-05T01:07:48.834636+00:00` | `{'sierra_depth_enrichment_status_v1': 3}` | `OK` |
| `sierra_depth_feature_snapshots.jsonl` | 160 | `2026-05-05T01:07:42.372036+00:00` | `{'sierra_depth_feature_snapshot_v1': 160}` | `OK` |
| `sierra_proxy_registry_status.jsonl` | 97 | `2026-05-05T01:07:32.411777+00:00` | `{'sierra_proxy_registry_status_v1': 97}` | `OK` |
| `strategy_follow_candidates.jsonl` | 49 | `2026-05-05T00:45:25.835815+00:00` | `{'strategy_follow_candidate_v1': 49}` | `OK` |
| `strategy_follow_evaluations.jsonl` | 316 | `2026-05-05T01:00:05.551024+00:00` | `{'strategy_follow_evaluation_v1': 316}` | `OK` |
| `trade_index_lifecycle_audit.jsonl` | 313 | `2026-05-05T01:03:18.049125+00:00` | `{'trade_index_lifecycle_audit_v1': 313}` | `ISSUES` |
| `v2b_forward_pair_resolution_audit.jsonl` | 97 | `2026-05-05T01:07:21.939742+00:00` | `{'v2b_forward_pair_resolution_audit_v1': 97}` | `OK` |
| `v2b_forward_pair_resolutions.jsonl` | 958 | `2026-05-05T01:02:58.773514+00:00` | `{'v2b_forward_pair_resolution_v1': 958}` | `OK` |
| `v2b_forward_pairs.jsonl` | 49 | `2026-05-05T00:45:25.838280+00:00` | `{'v2b_forward_pair_v1': 49}` | `OK` |

## Documented Waiting Lanes

| Log | Reason |
|---|---|
| `be_shadow_log.jsonl` | event-driven exit trigger; waits for filled trade BE condition |
| `ml_shadow_predictions.jsonl` | approval/target-refresh blocked |
| `partial_close_shadow_log.jsonl` | event-driven exit trigger; waits for filled trade TP/partial condition |
| `time_in_trade.jsonl` | event-driven exit close/management trigger |

## Issues

| Severity | Code | Path | Line | Message |
|---|---|---|---:|---|
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 1 | candidate XAGUSD_2026-05-04T07:15:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 4 | candidate XAGUSD_2026-05-04T07:30:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 5 | candidate XAGUSD_2026-05-04T07:45:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 6 | candidate XAGUSD_2026-05-04T08:00:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 7 | candidate XAGUSD_2026-05-04T08:15:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 8 | candidate XAGUSD_2026-05-04T08:30:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 9 | candidate XAGUSD_2026-05-04T08:45:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 10 | candidate XAGUSD_2026-05-04T09:00:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 11 | candidate XAGUSD_2026-05-04T09:15:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 12 | candidate XAGUSD_2026-05-04T09:30:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` | 21 | candidate GBPJPY_2026-05-04T03:00:00+00:00 lifecycle action codes are stale: stored=[] current=['OPPORTUNITY_CLUSTER_MISMATCH'] |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-14T15:30:05.012815+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-14T01:15:05.006410+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-15T13:15:57.164919+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-15T00:30:05.011237+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-16T00:16:00.503237+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-22T08:00:05.028587+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-23T07:16:14.138817+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPJPY_2026-04-28T09:00:05.010558+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-14T07:30:05.011677+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-14T14:00:57.743957+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-15T07:30:05.010905+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-15T13:16:01.327115+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-17T08:00:59.541491+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-17T14:15:05.012317+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-20T07:45:05.020140+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-20T15:31:14.730975+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-21T11:30:05.011826+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | GBPUSD_2026-04-22T07:16:12.155934+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | NAS100_2026-04-29T15:00:05.012307+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | NAS100_2026-05-01T08:15:00+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | US30_cash_2026-04-14T08:16:00.983581+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | US30_cash_2026-04-16T13:45:56.810509+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-15T13:15:57.398922+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-15T02:45:05.009485+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-16T15:00:05.011292+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-21T13:45:05.018194+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-22T15:15:05.016051+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-22T00:30:05.018068+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-23T08:45:05.012266+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-04-24T00:16:10.771453+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAGUSD_2026-05-01T08:30:00+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAUUSD_2026-04-15T14:15:05.007998+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAUUSD_2026-04-16T09:30:05.013547+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAUUSD_2026-04-16T13:16:01.126537+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAUUSD_2026-04-17T13:30:05.007149+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAUUSD_2026-05-01T08:15:00+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | XAUUSD_2026-05-01T15:45:00+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_RECORD_INVENTORY_INDEX_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\index\trade_record_inventory_index_2026-05-05.json` |  | inventory index fields are stale: ['by_lifecycle_completeness', 'by_trade_index_lifecycle_status'] |

## Notes

- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, and shadow-observer safety flags.
- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.
