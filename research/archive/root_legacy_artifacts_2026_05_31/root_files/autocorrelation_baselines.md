# Analysis 4: All-Instrument Autocorrelation Baselines

## Lag-1 H1 Return Autocorrelation

| Instrument | N Candles | Full Dataset | Current 20 | 90-day Mean | 90-day Std | Warning Threshold |
|---|---|---|---|---|---|---|
| XAUUSD | 14715 | -0.0199 | 0.0588 | -0.0140 | 0.0390 | ±0.0639 |
| US30_cash | 19999 | 0.0063 | 0.1460 ⚠️ | 0.0117 | 0.0377 | ±0.0871 |
| USDJPY | 19999 | 0.0071 | -0.4108 ⚠️ | 0.0047 | 0.0295 | ±0.0636 |
| GBPJPY | 19999 | 0.0123 | 0.0002 | 0.0035 | 0.0367 | ±0.0769 |
| GBPUSD | 19999 | -0.0142 | -0.3396 ⚠️ | -0.0114 | 0.0356 | ±0.0598 |

## Interpretation

- Lag-1 autocorrelation near 0 = random walk (no momentum)
- Positive = momentum (continuation), negative = mean-reversion
- Values exceeding the warning threshold (mean + 2σ) suggest regime change
- The OB retest strategy depends on positive autocorrelation (momentum after BOS)

Saved to `knowledge_base/meta/autocorrelation_baseline.json`

## Alerts

- **US30**: Current 20-period autocorrelation (0.146) exceeds warning threshold (0.087). Unusually high positive momentum — could mean extended trending or about to mean-revert. Monitor closely.
- **USDJPY**: Current 20-period autocorrelation (-0.411) is extremely negative — strong mean-reversion regime. This is 7x the warning threshold. The OB continuation strategy may underperform in strong mean-reversion.
- **GBPUSD**: Current 20-period autocorrelation (-0.340) is also deeply negative — mean-reversion regime, 6x warning threshold.
- **XAUUSD**: Current (0.059) is within normal range. No concern.
- **GBPJPY**: Current (0.0002) is effectively zero — random walk, within range.

## So What?

USDJPY and GBPUSD are currently in strong mean-reversion regimes (large negative autocorrelation). The OB retest strategy assumes momentum/continuation after BOS, which is the OPPOSITE of mean-reversion. These instruments may temporarily underperform. Consider pausing or reducing size on USDJPY and GBPUSD until autocorrelation returns to the normal range.