# Shadow Log Integrity Verification - 2026-05-04

**Schema:** `shadow_log_integrity_verification_v1`
**Generated:** `2026-05-05T04:12:35.659260+00:00`
**Overall status:** `OK_WITH_DOCUMENTED_WAITING_LANES`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

- JSONL files inspected: `81`
- JSONL rows inspected: `59760`
- Known-schema JSONL files: `58`
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
- J46/J49 exit-comparator audit health: `OK_WITH_DOCUMENTED_J46_J49_EXIT_COMPARATOR_AUDIT`
- S79/side-aware risk-context health: `OK_WITH_DOCUMENTED_S79_SIDE_AWARE_CONTEXT`
- Regime/decay outcome-join health: `OK_WITH_DOCUMENTED_REGIME_DECAY_CONTEXT`
- Decision-layer diagnostics health: `OK_WITH_DOCUMENTED_DECISION_DIAGNOSTICS_CONTEXT`
- Account/PnL truth health: `OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS`
- Trade-index lifecycle health: `OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS`
- Exit-management no-event/status health: `OK_WITH_DOCUMENTED_EXIT_MANAGEMENT_NO_EVENTS`
- Session-volatility/sweep status health: `OK_WITH_DOCUMENTED_SESSION_VOL_SWEEP_STATUS`
- Canary/restart governance health: `OK_WITH_DOCUMENTED_CANARY_RESTART_GOVERNANCE`
- Notification queue dead-zone health: `OK_WITH_DOCUMENTED_NOTIFICATION_QUEUE_DEAD_ZONE`
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
| `canary_restart_governance_status.jsonl` | 1 | `2026-05-05T02:42:49.483266+00:00` | `{'canary_restart_governance_status_v1': 1}` | `OK` |
| `candidate_ltf_path_order.jsonl` | 987 | `2026-05-05T02:44:30.381178+00:00` | `{'candidate_ltf_path_order_v1': 987}` | `OK` |
| `candidate_mso_snapshot_joins.jsonl` | 49 | `2026-05-05T01:05:40.755092+00:00` | `{'candidate_mso_snapshot_join_v1': 49}` | `OK` |
| `candidate_path_contract_audit.jsonl` | 95 | `2026-05-05T02:45:24.402953+00:00` | `{'candidate_path_contract_audit_v1': 95}` | `OK` |
| `candidate_path_follow.jsonl` | 972 | `2026-05-05T02:44:30.112456+00:00` | `{'candidate_path_follow_v1': 972}` | `OK` |
| `candidate_registry_audit.jsonl` | 49 | `2026-05-05T01:05:40.953706+00:00` | `{'candidate_registry_audit_v1': 49}` | `OK` |
| `context_control_audit.jsonl` | 95 | `2026-05-05T02:45:51.965612+00:00` | `{'context_control_audit_v1': 95}` | `OK` |
| `context_control_ledger.jsonl` | 49 | `2026-05-05T00:45:25.844667+00:00` | `{'context_control_forward_v1': 49}` | `OK` |
| `d1_bias_lag.jsonl` | 380 | `None` | `{}` | `OK` |
| `d1_bias_lag_recovery.jsonl` | 3 | `2026-05-04T08:03:31.297974+00:00` | `{'d1_bias_lag_recovery_v1': 3}` | `OK` |
| `databento_live_budget_ledger.jsonl` | 4 | `2026-05-04T23:37:15.740424+00:00` | `{'databento_live_budget_ledger_v1': 4}` | `OK` |
| `databento_live_confluence.jsonl` | 3 | `2026-05-04T23:37:15.739771+00:00` | `{'databento_live_confluence_v1': 3}` | `OK` |
| `databento_live_trigger_decisions.jsonl` | 70 | `2026-05-05T01:03:04.904221+00:00` | `{'databento_live_trigger_decision_v1': 70}` | `OK` |
| `decision_layer_diagnostics_join.jsonl` | 49 | `2026-05-05T04:11:47.390216+00:00` | `{'decision_layer_diagnostics_join_v1': 49}` | `OK` |
| `exit_management_shadow_status.jsonl` | 147 | `2026-05-05T02:04:39.067520+00:00` | `{'exit_management_shadow_status_v1': 147}` | `OK` |
| `external_source_blocker_status.jsonl` | 198 | `2026-05-05T02:44:42.161705+00:00` | `{'external_source_blocker_status_v1': 198}` | `OK` |
| `fvg_ob_confluence.jsonl` | 49 | `2026-05-05T00:45:25.843377+00:00` | `{'fvg_ob_confluence_forward_v1': 49}` | `OK` |
| `fvg_ob_confluence_audit.jsonl` | 175 | `2026-05-05T02:45:47.442188+00:00` | `{'fvg_ob_confluence_audit_v1': 175}` | `OK` |
| `fvg_ob_confluence_resolutions.jsonl` | 987 | `2026-05-05T02:44:35.692505+00:00` | `{'fvg_ob_confluence_resolution_v1': 987}` | `OK` |
| `gbpjpy_proxy_gap_status.jsonl` | 9 | `2026-05-05T01:08:23.488652+00:00` | `{'gbpjpy_orderflow_proxy_gap_status_v1': 9}` | `OK` |
| `j46_j49_exit_comparator_audit.jsonl` | 52 | `2026-05-05T03:28:08.562259+00:00` | `{'j46_j49_exit_comparator_audit_v1': 52}` | `OK` |
| `live_candidate_opportunity_clusters.jsonl` | 900 | `2026-05-05T02:44:37.624011+00:00` | `{'live_candidate_opportunity_cluster_v1': 900}` | `OK` |
| `live_candidate_strategy_rollups.jsonl` | 1097 | `2026-05-05T02:44:38.862937+00:00` | `{'live_candidate_strategy_rollup_v1': 1097}` | `OK` |
| `live_mechanical_strategy_shadow_outcomes.jsonl` | 24890 | `2026-05-05T02:44:32.492014+00:00` | `{'live_mechanical_strategy_shadow_outcome_v1': 24890}` | `OK` |
| `live_structural_strategy_metadata.jsonl` | 49 | `2026-05-05T01:02:58.728248+00:00` | `{'live_structural_strategy_metadata_v1': 49}` | `OK` |
| `missed_opportunity_shadow.jsonl` | 987 | `2026-05-05T02:44:36.811653+00:00` | `{'missed_opportunity_shadow_v1': 987}` | `OK` |
| `ml_shadow_status.jsonl` | 33 | `2026-05-05T02:44:42.161662+00:00` | `{'ml_shadow_status_v1': 33}` | `OK` |
| `nas100_orderflow_adverse_selection_status.jsonl` | 2 | `2026-05-05T01:07:48.691130+00:00` | `{'nas100_orderflow_adverse_selection_status_v1': 2}` | `OK` |
| `notification_queue_dead_zone_status.jsonl` | 1 | `2026-05-05T03:01:15.353738+00:00` | `{'notification_queue_dead_zone_status_v1': 1}` | `OK` |
| `opportunity_lifecycle_audit.jsonl` | 171 | `2026-05-05T02:45:28.429704+00:00` | `{'opportunity_lifecycle_audit_v1': 171}` | `OK` |
| `orderflow_primitives_status.jsonl` | 1 | `2026-05-05T01:45:54.730223+00:00` | `{'orderflow_primitives_status_v1': 1}` | `OK` |
| `pending_limit_lifecycle.jsonl` | 62 | `2026-05-05T00:00:05.158160+00:00` | `{'pending_limit_lifecycle_v1': 62}` | `OK` |
| `pending_limit_lifecycle_audit.jsonl` | 41 | `2026-05-05T01:05:41.142830+00:00` | `{'pending_limit_lifecycle_audit_v1': 41}` | `OK` |
| `pending_limit_lifecycle_join_backfill.jsonl` | 110 | `2026-05-05T01:02:58.633768+00:00` | `{'pending_limit_lifecycle_join_backfill_v1': 110}` | `OK` |
| `prefill_delivery_path.jsonl` | 49 | `2026-05-05T00:45:25.841096+00:00` | `{'prefill_delivery_path_v1': 49}` | `OK` |
| `prefill_delivery_path_audit.jsonl` | 175 | `2026-05-05T02:45:42.699505+00:00` | `{'prefill_delivery_path_audit_v1': 175}` | `OK` |
| `prefill_delivery_path_resolutions.jsonl` | 1018 | `2026-05-05T02:44:34.436376+00:00` | `{'prefill_delivery_path_resolution_v1': 1018}` | `OK` |
| `proxy_blocker_status.jsonl` | 33 | `2026-05-05T02:44:42.161637+00:00` | `{'proxy_blocker_status_v1': 33}` | `OK` |
| `regime_decay_outcome_join.jsonl` | 52 | `2026-05-05T03:54:29.684606+00:00` | `{'regime_decay_outcome_join_v1': 52}` | `OK` |
| `s79_side_aware_risk_context.jsonl` | 52 | `2026-05-05T03:38:35.347027+00:00` | `{'s79_side_aware_risk_context_v1': 52}` | `OK` |
| `session_volatility_sweep_status.jsonl` | 2 | `2026-05-05T02:25:12.699699+00:00` | `{'session_volatility_sweep_status_v1': 2}` | `OK` |
| `shadow_observer_status.jsonl` | 509 | `2026-05-05T04:06:56.708746+00:00` | `{'shadow_observer_status_v1': 509}` | `OK` |
| `shadow_observer_tick_enrichment.jsonl` | 31 | `2026-05-04T15:17:06.433237+00:00` | `{'shadow_observer_tick_enrichment_v1': 31}` | `OK` |
| `sierra_6b_si_depth_policy_status.jsonl` | 3 | `2026-05-05T01:32:54.304026+00:00` | `{'sierra_6b_si_depth_policy_status_v1': 3}` | `OK` |
| `sierra_confluence_source_status.jsonl` | 49 | `2026-05-05T01:03:05.141348+00:00` | `{'sierra_confluence_source_status_v1': 49}` | `OK` |
| `sierra_depth_enrichment_status.jsonl` | 3 | `2026-05-05T01:07:48.834636+00:00` | `{'sierra_depth_enrichment_status_v1': 3}` | `OK` |
| `sierra_depth_feature_snapshots.jsonl` | 160 | `2026-05-05T01:07:42.372036+00:00` | `{'sierra_depth_feature_snapshot_v1': 160}` | `OK` |
| `sierra_proxy_registry_status.jsonl` | 97 | `2026-05-05T01:07:32.411777+00:00` | `{'sierra_proxy_registry_status_v1': 97}` | `OK` |
| `storage_retention_status.jsonl` | 1 | `2026-05-05T03:11:54.325928+00:00` | `{'storage_retention_status_v1': 1}` | `OK` |
| `strategy_follow_candidates.jsonl` | 49 | `2026-05-05T00:45:25.835815+00:00` | `{'strategy_follow_candidate_v1': 49}` | `OK` |
| `strategy_follow_evaluations.jsonl` | 348 | `2026-05-05T03:00:05.246541+00:00` | `{'strategy_follow_evaluation_v1': 348}` | `OK` |
| `trade_index_lifecycle_audit.jsonl` | 313 | `2026-05-05T01:03:18.049125+00:00` | `{'trade_index_lifecycle_audit_v1': 313}` | `OK` |
| `v2b_forward_pair_resolution_audit.jsonl` | 175 | `2026-05-05T02:45:37.747728+00:00` | `{'v2b_forward_pair_resolution_audit_v1': 175}` | `OK` |
| `v2b_forward_pair_resolutions.jsonl` | 987 | `2026-05-05T02:44:33.231952+00:00` | `{'v2b_forward_pair_resolution_v1': 987}` | `OK` |
| `v2b_forward_pairs.jsonl` | 49 | `2026-05-05T00:45:25.838280+00:00` | `{'v2b_forward_pair_v1': 49}` | `OK` |

## Documented Waiting Lanes

| Log | Reason |
|---|---|
| `be_shadow_log.jsonl` | actual BE event rows only; no-event proof lives in exit_management_shadow_status.jsonl |
| `ml_shadow_predictions.jsonl` | owner-approved target refresh and read-only ML shadow implementation pending |
| `partial_close_shadow_log.jsonl` | actual partial-close trigger rows only; no-event proof lives in exit_management_shadow_status.jsonl |
| `time_in_trade.jsonl` | actual close/time-in-trade rows only; no-event proof lives in exit_management_shadow_status.jsonl |

## Issues

No structural/value issues found in inspected rows.

## Notes

- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, J46/J49 exit-comparator audit coverage, S79/side-aware risk-context coverage, exit-management no-event/status coverage, session-volatility/sweep cadence coverage, canary/restart governance coverage, and shadow-observer safety flags.
- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.
