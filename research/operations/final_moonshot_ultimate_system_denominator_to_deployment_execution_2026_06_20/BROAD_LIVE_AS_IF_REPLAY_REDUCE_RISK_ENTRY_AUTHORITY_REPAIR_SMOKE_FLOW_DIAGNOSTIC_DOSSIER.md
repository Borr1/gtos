# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T17:46:06Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -2.22327101 across 3 trades.
- Holdout guarded net R: -2.22327101 across 3 trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=3 win/loss/flat=0/3/0 net_r=-2.22327101 cash_pnl=-1636.17997163 risk_cash=1994.40732247
- raw_package_live_as_if holdout: trades=3 win/loss/flat=0/3/0 net_r=-2.22327101 cash_pnl=-1636.17997163 risk_cash=1994.40732247
- repaired_package_conversion_v3 holdout: trades=14 win/loss/flat=6/8/0 net_r=1.94357966 cash_pnl=2013.88669549 risk_cash=11129.0342389

## Guard Blocks

- holdout clear: orders=6 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 holdout BTCUSD: trades=1 net_r=-1.14902186 cash_pnl=-295.21898534 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-1060.8 w/l/f=0/1/0
- raw_package_live_as_if holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-1060.8 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-1060.8 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-517.64446663 w/l/f=0/1/0
- raw_package_live_as_if holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-517.64446663 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-517.56890529 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout US30_cash: trades=1 net_r=-0.48000961 cash_pnl=-501.13932829 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GBPJPY: trades=1 net_r=-0.17840029 cash_pnl=-197.3404678 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout AUDJPY: trades=1 net_r=-0.11547101 cash_pnl=-57.735505 w/l/f=0/1/0
- raw_package_live_as_if holdout AUDJPY: trades=1 net_r=-0.11547101 cash_pnl=-57.735505 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout AUDJPY: trades=1 net_r=-0.11547101 cash_pnl=-72.16938125 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
