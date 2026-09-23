# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-05T22:02:02Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=45 win/loss/flat=27/18/0 headline_net_r=21.82482975 cash_pnl=12465.17720161 risk_cash=26023.79295971 all_trade_rows=45 all_trade_net_r=21.82482975 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=3 headline_net_r=-1.59434619 all_trade_rows=3 all_trade_net_r=-1.59434619 cash_pnl=-1435.85079971 w/l/f=1/2/0
- repaired_package_conversion_v3 holdout GBPUSD: headline_trades=2 headline_net_r=-1.13773978 all_trade_rows=2 all_trade_net_r=-1.13773978 cash_pnl=-324.71095522 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout GBPJPY: headline_trades=2 headline_net_r=-0.50220636 all_trade_rows=2 all_trade_net_r=-0.50220636 cash_pnl=-808.59937721 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=5 headline_net_r=-0.3917763 all_trade_rows=5 all_trade_net_r=-0.3917763 cash_pnl=177.86091887 w/l/f=3/2/0
- repaired_package_conversion_v3 holdout USDCHF: headline_trades=1 headline_net_r=0.69754875 all_trade_rows=1 all_trade_net_r=0.69754875 cash_pnl=188.20287939 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDCAD: headline_trades=1 headline_net_r=1.17736842 all_trade_rows=1 all_trade_net_r=1.17736842 cash_pnl=815.83760998 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=5 headline_net_r=1.67152597 all_trade_rows=5 all_trade_net_r=1.67152597 cash_pnl=1062.55987483 w/l/f=3/2/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=2 headline_net_r=1.78773059 all_trade_rows=2 all_trade_net_r=1.78773059 cash_pnl=1233.86848135 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=1 headline_net_r=1.9542 all_trade_rows=1 all_trade_net_r=1.9542 cash_pnl=988.37223481 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=6 headline_net_r=4.48860545 all_trade_rows=6 all_trade_net_r=4.48860545 cash_pnl=2726.77406397 w/l/f=4/2/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=9 headline_net_r=6.65917826 all_trade_rows=9 all_trade_net_r=6.65917826 cash_pnl=4197.86560515 w/l/f=5/4/0
- repaired_package_conversion_v3 holdout USOIL_cash: headline_trades=8 headline_net_r=7.01474094 all_trade_rows=8 all_trade_net_r=7.01474094 cash_pnl=3642.9966654 w/l/f=6/2/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
