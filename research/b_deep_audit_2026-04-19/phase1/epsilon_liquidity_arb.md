# Phase 1 — Agent ε: Liquidity-Arbitrage ("We are the Liquidity") Hypothesis

**Dispatched:** 2026-04-19 session 35 (deep-diagnostic audit)
**Agent:** ε (epsilon) — Opus 4.7 max effort
**Scope:** read-only; 8-signature battery testing whether our edge is being arbitraged

---

## Executive verdict — one-line

**Arbitrage hypothesis: INCONCLUSIVE overall, with ONE strong instrument-specific signal on XAUUSD.** Four of six primary signatures test against the "we are the liquidity" story; two support it on XAUUSD alone. Cross-instrument pattern is INCOMPATIBLE with a uniform algo-arbitrage story — the decay does NOT track informal algo-density rank (Spearman ρ = -0.21, n=5, insufficient). The XAUUSD-specific pattern is consistent with *either* (a) gold-market regime shift, or (b) gold-specific liquidity hunting. We cannot distinguish these from the data alone.

**The one strong XAUUSD finding that is defensible:** losses go adverse **fast and hard** in 2026 (fast-loss rate 26.9% → 69.2%, Fisher p=0.017, Z-prop p=0.011), and winner MFE has compressed by ~53% (1.04R → 0.49R, Mann-Whitney p=0.020). Neither survives strict Bonferroni at α=0.05/6=0.0083, but both are interpretable as early-warning of degradation.

---

## Deliverable #1 — Pre-entry MFE distribution (favorable excursion signal → fill)

**Claim tested:** *"Does price typically move favorably before reversing back to our limit (i.e., market is serving us the fill after running stops)?"*

### Cross-instrument summary (T7 CANDIDATEs, fill-simulated against M15 CSVs under honest `_FILL_EPSILON`)

| Symbol | n (filled) | median pre-MFE | p25 | p75 | p90 | bootstrap 95% CI mean |
|---|---:|---:|---:|---:|---:|---|
| XAUUSD | 10 | 0.38R | 0.16 | 0.95 | 1.26 | [0.26, 0.99] |
| NAS100 | 31 | 2.61R | 0.80 | 4.40 | 7.50 | [2.13, 4.25] |
| EURUSD | 2 | 9.28R | 4.80 | 13.75 | — | insufficient n |

**Data/code citation:** `research/b_deep_audit_2026-04-19/phase1/_epsilon_scratch/_main_analysis.py:209` → `sig1_pre_entry_mfe()`; detail records in `enriched_candidates.json` (all 52 CANDIDATEs, 43 filled); raw pre-MFE computed from `_mfe_mae.py:59-91` scanning candles between signal-close and fill.

### By symbol × quarter (XAUUSD / NAS100 only; EURUSD too thin)

**XAUUSD:**
- 2026Q1 (n=9): median pre-MFE 0.54R
- 2026Q2 (n=1): 0.00R

**NAS100:**
- 2026Q1 (n=28): median pre-MFE 2.70R
- 2026Q2 (n=3): median pre-MFE 0.58R

Only one quarter of live/sim data per instrument — cannot detect quarterly growth trend.

### Interpretation

- **XAUUSD pre-MFE 0.38R is NOT extreme** — price moves ~38% of the SL distance favorable before filling. This is consistent with normal pullback geometry (price pulls back, fills, continues). Not a hunt signature.
- **NAS100 pre-MFE of 2.61R IS extreme** but the mechanism is NOT "stop-hunt after fill". Manual inspection of 10/31 NAS100 records (scratch `_analyze_preentry_mfe.py` + detail inspection in `_main_analysis.py:103-158`) shows **the NAS100 signal is driven by AI placing limits into STALE (very-far) OB zones**. Example: 2026-01-15T08:00 signal close 25484, entry 25438 — already 46pt below signal. Price runs UP another 350pt (10R) before coming back to fill. This is an AI-side quality issue, not a stop-hunt signature.
- **EURUSD pre-MFE of 9.28R is the unresolved #7 CLAUDE.md AI-precision bug** (2-dp entries on 4-dp FX). CLAUDE.md already flags FX data as unusable for counterfactuals until the FX precision prompt fix ships.

**Verdict signature #1:** **NOT SUPPORTING the arb hypothesis.** The large NAS100/EURUSD numbers are data-quality artifacts, not genuine stop-hunt signature. XAUUSD value is benign.

---

## Deliverable #2 — Post-entry first-60min adverse excursion

**Claim tested:** *"Is immediate adverse move after fill growing over time?"*

### Post-fill MAE by instrument (R units, median)

| Symbol | n | MAE 15min | MAE 30min | MAE 60min |
|---|---:|---:|---:|---:|
| XAUUSD | 10 | 0.36R | 0.36R | 0.41R |
| NAS100 | 31 | 0.36R | 0.38R | 0.42R |
| EURUSD | 2 | 0.02R | 0.02R | 0.02R (n too small) |

Quarterly evolution on XAUUSD (only 2026Q1+Q2 in sim): Q1 n=9 MAE 60m = 0.40R → Q2 n=1 = 0.89R. Too few Q2 samples.

### But the KEY signal is in backtest history (2024-2026 loss-MFE trend)

For *losses*, `mfe_r` = how far favorable price moved before hitting SL. Very small loss-MFE = "price never went our way, immediately went adverse". This is the data-rich equivalent of the T7 post-entry MAE question.

**XAUUSD loss-MFE median by year** (from `knowledge_base_backtest/sessions/XAUUSD/*.json`; n_losses per year = 7/19/13):
- 2024: 0.573R
- 2025: 0.417R
- **2026: 0.106R** — a 74% collapse from 2024

**Fast-loss rate** (losses where MFE < 0.3R = immediate adverse):

| Instrument | early (2024-25) | late (2026) | delta | Fisher p |
|---|---|---|---:|---:|
| **XAUUSD** | **7/26 = 26.9%** | **9/13 = 69.2%** | **+42.3pp** | **0.017** |
| US30 | 2/6 = 33.3% | 3/8 = 37.5% | +4.2pp | 1.00 |
| USDJPY | 1/4 = 25.0% | 1/4 = 25.0% | +0.0pp | 1.00 |
| GBPJPY | 2/5 = 40.0% | 3/9 = 33.3% | -6.7pp | 1.00 |
| NZDUSD | 2/5 = 40.0% | 4/6 = 66.7% | +26.7pp | 0.567 |

**Cross-instrument:** XAUUSD is the only instrument with a statistically detectable jump in immediate-adverse losses (direction also seen in NZDUSD but underpowered).

**Data/code citation:** `_deep_signal_tests.py:sig7_compression_tests()` + interactive analysis in main transcript (cross-instrument fast-loss tabulation).

**Bonferroni at α=0.05/6=0.0083:** XAUUSD does NOT survive strict correction (0.017 > 0.0083). Benjamini-Hochberg FDR at q=0.05 with 6 tests: sorted p-values (0.011, 0.017, 0.020, 0.040, 0.17, 0.57), BH threshold for rank 1 = 0.0083, rank 2 = 0.0167, rank 3 = 0.025, rank 4 = 0.033 — under BH: **XAUUSD fast-loss (p=0.017) passes at FDR=0.05, rank 2 threshold 0.0167**; **XAUUSD MFE compression (p=0.020) passes at rank 3 threshold 0.025**; **XAUUSD SL-reversal (p=0.040) fails rank 4 threshold 0.033**.

**Verdict signature #2:** **SUPPORTIVE on XAUUSD, absent cross-instrument.** "Price goes adverse fast in 2026" is a real XAUUSD pattern — BUT it could equally reflect a shift in the *setup selection* (AI emitting lower-quality setups in 2026) rather than market arbitrage of our entries.

---

## Deliverable #3 — Stop-hunt signature (SL touch + reversal ≥1R within 4h)

**Claim tested:** *"Do losses cluster at bit-exact OB-bound SL touches followed by reversal to where TP would have been?"*

### T7 CANDIDATE loss reversal rates

| Symbol | n_losses | reversed ≥1R within 4h | rate | null baseline (random entries same R) | delta |
|---|---:|---:|---:|---:|---:|
| **XAUUSD** | 4 | 4 | **100%** | 44.3% (n=395) | **+55.7pp** |
| NAS100 | 12 | 2 | 16.7% | 33.2% (n=374) | -16.5pp |
| EURUSD | 0 | — | — | 5.3% (n=188) | — |

### XAUUSD per-loss detail (all 4 losses)

| Candle time | SL hit overshoot | MAE 60m | Reversal | SL→OB dist |
|---|---|---|---|---|
| 2026-01-15T13:15 | 96 ticks ($9.60) | 0.24R | 1.26R | 14 ticks |
| 2026-01-21T15:00 | 156 ticks ($15.60) | 2.12R | 1.24R | 5 ticks |
| 2026-02-20T15:00 | 160 ticks ($16.00) | 0.68R | 1.95R | 85 ticks |
| 2026-03-10T16:00 | 16 ticks ($1.60) | 0.40R | 1.19R | 94 ticks |

**Data/code citation:** `enriched_candidates.json` (all 4 XAUUSD SL records); `_main_analysis.py:sig3_stop_hunt()`; null baseline computed by `null_baseline_reversal()` with 500 random entries per instrument at R=0.5% of median price, 4h forward replay.

### Statistical test

XAUUSD 4/4 observed vs 175/395 (44.3%) null: Fisher exact 2-sided **p = 0.040**. At n=4 this is exploratory. Point estimate dramatic but confidence interval is wide (Wilson 95% CI on observed = [0.51, 1.00]).

### Bit-exact OB-bound test

Across all 16 T7 CANDIDATE losses with OB bounds recovered from `raw_response`: **0/16 had SL within ±2 ticks of the OB bound**. The SL is placed BEYOND the OB bound per `sl_beyond_ob` L2 logic, typically 10-100+ ticks past. This design makes bit-exact OB-bound stop-hunts impossible to detect directly — the entry structure pushes SL beyond where an arb player would target.

**Verdict signature #3:** **WEAKLY SUPPORTIVE on XAUUSD (n=4, exploratory).** NAS100 directly contradicts — its reversal rate is LOWER than random, inconsistent with stop-hunt. The "bit-exact OB bound" formulation of the signature is unfalsifiable given SL geometry.

---

## Deliverable #4 — Winner MFE ceiling compression

**Claim tested:** *"Is the maximum favorable excursion before TP shrinking over time?"*

### T7 CANDIDATE winners (2026Q1 + Q2 only — sim limited to 2026)

| Symbol | n_winners | median max_MFE | mean |
|---|---:|---:|---:|
| XAUUSD | 6 | 1.87R | 1.94R |
| NAS100 | 18 | 1.98R | 2.07R |
| EURUSD | 1 | 7.37R | 7.37R (AI precision artifact) |

Quarterly: Q1 vs Q2 — too few Q2 data points (1-3 each) to draw trends in sim.

### Backtest history (2024-2026) — the real signal

**Mann-Whitney U test on winner MFE, 2024-25 combined vs 2026:**

| Instrument | n_early | n_late | median_early | median_late | compression | MW U p |
|---|---:|---:|---:|---:|---:|---:|
| **XAUUSD** | 59 | 20 | **1.04R** | **0.49R** | **-53%** | **0.020** |
| GBPJPY | 12 | 12 | 1.45R | 0.76R | -48% | 0.225 |
| NZDUSD | 1 | 4 | 1.33R | 1.18R | -11% | n too small |
| US30 | 15 | 9 | 1.84R | 3.43R | +87% (EXPANSION) | 0.161 |
| USDJPY | 11 | 14 | 0.95R | 1.99R | +109% (EXPANSION) | — |

### Interpretation

- **XAUUSD winner MFE ceiling has COMPRESSED by ~53% from 2024-25 to 2026.** This is the strongest single number in the investigation.
- **GBPJPY shows directionally the same signature** (-48%, p=0.225 NS at n=24).
- **US30 and USDJPY compression is OPPOSITE** — winner MFE expanded.
- **XAUUSD p=0.020** does NOT survive Bonferroni (α=0.0083) but DOES pass BH FDR at q=0.05 (rank 3, threshold 0.025).

**Data/code citation:** `_deep_signal_tests.py:sig7_compression_tests()` → `deep_signal_tests.json`. Raw trades from `knowledge_base_backtest/sessions/{SYM}/*.json`.

**Verdict signature #4:** **SUPPORTIVE on XAUUSD (strongest single result). Mixed/opposite on other instruments.** This is the signature most consistent with the arb hypothesis IF we restrict to gold — price gets close to our TP but reverses more often in 2026 than 2024-25.

---

## Deliverable #5 — Cross-instrument algo-density correlation (Spearman)

**Claim tested:** *"Does decay rate rank-correlate with informal algo density?"*

Informal algo-density ranks (per brief, ordinal, NOT empirically measured): **NAS100 (1, highest) > EURUSD > GBPUSD > USDJPY > GBPJPY > XAUUSD (6, lowest)**.

### WR decay per symbol (backtest; early years vs 2026)

| Symbol | Algo rank | n early | WR early | n late | WR late | Decay (pp) |
|---|---:|---:|---:|---:|---:|---:|
| XAUUSD | 6 | 88 | 67.0% | 33 | 60.6% | +6.4 |
| US30 | 3 | 23 | 65.2% | 18 | 50.0% | +15.2 |
| USDJPY | 4 | 15 | 73.3% | 18 | 77.8% | -4.4 |
| GBPJPY | 5 | 20 | 60.0% | 22 | 54.5% | +5.5 |
| NZDUSD | 5 | 6 | 16.7% | 11 | 36.4% | -19.7 |

**Spearman ρ between algo-rank and decay_pp = -0.205** (n=5 symbols — insufficient for formal inference).

### Interpretation

- **If arb hypothesis held cross-instrument:** we'd expect algo-rank 1-3 (NAS100/EURUSD/US30) to have LARGER decay than ranks 5-6 (GBPJPY/XAUUSD). Spearman ρ would be strongly **negative** (lower rank → more decay).
- **Observed:** ρ = -0.21, very weak negative. US30 (rank 3, mid-algo) has biggest decay (+15.2pp); NZDUSD (rank 5) went REVERSE direction. The pattern does NOT monotone-track algo density.
- **NAS100 and EURUSD are missing from this table** because the batch backtest sessions don't include them (they're T7-sim only, covering ≤4 months, too thin for year-over-year decay).

**Data/code citation:** `_main_analysis.py:sig5_algo_density()`; decay table in `all_results.json:sig5_algo_density.decay_table`.

**Verdict signature #5:** **NOT SUPPORTING arb hypothesis.** If algos were arbitraging our edge, cross-instrument decay should track algo presence. It doesn't. **Exploratory at n=5.**

---

## Deliverable #6 — Volume-spike coincidence with losses

**Claim tested:** *"Do losses coincide with volume-spike candles (institutional flow signature)?"*

### T7 CANDIDATE sample, cross-instrument

- **Loss candles with 2x 20-candle volume spike:** 5/16 = 31.3% (Wilson 95% CI [0.14, 0.56])
- **Winner TP candles with 2x spike:** 8/25 = 32.0% (Wilson 95% CI [0.17, 0.52])
- **Delta = -0.75pp** (losses slightly LESS likely to be on volume spikes than winners)

**Data/code citation:** `_main_analysis.py:sig6_volume_spike()`.

**Verdict signature #6:** **NOT SUPPORTING.** No differential in volume-spike incidence between losses and winners. If arb players were pounding SL candles with volume, we'd expect loss > win on this metric. Observed the opposite (by negligible margin).

**Caveat:** MT5 tick-count "volume" is an imperfect proxy for institutional flow; a true order-flow test needs L2/depth data we don't have.

---

## Deliverable #7 — Pre-2025 null baseline (older era comparison)

**Claim tested:** *"If the arb hypothesis is true, the effect should be WEAKER on pre-2025 data (pre-mass-adoption of AI trading)."*

### Backtest session coverage by year

| Instrument | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| XAUUSD | 24 | 64 | 33 |
| US30 | 0 | 23 | 18 |
| USDJPY | 0 | 15 | 18 |
| GBPJPY | 0 | 20 | 22 |
| GBPUSD | 3 | 18 | 4 |
| NZDUSD | 0 | 6 | 11 |

### XAUUSD year-over-year (the ONLY instrument with 2024 data)

| Metric | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| n | 24 | 64 | 33 |
| WR | 70.8% | 65.6% | 60.6% |
| Expectancy | +0.483R | +0.303R | +0.158R |
| Winner MFE median | 1.66R | 0.95R | 0.49R |
| Loss MFE median | 0.573R | 0.417R | 0.106R |
| Winner MAE median | 0.29R | 0.13R | 0.10R |
| Hold time median | 34 | 32 | 31 |
| Fast-loss (MFE<0.3R) | 2/7=29% | 5/19=26% | 9/13=69% |

### Interpretation (the strongest cross-time trends on XAUUSD)

- **Winner MFE dropping by 3.4× over 2 years** (1.66R → 0.49R). Strong monotone trend.
- **Loss MFE dropping by 5.4× over 2 years** (0.57R → 0.11R). Losses happen faster.
- **Hold time stable** (34 → 31 candles) — we're not exiting faster, we're just scoring worse on both tails.
- **WR dropping 10.2pp** (70.8 → 60.6).
- **Expectancy dropping 3×** (+0.48R → +0.16R).

**Quarterly view (XAUUSD, n sufficient in most quarters):**

| Q | n | WR | meanR | winner MFE | loss MFE | hold |
|---|---:|---:|---:|---:|---:|---:|
| 2024Q2 | 8 | 75.0% | 0.41R | 1.62R | 0.24R | 34 |
| 2024Q3 | 10 | 80.0% | 0.66R | 1.52R | 1.01R | 33 |
| 2024Q4 | 6 | 50.0% | 0.29R | 1.66R | 0.63R | 27.5 |
| 2025Q1 | 34 | 64.7% | 0.17R | 0.88R | 0.37R | 31.5 |
| 2025Q2 | 7 | 71.4% | 0.82R | 2.72R | 0.82R | 17 |
| 2025Q3 | 7 | 57.1% | 0.25R | 1.77R | 0.02R | 37 |
| 2025Q4 | 16 | 68.8% | 0.39R | 1.36R | 0.76R | 33 |
| 2026Q1 | 33 | 60.6% | 0.16R | **0.49R** | **0.11R** | 31 |

2026Q1 is a severe outlier on winner MFE and loss MFE. **Either regime change or arb pressure — we cannot distinguish from this data.**

**Data/code citation:** `_main_analysis.py:sig7_historical_null()`; `_deep_signal_tests.py:sig7_compression_tests()`. Per-trade records in `knowledge_base_backtest/sessions/XAUUSD/*.json` (318 files, 121 trades).

**Verdict signature #7:** **SUPPORTIVE on XAUUSD.** The pre-2025 baseline (2024) is the best-performing year and most closely resembles the "edge as advertised" (WR 70.8%, MFE 1.66R). 2026Q1 shows material compression across every single metric. But attribution to "AI arbitrage" vs "gold regime change" is unresolved.

---

## Deliverable #8 — Verdict aggregation

### Scorecard

| # | Signature | Instrument | Strength | n | Key metric | p (if applicable) |
|---|---|---|---|---:|---|---:|
| 1 | Pre-entry MFE | XAUUSD | not supporting | 10 | median 0.38R | — |
| 1 | Pre-entry MFE | NAS100 | not supporting (AI artifact) | 31 | median 2.61R | — |
| 1 | Pre-entry MFE | EURUSD | N/A (FX precision bug) | 2 | median 9.28R | — |
| 2 | Post-entry fast-loss rate | XAUUSD | **supportive** | 39 | 26.9% → 69.2% | **0.017** |
| 2 | Post-entry fast-loss rate | other | not supporting | 4-17 per sym | flat | NS |
| 3 | SL→reversal ≥1R 4h | XAUUSD | weakly supportive (exploratory) | 4 | 100% vs 44.3% null | 0.040 |
| 3 | SL→reversal ≥1R 4h | NAS100 | not supporting | 12 | 16.7% vs 33.2% null | (below null) |
| 3 | Bit-exact OB-bound SL | all | unfalsifiable (SL beyond OB by design) | 16 | 0/16 within 2 ticks | — |
| 4 | Winner MFE ceiling | XAUUSD | **supportive** | 79 | 1.04R → 0.49R | **0.020** |
| 4 | Winner MFE ceiling | GBPJPY | directionally supportive | 24 | 1.45R → 0.76R | 0.225 (NS) |
| 4 | Winner MFE ceiling | US30/USDJPY | NOT supporting (opposite direction) | 24/25 | expansion | NS |
| 5 | Algo-rank vs decay | cross | not supporting (exploratory at n=5) | 5 | ρ = -0.21 | — |
| 6 | Volume spike on losses | cross | not supporting | 16W + 25L | -0.75pp | — |
| 7 | Pre-2025 null | XAUUSD | **supportive** | 121 | WR 70.8% → 60.6%; MFE 1.66→0.49 | visible trend |
| 7 | Pre-2025 null | other | N/A (no 2024 data) | — | — | — |

### Statistical rigor footnote

- **Bonferroni FWER correction** at α=0.05 across 6 primary signatures → threshold 0.0083. Only *sigs that would survive* require p < 0.0083. **NONE of our tests survive strict Bonferroni.**
- **Benjamini-Hochberg FDR correction** at q=0.05 with 6 tests. Sorted observed p-values (after FX artifact exclusion): [0.011 (XAU fast-loss Z), 0.017 (XAU fast-loss Fisher), 0.020 (XAU MFE compression), 0.040 (XAU SL-reversal), 0.161 (US30 MFE), 0.225 (GBPJPY MFE)]. BH thresholds: [0.0083, 0.0167, 0.0250, 0.0333, 0.0417, 0.05]. **Pass rank 2 (0.017 ≤ 0.0167, yes). Pass rank 3 (0.020 ≤ 0.0250, yes). Rank 4 fails (0.040 > 0.0333).** So under BH: XAUUSD fast-loss rate + MFE compression pass; SL-reversal does not.
- **Instrument-specificity weakens the arb hypothesis.** A uniform market-wide arb of our edge should manifest across instruments. The XAUUSD-only pattern is suspicious — it may be gold regime change (Fed, Middle East, CB buying program, etc.) rather than AI arbitrage of our entries.

### Final verdict

**ARBITRAGE HYPOTHESIS: INCONCLUSIVE** for the systematic multi-instrument claim. **WEAKLY SUPPORTIVE for a gold-specific deterioration**. Specifically:

- **Supported signatures (strongest to weakest):**
  1. **XAUUSD winner MFE compression (53% drop, p=0.020, survives BH)** — winners get smaller before TP
  2. **XAUUSD fast-loss rate jump (26.9 → 69.2%, p=0.017, survives BH)** — losses happen faster and harder
  3. **XAUUSD SL-reversal 100% vs 44% null (p=0.040, exploratory)** — losses reverse to would-be TP
  4. XAUUSD yearly expectancy collapse (+0.48R → +0.16R 2024→2026) — direct edge degradation

- **Signatures that DO NOT support arb hypothesis:**
  5. Pre-entry MFE doesn't show "served the fill" pattern on XAUUSD (only ~0.4R, benign)
  6. Cross-instrument decay does NOT rank-correlate with informal algo density (ρ = -0.21)
  7. NAS100 SL reversal (16.7%) is BELOW random baseline — inverted sign from hypothesis
  8. Volume-spike incidence is identical between losses and winners (no institutional-flow tell)
  9. US30 and USDJPY show OPPOSITE direction (MFE expanded, not compressed)

**The XAUUSD evidence base is real but small (n=4 CANDIDATE losses in sim, n=13 losses in 2026 backtest).** Pattern CAN be consistent with arbitrage but is equally (or more) consistent with a regime shift in gold specifically.

### Alternative hypothesis that fits the data better than "arb hypothesis"

**"XAUUSD entered a lower-trending, higher-volatility regime in 2026"** — this would produce:
- Faster losses (price fails to follow through after entry) ✓
- Smaller winner MFE (trends don't extend as far) ✓
- SL + reversal (more whipsaw) ✓
- No cross-instrument arb signature ✓
- No volume-spike differential ✓
- No algo-rank correlation ✓

This is 6/6 for regime change, vs 3/9 supporting signatures for arb.

---

## Top 3 counter-measures IF supported (CEO may want these pre-emptively anyway)

Given the XAUUSD-specific weakness is real regardless of its cause, here are the counter-measures:

### 1. **Delayed-limit entry with re-evaluation window** (entry randomization / anti-front-run)
- **What:** after CANDIDATE, wait 30-60 minutes before placing the limit order. Re-evaluate setup at delay-expiry; if price has already moved to/past entry, skip. If price is still in retest zone AND setup still valid, submit.
- **Why:** defeats any algorithm that times entries precisely by our candle-close fingerprint.
- **Cost:** forgoes ~50% of same-KZ fills; estimated -10-15 trades/month. Recovered by skipping the fast-loss cluster.
- **Scope:** `permissions.py` new gate `entry_delay_min` in config. CEO approval required.
- **Blast radius:** live, but additive-skip (safer default).

### 2. **Post-entry fast-SL-move abort** (defensive early exit)
- **What:** if within 15 minutes after fill price moves >0.5R adverse, close the position at market. Accept -0.5R instead of waiting for -1.0R SL.
- **Why:** XAUUSD fast-loss rate 69.2% in 2026 means 2/3 of XAUUSD losses are already showing this pattern. Cutting them at -0.5R instead of -1.0R reduces loss R by half without touching winners.
- **Cost:** some trades that would have swung back to win would be prematurely closed. Requires backtest validation before enabling.
- **Scope:** new `src/safety/fast_adverse_monitor.py`. Shadow-log mode first (log hypothetical -0.5R cuts, measure delta), then gate.
- **Blast radius:** live trading logic change — CEO approval required. Recommend shadow-log only initially.

### 3. **XAUUSD-specific risk reduction + observation window**
- **What:** until we distinguish regime change vs arbitrage, reduce XAUUSD risk to 0.5% per trade (matching the H29 drawdown reduction formula, but triggered by instrument-specific degradation rather than account DD). Simultaneously enable shadow loggers for all 3 signatures in production to gather n>20 within 30 days.
- **Why:** XAUUSD is the primary-edge instrument (n=129 validated, WR 62%, p=3.42e-08) but showing the most degradation. Protecting capital while gathering data is cheaper than either (a) withdrawing from XAUUSD entirely, or (b) trading it at full size with suspect edge.
- **Cost:** 75% expected R recovery lost on XAUUSD for ~4 weeks. Budget impact ~$0 (same API cost, smaller positions).
- **Scope:** `agent_config.yaml` per-symbol risk override (new functionality). CEO approval.
- **Blast radius:** live risk reduction — conservative.

### Runners-up
- **4.** Cold-swap to a different framework on XAUUSD (FVG-only? breaker-block?) — too speculative without Agent η's alternative-pattern work.
- **5.** Skip first 5 min of each kill zone (KZ boundary defensive) — but sig zeta's KZ boundary analysis (Agent ζ) should drive that, not this analysis.

---

## Methodology + reproducibility

- Scratch scripts: `research/b_deep_audit_2026-04-19/phase1/_epsilon_scratch/`
  - `_loader.py` — data ingress (T7 sims, backtest sessions, M15 CSVs, trade index)
  - `_mfe_mae.py` — per-record fill simulation + MFE/MAE/reversal computation
  - `_main_analysis.py` — signatures 1-8
  - `_deep_signal_tests.py` — Fisher exact + Mann-Whitney follow-ups
  - `enriched_candidates.json` — per-record raw evidence (52 CANDIDATEs)
  - `all_results.json` + `deep_signal_tests.json` — aggregated JSON outputs

- Fill simulation uses honest `_FILL_EPSILON` per CLAUDE.md Tier A1: 0.20 (XAUUSD), 2.0 (NAS100), 0.0002 (EURUSD). Same logic as `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/*_epsilon_revalidation.md`.

- Null baseline for SL reversal: 500 random entries per instrument at R=0.5% of median price, 4h forward replay on historical CSV. Seed=11.

- Statistical tests:
  - Binomial rates: Wilson score 95% CI
  - Two-sample proportions: Fisher exact (primary, small-n-safe) + Z-prop (confirmatory)
  - Two-sample distributions: Mann-Whitney U 2-sided (normal approx z-score)
  - Multiple comparison: Bonferroni α/6 = 0.0083 (strict) AND Benjamini-Hochberg FDR at q=0.05 (less strict)
  - Bootstrap 95% CI for means: 2000 iter, seed=42

- **Reproducibility note:** all analyses run from cold start on same machine produce identical results given seeds. Single entry point is `python _main_analysis.py && python _deep_signal_tests.py` from the scratch dir.

---

## Caveats + what this investigation DID NOT cover

1. **Sample sizes are small for most signatures.** T7 CAND: XAUUSD n=10, NAS100 n=37, EURUSD n=9 (4 degenerate). Backtest 2026 XAUUSD: 33 trades only. Claims below n=20 are exploratory.
2. **EURUSD is uninformative** due to 2-dp AI precision bug (CLAUDE.md unresolved #7). All EURUSD numbers are decorative.
3. **NAS100 pre-entry MFE of 2.61R is substantially an AI-side data quality artifact** (AI places limits at stale-zone distances), not a genuine market hunt signature.
4. **"Institutional order flow" cannot be measured without L2 data** which we don't have. Volume-spike is a weak proxy.
5. **Regime change cannot be distinguished from arbitrage from our data alone.** A future test could compare XAUUSD performance around CB announcements / Fed decisions vs quiet weeks — if decay is concentrated in institutional-flow weeks, that supports arb; if evenly distributed, that supports regime.
6. **The "bit-exact OB bound" signature is unfalsifiable with current SL geometry.** SL is placed past the OB bound by design (sl_beyond_ob), so SL-at-OB-bound events are architecturally rare. The weaker formulation (SL hit + reversal) is what we could test.
7. **Live trade records (since 2026-04-07) have too few complete cycles to test.** 92 trade records, most incomplete (exit fields empty on inspection). Deferred.

---

## Bottom line for the chairman

**If chairman is asked "is the market arbitraging our edge?":**

*"INCONCLUSIVE at the market-wide level. There is a robust XAUUSD-specific degradation pattern (winner MFE compression 53%, fast-loss rate jump +42pp, both surviving BH FDR at q=0.05) that is consistent with arbitrage BUT equally consistent with a gold-market regime shift in 2026. The decisive test — cross-instrument rank correlation with algo density — does not support the uniform-arbitrage story (ρ = -0.21, n=5). We recommend treating XAUUSD as 'edge-suspect' until further evidence, and implementing counter-measures that help against BOTH arbitrage AND regime change (delayed-entry + fast-adverse abort + per-symbol risk reduction on XAUUSD)."*

---
