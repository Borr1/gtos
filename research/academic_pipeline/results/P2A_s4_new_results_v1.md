# Phase 2A: P2A_s4_new

**Date:** 2026-04-12
**Model:** claude-sonnet-4-20250514
**Effort:** none
**Prompt:** Phase 2A re-engineered (scored evaluation, no self-check, quantified tolerances)
**N MSOs:** 121
**Total cost:** $2.9731
**max_tokens:** 2000

---

## Results

| Metric | Value |
|--------|-------|
| CANDIDATE rate | 12.4% (15/121) |
| WR (of CANDIDATEs) | 60.0% (n=15) |
| CR x WR | 0.0744 |
| Lost trades WR | 65.1% (n=106) |
| WAIT count | 0 |
| Avg output tokens | 700 |
| Total cost | $2.9731 |
| Projected monthly (17 trades/mo) | $0.4177 |

---

## Comparison to Baselines

| Config | CR | WR | CR*WR |
|--------|----|----|-------|
| Sonnet 4 batch (old prompts) | 55.8% | 61.1% | 0.341 |
| S4.6 medium (old prompts) | 13.2% | 50.0% | 0.066 |
| S4.6 high (old prompts) | 17.4% | 52.4% | 0.091 |
| S4.6 max (old prompts) | 16.5% | 60.0% | 0.099 |
| **P2A_s4_new (NEW prompt)** | **12.4%** | **60.0%** | **0.0744** |

---

## Lost Trades Analysis

New prompt rejected **106** trades that Sonnet 4 originally accepted (all 121 were original CANDIDATEs).
- WR of rejected trades: 65.1%
- Interpretation: **OVER-REJECTING good trades** (WR=65.1% > 65%) — prompt too conservative.

> Rule of thumb:
> - WR > 65% → over-rejecting (bad)
> - WR < 50% → filtering correctly (good)
> - WR 50-65% → random noise (neutral)

---

## Symbol Breakdown

| Symbol | N total | N CANDIDATE | CR | WR |
|--------|---------|-------------|----|----|
| GBPUSD | 21 | 4 | 19.0% | 50.0% |
| XAUUSD | 100 | 11 | 11.0% | 63.6% |

---

## Decision Breakdown

| Decision | N | % |
|----------|---|---|
| CANDIDATE | 15 | 12.4% |
| NO_TRADE  | 106  | 87.6% |
| WAIT      | 0      | 0.0% |
| Other (errors) | 0 | 0.0% |

---

## Grade Distribution

A: 15, C: 106

---

## Confidence Distribution (CANDIDATEs only)

78: 15

---

## Framework Distribution (CANDIDATEs only)

ob_retest: 13, breaker_retest: 2

---

## Score Computation Examples (first 5 CANDIDATEs)

- **bt_2024-04-18_ny_001_xauusd**: Q1=15 Q2=20 Q3=15 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 95 → conf 78
- **bt_2024-05-28_ny_001_gbpusd**: Q1=15 Q2=20 Q3=15 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 95 → conf 78
- **bt_2025-02-12_london_001_xauusd**: Q1=15 Q2=20 Q3=15 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 95 → conf 78
- **bt_2025-02-18_ny_001_xauusd**: Q1=15 Q2=20 Q3=15 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 95 → conf 78
- **bt_2025-03-11_london_001_gbpusd**: Q1=15 Q2=20 Q3=15 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 95 → conf 78

---

## Token Usage

| Metric | Value |
|--------|-------|
| Avg input tokens | 4692 |
| Avg output tokens | 700 |
| Avg cost per call | $0.02457 |
| Total cost | $2.9731 |
| Projected monthly (17 trades/month) | $0.4177 |

---

## Raw Decision Log

| trade_id | outcome | new_decision | conf | grade | framework |
|----------|---------|--------------|------|-------|-----------|
| bt_2024-03-01_ny_001_gbpusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2024-04-01_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2024-04-02_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2024-04-03_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2024-04-08_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2024-04-18_ny_001_xauusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2024-05-28_ny_001_gbpusd              | LOSS     | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2024-06-05_ny_001_gbpusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2024-07-23_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2024-07-24_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2024-07-24_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2024-08-29_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2024-09-27_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2024-10-03_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-01-21_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-01-28_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-01-28_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-01-29_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-01-30_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-04_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-07_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-10_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-12_london_001_xauusd          | LOSS     | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-02-17_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-18_ny_001_xauusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-02-18_london_001_gbpusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-19_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-20_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-21_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-21_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-24_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-24_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-25_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-26_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-26_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-02-26_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-04_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-04_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-04_ny_002_gbpusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-05_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-05_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-07_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-11_london_001_gbpusd          | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-03-11_ny_002_gbpusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-13_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-13_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-14_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-17_london_001_xauusd          | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-03-18_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-18_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-19_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-21_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-03-21_ny_002_xauusd              | LOSS     | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-03-25_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-04-04_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-04-17_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-05-05_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-05-06_ny_001_gbpusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-06-10_ny_001_xauusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-06-11_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-06-11_ny_002_gbpusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-06-12_london_001_gbpusd          | LOSS     | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-06-12_ny_002_gbpusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-06-16_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-06-23_ny_001_xauusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-06-25_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-06-26_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-09-22_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-09-23_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-09-30_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-10-03_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-10-07_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-10-09_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-10-09_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-10-20_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-10-24_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-01_ny_001_gbpusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-10_ny_001_gbpusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-16_ny_001_xauusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-12-17_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-17_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-18_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-18_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-19_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-22_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-22_london_001_gbpusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-23_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2025-12-26_ny_001_xauusd              | WIN      | CANDIDATE    |   78 |     A |       ob_retest |
| bt_2025-12-30_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-05_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-06_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-06_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-09_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-09_ny_002_xauusd              | LOSS     | CANDIDATE    |   78 |     A |  breaker_retest |
| bt_2026-01-12_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-12_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-13_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-13_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-14_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-15_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-16_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-16_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-19_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-21_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-21_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-22_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-26_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-28_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-28_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-01-29_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-02-03_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-02-03_ny_002_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-02-04_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-02-04_ny_002_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-02-05_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-02-05_ny_002_xauusd              | LOSS     | CANDIDATE    |   78 |     A |  breaker_retest |
| bt_2026-03-06_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-03-09_london_001_xauusd          | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-03-10_ny_001_xauusd              | WIN      | NO_TRADE     |    0 |     C |            none |
| bt_2026-03-12_london_001_xauusd          | LOSS     | NO_TRADE     |    0 |     C |            none |
| bt_2026-03-13_ny_001_xauusd              | LOSS     | NO_TRADE     |    0 |     C |            none |
