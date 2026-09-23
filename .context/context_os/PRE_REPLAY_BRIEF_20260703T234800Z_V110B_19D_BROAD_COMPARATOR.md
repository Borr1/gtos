# V110B 19D Broad Comparator Pre-Replay Brief

Generated UTC: 2026-07-03T23:48:00Z

Broker/live/final remain closed. Local replay/package evaluation keeps full 82-sleeve authority and missed-opportunity accounting.

## Completed Comparator Required By Owner

- V92 hostile 2026-05-13..2026-05-17: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, +6228.63096022 cash, 37/14/0 W/L/F, 62 expired unfilled, 894 candidate axes, 39 scorecard/order axes, 25 filled axes, +17.76833767 same-window actual executable R.
- V97 hostile 2026-05-13..2026-05-17: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, +4461.09800786 cash, 23/24/0 W/L/F, 51 expired unfilled, 894 candidate axes, 29 scorecard/order axes, 18 filled axes, +13.48984606 same-window actual executable R.
- V97 vs V92: -4 trades, -15.45942505 net R, -15.6932219 gross/final R, -1767.53295236 cash, -11 expired unfilled, -10 scorecard/order axes, -7 filled axes.
- V97 added 19 trades for +0.99594545R and removed 23 V92 trades for +13.53876156R. Added transfers were net positive, but the transfer swap was net negative by -12.54281611R because stronger V92 transfers disappeared.

This hostile-window comparison is a bounded repair proof. It is not a denominator for the full 1.249M source-bound reservoir.

## Current Targeted Repair Evidence

- V109 same-window 2026-06-11..2026-06-15: 69 trades, -29.35093853 net R, -24.62275835 gross/final R, -7186.3386244 cash, 21/48/0 W/L/F.
- V110B targeted 2026-06-11..2026-06-15: 32 trades, -9.28107213 net R, -7.28785875 gross/final R, -1125.65618581 cash, 12/20/0 W/L/F, 0 expired unfilled.
- V110B vs V109 same-window: -37 trades, +20.0698664 net R, +17.3348996 gross/final R, +6060.68243859 cash, -9 wins, -28 losses.
- Added V110B trades: 6 for +1.7294421R. Removed V109 trades: 43 for -18.3404243R. Common trades: 26 for -11.01051423R.
- Interpretation: the role-scope/origin repair removed a net-negative transfer path and added a small positive set, but the remaining common executed trades are still losing.

## Current Missed / Bucket Evidence

- V110B missed rows: 20852 total, +2376.0633286 positive missed R across 1996 rows, -7590.31328573 negative missed R across 4852 rows, total scoreable -5214.24995713R.
- Missed scope: 15065 rows are cost-refused non-executable diagnostic; 5787 rows are cost-passed but without execution-bound order path diagnostic.
- Executed trade loss buckets: stop_reached_before_target is 16 trades for -16.91523009R; time_stop_close_mark_from_m15_proxy is 14 trades for +3.78405796R; target_reached_before_stop is 2 trades for +3.8501R.
- Top executed losses: XAGUSD -5.78909352R, UKOIL_cash -2.229R, GER40 -2.05661956R, XAUUSD -1.18871417R; NY -7.42854004R, London -5.29938177R, Tokyo +3.44684968R.

## Current Dirty Files And Active Changes

- Selector/scheduler/harness/test batch is dirty and intentional: `src/components/selector_v4.py`, `src/research/moonshot_scheduler_v4_best_trade_allocator.py`, `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`, and focused tests.
- The current patch batch is a correctness/performance repair, not a live/final promotion: router-refusal origin-family parity plus non-executable role-disposition scope across selector, scheduler, and missed-opportunity accounting.

## Subagent Findings Reconciled

- Leibniz: incorporated. V97 regressed V92 by displacing stronger V92 transfers; added V97 transfers were net positive but too weak.
- Gibbs: incorporated. Scheduler only checked first router-refusal origin family and missed non-executable role-disposition scope; patched across selector/scheduler/harness and focused tests.
- Gauss: partially incorporated. Marketable/fillability/lifecycle/profit-harvest repairs are present and tested. Entry-quality versus limit-fillability aliasing remains a watch item if broad replay shows fillability-quality drift.

## Mismatch Map

- Source-bound -> candidate: partially fixed; not the current primary choke in V92/V97 because candidate axes stayed 894/1101.
- Candidate -> selector: partially fixed; V110B remaining fills are still all source-bound router-refusal open-reduced materializations.
- Selector -> scheduler -> risk: improved but open; V110B removed net-negative V109 transfer, but all 32 fills remain open-reduced-risk.
- Risk -> order/fillability: partially fixed; no expired unfilled and no executed refused-cost rows in V110B, but missed diagnostic rows remain large.
- Lifecycle -> fill -> exit: open material leak; V110B losses are now dominated by stop geometry, not fill expiry.
- Ledger/verifier: partially fixed; missed rows are now correctly opportunity rows, not missing data.

## Replay Decision

Run the full 2026-06-01..2026-06-19 repaired-only compact fullgrid comparator with the same V110B code. This is warranted because the targeted V110B repair improved the V109 loss bucket without collapsing all opportunity, and the owner explicitly asked for broader exposure before more policy tuning.

Expected proof:

- Helped: full-window net R improves versus V109, removed trades are net-negative, added transfers are nontrivially positive, cost-refused/source-gap executed rows remain zero, and trade count does not collapse to a fake-positive no-trade state.
- Failed: full-window R worsens, missed positive R rises materially, removed winners dominate outside the 2026-06-11..15 bucket, or scorecard/order/fill transfer collapses.
- Next flaw exposed: if V110B remains negative with honest execution, patch the largest broad root leak next. Current targeted evidence points to exit/stop geometry and all-reduced-risk action translation rather than another one-day selector narrowing.
