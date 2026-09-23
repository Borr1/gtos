# GTOS Feedback Fleet — Architecture (v1 PLACE)

**Owner WORD:** 2026-09-19 — proceed all the way. Multi-demo fan-out **PLACE ON** for Free Trial / demo.  
**Chair:** redacted_account — ENFORCE / VETO / LABEL on Challenge. Chair / Jev / `run_book.py` still never place on observer books.  
**Fleet PLACE:** `mirror_fanout.py` only, on registry Free Trial / demo terminals.  
**VETO:** FTMO challenge↔challenge copy. Quarantine **0** forever.  
**Attached provenance:** `docs/ARCHITECTURE_df0a.md`, `docs/MIRROR_ADAPTER_DESIGN_0559.md`, `docs/MT5_FANOUT_CHAIR_PACK_0896.md` (P0/P1 drafts; this file supersedes place-OFF).

## Problem

Challenge live eyes are scarce. Friends watch the same trades on phone MT5 **demo / Free Trial** books and send short timing labels into close-loop so Jev converges — without N Challenge writers or prop-firm ToS landmines.

## Non-goals (waste cuts)

- No per-friend Challenge writers / full judgment stacks.
- No FTMO challenge copy-trade (ToS). Demo / Free Trial only.
- No Chair placing on friend accounts (fleet PLACE is a separate demo worker).
- No second NEWS_PROTOCOL invent (file tail of `fleet_events.jsonl` only).
- No polling every friend’s MT5 from Chair (one producer → fan-out).
- No HTTP ingest (CLI feedback only).
- Telegram is feedback notes, not a trade bus.

## Principles

1. **One producer.** Challenge book events already exist. Fleet **subscribes**.
2. **One relay / one outbox.** `fleet_relay.py` → `judgment/live/fleet_events.jsonl`.
3. **N demo workers.** One process per observer terminal path (`mirror_fanout.py --observer-id`).
4. **Thin observers.** Friend = registry row + phone MT5 viewing a mirrored demo.
5. **Fixed MICRO_LOT** (default `0.01`). Never Challenge R-scaled volume.
6. **Structured feedback only.** Enum labels into close_loop.

## Layers

```
Challenge writer (operator, login 0)
        │ book_event_ledger.jsonl / book_event_spoken.jsonl
        │ PLACE stays on this path only (existing Chair)
        ▼
  Fleet Relay (single process, --once cron or --follow)
        │ append outbox/fleet_events.jsonl
        ▼
  ┌─────┴──────────────┐
  worker Demo A        worker Demo B     …   (one PID / terminal)
  mirror_fanout.py     mirror_fanout.py
  PLACE ON Free Trial  PLACE ON demo
        │
        ▼
  Friend phone MT5 (viewer of that demo login)
        │
        ▼
  feedback_ingest.py  →  inbox/fleet_feedback.jsonl   (Telegram notes OK)
        │
        ▼
  promote_feedback_to_close_loop.py  →  LABEL rows only
        │
        ▼
  close_loop / Jev research (never place)
```

## Login / path lock

| Lock | Value |
|---|---|
| Source of events | **0** only |
| Quarantine | **0** — never source, never PLACE target |
| `FORBIDDEN_LOGINS` | `{0, 0}` |
| Challenge path | refuse `\\MT5\\FTMO\\` unless `_Trial` / `_redacted_account` / `_redacted_account` / demo markers |
| PLACE targets | Free Trial / demo registry rows only |
| FTMO challenge copy | **VETO** |

## Components

| ID | Role | Resource |
|---|---|---|
| `schemas/observers.v0.json` | Observer registry (empty until onboarded) | Tiny file |
| `fleet_relay.py` | Tail ledger → normalize → outbox | **One process** |
| `mirror_fanout.py` | Tail outbox → market open/close on **one** demo terminal | **One PID per terminal** |
| `mirror_adapter.py` | Ticket map + MICRO_LOT PLACE (injected MT5) | Used by the worker |
| `allowlist.py` | Login/path VETO | Fail closed before `order_send` |
| `fleet_event.v0` | Canonical fill/close/mfe event | Shared with close_loop |
| `promote_feedback_to_close_loop.py` | timing → miss_type; LABEL only | Cron after ingest |

## Relation to existing GTOS

- Reuses: Challenge book-event ledgers, close_loop lock, astra Challenge identity, PR #27 fleet foundation.
- Does not replace: Challenge writer, Jev APPLY, Chair sits, W7 `run_book.py`.
- Does not import `src.mt5.mt5_real.RealMT5` (Challenge / token path).
