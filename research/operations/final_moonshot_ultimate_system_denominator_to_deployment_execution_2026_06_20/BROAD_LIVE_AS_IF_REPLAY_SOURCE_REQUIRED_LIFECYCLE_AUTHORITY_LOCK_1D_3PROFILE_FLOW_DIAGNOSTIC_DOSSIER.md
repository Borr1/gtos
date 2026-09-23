# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-27T08:29:05Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -0.87277185 across 7 trades.
- Holdout guarded net R: -2.21354216 across 4 trades.
- Holdout guarded-minus-raw delta R: -1.34077031.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=4 win/loss/flat=1/3/0 net_r=-2.21354216 cash_pnl=-412.87443142 risk_cash=874.84298552
- raw_package_live_as_if holdout: trades=7 win/loss/flat=3/4/0 net_r=-0.87277185 cash_pnl=-78.41309941 risk_cash=1624.82519312
- repaired_package_conversion_v3 holdout: trades=7 win/loss/flat=6/1/0 net_r=1.99838263 cash_pnl=718.53779376 risk_cash=1880.56168967

## Guard Blocks

- holdout clear: orders=91 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 holdout BTCUSD: trades=1 net_r=-1.12600951 cash_pnl=-140.95484741 w/l/f=0/1/0
- raw_package_live_as_if holdout BTCUSD: trades=1 net_r=-1.12600951 cash_pnl=-140.87417386 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAUUSD: trades=2 net_r=-0.55392939 cash_pnl=-138.8920871 w/l/f=1/1/0
- guarded_causal_admission_repair_v2 holdout GER40: trades=1 net_r=-0.53360326 cash_pnl=-133.02749691 w/l/f=0/1/0
- raw_package_live_as_if holdout GER40: trades=1 net_r=-0.53360326 cash_pnl=-133.15266072 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=2 net_r=-0.51217522 cash_pnl=-128.82357498 w/l/f=1/1/0
- raw_package_live_as_if holdout USDJPY: trades=1 net_r=-0.26999316 cash_pnl=-67.49829 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout NZDUSD: trades=1 net_r=-0.11037312 cash_pnl=-27.59328 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=1 net_r=0.02 cash_pnl=2.51220156 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout GER40: trades=1 net_r=0.28280526 cash_pnl=71.1590203 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout XAUUSD: trades=2 net_r=0.32169619 cash_pnl=80.75944467 w/l/f=2/0/0
- raw_package_live_as_if holdout AUDUSD: trades=1 net_r=0.60417001 cash_pnl=151.17447992 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
