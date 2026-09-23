# Feedback-fleet DEMO observer health checklist

Run on the VPS after pull. Read-only. No Challenge mutate.

```powershell
python scripts\f5_desk\fleet_demo_health.py --offline
python scripts\f5_desk\vps_start_workers.ps1
python scripts\f5_desk\fleet_demo_health.py --mt5
```

| # | Check | Pass |
|---|---|---|
| 1 | Registry is `judgment/fleet/mirror/registry/observers.v0.json` | file exists |
| 2 | `mirror_fanout.targets` is `observer_friend_a`, `observer_redacted_account`, `observer_redacted_account` | redacted_account present |
| 3 | friend_a 0 @ `C:\MT5\FTMO_Trial` bal/eq readable, pos integer | `--mt5` |
| 4 | redacted_account 0 @ `C:\MT5\FTMO_redacted_account` same | `--mt5` |
| 5 | redacted_account 1514684855 @ `C:\MT5\FTMO_redacted_account` same | `--mt5` |
| 6 | Relay PID alive (`fleet_relay --follow`) | `relay.alive=true` |
| 7 | Three `mirror_fanout --follow` PIDs alive | `worker_alive=true` × 3 |
| 8 | `judgment/live/fleet_events.jsonl` exists and ages after a Challenge fill | `outbox.fresh` after next place |
| 9 | Health `place_on_challenge=false` and no observer login in `{0,0}` | fail-closed |
| 10 | Challenge writer HB unchanged; this script never `order_send`s | Chair read |

`--offline` is the CI / laptop default (registry + pid + outbox age only).
`--mt5` opens **demo** terminals only.
