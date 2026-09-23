# Codex Live Supervisor Active Checkpoint

Updated: 2026-06-01T22:30:30Z

Purpose: persistent recovery point for the active VPS live supervisor goal. Read this file after the mandatory repo preflight so work resumes from disk state, not chat memory.

## Resume Order

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/current_vnext_system_map.md`.
4. Read `.context/00_core/current_repo_reading_order.md`.
5. Read the active supervisor prompt at `research/science_program_2026_05/04_goal_prompts/VNEXT_VPS_LIVE_ACTIVATION_ACTIVE_SUPERVISOR_GOAL_PROMPT_2026-06-01.md`.
6. Read this checkpoint.
7. Read current verifier state only if needed: `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_SUPERVISOR_STATE.json`.

## Boundaries

- Do not perform manual broker order, deal, position, credential, paid API/vendor, or remote git actions.
- Canary is removed from live blocking logic. Do not regenerate canary cache or classify canary absence as approval-bound.
- Fix verified live/root defects in code/data/runtime, then reload affected components and verify. Do not loop on stale ledgers once an item is fixed.

## Current Live Baseline

- Active goal: `VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`.
- Live symbols: AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, GER40, JP225, NAS100, NZDUSD, SPX500, UK100, UKOIL_cash, US30_cash, USDCAD, USDCHF, USDJPY, USOIL_cash, XAGUSD, XAUUSD.
- Current execution policy: `momentum_exhaustion` primary with `partial_be_runner` exception.
- Last known process proof after reload recovery: 24 direct Python `run_agent.py --mode live --profile redacted_account` orchestrators, one per live symbol; 24 direct Python tick captures; one direct Python M1 capture; heartbeat monitor and notification worker direct Python; matching `cmd.exe` wrapper count 0. Proof collected at 2026-06-01T18:10Z after a second watchdog pass restarted stale `ETHUSD`.
- Last supervisor artifact verifier proof after broker-truth and stale-checkpoint repairs: `verify_vps_supervisor_artifacts.py` clean at 2026-06-01T18:46:19Z.

## Completed Current Defects

- Pre-geometry broader-origin `concurrent_cap_reached` false terminal block repaired in `src/components/orchestrator.py`; became advisory/deferred before dynamic router, selected-cell, geometry, and final gates.
- Watchdog persistent `cmd.exe` wrapper repaired in `scripts/watchdog.ps1`; direct Python orchestrator launch is current reload shape.
- Broader-origin candidate trade-record overwrite repaired in `src/components/trade_capture.py` and `src/components/orchestrator.py`; candidate-specific record identity and tests added.
- Supervisor artifact stale candidate classification repaired in `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/build_vps_supervisor_artifacts.py`; verifier clean after rebuild.
- Pending-limit market-fill R tracking repaired in `src/components/execution.py`; `sl_distance_override` now provides the account-risk denominator for TradeState R tracking when current tick-to-SL is zero or smaller than original software-limit risk.
- Broker entry-fill truth repaired in `src/components/execution.py` and `src/components/slippage_shadow_logger.py`; zero `OrderResult.price` now resolves source-backed MT5 history deal entry price before falling back to tick price, and slippage entry rows can carry `broker_entry_deal_history` / `BROKER_HISTORY_RECONCILED`.
- Adopted partial/residual recovery repaired in `src/components/orchestrator.py`; recovered partial events now carry source-backed entry row `cash_risk_amount`, entry volume, and SL distance when partial rows are zero/missing.
- Broker close/Telegram/daily PnL truth repaired in `src/notifications.py` and close wiring; broker-reconciled close rows prefer source-backed position net profit and explicit broker fields instead of local projected dollar truth.
- Data repair applied under repair id `codex_live_broker_truth_repair_2026_06_01_entry_price_pnl_hold_partial_recovery`; summary written to `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_BROKER_TRUTH_REPAIR_SUMMARY_2026-06-01.json`; current `shadow_logs/daily_pnl.json`, append-only `shadow_logs/daily_pnl_history.jsonl` correction rows, and affected trade records repaired from read-only MT5/deal/slippage evidence.
- Stale supervisor artifact defects repaired in `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/build_vps_supervisor_artifacts.py`; NAS100 historical ticket `241779188` no longer pollutes current ticket `242342001`, and current repaired records are included by source-event or record-mtime basis. Route-owned verifier clean.

## Active Checkpoint

Current step: final closure/package on `vps-prod-live-sync-2026-06-02`. Do not revisit old risk-clearance claims without fresh runtime evidence; the risk path was defective, has been patched/reloaded, and is now documented in the final handoff/audit.

Verified evidence:
- `python -m py_compile src\components\orchestrator.py src\components\execution.py src\components\slippage_shadow_logger.py src\notifications.py src\mt5\mt5_real.py` passed after current code patches.
- Focused pytest suite passed: zero order result broker entry history, entry-fill retry history reconciliation, recovered partial BE runner source geometry, adopted position recovery, MT5 position offset warmup, exit entry-time repair, broker-reconciled daily PnL truth, broker net-profit preference, close deal accounting fields, and pending-limit original-risk R tracking.
- Reload recovery proof: first watchdog pass restarted all orchestrators plus heartbeat/notification, but Python-only process check found `ETHUSD` missing; second watchdog pass restarted `ETHUSD` PID 12156. Final Python-only proof: 24/24 orchestrators, 24/24 tick captures, 1 M1 capture, 1 heartbeat, 1 notification worker, 0 matching `cmd.exe` wrappers.
- Current open/adoptable trade records were repaired from broker deal truth for `ETHUSD`, `USDJPY`, and `NAS100`; no manual broker order/position action was performed.
- 2026-06-01T18:46Z runtime proof: 24/24 orchestrators, 24/24 tick captures, 1 M1 capture, 1 heartbeat, 1 notification worker, 0 matching `cmd.exe` wrappers.
- 2026-06-01T18:46Z route verifier: `issue_count=0`, `ok=true`.
- Live file references: `resolved_live_required_dependency_clean`; no unresolved live-required missing/LFS/pointer dependency.
- Broker lifecycle: 3 open vNext positions reconciled to MT5 (`242190776`, `242212827`, `242342001`); close lifecycle remains pending because those positions are open.
- Candidate/risk audit snapshot: 302 candidate rows, 3 current/post-reload rows, 0 current value defects, 0 current risk-refusal mismatches, 0 post-reload selected-cell missing rows, 1495 selected-cell risk ledger rows.
- NAS100 SL/TP anomaly is historical/resolved for closed ticket `241779188`; current NAS100 ticket `242342001` is distinct and below its BE trigger in the snapshot, so it is not a current BE-defect.
- Risk-contract audit 2026-06-01T19:02Z:
  - Live vNext execution sizes from Stage13 selected-cell/source risk, then separately projects account/prop risk. It does not use redacted_account profile base risk as a substitute once selected-cell context is present.
  - Stage13 selected-cell ledger rows: 1495 total, 1229 positive at effective selected-cell risk `0.25`, 266 zero/unresolved, 0 effective rows above `0.25`. Configured profile-risk distribution remains distinct: `0.25` = 162 rows, `0.50` = 203 rows, `1.00` = 293 rows, `2.00` = 837 rows.
  - Current open/recent post-reload tickets `242190776` ETHUSD, `242212827` USDJPY, and `242342001` NAS100 all have execution `risk_pct=0.25`, selected-cell risk pct `0.25`, source selected-cell allowed true, prop action `ALLOW`, and cash risk around 250 USD. Prop max allowed risk pct was materially higher than 0.25 on all three, so prop/account risk did not force the 0.25 sizing.
  - Candidate risk audit all-row pass: 302 rows, 0 risk-refusal mismatches, 0 dynamic-reached null selected-cell defects, 0 zero-risk rows without reason. Current/post-reload rows are the three filled trades and all are source-bound positive selected-cell risk.
  - Repaired misleading Stage13 summary artifact field: `risk_rows_by_profile_risk_pct` was counting effective selected-cell risk. Builder now emits separate `risk_rows_by_configured_profile_risk_pct` and `risk_rows_by_effective_selected_cell_risk_pct`; Stage13 broker-risk summary and verifier regenerated, and verifier passed. This was an evidence-label defect, not live sizing behavior.
- Data-ingestion/live source repair 2026-06-01T21:54Z:
  - Root defect: BTCUSD/ETHUSD MT5 OHLC became malformed after an FTMO account/profile was added to the same terminal, even though the active terminal/account stayed redacted_account. Main M15 ingestion had repair coverage, but the lower-timeframe pending-limit monitor and M1 capture path could still consume raw malformed M1 bars.
  - Fixed `src/components/data_ingestion.py`, `src/components/orchestrator.py`, `src/components/execution.py`, `src/components/m1_capture.py`, and `src/components/broader_origin_generators.py` so M15/M1/M5 malformed OHLC is repaired from local tick parquet where possible and fails closed when repair evidence is unavailable. Pending-limit checks now carry OHLC repair telemetry and skip `repair_failed*` candles instead of treating corrupted highs/lows as fills.
  - Repaired existing `data/m1/` CSV materialization from tick evidence: 55 files scanned, 32,469 rows scanned, 13 files rewritten, 104 duplicate rows removed, 89 malformed BTC/ETH M1 rows repaired, 0 unrepaired malformed rows.
  - M1 capture reloaded and healthy after JSON-safe repair report fix and append/upsert dedupe fix; heartbeat `pipeline_state/daemon_heartbeat_m1_capture_all.json` showed PID 5192, `error_count=0`.
  - Focused tests: `python -m pytest tests/test_m1_capture.py tests/test_data_ingestion.py tests/test_broader_origin_generators.py -q` passed as part of the combined focused suite.
- Risk-composition repair 2026-06-01T22:06Z:
  - Root defect: selected-cell/source risk was overwritten into `effective_risk_pct` after autocorrelation/correlation/prop/account reductions. `src/components/execution.py` also rejected lower runtime overrides as `risk_pct_override_mismatch_selected_cell`.
  - Fixed `src/components/orchestrator.py` so selected-cell risk is a source-backed cap combined with runtime account/prop/correlation risk via `min(runtime_risk, selected_cell_risk)`, preserving zero/nonpositive risk and recording `gtos_vnext_selected_cell_risk_composition`.
  - Fixed the normal vNext path and the broader-origin geometry-repair path. The normal path now re-runs prop projection after selected-cell risk is known, so pre-selected profile risk cannot falsely reduce/defer/block a trade that selected-cell risk makes safe.
  - Fixed `src/components/execution.py` so lower runtime risk overrides are accepted when they are `<= selected_cell_risk_pct`; overrides above selected-cell risk still fail closed.
  - Correct Stage13 selected-cell ledger count using the actual field `effective_risk_per_trade_pct`: 1,229 positive selected cells at `0.25`, 266 zero/unresolved, 0 positive rows above `0.25`.
  - Focused tests: `python -m pytest tests/test_limit_order_flow.py tests/test_m1_capture.py tests/test_data_ingestion.py tests/test_broader_origin_generators.py tests/test_orchestrator.py::test_selected_cell_caps_runtime_risk_without_overwriting_lower_runtime_risk -q` => 104 passed. `python -m py_compile src/components/orchestrator.py src/components/execution.py src/components/m1_capture.py src/components/data_ingestion.py src/components/broader_origin_generators.py` passed.
  - Full `tests/test_orchestrator.py` surfaced one unrelated stale test failure in `TestSPRTWiring::test_finalize_exit_calls_sprt_update`; not caused by the risk patch. Do not treat that as risk reload proof.
  - Reload: 24 orchestrators were directly reloaded at `2026-06-01T22:06:10Z` because watchdog was in Malaysia-time dead zone and would intentionally clean up. Reload artifacts: `pipeline_state/risk_selected_cell_live_reload_before_20260601T220610Z.json`, `pipeline_state/risk_selected_cell_live_reload_after_20260601T220610Z.json`, and `pipeline_state/risk_selected_cell_live_reload_summary_20260601T220610Z.json`. Post-reload process proof: all 24 symbols alive, no missing, no duplicate orchestrators.

Next actions:
1. Commit and push the final scoped transfer package to `vps-prod-live-sync-2026-06-02`.
2. Do not stage raw runtime dirt: `pipeline_state/`, `shadow_logs/`, `data/m1/`, `knowledge_base/`, `.codex/config.toml`, `.context/LIVE_STATE.md`, or generated old program-control churn unless a future task proves a specific file is required for transfer context.
3. If resumed after the push, read `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_LIVE_SUPERVISOR_FINAL_CLOSURE_AUDIT_2026-06-01.md` first.

Final closure proof:
- Fresh read-only MT5 account probe at 2026-06-01T22:30:30Z confirmed redacted_account login `0`, server `redacted_account-Server 2`, company `redacted_account Ltd`, terminal `C:\Program Files\MetaTrader 5`, data path `host-local\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`.
- Fresh process count at 2026-06-01T22:30Z confirmed 24 live orchestrators, 24 tick captures, M1 capture, heartbeat monitor, notification worker, displacement logger, and MT5 terminal.
- BTCUSD tick capture heartbeat at 2026-06-01T22:29:30Z was `ok` with 20 new ticks. ETHUSD tick capture heartbeat at 2026-06-01T22:29:31Z was `ok` with 16 new ticks.
- After MT5 restart and component reload, fresh BTC/ETH MT5 bars were healthy in the post-restart probe; production code now repairs or fails closed if the broker history/feed corrupts again.
- `python -m pytest tests/test_limit_order_flow.py tests/test_m1_capture.py tests/test_data_ingestion.py tests/test_broader_origin_generators.py tests/test_orchestrator.py::test_selected_cell_caps_runtime_risk_without_overwriting_lower_runtime_risk -q` passed with 104 tests.
- `python -m pytest tests/test_start_all_runtime_contract.py tests/test_run_live_monitoring_maintenance.py -q` passed with 8 tests.
- `scripts/watchdog.ps1` parsed successfully and no longer launches live-monitoring maintenance through `cmd.exe`.
- No current live blocker remains from this supervisor route. Full `tests/test_orchestrator.py` still has one unrelated stale SPRT mock failure and should not be treated as live-health proof.

## Cleared Risk Position

Live `0.25%` is the current Stage13 effective selected-cell/source risk for every positive selected-cell row in the active ledger. The `1%`/`2%` numbers still exist as configured profile/scenario inputs in source evidence. After the 2026-06-01T22:06Z repair, live vNext final sizing must use `min(runtime account/prop/correlation risk, selected-cell source risk)`, not a selected-cell overwrite. This means normal full selected-cell trades stay at `0.25%`, but autocorrelation/prop/correlation reductions below `0.25%` are now valid and no longer fail as selected-cell mismatches.

## Checkpoint Rule

When resuming: update `Updated`, `Current step`, and any completed/active items here before relying on prior context. Once an item is fixed and reloaded with proof, do not keep chasing it unless fresh runtime evidence reopens it.
