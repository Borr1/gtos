# B12 — Confidence Scorer Deep Autopsy

**Status:** Implemented (research-only; no production wiring).
**Owner:** Phase 1 research program (Wave 2B AI-behavior cluster).
**Falsifiability:** `pytest tests/research_infra/test_confidence_autopsy.py -v` passes.
**Out of scope:** AI calls, prompt edits, production-config edits, live confidence
data ingestion (the live trade index does not store the AI-emitted score).

## Why this exists

CLAUDE.md says `confidence_filter_mode: shadow` because the AI's emitted
`confidence_score` is a rubber stamp — "98% get confidence=80". That is the
**global** read on the live data. B12 is the conditional zoom-in: even when a
signal is uninformative on average, it can still be predictive within specific
operating regimes (e.g. high-grade NY setups in trending bull markets).

If we find ANY stratum where `Spearman(confidence, realized_R) >= 0.2` AND
the Bonferroni-corrected permutation p < 0.05 AND n >= 20, that stratum is a
**conditional re-deployment** candidate the CEO can evaluate (e.g. confidence-
weighted sizing within the predictive stratum, scorer ignored elsewhere).

If we find nothing, B12 supplies the rigorous "scorer is dead" evidence so
future feature-engineering tasks (K54) treat the scorer as noise rather than
re-test the same hypothesis.

## Stratum definition

A stratum is the cross-product of axis values. Default axes:

```
symbol, regime, kill_zone, framework, setup_grade
```

A trade is assigned to exactly one stratum. The stratifier groups trades by
their normalized stratum tuple, computes the Spearman rank-order correlation
between `confidence` and `r_multiple` within each stratum, and applies a
permutation test for the empirical p-value.

### Why `hour_of_day` is not in the default axes

Adding 24 hours blows the family size up to several thousand strata, which
over-corrects every individual p-value to ~1.0 even when a real signal exists.
The CLI exposes `--strata-axes` so the CEO can invoke a smaller-cross
hour-aware run when she has a directed hypothesis (e.g. "is confidence
predictive specifically in NY-open hour for XAUUSD?"); the default cross stays
defensive.

### Why `direction` is not in the default axes

LONG/SHORT skew is severe under the v1 detector (228 LONG vs 24 SHORT in the
backtest population). Stratifying by direction would push most SHORT cells
below the n=20 floor and reduce statistical power without adding insight.
Direction can still be added via `--strata-axes` once the v2 detector
generates enough SHORT trades.

## Spearman vs Pearson

We use **Spearman** (rank-order) instead of Pearson because:

1. The AI's confidence is on a coarse 0-100 integer-ish scale with most mass
   at 70-85 and heavy ties; Pearson assumes a continuous metric.
2. Realized R has a fat-tailed distribution (per memory
   `project_distributional_findings`: gold tail index xi = 0.35, ~6.2x more
   3-sigma events than Gaussian). Pearson is dominated by tail outliers in
   such a distribution; Spearman is rank-invariant and robust to fat tails.
3. The hypothesis "higher confidence => higher R" is a monotone hypothesis,
   not a linear-coefficient hypothesis. Spearman tests exactly that.

## Bonferroni rationale

We test K hypotheses (K = number of strata that pass `n >= min_n`). Under the
global null (no stratum is genuinely predictive) we expect roughly `alpha * K`
strata to clear `p < alpha` by chance. Bonferroni protects the family-wise
error rate at `alpha` by requiring `p_corrected = p_raw * K < alpha`.

We deliberately count ONLY the strata we tested in the family size — strata
that hit `INSUFFICIENT_N` or `DEGENERATE` are excluded from the family
because they did not consume a test. The resulting correction is exactly
matched to the number of look-aheads.

This is more conservative than the Benjamini-Hochberg FDR correction used in
some research code, but for a "should we re-deploy a production filter?"
decision the family-wise error rate is the correct discipline.

## Permutation test mechanics

The empirical null is built by shuffling `confidence` within the stratum
`n_perms` times and recomputing Spearman rho on each shuffle. The empirical
two-sided p is:

```
p = (count(|rho_shuffled| >= |rho_observed|) + 1) / (n_perms + 1)
```

The `+1` in numerator and denominator is the Phipson-Smyth correction
(Phipson & Smyth 2010) — without it the smallest possible p is 0 even though
zero shuffles meeting the threshold does NOT prove the population p is zero.

### Why permutation, not parametric

The Spearman p-value tables assume large-sample asymptotic normality of the
test statistic. At n=20-40 (typical stratum size for B12) the asymptotic
approximation under-states the p-value when ties are present. The
permutation test is exact under exchangeability, which holds whenever the
stratum's trades were not curated to share a confidence-R relationship.

## Threshold choices

| Threshold | Default | Rationale |
| --- | --- | --- |
| `min_n` | 20 | Hard agent-rule no.6 in CLAUDE.md ("Claiming significance at n < 20" is prohibited). |
| `alpha` | 0.05 | Bonferroni-corrected family-wise error rate. |
| `rho_threshold` | 0.2 | Effect size: a |rho| < 0.2 explains less than 4% of rank variance and is not actionable. |
| `n_perms` | 1000 | Floor at p_min = 1/1001 ≈ 0.001 so a Bonferroni'd corrected p of 0.001 * 50 = 0.05 still resolves. |

## Data sources

The CLI consumes two read-only sources:

1. `research/**/all_results.json` — research backtest slices. Confidence is
   parsed from the `raw_response` JSON blob (the AI emits `"confidence_score":
   72` inside a fenced ```json``` block); realized R sits on the row as
   `r_multiple` for filled trades.
2. `knowledge_base_backtest/sessions/*.json` — XAUUSD-only batch sessions.
   Each session has per-candle `confidence` directly + a per-session
   `trade_summary.r_multiple`. We attribute the trade outcome to the FIRST
   `CANDIDATE` in the session's `candle_evaluations`.

Live trade records (`knowledge_base/index/_trade_index.json`) are NOT loaded:
the index does not carry the AI-emitted confidence score (closing the
`project_trade_records_enrichment_gap` is a downstream task). Including the
index would silently zero confidence on every live trade and fabricate a fake
axis.

## K54 handoff

K54 is the feature-engineering task in the Phase 1 program. B12's predictive
strata (if any) are direct hints:

- A stratum with high `|rho|` and low corrected p tells K54 that
  `(symbol, regime, kill_zone, framework, setup_grade)` is a meaningful
  conditioning surface — feature interactions worth engineering.
- Conversely, if B12 finds zero predictive strata, K54 should treat
  `confidence_score` as a noise feature and not waste cycles on it.

The autopsy.json output carries every tested stratum (with rho + corrected p)
so K54 can pick its top-K conditioning slices directly.

## Files

- `src/research_infra/confidence_autopsy.py` — module (statistics + stratification).
- `scripts/research/run_b12_confidence_autopsy.py` — CLI runner.
- `tests/research_infra/test_confidence_autopsy.py` — test suite.
- `research/ai_behavior/B12_confidence/{autopsy.json, report.md}` — outputs.

## Reproducing

```bash
python scripts/research/run_b12_confidence_autopsy.py \
    --output-dir research/ai_behavior/B12_confidence
```

The runner is deterministic given the same input data + `--seed`. Re-running
with the same seed produces identical autopsy.json / report.md.
