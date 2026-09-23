# Broad Live-As-If Replay Behavior - BROAD_LIVE_AS_IF_REPLAY_V121AB_HOSTILE_5D_RUNTIME_FINAL_RISK_AUTHORITY_GENERALIZATION_20260513_20260517

Broker/live/final authority remains closed. This is replay/proxy behavior only.

## Same-Window Result

- Window: `2026-05-13..2026-05-17`
- Baseline: trades `47`, net `13.89627731`, gross `18.2389067`, final `18.2389067`, cash `4461.09800786`, W/L/F `23/24/0`
- Candidate: trades `56`, net `15.33728438`, gross `19.31963588`, final `19.31963588`, cash `6869.54005741`, W/L/F `29/27/0`
- Delta: trades `9.0`, net `1.44100707`, gross `1.08072918`, final `1.08072918`, cash `2408.44204955`, wins `6.0`, losses `3.0`

## Added / Removed Transfers

- Added: count `50`, net `9.49159363`, gross `12.92207233`, final `12.92207233`, W/L/F `25/25/0`
- Removed: count `41`, net `8.05058656`, gross `11.84134315`, final `11.84134315`, W/L/F `19/22/0`
- Added transfer net positive: `True`
- Removed transfer net positive: `True`
- Added minus removed net R: `1.44100707`

## Candidate Behavior

- Candidate rows: `23970`
- Scorecard rows: `288`
- Order events / orders: `139` / `62`
- Missed rows / scoreable: `23899` / `4354`
- Risk cash / risk pct: `30964.42363412` / `29.4625`
- Trade sessions: `{'london': 29, 'ny': 21, 'tokyo': 6}`
- Trade sides: `{'LONG': 38, 'SHORT': 18}`
- Net by symbol: `{'AUDJPY': -0.11547101, 'AUDUSD': -2.13978803, 'GBPJPY': -0.50220636, 'GBPUSD': -1.13773978, 'GER40': 1.87044843, 'UKOIL_cash': 0.9084, 'US30_cash': 0.10709649, 'USDCHF': 0.69754875, 'USDJPY': -0.66176946, 'USOIL_cash': 7.01474094, 'XAGUSD': 3.45103246, 'XAUUSD': 5.84499195}`
- Close reasons: `{'stop_reached_before_target': 14, 'target_reached_before_stop': 11, 'time_stop_close_mark_from_m1': 31}`
- Risk ladder tiers: `{'full': 19, 'reduced': 37}`

## Order-Executable Transfer

- Row counts: `{'missed_order_executable_false_rows': 689, 'missed_order_executable_true_rows': 873, 'missed_order_executable_unknown_rows': 22337, 'missed_rows': 23899, 'order_order_executable_true_rows': 139, 'order_rows': 139, 'scorecard_order_executable_false_rows': 41, 'scorecard_order_executable_true_rows': 247, 'scorecard_rows': 288, 'trade_order_executable_true_rows': 56, 'trade_rows': 56}`
- Transfer status counts: `{'missed:final_blocked': 873, 'order:final_blocked': 9, 'order:order_bound': 130, 'scorecard:final_blocked': 247, 'trade:trade_bound': 56}`
- Blocker counts: `{'missed:cost_authority': 3, 'missed:fill_realism': 291, 'missed:headroom': 3, 'missed:lifecycle_authority': 66, 'missed:marketable_guard': 436, 'missed:scheduler_selection': 33, 'missed:selector_materialization': 41, 'order:fill_realism': 9, 'scorecard:daily_lockout': 39, 'scorecard:fill_realism': 91, 'scorecard:headroom': 2, 'scorecard:lifecycle_authority': 8, 'scorecard:lifecycle_expiry': 2, 'scorecard:marketable_guard': 89, 'scorecard:risk_basis_missing': 2, 'scorecard:selector_materialization': 14}`
- Comparator failures: `{}`

## Interpretation

- This artifact is normalized to the replay window shown above.
- It does not compare the one-day result to the global source-bound reservoir.
- Improvement is only valid if verifier scans remain clean and opportunity is not merely suppressed.
