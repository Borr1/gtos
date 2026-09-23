# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-04T16:32:00Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=4 win/loss/flat=0/4/0 headline_net_r=-3.802746 cash_pnl=-379.74586967 risk_cash=399.33525658 all_trade_rows=4 all_trade_net_r=-3.802746 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout USDJPY: headline_trades=1 headline_net_r=-1.1541 all_trade_rows=1 all_trade_net_r=-1.1541 cash_pnl=-115.28266089 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout BTCUSD: headline_trades=1 headline_net_r=-1.10336291 all_trade_rows=1 all_trade_net_r=-1.10336291 cash_pnl=-110.336291 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=1 headline_net_r=-1.03402526 all_trade_rows=1 all_trade_net_r=-1.03402526 cash_pnl=-103.16923031 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout EURUSD: headline_trades=1 headline_net_r=-0.51125783 all_trade_rows=1 all_trade_net_r=-0.51125783 cash_pnl=-50.95768747 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
