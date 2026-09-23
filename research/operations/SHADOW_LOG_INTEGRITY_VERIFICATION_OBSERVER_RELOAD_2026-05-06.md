# Shadow Log Integrity Verification - 2026-05-04

**Schema:** `shadow_log_integrity_verification_v1`
**Generated:** `2026-05-05T21:17:04.365808+00:00`
**Overall status:** `OK_WITH_DOCUMENTED_WAITING_LANES`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

- JSONL files inspected: `88`
- JSONL rows inspected: `85761`
- Known-schema JSONL files: `65`
- CSV shadow files inspected: `4`
- Documented waiting lanes: `3`
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
- Mechanical/context diagnostics health: `OK_WITH_DOCUMENTED_MECHANICAL_CONTEXT`
- K55/ML shadow health: `OK_WITH_DOCUMENTED_K55_ML_SHADOW`
- V2 structural selector readiness health: `OK_WITH_DOCUMENTED_V2_SELECTOR_NOT_READY`
- XAUUSD same-market extension health: `OK_WITH_DOCUMENTED_XAUUSD_SAME_MARKET_PREREGISTRATION`
- ES/MES preregistration health: `OK_WITH_DOCUMENTED_ES_MES_PREREGISTRATION`
- Shadow-observer hardening health: `OK_WITH_DOCUMENTED_SHADOW_OBSERVER_HARDENING`
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
| `account_truth_reconciliation_status.jsonl` | 76 | `2026-05-05T17:01:05.125224+00:00` | `{'account_truth_reconciliation_status_v1': 76}` | `OK` |
| `broker_actual_r_audit.jsonl` | 83 | `2026-05-05T17:01:57.641815+00:00` | `{'broker_actual_r_audit_v1': 83}` | `OK` |
| `canary_restart_governance_status.jsonl` | 5 | `2026-05-05T21:16:34.811746+00:00` | `{'canary_restart_governance_status_v1': 5}` | `OK` |
| `candidate_ltf_path_order.jsonl` | 1611 | `2026-05-05T17:00:36.149984+00:00` | `{'candidate_ltf_path_order_v1': 1611}` | `OK` |
| `candidate_mso_snapshot_joins.jsonl` | 66 | `2026-05-05T10:42:46.383659+00:00` | `{'candidate_mso_snapshot_join_v1': 66}` | `OK` |
| `candidate_path_contract_audit.jsonl` | 650 | `2026-05-05T17:01:48.672458+00:00` | `{'candidate_path_contract_audit_v1': 650}` | `OK` |
| `candidate_path_follow.jsonl` | 1527 | `2026-05-05T17:00:35.898433+00:00` | `{'candidate_path_follow_v1': 1527}` | `OK` |
| `candidate_registry_audit.jsonl` | 76 | `2026-05-05T17:01:47.974697+00:00` | `{'candidate_registry_audit_v1': 76}` | `OK` |
| `context_control_audit.jsonl` | 651 | `2026-05-05T17:01:56.861186+00:00` | `{'context_control_audit_v1': 651}` | `OK` |
| `context_control_ledger.jsonl` | 76 | `2026-05-05T17:00:24.732626+00:00` | `{'context_control_forward_v1': 76}` | `OK` |
| `d1_bias_lag.jsonl` | 448 | `None` | `{}` | `OK` |
| `d1_bias_lag_recovery.jsonl` | 3 | `2026-05-04T08:03:31.297974+00:00` | `{'d1_bias_lag_recovery_v1': 3}` | `OK` |
| `databento_live_budget_ledger.jsonl` | 4 | `2026-05-04T23:37:15.740424+00:00` | `{'databento_live_budget_ledger_v1': 4}` | `OK` |
| `databento_live_confluence.jsonl` | 3 | `2026-05-04T23:37:15.739771+00:00` | `{'databento_live_confluence_v1': 3}` | `OK` |
| `databento_live_trigger_decisions.jsonl` | 97 | `2026-05-05T17:00:54.598919+00:00` | `{'databento_live_trigger_decision_v1': 97}` | `OK` |
| `decision_layer_diagnostics_join.jsonl` | 76 | `2026-05-05T17:02:00.718749+00:00` | `{'decision_layer_diagnostics_join_v1': 76}` | `OK` |
| `es_mes_preregistration_status.jsonl` | 1 | `2026-05-05T05:39:58.217115+00:00` | `{'es_mes_preregistration_status_v1': 1}` | `OK` |
| `exit_management_shadow_status.jsonl` | 241 | `2026-05-05T17:02:02.505405+00:00` | `{'exit_management_shadow_status_v1': 241}` | `OK` |
| `external_source_blocker_status.jsonl` | 408 | `2026-05-05T17:01:05.192142+00:00` | `{'external_source_blocker_status_v1': 408}` | `OK` |
| `fvg_ob_confluence.jsonl` | 76 | `2026-05-05T17:00:24.731275+00:00` | `{'fvg_ob_confluence_forward_v1': 76}` | `OK` |
| `fvg_ob_confluence_audit.jsonl` | 1067 | `2026-05-05T17:01:54.955747+00:00` | `{'fvg_ob_confluence_audit_v1': 1067}` | `OK` |
| `fvg_ob_confluence_resolutions.jsonl` | 1611 | `2026-05-05T17:00:46.343505+00:00` | `{'fvg_ob_confluence_resolution_v1': 1611}` | `OK` |
| `gbpjpy_proxy_gap_status.jsonl` | 9 | `2026-05-05T01:08:23.488652+00:00` | `{'gbpjpy_orderflow_proxy_gap_status_v1': 9}` | `OK` |
| `j46_j49_exit_comparator_audit.jsonl` | 616 | `2026-05-05T17:01:58.313303+00:00` | `{'j46_j49_exit_comparator_audit_v1': 616}` | `OK` |
| `live_candidate_opportunity_clusters.jsonl` | 1757 | `2026-05-05T17:00:50.699855+00:00` | `{'live_candidate_opportunity_cluster_v1': 1757}` | `OK` |
| `live_candidate_strategy_rollups.jsonl` | 1994 | `2026-05-05T17:00:54.754936+00:00` | `{'live_candidate_strategy_rollup_v1': 1994}` | `OK` |
| `live_mechanical_strategy_shadow_outcomes.jsonl` | 34900 | `2026-05-05T17:00:39.514210+00:00` | `{'live_mechanical_strategy_shadow_outcome_v1': 34900}` | `OK` |
| `live_structural_strategy_metadata.jsonl` | 76 | `2026-05-05T17:00:40.791769+00:00` | `{'live_structural_strategy_metadata_v1': 76}` | `OK` |
| `lto_blocked_lane_status.jsonl` | 3 | `2026-05-05T06:23:04.960252+00:00` | `{'lto_blocked_lane_status_v1': 3}` | `OK` |
| `mechanical_context_diagnostics_join.jsonl` | 609 | `2026-05-05T17:02:01.582080+00:00` | `{'mechanical_context_diagnostics_join_v1': 609}` | `OK` |
| `missed_opportunity_shadow.jsonl` | 1611 | `2026-05-05T17:00:48.959461+00:00` | `{'missed_opportunity_shadow_v1': 1611}` | `OK` |
| `ml_shadow_predictions.jsonl` | 979 | `2026-05-05T17:02:03.208043+00:00` | `{'ml_shadow_prediction_v1': 979}` | `OK` |
| `ml_shadow_status.jsonl` | 68 | `2026-05-05T17:01:05.192092+00:00` | `{'ml_shadow_status_v1': 68}` | `OK` |
| `nas100_orderflow_adverse_selection_status.jsonl` | 6 | `2026-05-05T10:35:48.086566+00:00` | `{'nas100_orderflow_adverse_selection_status_v1': 6}` | `OK` |
| `notification_queue_dead_zone_status.jsonl` | 3 | `2026-05-05T17:16:03.284734+00:00` | `{'notification_queue_dead_zone_status_v1': 3}` | `OK` |
| `opportunity_lifecycle_audit.jsonl` | 1063 | `2026-05-05T17:01:49.417565+00:00` | `{'opportunity_lifecycle_audit_v1': 1063}` | `OK` |
| `orderflow_primitives_status.jsonl` | 6 | `2026-05-05T11:05:51.794802+00:00` | `{'orderflow_primitives_status_v1': 6}` | `OK` |
| `pending_limit_lifecycle.jsonl` | 141 | `2026-05-05T17:15:05.195591+00:00` | `{'pending_limit_lifecycle_v1': 141}` | `OK` |
| `pending_limit_lifecycle_audit.jsonl` | 45 | `2026-05-05T08:33:22.614110+00:00` | `{'pending_limit_lifecycle_audit_v1': 45}` | `OK` |
| `pending_limit_lifecycle_join_backfill.jsonl` | 189 | `2026-05-05T17:00:40.431881+00:00` | `{'pending_limit_lifecycle_join_backfill_v1': 189}` | `OK` |
| `prefill_delivery_path.jsonl` | 76 | `2026-05-05T17:00:24.729587+00:00` | `{'prefill_delivery_path_v1': 76}` | `OK` |
| `prefill_delivery_path_audit.jsonl` | 1073 | `2026-05-05T17:01:52.987518+00:00` | `{'prefill_delivery_path_audit_v1': 1073}` | `OK` |
| `prefill_delivery_path_resolutions.jsonl` | 1648 | `2026-05-05T17:00:43.596726+00:00` | `{'prefill_delivery_path_resolution_v1': 1648}` | `OK` |
| `proxy_blocker_status.jsonl` | 68 | `2026-05-05T17:01:05.192065+00:00` | `{'proxy_blocker_status_v1': 68}` | `OK` |
| `regime_decay_outcome_join.jsonl` | 612 | `2026-05-05T17:01:59.869339+00:00` | `{'regime_decay_outcome_join_v1': 612}` | `OK` |
| `s79_side_aware_risk_context.jsonl` | 83 | `2026-05-05T17:01:59.106378+00:00` | `{'s79_side_aware_risk_context_v1': 83}` | `OK` |
| `session_volatility_sweep_status.jsonl` | 2 | `2026-05-05T02:25:12.699699+00:00` | `{'session_volatility_sweep_status_v1': 2}` | `OK` |
| `shadow_observer_hardening_status.jsonl` | 37 | `2026-05-05T21:14:43.533271+00:00` | `{'shadow_observer_hardening_status_v1': 37}` | `OK` |
| `shadow_observer_status.jsonl` | 976 | `2026-05-05T21:13:38.904538+00:00` | `{'shadow_observer_status_v1': 976}` | `OK` |
| `shadow_observer_tick_enrichment.jsonl` | 63 | `2026-05-05T15:30:57.482913+00:00` | `{'shadow_observer_tick_enrichment_v1': 63}` | `OK` |
| `sierra_6b_si_depth_policy_status.jsonl` | 3 | `2026-05-05T01:32:54.304026+00:00` | `{'sierra_6b_si_depth_policy_status_v1': 3}` | `OK` |
| `sierra_confluence_source_status.jsonl` | 76 | `2026-05-05T17:00:54.684430+00:00` | `{'sierra_confluence_source_status_v1': 76}` | `OK` |
| `sierra_depth_enrichment_status.jsonl` | 9 | `2026-05-05T11:05:47.745168+00:00` | `{'sierra_depth_enrichment_status_v1': 9}` | `OK` |
| `sierra_depth_feature_snapshots.jsonl` | 220 | `2026-05-05T17:01:15.190489+00:00` | `{'sierra_depth_feature_snapshot_v1': 220}` | `OK` |
| `sierra_proxy_registry_status.jsonl` | 327 | `2026-05-05T10:35:41.544536+00:00` | `{'sierra_proxy_registry_status_v1': 327}` | `OK` |
| `storage_retention_status.jsonl` | 1 | `2026-05-05T03:11:54.325928+00:00` | `{'storage_retention_status_v1': 1}` | `OK` |
| `strategy_follow_candidates.jsonl` | 76 | `2026-05-05T17:00:24.724032+00:00` | `{'strategy_follow_candidate_v1': 76}` | `OK` |
| `strategy_follow_evaluations.jsonl` | 675 | `2026-05-05T18:45:16.456342+00:00` | `{'strategy_follow_evaluation_v1': 675}` | `OK` |
| `trade_index_lifecycle_audit.jsonl` | 338 | `2026-05-05T17:02:04.271523+00:00` | `{'trade_index_lifecycle_audit_v1': 338}` | `OK` |
| `v2_structural_selector_readiness.jsonl` | 52 | `2026-05-05T17:02:35.537239+00:00` | `{'v2_structural_selector_readiness_v1': 52}` | `OK` |
| `v2b_forward_pair_resolution_audit.jsonl` | 1067 | `2026-05-05T17:01:50.297161+00:00` | `{'v2b_forward_pair_resolution_audit_v1': 1067}` | `OK` |
| `v2b_forward_pair_resolutions.jsonl` | 1611 | `2026-05-05T17:00:40.892768+00:00` | `{'v2b_forward_pair_resolution_v1': 1611}` | `OK` |
| `v2b_forward_pairs.jsonl` | 76 | `2026-05-05T17:00:24.727656+00:00` | `{'v2b_forward_pair_v1': 76}` | `OK` |
| `xauusd_same_market_extension_status.jsonl` | 35 | `2026-05-05T21:15:49.880565+00:00` | `{'xauusd_same_market_extension_status_v1': 35}` | `OK` |

## Documented Waiting Lanes

| Log | Reason |
|---|---|
| `be_shadow_log.jsonl` | actual BE event rows only; no-event proof lives in exit_management_shadow_status.jsonl |
| `partial_close_shadow_log.jsonl` | actual partial-close trigger rows only; no-event proof lives in exit_management_shadow_status.jsonl |
| `time_in_trade.jsonl` | actual close/time-in-trade rows only; no-event proof lives in exit_management_shadow_status.jsonl |

## Issues

No structural/value issues found in inspected rows.

## Notes

- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, J46/J49 exit-comparator audit coverage, S79/side-aware risk-context coverage, exit-management no-event/status coverage, session-volatility/sweep cadence coverage, canary/restart governance coverage, and shadow-observer safety flags.
- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.
