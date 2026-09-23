# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-28T01:49:49Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 train: trades=31 win/loss/flat=15/16/0 net_r=-3.37646904 cash_pnl=-3124.71083285 risk_cash=9283.94381504
- raw_package_live_as_if train: trades=39 win/loss/flat=14/25/0 net_r=-15.12705571 cash_pnl=-3722.60979951 risk_cash=10448.54133505
- repaired_package_conversion_v3 train: trades=1 win/loss/flat=0/1/0 net_r=-1.0608 cash_pnl=-1060.8 risk_cash=1000.0

## Guard Blocks

- train clear: orders=118 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 train USDCHF: trades=3 net_r=-3.43929507 cash_pnl=-1708.08884173 w/l/f=0/3/0
- raw_package_live_as_if train AUDUSD: trades=5 net_r=-2.73772243 cash_pnl=-489.29464553 w/l/f=2/3/0
- raw_package_live_as_if train USDCHF: trades=4 net_r=-2.70025643 cash_pnl=-577.99229163 w/l/f=1/3/0
- guarded_causal_admission_repair_v2 train EURUSD: trades=2 net_r=-2.23213171 cash_pnl=-673.44066695 w/l/f=0/2/0
- raw_package_live_as_if train USDJPY: trades=6 net_r=-2.20696298 cash_pnl=-548.67826334 w/l/f=2/4/0
- raw_package_live_as_if train EURGBP: trades=2 net_r=-2.20004905 cash_pnl=-542.37988381 w/l/f=0/2/0
- raw_package_live_as_if train XAGUSD: trades=5 net_r=-2.16853534 cash_pnl=-533.74276973 w/l/f=1/4/0
- guarded_causal_admission_repair_v2 train UKOIL_cash: trades=2 net_r=-2.0916 cash_pnl=-508.45422852 w/l/f=0/2/0
- raw_package_live_as_if train UKOIL_cash: trades=3 net_r=-1.26819049 cash_pnl=-331.07163845 w/l/f=1/2/0
- raw_package_live_as_if train EURUSD: trades=1 net_r=-1.12044914 cash_pnl=-146.34714273 w/l/f=0/1/0
- raw_package_live_as_if train USDCAD: trades=1 net_r=-1.09461827 cash_pnl=-530.18693408 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 train GBPJPY: trades=5 net_r=-1.08549384 cash_pnl=-361.50215502 w/l/f=2/3/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
