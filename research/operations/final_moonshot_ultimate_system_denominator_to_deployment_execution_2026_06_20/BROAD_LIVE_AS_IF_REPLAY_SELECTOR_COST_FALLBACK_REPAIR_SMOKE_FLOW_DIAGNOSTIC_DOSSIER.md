# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T10:40:31Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -3.72702929 across 10 trades.
- Holdout guarded net R: -3.72702929 across 10 trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=10 win/loss/flat=4/6/0 net_r=-3.72702929 cash_pnl=-464.35913975 risk_cash=2839.18056396
- raw_package_live_as_if holdout: trades=10 win/loss/flat=4/6/0 net_r=-3.72702929 cash_pnl=-464.35913975 risk_cash=2839.18056396
- repaired_package_conversion_v3 holdout: trades=13 win/loss/flat=5/8/0 net_r=-4.27783523 cash_pnl=-3163.2717904 risk_cash=7438.16435275

## Guard Blocks

- holdout clear: orders=22 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 holdout NZDUSD: trades=1 net_r=-1.42459211 cash_pnl=-1415.89391684 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=1 net_r=-1.33314452 cash_pnl=-163.13793958 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GBPUSD: trades=1 net_r=-1.28620514 cash_pnl=-1111.89108575 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USOIL_cash: trades=1 net_r=-1.28333131 cash_pnl=-311.68399776 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout EURGBP: trades=1 net_r=-1.26746425 cash_pnl=-364.01797439 w/l/f=0/1/0
- raw_package_live_as_if holdout EURGBP: trades=1 net_r=-1.26746425 cash_pnl=-364.01797439 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout AUDUSD: trades=1 net_r=-1.19022789 cash_pnl=-168.08902887 w/l/f=0/1/0
- raw_package_live_as_if holdout AUDUSD: trades=1 net_r=-1.19022789 cash_pnl=-168.08902887 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-189.32847027 w/l/f=0/1/0
- raw_package_live_as_if holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-189.32847027 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-690.0625 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-519.21853012 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
