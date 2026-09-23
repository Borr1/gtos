# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-29T16:26:30Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=47 win/loss/flat=35/12/0 net_r=6.95421428 cash_pnl=695.48413093 risk_cash=4730.18876641

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout GBPJPY: trades=5 net_r=-1.72734527 cash_pnl=-174.412349 w/l/f=2/3/0
- repaired_package_conversion_v3 holdout EURUSD: trades=6 net_r=-1.31165993 cash_pnl=-132.39529052 w/l/f=4/2/0
- repaired_package_conversion_v3 holdout US30_cash: trades=7 net_r=2.55150546 cash_pnl=257.09075412 w/l/f=7/0/0
- repaired_package_conversion_v3 holdout XAUUSD: trades=16 net_r=3.40619816 cash_pnl=339.82053888 w/l/f=12/4/0
- repaired_package_conversion_v3 holdout UKOIL_cash: trades=13 net_r=4.03551586 cash_pnl=405.38047745 w/l/f=10/3/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
