# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T06:03:46Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=167 win/loss/flat=142/25/0 net_r=12.05331506 cash_pnl=3547.37004806 risk_cash=66851.09933326

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAGUSD: trades=6 net_r=-1.80721028 cash_pnl=-791.06430593 w/l/f=4/2/0
- repaired_package_conversion_v3 holdout GER40: trades=11 net_r=-1.44967341 cash_pnl=-381.24529851 w/l/f=7/4/0
- repaired_package_conversion_v3 holdout GBPJPY: trades=10 net_r=-1.23993749 cash_pnl=-590.5690863 w/l/f=8/2/0
- repaired_package_conversion_v3 holdout NZDUSD: trades=2 net_r=-1.16 cash_pnl=-1160.65732789 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout CHFJPY: trades=3 net_r=-1.03174817 cash_pnl=-677.28432736 w/l/f=2/1/0
- repaired_package_conversion_v3 holdout UK100: trades=9 net_r=-0.53745607 cash_pnl=-130.03368885 w/l/f=7/2/0
- repaired_package_conversion_v3 holdout USDJPY: trades=7 net_r=-0.51336049 cash_pnl=-567.23924481 w/l/f=5/2/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=14 net_r=-0.25655 cash_pnl=-35.13658374 w/l/f=12/2/0
- repaired_package_conversion_v3 holdout UKOIL_cash: trades=1 net_r=0.02 cash_pnl=5.20007849 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDCAD: trades=1 net_r=0.02 cash_pnl=20.70797763 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout AUDUSD: trades=2 net_r=0.04 cash_pnl=22.74634069 w/l/f=2/0/0
- repaired_package_conversion_v3 holdout EURJPY: trades=2 net_r=0.04 cash_pnl=33.32451124 w/l/f=2/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
