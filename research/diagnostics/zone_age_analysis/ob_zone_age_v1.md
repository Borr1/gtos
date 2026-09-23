# Q-2.2: OB Zone Age vs Continuation Rate

**Date:** 2026-04-11 19:14
**Version:** v1
**Script:** `research/diagnostics/zone_age_analysis/compute_zone_age_v1.py`

---

## 1  Data Source

| Field | Value |
|-------|-------|
| Source | H1 candle CSVs in `exports/multi_instrument/` |
| Instruments analysed | 13 of 13 |
| Total OBs detected | 16,087 |
| Total retest events (all touches) | 106,147 |
| First-touch events (touch_number == 1) | 23,575 |
| Multi-touch events (touch_number >= 2) | 82,572 |
| Instrument date ranges | 2022-11 to 2026-04 (≈ 3.5 years) |
| OB detection params | SWING_MIN_BARS=2, MIN_DISPLACEMENT_ATR=0.4, BODY_RATIO_MIN=0.4 |
| Retest window | 250 H1 bars (≈10 trading days) |
| Continuation window | 20 bars, target=1.25×ATR, stop=0.5×ATR |

### Per-Instrument Event Counts

| Instrument | OBs | 1st-Touch | Multi-Touch | Overall Cont% |
|-----------|-----|-----------|-------------|--------------|
| XAUUSD | 1188 | 1758 | 5750 | 41.5% |
| US30_cash | 1208 | 1762 | 5871 | 43.0% |
| GBPUSD | 1233 | 1828 | 6607 | 40.2% |
| USDJPY | 1235 | 1823 | 6358 | 40.0% |
| NZDUSD | 1261 | 1824 | 6501 | 41.4% |
| GBPJPY | 1239 | 1845 | 6972 | 40.6% |
| EURJPY | 1216 | 1797 | 6892 | 38.8% |
| EURUSD | 1211 | 1770 | 6117 | 40.5% |
| USDCAD | 1283 | 1822 | 6141 | 39.7% |
| AUDUSD | 1188 | 1720 | 6655 | 39.3% |
| XAGUSD | 1191 | 1708 | 5795 | 41.6% |
| US500_cash | 1309 | 1942 | 6314 | 41.4% |
| USOIL_cash | 1325 | 1976 | 6599 | 41.8% |

---

## 2  Age Metric Distributions

### Metric A — Formation Age (bars to first touch)

| Stat | Value |
|------|-------|
| n | 106,147 |
| mean | 73.1 |
| median | 47.0 |
| std | 74.6 |
| min | 1 |
| p25 | 5.0 |
| p75 | 127.0 |
| max | 250 |

### Metric B — Touch Number

| Stat | Value |
|------|-------|
| n | 106,147 |
| mean | 3.8 |
| median | 3.0 |
| std | 2.7 |
| min | 1 |
| p25 | 2.0 |
| p75 | 5.0 |
| max | 20 |

### Metric C — Bars Since Last Touch

| Stat | Value |
|------|-------|
| n | 106,147 |
| mean | 23.7 |
| median | 8.0 |
| std | 38.3 |
| min | 1 |
| p25 | 2.0 |
| p75 | 26.0 |
| max | 249 |

---

## 3  Quartile Analysis

### Metric A — Formation Age (bars)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–5 bars) | 26751 | 18195 | 68.0% | [67.5%, 68.6%] |
| Q2 (5–47 bars) | 26495 | 8220 | 31.0% | [30.5%, 31.6%] |
| Q3 (47–127 bars) | 26423 | 8373 | 31.7% | [31.1%, 32.3%] |
| Q4 (127–250 bars) | 26478 | 8437 | 31.9% | [31.3%, 32.4%] |

**Fisher exact tests (raw p):**

- Q1 vs Q4: 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*
- Q1 vs Q2: 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*
- Q2 vs Q3: 1.0106e-01 (corrected 5.9626e+00)
- Q3 vs Q4: 6.6753e-01 (corrected 3.9384e+01)

### Metric B — Touch Number (clipped 1–4)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (touch 1–2) | 43604 | 23476 | 53.8% | [53.4%, 54.3%] |
| Q2 (touch 2–3) | 16197 | 5073 | 31.3% | [30.6%, 32.0%] |
| Q3 (touch 3–4) | 46346 | 14676 | 31.7% | [31.2%, 32.1%] |

**Fisher exact tests (raw p):**

- Q1 vs Q2: 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*
- Q2 vs Q3: 4.2075e-01 (corrected 2.4824e+01)

### Metric C — Bars Since Last Touch

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–2 bars) | 28175 | 18588 | 66.0% | [65.4%, 66.5%] |
| Q2 (2–8 bars) | 26322 | 8301 | 31.5% | [31.0%, 32.1%] |
| Q3 (8–26 bars) | 25919 | 8229 | 31.7% | [31.2%, 32.3%] |
| Q4 (26–249 bars) | 25731 | 8107 | 31.5% | [30.9%, 32.1%] |

**Fisher exact tests (raw p):**

- Q1 vs Q4: 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*
- Q1 vs Q2: 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*
- Q2 vs Q3: 6.0487e-01 (corrected 3.5687e+01)
- Q3 vs Q4: 5.5744e-01 (corrected 3.2889e+01)

---

## 4  Logistic Regression

Model: `continuation ~ age_metric` (statsmodels Logit, Wald test on beta)

| Metric | n | beta | p (Wald) | pseudo-R² |
|--------|---|------|----------|-----------|
| Metric A: formation_age_bars | 106,147 | -0.005071 | 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT* | 0.02363 |
| Metric B: touch_number | 106,147 | -0.160871 | 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT* | 0.02865 |
| Metric C: bars_since_last_touch | 106,147 | -0.006385 | 5.5085e-258 (corrected 3.2500e-256) *SIGNIFICANT* | 0.00915 |

> **Beta interpretation:** negative beta for Metric A means older zones have lower
> continuation rates (confirming the pre-committed hypothesis if significant).

---

## 5  Threshold Scan (Metric A — Formation Age)

| Threshold | n(young) | Cont%(young) | n(old) | Cont%(old) | Δpp | Fisher p |
|-----------|----------|-------------|--------|------------|-----|---------|
|  10 bars | 31348 | 62.5% | 74799 | 31.6% | +31.0pp | 0.0000e+00 |
|  20 bars | 38550 | 56.4% | 67597 | 31.8% | +24.7pp | 0.0000e+00 |
|  30 bars | 44850 | 53.1% | 61297 | 31.7% | +21.4pp | 0.0000e+00 |
|  40 bars | 49779 | 50.9% | 56368 | 31.7% | +19.2pp | 0.0000e+00 |
|  50 bars | 54306 | 49.3% | 51841 | 31.7% | +17.6pp | 0.0000e+00 |
|  60 bars | 58317 | 48.1% | 47830 | 31.7% | +16.3pp | 0.0000e+00 |
|  70 bars | 62011 | 47.0% | 44136 | 31.8% | +15.2pp | 0.0000e+00 |
|  80 bars | 65893 | 46.2% | 40254 | 31.7% | +14.5pp | 0.0000e+00 |
|  90 bars | 68921 | 45.6% | 37226 | 31.7% | +13.8pp | 0.0000e+00 |
| 100 bars | 72106 | 44.9% | 34041 | 31.8% | +13.2pp | 0.0000e+00 |
| 110 bars | 74891 | 44.5% | 31256 | 31.7% | +12.8pp | 0.0000e+00 |
| 120 bars | 77537 | 44.0% | 28610 | 31.8% | +12.2pp | 3.8943e-289 |
| 130 bars | 80244 | 43.6% | 25903 | 31.9% | +11.6pp | 2.9787e-244 |
| 140 bars | 82697 | 43.2% | 23450 | 32.0% | +11.1pp | 2.7818e-210 |
| 150 bars | 85365 | 42.8% | 20782 | 32.2% | +10.6pp | 3.4659e-176 |
| 160 bars | 87634 | 42.6% | 18513 | 32.0% | +10.5pp | 3.2781e-158 |
| 170 bars | 89875 | 42.3% | 16272 | 31.9% | +10.5pp | 1.6110e-141 |
| 180 bars | 92145 | 42.1% | 14002 | 31.8% | +10.3pp | 1.1397e-120 |
| 190 bars | 94311 | 41.8% | 11836 | 31.7% | +10.1pp | 1.9233e-101 |
| 200 bars | 96302 | 41.6% |  9845 | 32.0% | +9.6pp | 2.1519e-77 |

**Optimal threshold (minimum Fisher p):** 10 bars
- Young (< 10 bars): 62.5%  n=31348
- Old (≥ 10 bars): 31.6%  n=74799
- Δ = +31.0pp  |  raw p = 0.0000e+00  |  Bonferroni: 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*

---

## 6  Touch Count Table (Metric B)

| Touch # | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| 1 | 23,575 | 17,133 | 72.7% | [72.1%, 73.2%] |
| 2 | 20,029 | 6,343 | 31.7% | [31.0%, 32.3%] |
| 3 | 16,197 | 5,073 | 31.3% | [30.6%, 32.0%] |
| 4+ | 46,346 | 14,676 | 31.7% | [31.2%, 32.1%] |

**Chi-squared across groups:** 0.0000e+00 (corrected 0.0000e+00) *SIGNIFICANT*

---

## 3C  Critical: Formation Age vs Touch Number — Confounding Check

The massive formation_age effect requires a confounding investigation.
Q1 (formation_age 1–5 bars) has 68% continuation; Q4 (127–250 bars) has 31.9%.
**But are these different-age zones, or the same zones retested multiple times?**

### Q1 (1–5 bars) composition by touch number

| Touch # | n | % of Q1 | Cont% |
|---------|---|---------|-------|
| 1 | 23,543 | 88.0% | 72.7% |
| 2 | 3,181 | 11.9% | 33.6% |
| 3+ | 27 | 0.1% | 22.2% |

> Q1 is **88% first-touch events** (the one with 72.7% continuation).
> Q2–Q4 are dominated by multi-touch events (touch 2, 3, 4+) which systematically have ~31–32% continuation.

### First-touch-only formation age distribution

| Stat | Value |
|------|-------|
| n (touch_number == 1) | 23,575 |
| median formation_age | **1 bar** |
| events with formation_age < 10 bars | 23,545 (99.9%) |
| events with formation_age ≥ 10 bars | 30 (0.1%) |

**The formation_age effect for the full dataset is a proxy for touch_number.**
Among first-touch events, 99.9% retest within 10 bars of formation — there is
essentially no variation in formation age for the events that matter to GTOS.

### First-touch formation age threshold scan (GTOS-relevant)

| Threshold | n(young) | Cont%(young) | n(old) | Cont%(old) | Δpp | Fisher p |
|-----------|----------|-------------|--------|------------|-----|---------|
| <10 bars | 23,545 | 72.7% | 30 | 43.3% | +29.4pp | 7.4e-04 |
| <20 bars | 23,565 | 72.7% | 10 | 70.0% | +2.7pp | 1.000 |
| <30 bars | 23,565 | 72.7% | 10 | 70.0% | +2.7pp | 1.000 |

> The only marginally significant threshold (10 bars) is based on just **30 events** (0.1% of first touches).
> No practically meaningful variation exists in formation age for first-touch events.

**Conclusion from confounding check:** The formation_age finding is real when pooling all touches,
but it is entirely explained by touch_number. The primary predictor is TOUCH NUMBER.

---

## 7  Per-Instrument Breakdown (Metric A — Formation Age)

Quartile analysis restricted to the 5 live GTOS instruments.
**Note:** These tables include all touch events (touch 1 + multi-touch).
For first-touch-only continuations by instrument, see Section 9.4.
The Q1 vs Q4 split reflects the touch-number confound documented in Section 3C.

### XAUUSD  (n=7,508 retest events)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–5 bars) | 1968 | 1392 | 70.7% | [68.7%, 72.7%] |
| Q2 (5–44 bars) | 1787 | 560 | 31.3% | [29.2%, 33.5%] |
| Q3 (44–124 bars) | 1887 | 581 | 30.8% | [28.7%, 32.9%] |
| Q4 (124–250 bars) | 1866 | 580 | 31.1% | [29.0%, 33.2%] |

Fisher tests (raw p):
- Q1 vs Q4: 1.5132e-136 (corrected 8.9279e-135) *SIGNIFICANT*
- Q1 vs Q2: 7.7627e-132 (corrected 4.5800e-130) *SIGNIFICANT*
- Q2 vs Q3: 7.2149e-01 (corrected 4.2568e+01)
- Q3 vs Q4: 8.5987e-01 (corrected 5.0732e+01)

### US30_cash  (n=7,633 retest events)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–4 bars) | 1912 | 1371 | 71.7% | [69.6%, 73.7%] |
| Q2 (4–47 bars) | 1921 | 615 | 32.0% | [30.0%, 34.1%] |
| Q3 (47–120 bars) | 1892 | 693 | 36.6% | [34.5%, 38.8%] |
| Q4 (120–250 bars) | 1908 | 604 | 31.7% | [29.6%, 33.8%] |

Fisher tests (raw p):
- Q1 vs Q4: 6.5722e-139 (corrected 3.8776e-137) *SIGNIFICANT*
- Q1 vs Q2: 5.8259e-137 (corrected 3.4373e-135) *SIGNIFICANT*
- Q2 vs Q3: 2.9908e-03 (corrected 1.7646e-01)
- Q3 vs Q4: 1.2979e-03 (corrected 7.6573e-02)

### USDJPY  (n=8,181 retest events)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–5 bars) | 2064 | 1440 | 69.8% | [67.8%, 71.7%] |
| Q2 (5–45 bars) | 2037 | 611 | 30.0% | [28.0%, 32.0%] |
| Q3 (45–129 bars) | 2067 | 624 | 30.2% | [28.2%, 32.2%] |
| Q4 (129–250 bars) | 2013 | 594 | 29.5% | [27.6%, 31.5%] |

Fisher tests (raw p):
- Q1 vs Q4: 1.2701e-149 (corrected 7.4939e-148) *SIGNIFICANT*
- Q1 vs Q2: 7.6500e-147 (corrected 4.5135e-145) *SIGNIFICANT*
- Q2 vs Q3: 9.1868e-01 (corrected 5.4202e+01)
- Q3 vs Q4: 6.5649e-01 (corrected 3.8733e+01)

### GBPJPY  (n=8,817 retest events)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–7 bars) | 2317 | 1512 | 65.3% | [63.3%, 67.2%] |
| Q2 (7–51 bars) | 2116 | 643 | 30.4% | [28.5%, 32.4%] |
| Q3 (51–130 bars) | 2180 | 685 | 31.4% | [29.5%, 33.4%] |
| Q4 (130–250 bars) | 2204 | 740 | 33.6% | [31.6%, 35.6%] |

Fisher tests (raw p):
- Q1 vs Q4: 3.8465e-102 (corrected 2.2694e-100) *SIGNIFICANT*
- Q1 vs Q2: 1.7413e-121 (corrected 1.0274e-119) *SIGNIFICANT*
- Q2 vs Q3: 4.6776e-01 (corrected 2.7598e+01)
- Q3 vs Q4: 1.2976e-01 (corrected 7.6556e+00)

### GBPUSD  (n=8,435 retest events)

| Quartile | n | Cont | Cont% | 95% CI |
|---------|---|------|-------|--------|
| Q1 (1–6 bars) | 2166 | 1415 | 65.3% | [63.3%, 67.3%] |
| Q2 (6–52 bars) | 2063 | 599 | 29.0% | [27.1%, 31.0%] |
| Q3 (52–131 bars) | 2103 | 683 | 32.5% | [30.5%, 34.5%] |
| Q4 (131–250 bars) | 2103 | 697 | 33.1% | [31.2%, 35.2%] |

Fisher tests (raw p):
- Q1 vs Q4: 1.1903e-99 (corrected 7.0228e-98) *SIGNIFICANT*
- Q1 vs Q2: 3.8045e-126 (corrected 2.2446e-124) *SIGNIFICANT*
- Q2 vs Q3: 1.7142e-02 (corrected 1.0114e+00)
- Q3 vs Q4: 6.6944e-01 (corrected 3.9497e+01)

---

## 8  Bonferroni Correction Summary

**Total tests in this analysis:** 59
**Bonferroni threshold (α=0.05):** 0.000847
**Equivalent: raw p must be < 8.4746e-04 to survive**

**Findings surviving Bonferroni correction:**

- Quartile formation_age_bars: Q1 vs Q4, raw p=0.0000e+00
- Quartile formation_age_bars: Q1 vs Q2, raw p=0.0000e+00
- Quartile touch_number_q: Q1 vs Q2, raw p=0.0000e+00
- Quartile bars_since_last_touch: Q1 vs Q4, raw p=0.0000e+00
- Quartile bars_since_last_touch: Q1 vs Q2, raw p=0.0000e+00
- Logistic formation_age_bars: beta=-0.005071, raw p=0.0000e+00
- Logistic touch_number: beta=-0.160871, raw p=0.0000e+00
- Logistic bars_since_last_touch: beta=-0.006385, raw p=5.5085e-258
- Threshold scan 10 bars: raw p=0.0000e+00
- Threshold scan 20 bars: raw p=0.0000e+00
- Threshold scan 30 bars: raw p=0.0000e+00
- Threshold scan 40 bars: raw p=0.0000e+00
- Threshold scan 50 bars: raw p=0.0000e+00
- Threshold scan 60 bars: raw p=0.0000e+00
- Threshold scan 70 bars: raw p=0.0000e+00
- Threshold scan 80 bars: raw p=0.0000e+00
- Threshold scan 90 bars: raw p=0.0000e+00
- Threshold scan 100 bars: raw p=0.0000e+00
- Threshold scan 110 bars: raw p=0.0000e+00
- Threshold scan 120 bars: raw p=3.8943e-289
- Threshold scan 130 bars: raw p=2.9787e-244
- Threshold scan 140 bars: raw p=2.7818e-210
- Threshold scan 150 bars: raw p=3.4659e-176
- Threshold scan 160 bars: raw p=3.2781e-158
- Threshold scan 170 bars: raw p=1.6110e-141
- Threshold scan 180 bars: raw p=1.1397e-120
- Threshold scan 190 bars: raw p=1.9233e-101
- Threshold scan 200 bars: raw p=2.1519e-77
- Touch count chi-sq: raw p=0.0000e+00

---

## 9  Conclusion

**The primary finding is touch number, not formation age.**

### 9.1  What the full-population tests show (all 106,147 events)

29 of 59 tests survive Bonferroni correction (α/n = 8.4746e-04). In the pooled dataset:

- **Metric A (formation age):** Q1 (1–5 bars) = 68.0% vs Q4 (127–250 bars) = 31.9% (Δ=+36.1pp). Beta=−0.0051, p≈0. **CONFIRMED SIGNIFICANT** in the full population.
- **Metric B (touch count):** Touch-1 = 72.7% vs Touch-2 = 31.7% (Δ=+41.0pp). Beta=−0.161, p≈0. **CONFIRMED SIGNIFICANT**.
- **Metric C (bars since last touch):** Q1 (1–2 bars) = 66.0% vs Q4 (26–249 bars) = 31.5% (Δ=+34.5pp). Beta=−0.0064, p≈0. **CONFIRMED SIGNIFICANT**.

### 9.2  Critical confound revealed (Section 3C)

The formation_age and bars_since_last_touch effects are **proxies for touch_number**:

- Q1 of formation_age (1–5 bars): **88% are touch-1 events** (which have 72.7% continuation)
- Q2–Q4 of formation_age: dominated by touch-2+ events (which have ~31–32% continuation)
- Within first-touch events only: **99.9% retest within 10 bars of formation** — no meaningful formation-age variation exists for GTOS's trading universe

### 9.3  The real finding

**Touch number is the operative predictor, not time/age.**

| Event type | n | Cont% | 95% CI |
|-----------|---|-------|--------|
| Touch 1 (first retest) | 23,575 | **72.7%** | [72.1%, 73.2%] |
| Touch 2 | 20,029 | **31.7%** | [31.0%, 32.3%] |
| Touch 3 | 16,197 | **31.3%** | [30.6%, 32.0%] |
| Touch 4+ | 46,346 | **31.7%** | [31.2%, 32.1%] |

The drop from touch-1 to touch-2 is **−41.0pp** and is consistent across all 13 instruments and all formation ages. After the first retest, continuation stabilises at ~31–32% regardless of how much additional time passes.

This is consistent with the Osler stop-cascade mechanism: the **first** retest depletes the densest stop cluster. Subsequent retests find conditions already depleted. The depletion is immediate (between touch 1 and touch 2), not gradual over time.

### 9.4  First-touch-only results (XAUUSD, US30, USDJPY, GBPJPY, GBPUSD)

| Instrument | n (touch 1) | Cont% |
|-----------|------------|-------|
| XAUUSD | 1,758 | **75.1%** |
| US30_cash | 1,762 | **75.1%** |
| USDJPY | 1,823 | **73.8%** |
| GBPJPY | 1,845 | **72.3%** |
| GBPUSD | 1,828 | **72.4%** |

These closely match the original mechanical screening results (70–74%), validating the methodology.

---

## 10  Actionable Recommendation for GTOS

**DO NOT add a zone age filter. GTOS already captures the optimal probability point.**

### Reasoning

1. **GTOS already trades touch-1 only** — the first time price returns to an OB zone. This gives 72.7% continuation across all instruments, which is what the original screening measured.

2. **Formation age within first-touch events has no practical variation** — 99.9% of first retests occur within 10 bars of OB formation, regardless of how old the zone "is" in calendar time.

3. **Adding a `formation_age < 10` filter would be nearly vacuous** — it would exclude only 30 events (0.1% of first touches) with a sample size too small (n=30) to draw reliable conclusions.

4. **The touch-count finding is already embedded in GTOS architecture** — the system creates a new OB on each new BOS/CHoCH and evaluates it once (first retest). It does not re-enter the same zone after a failed retest.

### WF-2 candidate (low priority)

The touch-count finding is strong (p≈0, Δ=41pp) and already operationalised. If the system is ever extended to consider re-entries on a failed first touch, **explicitly block re-entries on the same OB** — this would prevent taking the 31.7%-continuation second touch.

**Explicit confirmation rule (for documentation):** "After a first-retest trade on an OB (win or loss), do not re-trade the same zone." This is already implicit in current architecture but should be codified.

### Summary

| Question | Answer |
|---------|--------|
| Does zone age predict continuation? | Yes, in the full population (Bonferroni-corrected) |
| Is the effect driven by formation time or touch count? | Touch count — formation age is a proxy |
| Does this require a GTOS filter change? | No |
| Is GTOS already optimally positioned? | Yes — it trades touch-1 only at 72.7% |
| Is there any WF-2 candidate from this analysis? | Only: explicit "no re-entry on same OB" rule (already implicit) |
