# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-07-16T11:00:16Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: None.

## Trade Buckets

- repaired_package_conversion_v3 holdout: headline_trades=4 win/loss/flat=3/1/0 headline_net_r=2.12544422 cash_pnl=992.6201607 risk_cash=2142.02493426 all_trade_rows=6 all_trade_net_r=4.03591467 diagnostic_only_rows=2 diagnostic_only_net_r=1.91047045

## Guard Blocks


## Missed Opportunities

- repaired_package_conversion_v3 holdout: rows=6975 scoreable/unscoreable=1471/5504 all_scoreable_net_r=-1152.58538221 executable_rows/net_r=0/0.0 diagnostic_rows/net_r=1471/-1152.58538221 diagnostic_positive=401/322.45120558 diagnostic_negative=1070/-1475.03658779 diagnostic_flat=0

## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAUUSD: headline_trades=2 headline_net_r=-0.03204615 all_trade_rows=2 all_trade_net_r=-0.03204615 cash_pnl=-30.155048 w/l/f=1/1/0
- repaired_package_conversion_v3 holdout UKOIL_cash: headline_trades=0 headline_net_r=0.0 all_trade_rows=1 all_trade_net_r=0.0 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 holdout US30_cash: headline_trades=0 headline_net_r=0.0 all_trade_rows=1 all_trade_net_r=1.91047045 cash_pnl=0.0 w/l/f=0/0/0
- repaired_package_conversion_v3 holdout EURUSD: headline_trades=2 headline_net_r=2.15749037 all_trade_rows=2 all_trade_net_r=2.15749037 cash_pnl=1022.7752087 w/l/f=2/0/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
