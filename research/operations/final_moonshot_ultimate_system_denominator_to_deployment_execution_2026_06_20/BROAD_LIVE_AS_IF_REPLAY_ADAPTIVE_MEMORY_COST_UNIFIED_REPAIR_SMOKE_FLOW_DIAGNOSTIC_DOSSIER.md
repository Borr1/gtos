# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T19:53:49Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: None (None selected days of None configured days).
- Development raw net R: -6.33832732 across 60 trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- raw_package_live_as_if development: trades=60 win/loss/flat=23/37/0 net_r=-6.33832732 cash_pnl=-4500.42073104 risk_cash=37303.8445525
- raw_package_live_as_if train: trades=6 win/loss/flat=3/3/0 net_r=-1.21272876 cash_pnl=-472.70952905 risk_cash=3211.25647537

## Guard Blocks


## Worst Trade Buckets

- raw_package_live_as_if development UKOIL_cash: trades=9 net_r=-4.54564632 cash_pnl=-2098.50242685 w/l/f=2/7/0
- raw_package_live_as_if development USOIL_cash: trades=5 net_r=-3.60990905 cash_pnl=-1423.67946294 w/l/f=0/5/0
- raw_package_live_as_if development XAUUSD: trades=12 net_r=-2.12847356 cash_pnl=467.64199071 w/l/f=4/8/0
- raw_package_live_as_if train GER40: trades=1 net_r=-1.14383267 cash_pnl=-306.57206866 w/l/f=0/1/0
- raw_package_live_as_if development EURGBP: trades=1 net_r=-1.05946839 cash_pnl=-339.94061435 w/l/f=0/1/0
- raw_package_live_as_if development GER40: trades=1 net_r=-0.51319697 cash_pnl=-75.74747443 w/l/f=0/1/0
- raw_package_live_as_if development AUDUSD: trades=3 net_r=-0.45679513 cash_pnl=-592.40159574 w/l/f=2/1/0
- raw_package_live_as_if train GBPUSD: trades=1 net_r=-0.25630663 cash_pnl=-83.29965475 w/l/f=0/1/0
- raw_package_live_as_if development USDCAD: trades=1 net_r=-0.25321672 cash_pnl=-374.98623696 w/l/f=0/1/0
- raw_package_live_as_if train XAUUSD: trades=1 net_r=-0.25149871 cash_pnl=-251.49871 w/l/f=0/1/0
- raw_package_live_as_if development EURUSD: trades=6 net_r=-0.07919911 cash_pnl=-580.89175212 w/l/f=3/3/0
- raw_package_live_as_if train AUDUSD: trades=1 net_r=0.00968162 cash_pnl=7.21754893 w/l/f=1/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
