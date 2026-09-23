# T2c Model Shootout: Sonnet 4.6 effort=high

**Date:** 2026-04-11
**Model:** claude-sonnet-4-6
**Effort:** high (USE_EFFORT=True)
**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)
**N MSOs:** 121
**Total cost:** $4.3378

---

## Results

| Metric | Sonnet 4 (baseline) | Sonnet 4.6 effort=high |
|--------|--------------------|---------------------------------|
| CANDIDATE rate | 42.1% | 17.4% (21/121) |
| WR (of CANDIDATEs) | 70.6% | 52.4% (n=21) |
| CR × WR | 0.2975 | 0.0909 |
| Avg confidence | 80.0 | 74.0 |
| Avg output tokens | ~500 | 1270 |
| Cost per call | ~$0.020 | $0.0358 |
| Projected monthly (17 trades) | ~$0.34 | $0.6094 |

---

## Agreement Analysis

| Category | N | WR |
|----------|---|-----|
| Both CANDIDATE | 12 | 58.3% |
| Sonnet 4.6 only (gained) | 9 | 44.4% |
| Sonnet 4 only (lost) | 39 | 74.4% |
| Neither | 61 | — |
| **Agreement rate** | **60.3%** | — |
| McNemar χ²=17.521 p=0.000028 | SIGNIFICANT (p<0.05) | — |

---

## Lost Trades Analysis

Sonnet 4.6 effort=high rejected **39** trades that Sonnet 4 accepted.
- WR of rejected trades: 74.4%
- Interpretation: **OVER-REJECTING good trades** (WR=74.4% > 65%) — Opus-like behavior detected.

> Rule of thumb:
> - WR > 65% → over-rejecting (Opus-like, bad)
> - WR < 50% → filtering correctly (good)
> - WR 50-65% → random noise (neutral)

## Key Finding

Effort=high on Sonnet 4.6 is **worse** than Sonnet 4 at no effort for this task:
- CANDIDATE rate collapsed from 100% → 17.4% (rejected 83% of previously-accepted trades)
- The 39 rejected trades had 74.4% WR — these were **good trades being filtered out**
- WR of kept CANDIDATEs: 52.4% — barely above random
- CR×WR: 0.0909 vs baseline 1.0 × 70.6% = 0.2975
- McNemar p=0.000028 — change is statistically significant

---

## Framework Distribution (Sonnet 4.6 CANDIDATEs)

ob_retest:21

---

## Grade Distribution

C:57, B:33, A:15, B+:10, A+:6

---

## Confidence Distribution (CANDIDATEs only)

70:3, 72:6, 75:9, 78:1, 80:2

---

## Token Usage

| Metric | Value |
|--------|-------|
| Avg input tokens | 5601 |
| Avg output tokens | 1270 |
| Avg cost per call | $0.03585 |
| Total cost | $4.3378 |
| Projected monthly (17 trades/month) | $0.6094 |

---

## Decision Breakdown

| Decision | N | % |
|----------|---|---|
| CANDIDATE | 21 | 17.4% |
| NO_TRADE  | 88  | 72.7% |
| Other (errors, WAIT, etc.) | 12 | 9.9% |

---

## Raw Decision Log

| trade_id | outcome | orig_decision | new_decision | conf | grade |
|----------|---------|---------------|--------------|------|-------|
| bt_2024-03-01_ny_001_gbpusd              | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2024-04-01_london_001_xauusd          | LOSS     | CANDIDATE    | WAIT         |   0 |    B+ |
| bt_2024-04-02_london_001_xauusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2024-04-03_ny_001_xauusd              | WIN      | CANDIDATE    | WAIT         |   0 |     B |
| bt_2024-04-08_ny_001_xauusd              | LOSS     | CANDIDATE    | CANDIDATE    |  75 |     A |
| bt_2024-04-18_ny_001_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |    B+ |
| bt_2024-05-28_ny_001_gbpusd              | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2024-06-05_ny_001_gbpusd              | LOSS     | CANDIDATE    | CANDIDATE    |  72 |     A |
| bt_2024-07-23_ny_001_xauusd              | WIN      | CANDIDATE    | WAIT         |   0 |     B |
| bt_2024-07-24_london_001_xauusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2024-07-24_ny_002_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |    B+ |
| bt_2024-08-29_london_001_xauusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2024-09-27_ny_001_xauusd              | LOSS     | CANDIDATE    | WAIT         |   0 |    B+ |
| bt_2024-10-03_ny_001_xauusd              | LOSS     | CANDIDATE    | CANDIDATE    |  75 |     A |
| bt_2025-01-21_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-01-28_london_001_xauusd          | WIN      | CANDIDATE    | WAIT         |   0 |     B |
| bt_2025-01-28_ny_002_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-01-29_ny_001_xauusd              | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-01-30_london_001_xauusd          | WIN      | CANDIDATE    | WAIT         |   0 |    B+ |
| bt_2025-02-04_ny_001_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |    B+ |
| bt_2025-02-07_ny_001_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-02-10_london_001_xauusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-02-12_london_001_xauusd          | LOSS     | CANDIDATE    | CANDIDATE    |  75 |    A+ |
| bt_2025-02-17_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-18_ny_001_xauusd              | WIN      | CANDIDATE    | CANDIDATE    |  75 |    A+ |
| bt_2025-02-18_london_001_gbpusd          | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-02-19_ny_001_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-20_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-21_london_001_xauusd          | WIN      | CANDIDATE    | CANDIDATE    |  75 |     A |
| bt_2025-02-21_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-24_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-24_ny_002_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-25_london_001_xauusd          | LOSS     | NO_TRADE     | WAIT         |   0 |     B |
| bt_2025-02-26_london_001_xauusd          | LOSS     | NO_TRADE     | WAIT         |   0 |     B |
| bt_2025-02-26_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-02-26_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |    B+ |
| bt_2025-03-04_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-03-04_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-03-04_ny_002_gbpusd              | WIN      | CANDIDATE    | WAIT         |   0 |     B |
| bt_2025-03-05_ny_001_xauusd              | LOSS     | NO_TRADE     | WAIT         |   0 |    B+ |
| bt_2025-03-05_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-03-07_london_001_gbpusd          | WIN      | CANDIDATE    | CANDIDATE    |  72 |     A |
| bt_2025-03-11_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-03-11_ny_002_gbpusd              | WIN      | CANDIDATE    | CANDIDATE    |  72 |     A |
| bt_2025-03-13_london_001_xauusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-03-13_ny_002_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-03-14_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-03-17_london_001_xauusd          | WIN      | NO_TRADE     | CANDIDATE    |  80 |    A+ |
| bt_2025-03-18_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-03-18_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-03-19_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |    B+ |
| bt_2025-03-21_london_001_xauusd          | LOSS     | NO_TRADE     | CANDIDATE    |  75 |     A |
| bt_2025-03-21_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-03-25_ny_001_xauusd              | WIN      | NO_TRADE     | WAIT         |   0 |    B+ |
| bt_2025-04-04_ny_001_xauusd              | WIN      | CANDIDATE    | CANDIDATE    |  80 |    A+ |
| bt_2025-04-17_ny_001_xauusd              | WIN      | CANDIDATE    | CANDIDATE    |  75 |    A+ |
| bt_2025-05-05_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |  28 |     C |
| bt_2025-05-06_ny_001_gbpusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-06-10_ny_001_xauusd              | WIN      | CANDIDATE    | CANDIDATE    |  70 |     A |
| bt_2025-06-11_london_001_gbpusd          | WIN      | NO_TRADE     | WAIT         |  42 |     C |
| bt_2025-06-11_ny_002_gbpusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-06-12_london_001_gbpusd          | LOSS     | NO_TRADE     | NO_TRADE     |  28 |     C |
| bt_2025-06-12_ny_002_gbpusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-06-16_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-06-23_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-06-25_london_001_xauusd          | LOSS     | CANDIDATE    | CANDIDATE    |  70 |     A |
| bt_2025-06-26_ny_001_xauusd              | LOSS     | NO_TRADE     | CANDIDATE    |  70 |     A |
| bt_2025-09-22_ny_001_xauusd              | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-09-23_ny_001_xauusd              | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     B |
| bt_2025-09-30_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |  22 |     C |
| bt_2025-10-03_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-10-07_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-10-09_london_001_xauusd          | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-10-09_ny_002_xauusd              | LOSS     | NO_TRADE     | CANDIDATE    |  72 |     A |
| bt_2025-10-20_ny_001_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-10-24_ny_001_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-12-01_ny_001_gbpusd              | LOSS     | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-12-10_ny_001_gbpusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-12-16_ny_001_xauusd              | WIN      | NO_TRADE     | CANDIDATE    |  75 |     A |
| bt_2025-12-17_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-12-17_ny_002_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-12-18_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-12-18_ny_002_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-12-19_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2025-12-22_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     B |
| bt_2025-12-22_london_001_gbpusd          | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2025-12-23_ny_001_xauusd              | LOSS     | NO_TRADE     | CANDIDATE    |  72 |     A |
| bt_2025-12-26_ny_001_xauusd              | WIN      | NO_TRADE     | CANDIDATE    |  75 |     A |
| bt_2025-12-30_ny_001_xauusd              | LOSS     | NO_TRADE     | CANDIDATE    |  72 |     A |
| bt_2026-01-05_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-06_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-06_ny_002_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-09_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-09_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-12_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-12_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-13_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-13_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-14_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-15_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-16_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-16_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-19_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-21_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-21_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-22_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-26_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-28_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-01-28_ny_002_xauusd              | WIN      | NO_TRADE     | CANDIDATE    |  78 |    A+ |
| bt_2026-01-29_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-02-03_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-02-03_ny_002_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-02-04_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-02-04_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-02-05_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-02-05_ny_002_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-03-06_ny_001_xauusd              | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-03-09_london_001_xauusd          | WIN      | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-03-10_ny_001_xauusd              | WIN      | CANDIDATE    | NO_TRADE     |   0 |     C |
| bt_2026-03-12_london_001_xauusd          | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
| bt_2026-03-13_ny_001_xauusd              | LOSS     | NO_TRADE     | NO_TRADE     |   0 |     C |
