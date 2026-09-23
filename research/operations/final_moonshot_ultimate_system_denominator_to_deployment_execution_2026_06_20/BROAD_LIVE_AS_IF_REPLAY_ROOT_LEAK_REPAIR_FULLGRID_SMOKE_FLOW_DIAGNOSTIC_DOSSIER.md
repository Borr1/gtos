# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T21:34:52Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: 0.0 across 0 trades.
- Development guarded net R: 0.0 across 0 trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 development: trades=5 win/loss/flat=0/5/0 net_r=-5.40677468 cash_pnl=-2024.79703867 risk_cash=1872.31778476

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 development USDJPY: trades=1 net_r=-1.1041 cash_pnl=-686.44286452 w/l/f=0/1/0
- repaired_package_conversion_v3 development USOIL_cash: trades=1 net_r=-1.097 cash_pnl=-270.92888679 w/l/f=0/1/0
- repaired_package_conversion_v3 development UKOIL_cash: trades=1 net_r=-1.0958 cash_pnl=-270.63251973 w/l/f=0/1/0
- repaired_package_conversion_v3 development XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-272.25542763 w/l/f=0/1/0
- repaired_package_conversion_v3 development XAUUSD: trades=1 net_r=-1.04907468 cash_pnl=-524.53734 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
