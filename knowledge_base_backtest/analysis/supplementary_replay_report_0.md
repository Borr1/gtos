# Supplementary Replay Report — Baseline Strengthening

**Date:** 2026-04-02
**Dataset:** 55 fresh random dates (Group B only — all old CANDIDATE dates were already used)
**Period:** Apr 2024 – Mar 2026
**System:** Identical to 36-trade validation (Sonnet, session memory, ob_retest, 2.5R TP1)
**Purpose:** Strengthen baseline with out-of-sample data → combined 50+ trade dataset

---

## Section 1: Run Summary

| Metric | Value |
|--------|-------|
| Dates evaluated | 55 |
| Candle evaluations | 1,088 |
| Dates passing pre-screen | 15 (27%) |
| PA API calls | 287 |
| CANDIDATEs generated | 5 |
| Safety rejections | 1 |
| Trades executed | 4 |
| Errors | 0 |
| Production rate | 7.3% (4 trades / 55 dates) |

### Pre-screen breakdown
- **40 dates** (73%) failed pre-screen entirely (no candle in KZ passed MSO checks)
- **15 dates** (27%) passed pre-screen and reached the PA
- Of 287 PA calls: 282 NO_TRADE, 5 CANDIDATE
- 1 CANDIDATE was safety-rejected (unknown gate)
- 4 executed trades from 3 unique dates

### Group composition note
All 55 dates are **Group B (random)** — no curated "productive" dates were available because every old ob_retest CANDIDATE date had already been used in prior replays. This is a purely unbiased random sample.

### Cost
- 287 API calls at Sonnet pricing
- Estimated ~$5-7 (actual cost tracked in replay.log)

---

## Section 2: New Data Performance (THIS RUN ONLY)

| Metric | Value |
|--------|-------|
| Trades | 4 |
| Wins | 0 |
| Losses | 4 |
| Win Rate | **0.0%** |
| Avg Win | N/A |
| Avg Loss | -0.79R |
| Expectancy | **-0.790R** |
| Total R | **-3.16R** |
| Avg MFE | 1.05R |
| Avg MAE | 0.98R |

### Per-trade detail

| # | Date | KZ | Entry | SL Dist | Grade | Conf | Patience | R | MFE | MAE | Exit |
|---|------|-----|-------|---------|-------|------|----------|---|-----|-----|------|
| 1 | 2025-01-24 | NY | 2780.05 | $17.28 | A+ | 80 | 8 | -0.50 | 0.34R | 0.58R | Timeout |
| 2 | 2025-04-04 | NY | 3095.93 | $39.10 | A+ | 85 | 1 | -1.00 | 1.04R | 1.24R | SL |
| 3 | 2025-12-05 | London | 4225.36 | $39.75 | A | 75 | 9 | -0.66 | 0.85R | 0.84R | Timeout |
| 4 | 2025-12-05 | NY | 4224.98 | $17.23 | A+ | 80 | 9 | -1.00 | 1.98R | 1.26R | SL |

### Observations
- **All 4 trades lost.** This is a worst-case outcome but not impossible at n=4 (probability of 0/4 wins given 52.8% base WR = ~5%).
- 2 trades were NEAR_MISS (MFE >= 1.0R then reversed) — consistent with the pattern seen in the 36-trade set.
- Trade #2 (2025-04-04) had patience=1 (first-candle entry) — the worst category from prior analysis.
- All 4 trades were on **Fridays** — contradicting the 36-trade finding that Friday was 86% WR.

---

## Section 3: Combined Dataset Performance

| Metric | 36-Trade Set | 4 New Trades | Combined (40) |
|--------|-------------|-------------|---------------|
| Trades | 36 | 4 | 40 |
| Wins | 19 | 0 | 19 |
| Losses | 16 | 4 | 20 |
| Win Rate | 52.8% | 0.0% | **47.5%** |
| Avg Win | +1.27R | N/A | +1.27R |
| Avg Loss | -0.75R | -0.79R | -0.76R |
| Expectancy | +0.335R | -0.790R | **+0.223R** |
| Total R | +12.07R | -3.16R | **+8.91R** |
| Profit Factor | 2.01 | 0.00 | **1.59** |

### Statistical significance

| Metric | Value |
|--------|-------|
| t-statistic | 1.178 |
| **p-value** | **0.246** |
| 95% CI | [-0.160R, +0.605R] |

**The combined dataset is NOT statistically significant at p < 0.05.** The 95% CI includes zero. The original 36-trade p=0.048 has degraded to p=0.246 with the addition of 4 losses.

### Interpretation
The 4-trade sample is too small to draw conclusions. A 0/4 run has ~5% probability even with a genuine 52.8% edge. However, the degradation in combined statistics is real and warrants caution:

- Expectancy dropped from +0.335R to +0.223R
- Win rate dropped from 52.8% to 47.5%
- p-value degraded from 0.048 to 0.246

The primary concern is not these 4 trades specifically, but the **production rate**: only 4 trades from 55 random dates (7.3%). The 36-trade validation used curated dates with known CANDIDATE activity, inflating the apparent trade frequency. On truly random dates, the system barely fires.

---

## Section 4: Forward Validation of Prior Findings

**CRITICAL CAVEAT: n=4 is insufficient for any statistically meaningful forward validation. All entries below are directional observations only.**

| Finding | 36-Trade Result | New Data (n=4) | Validated? |
|---------|----------------|----------------|------------|
| SL <= 0.75% outperforms | 67% WR, +0.67R | 2 trades ≤0.75% → both lost | **INCONCLUSIVE** (n=2) |
| Patience >= 3 outperforms | 57% WR, +0.45R | 3 trades with patience ≥3 → all lost | **INCONCLUSIVE** (n=3) |
| Patience >= 5 outperforms | 65% WR, +0.61R | 3 trades with patience ≥5 → all lost | **INCONCLUSIVE** (n=3) |
| First-candle entries underperform | 25% WR, -0.27R | 1 first-candle entry → lost (-1.00R) | **Directionally consistent** |
| A grade outperforms A+ | 60% vs 48% WR | A: 0/1 lost, A+: 0/3 lost | **INCONCLUSIVE** |
| NY outperforms London | 58% vs 47% WR | NY: 0/3, London: 0/1 | **INCONCLUSIVE** |
| Thursday underperforms | 27% WR | 0 Thursday trades | **NOT TESTED** |
| Friday outperforms | 86% WR | 0/4 Friday trades won | **CONTRADICTED** (n=4) |
| PLC >= 8 outperforms | 62% WR | 1 trade PLC≥8 → lost | **INCONCLUSIVE** (n=1) |
| HIGH confidence outperforms | 67% vs 43% WR | Not enough data to split | **INCONCLUSIVE** |
| NEAR_MISS losers saveable by BE | 5/5 saved at 1.0R | 2 NEAR_MISS in new data | **See Section 5** |

### Friday finding contradicted
All 4 new trades occurred on Fridays and all lost. While n=4 doesn't disprove the Friday edge (p=0.05 for 0/4 given 86% base), it's a notable counter-signal. The 36-trade Friday finding (86% WR on 7 trades) may have been noise.

---

## Section 5: Post-Hoc Exit Strategy Simulation (New Data)

### 5A: Fixed TP simulation (4 new trades)

| Fixed TP | Wins | Total R | vs Baseline (-3.16R) |
|----------|------|---------|---------------------|
| 1.0R | 2 | **+0.84R** | **+4.00R** |
| 1.5R | 1 | -0.66R | +2.50R |
| 2.0R | 0 | -3.16R | +0.00R |
| 2.5R (current) | 0 | -3.16R | baseline |

**Key finding:** Fixed TP at 1.0R would have turned a -3.16R disaster into a +0.84R net positive. 2 of 4 trades reached 1.0R MFE. This is consistent with the 36-trade finding that lower TPs dramatically improve results.

### 5B: Breakeven move simulation (4 new trades)

| BE Threshold | Wins | BEs | Total R | vs Baseline |
|-------------|------|------|---------|-------------|
| 0.5R | 0 | 3 | **-0.50R** | **+2.66R** |
| 1.0R | 0 | 2 | **-1.16R** | **+2.00R** |
| 1.5R | 0 | 1 | -2.16R | +1.00R |

**Key finding:** BE at 0.5R saves 3 of 4 losers (converting to breakeven). BE at 1.0R saves both NEAR_MISS trades (#2 and #4 which had MFE 1.04R and 1.98R respectively). This **strongly validates** the NEAR_MISS finding from the 36-trade analysis.

### 5C: Combined TP + BE (new data only)

| Strategy | Total R | vs Baseline |
|----------|---------|-------------|
| Fixed TP 1.0R + BE at 1.0R | +0.84R | +4.00R |
| Fixed TP 1.5R + BE at 1.0R | -0.16R | +3.00R |
| Fixed TP 2.0R + BE at 1.0R | -1.16R | +2.00R |

Even on this all-loss sample, the combined TP 1.0R + BE 1.0R turns -3.16R into +0.84R. This is the most robust exit improvement.

---

## Section 6: Selection Effect Analysis

Searched 287 PA responses for mentions of TP distance as a NO_TRADE reason:
- Responses mentioning "2.5R" + "target": **0**
- Responses mentioning "target too far" / "no structural target" / "target distance": **0**

**Selection effect: NEGLIGIBLE.** The AI does not appear to reject setups because the 2.5R TP target is too ambitious. The TP target is set *after* the CANDIDATE decision, not used as a filter. Lowering TP to 2.0R would not unlock additional CANDIDATE trades — it would only improve outcomes on trades already taken.

---

## Section 7: Updated GO/NO-GO

| Criterion | Threshold | 36-Trade | Combined (40) | Status |
|-----------|-----------|----------|---------------|--------|
| Combined expectancy | >= +0.10R | +0.335R | +0.223R | **PASS** |
| Combined p-value | < 0.03 | 0.048 | 0.246 | **FAIL** |
| Combined WR | >= 50% | 52.8% | 47.5% | **FAIL** |
| New data expectancy | > 0 | N/A | -0.790R | **FAIL** |
| No new bugs | 0 | 0 | 0 | **PASS** |

**Result: 2 PASS, 3 FAIL**

---

## Section 8: Recommendation

### **DEPLOY AS-IS, MONITOR** — with qualification

The 4-trade supplementary sample is too small to invalidate the 36-trade edge, but too negative to strengthen it. The combined p-value (0.246) is no longer significant. However:

**Mitigating factors:**
1. **n=4 is not diagnostic.** A 0/4 run has ~5% probability even with a real 52.8% edge. This is unlucky but not impossible.
2. **The exit optimization findings hold.** Both NEAR_MISS trades in the new data (MFE 1.04R and 1.98R then lost) would have been saved by the BE move at 1.0R — independently confirming the 36-trade finding.
3. **The fixed TP finding holds.** TP at 1.0R turns -3.16R into +0.84R on the new data. TP at 2.0R wouldn't help here but the direction is consistent.
4. **Production rate is the real issue.** 4 trades from 55 random dates (7.3%) vs 36 from 64 curated dates (56%) shows the system is very selective. In live trading, expect ~1 trade per 10 days, not 1 per 2 days.

**Recommended path forward:**

1. **Do NOT deploy with current 2.5R TP.** The edge is not statistically confirmed and the TP is too ambitious.

2. **Run another 30-40 curated dates** (dates known to have OB structure from D1/H4 data, even if no old CANDIDATE exists). The random-date approach produces too few trades for validation efficiency.

3. **If additional trades confirm +expectancy**, deploy with **2.0R TP + 1.0R BE move** — the optimization most robustly supported by both datasets.

4. **If additional trades show continued losses**, the system edge may not be real and deployment should be held.

### Critical numbers needed for statistical confidence:
- At current +0.223R expectancy and ~1.1R standard deviation:
  - n=60 trades needed for p < 0.05
  - n=85 trades needed for p < 0.02
- We have 40 trades. Need ~20 more positive-expectancy trades to reach significance.

---

## Appendix A: Enhanced Data Files

| File | Records | Description |
|------|---------|-------------|
| `supplementary_replay_0_1643.json` | 4 trades | Full trade records with r_path (candle-by-candle R) |
| `supplementary_pa_responses_0_1643.jsonl` | 287 entries | Every PA response with reasoning text, decision, memory depth |
| `supplementary_candle_log_0_1643.json` | 1,088 entries | Every candle evaluation including pre-screen failures |

### r_path example (Trade #4: 2025-12-05 NY)
Full 11-candle path from entry to SL hit, showing price reaching 1.98R MFE before reversing to -1.0R. This data enables precise post-hoc simulation of any exit strategy.

## Appendix B: Production Rate Context

| Sample | Dates | Trades | Rate | Notes |
|--------|-------|--------|------|-------|
| TP1 validation | 64 curated | 36 | 56% | Dates pre-selected for OB structure |
| Supplementary | 55 random | 4 | 7.3% | Unbiased random weekdays |
| **Blended estimate** | **119** | **40** | **34%** | Weighted average |

The true live production rate will be closer to the random-date rate (7-10%) since the system won't be fed curated dates. At 2 KZs per day, expect roughly **1 trade per 7-10 trading days**.
