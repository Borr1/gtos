# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T05:27:15Z

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
- repaired_package_conversion_v3 development: trades=29 win/loss/flat=14/15/0 net_r=-11.49498487 cash_pnl=-3674.1453468 risk_cash=6866.46972334

## Guard Blocks

- development clear: orders=8 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 development USDCAD: trades=3 net_r=-1.93876257 cash_pnl=-296.97083024 w/l/f=1/2/0
- guarded_causal_admission_repair_v2 development AUDJPY: trades=1 net_r=-1.18 cash_pnl=-590.0 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 development GBPUSD: trades=1 net_r=-1.18 cash_pnl=-1180.0 w/l/f=0/1/0
- raw_package_live_as_if development AUDJPY: trades=1 net_r=-1.18 cash_pnl=-590.0 w/l/f=0/1/0
- raw_package_live_as_if development GBPUSD: trades=1 net_r=-1.18 cash_pnl=-1180.0 w/l/f=0/1/0
- repaired_package_conversion_v3 development AUDJPY: trades=1 net_r=-1.18 cash_pnl=-590.0 w/l/f=0/1/0
- repaired_package_conversion_v3 development EURGBP: trades=1 net_r=-1.18 cash_pnl=-658.98098746 w/l/f=0/1/0
- repaired_package_conversion_v3 development GBPUSD: trades=1 net_r=-1.18 cash_pnl=-1173.038 w/l/f=0/1/0
- repaired_package_conversion_v3 development JP225: trades=1 net_r=-1.18 cash_pnl=-157.11424324 w/l/f=0/1/0
- repaired_package_conversion_v3 development SPX500: trades=1 net_r=-1.18 cash_pnl=-175.83594705 w/l/f=0/1/0
- repaired_package_conversion_v3 development UKOIL_cash: trades=1 net_r=-1.17422501 cash_pnl=-175.45591515 w/l/f=0/1/0
- repaired_package_conversion_v3 development EURUSD: trades=2 net_r=-1.05534884 cash_pnl=-289.3496837 w/l/f=1/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
