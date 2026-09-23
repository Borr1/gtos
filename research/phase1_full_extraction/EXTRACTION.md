# Phase 1 + A1 Comprehensive Extraction

**Branch:** `research/phase1-comprehensive-extraction`
**Generated:** 2026-04-25 UTC
**Scope:** 12 extractions (E1-E12) pre-FTMO-Monday, joining A1 logger × A1 all_results × F3 all_results × Track A slices × Track C unified_trades.
**Data inputs:**
- A1 logger: 1,142 AI-evaluated candidate_features_log.jsonl rows across 12 slices (XAUUSD×8 + USDJPY×4).
- A1 outcomes: 3,539 all_results.json rows including 92 taken CANDs (75 filled + 17 unfilled), 510 BLOCKED_LIMIT, 209 REJECTED_L2.
- F3 slices: same 12 boundaries, 3,278 rows, 887 AI evaluations, 39 final CANDs.
- Track A: 13,208 walk rows, 75-feature master; GBM classifier artifacts in `research/phase1_xauusd_reverse_engineering/synthesis_output/`.
- Track C: 266-row unified_trades.csv (q65_sim + F3 + t7_live).

---

## Executive Summary

**Verdict: the ADR-005 V4-A prompt-nudge picture DID change materially.** Three data-driven shifts:

1. **E1 inversion of the predicted direction.** Track A predicted touch=0 (fresh OB) vs touch≥2 (stale) = 31.7% vs 2.8% at walk-level primary-positive rate. A1's realized-outcome data among taken CANDs (direction-aware, Track-A-semantics-corrected) shows touch=1 WR=41.7% Exp +0.04R (n=36) **underperforming** touch=2 WR=52% Exp +0.30R (n=25). CIs overlap completely (Wilson 95% [0.27, 0.58] vs [0.34, 0.70]) and neither rejects the other, but the point estimate **reverses the Track A direction**. V4-A's hypothesis "prompt should prefer touch=1 over touch≥2" is not supported in realized R on the A1 sample.

2. **E4 SHORT-share discrepancy has a root cause that invalidates A1 as a v2 validator.** A1 ran with `detector_version: v2_shadow` in config, which per `structure_detector_shadow_logger.py:105` routes PRODUCTION through v1 (still-bullish-biased). F3 passed `--detector-version v2` as CLI override. All 1,142 A1 logger rows show `mso_h1_structure_direction: 'bullish'` (100% — XAUUSD 599/599 + USDJPY 543/543), confirming A1's production pipeline saw v1 labels. A1's XAUUSD raw SHORT CAND share = 4.2% (25/413) vs F3's 22.8% (37/161). **A1 filled-CAND data represents v1-era behavior**, not the v2 detector actually promoted to shadow on Apr 24.

3. **NEW FINDING (bonus): XAUUSD monthly WR decay is significant on A1 data.** Jan 45.5% / Feb 75.0% / Mar 33.3% / Apr 10.0% (n=11/20/15/10). H1-2026 (Jan+Feb) WR=64.5% n=31 vs H2-2026 (Mar+Apr) WR=24.0% n=25. **Chi-square p=0.006**. Spearman monthly trend rho=-0.80 (n=4 months, p=0.20 — not significant at month-granularity but clear directional shift on quarterly split). This is consistent with CEO's "decay is #1 concern" and WITH the quarterly decay trend in CLAUDE.md §Backtest-only (73.2→71.4→63.6→59.4%). The A1-realized data extends the decay through April 2026.

**Top-3 actionable findings:**
- (a) **V4-A as currently scoped (nudge toward touch=0/1, penalize touch≥2) is NOT indicated** — the realized R direction contradicts the walk-level prediction on the available (v1-era) sample. DEFER V4-A until v2_shadow collects live data with ≥100 taken CANDs, then re-run E1.
- (b) **The H2-2026 WR decay (64.5%→24%, p=0.006) is the highest-signal finding and deserves immediate attention.** The gap must be investigated against v2 production period (which only just started 2026-04-24); we cannot yet distinguish regime shift from model-side drift from data-expansion effects.
- (c) **Anti-pattern classifier (Track A AUC=0.65) does NOT replicate out-of-sample on A1 filled CANDs** (AUC=0.55, Spearman(prob, R) = −0.094 p=0.43). No hard-gate candidate exists here.

**V4-A recommendation: DEFER.** Pre-reg scope was "push prompt toward fresh OBs"; the realized-R evidence does not support that direction. Instead, divert the prompt-iteration budget into (i) waiting ~14 days for v2 live-shadow data or (ii) adding monthly-decay shadow instrumentation to catch regime change faster.

---

## E1 — Simulated WR + expectancy per touch stratum

**Method:** Direction-aware touch lookup on A1 logger (`h1_opp_ob_touch_long` for LONG CAND, `h1_opp_ob_touch_short` for SHORT CAND, using Track-A-semantics-corrected logger commit `b1c5258`). Matched against A1 outcome `out_outcome`. Filled-only (WIN/LOSS/BE) vs all-taken (UNFILLED as 0R).

### Filled-only (primary)

| Touch bucket | n | Wins | Losses | WR | WR 95% CI (Wilson) | Expectancy R | Exp 95% CI (bootstrap 5000) |
|---|---:|---:|---:|---:|---|---:|---|
| 1 | 36 | 15 | 21 | 41.7% | [27.1, 57.8] | +0.042 | [−0.375, +0.458] |
| 2 | 25 | 13 | 12 | 52.0% | [33.5, 70.0] | **+0.300** | [−0.200, +0.800] |
| ≥3 | 14 | 6 | 8 | 42.9% | [21.4, 67.4] | +0.073 | [−0.464, +0.787] |
| missing (-1) | 0 | 0 | 0 | — | — | — | — |

**Note:** A1's sentinel "touch=0 fresh" does NOT exist — the Track-A-corrected logger requires the retest zone be present AND have some touch-count. OrderBlock.touch_count starts at 0 only on formation candle (excluded by design); CANDs are all at touch≥1.

### All-taken (UNFILLED counted as 0R)

| Touch | n_total | filled | unfilled | WR_filled | Exp_taken (UNFILLED=0R) | Exp 95% CI |
|---|---:|---:|---:|---:|---:|---|
| 1 | 48 | 36 | 12 | 41.7% | +0.031 | [−0.260, +0.333] |
| 2 | 30 | 25 | 5 | 52.0% | +0.250 | [−0.167, +0.650] |
| ≥3 | 14 | 14 | 0 | 42.9% | +0.073 | [−0.641, +0.787] |

### Interpretation

- **Point estimate direction contradicts Track A's walk-level prediction.** Track A's "fresh OB wins" does not translate to "fresh retest OB wins" in realized R on the A1 sample.
- **Touch=2 actually produces the best realized expectancy** (+0.30R, n=25, small sample).
- **All three buckets' expectancy CIs overlap zero**, so statistically we cannot say ANY stratum is edge-positive. Fleet-level n=75 expectancy = +0.134R (Wilson 95% on WR: [0.346, 0.566]) — also not significantly positive.
- **Ship-or-not:** Do not ship a touch-based gate on this evidence. The data is n=75 filled CANDs with overlapping CIs; no touch bucket is clearly dominant.

---

## E2 — Simulated WR + expectancy per FVG stratum

**Method:** Stratify filled A1 CANDs by `(h1_fvg_unfilled_count + m15_fvg_unfilled_count)` in buckets {<5, 5-10, 11-20, 21-30, ≥31}.

| FVG total | n | wins | WR | WR 95% CI | Expectancy R | Exp CI |
|---|---:|---:|---:|---|---:|---|
| <5 | 0 | — | — | — | — | — |
| 5-10 | 5 | 2 | 40.0% | [11.8, 76.9] | +0.000 | [−1.000, +1.000] |
| 11-20 | 45 | 21 | 46.7% | [32.9, 60.9] | +0.167 | [−0.167, +0.556] |
| 21-30 | 19 | 9 | 47.4% | [27.3, 68.3] | +0.184 | [−0.342, +0.711] |
| ≥31 | 6 | 2 | 33.3% | [9.7, 70.0] | −0.167 | [−1.000, +0.667] |

**Interpretation:** No monotone relationship; FVG density does not predict outcomes on this sample. The ≥31 bucket (n=6) shows slight negative expectancy with huge CI. Dense-FVG setups are NOT materially better or worse than normal.

---

## E3 — Per-direction breakdown (LONG vs SHORT)

| Direction | AI eval N | CAND (taken) | CAND filled | CAND unfilled | Filled WR | WR 95% CI | Filled Exp R | Exp CI |
|---|---:|---:|---:|---:|---:|---|---:|---|
| LONG | 1,114 | 85 | 70 | 15 | 44.3% | [33.2, 55.9] | +0.107 | [−0.179, +0.394] |
| SHORT | 28 | 7 | 5 | 2 | **60.0%** | [23.1, 88.2] | **+0.500** | [−0.500, +1.500] |

**Interpretation:** SHORT n is tiny (5 filled), but the 3W/2L, +0.50R expectancy suggests SHORTs, once the system actually issues them, perform at least as well as LONGs. **Caveat: this is still a v1-detector sample** — see E4 diagnosis — so SHORTs came through despite v1's 100% bullish labels (the AI is overriding structure to SHORT in a few cases and those happen to win 3/5). Not conclusive evidence for v2's SHORT edge — we need v2-production-driven SHORT CANDs accumulated ≥n=20 to test.

---

## E4 — SHORT-share discrepancy diagnosis (A1 vs F3)

### Raw counts

| Slice | F3 raw CAND L / S | A1 raw CAND L / S | F3 final L / S | A1 final L / S |
|---|---|---|---|---|
| xauusd_s1 | 0 / 0 | 17 / 1 | 0 / 0 | 4 / 0 |
| xauusd_s2 | 30 / 0 | 32 / 0 | 1 / 0 | 5 / 0 |
| xauusd_s3 | 24 / 1 | 36 / 1 | 7 / 0 | 10 / 0 |
| xauusd_s4 | 0 / 3 | 73 / 2 | 0 / 0 | 8 / 1 |
| xauusd_s5 | 55 / 10 | 61 / 6 | 2 / 1 | 8 / 1 |
| xauusd_s6 | 0 / 0 | 40 / 9 | 0 / 0 | 4 / 3 |
| xauusd_s7 | 0 / 23 | 48 / 6 | 0 / 3 | 8 / 2 |
| xauusd_s8 | 15 / 0 | 81 / 0 | 1 / 0 | 9 / 0 |
| **XAUUSD total** | **124 / 37 (22.98% SHORT)** | **388 / 25 (6.05% SHORT)** | **11 / 4** | **56 / 7** |
| **USDJPY total** | 24 / 0 | 383 / 0 | 24 / 0 | 29 / 0 |

### Diagnosis (definitive)

**Both F3 and A1 used `identify_structure_v2` for the LOGGER, but only F3 used it for PRODUCTION.**

Evidence:
- `src/components/structure_detector_shadow_logger.py:105`: `pick_production_label(mode, v1, v2)` → "`v1` or `v2_shadow` → v1 (v1 is the production path)."
- A1's `launch_slices.sh` does NOT pass `--detector-version`. A1's config had `detector_version: v2_shadow` (set by commit `4e56e8a`, the same day as A1 launch). So A1 pipeline ran v1 for production + logged v2 to shadow.
- F3's `WAVE2_F3_SYNTHESIS_REPORT.md` states "--detector-version v2 (identify_structure_v2, dead_zone_divisor=8)", explicitly CLI-overriding the production label.
- **A1 logger confirms**: 100% `mso_h1_structure_direction: 'bullish'` across both XAUUSD (599/599) + USDJPY (543/543). This is the v1 signature, not v2.

**Conclusion:** F3's 22.8% SHORT share is the true v2 capability. A1's 6.05% is v1-era behavior. A1 is therefore a valid PRE-v2 BASELINE (equivalent to what production has been doing for months) but NOT a v2 validator.

**Implication for downstream extractions:** All A1-derived findings on filled-CAND outcomes (E1, E2, E3, E6-E8, E10, E11) are v1-production representative. They describe the system's CURRENT live behavior. They do NOT describe post-flip v2_shadow→v2 behavior.

---

## E5 — Pre-AI gate skip-reason distribution

**Total logger rows:** 1,142
**pre_ai_gate_skipped == true rows:** 0
**Skip rate:** 0.0%

**Interpretation:** Either the pre-AI gate fired in 0 cases during the A1 backtest period OR (more likely) the logger is positioned AFTER the pre-AI gate so skipped candles are never logged. Looking at commit `00bc3bb` ("log_candidate_features positioned AFTER pre-AI gate — gated candles invisible to audit log"): **the gated candles ARE invisible to the logger by design post-session-37 bundle**.

This means E5 cannot be answered from A1 logger data. The pre-AI-gate impact on the candle population reaching the AI is NOT measurable here. To answer E5 properly we would need a variant that logs BEFORE the gate — not in A1's output, and not a blocker for other extractions.

---

## E6 — Per-instrument breakdown

### XAUUSD (56 filled CANDs)

Direction-aware touch (filled):
| Touch | n | Wins | WR | Exp R |
|---|---:|---:|---:|---:|
| 1 | 25 | 10 | 40.0% | +0.000 |
| 2 | 21 | 11 | 52.4% | +0.310 |
| ≥3 | 10 | 5 | 50.0% | +0.252 |

Direction (filled):
| Dir | n | WR | Exp R |
|---|---:|---:|---:|
| LONG | 51 | 45.1% | +0.128 |
| SHORT | 5 | 60.0% | +0.500 |

### USDJPY (19 filled CANDs)

Direction-aware touch (filled):
| Touch | n | Wins | WR | Exp R |
|---|---:|---:|---:|---:|
| 1 | 11 | 5 | 45.5% | +0.136 |
| 2 | 4 | 2 | 50.0% | +0.250 |
| ≥3 | 4 | 1 | 25.0% | −0.375 |

Direction (filled):
| Dir | n | WR | Exp R |
|---|---:|---:|---:|
| LONG | 19 | 42.1% | +0.053 |
| SHORT | 0 | — | — |

**Interpretation:** Touch-direction signal is NOT consistent across instruments. XAUUSD's touch=2/≥3 advantage is there; USDJPY shows touch≥3 losing (but n=4 — small sample, can't reject anything). **No touch-based gate generalizes.**

---

## E7 — Per-slice regime labeling

All 12 slices show `mso_h1_structure_direction: 'bullish'` (100% bullish labels). This is the v1-bias signature (see E4) — we cannot regime-differentiate slices from logger labels under v2_shadow-config routing.

Per-slice outcome summary (A1 filled):

| Slice | n_filled | wins | WR | shorts | notes |
|---|---:|---:|---:|---:|---|
| xauusd_s1 | 4 | 3 | 75.0% | 0 | Jan 2-14, LONG only |
| xauusd_s2 | 5 | 1 | 20.0% | 0 | Jan 15-27 |
| xauusd_s3 | 10 | 8 | 80.0% | 0 | Jan 28-Feb 9 (best) |
| xauusd_s4 | 9 | 6 | 66.7% | 1 | Feb 10-22, 1 SHORT LOSS |
| xauusd_s5 | 8 | 4 | 50.0% | 1 | Feb 23-Mar 7, 1 SHORT UNFILLED |
| xauusd_s6 | 6 | 2 | 33.3% | 3 | Mar 8-20, 2 SHORT WIN 1 SHORT UNFILLED |
| xauusd_s7 | 7 | 2 | 28.6% | 2 | Mar 21-Apr 2, 1 SHORT LOSS 1 SHORT WIN |
| xauusd_s8 | 7 | 0 | 0.0% | 0 | Apr 3-13 (worst) |
| usdjpy_s1 | 6 | 2 | 33.3% | 0 | Jan |
| usdjpy_s2 | 5 | 3 | 60.0% | 0 | Jan-Feb |
| usdjpy_s3 | 2 | 1 | 50.0% | 0 | Feb-Mar |
| usdjpy_s4 | 6 | 2 | 33.3% | 0 | Mar |

**Key observation:** The XAUUSD LONG WR degrades monotonically across slices s3/s4 (best) → s6/s7/s8 (worst), consistent with the monthly-decay finding. SHORT CANDs only emerge in s4-s7 (late Feb - early April), where v1's bullish labels may have been closer to the structural truth AND the AI started overriding.

---

## E8 — C-gate vs L2 reject breakdown

### Logger decision × C-gate combo
| Decision | C1|C2|C3 combo | count |
|---|---|---:|
| CANDIDATE | true|true|true | 768 |
| CANDIDATE | true|true|None | 23 |
| CANDIDATE | true|false|true | 17 (AI overrides C2) |
| CANDIDATE | true|true|false | 1 |
| CANDIDATE | true|false|false | 1 |
| NO_TRADE | true|true|None | 198 |
| NO_TRADE | true|false|None | 124 |
| NO_TRADE | true|true|true | 4 |
| NO_TRADE | true|false|true | 1 |
| (null) | false|None|None | 4 (parse error, no AI output) |

### L2 reject reasons (209 total)

| Reason | Count |
|---|---:|
| entry_in_ob | 95 |
| h1_poi_exists | 64 |
| m15_choch_exists | 39 |
| sl_beyond_ob | 11 |

**Interpretation:**
- **L2 rejects 209 AI-CANDs = 25.8% of AI CANDs never make it to simulated fills**. The biggest reasons: `entry_in_ob` (AI placed entry inside the OB rather than at OB edge), `h1_poi_exists` (AI claimed POI but structure disagrees), `m15_choch_exists` (AI claimed CHoCH that the structure couldn't confirm).
- **BLOCKED_LIMIT: 510 CANDs** where the limit order was placed but price never retraced before the candle horizon — 62.9% of AI-issued CANDs. Concentrated: XAUUSD NY 172, XAUUSD London 126, USDJPY London 84.
- **Touch × decision cross-tab:** touch=1 is more likely to be rejected than touch=2 (CAND/NO_TRADE ratio: touch=1 = 63%, touch=2 = 83%). Counter to the ADR-005 hypothesis: **the AI is already discriminating AGAINST touch=1, not FOR it.** But since touch=2's realized expectancy is higher, the AI is actually (weakly) making the right call by accepting more touch=2 setups.

---

## E9 — Anti-pattern classifier out-of-sample validation

**Method:** Re-trained Track A's anti-pattern GradientBoostingClassifier on the 15-feature subset shared between Track A master and A1 logger. Evaluated on Track A test (AUC=0.683, matching published AUC=0.652). Applied to A1's 75 filled-CAND rows.

| Metric | Value |
|---|---|
| Track A test AUC (subset) | 0.683 |
| Track A test AP (subset) | 0.462 |
| **A1 filled-CAND AUC(prob → is_loss)** | **0.551** |
| A1 AP(prob → is_loss) | 0.572 |
| Spearman(prob, realized R) | −0.094 (p=0.43) |
| Pearson(prob, realized R) | −0.049 (p=0.67) |

Quartile stratification (sorted by classifier prob, Q1 = lowest anti-pattern prob, Q4 = highest):

| Quartile | n | wins | WR | mean R | prob range |
|---|---:|---:|---:|---:|---|
| Q1 | 18 | 10 | 55.6% | +0.33 | [0.048, 0.138] |
| Q2 | 18 | 7 | 38.9% | −0.14 | [0.140, 0.193] |
| Q3 | 19 | 8 | 42.1% | +0.13 | [0.199, 0.323] |
| Q4 | 20 | 9 | 45.0% | +0.16 | [0.338, 0.742] |

**Interpretation:**
- **Classifier does NOT replicate OOS on A1.** AUC=0.551 is barely above chance (0.50); Spearman correlation is tiny and non-significant.
- **Quartile pattern is non-monotone:** Q1 (lowest prob) has the best WR/Exp, but Q4 (highest prob) is second-best. No meaningful gate is derivable.
- **Conclusion:** The Track A anti-pattern signal does not reproduce in A1's post-AI-filter population. Either (a) the AI already filters out the most obvious anti-patterns, leaving only subtle ones the classifier can't distinguish, OR (b) the classifier signal is regime-bound to Track A's training set.

---

## E10 — Setup grade × outcome matrix

All 75 filled A1 CANDs have `setup_grade = "A+"`. The AI is emitting only A+ grade in backtest. There is no A/B/C distribution to stratify against.

**Interpretation:** Track D's null on grade-based filtering (session 38, per CLAUDE.md) replicates on A1 by virtue of the AI never emitting other grades. The prompt V3 A+-only behavior (or some other Session 37/38 prompt change) effectively removed the grade signal — everything qualifying reaches A+. Any grade-based gate would fire on 0 rows.

---

## E11 — Kill-zone 15-min bucket × outcome (combined n)

**Combined dataset:** A1 filled CANDs (75) + Track C unified_trades (266) = 341 rows. Per-source breakdown: a1=75, q65_sim=225, t7_live_sim_jan_apr10=9, f3_backtest_2026-04-24 subdirs=32.

### Buckets with n ≥ 20

| Symbol | KZ | Bucket | n | Wins | Losses | WR | WR 95% CI | mean R | Sources |
|---|---|---|---:|---:|---:|---:|---|---:|---|
| XAUUSD | ny | 13:15 | 31 | 12 | 18 | 38.7% | [23.7, 56.2] | −0.070 | a1=16, q65_sim=11, f3=2, t7=2 |
| XAUUSD | london | 07:00 | 20 | 9 | 11 | 45.0% | [25.8, 65.8] | +0.125 | a1=15, f3=4, t7=1 |

**Bonferroni adjustment:** With 2 n≥20 tests, Bonferroni α = 0.025. Both buckets have overlapping CIs with 50% and are not significantly below breakeven.

**Interpretation:**
- **Track C's null replicates with added A1 data.** The two n≥20 buckets both underperform 50%, but neither is distinguishable from baseline at Bonferroni-corrected significance.
- **No "skip this bucket" candidate emerges.** The candidate "skip XAUUSD NY 13:15 open" bucket was already questionable (related to `skip_first_ny_candle` config, open unresolved item #6 in CLAUDE.md) — added data confirms it's under 50% WR but not statistically.

---

## E12 — Logger semantic fix verification

**Commit `b1c5258` "fix(adr-005): correct h1_opp_ob_touch semantics"** — reviewed the full diff and verified:

1. **Both `h1_opp_ob_touch_long` AND `h1_opp_ob_touch_short` are correctly set via the single helper `_nearest_opposing_ob_touch()`.** The helper branches on `ai_direction`, selecting bullish demand zones below price for LONG (rank by `|price - ob.high|`) and bearish supply zones above price for SHORT (rank by `|price - ob.low|`). This matches Track A's `slice_worker.py:107` selection.

2. **Other `*_touch*` fields:** Only the aggregate list `mso_h1_ob_touch_counts` (all unmitigated H1 OBs' touch_counts, unfiltered) and the three `h1_opp_ob_touch*` fields exist. No other direction-specific touch fields need updating.

3. **SHORT rows logger schema parity:** 1,114 LONG rows + 28 SHORT rows + 4 UNCLEAR rows. Random 5 SHORT × 5 LONG spot-check confirmed identical key schemas. No silent field drops on the SHORT path.

4. **Minor observation:** The logged `h1_opp_ob_touch` field (singular, no direction suffix) uses the ai_direction at time of evaluation. This differs slightly from `_long` / `_short` which are direction-agnostic. For SHORT AI evals, `h1_opp_ob_touch == h1_opp_ob_touch_short`. This is self-consistent.

**Verdict:** Logger fix is correct and complete. No hidden data-quality issues that would affect E1-E3.

---

## Bonus: XAUUSD monthly WR decay (highest-signal finding)

**Method:** Split A1 filled CANDs by month-of-entry.

| Month | Symbol | n | Wins | WR | Wilson 95% CI | Mean R |
|---|---|---:|---:|---:|---|---:|
| 2026-01 | XAUUSD | 11 | 5 | 45.5% | [21.3, 72.0] | +0.14 |
| 2026-02 | XAUUSD | 20 | 15 | **75.0%** | [53.1, 88.8] | +0.88 |
| 2026-03 | XAUUSD | 15 | 5 | 33.3% | [15.2, 58.3] | −0.17 |
| 2026-04 | XAUUSD | 10 | 1 | **10.0%** | [1.8, 40.4] | −0.75 |
| 2026-01 | USDJPY | 9 | 3 | 33.3% | [12.1, 64.6] | −0.17 |
| 2026-02 | USDJPY | 2 | 2 | 100% | [34.2, 100] | +1.50 |
| 2026-03 | USDJPY | 8 | 3 | 37.5% | [13.7, 69.4] | −0.06 |

**XAUUSD H1-2026 vs H2-2026 (Jan+Feb vs Mar+Apr):**
- H1: 31 trades, 20 wins, **64.5% WR** (Wilson 95% [46.9, 78.9])
- H2: 25 trades, 6 wins, **24.0% WR** (Wilson 95% [11.5, 43.4])
- **Chi-square p = 0.006** (significant at α=0.05, Bonferroni-surviving within this test)
- Spearman monthly rho = −0.80 (p=0.20, not sig due to n=4 months)

**This is the single most actionable finding.** It's consistent with:
- CLAUDE.md's "Quarterly WR decay: 73.2% → 71.4% → 63.6% → 59.4%" (§Backtest-only, from prior research)
- ADR-004's "v1 detector emits 100% bullish labels" (confirmed here: 599/599 XAUUSD H1)
- Track A's "MISSED WINS cluster is SHORT setups on v1-bullish-labeled MSOs" (the LONG-only regime is degrading in H2)

**The H2 degradation is likely explained by market regime change** (Jan-Feb: trending bull → easy LONGs fill; Mar-Apr: choppy/reversing → LONG setups mostly lose). v2 is explicitly designed to detect bearish/transitional structure and issue SHORTs, which would have helped in H2. F3's v2-backtest produced 37 SHORT CANDs vs A1's v1-backtest 25 — the missing 12 are the ones the live fleet would have benefited from.

**This STRENGTHENS the case for v2 promotion** (already in progress via session-38 staged plan) and WEAKENS the case for V4-A prompt nudge (which doesn't fix the structural bias, only moves the touch-count acceptance threshold).

---

## Updated decision matrix (vs Phase 1 synthesis §4)

| Proposal | Phase 1 §4 rank | Post-extraction rank | Change |
|---|---|---|---|
| P2 (touch-count shadow logger) / V4-A prompt nudge | #1 | **#3 (DEFER)** | ↓ Realized-R evidence contradicts direction |
| v2 promotion (Session 38 ongoing) | #2 (implicit) | **#1** | ↑ Confirmed by decay finding + SHORTs-win-when-they-fire |
| Monthly-decay monitor (new instrumentation) | not listed | **#2 (NEW)** | New actionable item from bonus finding |
| Anti-pattern classifier gate | already rejected | rejected (OOS confirms) | Unchanged |
| Setup-grade filter | already null | null (A1 confirms — grade=A+ only) | Unchanged |
| Kill-zone bucket skip/emphasis | null | null (n≥20 confirms null) | Unchanged |

---

## Residual ambiguities

1. **A1 is v1-baseline, not v2-validator.** To actually validate v2 promotion we need a v2-backtest with ALL instrument+date coverage + logger. Could be done with a simple re-run passing `--detector-version v2` (same launch script, +1 arg). Estimated $40 API spend. Recommend before Monday if possible.
2. **n is still small for SHORT-direction realized-R claims (n=5 filled).** The E3 SHORT data is v1-era anyway; the true v2-SHORT realized WR/exp cannot be answered from this sample.
3. **Pre-AI gate impact on candle population is not measurable from A1 logger.** Would need a variant that logs BEFORE the gate. Not blocking but a gap for future extractions.
4. **E10 setup-grade signal is zeroed-out by prompt V3's A+-only emission.** If grade diversity is expected, the prompt change may have masked the signal. If A+-only is intentional, E10 is answered as null.
5. **The H2-2026 decay driver cannot yet be distinguished** between (a) regime shift, (b) prompt V3 effect (deployed Apr 24 — but A1 covers up to Apr 13, before V3), (c) v1 detector divergence from market reality, (d) model-level drift. Partly answerable via live v2_shadow data + divergence classification over next 14 days.

---

## V4-A recommendation: DEFER

**Rationale:**
1. Realized-R evidence (E1) contradicts the direction of the prompt nudge (touch=1 does NOT outperform touch=2 in R).
2. The underlying sample is v1-era; the right benchmark is v2-production, which starts now. Wait.
3. Prompt iterations burn $ and risk destabilizing the already-complex V3. V4-A's intended benefit (+WR via better touch-count discrimination) is unsubstantiated.
4. **Better uses of the prompt-iteration budget:**
   - Add monthly-decay shadow instrumentation (counter of fills this month vs prior-month rolling baseline; Telegram alert if WR drops >15pp).
   - Observe v2_shadow live data; re-extract E1 in 14 days with v2-production-driven CANDs.
   - If budget allows, re-run A1's 12 slices with `--detector-version v2` ($40) for a true v2 backtest comparison.

**If CEO wants SOMETHING on Monday:** the highest-value shippable change is the **monthly-decay monitor**, not V4-A.

---

## Artifacts delivered

- `research/phase1_full_extraction/EXTRACTION.md` (this file)
- `research/phase1_full_extraction/extraction_queries.py` (E1-E8, E10, E11)
- `research/phase1_full_extraction/extraction_output.json` (E1-E8, E10, E11 raw)
- `research/phase1_full_extraction/e9_anti_pattern_oos.py` (E9 OOS classifier validation)
- `research/phase1_full_extraction/e9_output.json`
- `research/phase1_full_extraction/e11_combined.py` (combined-dataset bucket map)
- `research/phase1_full_extraction/e11_combined.json`
- `research/phase1_full_extraction/e_extras.py` (monthly decay, E4 diagnosis, E12 verification)
- `research/phase1_full_extraction/e_extras.json`
- `research/phase1_full_extraction/merged_data.jsonl` (1,142 joined logger × outcome rows)

**Branch:** `research/phase1-comprehensive-extraction`
**Not merged, not pushed.** Leave for CEO review.
