# Subagent Findings - Runtime, Process, Data Freshness

Agent: `019e89f1-3e2b-7801-8af9-5af3345ce912`

Scope: runtime/process/data freshness.

Status: read-only audit completed. The agent reported no file edits, no generated Python audit scripts as proof, and no broker/order/position/deal mutation.

## Clean Proofs Reported

- MT5 terminals were correct and not duplicated:
  - redacted_account terminal PID `7176`: `C:\Program Files\MetaTrader 5\terminal64.exe`;
  - FTMO terminal PID `4592`: `"C:\MT5\FTMO\terminal64.exe" /portable`.
- redacted_account full orchestrator fleet was present: 24 `run_agent.py --mode live --profile redacted_account --runtime-namespace redacted_account_live_bee34003` processes for all active symbols.
- Tick capture count was 24.
- Singleton services were present:
  - M1 capture PID `7572`;
  - notification worker PID `3272`;
  - heartbeat monitor PID `12168`;
  - displacement logger PID `10144`;
  - projector PID `9424`;
  - FTMO follower PID `8108`.
- Memory/CPU sample was healthy:
  - total visible memory `8388064 KB`;
  - free physical memory `3419248 KB`;
  - CPU sample `26.6%`.
- Projector/follower pipeline was fresh around the report:
  - projector heartbeat `20:21:34`;
  - follower heartbeat `20:21:34`;
  - canonical intent log last write `20:16:24`;
  - follower processed US30 at `20:16:25`.
- Notification worker was correctly namespaced:
  - PID `3272` used `pipeline_state\redacted_account_live_bee34003\notification_queue.jsonl`;
  - latest queue item at `20:05:52` was followed by `DELIVERED`;
  - legacy `pipeline_state\notification_queue.jsonl` was stale/noise from `07:06`.

## Findings

1. GER40 and UK100 live tick/M1 freshness was stale while watchdog reported OK.
   - Evidence:
     - `daemon_heartbeat_tick_capture_GER40_redacted_account_live_bee34003.json` and `daemon_heartbeat_tick_capture_UK100_redacted_account_live_bee34003.json` at `20:17:30Z` had `last_progress_utc: null`, `last_poll_status: ok`, `last_poll_new_tick_count: 0`.
     - Watchdog rows at `20:18:59` and `20:19:00` said OK with no data-progress timestamp.
     - M1 state showed GER40 and UK100 last closed candle `2026-06-02T19:58:00+00:00`, age `1225.479s`.
     - CSV tails stopped at `19:58`, last write `19:59:05`.
     - Tick files stopped at `20:00:39` and `20:00:17`.
   - Reported root cause:
     - `scripts/watchdog.ps1:1340-1346` treats null progress as OK.
     - `scripts/watchdog.ps1:1360-1365` starts tick capture with `--skip-tick-freshness-check`.
   - Required repair:
     - after a short grace window, null progress must become stale using last file row, `last_msc`, or session-aware market status.

2. SPX500 tick capture died and was recovered, but the failure cause was not logged.
   - Evidence:
     - watchdog `20:18:59 [TICK_CAP_SPX500] NOT RUNNING - Starting...`;
     - watchdog `20:19:00 STARTED - python PID 12316`;
     - heartbeat `20:19:30` showed `last_progress_utc=20:19:30`, `last_poll_new_tick_count=1`;
     - no current `tick_capture_SPX500.log` existed.
   - Required repair:
     - tick capture must write startup/crash stderr per symbol;
     - watchdog should persist death reason when a PID vanishes.

3. M1 no-candidate source packets were reading stale unnamespaced state.
   - Evidence:
     - `src/components/orchestrator.py:1343-1355` hardcoded `Path("pipeline_state") / "m1_capture_state.json"`.
     - A live `shadow_logs/gtos_vnext_replacement_monitoring.jsonl` row at `2026-06-02T20:15:20.827539+00:00` embedded `capture_state.path: pipeline_state\\m1_capture_state.json`, `updated_at_utc: 2026-06-02T07:09:22.037115+00:00`.
     - Active namespaced M1 heartbeat was current at `20:21`.
   - Impact:
     - live monitoring/source completeness can report stale M1 state.
   - Required repair:
     - use runtime namespace path, e.g. `m1_capture_state_redacted_account_live_bee34003.json`.

4. Active execution code was dirty at the time of the subagent report.
   - Evidence:
     - watchdog `20:18:55` warned drift on `scripts/dual_broker_execution_follower.py`, `tests/test_dual_broker_execution_follower.py`, `scripts/emergency_close_ger30_242667071.py`;
     - follower file last write `2026-06-02T20:16:43.947Z`;
     - follower PID `8108` started `19:49:29`.
   - Current main-session status:
     - this class was addressed for the follower/test files by commit and push `5652c67e1 runtime: preserve follower target trade provenance`;
     - `scripts/emergency_close_ger30_242667071.py` remains untracked emergency evidence and must be classified before final closure.
   - Required repair:
     - active-code drift should become a hard operational gate.

5. FTMO follower command line had duplicate recovery flag.
   - Evidence:
     - live PID `8108` command included `--replay-existing --replay-existing --reprocess-failed-intents --live-recovery-window-seconds 1800`.
     - Watchdog builds `$replayArg` at `scripts/watchdog.ps1:724-727` and appends another replay flag in `$liveRecoveryArg` at `scripts/watchdog.ps1:760-761`.
   - Impact:
     - benign under current argparse store-true, but command construction is brittle.
   - Required repair:
     - construct replay/recovery args once.

6. Live maintenance is suppressed while dual-broker bridge is active, and the guard can false-positive on test processes.
   - Evidence:
     - watchdog `20:19:03` skipped maintenance with PIDs `9424,8108,7808`;
     - PID `7808` was `python -m pytest ... tests\test_dual_broker_trade_record_projector.py ...`, not a bridge;
     - `scripts/watchdog.ps1:1008-1016` uses wildcard command substring matching.
     - `pipeline_state/live_monitoring_maintenance_state.json` still had `status: skipped`, reason `dual_broker_activation_guard_suppressed_widening_maintenance`.
   - Required repair:
     - exact-match script basename/process role;
     - exclude pytest;
     - decouple maintenance from always-on bridge/follower presence.

7. FTMO target trade state still contained inherited live trades with missing risk provenance.
   - Evidence:
     - `pipeline_state/operator_profile/dual_broker_target_trade_state.json` active count `8`;
     - older tickets `155108218`, `155108230`, `155129060`, `155129494`, `155129522`, `155207767` had `broker_cash_risk_per_lot: 0.0`, `broker_lot_sizing_diagnostic: null`, blank `cash_risk_amount_source/status`;
     - newer BTCUSD `155209892` and US30_cash `155211378` were broker verified.
   - Current main-session status:
     - commit `5652c67e1` repairs restore-time provenance annotation and intent lineage, but follower reload was pending when the user asked to hold.
   - Required repair:
     - apply reload and verify persisted state is no longer blank; ensure blank source is never treated as verified.

8. Closed-deal broker dollars are reconciled, but broker net-R remains blocked for pre-fix trades.
   - Evidence:
     - `shadow_logs/slippage.jsonl` NAS100 close at `20:05:51` had `broker_profit: -115.17`;
     - `cash_risk_amount: null`, `cash_risk_amount_status: SOURCE_NOT_CAPTURED`, `broker_net_r_status: CASH_RISK_SOURCE_NOT_CAPTURED`.
   - Required repair:
     - persist broker-verified cash risk at entry and backfill where broker-history evidence exists.

9. Shadow comparator R math was contaminated by near-zero denominator rows.
   - Evidence:
     - `partial_close_shadow_log.jsonl` and `trailing_stop_v1_shadow_log.jsonl` UKOIL rows at `19:50:03-19:50:04`;
     - `sl_distance: 1.4210854715202004e-14`;
     - huge `remaining_r` values such as `72761281479704.0`;
     - duplicate rows for same `trade_id`.
   - Required repair:
     - denominator epsilon guard;
     - undefined-R classification;
     - duplicate event idempotency;
     - quarantine/backfill affected rows.

10. Launcher/logging recovery remains weak.
    - Evidence:
      - `start_all.bat:111-129` still uses `wmic process call create`;
      - main `logs/redacted_account_live_bee34003/*.log` samples contained only `Invalid format. Hint: <paramlist>...` from `08:01`;
      - scheduled `TradingAgentDaily` still runs `start_all.bat`;
      - bridge stdout logs were stale/empty.
    - Required repair:
      - replace WMIC with PowerShell `Start-Process` launcher with proper argument arrays and deterministic stdout/stderr files.

11. Legacy unnamespaced runtime artifacts remain and one already leaked into current monitoring.
    - Evidence:
      - stale `pipeline_state/daemon_heartbeat_tick_capture_*.json` ages `47k-67k` seconds;
      - unnamespaced `data/ticks/*` and `data/m1/*` dirs stale around `04:44` or older;
      - M1 namespace leak above proves stale artifacts can still affect monitoring.
    - Required repair:
      - archive/quarantine legacy runtime artifacts;
      - make live namespace readers fail closed if they resolve unnamespaced state.
