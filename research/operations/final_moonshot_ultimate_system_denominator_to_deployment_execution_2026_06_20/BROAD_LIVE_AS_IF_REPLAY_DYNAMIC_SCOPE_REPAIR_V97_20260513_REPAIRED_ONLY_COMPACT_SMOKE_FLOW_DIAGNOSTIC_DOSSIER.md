# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-03T06:01:34Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=16 win/loss/flat=7/9/0 headline_net_r=4.47879525 cash_pnl=2014.79690301 risk_cash=2815.21449007 all_trade_rows=16 all_trade_net_r=4.47879525 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout BTCUSD: headline_trades=2 headline_net_r=-2.25045768 all_trade_rows=2 all_trade_net_r=-2.25045768 cash_pnl=-288.00502685 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=1 headline_net_r=-0.11547101 all_trade_rows=1 all_trade_net_r=-0.11547101 cash_pnl=-28.8677525 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=1 headline_net_r=1.8959 all_trade_rows=1 all_trade_net_r=1.8959 cash_pnl=193.9231499 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=1 headline_net_r=1.9542 all_trade_rows=1 all_trade_net_r=1.9542 cash_pnl=495.40062746 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=11 headline_net_r=2.99462394 all_trade_rows=11 all_trade_net_r=2.99462394 cash_pnl=1642.345905 w/l/f=5/6/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
