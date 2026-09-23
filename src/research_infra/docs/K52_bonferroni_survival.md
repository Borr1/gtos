# K52 — Bonferroni-Survival Re-Test

## Purpose

CLAUDE.md's "Validated Numbers — Confirmed (survives Bonferroni)" table lists
five findings. Those numbers were minted on the H1 batch dataset. K52 re-runs
each test on the **current** dataset and reports whether each finding still
survives Bonferroni correction.

A finding that fails survival is a feature that has lost statistical
discrimination — a useful signal for K54 (downstream ML model: drop
non-discriminating features) and a flag that the headline number in CLAUDE.md
is now stale.

## The five baseline findings

| # | Finding | Baseline value | Baseline n | Baseline corrected p |
|---|---|---|---|---|
| 1 | XAUUSD WR vs breakeven | 62.0% | 129 | 3.42e-08 |
| 2 | OB zone advantage vs 80% pullback | +16.8 pp | 173 + 136 (sim) | 0.003 |
| 3 | US30 WR vs breakeven | 58.5% | 41 | 8.34e-03 |
| 4 | USDJPY WR vs breakeven | 75.8% | 33 | 1.96e-04 |
| 5 | FVG-in-impulse signal across 6 instruments | +7-20 pp | (per-inst) | 0.080 (Bonf upper bound on 0.016 sign-test) |

These five make up the canonical K52 family. Family size for Bonferroni is
**always 5** regardless of how many tests can be run on current data — the
Bonferroni divisor is the size of the *baseline family*, not the size of the
*currently-runnable subset*. This is the conservative pre-registered choice.

## Test specs (one per finding)

### 1. XAUUSD WR vs breakeven (`xau_wr_vs_be`)

**Kind:** one-sample exact two-sided binomial test (`binomial_test`).
**H0:** wins / n drawn from Binomial(n, 0.5).
**Inputs:** `data["xau_ob_retest"] = {"wins": k, "n": n}` or
`{"filled_trades": [{"r": ...}, ...]}`. A "win" is `r > 0`; BE counts as a
loss (matches GTOS WR convention).
**Decision rule:** SURVIVES iff `current_corrected_p < α` (default α = 0.05),
n ≥ 20.

### 2. OB zone advantage (`ob_zone_advantage`)

**Kind:** two-proportion z-test (`two_sample_wr_test`).
**H0:** OB-zone WR equals 80%-pullback WR on the same BOS-event population.
**Inputs:** `data["ob_zone_vs_baseline_80pct"] = {"ob_wins", "ob_n",
"base_wins", "base_n"}`.
The CLI re-uses the Test A rerun population (219 BOS events; OB sim 122/173,
80% baseline 73/136).
**Decision rule:** SURVIVES iff `current_corrected_p < α`.

### 3. US30 WR vs breakeven (`us30_wr_vs_be`)

Same shape as test 1, with `data["us30_ob_retest"]`.

### 4. USDJPY WR vs breakeven (`usdjpy_wr_vs_be`)

Same shape as test 1, with `data["usdjpy_ob_retest"]`.

### 5. FVG-in-impulse across instruments (`fvg_in_impulse`)

**Kind:** pooled two-proportion z-test on the union of per-instrument FVG-in-
impulse OB outcomes vs non-FVG OB outcomes — *plus* a sign-test on the count
of instruments with positive delta (matches the original CLAUDE.md citation).
**Inputs:** `data["fvg_in_impulse_per_instrument"] = {"<INSTRUMENT>":
{"fvg_wins", "fvg_n", "non_wins", "non_n"}}`.
**Reported in summary:**
- pooled `wins_a/n_a/wins_b/n_b/wr_a/wr_b/delta_pp` and the pooled-z `raw_p`
  (treated as the primary `current_raw_p` so the family is type-consistent),
- per-instrument `delta_pp` deltas,
- `sign_test_n_positive`, `sign_test_n_total`, `sign_test_raw_p`
  (binomial PMF of "k of N positive" under p=0.5).
**Decision rule:** SURVIVES iff pooled `current_corrected_p < α`. The sign-test
result is reported but is not the primary survival criterion (the original
CLAUDE.md raw p of 0.0156 was a sign-test; we re-emit it for transparency).

## Methodology

### Hypothesis and statistic per test

| Test | H0 | Statistic | Critical |
|---|---|---|---|
| WR vs breakeven (per instrument) | wins / n ~ Binom(n, 0.5) | exact two-sided binomial | corrected p < α |
| OB zone advantage | p_a == p_b on same population | pooled-variance two-proportion z | corrected p < α |
| FVG-in-impulse | pooled p_fvg == pooled p_non | pooled-variance two-proportion z | corrected p < α |

### Bonferroni correction

`current_corrected_p = min(1.0, current_raw_p × 5)`. Tests that cannot be run
(populator returns None — e.g. realized R unavailable for an instrument)
**still consume their α/5 share**. This punishes data-availability gaps in
the conservative direction (a finding gets no easier to survive just because
the data is missing).

### Status taxonomy

| Status | Trigger |
|---|---|
| `SURVIVES` | inputs available, n ≥ n_min, corrected p < α |
| `FAILS` | inputs available, n ≥ n_min, corrected p ≥ α |
| `INSUFFICIENT_N` | inputs available but n < n_min OR raw/corrected p non-finite |
| `NO_DATA` | populator returned None (no current-data inputs) |

## Interpretation guide

- **All 5 SURVIVE.** Edge unchanged at the validated layer. Decay (per item #4
  in CLAUDE.md) is concentrated in instruments / conditions outside this
  five-finding family.
- **Some FAIL.** Each failure is a feature that has lost discrimination on
  current data. Update CLAUDE.md "Validated Numbers" with the new corrected
  p, demote the finding to "Confirmed, does NOT survive Bonferroni" or
  "Backtest-only", and **K54 should drop / down-weight that feature** in the
  ML model.
- **Some INSUFFICIENT_N / NO_DATA.** This typically reflects the FTMO free-
  trial EA exclusion (no live fills on USDJPY / US30 yet). Re-run K52 after
  paid-challenge fills accumulate (≥30 per instrument) before drawing a
  decay-vs-baseline conclusion. Treat status as "we cannot tell yet" — not
  evidence for or against survival.

### K54 ML-model implications

K54 (the downstream ML feature-selection model) uses K52 outcomes as a
selection prior:

- A `SURVIVES` finding contributes its corresponding feature with full weight.
- A `FAILS` finding's feature is dropped or aggressively regularised: the
  signal that minted the feature has lost discrimination on current data.
- An `INSUFFICIENT_N` / `NO_DATA` finding's feature is held in reserve —
  not actively used, but not deleted. Re-run K52 quarterly; promote on
  re-survival.

## Caveats

- **Test methodology vs original.** CLAUDE.md's published p-values were
  computed by historical ad-hoc scripts; the exact test (Fisher exact vs
  exact binomial vs chi-square) and the underlying wins/n may differ from
  what K52 uses. K52 standardises on **exact two-sided binomial for one-
  sample WR vs breakeven** and **pooled-variance two-proportion z for two-
  sample WR comparisons** — explicit, reproducible, dependency-free. The
  baseline `corrected_p` and `raw_p` strings displayed in the report are
  the *published* numbers from CLAUDE.md; the *current* p-values are
  computed under K52's standardised tests. Differences therefore can
  reflect either real decay OR test-methodology drift; the report flags
  this in caveats and the baseline column is informational.
- **Realized-R availability.** Live trade-records under FTMO free-trial EA
  exclusion have `execution: null` and produce no realized R. The CLI
  therefore augments live data with the legacy `_trade_index.json` (live-
  format) and `trades_unified.csv` (Test-A-rerun population) — both XAU +
  GBPUSD only at the current state of the project. US30 / USDJPY / GBPJPY
  one-sample WR tests will status `INSUFFICIENT_N` / `NO_DATA` until paid-
  challenge fills accumulate.
- **OB-zone test is structural-WR not realized-R.** The Test A rerun used
  H1-simulation outcomes calibrated against real fills; the +16.8 pp delta
  is in calibrated WR not realized R. K52 keeps the same convention.
- **FVG-in-impulse uses structural WR.** The current-data inputs come from
  the per-instrument structural backtest scorecard
  (`research/instrument_expansion_2026-04-25/01_per_instrument_scorecard.csv`),
  not from realised trades — the original CLAUDE.md +7-20 pp lift was
  cross-instrument structural too. The CLI converts per-instrument FVG-fill
  vs OB-retest WRs into the populator's expected `{fvg_wins, fvg_n,
  non_wins, non_n}` shape.
- **Family size 5 is hard-coded.** This module's `FAMILY_SIZE` constant is
  pre-registered. Do not bump the family size to "include some new test"
  without writing a new ADR and amending CLAUDE.md's Validated Numbers
  table — adding tests post-hoc inflates the α budget without honest
  pre-registration.
- **Walk-level evidence is not predictive of realized R.** All one-sample
  tests use realized R per filled trade. Two-sample structural tests are
  flagged as such in the report and should not be conflated with realised-
  outcome tests when triaging decay (see
  `feedback_walk_level_evidence_not_predictive`).

## Re-run cadence

- **Every 30 days** while the FTMO challenge is active. Decay is the CEO's
  #1 concern; a stale baseline silently underwrites every Validated Number
  citation in CLAUDE.md.
- **Immediately after** any of: v1→v2 detector promotion, prompt rewrite
  affecting framework selection, or the addition of a new instrument with
  ≥ 20 live fills.
- **Update CLAUDE.md in the same commit** when the survival verdict for any
  finding changes.

## Output files

```
research/edge_decomposition/K52_survival/
  ├── survival.json   # SurvivalReport serialised; family_size, alpha, n_min,
  │                   # per-test inputs/outputs/summary
  └── report.md       # human-readable verdict block + per-test detail
```

## Related research

- `.context/01_knowledge_base/validated_numbers_caveats.md` — long-form
  notes on each finding and the H2-2026 decay context.
- `.context/03_analysis/test_a_rerun_real_bos_results.md` — Test A rerun
  source for the OB-zone advantage.
- `research/instrument_expansion_2026-04-25/02_DECAY_ANALYSIS.md` — H1/H2
  per-instrument decay diagnostic (orthogonal: structural metrics, not
  Validated-Numbers retest).
- `src/research_infra/decay_velocity.py` — A2 per-instrument decay slope
  with Bonferroni correction (different family — decay slopes per
  instrument, not Validated-Numbers retest).
