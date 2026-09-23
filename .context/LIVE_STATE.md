# GTOS LIVE STATE (auto-generated — DO NOT HAND-EDIT)

**Generated:** 2026-08-20 11:35:10 UTC
**HEAD:** `459b2da33 F5 ceremony 20260825 executed 20260819 (owner GO): three WIDEN tags beside incumbents, locked_r rider, known-sleeves fix; token reminted to 2026-09-18; agent_config.yaml deliberately NOT committed (digest binds dirty bytes)`
**Latest handoff on disk:** `.context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md`

This file is the single source of truth for the _current_ GTOS state. It is rebuilt by `scripts/generate_live_state.py` from git + config + source. Handoffs are historical snapshots and will NOT reflect post-session changes; trust this file over any handoff when they disagree.

**Regenerate at session start, and again before producing any status/backlog synthesis.**

---

## Research context freshness

Curated research context lives in `.context/00_core/research_operating_doctrine.md` and `.context/00_core/research_current_state.md`. These docs are agent-updated, not auto-generated; this section only audits whether the current-state doc is stale versus the latest research-relevant commit.

| Check | Value |
|-------|-------|
| Status | `STALE_UPDATE_RESEARCH_CURRENT_STATE` |
| Latest research-relevant commit | `358398603 Compose F5 live-flow and Q1/Q2 shadow observation stack` |
| Current-state captured commit | `7ff640a8a` |
| Doctrine doc exists | `True` |
| Current-state doc exists | `True` |
| Mandatory references ok | `True` |
| Missing references | `none` |

**Action:** read the newer research artifacts directly and update `.context/00_core/research_current_state.md` before relying on its summary.

## Git status

```
 M config/agent_config.yaml
 D knowledge_base/meta/AUTOSTART_DISABLED.flag
 D pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag
 D pipeline_state/RESEARCH_RUNTIME_HALT.flag
 M scripts/capture_broker_swap_table.py
 M scripts/f5_keepalive_watchdog.ps1
 M shadow_logs/daily_pnl.json
 M shadow_logs/daily_pnl_history.jsonl
 M src/components/execution.py
 M src/components/execution_manager_v4.py
 M src/components/ultimate_book/book_owner.py
 M src/components/ultimate_book/governor_state.py
 M src/components/ultimate_book/live_flow.py
 M src/components/ultimate_book/order_router.py
 M src/components/ultimate_book/packet_emit_on_change.py
 M tests/test_execution_manager_v4.py
 M tests/ultimate_book/test_book_owner.py
 M tests/ultimate_book/test_f5_minimal_size.py
 M tests/ultimate_book/test_frozen_price_intent.py
 M tests/ultimate_book/test_governor_baseline.py
 M tests/ultimate_book/test_packet_emit_on_change.py
 M tests/ultimate_book/test_risk_unit_floor.py
?? INTENT_HEAD.txt
?? config/agent_config.yaml.bak-blossom-20260818-045744
?? judgment/
?? pipeline_state/_cleared_flags_20260812/
?? pipeline_state/f5_ceremony_20260825_prev_tags.txt
?? pipeline_state/f5_keepalive_expected_argv.json
?? pipeline_state/f5_keepalive_state.json
?? pipeline_state/operator_profile/notification_queue.jsonl
?? pipeline_state/runtime_control_atomic_halt_audit.jsonl
?? pipeline_state/ultimate_book/
?? scripts/gtos_m1_archive.ps1
?? scripts/gtos_swap_snapshot.ps1
?? scripts/gtos_token_verify_probe.ps1
?? scripts/gtos_token_verify_probe.py
?? scripts/gtos_token_verify_probe_task.xml
?? shadow_logs/broker_order_lifecycle_capture_v4.jsonl
?? shadow_logs/execution_manager_v4_decisions.jsonl
?? shadow_logs/f5_keepalive_LATEST-ALERT.txt
?? shadow_logs/f5_keepalive_flaps.jsonl
?? shadow_logs/f5_minimal/
?? shadow_logs/slippage_runtime.jsonl
?? shadow_logs/token_verify_probe.jsonl
?? shadow_logs/ultimate_book_launcher.jsonl
?? shadow_logs/ultimate_book_runtime_learning_packets.jsonl
?? shadow_logs/ultimate_book_runtime_learning_packets.jsonl.quarantine.jsonl
?? src/components/execution.py.b64.c0a38041abec492784ae1226801703f5
?? src/utils/broker_accounting.py
?? tests/test_broker_accounting.py
?? tests/ultimate_book/test_run_book_env_authority.py
```

### Uncommitted diff (tracked files, bounded stat)
```
 config/agent_config.yaml                           | 162 +++++-----
 knowledge_base/meta/AUTOSTART_DISABLED.flag        |   4 -
 pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag      |   4 -
 pipeline_state/RESEARCH_RUNTIME_HALT.flag          |   4 -
 scripts/capture_broker_swap_table.py               |  37 ++-
 scripts/f5_keepalive_watchdog.ps1                  |  20 +-
 shadow_logs/daily_pnl.json                         | 343 ++-------------------
 shadow_logs/daily_pnl_history.jsonl                |   4 +-
 src/components/execution.py                        |  90 ++++--
 src/components/execution_manager_v4.py             |   2 +-
 src/components/ultimate_book/book_owner.py         |  98 +++++-
 src/components/ultimate_book/governor_state.py     |  27 +-
 src/components/ultimate_book/live_flow.py          |   3 +-
 src/components/ultimate_book/order_router.py       |  57 +++-
 .../ultimate_book/packet_emit_on_change.py         |  24 +-
 tests/test_execution_manager_v4.py                 |  27 ++
 tests/ultimate_book/test_book_owner.py             |  16 +
 tests/ultimate_book/test_f5_minimal_size.py        |  41 ++-
 tests/ultimate_book/test_frozen_price_intent.py    |  86 +++++-
 tests/ultimate_book/test_governor_baseline.py      |  28 +-
 tests/ultimate_book/test_packet_emit_on_change.py  |  51 ++-
 tests/ultimate_book/test_risk_unit_floor.py        |  16 +
 22 files changed, 642 insertions(+), 502 deletions(-)
```

## Git LFS hydration

| Check | Value |
|-------|-------|
| Status | `degraded_lfs_inventory:[TIMEOUT after 8s]` |
| LFS tracked rows | `unknown` |
| Hydrated payload rows | `unknown` |
| Sparse checkout active | `False` |
| Sparse-excluded LFS rows | `0` |
| Missing pointer-only rows | `unknown` |
| Checked key paths in degraded mode | `0` |
| Pointer key paths in degraded mode | `10` |
| Missing key paths in degraded mode | `0` |

Key runtime/research LFS paths:

| Path | Hydration status |
|------|------------------|
| `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/gtos_vnext_runtime_decisions.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/strategy_follow_evaluations.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/gtos_vnext_replacement_monitoring.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/pending_limit_lifecycle.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/ml_shadow_predictions.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/v2b_forward_pair_resolution_audit.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/live_candidate_strategy_rollups.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `shadow_logs/prefill_delivery_path_audit.jsonl` | `present_as_lfs_pointer_inventory_degraded` |
| `research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json` | `present_as_lfs_pointer_inventory_degraded` |

**Action:** full `git lfs ls-files --long` did not finish inside the bounded live-state timeout. Treat repository-wide LFS counts as unknown in this run; use the key-path rows below plus route-specific selective hydration before claiming row-level facts from LFS-backed files.

## Last 20 runtime/research commits

```
459b2da33 F5 ceremony 20260825 executed 20260819 (owner GO): three WIDEN tags beside incumbents, locked_r rider, known-sleeves fix; token reminted to 2026-09-18; agent_config.yaml deliberately NOT committed (digest binds dirty bytes)
1b2ca2439 FrozenPriceIntent: name generation terminals on the cycle reason; keep the last closed H4 at session close.
2e3b2010d FrozenPriceIntent: persist a quote series so harvest can tell poll from tax
b32d2b2f9 FrozenPriceIntent: name the spread sample min-over-1s so a GBPJPY flicker is not a refuse.
671e19cb4 FrozenPriceIntent: 2-4 pip 5-digit FX is MODEL_INPUT_INVALID, not a quote skip.
ded7eca57 snapshot: armed FrozenPriceIntent V1 overlay on f5-live
d2d22c1a2 fix(f5): recover poisoned broker time offsets
f2d117c11 Fix F5 status for broker-step underfill
d7d1a4cfb Bind F5 launch and broker exposure contract
358398603 Compose F5 live-flow and Q1/Q2 shadow observation stack
bdd8f7ded Propagate F5 operator label to system alerts
3304401bc Report precise F5 pretrade cost refusals
42e679663 Fix F5 conviction to track accepted placements
6514a55e7 book_engine: count the two silent generation drops, so a starved sleeve stops looking like a quiet market
5e9c01904 F5: label experiment alerts, and fix a sizing check that would have false-alarmed
af93664cf Armed set: sync repo declaration to live host — THREE sleeves, not four
fc783ceae F5 A/B result: 34 bad -> 33 bad, 0 regressed, 1 fixed, +79 net passing
59b201829 F5 landing record: what was landed, what was measured, and the two owner-facing items
843fca410 Test suite green: report — 51 bad → 0, and six category-1 defects
7c9db9543 Suite green 7: two ceremony packages measured today's mainline instead of their own moment
```

## Active config (`config\agent_config.yaml`)

| Setting | Key | Value |
|---------|-----|-------|
| Framework(s) enabled | `model_a.enabled_frameworks` | `['ob_retest', 'fvg_fill', 'breaker_re_entry']` |
| Risk % / trade | `risk.risk_per_trade_pct` | `2.0` |
| Max daily loss % | `risk.max_daily_loss_pct` | `4.0` |
| Max concurrent positions | `risk.max_concurrent` | _missing_ |
| Min R:R | `risk.min_rr` | `1.5` |
| SL absolute min | `risk.sl_absolute_min` | `5.0` |
| DD reduction threshold | `drawdown_reduction.threshold` | `0.08` |
| DD reduced risk % | `drawdown_reduction.reduced_risk_pct` | `0.5` |
| Gap filter max % | `filters.max_gap_pct` | `1.5` |
| OB SL exception | `gate1.ob_retest_sl_exception` | `True` |
| OB SL min buffer ATR | `gate1.ob_retest_sl_min_buffer_atr` | `0.5` |
| Liquidity cluster gate | `gate1.sl_liquidity_cluster_enabled` | `False` |
| Liquidity cluster margin ATR | `gate1.sl_liquidity_cluster_margin_atr` | `0.5` |
| AI primary model | `ai.primary_model` | `claude-sonnet-4-6` |
| AI effort | `ai.primary_effort` | `max` |
| API timeout (s) | `ai.api_timeout_seconds` | `90` |
| Session memory | `session_memory_enabled` | `False` |
| Confidence filter mode | `confidence_filter_mode` | `shadow` |
| News filter | `news_filter.enabled` | `True` |
| Deployment phase | `deployment.phase` | `3` |
| Budget monthly cap (USD) | `budget.monthly_cap_usd` | `50.0` |

## Config-flag enforcement check

For each flag: count of matches in `src/`. **`0` = flag may be cosmetic — investigate before relying on it.** A non-zero count is necessary but not sufficient — the grep can hit logging strings, etc. Treat this as a starter signal, not proof.

| Flag | Config value | src/ matches | Description |
|------|--------------|--------------|-------------|
| `deployment.phase` | `3` | 29 | Paper/live mode flag |
| `gate1.ob_retest_sl_exception` | `True` | 20 | sl_too_tight OB bypass |
| `gate1.ob_retest_sl_min_buffer_atr` | `0.5` | 9 | Apr 16 sweep margin (inside exception) |
| `gate1.sl_liquidity_cluster_enabled` | `False` | 3 | Liquidity cluster reject gate |
| `session_memory_enabled` | `False` | 3 | T2b session memory disable |
| `news_filter.enabled` | `True` | 3 | News filter toggle |
| `drawdown_reduction.threshold` | `0.08` | 2 | H29 DD risk reduction |
| `budget.monthly_cap_usd` | `50.0` | 389 | API budget cap |
| `filters.max_gap_pct` | `1.5` | 11 | Gap filter |
| `confidence_filter_mode` | `shadow` | 5 | Confidence filter (shadow/live) |

## Active gates (`src/components/permissions.py`)

- `check_permissions` — line 99
- `_reject_if_runtime_halted` — line 145
- `_reject_if_trading_disabled` — line 206
- `_reject_if_killed_instrument` — line 248
- `_reject_if_deployment_phase_blocked` — line 287
- `_reject_if_vnext_prop_safe_selector_missing_or_blocked` — line 494
- `_reject_if_prop_firm_headroom_snapshot_missing_or_invalid` — line 585
- `_reject_if_scheduler_v4_not_selected_authority` — line 930
- `_reject_if_vnext_broker_net_pretrade_cost_refused` — line 1062
- `_reject_if_same_symbol_vnext_lifecycle_conflict` — line 1203
- `_reject_if_concurrent_cap_reached` — line 1340
- `_reject_if_cross_instrument_correlation_excess` — line 1384
- `_reject_if_market_whiteboard_v2_blocks` — line 1444
- `_reject_if_dormant` — line 1494
- `_reject_if_touch_count_too_high` — line 1578
- `_ob_retest_sl_exception_applies` — line 1687
- `_log_liquidity_distance` — line 1894
- `_reject_if_sl_behind_liquidity_cluster` — line 1932
- `_log_inverted_tp` — line 2312

## Watchdog integrations

Watchdog file: `scripts\watchdog.ps1`

Integrated hooks (substring matches):
- `ob_continuation_monitor`
- `api_refusal_monitor`
- `audit_session_volatility_sweep_status`
- `audit_notification_queue_dead_zone`
- `audit_storage_retention`
- `displacement_logger`

## Shadow-log freshness (`shadow_logs/`)

| Log | Last modified | Lines |
|-----|---------------|-------|
| account_pnl_truth_reconciliation.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| account_truth_reconciliation_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| ai_call_policy_decisions.jsonl | 2026-08-12 00:54 UTC | 0 |
| ai_decision_trace.jsonl | 2026-08-12 00:54 UTC | 0 |
| ai_narrowing_policy_shadow_evaluations.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| ai_supervisor_decisions.jsonl | 2026-08-12 00:54 UTC | 0 |
| be_shadow_log.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| broker_actual_r_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| broker_order_lifecycle_capture_v4.jsonl | 2026-08-19 11:48 UTC | 354 |
| candidate_features_log.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| candidate_ltf_path_order.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| candidate_mso_snapshot_joins.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| candidate_path_contract_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| candidate_path_follow.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| candidate_registry_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| context_control_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| context_control_ledger.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| continuation_no_retrace_candidates.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| continuation_no_retrace_resolutions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| cross_instrument_correlation_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| cusum_candidate_rate_daily.csv | 2026-08-12 00:54 UTC | 21 |
| d1_bias_lag.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| d1_bias_lag_recovery.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| daily_pnl_history.jsonl | 2026-08-20 07:30 UTC | lfs_pointer_not_hydrated |
| databento_live_budget_ledger.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| databento_live_confluence.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| databento_live_trigger_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| decision_layer_diagnostics_join.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| direction_emission_xau_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| displacement_events.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| drawdown_state_changes.jsonl | 2026-08-12 00:54 UTC | 0 |
| dumb_baseline_hypotheticals.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| equity_read_anomalies.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| es_mes_preregistration_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| execution_manager_v4_decisions.jsonl | 2026-08-19 09:00 UTC | 75 |
| exit_management_shadow_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| expired_poi_revalidation.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| external_source_blocker_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| f5_keepalive_flaps.jsonl | 2026-08-20 11:34 UTC | 681 |
| fvg_ob_confluence.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| fvg_ob_confluence_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| fvg_ob_confluence_resolutions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| fvg_ob_trade_record_bounds_current_repair_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| gbpjpy_proxy_gap_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| gtos_vnext_replacement_monitoring.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| gtos_vnext_runtime_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| heartbeat_flatten_events.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| j46_j49_exit_comparator_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| j46_j49_shadow_outcomes.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| liquidity_distance_log.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_candidate_opportunity_clusters.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_candidate_strategy_rollups.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_mechanical_strategy_shadow_outcomes.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_monitor.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_monitor_alerts.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_monitoring_maintenance_runs.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| live_structural_strategy_metadata.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| lto_blocked_lane_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| m15_choch_diagnostic_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| malformed_responses.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| mechanical_context_diagnostics_join.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| missed_opportunity_shadow.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| ml_shadow_predictions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| ml_shadow_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| nas100_depth_thinness_current_source_repair_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| nas100_orderflow_adverse_selection_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| nofill_forward_source_capture.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| notification_queue_dead_zone_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| ob_continuation_daily.csv | 2026-08-12 00:54 UTC | 197 |
| operator_market_intelligence.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| opportunity_lifecycle_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| orderflow_primitives_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| partial_close_backtest.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| partial_close_backtest_exact_only.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| partial_close_shadow_log.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| pending_lifecycle_tick_spread_reconstruction.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| pending_limit_lifecycle.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| pending_limit_lifecycle_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| pending_limit_lifecycle_join_backfill.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| prefill_delivery_path.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| prefill_delivery_path_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| prefill_delivery_path_resolutions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| proximity_shadow_log.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| proxy_blocker_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| regime_classifications.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| regime_decay_outcome_join.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| s79_side_aware_risk_context.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| scid_forward_source_capture.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| session_volatility_log.csv | 2026-08-12 00:54 UTC | 43 |
| session_volatility_sweep_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| shadow_observer_hardening_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| shadow_observer_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| shadow_observer_tick_enrichment.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sierra_6b_si_depth_policy_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sierra_confluence_source_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sierra_depth_enrichment_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sierra_depth_feature_snapshots.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sierra_proxy_registry_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sl_beyond_ob_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| slippage.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| slippage_runtime.jsonl | 2026-08-19 09:00 UTC | 162 |
| source_diagnostic_intelligence.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| standalone_fvg_poi_current_claim_repair_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| storage_retention_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| strategy_follow_candidates.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| strategy_follow_evaluations.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| structure_detector_backfill_2022_2023.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| structure_detector_backfill_2026.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| structure_detector_divergences.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| sweep_divergence_log.csv | 2026-08-12 00:54 UTC | 29 |
| swing_protected_stop_current_claim_repair_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| time_in_trade.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| token_verify_probe.jsonl | 2026-08-20 06:00 UTC | 105 |
| touch_count_gate_decisions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| trade_index_lifecycle_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| trailing_stop_v1_shadow_log.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| ultimate_book_launcher.jsonl | 2026-08-20 11:30 UTC | skipped_large_file_55.3MB |
| ultimate_book_runtime_learning_packets.jsonl | 2026-08-20 11:30 UTC | skipped_large_file_354.8MB |
| ultimate_book_runtime_learning_packets.jsonl.quarantine.jsonl | 2026-08-12 12:14 UTC | 1 |
| v2_structural_selector_readiness.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| v2b_forward_pair_resolution_audit.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| v2b_forward_pair_resolutions.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| v2b_forward_pairs.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| xagusd_fresh_ob_late_ny.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |
| xauusd_same_market_extension_status.jsonl | 2026-08-12 00:54 UTC | lfs_pointer_not_hydrated |

---

## Verification flow when a doc says "X is open"

1. Check **Git status** above — if claimed-uncommitted is not listed, the doc is stale.
2. Scan **Last 20 runtime/research commits** — if a matching commit appears, the doc is stale.
3. Grep the relevant code file — if enforcement exists, the doc is stale.
4. Trust this file. Update the stale doc in the same session.
