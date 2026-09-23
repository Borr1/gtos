# Challenge → fleet_events.jsonl wire (2026-09-21)

Chair never places on Challenge via demos. This file is the exact emit
path. `f5_launch` activation tokens and `place_seat_trust` KEEP tickets
are **not** touched.

## Destination

`judgment/live/fleet_events.jsonl` (repo-relative). Override with
`GTOS_FLEET_OUTBOX`. Legacy fallback: `judgment/fleet/outbox/fleet_events.jsonl`.

## Two producers, same file

### A. Direct emit (surgical hook)

```python
from judgment.fleet.book_event_emit import emit_close, emit_place

emit_place(ticket=293611741, symbol="XAUUSD", side="sell", sleeve="dsp_walked_hi")
emit_close(ticket=293611741, symbol="XAUUSD", side="sell", exit_class="orig_stop")
```

`normalize_book_row` stamps `source_login=0`. Quarantine
`0` and any other login are refused. No MT5 import. No
`order_send`. Call this from the Challenge **book-event** logger, not
from launch/token/KEEP files.

### B. Relay (already present; was dormant on VPS)

`judgment/fleet/fleet_relay.py --follow` tails, in order:

1. `GTOS_FLEET_LEDGER` if set
2. `judgment/live/book_event_ledger.jsonl`
3. `judgment/live/book_event_spoken.jsonl`
4. `/workspace/gtos/live/book_event_ledger.jsonl` (PR #28 default)

and appends normalized `fill` / `close` rows to the outbox above.

Chair 2026-09-21: `fleet_events.jsonl` mtime 2026-09-19, no live Python
mirror process. That is this relay (and the three fan-out workers)
being down — not a missing Challenge place path. `vps_start_workers.ps1`
starts the relay detached with the three observers.

## Kinds

| Challenge book | fleet_event.v0 |
|---|---|
| place / fill / open / deal_in | `fill` |
| close / closed / deal_out | `close` |
| mfe / high / candidate | ignored by fan-out |

## What this is not

- Not a Challenge `order_send`.
- Not a remint / flatten / KEEP-ticket consumer.
- Not a second NEWS_PROTOCOL.
