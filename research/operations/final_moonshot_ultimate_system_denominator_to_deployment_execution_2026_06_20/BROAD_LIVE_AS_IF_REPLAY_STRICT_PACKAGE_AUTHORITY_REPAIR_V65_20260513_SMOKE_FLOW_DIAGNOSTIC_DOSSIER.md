# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-02T02:57:31Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=8 win/loss/flat=5/3/0 headline_net_r=7.2254044 cash_pnl=2154.8255824 risk_cash=1658.81710161 all_trade_rows=17 all_trade_net_r=9.1399857 diagnostic_only_rows=9 diagnostic_only_net_r=1.9145813

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout BTCUSD: headline_trades=1 headline_net_r=-1.12444817 all_trade_rows=2 all_trade_net_r=-1.10444817 cash_pnl=-71.43489779 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=1 headline_net_r=-0.11547101 all_trade_rows=1 all_trade_net_r=-0.11547101 cash_pnl=-28.8677525 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=0 headline_net_r=0.0 all_trade_rows=1 all_trade_net_r=0.02 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=0 headline_net_r=0.0 all_trade_rows=1 all_trade_net_r=0.46932439 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=0 headline_net_r=0.0 all_trade_rows=3 all_trade_net_r=0.91528709 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=1 headline_net_r=1.87125937 all_trade_rows=1 all_trade_net_r=1.87125937 cash_pnl=475.51581442 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=1 headline_net_r=1.9542 all_trade_rows=1 all_trade_net_r=1.9542 cash_pnl=493.28398812 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=4 headline_net_r=4.63986421 all_trade_rows=7 all_trade_net_r=5.12983403 cash_pnl=1286.32843015 w/l/f=3/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
