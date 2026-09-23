# Knowledge Base Seeding — Pressure Test Results
**Date:** 2026-04-05
**Run by:** Claude Code automated test suite

---

## Summary

```
=== KNOWLEDGE BASE SEEDING PRESSURE TEST ===
Test 1 (Trade Index):          PASS — 18 gold, 42 GBPUSD, R values correct
Test 2 (Rolling Stats Math):   PASS — WR and expectancy match manual calc
Test 3 (Failure Patterns):     PASS — contains known patterns with correct numbers
Test 4 (Insights YAML):        PASS — parseable, has required sections
Test 5 (KB Context in Prompt): PASS — appears in prompt at ~96 tokens, before dynamic data
Test 6 (Graceful Degradation): PASS — no crash on missing files
Test 7 (No Calendar Conflict): PASS — both integrations coexist
Test 8 (Regression):           PASS — 578 tests passing
```

**Overall: 8/8 PASS**

---

## Test 1: Trade Index — Data Accuracy

- **Total trades:** 60
- **Gold (XAUUSD):** 18 trades — 11W / 7L = 61.1% WR
- **GBPUSD:** 42 trades — 26W / 16L = 61.9% WR
- **All required fields present:** trade_id, date, symbol, direction, outcome, r_multiple
- **All outcomes:** WIN or LOSS (no invalid values)

### Gold R-Value Cross-Reference (strategy_a values used, not original_r):
| Exit Type | Example Date | r_multiple | Expected | Match |
|-----------|-------------|------------|----------|-------|
| TP1 | 2024-04-18 | 1.5 | ~1.5 | YES |
| SL | 2024-04-08 | -1.0 | ~-1.0 | YES |
| TIMEOUT | 2024-10-03 | 0.3606 | variable | YES |
| TIMEOUT | 2025-02-18 | 0.7988 | variable | YES |
| TIMEOUT | 2025-03-25 | -0.0143 | variable | YES |

All 7 TP1 hits = exactly 1.5R. All 3 SL hits = exactly -1.0R. 8 timeouts = various values (correct).

---

## Test 2: Rolling Stats — Math Verification

| Metric | Computed | Reported | Match |
|--------|----------|----------|-------|
| Overall WR | 0.6167 | 0.6167 | YES |
| Overall Expectancy | 0.4449 | 0.4449 | YES |
| Total R | 26.6967 | 26.6967 | YES |
| Gold WR | 0.6111 | 0.6111 | YES |
| Gold Expectancy | 0.5026 | 0.5026 | YES |
| GBPUSD WR | 0.6190 | 0.6190 | YES |
| London WR | 0.5667 | 0.5667 | YES |
| NY WR | 0.6667 | 0.6667 | YES |

All values match to 4 decimal places.

---

## Test 3: Failure Patterns — Content Verification

4 active patterns found:

1. **fp_001_narrow_asian_range** — q1_narrow_wr=0.333, severity=HIGH
   - Source: system_improvements_20260403.md — Asian Range Quartile Analysis
2. **fp_002_cross_instrument_misalignment** — misaligned_wr=0.25, severity=HIGH
   - Source: system_improvements_20260403.md — Cross-Instrument Analysis
3. **fp_003_structure_misread** — 2 preventable losses, severity=MEDIUM
   - Source: system_deep_dive_pressure_test_v2_20260403.md
4. **fp_004_kill_zone_performance** — london=0.5667, ny=0.6667, severity=INFO
   - Source: computed from trade_index

The 33% and 25% WR figures are from the improvements analysis source data. fp_004 kill zone stats are independently computed from trade_index and match rolling_stats.json.

---

## Test 4: Insights YAML — Parseable and Accurate

- **Keys:** summary, last_10, by_instrument, by_kill_zone, cautions, data_source
- **WR cross-reference:** insights=0.6167, stats=0.6167 — MATCH
- **Expectancy cross-reference:** insights=0.4449, stats=0.4449 — MATCH
- **Trade count:** 60 — MATCH

---

## Test 5: KB Context in Prompt

- **KB block length:** 384 characters (~96 tokens)
- **Under 500 token limit:** YES (96 << 500)
- **Starts with `## System Context`:** YES
- **Contains win rate:** YES ("62% WR")
- **Contains last 10 trades:** YES
- **Contains caution warnings:** YES (3 cautions)
- **Appears BEFORE dynamic market data:** YES (verified in f-string template)

### Actual KB block injected into prompt:
```
## System Context
Stats: 60 trades, 62% WR, +0.44R exp, PF 2.4952
Last 10: [L -1.0R, W +1.5R, W +1.5R, W +1.5R, W +0.1R, L -1.0R, L -1.0R, W +0.3R, L -0.2R, W +1.5R]
Cautions:
- Narrow Asian range (<28% ADR) correlates with poor win rate
- GBPUSD trades misaligned with XAUUSD D1 direction have 25% WR
- AI accepting setups without valid H1 OB or with sub-threshold M15 displacement
```

---

## Test 6: Graceful Degradation

- All 4 KB files removed → `assemble_full_context()` returns empty layer dicts
- `_format_kb_context({}, {})` returns empty string
- No crashes, no exceptions
- Files restored successfully

---

## Test 7: No Calendar Conflict

Both integrations present in orchestrator.py:
- **Line 44:** `from src.utils.economic_calendar import load_calendar, should_block_trading`
- **Line 181:** `from src.components.knowledge_base import KnowledgeBase`
- **Line 111:** Calendar loaded during init (`self._calendar`)
- **Line 185:** KB created during analyzer init (`KnowledgeBase()`)

Pipeline flow: KB context assembled (in PrimaryAnalyzer.build_prompt) → calendar check (in orchestrator run loop) → API call. No interference.

---

## Test 8: Regression

```
578 passed, 19 warnings in 55.71s
```

All 578 tests pass. Warnings are deprecation notices for `table_names()` in lancedb (cosmetic only).
