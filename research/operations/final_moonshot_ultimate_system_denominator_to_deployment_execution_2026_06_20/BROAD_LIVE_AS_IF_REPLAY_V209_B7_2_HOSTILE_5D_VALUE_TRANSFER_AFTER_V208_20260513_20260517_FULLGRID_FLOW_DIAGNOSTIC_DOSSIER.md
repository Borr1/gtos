# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-09T04:18:51Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=18 win/loss/flat=11/7/0 headline_net_r=-3.47466796 cash_pnl=-868.32556257 risk_cash=4503.6890717 all_trade_rows=18 all_trade_net_r=-3.47466796 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout NAS100: headline_trades=2 headline_net_r=-2.18069019 all_trade_rows=2 all_trade_net_r=-2.18069019 cash_pnl=-544.99172008 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=5 headline_net_r=-1.49602349 all_trade_rows=5 all_trade_net_r=-1.49602349 cash_pnl=-373.91332932 w/l/f=3/2/0
- repaired_package_conversion_v3 holdout SPX500: headline_trades=1 headline_net_r=-1.08786699 all_trade_rows=1 all_trade_net_r=-1.08786699 cash_pnl=-271.85226638 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout UK100: headline_trades=1 headline_net_r=-1.08049326 all_trade_rows=1 all_trade_net_r=-1.08049326 cash_pnl=-271.33367849 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout JP225: headline_trades=1 headline_net_r=0.02 all_trade_rows=1 all_trade_net_r=0.02 cash_pnl=5.0065156 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=4 headline_net_r=0.02298609 all_trade_rows=4 all_trade_net_r=0.02298609 cash_pnl=6.23007441 w/l/f=3/1/0
- repaired_package_conversion_v3 holdout US30_cash: headline_trades=4 headline_net_r=2.32741988 all_trade_rows=4 all_trade_net_r=2.32741988 cash_pnl=582.52884169 w/l/f=4/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
