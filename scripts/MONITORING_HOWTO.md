# Live Monitoring — How To

## Setup

```bash
pip install pandas numpy scipy
```

## Recording Trades

After every trade closes, record it:

```bash
python scripts/live_monitor.py trade --result WIN --instrument XAUUSD --r_multiple 1.8
python scripts/live_monitor.py trade --result LOSS --instrument US30 --r_multiple 1.0
python scripts/live_monitor.py trade --result WIN --instrument USDJPY --r_multiple 2.1 --direction LONG
```

- `--result`: WIN, LOSS, or BE (breakeven)
- `--instrument`: XAUUSD, US30, USDJPY, GBPJPY, GBPUSD
- `--r_multiple`: R-multiple of the trade (e.g. 1.8 for a 1.8R winner)
- `--direction`: LONG or SHORT (optional but recommended)

Trade data is stored in `knowledge_base/meta/monitoring_state.json`.

## SPRT — Is the System Working?

```bash
python scripts/live_monitor.py sprt
```

Shows per-instrument and portfolio SPRT status:
- **CONTINUE**: Not enough data yet to decide
- **CONFIRMED**: System validated at the batch-tested win rate (keep trading)
- **KILLED**: System rejected — stop trading this instrument

The decision table shows how many wins/losses you need in upcoming trades to reach a decision.

## CUSUM — Is Performance Deteriorating?

```bash
python scripts/live_monitor.py cusum
```

Tracks two signals per instrument:
- **Deterioration**: Accumulates when WR drops below batch expectations. Alert at 3.0.
- **Improvement**: Accumulates when WR exceeds expectations. Signals outperformance at 3.0.

## Autocorrelation — Is the Edge Still There?

```bash
python scripts/live_monitor.py autocorr
```

Reads H1 historical data and computes rolling 20-period lag-1 return autocorrelation. Warning if autocorrelation drops below 0.03 for 3 consecutive months (suggests the microstructure edge may be disappearing).

## Weekly Review

```bash
python scripts/live_monitor.py weekly
```

Combines everything into one summary:
- SPRT status table with Wilson confidence intervals
- Rolling 10-trade win rates
- CUSUM deterioration/improvement
- Trade frequency (this week + 4-week avg)
- Equity curve (cumulative R)
- Long vs Short breakdown
- JPY correlation exposure check

Copy-paste the output into your weekly review discussion.

## Data Storage

All state is in `knowledge_base/meta/monitoring_state.json`. Back it up periodically. The file is human-readable JSON.
