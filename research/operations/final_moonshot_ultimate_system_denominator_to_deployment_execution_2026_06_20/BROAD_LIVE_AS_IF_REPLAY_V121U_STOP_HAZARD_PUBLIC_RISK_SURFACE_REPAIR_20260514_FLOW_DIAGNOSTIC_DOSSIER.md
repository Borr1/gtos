# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-05T13:51:58Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=24 win/loss/flat=9/15/0 headline_net_r=0.29253564 cash_pnl=24.60851082 risk_cash=2406.04506533 all_trade_rows=24 all_trade_net_r=0.29253564 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=4 headline_net_r=-1.94881681 all_trade_rows=4 all_trade_net_r=-1.94881681 cash_pnl=-195.98908586 w/l/f=1/3/0
- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=2 headline_net_r=-1.65108367 all_trade_rows=2 all_trade_net_r=-1.65108367 cash_pnl=-166.3861714 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=2 headline_net_r=-1.17811802 all_trade_rows=2 all_trade_net_r=-1.17811802 cash_pnl=-118.56249177 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=1 headline_net_r=-1.0458 all_trade_rows=1 all_trade_net_r=-1.0458 cash_pnl=-104.66335164 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GBPJPY: headline_trades=2 headline_net_r=-0.50220636 all_trade_rows=2 all_trade_net_r=-0.50220636 cash_pnl=-50.82718738 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout GBPUSD: headline_trades=1 headline_net_r=-0.04590952 all_trade_rows=1 all_trade_net_r=-0.04590952 cash_pnl=-4.61666014 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDCHF: headline_trades=1 headline_net_r=0.69754875 all_trade_rows=1 all_trade_net_r=0.69754875 cash_pnl=69.73746277 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USOIL_cash: headline_trades=1 headline_net_r=0.776728 all_trade_rows=1 all_trade_net_r=0.776728 cash_pnl=78.10774751 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=1 headline_net_r=0.78097687 all_trade_rows=1 all_trade_net_r=0.78097687 cash_pnl=78.05739711 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=9 headline_net_r=4.4092164 all_trade_rows=9 all_trade_net_r=4.4092164 cash_pnl=439.75085162 w/l/f=4/5/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
