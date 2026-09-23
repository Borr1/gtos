# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-15T15:33:04Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (31 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 development: headline_trades=4 win/loss/flat=3/1/0 headline_net_r=0.98832036 cash_pnl=98.24769712 risk_cash=395.31136071 all_trade_rows=61 all_trade_net_r=-2.76396743 diagnostic_only_rows=57 diagnostic_only_net_r=-3.75228779

## Guard Blocks


## Missed Opportunities

- repaired_package_conversion_v3 development: rows=154329 scoreable/unscoreable=26812/127517 all_scoreable_net_r=-24212.54521713 executable_rows/net_r=0/0.0 diagnostic_rows/net_r=26812/-24212.54521713 diagnostic_positive=6752/6616.22471941 diagnostic_negative=20060/-30828.76993654 diagnostic_flat=0

## Worst Trade Buckets

- repaired_package_conversion_v3 development BTCUSD: headline_trades=0 headline_net_r=0.0 all_trade_rows=1 all_trade_net_r=1.17978948 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development GER40: headline_trades=0 headline_net_r=0.0 all_trade_rows=1 all_trade_net_r=-1.09119657 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development EURUSD: headline_trades=0 headline_net_r=0.0 all_trade_rows=2 all_trade_net_r=0.82243377 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development GBPJPY: headline_trades=0 headline_net_r=0.0 all_trade_rows=6 all_trade_net_r=-0.92037494 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development UKOIL_cash: headline_trades=0 headline_net_r=0.0 all_trade_rows=8 all_trade_net_r=2.96117738 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development XAGUSD: headline_trades=0 headline_net_r=0.0 all_trade_rows=13 all_trade_net_r=3.2519951 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development XAUUSD: headline_trades=0 headline_net_r=0.0 all_trade_rows=26 all_trade_net_r=-9.95611201 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 development USDJPY: headline_trades=4 headline_net_r=0.98832036 all_trade_rows=4 all_trade_net_r=0.98832036 cash_pnl=98.24769712 w/l/f=3/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
