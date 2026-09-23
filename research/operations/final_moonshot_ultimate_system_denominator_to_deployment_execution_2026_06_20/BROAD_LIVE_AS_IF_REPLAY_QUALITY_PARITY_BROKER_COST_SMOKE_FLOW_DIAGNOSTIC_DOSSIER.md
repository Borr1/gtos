# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T09:14:19Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -1.07398201 across 9 trades.
- Holdout guarded net R: -1.07398201 across 9 trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=9 win/loss/flat=3/6/0 net_r=-1.07398201 cash_pnl=-84.8674056 risk_cash=2973.94649108
- raw_package_live_as_if holdout: trades=9 win/loss/flat=3/6/0 net_r=-1.07398201 cash_pnl=-84.8674056 risk_cash=2973.94649108
- repaired_package_conversion_v3 holdout: trades=17 win/loss/flat=7/10/0 net_r=1.31627413 cash_pnl=-684.1297177 risk_cash=7591.84734024

## Guard Blocks

- holdout clear: orders=20 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 holdout CHFJPY: trades=1 net_r=-1.17 cash_pnl=-1161.77610371 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout UK100: trades=1 net_r=-1.17 cash_pnl=-292.5 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout SPX500: trades=1 net_r=-1.14162891 cash_pnl=-286.53830955 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- raw_package_live_as_if holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-688.04406719 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-231.88376095 w/l/f=0/1/0
- raw_package_live_as_if holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-231.88376095 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-531.73624358 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout US30_cash: trades=1 net_r=-0.34486515 cash_pnl=-172.432575 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
