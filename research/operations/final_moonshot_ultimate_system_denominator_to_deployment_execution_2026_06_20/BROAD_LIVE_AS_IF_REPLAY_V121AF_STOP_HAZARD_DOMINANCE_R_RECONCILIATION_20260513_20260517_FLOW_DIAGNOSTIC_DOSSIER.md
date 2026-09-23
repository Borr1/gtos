# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-05T21:20:19Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=44 win/loss/flat=26/18/0 headline_net_r=20.26032016 cash_pnl=10420.02497129 risk_cash=24896.63276601 all_trade_rows=44 all_trade_net_r=20.26032016 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=3 headline_net_r=-1.59434619 all_trade_rows=3 all_trade_net_r=-1.59434619 cash_pnl=-1402.70334248 w/l/f=1/2/0
- repaired_package_conversion_v3 holdout GBPUSD: headline_trades=2 headline_net_r=-1.13773978 all_trade_rows=2 all_trade_net_r=-1.13773978 cash_pnl=-318.80616451 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout GBPJPY: headline_trades=2 headline_net_r=-0.50220636 all_trade_rows=2 all_trade_net_r=-0.50220636 cash_pnl=-786.93646395 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=5 headline_net_r=-0.3917763 all_trade_rows=5 all_trade_net_r=-0.3917763 cash_pnl=169.60711247 w/l/f=3/2/0
- repaired_package_conversion_v3 holdout USDCHF: headline_trades=1 headline_net_r=0.69754875 all_trade_rows=1 all_trade_net_r=0.69754875 cash_pnl=184.78045524 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDCAD: headline_trades=1 headline_net_r=1.17736842 all_trade_rows=1 all_trade_net_r=1.17736842 cash_pnl=801.00179903 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=2 headline_net_r=1.78773059 all_trade_rows=2 all_trade_net_r=1.78773059 cash_pnl=1210.11849657 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=1 headline_net_r=1.9542 all_trade_rows=1 all_trade_net_r=1.9542 cash_pnl=988.37223481 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=5 headline_net_r=1.9689008 all_trade_rows=5 all_trade_net_r=1.9689008 cash_pnl=1050.54321197 w/l/f=3/2/0
- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=6 headline_net_r=4.48860545 all_trade_rows=6 all_trade_net_r=4.48860545 cash_pnl=2736.03507124 w/l/f=4/2/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=8 headline_net_r=4.79729384 all_trade_rows=8 all_trade_net_r=4.79729384 cash_pnl=2186.18866358 w/l/f=4/4/0
- repaired_package_conversion_v3 holdout USOIL_cash: headline_trades=8 headline_net_r=7.01474094 all_trade_rows=8 all_trade_net_r=7.01474094 cash_pnl=3601.82389732 w/l/f=6/2/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
