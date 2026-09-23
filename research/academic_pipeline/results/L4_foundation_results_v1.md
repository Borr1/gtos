# L4 Foundation Analysis Results

**Date:** 2026-04-12 18:42
**Trades:** 129 (105 XAUUSD, 24 GBPUSD)
**Candle evaluations:** 31,145
**Date range:** 2024-03-01 to 2026-03-13
**WR:** 62.0% | **Mean R:** 0.278

---
## CLUSTER A: STOP-LOSS REFINEMENT

### A1: Sweeney MAE Scatter — Optimal SL Calibration

**Winner MAE (n=78):**
  P50: 0.138R
  P75: 0.288R
  P80: 0.354R
  P85: 0.399R
  P90: 0.544R
  P95: 0.630R

**Loser MAE (n=43):**
  P50: 1.065R
  P75: 1.251R
  P80: 1.294R
  P85: 1.413R
  P90: 1.456R
  P95: 2.028R

**Winner survival at MAE thresholds (% retained if SL = threshold):**
  SL=0.3R: 76.9% of winners survive
  SL=0.5R: 88.5% of winners survive
  SL=0.7R: 96.2% of winners survive
  SL=0.8R: 96.2% of winners survive
  SL=0.9R: 96.2% of winners survive
  SL=1.0R: 100.0% of winners survive

**Interpretation:** Current SL = 1.0R by definition.
Winners with MAE > 0.8R (nearly stopped out): 3.8%
Winners with MAE > 0.5R (significant heat): 11.5%
Median winner MAE: 0.138R
Median loser MAE: 1.065R (capped at 1.0R)

### A3: GPD / Heavy Tail Check on MAE
MAE kurtosis: 2.46 (>0 = heavier than normal)
D'Agostino-Pearson normality test: stat=39.1, p=3.25e-09
  -> REJECT normality
GPD fit (exceedances above P75=1.007):
  Shape (xi): 0.476 (heavy-tailed)
  Scale: 0.180
  Expected range xi=0.3-0.4 per Khan et al. (2023)

### A6: Tail Asymmetry — MAE vs MFE
MAE: mean=0.547, std=0.556, skew=1.365
MFE: mean=1.194, std=1.413, skew=1.738
MFE GPD shape (xi): -0.442
MAE GPD shape (xi): 0.476
  -> MAE tail IS heavier than MFE (asymmetric risk confirmed)
  -> SL needs more buffer than TP distance, per MDPI (2025)

### A7: Volatility-Regime SL Adequacy
Median SL/ATR ratio: 2.21
High-vol group (SL/ATR <= median): n=61, MAE mean=0.676R
Low-vol group (SL/ATR > median): n=60, MAE mean=0.377R
Mann-Whitney U: stat=2212, p=0.0475
  -> SIGNIFICANT: vol regime does affect MAE

### A8 + A11: Round-Number SL Effects (XAUUSD)
SL within $2 of $5 round: 86 (86.0%)
SL within $3 of $10 round: 64 (64.0%)

Near-round MAE: 0.524R (n=86)
Far-from-round MAE: 0.541R (n=14)
MWU (near > far): p=0.4506
  -> NOT confirmed: round-number SL proximity does not amplify MAE

A11 Chi-squared (SL clustering at $5 rounds): chi2=2.54, p=0.6379
  -> No clustering at round numbers

### A15: Serial Correlation Check (validates SL framework)
Trade-level R-multiple ACF(1): 0.1555
Ljung-Box test:
  Lag 1: stat=3.14, p=0.0765
  Lag 2: stat=3.17, p=0.2054
  Lag 3: stat=3.68, p=0.2979
  Lag 5: stat=3.69, p=0.5944
  -> No serial correlation (trades are independent)

### A20-A26: Kelly Sizing Analysis
**A20: Binary Kelly**
  WR=0.620, Avg Win=0.923R, Avg Loss=0.775R
  Kelly f* = 0.388 (38.8% of account)
  Half-Kelly = 0.194 (19.4%)
  Current: 1.0% -> 0.0x fraction of Kelly

**A21: Vince Optimal f (full distribution)**
  Worst loss: -1.000R
  Optimal f: 0.253 (25.3%)
  Geometric growth at optimal: 0.033007
  Growth at f=0.01 (current 1%): 0.002707
  Growth at f=0.02 (2%): 0.005278
  Growth at f=0.03 (3%): 0.007718

**A26: Unimodality check:** CONFIRMED (single peak)

**A25: Multi-Outcome Kelly**
  Full TP (>1.0R): n=22 (17.1%), mean R=2.432
  Partial win (0-1R): n=59 (45.7%), mean R=0.344
  Breakeven (-0.1 to 0.1R): n=12 (9.3%), mean R=0.034
  Partial loss (-1 to -0.1R): n=8 (6.2%), mean R=-0.234
  Full SL (-1R): n=36 (27.9%), mean R=-1.000

**FTMO Monte Carlo (10k paths, 90 trading days, current WR/RR):**
  f=1.0%: P(pass)=45.9%, P(bust)=9.9%, median equity=1.102
  f=1.5%: P(pass)=63.3%, P(bust)=24.3%, median equity=1.206
  f=2.0%: P(pass)=56.2%, P(bust)=37.2%, median equity=1.260
  f=2.5%: P(pass)=47.1%, P(bust)=49.7%, median equity=1.320
  f=3.0%: P(pass)=33.9%, P(bust)=65.5%, median equity=1.501

### A27: MAE by Kill Zone
  LONDON: n=60, MAE mean=0.565R, median=0.377R, P90=1.290R
  NY: n=68, MAE mean=0.531R, median=0.297R, P90=1.196R
  MWU test: p=0.2988
  -> No significant difference in MAE between sessions

---
## CLUSTER B: EXIT OPTIMIZATION

### B36: Conditional MFE Distribution (FOUNDATION)

**Unconditional P(reaching nR):**
  P(MFE >= 0.5R): 53.1% (n=68)
  P(MFE >= 1.0R): 36.7% (n=47)
  P(MFE >= 1.5R): 25.0% (n=32)
  P(MFE >= 2.0R): 19.5% (n=25)
  P(MFE >= 2.5R): 15.6% (n=20)
  P(MFE >= 3.0R): 13.3% (n=17)

**Conditional P(nR | mR reached) — the key exit table:**

  Given MFE >= 0.5R (n=68):
    P(MFE >= 1.0R | >= 0.5R): 69.1% (n=47)
    P(MFE >= 1.5R | >= 0.5R): 47.1% (n=32)
    P(MFE >= 2.0R | >= 0.5R): 36.8% (n=25)
    P(MFE >= 2.5R | >= 0.5R): 29.4% (n=20)

  Given MFE >= 1.0R (n=47):
    P(MFE >= 1.5R | >= 1.0R): 68.1% (n=32)
    P(MFE >= 2.0R | >= 1.0R): 53.2% (n=25)
    P(MFE >= 2.5R | >= 1.0R): 42.6% (n=20)
    P(MFE >= 3.0R | >= 1.0R): 36.2% (n=17)

  Given MFE >= 1.5R (n=32):
    P(MFE >= 2.0R | >= 1.5R): 78.1% (n=25)
    P(MFE >= 2.5R | >= 1.5R): 62.5% (n=20)
    P(MFE >= 3.0R | >= 1.5R): 53.1% (n=17)
    P(MFE >= 3.5R | >= 1.5R): 46.9% (n=15)

  Given MFE >= 2.0R (n=25):
    P(MFE >= 2.5R | >= 2.0R): 80.0% (n=20)
    P(MFE >= 3.0R | >= 2.0R): 68.0% (n=17)
    P(MFE >= 3.5R | >= 2.0R): 60.0% (n=15)
    P(MFE >= 4.0R | >= 2.0R): 28.0% (n=7)

### B1 + B2: Partial Close Decision
P(2R | 1R reached): 53.2% (n_reached_1R=47, n_reached_2R=25)
Kelly-optimal runner fraction: f2* = 0.064
  -> P(2R|1R) >= 50%: HOLD at 1R is correct. Partial close DESTROYS value.
P(3R | 2R reached): 68.0% (n=25)

### B4: MFE Distribution Skewness (partial close indicator)
Winner MFE skewness: 1.232
  -> RIGHT-SKEWED (>0.5): partial close at 1R may truncate big winners
Conditional MFE skewness (MFE > 1R): 0.922

### B23: Implementation Shortfall (IS) Decomposition
Overall IS: mean=0.907R, median=0.790R

**Winners (early exit cost):**
  IS mean: 0.676R (MFE captured: 86.4%)
  Trades where MFE > 2x actual R: 41 (51.2%)

**Losers (reversal cost):**
  IS mean: 1.291R
  Losers with MFE > 0.5R (was in profit then reversed): 16 (33.3%)
  Losers with MFE > 1.0R (was at +1R then lost): 9 (18.8%)

**Total IS breakdown:**
  Early exit cost (winners): 54.1R
  Reversal cost (losers): 62.0R
  -> REVERSAL dominates: tighter stops are priority

### B24: Entry Timing Within Kill Zone

**LONDON kill zone:**
  Early: n=29, WR=65.5%, mean R=0.240
  Mid: n=12, WR=75.0%, mean R=0.277
  Late: n=16, WR=81.2%, mean R=0.766

**NY kill zone:**
  Early: n=24, WR=58.3%, mean R=0.290
  Mid: n=24, WR=54.2%, mean R=0.251
  Late: n=16, WR=62.5%, mean R=0.320

### B25: Exit Strategy Efficient Frontier
*Simulated exits at different R-levels using MFE/MAE data:*

  TP=0.5R: E[R]=0.135, Var=0.285, Sharpe=0.253, WR=75.8%
  TP=1.0R: E[R]=0.225, Var=0.566, Sharpe=0.299, WR=70.3%
  TP=1.5R: E[R]=0.248, Var=0.811, Sharpe=0.275, WR=67.2%
  TP=2.0R: E[R]=0.265, Var=1.081, Sharpe=0.255, WR=64.1%
  TP=2.5R: E[R]=0.290, Var=1.311, Sharpe=0.253, WR=63.3%
  Actual: E[R]=0.288, Var=1.410, Sharpe=0.242, WR=62.5%

### B28: MFE vs Volatility Correlation
SL/ATR ratio vs MFE:
  Pearson: r=-0.413, p=0.0000
  Spearman: rho=-0.530, p=0.0000
  -> SIGNIFICANT: MFE scales with vol

### B34: High-Vol Regime Risk (Skewness)
High-vol (tight SL/ATR): n=61, R skew=0.602
Low-vol (wide SL/ATR): n=60, R skew=1.817

---
## CLUSTER C: ALPHA DECAY AND CROWDING

### C1: Formal Decay Test — First Half vs Second Half
First half: WR=65.6% (n=64), dates=2024-03-01 to 2025-06-10
Second half: WR=58.5% (n=65), dates=2025-06-11 to 2026-03-13
Difference: 7.2pp
Two-proportion z-test: z=0.838, p=0.4019
  -> NOT significant (cannot confirm decay)

### C6: Impulse Size Correlation with Trade Outcome
SL distance (impulse proxy) vs R-multiple: rho=-0.164, p=0.0726
  -> Does not confirm OFI

### C7: Win Rate by Session
  NY: WR=55.9% (n=68), mean R=0.237
  LONDON: WR=68.9% (n=61), mean R=0.323
Fisher exact (London vs NY): p=0.1487
  -> No significant difference

### C14: Winning Trade Magnitude Over Time
Spearman correlation (win order vs R): rho=0.028, p=0.8024
  -> STABLE: no compression in win magnitude
  Q1 (earliest): mean win R=0.665, n=20
  Q2: mean win R=1.188, n=20
  Q3: mean win R=1.147, n=20
  Q4 (latest): mean win R=0.690, n=20

### C15: Loss Tail Evolution
First-half losses: mean R=-0.764, worst=-1.000
Second-half losses: mean R=-0.786, worst=-1.000
First-half loser MAE P90: 1.943R
Second-half loser MAE P90: 1.294R
  -> Stable tails

### C16: Failure Clustering
Total outcomes: 129 (W=80, L=49)
Observed runs: 59
Expected runs (independence): 61.8
Wald-Wolfowitz runs test: z=-0.521, p=0.6024
  -> INDEPENDENT: no clustering detected
Outcome ACF(1): 0.0333
Max consecutive losses: 5

### C19: Round-Number OB Zone Continuation
Zones near $10 round: WR=60.0% (n=65)
Zones far from round: WR=68.6% (n=35)
Fisher exact: p=0.5154

### C20: Loss/Win Magnitude Asymmetry (Fade Effect)
Mean win: +0.923R
Mean loss (abs): 0.775R
Asymmetry ratio (loss/win): 0.840
  -> SYMMETRIC or favorable: wins >= losses

### C22: Edge Carrying Capacity — R vs Time
R-multiple trend over all trades: rho=-0.005, p=0.9509
  -> No significant trend

### C29: Outcome Variance Evolution (Fragility)
First-half R variance: 1.5397
Second-half R variance: 1.2903
Levene's test: stat=0.01, p=0.9192
  -> Stable variance

### C31: Decay Rate Benchmarking
Quarterly WR: [73.2, 71.4, 63.6, 59.4]
Total decline: 13.8pp over 4 quarters
Annualized rate: ~13.8pp/year
FX TA baseline (Menkhoff & Taylor): ~1pp/year
Post-publication benchmark (McLean & Pontiff): ~5pp/year
Observed: 14x faster than FX TA, 3x faster than post-pub
  -> CRITICAL: 14pp/year is too fast for pure edge decay. Regime effects likely dominate.

### C32: Trade Frequency vs Quality
Monthly trade count vs avg R: rho=0.369, p=0.1095
  -> No significant relationship

Monthly breakdown:
  2024-03: n=1, WR=0.0%, E[R]=-1.000
  2024-04: n=5, WR=60.0%, E[R]=0.314
  2024-05: n=2, WR=0.0%, E[R]=-1.000
  2024-06: n=1, WR=0.0%, E[R]=-1.000
  2024-07: n=3, WR=100.0%, E[R]=0.703
  2024-08: n=1, WR=100.0%, E[R]=0.160
  2024-09: n=1, WR=0.0%, E[R]=-1.000
  2024-10: n=3, WR=33.3%, E[R]=-0.323
  2025-01: n=5, WR=80.0%, E[R]=1.062
  2025-02: n=17, WR=58.8%, E[R]=-0.038
  2025-03: n=19, WR=78.9%, E[R]=0.591
  2025-04: n=2, WR=100.0%, E[R]=1.990
  2025-05: n=3, WR=66.7%, E[R]=1.600
  2025-06: n=9, WR=66.7%, E[R]=0.370
  2025-09: n=3, WR=0.0%, E[R]=-0.813
  2025-10: n=6, WR=66.7%, E[R]=0.070
  2025-12: n=16, WR=62.5%, E[R]=0.472
  2026-01: n=21, WR=57.1%, E[R]=0.040
  2026-02: n=6, WR=66.7%, E[R]=0.358
  2026-03: n=5, WR=60.0%, E[R]=0.282

### C33: Regime Decomposition of Quarterly WR Decline

**Quarterly stats:**
  2024Q1: n=1, WR=0.0%, E[R]=-1.000
  2024Q2: n=8, WR=37.5%, E[R]=-0.179
  2024Q3: n=5, WR=80.0%, E[R]=0.254
  2024Q4: n=3, WR=33.3%, E[R]=-0.323
  2025Q1: n=41, WR=70.7%, E[R]=0.388
  2025Q2: n=14, WR=71.4%, E[R]=0.865
  2025Q3: n=3, WR=0.0%, E[R]=-0.813
  2025Q4: n=22, WR=63.6%, E[R]=0.362
  2026Q1: n=32, WR=59.4%, E[R]=0.138

**C33a: Volatility regime**
Quarterly ATR ratio vs WR: rho=-0.356, p=0.3471
  2024Q1: ATR ratio=3.10, WR=0.0%
  2024Q2: ATR ratio=3.77, WR=42.9%
  2024Q3: ATR ratio=3.16, WR=80.0%
  2024Q4: ATR ratio=3.41, WR=0.0%
  2025Q1: ATR ratio=3.93, WR=72.5%
  2025Q2: ATR ratio=2.06, WR=76.9%
  2025Q3: ATR ratio=6.81, WR=0.0%
  2025Q4: ATR ratio=2.00, WR=68.4%
  2026Q1: ATR ratio=3.09, WR=59.4%

**C33b: Session composition shift**
  2024Q1: London=0% (WR=0%), NY=100% (WR=0%)
  2024Q2: London=25% (WR=50%), NY=75% (WR=33%)
  2024Q3: London=40% (WR=100%), NY=60% (WR=67%)
  2024Q4: London=33% (WR=100%), NY=67% (WR=0%)
  2025Q1: London=63% (WR=77%), NY=37% (WR=60%)
  2025Q2: London=43% (WR=50%), NY=57% (WR=88%)
  2025Q3: London=33% (WR=0%), NY=67% (WR=0%)
  2025Q4: London=23% (WR=40%), NY=77% (WR=71%)
  2026Q1: London=56% (WR=72%), NY=44% (WR=43%)

**C33c: Per-instrument WR trend**
  GBPUSD 2024Q1: WR=0.0% (n=1)
  GBPUSD 2024Q2: WR=0.0% (n=2)
  GBPUSD 2025Q1: WR=88.9% (n=9)
  GBPUSD 2025Q2: WR=83.3% (n=6)
  GBPUSD 2025Q4: WR=50.0% (n=6)
  XAUUSD 2024Q2: WR=50.0% (n=6)
  XAUUSD 2024Q3: WR=80.0% (n=5)
  XAUUSD 2024Q4: WR=33.3% (n=3)
  XAUUSD 2025Q1: WR=65.6% (n=32)
  XAUUSD 2025Q2: WR=62.5% (n=8)
  XAUUSD 2025Q3: WR=0.0% (n=3)
  XAUUSD 2025Q4: WR=68.8% (n=16)
  XAUUSD 2026Q1: WR=59.4% (n=32)

**C33d: In-sample overlap risk**
Earliest trade: 2024-03-01
  -> If parameters were tuned on data before 2024-03-01, no overlap
  -> If early trades overlap with optimization set, baseline WR is inflated
  ACTION: audit parameter tuning dates against first-quarter trade dates

---
## CLUSTER D: DRIFT MONITORING FOUNDATION

### D1-D3: CUSUM/EWMA Baseline from 31k Evaluations
Rolling 200-eval CANDIDATE rate:
  Mean: 0.049
  Std: 0.0418
  Min: 0.000 (date index: ~2024-10-18 14:45:00+00:00)
  Max: 0.205

CUSUM (p0=0.049, k=0.02, h=4.0):
  Positive shift alarms: 15973 (CANDIDATE rate increased)
  Negative shift alarms: 15231 (CANDIDATE rate decreased)
  Max CUSUM+: 159.10
  Max CUSUM-: 78.07

EWMA (lambda=0.2):
  Control limits: [-0.1671, 0.2655]
  Out-of-control points: 1407

---
## SYNTHESIS: KEY FINDINGS FOR PROMPT OPTIMIZATION

*Items below summarize the findings that directly inform how to optimize the prompt.*

1. **P(2R|1R)=53%** — hold at 1R is correct
2. **IS decomposition:** Reversal cost dominates (62.0R vs 54.1R)
3. **WR decay test:** NOT confirmed (p=0.402)
4. **Kelly f*=0.388** — current 1% is 0.0x Kelly fraction
5. **Loss/win asymmetry=0.84** — wins >= losses (favorable)

---
*Generated by L4_foundation_analysis.py*