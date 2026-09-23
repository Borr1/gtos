# T8 C1+C3 Only Prompt Results

**Date:** 2026-04-13 02:32
**Model:** claude-sonnet-4-6, effort=max
**Test:** C1 (H1 bias) + C3 (direction match) only. C2 (M15 alignment) removed.
**Total MSOs:** 121
**Total cost:** $1.79

## Summary

| Metric | T8 (C1+C3) | T6 (C1+C2+C3) | P2A v1 | Unfiltered | T8 vs T6 | T8 vs P2A |
|--------|-----------|----------------|--------|------------|----------|----------|
| MSOs evaluated | 121 | 121 | 121 | 121 | — | — |
| CANDIDATEs | 115 | 81 | 46 | 121 | +34 | +69 |
| CR | 95.0% | 66.9% | 38.0% | 100% | +28.1pp | +57.0pp |
| WR | 65.2% | 66.7% | 69.6% | 64.5% | -1.5pp | -4.4pp |
| CR×WR | 0.620 | 0.446 | 0.265 | 0.645 | +0.174 | +0.355 |
| Total R | +40.8R | +33.8R | +22.9R | +40.6R | +7.0R | +17.9R |
| Exp/trade | +0.355R | +0.417R | +0.498R | +0.336R | — | — |
| NO_TRADE WR | 50.0% | 60.0% | 60.6% | — | — | — |

## What T8 Tests

T6 kept C2 (M15 must not actively oppose H1). In T6:
- 40 NO_TRADEs total: 17 had m15_status=opposing (C2 failures, WR=47.1%), 23 had m15_status=aligned but still NO_TRADE (C1/C3 failures)
- 35 of 40 NO_TRADEs had h1_direction=bullish — meaning C2 was the primary gate

T8 removes C2. Expected:
- CR > 85% (C2-rejected trades now accepted)
- If C2 adds value: WR drops below 66.7% (more bad trades accepted)
- If C2 is noise: WR stays near 66.7%, Total R > T6 due to more trades
- Definitive test: Fisher exact on m15_opposing vs m15_aligned WR

## M15 Opposition Analysis — Does C2 Add Value?

This is the primary T8 finding. Among T8 CANDIDATEs, was M15 opposition a predictor?

| Group | n | WR | 95% CI | Total R |
|-------|---|----|--------|--------|
| m15_opposing=True (C2 would reject) | 12 | 50.0% | [21.7%, 78.3%] | -0.5R |
| m15_opposing=False (C2 would pass) | 103 | 67.0% | [57.9%, 76.1%] | +41.3R |

**Fisher exact test:** OR=0.49, p=0.3369

**Verdict: NOT SIGNIFICANT** — M15 opposition does not reliably predict outcomes (p=0.3369). C2 adds noise more than signal. Recommend removing C2.

WR difference: -17.0% (opposing vs aligned). Direction is correct (opposing has lower WR), but effect too small to be reliable.

## NO_TRADE Breakdown

Total NO_TRADE: 6
- H1 unclear/mixed (C1 fail): 4, WR=75.0%
- C3 direction mismatch: 2, WR=0.0%

**Expected:** T8 should have very few NO_TRADEs. The only valid rejection is H1 bias truly unclear. If T8 still shows many NO_TRADEs, the LLM is adding implicit gates despite being told not to.

## H1 Bias Distribution

- bullish: 116
- unclear: 4
- bearish: 1

Expected: ~95%+ bullish (dataset is majority XAUUSD longs in a bull market period).

## Post-hoc Zone Proximity (Python-computed, NOT LLM-assessed)

Proximity computed from MSO text by parsing H1 Unmitigated OBs and comparing to candle close price. Uses 2× H1 ATR(14) as the 'approaching' threshold.

This is the definitive test of whether zone proximity predicts outcomes (without the LLM proximity-estimation error seen in T5).

| Proximity | n | WR | Total R | Notes |
|-----------|---|----|---------|-------|
| inside | 3 | 100.0% [100.0%, 100.0%] | +5.9R | Price at zone edge |
| approaching | 18 | 77.8% [58.6%, 97.0%] | +7.8R | Within 2× ATR |
| far | 77 | 61.0% [50.1%, 71.9%] | +23.3R | > 2× ATR from zone |
| none | 17 | 64.7% [42.0%, 87.4%] | +3.8R |  |

If 'far' WR < 'inside'/'approaching' WR: zone proximity matters and should be a gate.
If 'far' WR ≈ 'inside'/'approaching': T5's proximity rejections were wrong, confirming T6/T8.

## Temporal Split

- Pre-2026: 86 trades, WR=66.3%, R=+34.6R
- 2026: 29 trades, WR=62.1%, R=+6.2R

## Statistical Notes

- T8 WR 95% CI: [56.5%, 73.9%] (n=115)
- WR vs 50% (random): z=3.26, p=0.0005
- WR vs 64.5% (unfiltered): z=0.16, p=0.4361
- WR vs 66.7% (T6): z=-0.34, p=0.6321
- n=121 in-sample. All findings are post-hoc on the training set.
- Bonferroni: T8 is test #8. Corrected threshold α=0.05/8=0.006.
- Live validation is required before deploying any T-series findings.

## Parse Errors

Count: 0

## C2 Value Verdict

Based on T8 results:

**C2 adds no significant value.** Fisher p=0.3369.
T8 Total R (+40.8R) > T6 (+33.8R): removing C2 captures more trades without proportional WR loss. C1+C3 is the more permissive and productive filter.
