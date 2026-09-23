# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-20T22:38:32Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (32 selected days of 901 configured days).
- Development raw net R: -6.89912669 across 32 trades.
- Development guarded net R: 4.82298732 across 43 trades.
- Holdout raw net R: -21.11411554 across 89 trades.
- Holdout guarded net R: -22.71376878 across 101 trades.
- Holdout guarded-minus-raw delta R: -1.59965324.

## Trade Buckets

- guarded_causal_admission_repair_v2 development: trades=43 win/loss/flat=22/21/0 net_r=4.82298732 cash_pnl=1970.3682671 risk_cash=17715.78425907
- guarded_causal_admission_repair_v2 holdout: trades=101 win/loss/flat=34/67/0 net_r=-22.71376878 cash_pnl=-6364.14477192 risk_cash=41563.24090952
- raw_package_live_as_if development: trades=32 win/loss/flat=13/19/0 net_r=-6.89912669 cash_pnl=-5840.00993641 risk_cash=13145.81483359
- raw_package_live_as_if holdout: trades=89 win/loss/flat=30/59/0 net_r=-21.11411554 cash_pnl=-1260.65569124 risk_cash=39885.97416832

## Guard Blocks

- development blocked: orders=584 blocked=584 scoreable_blocked=553 blocked_net_r=-143.01123732 blocked_w/l/f=186/367/0
- development clear: orders=407 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0
- holdout blocked: orders=1510 blocked=1510 scoreable_blocked=1452 blocked_net_r=-304.77122327 blocked_w/l/f=511/941/0
- holdout clear: orders=851 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 holdout XAUUSD: trades=7 net_r=-4.92007455 cash_pnl=-2102.5389937 w/l/f=1/6/0
- guarded_causal_admission_repair_v2 holdout GER40: trades=9 net_r=-4.73890677 cash_pnl=-982.91597058 w/l/f=2/7/0
- raw_package_live_as_if holdout JP225: trades=16 net_r=-4.39108015 cash_pnl=-1169.74492569 w/l/f=5/11/0
- raw_package_live_as_if holdout GBPJPY: trades=6 net_r=-4.1861232 cash_pnl=-2460.37424684 w/l/f=1/5/0
- guarded_causal_admission_repair_v2 holdout EURGBP: trades=6 net_r=-3.72368693 cash_pnl=-981.93470991 w/l/f=1/5/0
- guarded_causal_admission_repair_v2 development GER40: trades=3 net_r=-3.54 cash_pnl=-904.04783701 w/l/f=0/3/0
- raw_package_live_as_if holdout UK100: trades=3 net_r=-3.51431258 cash_pnl=-927.80121523 w/l/f=0/3/0
- raw_package_live_as_if holdout NZDUSD: trades=9 net_r=-3.41641299 cash_pnl=189.84986468 w/l/f=3/6/0
- guarded_causal_admission_repair_v2 holdout NAS100: trades=3 net_r=-3.37546662 cash_pnl=-622.57427554 w/l/f=0/3/0
- guarded_causal_admission_repair_v2 holdout NZDUSD: trades=9 net_r=-2.78679062 cash_pnl=-1693.28944942 w/l/f=3/6/0
- raw_package_live_as_if holdout EURGBP: trades=3 net_r=-2.47027599 cash_pnl=-445.6268702 w/l/f=0/3/0
- guarded_causal_admission_repair_v2 holdout CHFJPY: trades=2 net_r=-2.36 cash_pnl=-1633.8233648 w/l/f=0/2/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
