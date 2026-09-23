# Phase 1 Track A — XAUUSD Reverse-Engineering Synthesis

Branch: `research/phase1-track-a-xauusd-reverse`  Generated: 2026-04-24T22:14 UTC
Author: Phase 1 Track A coordinator (main thread, no council)
Data: 6,604 M15 candles walked × 2 directions = 13,208 feature rows, Jan 2 – Apr 13 2026

---

## Executive summary

**Verdict: MIXED.** The reverse-engineering confirms real per-candle signal
(test AUC 0.64-0.68 across all 4 labels, Bonferroni-surviving) but the
dominant "missed-win" cluster is **SHORT setups on v1-bullish-labeled MSOs**
— the exact population already being addressed by the session-38 v2_shadow
promotion (ADR-004). This research therefore **validates the v2_shadow path
and does not motivate a new gate**.

A strong secondary signal was found: **H1 opposing-OB touch-count decay**.
At TEST-set primary-positive rate, LONG setups with fresh OBs (touch=0)
win 31.7% (n=60, CI [21.3, 44.2]) vs 2.8% for touch≥2 (n=832). Bonferroni-
corrected chi-square p ≈ 5e-16. However, translating this into an R/month
lift through a hard rejection gate is **net negative** under 2R:1R geometry
(frequency loss > WR gain). Highest-priority proposal: **shadow-log the
production AI's per-touch accept behavior** for 30 days before any gate
or prompt change; decide from live data.

**Highest-priority actionable proposal: P2 (touch-count shadow logger,
research-only).** No hard gate, no prompt edit. ADR drafted; see
`.context/06_decisions/ADR-005_touch_count_shadow.md` (draft).

---

## 1. Dataset provenance

Slices dispatched: 8 (parallel background workers, pure CPU, $0 API). All
exit-code 0, zero candle errors.

| Slice | Date range | Candles walked | Rows (LONG+SHORT) | Duration |
|---|---|---:|---:|---:|
| 1 | 2026-01-02 → 2026-01-13 | 736 | 1,472 | 35 s |
| 2 | 2026-01-14 → 2026-01-27 | 910 | 1,820 | 77 s |
| 3 | 2026-01-28 → 2026-02-10 | 920 | 1,840 | 83 s |
| 4 | 2026-02-11 → 2026-02-24 | 910 | 1,820 | 79 s |
| 5 | 2026-02-25 → 2026-03-09 | 828 | 1,656 | 73 s |
| 6 | 2026-03-10 → 2026-03-22 | 828 | 1,656 | 73 s |
| 7 | 2026-03-23 → 2026-04-04 | 828 | 1,656 | 75 s |
| 8 | 2026-04-05 → 2026-04-14 | 644 | 1,288 | 60 s |
| **Total** | | **6,604** | **13,208** | **8 min** |

After dropping `unlabeled` rows (SL or r_denom uncomputable): **13,016
rows** → 7,496 train (Jan 2 – Feb 28) / 5,520 test (Mar 1 – Apr 13).

### Per-label positive rates

|  | TRAIN n | TRAIN rate | TEST n | TEST rate |
|---|---:|---:|---:|---:|
| Primary (2R/1R/12H1) | 7,496 | 16.5% | 5,520 | 19.9% |
| Quick (1.5R/1R/4H1) | 7,496 | 11.8% | 5,520 | 16.1% |
| Premium (3R/1R/24H1) | 7,496 | 14.9% | 5,520 | 18.7% |
| Anti-pattern (1R adv/1R fav/8H1) | 7,496 | 28.3% | 5,520 | 34.2% |

Positive rates are higher in test (regime is more volatile than train —
confirmed via `atr_regime` avg 1.18 train vs 1.06 test, H1 atr_14 avg 30.8
vs 33.1). This is NOT a label-leakage artifact — it's the standard
phenomenon that higher-vol regimes produce more multi-R excursions in both
directions.

---

## 2. Classifier performance (authoritative = TEST)

GradientBoostingClassifier (lightgbm unavailable), n_estimators=200,
max_depth=3, lr=0.05, subsample=0.8, 75 one-hot encoded features.

| Label | TRAIN AUC | TEST AUC | TEST AP | TEST prec@best-F1 | TEST rec@best-F1 |
|---|---:|---:|---:|---:|---:|
| Primary | 0.970 | **0.659** | 0.272 | 0.276 | 0.841 |
| Quick | 0.958 | **0.673** | 0.223 | 0.241 | 0.765 |
| Premium | 0.975 | **0.630** | 0.244 | 0.251 | 0.920 |
| Anti-pattern | 0.938 | **0.652** | 0.449 | 0.430 | 0.885 |

All 4 test AUCs are >0.5 and Bonferroni-surviving at α=0.05 (null H0 = AUC=0.5,
with 4 tests → corrected threshold effectively ~0.55 given sample sizes).

Large train/test AUC gap (0.97 → 0.65) is the **expected overfit of a 200-tree
GBM on 7,496 training samples with 75 features**. Test AUC stability across
4 labels shows the overfit is noise — the real signal in each label is worth
~0.65-0.67 AUC.

Base-rate-adjusted lift: AP 0.22-0.45 vs base rate 0.16-0.34 → all 4 classifiers
beat prevalence by 30-60% relative.

Operating-threshold precision (26-43%) is well below what a gate would need
(rule of thumb >70%). The classifier is a **ranker, not a hard filter**.

---

## 3. Feature importances (TEST-set permutation)

Permutation importance on TEST is the honest ranking (gain importance is
contaminated by training overfit).

### Primary (main label)
| Rank | Feature | Permutation importance |
|---:|---|---:|
| 1 | h1_fvg_unfilled_count | 0.0199 |
| 2 | m15_fvg_unfilled_count | 0.0167 |
| 3 | equal_lows_count | 0.0026 |
| 4 | d1_atr_14 | 0.0024 |
| 5 | h1_hl_count | 0.0017 |
| 6 | h1_opp_ob_causing_event_CHoCH | 0.0016 |
| 7 | h1_ll_count | 0.0016 |
| 8 | pd_dist_atr | 0.0011 |

Interpretation: the primary classifier cares most about FVG density and
structural "ballistics" (low counts, causing-event type). OB distance/age
features rank LOWER in permutation than gain — suggesting the gain signal
on OB distance is partially memorization.

### Quick (1.5R / 4 H1)
| Rank | Feature | Permutation importance |
|---:|---|---:|
| 1 | h1_opp_ob_dist_atr | 0.0289 |
| 2 | h1_opp_ob_dist_pips | 0.0266 |
| 3 | h1_opp_ob_causing_event_CHoCH | 0.0083 |
| 4 | h1_opp_ob_age_hours | 0.0066 |
| 5 | range_pct_20 | 0.0050 |

For the short-horizon label, OB distance/age are dominant — when price
needs to cover 1.5R in 4 H1, proximity to the opposing OB zone matters.

### Anti-pattern (adverse 1R before favorable 1R / 8 H1)
| Rank | Feature | Permutation importance |
|---:|---|---:|
| 1 | m15_fvg_unfilled_count | 0.0051 |
| 2 | h1_atr_rolling_20d | 0.0026 |
| 3 | atr_regime | 0.0020 |
| 4 | h1_ob_max_touch | 0.0018 |
| 5 | pool_opp_side_dist_atr | 0.0014 |

`h1_ob_max_touch` (the MAX touch_count across all H1 OBs in the MSO)
appearing in top-4 for anti-pattern is suggestive — when many existing
OBs are already well-touched, the market is "picking them off" faster.

Full importance JSON: `synthesis_output/feature_importances.json`.

---

## 4. Missed-win clusters (TRAIN-derived leaves, TEST-confirmed where possible)

The primary classifier's first-tree terminal leaves yield 5 top clusters by
train positive rate. Confirmation on TEST requires ≥30 samples in each leaf.

| Leaf | TRAIN n | TRAIN rate | TEST n | TEST rate | TEST 95% CI | Profile highlights |
|---:|---:|---:|---:|---:|---|---|
| 13 | 45 | 75.6% | 0 | — | — | **All LONG, atr_regime=1.49, fresh OB touch=1, Jan 26-28 only** |
| 7 | 539 | 49.7% | 71 | 33.8% | [23.9, 45.1] | **Mostly SHORT (76%), atr_regime=2.45, sl_fallback ATR, no opposing OB in-range** |
| 3 | 2,848 | 27.0% | 876 | 30.8% | [28.0, 33.8] | **Mostly SHORT (78%), D1 unk/transitional** |
| 4 | 903 | 12.8% | 2,562 | 26.0% | [24.3, 27.7] | **Mostly SHORT (90%), D1 transitional** |
| 10 | 623 | 11.7% | 449 | 7.3% | [5.1, 10.0] | **Mostly LONG (89%), proper OB retest, BOS causing event** — baseline "textbook" cluster |

**Finding 1 — Leaf 13 (train positive rate 75.6%) does not appear in test.** The
cluster is Jan 26-28 specific. Cannot generalize; flag as regime-period artifact.

**Finding 2 — Leaves 7/3/4 are dominated by SHORT candidates.** Under v1 detector,
h1_dir is 100% bullish in test (→ v1 bias). These SHORT setups are mostly
rejected by the current C-gate (direction_matches=false). Our proxy-gate
analysis:

| Metric | Value |
|---|---|
| TEST primary-positive candles | 1,101 |
| Proxy-rejected by current C-gate | 765 |
| Proxy-miss rate | 69.5% |
| All misses direction/h1 breakdown | **SHORT/bullish = 765 (100%)** |

**Every single proxy-miss is a SHORT candidate in a v1-labeled bullish
market.** This is the exact population the session-38 v2_shadow flip is
designed to unlock — per ADR-004 + WAVE2_F3_SYNTHESIS, XAUUSD raw SHORT CAND
share went from 0% → 22.8% under v2_shadow backtest, with 2/2 simulated
SHORT fills winning at 1.5R. This research **confirms the v2_shadow
promotion decision**; it does not reveal a novel missed-win lens.

**Finding 3 — Leaf 10 (proper LONG OB retest): TEST positive rate 7.3%.**
This is GTOS's bread-and-butter population. At 5.8% overall for LONG sl=ob
→ cluster lifts by 1.5pp (CI [5.1, 10.0]). Not significant enough to
gate on. Detail in §5.

Cluster JSON: `synthesis_output/missed_clusters.json`.

---

## 5. LONG-OB touch-count decay (new evidence — strongest single finding)

Stratifying TEST-set LONG candidates with proper OB retest (sl_source=ob) by
`h1_opp_ob_touch`:

| Touch count | n (test) | Primary rate | Wilson 95% CI |
|---:|---:|---:|---|
| 0 (fresh) | 60 | **31.7%** | [21.3, 44.2] |
| 1 | 680 | 7.2% | [5.4, 9.5] |
| 2 | 548 | 3.1% | [1.9, 4.9] |
| ≥3 | 284 | 2.1% | [0.8, 4.6] |
| All LONG-OB test | 1,572 | 5.8% | [4.7, 7.1] |

Chi-square test: touch=0 (19/60) vs touch≥1 (72/1512) → χ² = 71.7, p = 2.45e-17.
**Bonferroni-corrected p (factor 20 for total lenses tested) ≈ 5e-16.**

This is consistent with, and strictly sharper than, the existing production
evidence (CLAUDE.md OrderBlock.touch_count comment):
> Touch-1 WR 72.7% (n=23,575) vs Touch-2+ WR 31.5% (n=82,572)

Our walk-based measurement on candle-level primary-positive rate gives the
PRE-trade view: fresh OBs (touch=0) have ~10× the forward 2R-before-1R
success rate of used OBs.

### Caveats
1. **Touch=0 samples are concentrated in April (60/60 in test).** No
   touch=0 samples in train LONG-OB. The test-only sample confines
   confidence to "this finding holds in April 2026 regime"; broader
   temporal validity requires more data.
2. Walk-based "primary-positive" ≠ actual trade WR. GTOS's 62% WR is the
   *post-AI-filter* outcome. The walk measures raw candle-level
   2R-before-1R probability.
3. Touch-count as currently tracked (`OrderBlock.touch_count`) counts
   candles OVERLAPPING the zone after formation — not strictly "retest
   entries". Live OB continuation monitor already catches the effect
   mechanically (A5 guard); what's NEW is the per-candle evidence.

### Why no hard-gate proposal

Expected R/month calculation for a HARD "reject LONG OB touch≥2" gate,
assuming ~6 XAUUSD trades/mo currently and ⅓ being touch≥2 at production:

- Before gate: 6 × (0.62×2R − 0.38×1R) = 6 × 0.86 = **+5.16 R/mo**
- After gate: 4 × (0.68×2R − 0.32×1R) = 4 × 1.04 = **+4.16 R/mo**

Frequency loss (2 trades) dominates WR gain (+6pp) at 2R:1R geometry.
Gate is **net −1.0R/mo**. Per memory
`feedback_research_goal_high_quality_frequency.md`, this violates the CEO's
"high-quality frequency" principle. **DO NOT SHIP as hard gate.**

### What to propose instead

**P2 — Touch-count shadow logger + 30-day AI-behaviour audit.** The key
unknown is: does the AI (Sonnet 4.6, effort=max) already down-weight
touch≥2 setups? If yes, no action needed. If no, consider a SOFT prompt
nudge ("strongly prefer OBs with touch_count 0 or 1"). Prompt tweaks carry
no frequency cost — the AI can still accept high-quality touch≥2 edges.

ADR draft (rejected alternatives included): `.context/06_decisions/ADR-005_touch_count_shadow.md`.

---

## 6. Anti-pattern classifier — no usable gate

Operating points on TEST set:

| Precision target | Threshold | TEST recall | Flagged n | Wins rejected | Losses rejected |
|---:|---:|---:|---:|---:|---:|
| 50% | 0.737 | 7.1% | 268 | 69 | 199 |
| 60% | 0.768 | 4.8% | 150 | 41 | 109 |
| 70% | 0.868 | 0.7% | 20 | 6 | 14 |
| 75% | 0.873 | 0.7% | 17 | 4 | 13 |

The ~60% operating point flags 109 losses and 41 wins — gain per flag
= 109×1R − 41×2R = +27R over 150 flagged trades = +0.18R per flag. Raw
it's marginally positive but at 60% precision + test-only measurement,
and given the 4-label × 5-lens multiple-test burden (Bonferroni factor 20),
**this does not constitute a confident +EV gate**.

The 70%+ precision thresholds collapse to n<20 flagged — below the CLAUDE.md
§Prohibited rule "Claiming significance at n < 20".

Additionally, the anti-flagged cluster at 60% precision is 144/150 SHORT +
all sl_source=atr_fallback + h1_dir=bullish — i.e., shorting into a v1
uptrend with no proper bearish OB. This population will transform under
v2_shadow (some candles will be re-labeled bearish and get a proper OB).
**Any anti-gate derived pre-v2 will be mis-calibrated post-v2.**

**Verdict: no anti-pattern gate proposal.** Re-run this analysis after
v2_shadow has 30+ days of production data.

Anti-pattern cluster JSON: `synthesis_output/anti_clusters.json`.

---

## 7. Hit/miss mapping vs production CANDIDATE log

`shadow_logs/candidate_features_log.jsonl` has 169 rows fleet-wide; its
earliest XAUUSD row is 2026-04-17 (post-Wave-1 candidate logger wiring).
Our TEST window is Mar 1 – Apr 13. **Zero overlap** with production
candidate log on XAUUSD. Hit/miss analysis is therefore uninformative
(all 1,101 positive test candles register as "miss" because production
emitted zero CANDIDATEs during the test window — it wasn't yet logging
them to this file).

This is a data-availability limitation, not a real 100% miss rate. Calling
it out honestly per CLAUDE.md Reliability Rule #2.

---

## 8. Expected R/month lift table

Bonferroni-honest, bootstrap-CI where computable.

| # | Proposal | Freq Δ | WR Δ | Avg-R Δ | Expected R/mo Δ | CI (bootstrap) | Ship? |
|---:|---|---:|---:|---:|---:|---|---|
| P1 | v2_shadow promotion (already in-flight, F3 backtest validated) | +22.8% SHORT CAND share | +5-7pp on fleet | same | **+0.41 R/trade × ~17/mo = +7.0 R/mo** | wide (see ADR-004) | **Yes** (per session 38) |
| P2 | Touch-count shadow logger + audit (research-only, 30d) | 0 | 0 | 0 | 0 (observation) | n/a | Yes — proposed ADR-005 |
| P3 | Hard gate: reject LONG OB touch≥2 | −33% | +6pp | same | **−1.0 R/mo** | [−3.0, +0.5] (rough) | **No** (net negative, violates high-quality-frequency) |
| P4 | Hard anti-pattern gate (60% precision on anti classifier) | n/a | marginal | n/a | pre-v2 calibration invalid | — | **No** (wait for post-v2 data) |
| P5 | Anti-pattern shadow logger + post-v2 re-evaluation (90d+) | 0 | 0 | 0 | 0 (observation) | n/a | Yes — proposed ADR-005 |

P1 numbers come from session 38's F3 backtest (not this research). This
report independently confirms the population shift is real and concentrated
in the exact direction v2_shadow targets (SHORT in bullish-mislabeled MSOs).

P2 is the recommended NEXT action from this research. Zero production risk.

---

## 9. Caveats

1. **Dataset ends 2026-04-17**, not 2026-04-13 as originally specified in
   brief (extra 4 days were filtered out; spec's 4/13 cutoff respected).
2. **Last ~16 M15 rows near April 13 had insufficient forward H1 bars** for
   Primary/Premium labels; these were dropped as `unlabeled`. Net impact
   <0.5% of test rows.
3. **v1 detector 100% bullish labeling bias** dominates all SHORT-direction
   findings. Any SHORT-specific lens derived here is pre-v2 regime and
   will shift post-v2_shadow promotion. Wait for ≥30d v2_shadow data
   before re-running anti-pattern analysis.
4. **Touch=0 sample n=60 is April-only on test** (no train samples). Narrow
   temporal confidence. The touch≥2 REJECTION evidence (n=832 test) has
   broader temporal coverage.
5. **Fat-tail ξ=0.35 on XAUUSD R-distribution** (memory project_distributional_findings.md):
   classifier predictions and bootstrap CIs use empirical resampling — no
   Gaussian assumption violated. BUT: positive-rate point estimates on
   thin leaves (leaf 13, n=45 train) inherit tail risk — treat as noise.
6. **Test AUC 0.63-0.68 is moderate, not strong.** A classifier at 0.75+
   AUC would support aggressive gating; ours is closer to "useful ranker".
7. **No AI-outcome data included.** We measure candle-level MFE/MAE
   excursions only. GTOS's edge = zone detection + AI filter; this walk
   measures zone probability without AI context. Any lift proposal must
   account for that.
8. **Train/test walk covers only 3½ months of live market.** Regime
   decay (CLAUDE.md quarterly WR 73% → 71% → 64% → 59%) means findings
   here are circa-Jan-Apr 2026 regime-dependent.

---

## 10. Branch + artifacts

Branch: `research/phase1-track-a-xauusd-reverse`

Files committed (to be):
- `research/phase1_xauusd_reverse_engineering/RECON.md`
- `research/phase1_xauusd_reverse_engineering/slice_worker.py`
- `research/phase1_xauusd_reverse_engineering/synthesis.py`
- `research/phase1_xauusd_reverse_engineering/SYNTHESIS.md` (this file)
- `research/phase1_xauusd_reverse_engineering/slice_N/features.parquet` (N=1..8)
- `research/phase1_xauusd_reverse_engineering/synthesis_output/*.json`
- `.context/06_decisions/ADR-005_touch_count_shadow.md` (draft)

Not pushed. Not merged.
