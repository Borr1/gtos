# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T06:11:46Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=86 win/loss/flat=76/10/0 net_r=4.93505168 cash_pnl=935.94646205 risk_cash=33206.90286428

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout GER40: trades=7 net_r=-1.6707667 cash_pnl=-423.84139744 w/l/f=5/2/0
- repaired_package_conversion_v3 holdout SPX500: trades=1 net_r=-1.23 cash_pnl=-306.08082248 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout CHFJPY: trades=1 net_r=-1.18 cash_pnl=-737.5 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout NZDUSD: trades=1 net_r=-1.18 cash_pnl=-1185.02809989 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.18 cash_pnl=-593.43078452 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout NAS100: trades=4 net_r=-0.92036393 cash_pnl=-229.63131466 w/l/f=3/1/0
- repaired_package_conversion_v3 holdout EURUSD: trades=1 net_r=0.02 cash_pnl=20.03652267 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout GBPUSD: trades=1 net_r=0.02 cash_pnl=19.91869533 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDCAD: trades=2 net_r=0.04 cash_pnl=32.80170532 w/l/f=2/0/0
- repaired_package_conversion_v3 holdout US30_cash: trades=7 net_r=0.07119544 cash_pnl=34.34166788 w/l/f=6/1/0
- repaired_package_conversion_v3 holdout USOIL_cash: trades=3 net_r=0.08212113 cash_pnl=20.51442146 w/l/f=3/0/0
- repaired_package_conversion_v3 holdout EURGBP: trades=1 net_r=0.59627493 cash_pnl=597.32632587 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
