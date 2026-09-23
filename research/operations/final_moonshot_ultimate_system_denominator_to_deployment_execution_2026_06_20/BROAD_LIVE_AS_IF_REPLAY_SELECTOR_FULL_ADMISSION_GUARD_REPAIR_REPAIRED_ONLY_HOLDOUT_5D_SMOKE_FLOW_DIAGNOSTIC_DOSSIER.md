# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-25T04:08:52Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=43 win/loss/flat=18/25/0 net_r=-1.47512711 cash_pnl=-399.20349315 risk_cash=9496.12486166

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAGUSD: trades=5 net_r=-4.31343848 cash_pnl=-1082.47593777 w/l/f=0/5/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=3 net_r=-3.3376379 cash_pnl=-416.77568169 w/l/f=0/3/0
- repaired_package_conversion_v3 holdout AUDUSD: trades=1 net_r=-1.10116607 cash_pnl=-273.04123278 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout UKOIL_cash: trades=1 net_r=-1.0458 cash_pnl=-258.12181887 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GER40: trades=3 net_r=-0.39098669 cash_pnl=-105.76558325 w/l/f=1/2/0
- repaired_package_conversion_v3 holdout XAUUSD: trades=15 net_r=-0.23077228 cash_pnl=20.92320473 w/l/f=7/8/0
- repaired_package_conversion_v3 holdout GBPUSD: trades=1 net_r=-0.15372309 cash_pnl=-20.27769213 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout EURUSD: trades=1 net_r=0.37927287 cash_pnl=40.67855041 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDCHF: trades=1 net_r=0.81360006 cash_pnl=202.17680738 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout AUDJPY: trades=1 net_r=1.88696059 cash_pnl=211.73988596 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDCAD: trades=1 net_r=1.88790299 cash_pnl=465.05635451 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USOIL_cash: trades=1 net_r=1.953 cash_pnl=482.03472198 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
