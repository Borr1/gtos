# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-21T06:43:29Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (1 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -1.02863089 across 9 trades.
- Holdout guarded net R: -2.13673745 across 12 trades.
- Holdout guarded-minus-raw delta R: -1.10810656.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=12 win/loss/flat=4/8/0 net_r=-2.13673745 cash_pnl=-344.22398719 risk_cash=2675.29768146
- raw_package_live_as_if holdout: trades=9 win/loss/flat=3/6/0 net_r=-1.02863089 cash_pnl=-875.75479616 risk_cash=2160.95417157
- repaired_package_conversion_v3 holdout: trades=48 win/loss/flat=43/5/0 net_r=1.33549535 cash_pnl=732.14866418 risk_cash=20418.34716881

## Guard Blocks

- holdout clear: orders=26 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- raw_package_live_as_if holdout CHFJPY: trades=1 net_r=-1.19727212 cash_pnl=-598.63606 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout SPX500: trades=1 net_r=-1.193566 cash_pnl=-298.39761498 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAUUSD: trades=1 net_r=-1.17295263 cash_pnl=-589.79715631 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout GER40: trades=1 net_r=-1.15429197 cash_pnl=-254.06043597 w/l/f=0/1/0
- raw_package_live_as_if holdout GER40: trades=1 net_r=-1.15429197 cash_pnl=-197.18508286 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout NAS100: trades=1 net_r=-1.14721508 cash_pnl=-286.80964752 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- raw_package_live_as_if holdout UK100: trades=1 net_r=-1.12 cash_pnl=-280.0 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-126.02307968 w/l/f=0/1/0
- raw_package_live_as_if holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-304.51793213 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout XAGUSD: trades=1 net_r=-1.0608 cash_pnl=-532.01610226 w/l/f=0/1/0
- raw_package_live_as_if holdout XAUUSD: trades=1 net_r=-1.04081172 cash_pnl=-245.65287681 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
