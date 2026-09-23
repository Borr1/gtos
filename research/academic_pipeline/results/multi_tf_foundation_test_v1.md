# Multi-Timeframe Foundation Test — M15 OB Continuation

**Date:** 2026-04-13 00:15
**Data:** 5 instruments, 37,831 M15 candles, 11,248 at-OB events, 32,368 origin revisits
**Period:** 2024-01-02 to 2026-04-02 (2+ years)
**Instruments:** XAUUSD, GBPUSD, EURUSD, NAS100, XAGUSD
**Cost:** $0 (displacement database only)

---

## Hypothesis

> During H1 consolidation, M15 OB retest setups that align with H1 bias produce continuation rates above 55%.

**Pre-registered decision gate:** If no filter combination produces a rate > 55% that survives Bonferroni correction across 42 tests, the multi-TF expansion is dead.

---

## Results

### Baseline: M15 OB 1-Hour Continuation = 49.9% (random)

| Instrument | n (at OB) | cont_1h Rate | p-value (>50%) | Significant? |
|------------|-----------|--------------|----------------|-------------|
| All combined | 11,248 | 49.9% | 0.615 | NO |
| XAUUSD | 2,202 | 49.9% | 0.559 | NO |
| GBPUSD | 2,361 | 51.0% | 0.183 | NO |
| EURUSD | 2,371 | 51.8% | 0.046 | borderline |
| NAS100 | 2,033 | 48.2% | 0.950 | NO |
| XAGUSD | 2,281 | 48.3% | 0.953 | NO |

### Single Filters — None Work

| Filter | n | Rate | p-value | Significant? |
|--------|---|------|---------|-------------|
| Kill zone only | 2,872 | 48.4% | 0.959 | NO (worse) |
| M15 aligned with H1 | 2,281 | 51.2% | 0.138 | NO |
| High consol (>P75) | 2,811 | 51.0% | 0.137 | NO |
| Low consol (<P25) | 2,808 | 48.6% | 0.927 | NO (worse) |
| Strong body_ratio (>P75) | 2,800 | 48.1% | 0.980 | NO (worse) |
| Bullish OBs | 5,839 | 49.5% | 0.791 | NO |
| Bearish OBs | 5,409 | 50.3% | 0.342 | NO |
| London session | 3,276 | 50.2% | 0.410 | NO |
| NY session | 4,898 | 49.1% | 0.903 | NO |
| 2025+ only | 6,077 | 50.3% | 0.322 | NO |

### Combined Filters — Still Nothing Survives

| Filter | n | Rate | p-value | Bonferroni? |
|--------|---|------|---------|------------|
| KZ + M15 aligned | 602 | 53.3% | 0.056 | NO |
| KZ + aligned + strong body | 108 | 55.6% | 0.145 | NO |
| KZ + aligned + high consol | 68 | 51.5% | 0.452 | NO |
| KZ + aligned + low consol | 244 | 55.7% | 0.042 | NO (p > 0.0012) |
| London + aligned | 695 | 54.7% | 0.008 | NO (p > 0.0012) |
| NY + aligned | 959 | 48.7% | 0.799 | NO |
| KZ + bullish OB + aligned | 327 | 51.4% | 0.329 | NO |
| MAX: KZ+aligned+strong+bullish | 64 | 54.7% | 0.266 | NO |

### The Only Signal: Origin Revisit Continuation (different metric)

| Filter | n | revisit_continued | p-value | Bonferroni? |
|--------|---|-------------------|---------|------------|
| All revisited | 32,368 | 58.0% | 2e-184 | **YES** |
| KZ revisited | 7,270 | 56.1% | 3e-25 | **YES** |
| KZ revisited + aligned | 1,527 | 57.1% | 2e-08 | **YES** |

---

## Interpretation

### What the data says

1. **M15 OB at-candle continuation is 50% = random coin flip.** No filter combination on 37,831 candles across 5 instruments and 2+ years can lift this above 55% with statistical significance.

2. **Kill zone filtering makes it WORSE (48.4%).** The M15 OB pattern has no kill-zone edge.

3. **The origin-revisit-continuation signal exists at ~57%** but this is the OB retest rate itself — price revisits the OB zone and continues in the original direction 57% of the time. This is 13pp below the validated H1 rate of 70%.

4. **The 13pp gap (57% M15 → 70% H1) IS the H1 structural context edge.** The BOS filter on H1 provides the additional discrimination that separates tradeable from random.

### Why multi-TF expansion won't work

- The edge is NOT in the OB pattern itself (which is ~57% at M15)
- The edge is in the H1 BOS-filtered OB retest (which reaches ~70%)
- Going to lower timeframes removes the H1 structural context that provides the edge
- No M15 filter combination recovers the lost 13pp
- The fractal propagation concept is structurally valid but the edge doesn't propagate — it is specific to the H1-structure-break context

### What this means for frequency

Multi-TF expansion as a frequency multiplier is **ruled out**. The path to increased trade frequency must come from:
- Improved prompt selectivity (higher CR at same WR) — what Phase 2A is targeting
- More instruments (if they meet WR threshold)
- NOT from lower timeframe setups

---

## Bonferroni-Corrected Summary

42 tests performed. Bonferroni threshold: p < 0.0012.

**Survivors:** Only the origin-revisit-continuation metric (58%, 56.1%, 57.1%) — which measures the OB retest mechanism itself, not a new tradeable signal.

**Zero M15 OB at-candle continuation filters survive correction.**

---

## Decision

**KILL the multi-TF expansion idea.** The data is unambiguous across 5 instruments and 2+ years: M15 OBs without H1 structural context are random.
