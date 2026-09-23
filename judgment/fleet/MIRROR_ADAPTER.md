# Demo mirror fan-out — PLACE ON (Free Trial / demo)

**Status:** implemented (`mirror_adapter.py` + `mirror_fanout.py`).  
**Owner WORD 2026-09-19:** multi-demo fan-out PLACE **ON** for Free Trial / demo.  
**Still VETO:** FTMO challenge↔challenge copy, quarantine 0, Challenge path `C:\MT5\FTMO`.  
**P1 one-login design** (historical): `docs/MIRROR_ADAPTER_DESIGN_0559.md`.

## Goal

Challenge fills/closes on login **0** become visible on friend **demo / Free Trial** books at fixed micro lots so observers can LABEL timing. Telegram stays notes. Chair never `order_send`s on Challenge from this module.

## Data flow

```
fleet_relay.py  →  outbox/fleet_events.jsonl
                        │
                        ▼  (one worker process per terminal)
                 mirror_fanout.py --observer-id <id>
                        │ initialize(demo path, demo login) only
                        ▼
                 MT5 Free Trial / demo terminal
                        │
                        ▼
                 friend phone MT5
```

MetaTrader5 Python is one connection per process. That is why workers are N processes, not one process / N logins.

## Adapter contract

- **Input:** append-only `outbox/fleet_events.jsonl` (`kind` ∈ fill|close|…; only fill/close write).
- **State:** `outbox/mirror_state_<observer_id>.json` — byte offset + `challenge_ticket → demo_ticket`.
- **On fill:** market open same symbol/side; lot = `MICRO_LOT` (default `0.01`, env `GTOS_FLEET_MICRO_LOT`); comment `fleet:{ticket}`. Ignore Challenge volume.
- **On close:** close the mapped demo ticket. If unmapped, log + skip (do not invent).
- **Never:** Challenge `order_send`; never start a second book writer; never N judgment stacks; never NEWS_PROTOCOL.

## Hard refusals (before any `order_send`)

- target login ∈ `FORBIDDEN_LOGINS` = `{0, 0}`
- path contains `\MT5\FTMO\` without `_Trial` / `_redacted_account` / demo markers
- `account_kind` is challenge / live / funded / verification
- registry `status != active` or `place_enabled` false
- missing ticket / symbol / side on fill
- `account_info().login` after connect is a forbidden login (terminal already on Challenge) → shutdown

## Config

Observers: `schemas/observers.v0.json` (committed empty) or `GTOS_FLEET_REGISTRY` / `--registry`.  
Secrets: `password_env` (e.g. `GTOS_FLEET_DEMO_PASSWORD_FRIEND_ALEX`) — not git.  
`GTOS_FLEET_DRY_RUN=1` or `--dry-run`: validate + map, no `order_send`.  
Example row: `schemas/observers.example.json`.

## Resource budget

| Process | Count |
|---|---|
| Challenge writer | 1 (already running; sole payout PLACE) |
| Fleet relay | 1 |
| Demo PLACE worker | 1 per observer terminal |
| Per-friend judgment | 0 |

## Acceptance

- Fill then close of a Challenge ticket appears on each active demo (or dry-run map).
- Zero Challenge `order_send` from fleet code (unit tests mock MT5 and assert it).
- Challenge↔challenge copy remains VETO.
