# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-29T07:40:55Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (38 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: trades=19 win/loss/flat=7/12/0 net_r=-5.03584755 cash_pnl=-1366.11715307 risk_cash=4984.41297237

## Guard Blocks


## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAUUSD: trades=9 net_r=-2.57193161 cash_pnl=-638.85070942 w/l/f=3/6/0
- repaired_package_conversion_v3 holdout UKOIL_cash: trades=4 net_r=-2.29955494 cash_pnl=-575.94791248 w/l/f=1/3/0
- repaired_package_conversion_v3 holdout EURUSD: trades=3 net_r=-0.88384726 cash_pnl=-219.21189613 w/l/f=1/2/0
- repaired_package_conversion_v3 holdout US30_cash: trades=2 net_r=0.12148739 cash_pnl=-81.1339556 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout GBPJPY: trades=1 net_r=0.59799887 cash_pnl=149.02732056 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
