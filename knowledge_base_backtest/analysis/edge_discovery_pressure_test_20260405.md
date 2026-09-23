# Edge Discovery Pressure Test

**Test Date:** 2026-04-05
**Overall Result:** PASS
**Tests Passed:** 9/9 (Test 10 informational)

## Summary

| Test | Result | Details |
|---|---|---|
| Day Classification | PASS | Spot check 10/10, proportions within tolerance: True |
| Displacement Method | PASS |  |
| Criteria Adherence | PASS | 0 issues |
| Discovery/Val Split | PASS |  |
| Statistical Math | PASS | 0 recomputation issues |
| Overlap/Frequency | PASS | Correctly reports 0 additional trades |
| Cherry-Picking | PASS | All 6 hypotheses reported, ranking correct |
| Practical Viability | PASS |  |
| vs Existing Edge | PASS | Methodology mismatch flagged |

## Key Findings

### Test 1: Day Classification
- XAUUSD: 229/516 D1-clear (44.4%), expected ~39.9%
- GBPUSD: 259/581 D1-clear (44.6%), expected ~42.2%
- Spot check: 10/10
- Proportions consistent with strategic clarity investigation (within 5pp tolerance)

### Test 9: Methodology Mismatch (IMPORTANT)

| | Existing Edge | New Investigation |
|---|---|---|
| Metric | Simulated trade (TP 1.5R, SL, timeout) | 3h continuation (1.5x SL distance) |
| Gold WR | 61.1% | H1 best: 53.7% |
| Comparison | Direct comparison is **INVALID** | Different measurement methodologies |

Since all hypotheses failed even with the simpler metric, the conclusion holds.

### Test 10: Missing Checks

- **[MEDIUM]** Day-of-week effects: Thursday toxic for gold at 1.0R TP. No DOW filtering in hypotheses.
- **[LOW]** Seasonality analysis: Monthly distributions provided but no explicit seasonality test. March/December concentration unchecked.
- **[MEDIUM]** News/event contamination: No NFP/FOMC/CPI filter. Sweep signals during high-impact events aren't structural.
- **[LOW]** Spread and slippage: Sweep entries may have wide spreads. Not accounted for. Less critical since no edges passed.
- **[MEDIUM]** AI detectability from JSON: Mechanical rules are implementable in code. Good design choice.
- **[COVERED]** Maximum consecutive losses: Reported for top hypotheses in detailed analysis.

## Overall Assessment

The edge discovery investigation is **methodologically sound**:

1. Day classification consistent with previous work (~40-44% D1-clear rate)
2. All 6 hypotheses reported including failures — no cherry-picking
3. Bonferroni correction properly applied, Wilson CIs used
4. Clean discovery/validation split — no data leakage
5. The null result (no actionable edge on D1-unclear days) is well-supported

The D1 pre-screen is **not leaving easy money on the table**.

### Forward Recommendations

1. Pre-register H1 NY sweeps (57.4%, p=0.021) for Apr-Jun 2026 forward test
2. Collect more H4 OB Retest CAT1 data (34 signals inconclusive, not negative)
3. Document H2 FVG Fill anti-pattern (38-42% = negative edge)
4. Consider running top hypotheses through actual trade simulator as robustness check