# K54 v2 Cross-Period Replication

**Date:** 2026-04-28
**Author:** Cross-Period Replication Auditor
**Inputs:** `research/ml_program/scout/feature_matrix.parquet` (528 × 1,247) ; `research/ml_program/models/k54_v2/{meta,feature_prune_list,top_features,cpcv_paired_results,cross_instrument_results}.json`
**Code:** `research/ml_program/models/k54_v2_cross_period/cross_period_replication.py`
**Outputs:** `research/ml_program/models/k54_v2_cross_period/{k54_v2.lgb,k54_v1.lgb,meta.json,results.json,per_group_results.json}`

---

## 0. Critical preamble (read first)

The orchestrator brief estimated `n_train ≈ 280` from the Data Inventory audit. The audit's actual estimate (`data_inventory_audit.md:286-289`) was `~114 rows (XAUUSD 108 + GBPUSD 6). Insufficient on its own.` The audit explicitly recommended **augmenting via 2022-2023 mechanical OB synthesis BEFORE running cross-period replication** (item 5 in Section 9 of `data_inventory_audit.md`). Augmentation was NOT performed; this audit honors the brief literally and runs the cross-period split on the existing scout matrix as-is.

**Actual split:**
- **TRAIN (date < 2026-01-01):** n = 93 (XAUUSD 87 + GBPUSD 6). 93.5% XAUUSD-only.
- **TEST (2026-01-01 ≤ date ≤ 2026-04-28):** n = 435 (all 7 instruments).
- Train win-rate 0.667; Test win-rate 0.561 (Δ = -10.6 pp; population shift to lower-WR cohort).

**Implication:** This is **not a fair cross-period test of the v2 model's claimed cross-instrument generalization** because train data covers ~1.5 instruments (mostly XAUUSD). The headline test AUCs are dominated by "can a 90%-XAUUSD-trained model generalize to 6 unseen instruments + 1 seen-but-decayed XAUUSD cohort". Numbers below are real but interpret with this asymmetry in mind.

---

## 1. Test-period AUC vs CPCV reference

| Metric | Cross-Period (n_test=435) | CPCV (15 paths, n=528) | Δ |
|--------|---------------------------|-------------------------|---|
| **K54 v2 AUC** | **0.5016** | 0.5429 | **−0.0413** |
| **K54 v1 AUC** | **0.4804** | 0.5120 | **−0.0316** |
| **Mean lift (v2 − v1)** | **+0.0212** | +0.0309 | −0.0097 |
| DeLong p (paired, two-sided) | 0.5773 | 0.0015 (Stouffer combined) | — |
| Brier v2 | 0.2739 | n/a in artifact* | — |
| Brier v1 | 0.2740 | n/a in artifact* | — |

*Brier score not pre-computed in `cpcv_paired_results.json`. Test-period Brier 0.2739 is essentially identical to constant-rate prediction (test WR 0.561 → constant Brier ≈ 0.246), so v2 calibration adds ~0 over a "predict mean" baseline. v1 ties.

**Headline reading:**
- Both v2 and v1 absolute AUC on cross-period test fall to ~0.50 (random). The v2 absolute AUC drop of −0.0413 is **substantial** and exceeds the +0.0309 lift it claimed in CPCV.
- The +0.0212 paired lift in cross-period is within 0.01 of the CPCV +0.0309 lift (Δ = −0.0097), which trips the "ROBUST" threshold by the strict definition (|Δ| ≤ 0.01).
- However: the lift is **not statistically distinguishable from zero** on the test cohort (DeLong p = 0.5773). The CPCV combined p of 0.0015 was driven by aggregating across 15 paths; on the single test cohort, the lift's signal-to-noise is too weak for a cross-period claim.

---

## 2. Robustness verdict

**ROBUST_BY_DELTA_NOT_BY_SIGNIFICANCE.** Lift magnitude survives (|Δ| = 0.0097 ≤ 0.01), but absolute AUC for both models drops to ~0.50 and the lift is not significant on the test cohort (DeLong p = 0.58). The "lift survives" reading is technically correct on the v2−v1 differential but is not actionable: a +0.0212 lift between two models that both score ~0.5 means the production-relevant comparison "v2 better than no model" fails OOS.

The robustness gate from the brief was framed as: lift Δ ≤ 0.01 → ROBUST. The numerical answer is **ROBUST**. The honest scientific answer is the differential survives but the model itself does not — at this train/test asymmetry.

---

## 3. Per-group cross-period AUCs

| Group | n | AUC v2 | AUC v1 | Δ (v2 − v1) | Lift sign | CPCV lift sign | **Flipped?** |
|-------|---|--------|--------|-------------|-----------|----------------|--------------|
| GBPJPY | 62 | 0.5236 | 0.4343 | **+0.0893** | POS | NEG | YES |
| GBPUSD_USDJPY | 132 | 0.5115 | 0.4821 | **+0.0294** | POS | NEG | YES |
| NAS_US30 | 113 | 0.4569 | 0.5346 | **−0.0777** | NEG | POS | YES |
| XAU_XAG | 128 | 0.5206 | 0.4465 | **+0.0741** | POS | POS | NO |

- **3 of 4 groups flip lift sign vs CPCV.** Only XAU_XAG retains the CPCV-positive signal, and it is the group whose train data dominated the model (87/93 = 93.5% XAUUSD).
- **3 of 4 groups have positive cross-period lift** (vs 2 of 4 in CPCV). Despite more positives, the PATTERN is unstable: NAS_US30 (best CPCV lift +0.074) goes deeply negative on cross-period (−0.078); GBPJPY (worst CPCV lift −0.016) becomes the strongest cross-period positive (+0.089).
- This sign-flip rate (3/4) on cross-period vs CPCV is the strongest single piece of evidence that **CPCV per-group lifts in the K54 v2 build are not generalizing**. The structural reason is clear: per-group CPCV had 2024-2025 + 2026 data co-mingled; cross-period removes that overlap and exposes per-group decay.

---

## 4. Top-1 and top-30 feature persistence

**Global cross-period top-10** (HP idx 0: n=100, depth=3, lr=0.01 — selected by 4-fold CV):
1. ts__t_hour_14_oh — gain 1.0
2. ts__t_days_to_nearest_opex_signed — gain 1.0
3. ts__t_is_within_5d_of_quarterly_opex — gain 1.0
4. ts__t_day_of_year_sin — gain 1.0
5. ts__t_day_of_year_cos — gain 1.0
6-10. various vol__m15_atr_* — gain 0.0

The 4-fold CV selected the most-shrunk HP (depth=3, lr=0.01); the resulting model barely splits, which is why global gains are 1.0 / 0.0. To make top-30 comparison apples-to-apples, the **per-group XAU_XAG model with HP-matched to CPCV (n=100, depth=5, lr=0.1)** is the meaningful comparison.

**CPCV top-1 (`vol__h1_range_over_mean_50`, gain 6.0):** NOT in cross-period top-10. CP gain = 0.0 on the global model. Top-1 does not persist.

**CPCV per-group top-10 (XAU_XAG) vs cross-period (HP-matched, n=128 test cohort):**

| Feature | CPCV gain | CP-period gain | Ratio | Verdict |
|---------|-----------|-----------------|-------|---------|
| ts__t_days_to_nearest_opex_signed | 44.0 | **0.0** | 0.000 | **OVERFIT** |
| ts__t_day_of_year_cos | 40.0 | **0.0** | 0.000 | **OVERFIT** |
| ts__t_days_to_nearest_holiday_signed | 35.0 | **1.0** | 0.029 | **OVERFIT** |
| ts__t_day_of_year_sin | 28.0 | **0.0** | 0.000 | **OVERFIT** |

All 4 calendar features collapse to gain 0.0 / 1.0 on the 128-row 2026-only XAU_XAG cohort under the same HP that gave them gains 28-44 on the full 215-row CPCV cohort. The drop is ≥97% across the board.

This was checked under both:
- **Selected HP (n=100, depth=3, lr=0.01)** — global CP model: 4 calendar features in top-10 (gain 1.0 each), but with depth=3 nearly any feature reaches gain 1.0.
- **CPCV-matched HP (n=100, depth=5, lr=0.1)** — XAU_XAG-only TEST cohort: all 4 calendar features have gain 0.0 / 1.0; the top-15 is dominated by structure + volatility + liquidity + microstructure features (`struct__H1__nearest_ob_dist_atr__lb20` gain 71, `vol__m15_vol_of_range_ratio_20` gain 63, etc.).

**Verdict on calendar feature persistence: OVERFIT.** All 4 of the audit-flagged calendar features show ≥97% gain reduction on the 2026-only XAU_XAG test cohort. **The CF-10 hypothesis from the audit (calendar features memorized 2024-2025 high-impact dates) is empirically confirmed.**

The new top features on the cross-period XAU_XAG model are structurally meaningful and instrument-appropriate (OB distance, volatility ratio, liquidity sweep retest), suggesting a per-group K54 v2 retrained per cohort would land on different — and more defensible — features.

---

## 5. Calibration (Brier score)

- **Test cohort Brier v2: 0.2739**
- Constant-rate baseline (predict win_rate=0.561 on every row): Brier = 0.561 × (1−0.561) = 0.2466
- Test Brier v2 is **WORSE** than constant prediction (0.2739 > 0.2466 → mean square error inflated by 11%).
- v1 ties at 0.2740 (no calibration advantage either).

Calibration is **not preserved** on cross-period test. Both models predict probabilities slightly worse than the win-rate prior. This compounds the AUC-near-0.50 result: the model adds neither rank-ordering signal nor calibrated probabilities.

---

## 6. Methodology checks performed

1. **HP selection separation:** 4-fold time-ordered CV on TRAIN cohort only. No test peek. (`cross_period_replication.py:select_hp_via_4fold`)
2. **Patch-1 prune list reused exactly** (13 features dropped, same as `feature_prune_list.json`). (`cross_period_replication.py:apply_existing_prune`)
3. **DeLong test** identical implementation to `train_k54_v2.py:367-433`.
4. **Calibration:** Platt sigmoid using a 1/8 inner-validation slice from train sorted by date.
5. **Symbol asymmetry between train and test:** 87 of 93 train rows are XAUUSD; 5 of 7 test instruments have **zero** train representation. This is documented in `results.json:audit_caveat`.

---

## 7. Recommendations (out of scope but warranted)

1. **The brief's `n_train ≈ 280` estimate is wrong.** Update the K54 program documentation to cite the audit's actual `n_train ≈ 114` recommendation alongside the augmentation prerequisite.
2. **Cross-period replication is not a meaningful test** at this train/test composition imbalance. Either:
   - (a) Synthesize 2022-2023 mechanical OB labels per `data_inventory_audit.md:276` (estimated +100-200 rows on GBPJPY/US30_cash) before re-running, OR
   - (b) Restrict cross-period claim to XAUUSD-only (the only instrument with adequate train representation; n=87+77=164 rows).
3. **Calendar-feature CF-10 confirmation:** all 4 audit-flagged calendar features overfit. They should be **stratified-importance audited** in any per-group re-build, ideally pruned from XAU_XAG group input or held-out via leakage-aware CV. The risk is that the v2 model is encoding XAUUSD-specific 2024-2025 directional macro events (FOMC dates, NFP, OPEX) that won't repeat with the same valence in 2026+.
4. **Per-group sign flips (3/4):** the CPCV per-group result was driven by within-period leakage. Real cross-period generalization is closer to a coin flip per group at the v2 model's current configuration.

---

## 8. Files written

- `research/ml_program/models/k54_v2_cross_period/cross_period_replication.py` (528 lines, code)
- `research/ml_program/models/k54_v2_cross_period/k54_v2.lgb` (final v2 booster)
- `research/ml_program/models/k54_v2_cross_period/k54_v1.lgb` (final v1 booster)
- `research/ml_program/models/k54_v2_cross_period/meta.json` (HP, AUCs, verdicts)
- `research/ml_program/models/k54_v2_cross_period/results.json` (full per-feature, per-group results)
- `research/ml_program/models/k54_v2_cross_period/per_group_results.json` (per-group + sign-flips vs CPCV)

All files written with `encoding="utf-8"`. No production state modified. No Anthropic API calls. Holdout (2026-04-29 to 2026-05-12) NOT touched.
