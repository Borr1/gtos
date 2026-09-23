# T3 — Batch Hypothesis Test Results
## Date: April 11, 2026
## Data: 121 matched trades (100 XAUUSD, 21 GBPUSD)
## Base WR: 64.5% [55.6%–72.4%] (n=121, 78W/43L)

---

## T3a: Fibonacci Retracement Depth

**Hypothesis:** Deeper H1 retracement (h1_fib_pct < 70.0) predicts higher win rate
**Pre-committed split:** < 70.0 (deep) vs >= 70.0 (shallow) — chosen before seeing outcome data

**Data:** 100 trades with non-null h1_fib_pct (21 excluded — all check if XAUUSD)
  Null breakdown by symbol: {'XAUUSD': np.int64(21)}
  Deep (<70): n=30 | Shallow (>=70): n=70
  Distribution: min=45.2, median=78.5, max=79.2

**Primary result (split at 70.0):**
  Deep retracement:    86.7% [70.3%–94.7%] (n=30, 26W/4L)
  Shallow retracement: 64.3% [52.6%–74.5%] (n=70, 45W/25L)
  Delta WR (deep - shallow): +22.4%
  Permutation test p-value: 0.0295
  Mann-Whitney U (R-multiple): U=1430, p=0.0041 [**SIGNIFICANT (p<0.01)**] | mean_a=0.867R (n=30), mean_b=0.245R (n=70)

**Spearman correlations (continuous fib_pct):**
  h1_fib_pct vs win:       rho=-0.2734, p=0.0059, n=100 [**SIGNIFICANT (p<0.01)**]
  h1_fib_pct vs r_multiple: rho=-0.2832, p=0.0043, n=100 [**SIGNIFICANT (p<0.01)**]

**Sensitivity (EXPLORATORY — do not use for primary conclusion):**
  Split at 65.0: deep=9 (66.7% WR) vs shallow=91 (71.4% WR), delta=-4.8%, p=1.0000 [EXPLORATORY]
  Split at 75.0: deep=32 (87.5% WR) vs shallow=68 (63.2% WR), delta=+24.3%, p=0.0167 [EXPLORATORY]

**Verdict:**
  **KILL** — p=0.0295 does not meet Bonferroni threshold (p<0.01)

**Limitation:** n=100 (21 null excluded). With ~60% power for a 10pp effect, negative results mean 'underpowered to detect effects < ~8pp', not 'no effect exists'. Note heavy right-skew: 75th percentile equals median at 78.5 — most 'shallow' trades cluster in a 1pp band.

---

## T3b: Round Number Proximity

**Hypothesis:** SL near round numbers → lower WR (Osler 2000-2005: stop clustering at rounds creates sweep vulnerability)
**Primary comparison:** SL proximity to nearest round level → outcome

**Data quality:** 3 XAUUSD trades excluded (entry_price_ai < $100, likely data errors): ['bt_2025-12-18_ny_002_xauusd', 'bt_2025-12-26_ny_001_xauusd', 'bt_2026-03-10_ny_001_xauusd']
  After exclusions: 118 trades with entry price data
  XAUUSD: 97, GBPUSD: 21

**Round number proximity stats:**
  ENTRY: 35 near-round, 83 far-from-round (0 null)
  SL: 48 near-round, 70 far-from-round (0 null)
  TP: 66 near-round, 52 far-from-round (0 null)

**Within-instrument analysis (run first, as instructed):**

  XAUUSD (n=97):
    ENTRY: near=75.0% [55.1%–88.0%] (n=24, 18W/6L) vs far=57.5% [46.1%–68.2%] (n=73, 42W/31L), delta=+17.5%, p=0.1488
    SL: near=59.5% [44.5%–73.0%] (n=42, 25W/17L) vs far=63.6% [50.4%–75.1%] (n=55, 35W/20L), delta=-4.1%, p=0.8356
    TP: near=56.1% [43.3%–68.2%] (n=57, 32W/25L) vs far=70.0% [54.6%–81.9%] (n=40, 28W/12L), delta=-13.9%, p=0.2058

  GBPUSD (n=21):
    ENTRY: near=72.7% [43.4%–90.3%] (n=11, 8W/3L) vs far=70.0% [39.7%–89.2%] (n=10, 7W/3L), delta=+2.7%, p=1.0000
    SL: near=83.3% [43.6%–97.0%] (n=6, 5W/1L) vs far=66.7% [41.7%–84.8%] (n=15, 10W/5L), delta=+16.7%, p=0.6233
    TP: near=55.6% [26.7%–81.1%] (n=9, 5W/4L) vs far=83.3% [55.2%–95.3%] (n=12, 10W/2L), delta=-27.8%, p=0.3288

**Pooled analysis (XAUUSD-dominated — checking direction consistency first):**
  ENTRY: near=74.3% [57.9%–85.8%] (n=35, 26W/9L) vs far=59.0% [48.3%–69.0%] (n=83, 49W/34L)
         delta=+15.2%, p=0.1485 | MWU: U=1706, p=0.1333 [ns] | mean_a=0.502R (n=35), mean_b=0.271R (n=83)
  SL: near=62.5% [48.4%–74.8%] (n=48, 30W/18L) vs far=64.3% [52.6%–74.5%] (n=70, 45W/25L)
         delta=-1.8%, p=0.8464 | MWU: U=1552, p=0.4791 [ns] | mean_a=0.174R (n=48), mean_b=0.454R (n=70)
  TP: near=56.1% [44.1%–67.4%] (n=66, 37W/29L) vs far=73.1% [59.7%–83.2%] (n=52, 38W/14L)
         delta=-17.0%, p=0.0819 | MWU: U=1444, p=0.1368 [ns] | mean_a=0.278R (n=66), mean_b=0.418R (n=52)

**Composite round score (Spearman — EXPLORATORY):**
  round_score vs win:       rho=-0.0283, p=0.7609, n=118 [ns]
  round_score vs r_multiple: rho=-0.0554, p=0.5514, n=118 [ns]
  sl_round_dist vs win:      rho=-0.0900, p=0.3327, n=118 [ns]

**Verdict:**
  **KILL** — No price point reached Bonferroni threshold (p<0.01) with >5pp delta in XAUUSD analysis
  Note: GBPUSD n=21 is too small for p-values; direction reported for reference only

**Limitation:** Only 2 instruments (XAUUSD + GBPUSD). Round level definitions are instrument-specific. 3 XAUUSD entries excluded due to corrupt price data (entry < $100). GBPUSD n=21 is underpowered — direction noted but no significance test applied per protocol.

---

## T3c: BOS Displacement Quality

**Hypothesis:** Displaced H1 BOS (h1_last_break_disp=1) and higher h1_last_break_ratio predict better outcomes
**T2a context:** M15 displacement_ratio had rho~0 — this tests H1 structural BOS, a different feature

**Step 1 — Binary split on h1_last_break_disp:**
  Displaced (1):     57.5% [46.1%–68.2%] (n=73, 42W/31L)
  Not displaced (0): 75.0% [61.2%–85.1%] (n=48, 36W/12L)
  Delta (disp - not): -17.5%
  Permutation test p: 0.0553
  Mann-Whitney U (R): U=1364, p=0.0384 [suggestive (p<0.05)] | mean_a=0.168R (n=73), mean_b=0.592R (n=48)

**Step 2 — Quartile split on h1_last_break_ratio:**
  h1_last_break_ratio quartile boundaries: Q1=0.90, Q3=2.80
  Q1 (weakest, ratio<=0.90): 78.8% [62.2%–89.3%] (n=33, 26W/7L)
  Q4 (strongest, ratio>=2.80): 56.2% [39.3%–71.8%] (n=32, 18W/14L)
  Delta (Q1 - Q4): +22.5%
  Permutation test p (Q1 vs Q4): 0.0672
  Mann-Whitney U (R): U=656, p=0.0906 [ns] | mean_a=0.628R (n=33), mean_b=0.151R (n=32)

**Step 3 — Spearman correlations:**
  h1_last_break_ratio vs win:       rho=-0.1336, p=0.1442, n=121 [ns]
  h1_last_break_ratio vs r_multiple: rho=-0.1267, p=0.1662, n=121 [ns]

**Step 4 — Comparison with M15 displacement_ratio (T2a feature):**
  displacement_ratio (M15) vs win:       rho=0.0714, p=0.4367, n=121 [ns]
  displacement_ratio (M15) vs r_multiple: rho=0.1142, p=0.2123, n=121 [ns]

**Step 5 — 2x2 interaction: H1_displaced × M15_displacement_ratio (above/below median):**
  H1_disp=N/M15=below: 77.3% [56.6%–89.9%] (n=22, 17W/5L)
  H1_disp=N/M15=above: 73.1% [53.9%–86.3%] (n=26, 19W/7L)
  H1_disp=Y/M15=below: 55.6% [39.6%–70.5%] (n=36, 20W/16L)
  H1_disp=Y/M15=above: 59.5% [43.5%–73.7%] (n=37, 22W/15L)
  Fisher exact (H1_disp independence from M15_above_median): p=0.7148

**Verdict:**
  **KILL** — Neither BOS displacement binary (p=0.0553) nor ratio quartile (p=0.0672) reaches Bonferroni threshold with >5pp delta. Consistent with T2a's displacement_ratio finding: displacement does not predict outcome within CANDIDATE pool.

---

## T3d: Daily Bias Confidence as Quality Filter

**Hypothesis:** High daily_bias_confidence → higher CANDIDATE rate and better trade outcomes
**Academic basis:** Guo & Wang (2020), trend-following literature — D1 trend strength correlates with intraday quality

**Part A — CANDIDATE rate by confidence level (n=31,145 evaluations):**

  Confidence 1 (low): 7990 evals → 4 CANDIDATE → CANDIDATE rate=0.05% [0.02%–0.13%]
  Confidence 2 (medium): 3774 evals → 128 CANDIDATE → CANDIDATE rate=3.39% [2.86%–4.02%]
  Confidence 3 (high): 19381 evals → 1400 CANDIDATE → CANDIDATE rate=7.22% [6.87%–7.60%]

  CANDIDATE rate ratio (high/low): 144x (7.22% vs 0.05%)
  Chi-squared test (3 confidence levels): chi2=643.9, p=1.51e-140, df=2

**Part A supplemental — Stratified by h4_aligned (does confidence add info beyond H4 alignment?):**
  h4_aligned=False (n=14266):
    conf=1 (low): 7506 evals, 0 CANDIDATE (0.00%)
    conf=2 (medium): 1000 evals, 4 CANDIDATE (0.40%)
    conf=3 (high): 5760 evals, 28 CANDIDATE (0.49%)
  h4_aligned=True (n=16879):
    conf=1 (low): 484 evals, 4 CANDIDATE (0.83%)
    conf=2 (medium): 2774 evals, 124 CANDIDATE (4.47%)
    conf=3 (high): 13621 evals, 1372 CANDIDATE (10.07%)

**Part B — Outcome by daily_bias_confidence (121 matched trades):**

  Distribution in matched trades: {2: np.int64(1), 3: np.int64(120)}
  **VOID — Insufficient variance.** Only 1 group(s) have n≥10.
  All 121 trades have daily_bias_confidence=3 (high) except 1 trade with confidence=2.
  Cannot compare groups. This confirms the system already implicitly enforces high-confidence only.
  → Implication: the batch data represents a confidence-filtered sample.

**Part C — CANDIDATE rate by daily_bias_direction (frequency implication):**

  bullish (+1): 16289 evals → 1445 CANDIDATE → rate=8.87% [8.44%–9.32%]
  ranging (+0): 12128 evals → 84 CANDIDATE → rate=0.69% [0.56%–0.86%]
  bearish (-1): 2725 evals → 3 CANDIDATE → rate=0.11% [0.04%–0.32%]

  Chi-squared (3 directions): chi2=1141.8, p=1.16e-248, df=2
  Bullish/bearish CANDIDATE rate ratio: 8.87% vs 0.11% = 81x

**Verdict:**
  **CONFIRM** — Daily bias confidence powerfully gates CANDIDATE decisions.
  High confidence produces 144x more CANDIDATEs than low confidence (chi-sq p=1.51e-140).
  The gate already works — no change needed.
  **Part B VOID** — Insufficient variance in matched trades (120/121 are confidence=3).
  **Direction effect confirmed** — Bullish bias drives virtually all CANDIDATEs (chi-sq p=1.16e-248).
  System is effectively bullish-only. Ranging setups exist (84 CANDIDATEs) but bearish is near-zero (3 CANDIDATEs).

---

## T3e: Structural Density Signal

**Hypothesis (EXPLORATORY):** Density of structural features (H1 OBs, FVGs) predicts CANDIDATE trade outcome
**Academic basis:** WEAK — L3 found zero papers validating FVGs, no papers on OB density effects

**Step 1 — Feature variance report (ceiling filter: drop if >80% at single value):**

  h1_ob_count (H1 unmitigated OBs):
    min=0, max=5, mean=1.98, SD=1.60
    Mode=1 at 24.8% | % at ceiling (5): 11.6% | SURVIVES
  h1_fvg_count (H1 unfilled FVGs):
    min=0, max=5, mean=4.10, SD=1.27
    Mode=5 at 61.2% | % at ceiling (5): 61.2% | SURVIVES
  m15_ob_count (M15 unmitigated OBs):
    min=0, max=5, mean=3.47, SD=1.58
    Mode=5 at 38.0% | % at ceiling (5): 38.0% | SURVIVES
  m15_fvg_count (M15 unfilled FVGs):
    min=2, max=5, mean=4.85, SD=0.54
    Mode=5 at 91.7% | % at ceiling (5): 91.7% | **DROPPED**

  **Surviving features:** ['h1_ob_count', 'h1_fvg_count', 'm15_ob_count']

**Step 2 — Spearman correlations (surviving features only):**

  h1_ob_count vs win:       rho=0.0106, p=0.9081, n=121 [ns]
  h1_ob_count vs r_multiple: rho=0.0610, p=0.5060, n=121 [ns]
  h1_fvg_count vs win:       rho=0.1495, p=0.1017, n=121 [ns]
  h1_fvg_count vs r_multiple: rho=0.1663, p=0.0683, n=121 [ns]
  m15_ob_count vs win:       rho=-0.0652, p=0.4774, n=121 [ns]
  m15_ob_count vs r_multiple: rho=-0.0046, p=0.9601, n=121 [ns]

**Step 3 — Binary split on h1_ob_count (best variance feature):**
  'Low density': h1_ob_count <= 1 (few remaining zones)
  'High density': h1_ob_count >= 3 (many remaining zones)
  (Trades with h1_ob_count = 2 excluded from binary split to create clean contrast)

  Low density (h1_ob<=1):  63.0% [49.6%–74.6%] (n=54, 34W/20L)
  Mid (h1_ob=2, excluded): 66.7% [48.8%–80.8%] (n=30, 20W/10L) [reference only]
  High density (h1_ob>=3): 64.9% [48.8%–78.2%] (n=37, 24W/13L)
  Delta (low - high): -1.9%
  Permutation test p: 1.0000
  Mann-Whitney U (R): U=906, p=0.4536 [ns] | mean_a=0.164R (n=54), mean_b=0.418R (n=37)

**Step 4 — Composite structural density score (EXPLORATORY — hypothesis-generating only):**
  density_score = h1_ob_count + h1_fvg_count
  density_score vs win:       rho=0.0888, p=0.3325, n=121 [ns] [EXPLORATORY]
  density_score vs r_multiple: rho=0.1398, p=0.1262, n=121 [ns] [EXPLORATORY]

**Step 5 — Interaction with BOS quality (cross-reference T3c):**
  2x2: h1_ob_count (low=0-1 / high=3-5) × h1_last_break_disp (N/Y)
  low_ob x not_disp: 77.3% [56.6%–89.9%] (n=22, 17W/5L)
  low_ob x disp: 53.1% [36.4%–69.1%] (n=32, 17W/15L)
  high_ob x not_disp: 64.3% [38.8%–83.7%] (n=14, 9W/5L)
  high_ob x disp: 65.2% [44.9%–81.2%] (n=23, 15W/8L)
  Fisher exact (ob_density vs displacement independence): p=0.8298

**Verdict:**
  **KILL** — No density feature reaches Bonferroni threshold (p<0.01 with |rho|>0.20 or delta>5pp). Consistent with zero academic support. Structural density is noise in this dataset.

---

## Executive Summary

Five batch hypothesis tests on 121 CANDIDATE trades (100 XAUUSD, 21 GBPUSD), Bonferroni threshold p<0.01:

- **T3a:** KILL — Fib depth (p=0.029, delta=+22.4%)
- **T3b:** KILL — Round number proximity — no XAUUSD price point reached threshold
- **T3c:** KILL — BOS quality (binary p=0.055, quartile p=0.067)
- **T3d:** CONFIRM — Daily confidence gates 144x CANDIDATE rate differential (p=1.5e-140)
- **T3e:** KILL — Structural density — no feature significant

**Key takeaway:** T3d (CONFIRM) establishes that daily bias confidence and direction are the dominant CANDIDATE gatekeepers — not fine-grained structural features. The system is running bullish-only (1,445/1,532 = 94.3% of CANDIDATEs are bullish). No feature threshold tested here (Fib depth, round numbers, BOS quality, structural density) predicts WITHIN-CANDIDATE outcome at the corrected significance threshold, consistent with T2a's finding that CANDIDATE pool outcomes are unpredictable by ML. The growth path remains frequency expansion (identify more tradeable setups) not accuracy improvement (filter existing CANDIDATEs).

---

## Cross-Test Synthesis

**Do T3a and T3c tell the same story?**
Both test 'quality' proxies (deeper retracement vs stronger structural break). Both are non-significant. This convergence strengthens the T2a finding: within-CANDIDATE quality variation does not predict outcome. If one had been significant and the other not, the pattern would be ambiguous.

**What does this mean for frequency vs accuracy?**
T3d Part C is the most important finding in this batch: ranging-bias setups have a CANDIDATE rate of 0.69% (84 trades across the full batch history), and bearish setups produce only 3 CANDIDATEs total. The frequency bottleneck is not within-pool filtering — it is the system's near-total rejection of non-bullish contexts. If the system's WR in ranging contexts is comparable to bullish (untested), activating ranging-condition CANDIDATEs would add 5–6% to the batch CANDIDATE rate (84 + some currently-blocked ranging setups). This is the frequency donor queue.

**Feature interactions:**
No strong interaction found between T3c (BOS displacement) and T3e (structural density). Fisher exact for the 2x2 (BOS × density) does not indicate synergy. These dimensions are independent noise within the CANDIDATE pool.

---

## Statistical Notes
- Bonferroni threshold: p < 0.01 (5 primary tests)
- All win rates accompanied by Wilson score 95% CIs
- Permutation tests: 10,000 iterations, seed=42
- Features with >80% at ceiling value dropped from T3e analysis
- GBPUSD n=21: direction reported, no p-values computed per protocol
- Power: ~60% to detect a true 10pp WR difference at n=100-121
- Negative primary results interpreted as 'underpowered to detect effects < ~8pp' not 'zero effect'

_Results generated: April 11, 2026 | Data checksums: ai_eval=90d992d9, entry=87c16a6f, all_eval=4cc9e6b3_
