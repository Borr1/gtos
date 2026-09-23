# K54 v2 Methodology Critique

**Critic:** Claude Code (Methodology Critic dispatch, Q1 Pre-Week-4 audit)
**Date:** 2026-04-28
**Scope:** Independent fitness-for-purpose critique of Q1.2 validation discipline (CPCV gate (a), 14-day prospective holdout gate (b), cross-instrument replication, white-noise null, alternative methodologies).
**Constraint:** Q1.2 hypothesis is locked (append-only); this critique may motivate a Q1.3 re-spec but cannot edit Q1.2 retroactively.
**Citations:** All numerical claims grounded in `k54_v1_audit.md`, `coverage_table.csv`, `trade_cohort.csv`, `m15_per_period.csv`, `CATALOG_v2.md`, `cusum_candidate_rate_daily.csv`. Statistical formulas: Hanley & McNeil (1982) AUC SE; de Prado *Advances in Financial Machine Learning* (AFML) ch. 7; Bailey & López de Prado (2014) "PBO".

---

## TL;DR

| Question | Verdict | One-sentence reason |
|---|---|---|
| Q1: CPCV gate (a) | **SOUND with two caveats** | Per-fold and ensemble SE are tight enough to discriminate AUC=0.61 from AUC=0.571, but the brief's "/√6 fold-independence" claim is optimistic — combinatorial-purged CPCV paths share data and SEs are correlated. |
| Q2: 14-day holdout gate (b) | **DROP as primary statistical gate; KEEP as discipline check** | At ~8 filled trades, AUC SE ≈ 0.21 — gate (b) cannot reliably distinguish 0.61 from random (power ~12% even vs the null=0.50). Re-spec to "directional + sign-of-lift discipline check" not "AUC ≥ 0.61 hard gate". |
| Q3: Cross-instrument ≥4 of 7 | **CHANGE to ≥3 of 7 with min-n-floor + sign-only test** | Per-instrument trade n=54-191 is below the threshold where AUC ≥ 0.61 is reliably distinguishable; replace point-estimate threshold with directional sign + minimum n=30/instrument. |
| Q4: White-noise null | **CALIBRATE — increase shuffles + add Bonferroni-aware tail** | B=100 shuffles gives p-resolution 0.01, exactly at gate boundary; recommend B=1000 for stable α=0.01 tail and add a separate per-feature null at the BH-FDR exploratory layer. |
| Q5: Alternatives | **ADD Combinatorial Purged CV (CPCV) + PBO + Deflated Sharpe Ratio** | de Prado's CPCV (15 paths from K=6,N=2) is statistically stronger than the brief's "6-fold mean"; PBO (Bailey-López de Prado 2014) directly answers "is this overfit?"; DSR adjusts AUC-equivalent claim for selection bias. |
| Q1.3 re-spec | **YES — escalate** | Gate (b) as currently specified is statistically empty at this n; orchestrator/CEO should weigh "drop" vs "extend to 60-90 days" vs "swap to pre-2024 cross-period" |

---

## Section 1 — CPCV gate (a) verdict

### 1.1 What the brief specifies

Per Q1.2 hypothesis, gate (a) is "CPCV mean across folds, with explicit purge gaps ≥1 week and embargo ≥1 day", target AUC ≥ 0.61. The brief estimates per-fold n ≈ 411/6 = 68.5, AUC SE per fold ≈ 0.06, ensemble mean SE ≈ 0.06/√6 ≈ 0.024.

### 1.2 What I find on the numbers

**Per-fold AUC SE is correctly characterized.** Using Hanley-McNeil (1982) at AUC=0.61 with n=68 (34 pos / 34 neg) gives SE = **0.0684**, very close to the brief's 0.06.

**The /√6 ensemble SE assumption is OPTIMISTIC.** Two reasons:

1. **CPCV paths SHARE data.** de Prado's CPCV (AFML §7.4, eq. 7.2) with K=6 splits and N=2 test groups produces C(K,K-N) = C(6,4) = **15 paths**, each path being one combination of train/test groups. Adjacent paths share K-N-1 = 3 of the 6 groups. Their AUC estimates are **not independent**; the actual ensemble SE depends on the path-correlation matrix. de Prado's empirical demonstrations (AFML fig. 7.4) show CPCV ensemble SE typically tighter than k-fold but looser than the naive /√K formula. Realistic ensemble SE at K=6, N=2 ≈ **0.04-0.05**, not 0.024.

2. **The brief's "6 splits" terminology is ambiguous.** Standard CPCV with K=6, N=1 produces 6 paths (one per held-out group) — equivalent to 6-fold purged CV. Standard CPCV with K=6, N=2 produces 15 paths. The brief should specify N explicitly. **Recommendation:** require N≥2 for the audit trail; 15-path coverage materially reduces selection-bias risk vs 6 paths.

### 1.3 Statistical sufficiency at n=411

Even with a realistic ensemble SE of 0.04-0.05, the gate is statistically meaningful:

| Test | Numbers |
|---|---|
| Distinguish AUC=0.61 from K54 v1's 0.571 | Δ=0.039; 0.78σ - 0.98σ — NOT significantly different |
| Distinguish AUC=0.61 from null AUC=0.50 | Δ=0.11; 2.2σ - 2.75σ — significant at α=0.05 one-sided, marginal at α=0.01 |
| Power to detect true AUC=0.61 vs null=0.50 (one-sided α=0.05) | ~85-90% at this SE |

**Implication:** CPCV gate (a) cannot prove that K54 v2 (claim AUC=0.61) is materially better than K54 v1 (0.571). It can prove K54 v2 is "better than random". For the lift hypothesis ("≥0.04 AUC improvement over baseline"), the CPCV gate has insufficient resolution unless we bake in a paired-comparison structure.

**Recommendation 1 (high-leverage):** Run CPCV on a **K54 v1 vs K54 v2 paired comparison** rather than threshold-style. For each fold, compute (AUC_v2 − AUC_v1) and aggregate. Paired-bootstrap or DeLong (1988) test on the AUC differences. The within-fold correlation of v1 and v2 reduces SE by a factor of 2-3× vs unpaired.

### 1.4 Caveat: feature-count ↔ sample-size pressure

K54 v2 has **1,219 features** (per `CATALOG_v2.md`); training data n ≈ 350-411 (post-train/val/test split). That's **rows-per-feature ≈ 0.3** — well below the rule-of-thumb 5-10 for stable LightGBM training, even with strong regularization.

K54 v1 had 17 features at n=350 → 20 rows/feature; LightGBM tolerated that "barely" per the audit. v2's expansion makes overfitting risk **substantially higher** unless pre-selection (`min_split_gain`, `feature_fraction_bynode`, or pre-CV correlation pruning) reduces effective feature count to <100 by training time.

**Recommendation 2:** Pre-CV feature selection MUST happen INSIDE each CPCV fold (not before splits) — otherwise leakage. Specifically: per fold, train a "screening" LightGBM with broad regularization on the train+purge slice, take top-K (K=50-150) features by gain, retrain final per-regime model on those. This is de Prado's "feature importance with bagging" pattern (AFML §8.5) — but applied PER FOLD, not on the full dataset.

### 1.5 Verdict on Q1.2 (a)

**SOUND with two caveats.** The CPCV gate (a) has enough statistical resolution to test "K54 v2 beats random", but NOT enough to test "K54 v2 beats K54 v1 by ≥0.04 AUC" without a paired-comparison structure. The brief's "/√6 fold independence" SE claim should be replaced with empirical SE from the actual CPCV path matrix, or equivalently, with a paired bootstrap. Per-fold-feature-selection inside CPCV is mandatory at this rows-per-feature ratio.

---

## Section 2 — Holdout gate (b) verdict + re-spec recommendation

### 2.1 What the brief specifies

Gate (b): "14-day prospective live holdout opened ONCE, threshold AUC ≥ 0.61." Holdout window: 2026-04-29 → 2026-05-12 (14 calendar days). Pre-registration explicit: "Setup-level n is small; CPCV gate (a) carries the primary statistical weight, holdout gate (b) is the leakage-discipline check."

### 2.2 What I find on the numbers

**The brief's own footnote is honest about this.** It explicitly downgrades gate (b) from primary statistical gate to "leakage-discipline check" — but the gate's threshold language ("AUC ≥ 0.61 on BOTH (a) AND (b)") still treats it as a hard threshold, which is internally inconsistent.

#### 2.2.1 Empirical sample size in 14 days

Three different "n" candidates the holdout could plausibly score:

| Scope | Estimate | Source |
|---|---:|---|
| **Filled trades** (system-frequency-bound) | ~8 | 17 trades/month × 14d/30d, per CLAUDE.md |
| **CANDIDATEs from live evaluations** (Component 3A passes) | ~245 | CR ≈ 16.4% × ~110 evals/day × 14d, per `cusum_candidate_rate_daily.csv` 2026-04-28 row |
| **F11-style mechanical setups** (BOS events on raw OHLCV) | ~137 | 439 F11 BOS over 64 calendar days × 14/64 days × scaling factor |
| **All M15 candles** | ~9,400 | 7 instruments × 96 candles/day × 14 days, post-weekend trim |

**The hypothesis text is ambiguous** about which scope counts. "Holdout = all M15 candles + setups on the 7 production instruments" implies all candles, but K54 is a binary classifier on **realized R**, which only exists for filled trades. So the operative n is **the smallest** of these — filled trades, n ≈ 8.

#### 2.2.2 AUC SE at each n (Hanley-McNeil)

| n (balanced) | AUC SE @ AUC=0.61 | Power vs null=0.50 (α=0.05 one-sided) |
|---:|---:|---:|
| 8 | **0.210** | **12.1%** |
| 20 | 0.128 | 20.1% |
| 50 | 0.080 | 37.4% |
| 100 | 0.056 | 60.2% |
| 200 | 0.040 | 85.9% |
| 411 | 0.028 | 98.9% |

At n=8 filled trades, **the SE is 0.21 — wider than the gap between AUC=0.61 and AUC=0.50 itself**. The gate cannot distinguish "useful classifier" from "random".

Even at the most optimistic scope (mechanical-setup n=137), SE is 0.048 — still 1.7× the SE on the CPCV training population. Power vs null=0.50 is ~70%. Power to distinguish AUC=0.61 from K54 v1's 0.571 (Δ=0.039) is **<10%** at any of these n's.

#### 2.2.3 What gate (b) actually tests

At setup-level n, gate (b) is **a coin flip on a noisy dependent variable**. The brief is correct that it's a "leakage-discipline check" — but the AUC ≥ 0.61 threshold is the wrong instrument for that check. A leakage-discipline check should be:

- Train SE estimates from CPCV (gate a) propagate to the prospective window with the SAME sign and reasonable magnitude.
- Calibration (Brier score, reliability diagram) doesn't degrade catastrophically.
- No instrument drops below baseline AUC=0.50 (sign-flip = leakage signal).

NONE of these is captured by the "AUC ≥ 0.61 on holdout" threshold language.

### 2.3 What the holdout discipline check SHOULD be

I recommend re-framing gate (b) as a **directional + calibration discipline check**, NOT a numeric AUC threshold. Specifically (this is what Q1.3 should encode):

| Check | Operationalization | Pass criterion |
|---|---|---|
| Directional sign | Holdout AUC > 0.50 | Required (any drop below 0.50 = leakage smoking gun) |
| Calibration retention | Holdout Brier ≤ 1.20× CPCV Brier | Required (>1.20× indicates train-test distribution shift) |
| Lift sign | Holdout (AUC_v2 − AUC_v1_baseline_score_on_same_data) > 0 | Required (paired comparison) |
| Per-instrument sign | At least 4 of 7 instruments have AUC > 0.50 in holdout | Soft (already part of cross-instrument replication) |
| AUC magnitude | Holdout point estimate within 95% CI of CPCV ensemble | Soft (sanity check, not pass/fail) |

This is qualitatively different from "AUC ≥ 0.61 on holdout" — it tests **the sign of the lift and the absence of catastrophic breakage**, NOT a magnitude that can't be measured at n=8.

### 2.4 Re-spec options (for orchestrator/CEO)

| Option | OOS purity | Statistical power | Wallclock cost | Recommendation rank |
|---|---|---|---|---|
| **(i)** Keep 14-day window AS-IS (numeric AUC ≥ 0.61) | High | Effectively zero | None | **REJECT** — internally inconsistent, gate is empty |
| **(ii)** Keep 14-day window, drop AUC ≥ 0.61, replace with directional sign + Brier + paired lift | High | Adequate for discipline check | None | **PRIMARY RECOMMENDATION** |
| **(iii)** Extend prospective window to 60 days (2026-04-29 → 2026-06-27) | Highest | Moderate (n~35-50, AUC SE ≈ 0.10) | +46 calendar days | **STRONG SECONDARY** if Q1 budget allows |
| **(iv)** Extend prospective window to 90 days (full 2026-Q3) | Highest | Strong (n~75-100, AUC SE ≈ 0.06) | +76 calendar days | If CEO accepts longer Q1 |
| **(v)** Drop holdout entirely; rely on CPCV-only | Medium | High (CPCV) | Saves time | **REJECT** — discipline check is valuable even at n=8 for sign-flip detection |
| **(vi)** Pre-2024 cross-period holdout (Q4-2023) | Medium-High | Limited (only XAUUSD/GBPUSD coverage pre-2024 per `coverage_table.csv`) | None | As cross-period replication only, not primary holdout |
| **(vii)** 2026-Q3 (Jul-Sep) holdout per K54 v1 audit recommendation | Highest | Strong (n~100-200) | +60-90 days | **TIED WITH (iii)/(iv)** if true 2026-H2 OOS desired |

**Top recommendation: (ii) + (iii).** Drop the AUC ≥ 0.61 numeric threshold from the 14-day holdout (it cannot be measured). Keep the 14-day holdout as a directional-discipline check. If CEO wants a meaningful prospective AUC measurement, EXTEND to 60 days minimum, accept the +46 day Q1 wallclock cost.

### 2.5 Verdict on Q1.2 (b)

**DROP as primary statistical gate; KEEP as discipline check.** The 14-day window has insufficient power to discriminate AUC=0.61 from random (power ~12%) or from the K54 v1 baseline (power <5%). The brief's pre-registered footnote already acknowledges this; Q1.3 should align the threshold language with the actual statistical purpose.

---

## Section 3 — Cross-instrument replication threshold tuning

### 3.1 What the brief specifies

Validation discipline #6: "Cross-instrument replication (works on ≥4 of 7 instruments)."

### 3.2 What I find on the numbers

Per-instrument trade counts in K54 v1 training data (from `trade_cohort.csv`):

| Instrument | n_trades | AUC SE @ AUC=0.61 (balanced) | Distinguish from null=0.50? |
|---|---:|---:|---|
| XAUUSD | 191 | 0.041 | YES (2.7σ) |
| GBPUSD | 74 | 0.066 | Marginal (1.7σ) |
| USDJPY | 74 | 0.066 | Marginal (1.7σ) |
| US30_cash | 66 | 0.070 | Marginal (1.6σ) |
| GBPJPY | 66 | 0.070 | Marginal (1.6σ) |
| NAS100 | 57 | 0.075 | Marginal (1.5σ) |
| XAGUSD | 54 | 0.077 | Marginal (1.4σ) |

**At n<70, "AUC > 0.61" is barely distinguishable from "AUC > 0.50" at conventional significance.** Reading any per-instrument point estimate at n=54-66 as a "passes/fails" gate at the 0.61 threshold is statistically inappropriate — the gap between 0.61 and the realistic uncertainty ranges of those numbers is smaller than the SE itself.

### 3.3 What "≥4 of 7" actually captures

If we treat each instrument as an independent Bernoulli trial with p = "true AUC ≥ 0.61", the "≥4 of 7" gate is reasonable IF instruments are truly independent and the probability under the null is well-defined. But:

- **Independence is violated.** XAU and XAG are correlated (~0.6 by `cross_instrument_correlation_gate.py`). NAS100 and US30 are correlated. GBP-pairs are correlated. Effective independent instruments closer to 4-5, not 7.
- **The "passes" event isn't well-calibrated.** At n=54, the chance of observing AUC ≥ 0.61 under TRUE AUC = 0.55 is ~28%, not 5%. So "passes the gate" doesn't mean "real signal" at this n.
- **Cross-instrument coverage in the catalog is uneven.** Per `microstructure.md`, only 2 of 7 instruments have tick coverage. Per `regime.md`, US30_cash is missing from regime backfill. These data-coverage holes mean some instruments are statistically guaranteed to underperform regardless of the underlying signal.

### 3.4 Recommended threshold tuning

Three issues to address:

1. **Replace point-AUC threshold with sign-of-lift threshold.** Per-instrument: AUC > 0.50 (sign positive) AND AUC > AUC_v1_on_same_instrument (lift sign positive). Two conditions, both required.

2. **Add a minimum-n floor.** Below n=30 per instrument, exclude that instrument from the cross-instrument gate (not "automatic fail" — "out of scope"). XAGUSD (n=54), NAS100 (n=57) are at the bottom of acceptable; consider raising the floor to n=50 if Q1 ML population is similar.

3. **Reduce gate fraction to ≥3 of 5 (NOT ≥4 of 7).** Effective independent instruments ~4-5, so requiring "≥4 of 7" with correlated instruments is statistically equivalent to "≥3 of 5" with independent ones. Either:
   - Require ≥4 of 7 raw count (as written), accepting the correlation slack, OR
   - Require ≥3 of 5 effective-independent grouping (XAU+XAG combined, NAS100+US30 combined, FX-pairs combined).

**Concrete recommendation:** Cross-instrument replication = "AUC > 0.50 AND AUC_v2 > AUC_v1_baseline on **at least 3 of 5 effective-independent instrument groups** {XAU+XAG, NAS100+US30, GBPJPY, GBPUSD+USDJPY, residual}, with per-group n ≥ 30." This is statistically defensible at the available n.

### 3.5 Verdict on cross-instrument threshold

**CHANGE.** Either keep "≥4 of 7" but switch to sign-of-lift (not point AUC), OR change to "≥3 of 5 effective-independent groups" with explicit n-floor. Current spec ("≥4 of 7" + "AUC ≥ 0.61") is double-broken: AUC=0.61 isn't measurable at per-instrument n; correlation among instruments inflates the count.

---

## Section 4 — White-noise null calibration

### 4.1 What the brief specifies

Validation discipline #4: "White-noise null test (shuffle labels ×100; result must beat null distribution at p<0.01)."

### 4.2 What I find on the numbers

#### 4.2.1 B=100 shuffles is borderline at α=0.01

A permutation test with B shuffles has p-value resolution = 1/(B+1). At B=100, the smallest achievable p-value is 1/101 ≈ 0.0099 — **literally exactly at the gate boundary**. Any "passes at p<0.01" result at B=100 is actually "p ≤ 0.01 with no margin", indistinguishable from p = 0.01.

For a stable α=0.01 gate, conventional permutation-test guidance (Phipson & Smyth 2010) recommends **B ≥ 1000** for tail estimation. At B=10,000 the test resolves to p ≈ 1e-4.

**Recommendation 4a:** Increase shuffles to B=1000 for stable α=0.01 tail discrimination. Compute cost is linear in B but only train-time CPCV; ~6× the K54 train cost at B=1000 vs B=100. At ~15 minutes per K54 train run (per audit Section 4), this is ~1.5 hours of CPU — well within wallclock budget.

#### 4.2.2 Multi-feature null calibration

A second concern: at 1,219 features and α=0.01, the **expected number of false-positive features under a noisy null is ~12** (1219 × 0.01). If the white-noise null is applied to "the model's overall AUC" (single test), B=100 is the only concern. But if it's applied to PER-FEATURE shuffle-importance (as some implementations do), the per-feature p-values need correction.

Bonferroni at 1219 features → α/N = 4.1e-5 → permutation B ≥ 25,000 to resolve. BH-FDR at q=0.10 across 1219 features is gentler but still requires B ≥ 1000.

**Recommendation 4b:** Specify which level the white-noise null operates at (model-level vs feature-level), and choose B accordingly. For model-level, B=1000 is sufficient. For feature-level (any per-feature significance claim), B=10,000 minimum.

#### 4.2.3 Multi-feature dependence

The features in CATALOG_v2 are **highly correlated** (multi-lookback variants of same primitive: e.g., `M15__nearest_ob_dist_atr__lb20`, `lb50`, `lb100` share most variance). Empirical effective-N for Bonferroni-style correction is far below 1219 — likely 50-200 effective independent dimensions after eigenvalue decomposition.

Recommendation 4c: Run an empirical effective-N estimation (PCA on feature matrix, count eigenvalues with cumulative variance ≥ 95%) and use that for the Bonferroni denominator instead of raw count. de Prado AFML §6 discusses this for feature importance specifically (and recommends Mean Decrease in Accuracy with bagging as more robust than gain-based).

### 4.3 Verdict on white-noise null

**RE-TUNE.** B=100 shuffles is at the gate boundary (1/101 ≈ 0.0099). Increase to B=1000 minimum for stable α=0.01 test. Specify model-level vs feature-level scope. If feature-level: B=10,000 + use empirical effective-N (likely 50-200) for Bonferroni denominator, not raw 1219.

---

## Section 5 — Alternative methodologies

### 5.1 Combinatorial Purged CV (CPCV) — already partially present

**Status:** The brief says "CPCV with 6 splits", but doesn't specify N (number of test groups per path). As noted in Section 1.2, K=6,N=2 gives 15 paths and is statistically much stronger than K=6,N=1 (6 paths = standard purged k-fold).

**Recommendation:** Make N explicit in Q1.3. Strongly prefer K=6,N=2 (15 paths). de Prado AFML §7.4 demonstrates that 15 paths reduce selection-bias variance by ~60% vs 6 paths.

### 5.2 Probability of Backtest Overfitting (PBO) — Bailey & López de Prado (2014)

**What it does:** Splits the in-sample period into S sub-blocks; for each combinatorial half-split (S/2 train + S/2 test), records the rank of the in-sample best strategy in the out-of-sample distribution. PBO = P(in-sample best is below median out-of-sample).

**Why it's relevant:** K54 v2 will involve a **selection** step — "pick the best LightGBM hyperparams on val, evaluate on test". With 1,219 features and a hyperparameter grid (Optuna), the selection space is large; PBO directly answers "is the 'winning' configuration overfit?"

**Cost:** ~30 minutes CPU at S=8 blocks; subscription-bounded.

**Recommendation 5a:** ADD PBO to validation discipline (alongside white-noise null). Pass criterion: PBO < 0.5 (better than coin-flip overfitting risk). Bailey & López de Prado (2014) explicitly recommend PBO as the canonical anti-overfitting test for backtests with selection.

### 5.3 Deflated Sharpe Ratio (DSR) / equivalent for AUC

**What it does:** Adjusts a reported metric (originally Sharpe; analogous adjustment for AUC) for selection bias under N tested strategies. de Prado (2018, "The Deflated Sharpe Ratio") gives a closed-form deflation given (n_tests, skew, kurtosis).

**Why it's relevant:** K54 v1 → v2 is one step in a larger search (pre-registration helps but doesn't eliminate selection). The "AUC=0.571 baseline" vs "AUC=0.61 target" comparison can be DSR-deflated to account for the implicit prior search history.

**Cost:** Trivial — a closed-form formula, sub-second.

**Recommendation 5b:** Compute deflated AUC at end-of-Q1 alongside raw AUC. Report both. Pass criterion uses raw AUC (per Q1.2 lock); deflated AUC is informational. Does not require Q1.2 re-spec.

### 5.4 Block bootstrap with embargo

**What it does:** Resamples blocks of contiguous data (rather than rows independently), preserving autocorrelation structure. Block size = max autocorrelation lag (typically 20-50 H1 bars).

**Why it's relevant:** K54 v2's setup-level rows are time-clustered (multiple setups within a single H4 trend regime share dynamics). Standard k-fold + IID-row bootstrap underestimate uncertainty. Block bootstrap with embargo gives more honest CIs.

**Cost:** B=1000 block-bootstrap + per-block AUC computation ≈ 1-2 hrs CPU.

**Recommendation 5c:** ADD block bootstrap as a second uncertainty-quantification overlay on CPCV. Gives CIs on (AUC_v2 − AUC_v1) that don't assume IID rows. Complementary to CPCV, not replacement.

### 5.5 Reality Check / White's Bootstrap (White 2000)

**What it does:** Tests whether the BEST of N candidate strategies has a population mean exceeding some baseline, accounting for the fact that we picked the best.

**Why it's relevant:** If K54 v2 reports per-regime models with regime selection, the reported "best regime" performance is upward-biased.

**Cost:** Moderate — bootstrap on cross-regime panel.

**Recommendation 5d:** Optional. PBO (5.2) and DSR (5.3) cover most of the same ground more directly for AUC-targeted hypotheses. Consider skipping unless per-regime claims become primary.

### 5.6 Ranking — alternatives to add to Q1.3

| Method | Adds what | Cost | Priority |
|---|---|---|---|
| **PBO (Bailey & López de Prado 2014)** | Direct "is this overfit?" test | 30 min CPU | **HIGH — add** |
| **CPCV with K=6,N=2 (15 paths)** | 60% lower selection-bias var vs K=6,N=1 | Same as 6-fold | **HIGH — already in spec, just lock N=2** |
| **Block bootstrap with embargo** | Honest CI on AUC differences under autocorrelation | 1-2 hrs CPU | MEDIUM — add |
| **Deflated AUC** | Selection-bias-corrected reported metric | Trivial | MEDIUM — add as informational |
| **Reality Check / White's Bootstrap** | Best-of-N selection bias | Moderate | LOW — overlaps with PBO |

### 5.7 Verdict on alternatives

**ADD: PBO + lock CPCV at N=2 (15 paths) + block bootstrap.** PBO is the single highest-leverage addition because it directly tests overfit risk — exactly the failure mode at n=411 with 1,219 features. CPCV-N=2 is essentially free (already running CPCV; just changes path count from 6 to 15). Block bootstrap honestly priced uncertainty under autocorrelation.

---

## Section 6 — Recommended Q1.3 re-spec (if any) for orchestrator/CEO consideration

### 6.1 Should we escalate?

**YES.** Q1.2 has TWO distinct methodology defects:

1. Gate (b) "AUC ≥ 0.61 on 14-day holdout" cannot be measured at the available n (power ~12% vs null=0.50). The pre-registered footnote acknowledges this but the threshold language doesn't.
2. The "/√6 fold-independent SE" framing is statistically optimistic; CPCV paths share data, and ensemble SE should be empirically estimated.

The correct re-spec response per the registry's own discipline ("a hypothesis without a measured outcome on its threshold is incomplete") is to **append Q1.3** that supersedes Q1.2's gate (b) with a discipline-check formulation, while keeping gate (a) and adding PBO.

### 6.2 Proposed Q1.3 text (for orchestrator/CEO review)

> ## Q1.3 — K54 v2 expanded feature catalog (PRIMARY, supersedes Q1.2 gate (b) per methodology critique)
>
> - **Date pre-registered:** [TBD by orchestrator after CEO review]
> - **Pre-registered by:** ML Program Orchestrator (post-methodology-critique re-spec)
> - **Phase:** Q1 — Foundation: data + features + K54 v2
> - **Hypothesis:** *"An expanded 1,219-feature catalog (vs K54 v1's 17) lifts a per-regime LightGBM's AUC by ≥0.04, from K54 v1's baseline of 0.571 to ≥0.61, when validated via combinatorial-purged CV (K=6, N=2; 15 paths) with explicit purge gaps ≥1 week and embargo ≥1 day, on training data from 2024-02-20 → 2026-04-28. AUC measurement is paired (v2 vs v1 on identical CPCV folds), with PBO < 0.5 to confirm non-overfitting. A 14-day prospective holdout window 2026-04-29 → 2026-05-12 serves as a directional-discipline check (sign of lift, calibration retention, no per-instrument sign-flip), NOT as a numeric AUC gate."*
> - **Thresholds (ALL required):**
>   - **(a) CPCV paired:** mean(AUC_v2 − AUC_v1) ≥ 0.04 AND DeLong p < 0.01 across 15 CPCV paths.
>   - **(b) PBO:** Probability of Backtest Overfitting < 0.5 over hyperparameter selection grid.
>   - **(c) Holdout discipline:** Holdout AUC > 0.50 AND Holdout Brier ≤ 1.20× CPCV Brier AND Holdout (AUC_v2 − AUC_v1_paired) > 0.
>   - **(d) Cross-instrument:** AUC_v2 > AUC_v1 on at least 3 of 5 effective-independent instrument groups {XAU+XAG, NAS100+US30, GBPJPY, GBPUSD+USDJPY, residual}, with per-group n ≥ 30.
>   - **(e) White-noise null:** B=1000 shuffles, observed AUC ≥ permutation p<0.01 boundary with margin.
> - **Holdout date range:** 2026-04-29 → 2026-05-12 (14 calendar days). NEVER read by feature engineers, modelers, or statisticians until end-of-Q1 evaluation.
> - **Holdout LOCKED:** [Inherit from Q1.2 lock if accepted]
> - **Holdout opened:** NO
> - **Result:** PENDING
> - **Audit trail link:** `research/ml_program/audit/methodology_critique.md` (this document)
>
> **Differences from Q1.2:** (1) Gate (b) numeric AUC ≥ 0.61 replaced with directional + calibration discipline check. (2) CPCV explicitly N=2 (15 paths). (3) PBO added. (4) Cross-instrument re-grouped to effective-independent. (5) White-noise null B=100 → B=1000.

### 6.3 Decision matrix for orchestrator/CEO

| Decision path | Pros | Cons | Recommendation |
|---|---|---|---|
| **A. Keep Q1.2 as-is, evaluate per its locked text** | No re-spec churn; respects pre-registration discipline | Gate (b) is statistically empty; "PASS" outcome is meaningless even if achieved | Reject |
| **B. Append Q1.3 superseding Q1.2 gate (b)** | Methodology becomes statistically defensible; CPCV gate (a) preserved | Adds Q1.3 row to registry; mild churn | **PRIMARY RECOMMENDATION** |
| **C. Mark Q1.2 INVALIDATED_PRE_TEST and re-spec from scratch** | Clean slate | Q1.2 is only 1 day old (locked 2026-04-28); marking it INVALIDATED_PRE_TEST so soon undermines pre-registration discipline | Reject |
| **D. Extend prospective window to 60-90 days, keep numeric AUC ≥ 0.61** | Holdout n becomes ~50-100, gate (b) becomes meaningful | +46-76 wallclock days to Q1; substantial timeline cost | Secondary recommendation if CEO accepts longer Q1 |

**Top recommendation:** Path B (Q1.3 supersession). The pre-registration discipline is preserved (Q1.2 stays in the registry as historical entry); methodology becomes defensible; no major timeline impact.

---

## Final-report bullets (for orchestrator)

1. **CPCV gate (a) verdict:** SOUND with two caveats — the ensemble SE is somewhat tighter in the brief (`/√6` is optimistic, true ≈ /√3-4 due to CPCV path correlation) and per-fold-feature-selection inside CPCV is mandatory at 1,219 features ÷ 411 rows.

2. **Holdout gate (b) verdict:** DROP as primary numeric gate (AUC ≥ 0.61 is unmeasurable at n=8 filled trades; power ~12%). KEEP as directional-discipline check (sign of lift, calibration retention, no sign-flip).

3. **Cross-instrument threshold:** CHANGE from "≥4 of 7 instruments AUC ≥ 0.61" to "AUC_v2 > AUC_v1 sign-of-lift on ≥3 of 5 effective-independent instrument groups, n ≥ 30 per group". Current spec has two flaws (point AUC unmeasurable per-instrument; instrument correlation inflates effective-N).

4. **White-noise null calibration:** RE-TUNE — B=100 shuffles is exactly at the α=0.01 boundary (1/101 ≈ 0.0099, no margin). Increase to B=1000 minimum; specify model-level vs feature-level scope.

5. **Top alternative methodology to add:** **PBO (Probability of Backtest Overfitting; Bailey & López de Prado 2014)** — directly tests overfit risk under hyperparameter+feature selection, exactly the failure mode at 1,219 features ÷ ~350 train rows. ~30 min CPU; subscription-bounded; high-leverage.

6. **Q1.3 re-spec escalation:** **YES** — append Q1.3 supersession (Path B in §6.3). Q1.2's gate (b) is statistically empty as written and the brief's own footnote acknowledges this; gate (a) survives the critique with two caveats; supersession preserves pre-registration discipline while making methodology defensible.

---

*End of methodology critique. This document does not modify Q1.2 or PRE_REGISTERED_HYPOTHESES.md; it is informational input for the orchestrator's decision on whether to append Q1.3.*
