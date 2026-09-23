# CODEX USOIL Tick-Capture Repair Checkpoint - 2026-06-02 17:58Z

## Scope

Dual-broker live supervisor continuation after `LIVE_STATE` regeneration on commit `ddc3a1d00`.

This checkpoint records a repair to the redacted_account data-capture footprint only. No broker orders,
positions, deals, or manual trade mutations were performed.

## Defect

Post-push health verification showed the runtime was otherwise shaped correctly but redacted_account
tick capture was `23/24`.

Missing symbol:

- `USOIL_cash`

Evidence:

- Expected current vNext symbols: 24.
- Running `run_agent.py`: 24.
- Running `src.components.tick_capture`: 23.
- Running FTMO followers: 1.
- Running trade-record projectors: 1.
- Running M1 capture: 1.
- Running notification workers: 1.
- Running MT5 terminals: 2.

The stale heartbeat for
`pipeline_state/daemon_heartbeat_tick_capture_USOIL_cash_redacted_account_live_bee34003.json`
showed prior PID `10780` with last progress around `2026-06-02T17:51:27Z`, but no live Python
tick-capture process remained for `USOIL_cash`.

## Repair

Verified from disk that `USOIL_cash` belongs in the active 24-symbol redacted_account live surface and
that the redacted_account MT5 broker symbol mapping is `USOUSD`.

First direct `Start-Process` attempt exited immediately because the terminal path with spaces was
not preserved as one Python argument. The corrected launch used a single quoted argument string:

```powershell
C:\PROGRA~1\Python313\python.exe -m src.components.tick_capture --symbol USOIL_cash --mt5-symbol USOUSD --runtime-namespace redacted_account_live_bee34003 --terminal-path "C:\Program Files\MetaTrader 5\terminal64.exe" --skip-tick-freshness-check
```

Corrected process:

- PID: `9336`
- Runtime namespace: `redacted_account_live_bee34003`
- Broker symbol: `USOUSD`
- Terminal path: `C:\Program Files\MetaTrader 5\terminal64.exe`

## After-State

Process snapshot at `2026-06-02T17:57:24Z`:

- Free memory: `1720.67 MB`
- Free memory percent: `21.01%`
- Python processes: `55`
- redacted_account `run_agent.py`: `24`
- redacted_account `src.components.tick_capture`: `24`
- FTMO execution follower: `1`
- Trade-record projector: `1`
- M1 capture: `1`
- Notification worker: `1`
- MT5 terminals: `2`
- USOIL tick PID: `9336`

Fresh USOIL heartbeat:

```json
{
  "utc": "2026-06-02T17:57:22.767338+00:00",
  "pid": 9336,
  "name": "tick_capture_USOIL_cash_redacted_account_live_bee34003",
  "last_progress_utc": "2026-06-02T17:57:22.767280+00:00",
  "symbol": "USOIL_cash",
  "last_poll_status": "ok",
  "last_poll_new_tick_count": 4,
  "last_progress_source": "current_poll_new_ticks"
}
```

Route verifier:

```json
{"failure_count": 0, "status": "PASS"}
```

## Current Status

The live process footprint is healthy after this repair. Continue monitoring the next canonical
intent after `2026-06-02T17:31:14Z` to prove the patched FTMO follower path on fresh live evidence.
