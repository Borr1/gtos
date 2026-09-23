# VPS Live Supervisor Final Closure Audit - 2026-06-01

Route: `vps-prod-live-sync-2026-06-02`

Purpose: final transfer context for the other machine's post-V3 research/integration session. This file summarizes all relevant live-session repairs and current truth, not only the risk work.

## Branch And Scope

- Branch: `vps-prod-live-sync-2026-06-02`
- Main target: untouched by this route.
- Starting VPS sync HEAD before final closure package: `cc5f95c7e3aa3fe1469eedf67711a980005612f0`
- Final branch HEAD: the commit containing this file; the operator final response records the pushed hash.
- Included scope: production code, config, watchdog/launcher behavior, tests/verifiers, context handoff/checkpoint files, and canary cleanup context relevant to local research.
- Excluded scope: secrets, credentials, MT5 terminal-local data, raw runtime logs, tick/M1 captures, caches, reload proof JSON churn, and unrelated generated research dirt.

## Current Live State

Fresh read-only proof at `2026-06-01T22:30:30Z`:

- Account login: `0`
- Server/company: `redacted_account-Server 2` / `redacted_account Ltd`
- Account name: `redacted_account-STLR 2-Step P1- Borhen Benltaief`
- Equity/balance at probe: `100214.27` / `99706.8`
- Terminal: `C:\Program Files\MetaTrader 5`
- Data path: `host-local\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
- Terminal connected/trade allowed: `true` / `true`
- MT5 auto-trading issue was user-side terminal switch state and is now enabled by the user.

Process proof at `2026-06-01T22:30Z`:

- Live orchestrators: `24`
- Tick captures: `24`
- M1 capture: `1`
- Heartbeat monitor: `1`
- Notification worker: `1`
- Displacement logger: `1`
- MT5 terminal: `1`

All 24 broker symbols selected in MT5 at the read-only probe. Non-24h symbols can show older tick timestamps outside active exchange windows; the tick-capture heartbeat/liveness contract now treats legitimate quote pauses differently from process failure.

## Repairs Included

Risk composition:

- Fixed `src/components/orchestrator.py` so selected-cell risk is a source-backed cap and final risk is `min(runtime account/prop/correlation risk, selected-cell source risk)`.
- Fixed the normal vNext path to re-run prop/account projection after selected-cell risk is known.
- Fixed `src/components/execution.py` so lower runtime risk overrides are valid when they are `<= selected_cell_risk_pct`; overrides above selected-cell risk still fail closed.
- Added tests in `tests/test_limit_order_flow.py` and `tests/test_orchestrator.py`.

Crypto OHLC / data ingestion:

- Verified BTCUSD/ETHUSD MT5 history/feed OHLC corruption after the FTMO account/profile was added to the same terminal, while the active account remained redacted_account.
- Fixed `src/components/data_ingestion.py` to filter unclosed bars and repair malformed closed M15/M1/M5 OHLC from local tick parquet when available.
- Fixed `src/components/broader_origin_generators.py` to fail source-quality gates when recent M15 repair failed.
- Fixed `src/components/orchestrator.py` lower-timeframe/pending-limit paths to repair M1/M5/M15 inputs and fail closed on unrepaired source corruption.
- Fixed `src/components/execution.py` pending-limit fill checks to refuse unrepaired malformed candles.
- Fixed `src/components/m1_capture.py` to repair M1 rows before persistence, skip unrepaired malformed rows, and atomic-upsert by `(symbol,time_utc)` to remove duplicate stale rows.
- Existing `data/m1/` runtime materialization was repaired locally from tick evidence: `55` files scanned, `32469` rows scanned, `13` files rewritten, `104` duplicates removed, `89` malformed BTC/ETH rows repaired, `0` unrepaired malformed rows. Those runtime CSVs are intentionally not staged.

Watchdog/runtime:

- Fixed `scripts/watchdog.ps1` live-monitoring maintenance to launch Python directly instead of through `cmd.exe`.
- Preserved hidden/no-window launch behavior and redirected stdout/stderr into the maintenance log.
- Added `tests/test_start_all_runtime_contract.py` coverage for the no-`cmd.exe` maintenance launcher.

Canary cleanup:

- Canary is not a live approval/blocking dependency.
- The current maintenance runner contains no active canary step.
- Old canary-governance strings in runtime logs are stale historical output and not a live blocker.

Broker/notification/lifecycle repairs from the live session:

- Broker entry-fill truth resolves MT5 history deal price when `OrderResult.price` is zero.
- Pending-limit market-fill R tracking keeps original intended SL/risk denominator.
- Adopted partial/residual recovery carries source-backed cash risk, entry volume, and SL distance.
- Broker close, Telegram, and daily PnL truth prefer broker-reconciled net profit and close-deal fields.
- Supervisor artifact stale-current classification no longer lets old historical tickets pollute current live tickets.

## Risk Numbers

Selected-cell source truth:

- Stage13 selected-cell rows: `1495`
- Positive selected-cell rows at effective risk `0.25`: `1229`
- Zero/unresolved selected-cell rows: `266`
- Positive selected-cell rows above `0.25`: `0`
- Configured profile risk distribution: `0.25=162`, `0.5=203`, `1.0=293`, `2.0=837`

Final risk contract:

- Selected-cell/source risk and account/prop/correlation risk stay separate.
- Selected-cell risk caps live risk; it does not overwrite a lower runtime reduction.
- Runtime reductions below selected-cell risk are valid and must not be rejected as a mismatch.
- Prop/account projection is evaluated after selected-cell risk is known on the normal path.

## Verification

Commands run and passed:

- `python -m py_compile src/components/orchestrator.py src/components/execution.py src/components/m1_capture.py src/components/data_ingestion.py src/components/broader_origin_generators.py`
- `python -m pytest tests/test_limit_order_flow.py tests/test_m1_capture.py tests/test_data_ingestion.py tests/test_broader_origin_generators.py tests/test_orchestrator.py::test_selected_cell_caps_runtime_risk_without_overwriting_lower_runtime_risk -q` -> `104 passed`
- `python -m pytest tests/test_start_all_runtime_contract.py tests/test_run_live_monitoring_maintenance.py -q` -> `8 passed`
- PowerShell parser check for `scripts/watchdog.ps1` -> `watchdog_ps1_parse_ok`

Read-only runtime proof:

- Fresh MT5 account probe confirmed redacted_account, not FTMO.
- Fresh process count confirmed all 24 orchestrators and all 24 tick captures running.
- BTCUSD tick capture heartbeat at `2026-06-01T22:29:30Z`: `last_poll_status=ok`, `last_poll_new_tick_count=20`.
- ETHUSD tick capture heartbeat at `2026-06-01T22:29:31Z`: `last_poll_status=ok`, `last_poll_new_tick_count=16`.
- After MT5 restart and component reload, raw BTC/ETH MT5 bars were healthy in the post-restart probe and no new repair was needed on fresh closed bars.

Known non-blocking test debt:

- Full `tests/test_orchestrator.py` has one unrelated stale SPRT mock failure in `TestSPRTWiring::test_finalize_exit_calls_sprt_update`. It is not caused by the risk/data-ingestion patches and is not live-health proof.

## Files To Transfer

Production/config/test/watchdog changes staged for the final branch package:

- `config/agent_config.yaml`
- `src/components/broader_origin_generators.py`
- `src/components/data_ingestion.py`
- `src/components/execution.py`
- `src/components/m1_capture.py`
- `src/components/orchestrator.py`
- `scripts/watchdog.ps1`
- `tests/test_broader_origin_generators.py`
- `tests/test_data_ingestion.py`
- `tests/test_limit_order_flow.py`
- `tests/test_m1_capture.py`
- `tests/test_orchestrator.py`
- `tests/test_start_all_runtime_contract.py`

Context/handoff files staged for the other research session:

- `.context/04_agents/CODEX_LIVE_SUPERVISOR_ACTIVE_CHECKPOINT.md`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_PROD_LIVE_SYNC_HANDOFF_2026-06-02.md`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_LIVE_SUPERVISOR_FINAL_CLOSURE_AUDIT_2026-06-01.md`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_LIVE_SUPERVISOR_FINAL_CLOSURE_AUDIT_2026-06-01.json`

Compact dated route summaries staged for research context:

- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_BROKER_TRUTH_REPAIR_SUMMARY_2026-06-01.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_CURRENT_CANDIDATE_DECISION_AUDIT_SUMMARY_2026-06-01.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_TODAY_CANDIDATE_REJECTION_SUMMARY_2026-06-01.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_TODAY_TRADE_RECORD_AUDIT_SUMMARY_2026-06-01.json`

These compact summaries carry useful route evidence and generated timestamps. They are historical route context; this final closure audit is the current-health authority after the late MT5 restart/data-ingestion/risk-composition repairs.

## Excluded Dirty Context

The following remain unstaged because they are runtime state, local-only settings, captures, logs, caches, generated old research dirt, or terminal-local proof:

- `.codex/config.toml`
- `.context/LIVE_STATE.md`
- `data/m1/`
- `data/economic_calendar.csv`
- `data/news_calendar.json`
- `pipeline_state/`
- `shadow_logs/`
- `knowledge_base/`
- `research/program_control/` generated churn
- live route JSONL ledgers under `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/` except the explicit final handoff/audit and compact summary files listed above
- MT5 reload/probe JSON files

## Remaining Blockers

No current live blocker remains from my side after the MT5 restart, code repairs, reload, focused tests, and read-only process/account/tick proof.

Owner action if the crypto OHLC corruption reappears on fresh bars: restart MT5 again and consider a separate redacted_account-only MT5 terminal/data-folder rebuild during a maintenance window. The production code now repairs or fails closed instead of consuming corrupted candles.

## Merge Notes

For local post-V3 integration, preserve these invariants:

- Do not restore canary as a live blocker.
- Do not merge away selected-cell risk cap semantics.
- Do not let account/prop risk and selected-cell/source risk overwrite each other.
- Do not let lower runtime risk reductions fail as selected-cell mismatches.
- Preserve MT5 OHLC repair/fail-closed gates across ingestion, broader-origin source quality, pending-limit fill checks, and M1 capture.
- Preserve direct Python watchdog launches and no persistent `cmd.exe` wrappers.
- Keep broker/Telegram/daily PnL truth tied to broker history/deal evidence where available.
