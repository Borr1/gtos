<!-- SUPERSEDED IN PART — 2026-09-19 Owner WORD: Free Trial / demo fan-out PLACE is ON.
     Living docs: ../ARCHITECTURE.md, ../MIRROR_ADAPTER.md, ../RUNBOOK.md
     Still binding from this file: Challenge source 0; quarantine 0;
     VETO challenge↔challenge copy; no NEWS_PROTOCOL; one relay; terminals required for PLACE.
     Attached as provenance from the 2026-09-19 chair pack / P1 one-login design. -->

# Mirror Adapter Design — P1 demo (one login)

**As-of:** 2026-09-19 ~13:45 ICT  
**Scope:** Sync Challenge `outbox/fleet_events.jsonl` → **ONE** MT5 **demo** login so a friend can watch tickets on phone.  
**Chair verbs:** LABEL / ENFORCE / VETO only. **Never place / remint / flatten on Challenge from this path.**

---

## Goal

Make Challenge fills/closes visible on a single demo account (fixed micro lots) so observers can LABEL timing without running judgment stacks.

## Options compared

| Option | What it is | Cost / ops | Reliability | Verdict |
|--------|------------|------------|-------------|---------|
| **A. MetaTrader5 Python on small always-on host** | Process using MetaTrader5 package + demo terminal; read `outbox/fleet_events.jsonl`; open/close on **demo only** | Needs Windows (or Wine) host with MT5 terminal always up; one Python process; demo secrets only | High if host stays up | **Preferred for P1** when a cheap Windows mini / spare VPS demo terminal slot exists |
| **B. Thin EA on demo** | MQL5 EA on demo chart; polls a tiny HTTP/file command queue written from Chair | EA lives inside demo terminal; Chair writes commands only | High once installed; no second Python stack | **Fallback** if demo terminal is already 24/7 and Python host is heavier |
| **C. N friend Challenge writers / judgment stacks** | Clone full book / judgment per friend | O(N) CPU, ToS landmines, Chair place risk | Waste | **REJECTED** |

### Decision (cheapest reliable path)

1. **Default P1:** **Option A** — one MetaTrader5 Python worker + one demo terminal. Size = **fixed micro lots** (e.g. 0.01), not Challenge R-scaled.
2. **Fallback:** **Option B** thin EA if the demo terminal is already the always-on surface.
3. **Reject:** N judgment stacks, per-friend Challenge writers, FTMO Challenge copy-trade as default (**FTMO VETO** until owner + ToS review).

## Hard locks

| Lock | Value |
|------|--------|
| Source login (events) | **0** only |
| Quarantine | **0** — never fleet source |
| Mirror target | **ONE demo login** (registry row); never Challenge |
| Chair on Challenge via mirror | **forbidden** (no place/remint/flatten) |
| Size | Fixed micro lots; ignore Challenge volume |
| Judgment | **None** on mirror path — ticket mirror only |
| FTMO Challenge copy | **VETO default** |

## Data flow

```
Challenge book_event ledger (one VPS watcher)
        │
        ▼
  relay_stub.py → outbox/fleet_events.jsonl
        │
        ▼
  mirror_adapter (P1, single process)  [not built yet]
        │ open/close on demo login only
        ▼
  MT5 demo terminal (Python API or thin EA)
        │
        ▼
  Friend phone MT5 (viewer)
        → feedback_ingest.py → promote_feedback_to_close_loop.py → LABEL
```

## Adapter contract (sketch; implement later)

- **Input:** append-only `outbox/fleet_events.jsonl` (`kind` ∈ fill|close|…).
- **State:** `outbox/mirror_state.json` — byte/event offset + map `challenge_ticket → demo_ticket`.
- **On fill:** open demo market same symbol/side; lot = `MICRO_LOT` (default `0.01`); comment `fleet:{ticket}`.
- **On close:** close mapped demo ticket; if unmapped, log + skip (do not invent).
- **Never:** Challenge `order_send`; never start a second book writer; never N judgment stacks.

## Resource budget

- **One** mirror process + **one** demo terminal.
- Scale observers by adding phone viewers (or later demos still fed by **one** adapter) — not O(N) writers.

## Non-goals

- No NEWS_PROTOCOL invent.
- No Telegram fan-out here (P1 notify cards are separate).
- No multi-demo until one-login demo is proven.

## Success for P1 demo

- Latency fill→demo open < 60s typical.
- Friend sees ticket on phone with MT5 + demo login only.
- Zero Challenge orders attributed to mirror adapter.
