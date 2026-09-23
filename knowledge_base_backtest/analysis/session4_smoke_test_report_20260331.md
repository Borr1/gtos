# Session 4 Smoke Test Report
Generated: 2026-03-31
Batch: msgbatch_01VCZZM7cCZhW9Nb9MybySZq
Period: 2025-10-01 to 2025-10-31 (16 sessions)

## Results
- Total trades: 5 (London: 1, NY: 4)
- Wins: 5, Losses: 0, Win rate: 100%
- Total R: +5.29R, Expectancy: +1.06R/trade
- Cost: $3.27

## Trade Detail
| Trade ID | Framework | KZ | Outcome | R | MFE | MAE | Exit |
|----------|-----------|-----|---------|------|------|------|------|
| bt_2025-10-03_ny_001 | ob_retest | ny | WIN | +0.32R | 0.43R | 0.09R | timeout |
| bt_2025-10-09_london_001 | ob_retest | london | WIN | +0.81R | 1.34R | 0.00R | trail |
| bt_2025-10-09_ny_002 | ob_retest | ny | WIN | +0.24R | 0.80R | 0.29R | BE |
| bt_2025-10-20_ny_001 | ob_retest | ny | WIN | +1.23R | 2.77R | 0.00R | TP3 runner |
| bt_2025-10-24_ny_001 | ob_retest | ny | WIN | +2.69R | 3.92R | 0.00R | trail |

## Verification Checklist
- [x] All trades are ob_retest (zero session_sweep)
- [x] MFE present on all trades
- [x] MAE present on all trades
- [x] exit_substate present on all trades
- [x] Confidence scores: {80, 85} — rubric being applied (still narrow range)
- [x] London ob_retest working (1 trade)
- [x] NY ob_retest working (4 trades)
