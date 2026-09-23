# Feedback Fleet — operator README

One relay. N demo PLACE workers (one PID per Free Trial / demo terminal).  
Source login **0**. Quarantine **0**. FTMO challenge copy **VETO**.  
Chair / Jev never place on observer books. Telegram is feedback notes only.

## Relay (one process)

```bash
python3 judgment/fleet/fleet_relay.py --once
python3 judgment/fleet/fleet_relay.py --follow --sleep-s 2
export GTOS_FLEET_LEDGER=/workspace/gtos/live/book_event_ledger.jsonl
```

Discovery if you omit `--ledger`: `GTOS_FLEET_LEDGER`, then `judgment/live/book_event_{ledger,spoken}.jsonl`, then `$GTOS_LIVE_DIR/…`, then `/workspace/gtos/live/…`.
Outbox of record: `judgment/live/fleet_events.jsonl`.

## Demo PLACE (one worker per observer terminal)

```bash
export GTOS_FLEET_DEMO_PASSWORD_FRIEND_ALEX='…'
python3 judgment/fleet/mirror_fanout.py --print-launchers
python3 judgment/fleet/mirror_fanout.py --observer-id friend_alex --follow
# rehearsal without a terminal:
python3 judgment/fleet/mirror_fanout.py --observer-id friend_alex --once --dry-run
```

Fixed `MICRO_LOT` default `0.01` (`GTOS_FLEET_MICRO_LOT`). Comment `fleet:{ticket}`.  
Hard allowlist: `judgment/fleet/allowlist.py`. Runbook: `RUNBOOK.md`.

Live registry: `mirror/registry/observers.v0.json` (`observer_friend_a` / `observer_redacted_account` / `observer_redacted_account` in `mirror_fanout.targets`).  
Schema lock (empty): `schemas/observers.v0.json`. Secrets via `password_env`, never git.

```powershell
powershell -File scripts\f5_desk\vps_start_workers.ps1
python scripts\f5_desk\fleet_demo_health.py --offline
```

## Ingest a friend’s label

```bash
python3 judgment/fleet/feedback_ingest.py \
  --observer-id friend_alex \
  --ticket 293611741 \
  --timing too_early \
  --symbol XAUUSD \
  --note "entered into the spike"
```

Timings: `too_early` `too_late` `ok_timing` `wrong_session` `wrong_symbol_bias` `stop_too_tight` `stop_too_wide` `should_have_flat` `should_have_held` `unclear`.

## Promote into close_loop (LABEL only)

```bash
python3 judgment/fleet/promote_feedback_to_close_loop.py
```

Every row has `verb=LABEL`, `place=false`.

## Resource budget

| Process | When |
|---|---|
| `fleet_relay.py` | **one** PID |
| `mirror_fanout.py --observer-id X` | **one PID per demo terminal** |
| ingest / promote | on-demand |
| Challenge writer | already running; **do not duplicate** |

## Tests

```bash
python3 -m pytest tests/judgment/test_fleet_foundation.py tests/judgment/test_mirror_fanout.py -q
```
