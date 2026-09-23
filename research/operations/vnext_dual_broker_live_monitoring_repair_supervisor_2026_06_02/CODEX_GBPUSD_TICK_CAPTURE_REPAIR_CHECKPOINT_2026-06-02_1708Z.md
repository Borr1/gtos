# CODEX GBPUSD Tick Capture Repair Checkpoint - 2026-06-02 17:08Z

Route: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`

Evidence class: `DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`

Runtime effect boundary: single redacted_account tick-capture process launch only; no manual broker order, position, deal, or account mutation.

## Finding

After the post-compaction preflight and scoped projector verification, process extraction showed 24 redacted_account `run_agent.py` processes but only 23 redacted_account `src.components.tick_capture` processes. The missing tick-capture symbol was `GBPUSD`.

The namespaced GBPUSD tick heartbeat and data state had advanced at `2026-06-02T17:03:23Z`, but the recorded heartbeat PID `7720` was no longer present in the process table at `2026-06-02T17:06:22Z`.

## Before Launch

- UTC checkpoint: `2026-06-02T17:06:42.4549474Z`
- Free memory: `1808.52 MB` (`22.08%`)
- Python processes: `53`
- redacted_account tick captures: `23`
- GBPUSD tick captures: `0`
- MT5 terminal64 processes: `2`

## Repair

Started exactly one direct hidden Python worker:

```powershell
C:\PROGRA~1\Python313\python.exe -m src.components.tick_capture --symbol GBPUSD --mt5-symbol GBPUSD --runtime-namespace redacted_account_live_bee34003 --terminal-path "C:\Program Files\MetaTrader 5\terminal64.exe" --skip-tick-freshness-check
```

The first launch attempt failed before runtime initialization because PowerShell split the unquoted terminal path and `tick_capture.py` rejected `Files\MetaTrader 5\terminal64.exe` as an unknown argument. The corrected quoted launch started PID `7588`.

## After Launch

- UTC checkpoint: `2026-06-02T17:08:06.1743952Z`
- Free memory: `1641.60 MB` (`20.04%`)
- Python processes: `54`
- redacted_account run agents: `24`
- FTMO run agents: `0`
- redacted_account tick captures: `24`
- Missing tick-capture symbols: none
- FTMO follower: `1`
- Projector: `1`
- M1 capture: `1`
- Notification worker: `1`
- MT5 terminal64 processes: `2`

GBPUSD tick heartbeat after repair:

```json
{"utc":"2026-06-02T17:08:04.149023+00:00","pid":7588,"last_poll_status":"ok","last_poll_new_tick_count":3,"total_ticks_written":107712}
```

GBPUSD repair log showed broker offset detection, daemon start, and `520` ticks flushed immediately.

## Status

`repaired_verified`. The process footprint is back to the intended lightweight dual-broker shape: one full redacted_account fleet, FTMO execution follower, projector, 24 redacted_account tick captures, one M1 capture, one notification worker, and two MT5 terminals.

Remaining process-footprint item: the 24 redacted_account `cmd.exe` wrappers around `run_agent.py` remain a controlled optimization item for a safe future all-worker reload. They are not duplicate Python workers and were not restarted for this repair.
