# Replay Blitz Report — New System Forward Validation
**Date:** 2026-04-02
**System Version:** Breaker blocks + Extended London KZ + Confidence Scorer (shadow)
**Replay Mode:** Sequential with session memory (high-fidelity live pipeline simulation)

---

## 1. Date Selection

### Run 1 — Random Sample (True Out-of-Sample)
- **50 dates** evenly spread across Apr 2024 – Mar 2026
- NOT in the 101-trade batch or previous replay
- 114 API calls, $2.11 cost
- **Result: 2 trades** (4% trade-production rate)

### Run 2 — Known-Productive Supplement
- **16 dates** where the OLD system produced trades, but the new system hasn't evaluated
- 320 candles passed pre-screen → all 16 dates reached PA
- ~155 API calls, ~$1.48 cost
- **Result: 5 trades** (31% trade-production rate on curated dates)

### Combined Dataset
- **66 dates** total evaluated
- **7 trades** produced
- **1 rejected** by safety checks
- **1 error** (CANDIDATE with null trade_parameters on 2025-02-26)
- ~$3.59 total API cost

---

## 2. Overall Performance

| Metric | Value |
|--------|-------|
| Total trades | 7 |
| Wins | 3 (42.9%) |
| Losses | 4 (57.1%) |
| Total R | -3.39R |
| Expectancy | **-0.48R** |
| Win R total | +0.61R (avg win +0.20R) |
| Loss R total | -4.00R (avg loss -1.00R) |
| Profit Factor | 0.15 |

### vs Batch Backtest Comparison
On the 16 supplementary dates, the old batch system had 19 trades (47.4% WR, -0.10R exp).
The replay system took only 5 trades on those same dates — much more selective but still negative.

**15 trades the batch took were skipped by replay** — primarily due to:
- Stricter pre-screen (L1_d1_transitional filtering)
- PA requiring M15 CHoCH + displacement confirmation (U3)
- Session memory context (prior NO_TRADE evaluations making PA more cautious)

---

## 3. Per-Framework Breakdown

### ob_retest (6 trades)
| Date | KZ | Direction | Outcome | R | Grade | Conf |
|------|-----|-----------|---------|---|-------|------|
| 2025-02-13 | NY | LONG | WIN | +0.29 | A | 75 |
| 2025-02-21 | London | LONG | WIN | +0.11 | A+ | 80 |
| 2025-03-18 | NY | LONG | WIN | +0.21 | A | 80 |
| 2025-03-21 | London | LONG | LOSS | -1.00 | A | 75 |
| 2025-03-21 | NY | LONG | LOSS | -1.00 | A+ | 80 |
| 2025-03-24 | London | LONG | LOSS | -1.00 | A | 80 |

- **WR: 50%** (3W/3L)
- **Expectancy: -0.40R**
- **Total R: -2.39R**
- Note: All 3 losses were -1.00R (full stop-loss hit). All 3 wins were partial (+0.20R avg, session timeout exits).

### breaker_retest (1 trade)
| Date | KZ | Direction | Outcome | R | Grade | Conf |
|------|-----|-----------|---------|---|-------|------|
| 2025-02-25 | London | LONG | LOSS | -1.00 | A | 80 |

- **WR: 0%** (0W/1L)
- **Expectancy: -1.00R**
- Sample size too small to draw framework conclusions.

### breaker_retest REJECTED (1)
| Date | KZ | Rejection Reason |
|------|-----|------------------|
| 2025-02-21 | NY | gate1_safety: direction_mismatch |

---

## 4. Extended London Kill Zone Analysis (09:30–10:30 UTC)

### Run 1 (50 dates)
- **49 candle evaluations** in extended window across all dates
- **0 CANDIDATE** trades
- All were NO_TRADE (PA rejections for U3/U4 violations)

### Run 2 (16 dates)
- The 2025-02-25 breaker_retest trade was at 09:00 UTC (core window, not extended)
- The 2025-03-24 trade was at 09:00 UTC (core window)
- **0 trades in the extended 09:30–10:30 window**

### Verdict
The extended London KZ (09:30–10:30) produced **zero additional trades** across 66 dates. It adds evaluation cost without adding trade opportunities in this sample.

---

## 5. Confidence Scorer Forward Validation

### By Confidence Grade
| Grade | Trades | Wins | WR | Avg R |
|-------|--------|------|----|-------|
| HIGH | 6 | 2 | 33.3% | -0.58R |
| MEDIUM | 1 | 1 | 100% | +0.11R |

### By price_level_count
| PLC | Trades | Wins | WR |
|-----|--------|------|----|
| 7 | 1 | 1 | 100% |
| 8 | 3 | 1 | 33% |
| 9 | 2 | 1 | 50% |
| 10 | 1 | 0 | 0% |

**PLC >= 8 proxy:** 6 trades, 2W/4L = 33% WR — **DOES NOT validate** on forward data. The original in-sample finding (PLC >= 8 predicts winners) is not confirmed.

### By hesitation_score
| HS | Trades | Wins | WR |
|----|--------|------|----|
| 0 | 1 | 1 | 100% |
| 1 | 5 | 2 | 40% |
| 2 | 1 | 0 | 0% |

**HS <= 2 proxy:** All 7 trades had HS <= 2 (no discrimination). The HS = 0 trade won, but n=1.
**Directional signal:** HS shows weak inverse relationship (lower HS slightly better), but sample is too small.

### Confidence Scorer Summary
- All trades scored HIGH or MEDIUM — the scorer is not creating enough separation
- The proxies discovered on the 101-trade in-sample data **do not forward-validate** with this sample
- However, n=7 is far too small for definitive conclusions

---

## 6. Safety Check Performance

| Check | Count | Details |
|-------|-------|---------|
| REJECTED by safety | 1 | direction_mismatch on breaker_retest |
| Would-have-been outcome | N/A | breaker_retest has 0% WR, rejection likely saved a loss |

The safety system correctly rejected a breaker_retest CANDIDATE that had a direction conflict. Given breaker_retest's 0% WR in this sample, this was a good rejection.

---

## 7. Session Memory Impact

### Memory Context at Entry
| Trade | Memory Entries | Prior Context |
|-------|---------------|---------------|
| 2025-02-13 NY | 6 | 5× NO_TRADE (U3 failure) then CANDIDATE |
| 2025-02-25 London | 6 | 5× NO_TRADE (U3 unmet) then CANDIDATE |
| 2025-02-21 London | 1 | Direct CANDIDATE on first eval |
| 2025-03-18 NY | 2 | 1× NO_TRADE then CANDIDATE |
| 2025-03-21 London | 2 | 1× NO_TRADE then CANDIDATE |
| 2025-03-21 NY | 2 | 1× NO_TRADE then CANDIDATE |
| 2025-03-24 London | 4 | 3× NO_TRADE then CANDIDATE |

### Pattern Observed
- Trades with **extensive prior NO_TRADE context** (5-6 entries) showed the AI waiting for proper confirmation — both of these were the first replay run's trades
- **Average memory entries at entry: 3.2-6.0** depending on run
- Session memory creates a "patience" effect — the AI evaluates multiple candles before committing
- No evidence that session memory flipped a loss to a win in this sample (unlike the Feb 12 example from Sprint 1.5)

---

## 8. Critical Issue: Trade Frequency

The most significant finding is the **extremely low trade frequency**:

| Metric | Value |
|--------|-------|
| Dates evaluated | 66 |
| Dates producing trades | 7 (10.6%) |
| Trades per date | 0.11 |
| Pre-screen rejection rate | 88% (Run 1), 0% (Run 2 curated) |
| Dominant pre-screen reason | L1_d1_transitional (72% of rejections) |
| PA rejection rate (post pre-screen) | 98% |
| Dominant PA reason | U3 M15 confirmation missing (50%), U4 HTF conflict (50%) |

On the random 50-date sample, **only 6 dates even reached the PA** (12%). The `L1_d1_transitional` filter is responsible for most rejections — it's rejecting dates where D1 structure is unclear/transitional.

### Implication
At this trade frequency (~1 trade per 10 trading days), the system would produce ~2 trades/month. This is consistent with the highly selective design but makes statistical validation extremely slow.

---

## 9. Bug Report

**CANDIDATE with null trade_parameters** on 2025-02-26:
- The PA returned decision=CANDIDATE but trade_parameters=None
- Caused `AttributeError: 'NoneType' object has no attribute 'direction'` in session memory update
- The entire date was skipped
- This is the same Pydantic validation bug pattern seen before — needs investigation

---

## 10. GO / NO-GO Assessment

### Criteria Check

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| Overall expectancy | >= +0.10R | **-0.48R** | FAIL |
| Win rate | >= 55% | **42.9%** | FAIL |
| ob_retest positive exp | > 0 | **-0.40R** | FAIL |
| No catastrophic failures | N/A | 1 bug (null params) | WARN |
| Confidence scorer validates | directionally correct | **Not validated** | FAIL |

### Verdict: **NO-GO**

**Primary reasons:**
1. **Negative expectancy (-0.48R)** — significantly below the +0.10R floor
2. **Win rate (42.9%)** — below the 55% threshold
3. **Poor risk-reward on wins** — average win is +0.20R while average loss is -1.00R (1:5 ratio, inverted)
4. **Confidence scorer does not forward-validate** — PLC >= 8 proxy showed 33% WR vs in-sample prediction of higher WR

### Mitigating Factors
- **Sample size is very small (n=7)** — not statistically significant
- **All wins exited via session timeout**, not TP1 hit — suggests the outcome evaluation may be cutting winners short
- **The system is extremely selective** — 88% pre-screen rejection rate means it's very conservative
- **No losses exceeded -1.00R** — risk management is working

### Recommended Actions Before Funded Account

1. **Fix the win-exit problem**: All 3 wins were +0.11R to +0.29R (session timeout exits). If TP1 is set correctly, these should be reaching TP1 for full R:R. Investigate why wins are being cut short.

2. **Fix the null trade_parameters bug**: CANDIDATE decisions with null parameters waste API calls and skip valid dates.

3. **Run a larger replay** (100+ dates from the productive-date pool) to get a statistically meaningful sample before deciding.

4. **Consider relaxing pre-screen**: The `L1_d1_transitional` filter rejected 72% of all candles. If this is too aggressive, the system will miss valid setups during transitional markets.

5. **Validate TP placement**: The average win of +0.20R with a minimum R:R of 2.5 suggests TPs are rarely hit. Check if TP1 levels are too ambitious.

---

## Appendix: All Trades

| # | Date | KZ | Framework | Dir | Entry | SL | TP1 | R:R | Grade | Conf | Outcome | R | PLC | HS | Exit |
|---|------|-----|-----------|-----|-------|-----|-----|-----|-------|------|---------|---|-----|----|----|
| 1 | 2025-02-13 | NY | ob_retest | LONG | 2919.73 | 2890.16 | 2993.46 | 2.5 | A | 75 | WIN | +0.29 | 9 | 1 | timeout |
| 2 | 2025-02-21 | London | ob_retest | LONG | 2930.13 | 2878.03 | 2960.78 | 2.5 | A+ | 80 | WIN | +0.11 | 7 | 1 | timeout |
| 3 | 2025-02-25 | London | breaker_retest | LONG | 2939.05 | 2924.10 | 2946.50 | 2.8 | A | 80 | LOSS | -1.00 | 9 | 1 | SL hit |
| 4 | 2025-03-18 | NY | ob_retest | LONG | 3023.17 | 2982.05 | 3030.00 | 2.5 | A | 80 | WIN | +0.21 | 8 | 0 | timeout |
| 5 | 2025-03-21 | London | ob_retest | LONG | 3031.59 | 3000.68 | 3031.00 | 2.5 | A | 75 | LOSS | -1.00 | 10 | 1 | SL hit |
| 6 | 2025-03-21 | NY | ob_retest | LONG | 3022.23 | 2999.00 | 3035.00 | 2.5 | A+ | 80 | LOSS | -1.00 | 8 | 1 | SL hit |
| 7 | 2025-03-24 | London | ob_retest | LONG | 3023.27 | 2982.05 | 3030.00 | 2.5 | A | 80 | LOSS | -1.00 | 8 | 2 | SL hit |

**Note:** Trade #5 has TP1 (3031.00) below entry (3031.59) — possible TP calculation error.
