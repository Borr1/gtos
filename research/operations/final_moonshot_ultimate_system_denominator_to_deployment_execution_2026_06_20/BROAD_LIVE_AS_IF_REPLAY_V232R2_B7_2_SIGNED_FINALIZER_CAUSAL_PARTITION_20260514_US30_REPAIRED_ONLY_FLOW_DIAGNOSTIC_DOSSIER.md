# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-12T00:55:00Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=1 win/loss/flat=1/0/0 headline_net_r=0.1675249 cash_pnl=16.75249 risk_cash=100.0 all_trade_rows=1 all_trade_net_r=0.1675249 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout US30_cash: headline_trades=1 headline_net_r=0.1675249 all_trade_rows=1 all_trade_net_r=0.1675249 cash_pnl=16.75249 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
