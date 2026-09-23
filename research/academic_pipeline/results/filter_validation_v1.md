# Filter Validation — Gap Ceiling + Touch-1
# XAUUSD Jan 2 – Apr 10, 2026

**Analysis date:** 2026-04-13
**Source:** research/t7_live_simulation/all_results_jan_apr10.json
**Baseline:** 557 entry_in_ob rejections, Scenario A: +45.0R / 45.5% WR

## Validation Checks

- [PASS] 557 records extracted (got 557)
- [PASS] Baseline fill rate: 332/557 = 59.6% (got 332/557)
- [PASS] Baseline WR: 148/325 = 45.5% (got 148/325 = 45.5%)
- [PASS] Baseline Total R: +45.0 (got +45.0R)
- [PASS] M15 index alignment: first record maps to valid M15 candle
- [FAIL] Touch-1 count plausible: 10–500 (got 0)
- [PASS] No M15 lookup misses (got 0 misses)

## 1. Filter Population Counts

| Filter | Records | % of 557 |
|--------|---------|-----------|
| No filter (baseline) | 557 | 100% |
| Gap ≤ 1.5% | 264 | 47.4% |
| Gap ≤ 2.0% | 361 | 64.8% |
| Gap ≤ 2.5% | 478 | 85.8% |
| Touch-1 only | 0 | 0.0% |
| Gap ≤ 2.0% + Touch-1 | 0 | 0.0% |

## 2. Scenario A Performance by Filter

| Filter | N setups | Fills | Resolved | WR | Total R |
|--------|----------|-------|----------|----|---------|
| Baseline (no filter) | 557 | 332/557 (59.6%) | 325 | 45.5% | +45.0R |
| Gap ≤ 1.5% only | 264 | 159/264 (60.2%) | 153 | 61.4% | +82.0R |
| Gap ≤ 2.0% only | 361 | 217/361 (60.1%) | 210 | 48.1% | +42.5R |
| Gap ≤ 2.5% only | 478 | 286/478 (59.8%) | 279 | 43.7% | +26.0R |
| Touch-1 only | 0 | 0 | 0 | N/A | +0.0R |
| Gap ≤ 2.0% + Touch-1 | 0 | 0 | 0 | N/A | +0.0R |

## 3. Monthly Breakdown

### 3a. Gap ≤ 1.5% Only (the only gap filter that improves baseline)

| Month | N setups | Fills | Resolved | WR | Total R |
|-------|----------|-------|----------|----|---------|
| 2026-01 | 41 | 14 | 14 | 64.3% | +8.5R |
| 2026-02 | 88 | 58 | 58 | 84.5% | +64.5R |
| 2026-03 | 79 | 69 | 69 | 39.1% | -1.5R |
| 2026-04 | 56 | 18 | 12 | 75.0% | +10.5R |

### 3b. Gap ≤ 2.0% + Touch-1 Combined (specified in EXEC prompt)

Combined filter produces 0 setups — touch-1 is untestable with current data (see F1 and Section 4).
All monthly cells are 0/N/A.

## 4. Touch Distribution Analysis

**Note on touch-1 definition:** "Prior touch count" was computed by scanning all M15 candles from index 0 (Jan 2, 2026) up to the record's candle_time. A "touch" = any candle with low ≤ ob_high. Since the M15 dataset begins Jan 2 and XAUUSD price has been near every OB zone level repeatedly since then, ALL 557 records have prior_touch_count ≥ 11. The "touch-1" filter (prior_touch_count = 0) eliminates all setups because it tests "never touched since Jan 2," which is never true for any zone evaluated in Jan–Apr.

**Root cause:** The Q-2.2 touch-1 hypothesis (72.7% WR) was measured relative to zone creation time — i.e., the first retest of an OB zone after it formed. The simulation results do not store zone creation timestamps, so this filter cannot be accurately implemented without adding that field to the simulation output.

| Prior touches (since Jan 2) | Count | % | Scenario A WR |
|-----------------------------|-------|---|--------------|
| 0 (never touched) | 0 | 0.0% | N/A |
| 1 | 0 | 0.0% | N/A |
| 2 | 0 | 0.0% | N/A |
| 3–5 | 0 | 0.0% | N/A |
| 6–10 | 0 | 0.0% | N/A |
| 11+ | 557 | 100.0% | 45.5% |

## 5. Key Findings

**F1: Touch-1 filter is untestable with current data.**
All 557 records have prior_touch_count ≥ 11 when scanning from Jan 2 dataset start. The Q-2.2 touch-1 result (72.7% WR) was measured relative to zone creation time, which is not stored in simulation results. To implement this filter, `simulate_t7_live_period.py` must log the OB zone formation candle_time alongside l2_reason. Until then, the touch-1 filter cannot be applied.

**F2: Gap ceiling is a strong positive filter — especially at 1.5%.**
- Gap ≤ 1.5%: 264 setups (47.4%), WR=**61.4%**, Total R=**+82.0R** (+0.31R/setup)
- Gap ≤ 2.0%: 361 setups (64.8%), WR=48.1%, Total R=+42.5R (+0.12R/setup)
- Gap ≤ 2.5%: 478 setups (85.8%), WR=43.7%, Total R=+26.0R (+0.05R/setup)
- Baseline (no filter): 557 setups, WR=45.5%, Total R=+45.0R (+0.08R/setup)

The 1.5% ceiling removes 293 setups (gap >1.5%) that contribute -37.0R combined (≈-0.13R/setup), implying those "stalest" setups are strongly net-negative. The 2.0% ceiling removes a 1.5–2.0% band that contributes -39.5R over only 97 setups (≈-0.41R/setup — highly negative).

**F3: Gap ≤ 1.5% is the only threshold that improves both WR and total R above baseline.**
- 1.5%: WR +15.9pp vs baseline, Total R +37.0R vs baseline — clear improvement
- 2.0%: WR +2.6pp, Total R -2.5R — marginal WR gain costs total R
- 2.5%: WR -1.8pp, Total R -19.0R — worse than baseline on both metrics

**F4: March WR remains below 40% breakeven even with gap ≤ 1.5% filter.**
- Baseline March (all 557): WR=33.3%, -14.5R
- Gap ≤1.5% March: WR=39.1%, -1.5R (79 setups, 69 fills, 69 resolved)
- The gap filter recovers March from -14.5R to -1.5R but WR still falls short of the 1.5R system breakeven (40%). Feb was exceptional (84.5%, +64.5R). March weakness appears structural, not curable by gap filtering alone.

**F5: Sample size note.**
Gap ≤1.5% produces 153 resolved trades across Jan–Apr — sufficient for descriptive comparison but not large enough for significance testing. No p-values computed; this is exploratory. Formal testing requires independent out-of-sample validation.
