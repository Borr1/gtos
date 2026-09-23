# V109 Broad Exposure Pre-Replay Brief

Generated UTC: 2026-07-03T21:21:20Z

Broker/live/final remain closed. Local replay/package evaluation retains full 82-sleeve authority.

## Current Replay Truth

- Latest hostile same-window comparator requested: V92 vs V97 over 2026-05-13..2026-05-17 is complete on disk.
- V92 hostile: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, +6228.63096022 cash, 37/14/0 W/L/F, 62 expired unfilled.
- V97 hostile: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, +4461.09800786 cash, 23/24/0 W/L/F, 51 expired unfilled.
- V97 delta vs V92: -4 trades, -15.45942505 net R, -15.6932219 gross/final R, -1767.53295236 cash, -14 wins, +10 losses, -11 expired unfilled.
- V97 added 19 trades for +0.99594545R, but removed 23 trades for +13.53876156R. Added transfers were net positive, but net worse because they displaced stronger V92 transfers.

## Same-Window Transfer Denominator

- V92: 1101 package axes, 894 candidate-generated axes, 39 scorecard/order axes, 25 filled axes, +17.76833767 actual executable R, +218870.181480028 source-bound R available inside this replay window.
- V97: 1101 package axes, 894 candidate-generated axes, 29 scorecard/order axes, 18 filled axes, +13.48984606 actual executable R, +222423.262022048 source-bound R available inside this replay window.
- V97 transfer delta: candidate axes unchanged, scorecard/order axes -10, filled axes -7, actual executable R -4.27849161.
- This five-day smoke proves local V97 behavior only. It does not prove total million-R reservoir conversion.

## Current Broader Baselines

- V106 hostile current-code behavior: 83 trades, +32.57834226 net R, +39.15063139 gross/final R, 56/27/0, 49 scorecard/order axes, 48 filled axes.
- V107 non-May five-day current-code behavior: 108 trades, +17.04075961 net R, +25.00079247 gross/final R, 67/41/0, 61 scorecard/order axes, 57 filled axes.
- V108 one-day truth smoke: synthetic all-candidate finalizer probes are diagnostic-only without exact scheduler binding; no selected-trade behavior change versus the V106 May-14 slice.
- V104 non-May 19D baseline: 112 trades, +14.66106256 net R, +23.29090562 gross/final R, 51/61/0, 56 scorecard/order axes, 52 filled axes.

## Open Root Mismatch Classes

- Source-bound -> candidate is not the immediate choke in these windows: candidate-generated axes are stable at 894/1101 for V92/V97/V106/V107.
- Candidate -> selector is partially fixed: V106/V107 improve versus V97/V105 but do not materially expand candidate-axis conversion.
- Selector -> scheduler -> risk remains the major bottleneck: scorecard/order axes are still tiny versus candidate axes.
- Risk -> order/fillability is partially fixed: broker-cost REFUSED/source-gap executions remain zero, but missed positive R is still large.
- Lifecycle/exit quality remains open: V97 removed strong V92 profit-harvest/lifecycle winners, and V106/V107 gains are not yet proof of broad transfer expansion.
- Ledger truth is partially fixed: V108 repaired diagnostic-only finalizer probes, but broad behavior must be rerun with this truth surface.

## Next Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V109_CURRENT_CODE_20260601_20260619_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: 2026-06-01..2026-06-19
- Profile: `repaired_package_conversion_v3`
- Surface: full 24-symbol fullgrid, compact missed ledger, candidate index retained, packet sidecar omitted.
- Tick mode: `--skip-tick-source` for direct comparability with V92/V97/V106/V107. Tick-hydrated fillability is a separate follow-up if the broader run implicates tick/source fillability.

## Success And Failure Criteria

- Helped: V109 beats the V104 19D baseline without suppressing opportunity, with higher or equal scorecard/order/fill transfer, zero cost-refused/source-gap executions, and net-positive added transfer quality.
- Failed: V109 loses versus V104 19D, reduces scorecard/order/fill transfer, increases missed positive R materially, or gets positive only by suppressing trades.
- Exposes next flaw: all orders remain open-reduced-risk, scheduler-not-selected dominates source-bound leakage, or exit/stop/profit-harvest buckets dominate the added losses. In that case patch that same-root chain before another broad replay.
