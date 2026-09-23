# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T07:06:27Z

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
- repaired_package_conversion_v3 holdout: trades=40 win/loss/flat=35/5/0 net_r=1.00830024 cash_pnl=1055.31938025 risk_cash=18272.00683893

## Guard Blocks

- holdout clear: orders=20 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 holdout SPX500: trades=1 net_r=-1.14162891 cash_pnl=-288.26634306 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- raw_package_live_as_if holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-231.88376095 w/l/f=0/1/0
- raw_package_live_as_if holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-231.88376095 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-537.9416645 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout US30_cash: trades=3 net_r=-0.54434147 cash_pnl=-278.32931877 w/l/f=2/1/0
- repaired_package_conversion_v3 holdout GER40: trades=7 net_r=-0.38720903 cash_pnl=-99.6983912 w/l/f=6/1/0
- guarded_causal_admission_repair_v2 holdout AUDUSD: trades=1 net_r=-0.2560478 cash_pnl=-57.82461234 w/l/f=0/1/0
- raw_package_live_as_if holdout AUDUSD: trades=1 net_r=-0.2560478 cash_pnl=-57.82461234 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
