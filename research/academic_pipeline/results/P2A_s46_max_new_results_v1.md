# Phase 2A: P2A_s46_max_new

**Date:** 2026-04-12
**Model:** claude-sonnet-4-6
**Effort:** max (USE_EFFORT=True)
**Prompt:** Phase 2A re-engineered (scored evaluation, no self-check, quantified tolerances)
**N MSOs:** 121
**Total cost:** $4.2717
**max_tokens:** 2000

---

## Results

| Metric | Value |
|--------|-------|
| CANDIDATE rate | 38.0% (46/121) |
| WR (of CANDIDATEs) | 69.6% (n=46) |
| CR x WR | 0.2645 |
| Lost trades WR | 61.3% (n=75) |
| WAIT count | 14 |
| Avg confidence | 76.5 |
| Avg output tokens | 1419 |
| Total cost | $4.2717 |

---

## Comparison to T2c (old prompt)

| Config | CR | WR | CR*WR |
|--------|----|----|-------|
| Sonnet 4 batch (old prompts) | 55.8% | 61.1% | 0.341 |
| T2c S4.6 high (old prompt) | 17.4% | 52.4% | 0.091 |
| T2c S4.6 max (old prompt) | 16.5% | 60.0% | 0.099 |
| **P2A_s46_max_new (NEW prompt)** | **38.0%** | **69.6%** | **0.2645** |

---

## Lost Trades Analysis

New prompt rejected **75** trades that the original system accepted (all 121 were originally CANDIDATE).
- WR of rejected trades: 61.3%
- Interpretation: **Random rejection** (WR=61.3%, 50-65%) — no discriminatory signal.

> Rule of thumb:
> - WR > 65% → over-rejecting (bad)
> - WR < 50% → filtering correctly (good)
> - WR 50-65% → random noise (neutral)

---

## Decision Breakdown

| Decision | N | % |
|----------|---|---|
| CANDIDATE | 46 | 38.0% |
| NO_TRADE  | 61  | 50.4% |
| WAIT | 14 | 11.6% |
| Other (errors, etc.) | 0 | 0.0% |

---

## Grade Distribution

A:31, C:63, B:13, A+:10, B+:4

---

## Framework Distribution (CANDIDATEs)

ob_retest:44, breaker_retest:2

---

## Confidence Distribution (CANDIDATEs)

73:14, 78:31, 81:1

---

## Token Usage

| Metric | Value |
|--------|-------|
| Avg input tokens | 4674 |
| Avg output tokens | 1419 |
| Avg cost per call | $0.03530 |
| Total cost | $4.2717 |
| Projected monthly (17 trades/month) | $0.6002 |

---

## Raw Decision Log

| trade_id | outcome | new_decision | confidence | grade |
|----------|---------|--------------|------------|-------|
| bt_2024-03-01_ny_001_gbpusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2024-04-01_london_001_xauusd          | LOSS     | WAIT         |   0 |     C |
| bt_2024-04-02_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2024-04-03_ny_001_xauusd              | WIN      | WAIT         |   0 |     C |
| bt_2024-04-08_ny_001_xauusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2024-04-18_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2024-05-28_ny_001_gbpusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2024-06-05_ny_001_gbpusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2024-07-23_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     B |
| bt_2024-07-24_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2024-07-24_ny_002_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2024-08-29_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2024-09-27_ny_001_xauusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2024-10-03_ny_001_xauusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2025-01-21_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-01-28_london_001_xauusd          | WIN      | WAIT         |  52 |     B |
| bt_2025-01-28_ny_002_xauusd              | WIN      | WAIT         |  52 |     B |
| bt_2025-01-29_ny_001_xauusd              | LOSS     | WAIT         |   0 |     B |
| bt_2025-01-30_london_001_xauusd          | WIN      | CANDIDATE    |  73 |     A |
| bt_2025-02-04_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-02-07_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-02-10_london_001_xauusd          | WIN      | WAIT         |   0 |     C |
| bt_2025-02-12_london_001_xauusd          | LOSS     | CANDIDATE    |  78 |     A |
| bt_2025-02-17_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-02-18_london_001_gbpusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-02-18_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |    A+ |
| bt_2025-02-19_ny_001_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-02-20_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-02-21_london_001_xauusd          | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-02-21_ny_002_xauusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2025-02-24_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-02-24_ny_002_xauusd              | WIN      | CANDIDATE    |  73 |     A |
| bt_2025-02-25_london_001_xauusd          | LOSS     | WAIT         |  52 |     B |
| bt_2025-02-26_london_001_gbpusd          | WIN      | CANDIDATE    |  73 |    B+ |
| bt_2025-02-26_london_001_xauusd          | LOSS     | WAIT         |   0 |     B |
| bt_2025-02-26_ny_002_xauusd              | LOSS     | CANDIDATE    |  73 |    B+ |
| bt_2025-03-04_london_001_gbpusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-03-04_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-03-04_ny_002_gbpusd              | WIN      | WAIT         |  52 |     B |
| bt_2025-03-05_london_001_gbpusd          | WIN      | CANDIDATE    |  73 |     A |
| bt_2025-03-05_ny_001_xauusd              | LOSS     | WAIT         |  52 |     B |
| bt_2025-03-07_london_001_gbpusd          | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-03-11_london_001_gbpusd          | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-03-11_ny_002_gbpusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-03-13_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-03-13_ny_002_xauusd              | WIN      | WAIT         |   0 |     C |
| bt_2025-03-14_london_001_xauusd          | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-03-17_london_001_xauusd          | WIN      | CANDIDATE    |  81 |    A+ |
| bt_2025-03-18_london_001_gbpusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-03-18_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-03-19_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-03-21_london_001_xauusd          | LOSS     | CANDIDATE    |  78 |     A |
| bt_2025-03-21_ny_002_xauusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2025-03-25_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |    A+ |
| bt_2025-04-04_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |    A+ |
| bt_2025-04-17_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-05-05_london_001_xauusd          | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-05-06_ny_001_gbpusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-06-10_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-06-11_london_001_gbpusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-06-11_ny_002_gbpusd              | WIN      | CANDIDATE    |  78 |    A+ |
| bt_2025-06-12_london_001_gbpusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-06-12_ny_002_gbpusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-06-16_london_001_gbpusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-06-23_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |    A+ |
| bt_2025-06-25_london_001_xauusd          | LOSS     | CANDIDATE    |  73 |     A |
| bt_2025-06-26_ny_001_xauusd              | LOSS     | WAIT         |  52 |     B |
| bt_2025-09-22_ny_001_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-09-23_ny_001_xauusd              | LOSS     | CANDIDATE    |  78 |     A |
| bt_2025-09-30_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-10-03_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-10-07_ny_001_xauusd              | WIN      | CANDIDATE    |  73 |    A+ |
| bt_2025-10-09_london_001_xauusd          | LOSS     | CANDIDATE    |  73 |     A |
| bt_2025-10-09_ny_002_xauusd              | LOSS     | CANDIDATE    |  73 |    A+ |
| bt_2025-10-20_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |     B |
| bt_2025-10-24_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-12-01_ny_001_gbpusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-12-10_ny_001_gbpusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-12-16_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-12-17_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-12-17_ny_002_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-12-18_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-12-18_ny_002_xauusd              | WIN      | CANDIDATE    |  78 |     A |
| bt_2025-12-19_ny_001_xauusd              | WIN      | CANDIDATE    |  73 |     A |
| bt_2025-12-22_london_001_gbpusd          | WIN      | CANDIDATE    |  73 |     A |
| bt_2025-12-22_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2025-12-23_ny_001_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2025-12-26_ny_001_xauusd              | WIN      | CANDIDATE    |  78 |    A+ |
| bt_2025-12-30_ny_001_xauusd              | LOSS     | CANDIDATE    |  73 |    B+ |
| bt_2026-01-05_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-06_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-06_ny_002_xauusd              | WIN      | CANDIDATE    |  73 |     A |
| bt_2026-01-09_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-09_ny_002_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-12_london_001_xauusd          | WIN      | CANDIDATE    |  73 |    A+ |
| bt_2026-01-12_ny_002_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-13_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-13_ny_002_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-14_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-15_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-16_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-16_ny_002_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-19_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-21_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-01-21_ny_002_xauusd              | LOSS     | WAIT         |  55 |     B |
| bt_2026-01-22_london_001_xauusd          | WIN      | CANDIDATE    |  78 |     B |
| bt_2026-01-26_london_001_xauusd          | WIN      | CANDIDATE    |  78 |     A |
| bt_2026-01-28_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-28_ny_002_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-01-29_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-02-03_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-02-03_ny_002_xauusd              | WIN      | WAIT         |  52 |     B |
| bt_2026-02-04_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-02-04_ny_002_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-02-05_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-02-05_ny_002_xauusd              | LOSS     | NO_TRADE     |   0 |    B+ |
| bt_2026-03-06_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-03-09_london_001_xauusd          | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-03-10_ny_001_xauusd              | WIN      | NO_TRADE     |   0 |     C |
| bt_2026-03-12_london_001_xauusd          | LOSS     | NO_TRADE     |   0 |     C |
| bt_2026-03-13_ny_001_xauusd              | LOSS     | NO_TRADE     |   0 |     C |
