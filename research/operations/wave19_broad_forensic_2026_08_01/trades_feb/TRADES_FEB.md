# February executed-trade walk — Session FA wave-19 forensic

Walker for the 58 executed February trades of `CP_FEBRUARY_TRUE_UTC_S0R0_V1` (broad V4,
S0R0 neutral-selection / fixed-sizing arm, true-UTC clock). February re-decode authorized
by the owner mandate of 2026-08-01 for defect attribution only. March and live-forward
outcomes untouched. Evidence class: LANE_ITERATION_EVIDENCE — unbilled, never admission-grade.

Sources (read-only): the wave18 route ledgers
(`.../CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_{TRADE,ORDERED_PATH_ORACLE}_LEDGER.jsonl`,
`_SUMMARY.json`), the committed lane trade table, pool receipt, first-read protocol/result,
and the February compact scoreable pool (24,239 rows, streamed). Scripts `01_*.py`–`04_*.py`
in this directory regenerate every number.

## 1. Reconciliation — exact on every axis

| quantity | receipt | recomputed | match |
|---|---|---|---|
| executed trades | 58 | 58 | exact |
| realized physical net R | -3.96139869 | -3.96139869 (sum of 58 `net_r`) | exact, 8 dp |
| physical gross R (SUMMARY `split_profile_stats[0]`) | +0.20391894 | +0.20391894 | exact |
| physical execution cost R | 4.16531763 | 4.16531764 (sum `cost_r`) | 1e-8 |
| win/loss counts | 24 / 34, win rate 0.4137931 | 24 / 34 | exact |
| pool scoreable rows / positive | 24,239 / 7,498 | 24,239 / 7,498 | exact |
| pool mean net / winner / loser | -0.64002116 / +0.8482149 / -1.30657596 | same | exact |
| base_rate_positive / breakeven | 0.309336 / 0.606359 | 0.3093362 / 0.6063586 | exact |

Unlike January (55 of 57 trades scoreable, 2 `terminal_r_unscoreable`), **all 58 February
trades are scoreable** and the realized figure sums all 58.

## 2. The headline the aggregates hide

**The executed February book is gross-POSITIVE: +0.204 R before cost. The whole -3.961 R
realized loss is the 4.165 R execution-cost bill.** January under the same walk: gross
-1.221 R, cost 4.285 R, net -5.506 R. Two independent months, the same shape: a
near-zero-gross book paying a stable ~4.2 R/month cost bill at ~0.07 R/trade.

This is the opposite of the pool, where cost is 76.5% of an already-negative surface
(pool gross sum -3,649 R; cost 11,864 R; net -15,513 R). The executed slice (neutral-hash
selection) happens to land on low-cost rows (0.072 R/trade vs 0.489 R/row pool mean).

## 3. Precision decomposition (mission item 3)

**(a) What "precision" is.** A POOL metric, not a trade metric
(`CP_FEBRUARY_FIRST_READ_PROTOCOL_V1.json` → `decision_population.precision_metrics`):
`base_rate_positive` = share of the 24,239 diagnostic-scoreable missed-opportunity rows with
cost-true `opportunity_net_proxy_r` > 0 (7,498/24,239 = 0.309336); `breakeven_precision` =
|mean loser| / (mean winner + |mean loser|) = 1.30657596 / 2.15479086 = 0.606359.

**(b) Trade-level W/L asymmetry is the OPPOSITE of the pool's.** The 58 trades: precision
24/58 = 0.4138; mean winner +0.8173, mean loser -0.6934 → trade-level breakeven **0.4590**,
headroom **-0.0452**. The 0.606 breakeven is set by the pool's fat loser tail (-1.307 vs
+0.848), not by anything the executed book did.

**(c) Where the pool asymmetry comes from: cost, not gross geometry.** At gross the pool
asymmetry is *favorable* (winner +1.0507, loser -0.8665, breakeven 0.4519 < 0.5). The
0.4519 → 0.6064 inflation is entirely cost, through two channels: net losers carry 1.84×
the winners' cost load (0.5700 vs 0.3097 R/row), and 1,546 gross-positive rows (+820.9 R)
are flipped into the loser tail (-722.3 R), which also drops precision 0.3731 → 0.3093.
Exit truncation exists (21/58 executed trades marked at the 120-min path end, median hold
91 min) but nets only -1.28 R; stop closes carry -18.37 R and giveback/harvest exits
+12.95 R.

**(d) Zero-cost counterfactual.**
- Pool: precision 0.3731 vs breakeven 0.4519 → headroom **-0.0788, still negative**; sum
  -3,649 R. Cost explains 73.5% of the -0.297 headroom gap; the residual -0.079 is genuine
  gross negativity. Binary endpoints agree (hit rate 0.2061 vs 1/3).
- Executed 58: precision 25/58 = 0.4310 vs breakeven 0.4287 → **+0.0023, marginally
  positive**, sum +0.204 R. At zero cost the executed slice crosses breakeven — barely,
  at n=58.

**(e) Ex-ante subpopulations.** None clears its own breakeven at usable n. The two that do
— `current_breaker_re_entry` (n=3, +1.218 R, 3/3) and `structural_distance_extreme` (n=1,
+1.170 R) — repeat January's sign (n=8 +4.356 and n=7 +3.499, both above own breakeven) and
are exactly the factory's already-mined direction (CQ inverted-breaker).
`current_fvg_fill` is below its own breakeven in both months. Direction and session FLIP
between months (Jan LONG +4.89 / SHORT -10.39; Feb LONG -2.87 / SHORT -1.10; Jan london
+2.53 / ny -6.05; Feb london -2.01 / ny -0.37) — selection/regime noise, not mechanism.

## 4. Loss attribution (mission item 4) — classes sum to -3.96140 R

Rules (priority): target_hit → winners-non-target (in `other`) → cost_dominated
(gross≥0, net≤0) → direction_wrong (mfe < 0.25 R) → exit_geometry (mfe - cost > 0: a
net-profitable exit existed on the ordered path) → stop_hit → horizon_marked → other.

| class | n | net R | gross R | cost R | mean MFE | mean MAE |
|---|---:|---:|---:|---:|---:|---:|
| target_hit | 2 | +3.857 | +4.000 | 0.143 | +2.08 | +0.18 |
| other (winner_non_target_exit) | 22 | +15.758 | +17.410 | 1.651 | +1.58 | -0.44 |
| cost_dominated | 1 | -0.017 | +0.019 | 0.036 | +0.26 | -0.09 |
| direction_wrong | 10 | -9.594 | -8.814 | 0.780 | +0.10 | -0.96 |
| exit_geometry | 23 | -13.965 | -12.411 | 1.555 | +0.55 | -0.78 |

January under identical rules (n=57, sum -5.506): direction_wrong 11 / -9.697;
exit_geometry 21 / -19.951; target_hit 6 / +11.911; other 17 / +12.231; unscoreable 2.
`stop_hit`/`horizon_marked` are empty in both months because every stop/horizon loser is
absorbed upstream by direction_wrong or exit_geometry — i.e. every loser either never had
0.25 R of favorable excursion or had a net-profitable exit it failed to take.

**Stable failure signature across two independent months (mechanism verdict):**
1. direction_wrong is eerily constant: -9.59 R (n=10) vs -9.70 R (n=11).
2. exit_geometry is the largest loss class both months (-13.97 / -19.95).
3. stop-first-touch trades carry essentially all losses (Feb -17.85 on 18; Jan -25.45 on
   25); target-first-touch trades are 100% positive both months (+12.84 on 11; +12.79 on 7).
4. Family signs identical: fvg negative, breaker + structural positive, both months.
5. The ~4.2 R/month cost bill on near-zero gross, both months.

**Unstable (selection/regime, NOT mechanism):** direction, session, symbol mix (XAUUSD
24→40 of the book; UKOIL_cash +8.74 R in January, zero February trades).

Oracle bound: perfect exits at each trade's MFE (cost held) would have made +48.63 R vs
realized -3.96 (gap 52.6 R) — an unreachable bound, quoted only to size the exit-capture
channel.

## 5. Anomalies

1. **candidate_id is not unique on trades**: 44 unique ids across 58 rows (re-entries).
   Naive id joins undercount; the walk keys on rows.
2. **Model scores are non-discriminative on the executed set**: `candidate_confidence` =
   0.55 on all 58 (flat); winners vs losers means: probability 0.8131 / 0.8135,
   expectancy_r 0.9914 / 0.9927, expected_net_r 0.9212 / 0.9309. Expected net +0.93
   R/trade vs realized -0.068: a ~1.0 R/trade calibration gap with zero rank power.
3. **8/58 trades are not headline_result_eligible** (7 `m1_proxy_replay_not_headline
   _authority_ordered_tick_required`, 1 guarded-market-fallback) yet are inside the
   realized physical -3.961 — correct per the physical definition, but do not read the 58
   as headline-grade.
4. **ORDERED_PATH_ORACLE ledger has 66 rows / 48 unique ids** (10 dup ids, 4 ids with no
   trade row); all 44 trade ids covered.
5. **Horizon truncation**: 21/58 trades (36%) end as `path_end_mark_to_market` at the
   120-min horizon; median hold 91 min, max 120. The arm never lets a third of the book
   resolve its geometry.
6. Pool receipt `binary_population` (950 target / 3,660 stop) is a different subpopulation
   from the pool close-reason counts (2,811 target_reached / 11,499 stop_reached) —
   definitions differ; not reconciled here (open question, not a fault finding).

## Outputs

- `TRADES_FEB_TABLE.json` — 58-trade projection (identity, mechanism, session, times,
  prices, close_reason, gross/cost/net, sizing, decision scores, MFE/MAE, first-touch,
  best_available_exit, loss_class).
- `TRADES_FEB_ATTRIBUTION.json` — class rules, Feb + Jan class totals, aggregations by
  family/direction/symbol/session/close_reason/first-touch for both months.
- `PRECISION_DECOMP.json` — items (a)–(e) with cross-checks.
- `FEB_POOL_PRECISION_STATS.json` — streamed pool recomputation (net, zero-cost gross,
  cost channels, close-reason mix by sign).
- Scripts `01_extract_trades_feb.py`, `02_pool_precision_stats.py`,
  `03_attribution_and_aggregations.py`, `04_precision_decomp.py`.
