# Shadow Log Integrity Verification - 2026-05-04

**Schema:** `shadow_log_integrity_verification_v1`
**Generated:** `2026-05-05T01:17:23.966964+00:00`
**Overall status:** `OK_WITH_DOCUMENTED_WAITING_LANES`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

- JSONL files inspected: `70`
- JSONL rows inspected: `57980`
- Known-schema JSONL files: `47`
- CSV shadow files inspected: `4`
- Documented waiting lanes: `4`
- Candidate/MSO join health: `OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS`
- Candidate registry audit health: `OK_WITH_DOCUMENTED_REGISTRY_LIMITATIONS`
- Candidate path contract health: `OK_WITH_DOCUMENTED_PATH_LIMITATIONS`
- Opportunity lifecycle audit health: `OK_WITH_DOCUMENTED_LIFECYCLE_LIMITATIONS`
- Pending-limit lifecycle audit health: `OK_WITH_DOCUMENTED_PENDING_LIFECYCLE_LIMITATIONS`
- V2b forward-pair resolution audit health: `OK_WITH_DOCUMENTED_V2B_LIMITATIONS`
- Pre-fill delivery path audit health: `OK_WITH_DOCUMENTED_PREFILL_LIMITATIONS`
- FVG/OB confluence audit health: `OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS`
- Context/control audit health: `OK_WITH_DOCUMENTED_CONTEXT_CONTROL_LIMITATIONS`
- Broker actual-R audit health: `OK_WITH_DOCUMENTED_ACCOUNTING_LIMITATIONS`
- Account/PnL truth health: `OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS`
- Trade-index lifecycle health: `OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS`
- Issues: `0`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 0 |
| `SERIOUS` | 0 |
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
| `d1_bias_lag.jsonl` | 373 | `None` | `{}` | `OK` |
| `d1_bias_lag_recovery.jsonl` | 3 | `2026-05-04T08:03:31.297974+00:00` | `{'d1_bias_lag_recovery_v1': 3}` | `OK` |
| `databento_live_budget_ledger.jsonl` | 4 | `2026-05-04T23:37:15.740424+00:00` | `{'databento_live_budget_ledger_v1': 4}` | `OK` |
| `databento_live_confluence.jsonl` | 3 | `2026-05-04T23:37:15.739771+00:00` | `{'databento_live_confluence_v1': 3}` | `OK` |
| `databento_live_trigger_decisions.jsonl` | 70 | `2026-05-05T01:03:04.904221+00:00` | `{'databento_live_trigger_decision_v1': 70}` | `OK` |
| `external_source_blocker_status.jsonl` | 192 | `2026-05-05T01:16:27.064220+00:00` | `{'external_source_blocker_status_v1': 192}` | `OK` |
| `fvg_ob_confluence.jsonl` | 49 | `2026-05-05T00:45:25.843377+00:00` | `{'fvg_ob_confluence_forward_v1': 49}` | `OK` |
| `fvg_ob_confluence_audit.jsonl` | 146 | `2026-05-05T01:17:17.837674+00:00` | `{'fvg_ob_confluence_audit_v1': 146}` | `OK` |
| `fvg_ob_confluence_resolutions.jsonl` | 958 | `2026-05-05T01:03:01.396090+00:00` | `{'fvg_ob_confluence_resolution_v1': 958}` | `OK` |
| `gbpjpy_proxy_gap_status.jsonl` | 9 | `2026-05-05T01:08:23.488652+00:00` | `{'gbpjpy_orderflow_proxy_gap_status_v1': 9}` | `OK` |
| `live_candidate_opportunity_clusters.jsonl` | 882 | `2026-05-05T01:16:22.373406+00:00` | `{'live_candidate_opportunity_cluster_v1': 882}` | `OK` |
| `live_candidate_strategy_rollups.jsonl` | 1068 | `2026-05-05T01:16:23.810052+00:00` | `{'live_candidate_strategy_rollup_v1': 1068}` | `OK` |
| `live_mechanical_strategy_shadow_outcomes.jsonl` | 24426 | `2026-05-05T01:02:58.074721+00:00` | `{'live_mechanical_strategy_shadow_outcome_v1': 24426}` | `OK` |
| `live_structural_strategy_metadata.jsonl` | 49 | `2026-05-05T01:02:58.728248+00:00` | `{'live_structural_strategy_metadata_v1': 49}` | `OK` |
| `missed_opportunity_shadow.jsonl` | 958 | `2026-05-05T01:03:02.644592+00:00` | `{'missed_opportunity_shadow_v1': 958}` | `OK` |
| `ml_shadow_status.jsonl` | 32 | `2026-05-05T01:16:27.064172+00:00` | `{'ml_shadow_status_v1': 32}` | `OK` |
| `nas100_orderflow_adverse_selection_status.jsonl` | 2 | `2026-05-05T01:07:48.691130+00:00` | `{'nas100_orderflow_adverse_selection_status_v1': 2}` | `OK` |
| `opportunity_lifecycle_audit.jsonl` | 142 | `2026-05-05T01:16:35.380930+00:00` | `{'opportunity_lifecycle_audit_v1': 142}` | `OK` |
| `pending_limit_lifecycle.jsonl` | 62 | `2026-05-05T00:00:05.158160+00:00` | `{'pending_limit_lifecycle_v1': 62}` | `OK` |
| `pending_limit_lifecycle_audit.jsonl` | 41 | `2026-05-05T01:05:41.142830+00:00` | `{'pending_limit_lifecycle_audit_v1': 41}` | `OK` |
| `pending_limit_lifecycle_join_backfill.jsonl` | 110 | `2026-05-05T01:02:58.633768+00:00` | `{'pending_limit_lifecycle_join_backfill_v1': 110}` | `OK` |
| `prefill_delivery_path.jsonl` | 49 | `2026-05-05T00:45:25.841096+00:00` | `{'prefill_delivery_path_v1': 49}` | `OK` |
| `prefill_delivery_path_audit.jsonl` | 146 | `2026-05-05T01:17:17.657015+00:00` | `{'prefill_delivery_path_audit_v1': 146}` | `OK` |
| `prefill_delivery_path_resolutions.jsonl` | 989 | `2026-05-05T01:03:00.094160+00:00` | `{'prefill_delivery_path_resolution_v1': 989}` | `OK` |
| `proxy_blocker_status.jsonl` | 32 | `2026-05-05T01:16:27.064145+00:00` | `{'proxy_blocker_status_v1': 32}` | `OK` |
| `shadow_observer_status.jsonl` | 458 | `2026-05-05T01:15:28.511663+00:00` | `{'shadow_observer_status_v1': 458}` | `OK` |
| `shadow_observer_tick_enrichment.jsonl` | 31 | `2026-05-04T15:17:06.433237+00:00` | `{'shadow_observer_tick_enrichment_v1': 31}` | `OK` |
| `sierra_confluence_source_status.jsonl` | 49 | `2026-05-05T01:03:05.141348+00:00` | `{'sierra_confluence_source_status_v1': 49}` | `OK` |
| `sierra_depth_enrichment_status.jsonl` | 3 | `2026-05-05T01:07:48.834636+00:00` | `{'sierra_depth_enrichment_status_v1': 3}` | `OK` |
| `sierra_depth_feature_snapshots.jsonl` | 160 | `2026-05-05T01:07:42.372036+00:00` | `{'sierra_depth_feature_snapshot_v1': 160}` | `OK` |
| `sierra_proxy_registry_status.jsonl` | 97 | `2026-05-05T01:07:32.411777+00:00` | `{'sierra_proxy_registry_status_v1': 97}` | `OK` |
| `strategy_follow_candidates.jsonl` | 49 | `2026-05-05T00:45:25.835815+00:00` | `{'strategy_follow_candidate_v1': 49}` | `OK` |
| `strategy_follow_evaluations.jsonl` | 320 | `2026-05-05T01:15:05.120263+00:00` | `{'strategy_follow_evaluation_v1': 320}` | `OK` |
| `trade_index_lifecycle_audit.jsonl` | 313 | `2026-05-05T01:03:18.049125+00:00` | `{'trade_index_lifecycle_audit_v1': 313}` | `OK` |
| `v2b_forward_pair_resolution_audit.jsonl` | 146 | `2026-05-05T01:17:17.927166+00:00` | `{'v2b_forward_pair_resolution_audit_v1': 146}` | `OK` |
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

No structural/value issues found in inspected rows.

## Notes

- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, and shadow-observer safety flags.
- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.
