<!-- SUPERSEDED IN PART — 2026-09-19 Owner WORD: Free Trial / demo fan-out PLACE is ON.
     Living docs: ../ARCHITECTURE.md, ../MIRROR_ADAPTER.md, ../RUNBOOK.md
     Still binding from this file: Challenge source 0; quarantine 0;
     VETO challenge↔challenge copy; no NEWS_PROTOCOL; one relay; terminals required for PLACE.
     Attached as provenance from the 2026-09-19 chair pack / P1 one-login design. -->

# GTOS Feedback Fleet — Architecture (v0)

**Owner WORD:** 2026-09-19 — proceed all the way; foundation first; optimal resources; no waste.  
**Chair:** redacted_account — ENFORCE/VETO/LABEL only; never place/remint/flatten on observer books.

## Problem

Challenge live eyes are scarce. We need many human observers watching the same trades on phones, labeling timing/regime mistakes, feeding close-loop so Jev converges — without N heavy writers or prop-firm ToS landmines.

## Non-goals (explicit waste cuts)

- No per-friend Challenge writers / full judgment stacks.
- No FTMO challenge copy-trade as default (ToS risk). Demo/practice first.
- No Chair placing on friend accounts.
- No second NEWS_PROTOCOL invent.
- No polling every friend’s MT5 from Chair sits (one producer → fan-out).

## Principles

1. **One producer.** Challenge book events (fill/close/mfe) already exist (`watch_book_events` / ledger). Fleet **subscribes**, does not re-discover books.
2. **Thin observers.** Friend = registry row + phone MT5 viewing a **demo** that mirrors tickets. Config on their side ≈ install app + login.
3. **Structured feedback only.** Enum labels into close_loop (extend miss_type / human_timing), not free chat as source of truth.
4. **Scale by fan-out, not multiply compute.** One fleet relay process; N demos are cheap terminals.

## Layers

```
Challenge writer (operator)
        │ book events (fill/close)
        ▼
  Fleet Relay (single process)
        │ append fleet_events.jsonl
        │ optional webhook / Telegram card
        ▼
  ┌─────┴──────┐
  Demo A   Demo B  …   (MT5 mobile viewers)
        │
        ▼
  Feedback Inbox (early|late|wrong_session|wrong_symbol|ok_win|ok_loss|note)
        │
        ▼
  close_loop labels → Jev research (LABEL only)
```

## Components

| ID | Role | Resource note |
|----|------|----------------|
| `fleet_registry.json` | Observer id, display name, demo login, status, invite token hash | Tiny file |
| `fleet_relay` | Tail Challenge book-event ledger → normalize → outbox | One process; reuse VPS watch PIDs if possible |
| `fleet_event.v0` | Canonical event schema (ticket, symbol, side, open/close, R, sleeve) | Shared with close_loop |
| `fleet_feedback.v0` | Human label schema | Append-only inbox jsonl |
| `mirror_adapter` (phase 1b) | Optional: push open/close to demo accounts via thin EA/API | Only when demos exist; not N judgment stacks |
| `observer_guide.md` | Friend: install MT5, open demo, watch, send feedback | Zero Chair config |

## Phases (optimal order)

**P0 — Foundation (now)**  
Schemas, registry, architecture, feedback inbox CLI, close_loop enum extension, relay stub that reads existing book_event ledger → fleet outbox. No friend accounts required yet.

**P1 — Human visible**  
Telegram/Grok notify cards per fill/close (friends need zero MT5 if they only label from cards). Parallel: demo mirror adapter for one test login.

**P2 — Phone MT5 mirrors**  
Onboard first friend demo; mirror adapter syncs Challenge tickets 1:1 (size optional scaled-down); feedback buttons → inbox.

**P3 — Scale**  
N observers, rate-limit feedback, aggregate miss_type into sleeve crosstab; still one relay.

## Security / ToS

- Demo credentials stored as env/secrets refs, not in git.
- FTMO challenge accounts: **VETO default** until owner + ToS review.
- Verification login 0 stays quarantined — never fleet source.
- Source login for events: **0 only**.

## Success metrics

- Event→outbox latency < 60s for fills/closes.
- Feedback → close_loop row same day.
- CPU: one relay, not O(N) writers.
- Friend setup time < 10 minutes.

## Relation to existing GTOS

- Reuses: `book_event_*` ledgers, `close_loop` schema, Challenge sit truth.
- Does not replace: Challenge writer, Jev APPLY, Chair sits.
