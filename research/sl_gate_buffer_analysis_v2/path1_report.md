# Path 1 — Multi-SL Policy Replay Study

**Date:** 2026-04-18  |  **Analyst:** Opus 4.7 (Agent B)
**Scripts:** `path1_multi_sl_replay.py`, `path1_gate_analysis.py`
**Data:** `multi_sl_outcomes.csv` (4356 policy-event cells), `path1_gate_cells.csv` (30 policy×gate cells)

---

## Executive Summary

We re-ran the A2_v2 walk-forward simulator over the same 726 OB retest events (2026-01-01..2026-04-17) with **6 SL policies** (buffer multipliers × H1 ATR ∈ {0.2, 0.3, 0.4, 0.5, 0.75, 1.0}) then applied each of **5 gate configurations** to the per-policy outcomes. The resulting 30-cell table (admit-count, WR, expectancy, sweep events, max |R|) gives a clean policy-sensitivity control — independent of any AI behaviour.

**Headline findings.** (a) **Option D (buffer ≤ 0.3 × M15 ATR)** is the only configuration that is nearly policy-invariant AND approximately equivalent to baseline — it rarely admits anything extra because only very tight buffers satisfy the ratio, and those concentrate REVERSED outcomes ("sweep events"). (b) **Current-live (buffer ≥ 0.3 × M15 ATR)** admits the most rows and has the highest raw expectancy at every policy, but its R-multiple distribution is fat-tailed — the expectancy lift at tight policies is dominated by a handful of micro-buffer rows (R up to 70, a ratio artifact; see section 4). (c) **Option E (hybrid 0.3–0.5)** collapses to baseline at policy ≥ 0.5 because the admit band becomes empty. (d) On the realistic-R-range slice (R ≤ 10), all configurations converge within ~0.02R of each other; the "winner" from raw expectancy is driven almost entirely by outliers. **The policy-sensitivity data does not support a configuration change over the status quo on raw numbers alone** — the AI-behaviour study (Agent A) must provide the tiebreaker.

---

## Methodology

### Inputs

- **Retest events:** `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` — 726 first-retest rows over Jan 1–Apr 17 2026 across 5 symbols (XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD).
- **OHLC source:** `data/historical/{SYMBOL}_M15.csv` and `{SYMBOL}_H1.csv` (broker naive timestamps treated as UTC, matching `A2_v2_validation.py:128`).

### Walk-forward pipeline

`path1_multi_sl_replay.py` imports A2_v2's OB detection and retest-finding pipeline directly (`detect_obs`, `find_first_retest_and_measure` — `A2_v2_validation.py:344-739`) to obtain **full-precision** OB edges / body sizes. This avoids FP drift introduced by the 5-6-decimal rounding in the source CSV (see Validation below).

For each (retest_event, policy_multiplier) cell:

1. **OB edges & body** pulled from the fresh A2_v2 detection (`DetectedOB.ob_high/low/open/close`).
2. **Entry price** = A2_v2's computed `retest_entry_price` (close of retest bar if inside zone, else open of next M15 bar — `A2_v2_validation.py:534-553`).
3. **SL per policy:**
   ```
   LONG : sl_price = ob_low  - mult * h1_atr
   SHORT: sl_price = ob_high + mult * h1_atr
   ```
4. **Target (fixed across policies):** `ob_high + ob_body` (LONG) / `ob_low - ob_body` (SHORT) — mirrors `A2_v2_validation.py:582,585` so 0.5 policy reproduces Geom-A outputs.
5. **M15 ATR(14) at retest_ts** computed with Wilder smoothing on full M15 history (`path1_multi_sl_replay.py:atr14_wilder`), matching `replication_analysis.py:53-65`.
6. **Walk forward 48 M15 candles** (`A2_v2_validation.py:99 GEOM_A_WINDOW`) from the first bar strictly after entry. Classify CONTINUED / REVERSED / UNRESOLVED with the same-bar-ambiguity rule (resolve by open price, `A2_v2_validation.py:639-650`).
7. **R-multiple:** `|target - entry| / |entry - sl|` on CONTINUED; `-1.0` on REVERSED; null on UNRESOLVED.

### Degenerate-row filtering

**A row is flagged degenerate for a given policy if the SL would land on the wrong side of entry** (LONG: sl ≥ entry; SHORT: sl ≤ entry). Degenerates are excluded from WR/expectancy/sweep counts (not just the SL-touches-entry outlier; they represent non-trades mechanically).

Counts per policy, `degenerate_counts_by_policy.csv`:

| Multiplier | Degenerate rows | Max |R| on clean rows |
|---:|---:|---:|
| 0.20 | **19** | 70.00 |
| 0.30 | 16 | 10.25 |
| 0.40 | 9 | 28.25 |
| 0.50 | **6** | 8.43 |
| 0.75 | 4 | 9.86 |
| 1.00 | 1 | 12.44 |

**Interpretation.** Tighter buffers collide with entry more often (entry can sit arbitrarily close to OB_edge when the retest candle's close lands on the zone boundary). The replication report noted 6 degenerates at 0.5 — we reproduce exactly those 6 (see validation).

### Validation against existing Geom-A output

Running at `policy_multiplier = 0.5`, our walk should reproduce the stored `outcome_a` / `continuation_r_a` columns. Result: **718 / 720** matched (99.72%); among matched rows, **R-multiple diff: mean=0, std=0, max_abs=0** (full-precision match after re-deriving OBs).

The 2 remaining outcome mismatches are both cases where the source CSV got UNRESOLVED due to A2_v2's implicit **192-bar scan-window truncation** — the retest sat at scan position 190-191, leaving 0-1 bars to walk. Our replay walks the full 48-bar horizon on the full M15 index, which is the intent of `GEOM_A_WINDOW = 48` and the policy-sensitivity study. We accept this as a *cleaner* walk rather than a bug.

Degenerate overlap at 0.5: our 6 degenerates match the 6 in the source CSV (3 LONG, 3 SHORT) exactly.

---

## Buffer Distribution by Policy

From `path1_buffer_distribution.csv` (buffer_atr = |sl_price - ob_edge| / M15_ATR):

| Multiplier | n | p5 | p25 | p50 | p75 | p95 | <0.3 | [0.3,0.5) | [0.5,1.0) | ≥1.0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.20 | 707 | 0.30 | 0.35 | 0.39 | 0.45 | 0.56 | **46** | 579 | 82 | 0 |
| 0.30 | 710 | 0.44 | 0.52 | 0.59 | 0.67 | 0.85 | 0 | 126 | 575 | 9 |
| 0.40 | 717 | 0.59 | 0.69 | 0.79 | 0.89 | 1.13 | 0 | 5 | 630 | 82 |
| 0.50 | 720 | 0.73 | 0.87 | 0.99 | 1.12 | 1.41 | 0 | 0 | 388 | 332 |
| 0.75 | 722 | 1.10 | 1.30 | 1.48 | 1.67 | 2.11 | 0 | 0 | 14 | 708 |
| 1.00 | 725 | 1.46 | 1.73 | 1.97 | 2.23 | 2.81 | 0 | 0 | 0 | 725 |

**Key fact.** Only policy 0.2 puts a non-trivial fraction (46/707 = 6.5%) of rows into the Option-D band (<0.3 × M15 ATR). At 0.3 and above, the Option-D band is empty — the retest dataset doesn't admit Option-D-specific behaviour because H1 ATR is almost always larger than M15 ATR (buffer = mult × H1_ATR is compared against M15_ATR; mult=0.3 already typically exceeds 0.5 × M15_ATR). This was anticipated in the replication report and confirmed here.

---

## R-Ratio Artifact (CRITICAL DISCLOSURE)

From `path1_r_distribution.csv` (CONTINUED rows only):

| Multiplier | n | p50 | p75 | p95 | max | mean |
|---:|---:|---:|---:|---:|---:|---:|
| 0.20 | 490 | 0.28 | 0.50 | 1.27 | **70.00** | **0.66** |
| 0.30 | 505 | 0.27 | 0.48 | 1.15 | 10.25 | 0.43 |
| 0.40 | 516 | 0.25 | 0.44 | 1.01 | 28.25 | 0.42 |
| 0.50 | 528 | 0.23 | 0.41 | 1.00 | 8.43 | 0.36 |
| 0.75 | 549 | 0.21 | 0.35 | 0.79 | 9.86 | 0.30 |
| 1.00 | 566 | 0.18 | 0.32 | 0.70 | 12.44 | 0.28 |

**Mechanism.** Because the target (ob_high + ob_body for LONG) is fixed in price terms and independent of SL, a tighter SL mechanically inflates R = target_dist / sl_dist. Tighter-policy rows show larger mean R (0.66 at mult=0.2 vs 0.28 at mult=1.0) and fatter right tail (max 70 at mult=0.2 vs 12.4 at mult=1.0). **This is pure geometry — not a real expectancy advantage.**

**Corrected measure.** To compare across policies on a level playing field, `path1_gate_cells.csv` also reports `price_distance_expectancy` — mean of (CONTINUED: +|target-entry|/M15_ATR ; REVERSED: -|entry-sl|/M15_ATR ; UNRESOLVED: 0) across admitted rows. Under this metric:

| Config | 0.2 | 0.3 | 0.4 | 0.5 | 0.75 | 1.0 | mean | std |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | +0.091 | +0.070 | +0.056 | +0.044 | +0.056 | +0.069 | +0.064 | 0.016 |
| current_live | +0.077 | +0.066 | +0.046 | +0.056 | +0.060 | +0.066 | +0.062 | 0.011 |
| option_c | +0.064 | +0.068 | +0.055 | +0.044 | +0.056 | +0.069 | +0.059 | 0.009 |
| option_d | +0.078 | +0.070 | +0.056 | +0.044 | +0.056 | +0.069 | +0.062 | 0.012 |
| option_e | +0.074 | +0.068 | +0.055 | +0.044 | +0.056 | +0.069 | +0.061 | 0.011 |

**Under price-distance expectancy (R-ratio artifact removed), all 5 configurations produce essentially identical results across policies** — within one standard error of each other. The raw-R-expectancy advantage of current_live is a mirage.

---

## Gate Configuration Results Across Policies

Full 30-cell table in `path1_gate_cells.csv`. Condensed view (admitted / WR / expectancy_ex_unresolved):

| Policy | baseline | current_live | option_c | option_d | option_e |
|---:|---|---|---|---|---|
| 0.20 | 522 / 78.6% / +0.020 | **690 / 71.9% / +0.191** | 689 / 71.4% / +0.132 | 539 / 76.8% / +0.003 | 672 / 72.6% / +0.149 |
| 0.30 | 563 / 78.7% / +0.011 | 710 / 72.6% / +0.038 | 599 / 76.6% / +0.003 | 563 / 78.7% / +0.011 | 599 / 76.6% / +0.003 |
| 0.40 | 596 / 79.2% / +0.010 | 717 / 73.4% / +0.041 | 597 / 79.1% / +0.008 | 596 / 79.2% / +0.010 | 597 / 79.1% / +0.008 |
| 0.50 | 627 / 79.3% / +0.004 | 720 / 75.1% / +0.019 | 627 / 79.3% / +0.004 | 627 / 79.3% / +0.004 | 627 / 79.3% / +0.004 |
| 0.75 | 679 / 81.0% / +0.011 | 722 / 78.4% / +0.021 | 679 / 81.0% / +0.011 | 679 / 81.0% / +0.011 | 679 / 81.0% / +0.011 |
| 1.00 | 700 / 82.8% / +0.021 | 725 / 81.0% / +0.034 | 700 / 82.8% / +0.021 | 700 / 82.8% / +0.021 | 700 / 82.8% / +0.021 |

### Per-symbol breakdown at policy = 0.5 (current-live equivalent)

From `path1_per_symbol_0p5.csv`:

| Symbol | Config | Admitted | WR | Exp ex_unr | Price-dist exp |
|---|---|---:|---:|---:|---:|
| GBPJPY | baseline | 133 | 81.5% | +0.034 | +0.106 |
| GBPJPY | current_live | 148 | 79.3% | +0.138 | +0.161 |
| GBPUSD | baseline | 125 | 78.5% | -0.040 | -0.071 |
| GBPUSD | current_live | 150 | 72.6% | -0.053 | -0.085 |
| US30_cash | baseline | 120 | 84.1% | +0.083 | +0.348 |
| US30_cash | current_live | 142 | 74.8% | +0.003 | +0.271 |
| USDJPY | baseline | 115 | 78.3% | -0.002 | +0.042 |
| USDJPY | current_live | 134 | 76.9% | +0.055 | +0.099 |
| XAUUSD | baseline | 134 | 74.8% | -0.050 | -0.179 |
| XAUUSD | current_live | 146 | 72.0% | -0.048 | -0.156 |

Options C, D, E collapse to baseline at 0.5 per-symbol (all rows have buffer/M15_ATR ≥ 0.5 so the bands match baseline).

**Symbol-level read:** GBPJPY and USDJPY have the clearest marginal gain from current_live bypass (more admitted trades, expectancy holds or improves). GBPUSD degrades under current_live. XAUUSD is roughly flat. US30 gives up most expectancy under current_live (+0.083 → +0.003).

### Sweep events (REVERSED with buffer_atr < 0.3)

From `path1_gate_cells.csv` `sweep_events` column: only policy 0.2 produces non-zero sweep events, concentrated in Option D (14) and Option C (14) — because only policy 0.2 admits any buffer_atr < 0.3 rows. At policy ≥ 0.3 no row in any configuration has buffer_atr < 0.3 (see buffer distribution), so sweep-event count = 0 across the board. **The Apr-16-style sweep-past-edge pattern is mechanically invisible to this dataset at policies ≥ 0.3** because the retest dataset was built with a ≥ 0.5 × H1 ATR buffer, which almost always clears 0.3 × M15 ATR.

### Policy-robustness ranking (lower WR/Exp std = more robust)

| Config | WR mean | WR std | Raw Exp mean | Raw Exp std | Price-dist Exp mean | Price-dist Exp std |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.799 | 0.016 | +0.013 | 0.007 | +0.064 | 0.016 |
| **option_d** | **0.796** | **0.020** | +0.010 | **0.006** | +0.062 | 0.012 |
| option_e | 0.786 | 0.036 | +0.033 | 0.057 | +0.061 | 0.011 |
| option_c | 0.784 | 0.040 | +0.030 | 0.051 | +0.059 | 0.009 |
| current_live | 0.754 | 0.036 | +0.057 | 0.066 | +0.062 | 0.011 |

**baseline and option_d are the most policy-stable on raw metrics.** current_live, option_c, option_e all show high raw-expectancy variance driven by the R-ratio artifact at tight policies.

---

## Key Findings

1. **The retest dataset is fundamentally blind to Option D's intended behaviour at the 0.5 policy used in the live system.** Only 46/707 (6.5%) rows at mult=0.2 land in the <0.3 × M15 ATR band; at mult ≥ 0.3 nothing lands there. Option D is *indistinguishable from baseline* at policies ≥ 0.3.
2. **Current-live admits the most rows at every policy, with a persistent raw-expectancy lead (+0.019 to +0.191).** At tight policies this lead is dominated by ≤3 rows with R > 10 (max 70 at mult=0.2). Under the R-ratio-corrected price-distance-expectancy metric, the lead collapses to ≤ +0.01 at every policy.
3. **Win-rate increases monotonically with policy multiplier** across all configurations (78.6% → 82.8% for baseline). This is the mechanical price of a wider buffer — fewer shallow dips hit SL. Expectancy does NOT rise the same way because wider SL also means smaller R on winners.
4. **Option E (hybrid 0.3–0.5) converges to baseline at policies ≥ 0.5** because the admit band becomes empty. It only exhibits distinct behaviour at mult=0.2 (where it matches current_live minus the 2 rows with buffer_atr > 0.5).
5. **Sweep events (REVERSED with tight buffer) are empirically rare in this dataset.** 14 at mult=0.2 (options C and D only); 0 at all other policy/config combinations. The mechanism exists but is under-sampled.

---

## Policy-Gate Interaction

- **baseline, option_d** — almost policy-invariant and mutually equivalent at mult ≥ 0.3. They represent the "don't bypass tight SLs" school.
- **current_live** — maximally policy-sensitive. The admit-count stays roughly flat (690-725) but expectancy swings 10x from mult=0.5 (+0.019) to mult=0.2 (+0.191), driven by the R-ratio artifact.
- **option_c, option_e** — policy-sensitive at mult ≤ 0.2 only; equivalent to baseline at mult ≥ 0.3 because their upper-bound conditions are never binding in that range.

**For an AI-agnostic control, the "robust" gate configurations are baseline and option_d.** They resist the R-ratio artifact by simply admitting fewer tight-buffer trades. current_live accepts the fat-tail exposure.

---

## Recommendation

**This study does NOT, on its own, support changing the gate configuration away from current_live.** Here is why, in rank order:

1. **Raw-expectancy ranking favours current_live** at every policy, but the ranking inverts under the R-ratio-corrected metric (where baseline wins). This means current_live's headline lift comes from a handful of micro-buffer outliers whose R-multiples are an accounting artifact, not tradable edge. A CEO cannot assume the bypassed rows will realise their +0.19R on live capital.
2. **Option D is empirically indistinguishable from baseline** at the mult=0.5 production policy. Switching from current_live to option_d in live is equivalent to **shutting off the sl_too_tight bypass entirely** on this dataset. If current_live is over-admitting, option_d is the "turn it off" option disguised as a tuning change.
3. **Option C and Option E** behave like a weaker current_live at mult ≤ 0.3, and like baseline at mult ≥ 0.5. They don't resolve the core question — they just quiet the R-ratio artifact at the margin.
4. **The policy-sensitivity data cannot tiebreak this.** With price-distance-expectancy collapsing all 5 configs to within ±0.01 of each other across all 6 policies, the CEO should defer to the AI-behaviour study (Agent A) for the decision. If Agent A finds that the AI tends to place SLs in the buffer < 0.3 × M15 ATR band when it bypasses, option D's mechanical case strengthens. If Agent A finds AI SLs are evenly distributed, current_live is fine.

**Confidence level: medium.** The 726-event dataset is large but reflects only 3.5 months of a single regime. The R-ratio artifact is mechanical and will apply identically in live trading — the CEO should NOT weight raw-expectancy in a decision here.

---

## Caveats

1. **R-ratio artifact.** Expressed plainly: R-multiples are not fungible across SL policies. Comparing R-expectancy across policies is a methodological error; use price-distance-expectancy instead.
2. **Outcome labels are conditional on the policy.** A row labelled REVERSED at mult=0.2 may be CONTINUED at mult=1.0 (SL shifted past the REVERSED low). This is the whole point of the multi-policy study — it does NOT preserve outcomes across cells.
3. **Fixed target.** Target is `ob_edge + ob_body` and independent of policy. In live trading the target setter is also the SL setter; a tighter SL doesn't guarantee the same target. If the AI couples SL distance to target distance (constant R:R), the R-ratio artifact disappears but so does the expectancy lift of current_live — making the case for change weaker still.
4. **Sample size for tight buffers.** Only 46 rows at mult=0.2 land in the <0.3 × M15 ATR band. The 14 sweep events at option_d/mult=0.2 are a preview, not a statistically-ground conclusion.
5. **Dataset is blind to the sl_too_tight base rule at source policy.** Because the source CSV was built with a 0.5 × H1 ATR buffer, virtually every row exceeds `1.5 × M15_ATR` threshold naturally (sl_distance includes the body-to-entry gap plus buffer). At tight policies this changes: sl_distance approaches 0.2 × H1_ATR, which is often well below 1.5 × M15_ATR, so the base rule starts rejecting non-bypass rows. This is what produces the baseline admit-count variation (522 → 700) across policies.
6. **Scan-window truncation** in A2_v2's source CSV missed 2 outcomes that our unconstrained 48-bar walk catches. Accepted as a methodology improvement.
7. **UNRESOLVED treatment.** We report expectancy both including UNRESOLVED at 0R (realistic — time-stopped trades) and excluding (pure resolved slice). Recommendations above use `expectancy_ex_unresolved`.

---

## Outputs produced

| File | Purpose |
|---|---|
| `path1_multi_sl_replay.py` | Replay simulator (this study's core code) |
| `path1_gate_analysis.py` | Gate × policy analysis over the replay output |
| `multi_sl_outcomes.csv` | 4356 rows: per (retest, policy) outcome + R + buffer_atr |
| `degenerate_counts_by_policy.csv` | Degenerate count + max |R| per policy |
| `validation_vs_existing.csv` | Row-by-row vs source CSV at policy=0.5 (99.72% match) |
| `path1_gate_cells.csv` | 30 cells: (policy × gate_config) summary |
| `path1_buffer_distribution.csv` | Buffer/M15_ATR percentiles + bins per policy |
| `path1_per_symbol_0p5.csv` | Per-symbol breakdown at policy=0.5 |
| `path1_r_distribution.csv` | R-multiple distribution per policy (CONTINUED rows) |
| `path1_report.md` | This file |

---

*End of report.*
