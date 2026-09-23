# Edge Discovery on D1-Unclear Days

**Generated:** 2026-04-03 20:38 UTC
**Data Range:** 2024-04-01 to 2026-03-30
**Discovery Period:** 2024-04-01 to 2025-06-30
**Validation Period:** 2025-07-01 to 2026-03-30
**Bonferroni α:** 0.0083 (0.05/6)

## 1. Day Classification Summary

### XAUUSD (516 trading days)

| D1 Direction | Count | % |
|---|---|---|
| transitional | 267 | 51.7% |
| bullish | 174 | 33.7% |
| bearish | 55 | 10.7% |
| insufficient_data | 20 | 3.9% |

**D1-Clear:** 229 (44.4%)
**D1-Unclear:** 287 (55.6%)

| Category | Count | % | Description |
|---|---|---|---|
| PASS | 174 | 33.7% | D1 clear + H4 aligned |
| CAT1 | 272 | 52.7% | D1 unclear + H4/H1 aligned |
| CAT2 | 1 | 0.2% | All unclear |
| CAT3 | 68 | 13.2% | H4 mismatch |
| CAT4 | 1 | 0.2% | H1 conflict |

### GBPUSD (581 trading days)

| D1 Direction | Count | % |
|---|---|---|
| transitional | 286 | 49.2% |
| bullish | 135 | 23.2% |
| bearish | 124 | 21.3% |
| insufficient_data | 36 | 6.2% |

**D1-Clear:** 259 (44.6%)
**D1-Unclear:** 322 (55.4%)

| Category | Count | % | Description |
|---|---|---|---|
| PASS | 146 | 25.1% | D1 clear + H4 aligned |
| CAT1 | 266 | 45.8% | D1 unclear + H4/H1 aligned |
| CAT2 | 4 | 0.7% | All unclear |
| CAT3 | 165 | 28.4% | H4 mismatch |
| CAT4 | 0 | 0.0% | H1 conflict |


## 2. Baseline Displacement Quality: D1-Clear vs D1-Unclear

### D1-Clear
- Displacements: 1947 across 152 dates
- Per-date average: 12.81
- 3h Continuation rate: 49.4%
- Avg MFE (3h): 15.05
- Avg MAE (3h): 13.99
- MFE/MAE ratio: 1.076

### D1-Unclear
- Displacements: 4694 across 364 dates
- Per-date average: 12.9
- 3h Continuation rate: 49.2%
- Avg MFE (3h): 11.22
- Avg MAE (3h): 10.99
- MFE/MAE ratio: 1.020

**Statistical test (Mann-Whitney U):** p = 0.926158 — NOT significant


## 3. Per-Hypothesis Results

### Summary Table

| H# | Hypothesis | Disc N | Disc Rate | Disc p | Val N | Val Rate | Val p | Verdict |
|---|---|---|---|---|---|---|---|---|
| H1 | Session Sweep Reversal | 654 | 48.9% | 0.7212 | 382 | 53.7% | 0.0835 | 🔴 RED |
| H2 | FVG Fill Entry | 327 | 38.8% | 1.0000 | 170 | 42.4% | 0.9810 | 🔴 RED |
| H3 | Asian Sweep London Continuation | 61 | 8.2% | 1.0000 | 50 | 8.0% | 1.0000 | 🔴 RED |
| H4 | H4-Anchored OB Retest (D1 Removed) | 24 | 41.7% | 0.8463 | 10 | 30.0% | 0.9453 | ⚪ INSUFFICIENT_DATA |
| H5 | Multi-Sweep Confluence | 336 | 51.5% | 0.3118 | 194 | 47.9% | 0.7409 | 🔴 RED |
| H6 | PD Range Extreme Reversion | 174 | 54.0% | 0.1622 | 103 | 51.5% | 0.4219 | 🔴 RED |

### H1: Session Sweep Reversal

**Discovery Period:**
- n = 654, hits = 320
- Continuation rate: 48.9% [45.1% - 52.8%]
- p-value: 0.721229 
- Avg MFE: 3.44, Avg MAE: 3.63
- MFE/MAE ratio: 0.948
- Avg R-multiple: 2.128
- Edge score: -0.274

**Validation Period:**
- n = 382, hits = 205
- Continuation rate: 53.7% [48.6% - 58.6%]
- p-value: 0.083530 
- Avg MFE: 7.80, Avg MAE: 7.00
- MFE/MAE ratio: 1.115
- Avg R-multiple: 2.265
- Edge score: 0.716

**D1-Clear:** 488 signals, 248/488 cont (50.8%)
**D1-Unclear:** 548 signals, 277/548 cont (50.5%)


### H2: FVG Fill Entry

**Discovery Period:**
- n = 327, hits = 127
- Continuation rate: 38.8% [33.7% - 44.2%]
- p-value: 0.999980 
- Avg MFE: 5.31, Avg MAE: 3.77
- MFE/MAE ratio: 1.407
- Avg R-multiple: 4.002
- Edge score: -2.018

**Validation Period:**
- n = 170, hits = 72
- Continuation rate: 42.4% [35.2% - 49.9%]
- p-value: 0.980968 
- Avg MFE: 13.47, Avg MAE: 13.50
- MFE/MAE ratio: 0.998
- Avg R-multiple: 3.928
- Edge score: -0.997

**D1-Clear:** 214 signals, 76/214 cont (35.5%)
**D1-Unclear:** 283 signals, 123/283 cont (43.5%)


### H3: Asian Sweep London Continuation

**Discovery Period:**
- n = 61, hits = 5
- Continuation rate: 8.2% [3.5% - 17.8%]
- p-value: 1.000000 
- Avg MFE: 6.60, Avg MAE: 6.96
- MFE/MAE ratio: 0.949
- Avg R-multiple: 0.541
- Edge score: -3.265

**Validation Period:**
- n = 50, hits = 4
- Continuation rate: 8.0% [3.1% - 18.8%]
- p-value: 1.000000 
- Avg MFE: 20.77, Avg MAE: 17.87
- MFE/MAE ratio: 1.162
- Avg R-multiple: 1.072
- Edge score: -2.970

**D1-Clear:** 54 signals, 6/54 cont (11.1%)
**D1-Unclear:** 57 signals, 3/57 cont (5.3%)


### H4: H4-Anchored OB Retest (D1 Removed)

**Discovery Period:**
- n = 24, hits = 10
- Continuation rate: 41.7% [24.5% - 61.2%]
- p-value: 0.846272 
- Avg MFE: 5.89, Avg MAE: 3.28
- MFE/MAE ratio: 1.798
- Avg R-multiple: 1.633
- Edge score: -0.408

**Validation Period:**
- n = 10 (INSUFFICIENT, need ≥ 20)


### H5: Multi-Sweep Confluence

**Discovery Period:**
- n = 336, hits = 173
- Continuation rate: 51.5% [46.2% - 56.8%]
- p-value: 0.311750 
- Avg MFE: 3.53, Avg MAE: 3.94
- MFE/MAE ratio: 0.895
- Avg R-multiple: 3.766
- Edge score: 0.273

**Validation Period:**
- n = 194, hits = 93
- Continuation rate: 47.9% [41.0% - 54.9%]
- p-value: 0.740860 
- Avg MFE: 9.68, Avg MAE: 9.03
- MFE/MAE ratio: 1.072
- Avg R-multiple: 4.987
- Edge score: -0.287

**D1-Clear:** 238 signals, 114/238 cont (47.9%)
**D1-Unclear:** 292 signals, 152/292 cont (52.1%)


### H6: PD Range Extreme Reversion

**Discovery Period:**
- n = 174, hits = 94
- Continuation rate: 54.0% [46.6% - 61.3%]
- p-value: 0.162187 
- Avg MFE: 3.38, Avg MAE: 4.83
- MFE/MAE ratio: 0.701
- Avg R-multiple: 2.244
- Edge score: 0.531

**Validation Period:**
- n = 103, hits = 53
- Continuation rate: 51.5% [41.9% - 60.9%]
- p-value: 0.421949 
- Avg MFE: 12.32, Avg MAE: 12.67
- MFE/MAE ratio: 0.972
- Avg R-multiple: 2.340
- Edge score: 0.148


## 4. Cross-Hypothesis Analysis

### Edge Quality Ranking

| Rank | Hypothesis | Val Rate | Val N | Edge Score | Verdict |
|---|---|---|---|---|---|
| 1 | H1: Session Sweep Reversal | 53.7% | 382 | 0.716 | RED |
| 2 | H6: PD Range Extreme Reversion | 51.5% | 103 | 0.148 | RED |
| 3 | H5: Multi-Sweep Confluence | 47.9% | 194 | -0.287 | RED |
| 4 | H4: H4-Anchored OB Retest (D1 Removed) | 30.0% | 10 | -0.632 | INSUFFICIENT_DATA |
| 5 | H2: FVG Fill Entry | 42.4% | 170 | -0.997 | RED |
| 6 | H3: Asian Sweep London Continuation | 8.0% | 50 | -2.970 | RED |

### Frequency Estimate
- Valid hypotheses (>55% val rate): 0
- Unique dates with signals: 0
- Additional trades per month: 0.0
- Combined avg R-multiple: 0.000

## 5. Top Hypothesis Detailed Analysis

### H1: Session Sweep Reversal

- Total signals: 1036
- Max consecutive losses: 12
- Profit factor (raw): 1.13
- R-based profit factor: 3.70

**Monte Carlo (50-trade sequences):**
- P5 (worst 5%): 35.10R
- P25: 52.94R
- P50 (median): 65.70R
- P75: 79.45R

**Monthly Distribution:**
| Month | Signals |
|---|---|
| 2024-01 | 22 |
| 2024-02 | 22 |
| 2024-03 | 35 |
| 2024-04 | 28 |
| 2024-05 | 47 |
| 2024-06 | 41 |
| 2024-07 | 27 |
| 2024-08 | 41 |
| 2024-09 | 46 |
| 2024-10 | 35 |
| 2024-11 | 32 |
| 2024-12 | 48 |
| 2025-01 | 37 |
| 2025-02 | 36 |
| 2025-03 | 64 |
| 2025-04 | 27 |
| 2025-05 | 34 |
| 2025-06 | 32 |
| 2025-07 | 45 |
| 2025-08 | 37 |
| 2025-09 | 41 |
| 2025-10 | 36 |
| 2025-11 | 42 |
| 2025-12 | 46 |
| 2026-01 | 50 |
| 2026-02 | 39 |
| 2026-03 | 46 |

### H6: PD Range Extreme Reversion

- Total signals: 277
- Max consecutive losses: 6
- Profit factor (raw): 0.90
- R-based profit factor: 4.09

**Monte Carlo (50-trade sequences):**
- P5 (worst 5%): 41.58R
- P25: 59.18R
- P50 (median): 72.13R
- P75: 85.29R

**Monthly Distribution:**
| Month | Signals |
|---|---|
| 2024-01 | 9 |
| 2024-02 | 4 |
| 2024-03 | 3 |
| 2024-04 | 4 |
| 2024-05 | 8 |
| 2024-06 | 11 |
| 2024-07 | 12 |
| 2024-08 | 10 |
| 2024-09 | 12 |
| 2024-10 | 8 |
| 2024-11 | 16 |
| 2024-12 | 16 |
| 2025-01 | 11 |
| 2025-02 | 6 |
| 2025-03 | 7 |
| 2025-04 | 23 |
| 2025-05 | 9 |
| 2025-06 | 5 |
| 2025-07 | 16 |
| 2025-08 | 9 |
| 2025-09 | 16 |
| 2025-10 | 10 |
| 2025-11 | 11 |
| 2025-12 | 8 |
| 2026-01 | 7 |
| 2026-02 | 14 |
| 2026-03 | 10 |
| 2026-04 | 2 |


## 6. Statistical Rigor

- **Bonferroni correction:** 6 hypotheses tested, adjusted α = 0.0083
- **Minimum sample:** n ≥ 20 per hypothesis per period
- **Continuation metric:** Price reaches 1.5× SL distance in expected direction within 3 hours
- **Null hypothesis:** Each signal has 50% chance of continuation (coin flip)
- **Test:** One-sided binomial test (H_a: p > 0.5)
- **Confidence intervals:** Wilson score intervals at 95%
- **Discovery/Validation split:** Chronological (no leakage)

## 7. Sub-Split Analysis — Conditional Edges

Examining sub-populations within the top hypotheses for conditional edges:

### H1: Session Sweep Reversal — Sub-Splits

| Sub-Split | N | Hits | Rate | p-value |
|---|---|---|---|---|
| **By Kill Zone (Validation)** | | | | |
| London | 178 | 88 | 49.4% | 0.5889 |
| NY | 204 | 117 | **57.4%** | **0.0210** |
| **By Level (All)** | | | | |
| Asian High | 422 | 213 | 50.5% | 0.4420 |
| Asian Low | 317 | 160 | 50.5% | 0.4553 |
| PDH | 174 | 87 | 50.0% | 0.5302 |
| PDL | 123 | 65 | 52.8% | 0.2943 |
| **By D1 Condition (All)** | | | | |
| D1-Clear | 488 | 248 | 50.8% | 0.3757 |
| D1-Unclear | 548 | 277 | 50.5% | 0.4154 |
| **By Instrument (All)** | | | | |
| XAUUSD | 422 | 210 | 49.8% | 0.5580 |
| GBPUSD | 614 | 315 | 51.3% | 0.2725 |

**Notable finding:** H1 sweep reversals in the NY kill zone during validation show 57.4% (p=0.021). This is NOT Bonferroni significant (needs p < 0.0083), and this is a post-hoc sub-split (further inflating multiple comparison risk). However, it is the strongest individual signal in the dataset and may warrant focused future investigation.

### H6: PD Range Extreme Reversion — Sub-Splits

| Sub-Split | N | Hits | Rate | p-value |
|---|---|---|---|---|
| PDH sweep | 175 | 91 | 52.0% | 0.3251 |
| PDL sweep | 102 | 56 | 54.9% | 0.1865 |
| Reached mid-range | 33/277 | — | 11.9% | — |

The mean-reversion target (price returning to PD mid-range) only fires 11.9% of the time, which kills the mean-reversion premise of H6.

## 8. Overall Conclusion

- **GREEN (validated):** 0 hypotheses
- **YELLOW (promising):** 0 hypotheses
- **RED (not significant):** 5 hypotheses
- **Insufficient data:** 1 hypotheses (H4: only 34 total signals)

**Additional trades per month:** 0
**Combined validated expectancy:** 0R per trade

**D1-Unclear days represent 609/1097 (55.5%) of all trading days.**

### Key Findings

1. **D1-unclear days are NOT fundamentally lower quality.** The baseline displacement comparison shows near-identical continuation rates (49.4% vs 49.2%, p=0.93). The raw displacement quality is statistically indistinguishable. Price moves just as much — the system just doesn't trade.

2. **None of the 6 hypotheses produced a statistically significant edge after Bonferroni correction.** The strongest result was H1 Session Sweep Reversal (53.7% in validation, p=0.084), which falls short of even the uncorrected p < 0.05 threshold.

3. **The conditional sub-split of H1 NY sweeps (57.4%, p=0.021)** is the most promising lead but requires:
   - A pre-registered hypothesis (this was found post-hoc)
   - Forward testing on new data
   - Understanding why NY shows edge but London doesn't (possibly: NY can fade London structure failures)

4. **H3 Asian Sweep has a measurement artifact.** The 8% rate reflects that Asian range is too wide as SL (mean SL ~full Asian range), making 1.5R targets unreachable in 3h for most setups. The concept may have merit with tighter SL placement.

5. **H4 OB Retest had insufficient sample size** (34 signals total, 10 in validation). This remains an open question — the existing +0.503R Phase 1 result on D1-clear days may simply require more CAT1 test data.

6. **H2 FVG Fill showed NEGATIVE edge** (38-42% continuation), suggesting FVG fills in isolation are mean-reverting — price enters FVGs but does NOT continue through them at the 1.5R threshold. This is an important anti-pattern.

### Recommendation

The current system's D1 pre-screen is NOT leaving easy money on the table. D1-unclear days do not contain readily extractable mechanical edges at the significance levels tested. The system should:

1. **Keep the D1 pre-screen** — it provides discipline without provably missing opportunities
2. **Investigate H1 NY sweeps further** — pre-register this hypothesis and test on future data (Apr-Jun 2026)
3. **Consider reducing H4 OB Retest's D1 requirement selectively** — the 34-signal sample for CAT1 dates is inconclusive, not negative. A targeted live trial on CAT1 dates with extra caution (reduced position size) could be informative
4. **Do NOT implement H2 FVG Fill or H3 Asian Sweep** — these showed negative expectancy