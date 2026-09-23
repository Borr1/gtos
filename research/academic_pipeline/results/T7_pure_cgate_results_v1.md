# T7 Pure C-Gate Prompt Results

**Date:** 2026-04-13 02:32
**Model:** claude-sonnet-4-6, effort=max, max_tokens=1200
**Total MSOs:** 121
**Total cost:** $1.65

## Design

T7 removes ALL zone/proximity/RR content from the system prompt. The LLM receives:
- The full MSO user_message (which still contains OB data)
- A system prompt with ONLY: kill zones, C1/C2/C3 structural gates, decision rule
- An explicit instruction to IGNORE order block and FVG data for the decision

Post-hoc zone proximity is computed by Python after evaluations (LLM never sees it).

**Hypothesis:** Removing zone framing from the prompt will eliminate (or drastically
reduce) the 22 DIVs seen in T6, recovering them as CANDIDATEs.

## Summary Comparison

| Metric | T7 Pure C-Gate | T6 C-Gate | P2A v1 | Unfiltered | T6 sim fix |
|--------|----------------|-----------|--------|------------|------------|
| MSOs evaluated | 121 | 121 | 121 | 121 | 121 |
| CANDIDATEs | 104 | 81 | 46 | 121 | ~103 |
| CR | 86.0% | 66.9% | 38.0% | 100% | ~85% |
| WR | 66.3% | 66.7% | 69.6% | 64.5% | ~67% |
| CR×WR | 0.570 | 0.446 | 0.265 | 0.645 | ~0.57 |
| Total R | +39.5R | +33.8R | +22.9R | +40.6R | ~+41.2R |
| DIVs (bad NO_TRADEs) | 0 | 22 | N/A | — | 0 |
| Zone leaks | 0 | 22 | N/A | — | 0 |
| Parse errors | 1 | 0 | 21 | — | — |

## What Changed from T6

T6 finding: 22/40 NO_TRADEs were DIVs — LLM acknowledged C-gates pass but
rejected based on zone proximity despite 'informational only' label:
  > 'OB Retest framework requires price to be retesting an unmitigated order block'

T7 fix: Remove all zone discussion from prompt. System prompt contains:
  - NO zone, order block, proximity, distance, ATR, FVG, or RR in decision gates
  - ONE instruction: 'The MSO contains OB/FVG data. Ignore it for your decision.'
  - Decision is purely: H1 bias + M15 non-opposition

## Decision Integrity Analysis

**DIVs in T7: 0** (T6 had 22)

**Zero DIVs detected. T7 eliminated all decision integrity violations.**

**Zone leaks in reasoning: 0**

## C-Gate Failure Breakdown (NO_TRADEs)

Total NO_TRADEs: 16

- **C1 fail** (H1 unclear/no structure): n=3, WR=100.0%, R=+2.9R
- **C2 fail** (M15 actively opposing H1): n=13, WR=38.5%, R=-4.0R

## H1 Bias Distribution

- bullish: 115
- unclear: 3
- bearish: 2
- unknown: 1

## Post-Hoc Zone Proximity — CANDIDATEs

(Computed by Python from MSO text — LLM never saw this)

This analysis answers: does zone proximity at candle-close correlate with outcome?
If 'far' trades have high WR, it confirms proximity-at-close is NOT predictive.

| Proximity | n | WR | Total R | Interpretation |
|-----------|---|----|---------|----------------|
| inside | 21 | 61.9% | +13.3R | Price already at OB at close |
| approaching | 29 | 75.9% | +20.7R | Price within 2x M15 ATR of OB |
| far | 46 | 63.0% | +3.1R | Price >2x M15 ATR from OB |
| none | 8 | 62.5% | +2.4R | No relevant OB found in MSO |

**Expected finding:** 'far' group should have competitive WR (matches T5 finding:
Q2 proximity WAITs had 79.2% WR). Proximity at candle-close ≠ proximity at entry.
Real entries occur when price reaches the OB during the session, not at close.

## Temporal Split (CANDIDATEs)

- Pre-2026: 79 trades, WR=67.1%, R=+31.8R
- 2026:     25 trades, WR=64.0%, R=+7.7R

2026 WR decline observed in previous tests reflects known quarterly decay trend
(73.2% → 59.4% over 4 quarters, documented in CLAUDE.md validated numbers).

## Statistical Tests

- WR 95% CI: [57.3%, 75.4%] (n=104)
- WR vs 50% (random): z=3.53, p=0.0002 (one-tail)
- WR vs 64.5% (unfiltered): z=0.40, p=0.3452 (one-tail)

**Limitations:**
- n=121 in-sample. All results are post-hoc analysis of the training set.
- Bonferroni: T7 is test #7 in sequence. Threshold: p < 0.05/7 = 0.007.
- Live validation against new data is the only meaningful test.
- n=121 is underpowered to distinguish T7 WR from unfiltered WR (64.5%).

## Parse Errors

Count: 1

## Next Steps

**T7 is a deployment candidate.** Get CEO approval before deploying.

T7 would replace T6/P2A v1 as the live prompt. Evidence:
- CR×WR = 0.570 vs P2A v1 = 0.265 (115% improvement)
- Total R = +39.5R vs P2A v1 = +22.9R
- DIVs eliminated: fewer spurious rejections
