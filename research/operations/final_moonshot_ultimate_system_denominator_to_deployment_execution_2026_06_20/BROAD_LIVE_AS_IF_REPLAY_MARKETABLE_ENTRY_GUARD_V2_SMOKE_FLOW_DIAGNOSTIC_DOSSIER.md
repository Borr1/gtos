# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T05:34:46Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: -2.36 across 2 trades.
- Development guarded net R: -2.36 across 2 trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 development: trades=2 win/loss/flat=0/2/0 net_r=-2.36 cash_pnl=-1770.0 risk_cash=1500.0
- raw_package_live_as_if development: trades=2 win/loss/flat=0/2/0 net_r=-2.36 cash_pnl=-1770.0 risk_cash=1500.0
- repaired_package_conversion_v3 development: trades=30 win/loss/flat=16/14/0 net_r=-7.00592986 cash_pnl=-2109.14749447 risk_cash=13515.64885315

## Guard Blocks

- development clear: orders=8 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- guarded_causal_admission_repair_v2 development AUDJPY: trades=1 net_r=-1.18 cash_pnl=-590.0 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 development GBPUSD: trades=1 net_r=-1.18 cash_pnl=-1180.0 w/l/f=0/1/0
- raw_package_live_as_if development AUDJPY: trades=1 net_r=-1.18 cash_pnl=-590.0 w/l/f=0/1/0
- raw_package_live_as_if development GBPUSD: trades=1 net_r=-1.18 cash_pnl=-1180.0 w/l/f=0/1/0
- repaired_package_conversion_v3 development BTCUSD: trades=1 net_r=-1.18 cash_pnl=-147.5 w/l/f=0/1/0
- repaired_package_conversion_v3 development ETHUSD: trades=1 net_r=-1.18 cash_pnl=-147.5 w/l/f=0/1/0
- repaired_package_conversion_v3 development EURGBP: trades=1 net_r=-1.18 cash_pnl=-733.38223846 w/l/f=0/1/0
- repaired_package_conversion_v3 development JP225: trades=1 net_r=-1.18 cash_pnl=-295.0 w/l/f=0/1/0
- repaired_package_conversion_v3 development NAS100: trades=1 net_r=-1.18 cash_pnl=-295.0 w/l/f=0/1/0
- repaired_package_conversion_v3 development UK100: trades=1 net_r=-1.18 cash_pnl=-295.35984083 w/l/f=0/1/0
- repaired_package_conversion_v3 development USDJPY: trades=2 net_r=-0.99510424 cash_pnl=-995.64560927 w/l/f=1/1/0
- repaired_package_conversion_v3 development XAGUSD: trades=2 net_r=-0.82344447 cash_pnl=-303.96649159 w/l/f=1/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
