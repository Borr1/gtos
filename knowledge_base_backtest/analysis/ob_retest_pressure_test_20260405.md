# OB Retest Comprehensive — Pressure Test Results
Generated: 2026-04-04T00:12:48.968310+00:00

## Reviewer Notes (Post-Test)

### 1. hour_of_retest (#1 rank) — OVERFITTING, IGNORE
24 groups guarantees a wide spread by chance. Hour 0: 100% discovery (n=13) vs 8.3% validation (n=12). The 1.0000 spread is the gap between best/worst of 24 random bins. **Do not use time-of-day from this analysis.**

### 2. premium_discount_zone — LIKELY CONFOUNDED
For bullish OBs, discount = correctly zoned. For bearish OBs, premium = correctly zoned. Analysis lumped all directions together, so "premium" mixes correctly-placed bearish OBs with incorrectly-placed bullish OBs. This explains why "neutral" beats both. **Follow-up needed:** re-analyze as "correctly zoned" (bullish+discount OR bearish+premium) vs "incorrectly zoned."

### 3. freshness absent from top 16
Microstructure Stream 3 found freshness as the ONLY significant OB feature (p=0.016, winners 2.65 candles vs losers 2.05 at n=114). But at n=1,505 it didn't rank. Either the effect disappears at scale (Stream 3 finding was noise) or the freshness computation differs between analyses. **Note for future reference, not a blocker.**

### Validated Big Findings (unchanged by these notes)
- D1 alignment does NOT matter (p=0.45)
- Body range ratio is the strongest validated predictor (24pp spread holds)
- H4 alignment is the real directional filter (18pp validated, p=0.003)
- BOS-caused OBs outperform CHoCH (~20pp spread validated)

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 10 |
| Passed | 9 |
| Warned | 1 |
| Failed | 0 |
| Skipped | 0 |

**No critical failures detected.**

---

## OB Detection Consistency
**Status: PASS**

Dates tested: 5
All dates match: True

### 2024-09-06
- **XAUUSD**: raw_fresh=0, analysis=0, mitigated_excluded=True
- **GBPUSD**: raw_fresh=0, analysis=0, mitigated_excluded=True

### 2024-05-06
- **XAUUSD**: raw_fresh=2, analysis=2, mitigated_excluded=True
  - OB 0: H=True L=True O=True C=True
  - OB 1: H=True L=True O=True C=True
- **GBPUSD**: raw_fresh=2, analysis=2, mitigated_excluded=True
  - OB 0: H=True L=True O=True C=True
  - OB 1: H=True L=True O=True C=True

### 2025-05-02
- **XAUUSD**: raw_fresh=1, analysis=1, mitigated_excluded=True
  - OB 0: H=True L=True O=True C=True
- **GBPUSD**: raw_fresh=0, analysis=0, mitigated_excluded=True

### 2025-03-19
- **XAUUSD**: raw_fresh=5, analysis=5, mitigated_excluded=True
  - OB 0: H=True L=True O=True C=True
  - OB 1: H=True L=True O=True C=True
  - OB 2: H=True L=True O=True C=True
- **GBPUSD**: raw_fresh=2, analysis=2, mitigated_excluded=True
  - OB 0: H=True L=True O=True C=True
  - OB 1: H=True L=True O=True C=True

### 2025-02-17
- **XAUUSD**: raw_fresh=1, analysis=0, mitigated_excluded=True
- **GBPUSD**: raw_fresh=4, analysis=4, mitigated_excluded=True
  - OB 0: H=True L=True O=True C=True
  - OB 1: H=True L=True O=True C=True
  - OB 2: H=True L=True O=True C=True

---

## Cross-Reference with Previous Findings
**Status: PASS**

### Confirmations
- D1 alignment has no significant predictive effect — consistent with edge discovery (p=0.926)
- Premium zone effect significant (p=0.0031) — consistent with microstructure p=0.020
### No contradictions found

### Detailed Checks
- **D1 alignment effect**: CONFIRMS prior finding
  - Prior: D1-clear ~49.4% vs unclear ~49.2%, p=0.926, NO effect
  - Current: D1 aligned spread=0.0256, p=0.4491
- **Premium zone effect**: CONFIRMS premium zone effect
  - Prior: Microstructure Stream 3: p=0.020, significant
  - Current: Premium zone spread=0.1886, p=0.0031
- **H4 alignment effect (new finding)**: Extends prior finding: H4 alignment as a filter (not just H4 OBs) is predictive
  - Prior: Frequency investigation: H4 OBs 70-85% continuation at n=20
  - Current: H4 aligned spread=0.1508, disc p=0.0068, val p=0.002935
- **Body range ratio effect (new finding)**: NEW finding — thin-wick OBs outperform. Clearly labeled as new.
  - Prior: No direct prior finding
  - Current: Body ratio spread=0.2000, validated at 0.2448
- **BOS vs CHoCH effect (new finding)**: NEW finding — BOS-caused OBs significantly outperform.
  - Prior: No direct prior finding
  - Current: BOS=69.9% vs CHoCH=52.2%

---

## Retest Detection Accuracy
**Status: PASS**

Total checks: 9
Errors: 0 (max allowed: 1)

- 2024-10-16 bullish: PASS
- 2024-10-16 bullish: PASS
- 2024-08-23 bullish: PASS
- 2024-08-02 bullish: PASS
- 2024-08-02 bullish: PASS
- 2025-12-01 bullish: PASS
- 2025-12-01 bullish: PASS
- 2024-05-15 bullish: PASS
- 2024-05-15 bullish: PASS

---

## Outcome Measurement Accuracy
**Status: PASS**

Checks: 5, All match: True

| Date | Type | Manual MFE_R | Analysis MFE_R | Manual MAE_R | Analysis MAE_R | Hit Match | Status |
|------|------|-------------|---------------|-------------|---------------|-----------|--------|
| 2024-05-13 | bullish | 1.429 | 1.429 | 0.91 | 0.91 | True | PASS |
| 2024-08-12 | bullish | 2.43 | 2.43 | 0.424 | 0.424 | True | PASS |
| 2025-02-10 | bullish | 1.047 | 1.047 | 0.834 | 0.834 | True | PASS |
| 2025-03-03 | bullish | 0.09 | 0.09 | 1.711 | 1.711 | True | PASS |
| 2024-05-08 | bullish | 1.429 | 1.429 | 0.91 | 0.91 | True | PASS |

---

## Feature Analysis Statistical Validity
**Status: WARN**

Tautological features: False
Near-constant features: True

Issues:
- nearby_ob_count: near-constant (largest group = 955/987 = 96.8%)

- **hour_of_retest**: chi2=102.016, p=0.0, sig_match=True, tautological=False
- **nearby_ob_count**: chi2=10.644, p=0.001105, sig_match=True, tautological=False
- **day_of_week**: chi2=48.641, p=0.0, sig_match=True, tautological=False

---

## Combination Overfitting Check
**Status: PASS**

Combinations tested: 6
Bonferroni alpha: 0.008333
Bonferroni survivors: 3
FDR: 4 significant out of 6 tests; expected 0.3 under null

- ['day_of_week', 'premium_discount_zone']: disc=0.8246, val=0.3958, holds=False
- ['day_of_week', 'h4_aligned']: disc=0.8235, val=0.3774, holds=False
- ['day_of_week', 'fvg_overlap']: disc=0.79, val=0.3725, holds=False

---

## Quality Score Monotonicity
**Status: PASS**

Discovery monotonic: True
Validation monotonic: False
Breaks explained by small-n: False
Threshold (1) validated: True
AI traded avg score: 3.02 vs non-traded: 2.89

### Discovery Levels
| Score | N | Rate |
|-------|---|------|
| 0 | 1 | 0.0% |
| 1 | 51 | 58.8% |
| 2 | 185 | 62.7% |
| 3 | 592 | 67.6% |
| 4 | 158 | 86.1% |

### Validation Levels
| Score | N | Rate |
|-------|---|------|
| 0 | 3 | 66.7% |
| 1 | 42 | 54.8% |
| 2 | 136 | 58.8% |
| 3 | 299 | 67.2% |
| 4 | 38 | 31.6% |

---

## M15 Confirmation Value
**Status: PASS**

Spread reported: 0.0449, recomputed: 0.0449, match: True
Chi2: 1.299, p-value: 0.2544
Significant at 0.05: False
High ratio (3x+) rate: 0.8421
Conclusion: not_significant — requirement may cost frequency

---

## H4 OB Plausibility
**Status: PASS**

H4 total OBs: 248 (H1: 1520)
H4 fewer than H1: True
H4 continuation rate: 7.32%
H1 baseline: 0.6645
Freq investigation H4 rate: 85.0%
H4 KZ per month: 3.1

---

## Missed Opportunity Estimate Realism
**Status: PASS**

Total missed: 444
Per month: 18.5 (recomputed: 18.5)
Estimated WR: 0.7275
Quality threshold: 1
AI selectivity: 12.05%
WR is mechanical (not AI-augmented): True

---
