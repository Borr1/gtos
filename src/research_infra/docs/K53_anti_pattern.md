# K53 — Loser Anti-Pattern Classifier

**Module:** `src/research_infra/loser_anti_pattern.py`
**CLI:** `scripts/research/run_k53_loser_anti_pattern.py`
**Tests:** `tests/research_infra/test_loser_anti_pattern.py`
**Phase:** Phase 1 ($0 API; pure-Python clustering + classification)
**Branch:** `feat/research-k53-loser-anti-pattern` (initial)
**F3 follow-up branch:** `feat/research-f3-k53-source-stratified` (source-stratified re-run)

---

## SOURCE-CONFOUNDING CAVEAT (F3 — read first)

The original K53 (commit `2d3afa4`) ran a single k-means + classifier
across the joined `unified_filled_cands.jsonl` (217 rows = Phase 1 75 +
Tier 2 142). Result: **train AUC 0.996 → H2 holdout AUC 0.598** —
severe overfitting.

**Diagnosis (F3, 2026-04-27):** the schemas of the two sources are
different.
* Phase 1 rows (XAUUSD/USDJPY) carry the full MSO numeric panel
  (`mso_h1_nearest_ob_distance_atr`, `mso_h1_unmitigated_ob_count`,
  `displacement_quality_ord`, `bias_confidence_ord`, etc.).
* Tier 2 rows (EURUSD, GER40, NAS100, UK100, XAGUSD) carry only the
  parsed AI-response fields. Missing MSO fields are median-imputed to
  defaults (e.g. `ob_retest_distance_atr → 2.0`, ordinal qualities → 1.0).

The classifier picked up the imputed-vs-real numeric pattern as a
high-signal predictor, but that pattern is identity-of-source, not
identity-of-loss. The split is geometric (Phase 1 features distribute
differently from Tier 2 features), and a tree-based model finds it
in <100 estimators.

The F3 fix is two CLI flags + two module functions that cluster /
classify WITHIN each source so the schema gap cannot leak.

### Honest baselines (post-F3, gradient boosting on full feature set)

| Mode | Source(s) | n | train AUC | test AUC | H2 holdout AUC |
|---|---|---:|---:|---:|---:|
| Original mixed (commit `2d3afa4`) | phase1+tier2 | 217 | 0.996 | 0.526 | 0.598 |
| `--source-filter phase1` | phase1 | 75 | 1.000 | 0.208 | 0.400 |
| `--per-source` → `phase1` | phase1 | 75 | 1.000 | 0.208 | 0.400 |
| `--per-source` → `tier2` | tier2 | 142 | 1.000 | 0.679 | 0.511 |

The phase1 honest holdout is **0.40** — below chance. The model is
worse than random on H2 once the schema confound is removed, which is
the SYSTEM_DECAY signature already documented for A1 / K51 / K52.
Real anti-patterns do not surface in this dataset at this n.

---

## What this answers

Strategic question:

> Across the ~150+ losing trades in our historical record, do they cluster
> into a small set of identifiable anti-patterns (e.g. "high touch_count +
> low displacement + range regime")? If yes, those clusters are exactly the
> features the K54 ML classifier should attend to.

Direct precursor to **K54** — the ML classifier (gradient boosting +
walk-forward + per-regime ensemble). K53 produces the feature engineering
hints; K54 wires the trained model.

Memory `feedback_walk_level_evidence_not_predictive`: **walk-level features
vary per stratum, but realized R is the validation ground truth.** Our
loss label is `realized_r ≤ 0`, never gate-pass / gate-reject.

Memory `project_a1_dumb_baseline_verdict_2026-04-26`: A1 found the
mechanical-vs-AI gap stable across the year — SYSTEM_DECAY, not regime
decay. Losses are concentrated where AI selectivity broke; we expect
clusters to skew toward H2-2026 frequency.

---

## Methodology

### 1. Feature extraction

Same canonical features as K50 (causal edge attribution), projected from the
unified Phase 1 + Tier 2 jsonl
(`research/accepted_candidates_loser_mining/unified_filled_cands.jsonl`,
217 filled CANDIDATEs across 7 instruments, 101 losers).

| Feature | Source field | Encoding |
|---|---|---|
| `ob_retest_distance_atr` | `mso_h1_nearest_ob_distance_atr` | float, missing → 2.0 |
| `displacement_quality_ord` | `displacement_quality` | LOW=0, MEDIUM=1, HIGH=2; missing → 1.0 |
| `fvg_h1_unfilled_count` | `h1_fvg_unfilled_count` | int |
| `fvg_m15_unfilled_count` | `m15_fvg_unfilled_count` | int |
| `fvg_present` | derived | 1 if any FVG, else 0 |
| `touch_count` | `touch_count_at_eval` | int |
| `ob_touch_max` | `ob_touch_max` | int |
| `direction_matches_h1` | derived | 1/0 alignment with H1 structure |
| `hour_sin`, `hour_cos` | `hour_utc` | cyclic encoding |
| `day_of_week` | `day_of_week` | 0..6 |
| `framework_*` (3) | `framework` | one-hot {ob_retest, fvg_fill, breaker_re_entry} |
| `session_*` (4) | `kill_zone` | one-hot {london, ny, tokyo, off} |
| `regime_*` (2) | `mso_h1_structure_direction` | one-hot {bullish, bearish} |
| `sweep_quality_ord` | `sweep_quality` | 0/1/2 |
| `bias_confidence_ord` | `bias_confidence` | 0/1/2 |
| `fib_retracement_pct` | `fib_retracement_pct` | float |
| `risk_reward` | `risk_reward` | tp_distance / sl_distance |

24 features total; deterministic order. No look-ahead — every feature is
evaluable at the candidate-emission moment.

### 2. Loss filter

A trade is a "loser" when `realized_r ≤ 0`. Including the `r == 0` boundary
catches break-even-stop outcomes which a hard-gated `< 0` would split
inconsistently across rounding boundaries.

### 3. K-means clustering on losers only

* k searched over `k_range` (default `(3, 7)` — small to keep clusters
  human-interpretable; large enough to surface a "few distinct anti-patterns"
  hypothesis).
* Optimal k chosen by silhouette score (Euclidean distance, mean
  coefficient over all loser points).
* Random restarts (`n_init=10`) with k-means++ seeding.
* `prefer_sklearn=True` by default; falls back to in-house Lloyd's
  algorithm + silhouette implementation when sklearn is unavailable.

Silhouette interpretation:
* `> 0.5`: strong cluster structure → anti-patterns are real and distinct.
* `0.25 - 0.5`: moderate / partial structure.
* `< 0.25`: weak structure → losses do not separate cleanly. The classifier
  importance ranking matters more than the cluster centroids.

### 4. Per-cluster reporting

For each cluster:
* Size, centroid, mean realized R, top-3 distinguishing features by
  absolute deviation from population centroid.
* Per-instrument breakdown.
* Per-time-half breakdown (H1 / H1.5 / H2).
* H2-2026 frequency within cluster (rows whose timestamp is ≥
  `--time-slice` flag, default `2026-03-01`).

### 5. Binary classifier (loss vs win, full population)

Trained on all 217 filled CANDs.

* Default: `GradientBoostingClassifier` (n_estimators=100, max_depth=3).
* Falls back to L2-regularized logistic regression when sklearn is
  unavailable, or when `--no-sklearn` is passed.
* Reports:
  * `train_auc` — in-sample after fit (upper-bound reference, NOT a
    generalization metric).
  * `test_auc` — random-split held-out test (default 25%).
  * `holdout_auc` — time-slice held-out test (rows with timestamp ≥
    `--time-slice`).
  * `regime_stationarity_ratio = holdout_auc / test_auc`. **< 0.85
    implies meaningful regime drift between H1 and H2 — the
    SYSTEM_DECAY signature when paired with A1's verdict.**
  * Per-feature importance (sorted descending by absolute LR coefficient
    or GBM impurity-decrease).

### 6. Time-slice cross-validation rationale

Regime non-stationarity is the **number-one risk** for any anti-pattern
classifier:
* H1-2026 XAUUSD WR was 64.5% (n=31).
* H2-2026 XAUUSD WR is **24.0%** (n=25). χ² p=0.006.

A classifier trained on H1+H2 random-split data may memorize signals that
do not generalize. The held-out time slice (default H2-2026) is our
honest generalization test. If `holdout_auc << test_auc`, the
"anti-patterns" are time-bound and K54's training pipeline must use
walk-forward splits, not random splits.

---

## Outputs

Written to `--output-dir` (e.g.
`research/edge_decomposition/K53_anti_pattern/`):

| Path | Content |
|---|---|
| `clusters.json` | Per-cluster size / mean R / centroid / top-3 features / instruments / halves / H2 frequency |
| `classifier_metrics.json` | Train AUC, test AUC, holdout AUC, regime ratio, per-feature importance |
| `feature_matrix.json` | Exported feature matrix (auditable; one row per filled CAND) |
| `anti_pattern_report.md` | Human-readable verdict (mandate format) |

When `--per-source` is set, the four files above appear under each
source subdirectory (`<output-dir>/<source>/...`) and an additional
top-level `per_source_summary.json` aggregates the per-source metadata
+ AUCs.

---

## F3 source-stratified flags + module API (added 2026-04-27)

### CLI flags

| Flag | Behavior |
|---|---|
| `--source-filter {phase1,tier2,all}` | Single pass restricted to one source tag. `all` (default) reproduces the original mixed-source K53. Use `phase1` for the honest baseline on the 75 full-MSO rows. |
| `--per-source` | Independent runs per source tag. Outputs land at `<output-dir>/<source>/`. Mutually exclusive with `--source-filter`. Sources below `--min-rows-per-source` (default 20) or `--min-losers-per-source` (default 8) are silently skipped. |
| `--min-rows-per-source` | Threshold below which `--per-source` skips a source's classifier (default 20). |
| `--min-losers-per-source` | Threshold below which `--per-source` skips a source's clustering (default 8). |

### Module API

Two new pure functions in `src.research_infra.loser_anti_pattern`:

* `cluster_losers_by_source(loser_features, sources, k_range=...) -> dict[str, ClusterReport]`
  — clusters within each source independently. Sources below
  `min_n_per_source` (default 8) return a sentinel `ClusterReport`
  with `k=1, silhouette=0.0` so callers can render the empty case
  without branching.
* `train_loss_classifier_per_source(X, y, sources, ...) -> dict[str, ClassifierReport]`
  — trains one classifier per source. Sources below `min_n_per_source`
  (default 20) are absent from the returned dict; same for sources
  with single-class y.

### When to use each mode

* **`--source-filter phase1`** — when you need the honest XAUUSD/USDJPY
  baseline. This is the F3 default for the K53 follow-up: 75 rows is
  small but every numeric feature is real (not imputed).
* **`--source-filter tier2`** — observational read on the 142 Tier 2
  rows (EURUSD, GER40, NAS100, UK100, XAGUSD). The MSO-numeric features
  carry imputed defaults so the classifier signals are mostly
  framework / kill-zone / hour patterns. Useful for cross-instrument
  generalization checks; not authoritative on its own.
* **`--per-source`** — when you want a side-by-side comparison without
  re-running the CLI twice. Writes both source dirs + the aggregate
  summary in one pass. **This is the canonical K54-handoff layout.**
* **`--source-filter all`** (default) — reproduce the original
  confounded baseline. Useful only for parity checks against commit
  `2d3afa4`. NOT a generalization metric.

---

## Hard rules

* No production-code dependencies (only stdlib; sklearn optional).
* No AI / Anthropic API calls.
* Read-only inputs:
  `research/accepted_candidates_loser_mining/unified_filled_cands.jsonl`.
* `realized_r` is the ground-truth label — never walk-level outcomes.

---

## K54 handoff

K54 wires the actual ML classifier into the live system as a shadow gate.
The K53 outputs become K54's inputs:

1. **Feature engineering hints** — `feature_importance` from K53's
   `classifier_metrics.json` ranks the 24 features. K54's gradient
   boosting model should:
   * Drop features with importance < 0.01 (zero-information).
   * Boost the top-5 importance features into the per-regime ensemble
     (one model per regime tag, weights blended at inference).

2. **Cluster signatures as labeled rules** — each cluster's top-3
   distinguishing features are a candidate "anti-pattern rule":
   `(touch_count ≥ X) ∧ (displacement ≤ Y) ∧ (regime = range)`. K54's
   walk-forward training compares its learned tree paths against these
   hand-derived rules; rules that match a tree path with high purity
   become first-class hard rejection candidates (K55 wire decision).

3. **Walk-forward-vs-random AUC gap** — if K53's
   `regime_stationarity_ratio < 0.85`, K54's training pipeline MUST
   use walk-forward splits (purged k-fold or expanding window). Random
   splits are not acceptable for K54 in that case.

4. **H2-2026 most-actionable cluster** — the cluster with highest
   H2 frequency tells K54 which anti-pattern to weight most heavily.
   This is the anti-pattern most likely to appear in the next 30 days
   of live trades.

---

## Caveats

* **n=101 losers is a small population for clustering.** Silhouette
  scores below 0.25 are likely on real data; the classifier importance
  ranking is the more durable signal.
* **Per-instrument power is limited.** XAUUSD has 30 losers (largest
  sample); EURUSD has 4. Per-instrument cluster results are not
  reliable below n=20.
* **The unified jsonl conflates Phase 1 + Tier 2 schemas.** Phase 1
  rows have full MSO numeric features; Tier 2 rows have parsed
  AI-response features. We median-impute missing fields, but a
  classifier trained on the joined matrix WILL pick up the source
  difference as a confounding signal — confirmed by F3
  (2026-04-27, see top-of-doc caveat). Always run with
  `--source-filter phase1` or `--per-source` for honest H2 holdout
  AUC. The mixed `--source-filter all` mode is parity-only.
* **Random `seed` matters at small n.** Cluster assignments are
  stochastic at this sample size. Set `--seed` for reproducibility;
  reproduce results with multiple seeds before drawing conclusions.
* **Feature 0 (`ob_retest_distance_atr`) defaults to 2.0 when missing.**
  Tier 2 rows lack this field, so 142 of 217 rows carry the imputed
  value. This default-vs-real divergence is the main mechanism
  driving the source confound in mixed-mode runs.
* **F3 phase1 holdout AUC = 0.40 is below chance.** With the schema
  confound removed, the classifier does worse than random on H2
  rows. This is consistent with A1's SYSTEM_DECAY verdict —
  H1 anti-pattern features do not transfer to H2. **Do NOT ship a
  K54 hard gate based on the mixed-source AUC = 0.598.** The honest
  generalization signal is 0.40, and a hard gate at that level
  would cost expectancy on real H2 trades.
