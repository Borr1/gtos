# B14 — Walk-Level vs Realized-R Systematic Study

**Status:** Implemented (research-only; no production wiring).
**Owner:** Phase 1 AI-behavior research program.
**Falsifiability:** `pytest tests/research_infra/test_walk_level_validator.py -v` passes (37 tests).
**Out of scope:** AI calls, prompt edits, production-config edits, gate changes.

## Why this exists

Memory `feedback_walk_level_evidence_not_predictive` records the observation
from session 39 that walk-level statistical evidence (touch-count walk-level
p=5e-16) does NOT translate into realized-R differences across strata — in
that case the touch=2 stratum actually BEAT touch=1 in realized R despite
losing the walk-level test in the opposite direction. The default policy
became: walk-level evidence is misleading; require realized-R validation
before any gate or prompt change.

B14 stress-tests that policy across the FULL family of walk-level signals
in MSO `raw_data`. The strategic question:

> Across all walk-level signals (touch count, OB-distance, FVG overlap,
> liquidity proximity, displacement quality, bias alignment, session,
> framework, regime, setup grade, etc.), is there ANY where the walk-level
> partition ALSO partitions realized R AND the direction matches?

A "yes" answer would identify candidate features for K54 (ML classifier
training pipeline) — they would be the rare walk-level signals that
empirically translate to realized R. A "no" answer reinforces the
default policy.

## Methodology

For each walk-level signal in the registry:

1. **Stratify** trades by signal value. Continuous signals are bucketed via
   the registered `label_fn`; categorical signals pass through verbatim.
2. **Per-stratum summary**: realized-R distribution (n, mean, median, total,
   WR, Wilson 95% CI on WR).
3. **Kruskal-Wallis test** on the stratum realized-R lists. Non-parametric
   (rank-based) — chosen over ANOVA because gold realized-R has fat tails
   (memory `project_distributional_findings`: ξ=0.35) and a single 1.5R
   outlier should not carry a stratum's mean.
4. **Bonferroni correction** across the family of TESTED signals
   (`p_corrected = min(1, p_raw * family_size)`). `INSUFFICIENT_N` signals
   do NOT inflate the family count — they were not actually tested.
5. **Direction-consistency check** — compare the walk-level a-priori
   ranking against the realized-R ranking. A signal where the realized
   ranking is opposite to the walk ranking is the FAILURE mode documented
   in memory `feedback_walk_level_evidence_not_predictive`.
6. **Status assignment**:
   - `SURVIVOR`: `p_bonferroni < 0.05` AND `direction_consistent is True`
   - `NON_PREDICTIVE`: tested but failed at least one criterion
   - `INSUFFICIENT_N`: fewer than 2 strata had `n >= min_stratum_n` (default 10)

## Signal registry

Each entry in `SIGNAL_REGISTRY` is a `(extract, label_fn, walk_ranking)` triple.

### Structural / micro-structure signals

| Signal | Source field(s) | Bucketing | Walk ranking (best → worst) |
| --- | --- | --- | --- |
| `touch_count` | `h1_opp_ob_touch_long`/`_short` (direction-aware), `h1_opp_ob_touch`, `touch_count` | `1` / `2` / `>=3` | `1` → `2` → `>=3` (ADR-005: fewer touches = stronger zone) |
| `touch_count_max_mso` | `mso_h1_ob_touch_counts` (max of list) | `1` / `2` / `>=3` | `1` → `2` → `>=3` |
| `ob_retest_distance_atr` | `ob_retest_distance_atr`, `mso_h1_nearest_ob_distance_atr` | `<0.3` / `0.3-0.6` / `0.6-1.0` / `>=1.0` | `0.3-0.6` → `<0.3` → `0.6-1.0` → `>=1.0` |
| `fvg_overlap_pct` | `fvg_overlap_pct` | `0-25%` / `25-50%` / `50-75%` / `>=75%` | `>=75%` → `50-75%` → `25-50%` → `0-25%` |
| `liquidity_proximity_atr` | `liquidity_proximity_atr` | `<0.5` / `0.5-1.0` / `>=1.0` | `<0.5` → `0.5-1.0` → `>=1.0` |
| `displacement_quality_score` | `displacement_quality_score` | `low(<4)` / `med(4-6)` / `high(>=7)` | `high(>=7)` → `med(4-6)` → `low(<4)` |
| `unmitigated_ob_count` | `mso_h1_unmitigated_ob_count` | `0` / `1-2` / `>=3` | `>=3` → `1-2` → `0` |
| `h1_fvg_unfilled_count` | `h1_fvg_unfilled_count` | `0-2` / `3-6` / `>=7` | `>=7` → `3-6` → `0-2` |
| `m15_clv_current` | `mso_m15_clv_current` | `lower-third` / `mid` / `upper-third` | None (mixed direction across LONG/SHORT cohort) |
| `m15_buy_fraction` | `mso_m15_bvc_buy_fraction` | `bear` / `balanced` / `bull` | None |
| `bias_alignment` | `bias_alignment` | `aligned` / `opposed` | `aligned` → `opposed` |

### Categorical signals (no a-priori direction)

| Signal | Source field(s) | Notes |
| --- | --- | --- |
| `session_id` | `session`, `kill_zone` | Off-hours dropped |
| `framework_id` | `framework`, `logger_framework`, `framework_id` | |
| `regime_tag` | `regime`, `regime_tag` | Production source: `mso_h1_structure_direction` proxy |
| `setup_grade` | `setup_grade`, `logger_setup_grade`, `out_setup_grade` | Walk ranking: `A+` → `A` → `B` → `C` |

## Interpretation rules

### How to read the verdict

* **Survivor count > 0**: The walk-level evidence policy in memory
  `feedback_walk_level_evidence_not_predictive` should be REFINED. At
  least one signal empirically translates to realized R. Add to K54
  feature priorities.
* **Survivor count = 0** (current state, 2026-04-26): Memory
  `feedback_walk_level_evidence_not_predictive` is REINFORCED. Walk-level
  signals are misleading priors. K54 should NOT use them as direct
  features without out-of-sample validation.
* **Most-predictive signal (smallest p)**: Surface even when not a
  survivor — this is the closest the family came to predictive, useful
  for follow-up depth analysis.

### Why direction consistency is required

A signal can hit `KW p < 0.05` while having a realized-R ranking that is
the opposite of the walk-level prior. That is a FALSE POSITIVE for a
walk-level claim — it means the strata DIFFER but the prior was wrong
about WHICH way they differ. Memory `feedback_walk_level_evidence_not_predictive`
documents touch-count as exactly this case: walk-level evidence said
`touch=1 > touch=2`, but realized R said the opposite. Such signals are
classified `NON_PREDICTIVE` even when the test is significant — the
walk-level prior is broken.

### Why insufficient-n signals don't inflate Bonferroni

The Bonferroni denominator is the count of signals that actually got a
KW result. If a signal had only 1 stratum with `n >= min_stratum_n`,
no test was performed and that signal cannot be a survivor — counting
it in the family would over-correct and miss real survivors elsewhere.

## Source data

Primary source (the validator's CLI loads first):

* `research/phase1_full_extraction/merged_data.jsonl` — 1142 logger rows,
  75 filled CANDIDATEs across XAUUSD + USDJPY. Carries every walk-level
  signal in MSO `raw_data` joined to `out_outcome` + `out_r_multiple`.

Secondary sources (sparser walk-level coverage; used to enlarge n on
categorical signals):

* `research/**/all_results.json` — backtest slice rows.
* `knowledge_base/index/_trade_index.json` — historical batch + live
  trade summary.

Trade dedupe is by `(symbol, candle_close_time, r_multiple)`.

## K54 handoff

Per the research program kickoff (`.context/02_session_handoffs/RESEARCH_PROGRAM_KICKOFF.md`),
K54 (ML classifier training pipeline) takes Phase 1 feature outputs as
inputs:

> "Train XGBoost/LightGBM on labeled CAND outcome data using Phase 1
> feature outputs (K50-53 SHAP features + B12 confidence conditionals
> + B14 walk-level survivors + H36-38 regime tags + Q72 spread context)."

The B14 contract for K54:

* If `report.survivors` is non-empty → those signal names are the
  HIGH-PRIORITY features for the K54 training set. Their realized
  rankings (in the `report.strata_by_signal` payload) tell K54 which
  stratum boundaries to encode (e.g. categorical for survivor signals
  vs continuous for non-survivors).
* If `report.survivors` is empty → K54 should NOT add walk-level signals
  as direct features without first validating against out-of-sample
  realized R. Instead K54 should rely on K50-K53 SHAP-derived features
  and outcome-conditional confidence (B12) for its primary feature set.

The `evaluation.json` payload is the canonical hand-off — K54 reads
`survivors` (list of signal names) + `strata_by_signal[<sig>]` (per-stratum
realized R + ranks) directly.

## Files

* `src/research_infra/walk_level_validator.py` — pure-Python module
  (no scipy). Public surface: `SIGNAL_REGISTRY`, `stratify_by_signal`,
  `kruskal_wallis`, `evaluate_signals`, `ValidatorReport`, `SignalReport`,
  `StratumRow`.
* `scripts/research/run_b14_walk_level_validator.py` — CLI runner that
  loads from `research/phase1_full_extraction/merged_data.jsonl` +
  research slices + trade index, evaluates the full registry, writes
  `evaluation.json` + `report.md`.
* `tests/research_infra/test_walk_level_validator.py` — 37-test
  coverage (stratify edges, Kruskal-Wallis hand-verified, Wilson CI,
  direction consistency, end-to-end planted survivor / null /
  flipped / insufficient-n cases, Bonferroni inflation, registry
  surface).
* `src/research_infra/docs/B14_walk_level.md` — this document.
