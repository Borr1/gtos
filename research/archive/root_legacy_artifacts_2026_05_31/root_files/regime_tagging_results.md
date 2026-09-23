# Regime Tagging Feasibility — XAUUSD Backtest

**Generated:** 2026-04-05 08:09

## Data Summary

- **D1 candles:** 772 (2023-04-03 to 2026-03-30)
- **XAUUSD trade dates:** 129
- **Identification method:** entry_price > 1500 (batch) + all session trades (XAUUSD-only era)

## Regime Definitions

| Regime | Definition |
|--------|------------|
| TRENDING | 3+ consecutive HH/HL (up) or LH/LL (down) on D1 swing pivots |
| VOLATILE | D1 ATR(14) > 1.5x its 20-period SMA |
| RANGING  | Everything else |

*Note: VOLATILE takes precedence over TRENDING when both conditions are met.*

## D1 Regime Distribution

| Regime | Bars | % |
|--------|------|---|
| TRENDING | 170 | 22.0% |
| VOLATILE | 29 | 3.8% |
| RANGING | 573 | 74.2% |

## Win Rate by Regime

| Regime | Trades | Wins | Losses | BE | Win Rate | Total R | Avg R/Trade | Avg Winner | Avg Loser |
|--------|--------|------|--------|----|----------|---------|-------------|------------|----------|
| TRENDING | 23 | 12 | 11 | 0 | 52.2% | +0.34R | +0.015R | +0.945R | -1.000R |
| VOLATILE | 8 | 5 | 3 | 0 | 62.5% | +3.41R | +0.426R | +1.156R | -0.790R |
| RANGING | 98 | 64 | 32 | 2 | 65.3% | +55.77R | +0.569R | +1.274R | -0.803R |

**Overall:** 129 trades, +59.52R total

## Trade-by-Trade Detail

| Date | Regime | Outcome | R-Multiple |
|------|--------|---------|------------|
| 2024-06-05 | TRENDING | LOSS | -1.00R |
| 2024-07-11 | TRENDING | WIN | +2.92R |
| 2024-07-23 | TRENDING | WIN | +1.87R |
| 2024-09-27 | TRENDING | LOSS | -1.00R |
| 2025-01-06 | TRENDING | LOSS | -1.00R |
| 2025-01-09 | TRENDING | WIN | +0.42R |
| 2025-02-07 | TRENDING | WIN | +0.15R |
| 2025-02-10 | TRENDING | WIN | +0.52R |
| 2025-02-12 | TRENDING | LOSS | -1.00R |
| 2025-09-22 | TRENDING | LOSS | -1.00R |
| 2025-09-23 | TRENDING | WIN | +0.56R |
| 2025-09-30 | TRENDING | LOSS | -1.00R |
| 2025-10-02 | TRENDING | LOSS | -1.00R |
| 2025-10-03 | TRENDING | WIN | +1.07R |
| 2025-10-07 | TRENDING | WIN | +0.13R |
| 2025-10-09 | TRENDING | LOSS | -1.00R |
| 2025-10-14 | TRENDING | WIN | +1.81R |
| 2025-10-15 | TRENDING | LOSS | -1.00R |
| 2025-10-16 | TRENDING | WIN | +0.75R |
| 2025-10-17 | TRENDING | WIN | +0.39R |
| 2025-12-01 | TRENDING | WIN | +0.75R |
| 2025-12-29 | TRENDING | LOSS | -1.00R |
| 2026-03-20 | TRENDING | LOSS | -1.00R |
| 2025-04-17 | VOLATILE | WIN | +3.47R |
| 2025-10-20 | VOLATILE | WIN | +1.26R |
| 2025-10-24 | VOLATILE | WIN | +0.35R |
| 2026-01-29 | VOLATILE | LOSS | -1.00R |
| 2026-02-03 | VOLATILE | WIN | +0.50R |
| 2026-02-04 | VOLATILE | LOSS | -1.00R |
| 2026-02-05 | VOLATILE | WIN | +0.20R |
| 2026-02-10 | VOLATILE | LOSS | -0.37R |
| 2024-01-25 | RANGING | WIN | +0.75R |
| 2024-01-31 | RANGING | WIN | +0.75R |
| 2024-02-06 | RANGING | WIN | +2.38R |
| 2024-03-01 | RANGING | LOSS | -1.00R |
| 2024-03-13 | RANGING | LOSS | -0.10R |
| 2024-03-15 | RANGING | LOSS | -1.00R |
| 2024-03-18 | RANGING | LOSS | -1.00R |
| 2024-04-01 | RANGING | LOSS | -0.12R |
| 2024-04-02 | RANGING | WIN | +1.89R |
| 2024-04-03 | RANGING | WIN | +0.05R |
| 2024-04-24 | RANGING | WIN | +0.75R |
| 2024-04-25 | RANGING | WIN | +0.06R |
| 2024-05-24 | RANGING | WIN | +1.90R |
| 2024-05-28 | RANGING | LOSS | -0.74R |
| 2024-05-31 | RANGING | WIN | +0.06R |
| 2024-06-26 | RANGING | WIN | +0.92R |
| 2024-07-24 | RANGING | WIN | +0.15R |
| 2024-07-30 | RANGING | WIN | +1.13R |
| 2024-07-31 | RANGING | WIN | +1.39R |
| 2024-08-07 | RANGING | WIN | +0.75R |
| 2024-08-29 | RANGING | WIN | +0.16R |
| 2024-09-03 | RANGING | WIN | +0.82R |
| 2024-09-06 | RANGING | LOSS | -1.00R |
| 2024-09-11 | RANGING | LOSS | -0.34R |
| 2024-10-04 | RANGING | LOSS | -1.00R |
| 2024-12-09 | RANGING | WIN | +0.14R |
| 2024-12-12 | RANGING | LOSS | -1.00R |
| 2024-12-18 | RANGING | WIN | +3.56R |
| 2024-12-27 | RANGING | WIN | +1.05R |
| 2025-01-28 | RANGING | WIN | +0.97R |
| 2025-01-29 | RANGING | LOSS | -0.09R |
| 2025-01-30 | RANGING | WIN | +3.77R |
| 2025-02-04 | RANGING | WIN | +0.57R |
| 2025-02-18 | RANGING | LOSS | -0.22R |
| 2025-02-25 | RANGING | WIN | +0.29R |
| 2025-02-26 | RANGING | WIN | +1.18R |
| 2025-03-04 | RANGING | WIN | +2.34R |
| 2025-03-05 | RANGING | WIN | +2.62R |
| 2025-03-06 | RANGING | LOSS | -1.00R |
| 2025-03-07 | RANGING | WIN | +1.38R |
| 2025-03-11 | RANGING | WIN | +1.68R |
| 2025-03-14 | RANGING | LOSS | -1.00R |
| 2025-03-18 | RANGING | WIN | +0.33R |
| 2025-03-24 | RANGING | WIN | +0.75R |
| 2025-04-04 | RANGING | WIN | +0.51R |
| 2025-04-29 | RANGING | LOSS | -1.00R |
| 2025-05-05 | RANGING | WIN | +2.13R |
| 2025-05-06 | RANGING | WIN | +1.69R |
| 2025-06-10 | RANGING | WIN | +1.25R |
| 2025-06-11 | RANGING | WIN | +1.59R |
| 2025-06-12 | RANGING | WIN | +0.17R |
| 2025-06-16 | RANGING | WIN | +1.16R |
| 2025-06-25 | RANGING | WIN | +0.62R |
| 2025-06-26 | RANGING | LOSS | -1.00R |
| 2025-07-14 | RANGING | WIN | +0.75R |
| 2025-08-07 | RANGING | WIN | +0.44R |
| 2025-08-28 | RANGING | WIN | +2.48R |
| 2025-10-30 | RANGING | WIN | +0.75R |
| 2025-11-03 | RANGING | WIN | +0.75R |
| 2025-11-10 | RANGING | LOSS | -1.00R |
| 2025-12-03 | RANGING | WIN | +4.14R |
| 2025-12-04 | RANGING | LOSS | -1.00R |
| 2025-12-09 | RANGING | LOSS | -1.00R |
| 2025-12-10 | RANGING | WIN | +2.90R |
| 2025-12-11 | RANGING | WIN | +2.58R |
| 2025-12-12 | RANGING | LOSS | -1.00R |
| 2025-12-15 | RANGING | LOSS | -1.00R |
| 2025-12-16 | RANGING | WIN | +1.68R |
| 2025-12-17 | RANGING | WIN | +0.75R |
| 2025-12-18 | RANGING | LOSS | -1.00R |
| 2025-12-19 | RANGING | WIN | +1.91R |
| 2025-12-22 | RANGING | WIN | +0.67R |
| 2025-12-23 | RANGING | WIN | +0.75R |
| 2025-12-26 | RANGING | BREAKEVEN | -0.02R |
| 2025-12-31 | RANGING | WIN | +0.52R |
| 2026-01-02 | RANGING | LOSS | -1.00R |
| 2026-01-05 | RANGING | WIN | +2.24R |
| 2026-01-06 | RANGING | WIN | +2.42R |
| 2026-01-07 | RANGING | LOSS | -1.00R |
| 2026-01-08 | RANGING | WIN | +2.67R |
| 2026-01-15 | RANGING | WIN | +0.23R |
| 2026-01-16 | RANGING | LOSS | -1.00R |
| 2026-01-19 | RANGING | WIN | +0.55R |
| 2026-01-21 | RANGING | LOSS | -0.26R |
| 2026-01-22 | RANGING | WIN | +1.45R |
| 2026-01-26 | RANGING | WIN | +1.16R |
| 2026-01-28 | RANGING | LOSS | -1.00R |
| 2026-02-18 | RANGING | WIN | +0.81R |
| 2026-02-23 | RANGING | WIN | +0.75R |
| 2026-02-24 | RANGING | BREAKEVEN | -0.03R |
| 2026-02-25 | RANGING | WIN | +1.25R |
| 2026-03-05 | RANGING | LOSS | -1.00R |
| 2026-03-06 | RANGING | WIN | +3.03R |
| 2026-03-09 | RANGING | WIN | +0.23R |
| 2026-03-10 | RANGING | LOSS | -0.69R |
| 2026-03-12 | RANGING | LOSS | -1.00R |
| 2026-03-13 | RANGING | LOSS | -1.00R |
| 2026-03-16 | RANGING | LOSS | -0.14R |

## Key Takeaways

- **Highest win rate:** RANGING at 65.3% (98 trades)
- **Lowest win rate:** TRENDING at 52.2% (23 trades)
- **Best expectancy:** RANGING at +0.569R per trade

## Feasibility Assessment

Regime tagging is **FEASIBLE** with the available data:

1. XAUUSD_D1.csv has sufficient OHLC history (772 bars from 2023-04-03)
2. Swing detection and ATR computation work cleanly on this data
3. 129 trade dates were successfully matched to D1 regime tags

### Next Steps

- Use regime tags as a filter: skip or reduce size in underperforming regimes
- Consider adding regime as a feature in the pre-session analysis pipeline
- Test different ATR multiplier thresholds (current: 1.5x) and swing lookbacks
- If extending to other instruments, compute separate D1 regime per symbol
