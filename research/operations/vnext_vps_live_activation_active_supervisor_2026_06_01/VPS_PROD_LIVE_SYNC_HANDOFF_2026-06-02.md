# VPS Production Live Sync Handoff - 2026-06-02

Branch: `vps-prod-live-sync-2026-06-02`
Starting branch: `main`
Starting HEAD: `1f25962cde02047be459a6e361ddff7c6efc6d2a`
Final branch HEAD: the commit containing this file; use `git rev-parse HEAD` after checkout. The exact pushed hash is also recorded in the operator final response because a commit cannot self-embed its own final hash.

Scope: package the exact VPS live production truth for local post-V3 integration. This includes live production code, config/profile behavior, launcher/watchdog/supervisor behavior, Stage13 risk-contract proof, canary cleanup, and focused tests/verifiers. It excludes secrets, credentials, live runtime churn, raw logs, data captures, caches, and unrelated generated research dirt.

## Final Closure Addendum - 2026-06-01T22:30Z

This handoff has been updated after the late live repairs and the MT5 restart check. The branch remains `vps-prod-live-sync-2026-06-02`; `main` is not the target of this route.

Current branch state before the final closure commit: `cc5f95c7e3aa3fe1469eedf67711a980005612f0`.

Late live-session findings and fixes now included in this branch:

- MT5/account verification after the FTMO account was added to the same terminal: the active terminal is still redacted_account login `0`, server `redacted_account-Server 2`, company `redacted_account Ltd`, path `C:\Program Files\MetaTrader 5`, data path `host-local\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`.
- BTCUSD/ETHUSD malformed OHLC was verified in MT5 history/feed state before the MT5 restart. Production code now filters unclosed bars, repairs malformed M15/M1/M5 closed bars from local tick parquet when possible, and fails closed when source repair cannot prove a valid candle.
- Existing `data/m1/` materialization was repaired locally from tick evidence as runtime data, not staged into git: `55` files scanned, `32469` rows scanned, `13` files rewritten, `104` duplicate rows removed, `89` malformed BTC/ETH rows repaired, `0` unrepaired malformed rows.
- After the user restarted MT5, direct read-only MT5 proof at `2026-06-01T22:30:30Z` showed all 24 broker symbols selected with tick snapshots available. Non-24h symbols can have older tick times outside active exchange windows; tick capture liveness handles that without treating quote silence as a crash.
- The current process proof at `2026-06-01T22:30Z` is `24` live orchestrators, `24` tick captures, `1` M1 capture, `1` heartbeat monitor, `1` notification worker, `1` displacement logger, and `1` MT5 terminal.
- The risk finding below is corrected: there was an actual runtime composition defect after the earlier label audit. Orchestrator now composes final risk as `min(runtime account/prop/correlation risk, selected-cell source risk)` and execution allows runtime reductions below the selected-cell cap.
- Watchdog live-monitoring maintenance no longer launches through `cmd.exe`; it starts Python directly with hidden/no-window process settings and redirected logs.
- Current maintenance code contains no active canary step. Old `canary_restart_governance` strings in logs are stale runtime output, not current live blocking logic.

## Active Live Surface

Current live command shape:

- Orchestrators: `python.exe run_agent.py --symbol <SYMBOL> --mode live --profile redacted_account`
- Tick captures: `python.exe -m src.components.tick_capture --symbol <SYMBOL> --mt5-symbol <BROKER_ALIAS> --skip-tick-freshness-check`
- M1 capture: `python.exe -m src.components.m1_capture --profile redacted_account`
- Heartbeat monitor: `python.exe -m src.safety.heartbeat_monitor`
- Notification worker: `python.exe -m src.utils.notification_queue --worker`
- Displacement logger: `python.exe scripts/displacement_logger.py --continuous`
- MT5 terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`

Current symbol set:

`AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, GER40, JP225, NAS100, NZDUSD, SPX500, UK100, UKOIL_cash, US30_cash, USDCAD, USDCHF, USDJPY, USOIL_cash, XAGUSD, XAUUSD`

Broker aliases used by tick capture:

- Direct: `AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, JP225, NZDUSD, SPX500, UK100, USDCAD, USDCHF, USDJPY, XAGUSD, XAUUSD`
- Aliased: `GER40 -> GER30`, `NAS100 -> NDX100`, `UKOIL_cash -> UKOUSD`, `US30_cash -> US30`, `USOIL_cash -> USOUSD`

Reload proof after the sync-branch code/test fix:

- `2026-06-01 19:20:55` to `19:22:58` watchdog restarted 24 orchestrators.
- Current process scan after reload showed 24/24 live orchestrators, 24/24 tick captures, M1 capture, heartbeat monitor, notification worker, and displacement logger.
- No manual broker order, deal, position, credential, or paid API action was performed.

## Account And Risk Settings

MT5/account snapshot source: `VPS_MT5_ACCOUNT_READINESS.json`, generated `2026-06-01T18:41:23Z`.

- Company/server: `redacted_account Ltd` / `redacted_account-Server 2`
- Currency/leverage: `USD`, `100`
- Balance/equity at snapshot: `100235.58` / `100185.67`
- Positions/orders at snapshot: `3` / `0`
- Trading flags: `trade_allowed=true`, `trade_expert=true`
- Broker time offset: `+10800` seconds (GMT+3)
- MT5 terminal path: `C:\Program Files\MetaTrader 5`
- MT5 data path: `host-local\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`

Current risk contract:

- `config/agent_config.yaml` base risk remains `risk.risk_per_trade_pct: 2.0`.
- redacted_account profile/config values remain source inputs, not the final selected-cell sizing substitute.
- vNext production requires selected-cell risk ledger:
  `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_2026-05-26.jsonl`
- Selected-cell risk is evaluated first from Stage13 source evidence; account/prop risk is projected separately afterward.
- Prop config includes initial balance `100000`, daily/overall limits `5%/10%`, internal GTOS overlay daily `4%`, risk scenarios `[0.25, 0.5, 1.0]`, min reduced risk `0.25`.

## Live-Session Fixes Included

The handoff covers all relevant fixes made during the live VPS session:

- Removed live canary boot/cache/governance dependency from config, orchestrator, heartbeat monitor, watchdog/checklists, AI audit surfaces, prompt A/B harness, tests, and canary fixture/script files.
- Reclassified the old LTO036 canary governance artifact as historical/optional, and removed the tracked canary governance shadow status log from the sync surface.
- Repaired watchdog launch shape so orchestrators and daemons are direct Python processes instead of persistent `cmd.exe` wrappers; watchdog default is live redacted_account mode.
- Repaired tick/M1 watchdog supervision to use liveness heartbeat where quote/data progress can legitimately pause.
- Repaired pre-geometry broader-origin `concurrent_cap_reached` false terminal blocking; it is advisory/deferred until selected-cell/router/final gates can evaluate source-backed candidates.
- Repaired broader-origin candidate trade-record overwrite by adding candidate-specific record identity.
- Repaired selected-cell risk LFS/materialization detection, reload behavior, source identity drift checks, and refusal reason labeling.
- Repaired selected-cell risk chronology so account/prop risk and source selected-cell risk remain separate.
- Repaired risk execution-critical unresolved handling: commission/source facts that are not execution-critical no longer falsely block valid selected-cell rows.
- Repaired Stage13 risk summary label mismatch by separating configured profile-risk counts from effective selected-cell risk counts.
- Repaired broker entry-fill truth: zero `OrderResult.price` now resolves MT5 history deal price before fallback and slippage rows carry broker history reconciliation source.
- Repaired pending-limit market-fill R tracking so original software-limit risk distance is retained for state/R/Telegram math.
- Repaired adopted partial/residual recovery so recovered partial events carry source-backed cash risk, entry volume, and SL distance.
- Repaired broker close, Telegram, and daily PnL truth to prefer broker-reconciled net profit and close-deal fields over local projected dollar values.
- Repaired supervisor artifact stale-current classification, including NAS100 historical ticket pollution against the current ticket.
- Repaired Gate3 instrumentation so optional same-symbol position snapshot failures do not falsely mark MT5 disconnected.
- Repaired test/mock contracts for real MT5 `TRADE_ACTION_SLTP` and updated heartbeat tests to the current 24-symbol kill-zone schedule.
- Repaired OB-continuation monitoring source path resolution for CSV pointer/sibling paths and current vNext symbol coverage.

## Risk Mismatch Finding - Corrected Final Truth

The final investigation found two separate issues.

First, the Stage13 evidence artifact had a label defect. The old summary field `risk_rows_by_profile_risk_pct` was actually counting effective selected-cell risk. It is replaced by separate configured-profile and effective-selected-cell counts.

Second, live runtime had a real composition defect: after account/prop/correlation reductions were computed, orchestrator could overwrite the reduced runtime risk with selected-cell risk. `src/components/execution.py` could then reject a lower runtime override as `risk_pct_override_mismatch_selected_cell`. That was wrong because selected-cell risk is a source-backed cap, not a value that must overwrite every lower account/prop/correlation reduction.

Exact final risk contract:

- Selected-cell/source risk and account/prop/correlation risk are separate.
- Final live risk is `min(runtime_account_prop_correlation_risk, selected_cell_source_risk)` when both are positive.
- Nonpositive runtime risk remains nonpositive and is not overwritten into a trade.
- Runtime risk overrides lower than or equal to the selected-cell cap are valid.
- Runtime risk overrides above the selected-cell cap still fail closed.
- The normal orchestrator path re-runs prop/account projection after selected-cell risk is known, so pre-selected profile risk cannot falsely reduce, defer, or block a trade that selected-cell risk makes safe.

Selected-cell source truth:

- Stage13 selected-cell ledger has `1495` rows.
- `1229` positive selected-cell rows use effective selected-cell risk `0.25`.
- `266` rows are zero/unresolved.
- `0` positive selected-cell rows are above `0.25`.
- Configured profile-risk distribution remains separate: `0.25 = 162`, `0.5 = 203`, `1.0 = 293`, `2.0 = 837`.

Current open/recent post-reload trade proof:

- ETHUSD ticket `242190776`: execution risk `0.25`, cash risk about `251.99`, selected-cell `STAGE13-FN-RISK-CELL-000221`, prop action `ALLOW`.
- USDJPY ticket `242212827`: execution risk `0.25`, cash risk about `251.94`, selected-cell `STAGE13-FN-RISK-CELL-001170`, prop action `ALLOW`.
- NAS100 ticket `242342001`: execution risk `0.25`, cash risk about `250.59`, selected-cell `STAGE13-FN-RISK-CELL-000845`, prop action `ALLOW`.

All-row candidate risk audit:

- Candidate rows: `302`
- Post-reload candidate rows: `3`
- Current value defects: `0`
- Current risk-refusal mismatches: `0`
- Post-reload selected-cell ledger missing/empty: `0`
- Risk ledger rows: `1495`

## Verification

Commands run and results:

- `python -m py_compile ...` for touched runtime, launcher, supervisor, and Stage13 builder/verifier files: passed.
- `python research/.../build_vnext_replacement_stage13_redacted_account_broker_risk_geometry.py; python research/.../verify_vnext_replacement_stage13_redacted_account_broker_risk_geometry.py`: passed.
  - `selected_cell_risk_rows=1495`
  - `selected_cell_risk_positive_rows=1229`
  - `risk_rows_by_configured_profile_risk_pct={"0.25":162,"0.5":203,"1.0":293,"2.0":837}`
  - `risk_rows_by_effective_selected_cell_risk_pct={"0.0":266,"0.25":1229}`
- `python research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/verify_vps_supervisor_artifacts.py`: `ok=true`, `issue_count=0`.
- Focused pytest suite:
  `python -m pytest tests/test_execution.py tests/test_notifications.py tests/test_trade_capture.py tests/test_pending_limit_lifecycle_logger.py tests/test_vnext_broader_origin_orchestrator.py tests/test_watchdog_e2e_verify.py tests/test_heartbeat_monitor.py tests/test_m1_capture.py tests/test_tick_capture.py tests/test_mt5.py tests/test_mt5_daemon_runtime.py tests/test_start_all_runtime_contract.py research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/test_vps_supervisor_artifacts.py -q`
  - Result: `408 passed, 1 skipped`
- Initial focused pytest run exposed 7 failures. All were fixed and the targeted rerun passed `7 passed` before the full focused suite passed.
- Live reload after sync-branch runtime fix: watchdog restarted all 24 orchestrators and current process proof is 24/24 live orchestrators.
- Late focused suite after the data-ingestion/risk-composition repairs:
  `python -m pytest tests/test_limit_order_flow.py tests/test_m1_capture.py tests/test_data_ingestion.py tests/test_broader_origin_generators.py tests/test_orchestrator.py::test_selected_cell_caps_runtime_risk_without_overwriting_lower_runtime_risk -q`
  - Result: `104 passed`
- Late watchdog/maintenance suite:
  `python -m pytest tests/test_start_all_runtime_contract.py tests/test_run_live_monitoring_maintenance.py -q`
  - Result: `8 passed`
- PowerShell parser check for `scripts/watchdog.ps1`: `watchdog_ps1_parse_ok`

## Dirty Path Classification

Exhaustive per-path dirty classification is in:

`research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_PROD_LIVE_SYNC_DIRTY_PATH_CLASSIFICATION_2026-06-02.json`

The classification records each dirty path, class, include/exclude decision, and reason.

Included categories:

- Production code
- Production config/profile
- Launcher/supervisor/watchdog
- Tests/verifiers
- Stage13 broker/risk contract artifacts and LFS-backed ledgers needed to reproduce current live risk behavior
- Canary cleanup code/tests/scripts/research harness changes that remove stale live-blocker pollution
- LTO036 canary-governance context repair and tracked canary-governance shadow-log deletion

Excluded categories:

- `.codex/config.toml` local config
- `.context/LIVE_STATE.md` and local checkpoint churn
- `pipeline_state/`, `shadow_logs/`, `knowledge_base/`, `data/m1/`, and live route JSON/JSONL runtime artifacts
- MT5/live runtime reload proof files generated during this session
- Large/generated old program-control and ML shadow outputs not required to reproduce the VPS live production surface
- Secrets, credentials, and terminal-local runtime state

## Merge Notes For Local Post-V3 Integration

- Merge this branch after local Selector V3, Scheduler V3, and Execution Policy V3 are present.
- Expect conflicts around `src/components/orchestrator.py`, `src/components/execution.py`, `src/components/gtos_vnext_runtime.py`, `src/safety/heartbeat_monitor.py`, watchdog scripts, and selected-cell risk config.
- Preserve these invariants:
  - Canary is not a live approval/blocking dependency.
  - Selected-cell/source risk and account/prop risk are separate.
  - Positive selected-cell effective risk, not configured profile risk, sizes vNext dynamic orders.
  - Non-execution-critical missing commission/source metadata must not falsely reject trades.
  - Broker entry/close truth comes from MT5 history/deal evidence where available.
  - Pending-limit market fills retain the original intended risk denominator.
  - Direct Python watchdog launch shape stays intact.
  - Supervisor artifacts must not treat old historical tickets as current live positions.

Remaining live proof gap: the three open vNext positions still need natural close/deal reconciliation. That is not a branch blocker and no manual broker action was performed.
