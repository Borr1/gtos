# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-25T09:07:35Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=44 win/loss/flat=17/27/0 net_r=-2.64745336 cash_pnl=57.05105784 risk_cash=10412.30774992

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAGUSD: trades=9 net_r=-3.95501835 cash_pnl=-686.60262923 w/l/f=1/8/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=3 net_r=-3.3376379 cash_pnl=-425.2681133 w/l/f=0/3/0
- repaired_package_conversion_v3 holdout AUDUSD: trades=1 net_r=-1.10116607 cash_pnl=-279.01931345 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-262.20176877 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GER40: trades=3 net_r=-0.37307064 cash_pnl=-297.87319183 w/l/f=1/2/0
- repaired_package_conversion_v3 holdout GBPJPY: trades=1 net_r=0.03050277 cash_pnl=11.6498629 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout EURUSD: trades=1 net_r=0.37927287 cash_pnl=39.29171275 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDJPY: trades=9 net_r=2.17766089 cash_pnl=548.82437167 w/l/f=5/4/0
- repaired_package_conversion_v3 holdout XAUUSD: trades=16 net_r=4.57900307 cash_pnl=1408.2501271 w/l/f=8/8/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
