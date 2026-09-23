# T2c Model Shootout: Sonnet 4.6 effort=max

**Date:** 2026-04-12
**Model:** claude-sonnet-4-6
**Effort:** max
**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)
**N MSOs:** 121
**Total cost:** $4.3183

## Results

| Metric | Sonnet 4 (baseline) | Sonnet 4.6 effort=max |
|--------|--------------------|---------------------------------|
| CANDIDATE rate | 100% (by construction) | 16.5% |
| WR (of CANDIDATEs) | 64.5% (n=121) | 60.0% (n=20) |
| CR × WR | 0.6446 | 0.0992 |
| Avg confidence | 36.1 | 75.7 |
| Avg output tokens | ~500 | 1259 |
| Cost per call | ~$0.02 | $0.0357 |

## Agreement Analysis

| Category | N | WR |
|----------|---|-----|
| Both CANDIDATE | 20 | 60.0% |
| Sonnet 4.6 rejects (lost trades) | 101 | 65.3% |

## Lost Trades Analysis

Sonnet 4.6 rejected 101 trades that Sonnet 4 accepted.
- WR of rejected trades: 65.3%
- **Verdict:** OVER-REJECTING: 65.3% WR on rejected trades > 65% — removing good trades (Opus-like behavior)
- McNemar's test p=0.000000 — statistically significant shift in CANDIDATE rate

## Framework Distribution (Sonnet 4.6 CANDIDATEs)

- none: 1
- ob_retest: 19

## Grade Distribution

- A: 15
- A+: 5
- B: 1
- B+: 13
- C: 87

## Confidence Distribution

- 70: 1
- 72: 3
- 75: 11
- 78: 1
- 80: 3
- 85: 1

## Token Usage

- Avg input tokens: 5600
- Avg output tokens: 1259
- Total cost: $4.3183
- Projected monthly cost at 17 trades/month: $0.61

## Raw Decision Log

| trade_id | outcome | original_decision | new_decision | new_confidence | new_grade |
|----------|---------|------------------|--------------|----------------|-----------|
| bt_2024-03-01_ny_001_gbpusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-04-01_london_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-04-02_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2024-04-03_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-04-08_ny_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | A |
| bt_2024-04-18_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2024-05-28_ny_001_gbpusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-06-05_ny_001_gbpusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-07-23_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2024-07-24_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-07-24_ny_002_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2024-08-29_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2024-09-27_ny_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2024-10-03_ny_001_xauusd | LOSS | CANDIDATE | CANDIDATE | 75 | A |
| bt_2025-01-21_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-01-28_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-01-28_ny_002_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-01-29_ny_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-01-30_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-02-04_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2025-02-07_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-02-10_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2025-02-12_london_001_xauusd | LOSS | CANDIDATE | CANDIDATE | 75 | A+ |
| bt_2025-02-17_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-18_ny_001_xauusd | WIN | CANDIDATE | CANDIDATE | 75 | A |
| bt_2025-02-18_london_001_gbpusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-02-19_ny_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-20_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-21_london_001_xauusd | WIN | CANDIDATE | CANDIDATE | 80 | A+ |
| bt_2025-02-21_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-24_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-24_ny_002_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-25_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | B+ |
| bt_2025-02-26_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-02-26_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | B |
| bt_2025-02-26_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2025-03-04_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-03-04_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-03-04_ny_002_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | B+ |
| bt_2025-03-05_ny_001_xauusd | LOSS | NO_TRADE | WAIT | 0 | B+ |
| bt_2025-03-05_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-03-07_london_001_gbpusd | WIN | CANDIDATE | CANDIDATE | 72 | A |
| bt_2025-03-11_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-03-11_ny_002_gbpusd | WIN | CANDIDATE | CANDIDATE | 75 | A |
| bt_2025-03-13_london_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-03-13_ny_002_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-03-14_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-03-17_london_001_xauusd | WIN | NO_TRADE | CANDIDATE | 80 | A+ |
| bt_2025-03-18_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-03-18_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-03-19_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | B+ |
| bt_2025-03-21_london_001_xauusd | LOSS | NO_TRADE | CANDIDATE | 75 | B+ |
| bt_2025-03-21_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-03-25_ny_001_xauusd | WIN | NO_TRADE | CANDIDATE | 75 | A |
| bt_2025-04-04_ny_001_xauusd | WIN | CANDIDATE | CANDIDATE | 85 | A+ |
| bt_2025-04-17_ny_001_xauusd | WIN | CANDIDATE | CANDIDATE | 75 | A |
| bt_2025-05-05_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 28 | C |
| bt_2025-05-06_ny_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-06-10_ny_001_xauusd | WIN | CANDIDATE | CANDIDATE | 75 | A |
| bt_2025-06-11_london_001_gbpusd | WIN | NO_TRADE | NO_TRADE | 22 | C |
| bt_2025-06-11_ny_002_gbpusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-06-12_london_001_gbpusd | LOSS | NO_TRADE | NO_TRADE | 22 | C |
| bt_2025-06-12_ny_002_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-06-16_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-06-23_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-06-25_london_001_xauusd | LOSS | CANDIDATE | CANDIDATE | 75 | A |
| bt_2025-06-26_ny_001_xauusd | LOSS | NO_TRADE | CANDIDATE | 70 | A |
| bt_2025-09-22_ny_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-09-23_ny_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-09-30_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 35 | C |
| bt_2025-10-03_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-10-07_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-10-09_london_001_xauusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-10-09_ny_002_xauusd | LOSS | NO_TRADE | CANDIDATE | 78 | A |
| bt_2025-10-20_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-10-24_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-12-01_ny_001_gbpusd | LOSS | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-12-10_ny_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-12-16_ny_001_xauusd | WIN | NO_TRADE | CANDIDATE | 80 | A+ |
| bt_2025-12-17_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-12-17_ny_002_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-12-18_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-12-18_ny_002_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-12-19_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-12-22_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2025-12-22_london_001_gbpusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2025-12-23_ny_001_xauusd | LOSS | NO_TRADE | CANDIDATE | 72 | A |
| bt_2025-12-26_ny_001_xauusd | WIN | NO_TRADE | CANDIDATE | 75 | A |
| bt_2025-12-30_ny_001_xauusd | LOSS | NO_TRADE | CANDIDATE | 75 | A |
| bt_2026-01-05_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-06_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-06_ny_002_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-09_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-09_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-12_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-12_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-13_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-13_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-14_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-15_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-16_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-16_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-19_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-21_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-21_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-22_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-26_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-28_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-01-28_ny_002_xauusd | WIN | NO_TRADE | CANDIDATE | 72 | A |
| bt_2026-01-29_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-02-03_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-02-03_ny_002_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-02-04_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-02-04_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-02-05_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-02-05_ny_002_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-03-06_ny_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-03-09_london_001_xauusd | WIN | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-03-10_ny_001_xauusd | WIN | CANDIDATE | NO_TRADE | 0 | C |
| bt_2026-03-12_london_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
| bt_2026-03-13_ny_001_xauusd | LOSS | NO_TRADE | NO_TRADE | 0 | C |
