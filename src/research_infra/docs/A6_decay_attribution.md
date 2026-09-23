# A6 — Bayesian Decay Attribution

**Question.** Given the Wave 2A SYSTEM_DECAY verdict (A1: AI-vs-mechanical gap eroded H1->H2), decompose the WR loss across components (OB-zone, displacement, FVG, touch_count, framework, session, side, regime). How much of the H1->H2 decay attributes to each? Which is the dominant driver?

**Output.** `(component, value) -> {n, wins, WR, posterior, 95% CI}` per period, plus a per-component decay attribution number with credible interval and Bonferroni-corrected p-value. Sanity check: sum of attributed decays compared to observed delta.

---

## Inputs

| Source | Purpose |
|--------|---------|
| `research/decay_diagnostic/A1_dumb_baseline/results.jsonl` | Per-CAND mechanical-vs-AI realized R (133 XAUUSD entries; 33 with AI realized R; 28 in H1 / 5 in H2). |
| `research/**/all_results*.json` | The richer realized-R corpus that produced the A2 / F3 / instrument_expansion / lira / v4 / b_deep_audit / dumb_momentum / monthly_decay outputs. **107 XAUUSD 2026 CANDs with realized R** — this is the default A6 source. |
| `research/decay_diagnostic/A5_regime_matrix/cands_with_regime.jsonl` | A5's per-CAND regime tag (joined on `(symbol, candle_close_time)`). 107/107 match against `all_results` because A5 is built from that same corpus. |
| `knowledge_base/index/_trade_index.json` | KB trade index. Joined on `(symbol, date)` to populate `displacement_quality`. **No 2026 trade-index rows carry displacement_quality** — coverage zero on the decay window. |

The brief's mention of `knowledge_base/trades_unified.csv` is preserved for forward compatibility; the file does not exist in the current tree. "File not found is acceptable" per CLAUDE.md.

The brief also references `knowledge_base_backtest/sessions/` — these are richer per-session JSONs but they don't carry `touch_count` / `fvg_present` / `displacement_quality` per CANDIDATE row either (their `candle_evaluations[]` records `decision`, `setup_grade`, `framework`, `confidence`, `kill_zone`, `trade_id` only).

---

## Why two source modes (`--source all_results | a1`)

The script defaults to the `all_results` source because it carries the population that matches the H1->H2 decay finding the brief is asking about. The A1 source is preserved for cross-validation but exposes a thinner sample (33 / 107) and is the right source if the user wants the AI-vs-mechanical-arm comparison cohort.

Concretely:

* `--source all_results` (default): 107 XAUUSD CANDs with realized R. H1 n=63, H2 n=44. Observed WR delta: +8.98pp.
* `--source a1`: 33 XAUUSD CANDs with realized R. H1 n=28, H2 n=5. H2 sample too thin for any per-component stratification.

---

## Bayesian model

### Posterior

For each `(period, component_value)` stratum we model wins as Binomial(n, p) with a Beta(prior_a, prior_b) prior. The conjugate posterior is:

    p | data ~ Beta(prior_a + wins, prior_b + losses)

### Default prior: Beta(1, 1)

Beta(1, 1) is the uniform-on-[0, 1] prior. Subjective alternatives we considered and rejected:

| Prior | Rationale | Why rejected |
|-------|-----------|--------------|
| Beta(1, 1) (uniform) | Non-committal; data drives the posterior. | **Chosen.** The diagnostic question is whether the H2 distribution differs from the H1 distribution; we want the data to dominate the posterior. |
| Beta(0.5, 0.5) (Jeffreys) | Translation-invariant; standard "non-informative" alternative. | Marginally different from uniform; the difference is invisible at our sample sizes (n ~ 30-60 per stratum). Pick the simpler one. |
| Beta(7, 3) (informed: ~70% OB-edge baseline) | The project's published OB-zone WR baseline. | An informed prior would partially **mask** the very decay we're trying to detect. The point of A6 is to ask whether H2 differs from H1 — not to ask whether H2 differs from the prior. |

The rejected alternatives are documented in this file (per memory `feedback_decision_preservation.md`) so a future operator can re-run with a different prior if they want a sensitivity analysis.

### 95% credible interval

For each per-stratum posterior we compute a two-sided equal-tailed 95% credible interval. We use `scipy.stats.beta.ppf` if SciPy is installed; otherwise we fall back to a bisection on the regularised-incomplete-Beta CDF computed via a Lentz-style continued fraction. Both paths agree to <=1e-6 on hand-verified cases.

For the **per-component attributed decay** we compute a Monte Carlo credible interval: for each of the 4000 draws we sample WR_h1 ~ Beta_h1 and WR_h2 ~ Beta_h2 for each used stratum, recompute `sum( (WR_h1 - WR_h2) * n_share_h2 )`, and take the 2.5% / 97.5% quantiles over the sample. The seed (default `20260426`) is deterministic so reruns are bit-stable.

---

## Attribution arithmetic

For component `c` with strata `s_1, s_2, ..., s_k`:

    attributed_decay(c) = sum_strata( (WR_h1(s) - WR_h2(s)) * n_share_h2(s) )

where:

* `n_share_h2(s) = n_h2(s) / sum_used( n_h2 )` — H2 weighting so each component's attribution sums to a value comparable to the observed H2-vs-H1 WR delta.
* The sum is over **strata used in the attribution**: those where BOTH `n_h1 >= LOW_N_THRESHOLD` AND `n_h2 >= LOW_N_THRESHOLD` AND `value != MISSING_VALUE`.

Strata that fail any of those conditions are reported separately in `skipped_strata` with the reason (`LOW_N_H1` / `LOW_N_H2` / `ABSENT_H1` / `ABSENT_H2` / `MISSING_BOTH`) so the reader can distinguish "this stratum had no data" from "this stratum had data but was below the n floor."

### Sanity check: total vs observed

We expect `sum_components(attributed_decay) ~ observed_delta * family_size` if components were a partition with no overlap — but they aren't (each component is its own complete decomposition). The right comparison is:

* `mean_components(attributed_decay) ~ observed_delta` — averaging across components recovers the observed delta in expectation.
* `residual_pp = observed_delta - mean(attributed_decay)`.

A large positive residual would mean the components in the family don't capture the dominant driver; a large negative residual would mean some components OVER-explain (typical when one component is well-correlated with the period split, e.g. `bias` here).

For the default XAUUSD run on 107 trades:

| Quantity | Value |
|---------:|---:|
| Observed delta | +8.98pp |
| Mean attributed across 11 components | +12.68pp |
| Residual | -3.70pp |

The mild over-attribution is consistent with `side` and `bias` being effectively two views of the same underlying signal (LONG-only H1 vs split-direction H2), each fully explaining the decay on its own.

---

## Bonferroni correction

We compute a per-component chi-square heterogeneity p-value across used strata (sum of 2x2 chi-squares, df = number of used strata) and apply Bonferroni: `bonf_p = min(1.0, raw_p * family_size)`. This is the standard family-wise error correction applied across the component-attribution family.

For the default run: only `side` (raw_p=0.0051, bonf_p=0.0560) and `bias` (raw_p=0.0061, bonf_p=0.0673) come close to the conventional 0.05 threshold post-correction. Both are at the boundary — we report them as **suggestive** rather than confirmed at the family-wise level.

---

## Components attributed in the default run

| Component | Source | Notes |
|-----------|--------|-------|
| `framework` | A1 / all_results | Single-stratum (`ob_retest`) on this dataset. Provides whole-sample H1 vs H2 baseline only. |
| `kill_zone` | A1 / all_results | london / ny. Plays the role of "session" from the brief. |
| `side` | A1 (all_results: from `direction`) | LONG / SHORT. Strongest decay driver in this dataset. |
| `ob_zone` | Synthesized from `framework` | `ob_pullback` for `ob_retest`, `other` otherwise. NOT a per-CAND OB-zone-quality measurement. |
| `displacement_quality` | trade_index | 0/107 matched in 2026 — surfaces as `MISSING_VALUE` (skipped from sum). |
| `fvg_present` | Synthesized from `framework` | `no_fvg_required` for `ob_retest`, `fvg` for `fvg_fill`. NOT a per-CAND FVG-detection signal. |
| `touch_count` | (data gap) | Not joinable from A1 / A5 / sessions — surfaces as `MISSING_VALUE` (skipped from sum). |
| `setup_grade` | A5 / all_results | A / A+ in this corpus. |
| `bias` | all_results | bullish / bearish. Mirror image of `side` here. |
| `l2_passed` | all_results | Single-stratum (`pass`) because only L2-passed CANDs reach realized R. |
| `regime` | A5 | bullish / bearish / transitional / UNTAGGED. ~70% of A5-tagged XAUUSD entries are UNTAGGED in 2026. |

---

## Data gaps (acknowledged)

The brief asks for OB-zone, displacement, FVG, touch_count, framework, and session attribution. Of these:

* **session**: covered by `kill_zone`.
* **framework**: covered by `framework`.
* **OB-zone**: only a coarse synthesized proxy is available. A real OB-zone measurement would need a per-CAND zone classification (premium/discount, distance from equilibrium, MFE-into-zone, etc.) that none of the joined sources expose.
* **displacement**: only available for ~28/105 historical XAUUSD trades, ZERO of which fall in the 2026 H1/H2 window. The component fires `MISSING_VALUE` and is excluded from the sum.
* **FVG**: only a coarse framework-proxy. A real FVG-presence measurement would need per-CAND market_state inspection.
* **touch_count**: not joinable from any of the sources the brief listed.

These gaps are **acknowledged in the report** and would close if a future K-task pre-computes per-CAND market_state features and snapshots them into a joinable JSONL.

---

## Walk-level vs realized R

Per memory `feedback_walk_level_evidence_not_predictive`, this module operates on **realized** R-multiples joined per `(symbol, candle_close_time, side)`. Walk-level decision counts (gate-pass / reject) are not used for attribution. Each component's per-stratum WR is the realized win-rate on the cohort of trades that actually reached an outcome — not the count of walk-level decisions that passed the gate.

This matters because the H1 vs H2 split changes both the walk-level decision distribution AND the realized R distribution, and the dominant driver was confirmed by Track A walk-level evidence (`p=5e-16` on touch-count decay) but **reversed** under realized-R analysis (`touch=2 Exp +0.30R > touch=1 +0.04R`). A6 is the realized-R pass.

---

## Reproduction

    python scripts/research/run_a6_decay_attribution.py \
        --output-dir research/decay_diagnostic/A6_attribution \
        --source all_results

Outputs:

* `attribution.json` — full machine-readable per-component decay decomposition with all per-stratum stats and CIs.
* `report.md` — markdown verdict + caveats + methodology.

The script is offline-only, $0 spend, deterministic given the same input corpus and `--ci-seed`.
