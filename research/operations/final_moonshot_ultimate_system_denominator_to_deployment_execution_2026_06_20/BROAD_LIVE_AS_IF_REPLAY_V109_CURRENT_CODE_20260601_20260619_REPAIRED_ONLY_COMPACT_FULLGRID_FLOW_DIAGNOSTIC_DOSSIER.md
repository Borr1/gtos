# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-03T22:23:41Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (19 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=247 win/loss/flat=128/119/0 headline_net_r=-0.62198945 cash_pnl=-1195.35960987 risk_cash=60674.75410859 all_trade_rows=247 all_trade_net_r=-0.62198945 diagnostic_only_rows=0 diagnostic_only_net_r=0.0

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout USOIL_cash: headline_trades=27 headline_net_r=-4.18083948 all_trade_rows=27 all_trade_net_r=-4.18083948 cash_pnl=-1129.66037557 w/l/f=10/17/0
- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=39 headline_net_r=-4.08860072 all_trade_rows=39 all_trade_net_r=-4.08860072 cash_pnl=-2070.20145656 w/l/f=17/22/0
- repaired_package_conversion_v3 holdout EURUSD: headline_trades=5 headline_net_r=-3.95083981 all_trade_rows=5 all_trade_net_r=-3.95083981 cash_pnl=-1040.25036826 w/l/f=1/4/0
- repaired_package_conversion_v3 holdout GBPUSD: headline_trades=1 headline_net_r=-1.09725251 all_trade_rows=1 all_trade_net_r=-1.09725251 cash_pnl=-277.41227513 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=4 headline_net_r=-0.69675972 all_trade_rows=4 all_trade_net_r=-0.69675972 cash_pnl=-184.80373398 w/l/f=2/2/0
- repaired_package_conversion_v3 holdout USDCHF: headline_trades=16 headline_net_r=-0.65848462 all_trade_rows=16 all_trade_net_r=-0.65848462 cash_pnl=-184.12997263 w/l/f=11/5/0
- repaired_package_conversion_v3 holdout BTCUSD: headline_trades=8 headline_net_r=-0.26533492 all_trade_rows=8 all_trade_net_r=-0.26533492 cash_pnl=-39.19034692 w/l/f=2/6/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=39 headline_net_r=-0.26250216 all_trade_rows=39 all_trade_net_r=-0.26250216 cash_pnl=-951.70666632 w/l/f=22/17/0
- repaired_package_conversion_v3 holdout GER40: headline_trades=16 headline_net_r=0.10812171 all_trade_rows=16 all_trade_net_r=0.10812171 cash_pnl=66.4143098 w/l/f=8/8/0
- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=8 headline_net_r=0.56458311 all_trade_rows=8 all_trade_net_r=0.56458311 cash_pnl=141.10793019 w/l/f=4/4/0
- repaired_package_conversion_v3 holdout US30_cash: headline_trades=2 headline_net_r=1.06762626 all_trade_rows=2 all_trade_net_r=1.06762626 cash_pnl=268.55242522 w/l/f=2/0/0
- repaired_package_conversion_v3 holdout USDCAD: headline_trades=4 headline_net_r=1.64788979 all_trade_rows=4 all_trade_net_r=1.64788979 cash_pnl=423.73319295 w/l/f=3/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
