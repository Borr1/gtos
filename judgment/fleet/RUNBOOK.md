# Feedback Fleet — PLACE runbook (one worker per observer terminal)

Windows host with one MetaTrader 5 terminal **per** Free Trial / demo login.  
Linux CI uses `--dry-run` or an injected mock. Do not point a worker at `C:\MT5\FTMO` or login `0`.

## 0. Relay (one process, already the producer)

```bash
export GTOS_FLEET_LEDGER=/workspace/gtos/live/book_event_ledger.jsonl
python3 judgment/fleet/fleet_relay.py --follow --sleep-s 2
```

Outbox of record: `judgment/live/fleet_events.jsonl`.  
Legacy: `judgment/fleet/outbox/fleet_events.jsonl`. See `FLEET_EVENT_WIRE.md`.

VPS (all three observers + relay, detached):

```powershell
powershell -File scripts\f5_desk\vps_start_workers.ps1
python scripts\f5_desk\fleet_demo_health.py --offline
```

## 1. Registry + secrets

Copy `judgment/fleet/schemas/observers.example.json` → a local registry (or edit `observers.v0.json` on the host only).

Each PLACE row needs:

- `account_kind`: `demo` or `free_trial`
- `demo_login`: the friend’s trial login (never 0 / 0)
- `terminal_path`: that login’s portable terminal, e.g. `C:\MT5\FTMO_Trial\terminal64.exe`
- `server`: broker demo server
- `password_env`: name of the env var that holds the password
- `place_enabled`: true
- `status`: active

```bash
export GTOS_FLEET_DEMO_PASSWORD_FRIEND_ALEX='…'
export GTOS_FLEET_REGISTRY=judgment/fleet/schemas/observers.v0.json
export GTOS_FLEET_MICRO_LOT=0.01          # optional; default 0.01
# export GTOS_FLEET_DRY_RUN=1             # rehearsal; no order_send
```

Telegram-only rows stay `place_enabled: false`. They do not get a worker.

## 2. Print one command per terminal

```bash
python3 judgment/fleet/mirror_fanout.py --print-launchers
```

## 3. Start one worker per observer

Each command is its own process (MetaTrader5 = one terminal per PID):

```bash
python3 judgment/fleet/mirror_fanout.py --observer-id friend_alex --follow
python3 judgment/fleet/mirror_fanout.py --observer-id friend_sam --follow
```

Cron form:

```bash
python3 judgment/fleet/mirror_fanout.py --observer-id friend_alex --once
```

State file: `judgment/fleet/outbox/mirror_state_friend_alex.json`  
(`offset_bytes` + `ticket_map`).

## 4. What a worker does

| fleet_event | demo action |
|---|---|
| `fill` | `order_send` market, same symbol/side, `MICRO_LOT`, comment `fleet:{ticket}` |
| `close` | close mapped demo ticket; skip if unmapped |
| `mfe` / `high` / `candidate` | ignore |

## 5. Feedback (Telegram notes OK; not a place path)

```bash
python3 judgment/fleet/feedback_ingest.py --observer-id friend_alex --ticket 293611741 --timing too_early
python3 judgment/fleet/promote_feedback_to_close_loop.py
```

## 6. Refuse list (worker exits 2)

- `--observer-id` missing or unknown
- login in `{0, 0}`
- path `...\MT5\FTMO\...` without `_Trial` / `_redacted_account` / `_redacted_account` / demo
- account kind challenge / live / funded
- MetaTrader5 missing and not `--dry-run`

## 7. Tests

```bash
python3 -m pytest tests/judgment/test_fleet_foundation.py tests/judgment/test_mirror_fanout.py -q
```
