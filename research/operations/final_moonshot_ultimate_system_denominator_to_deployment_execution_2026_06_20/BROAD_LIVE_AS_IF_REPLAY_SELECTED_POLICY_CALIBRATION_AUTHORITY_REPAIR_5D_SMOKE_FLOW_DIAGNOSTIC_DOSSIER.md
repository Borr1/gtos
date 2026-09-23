# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-29T20:40:05Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 train: trades=86 win/loss/flat=39/47/0 net_r=-12.1983158 cash_pnl=-1217.55614978 risk_cash=8523.19286198

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 train USDCHF: trades=7 net_r=-6.35395489 cash_pnl=-629.77739258 w/l/f=1/6/0
- repaired_package_conversion_v3 train XAUUSD: trades=9 net_r=-3.56218933 cash_pnl=-353.29881156 w/l/f=4/5/0
- repaired_package_conversion_v3 train UKOIL_cash: trades=10 net_r=-2.96862517 cash_pnl=-294.55825486 w/l/f=3/7/0
- repaired_package_conversion_v3 train USDCAD: trades=4 net_r=-2.70034309 cash_pnl=-268.39131667 w/l/f=1/3/0
- repaired_package_conversion_v3 train EURGBP: trades=2 net_r=-2.02927154 cash_pnl=-201.89634846 w/l/f=0/2/0
- repaired_package_conversion_v3 train EURUSD: trades=7 net_r=-1.97917102 cash_pnl=-197.27503299 w/l/f=3/4/0
- repaired_package_conversion_v3 train AUDUSD: trades=5 net_r=-0.80507327 cash_pnl=-81.56537364 w/l/f=2/3/0
- repaired_package_conversion_v3 train AUDJPY: trades=4 net_r=-0.65282481 cash_pnl=-64.49074378 w/l/f=2/2/0
- repaired_package_conversion_v3 train GER40: trades=1 net_r=-0.3006553 cash_pnl=-29.58679622 w/l/f=0/1/0
- repaired_package_conversion_v3 train GBPJPY: trades=6 net_r=-0.1350609 cash_pnl=-13.98911328 w/l/f=3/3/0
- repaired_package_conversion_v3 train US30_cash: trades=2 net_r=0.47120875 cash_pnl=46.7558311 w/l/f=1/1/0
- repaired_package_conversion_v3 train NZDUSD: trades=1 net_r=0.6965738 cash_pnl=68.9951211 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
