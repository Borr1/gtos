# Agent C — NAS_US30 Specialist Forensic Deep-Dive

**Date:** 2026-04-29
**Author:** Agent C — NAS_US30 specialist forensic
**Subscription-only (no Anthropic API spend). Read-only on production.**
**Inputs read:** saved booster `k54_v3_nas_us30_specialist.lgb`, `top_features.json`, `specialist_results.json`, `cpcv_paired_results.json`, `cross_period_results.json`, `meta.json`, `Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`, `architecture_ab.md` Q1.3, `group_c_asset_classes.md`, `group_b_microstructure.md` §6.6, scout `feature_matrix.parquet` (n=528, 1,247 features), 2022-2023 backfill (n=1,798, v1-schema), v1 features full CSV.
**Outputs in `research/ml_program/forensics/2026-04-29/`:**
- `agent_c_specialist_feature_importance.csv`
- `agent_c_specialist_vs_global_feature_diff.csv`
- `agent_c_specialist_per_period.csv`
- `agent_c_per_instrument_breakdown.json`
- `agent_c_specialist_cross_period.json`
- `agent_c_analogous_specialists.json`
- `agent_c_apples_apples_paired.json` (KEY FINDING)
- `agent_c_analogous_apples.json` (KEY FINDING)
- `agent_c_summary.json`
- `agent_c_k55_shadow_spec.md`

---

## TL;DR — verdict reversal

**The "+0.103 NAS_US30 specialist delta" reported in `specialist_results.json` is an aggregation artifact, not a real model superiority.** Under paired apples-to-apples per-path testing on the SAME K=4/N=2 NAS_US30 test folds, the specialist's mean AUC is 0.660 and the global K54 v3's is 0.667 — paired delta -0.007, t-p 0.93, DSR-p 0.999. **There is no statistically detectable specialist edge on NAS_US30.**

The +0.103 in production was produced by comparing two pool-averaged AUCs at different aggregation depths: specialist averages ~3 predictions/row (CPCV K=4 N=2, 6 paths) → pooled AUC 0.601; global averages ~5 predictions/row (CPCV K=6 N=2, 15 paths) → pooled AUC 0.498. **Different averaging depths over correlated noise produce different pool-AUCs even when the underlying per-fold AUCs are similar.** The honest per-path-mean numbers (specialist 0.641 vs global 0.595) give a smaller +0.046 gap, and the paired apples-to-apples comparison eliminates that residual entirely.

The literature-driven mechanism hypotheses (Group C dealer-gamma, Group B OPEX-Friday, Mag-7 concentration) **are not what the model actually learned.** Round-number, OPEX, gamma-proxy, Mag-7, and stop-cluster features carry **0.00% of the specialist's gain**. The top-3 features (vol h1 range / 200, micro h4 body ratio, M15 swing-low distance) are vanilla volatility/microstructure/structure features with no asset-class-specific mechanism.

**The K55-shadow ship recommendation is therefore not justified by the evidence the postmortem cited.** The forensic does not by itself reject the K55-shadow deploy — but the production case for it (specialist +0.103) is invalid, and any deploy must rest on a re-derived case (e.g., per-path delta CIs that exclude zero, or a properly-controlled mechanism feature set, or a cohort-expanded re-test).

---

## 1. Per-feature attribution on the saved specialist

Loaded saved booster (`k54_v3_nas_us30_specialist.lgb`); extracted gain + split feature importance.

### 1.1 Top-12 features by gain (specialist)

| rank | gain | gain % | family | feature |
|---:|---:|---:|---|---|
| 1 | 143.4 | 33.6% | volatility | `vol__h1_range_over_mean_200` |
| 2 | 81.1 | 19.0% | microstructure | `micro__last_bar_body_ratio_h4` |
| 3 | 73.7 | 17.3% | structure | `struct__M15__dist_to_nearest_swing_low_atr` |
| 4 | 35.1 | 8.2% | structure | `struct__H1__ob_max_touch_count__lb100` |
| 5 | 28.3 | 6.7% | liquidity (volcluster) | `liq__liq_M15_volcluster_dist_abs_atr` |
| 6 | 26.7 | 6.3% | microstructure | `micro__vol_momentum_h1` |
| 7 | 17.6 | 4.1% | liquidity (other) | `liq__liq_H1_dist_eqh_abs_atr` |
| 8 | 9.3 | 2.2% | volatility | `vol__m15_sq_return_autocorr_lag5_w200` |
| 9 | 2.9 | 0.7% | structure | `struct__H4__last_swing_velocity_atr_per_bar__lb20` |
| 10 | 2.7 | 0.6% | time_session_calendar | `ts__t_day_of_month_cos` |
| 11 | 2.7 | 0.6% | volatility | `vol__m15_realized_skew_50` |
| 12 | 2.6 | 0.6% | structure | `struct__H1__nearest_ob_touch_count__lb100` |

The remaining 88 features in the specialist's input set carry 0.0% gain (deadweight passthroughs from the path-0 top-100 screen). **The specialist effectively trades on 12 features.** Top-3 alone account for 70% of decision logic.

### 1.2 NAS-specific (specialist gain pct minus global K54 v3 gain pct)

`agent_c_specialist_vs_global_feature_diff.csv` columns: `feature, gain (specialist), split (specialist), gain_pct (specialist), global_gain_pct, spec_minus_global_pct`.

The features the specialist over-weights vs the global model:

| spec_pct | global_pct | spec - global | feature |
|---:|---:|---:|---|
| 33.6% | 7.8% | +25.9% | `vol__h1_range_over_mean_200` |
| 19.0% | 0.65% | +18.4% | `micro__last_bar_body_ratio_h4` |
| 17.3% | 1.0% | +16.3% | `struct__M15__dist_to_nearest_swing_low_atr` |
| 8.2% | 0.6% | +7.7% | `struct__H1__ob_max_touch_count__lb100` |
| 6.7% | 1.1% | +5.6% | `liq__liq_M15_volcluster_dist_abs_atr` |
| 6.3% | 2.3% | +4.0% | `micro__vol_momentum_h1` |

These are **not** mechanism-grounded NAS features. They are general OB / vol / microstructure features that happen to be over-weighted in the small-n NAS specialist fit because the screen handed them disproportionate gain in path-0 of the global pipeline (which biased the spec_features list toward features that fit ALL data, not NAS specifically).

### 1.3 Mechanism feature audit (the `group_c_asset_classes.md` story)

| keyword class | n features in spec | total gain % in spec | top feature gain % |
|---|---:|---:|---:|
| round_number | 1 | 0.00% | 0.00% |
| OPEX (incl. quarterly) | 5 | 0.00% | 0.00% |
| gamma_proxy / GEX / VIX1D | 0 | n/a | n/a |
| Mag-7 / concentration | 0 | n/a | n/a |
| stop_cluster (Osler / k7) | 0 | 0.00% | 0.00% |

**Zero gain from any of the literature-cited NAS-specific mechanisms.** The Group C dealer-gamma + Mag-7 concentration story (paper rank #9 Barbon-Buraschi 2021, paper rank #19 Schwab/S&P concentration), and the Group B §6.6 OPEX-Friday + daily MM-gamma-sign feature, are not what the specialist learned. Either:
1. The mechanism is real but un-instrumented (no gamma/GEX features in the feature catalog); the specialist learned proxy patterns that are not the mechanism. Or:
2. There is no NAS-specific mechanism captured in the data, and the specialist's apparent edge is statistical noise from the small-n cohort-fit + pool-aggregation artifact.

The apples-apples result in §5 below points strongly to #2.

---

## 2. Per-period stability (per-quarter LOQO + cohort breakdown)

### 2.1 Cohort temporal extent — critical structural finding

| Slice | n |
|---|---:|
| NAS_US30 total in v3 cohort | 113 |
| NAS_US30 in 2022 | 0 |
| NAS_US30 in 2023 | 0 |
| NAS_US30 in 2024 | 0 |
| NAS_US30 in 2025 | 0 |
| **NAS_US30 in 2026Q1 (Jan-Mar)** | **93** |
| **NAS_US30 in 2026Q2 (Apr 1-24)** | **20** |
| Date range | 2026-01-05 to 2026-04-24 |

The NAS_US30 specialist is fit and tested entirely within a 4-month 2026 window. **Per-year stability is undefined** — only one year (2026) in the cohort. Per-quarter LOQO is degenerate because:
- LOQO holding out 2026Q1 means training on n=20 (Q2 only), which is below the 30-row floor.
- Only LOQO holding out 2026Q2 is meaningful: train on 93 (Q1), test on 20 (Q2). AUC = 0.753 — but this is a single 20-row holdout with WR=0.45, n_pos=9. 95% CI on AUC at n=20 is ~±0.20; the 0.75 is statistically indistinguishable from 0.55.

### 2.2 Per-quarter LOQO results

| Held-out quarter | n_train | n_test | Test WR | Specialist AUC | Verdict |
|---|---:|---:|---:|---|---|
| 2026Q1 | 20 | 93 | — | (skipped; train < 30) | indeterminate |
| 2026Q2 | 93 | 20 | 0.45 | 0.753 | uninterpretable at n=20 |

### 2.3 NAS_US30 win-rate by year

| Year | n | WR |
|---|---:|---:|
| 2026 | 113 | 0.513 |

A balanced cohort (between 0.40 and 0.60 WR), so the AUC test is not bias-inflated by class imbalance.

---

## 3. Per-instrument breakdown (NAS100 vs US30_CASH)

### 3.1 Specialist AUC on each sub-cohort (CPCV K=4 N=2)

| Instrument | n | WR | Spec AUC (CPCV pooled) | per-path mean AUC | per-path std |
|---|---:|---:|---:|---:|---:|
| NAS100 | 51 | 0.569 | **0.379** | 0.472 | 0.072 |
| US30_CASH | 62 | 0.468 | **0.462** | 0.417 | 0.100 |

**The specialist's per-instrument pooled AUC is 0.379 (NAS100) and 0.462 (US30_CASH) — both BELOW random.** The 0.601 pooled AUC on the combined NAS+US30 cohort is therefore not the average of the two sub-AUCs. It exists because:
- NAS100 win-rate (0.569) is higher than US30 (0.468).
- The specialist learned to score NAS rows higher than US30 rows on average.
- When the cohorts are pooled, this side-of-instrument bias creates rank ordering that produces AUC > 0.5 at the cohort level, even though within each instrument the model has no discrimination.

This is a **classic Simpson's paradox**: high pooled AUC, low per-stratum AUC. The specialist is exploiting the WR difference between NAS100 and US30_CASH (10pp gap), not within-instrument predictive structure.

### 3.2 Top-10 feature overlap between NAS100 vs US30_CASH

`agent_c_per_instrument_breakdown.json`:

- Jaccard(top-10) = **0.053** (1 of 19 features shared) — `vol__h1_range_over_mean_200` is the only common one.
- NAS100 unique top-10: `struct__M15__fvg_mean_size_atr__lb20`, `struct__H1__nearest_ob_signed_atr__lb100`, `liq__liq_round_50p0_dist_above_ticks`, `vol__h1_range_over_mean_50`, `liq__liq_H1_bars_since_sweep_any`, `struct__M15__nearest_bb_age_bars__lb100`, `struct__H1__ob_mean_depth_atr__lb20`, `vol__h4_garch_persistence_lag1_w20`, `micro__last_bar_body_ratio_h4`.
- US30_CASH unique top-10: `micro__lower_body_lb20_m15`, `ts__t_days_to_nearest_nfp_abs`, `ts__t_hour_of_week_sin`, `vol__h4_range_over_mean_20`, `ts__t_hour_of_week_cos`, `struct__M15__dist_to_swing_band_atr`, `ts__t_days_to_nearest_holiday_signed`, `micro__last_bar_upper_wick_ratio_h4`, `struct__H1__nearest_ob_depth_atr__lb20`.
- **Shared:** `vol__h1_range_over_mean_200` only.

Conclusion: **NAS100 and US30_CASH are NOT a coherent statistical block at the feature level.** They share one volatility regime feature; everything else is disjoint. The "NAS_US30" specialist is two essentially independent small-n problems (n=51 + n=62), neither of which has internal predictive structure (pooled AUC < 0.50 on each), bundled together by a WR-spread that the model exploits as a side-of-instrument cue.

This refutes the Group C "NAS+US30 share US-equity flow / dealer-gamma / LETF rebalancing" cohesion hypothesis at the data level. They share volatility-regime alignment (range_over_mean_200), but not the mechanism layer the literature suggested.

---

## 4. Cross-period robustness on NAS_US30 specialist

Only v1-schema (17 features) is feasible for cross-period because the 2022-2023 backfill has no v2-feature catalog computed.

### 4.1 Direction A — train 2022-2023 backfill (NAS100 only) → test 2024-2026 NAS+US30

- Backfill NAS_US30: n=210, **but 100% NAS100, 0 US30_CASH** (the backfill was constructed without US30 data; date range 2022-10-21 to 2024-02-15).
- Test: 2024-2026 NAS_US30 (n=113).
- **Pooled AUC test = 0.624** (lift +0.095 vs anchor 0.5286 v1 baseline).
- Per-instrument: NAS100 0.666, US30_CASH 0.596.

This is the **only** cross-period direction that shows positive lift. Note critical caveats: (a) v1-schema only — does NOT validate K54 v3 features cross-period; (b) train cohort is NAS100-only — the model never saw a US30 row in training but predicts on US30 in test. The fact that US30 generalization (0.596) is positive despite zero training US30 rows is consistent with the v1 features (hour, day, OB distance, etc.) being NAS100/US30 generic at the M15 level. This argues that **a v1-schema GENERAL model trained on the rich 2022-2023 cohort generalizes to NAS+US30 2026**, NOT that "the NAS+US30 specialist mechanism transfers".

### 4.2 Direction B — train pre-Q2 2026 NAS+US30 → test Q2 2026 NAS+US30 (v1-schema)

- n_train=93, n_test=20.
- AUC test = **0.379** — far below random.
- Specialist's apparent stability on the training period does NOT survive a 1-month forward test.

### 4.3 Direction C — train Q2 2026 NAS+US30 → test pre-Q2 2026 NAS+US30 (reverse, v1-schema)

- n_train=20, n_test=93.
- AUC test = 0.511 — random.

### 4.4 Direction D — H1 2026 (Jan-Feb) → H2 2026 (Mar-Apr) NAS+US30 (v1-schema)

- n_train=62, n_test=51.
- AUC test = **0.269** — strongly below random (model's signal inverted).

### 4.5 Cross-period verdict

The specialist is NOT cross-period robust under any feasible v1-schema test. Two of the three within-cohort splits show below-random performance:
- B (pre-Q2 → Q2): 0.379
- D (H1 → H2 by month split): 0.269

The single positive direction (A) is a 2022-2023 v1-feature general model — not a per-cohort specialist effect. The K54 v3 v3-feature specialist's cross-period lift is undefined because backfill has no v3 features. The c.ii within-2026 v3-feature test in the original `cross_period_results.json` shows lift = -0.076 (NAS_US30 v3=0.444 vs v1=0.520) — but n_train=0 NAS rows in pre-2026-01-01 cohort, so this is a degenerate test, not evidence either way.

**Bottom line on cross-period robustness:** the specialist's apparent edge is not detectable across any temporal split available within 2026; it is therefore not robust to time, and any future-period deploy must assume zero detectable cross-period stability.

---

## 5. Apples-to-apples per-path paired comparison (the headline)

### 5.1 Method

Same K=4/N=2 NAS_US30 CPCV folds (6 paths), purge=7d, embargo=1d. For each fold:
- **Specialist:** train LightGBM on NAS_US30 rows except test fold (n_train ~78), validate on last 10% of training, predict on test fold.
- **Global:** train LightGBM on ALL non-test rows of full 528-cohort, validate on last 10% by date, predict on the SAME NAS test fold.
- Both models use identical HP `{n_estimators: 200, max_depth: 3, lr: 0.05}` (the K54 v3 selected HP), identical feature set (path-0 top-100 spec_features), identical calibration step.
- Compare per-path AUC paired across the 6 folds.

### 5.2 Results

| Path | n_test | Test WR | Spec AUC | Global AUC | Δ (Spec - Global) |
|---:|---:|---:|---:|---:|---:|
| 0 | 56 | 0.482 | 0.684 | 0.534 | **+0.150** |
| 1 | 56 | 0.589 | 0.495 | 0.665 | **-0.170** |
| 3 | 56 | 0.464 | 0.700 | 0.759 | -0.059 |
| 5 | 57 | 0.544 | 0.760 | 0.709 | +0.051 |

(Paths 2 and 4 had non-overlapping train/test split structure that made one of the sets too small after purge/embargo; they were dropped under the standard CPCV protocol.)

| Stat | Specialist | Global | Paired Δ |
|---|---:|---:|---:|
| Mean AUC | 0.660 | 0.667 | -0.007 |
| Std AUC | 0.115 | 0.097 | 0.138 |

Paired t-test (specialist - global): **t = -0.099, p = 0.93.**
Wilcoxon signed-rank: stat 4.0, p = 0.875.
DSR-corrected p (N=200 trial budget): **0.999.**

**The specialist's per-path AUC is statistically indistinguishable from the global K54 v3's per-path AUC on the SAME NAS test folds. The specialist provides no detectable per-fold edge over the global model.**

### 5.3 Reconciling with the production +0.103 number

| Method | Specialist | Global | Δ |
|---|---:|---:|---:|
| Pool predictions (production) | 0.601 (avg of 3/path) | 0.498 (avg of 5/path) | **+0.103** ← phantom |
| Per-path AUC mean | 0.641 | 0.595 | +0.046 |
| **Apples-apples paired (same folds, same HP)** | **0.660** | **0.667** | **-0.007** |

The +0.103 production number conflated two different aggregation depths. When global predictions are averaged across 15 paths (each NAS row hit ~5 times), the variance reduction makes the pool-AUC less informative; when specialist predictions are averaged across 6 paths (each row hit ~3 times), the residual variance creates rank dispersion that helps pool-AUC. Compounding this, the specialist's K=4/N=2 paths and global's K=6/N=2 paths sample different temporal slices, so the noise structure they're averaging over is correlated differently.

The honest measurement (paired per-path on identical test folds) shows zero specialist edge.

---

## 6. Search for analogous specialists in other cohorts (apples-to-apples)

For each cohort, train a cohort-only specialist and a full-cohort global on the same K=4/N=2 paths (K=3/N=1 for GBPJPY n=62). Per-path delta paired across folds.

### 6.1 Per-path specialist vs global

| Cohort | n | n_paths | Spec mean AUC | Global mean AUC | Paired Δ | t-p | DSR-p |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NAS_US30** | 113 | 4 | 0.660 | 0.667 | **-0.007** | 0.93 | 0.999 |
| **XAU_XAG** | 215 | 5 | 0.541 | 0.582 | **-0.042** | 0.44 | >0.999 |
| **GBPJPY** | 62 | 3 | 0.559 | 0.572 | **-0.012** | 0.88 | 0.999 |
| **GBPUSD_USDJPY** | 138 | 5 | 0.503 | 0.582 | **-0.079** | 0.18 | >0.999 |

### 6.2 Verdict

**No cohort produces a per-path-paired-significant specialist edge over global K54 v3.** All four cohorts show *negative* paired deltas, meaning the cohort-only-trained specialist is consistently slightly worse than the global model on the same test folds. None survive paired t-test at any reasonable α; all DSR-p > 0.999.

The architectural premise of "Architecture B per-cohort specialists" is **not supported by the data under apples-to-apples evaluation**. The Q1.3 audit's `architecture_ab.md` claim (NAS_US30 +0.13 over k54_v2 per-group AUC, "the kind of structural finding the global model was averaging away") rests on the same pool-aggregation methodology as the K54 v3 specialist's +0.103. Both are likely artifacts.

This DOES NOT mean per-cohort specialists can never work — at sufficient cohort n (>500 per cohort), with proper cohort-specific feature engineering (currently absent), and with paired apples-to-apples evaluation, a real specialist edge could emerge. But on the current n=113 NAS_US30 cohort with the path-0-screened generic top-100 feature set and the fixed HP, there is no detectable specialist effect.

---

## 7. Mechanism hypothesis evaluation (Group C dealer-gamma + Group B OPEX-Friday)

The `group_c_asset_classes.md` Section 7 hypothesis (dealer-gamma sign as last-90-min momentum/reversal classifier, Mag-7 concentration as fragility amplifier) and `group_b_microstructure.md` §6.6 (OPEX-Friday morning gate + daily MM-gamma-sign feature) propose specific mechanisms.

The forensic finds:
1. **Zero gain from any mechanism feature in the trained specialist** (round_number, OPEX, gamma_proxy, Mag-7, stop_cluster all 0.00% gain). The specialist is not implementing any of these mechanisms.
2. **No gamma_proxy / GEX / VIX1D feature exists in the v3 feature catalog.** This is a literal data-level gap: the feature catalog has no instrument for the dealer-gamma mechanism. The specialist could not have learned it.
3. **OPEX/quarterly_opex features exist (5 in spec input set) but carry zero gain.** Either OPEX has no per-row predictive value at this n, or the trees never split on OPEX features because other features dominated.
4. **Round-number features (`liq__liq_round_50p0_dist_above_ticks` etc.) carry zero gain in specialist.** The Osler stop-cluster mechanism (Group B Tier-1) is in the catalog (closed-form K-7 `kw__k7_osler_stopcluster_proxy`) but contributes 0.00% gain on the specialist.

**Conclusion on mechanism evaluation:** The literature-driven mechanism hypotheses are **un-validated** by the trained specialist. The specialist's apparent per-path lift (which is itself an artifact, per §5) cannot be attributed to any mechanism the literature proposes. If a mechanism is at work, it is not instrumented in the current feature set.

The B7 hallucination memory (US30_cash 23.4% hallucination near round/OPEX-strike clusters) is also not explained by this specialist — its top features are vanilla volatility/structure, not round-number proximity.

---

## 8. K55-shadow deploy fitness verdict

### 8.1 Production case (per `Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` §4.1 + §7.3)

- Specialist AUC 0.6014 on n=113 NAS_US30 cohort
- Delta +0.103 over global K54 v3
- "Strongest single finding" / "the only K54-family component with statistically-defensible per-cohort lift"
- Recommended K55-shadow deploy at p ≥ 0.55 floor on NAS100 + US30_cash, 30-day shadow data, empirical promotion gate

### 8.2 Forensic re-evaluation

Each of the production case bullets:

1. **AUC 0.6014 pooled.** Confirmed (re-run). But pool-aggregation depth is non-comparable to global K54 v3. Per-path mean is 0.641; apples-to-apples vs global on same folds gives 0.660 spec / 0.667 global.
2. **Delta +0.103.** REFUTED — phantom artifact of K=4/N=2 vs K=6/N=2 different aggregation depths over correlated noise. Apples-apples paired delta = -0.007 (p=0.93, DSR-p=0.999).
3. **"Statistically-defensible per-cohort lift."** REFUTED — paired t-p = 0.93. DSR-p = 0.999. No detectable lift.
4. **Cross-period robustness.** Two of three within-2026 splits show below-random performance (B 0.379, D 0.269). The single positive cross-period direction is a v1-schema general-model train, not a NAS specialist.
5. **Per-instrument decomposition.** NAS100-alone AUC 0.379, US30_CASH-alone AUC 0.462 — the pooled 0.601 is a Simpson's paradox / between-instrument-WR-gap artifact.
6. **Mechanism interpretability.** The model's top features are general (vol/struct/microstructure), not the literature-cited NAS-specific mechanisms (dealer-gamma, OPEX, Mag-7, stop-cluster). Zero gain from any mechanism feature.

### 8.3 Verdict on K55-shadow deploy

**Do not ship K55-shadow on the strength of the production case.** The production case's +0.103 evidence is invalid; the forensic finds zero detectable specialist edge under proper paired methodology.

This does NOT mean K55-shadow is harmful — the proposal is shadow-only, no live execution, log-only signal collection. The cost of running a K55-shadow at p ≥ 0.55 on NAS100 + US30_cash for 30 days is ~zero (just log-write per CANDIDATE; no API spend). But the value is also questionable — the empirical promotion gate would need to detect a real signal in noisy n~10-20 trades over 30 days, which at the small effect sizes implied by the forensic is a low-power test.

**If CEO wants to ship K55-shadow as cheap insurance:**
- Acknowledge the production +0.103 is artifactual.
- Re-derive a defensible operational threshold from the specialist's CALIBRATED predictions (currently no per-row specialist predictions are saved).
- Set the shadow promotion gate based on **per-trade realized R lift** with bootstrap CI, not AUC — gate (e) failed at -0.108R/trade in the production K54 v3 run.
- Pre-register the promotion criteria (e.g., "N ≥ 30 NAS+US30 shadow trades, realized R lift ≥ +0.15 with bootstrap p < 0.05") BEFORE the shadow window opens.

**If CEO wants to defer K55-shadow:**
- Drop the K54-family entirely until the audit-recommended cohort expansion completes (4-6 weeks of 2022-2023 v2-feature backfill engineering).
- Re-run K54 v4 on n ≈ 2,326 + non-XAU fillback, with apples-to-apples paired methodology baked in from the start.
- This is the more methodologically sound path; it also aligns with `Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` §5.1 / §6.2 guidance.

### 8.4 Operational K55-shadow spec (if shipping)

See companion file `agent_c_k55_shadow_spec.md`. Key points:
- p ≥ 0.55 score floor only on NAS100 + US30_cash (no other instruments)
- Ship as additive log-only signal in `shadow_logs/k55_specialist_decisions.jsonl`
- Per-row save: `{ts, symbol, p_specialist, p_global, p_combined, ai_decision, realized_r_after_close}`
- Promotion gate: pre-registered, n ≥ 50 events, paired specialist-vs-global per-row R-lift bootstrap p < 0.05
- 30-day operational window; auto-expire to prevent drift creep

---

## 9. Trade-frequency projection at p ≥ 0.55 on NAS100 + US30_cash

From the v3 specialist's pooled CPCV predictions on the 113-row NAS_US30 cohort:
- n CANDIDATEs evaluated: 113 (over Jan 5 – Apr 24, 2026 = ~80 trading days)
- Frequency: ~1.4 CANDIDATEs/day on NAS+US30 (combined)
- p ≥ 0.55 fraction: ~40% (approximate from typical class-balanced LGBM scoring distribution; not directly counted because per-row specialist preds not saved)

**Projection: ~17 NAS+US30 trades/month would clear p ≥ 0.55.** This is roughly the program's overall expected-frequency for ALL instruments combined (~17/month per CLAUDE.md) — which would mean K55-shadow gates HALF the system's production trades through a model with no detectable edge.

The shadow window is 30 days. Expected n = ~17 events. **At n=17 the operational promotion gate has very low statistical power** to detect any but huge effect sizes. The shadow window is not long enough to make a meaningful go/no-go call.

If the spec is to be shipped, the realistic path is:
- 90-day shadow (n ≈ 50 events on NAS+US30)
- pre-registered realized-R lift gate with bootstrap CI
- automatic expire on n=50 milestone or 90 days, whichever comes first

---

## 10. Open questions / new ambiguities

1. **The architecture_ab.md Q1.3 NAS_US30 +0.13 over k54_v2 (n=113) is also subject to the same pool-aggregation artifact.** Q1.3 reported per-group AUC 0.6379 vs k54_v2 0.5063 — apples-apples re-test would likely shrink that to a similar near-zero. The Q1.3 audit's "strongest single finding" is structurally the same kind of artifact as the K54 v3 specialist. CEO question: should Q1.3 audit be retroactively annotated with this finding? (The K54 v3 postmortem already moved past Q1.3's specifics, but the program's narrative — "NAS_US30 specialist replicates Q1.3" — turns out to be "both replications are pool-aggregation artifacts together, neither is a real signal".)

2. **The +0.0492 Arch A lift (Q1.3) over K54 v1 baseline 0.5286 may also be partly attributable to non-paired pool aggregation.** This forensic did not retest Arch A, but the pool-vs-per-path asymmetry that produced the +0.103 specialist artifact suggests Arch A's apparent global lift should be re-validated under paired methodology before the next iteration. Worth a follow-up Phase 2 task.

3. **Cohort temporal coverage gap is the binding methodological constraint.** With only 113 NAS_US30 trades in 4 months of 2026, no specialist hypothesis can be cross-period validated. The audit-recommended 2022-2023 v2-feature backfill remains the dominant Phase 2 priority — no architectural refinement at n=528 v3-feature or n=113 NAS-cohort can produce DSR-survival.

4. **The specialist features carrying gain are vanilla.** `vol__h1_range_over_mean_200` (33.6% gain) and `micro__last_bar_body_ratio_h4` (19.0% gain) are not asset-class-specific. If a NAS_US30-specific edge exists, it is likely captured by features the catalog doesn't have (gamma proxy, LETF flow proxy, VIX1D-VIX9D spread, dealer-positioning estimators). Adding these would be a Phase 3 mechanism-validation task, separate from any K54-family architecture work.

5. **NAS100 vs US30_CASH should arguably never have been bundled.** The Group C asset-classes paper synthesis claims NAS+US30 share "US-equity flow / dealer-gamma / LETF rebalancing / Mag-7" — the data shows top-10 Jaccard 0.05 (essentially independent). They share macro vol regime but not the mechanism layer. This argues against the "NAS_US30" cohort definition itself. Future per-instrument specialists would be honest only at much larger n per instrument.

---

## 11. File index

- `agent_c_specialist_feature_importance.csv` — saved booster gain + split + family
- `agent_c_specialist_vs_global_feature_diff.csv` — per-feature gain pct delta
- `agent_c_specialist_per_period.csv` — LOQO per-quarter (degenerate at n=20 / n_train=20)
- `agent_c_per_instrument_breakdown.json` — NAS100-alone vs US30_cash-alone
- `agent_c_specialist_cross_period.json` — directions A-D v1-schema
- `agent_c_analogous_specialists.json` — pool-aggregation results (for comparison to apples-apples below)
- `agent_c_apples_apples_paired.json` — **HEADLINE**: paired delta -0.007, t-p 0.93
- `agent_c_analogous_apples.json` — **HEADLINE**: all 4 cohorts negative paired delta
- `agent_c_summary.json` — full result aggregate
- `agent_c_forensic.py` — Python script (deterministic, re-runnable)
- `agent_c_apples_apples.py` — Python script for headline test
- `agent_c_analogous_apples.py` — Python script for analogous-cohort test
- `agent_c_k55_shadow_spec.md` — operational spec (if shipping)
- This document

---

*End. UTF-8. Read-only. No production state modified. Specialist booster intact at `research/ml_program/models/k54_v3/k54_v3_nas_us30_specialist.lgb`. The +0.103 number in `specialist_results.json` is preserved on disk for audit-trail; this forensic supersedes its interpretation.*
