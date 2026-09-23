# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-09T00:22:26Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=72 win/loss/flat=41/31/0 headline_net_r=-5.20239659 cash_pnl=-3907.50669036 risk_cash=30668.26839984 all_trade_rows=73 all_trade_net_r=-4.85125425 diagnostic_only_rows=1 diagnostic_only_net_r=0.35114234

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout UK100: headline_trades=4 headline_net_r=-3.18002143 all_trade_rows=4 all_trade_net_r=-3.18002143 cash_pnl=-1315.9605359 w/l/f=1/3/0
- repaired_package_conversion_v3 holdout XAGUSD: headline_trades=3 headline_net_r=-1.9798854 all_trade_rows=3 all_trade_net_r=-1.9798854 cash_pnl=-1319.46339046 w/l/f=1/2/0
- repaired_package_conversion_v3 holdout AUDUSD: headline_trades=5 headline_net_r=-1.94929784 all_trade_rows=5 all_trade_net_r=-1.94929784 cash_pnl=-245.98045626 w/l/f=2/3/0
- repaired_package_conversion_v3 holdout NAS100: headline_trades=6 headline_net_r=-1.48762269 all_trade_rows=6 all_trade_net_r=-1.48762269 cash_pnl=-727.35346589 w/l/f=3/3/0
- repaired_package_conversion_v3 holdout JP225: headline_trades=5 headline_net_r=-1.3337849 all_trade_rows=6 all_trade_net_r=-0.98264256 cash_pnl=-384.87761486 w/l/f=3/2/0
- repaired_package_conversion_v3 holdout GBPJPY: headline_trades=1 headline_net_r=-1.09019743 all_trade_rows=1 all_trade_net_r=-1.09019743 cash_pnl=-1293.34690928 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout SPX500: headline_trades=2 headline_net_r=-1.06786699 all_trade_rows=2 all_trade_net_r=-1.06786699 cash_pnl=-259.87925829 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout USDCHF: headline_trades=2 headline_net_r=-0.37444362 all_trade_rows=2 all_trade_net_r=-0.37444362 cash_pnl=-981.59581203 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout AUDJPY: headline_trades=1 headline_net_r=-0.11547101 all_trade_rows=1 all_trade_net_r=-0.11547101 cash_pnl=-72.16938125 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout CHFJPY: headline_trades=1 headline_net_r=-0.02420813 all_trade_rows=1 all_trade_net_r=-0.02420813 cash_pnl=-5.92273044 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: headline_trades=4 headline_net_r=0.20277457 all_trade_rows=4 all_trade_net_r=0.20277457 cash_pnl=146.84727119 w/l/f=2/2/0
- repaired_package_conversion_v3 holdout US30_cash: headline_trades=13 headline_net_r=1.59721128 all_trade_rows=13 all_trade_net_r=1.59721128 cash_pnl=656.9296798 w/l/f=10/3/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
