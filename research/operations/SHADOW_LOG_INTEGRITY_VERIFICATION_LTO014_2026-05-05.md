# Shadow Log Integrity Verification - 2026-05-04

**Schema:** `shadow_log_integrity_verification_v1`
**Generated:** `2026-05-05T01:02:21.639956+00:00`
**Overall status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

- JSONL files inspected: `70`
- JSONL rows inspected: `56137`
- Known-schema JSONL files: `47`
- CSV shadow files inspected: `4`
- Documented waiting lanes: `4`
- Candidate/MSO join health: `OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS`
- Candidate registry audit health: `ACTION_REQUIRED`
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
- Issues: `16`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 0 |
| `SERIOUS` | 4 |
| `MODERATE` | 12 |
| `LOW` | 0 |

## Known Forward/Shadow Logs

| Log | Rows | Latest UTC | Schemas | Status |
|---|---:|---|---|---|
| `account_pnl_truth_reconciliation.jsonl` | 15 | `2026-05-04T22:58:26.680526+00:00` | `{'account_pnl_truth_reconciliation_v1': 15}` | `OK` |
| `account_truth_reconciliation_status.jsonl` | 48 | `2026-05-04T17:02:55.635818+00:00` | `{'account_truth_reconciliation_status_v1': 48}` | `OK` |
| `broker_actual_r_audit.jsonl` | 55 | `2026-05-04T22:39:31.201170+00:00` | `{'broker_actual_r_audit_v1': 55}` | `OK` |
| `candidate_ltf_path_order.jsonl` | 909 | `2026-05-04T19:01:52.826638+00:00` | `{'candidate_ltf_path_order_v1': 909}` | `ISSUES` |
| `candidate_mso_snapshot_joins.jsonl` | 48 | `2026-05-04T20:16:05.307427+00:00` | `{'candidate_mso_snapshot_join_v1': 48}` | `OK` |
| `candidate_path_contract_audit.jsonl` | 48 | `2026-05-04T20:36:48.454770+00:00` | `{'candidate_path_contract_audit_v1': 48}` | `OK` |
| `candidate_path_follow.jsonl` | 925 | `2026-05-04T19:01:52.370329+00:00` | `{'candidate_path_follow_v1': 925}` | `ISSUES` |
| `candidate_registry_audit.jsonl` | 48 | `2026-05-04T20:27:46.937586+00:00` | `{'candidate_registry_audit_v1': 48}` | `ISSUES` |
| `context_control_audit.jsonl` | 48 | `2026-05-04T22:14:53.057473+00:00` | `{'context_control_audit_v1': 48}` | `OK` |
| `context_control_ledger.jsonl` | 49 | `2026-05-05T00:45:25.844667+00:00` | `{'context_control_forward_v1': 49}` | `OK` |
| `d1_bias_lag.jsonl` | 372 | `None` | `{}` | `OK` |
| `d1_bias_lag_recovery.jsonl` | 3 | `2026-05-04T08:03:31.297974+00:00` | `{'d1_bias_lag_recovery_v1': 3}` | `OK` |
| `databento_live_budget_ledger.jsonl` | 4 | `2026-05-04T23:37:15.740424+00:00` | `{'databento_live_budget_ledger_v1': 4}` | `OK` |
| `databento_live_confluence.jsonl` | 3 | `2026-05-04T23:37:15.739771+00:00` | `{'databento_live_confluence_v1': 3}` | `OK` |
| `databento_live_trigger_decisions.jsonl` | 48 | `2026-05-04T17:02:52.945371+00:00` | `{'databento_live_trigger_decision_v1': 48}` | `OK` |
| `external_source_blocker_status.jsonl` | 180 | `2026-05-04T19:02:05.222639+00:00` | `{'external_source_blocker_status_v1': 180}` | `ISSUES` |
| `fvg_ob_confluence.jsonl` | 49 | `2026-05-05T00:45:25.843377+00:00` | `{'fvg_ob_confluence_forward_v1': 49}` | `OK` |
| `fvg_ob_confluence_audit.jsonl` | 48 | `2026-05-04T22:00:03.094277+00:00` | `{'fvg_ob_confluence_audit_v1': 48}` | `OK` |
| `fvg_ob_confluence_resolutions.jsonl` | 909 | `2026-05-04T19:01:58.701418+00:00` | `{'fvg_ob_confluence_resolution_v1': 909}` | `ISSUES` |
| `gbpjpy_proxy_gap_status.jsonl` | 3 | `2026-05-05T01:01:04.533642+00:00` | `{'gbpjpy_orderflow_proxy_gap_status_v1': 3}` | `OK` |
| `live_candidate_opportunity_clusters.jsonl` | 800 | `2026-05-04T19:02:00.883339+00:00` | `{'live_candidate_opportunity_cluster_v1': 800}` | `ISSUES` |
| `live_candidate_strategy_rollups.jsonl` | 970 | `2026-05-04T19:02:02.256696+00:00` | `{'live_candidate_strategy_rollup_v1': 970}` | `ISSUES` |
| `live_mechanical_strategy_shadow_outcomes.jsonl` | 23642 | `2026-05-04T19:01:55.399693+00:00` | `{'live_mechanical_strategy_shadow_outcome_v1': 23642}` | `ISSUES` |
| `live_structural_strategy_metadata.jsonl` | 48 | `2026-05-04T17:02:47.806500+00:00` | `{'live_structural_strategy_metadata_v1': 48}` | `OK` |
| `missed_opportunity_shadow.jsonl` | 909 | `2026-05-04T19:01:59.885459+00:00` | `{'missed_opportunity_shadow_v1': 909}` | `ISSUES` |
| `ml_shadow_status.jsonl` | 30 | `2026-05-04T19:02:05.222594+00:00` | `{'ml_shadow_status_v1': 30}` | `ISSUES` |
| `nas100_orderflow_adverse_selection_status.jsonl` | 1 | `2026-05-04T23:55:21.254240+00:00` | `{'nas100_orderflow_adverse_selection_status_v1': 1}` | `OK` |
| `opportunity_lifecycle_audit.jsonl` | 48 | `2026-05-04T20:53:41.275004+00:00` | `{'opportunity_lifecycle_audit_v1': 48}` | `ISSUES` |
| `pending_limit_lifecycle.jsonl` | 62 | `2026-05-05T00:00:05.158160+00:00` | `{'pending_limit_lifecycle_v1': 62}` | `OK` |
| `pending_limit_lifecycle_audit.jsonl` | 4 | `2026-05-04T21:12:31.143861+00:00` | `{'pending_limit_lifecycle_audit_v1': 4}` | `OK` |
| `pending_limit_lifecycle_join_backfill.jsonl` | 108 | `2026-05-04T17:27:51.077792+00:00` | `{'pending_limit_lifecycle_join_backfill_v1': 108}` | `OK` |
| `prefill_delivery_path.jsonl` | 49 | `2026-05-05T00:45:25.841096+00:00` | `{'prefill_delivery_path_v1': 49}` | `OK` |
| `prefill_delivery_path_audit.jsonl` | 48 | `2026-05-04T21:48:50.123634+00:00` | `{'prefill_delivery_path_audit_v1': 48}` | `OK` |
| `prefill_delivery_path_resolutions.jsonl` | 940 | `2026-05-04T19:01:57.417125+00:00` | `{'prefill_delivery_path_resolution_v1': 940}` | `ISSUES` |
| `proxy_blocker_status.jsonl` | 30 | `2026-05-04T19:02:05.222566+00:00` | `{'proxy_blocker_status_v1': 30}` | `ISSUES` |
| `shadow_observer_status.jsonl` | 452 | `2026-05-05T00:55:18.394944+00:00` | `{'shadow_observer_status_v1': 452}` | `OK` |
| `shadow_observer_tick_enrichment.jsonl` | 31 | `2026-05-04T15:17:06.433237+00:00` | `{'shadow_observer_tick_enrichment_v1': 31}` | `OK` |
| `sierra_confluence_source_status.jsonl` | 48 | `2026-05-04T17:02:52.982637+00:00` | `{'sierra_confluence_source_status_v1': 48}` | `OK` |
| `sierra_depth_enrichment_status.jsonl` | 2 | `2026-05-05T00:44:22.684081+00:00` | `{'sierra_depth_enrichment_status_v1': 2}` | `OK` |
| `sierra_depth_feature_snapshots.jsonl` | 159 | `2026-05-05T00:44:18.847004+00:00` | `{'sierra_depth_feature_snapshot_v1': 159}` | `OK` |
| `sierra_proxy_registry_status.jsonl` | 48 | `2026-05-05T00:36:58.516963+00:00` | `{'sierra_proxy_registry_status_v1': 48}` | `OK` |
| `strategy_follow_candidates.jsonl` | 49 | `2026-05-05T00:45:25.835815+00:00` | `{'strategy_follow_candidate_v1': 49}` | `OK` |
| `strategy_follow_evaluations.jsonl` | 316 | `2026-05-05T01:00:05.551024+00:00` | `{'strategy_follow_evaluation_v1': 316}` | `OK` |
| `trade_index_lifecycle_audit.jsonl` | 312 | `2026-05-04T23:11:21.152648+00:00` | `{'trade_index_lifecycle_audit_v1': 312}` | `ISSUES` |
| `v2b_forward_pair_resolution_audit.jsonl` | 48 | `2026-05-04T21:30:46.096914+00:00` | `{'v2b_forward_pair_resolution_audit_v1': 48}` | `OK` |
| `v2b_forward_pair_resolutions.jsonl` | 909 | `2026-05-04T19:01:56.087348+00:00` | `{'v2b_forward_pair_resolution_v1': 909}` | `ISSUES` |
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
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_ltf_path_order.jsonl` |  | latest timestamp age 360.5m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_path_follow.jsonl` |  | latest timestamp age 360.5m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\external_source_blocker_status.jsonl` |  | latest timestamp age 360.3m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\fvg_ob_confluence_resolutions.jsonl` |  | latest timestamp age 360.4m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\live_candidate_opportunity_clusters.jsonl` |  | latest timestamp age 360.3m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\live_candidate_strategy_rollups.jsonl` |  | latest timestamp age 360.3m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\live_mechanical_strategy_shadow_outcomes.jsonl` |  | latest timestamp age 360.4m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\missed_opportunity_shadow.jsonl` |  | latest timestamp age 360.4m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\ml_shadow_status.jsonl` |  | latest timestamp age 360.3m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\prefill_delivery_path_resolutions.jsonl` |  | latest timestamp age 360.4m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\proxy_blocker_status.jsonl` |  | latest timestamp age 360.3m exceeds 90m |
| `MODERATE` | `FRESHNESS_THRESHOLD_EXCEEDED` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\v2b_forward_pair_resolutions.jsonl` |  | latest timestamp age 360.4m exceeds 90m |
| `SERIOUS` | `CANDIDATE_REGISTRY_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_registry_audit.jsonl` |  | candidate USDJPY_2026-05-05T00:45:00+00:00 has no append-only candidate registry audit row |
| `SERIOUS` | `OPPORTUNITY_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\opportunity_lifecycle_audit.jsonl` |  | candidate USDJPY_2026-05-05T00:45:00+00:00 has no append-only opportunity lifecycle audit row |
| `SERIOUS` | `TRADE_INDEX_LIFECYCLE_AUDIT_MISSING` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\trade_index_lifecycle_audit.jsonl` |  | USDJPY_2026-05-05T00:45:00+00:00 has no LTO-026 trade-index lifecycle audit row |
| `SERIOUS` | `TRADE_RECORD_INVENTORY_INDEX_STALE` | `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\index\trade_record_inventory_index_2026-05-05.json` |  | inventory index fields are stale: ['by_final_outcome', 'by_lifecycle_completeness', 'by_symbol', 'by_trade_index_lifecycle_status', 'entries.source_path', 'index_count', 'latest_record_date', 'trade_record_count'] |

## Notes

- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, and shadow-observer safety flags.
- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.
