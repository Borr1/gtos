# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T06:57:25Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -3.54244579 across 11 trades.
- Holdout guarded net R: -3.54244579 across 11 trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=11 win/loss/flat=2/9/0 net_r=-3.54244579 cash_pnl=-524.7505294 risk_cash=3071.63861417
- raw_package_live_as_if holdout: trades=11 win/loss/flat=2/9/0 net_r=-3.54244579 cash_pnl=-524.7505294 risk_cash=3071.63861417
- repaired_package_conversion_v3 holdout: trades=33 win/loss/flat=29/4/0 net_r=1.08129353 cash_pnl=1721.4622695 risk_cash=17037.77156618

## Guard Blocks

- holdout clear: orders=22 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=2 net_r=-2.1216 cash_pnl=-332.31869889 w/l/f=0/2/0
- raw_package_live_as_if holdout XAGUSD: trades=2 net_r=-2.1216 cash_pnl=-332.31869889 w/l/f=0/2/0
- repaired_package_conversion_v3 holdout SPX500: trades=1 net_r=-1.13846249 cash_pnl=-290.9330142 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- raw_package_live_as_if holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-535.7942259 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-114.68405981 w/l/f=0/1/0
- raw_package_live_as_if holdout USOIL_cash: trades=1 net_r=-1.047 cash_pnl=-114.68405981 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=1 net_r=-1.03818762 cash_pnl=-519.09381 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout UK100: trades=4 net_r=-0.88617571 cash_pnl=-222.87196471 w/l/f=3/1/0
- repaired_package_conversion_v3 holdout GER40: trades=5 net_r=-0.60712124 cash_pnl=-157.46436704 w/l/f=4/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
