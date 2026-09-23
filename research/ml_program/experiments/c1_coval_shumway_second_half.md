# C-1: Coval-Shumway 2005 Second-Half-of-Session OB-Retest A/B Test

**Experiment ID:** C-1 (MASTER_BACKLOG.md `C-1` / HYPOTHESIS_BACKLOG.md `H-15`)
**Bundle:** B-8 quick-win
**Author:** Phase 4 dispatch agent (Opus 4.7, max effort)
**Date:** 2026-04-29
**Status:** PRE-REGISTERED → executed (single pass; no peeking)

---

## 1. PRE-REGISTERED HYPOTHESIS (written BEFORE looking at any second-half data)

> "OB-retest entries in the second half of a kill-zone (split at the kill-zone midpoint per CLAUDE.md kill-zone schedule) achieve realized-R mean ≥ +0.05R higher than first-half entries on the post-2022-2023-backfill cohort (n ≈ 2,326), with stationary block bootstrap p < 0.05 (DSR-corrected for ≈10 stratifications). Sign of the difference must be positive on ≥3 of 4 effective instrument groups (XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY)."

**Source mechanism (Coval-Shumway 2005 "Do Behavioral Biases of Investors Affect the Prices They Pay?"):** Distressed proprietary CBOT traders who lose money in the morning session take ~16% more above-average risk in the afternoon, accumulate larger inventory, and their inventory-driven prices revert FASTER than informed-flow prices. The empirical analog: distressed counterparty flow concentrates in the second half of a session. GTOS's OB-retest edge — exploiting stop-cascade mean-reversion at the last opposing pre-cascade candle — should therefore be MORE concentrated in the second half of any kill zone, after distressed counterparty flow has had time to accumulate.

**Operative GTOS prediction (testable from existing data):** Mean realized-R for OB-retest entries in second-half-of-KZ > first-half-of-KZ, on a per-instrument-group basis.

**This hypothesis is the standalone Tier-1 element of B-8 quick-win bundle.**

---

## 2. METHODOLOGY (designed BEFORE looking at outcome data)

### 2.1 Data sources (verified before use)

1. **Primary cohort** (2022-2023 mechanical):
   - File: `data/historical_2022_2023/trade_cohort.csv`
   - Rows: 1,798 mechanical OB-retest trades (all from `f11_mechanical` source)
   - Schema: `trade_id, source, date_iso, symbol, instrument_class, direction_long_short, kill_zone, hour_utc, day_of_week, framework, regime_tag, ob_distance_atr, ob_age_candles, displacement_quality_score, touch_count, realized_r, win_label, ...`
   - Date range: 2022-01-04 → 2024-02-19
   - Symbols: XAUUSD (394), XAGUSD (418), GBPUSD (400), USDJPY (376), NAS100 (210)
   - Within-KZ rows: 1,242

2. **Secondary cohort** (K54 v1 modeler dataset, 2024+):
   - File: `research/ml_program/models/k54_v1_features_full.csv`
   - Rows: 582 (mix: `f11_mechanical` 2024 backfill + `unified_csv` Q1.3 + `trade_index` 129)
   - Date range: 2024-04-01 → 2026-04-24
   - Symbols: XAUUSD, GBPUSD, USDJPY, NAS100, US30_CASH, GBPJPY
   - Within-KZ rows: 409

3. **Combined deduped cohort** (by `trade_id`):
   - Rows: 2,380; within-KZ: 1,651
   - This is the test population (close to dispatch's n≈2,326 expected; difference comes from `kill_zone == "other"` exclusion).

### 2.2 Kill-zone midpoint definition (UTC; from CLAUDE.md)

| Symbol | KZ | Window | Midpoint | First-half hours | Second-half hours |
|---|---|---|---|---|---|
| XAUUSD | London | 07:00-10:30 | 08:45 | {7, 8} | {9, 10} |
| XAUUSD | NY | 13:00-17:00 (skip 13:00-13:15) | 15:00 | {13, 14} | {15, 16} |
| US30 / US30_CASH | London | 08:00-10:30 | 09:15 | {8, 9} | {10} |
| US30 / US30_CASH | NY | 13:30-16:00 | 14:45 | {13, 14} | {15} |
| USDJPY | London | 07:00-09:30 | 08:15 | {7, 8} | {9} |
| USDJPY | NY | 13:00-15:30 | 14:15 | {13, 14} | {15} |
| USDJPY | Tokyo | 00:00-03:00 | 01:30 | {0, 1} | {2} |
| GBPJPY | London | 07:00-09:30 | 08:15 | {7, 8} | {9} |
| GBPJPY | NY | 13:00-15:30 | 14:15 | {13, 14} | {15} |
| GBPJPY | Tokyo | 00:00-03:00 | 01:30 | {0, 1} | {2} |
| GBPUSD | London | 07:00-12:00 | 09:30 | {7, 8, 9} | {10, 11} |
| GBPUSD | NY | 13:00-15:30 | 14:15 | {13, 14} | {15} |
| XAGUSD | London (proxy XAUUSD) | 07:00-10:30 | 08:45 | {7, 8} | {9, 10} |
| XAGUSD | NY (proxy XAUUSD) | 13:00-17:00 | 15:00 | {13, 14} | {15, 16} |
| NAS100 | London (proxy US30) | 08:00-10:30 | 09:15 | {8, 9} | {10} |
| NAS100 | NY (proxy US30) | 13:30-16:00 | 14:45 | {13, 14} | {15} |

**Boundary rule.** Trades with `hour_utc < first-half-min` or `hour_utc > second-half-max` are dropped (outside the kill-zone window even though the cohort labels them with that KZ — defensive). Hour at exactly the midpoint hour falls into second-half (e.g., NY at hour 15 is second-half). All entries are at HH:00 UTC granularity (verified empirically — `df.date_iso.dt.minute.value_counts()` shows only `0`).

**Tokyo for non-JPY instruments.** XAGUSD/GBPUSD/XAUUSD/NAS100/US30_CASH labeled `tokyo` in cohort but their KZ schedule does not include Tokyo per CLAUDE.md. We exclude those rows from the test for those symbols (not in canonical KZ schedule).

### 2.3 Stratification design

Aggregate test on 1,651 within-KZ trades (post-window-filter), then stratified by:

1. **Per instrument group** (4 effective groups for sign-count gate):
   - GROUP_XAU = {XAUUSD, XAGUSD}
   - GROUP_INDEX = {NAS100, US30_CASH}
   - GROUP_GBPJPY = {GBPJPY}
   - GROUP_USD_FX = {GBPUSD, USDJPY}
2. **Per kill-zone** (London / NY / Tokyo).
3. **Per regime tag** (bullish / bearish / transitional).
4. **Per side** (LONG / SHORT).

### 2.4 Test statistic and inference

- **Statistic:** mean realized-R difference: `Δ = mean_R(second_half) - mean_R(first_half)`.
- **Stationary block bootstrap (Politis-Romano 1994):** B = 1,000 resamples. Block size = `max(5, ceil(1 / (1 - AR1)))` where AR1 is lag-1 autocorrelation of the realized-R series (sorted by `date_iso`); empirically near zero in trade-record series, so block size will hit the `max(5, …)` floor in most strata.
  - For each bootstrap replicate, sample blocks of contiguous rows (with replacement) until the resampled set matches each half's row count, then compute `Δ_b`. Two-sided p-value = 2 × min(P(Δ_b ≥ 0), P(Δ_b ≤ 0)) under the null shift `Δ = 0` (centered). Specifically: shift bootstrap distribution by mean to center at 0, compute p-value as `2 × min(mean(centered ≥ |Δ_obs|), mean(centered ≤ -|Δ_obs|))`. (Standard Romano paired-bootstrap centering.)
- **DSR (Bailey-Lopez de Prado 2014):** Apply Deflated Sharpe Ratio adjustment for the multiplicity of stratifications. Using a conservative trial-count of 10 (the dispatch brief's anchor; equals 1 aggregate + 4 group + 3 KZ + 3 regime − overlap). Effective trial count is justified in section 4.
- **PASS gates (per dispatch):**
  - Aggregate Δ ≥ +0.05R, AND
  - Aggregate stationary-bootstrap p < 0.05, AND
  - DSR-corrected p < 0.05, AND
  - Sign(Δ) > 0 in ≥ 3 of 4 effective instrument groups.
- **FAIL** if any gate not met → honest negative report.

### 2.5 Deviations / caveats logged BEFORE running

- **Hour resolution is HH:00.** The midpoint cuts (e.g., 08:45) cannot be applied at minute precision. The split is therefore at the integer-hour boundary nearest the midpoint, biased downward where the midpoint is :30 or :45 (so e.g. NY 13:30-16:00 midpoint 14:45 is implemented as first={13, 14} second={15}; trades at 14:45 would conceptually be "second half" but cohort logs them as 14, so they fall in first-half; this is a SLIGHT BIAS AGAINST the hypothesis, conservative).
- **Single-bar second-half windows** (US30 London, NAS100 London, USDJPY/GBPJPY London/NY/Tokyo, GBPUSD NY) reduce statistical power per-stratum. Aggregate test compensates.
- **Q1.3 cohort (`unified_csv` source, 110 rows)** has date-only timestamps, no hour. These rows are EXCLUDED from the per-half analysis (kept only for descriptive reference). Same for `trade_index` 33-row subset.
- **`f11_mechanical` cohort is mechanical OB-retest only** (no AI overlay) — this is the exact substrate for the "OB zone advantage" Coval-Shumway predicts.

---

## 3. RESULTS

(Filled in after running `scripts/research/c1_coval_shumway_audit.py`.)

### 3.1 Aggregate

| Stratum | n_first | n_second | mean_R_first | mean_R_second | diff | WR_first | WR_second | bootstrap_p | DSR_p | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| aggregate | 754 | 431 | +0.4390 | +0.4996 | +0.0605 | 60.7% | 60.6% | 0.4220 | 1.0000 | FAIL |


### 3.2 Per-instrument-group

| Stratum | n_first | n_second | mean_R_first | mean_R_second | diff | WR_first | WR_second | bootstrap_p | DSR_p | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| group_XAU_XAG | 328 | 230 | +0.5132 | +0.5459 | +0.0327 | 67.4% | 62.2% | 0.7370 | 1.0000 | FAIL |
| group_INDEX | 89 | 48 | +0.2046 | +0.4951 | +0.2905 | 48.3% | 60.4% | 0.1990 | 1.0000 | FAIL |
| group_GBPJPY | 16 | 10 | +0.3068 | +0.0000 | -0.3068 | 50.0% | 40.0% | 0.4000 | 1.0000 | FAIL |
| group_USD_FX | 321 | 143 | +0.4348 | +0.4615 | +0.0267 | 57.9% | 59.4% | 0.8530 | 1.0000 | FAIL |


### 3.3 Per-kill-zone

| Stratum | n_first | n_second | mean_R_first | mean_R_second | diff | WR_first | WR_second | bootstrap_p | DSR_p | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| kz_london | 371 | 206 | +0.4464 | +0.3775 | -0.0689 | 62.3% | 55.3% | 0.5500 | 1.0000 | FAIL |
| kz_ny | 309 | 191 | +0.4512 | +0.6354 | +0.1842 | 60.5% | 66.0% | 0.0900 | 0.9000 | FAIL |
| kz_tokyo | 74 | 34 | +0.3514 | +0.4758 | +0.1245 | 54.1% | 61.8% | 0.4760 | 1.0000 | FAIL |


### 3.4 Per-regime

| Stratum | n_first | n_second | mean_R_first | mean_R_second | diff | WR_first | WR_second | bootstrap_p | DSR_p | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| regime_bullish | 242 | 174 | +0.4814 | +0.4920 | +0.0106 | 60.3% | 59.2% | 0.9130 | 1.0000 | FAIL |
| regime_bearish | 150 | 115 | +0.5680 | +0.4653 | -0.1028 | 63.3% | 60.0% | 0.4470 | 1.0000 | FAIL |
| regime_transitional | 214 | 118 | +0.4125 | +0.5587 | +0.1462 | 56.5% | 63.6% | 0.3060 | 1.0000 | FAIL |


### 3.5 Per-side

| Stratum | n_first | n_second | mean_R_first | mean_R_second | diff | WR_first | WR_second | bootstrap_p | DSR_p | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| side_LONG | 456 | 213 | +0.3944 | +0.4635 | +0.0691 | 60.5% | 59.2% | 0.4720 | 1.0000 | FAIL |
| side_SHORT | 298 | 218 | +0.5074 | +0.5348 | +0.0274 | 61.1% | 61.9% | 0.8340 | 1.0000 | FAIL |


### 3.6 Verdict

- **Aggregate Δ (mean realized-R, second − first):** +0.0605R
- **Aggregate stationary-bootstrap p:** 0.4220
- **Aggregate DSR-corrected p:** 1.0000
- **Sign-count gate (sign(diff)>0 in instrument groups):** 3/4 (need ≥ 3/4)
- **PROMOTION VERDICT:** **FAIL**


---

## 4. INTERPRETATION + RECOMMENDATION

### 4.1 Verdict — **FAIL**

The pre-registered hypothesis fails. Despite a directionally favourable aggregate point estimate (+0.0605R), the stationary block bootstrap p = 0.4220 is far above the 0.05 threshold; the DSR-adjusted (Bonferroni proxy) p saturates at 1.0. The promotion gate requires PASS on (a) Δ ≥ +0.05R, (b) bootstrap p < 0.05, (c) DSR-p < 0.05, AND (d) sign-count ≥ 3/4. We pass (a) and (d), fail (b) and (c). **Coval-Shumway 2005's distressed-trader-flow prediction is not statistically supported in the GTOS OB-retest realized-R cohort at n = 1,185 within-KZ-window OB-retest trades.**

### 4.2 What the data actually shows (descriptive layer)

1. **Aggregate point estimate is in the predicted direction** (+0.0605R), but the standard error is large enough that we cannot reject the null at any conventional confidence level. With n = 1,185 and an observed difference of ~0.06R against a per-trade R standard deviation of ~1.0R, the implied SE is ~0.07R, and the 95% CI on Δ contains zero by a wide margin.
2. **NY kill-zone is the strongest sub-cell** (Δ = +0.184R, p = 0.090). This is the only stratum to clear the bootstrap-p borderline-suggestive bar. This is *interesting* because:
   - NY kill-zone is the second session of the trading day in UTC — by the time NY opens (13:00 UTC), London traders have had ~6 hours to accumulate disposition-effect-driven losses.
   - The Coval-Shumway prediction was originally about *afternoon-session* CBOT trading (post-1pm Chicago = post-19:00 UTC) on the floor, where prop-trader morning-session losses fed afternoon revenge-trading. The cleanest analog in GTOS would be *NY-session-second-half-after-London-volatility*; the +0.184R point estimate is the largest in the table, and the p = 0.09 is suggestive but not promotion-grade.
3. **London kill-zone goes the wrong way** (Δ = −0.069R). This is mechanistically consistent with Coval-Shumway: London is the *first* major session of the global day (when only Tokyo traders are stressed), so distressed-flow accumulation is minimal — second-half London should NOT outperform first-half London much, if at all. Mild negative point estimate plus p = 0.55 → null.
4. **Transitional regime second-half outperforms** (+0.146R, p = 0.31). Suggestive but underpowered. *Mechanistically* this aligns with the F15 finding that decision-layer noise increases when the regime is transitioning — and Coval-Shumway predicts disposition-effect-driven distressed flow concentrates exactly where directional uncertainty produces losing positions.
5. **GBPJPY group goes wrong way** (Δ = −0.307R) but n = (16, 10) is too small to weigh — pure noise floor (one extra winning trade flips sign).
6. **No regime × KZ interaction was tested** (would be > 10 trials); leaving for K54 v3 if the directional pattern survives a higher-N replication.
7. **First-half WR ≈ second-half WR** (60.7% vs 60.6% aggregate). The small first-half/second-half R-difference comes from the magnitude of the realized R distribution (likely longer holds → larger MFE-to-realized capture), not from a hit-rate difference. This is *consistent* with Coval-Shumway (price reverts further when distressed flow is larger) but not with a simple hit-rate edge.

### 4.3 Why the directional signal failed to clear significance

Three plausible explanations, in approximate order of likelihood:

1. **Per-trade realized-R variance is too high relative to the population effect size.** With per-trade SD ≈ 1.0R and n ≈ 1,185 split (754, 431), detecting a Δ of even +0.10R requires p ≈ 0.05 on raw bootstrap (need |t| ≈ 1.96 → effect ≈ 0.10R observed). The observed +0.06R is at exactly half of the minimum detectable effect at this n. **Conclusion: this experiment was statistically underpowered for a +0.05R-magnitude claim, even before DSR correction.**
2. **Hour granularity (HH:00) coarsens the midpoint split.** Midpoints at :30/:45 had to be assigned to integer-hour windows; in 4 of 12 (sym × KZ) cells the second-half collapses to a single integer hour. The 754/431 imbalance reflects this: most KZ-time-spans put more integer-hours in the first half. The single-hour second-half windows have less internal time-of-day variation to drive the Coval-Shumway accumulation effect.
3. **The Coval-Shumway mechanism may not transmit to the OB-retest entry channel.** Coval-Shumway 2005 measured *price impact reversion* on prop-trader inventory. GTOS's edge is *zone selection at structural pivots*; the disposition-effect-driven counterparty pool is the substrate Group E F-2 identifies as the operative mechanism, but the time-of-session axis may not be the right slicing axis to extract the effect — *intra-day session-stress proxies (running RV, intraday DD)* may be the better axis. (See H-E16 in HYPOTHESIS_BACKLOG.md for the high-RV variant.)

### 4.4 Recommendation

**Do NOT add `is_second_half_of_kz` as a binary feature to K54 v3.** The hypothesis fails its pre-registered promotion gate; the K54 v3 catalog should not absorb features that do not clear DSR + bootstrap-p discipline (per `feedback_paired_fixed_hp_discipline`).

**Two follow-ups are warranted (low cost):**

1. **C-1b — NY-only retest at higher precision.** The NY KZ p = 0.090 is the only borderline-suggestive cell. If a finer-grained timestamp (M15 / M1) is available for the NY second-half cohort (XAU NY hour ∈ {15, 16}), re-run with minute-level midpoint splits — the integer-hour coarsening means the current test biases against the hypothesis on NY (mid 15:00 puts hour 15 trades into "second half" en bloc rather than splitting them). Estimated cost: low (rebuild NY-cohort timestamps from `live_evaluations/` H1-reconstructed entries).
2. **C-1c — high-RV-conditioned variant (H-E16 from HYPOTHESIS_BACKLOG.md).** Coval-Shumway's mechanism is fundamentally *stress*-driven, not *time-of-session*-driven. The cleaner test is "OB-retest WR conditional on current-day realized vol decile." Decile 9-10 (highest stress) should outperform decile 1-2 (calmest). This uses the same data (already-loaded MT5 H1 series) plus a single rolling-RV computation. Falls under V-1 in MASTER_BACKLOG.md (realized-vol-percentile feature).

**Both follow-ups are still B-tier, not A-tier.** Phase 2 should keep K54 v3 architectural priorities (K-4 micro-price, K-5 W-unit normalization, K-7 stop-cluster, K-8 power-law-decayed OB-age, K-12 meta-labeling) ABOVE this thread.

### 4.5 What this test rules out

- The simplest version of Coval-Shumway transmission ("just-second-half-of-kz") at a +0.05R promotion bar.
- The need to split intraday-time into a binary feature for K54 v3 at 2026-04-29.
- The hypothesis that GTOS's OB-edge has a strong directional time-of-day asymmetry detectable at H1 hour resolution at n = 1,185.

### 4.6 What this test cannot rule out

- A real but smaller-effect-size Coval-Shumway transmission (Δ ∈ [0.02R, 0.05R]) that would require n > 5,000 to detect.
- A NY-specific transmission (the +0.184R point estimate at p = 0.09 is consistent with this and would clear gates at a 2x expansion of the cohort if signed signs hold).
- A high-RV-conditioned transmission (the F-2 / H-E16 variant), which we did not test here.
- A continuous "time-since-KZ-open" feature — the binary midpoint split discards information; a continuous feature could survive.

### 4.7 Honest negative report — to KILLED_HYPOTHESES.md

This experiment is killed in its **binary `is_second_half_of_kz` form**. The C-1b (NY-only finer precision) and C-1c (RV-conditioned) variants remain alive in MASTER_BACKLOG.md and HYPOTHESIS_BACKLOG.md as Phase 2 candidates.

---

## 5. REPRODUCIBILITY

- Script: `scripts/research/c1_coval_shumway_audit.py`
- Output JSON: `research/ml_program/experiments/c1_coval_shumway_results.json`
- Random seed: `42` (numpy + python `random`).
- Bootstrap B = 1000.
- All input files locked at session start; no source code paths writable from this script.
