# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T20:15:01Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (2 selected days of 901 configured days).
- Development raw net R: -0.43857516 across 14 trades.
- Development guarded net R: -0.68879549 across 12 trades.
- Holdout raw net R: None across None trades.
- Holdout guarded net R: None across None trades.
- Holdout guarded-minus-raw delta R: 0.0.

## Trade Buckets

- guarded_causal_admission_repair_v2 development: trades=12 win/loss/flat=8/4/0 net_r=-0.68879549 cash_pnl=-955.13130586 risk_cash=5965.22686633
- raw_package_live_as_if development: trades=14 win/loss/flat=9/5/0 net_r=-0.43857516 cash_pnl=-295.12905851 risk_cash=6280.56331403
- repaired_package_conversion_v3 development: trades=21 win/loss/flat=10/11/0 net_r=-6.27565448 cash_pnl=-5810.32865381 risk_cash=12767.99021095

## Guard Blocks

- development clear: orders=24 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 development GBPUSD: trades=3 net_r=-2.09506381 cash_pnl=-1063.73257705 w/l/f=1/2/0
- raw_package_live_as_if development XAUUSD: trades=3 net_r=-1.98473003 cash_pnl=-561.50448636 w/l/f=1/2/0
- repaired_package_conversion_v3 development XAUUSD: trades=3 net_r=-1.98473003 cash_pnl=-1554.31003213 w/l/f=1/2/0
- repaired_package_conversion_v3 development EURUSD: trades=2 net_r=-1.15548702 cash_pnl=-1721.05955552 w/l/f=0/2/0
- repaired_package_conversion_v3 development GBPJPY: trades=1 net_r=-1.14785668 cash_pnl=-204.77566249 w/l/f=0/1/0
- repaired_package_conversion_v3 development AUDUSD: trades=2 net_r=-1.09164151 cash_pnl=-1643.84598491 w/l/f=1/1/0
- repaired_package_conversion_v3 development USDCHF: trades=1 net_r=-1.07103901 cash_pnl=-323.60149197 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 development UKOIL_cash: trades=1 net_r=-1.0458 cash_pnl=-203.74709198 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 development AUDUSD: trades=3 net_r=-1.03808947 cash_pnl=-1096.31248871 w/l/f=2/1/0
- guarded_causal_admission_repair_v2 development XAUUSD: trades=2 net_r=-0.93990085 cash_pnl=-375.49726136 w/l/f=1/1/0
- repaired_package_conversion_v3 development UKOIL_cash: trades=2 net_r=-0.75244836 cash_pnl=-369.51417867 w/l/f=1/1/0
- raw_package_live_as_if development GER40: trades=1 net_r=-0.51319697 cash_pnl=-67.7226637 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
