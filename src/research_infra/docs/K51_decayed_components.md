# K51 — Decayed-Component Identification

Research-only infrastructure for tracking per-component R-attribution
trajectories across rolling windows of trades, and identifying which
components have lost edge magnitude relative to an earlier baseline.

**Branch (F5 update):** `feat/research-f5-k51-shap-proper`
**Original branch:** `feat/research-k51-decayed-components`
**Module:** `src/research_infra/decayed_component_identifier.py`
**CLI:** `scripts/research/run_k51_decayed_components.py`
**Tests:** `tests/research_infra/test_decayed_component_identifier.py`
**Pure-Python core; ML deps optional** (SHAP path activates when
``shap`` + a tree backend are importable).

---

## Install requirement (F5 update)

The proper-method (SHAP) path needs:

```
pip install "shap>=0.42" "lightgbm>=4.0" "scikit-learn>=1.3"
```

These are now declared in ``requirements.txt`` (research-only deps
section). When they are missing, K51 falls back to the original
permutation-importance estimator with no behaviour change beyond the
``method`` field on each ``TrajectoryPoint`` reading
``"permutation_importance"`` instead of ``"shap_treeexplainer"``.

`numpy` is already a hard dependency. `scikit-learn` is a transitive
dependency of `shap` and is also used as a fallback tree backend
(``GradientBoostingRegressor``) when ``lightgbm`` is unavailable.

---

## What this answers

For each canonical feature (kill_zone, framework, direction, daily_bias,
sweep_quality, displacement_quality, setup_grade, liquidity_pool_type,
planned_rr, mfe_r, mae_r, hold_time_candles), **how does its
contribution to realized-R variance evolve across non-overlapping
rolling windows?** Which features that USED TO matter no longer do?

This is the time-evolution complement of K50 (population-level edge
attribution). K50 ranks components by *current* R contribution; K51
zooms in on **trajectories** so a component that is currently invisible
at population level can be flagged as having had a real H1 contribution
that has since decayed away.

Strategic context: A1 indicates SYSTEM_DECAY (the AI has lost
selectivity). Knowing _which_ axes the AI lost selectivity along feeds
both prompt research (P68-P70) and the K54 ML-classifier feature
selection step.

---

## Methodology (F5 update — proper SHAP + Bonferroni + bootstrap CI)

### 1. Feature engineering (shared with K50)

Per-trade canonical feature dicts are built by `extract_features()`.
The function reads from a trade dict with `r_multiple` /
`exit.realized_R` (per the v1.1 instrumentation schema) and pulls the
following fields, falling back through nested `metadata` /
`trade_parameters` blocks when needed:

Categorical features:
- `framework`         (`ob_retest` / `fvg_fill` / `breaker_re_entry`)
- `direction`         (`LONG` / `SHORT`)
- `kill_zone`         (`london` / `ny` / `tokyo` / ...)
- `daily_bias`        (`bullish` / `bearish` / `neutral`)
- `sweep_quality`     (`clean` / `messy` / `none`)
- `displacement_quality` (`strong` / `weak` / `none`)
- `setup_grade`       (`A+` / `A` / `B` / `C`)
- `liquidity_pool_type` (`asian_high` / `asian_low` / ...)

Numerical features (bucketed into terciles per-window):
- `planned_rr`
- `mfe_r`              (post-trade outcome — included for descriptive
                          attribution, not as a predictor)
- `mae_r`              (same caveat as `mfe_r`)
- `hold_time_candles`

Missing categorical → literal `"missing"`. Missing numeric → `None` →
`"missing"` bucket.

These canonical lists are exposed at module level
(`CANONICAL_CATEGORICAL_FEATURES`, `CANONICAL_NUMERICAL_FEATURES`,
`CANONICAL_FEATURES`) so K50 imports the same lists and produces
apples-to-apples attribution.

### 2. Rolling attribution

Trades are sorted ascending by timestamp and bucketed into
**non-overlapping** windows of size N (default 50). Window k covers
trades `[k*N, (k+1)*N)`. Non-overlapping windows are essential: they
give independent samples for any downstream slope/regression analysis.

For each window, compute per-feature importance by one of two paths:

**SHAP path (preferred when available).**
1. Bucket-encode every categorical feature to integer index;
   tercile-bucket every numeric feature.
2. Fit a tree regressor (LightGBM > XGBoost > sklearn-GBM) on the
   bucket-encoded matrix targeting realized R.
3. Run :class:`shap.TreeExplainer` and take per-feature **mean(|SHAP|)**
   as the importance.

The SHAP path captures **interaction-aware** importance — a feature can
be uninformative on its own (univariate) but jointly informative with
another and SHAP picks that up because TreeExplainer attributes per-
trade contributions.

**Permutation-importance fallback (deterministic).**
- Baseline MSE = MSE of an intercept-only predictor (predict mean R
  always).
- Per-feature MSE = MSE of a stratum-mean predictor (predict the mean
  R of all trades sharing this feature's value).
- Importance = `max(baseline_mse - feature_mse, 0)`.

This is a univariate variance-reduction proxy; faster than SHAP, fully
deterministic, no third-party deps. Used in pure-Python environments
or via ``--method permutation``.

### 3. Bootstrap 95% CI per importance estimate (F5 addition)

For each window, resample trades within the window
``--bootstrap-n-resamples`` times (default 100) **with replacement**,
re-compute the importance, and take the 2.5/97.5 percentiles of the
bootstrap distribution. Each ``TrajectoryPoint`` carries
``ci_low`` / ``ci_high``. ``--bootstrap-n-resamples 0`` skips the
bootstrap (CI bounds == point estimate).

The bootstrap is per-window (not pooled across windows) because the
importance statistic is itself per-window — the CI captures sampling
variability of the within-window importance, not of the trajectory.

### 4. Decay identification (F5 — Bonferroni-gated)

Per-feature trajectories are split chronologically into H1 (first half
of windows) and H2 (second half). For each feature:

1. Compute drop_pct = (h1_mean − h2_mean) / h1_mean.
2. Run a **one-sided Welch's t-test** on the H1 vs H2 importance
   samples with null hypothesis ``H0: H1_mean ≤ H2_mean``. A small p
   means H1 mean is significantly LARGER than H2 mean (i.e. decay).
3. **Apply Bonferroni correction** with family size =
   ``len(CANONICAL_FEATURES)`` (12 features in the canonical set). The
   H1/H2 importance-delta test is a hypothesis test family — running
   it across all canonical features inflates Type I error unless
   corrected. Family size matches ``bonferroni_survival.py`` (K52)'s
   pattern.
4. Classification:
   - **Decayed**: ``drop_pct ≥ threshold_pct`` AND ``h1_mean > 0`` AND
     ``bonferroni_p < alpha`` AND both halves have ≥1 window.
   - **Newly important**: ``h1_mean == 0`` AND ``h2_mean > 0`` AND
     ``(h2_mean - h1_mean) ≥ threshold_pct * h2_mean`` (no Bonferroni
     gate — this is a discovery flag, not a confirmatory test).
   - **Stable**: feature has windows in both halves but neither rule
     fires (including features with large drops that fail Bonferroni —
     reported with ``status = "suggestive"`` in the all-feature table).

Default threshold is **0.40** (40% drop), default α is **0.05** (CLI
flag `--alpha`). The CLI's `--threshold-pct` and `--alpha` knobs
make both knobs a one-line change.

---

## Why proper-method matters: original vs F5 comparison

The original K51 (permutation-importance, no Bonferroni) was a screening
tool. The F5 update lifts it to a confirmatory tool by adding:

1. **SHAP attribution** — captures interaction-aware importance, not
   just univariate variance reduction. SHAP is the gold-standard for
   model-agnostic per-feature attribution and is the de-facto "edge
   attribution" standard in the GTOS K-series (also used in K50).
2. **Bonferroni correction** across the canonical-feature family — the
   original code-comment explicitly stated "Bonferroni-style cost of
   testing ~12 canonical features at α=0.05 is not formally applied
   here — this is a screening tool". F5 closes that gap.
3. **Bootstrap 95% CI** — gives a sampling-error band per importance
   estimate so single-window noise can be triaged from real signal.

### Empirical comparison (smoke run on 129 filled trades, window=30)

The F5 CLI auto-detects an existing
``research/edge_decomposition/K51_decayed_original/trajectories.json``
sibling directory and writes a ``comparison.md`` block. On the smoke
run:

| Original (permutation, no Bonf) | Proper-method (SHAP, Bonf α=0.05) |
| --- | --- |
| 3 decayed, 0 newly important, 9 stable | 0 decayed, 0 newly important, 12 stable |
| Most decayed: displacement_quality (+97.5%) | (none survive Bonferroni) |
| direction +97.5%, kill_zone +65.0% | direction sign-flips: H2 importance ↑ vs H1 |

**Sign-flips between methods.** Three features that the original
flagged as decayed (`displacement_quality`, `direction`, `kill_zone`)
either reduce in magnitude under SHAP or **flip sign** (H2 mean
importance > H1 mean importance for `direction` and `kill_zone`).
Reading: under SHAP's interaction-aware lens, those features' H2
contribution to realised-R variance is comparable to or larger than
their H1 contribution. The univariate stratum-mean estimator was
catching marginal-mean shifts that don't survive a tree-model's joint
fit.

**No Bonferroni-surviving decay at this sample size.** With only 4
windows of 30 trades (2 per half) and a 12-feature family, the H1/H2
Welch's t-test cannot achieve `bonf p < 0.05` — the corrected
threshold demands `raw_p < 0.05/12 ≈ 0.004`, which requires either
larger-window data (more windows) or a much wider H1/H2 separation
than the live data shows. The comparison is the correct read: the
original K51's "decayed" features are **screening hints, not
significant signals**; under proper attribution + correction, no
single feature has yet collapsed.

This is the methodology lesson: K51 should be re-run as soon as the
trade record corpus grows past ~200 filled trades, ideally with
window=50 → 4-windows-per-half. Until then, treat every "decayed"
flag from the permutation path as a hypothesis to validate via the
proper SHAP + Bonferroni run, not as a confirmed decay.

---

## Threshold rationale

The 40% drop threshold is the original brief's pre-registered cutoff.
Under the F5 update, the threshold is now combined with a
Bonferroni-corrected significance gate. The dual gate trades off:

- **False positive rate**: a 40% importance drop on a 30-trade window
  with realistic per-trade R-variance has roughly a 10-15% probability
  under the null. The Bonferroni correction
  (`bonf_p = raw_p * family_size`) makes it conservative — at family
  size 12 and α=0.05, raw_p must be < 0.004 to clear the gate. With
  2 windows per half this is hard to clear; small-sample regimes
  default to "no significant decay" rather than over-claiming.

- **False negative rate**: a 30% drop is marked stable rather than
  decayed at threshold=0.40, regardless of significance.

K54 should re-screen with both thresholds and check robustness. The
CLI's `--threshold-pct` and `--alpha` knobs make this a one-line
change each.

---

## K50 + K51 relationship

K50 (causal edge attribution): one shot, full-population. Ranks the
canonical features by their R-attribution magnitude across **all
historical trades**. Output: ordered list of features by magnitude,
with confidence intervals.

K51 (decayed-component identification): same feature set, **rolling
windows over time**. Output: per-feature trajectory (with bootstrap
CI) + decay classification (with Bonferroni-gated significance).

The two modules share `extract_features`, `CANONICAL_FEATURES`,
`build_feature_matrix`, and the realised-R extraction helpers — when
K50 ships it imports these directly from
`src.research_infra.decayed_component_identifier` so the two views are
guaranteed apples-to-apples. Under the F5 update, both also share the
SHAP TreeExplainer pattern.

Cross-reading rule:

- If K50 ranks a feature **high** AND K51 flags it **decayed**: it's
  the active decay vector. Investigate the corresponding strata in
  prompt research / shadow-logger expansion (P68-P70). High-priority
  for K54 feature selection.
- If K50 ranks a feature **low** AND K51 flags it **decayed**: it was
  never load-bearing. Skip.
- If K50 ranks a feature **high** AND K51 flags it **stable**: it's
  the resilient backbone of the edge. Preserve through any prompt
  changes. Top candidates for K54 must-have features.
- If K50 ranks a feature **low** AND K51 flags it **newly
  important**: it's an emerging edge axis. Worth investigating in K54
  ensemble / regime-conditional models.

---

## K54 handoff

K54 (ML-classifier training, algorithmic-gate migration step 1) is the
downstream consumer of this module's output:

1. **Feature selection.** Use the union of K50's high-rank features and
   K51's stable + newly-important features as the K54 base feature
   set. Drop K51's decayed features unless K54's per-regime ensembling
   resurrects them.

2. **Train/test split.** K51 H1/H2 boundary is a defensible time-based
   holdout: train K54 on H1, validate on H2, measure regime-non-
   stationarity sensitivity.

3. **Per-regime ensemble.** When a feature is decayed at full-fleet
   level but stable within one regime (regime-conditional decay), K54's
   per-regime ensemble can preserve the edge. K51's outputs by
   themselves don't surface this — re-run K51 with a `--symbols` filter
   per regime to test.

4. **Calibration target.** K51's H2 mean importance per feature is the
   floor that K54's ML-classifier feature contribution should beat at
   minimum. If K54's ML attribution for the same feature falls below
   K51's H2 importance, the model is not learning what's available.

---

## CLI summary

```
python scripts/research/run_k51_decayed_components.py \
    --output-dir research/edge_decomposition/K51_decayed_proper_shap \
    --window 30 \
    --threshold-pct 0.40 \
    --alpha 0.05 \
    --method auto \
    --bootstrap-n-resamples 100 \
    --bootstrap-seed 0 \
    --ci-alpha 0.05
```

Knobs:
- `--method {auto, shap, permutation}` — `auto` picks SHAP when
  available. `shap` errors if SHAP is missing. `permutation` is the
  always-on deterministic fallback.
- `--alpha FLOAT` — Bonferroni significance threshold for the H1/H2
  importance-delta test family. Default 0.05.
- `--bootstrap-n-resamples INT` — within-window resamples for the 95%
  CI. Default 100. Set to 0 to skip the bootstrap.
- `--bootstrap-seed INT` — reproducibility seed for the resampler.
- `--ci-alpha FLOAT` — CI level (default 0.05 → 95% CI).

When the F5 CLI is run with `--output-dir <dir>` and a sibling
directory `<dir>/../K51_decayed_original/trajectories.json` exists, a
`comparison.md` block is auto-generated alongside `decay_report.md`.

---

## Schema

Trade dict (input)::

    {
        "trade_id": "...",
        "symbol": "XAUUSD",
        "candle_close_time": "2026-04-15T13:15:00Z",  # ISO-8601 UTC
        "direction": "LONG"|"SHORT",
        "framework": "ob_retest"|"fvg_fill"|"breaker_re_entry",
        "kill_zone": "london"|"ny"|"tokyo"|...,
        "daily_bias": "bullish"|"bearish"|"neutral",
        "sweep_quality": "clean"|"messy"|"none",
        "displacement_quality": "strong"|"weak"|"none",
        "setup_grade": "A+"|"A"|"B"|"C",
        "liquidity_pool_type": "asian_high"|"asian_low"|...,
        "planned_rr": 2.5,
        "mfe_r": 1.92,
        "mae_r": -0.4,
        "r_multiple": 1.89,                          # realized R
        # OR nested:
        "exit": {"realized_R": 1.89},
    }

TrajectoryPoint (output) — one per `(feature, window_index)`::

    TrajectoryPoint(
        feature="kill_zone",
        window_index=2,
        window_end_iso="2026-03-15T17:00:00+00:00",
        n=50,
        importance=0.082,
        ci_low=0.034,                # 2.5 percentile
        ci_high=0.131,               # 97.5 percentile
        method="shap_treeexplainer", # or "permutation_importance"
    )

DecayReport (output) — feature decay table includes raw_p,
bonferroni_p, survives_bonferroni, family_size::

    DecayReport(
        threshold_pct=0.40,
        alpha=0.05,
        family_size=12,
        h1_period=("2026-01-02", "2026-02-28"),
        h2_period=("2026-03-01", "2026-04-26"),
        decayed=(FeatureDecay(feature="setup_grade",
                              h1_mean=0.42, h2_mean=0.10,
                              drop_pct=0.762,
                              n_h1_windows=3, n_h2_windows=3,
                              raw_p=0.001, bonferroni_p=0.012,
                              survives_bonferroni=True,
                              family_size=12), ...),
        newly_important=(...),
        stable=(...),
        all_features=(...),
        n_total_windows=6,
        n_total_trades=300,
        method="shap_treeexplainer",
    )

---

## Out of scope

- No production-code modifications.
- No AI / Anthropic API calls.
- No multi-instrument joint attribution. Run per-instrument by passing
  `--symbols XAUUSD` etc. to surface fleet-wide vs instrument-specific
  decay.
- No regime-conditional decay split. Re-run with regime-restricted
  trades from the K51 input pipe.

---

## Caveats

- **Window-level noise.** Single-window importance is a single
  difference-of-MSE statistic on N trades; trajectories are inherently
  noisy. Read the trajectory shape AND the bootstrap CI, not single
  windows.
- **Post-trade leakage.** `mfe_r` and `mae_r` are post-trade outcomes
  (excursions during the trade), not entry-time predictors. Their
  importance is descriptive of the realized-R-shape relationship, not
  predictive. K54 should drop these from the predictive feature set.
- **Time-stamp granularity.** H1/H2 split is by window index, not
  calendar date. With non-uniform trade frequency, a calendar-date H1/H2
  could differ. The current implementation gives equal weight to each
  window which is appropriate for the importance question (each window
  is one observation of the importance statistic).
- **Bonferroni over the full family is conservative.** With small-N
  windows, the corrected α=0.05 demands raw_p < 0.004, which is
  difficult to achieve. This is intentional — under-power for
  marginal claims is a feature, not a bug. Re-run as the corpus
  grows.
- **Stratum-mean MSE penalty (permutation path only).** A feature with
  very-high cardinality (e.g. `liquidity_pool_type` with 8+ values
  across a 50-trade window) can artificially reduce stratum-MSE just
  by overfitting per-stratum means. The SHAP path is more robust
  (tree regressor regularises this); the permutation path remains as
  a fallback only.
- **No multi-instrument confound control.** Default mode joins all
  symbols. Cross-instrument trades have different R-baselines (XAUUSD
  has +0.30R/trade expectancy, GBPJPY raw less). The within-window
  baseline-mean centering partially absorbs this but per-symbol
  attribution is the principled fix — use `--symbols` to isolate.
