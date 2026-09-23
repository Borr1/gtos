# Feasibility Checks: Three Expansion Hypotheses

**Date:** 2026-04-01
**Baseline:** ob_retest on XAUUSD, 101 trades, +0.235R expectancy, 69.3% WR, ~5 trades/month

---

## Check 1: Breaker Block Frequency

### What We Tested
A breaker block forms when an order block FAILS — price trades through it, and the failed zone becomes a potential entry from the other side. We counted how often this pattern occurs during kill zones using H1 candle data from Apr 2024 - Mar 2026.

### Raw Numbers

| Metric | Count |
|--------|-------|
| H1 order blocks formed | 1,538 |
| OBs mitigated/broken (became breaker blocks) | 1,313 (85.4%) |
| Breaker blocks subsequently retested | 1,287 |
| **Retests during kill zones** | **250** |
| — London (07:00-09:30) | 98 |
| — NY (13:00-15:30) | 152 |
| Retests outside kill zones | 1,037 |

| Timing Metric | Value |
|---------------|-------|
| Average hours from OB failure to breaker retest | 32.9h |
| **KZ breaker retests per month** | **10.4** |
| Range: lowest month (Feb 2026) | 2 |
| Range: highest month (May 2025) | 24 |

### Monthly Breakdown

| Month | KZ Retests | Total Retests |
|-------|-----------|---------------|
| 2024-04 | 8 | 30 |
| 2024-05 | 21 | 70 |
| 2024-06 | 10 | 49 |
| 2024-07 | 13 | 66 |
| 2024-08 | 12 | 62 |
| 2024-09 | 7 | 35 |
| 2024-10 | 4 | 43 |
| 2024-11 | 17 | 78 |
| 2024-12 | 11 | 58 |
| 2025-01 | 19 | 84 |
| 2025-02 | 9 | 54 |
| 2025-03 | 5 | 29 |
| 2025-04 | 8 | 58 |
| 2025-05 | 24 | 92 |
| 2025-06 | 12 | 55 |
| 2025-07 | 5 | 56 |
| 2025-08 | 11 | 48 |
| 2025-09 | 9 | 39 |
| 2025-10 | 10 | 72 |
| 2025-11 | 6 | 38 |
| 2025-12 | 7 | 30 |
| 2026-01 | 9 | 37 |
| 2026-02 | 2 | 44 |
| 2026-03 | 11 | 60 |

### Interpretation

85% of H1 order blocks eventually get mitigated — this is expected in a ranging/mean-reverting intraday structure. Of those, nearly all get retested, and 10.4 of those retests per month fall during kill zones.

This is significantly higher raw frequency than ob_retest (~5 trades/month). Even after applying Claude's AI filtering (which typically passes ~10-15% of raw candidates as CANDIDATE), we'd expect 1-2 breaker block trades per month.

**Important caveats:**
- This counts raw pattern frequency, not profitability
- The simplified detection doesn't apply M15 confirmation or D1/H4 bias checks
- Some of these breaker retests may overlap with our existing ob_retest triggers (same price zone, different classification)
- The detection algorithm is simplified — production would use the full MSO pipeline

### Verdict: **PROMISING**

10.4 KZ retests/month far exceeds the 3/month threshold. Even with aggressive AI filtering, breaker blocks could add 1-2 trades/month to the existing ~5, representing a 20-40% increase in trade frequency. **Justify building a full breaker block strategy for backtesting with Claude.**

---

## Check 2: Tick Volume Preliminary

### Data Availability

The M15 CSV files contain a `volume` column with integer values (range: ~300-5000). MT5 forex exports store tick volume in this field (real volume is always 0 for forex). This IS tick volume data.

**Data available: YES** — 47,142 M15 candles with tick volume, all 101 trades matched.

### Preliminary Volume Analysis

| Metric | WIN trades (n=70) | LOSS trades (n=28) | Difference |
|--------|------------------|-------------------|------------|
| **Trigger candle volume** | | | |
| Mean | 2,782 | 3,083 | -9.8% |
| Median | 1,152 | 1,096 | +5.1% |
| **Pre-trigger candle volume** | | | |
| Mean | 2,543 | 2,403 | +5.9% |
| Median | 1,124 | 1,044 | +7.7% |
| **Relative to KZ average** | | | |
| Mean | 1.03x | 1.05x | -2.4% |

### Interpretation

There is **no meaningful volume difference** between winning and losing trades:
- Trigger candle: losses have slightly HIGHER mean volume (-9.8%), but medians are nearly identical
- Pre-trigger candle: winners have marginally higher volume (+5.9%), but the difference is tiny
- Relative to KZ average: both groups trade at essentially 1.0x the session average volume

The mean/median divergence on trigger candles (mean=2782 vs median=1152 for wins) suggests a few high-volume outliers distorting the mean. The median comparison is more reliable and shows no difference.

### Verdict: **NOT PROMISING**

Tick volume does not differentiate winning from losing ob_retest trades. The differences are noise-level (< 10%) and inconsistent in direction. Volume-based confidence filtering would not work for this strategy.

**Do not invest further in volume analysis for ob_retest.** Volume might matter for other pattern types (e.g., breaker blocks where you want to see high volume on the mitigation candle), but that's a separate test for later.

---

## Check 3: Wider Kill Zone Opportunity Scan

### Candle Counts by Window

| Window | M15 Candles (24mo) | Per Month |
|--------|-------------------|-----------|
| Pre-London (06:00-07:00) | 2,052 | 85.5 |
| **Current London (07:00-09:30)** | **5,140** | **214.2** |
| Post-London (09:30-10:30) | 2,057 | 85.7 |
| Pre-NY (12:00-13:00) | 2,064 | 86.0 |
| **Current NY (13:00-15:30)** | **5,159** | **215.0** |
| Post-NY (15:30-17:00) | 3,093 | 128.9 |

### Pre-Screen Pass Rates

Using simplified D1 bias + H4 alignment check (same logic as production):

| Extended Window | Total Candles | Pre-Screen Passed | Pass Rate |
|----------------|---------------|-------------------|-----------|
| Pre-London (06:00-07:00) | 2,052 | 820 | **40.0%** |
| Post-London (09:30-10:30) | 2,057 | 729 | 35.4% |
| Pre-NY (12:00-13:00) | 2,064 | 718 | 34.8% |
| Post-NY (15:30-17:00) | 3,093 | 1,090 | 35.2% |

### Overlap with Existing Trade Dates

On the 82 unique dates where ob_retest already took trades:

| Extended Window | Pre-screened candles on NON-trade days |
|----------------|----------------------------------------|
| Pre-London (06:00-07:00) | 696 |
| Post-London (09:30-10:30) | 593 |
| Pre-NY (12:00-13:00) | 570 |
| Post-NY (15:30-17:00) | 868 |

All 82 trade dates overlap with all extended windows (expected — a trade date has candles in every window). The key metric is the "non-trade day" candles that pass pre-screen — these represent genuinely NEW opportunities the system currently misses.

### Interpretation

**Pre-London (06:00-07:00) has the highest pre-screen pass rate (40.0%)** — this makes sense because the D1/H4 bias established overnight tends to be strongest just before London opens. However:

1. **Pre-London is risky.** The 06:00-07:00 window is before the London open. Institutional flow hasn't started. Setups here lack the liquidity confirmation that makes London 07:00-09:30 work. Our vertical analysis showed London early (07:00-08:15) already underperforms London late (08:15-09:30) by 17% WR — going EARLIER than 07:00 is likely worse.

2. **Post-NY (15:30-17:00) has the most raw volume** (868 passed candles on non-trade days) because it's a wider window (1.5 hours vs 1 hour). But post-NY is after the main institutional session and tends to have lower liquidity and more choppy action.

3. **Post-London (09:30-10:30) is the most natural extension.** London institutional flow often continues past 09:30. The vertical analysis showed London late (08:15-09:30) has 82.8% WR — the 09:30-10:30 window is a continuation of this high-WR period.

4. **Pre-NY (12:00-13:00)** would catch the London/NY overlap preparation. Some institutional positioning happens here. 570 pre-screened candles on non-trade days (~24/month).

### Verdict: **WORTH TESTING — Post-London (09:30-10:30) first**

Extending London from 09:30 to 10:30 is the lowest-risk test:
- It's a natural continuation of the high-WR London late window
- ~593 pre-screened candles on non-trade days (~25/month)
- Institutional London flow often extends to 10:00-10:30
- Minimal risk of catching choppy/low-liquidity conditions

**Do NOT test Pre-London (06:00-07:00)** — going earlier than 07:00 contradicts our finding that London early already underperforms.

**Pre-NY (12:00-13:00) is second priority** — could catch London/NY overlap setups.

---

## Summary

| Hypothesis | Verdict | Next Step | Expected Impact |
|------------|---------|-----------|-----------------|
| **Breaker Block Strategy** | **PROMISING** | Build framework, create PA prompt, run batch backtest | +1-2 trades/month (20-40% more frequency) |
| **Tick Volume Filter** | **NOT PROMISING** | Kill this hypothesis | None — no signal detected |
| **Wider Kill Zones** | **WORTH TESTING** | Extend London to 10:30, test with existing ob_retest | +0-1 trades/month, possibly at high WR |

### Priority Order
1. **Breaker blocks** — highest potential impact, well-supported by frequency data
2. **Post-London extension** — low cost to test (just change `LONDON_END` config), leverages existing edge
3. ~~Tick volume~~ — killed, no signal

### What NOT To Do
- Don't widen ALL kill zones at once — test Post-London first, validate, then consider Pre-NY
- Don't build breaker blocks AND wider KZ simultaneously — breaker blocks first (higher potential)
- Don't revisit tick volume unless we get true tick-by-tick data (not just bar volume)
