# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-29T18:23:12Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=6 win/loss/flat=3/3/0 net_r=0.10198273 cash_pnl=9.88407935 risk_cash=600.09652245

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAUUSD: trades=1 net_r=-1.05434912 cash_pnl=-105.434912 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout GBPUSD: trades=1 net_r=-0.45273974 cash_pnl=-45.32036357 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=2 net_r=-0.19619843 cash_pnl=-19.82291494 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout AUDUSD: trades=1 net_r=0.60417001 cash_pnl=60.47890673 w/l/f=1/0/0
- repaired_package_conversion_v3 holdout UKOIL_cash: trades=1 net_r=1.20110001 cash_pnl=119.98336313 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
