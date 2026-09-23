# T3 — Batch Hypothesis Tests: Feature Thresholds & Structural Filters
## For: Claude Code execution agent (Sonnet, max effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor (Opus)
## Basis: phase1_edge_optimization_papers_v1.md (L3, 78 papers), T2a results (121-trade feature analysis)
## Data discovery verified by: Advisor direct inspection of CSV headers and distributions

---

## Prerequisites

```bash
pip install scikit-learn pandas scipy numpy
```

**Required skills/tools:** Python data analysis, statistical testing (scipy.stats), Wilson confidence intervals, permutation tests. No API keys needed — analysis-only on existing data.

**Codebase reading required BEFORE running tests:**
1. Read `research/academic_pipeline/data/ai_evaluation_features.csv` — 121 matched trades, 43 columns
2. Read `research/academic_pipeline/data/entry_engineering_dataset.csv` — 129 trades with price data (121 with data_available=True)
3. Read `research/academic_pipeline/data/all_evaluations_features.csv` — 31,145 evaluations (1,532 CANDIDATE, 29,613 NO_TRADE)

---

## Overview

Run 5 zero-cost hypothesis tests on existing GTOS batch data. These test specific structural features identified by the L3 literature search (78 papers across 12 edge optimization questions) and the T2a diagnostic results (121 CANDIDATE trades, all ML models at AUC~0.5).

**Context:** T2a proved that trade outcomes within the CANDIDATE pool are unpredictable by ML models (AUC~0.5, all worse than majority-class baseline). This means **accuracy cannot be improved** — the growth path is **more trades at the same ~65% base rate**. These 5 tests look for feature thresholds that could:
- Filter out a low-WR subgroup (improving pool quality) → accuracy gain
- Identify currently-rejected setups that are actually tradeable → frequency gain
- Validate or kill L3 paper findings against our actual data

**Bonferroni correction:** 5 primary tests → p < 0.01 significance threshold for each.
**Practical significance:** Effects < 5pp WR or < 0.10R expected value are "detectable but negligible."
**Sample:** 121 trades (100 XAUUSD, 21 GBPUSD). Power is limited — a true 10pp effect has ~60% power at n=121. Be explicit about what you CANNOT detect.

---

## Statistical Methods (use for ALL tests)

### Wilson Confidence Intervals (MANDATORY — never use Wald/normal approximation)

```python
from scipy.stats import norm

def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple:
    """Wilson score interval for proportions. Use this for ALL WR estimates."""
    if total == 0:
        return (0.0, 0.0)
    p_hat = successes / total
    denom = 1 + z**2 / total
    center = (p_hat + z**2 / (2 * total)) / denom
    spread = z * ((p_hat * (1 - p_hat) / total + z**2 / (4 * total**2)) ** 0.5) / denom
    return (center - spread, center + spread)
```

### Permutation Test (PRIMARY method for small-sample comparisons)

```python
import numpy as np

def permutation_test_wr(group_a_wins, group_a_total, group_b_wins, group_b_total,
                        n_permutations=10000, seed=42):
    """Two-sample permutation test for win rate difference."""
    rng = np.random.default_rng(seed)
    outcomes_a = [1]*group_a_wins + [0]*(group_a_total - group_a_wins)
    outcomes_b = [1]*group_b_wins + [0]*(group_b_total - group_b_wins)
    pooled = np.array(outcomes_a + outcomes_b)
    observed_diff = group_a_wins/group_a_total - group_b_wins/group_b_total

    count = 0
    for _ in range(n_permutations):
        rng.shuffle(pooled)
        perm_a = pooled[:group_a_total].mean()
        perm_b = pooled[group_a_total:].mean()
        if abs(perm_a - perm_b) >= abs(observed_diff):
            count += 1
    return count / n_permutations
```

### Spearman Rank Correlation (for continuous features)

```python
from scipy.stats import spearmanr

# Use for: feature vs r_multiple, feature vs win (binary)
# Report: rho, p-value, n
```

### Mann-Whitney U (for continuous outcomes between groups)

```python
from scipy.stats import mannwhitneyu

# Use for: R-multiple comparison between groups
# Two-sided test always
```

---

## Test T3a: Fibonacci Retracement Depth

### Hypothesis
**H-T3a:** Deeper H1 retracement (lower fib_pct) predicts higher win rate among CANDIDATE trades. Based on: T2a found h1_fib_pct had the strongest Spearman correlation with outcome (rho=-0.2734, p=0.006 raw) but it FAILED Bonferroni correction for 24 features (threshold p<0.002). This test isolates the effect with a pre-committed split point.

### Data
- Source: `research/academic_pipeline/data/ai_evaluation_features.csv`
- Column: `h1_fib_pct` (range 45.2–79.2, mean 74.3)
- Coverage: 100/121 trades have non-null values (21 null — all XAUUSD)
- Outcome columns: `win` (binary), `r_multiple` (continuous)

### Pre-committed split point
- **Deep retracement:** h1_fib_pct < 70.0 (below the median cluster)
- **Shallow retracement:** h1_fib_pct >= 70.0

This split is chosen BEFORE seeing the outcome breakdown because 70.0 separates the lower tail from the dense cluster at 78-79.

### Method

```
Step 1: Filter to non-null h1_fib_pct (expect n~100)
Step 2: Split into deep (<70) and shallow (>=70) groups
Step 3: Report group sizes, WR (Wilson CI), mean R-multiple (with SE)
Step 4: Permutation test for WR difference (10,000 permutations)
Step 5: Mann-Whitney U for R-multiple difference
Step 6: Spearman correlation: h1_fib_pct vs win, h1_fib_pct vs r_multiple
Step 7: Sensitivity: repeat with split at 65.0 and 75.0 (exploratory only, DO NOT use for primary conclusion)
```

### Decision gate (pre-committed)
| Outcome | Threshold | Action |
|---------|-----------|--------|
| Deep WR significantly higher | p < 0.01 AND delta_WR > 5pp | **IMPLEMENT**: Add h1_fib_pct < 70 as positive weight in prompt |
| Deep WR significantly lower | p < 0.01 AND delta_WR > 5pp | **IMPLEMENT**: Add fib_pct threshold to reject shallow setups |
| Spearman significant | p < 0.01, |rho| > 0.20 | **TEST**: Design shadow filter on continuous fib_pct |
| Not significant | p >= 0.01 OR |delta_WR| < 5pp | **KILL**: Fib depth does not predict outcome within CANDIDATE pool |

---

## Test T3b: Round Number Proximity

### Hypothesis
**H-T3b:** Trade entries, stop losses, or take profits near psychologically significant round numbers have different outcomes than those away from round numbers. Based on: Osler (2000, 2003, 2005) — order clustering at round numbers creates liquidity pools; Niederhoffer (1965) — round numbers as support/resistance. L3 rated this HIGH confidence with direct academic support.

### Data
- Source: `research/academic_pipeline/data/entry_engineering_dataset.csv`
- Columns: `entry_price_ai`, `stop_loss`, `take_profit_1`, `zone_matched_high`, `zone_matched_low`, `symbol`, `sl_distance_atr`
- Also join `win` and `r_multiple` from `ai_evaluation_features.csv` using `trade_id`
- Population: 121 trades with data_available (105 XAUUSD, 24 GBPUSD; note: only 121 of 129 have data_available=True, filter on this)

### Round number definitions

**XAUUSD** (gold, priced in USD/oz):
| Level | Increment | Examples | Weight |
|-------|-----------|----------|--------|
| Minor | $25 | 2325, 2350, 2375 | 1 |
| Major | $50 | 2300, 2350, 2400 | 2 |
| Mega | $100 | 2300, 2400, 2500 | 3 |

**GBPUSD** (FX, priced to 5 decimals):
| Level | Increment | Examples | Weight |
|-------|-----------|----------|--------|
| Minor | 0.0050 | 1.2650, 1.2700 | 1 |
| Major | 0.0100 | 1.2600, 1.2700 | 2 |
| Mega | 0.0500 | 1.2500, 1.3000 | 3 |

### Method

```python
# Step 1: Compute distance to nearest round level for each price point

def nearest_round_distance(price, symbol, level='minor'):
    """Distance to nearest round number, normalized by SL distance (ATR-based)."""
    if symbol == 'XAUUSD':
        increments = {'minor': 25, 'major': 50, 'mega': 100}
    elif symbol == 'GBPUSD':
        increments = {'minor': 0.005, 'major': 0.01, 'mega': 0.05}
    else:
        return None
    inc = increments[level]
    nearest = round(price / inc) * inc
    return abs(price - nearest)

# Step 2: For each trade, compute:
#   - entry_round_dist: distance from entry_price_ai to nearest minor round
#   - sl_round_dist: distance from stop_loss to nearest minor round
#   - tp_round_dist: distance from take_profit_1 to nearest minor round
#   - zone_center_round_dist: distance from (zone_high+zone_low)/2 to nearest minor round
#   Normalize all by sl_distance (in price units, not ATR) for cross-instrument comparability

# Step 3: Binary classification — "near round" vs "far from round"
#   XAUUSD: "near" = within $5 of any $25 level (20% of increment)
#   GBPUSD: "near" = within 0.0010 of any 0.0050 level (20% of increment)

# Step 4: For each price point (entry, SL, TP, zone center):
#   - Compute WR for "near round" vs "far from round" (Wilson CIs)
#   - Permutation test for WR difference
#   - Mann-Whitney U for R-multiple difference
#   - Report: n_near, n_far, WR_near (CI), WR_far (CI), p_perm, delta_WR

# Step 5: Composite round number score
#   weighted_score = entry_near*1 + sl_near*2 + tp_near*1
#   (SL near round is weighted double — Osler's finding is that stop orders
#    cluster at rounds, creating vulnerability for stop hunts)
#   Spearman: weighted_score vs win, weighted_score vs r_multiple
```

**CRITICAL:** The primary comparison is **SL proximity to round numbers → outcome**. This is the strongest prediction from Osler (2003): stop-loss orders cluster at round numbers, making them vulnerable to stop sweeps. A SL placed near a round number should have WORSE outcomes (more stop-outs).

### Decision gate (pre-committed)
| Outcome | Threshold | Action |
|---------|-----------|--------|
| SL near round → lower WR | p < 0.01 AND delta_WR > 5pp | **IMPLEMENT**: Add round-number SL check to execution engine |
| Entry near round → different WR | p < 0.01 AND delta_WR > 5pp | **TEST**: Design shadow filter for entry proximity |
| TP near round → higher WR | p < 0.01 (TP at round = better target) | **IMPLEMENT**: Adjust TP snapping logic |
| No effect for any price point | All p >= 0.01 | **KILL**: Round numbers irrelevant at OB-zone scale |

---

## Test T3c: BOS Displacement Quality

### Hypothesis
**H-T3c:** Higher-quality structural breaks (larger displacement ratio, displaced flag = True) predict better trade outcomes among CANDIDATEs. Based on: SMC theory that impulsive (displaced) BOS signals genuine institutional flow vs. gradual breaks that may be retail noise. T2a found displacement_ratio had near-zero Spearman correlation (rho~0) with outcome, but T2a tested the M15 confirmation displacement — this test isolates the H1 structural break quality.

### Data
- Source: `research/academic_pipeline/data/ai_evaluation_features.csv`
- Columns:
  - `h1_last_break_ratio` — BOS displacement ratio on H1 (range 0.1–7.3, mean 1.98)
  - `h1_last_break_disp` — binary: 1=displaced BOS, 0=not (73 displaced, 48 not)
  - `displacement_ratio` — M15 confirmation displacement (range 0.4–8.2, mean 2.43)
- Outcome: `win` (binary), `r_multiple` (continuous)
- Population: 121 trades (all have these fields)

### Method

```
Step 1: Binary split on h1_last_break_disp (displaced=73 vs not=48)
  - WR for each group (Wilson CIs)
  - Permutation test for WR difference
  - Mann-Whitney U for R-multiple difference

Step 2: Quartile split on h1_last_break_ratio
  - Q1 (weakest breaks) vs Q4 (strongest breaks) comparison
  - Permutation test: Q1 WR vs Q4 WR
  - Mann-Whitney U: Q1 R vs Q4 R

Step 3: Spearman correlations
  - h1_last_break_ratio vs win
  - h1_last_break_ratio vs r_multiple
  - Report: rho, p-value, n

Step 4: Interaction with displacement_ratio
  - Create 2x2: H1_displaced (Y/N) x M15_displacement_ratio (above/below median)
  - Report WR for each cell (Wilson CIs)
  - Fisher exact test for independence

Step 5: Compare h1_last_break_ratio predictive power vs displacement_ratio
  - Spearman for both vs outcome
  - Report which (if either) has stronger signal
```

### Decision gate (pre-committed)
| Outcome | Threshold | Action |
|---------|-----------|--------|
| Displaced BOS → higher WR | p < 0.01 AND delta_WR > 5pp | **IMPLEMENT**: Require h1_last_break_disp=True in CANDIDATE gate |
| h1_last_break_ratio quartile effect | p < 0.01 for Q1 vs Q4, delta > 5pp | **TEST**: Shadow filter on BOS ratio minimum |
| No effect | Both p >= 0.01 | **KILL**: BOS quality doesn't predict outcome within CANDIDATE pool (consistent with T2a's displacement_ratio finding) |

---

## Test T3d: Daily Bias Confidence as Quality Filter

### Hypothesis
**H-T3d:** Evaluations made when the AI assesses high daily bias confidence produce a different CANDIDATE rate and different trade outcomes than those with low/medium confidence. Based on: Multiple L3 papers (Guo & Wang 2020; various trend-following literature) found D1 trend strength correlates with intraday setup quality. Academic consensus: trade WITH the daily trend, not against it.

### Data

**Part A — Gate analysis (full population):**
- Source: `research/academic_pipeline/data/all_evaluations_features.csv`
- Column: `daily_bias_confidence` (encoded: 3=high, 2=medium, 1=low)
- Population: 31,145 evaluations (1,532 CANDIDATE, 29,613 NO_TRADE)
- Distribution across all evals: high=19,381, medium=3,774, low=7,990
- Distribution among CANDIDATEs: high=1,400, medium=128, low=4

**Part B — Outcome analysis (matched trades):**
- Source: `research/academic_pipeline/data/ai_evaluation_features.csv`
- Note: Among the 121 matched trades, daily_bias_direction=1 (bullish) for ALL trades. daily_bias_confidence may have more variance — check and report.
- If insufficient variance: this part is VOID. State that explicitly. Do not force a conclusion.

### Method

```
Part A: CANDIDATE rate by daily bias confidence
  Step 1: Compute CANDIDATE rate for each confidence level
    - high: n_cand / n_total, Wilson CI
    - medium: n_cand / n_total, Wilson CI
    - low: n_cand / n_total, Wilson CI
  Step 2: Chi-squared test for independence (confidence level vs CANDIDATE decision)
  Step 3: Report CANDIDATE rate ratio: high/low
  Step 4: Also stratify by h4_aligned (True/False) — does daily bias confidence
          add information beyond H4 alignment?

Part B: Outcome by daily bias confidence (IF sufficient variance exists)
  Step 1: Check daily_bias_confidence distribution among 121 matched trades
  Step 2: IF at least 2 groups have n >= 10:
    - WR comparison (Wilson CIs, permutation test)
    - R-multiple comparison (Mann-Whitney U)
  Step 3: IF fewer than 2 groups with n >= 10:
    - State: "Insufficient variance for within-CANDIDATE outcome analysis"
    - Report what the distribution actually is
    - DO NOT fabricate a conclusion

Part C: Daily bias direction as frequency indicator
  Step 1: Among all 31,145 evaluations, compute CANDIDATE rate by direction:
    - bullish (encoded 1.0): n=16,289 → CANDIDATE rate?
    - ranging (encoded 0.0): n=12,128 → CANDIDATE rate?
    - bearish (encoded -1.0): n=2,725 → CANDIDATE rate?
  Step 2: Chi-squared test for independence
  Step 3: This tells us: does bullish bias produce more CANDIDATEs? (frequency implication)
```

### Decision gate (pre-committed)
| Outcome | Threshold | Action |
|---------|-----------|--------|
| CANDIDATE rate 3x+ higher for high confidence | Chi-sq p < 0.01 | **CONFIRM**: Daily bias confidence is already implicitly filtering (the gate works). Document but no change needed. |
| Low-confidence CANDIDATEs have LOWER WR | Part B p < 0.01, delta > 5pp | **IMPLEMENT**: Add explicit daily_bias_confidence >= medium check |
| Low-confidence CANDIDATEs have SAME or HIGHER WR | Part B p >= 0.01 | **FLAG**: The gate may be too restrictive. Low-confidence setups could be frequency donors. Queue for T2b API testing. |
| Part B void (no variance) | n < 10 in any non-primary group | **DEFER**: Cannot test within-CANDIDATE outcome. Note for future data collection. |

---

## Test T3e: Structural Density Signal

### Hypothesis
**H-T3e:** The density of structural features (unmitigated OBs, unfilled FVGs) on H1 at the time of evaluation predicts CANDIDATE trade outcome. Based on: SMC theory that "clean" charts (few remaining zones) produce cleaner price action. Academic basis is WEAK — L3 found zero papers validating FVGs and no papers on OB density effects. This is an EXPLORATORY test.

### Data
- Source: `research/academic_pipeline/data/ai_evaluation_features.csv`
- Columns:
  - `h1_ob_count` — unmitigated H1 order blocks (range 0–5, mean 2.0)
  - `h1_fvg_count` — unfilled H1 FVGs (range 0–5, mean 4.1, capped at 5 by MSO)
  - `m15_ob_count` — unmitigated M15 order blocks
  - `m15_fvg_count` — unfilled M15 FVGs (range 2–5, mean 4.85, nearly all 5)
- Outcome: `win` (binary), `r_multiple` (continuous)
- Population: 121 trades

**Known limitation:** MSO text truncates to the most recent 5 of each feature. This means counts >= 5 are censored. m15_fvg_count is almost all 5 (useless). h1_ob_count has real variance. h1_fvg_count has some variance. m15_ob_count may have variance — check.

### Method

```
Step 1: Distribution report for each count feature
  - h1_ob_count, h1_fvg_count, m15_ob_count, m15_fvg_count
  - For each: min, max, mean, SD, % at ceiling (5)
  - DROP any feature with >80% at a single value (no variance to test)

Step 2: For each surviving feature:
  - Spearman correlation with win and r_multiple
  - Report: rho, p-value, n

Step 3: Binary split for h1_ob_count (best variance feature)
  - "Low density": h1_ob_count <= 1 (few remaining zones)
  - "High density": h1_ob_count >= 3 (many remaining zones)
  - WR comparison (Wilson CIs, permutation test)
  - Mann-Whitney U for R-multiple

Step 4: Composite structural density score (EXPLORATORY)
  - density_score = h1_ob_count + h1_fvg_count (only features with variance)
  - Spearman: density_score vs win, density_score vs r_multiple
  - This is hypothesis-generating ONLY — do not claim significance

Step 5: Interaction with BOS quality (cross-reference T3c)
  - 2x2: h1_ob_count (low/high) x h1_last_break_disp (yes/no)
  - Report WR for each cell
  - Fisher exact test
```

### Decision gate (pre-committed)
| Outcome | Threshold | Action |
|---------|-----------|--------|
| h1_ob_count correlates with outcome | Spearman p < 0.01, |rho| > 0.20 | **TEST**: Shadow filter on structural density |
| Low-density → higher WR | p < 0.01 AND delta_WR > 5pp | **TEST**: Add "clean chart" preference to prompt |
| High-density → higher WR | p < 0.01 AND delta_WR > 5pp | **TEST**: Add "rich structural" preference to prompt |
| No feature significant | All p >= 0.01 | **KILL**: Structural density is noise (expected, given zero academic support for these features) |

---

## Output Requirements

### File 1: `research/academic_pipeline/results/T3_batch_hypothesis_results_v1.md`

Structure:

```markdown
# T3 — Batch Hypothesis Test Results
## Date: [execution date]
## Data: 121 matched trades (100 XAUUSD, 21 GBPUSD)

### Executive Summary
[2-3 sentences: which tests passed/failed, key actionable findings]

### T3a: Fibonacci Retracement Depth
- **Primary result:** [deep WR% (CI) vs shallow WR% (CI), delta, p-value]
- **Spearman:** [rho, p]
- **Sensitivity splits:** [65.0 and 75.0 results — EXPLORATORY]
- **Verdict:** [IMPLEMENT / TEST / KILL]
- **Limitation:** [n~100, missing 21 trades with null fib_pct]

### T3b: Round Number Proximity
- **SL proximity (primary):** [near_round WR% (CI) vs far WR% (CI), delta, p]
- **Entry proximity:** [same format]
- **TP proximity:** [same format]
- **Composite score:** [Spearman rho, p]
- **Verdict:** [IMPLEMENT / TEST / KILL]
- **Limitation:** [only 2 instruments, gold-specific round levels]

### T3c: BOS Displacement Quality
- **Displaced vs not (primary):** [WR% (CI) each, delta, p]
- **h1_last_break_ratio quartiles:** [Q1 WR vs Q4 WR, p]
- **Spearman:** [rho, p for ratio vs win]
- **Interaction with M15 displacement:** [2x2 table]
- **Verdict:** [IMPLEMENT / TEST / KILL]

### T3d: Daily Bias Confidence
- **Part A (gate analysis):** [CANDIDATE rate by confidence level, chi-sq p]
- **Part B (outcome):** [results or "VOID — insufficient variance"]
- **Part C (direction → frequency):** [CANDIDATE rate by direction, chi-sq p]
- **Verdict:** [CONFIRM / IMPLEMENT / FLAG / DEFER]

### T3e: Structural Density
- **Feature variance report:** [which features survived >80% ceiling filter]
- **Spearman correlations:** [table: feature, rho, p]
- **h1_ob_count split:** [low vs high WR, p]
- **Composite (exploratory):** [rho, p — NOT for primary conclusion]
- **Verdict:** [TEST / KILL]

### Cross-Test Synthesis
[Which features, if any, interact? Do T3a and T3c tell the same story?
What does this mean for the "frequency vs accuracy" strategic question?]

### Statistical Notes
- Bonferroni threshold: p < 0.01 (5 primary tests)
- All CIs are Wilson score intervals
- Permutation tests: 10,000 iterations, seed=42
- Features with >80% at ceiling value were dropped from analysis
```

### File 2: `research/academic_pipeline/T3_batch_hypothesis_analysis.py`

The complete Python script. Must be re-runnable: `python research/academic_pipeline/T3_batch_hypothesis_analysis.py`

Requirements:
- Read data from CSV files (relative paths from project root)
- Print all results to stdout AND write to results file
- Set random seed (42) for reproducibility
- Include data validation checks at the top (expected columns, row counts)
- Handle missing values explicitly (report, don't silently drop)

### File 3: `research/academic_pipeline/data/T3_test_details.csv`

Per-trade details for review:
- trade_id, symbol, outcome, r_multiple
- h1_fib_pct, fib_group (deep/shallow)
- entry_round_dist_norm, sl_round_dist_norm, tp_round_dist_norm, round_group
- h1_last_break_ratio, h1_last_break_disp, bos_quality_quartile
- h1_ob_count, structural_density_group

---

## Constraints

1. **Do NOT use the all_evaluations dataset for outcome analysis.** Only 121 trades have matched outcomes. The 31,145 evaluations are for gate-function analysis (T3d Part A/C) ONLY.

2. **Do NOT compute p-values and then choose split points.** All split points are defined above BEFORE you see the data. Sensitivity analyses at other split points are explicitly labeled EXPLORATORY.

3. **Do NOT claim significance at the Bonferroni threshold and then also claim significance for exploratory sub-analyses.** Primary findings need p < 0.01. Exploratory findings are reported as "suggestive (p = X)" regardless of their p-value.

4. **Do NOT compare win rates without Wilson CIs.** Every WR% MUST be accompanied by its 95% CI. If the CIs overlap substantially, the comparison is inconclusive regardless of the permutation test.

5. **Do NOT pool XAUUSD and GBPUSD without checking for interaction.** For T3b (round numbers), the instruments have DIFFERENT round levels. Run within-instrument first, then pool only if effects are in the same direction.

6. **Handle the n=121 honestly.** This sample has ~60% power for a 10pp WR difference. If you find nothing, say "underpowered to detect effects < Xpp" — do NOT say "no effect exists."

7. **Reproducibility:** All random seeds = 42. Print data checksums (row count, win count) at the top of output to verify data integrity.

8. **No fabricated numbers.** If a computation fails or produces unexpected results, report the actual output. "File not found" or "unexpected format" are always acceptable. Invented data is NEVER acceptable.

9. **Runtime:** This should complete in under 5 minutes on a laptop. No heavy computation needed — these are simple statistical tests on 121 rows.

---

## Pressure Test Log

| Concern | Resolution |
|---------|------------|
| n=121 too small for 5 simultaneous tests | Bonferroni corrected (p<0.01). Power analysis reported. Negative results are "underpowered" not "null." |
| Fib split at 70.0 is arbitrary | Split chosen BEFORE seeing outcome data. Based on distribution shape (dense cluster 78-79 vs lower tail). Sensitivity at 65 and 75 reported as exploratory. |
| Round number distance definition varies by instrument | Per-instrument round levels defined explicitly. Within-instrument analysis first, pool only if consistent. |
| h1_last_break_ratio may duplicate T2a displacement_ratio finding | Different feature: H1 BOS ratio (structural) vs M15 displacement (confirmation). T2a tested M15 only. Both Spearman correlations reported for comparison. |
| daily_bias_confidence has near-zero variance among matched trades | Part B explicitly may be VOID. Part A uses full 31,145-eval population where variance exists. |
| FVG/OB counts capped at 5 by MSO | Ceiling filter: drop features with >80% at single value. h1_ob_count (mean 2.0) survives. m15_fvg_count (mean 4.85) likely dropped. |
| Multiple testing within each test (e.g., entry+SL+TP in T3b) | Primary comparison pre-specified for each test. Secondary comparisons labeled exploratory. |
| GBPUSD n=21 too small for within-instrument analysis | Report GBPUSD separately for transparency but do NOT compute p-values for n<20 subgroups. |

---

## What This Prompt Does NOT Cover

- **DC framework testing** (requires implementation, separate T3-DC prompt)
- **FOMC/macro event filtering** (requires external event calendar, future wave)
- **Session-specific performance** (london vs NY — observed 72% vs 58% in raw data, but this is a separate hypothesis requiring its own test design)
- **Multi-instrument expansion** (batch data only covers XAUUSD + GBPUSD)
- **API-based experiments** (covered by T2b, separate prompt already written)
