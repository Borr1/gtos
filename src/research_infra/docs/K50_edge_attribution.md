# K50 — Causal Edge Attribution (SHAP / Bayesian)

Research-only infrastructure that quantifies how much realised R per filled
trade attributes to each engineered edge feature. Output feeds **K54** ML
classifier feature engineering.

**Branch (F16 update):** `feat/research-f16-k50-proper-shap`
**Original branch:** `feat/research-k50-edge-attribution` (commit `44d0644`)
**Module:** `src/research_infra/edge_attribution.py`
**CLI:** `scripts/research/run_k50_edge_attribution.py`
**Tests:** `tests/research_infra/test_edge_attribution.py` (36 tests after
F16; 13 net-new for proper-SHAP / Bonferroni / bootstrap CI / `--alpha`)
**No AI calls.** $0 API cost. Pure-Python + NumPy (sklearn already a repo
dep; lightgbm / xgboost / shap optional with graceful fallbacks).

---

## Install requirement (F16 update — mirror of F5 for K51)

The proper-method (SHAP) path needs:

```
pip install "shap>=0.42" "lightgbm>=4.0" "scikit-learn>=1.3"
```

These are now declared in ``requirements.txt`` (research-only deps
section, added by F5 for K51 and re-used by F16 for K50). When they are
missing, K50 falls back to the original permutation-importance estimator
with no behaviour change beyond the ``method`` field on the output
reading ``"permutation_importance"`` instead of ``"shap_treeexplainer"``.

The CLI's ``--method`` flag exposes three modes:

- ``--method auto`` (default): SHAP when available, permutation
  otherwise.
- ``--method shap``: forces SHAP; raises ``RuntimeError`` if the
  ``shap`` package is missing.
- ``--method permutation``: forces the deterministic fallback (used in
  tests + low-dep environments).

---

## What this answers

> Of the realised R per trade, what fraction attributes to OB-zone advantage,
> displacement quality, FVG presence, touch_count, framework choice,
> kill-zone session, time-of-day, and regime?

Two complementary methods on the same target so we can sanity-check each
other:

1. **SHAP** — non-linear, per-trade attribution from a fitted gradient-boosting
   regressor. Captures interactions and threshold effects.
2. **Bayesian linear regression** — linear, monotone, with explicit posterior
   uncertainty. Conjugate normal-inverse-gamma; pure NumPy.

Spearman correlation between the two rankings is reported as a sanity check.

---

## Feature engineering rationale

Eight features per trade, computed deterministically by
`_trade_to_features()`:

| Feature | Type | Source field(s) | Rationale |
|---|---|---|---|
| `ob_retest_distance_atr` | continuous | `ob_retest_distance_atr` / `proximity_atr` / derived from `entry_price`, `ob_top`, `atr` | Captures "how deep into the zone" the entry sits — a proxy for OB-zone advantage strength. |
| `displacement_quality_score` | ordinal-as-continuous | `displacement_quality` ∈ {strong=1.0, medium=0.5, ambiguous=0.25, weak=0.0} | Continuation tends to follow strong displacement (Test A rerun, +17pp). |
| `fvg_present` | binary | `fvg_present` / `fvg_in_impulse` / `framework == fvg_fill` | Cross-instrument +7-20pp signal (Validated Numbers). |
| `touch_count` | integer | `touch_count` / `ob_touch_count` | ADR-005 (touch=2 H2-2026 Exp R = -0.688R; touch=1 = +0.022R). Probably a strong negative contributor in H2. |
| `framework_id` | categorical (int) | `framework` ∈ {ob_retest=0, fvg_fill=1, breaker_re_entry=2, none=-1} | Framework dispatch may carry uneven realised-R; surfaces multi-framework dispatch suppression. |
| `session_id` | categorical (int) | `kill_zone` ∈ {london=0, ny=1, tokyo=2, off=-1} | Kill-zone matters per Validated Numbers; LON vs NY decay separable. |
| `hour_of_day_utc` | integer | `candle_close_time` parsed → hour | Captures intra-window positioning (e.g. 13:00-13:15 NY skip). |
| `regime_tag` | categorical (int) | `regime_tag` / `regime` ∈ {trend_up=0, trend_down=1, range_high_vol=2, range_low_vol=3, unknown=-1} | Pragmatic V1 H4-swing classifier output (shadow-only); attribution shows whether labels matter for realised R. |

**Encoding choice:** categoricals are integer-encoded rather than one-hot.
This is fine for the GBM (tree splits handle ordinals), but the Bayesian
linear model treats them as ordinal — interpret Bayesian coefficients on
those columns directionally rather than as absolute effect sizes.

---

## SHAP vs Bayesian comparison

### SHAP (preferred path)

- Backend selection: `lightgbm` → `xgboost` → `sklearn.GradientBoostingRegressor`
  (first available wins; tagged on `model._k50_backend`).
- Explainer: `TreeExplainer` (fast, exact for tree models) → `KernelExplainer`
  (model-agnostic, slow) → permutation importance (terminal fallback).
- Aggregation: `mean |SHAP|` per feature → relative importance.
  `mean SHAP` per feature → directional impact (positive = on average raises R).

### Bayesian linear (sanity check)

- Standardise X (zero mean, unit std per column).
- Append intercept column (never standardised).
- Conjugate prior: `beta | sigma^2 ~ N(0, sigma^2/lambda)`,
  `sigma^2 ~ InvGamma(a, b)`. Default `lambda=1e-3`, `a=b=1e-3` → near-flat.
- Posterior mean and standard deviation per coefficient.
- Mode of `sigma^2` reported for noise calibration.
- Raw-space coefficient = `posterior_mean / std_of_X_column` → directly
  interpretable as "1 unit of feature → Y units of R".

### Spearman rank correlation
`spearman_rank_delta()` returns `r`, list of features in each ordering, and
the overlap count `n`. Production CLI reports this in `report.md` Caveats.

---

## Permutation-importance fallback

If `shap` is not installed, `compute_shap_attribution` falls back to
`sklearn.inspection.permutation_importance` with `n_repeats=10`,
`scoring="r2"`. The fallback returns a pseudo-SHAP matrix where every row
is identical (the per-feature permutation importance); `mean |SHAP|`
aggregation still produces correct rankings, but per-trade variability is
lost. Documented in module docstring.

This keeps the public interface identical regardless of optional-dep state.

The original K50 commit (`44d0644`) shipped its empirical findings under
this fallback (the local environment lacked `shap` at the time). The F16
re-run with proper SHAP **demotes the original ranking** — see the
methodology comparison below.

---

## F16 update — proper SHAP + Bonferroni + bootstrap CI

The F16 update mirrors F5's K51 update for K50. New behaviours:

1. **SHAP path enforcement.** `compute_shap_attribution(model, X, names,
   method="shap")` now forces the SHAP path; `RuntimeError` is raised
   when the `shap` package is unavailable rather than silently falling
   back to permutation.
2. **Bootstrap 95% CI per feature.**
   `compute_shap_attribution_with_ci(X, y, names, n_resamples=100)`
   resamples filled trades with replacement, refits the regressor,
   re-explains, and aggregates the per-feature mean |SHAP| distribution
   into 2.5/97.5 percentile bounds (`FeatureCI` dataclass). The CLI
   exposes `--bootstrap-n-resamples`, `--bootstrap-seed`, `--ci-alpha`.
3. **Bonferroni-corrected H1/H2 importance-delta test.**
   `h1_h2_importance_test(h1_dists, h2_dists, names, alpha=0.05,
   family_size=8)` runs a one-sided Welch's t-test on the H1 vs H2 mean
   |SHAP| bootstrap distributions per feature, then applies Bonferroni
   correction across the canonical-feature family (size 8).
   `family_size` defaults to `len(FEATURE_NAMES)`. `--alpha` (default
   0.05) controls the significance threshold. A feature is "decayed"
   when `delta > 0` AND `bonferroni_p < alpha`.
4. **Comparison block.** When `K50_attribution_proper_shap` is the
   output and the sibling `K50_attribution/ranking.json` exists, the
   CLI auto-emits `comparison.md` with the proper-SHAP-vs-original
   table.

The F16 patterns are byte-compatible with F5 (K51) — the `_betainc`
expansion, Welch's t-test, and Bonferroni helper all live in
`edge_attribution.py` mirrored from `decayed_component_identifier.py`
so the two K-series modules cannot drift on numerical conventions.

### Empirical findings (215-trade XAUUSD run, F16 proper-SHAP)

Run on `_trade_index.json` merged with `trades_unified.csv`, filtered to
XAUUSD, 215 filled trades, **`--method shap` forced**, 100 bootstrap
resamples. Output:
`research/edge_decomposition/K50_attribution_proper_shap/`.

| Feature | proper SHAP rel imp% | bootstrap 95% CI | mean SHAP | H1 vs H2 bonf p |
|---|---:|---|---:|---:|
| displacement_quality_score | 38.0% | [0.037, 0.241] | +0.0016 | **1.69e-05 (DECAYED)** |
| framework_id | 33.6% | [0.035, 0.216] | -0.0029 | 0.3766 (suggestive) |
| session_id | 28.4% | [0.025, 0.188] | +0.0013 | 1.0000 (stable) |
| ob_retest_distance_atr | 0.0% | [0, 0] | 0 | — |
| fvg_present | 0.0% | [0, 0] | 0 | — |
| touch_count | 0.0% | [0, 0] | 0 | — |
| hour_of_day_utc | 0.0% | [0, 0] | 0 | — |
| regime_tag | 0.0% | [0, 0] | 0 | — |

### Comparison: original permutation vs proper SHAP

| Feature | original mean importance% | proper SHAP rel imp% | rank delta | status change |
|---|---:|---:|---:|---|
| displacement_quality_score | 16.4% | **38.0%** | -1 | **became #1** |
| framework_id | **75.0%** | 33.6% | +1 | **lost #1 dominance** |
| session_id | 5.5% | 28.4% | +0 | promoted by joint attribution |
| hour_of_day_utc | 3.1% | 0.0% | +3 | demoted to zero under tree-SHAP |

**Verdict:** K50's original "framework_id 75% importance" verdict does
NOT replicate under proper SHAP. The dominant feature flips to
`displacement_quality_score`. `framework_id` keeps a non-trivial share
(33.6%) but loses #1 ranking and shows a slightly negative average
SHAP. `session_id` triples its relative share (5.5% → 28.4%) under
joint attribution because the GBM's tree splits assign credit
differently from the univariate permutation-MSE-reduction proxy.

This mirrors F5's K51 finding: 2/3 of the original "decayed" features
(`displacement_quality`, `direction`, `kill_zone`) sign-flipped or
weakened to "suggestive" under proper SHAP. The methodology lesson is
the same — **permutation importance without correction is a screening
tool, not a confirmatory feature ranking**.

### Bonferroni-corrected decay verdict

The H1 vs H2 importance-delta test (107 / 108 trades per half) flags
`displacement_quality_score` as the **only** feature surviving
Bonferroni at α=0.05 (raw p = 2.11e-06, corrected p = 1.69e-05). H1
mean |SHAP| 0.174 → H2 mean |SHAP| 0.123, a 30% drop. `framework_id`
shows a small drop (0.120 → 0.106) that does not survive Bonferroni
correction (corrected p = 0.38, "suggestive" status). All other
features are zero on both sides (legacy data sparsity, see caveat
below).

### Strategic implication for K54 feature engineering

1. **Drop `framework_id` from the K54 must-have list.** Under proper
   SHAP it is no longer dominant; the original 75-81% relative-importance
   number was an artifact of the univariate permutation estimator
   over-attributing variance to the single mostly-constant feature in
   the legacy schema.
2. **Promote `displacement_quality_score` to #1.** It survives both the
   bootstrap CI (lower bound 0.037, well above zero) AND the H1/H2
   Bonferroni-corrected decay test. K54 should treat it as the
   load-bearing feature and re-train any classifier ablations against
   its inclusion.
3. **`session_id` is a sleeper.** Hidden under permutation, surfaces
   strongly under tree-SHAP. K54 must include kill-zone as a feature
   with categorical encoding.
4. **Defer the four zero-imp features** (`ob_retest_distance_atr`,
   `fvg_present`, `touch_count`, `regime_tag`) until v1.1 trade-records
   backfill them — same caveat as the original K50 (legacy
   session-simulator schema does not populate them).

**Critical caveat — legacy data sparsity (unchanged from original).**
Four features hit zero |SHAP|: `ob_retest_distance_atr`, `fvg_present`,
`touch_count`, `regime_tag`. These columns are uniformly missing in the
legacy session-simulator schema and default to 0.0 / -1 in
`_trade_to_features`. Any conclusion about their real importance is
**deferred** until production trade-records (`v1.1` instrumentation)
supply non-trivial values. F16 does not fix this; it only sharpens the
attribution on the three features that DO have data.

---

## Interpretation guide

When reading the report:

- **`mean |SHAP|`** → magnitude only. Larger = the feature changes R more,
  in either direction.
- **`mean SHAP`** → average direction. Positive = feature on average pushes
  R up; negative = pushes R down.
- **`relative importance`** → that feature's `mean |SHAP|` as a share of
  the sum across features. Always sums to 100% within rounding.
- **`Bayesian rank`** → independent ranking from a linear model. Should
  roughly match SHAP (`spearman_r > 0.7` is healthy).
- **Bayesian `posterior mean ± std`** → for Bayesian standardised
  coefficients, ratios `mean / std > 2.0` are roughly "credibly nonzero"
  in Bayesian parlance.

**Decay diagnostic.** The H1/H2 split (sort all trades by date, split at
midpoint, run attribution on each half) surfaces features whose rank
dropped in H2. Reported in `report.md` as `Decayed since H1`. NOT a hard
gate — purely observational.

---

## K54 handoff

K54 is the "ML classifier replaces the AI gate" research door. K50 outputs
form the **feature inventory** that K54 trains over:

1. K54 reads `research/edge_decomposition/K50_attribution/ranking.json`.
2. Features with `mean_abs_shap >= threshold` (e.g. relative_importance ≥ 5%)
   become K54's input vector.
3. Features that ranked zero in K50 due to data sparsity (see caveat above)
   need a **data backfill pass** before K54 can use them. K54 brief should
   include a "feature availability" gate that fails if any selected feature
   has < 50% non-default coverage in the training population.

K50 does not propose system changes; K50 is a feature catalog.

---

## Out of scope

- Production code changes — K50 is offline analysis only.
- AI API calls — none.
- Causal identification at the level of "remove this feature → live R drops
  by X" — that requires shadow-run ablation (K54-adjacent), not SHAP.
  SHAP attribution is correlational under model assumptions, not
  counterfactual.

---

## File map

| Path | Purpose |
|---|---|
| `src/research_infra/edge_attribution.py` | Module: feature builder, GBM trainer, SHAP/permutation attributor, bootstrap-CI helper, Bonferroni-corrected H1/H2 importance test, Bayesian linear regressor, Spearman delta |
| `scripts/research/run_k50_edge_attribution.py` | CLI: load trades → fit → attribute → bootstrap CI → H1/H2 Bonferroni test → write artefacts |
| `tests/research_infra/test_edge_attribution.py` | 36 unit tests (23 original + 13 net-new for F16: SHAP path enforcement, bootstrap CI math, Bonferroni family, `--alpha` CLI flag) |
| `src/research_infra/docs/K50_edge_attribution.md` | This document |
| `research/edge_decomposition/K50_attribution/{shap_values.json, ranking.json, report.md}` | Original (permutation, no Bonferroni) outputs from commit `44d0644` — preserved for comparison |
| `research/edge_decomposition/K50_attribution_proper_shap/{shap_values.json, ranking.json, report.md, comparison.md}` | F16 proper-SHAP outputs |

## CLI summary (F16 update)

```
python scripts/research/run_k50_edge_attribution.py \
    --output-dir research/edge_decomposition/K50_attribution_proper_shap \
    --method shap \
    --alpha 0.05 \
    --bootstrap-n-resamples 100 \
    --bootstrap-seed 0 \
    --ci-alpha 0.05 \
    --symbols XAUUSD
```

Knobs:
- `--method {auto, shap, permutation}` — `auto` picks SHAP when
  available. `shap` errors if SHAP is missing. `permutation` is the
  always-on deterministic fallback.
- `--alpha FLOAT` — Bonferroni significance threshold for the H1/H2
  importance-delta test family. Default 0.05.
- `--bootstrap-n-resamples INT` — bootstrap resamples per feature for
  the 95% CI. Default 100. Set to 0 to skip the bootstrap.
- `--bootstrap-seed INT` — reproducibility seed for the resampler.
- `--ci-alpha FLOAT` — CI level (default 0.05 → 95% CI).
- `--no-comparison` — skip the auto-generated `comparison.md` block.
- `--original-ranking PATH` — explicit override for the original
  K50_attribution/ranking.json path.
