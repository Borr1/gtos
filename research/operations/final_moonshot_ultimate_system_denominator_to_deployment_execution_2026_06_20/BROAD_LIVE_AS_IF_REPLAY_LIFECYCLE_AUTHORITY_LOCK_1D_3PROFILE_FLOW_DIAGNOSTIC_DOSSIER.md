# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-27T07:54:01Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -0.87277185 across 7 trades.
- Holdout guarded net R: -1.65961277 across 2 trades.
- Holdout guarded-minus-raw delta R: -0.78684092.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=10 win/loss/flat=5/5/0 net_r=0.35340914 cash_pnl=320.18633062 risk_cash=1844.22248356
- raw_package_live_as_if holdout: trades=7 win/loss/flat=3/4/0 net_r=-0.87277185 cash_pnl=-78.41309941 risk_cash=1624.82519312
- repaired_package_conversion_v3 holdout: trades=15 win/loss/flat=14/1/0 net_r=5.92273855 cash_pnl=1694.72831581 risk_cash=3617.06654351

## Guard Blocks

- holdout clear: orders=66 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 holdout BTCUSD: trades=2 net_r=-2.25294745 cash_pnl=-283.68808883 w/l/f=0/2/0
- raw_package_live_as_if holdout BTCUSD: trades=1 net_r=-1.12600951 cash_pnl=-140.87417386 w/l/f=0/1/0
- raw_package_live_as_if holdout GER40: trades=1 net_r=-0.53360326 cash_pnl=-133.15266072 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=2 net_r=-0.51217522 cash_pnl=-128.82357498 w/l/f=1/1/0
- guarded_causal_admission_repair_v2 holdout GER40: trades=3 net_r=-0.33330553 cash_pnl=-131.04111055 w/l/f=1/2/0
- raw_package_live_as_if holdout USDJPY: trades=1 net_r=-0.26999316 cash_pnl=-67.49829 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout NZDUSD: trades=1 net_r=-0.11037312 cash_pnl=-27.59328 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=2 net_r=0.04 cash_pnl=5.0728602 w/l/f=2/0/0
- repaired_package_conversion_v3 holdout GER40: trades=1 net_r=0.28280526 cash_pnl=71.84871222 w/l/f=1/0/0
- raw_package_live_as_if holdout AUDUSD: trades=1 net_r=0.60417001 cash_pnl=151.17447992 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout AUDUSD: trades=1 net_r=0.60417001 cash_pnl=153.24349994 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=0.88008429 cash_pnl=443.47184531 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
