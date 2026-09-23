# Broad Live-As-If Replay Flow Diagnostic

Generated: 2026-06-25T03:44:08Z

Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.

## Raw vs Guarded

- Coverage: bounded_replay_materialization_not_full_available_universe (5 selected days of 901 configured days).
- Development raw net R: None across None trades.
- Development guarded net R: None across None trades.
- Holdout raw net R: -6.28382981 across 35 trades.
- Holdout guarded net R: 3.78471254 across 27 trades.
- Holdout guarded-minus-raw delta R: 10.06854235.

## Trade Buckets

- guarded_causal_admission_repair_v2 holdout: trades=27 win/loss/flat=12/15/0 net_r=3.78471254 cash_pnl=1975.60694066 risk_cash=6522.42131942
- raw_package_live_as_if holdout: trades=35 win/loss/flat=13/22/0 net_r=-6.28382981 cash_pnl=-1305.59182829 risk_cash=8808.80205035
- repaired_package_conversion_v3 holdout: trades=44 win/loss/flat=18/26/0 net_r=1.40956687 cash_pnl=256.1838653 risk_cash=10173.81785359

## Guard Blocks

- holdout clear: orders=98 blocked=0 scoreable_blocked=0 blocked_net_r=0.0 blocked_w/l/f=0/0/0

## Worst Trade Buckets

- repaired_package_conversion_v3 holdout XAGUSD: trades=10 net_r=-5.02780036 cash_pnl=-865.57392075 w/l/f=1/9/0
- guarded_causal_admission_repair_v2 holdout BTCUSD: trades=3 net_r=-3.33649918 cash_pnl=-418.21256586 w/l/f=0/3/0
- raw_package_live_as_if holdout XAUUSD: trades=3 net_r=-3.25514678 cash_pnl=-808.82004587 w/l/f=0/3/0
- raw_package_live_as_if holdout EURUSD: trades=3 net_r=-2.55264534 cash_pnl=-578.05213873 w/l/f=0/3/0
- guarded_causal_admission_repair_v2 holdout USDJPY: trades=4 net_r=-2.24027632 cash_pnl=-421.59399233 w/l/f=1/3/0
- guarded_causal_admission_repair_v2 holdout XAGUSD: trades=3 net_r=-2.15746638 cash_pnl=-541.60398073 w/l/f=0/3/0
- raw_package_live_as_if holdout XAGUSD: trades=4 net_r=-1.98464158 cash_pnl=-490.75903629 w/l/f=1/3/0
- raw_package_live_as_if holdout EURGBP: trades=1 net_r=-1.13593688 cash_pnl=-277.97944393 w/l/f=0/1/0
- raw_package_live_as_if holdout BTCUSD: trades=1 net_r=-1.12600951 cash_pnl=-140.7143133 w/l/f=0/1/0
- raw_package_live_as_if holdout AUDUSD: trades=1 net_r=-1.10794446 cash_pnl=-276.15268567 w/l/f=0/1/0
- guarded_causal_admission_repair_v2 holdout GBPJPY: trades=1 net_r=-1.10256881 cash_pnl=-277.59536391 w/l/f=0/1/0
- repaired_package_conversion_v3 holdout BTCUSD: trades=1 net_r=-1.10246696 cash_pnl=-139.13709417 w/l/f=0/1/0

## Interpretation

- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.
- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.
- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.
