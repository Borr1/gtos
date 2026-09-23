# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-02T04:14:57Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=14 win/loss/flat=6/8/0 headline_net_r=4.26374144 cash_pnl=1318.08653321 risk_cash=3155.28283576 all_trade_rows=14 all_trade_net_r=4.26374144 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout BTCUSD: headline_trades=1 headline_net_r=-1.12779365 all_trade_rows=1 all_trade_net_r=-1.12779365 cash_pnl=-142.2489844 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=1 headline_net_r=-1.06166901 all_trade_rows=1 all_trade_net_r=-1.06166901 cash_pnl=-134.59882332 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=1 headline_net_r=-0.37768323 all_trade_rows=1 all_trade_net_r=-0.37768323 cash_pnl=-94.4208075 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=1 headline_net_r=-0.11547101 all_trade_rows=1 all_trade_net_r=-0.11547101 cash_pnl=-28.8677525 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=2 headline_net_r=0.1217968 all_trade_rows=2 all_trade_net_r=0.1217968 cash_pnl=7.51189927 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=1 headline_net_r=1.87125937 all_trade_rows=1 all_trade_net_r=1.87125937 cash_pnl=472.04512088 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=1 headline_net_r=1.9542 all_trade_rows=1 all_trade_net_r=1.9542 cash_pnl=491.23035641 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=6 headline_net_r=2.99910217 all_trade_rows=6 all_trade_net_r=2.99910217 cash_pnl=747.43552437 w/l/f=3/3/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
