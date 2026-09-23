# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T05:53:01Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- repaired_package_conversion_v3 development: trades=50 win/loss/flat=42/8/0 net_r=2.46158609 cash_pnl=-409.20587563 risk_cash=18717.6192347

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 development JP225: trades=1 net_r=-1.18 cash_pnl=-295.0 w/l/f=0/1/0
- repaired_package_conversion_v3 development UK100: trades=1 net_r=-1.18 cash_pnl=-295.90759131 w/l/f=0/1/0
- repaired_package_conversion_v3 development BTCUSD: trades=2 net_r=-1.12036021 cash_pnl=-140.11161308 w/l/f=1/1/0
- repaired_package_conversion_v3 development GER40: trades=4 net_r=-1.12 cash_pnl=-281.15628582 w/l/f=3/1/0
- repaired_package_conversion_v3 development USDJPY: trades=2 net_r=-0.99510424 cash_pnl=-1000.07365359 w/l/f=1/1/0
- repaired_package_conversion_v3 development US30_cash: trades=3 net_r=-0.97614046 cash_pnl=-489.58619691 w/l/f=2/1/0
- repaired_package_conversion_v3 development SPX500: trades=6 net_r=-0.0143532 cash_pnl=-4.36999381 w/l/f=5/1/0
- repaired_package_conversion_v3 development EURGBP: trades=1 net_r=0.02 cash_pnl=12.4443826 w/l/f=1/0/0
- repaired_package_conversion_v3 development GBPJPY: trades=1 net_r=0.02 cash_pnl=19.85308026 w/l/f=1/0/0
- repaired_package_conversion_v3 development USDCAD: trades=1 net_r=0.02 cash_pnl=20.06153161 w/l/f=1/0/0
- repaired_package_conversion_v3 development AUDUSD: trades=2 net_r=0.04 cash_pnl=39.67543775 w/l/f=2/0/0
- repaired_package_conversion_v3 development USOIL_cash: trades=3 net_r=0.06 cash_pnl=14.95920774 w/l/f=3/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
