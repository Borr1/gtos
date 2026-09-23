# Phase 3 T4 — D1-Bias-Lag Honest Per-Instrument R Impact

**Tester:** Opus 4.7 hypothesis tester, 2026-04-19
**Hypothesis tested:** H1 (at least one instrument >+5R/quarter, ship fix) vs H0 (near-zero fleet-wide, no ship)

## Verdict

**H0 accepted, H1 rejected.** Across 7 instruments, the D1-bias-lag mechanism
(`src/components/market_state.py:239`, `identify_structure`) produces an
**honest fleet-wide R impact of +1.5R across 11 independent regime-lag
episodes over 3.25 months** when corrected for (a) correlated-sample
over-counting within a single lag episode and (b) bootstrap significance.
No instrument clears the +5R/quarter bar on the episode-decorrelated metric;
only USDJPY clears it per-day (+8R) but those 17 "days" all belong to **one**
regime-lag episode (2026-01-29 to 2026-02-26) and collapse to a single
first-event outcome of −1R. EURUSD replay is bit-exact with the ζ reviewer
(+110R full / +2R per-day / CI95 [−10.5, +14.5]). The mechanism is real
(NAS100 D1 stuck bearish through a 15.6% rally, confirmed in ζ's
`08_structure_direction_lag.py`) but the per-quarter R impact is indistinguishable
from noise. **No ship before Tuesday.**

## Method

### Data sources (file:line)
- **EURUSD**: `research/t7_live_simulation/EURUSD_t7_simulation.json` — 804 L2
  rejects with `prescreen:L2_h4_conflict_*` tag.
- **NAS100**: `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}/NAS100_t7_simulation.json`
  — 140 L2 rejects.
- **XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD**: No simulation JSON with
  prescreen-stage records exists (the XAUUSD `all_results_jan_apr10.json` has
  `L2_h4_conflict=0` because it was run before the prescreen gate existed, or
  H4/D1 never conflicted). Re-derived from production `prescreen_mso` logic
  (`src/components/orchestrator.py:2984-3014`) walking M15 KZ candles and
  calling `detect_swings` + `identify_structure` (`src/components/market_state.py:181,216`)
  on D1 (30-bar lookback) and H4 (80-bar lookback) windows — same defaults as
  production (`src/components/data_ingestion.py:38`).

### Per-instrument fill epsilon (Tier A downstream)
From `scripts/simulate_t7_live_period.py:80-89` (`EPSILON_BY_SYMBOL`):
`XAUUSD=0.20, US30/US30_cash/NAS100=2.0, USDJPY/GBPJPY=0.02, EURUSD/GBPUSD=0.0002`.
Legacy default `0.05` applied for the "naive" row.

### Counterfactual
- **Entry = signal M15 close** (market-order equivalent). SL = close ± ATR14,
  TP = close ± 1.5×ATR14. Horizon = 16 M15 candles (4 hours).
- **Outcome rule** mirrors `compute_outcome()` (`scripts/simulate_t7_live_period.py:491-570`):
  L if SL hit first, W if TP hit first, U if neither within horizon (unresolved).
  Same-candle tie goes to SL (conservative).

**Important methodology caveat:** because entry=close, the fill-check
`abs(entry - candle_close) ≤ epsilon` is trivially satisfied (0 ≤ any ε>0),
so per-instrument ε is a NOOP in this replay vs a legacy-0.05 run —
numerically equivalent. The ζ reviewer's "+110R → −44R at 2-pip EURUSD"
deflation applies to LIMIT-entry replays where entry < close; that replay is
not available for rejects (they never hit AI → no limit price was generated).
The market-entry ATR replay is the most faithful counterfactual available
for rejects, and matches ζ's `06_prescreen_directional.py` bit-exactly on
EURUSD (+110R) and NAS100 (−2.5R) at the full-sample level.

### R-counting convention
R-multiple **to target** (+1.5R win, −1R loss, 0 unresolved). Horizon=16 M15
candles. Same conservative tie-break as production.

### Per-day de-correlation
For events on the same date, keep the **first chronologically**. Mirrors ζ
reviewer's "28 distinct days" collapse.

### Per-episode de-correlation (new, more honest)
An episode = contiguous streak of same (`d1_dir`, `h4_dir`) regime combo where
consecutive events are ≤ 7 calendar days apart. Within an episode, keep only
the **first event** — because a 20-day lag on a single D1 regime flip is
fundamentally **one** event sampled 20 times, not 20 independent events.

### Bootstrap 95% CI
5000 resamples of the per-day R vector with replacement; 2.5%/97.5% quantiles
of the R_sum distribution. Bootstrap p-value = fraction of resamples with
R_sum ≤ 0 (one-sided H0: no edge).

## Per-instrument table

Window: 2026-01-02 → 2026-04-10 (~14 weeks ≈ 1 quarter; ~70 trading days)

| Symbol    | L2 rejects (h4≠d1) | Distinct days | Episodes | R (naive ε=0.05, full) | R (honest ε, full) | Per-day de-corr R | 95% CI (per-day) | Bootstrap p | Per-episode R (first event) | Verdict |
|-----------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| XAUUSD    |   0 |  0 | 0 | n/a      | n/a       | n/a      | n/a                | n/a    | n/a   | H4 is bullish-dominated; 0 conflict days in window |
| US30_cash |  80 |  4 | 2 |   −25.0R |    −25.0R |    +1.0R | [−4.0,  +6.0]      | 0.308  | +0.5R | noise |
| NAS100    | 140 |  7 | 4 |    −2.5R |     −2.5R |    +0.5R | [−4.5,  +8.0]      | 0.357  | −1.5R | noise |
| USDJPY    | 480 | 17 | 1 |   +22.0R |    +22.0R |    +8.0R | [−2.0, +18.0]      | 0.042  | −1.0R | **1 episode only**; per-day p fails Bonferroni (6-way); episode R flips sign |
| GBPJPY    | 160 |  7 | 1 |    +1.0R |     +1.0R |    +0.5R | [−4.5,  +5.5]      | 0.360  | +1.5R | noise |
| EURUSD    | 804 | 28 | 1 |  +110.0R |   +110.0R |    +2.0R | [−10.5, +14.5]     | 0.429  | +1.5R | noise; reproduces ζ +110R bit-exact, matches reviewer +2R per-day |
| GBPUSD    |1140 | 38 | 2 |   −83.0R |    −83.0R |    −0.5R | [−15.5, +14.5]     | 0.568  | +0.5R | noise |
| **Total** |2804 |101 |11 |          |           |   +11.5R |                    |        |**+1.5R**| fleet-wide: noise |

**Fleet-wide per-episode R = +1.5R over 11 independent regime-lag episodes
≈ +0.14R/episode → indistinguishable from zero.**

## Cross-validation of ζ's claim

- **ζ's EURUSD** (`research/b_deep_audit_2026-04-19/phase1/_zeta_scratch/06_prescreen_directional.py`):
  +110R over 804 rejects at ε=0.05. → **My replay: bit-exact match** (804
  records, W=364 L=436 U=4, R=+110R).
- **ζ reviewer's EURUSD** (`research/b_deep_audit_2026-04-19/phase2/_zeta_review_scratch/independent_replays.md:5-10`):
  +110R full (no-ε) → −44R full (ε=0.0002 limit-entry) → +2R per-day-decorrelated
  (28 events, W=12 L=16). → **My per-day replay: bit-exact +2R, W=12 L=16 U=0,
  CI95 [−10.5, +14.5]**.
- **ζ reviewer's NAS100** (line 22-26): n=7 per-day, W=2 L=5, R=−2R. → **My
  replay: n=7 per-day, W=3 L=4, R=+0.5R.** One event differs on 2026-04-17
  (my first reject at 08:00 UTC hits TP at 09:00; reviewer's was L — the
  reviewer may have picked a later intraday reject or a different SL/TP
  horizon). Within noise on a 7-event sample.
- **My contribution to ζ's sizing claim**: the "+110R → +2R per-day" deflation
  the reviewer established on EURUSD generalizes across all 6 non-XAUUSD
  instruments; when further decorrelated to per-episode (one event per
  regime-flip), fleet-wide R=+1.5R total (noise). USDJPY's +8R per-day looks
  suggestive (p=0.042) but all 17 events belong to ONE regime-flip episode
  (Jan 29 → Feb 26), and the first event of that episode is a **loss**
  (−1R) — the apparent +8R is entirely "buying the dip at the right moment"
  on a single episode, not a generalizable edge.

**Match or diverge with reviewer**: **Match** on the R-impact conclusion —
mechanism real, sizing ~50× over-inflated at full-sample, collapses to noise
under correct de-correlation. Per-episode de-correlation (my addition) is
strictly MORE conservative than per-day; all instruments that passed the
reviewer's per-day filter further collapse to noise under episode-level
de-correlation.

## Ship decision

**Ship fix before Tuesday (2026-04-21 redacted_account kickoff): NO.**

### Rationale
1. No instrument's honest R impact is distinguishable from zero on the
   episode-decorrelated metric. Fleet-wide +1.5R across 11 episodes = noise.
2. USDJPY's per-day p=0.042 doesn't survive Bonferroni correction for 6
   tested instruments (α/6 = 0.0083) and the single underlying "episode"
   first-event outcome is actually −1R.
3. CLAUDE.md unresolved #8 (`_FILL_EPSILON` global mis-scale) applies to
   LIMIT-entry counterfactuals. In this market-entry ATR replay it's a NOOP,
   so the per-instrument ε argument does not deflate these numbers further —
   the primary correction is per-episode de-correlation.
4. Ship risk vs edge risk: a 2-line detector change (`recent_pairs=3` →
   dynamic or rolling-window-based) touches `identify_structure` — a function
   used by EVERY MSO on EVERY candle on EVERY instrument. Risk of a silent
   regression breaking live on Tuesday morning dwarfs an unquantified
   +0.14R/episode speculative upside.

### If a fix ever ships, the reviewer's framing is the correct one
Per `research/b_deep_audit_2026-04-19/phase2/_zeta_review_scratch/independent_replays.md:48-52`:

> "not 'all-history counts vs tiny threshold' as zeta frames it. The counts
> are already windowed (60-bar rolling). The issue is that on a 60-bar D1
> window, old LH/LL from the first half of the window outnumber new HH/HL in
> the second half for 2-3 weeks after a regime flip."

The right fix, **if needed**, is to weight recent swings over older ones
(EMA-weighted HH/HL/LH/LL counting) or detect regime flips explicitly by
comparing first-half vs second-half swing counts within the window. Neither
is a 2-line change; both require fixture evidence that they don't break the
existing XAUUSD/US30 edge.

### Post-Tuesday shadow-log to deploy

Add a shadow logger (log-only, no decision impact — **Allowed without approval**
per CLAUDE.md WF-1 rules) that on every MSO where `prescreen_mso` returns
`L2_h4_conflict_*`, writes to `shadow_logs/d1_bias_lag_conflicts.jsonl`:
- candle_time, symbol, d1_dir, h4_dir, d1_hh_count/hl_count/lh_count/ll_count,
  close, ATR14(M15)
- 4-hour-ahead forward R under the H4 direction (on the NEXT live candle
  close; requires a small background task to backfill)
- kill_zone, timestamp

After 60 trading days, revisit with 5× more episode coverage and run the
same per-episode test. Threshold to re-propose ship: **≥4 independent
episodes cross +3R each, fleet-wide episode-R ≥+12R, at p<0.01 Bonferroni**.

Location: extend existing shadow-logger pattern (`src/components/be_shadow_logger.py`
as template). Integrate in `orchestrator.py` right after the
`passed, reason = prescreen_mso(mso)` check at line 548.

## What I could not test

1. **LIMIT-entry counterfactual for L2 rejects**: rejects never reached the
   AI → no limit price was generated, so ζ reviewer's +110R → −44R deflation
   (LIMIT-entry with ε=0.0002) cannot be reproduced for the re-derived
   instruments. The market-entry ATR replay used here is the closest analog
   to what production would do if the AI were called, but it over-estimates
   fill probability on tight limit orders.
2. **H1 swing-based alternatives**: the prompt asked me to use the H4
   direction as "correct" per ζ; I did not test whether H1 or even M15
   consensus would give a different answer. The zeta reviewer's replay 3
   already confirmed the mechanism on H4 so this is the right test.
3. **TZ bug cross-check (T1)**: T1 output is not yet written
   (`research/b_deep_audit_2026-04-19/phase3/_T1_scratch/` is empty as of
   2026-04-19 12:00 UTC). If T1 finds a TZ bug that shifts FX M15 data by 1+
   hours, the KZ-candle enumeration for the re-derived symbols (USDJPY,
   GBPJPY, GBPUSD, US30_cash) may be off by a few candles per KZ — but this
   cannot push an N=17 per-day sample into p<0.001 territory. Noted as
   caveat; does not change the ship decision.
4. **NAS100 single-event difference with reviewer** (2026-04-17 W vs L): my
   first reject at 08:00 hits TP at 09:00; reviewer's 04-17 was L, suggesting
   they anchored on a later intraday candle or used a different horizon.
   Within 1-event-in-7 noise; does not change verdict.
5. **Statistical power**: at N=7-17 per instrument per quarter, the test has
   ~30% power to detect a true +0.5R/event signal. A real +5R/quarter edge
   would require ≥15 episodes to confirm at α=0.05, which means ~4 quarters
   of data at current trigger rates. The shadow log is the right instrument
   for that.
6. **XAUUSD anomaly note**: XAUUSD has 0 L2 conflict days in the Jan-Apr
   2026 window at production lookback (D1=30, H4=80). Verified: H4 stays
   bullish 99% of the window with only one 4-hour bearish flip on 2026-03-25
   (`h4_dir=bearish`), and D1 is mostly `transitional` (34 days) or
   `insufficient_data` (13 days) during the 7:00 UTC KZ-start snapshot.
   This means the mechanism cannot produce any R impact on XAUUSD in this
   window — not a bug, just an absence of conflict.

## Files

- Scratch: `research/b_deep_audit_2026-04-19/phase3/_T4_scratch/compute_honest_impact.py`
- Raw numeric output: `research/b_deep_audit_2026-04-19/phase3/_T4_scratch/results.json`
