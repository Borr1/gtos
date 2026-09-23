# T6 C-Gate Only Prompt Results

**Date:** 2026-04-13 01:43
**Model:** claude-sonnet-4-6, effort=max
**Total MSOs:** 121
**Total cost:** $2.07

## Summary

| Metric | T6 C-Gate | T5 C-Gate (sim) | P2A v1 | Unfiltered | Delta vs P2A |
|--------|-----------|-----------------|--------|------------|--------------|
| MSOs evaluated | 121 | 85 | 121 | 121 | — |
| CANDIDATEs | 81 | ~85 | 46 | 121 | +35 |
| CR | 66.9% | ~70.2% | 38.0% | 100% | +28.9pp |
| WR | 66.7% | ~69.4% | 69.6% | 64.5% | -2.9pp |
| CR×WR | 0.446 | ~0.487 | 0.265 | 0.645 | +0.181 |
| Total R | +33.8R | ~+44.2R | +22.9R | +40.6R | +10.9R |
| NO_TRADE WR | 60.0% | ~52.8% | 60.6% | — | — |

## What Changed from T5

T5 finding: Q-checks (proximity, RR) filter OUT the best trades:
- WAIT Q2 proximity fail: n=24, WR=79.2% — best group in dataset
- WAIT Q3 RR fail: n=9, WR=55.6%
- CANDIDATE (C+Q pass): n=29, WR=62.1% — WORST group

T6 fix: decision = C1+C2+C3 only. Zone/proximity/RR are logged as informational.

## C-Gate Failure Analysis

NO_TRADE total: 40
- C2 failures (M15 actively opposing): 33, WR=57.6%
- C1 failures (H1 bias unclear): 7, WR=71.4%

## H1 Bias Distribution

- bullish: 116
- bearish: 3
- unclear: 2

## Informational: Zone Proximity in CANDIDATEs

(Logged only — did NOT affect CANDIDATE/NO_TRADE decision)

- inside: n=36, WR=69.4%
- approaching: n=29, WR=62.1%
- far: n=16, WR=68.8%

If Q2 proximity had been applied as a gate, any 'far' trades would have been rejected.
WR comparison between proximity groups shows whether proximity still predicts outcomes.

## Temporal Split

- Pre-2026: 68 trades, WR=67.6%, R=+28.6R
- 2026: 13 trades, WR=61.5%, R=+5.2R

## Parse Errors

Count: 0

## Statistical Notes

- WR 95% CI: [56.4%, 76.9%] (n=81)
- WR vs 50% (random): z=3.18, p=0.0007
- WR vs 64.5% (unfiltered): z=0.41, p=0.3396
- n=121 in-sample. No held-out set exists yet.
- All findings are in-sample. Live validation required before deployment.
