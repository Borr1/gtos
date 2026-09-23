# Decision 001 — Task A: OB Continuation Rolling-50 Monitor

**Date:** 2026-04-17 (Session 24)
**Status:** Decided. Approach A dispatched.
**Decider:** CEO Borhen
**Context:** Handoff 23 (`23_apr17_task_C_canary_cache_handoff.md`) listed P2-8 "OB continuation rolling-50 monitor" as OPEN. Handoff 23's fresh-session prompt briefed Task A as a reader of `knowledge_base/meta/ob_retest_events_*.json`.

---

## The blocker that forced this decision

Schema reconnaissance on the live OB event log (`knowledge_base/meta/ob_retest_events_*.json`) revealed two problems that made the briefed Task A un-buildable as-specified:

1. **No outcome resolver exists.** `_log_ob_retest_event()` in `src/components/orchestrator.py:2404-2460` writes `outcome: "PENDING"` on every event. Grep of `src/` and `scripts/` found no code path that ever updates a PENDING event to CONTINUED/REVERSED/WIN/LOSS.
2. **Data volume is far below threshold.** Across 5 instruments since Apr 10: **2 events total, both PENDING** (all in GBPJPY). Rolling-50 from live event accumulation would take ~40 days per instrument at current rate.

The 70% baseline / <60% alarm in CLAUDE.md came from Test A rerun (n=219 BOS events) computed by `scripts/ob_retest_comprehensive.py` against historical CSVs — NOT from the live event stream. The live stream was added later for edge-decay monitoring but the resolver loop is missing.

---

## Decision: **Approach A — Historical-rolling monitor**

Adapt the existing `scripts/ob_retest_comprehensive.py` methodology into a standalone monitor that reads M15 historical CSVs in `data/historical_2026/`, detects OBs via `src/components/market_state.py` primitives, walks forward to classify each retest as CONTINUED or REVERSED, and maintains a rolling-50 window per-instrument + portfolio-wide. Alarms when any window rate < 60%. Appends daily snapshot to `shadow_logs/ob_continuation_daily.csv`.

**Why this wins *right now*:**
- Reuses battle-tested methodology (the same code that produced the +17pp validated finding).
- Enough data on day 1 for genuine rolling-50 (580+ historical days per CLAUDE.md).
- Zero `src/components/` edits required — respects Task A guardrails.
- Cron-friendly (6h).
- Catches mechanical OB decay *independent* of the live event log's resolver gap.

---

## Alternatives rejected — but kept on the table

### Approach B — Build monitor + outcome resolver on a side file

Monitor reads each PENDING event from the live log, pulls M15 post-retest candles, applies the continuation rule, and writes the resolved outcome to a **side file** (`shadow_logs/ob_retest_resolutions.jsonl`) — never mutates the production event file. Then computes rolling-50 over live+resolved stream.

**Why rejected for now:**
- Data volume problem unsolved: even with a resolver, the live log accumulates ~1.25 events/day across all 5 instruments. Rolling-50 still takes ~40 days to warm up.
- Requires CEO sign-off on the canonical continuation classification rule before coding — an extra decision cycle.
- Adds a second source of truth for OB outcomes (production log PENDING + side file RESOLVED) — structural debt.

**When to revisit:** If Approach A's historical-rolling monitor proves to have blind spots in *live* decay detection (i.e., edge decays within a period the historical window doesn't capture), Approach B becomes the right augmentation.

### Approach C — Fix the upstream gap: build the resolver into `_log_ob_retest_event` (or companion in `src/components/`)

Extend the live event logger to resolve outcomes in-line as post-retest candles arrive. Then the originally-briefed Task A (simple rolling-50 reader on live events) becomes trivial.

**Why rejected for now:**
- Violates Task A guardrail explicitly: "No `src/components/` changes."
- Requires WF-1 approval as a trading-logic-adjacent change (even though observation-only, the code runs in the live trading loop).
- Timeline is wrong: we need edge-decay observability *now*, not after a WF-1 cycle for orchestrator changes.

**When to revisit:** This is the **correct long-term fix**. Once Approach A is shipped and observing, open a follow-up WF-1 task to build the in-line resolver so the live event log becomes self-consistent. Approach A becomes the belt; Approach C is the suspenders.

### Approach D — Defer Task A; ship lower-priority items first

Skip Task A entirely this session. Clean up `CLAUDE.md` drift (test count, test paths), close out P4-13 (stale 0.3 ATR comments), P4-14 (XAUUSD Session ATR scope check), and wait for a better Task A design to crystallize.

**Why rejected for now:**
- CLAUDE.md explicitly calls OB continuation rate the **#1 primary decay metric** for the system's edge. Deferring it leaves the biggest observability gap open.
- The <60% alarm is the canary that catches edge-decay *before* SPRT, CUSUM, or an emergency stop. Every day without it is a day the system could be silently losing edge.
- Approach A is buildable today with existing methodology and data.

**When Approach D would have been better:** If the existing batch methodology in `ob_retest_comprehensive.py` had turned out to be load-bearing-broken or methodologically disputed, deferring until the methodology stabilized would have been correct. That's not the case (Test A rerun is peer-reviewed, p=0.003).

---

## Consequences of choosing A

**Accepted:**
- Monitor observes mechanical OB continuation on *historical* data + any freshly-pulled MT5 data, not on live-production retests seen by the running orchestrators.
- The live event log's resolver gap remains open — Approach C stays on the backlog.
- Data dependency on `data/historical_2026/` freshness — if the CSV exports go stale, the rolling window drifts older.

**Not accepted / still covered:**
- Observation-only property preserved — monitor never touches trading decisions.
- No `src/components/`, `prompts/`, `config/` changes — WF-1 compliance maintained.

---

## Revisit triggers

- **Approach B triggers:** First month of Approach A shows the historical window missing a short-term decay that SPRT caught.
- **Approach C triggers:** Approach A proves stable *and* CEO opens a WF-1 window for orchestrator improvements; bundle the in-line resolver there.
- **Approach D triggers:** N/A — Approach A ships.

---

*This decision record is part of the GTOS architecture decision log at `.context/06_decisions/`. Future alternatives should be documented here with the same structure, even when not chosen — the unchosen options are not failures, they are options we decided weren't right **yet**.*
