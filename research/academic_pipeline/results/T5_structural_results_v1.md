# T5 Structural-Only Prompt Results

**Date:** 2026-04-13 01:00
**Model:** claude-sonnet-4-6, effort=max
**Total MSOs:** 121
**Total cost:** $2.30

## Summary

| Metric | T5 Structural | P2A v1 Baseline | Unfiltered | Delta vs P2A |
|--------|---------------|-----------------|------------|-------------|
| MSOs evaluated | 121 | 121 | 121 | — |
| CANDIDATEs | 29 | 46 | 121 | -17 |
| CR | 24.0% | 38.0% | 100% | -14.0pp |
| WR | 62.1% | 69.6% | 64.5% | -7.5pp |
| CR×WR | 0.149 | 0.265 | 0.645 | -0.116 |
| Total R | +11.8R | +22.9R | +40.6R | -11.1R |
| Rejected WR | 63.4% | 60.6% | — | — |

## Key changes from P2A v1

1. C1: H1 is primary and sufficient (D1 optional, H4 removed)
2. C2: M15 not opposing (H4 reference removed)
3. Q1-Q7 scoring removed entirely (r=-0.06, p=0.574 — no signal)
4. Three binary checks replace scoring: zone exists + proximity + RR
5. M15 CHoCH no longer required for CANDIDATE
6. Proximity threshold relaxed to 2x ATR (was 1x)

## H1 Bias Distribution

- bullish: 95
- : 21
- bearish: 5

## Zone Distribution

- M15_OB: 21
- H1_OB: 8

## Temporal Split

- Pre-2026: 25 trades, WR=60.0%
- 2026: 4 trades, WR=75.0%

## Parse Errors

Count: 21
