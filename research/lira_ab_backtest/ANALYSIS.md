# LIRA A/B 12-Slice Backtest — Analysis

**Analysis script SHA256:** `3d7a07e30eef41cf721e29969a1780e2d20fb883a9f9ba2849465f316ed58368`
**Generated:** 2026-04-25 00:23 UTC
**Pre-registered criteria:** see `PREREGISTRATION.md` — frozen before analysis ran.

## Data

12 slices executed with `--detector-version v2` + LIRA system prompt + DP4 schema_adapter.
- Fleet total cost: $32.70 (budget $80 hard cap)
- Fleet evaluations (API calls): 1173
- Fleet CANDs: 54 raw / 48 filled
- Fleet parse errors: 0 of 1173 = 0.0%

## Fleet-level — 3-way comparison (LIRA vs A2-V3 vs F3-V3)

All three runs use IDENTICAL 12 slices, IDENTICAL v2 detector, IDENTICAL fill logic.
Only difference: LIRA uses decision-first prompt + schema adapter.

| Metric | LIRA (this) | A2 V3 (v2 detector) | F3 V3 (v2 detector) |
|---|---:|---:|---:|
| Raw CAND | 54 | 37 | 588 |
| Filled | 48 | 30 | 32 |
| WR (filled) | 43.8% | 53.3% | 56.2% |
| Expectancy | +0.094R | +0.333R | +0.407R |
| Total R | +4.50R | +10.00R
| MaxDD | 9.00R | 3.00R
| Parse errors | 0 (0.0%) | unknown | unknown |

### LIRA confidence intervals (Wilson WR, bootstrap Exp)

- Fleet WR: 43.8% CI [30.7%, 57.7%]
- Fleet Exp R: +0.094R CI [-0.271R, +0.458R]
- Fleet LONG WR: 42.2% CI [29.0%, 56.7%]
- Fleet SHORT WR: 66.7% CI [20.8%, 93.9%]

## XAUUSD — 3-way comparison

| Metric | LIRA (this) | A2 V3 | F3 V3 |
|---|---:|---:|---:|
| Raw CAND | 15 | 13 | 162 |
| LONG raw share | 80.0% | 69.2% | — |
| SHORT raw share | 20.0% | 30.8% | 22.8% |
| Filled | 14 (L 12/S 2) | 11 | 13 |
| WR filled | 50.0% | 45.5% | — |
| Expectancy | +0.250R | +0.136R | +0.347R |
| Total R | +3.50R | +1.50R
| LONG WR | 41.7% | 33.3% | 45.5% |
| SHORT WR | 100.0% | 100.0% | 100.0% |
| MaxDD | 3.00R | 3.00R

## USDJPY — 3-way comparison

| Metric | LIRA (this) | A2 V3 | F3 V3 |
|---|---:|---:|---:|
| Raw CAND | 39 | 24 | 426 |
| LONG raw share | 97.4% | 100.0% | — |
| SHORT raw share | 2.6% | 0.0% | 0.0% |
| Filled | 34 (L 33/S 1) | 19 | 19 |
| WR filled | 41.2% | 57.9% | — |
| Expectancy | +0.029R | +0.447R | +0.447R |
| Total R | +1.00R | +8.50R
| LONG WR | 42.4% | 57.9% | 57.9% |
| SHORT WR | 0.0% | 0.0% | 0.0% |
| MaxDD | 6.00R | 3.00R

## Per-slice summary

| Slice | Raw | L/S | Filled | L/S | Wins | Total R | Parse | Cost |
|---|---:|---|---:|---|---:|---:|---:|---:|
| usdjpy_s1 | 8 | 8/0 | 8 | 8/0 | 4 | +2.00 | 0 | $6.02 |
| usdjpy_s2 | 9 | 8/1 | 9 | 8/1 | 5 | +3.50 | 0 | $5.64 |
| usdjpy_s3 | 13 | 13/0 | 8 | 8/0 | 3 | -0.50 | 0 | $6.00 |
| usdjpy_s4 | 9 | 9/0 | 9 | 9/0 | 2 | -4.00 | 0 | $6.01 |
| xauusd_s1 | 0 | 0/0 | 0 | 0/0 | 0 | +0.00 | 0 | $0.00 |
| xauusd_s2 | 1 | 1/0 | 1 | 1/0 | 0 | -1.00 | 0 | $1.02 |
| xauusd_s3 | 8 | 8/0 | 8 | 8/0 | 5 | +4.50 | 0 | $1.19 |
| xauusd_s4 | 0 | 0/0 | 0 | 0/0 | 0 | +0.00 | 0 | $0.19 |
| xauusd_s5 | 2 | 2/0 | 2 | 2/0 | 0 | -2.00 | 0 | $2.83 |
| xauusd_s6 | 0 | 0/0 | 0 | 0/0 | 0 | +0.00 | 0 | $1.32 |
| xauusd_s7 | 3 | 0/3 | 2 | 0/2 | 2 | +3.00 | 0 | $1.18 |
| xauusd_s8 | 1 | 1/0 | 1 | 1/0 | 0 | -1.00 | 0 | $1.30 |

## Pre-registered LIRA criteria check

| Criterion | Threshold | Observed | Status |
|---|---:|---:|---|
| LIRA fleet Exp R | >= +0.400R | +0.094R | FAIL |
| LIRA parse rate | <= 5.0% | 0.0% | PASS |
| LIRA XAUUSD SHORT WR | >= 40% if n>=3 | 100.0% (n=2) | PASS |
| LIRA fleet MaxDD | <= 8R | 9.00R | FAIL |

## STAY triggers check

- lira_fleet_exp_le_a2_baseline (+0.333R): TRIGGERED
- lira_parse_rate_gt_5pct: no
- in_halt_window (Exp R in (+0.333, +0.40)): no

## VERDICT: **LIRA-STAY**

LIRA-STAY: lira_fleet_exp_le_a2_baseline. DP4 surprise was data-thin / cherry-picked. V3 stays as production prompt; shelve LIRA or re-investigate the 3-slice DP4 result for missing context.