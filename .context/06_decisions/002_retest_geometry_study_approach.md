# Decision 002 — Retest Geometry Study: Methodology & Scope

**Date:** 2026-04-18 (Session 25)
**Status:** Decided. Implementation dispatched to A1.
**Decider:** CEO Borhen
**Context:** Session 24 parked a retest-geometry study (`24_apr18_task_A_ob_continuation_monitor_handoff.md`). Goal: characterize the *geometry* of OB retests — penetration depth, MAE distribution, recovery speed, session-dependence — that the OB continuation rolling-50 monitor (Task A, session 24) and the Test A rerun (n=219, +17pp, p=0.003) do not capture.

---

## What we're trying to learn

The continuation rate tells us *whether* OBs continue. The retest geometry tells us *how*:

- **MAE distribution** — informs tight-SL tolerance. Directly relevant to the `sl_too_tight` blocker (handoff 16, ~4-5 trades/week blocked) and the 0.3 → 0.5 ATR SL margin change in session 19.
- **Penetration frequency** — what % of retests pierce the OB edge before reversing? Informs whether we should enter at OB edge, midpoint, or wait for penetration.
- **Time-to-MAE vs time-to-continuation** — does a slow retest predict reversal? Fast reclaim predict continuation?
- **Session-dependence** — London/NY/Tokyo retests differ? Any session worth avoiding or emphasizing?
- **OB-body-size normalization** — do small, medium, large OBs retest differently?

These are **empirical distributional questions**, not inference questions. The edge is known and quantified; the *shape* of the retest dynamics is not.

---

## Decision: Full-2026 historical + separate live-period report

### Data scope

1. **Historical sweep (primary):** 2026-01-01 → 2026-04-17 across all 5 symbols (XAUUSD, US30, USDJPY, GBPJPY, GBPUSD). Pure mechanical OB detection + walk-forward classification. Distributional baseline.
2. **Live-period report (separate):** 2026-04-07 → 2026-04-17 subset, joined against live system records (`knowledge_base/live_evaluations/`, `knowledge_base/trade_records/`, `knowledge_base/no_trades/`). Answers: of the retests our methodology flags, what did the live system see, decide, and execute? Where did we miss?

**Why the split (CEO-explicit, Session 25):** The historical report is a market-data characterization. The live-period report is a system-accuracy audit. Mixing them obscures questions like "did the system miss retests that continued?" or "did CANDIDATEs align with mechanically-predicted continuations?"

### Symbols

All 5, including GBPUSD (observer status preserved per CEO decision locked through 2026-04-30; data exists, include it).

### Methodology

- **OB detection:** reuse production primitives from `src/components/market_state.py` (import, do not reimplement). A3 cold review will verify parity.
- **Session labels:** reuse production `src/components/session_detector.py`.
- **Retest definition:** first M15 candle where price (low for long-side OB, high for short-side OB) enters the OB body/zone after formation. Multiple retests of the same OB: first-retest only (matches production semantics).
- **Walk-forward resolution window:** 48 M15 candles (12h) — enough for 1R continuation or reversal to SL. Beyond → UNRESOLVED.
- **ATR normalization:** H1 ATR(14) at retest candle.
- **SL definition:** opposing side of OB + 0.5 × ATR (current production, per handoff 19).
- **1R target:** retest_entry + ob_body_size past the far edge (one OB-body worth of continuation).

### Per-retest output schema

Exact fields in every CSV row:
`symbol, ob_formation_ts, retest_ts, retest_date, session, side, ob_body_size_pips, ob_body_size_atr, ob_body_size_pct_price, retest_entry_price, mae_pips, mae_atr, mae_pct_ob_body, penetration_pips, penetration_atr, time_to_mae_candles, time_to_continuation_candles, outcome, continuation_r`

### Agent architecture (CEO-approved)

- **A1 — Implementation:** Opus 4.7, worktree isolation, long detailed brief for max-effort work
- **A2 — Independent statistical validation:** Opus 4.7, no isolation, fresh context, different code path (pandas-only, no shared helpers), re-derives key distributions
- **A3 — Cold methodology/adversarial review:** Opus 4.7, no isolation, audits for look-ahead bias, OB-detection parity with production, session-boundary edge cases, DST transitions

A2 and A3 run **in parallel after A1 reports done**.

---

## Alternatives rejected — but kept on the table

### Approach B — Per-instrument parallel agents (5 concurrent impl agents, one per symbol)

Spawn one implementation agent per symbol in parallel, each building its own detector + analysis for a single symbol.

**Why rejected for now:**
- Code duplication across 5 independently-written detectors risks drift in OB-detection semantics. A single library implementation tested once is more reliable than 5 parallel reimplementations.
- Wall-clock savings from parallelism don't outweigh the maintenance cost — future studies (backtest variations, regime comparisons) will reuse this library.
- A3 cold-review becomes 5× harder if there are 5 different detectors.

**When to revisit:** If A1's wall-clock exceeds 2h and we need fast iteration, fall back to per-symbol parallelism over a **shared** library (A1 builds the lib, 5 thin driver agents run it per-symbol in parallel). Not independent reimplementations.

### Approach C — Live-event stream only (`knowledge_base/meta/ob_retest_events_*.json`)

Drive the study off the live event log.

**Why rejected for now:**
- Same blocker ADR 001 diagnosed for Task A: n=2 total live events, resolver gap, data too thin for distributional analysis. Even with full WF-1 accumulation the stream won't carry enough retests for months.
- Live events are event-subsetted (only retests the orchestrator actually sees during KZs) — not a full market-data characterization.

**When to revisit:** Once the live-event resolver ships (ADR 001 Approach C) and accumulates ≥100 resolved events per symbol, use this stream as an **ongoing monitor** that complements this one-off historical study — not as a substitute.

### Approach D — Include pre-2024 data (2022-2023)

Pull MT5 data back 2+ years and study across a wider regime.

**Why rejected for now:**
- 2024-2026 already gives ~2 years × 96 M15 candles/day × 5 symbols = substantial n per symbol per session.
- Pre-2024 carries regime-shift contamination: Fed pivot timing, DXY cycle shift, gold/USD relationship changes across 2022-2024 are real and documented. Mixing regimes weakens the characterization of the regime we're actually trading.

**When to revisit:** If per-session per-symbol cells in the historical report have n<30, pull 2022-2023 as an extension — flagged as a **separate regime** for comparison, not merged.

### Approach E — Combined single report (historical + live mixed)

One markdown report with historical distribution and live-period comparison in the same tables.

**Why rejected:** CEO-explicit (Session 25). Mixing market-data distribution with system-decision audit hides both. Separation preserves interpretability; live-period report can cross-reference the historical baseline.

**When to revisit:** N/A — CEO preference is the decider.

---

## Consequences of choosing this approach

**Accepted:**
- Data dependency: `data/historical/` ends 2026-03-30. A1 forward-fills 2026-04-01 → 2026-04-17 from MT5 (append-only; no file rewrites).
- Historical and live-period reports may diverge. That divergence, if large, is itself a finding — not a methodology bug.
- OB detection semantics inherited from production `market_state.py`. If that module has an undiscovered bug, our retest-geometry numbers reflect it. A3 explicitly audits this parity.
- Study is one-off. It does not become a live monitor. Ongoing monitoring continues via Task A's rolling-50 (session 24) and, eventually, the live-event resolver (ADR 001 Approach C).

**Not accepted / still covered:**
- Observation-only property preserved. Zero `src/components/`, `prompts/`, `config/` changes. WF-1 compliance maintained.
- No live-system mutation. Cross-reference reads only from `knowledge_base/live_evaluations/`, `knowledge_base/trade_records/`, `knowledge_base/no_trades/`.

---

## Revisit triggers

- **Approach B triggers:** A1 wall-clock > 2h.
- **Approach C triggers:** Live-event resolver ships (ADR 001 Approach C) and accumulates ≥100 resolved events per symbol.
- **Approach D triggers:** Any per-session per-symbol cell in historical report has n<30; or CEO requests explicit regime comparison.
- **Approach E triggers:** N/A.

---

*This decision record is part of the GTOS architecture decision log at `.context/06_decisions/`. ADR 001 established the format; this ADR follows it. Rejected approaches are not failures — they are options we decided weren't right **yet**.*
