# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-29T21:06:10Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 train: trades=84 win/loss/flat=35/49/0 net_r=-5.34850595 cash_pnl=-538.81828159 risk_cash=8345.01147071

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 train UKOIL_cash: trades=8 net_r=-5.84154759 cash_pnl=-582.03750586 w/l/f=1/7/0
- repaired_package_conversion_v3 train USDCHF: trades=6 net_r=-4.63509478 cash_pnl=-461.26572215 w/l/f=1/5/0
- repaired_package_conversion_v3 train USDCAD: trades=4 net_r=-2.81304862 cash_pnl=-280.03957122 w/l/f=1/3/0
- repaired_package_conversion_v3 train EURGBP: trades=2 net_r=-2.02927154 cash_pnl=-201.68748608 w/l/f=0/2/0
- repaired_package_conversion_v3 train EURUSD: trades=7 net_r=-1.37117058 cash_pnl=-135.37736949 w/l/f=2/5/0
- repaired_package_conversion_v3 train XAUUSD: trades=10 net_r=-0.88981874 cash_pnl=-89.31751987 w/l/f=5/5/0
- repaired_package_conversion_v3 train AUDUSD: trades=5 net_r=-0.80507327 cash_pnl=-80.89310965 w/l/f=2/3/0
- repaired_package_conversion_v3 train AUDJPY: trades=4 net_r=-0.65282481 cash_pnl=-64.63565443 w/l/f=2/2/0
- repaired_package_conversion_v3 train GBPJPY: trades=7 net_r=-0.49634553 cash_pnl=-50.58573542 w/l/f=3/4/0
- repaired_package_conversion_v3 train XAGUSD: trades=7 net_r=-0.45914298 cash_pnl=-46.90989243 w/l/f=2/5/0
- repaired_package_conversion_v3 train GER40: trades=1 net_r=-0.3006553 cash_pnl=-29.73282915 w/l/f=0/1/0
- repaired_package_conversion_v3 train US30_cash: trades=2 net_r=0.76493604 cash_pnl=76.04710092 w/l/f=1/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
