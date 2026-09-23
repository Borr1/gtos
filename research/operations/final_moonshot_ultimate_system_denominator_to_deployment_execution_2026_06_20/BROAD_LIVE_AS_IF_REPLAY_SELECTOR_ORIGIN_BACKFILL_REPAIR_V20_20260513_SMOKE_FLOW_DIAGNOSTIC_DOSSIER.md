# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-01T14:48:49Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=8 win/loss/flat=7/1/0 net_r=7.68334157 cash_pnl=769.89521628 risk_cash=802.85522634

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout AUDUSD: trades=1 net_r=0.604705 cash_pnl=60.73485566 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: trades=1 net_r=1.51496719 cash_pnl=152.30052561 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USOIL_cash: trades=3 net_r=2.76976598 cash_pnl=277.21480344 w/l/f=3/0/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=3 net_r=2.7939034 cash_pnl=279.64503157 w/l/f=2/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
