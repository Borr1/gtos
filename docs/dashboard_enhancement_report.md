# Dashboard Enhancement — Implementation Report

**Date:** 2026-04-05
**Status:** COMPLETE — all 659 tests pass
**Cost:** $0
**Impact on trading:** ZERO — read-only dashboard additions

---

## What Was Built

Two new sections added to the existing `scripts/live_monitor.py dashboard` command, making the new shadow data collection visible in the weekly review dashboard.

---

## Section 6: Evaluation Distribution

**Location in dashboard:** After Section 5 (OB Continuation), before the closing separator.

**What it shows:**

```
────────────────────────────────────────────────────────────────────────
 SECTION 6: EVALUATION DISTRIBUTION
────────────────────────────────────────────────────────────────────────
  Instrument   Evaluations   CANDIDATEs     Rate
  --------------------------------------------
  XAUUSD              140            8     5.7%

  Session memory at CANDIDATE time:
    Mean: 4.2 prior evals
    Min: 0, Max: 11

  Top 5 NO_TRADE reasons:
     87x no_h1_poi
     23x insufficient_displacement
     12x no_m15_confirmation
      8x counter_trend
      4x no_sweep_detected
```

**Data source:** Reads JSONL files from `knowledge_base/live_evaluations/{symbol}/{date}.jsonl` — the files written by the new `EvaluationLogger` component.

**What it tells management:**
- **CANDIDATE rate** — what fraction of candles the AI considers tradeable. If this is >15%, the system may be over-triggering. If <2%, it may be too restrictive.
- **Session memory at CANDIDATE time** — do trades happen on the first candle evaluated (memory=0) or after building context (memory=5+)? This informs whether session memory adds value.
- **NO_TRADE reasons** — why the AI rejects candles. If one reason dominates (e.g., 90% are "no_h1_poi"), the pre-screen may be better handled by a cheaper filter.

---

## Section 7: Devil's Advocate Shadow

**Location in dashboard:** After Section 6, final section before closing separator.

**What it shows:**

```
────────────────────────────────────────────────────────────────────────
 SECTION 7: DEVIL'S ADVOCATE SHADOW
────────────────────────────────────────────────────────────────────────
  DA evaluations: 8
  Winner avg max_risk: 35%
  Loser avg max_risk:  58%
  Gap: 23pp (losers higher — signal!)
```

**Data source:** Reads `shadow_da` field from trade records in the live state file (same state loaded by all other dashboard sections).

**What it tells management:**
- **Whether DA max_risk_pct correlates with actual outcomes.** If losers consistently have higher DA risk scores than winners, the DA has predictive value and should become a live gate in WF-2.
- **The gap magnitude.** A 20+pp gap is strong signal. A <10pp gap means the DA can't discriminate.
- During WF-1, this section will show "No DA shadow data yet" until the first CANDIDATE trades are executed with DA enabled.

---

## Exact Code Changes

**Single file modified:** `scripts/live_monitor.py`

**Lines added:** +90

**What changed:** Two code blocks inserted between the end of Section 5 (OB Continuation) and the closing `print("=" * 72)` separator. No existing code was modified or moved.

**Section 6 logic:**
1. Scans `knowledge_base/live_evaluations/` directory
2. For each instrument subdirectory, reads all `.jsonl` files
3. Counts total evaluations and CANDIDATEs per instrument
4. Collects `session_memory_count` values at CANDIDATE time
5. Tallies `no_trade_reason` strings from NO_TRADE evaluations
6. Displays table + memory stats + top 5 rejection reasons

**Section 7 logic:**
1. Reads the existing dashboard state (same `load_state()` used by all sections)
2. Filters trades that have a `shadow_da` field with `max_risk_pct`
3. Splits into winners/losers
4. Computes mean max_risk for each group
5. Reports the gap and whether it indicates signal

Both sections handle the "no data yet" case gracefully — they print a single informational line and move on.

---

## How To View

```bash
python3 scripts/live_monitor.py dashboard
```

The two new sections appear at the bottom of the existing 5-section dashboard. No new CLI flags or arguments needed.

---

## Testing

- **659 tests pass** (full suite, no changes to any test)
- **Smoke tested:** `python3 scripts/live_monitor.py dashboard` runs cleanly with "No data yet" messages for both new sections (correct — no live data exists yet)
- **No import changes** — the dashboard already imports `json` and `os`; no new dependencies

---

## Relationship to Shadow Data Collection

This dashboard enhancement is the **visibility layer** for the shadow data collection system. The data flow is:

```
Live Pipeline                              Dashboard
─────────────                              ─────────
EvaluationLogger → JSONL files           → Section 6 reads JSONL
DevilsAdvocate → trade_record.shadow_da  → Section 7 reads state
```

Without the dashboard sections, the shadow data would collect silently with no visibility until someone writes an analysis script. With them, every weekly `dashboard` review automatically surfaces the key metrics.
