# GTOS Daily Monitoring Checklist - 2026-05-05

**Schema:** `gtos_daily_monitoring_checklist_v1`
**Generated:** `2026-05-06T00:26:19.475267+00:00`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Required Commands

### Baseline

- `python scripts/generate_live_state.py`
- `python scripts/watchdog_e2e_verify.py --verbose`
- `python scripts/verify_forward_capture_readiness.py --output-json research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md`
- `python scripts/audit_live_shadow_followup_coverage.py --output-json research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json --output-md research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`

### Live Shadow Sequence

- `python scripts/run_live_monitoring_maintenance.py --max-hours 72 --step-timeout-seconds 300`
- `python scripts/_live_monitor_iter.py`
- `python scripts/follow_live_candidate_paths.py --max-hours 12`
- `python scripts/backfill_candidate_registry_audit.py`
- `python scripts/backfill_candidate_path_contract_audit.py`
- `python scripts/backfill_opportunity_lifecycle_audit.py`
- `python scripts/backfill_pending_limit_lifecycle_audit.py`
- `python scripts/backfill_v2b_forward_pair_resolution_audit.py`
- `python scripts/audit_v2_structural_selector_readiness.py`
- `python scripts/backfill_prefill_delivery_path_audit.py`
- `python scripts/backfill_fvg_ob_confluence_audit.py`
- `python scripts/backfill_context_control_audit.py`
- `python scripts/backfill_broker_actual_r_audit.py`
- `python scripts/backfill_j46_j49_exit_comparator_audit.py`
- `python scripts/backfill_s79_side_aware_risk_context.py`
- `python scripts/backfill_regime_decay_outcome_join.py`
- `python scripts/backfill_decision_layer_diagnostics_join.py`
- `python scripts/backfill_mechanical_context_diagnostics_join.py`
- `python scripts/backfill_k55_ml_shadow_predictions.py`
- `python scripts/audit_lto_blocked_lane_readiness.py`
- `python scripts/audit_xauusd_same_market_extension.py`
- `python scripts/audit_es_mes_preregistration.py`
- `python scripts/audit_shadow_observer_hardening.py`
- `python scripts/backfill_account_pnl_truth_reconciliation.py`
- `python scripts/backfill_trade_index_lifecycle_audit.py`
- `python scripts/audit_sierra_proxy_registry.py`
- `python scripts/enrich_sierra_live_candidate_depth_features.py --max-hours 24 --max-file-size-mb 128 --max-per-symbol 2 --limit 6`
- `python scripts/audit_sierra_live_depth_confluence.py`
- `python scripts/audit_nas100_orderflow_adverse_selection.py`
- `python scripts/audit_gbpjpy_orderflow_proxy_gap.py`
- `python scripts/audit_sierra_6b_si_depth_policy.py`
- `python scripts/audit_orderflow_primitives.py`
- `python scripts/backfill_exit_management_no_event_status.py`
- `python scripts/audit_session_volatility_sweep_status.py`
- `python scripts/audit_canary_restart_governance.py`
- `python scripts/audit_notification_queue_dead_zone.py`
- `python scripts/audit_storage_retention.py --dry-run`
- `python scripts/summarize_live_shadow_opportunities.py`
- `python scripts/verify_shadow_log_integrity.py`
- `python scripts/audit_live_shadow_data_health.py`

### Research Intelligence Sequence

- `python scripts/backfill_m15_choch_diagnostics.py`
- `python scripts/backfill_continuation_no_retrace_shadow.py`
- `python scripts/backfill_xagusd_fresh_ob_late_ny.py`

### Source Governance Sequence

- `python scripts/build_lto031_lto032_source_contract_registry.py`
- `python scripts/build_lto031_lto032_free_public_source_manifests.py`
- `python scripts/build_lto031_lto032_databento_credit_replay_manifests.py`
- `python scripts/build_lto031_lto032_sierra_scid_footprint_profile_plan.py`
- `python scripts/build_lto032_options_gamma_vrp_source_manifests.py`
- `python scripts/build_k55_source_bundle_integration_plan.py`

### Additional Runbook Commands

- `python scripts/watchdog_e2e_verify.py --verbose`
- `python scripts/verify_forward_capture_readiness.py --output-json research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md`
- `python scripts/audit_live_shadow_followup_coverage.py --output-json research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json --output-md research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`
- `python scripts/run_shadow_observer.py --mode live --profile redacted_account --once`
- `python scripts/run_shadow_observer.py --mode live --profile redacted_account`
- `python scripts/run_shadow_observer.py --mode live --profile redacted_account --symbols EURUSD,GER40`
- `python scripts/verify_forward_capture_readiness.py`

## Expected Lanes

| Follow ID | LTO | Status | Row paths |
|---|---|---|---|
| `LIVE-FOLLOW-032` | `LTO-040` Research Queue / Master Backlog Integration | `DONE` | `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`, `scripts/_live_monitor_iter.py` |
| `LIVE-FOLLOW-032` | `LTO-034` Live Monitoring Goal / Runbook Persistence | `DONE` | `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`, `scripts/_live_monitor_iter.py` |
| `LIVE-FOLLOW-001` | `LTO-039` Shadow Log Integrity And Semantic Data Health | `DONE` | `shadow_logs/live_candidate_opportunity_clusters.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl` |
| `LIVE-FOLLOW-003B` | `LTO-039` Shadow Log Integrity And Semantic Data Health | `DONE` | `shadow_logs/live_candidate_opportunity_clusters.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl` |
| `LIVE-FOLLOW-001` | `LTO-001` AI-Independent MSO Evaluation Anchor | `DONE` | `shadow_logs/strategy_follow_evaluations.jsonl` |
| `LIVE-FOLLOW-002` | `LTO-002` AI Candidate Registry And External Confluence | `DONE` | `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-003` | `LTO-003` Candidate Path Follow | `DONE` | `shadow_logs/candidate_path_follow.jsonl` |
| `LIVE-FOLLOW-003B` | `LTO-004` Opportunity Duplicate Lifecycle | `DONE` | `shadow_logs/live_candidate_opportunity_clusters.jsonl` |
| `LIVE-FOLLOW-004` | `LTO-005` Pending-Limit Lifecycle Truth | `DONE` | `shadow_logs/pending_limit_lifecycle.jsonl` |
| `LIVE-FOLLOW-003` | `LTO-006` V2b Forward Pair Resolution | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl`, `shadow_logs/v2b_forward_pairs.jsonl` |
| `LIVE-FOLLOW-005` | `LTO-006` V2b Forward Pair Resolution | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl`, `shadow_logs/v2b_forward_pairs.jsonl` |
| `LIVE-FOLLOW-025` | `LTO-006` V2b Forward Pair Resolution | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl`, `shadow_logs/v2b_forward_pairs.jsonl` |
| `LIVE-FOLLOW-003` | `LTO-007` V3 / Pre-Fill Delivery Path | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/prefill_delivery_path.jsonl` |
| `LIVE-FOLLOW-006` | `LTO-007` V3 / Pre-Fill Delivery Path | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/prefill_delivery_path.jsonl` |
| `LIVE-FOLLOW-007` | `LTO-008` FVG/OB Confluence And Disagreement | `DONE` | `shadow_logs/fvg_ob_confluence.jsonl` |
| `LIVE-FOLLOW-008` | `LTO-009` Context/Control Ledger For CL/ZN/VIX/VXM | `DONE` | `shadow_logs/context_control_ledger.jsonl`, `shadow_logs/shadow_observer_hardening_status.jsonl` |
| `LIVE-FOLLOW-012` | `LTO-015` Broker Actual-R, Slippage, Cost, And Exit Accounting | `DONE` | `shadow_logs/be_shadow_log.jsonl`, `shadow_logs/daily_pnl.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/equity_read_anomalies.jsonl`, `shadow_logs/j46_j49_shadow_outcomes.jsonl`, `shadow_logs/partial_close_shadow_log.jsonl`, `shadow_logs/slippage.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-013` | `LTO-015` Broker Actual-R, Slippage, Cost, And Exit Accounting | `DONE` | `shadow_logs/be_shadow_log.jsonl`, `shadow_logs/daily_pnl.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/equity_read_anomalies.jsonl`, `shadow_logs/j46_j49_shadow_outcomes.jsonl`, `shadow_logs/partial_close_shadow_log.jsonl`, `shadow_logs/slippage.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-018` | `LTO-015` Broker Actual-R, Slippage, Cost, And Exit Accounting | `DONE` | `shadow_logs/be_shadow_log.jsonl`, `shadow_logs/daily_pnl.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/equity_read_anomalies.jsonl`, `shadow_logs/j46_j49_shadow_outcomes.jsonl`, `shadow_logs/partial_close_shadow_log.jsonl`, `shadow_logs/slippage.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-023` | `LTO-015` Broker Actual-R, Slippage, Cost, And Exit Accounting | `DONE` | `shadow_logs/be_shadow_log.jsonl`, `shadow_logs/daily_pnl.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/equity_read_anomalies.jsonl`, `shadow_logs/j46_j49_shadow_outcomes.jsonl`, `shadow_logs/partial_close_shadow_log.jsonl`, `shadow_logs/slippage.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-012` | `LTO-025` Account/PnL Truth And Evidence-Class Separation | `DONE` | `shadow_logs/daily_pnl.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/equity_read_anomalies.jsonl`, `shadow_logs/j46_j49_shadow_outcomes.jsonl`, `shadow_logs/slippage.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-023` | `LTO-025` Account/PnL Truth And Evidence-Class Separation | `DONE` | `shadow_logs/daily_pnl.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/equity_read_anomalies.jsonl`, `shadow_logs/j46_j49_shadow_outcomes.jsonl`, `shadow_logs/slippage.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-004` | `LTO-026` Trade Index Staleness And Lifecycle Completeness | `DONE` | `knowledge_base/trade_records/_trade_index.json`, `shadow_logs/pending_limit_lifecycle.jsonl` |
| `LIVE-FOLLOW-024` | `LTO-026` Trade Index Staleness And Lifecycle Completeness | `DONE` | `knowledge_base/trade_records/_trade_index.json`, `shadow_logs/pending_limit_lifecycle.jsonl` |
| `LIVE-FOLLOW-009` | `LTO-010` Databento Targeted Live Confluence | `DONE` | `shadow_logs/databento_live_confluence.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-011` | `LTO-010` Databento Targeted Live Confluence | `DONE` | `shadow_logs/databento_live_confluence.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-031` | `LTO-010` Databento Targeted Live Confluence | `DONE` | `shadow_logs/databento_live_confluence.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-011` | `LTO-011` NAS100/NQ Orderflow Adverse-Selection Diagnostic | `DONE` | `shadow_logs/databento_live_confluence.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-010` | `LTO-012` Sierra Local Depth Confluence | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-002` | `LTO-013` Sierra Source/Parity Registry | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-010` | `LTO-013` Sierra Source/Parity Registry | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-028` | `LTO-013` Sierra Source/Parity Registry | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-022` | `LTO-014` GBPJPY Sierra/Databento Proxy Gap | `DONE` | - |
| `LIVE-FOLLOW-028` | `LTO-030` 6B Sampling Alignment And SI Depth Definition | `DONE` | `shadow_logs/candidate_path_follow.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-029` | `LTO-031` External Feed Blockers | `SOURCE_BLOCKED` | - |
| `LIVE-FOLLOW-030` | `LTO-032` Options/Gamma, VRP, FlashAlpha Basic GEX | `SOURCE_BLOCKED` | - |
| `LIVE-FOLLOW-009` | `LTO-033` X-1/X-2/X-3 Imbalance / Meta-Order-Flow Primitives | `DONE` | `shadow_logs/databento_live_confluence.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-031` | `LTO-033` X-1/X-2/X-3 Imbalance / Meta-Order-Flow Primitives | `DONE` | `shadow_logs/databento_live_confluence.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-018` | `LTO-021` Exit-Management Shadows: BE, Partial Close, Time In Trade | `DONE` | `shadow_logs/be_shadow_log.jsonl`, `shadow_logs/partial_close_shadow_log.jsonl`, `shadow_logs/time_in_trade.jsonl` |
| `LIVE-FOLLOW-019` | `LTO-022` Session Volatility And US30 Sweep Divergence | `DONE` | `shadow_logs/session_volatility_log.csv`, `shadow_logs/sweep_divergence_log.csv` |
| - | `LTO-036` Watchdog, Canary Skip, And Restart Governance | `DONE` | - |
| - | `LTO-037` Notification Queue Dead-Zone Policy | `DONE` | - |
| - | `LTO-038` Storage, Retention, And Non-Overwrite | `DONE` | - |
| `LIVE-FOLLOW-013` | `LTO-016` J46-J49 Exit Policy Comparator | `DONE` | `shadow_logs/j46_j49_shadow_outcomes.jsonl` |
| `LIVE-FOLLOW-014` | `LTO-017` S79 / Side-Aware Compounding Context | `DONE` | `pipeline_state/side_aware_sprt_state.json`, `shadow_logs/daily_pnl_history.jsonl`, `shadow_logs/strategy_follow_candidates.jsonl` |
| `LIVE-FOLLOW-015` | `LTO-018` Regime Classifier And Monthly Decay | `DONE` | `shadow_logs/ob_continuation_daily.csv`, `shadow_logs/regime_classifications.jsonl` |
| `LIVE-FOLLOW-016` | `LTO-019` Decision-Layer Diagnostics | `DONE` | `shadow_logs/candidate_features_log.jsonl`, `shadow_logs/d1_bias_lag.jsonl`, `shadow_logs/direction_emission_xau_audit.jsonl`, `shadow_logs/sl_beyond_ob_decisions.jsonl`, `shadow_logs/touch_count_gate_decisions.jsonl` |
| `LIVE-FOLLOW-017` | `LTO-020` Mechanical Baselines, Proximity, Liquidity, Displacement, Structure Divergence | `DONE` | `shadow_logs/displacement_events.jsonl`, `shadow_logs/dumb_baseline_hypotheticals.jsonl`, `shadow_logs/liquidity_distance_log.jsonl`, `shadow_logs/proximity_shadow_log.jsonl`, `shadow_logs/structure_detector_divergences.jsonl` |
| `LIVE-FOLLOW-020` | `LTO-023` K55 / ML Shadow | `DONE` | `shadow_logs/ml_shadow_predictions.jsonl` |
| `LIVE-FOLLOW-021` | `LTO-024` Component 3B / Tool Grounding / Reflexion | `APPROVAL_BLOCKED` | - |
| `LIVE-FOLLOW-005` | `LTO-027` V2 Structural Oracle / As-Of Selector | `DONE` | `shadow_logs/strategy_follow_evaluations.jsonl`, `shadow_logs/v2b_forward_pairs.jsonl` |
| `LIVE-FOLLOW-025` | `LTO-027` V2 Structural Oracle / As-Of Selector | `DONE` | `shadow_logs/strategy_follow_evaluations.jsonl`, `shadow_logs/v2b_forward_pairs.jsonl` |
| `LIVE-FOLLOW-026` | `LTO-028` XAUUSD Same-Market Structural Path Extension | `DONE` | `shadow_logs/strategy_follow_candidates.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl`, `shadow_logs/xauusd_same_market_extension_status.jsonl` |
| `LIVE-FOLLOW-027` | `LTO-029` ES/MES Strategy-Cohort Pre-Registration | `DONE` | `shadow_logs/es_mes_preregistration_status.jsonl` |
| `LIVE-FOLLOW-008` | `LTO-035` No-AI MSO Shadow Observer Instruments | `DONE` | `shadow_logs/context_control_ledger.jsonl`, `shadow_logs/shadow_observer_hardening_status.jsonl`, `shadow_logs/shadow_observer_status.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl` |
| `LIVE-FOLLOW-033` | `LTO-035` No-AI MSO Shadow Observer Instruments | `DONE` | `shadow_logs/context_control_ledger.jsonl`, `shadow_logs/shadow_observer_hardening_status.jsonl`, `shadow_logs/shadow_observer_status.jsonl`, `shadow_logs/strategy_follow_evaluations.jsonl` |
| `NEXT-IMPROVEMENT-2B` | `NEXT-M15-CHOCH` M15 CHoCH Diagnostic Expansion | `RESEARCH_SHADOW_ONLY` | `shadow_logs/m15_choch_diagnostic_audit.jsonl`, `research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.json` |
| `NEXT-IMPROVEMENT-2A` | `NEXT-CONTINUATION-NO-RETRACE` Continuation / No-Retrace Shadow Lane | `RESEARCH_SHADOW_ONLY` | `shadow_logs/continuation_no_retrace_candidates.jsonl`, `shadow_logs/continuation_no_retrace_resolutions.jsonl`, `research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.json` |
| `NEXT-IMPROVEMENT-2C` | `NEXT-XAGUSD-FRESH-OB` XAGUSD Fresh-OB Late-NY Tracking | `RESEARCH_SHADOW_ONLY` | `shadow_logs/xagusd_fresh_ob_late_ny.jsonl`, `research/program_control/XAGUSD_FRESH_OB_LATE_NY_STATUS_2026-05-06.json` |
| `SOURCE-GOVERNANCE-2026-05-06` | `LTO-031/LTO-032-P0-P4` LTO031/LTO032 Source Contracts And Manifests | `SOURCE_GOVERNANCE_READY_SHADOW_ONLY` | `research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json`, `research/program_control/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.json`, `research/program_control/LTO031_LTO032_DATABENTO_CREDIT_REPLAY_MANIFESTS_2026-05-06.json`, `research/program_control/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.json`, `research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.json` |
| `K55-SOURCE-BUNDLE-2026-05-06` | `LTO-023/LTO-031/LTO-032-P5` K55 Source-Bundle Governance | `K55_SOURCE_BUNDLE_GOVERNANCE_READY_SHADOW_ONLY` | `research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.json`, `research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md` |

## Restart Policy

- `production_orchestrators`: Restart only after additive capture code is changed and tests pass, or after a verified active-KZ failure. Use the existing durable Windows scheduled task when a full fleet reload is required.
- `shadow_observer`: Restart after observer schema/lifecycle changes or verified observer staleness; keep no-AI/no-order/no-Databento boundaries intact.
- `watchdog_notification`: Restart or wait for scheduled watchdog only after dead-zone policy changes; do not force notification workers during expected dead-zone cleanup.
- `sierra`: Do not restart Sierra unless file capture stalls or chartbook/source setup requires operator-side action.
- `databento`: Databento live collection is owner-approved for LTO010 value-max forward confluence. Start only through the registered collector when a trigger exists, collector env/API key are present, and cost/cooldown caps pass; every paid call must land in the confluence and budget ledgers with candidate/trigger join keys.

## Safety Counters

| Counter | Required value |
|---|---:|
| `ai_calls` | 0 |
| `canary_calls` | 0 |
| `order_calls` | 0 |
| `paid_data_calls` | 0 |

## Cadence

- Active kill zone: every 5 minutes
- Between kill zones: every 15 minutes
- Owner update: every 30 minutes and immediately for verified URGENT/SERIOUS findings

## Blocked Lane Handling

- `SOURCE_NOT_CAPTURED`: preserve blocker unless exact point-in-time source evidence exists
- `SOURCE_BLOCKED`: write/read blocker rows or reports; do not infer values
- `APPROVAL_BLOCKED`: do not activate or call blocked service/model without owner approval
- `EVENT_WAITING`: emit no-event/status proof where applicable
