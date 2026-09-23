# Correlation-Aware Position Sizing — Design Doc

## What
Before placing a trade on instrument B, check if instrument A already
has an open position. If A and B are correlated (>0.60), reduce
position size to keep total portfolio heat within limits.

## Rules
1. Max portfolio heat: 3% of account (e.g., 3 simultaneous 1% trades)
2. If a new trade's instrument correlates >0.60 with an open position:
   - Reduce new trade size by 50% (0.5% instead of 1%)
   - OR skip if portfolio heat would exceed 3%
3. Negative correlation (-0.40 to -1.0) is fine — it's natural hedging

## Correlation pairs to hard-code (from screening):
- EURUSD <-> GBPUSD: 0.64 -> shared budget
- AUDUSD <-> NZDUSD: 0.83 -> shared budget
- US30 <-> US500: 0.94 -> pick one
- XAUUSD <-> XAGUSD: 0.77 -> pick one
- EURJPY <-> GBPJPY: 0.74 -> shared budget

## Currently deployed instruments and their correlations:
- XAUUSD <-> USDJPY: -0.42 (negative — GOOD, natural hedge)
- XAUUSD <-> GBPUSD: 0.28 (low — GOOD, independent)
- XAUUSD <-> US30: 0.10 (near-zero — GOOD, independent)
- USDJPY <-> GBPUSD: -0.29 (negative — GOOD)
- USDJPY <-> US30: -0.05 (near-zero — GOOD)
- GBPUSD <-> US30: 0.01 (near-zero — GOOD)
- All four can trade simultaneously at full size

## Implementation
In orchestrator.py, before calling safe_place_order():
1. Get list of currently open positions
2. For each open position, check correlation with the new trade's instrument
3. If any correlation > 0.60: reduce size or skip
4. Log the sizing decision

## Estimated effort: 2-3 hours
## Risk: Medium — touches the execution path, needs careful testing
