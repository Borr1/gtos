# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T10:54:11Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -4.36555863 across 5 trades.
- Holdout guarded net R: -4.36555863 across 5 trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=5 win/loss/flat=0/5/0 net_r=-4.36555863 cash_pnl=-1641.38364683 risk_cash=1996.54186421
- raw_package_live_as_if holdout: trades=5 win/loss/flat=0/5/0 net_r=-4.36555863 cash_pnl=-1641.38364683 risk_cash=1996.54186421
- repaired_package_conversion_v3 holdout: trades=7 win/loss/flat=3/4/0 net_r=1.16123137 cash_pnl=452.68584693 risk_cash=3379.3981847

## Guard Blocks

- holdout clear: orders=10 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-276.025 w/l/f=0/1/0
- raw_package_live_as_if holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-276.025 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout USDJPY: trades=1 net_r=-1.1041 cash_pnl=-690.0625 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-530.4 w/l/f=0/1/0
- raw_package_live_as_if holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-530.4 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-533.34789389 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-258.12933183 w/l/f=0/1/0
- raw_package_live_as_if holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-258.12933183 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout AUDJPY: trades=1 net_r=-0.11547101 cash_pnl=-57.735505 w/l/f=0/1/0
- raw_package_live_as_if holdout AUDJPY: trades=1 net_r=-0.11547101 cash_pnl=-57.735505 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
