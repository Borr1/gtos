# Shadow Data Collection — Implementation Report

**Date:** 2026-04-05
**Status:** COMPLETE — all 659 tests pass
**Cost to implement:** $0 (code only)
**Live cost:** ~$0.025 per CANDIDATE (one DA API call)
**Impact on trading decisions:** ZERO — all logging is observational, nothing gates execution

---

## What Was Built

Three new capabilities added to the live trading pipeline, all running in shadow mode alongside the existing system. None of them modify, gate, or influence any trading decision.

### Component 1: Devil's Advocate Shadow Evaluator

**New file:** `src/components/devils_advocate.py`

**What it does:** After the Primary Analyzer approves a CANDIDATE trade, a second AI call (Sonnet) evaluates the trade from a risk perspective. It identifies the 3 most specific threats to the trade, each with:
- A description citing exact price levels
- A confirming price level that would signal the risk is materializing
- A probability estimate (0-100%)
- A category (STRUCTURAL_RESISTANCE, MOMENTUM_EXHAUSTION, DISPLACEMENT_DOUBT, TIMING_CONFLICT, CONTEXT_MISMATCH)

**What it does NOT do:**
- Does NOT block any trade
- Does NOT modify position sizing
- Does NOT delay execution
- If the API call fails for any reason, it silently logs a warning and returns `{"error": "..."}` — execution continues normally

**Output:** Stored in the trade record under `record["shadow_da"]`. Example:
```json
{
  "risks": [
    {"description": "Resistance at 2765.50 from prior session high", "confirming_level": 2765.50, "probability_pct": 40, "category": "STRUCTURAL_RESISTANCE"},
    {"description": "Momentum exhaustion after 3 consecutive BOS", "confirming_level": 2758.00, "probability_pct": 30, "category": "MOMENTUM_EXHAUSTION"},
    {"description": "Late London KZ — 25 min before close", "confirming_level": 0, "probability_pct": 20, "category": "TIMING_CONFLICT"}
  ],
  "max_risk_pct": 40,
  "overall_risk_assessment": "Moderate risk. Main concern is structural resistance."
}
```

**Why:** During WF-1 (April 7 – July 7), we'll collect DA scores alongside actual trade outcomes. After 50+ trades, we can test whether DA max_risk_pct correlates with losses. If losers consistently have higher DA scores than winners, the DA becomes a live gate in WF-2.

---

### Component 2: Per-Evaluation Structured Logger

**New file:** `src/components/evaluation_logger.py`

**What it does:** Logs a structured JSONL record for EVERY M15 candle the AI evaluates — not just CANDIDATEs, but NO_TRADE and WAIT decisions too. Each record captures:

| Field | Description |
|---|---|
| `decision` | CANDIDATE / NO_TRADE / WAIT |
| `daily_bias_direction` | bullish / bearish / ranging |
| `daily_bias_confidence` | high / medium / low |
| `h4_aligned` | true / false |
| `h1_poi_type` | OB / FVG / none / etc. |
| `h1_zone` | premium / discount / neutral |
| `h1_fib_pct` | Fibonacci retracement % |
| `h1_causing_event` | BOS / CHoCH / unknown |
| `sweep_detected` | true / false |
| `sweep_type` | asian_high / pdl / etc. |
| `m15_displacement_quality` | strong / medium / weak |
| `m15_displacement_ratio` | Body vs avg ratio |
| `setup_grade` | A+ / A / B+ / B / C |
| `confidence_score` | 0-100 |
| `session_memory_count` | How many prior evals in this KZ |
| `align_score` | 0-4 timeframe alignment |
| `spread` | Current spread in price units |
| `candle_index_in_kz` | 0-indexed position within KZ window |
| `no_trade_reason` | Why it was rejected (if NO_TRADE) |
| `reasoning_word_count` | Length of AI's reasoning text |
| `reasoning_price_count` | How many price levels the AI cited |

**Full reasoning text** is saved for:
- ALL CANDIDATE and WAIT evaluations
- The FIRST NO_TRADE of each kill zone session
- 20% random sample of remaining NO_TRADEs

**Storage:** `knowledge_base/live_evaluations/{symbol}/{date}.jsonl` — one line per evaluation, append-only.

**Why:** This is the dataset that will power all future analysis: which evaluation steps actually predict outcomes (Analysis 3 from the sprint showed Steps 1, 2, 5 had zero variance — now we'll measure live), what NO_TRADE reasons dominate, whether session memory count correlates with CANDIDATE quality, etc.

---

### Component 3: Enriched Trade Records

**Modified file:** `src/components/orchestrator.py`

Every CANDIDATE trade record now includes a `shadow_data` section:

```json
{
  "shadow_data": {
    "session_memory_count": 4,
    "align_score": 3,
    "spread_at_entry": 0.25,
    "candle_index_in_kz": 7,
    "h1_poi_type": "OB",
    "h1_fib_pct": 78.5,
    "h1_causing_event": "BOS",
    "h1_zone": "discount",
    "sweep_detected": true,
    "sweep_type": "asian_high",
    "m15_displacement_quality": "strong",
    "m15_displacement_ratio": 2.4
  },
  "shadow_da": { ... }
}
```

These fields were previously lost after the AI response was parsed. Now they're persisted for every trade, enabling post-hoc analysis of which features predict outcomes.

---

## Exact Code Changes

### New Files (3)
| File | Lines | Purpose |
|---|---|---|
| `src/components/devils_advocate.py` | 92 | Shadow DA evaluator with non-blocking API call |
| `src/components/evaluation_logger.py` | 118 | JSONL logger for every candle evaluation |
| `tests/test_shadow_data_collection.py` | 196 | 14 tests covering DA, eval logger, and helpers |

### Modified Files (2)
| File | Lines Added | What Changed |
|---|---|---|
| `src/components/orchestrator.py` | +81 | Imports, init, eval logging hook, DA call, shadow_data enrichment, 2 helper methods |
| `scripts/live_monitor.py` | +90 | Dashboard sections 6 (eval distribution) and 7 (DA shadow scores) |

### Zero Files Removed or Renamed

---

## Safety Architecture

Every shadow component is wrapped in `try/except` with non-blocking fallback:

```
Eval Logger fails → logger.debug(), execution continues
DA API fails → returns {"error": "..."}, execution continues
Shadow data enrichment fails → logger.debug(), record saved without it
```

The pipeline flow is unchanged:
```
PA → [eval_logger] → CANDIDATE check → create_record → [shadow_data] → [DA] → L2 verify → permissions → execute
       ↑ non-blocking                     ↑ non-blocking    ↑ non-blocking
```

No existing test was modified. 659 total tests pass (645 existing + 14 new).

---

## Dashboard Visibility

`scripts/live_monitor.py dashboard` now shows two new sections:

**Section 6 — Evaluation Distribution:** Per-instrument count of evaluations vs CANDIDATEs, CANDIDATE rate, session memory stats at entry time, top 5 NO_TRADE reasons.

**Section 7 — Devil's Advocate Shadow:** DA evaluation count, winner vs loser average max_risk, and whether the gap indicates signal.

Both sections show "No data yet" until the live system starts generating evaluations.

---

## Config Options

Both components read from `config/agent_config.yaml`:

```yaml
devils_advocate:
  shadow_enabled: true    # set false to disable DA calls entirely
  model: claude-sonnet-4-20250514  # which model to use for DA
```

The eval logger has no config — it always runs (zero cost, local file writes only).
