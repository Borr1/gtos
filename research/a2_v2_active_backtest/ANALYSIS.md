# A2 v2-Active Backtest — Analysis

**Analysis script SHA256:** `b06631e8b2dda6a420c50897818c4d6c29a1aa56869b7c5b34d159548373f13a`
**Generated:** 2026-04-24 19:12 UTC
**Pre-registered criteria:** see `PREREGISTRATION.md` — criteria frozen before analysis ran.

## Data

12 slices executed with `--detector-version v2` (NOT v2_shadow — true v2 active).
- Fleet total cost: $37.59 (budget $40)
- Fleet CANDs: 37 raw / 30 filled

## Fleet-level stats

| Metric | v2-active (A2) | v1-production (F3 baseline) | Delta |
|---|---:|---:|---:|
| Raw CAND | 37 | 588 | -551 |
| Filled | 30 | 32 | -2 |
| WR (filled) | 53.3% [CI 36.1%, 69.8%] | 56.2% | -2.9pp |
| Expectancy | +0.333R [CI -0.083R, +0.750R] | +0.407R | -0.074R |
| Total R | +10.00R | +13.00R | -3.00R |
| MaxDD | 3.00R | n/a | — |
| LONG WR | 50.0% [CI 32.6%, 67.4%] | — | — |
| SHORT WR | 100.0% [CI 34.2%, 100.0%] | — | — |

## XAUUSD detail

| Metric | v2-active (A2) | F3 v2 reference |
|---|---:|---:|
| Raw CAND | 13 | 162 |
| LONG raw share | 69.2% | — |
| SHORT raw share | 30.8% | 22.8% |
| Filled | 11 (L 9 / S 2) | 13 (L 11 / S 2) |
| WR filled | 45.5% [CI 21.3%, 72.0%] | — |
| Expectancy | +0.136R [CI -0.545R, +0.818R] | +0.347R |
| Total R | +1.50R | +4.50R |
| LONG WR | 33.3% [CI 12.1%, 64.6%] | 45.5% |
| SHORT WR | 100.0% [CI 34.2%, 100.0%] | 100.0% |
| MaxDD | 3.00R | 2.0R |

## USDJPY detail

| Metric | v2-active (A2) | F3 v2 reference |
|---|---:|---:|
| Raw CAND | 24 | 426 |
| LONG raw share | 100.0% | — |
| SHORT raw share | 0.0% | 0.0% |
| Filled | 19 (L 19 / S 0) | 19 (L - / S 0) |
| WR filled | 57.9% [CI 36.3%, 76.9%] | — |
| Expectancy | +0.447R [CI -0.079R, +0.974R] | +0.447R |
| Total R | +8.50R | +8.50R |
| LONG WR | 57.9% [CI 36.3%, 76.9%] | 57.9% |
| SHORT WR | 0.0% [CI 0.0%, 0.0%] | 0.0% |
| MaxDD | 3.00R | 3.0R |

## Per-slice summary

| Slice | Raw | L/S | Filled | L/S | Wins | Total R | Cost |
|---|---:|---|---:|---|---:|---:|---:|
| usdjpy_s1 | 6 | 6/0 | 6 | 6/0 | 3 | +1.50 | $6.03 |
| usdjpy_s2 | 6 | 6/0 | 6 | 6/0 | 5 | +6.50 | $6.04 |
| usdjpy_s3 | 7 | 7/0 | 2 | 2/0 | 1 | +0.50 | $6.04 |
| usdjpy_s4 | 5 | 5/0 | 5 | 5/0 | 2 | +0.00 | $6.00 |
| xauusd_s1 | 0 | 0/0 | 0 | 0/0 | 0 | +0.00 | $0.00 |
| xauusd_s2 | 1 | 1/0 | 1 | 1/0 | 0 | -1.00 | $1.50 |
| xauusd_s3 | 5 | 5/0 | 5 | 5/0 | 3 | +2.50 | $1.70 |
| xauusd_s4 | 0 | 0/0 | 0 | 0/0 | 0 | +0.00 | $0.29 |
| xauusd_s5 | 3 | 2/1 | 2 | 2/0 | 0 | -2.00 | $4.27 |
| xauusd_s6 | 0 | 0/0 | 0 | 0/0 | 0 | +0.00 | $2.00 |
| xauusd_s7 | 3 | 0/3 | 2 | 0/2 | 2 | +3.00 | $1.73 |
| xauusd_s8 | 1 | 1/0 | 1 | 1/0 | 0 | -1.00 | $1.99 |

## Pre-registered criteria check

| Criterion | Threshold | Observed | Status |
|---|---:|---:|---|
| Fleet Exp R | ≥ +0.150R | +0.333R | PASS |
| XAUUSD SHORT share | ≥ 15% | 30.8% | PASS |
| Fleet LONG WR | ≥ 55% | 50.0% | FAIL |
| Fleet MaxDD | ≤ 8R | 3.00R | PASS |

## STAY triggers check

- fleet_exp_neg: no
- fleet_long_wr_lt_45pct: no
- halt_window (LONG WR in [45%, 55%]): YES

## VERDICT: **HALT**

HALT / council: fleet_long_wr_ge_55pct. CEO review required before Monday detector decision.