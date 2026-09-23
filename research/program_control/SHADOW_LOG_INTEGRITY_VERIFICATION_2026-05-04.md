# Shadow Log Integrity Verification - 2026-05-04

**Schema:** `shadow_log_integrity_verification_v1`
**Generated:** `2026-06-01T19:03:22.242849+00:00`
**Overall status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

- JSONL files inspected: `110`
- JSONL rows inspected: `369678`
- Known-schema JSONL files: `66`
- CSV shadow files inspected: `4`
- Documented waiting lanes: `3`
- Candidate/MSO join health: `ACTION_REQUIRED`
- Candidate registry audit health: `ACTION_REQUIRED`
- Candidate path contract health: `OK_WITH_DOCUMENTED_PATH_LIMITATIONS`
- Opportunity lifecycle audit health: `ACTION_REQUIRED`
- Pending-limit lifecycle audit health: `ACTION_REQUIRED`
- V2b forward-pair resolution audit health: `OK_WITH_DOCUMENTED_V2B_LIMITATIONS`
- Pre-fill delivery path audit health: `OK_WITH_DOCUMENTED_PREFILL_LIMITATIONS`
- FVG/OB confluence audit health: `OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS`
- Context/control audit health: `ACTION_REQUIRED`
- Broker actual-R audit health: `ACTION_REQUIRED`
- J46/J49 exit-comparator audit health: `ACTION_REQUIRED`
- S79/side-aware risk-context health: `OK_WITH_DOCUMENTED_S79_SIDE_AWARE_CONTEXT`
- Regime/decay outcome-join health: `OK_WITH_DOCUMENTED_REGIME_DECAY_CONTEXT`
- Decision-layer diagnostics health: `ACTION_REQUIRED`
- Mechanical/context diagnostics health: `OK_WITH_DOCUMENTED_MECHANICAL_CONTEXT`
- K55/ML shadow health: `OK_WITH_DOCUMENTED_K55_ML_SHADOW`
- V2 structural selector readiness health: `OK_WITH_DOCUMENTED_V2_SELECTOR_NOT_READY`
- XAUUSD same-market extension health: `OK_WITH_DOCUMENTED_XAUUSD_SAME_MARKET_PREREGISTRATION`
- ES/MES preregistration health: `OK_WITH_DOCUMENTED_ES_MES_PREREGISTRATION`
- Shadow-observer hardening health: `ACTION_REQUIRED`
- Account/PnL truth health: `ACTION_REQUIRED`
- Trade-index lifecycle health: `OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS`
- Exit-management no-event/status health: `OK_WITH_DOCUMENTED_EXIT_MANAGEMENT_NO_EVENTS`
- Session-volatility/sweep status health: `OK_WITH_DOCUMENTED_SESSION_VOL_SWEEP_STATUS`
- Notification queue dead-zone health: `ACTION_REQUIRED`
- AI narrowing policy shadow-evaluation health: `OK_WITH_DEFAULT_OFF_AI_NARROWING_SHADOW_EVALUATIONS`
- Issues: `161194`

## Issue Counts

| Severity | Count |
|---|---:|
| `CRITICAL` | 12 |
| `SERIOUS` | 161173 |
| `MODERATE` | 9 |
| `LOW` | 0 |

## Known Forward/Shadow Logs

| Log | Rows | Latest UTC | Schemas | Status |
|---|---:|---|---|---|
| `account_pnl_truth_reconciliation.jsonl` | 28 | `2026-05-17T13:46:32.985379+00:00` | `{'account_pnl_truth_reconciliation_v1': 28}` | `ISSUES` |
| `account_truth_reconciliation_status.jsonl` | 404 | `2026-06-01T12:11:30.398297+00:00` | `{'account_truth_reconciliation_status_v1': 404}` | `OK` |
| `ai_decision_trace.jsonl` | 0 | `None` | `{}` | `OK` |
| `ai_narrowing_policy_shadow_evaluations.jsonl` | 4083 | `2026-06-01T18:03:27.888049+00:00` | `{'ai_narrowing_policy_shadow_evaluation_v1': 4083}` | `OK` |
| `broker_actual_r_audit.jsonl` | 284 | `2026-05-17T13:46:25.050354+00:00` | `{'broker_actual_r_audit_v1': 284}` | `ISSUES` |
| `candidate_ltf_path_order.jsonl` | 11421 | `2026-06-01T17:33:50.886320+00:00` | `{'candidate_ltf_path_order_v1': 11421}` | `OK` |
| `candidate_mso_snapshot_joins.jsonl` | 66 | `2026-05-05T10:42:46.383659+00:00` | `{'candidate_mso_snapshot_join_v1': 66}` | `OK` |
| `candidate_path_contract_audit.jsonl` | 6475 | `2026-06-01T18:03:32.679530+00:00` | `{'candidate_path_contract_audit_v1': 6475}` | `OK` |
| `candidate_path_follow.jsonl` | 7822 | `2026-06-01T17:33:39.678061+00:00` | `{'candidate_path_follow_v1': 7822}` | `OK` |
| `candidate_registry_audit.jsonl` | 506 | `2026-06-01T18:03:30.764385+00:00` | `{'candidate_registry_audit_v1': 506}` | `ISSUES` |
| `context_control_audit.jsonl` | 6562 | `2026-06-01T18:07:28.900161+00:00` | `{'context_control_audit_v1': 6562}` | `ISSUES` |
| `context_control_ledger.jsonl` | 506 | `2026-06-01T17:33:33.420352+00:00` | `{'context_control_forward_v1': 506}` | `OK` |
| `d1_bias_lag.jsonl` | 549 | `None` | `{}` | `OK` |
| `d1_bias_lag_recovery.jsonl` | 3 | `2026-05-04T08:03:31.297974+00:00` | `{'d1_bias_lag_recovery_v1': 3}` | `OK` |
| `databento_live_budget_ledger.jsonl` | 4 | `2026-05-04T23:37:15.740424+00:00` | `{'databento_live_budget_ledger_v1': 4}` | `OK` |
| `databento_live_confluence.jsonl` | 3 | `2026-05-04T23:37:15.739771+00:00` | `{'databento_live_confluence_v1': 3}` | `OK` |
| `databento_live_trigger_decisions.jsonl` | 425 | `2026-06-01T12:01:56.452656+00:00` | `{'databento_live_trigger_decision_v1': 425}` | `OK` |
| `decision_layer_diagnostics_join.jsonl` | 713 | `2026-06-01T18:07:53.372355+00:00` | `{'decision_layer_diagnostics_join_v1': 713}` | `ISSUES` |
| `es_mes_preregistration_status.jsonl` | 10 | `2026-06-01T00:37:08.864871+00:00` | `{'es_mes_preregistration_status_v1': 10}` | `OK` |
| `exit_management_shadow_status.jsonl` | 1201 | `2026-06-01T18:09:03.375151+00:00` | `{'exit_management_shadow_status_v1': 1201}` | `OK` |
| `external_source_blocker_status.jsonl` | 1050 | `2026-06-01T12:11:33.370375+00:00` | `{'external_source_blocker_status_v1': 1050}` | `ISSUES` |
| `fvg_ob_confluence.jsonl` | 517 | `2026-06-01T17:33:33.417959+00:00` | `{'fvg_ob_confluence_forward_v1': 517}` | `OK` |
| `fvg_ob_confluence_audit.jsonl` | 8732 | `2026-06-01T18:06:34.121616+00:00` | `{'fvg_ob_confluence_audit_v1': 6655, 'fvg_ob_confluence_audit_v2': 2077}` | `OK` |
| `fvg_ob_confluence_resolutions.jsonl` | 8235 | `2026-06-01T16:42:34.882178+00:00` | `{'fvg_ob_confluence_resolution_v1': 8235}` | `ISSUES` |
| `gbpjpy_proxy_gap_status.jsonl` | 50 | `2026-06-01T18:08:47.178379+00:00` | `{'gbpjpy_orderflow_proxy_gap_status_v1': 50}` | `OK` |
| `j46_j49_exit_comparator_audit.jsonl` | 6500 | `2026-06-01T19:46:11+00:00` | `{'j46_j49_exit_comparator_audit_v1': 6500}` | `ISSUES` |
| `live_candidate_opportunity_clusters.jsonl` | 7257 | `2026-06-01T11:55:58.546035+00:00` | `{'live_candidate_opportunity_cluster_v1': 7257}` | `ISSUES` |
| `live_candidate_strategy_rollups.jsonl` | 7051 | `2026-06-01T12:02:08.200496+00:00` | `{'live_candidate_strategy_rollup_v1': 7051}` | `ISSUES` |
| `live_mechanical_strategy_shadow_outcomes.jsonl` | 154992 | `2026-06-01T17:41:58.419361+00:00` | `{'live_mechanical_strategy_shadow_outcome_v1': 154992}` | `OK` |
| `live_structural_strategy_metadata.jsonl` | 5322 | `2026-06-01T11:39:08.035896+00:00` | `{'live_structural_strategy_metadata_v1': 5322}` | `OK` |
| `lto_blocked_lane_status.jsonl` | 3 | `2026-05-05T06:23:04.960252+00:00` | `{'lto_blocked_lane_status_v1': 3}` | `OK` |
| `mechanical_context_diagnostics_join.jsonl` | 6548 | `2026-06-01T18:07:58.277918+00:00` | `{'mechanical_context_diagnostics_join_v1': 6548}` | `OK` |
| `missed_opportunity_shadow.jsonl` | 7163 | `2026-06-01T11:53:57.849396+00:00` | `{'missed_opportunity_shadow_v1': 7163}` | `ISSUES` |
| `ml_shadow_predictions.jsonl` | 4009 | `2026-06-01T18:08:53.530372+00:00` | `{'ml_shadow_prediction_v1': 4009}` | `OK` |
| `ml_shadow_status.jsonl` | 175 | `2026-06-01T12:11:33.369898+00:00` | `{'ml_shadow_status_v1': 175}` | `ISSUES` |
| `nas100_orderflow_adverse_selection_status.jsonl` | 42 | `2026-05-31T23:01:59.952939+00:00` | `{'nas100_orderflow_adverse_selection_status_v1': 42}` | `OK` |
| `notification_queue_dead_zone_status.jsonl` | 26 | `2026-06-01T18:09:06.566300+00:00` | `{'notification_queue_dead_zone_status_v1': 26}` | `ISSUES` |
| `opportunity_lifecycle_audit.jsonl` | 7703 | `2026-06-01T18:03:38.071146+00:00` | `{'opportunity_lifecycle_audit_v1': 7703}` | `ISSUES` |
| `orderflow_primitives_status.jsonl` | 123 | `2026-06-01T18:08:52.693565+00:00` | `{'orderflow_primitives_status_v1': 123}` | `OK` |
| `pending_limit_lifecycle.jsonl` | 443 | `2026-06-01T18:46:07.191343+00:00` | `{'pending_limit_lifecycle_v1': 443}` | `OK` |
| `pending_limit_lifecycle_audit.jsonl` | 310 | `2026-06-01T18:03:47.420833+00:00` | `{'pending_limit_lifecycle_audit_v1': 310}` | `ISSUES` |
| `pending_limit_lifecycle_join_backfill.jsonl` | 817 | `2026-06-01T17:51:25.919311+00:00` | `{'pending_limit_lifecycle_join_backfill_v1': 817}` | `OK` |
| `prefill_delivery_path.jsonl` | 506 | `2026-06-01T17:33:33.415850+00:00` | `{'prefill_delivery_path_v1': 506}` | `OK` |
| `prefill_delivery_path_audit.jsonl` | 8765 | `2026-06-01T18:05:34.351722+00:00` | `{'prefill_delivery_path_audit_v1': 8765}` | `OK` |
| `prefill_delivery_path_resolutions.jsonl` | 8284 | `2026-06-01T16:38:19.553201+00:00` | `{'prefill_delivery_path_resolution_v1': 8284}` | `ISSUES` |
| `proxy_blocker_status.jsonl` | 175 | `2026-06-01T12:11:33.369136+00:00` | `{'proxy_blocker_status_v1': 175}` | `ISSUES` |
| `regime_decay_outcome_join.jsonl` | 6693 | `2026-06-01T18:07:48.032223+00:00` | `{'regime_decay_outcome_join_v1': 6693}` | `OK` |
| `s79_side_aware_risk_context.jsonl` | 1143 | `2026-06-01T18:07:45.570563+00:00` | `{'s79_side_aware_risk_context_v1': 1143}` | `OK` |
| `session_volatility_sweep_status.jsonl` | 32 | `2026-06-01T14:23:21.234077+00:00` | `{'session_volatility_sweep_status_v1': 32}` | `OK` |
| `shadow_observer_hardening_status.jsonl` | 94 | `2026-06-01T10:10:40.922516+00:00` | `{'shadow_observer_hardening_status_v1': 94}` | `ISSUES` |
| `shadow_observer_status.jsonl` | 4134 | `2026-05-13T00:13:19.824677+00:00` | `{'shadow_observer_status_v1': 4134}` | `ISSUES` |
| `shadow_observer_tick_enrichment.jsonl` | 88 | `2026-05-12T14:55:34.264707+00:00` | `{'shadow_observer_tick_enrichment_v1': 88}` | `OK` |
| `sierra_6b_si_depth_policy_status.jsonl` | 6 | `2026-05-31T23:02:04.513212+00:00` | `{'sierra_6b_si_depth_policy_status_v1': 6}` | `OK` |
| `sierra_confluence_source_status.jsonl` | 404 | `2026-06-01T12:02:02.911827+00:00` | `{'sierra_confluence_source_status_v1': 404}` | `OK` |
| `sierra_depth_enrichment_status.jsonl` | 55 | `2026-06-01T18:08:44.170673+00:00` | `{'sierra_depth_enrichment_status_v1': 55}` | `OK` |
| `sierra_depth_feature_snapshots.jsonl` | 664 | `2026-06-01T18:08:43.267774+00:00` | `{'sierra_depth_feature_snapshot_v1': 664}` | `OK` |
| `sierra_proxy_registry_status.jsonl` | 10110 | `2026-06-01T18:08:35.892463+00:00` | `{'sierra_proxy_registry_status_v1': 10110}` | `OK` |
| `storage_retention_status.jsonl` | 12 | `2026-06-01T00:05:07.920778+00:00` | `{'storage_retention_status_v1': 12}` | `OK` |
| `strategy_follow_candidates.jsonl` | 506 | `2026-06-01T17:33:33.407167+00:00` | `{'strategy_follow_candidate_v1': 506}` | `ISSUES` |
| `strategy_follow_evaluations.jsonl` | 4343 | `2026-06-01T19:00:11.348282+00:00` | `{'strategy_follow_evaluation_v1': 4343}` | `OK` |
| `trade_index_lifecycle_audit.jsonl` | 880 | `2026-06-01T19:02:02.922240+00:00` | `{'trade_index_lifecycle_audit_v1': 880}` | `OK` |
| `v2_structural_selector_readiness.jsonl` | 214 | `2026-06-01T18:07:34.748570+00:00` | `{'v2_structural_selector_readiness_v1': 214}` | `OK` |
| `v2b_forward_pair_resolution_audit.jsonl` | 8764 | `2026-06-01T18:03:59.486658+00:00` | `{'v2b_forward_pair_resolution_audit_v1': 8764}` | `OK` |
| `v2b_forward_pair_resolutions.jsonl` | 8271 | `2026-06-01T16:25:08.924992+00:00` | `{'v2b_forward_pair_resolution_v1': 8271}` | `ISSUES` |
| `v2b_forward_pairs.jsonl` | 506 | `2026-06-01T17:33:33.413228+00:00` | `{'v2b_forward_pair_v1': 506}` | `OK` |
| `xauusd_same_market_extension_status.jsonl` | 139 | `2026-06-01T00:37:06.445030+00:00` | `{'xauusd_same_market_extension_status_v1': 139}` | `OK` |

## Documented Waiting Lanes

| Log | Reason |
|---|---|
| `ai_decision_trace.jsonl` | hash-only AI decision trace rows are emitted only on post-patch PrimaryAnalyzer calls; no rows are expected while the research runtime halt is active |
| `be_shadow_log.jsonl` | actual BE event rows only; no-event proof lives in exit_management_shadow_status.jsonl |
| `partial_close_shadow_log.jsonl` | actual partial-close trigger rows only; no-event proof lives in exit_management_shadow_status.jsonl |

## Issues

| Severity | Code | Path | Line | Message |
|---|---|---|---:|---|
| `CRITICAL` | `INVALID_JSON` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\account_pnl_truth_reconciliation.jsonl` | 1 | Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0) |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 2 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 3 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 4 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 5 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 6 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 7 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 8 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 9 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 10 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 11 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 12 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 13 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 14 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 15 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 16 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 17 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 18 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 19 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 20 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 21 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 22 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 23 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 24 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 25 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 26 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 27 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 28 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/account_pnl_truth_reconciliation.jsonl` | 29 | missing or empty required field promotion_verdict |
| `CRITICAL` | `INVALID_JSON` | `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\broker_actual_r_audit.jsonl` | 1 | Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0) |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 2 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 3 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 4 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 5 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 6 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 7 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 8 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 9 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 10 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 11 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 12 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 13 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 14 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 15 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 16 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 17 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 18 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 19 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 20 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 21 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 22 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 23 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 24 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 25 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 26 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 27 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 28 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 29 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 30 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 31 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 32 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 33 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 34 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 35 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 36 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 37 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 38 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 39 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 40 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 41 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 42 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 43 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 44 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 45 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 46 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 47 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 48 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 49 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 50 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 51 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 52 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 53 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 54 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 55 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 56 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 57 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 58 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 59 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 60 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 61 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 62 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 63 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 64 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 65 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 66 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 67 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 68 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 69 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 70 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 71 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 72 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 73 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 74 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 75 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 76 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 77 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 78 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 79 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 80 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 81 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 82 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 83 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 84 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 85 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 86 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 87 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 88 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 89 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 90 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 91 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 92 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 93 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 94 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 95 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 96 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 97 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 98 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 99 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 100 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 101 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 102 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 103 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 104 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 105 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 106 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 107 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 108 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 109 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 110 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 111 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 112 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 113 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 114 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 115 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 116 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 117 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 118 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 119 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 120 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 121 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 122 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 123 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 124 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 125 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 126 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 127 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 128 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 129 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 130 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 131 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 132 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 133 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 134 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 135 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 136 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 137 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 138 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 139 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 140 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 141 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 142 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 143 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 144 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 145 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 146 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 147 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 148 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 149 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 150 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 151 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 152 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 153 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 154 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 155 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 156 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 157 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 158 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 159 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 160 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 161 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 162 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 163 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 164 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 165 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 166 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 167 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 168 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 169 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 170 | missing or empty required field promotion_verdict |
| `SERIOUS` | `MISSING_REQUIRED_FIELD` | `shadow_logs/broker_actual_r_audit.jsonl` | 171 | missing or empty required field promotion_verdict |

Only first 200 issues shown; JSON contains all `161194` issues.

## Notes

- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, J46/J49 exit-comparator audit coverage, S79/side-aware risk-context coverage, AI narrowing shadow-evaluation coverage, exit-management no-event/status coverage, session-volatility/sweep cadence coverage, shadow-observer safety flags.
- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.
