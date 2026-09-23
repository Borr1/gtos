# A4 Before-Framework-Fix Full-Cohort R — n=11

**Date:** 2026-04-28
**Branch:** `research/a4-before-framework-full-cohort-sim`
**Main HEAD at sim:** `c24f1e176881f3ca1dfed0089469436a8d4f3001`
**Output JSON:** `research/a4_trending_bull_replay_2026-04-28/a4_before_framework_fix_full_cohort_R.json`

## Methodology

M1 fill simulation across the full 11-record A4 trending_bull cohort using the
**current post-FA-2 AI emissions** from `replay_outcomes.jsonl` (non-zero
`sl_buffer_applied`). Mirrors the semantics of `fill_simulator_m1.py` exactly:

- LIMIT order at `entry_price` placed at `candle_time_utc`.
- LONG: filled when M1 `low <= entry`; thereafter SL hit on `low <= sl`, TP1 on `high >= tp1`.
- Same-bar SL+TP collision -> adverse-first (SL wins).
- Forward-walk horizon: 192 M15 candles = 2880 M1 bars (~48h, matches pending-intent expiry).
- `FILLED_WIN` = TP1 hit; `FILLED_LOSS` = SL hit; `NEVER_FILLED` = limit untouched in horizon.

This represents the cohort's R distribution **with the sl_beyond_ob fix on main
HEAD applied** (already shipped commit `2c75f98` and 4 sister fixes), but **without**
the multi-framework dispatch fix (in flight on a separate branch).

## Per-record outcomes

| trade_id | dir | entry | SL | TP1 | buf | outcome | fill_time | exit_reason | realized_R |
|---|---|---|---|---|---|---|---|---|---|
| 2026-04-15_ny_1315 | LONG | 4777.43 | 4757.77 | 4806.92 | 4.37 | FILLED_WIN | 4/16 17:40 | tp1_hit | +1.500 |
| 2026-04-15_ny_1330 | LONG | 4777.43 | 4757.73 | 4807.00 | 4.47 | FILLED_WIN | 4/16 17:40 | tp1_hit | +1.501 |
| 2026-04-15_ny_1345 | LONG | 4777.43 | 4757.65 | 4807.13 | 4.54 | FILLED_WIN | 4/16 17:40 | tp1_hit | +1.502 |
| 2026-04-15_ny_1415 | LONG | 4777.43 | 4757.67 | 4807.12 | 4.47 | FILLED_WIN | 4/16 17:40 | tp1_hit | +1.503 |
| 2026-04-15_ny_1615 | LONG | 4777.43 | 4757.55 | 4807.16 | 4.59 | FILLED_WIN | 4/16 17:40 | tp1_hit | +1.495 |
| 2026-04-15_ny_1700 | LONG | 4777.43 | 4757.80 | 4806.88 | 4.34 | FILLED_WIN | 4/16 17:40 | tp1_hit | +1.500 |
| 2026-04-16_london_0800 | LONG | 4796.28 | 4783.65 | 4815.22 | 3.79 | FILLED_LOSS | 4/16 16:52 | sl_hit | -1.000 |
| 2026-04-16_london_0930 | LONG | 4796.28 | 4783.57 | 4815.35 | 3.87 | FILLED_LOSS | 4/16 16:52 | sl_hit | -1.000 |
| 2026-04-16_ny_1316 | LONG | 4796.28 | 4783.87 | 4814.90 | 3.57 | FILLED_LOSS | 4/16 16:52 | sl_hit | -1.000 |
| 2026-04-17_ny_1315 | LONG | 4793.86 | 4776.93 | 4819.26 | 5.18 | FILLED_WIN | 4/17 13:16 | tp1_hit | +1.500 |
| 2026-04-17_ny_1330 | LONG | 4743.87 | 4732.01 | 4761.66 | 5.19 | FILLED_WIN | 4/20 02:45 | tp1_hit | +1.500 |

## Aggregate stats

| Metric | Value |
|---|---|
| n | 11 |
| n_filled | 11 |
| n_wins | 8 |
| n_losses | 3 |
| n_never_filled | 0 |
| n_open_at_horizon | 0 |
| WR (filled-only) | 72.7% |
| Mean R (filled-only) | **+0.818R** |
| Sum R | +9.00R |

Because all 11 records filled, the alternative aggregations (`neverfilled=0` /
`neverfilled=-0.5`) collapse to the same number (+0.818R).

## Verdict band

**Verdict: GREEN.**

- Filtered mean R = **+0.818R** (>= +0.30R threshold)
- Filtered WR = **72.7%** (>= 50% threshold)

Both GREEN conditions met by wide margin.

## Comparison vs Stage 2.5 (n=4)

Stage 2.5 reported mean R = +0.25R, WR = 50% on the 4 historically-filled
records (using historical zero-buffer SL/TP parameters). The full-cohort
re-sim with current emissions delivers **+0.818R / 72.7% WR on n=11**, a
material upward revision driven by:

1. The 7 historically-rejected records all filled at the post-FA-2 entry/SL,
   and 6 of those 7 won (+1.5R each).
2. The post-FA-2 prompt produces non-zero `sl_buffer_applied` (range 3.57 - 5.19),
   widening SL by ~3.5-5.2 points and reducing wick-out losses.

## Stage 2.5 sanity check

All 4 originally-simulated records produce **matching outcome categories**:

| trade_id | Stage 2.5 outcome | New sim outcome | Match |
|---|---|---|---|
| 2026-04-15_ny_1415 | FILLED_WIN | FILLED_WIN | yes |
| 2026-04-16_london_0930 | FILLED_LOSS | FILLED_LOSS | yes |
| 2026-04-16_ny_1316 | FILLED_LOSS | FILLED_LOSS | yes |
| 2026-04-17_ny_1330 | FILLED_WIN | FILLED_WIN | yes |

**4 / 4 outcome match.** The new sim's realized R values differ slightly from
Stage 2.5 (e.g. Stage 2.5 had `1.4997` vs new `1.503` for `2026-04-15_ny_1415`)
because the post-FA-2 SL is ~3.5-5pts wider than the historical zero-buffer SL,
giving slightly different `tp1_distance / sl_distance` ratios.

## Notable observations

1. **Six of the 7 newly-simulated records WIN** at +1.5R. The FA-2 fix substantially
   improved this cohort's filtered R.
2. **`2026-04-17_ny_1330` fills only at Mon 4/20 02:45** (across the weekend).
   Friday 4/17 13:30+ price never reached limit=4743.87; Monday open M1 low
   was 4740.83. Within bar-count horizon (735 / 2880).
3. **All 6 Apr-15 LONGs share the same fill timestamp (4/16 17:40)** because they
   share entry=4777.43; price first broke that level on 4/16 evening.
4. **Apr-16 cohort (3 LONGs at 4796.28) all lose** — price filled at 16:52 then
   wicked SL by 17:40 in the same downside leg that ultimately produced the
   4/16 17:40 +1.5R LONG fills for the prior-day cohort. SL spread (3.57-3.87)
   was tighter than the wick excursion.

## Caveats

- Adverse-first M1 same-bar SL+TP resolution is conservative; intra-M1 tick
  data (not available) could flip a small number of close-call bars.
- Sim represents post-FA-2 prompt with `sl_beyond_ob` fix but **without** the
  multi-framework dispatch fix (separate branch). Post-multi-framework results
  may differ if the dispatch change re-routes any of these 11 records to a
  non-`ob_retest` framework.
- All 11 records are LONG (cohort=trending_bull). No SHORT-side validation.
- `sum_r = +9.00R` aggregates wins and losses without per-trade risk weighting;
  R is the only output dimension.
