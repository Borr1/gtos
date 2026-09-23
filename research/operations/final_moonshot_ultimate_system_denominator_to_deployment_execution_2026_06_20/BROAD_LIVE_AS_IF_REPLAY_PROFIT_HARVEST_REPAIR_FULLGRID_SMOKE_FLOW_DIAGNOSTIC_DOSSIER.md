# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-22T02:24:40Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: 0.0 across 0 trades.
- Development guarded net R: 0.0 across 0 trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 development: trades=8 win/loss/flat=5/3/0 net_r=-1.74207665 cash_pnl=-993.20422513 risk_cash=2910.39663742

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 development USDJPY: trades=1 net_r=-1.1041 cash_pnl=-691.14669184 w/l/f=0/1/0
- repaired_package_conversion_v3 development XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-243.76872843 w/l/f=0/1/0
- repaired_package_conversion_v3 development XAUUSD: trades=3 net_r=-0.37284652 cash_pnl=-256.08315809 w/l/f=2/1/0
- repaired_package_conversion_v3 development USOIL_cash: trades=1 net_r=0.22798576 cash_pnl=56.75937791 w/l/f=1/0/0
- repaired_package_conversion_v3 development UKOIL_cash: trades=2 net_r=0.56768411 cash_pnl=141.03497532 w/l/f=2/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
