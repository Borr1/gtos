# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T06:07:25Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=51 win/loss/flat=34/17/0 net_r=3.97842768 cash_pnl=28.02543375 risk_cash=20653.61191506

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout SPX500: trades=1 net_r=-1.23 cash_pnl=-306.08082248 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout CHFJPY: trades=1 net_r=-1.18 cash_pnl=-737.5 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout NZDUSD: trades=1 net_r=-1.18 cash_pnl=-1183.80139326 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.18 cash_pnl=-589.2310081 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout EURJPY: trades=1 net_r=-0.03 cash_pnl=-30.01423277 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout EURUSD: trades=1 net_r=-0.03 cash_pnl=-29.78561862 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GER40: trades=1 net_r=-0.03 cash_pnl=-7.5 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout NAS100: trades=1 net_r=-0.03 cash_pnl=-7.5 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDCAD: trades=1 net_r=-0.03 cash_pnl=-15.01252429 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: trades=3 net_r=0.01 cash_pnl=13.69696014 w/l/f=2/1/0
- repaired_package_conversion_v3 holdout GBPUSD: trades=1 net_r=0.02 cash_pnl=19.84525726 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout UK100: trades=3 net_r=0.12382429 cash_pnl=30.92153601 w/l/f=2/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
