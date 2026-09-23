# LIRA A/B Deep Forensic — Agent Beta Independent Analysis

**Branch:** `research/lira-forensic-beta`
**Date:** 2026-04-25
**Mode:** Independent of Agent Alpha — same brief, no conferral.
**Method:** Recompute everything from RAW `all_results.json` files; trust no narrative.
**Verdict on SYNTHESIS.md:** Direction correct (LIRA underperforms A2 on shared setups), several quantitative claims **wrong or inflated**, one critical pre-reg gate **falsely failed** due to a bug in the analyzer.

---

## TL;DR — Top 5 Beta Findings

1. **`analyze.py` MaxDD computation is wrong: chronological ordering not enforced.** Reported fleet MaxDD = 9.0R (`research/lira_ab_backtest/analysis_output.json:50`) is computed by walking trades in **slice-iteration order** (alphabetical: usdjpy_s1...usdjpy_s4 then xauusd_s1...xauusd_s8 — `analyze.py:111` uses `sorted(os.listdir())`, line 226 calls `max_drawdown_from_peak(r_series)` on that order). Re-computed chronologically (real-world fleet equity curve), **LIRA fleet MaxDD = 6.0R**, peak +10.5R at 2026-02-09, trough +4.5R at end. The pre-reg gate `lira_fleet_maxdd_le_8R: false` (`analysis_output.json:9`) is **mathematically wrong**; with chronological ordering it would have **PASSED**. Asymmetric — same bug makes A2's reported MaxDD = 3.0R artificially low; chronological A2 = 5.0R. The "9R vs 3R, 3× drawdown" framing in SYNTHESIS.md:29 is purely an artifact.

2. **The "+63% more USDJPY CANDs" finding is largely a coverage-gap artifact, not prompt permissiveness.** A2 hit per-slice $6 budget cap and stopped EARLIER in time than LIRA on every USDJPY slice (LIRA prompt is shorter so it got further). Per-slice candle coverage:
   - usdjpy_s1: A2 covered Jan 2-19 (359 candles); LIRA covered Jan 2-21 (436). LIRA evaluated 77 MORE candles.
   - usdjpy_s2: A2 covered Jan 27-Feb 9 (290); LIRA covered Jan 27-Feb 20 (608). **LIRA evaluated 318 MORE candles.**
   - usdjpy_s3: A2 covered Feb 23-Mar 4 (237); LIRA covered Feb 23-Mar 13 (469). LIRA: 232 MORE.
   - usdjpy_s4: A2 covered Mar 18-30 (264); LIRA covered Mar 18-Apr 3 (406). LIRA: 142 MORE.
   When restricted to the **A2-covered time window**, LIRA produces only **+1 extra USDJPY LONG CAND** (20 vs 19), not the +14 that a naïve count suggests. Of LIRA's 21 "extra" USDJPY LONGs vs A2, **13 (62%) are at candle times A2 never evaluated** (no `cost > 0` row at that timestamp). Only 6/21 are L2_REJECTED, 1/21 c2_m15_opposing, 1/21 BLOCKED_LIMIT.

3. **SL-tightness magnitude in SL_GEOMETRY_DIAGNOSTIC.md is overstated by ~50×.** Diagnostic claim "0.2-0.4% tighter SL on common XAUUSD LONGs" came from cherry-picking the 9 cases with `>0.5%` SL divergence (`SL_GEOMETRY_DIAGNOSTIC.md:25`). On all 28 common (slice, candle, direction) pairs, the **median signed SL-distance delta is -0.003pp** (essentially zero), mean **-0.087pp** (LIRA ~0.09pp tighter). That said, the **direction is still significant**: Wilcoxon signed-rank on 23 nonzero pairs gives p=0.0068 (LIRA tighter on 16/23). The SL effect is real but ~50× smaller than the diagnostic implies. 1/28 (3.6%) of common pairs flipped WIN→LOSS due to SL — not a systematic SL issue.

4. **Confidence_tier label has no discriminating power on LIRA fleet.** Q7: high_conviction n=21 WR=42.9% [24.5,63.5%] ExpR +0.071R; moderate n=12 WR=41.7% [19.3,68.0%] ExpR +0.042R; marginal_pass n=1 WR=100%. Two-proportion z-test high_conviction vs moderate: **p=0.947** (no signal). Marginal_pass too small to test (n=1). The tier is essentially a coin flip and **anti-discriminative on USDJPY LONG specifically** (high_conviction n=14 WR=35.7% < moderate n=5 WR=40.0%).

5. **F3 cross-check: LIRA's "extra" CANDs that F3 also took perform OK; the pure-LIRA-only CANDs net to zero, not a clear loss.** LIRA CANDs that ALSO appear in F3's run: 28 (52% of LIRA's 54). Filled 23, WR 47.8%, ExpR +0.196R, Total +4.5R. LIRA CANDs F3 did NOT take: 26. Filled 25, WR 40.0%, ExpR 0.000R, **Total 0R** (10 wins × 1.5R = +15R, 15 losses × −1R = −15R). **The "extra" LIRA CANDs aren't bleeding equity — they're break-even dilution.** That doesn't make LIRA better, but it deflates the "LIRA loses money on extra CANDs" narrative in SYNTHESIS.md:23-24.

---

## Disagreements with α (likely interpretations)

If α reproduced SYNTHESIS.md's headline claims, Beta disagrees on:

- **DISAGREE on 9R MaxDD failing pre-reg gate.** Beta finds chronological MaxDD = 6.0R; gate would PASS. The 9R figure is a code bug. Need α to verify independently.
- **DISAGREE on "0.2-0.4% tighter SL" magnitude.** Median across 28 common pairs is ~0pp; mean is 0.087pp. Direction is correct (Wilcoxon p=0.0068) but magnitude exaggerated.
- **DISAGREE on "+63% more USDJPY CANDs" being LIRA's prompt loosening.** It's primarily an A2 coverage truncation artifact. Within coverage-matched window, LIRA produces +1 USDJPY LONG (20 vs 19), not +14.
- **AGREE on direction:** LIRA does slightly underperform A2 on coverage-matched setups (-0.23R/trade ExpR; LIRA matched 34/+0.103R vs A2 30/+0.333R). The relative ordering survives all corrections.
- **PARTIAL AGREEMENT on STAY verdict:** Even with corrected MaxDD (6.0 < 8.0R PASS), the primary stay-trigger `lira_fleet_exp_le_a2_baseline` (+0.094 ≤ +0.333) STILL fires regardless of MaxDD. Verdict LIRA-STAY is durable to the bug fix. But the **stated reasoning ("3× drawdown") in SYNTHESIS.md:29 should be retracted**.

---

## Q1 — Per-slice breakdown (recomputed from raw)

Confirmed all per-slice numbers in SYNTHESIS.md table at `:112-126` and analysis_output.json `:117-333`. Match exactly:

| Slice | LIRA filled / R / WR | A2 filled / R / WR | Beta verifies |
|---|---:|---:|---|
| xauusd_s1 | 0 / +0R / — | 0 / +0R / — | match |
| xauusd_s2 | 1 / -1R / 0.0% | 1 / -1R / 0.0% | match |
| xauusd_s3 | 8 / +4.5R / 62.5% | 5 / +2.5R / 60.0% | match |
| xauusd_s4 | 0 / +0R / — | 0 / +0R / — | match |
| xauusd_s5 | 2 / -2R / 0.0% | 2 / -2R / 0.0% | match |
| xauusd_s6 | 0 / +0R / — | 0 / +0R / — | match |
| xauusd_s7 | 2 / +3R / 100% | 2 / +3R / 100% | match |
| xauusd_s8 | 1 / -1R / 0.0% | 1 / -1R / 0.0% | match |
| usdjpy_s1 | 8 / +2R / 50.0% | 6 / +1.5R / 50.0% | match |
| usdjpy_s2 | 9 / +3.5R / 55.6% | 6 / +6.5R / 83.3% | match |
| usdjpy_s3 | 8 / -0.5R / 37.5% | 2 / +0.5R / 50.0% | match |
| usdjpy_s4 | 9 / -4R / 22.2% | 5 / +0R / 40.0% | match |
| **Fleet** | **48 / +4.5R / 43.8%** | **30 / +10.0R / 53.3%** | **match** |

No discrepancies in per-slice numbers. **MaxDD discrepancy isolated to fleet aggregation only** (slice-level MaxDDs are correct because each slice is internally chronological).

`research/lira_ab_deep_forensic/beta_analysis.json` `q1_per_slice` has full reproduction.

---

## Q2 — Decision divergence audit

| Bucket | Beta count | SYNTHESIS / SL_GEO claim |
|---|---:|---:|
| Common (slice, candle, dir) | **28** | 28 (`SL_GEOMETRY_DIAGNOSTIC.md:6` "28") — match |
| LIRA-only | **26** | 26 — match |
| A2-only | **9** | 9 — match |
| Same time, dir-disagree | **0** | not mentioned |

No disagreements in bucket counts. Importantly, **0 cases of direction disagreement** on the same candle — when both produce CAND, they always agree on direction.

---

## Q3 — USDJPY LONG over-permissiveness (independent feature analysis)

### Raw counts (all 54 LIRA CANDs vs 37 A2 CANDs across all 12 slices)
- LIRA USDJPY LONGs: 38
- A2 USDJPY LONGs: 24

### Coverage-matched (LIRA restricted to A2's evaluated time window per slice)
- LIRA USDJPY LONGs: **20**
- A2 USDJPY LONGs: **19**
- **Delta: +1 (5%)**, NOT +14 (58%)

The "63% more USDJPY CANDs" finding in SYNTHESIS.md:79 is **almost entirely** explained by:
- **Coverage gap:** A2 hit budget earlier → less time evaluated → fewer evaluations → fewer CANDs.
- 13/21 LIRA-only USDJPY LONGs are at candle times A2 never evaluated (cost=0).

### Within coverage-matched, what does the LIRA prompt actually do that A2 doesn't?

**8/21 LIRA-only USDJPY LONGs** are inside A2's time window. Of these:
- 6 were `REJECTED_L2` by A2 (L2 prescreen rejection in V3 prompt — these are real prompt-divergence cases).
- 1 was `c2_m15_opposing` (V3's C2 gate rejected M15 stance).
- 1 was `BLOCKED_LIMIT` (other infrastructure block).

So the **true V3-rejected/LIRA-accepted set is ≤8 USDJPY LONGs**, not 14. Of those 8 filled, 4 WIN, 4 LOSS → +1.0R (essentially flat).

### Tier discrimination on coverage-matched LIRA USDJPY LONGs

| Tier | n | WR | ExpR |
|---|---:|---:|---:|
| high_conviction | 14 | 35.7% | -0.107R |
| moderate | 5 | 40.0% | 0.000R |
| marginal_pass | 1 | 100% | +1.500R |

**Inverted ordering** — high_conviction performs WORST. Beta's hypothesis: the "high_conviction" label inside the LIRA prompt is producing **false-confidence high-volume LONG calls in a chop regime**, exactly the regime where structural bias detection over-fires.

### Per-gate signal
**ALL 20 coverage-matched LIRA USDJPY LONGs passed `["C1","C2","C3"]`** — no per-gate variance to analyze. Gates are not differentiating.

### setup_grade
| Grade | Count |
|---|---:|
| A+ | 14 |
| A | 5 |
| B | 1 |

Heavily weighted to A+. WR by grade not informative (cells too small).

---

## Q4 — SL-placement delta (math redone)

### All 28 common (slice, candle, dir) pairs

| Metric | Beta | SYNTHESIS/SL_GEO |
|---|---:|---:|
| n | 28 | 28 |
| LIRA tighter | 15 (53.6%) | "7/9" — but only on 0.5% subset |
| LIRA looser | 13 (46.4%) | not stated |
| Median \|delta\| | **0.022%** | not given |
| Mean \|delta\| | **0.109%** | "0.2-0.4%" — too high |
| Median signed (LIRA% − A2%) | **−0.003pp** | not given |
| Mean signed | **−0.087pp** | not given |
| Wilcoxon signed-rank on 23 nonzero | **p=0.0068** | not given |
| WIN→LOSS (A2→LIRA) | 1 (xauusd_s3 01-30 08:00) | 1 |
| LOSS→WIN | 0 | 0 |
| WIN→UNFILLED | 1 (usdjpy_s3 03-02 07:00) | 1 |
| UNFILLED→WIN | 1 (usdjpy_s3 02-26 00:15) | 1 |

### Verdict on SL claim
- **Direction correct, magnitude wrong by ~50×.** The "0.2-0.4% tighter on common XAUUSD LONGs" claim was derived from cherry-picking the **9 pairs with >0.5% divergence** (the divergence threshold itself). On the full 28 common pairs the median delta is essentially zero, but the SIGN distribution is statistically biased (16/23 nonzero pairs LIRA-tighter, p=0.0068). The economic claim "this caused LIRA to lose more" rests on **1/28 W→L conversion** which is not statistically significant alone (it's offset by an UNFILLED→WIN at 02-26).

---

## Q5 — Stratum dominance (filled, not coverage-matched)

| Symbol | Direction | KZ | LIRA n / WR / ExpR | A2 n / WR / ExpR | Δ ExpR |
|---|---|---|---:|---:|---:|
| USDJPY | LONG | london | 12 / 41.7% / +0.042 | 7 / 71.4% / +0.786 | **−0.744** |
| USDJPY | LONG | ny | 6 / 33.3% / −0.167 | 6 / 50.0% / +0.250 | −0.417 |
| USDJPY | LONG | tokyo | 15 / 46.7% / +0.167 | 6 / 50.0% / +0.250 | −0.083 |
| USDJPY | SHORT | tokyo | 1 / 0.0% / −1.000 | 0 / — | −1.000 |
| XAUUSD | LONG | london | 7 / 42.9% / +0.071 | 5 / 40.0% / +0.000 | **+0.071** |
| XAUUSD | LONG | ny | 5 / 40.0% / +0.000 | 4 / 25.0% / −0.375 | **+0.375** |
| XAUUSD | SHORT | london | 2 / 100% / +1.500 | 2 / 100% / +1.500 | 0 |

### Where LIRA is strongest
- **XAUUSD LONG NY** (+0.375R/trade vs A2): 5 trades, 2 wins (40%) vs A2's 4 trades, 1 win (25%). Small n; not dispositive.
- **XAUUSD LONG London** (+0.071R/trade): tiny edge.
- **XAUUSD SHORT** (+0R/trade): tied — no edge.

### Where LIRA is weakest
- **USDJPY LONG London** (−0.744R/trade) — biggest source of fleet underperformance.
- **USDJPY LONG NY** (−0.417R/trade).

**Surprise:** USDJPY London is where LIRA underperforms most. SYNTHESIS framed this as a USDJPY-wide problem; Beta finds it's concentrated in the morning London KZ for USDJPY LONGs specifically. Tokyo (15 trades) is roughly tied with A2 (6 trades) on a per-trade basis (+0.167 vs +0.250). The London KZ delta of -0.744R is dominated by 5 LIRA London LONGs in usdjpy_s4 (Mar 18 - Apr 3) where LIRA had 4 LOSSES and 1 WIN (-2.5R), and A2 didn't have any London CANDs in that period.

---

## Q6 — Per-month aggregation (chronological regime check)

| Month | LIRA n / WR / ExpR | A2 n / WR / ExpR | Δ ExpR |
|---|---:|---:|---:|
| 2026-01 | 11 / 36.4% / −0.091 | 9 / 44.4% / +0.111 | −0.202 |
| 2026-02 | 16 / 68.8% / +0.719 | 9 / 77.8% / +0.944 | −0.226 |
| 2026-03 | 18 / 33.3% / −0.167 | 11 / 45.5% / +0.136 | −0.303 |
| 2026-04 | 3 / 0% / −1.000 | 1 / 0% / −1.000 | 0 |

**LIRA loses ground every month.** No regime where LIRA outperforms. Worst gap is March (−0.30R per trade) — note this is the period most affected by the truncation gap on usdjpy_s3/s4. February saw the strongest absolute performance for both variants. April n is tiny (only 1 trading week in last slice).

### v2_shadow detector regime test
The brief asked: "Did LIRA do better in bearish-regime slices (where v2 detector emits SHORTs)?" — **No bearish-regime slices in this run.** All 12 slices use v2 detector. Only 3 LIRA SHORTs total (xauusd_s7 ×3). LIRA's XAUUSD SHORTs are 100% WIN (n=2 filled), tied with A2. **No signal that LIRA-vs-V3 differs by regime within this dataset.**

---

## Q7 — Confidence_tier discrimination

### LIRA fleet (all 48 filled trades)

| Tier | n | wins | WR (Wilson 95% CI) | ExpR |
|---|---:|---:|---:|---:|
| high_conviction | 26 | 12 | 46.2% [28.8, 64.5] | +0.154 |
| moderate | 19 | 8 | 42.1% [23.1, 63.7] | +0.053 |
| marginal_pass | 3 | 1 | 33.3% [6.1, 79.2] | −0.167 |

high_conviction vs moderate (two-prop z): **p ≈ 0.78** — NO discrimination.
high_conviction vs marginal_pass: p = 0.66 — NO discrimination (tiny n).

### A2 fleet
A2's V3 prompt does NOT emit `confidence_tier`. All 30 A2 trades have tier=`unknown`. Cannot compare A2 tier discrimination.

### Verdict
**Confidence_tier in LIRA prompt is statistically indistinguishable from random labeling.** This is consistent with the historical finding (CLAUDE.md:Validated Numbers) that the older confidence scorer was a rubber stamp (98% gave 80). LIRA's tier appears to inherit this behavior — wide spread of labels but no real WR variance.

---

## Additional questions

### Parse-error distribution
- LIRA: **0/1173 parse errors (0.00%) across all 12 slices.**
- Distribution per slice: All 12 slices = 0 errors. Even distribution.
- This is contingent on the schema_adapter fix (`research/v4_prompt_engineering/dp4_lira/schema_adapter.py`) landed pre-launch (commit 4892008 per `SYNTHESIS.md:140`). With fix: 0%; without fix: estimated 5-15% based on double-block self-correction trigger pattern.

### UNFILLED rates
- LIRA: 6/54 = **11.1%**
- A2: 7/37 = **18.9%**
- Mechanism: LIRA's marginally tighter SL → tighter TP1 (since fixed RR=1.5) → easier to fill TP1 in noise. Also UNFILLED concentrates on usdjpy_s3 (LIRA 5/13, A2 5/7) where Feb 26-Mar 4 saw price gaps past entry levels — same regime issue affecting both variants.

### Token / cost per CANDIDATE
| Variant | n CANDs | mean input | mean output | median output |
|---|---:|---:|---:|---:|
| LIRA | 54 | 6,836 | 619 | 579 |
| A2 (V3) | 37 | 9,805 | 945 | 927 |

LIRA produces **30% fewer input tokens** and **35% fewer output tokens** than V3 (consistent with 45.7% prompt size reduction). Per-CAND cost: LIRA $0.027 vs A2 $0.046 — LIRA is **41% cheaper per CAND**.

But: **API spend per fill** = $32.70 / 48 fills = $0.68 (LIRA) vs $37.59 / 30 fills = $1.25 (A2). **LIRA actually generates fills CHEAPER per fill** ($/fill = $0.68 vs $1.25, 46% savings). However, expected R/$ is what matters and LIRA's flat ExpR makes this irrelevant.

### F3 cross-check (interesting)
- F3 CANDs: 39 (similar to A2's 37)
- LIRA CANDs that F3 ALSO took: 28 (52% overlap)
- LIRA CANDs F3 didn't take: 26
  - Filled 25, WR 40%, **Total R = 0R** (10 wins × 1.5R = +15R, 15 losses × −1R = −15R)
  - **The "extra" LIRA CANDs are net flat, not net negative.** 
- LIRA CANDs that F3 DID take: 28
  - Filled 23, WR 47.8%, ExpR +0.196R, Total +4.5R

This nuances the SYNTHESIS narrative: LIRA's extra setups don't BLEED equity — they DILUTE it. This still kills the prompt economically (lower ExpR), but the framing in SYNTHESIS.md:23 ("extra CANDs lose more often than they win") is misleading. They lose **as often as they win**, contributing 0R to fleet equity. The fleet ExpR drops from A2's +0.333 to LIRA's +0.094 because the denominator (n=48 vs n=30) grew faster than the numerator (R=4.5 vs R=10).

---

## Verdict on agent α's likely report

**If α reproduced SYNTHESIS.md verbatim**, α inherited 3 errors from the analyzer:
1. **MaxDD ordering bug** in `analyze.py:226` — should have been caught by recomputation.
2. **SL magnitude inflation** — diagnostic cherry-picked subset.
3. **Coverage-gap framing** — A2's truncated coverage inflated LIRA's "extra CAND" count.

**If α independently caught all 3**, then α and Beta should agree on:
- Verdict LIRA-STAY (still correct because primary trigger is exp_le_a2_baseline, not MaxDD).
- Direction of SL effect (LIRA tighter, but tiny magnitude).
- LIRA's USDJPY weakness is real but smaller than headline suggests.

**Disagree even more strongly if α didn't catch them.**

---

## Recommendation re: SYNTHESIS

1. **Fix `analyze.py:226`** to chronologically sort fleet `r_series` before `max_drawdown_from_peak`. Re-run; report shows true MaxDD = 6.0R.
2. **Update SYNTHESIS.md:29 + :48** to reflect 6.0R / 5.0R MaxDDs (not 9.0R / 3.0R).
3. **Update SYNTHESIS.md:79** ("63% more USDJPY CANDs") to note this is partly coverage-gap. Coverage-matched delta is +5%, not +63%.
4. **Update SL_GEOMETRY_DIAGNOSTIC.md** to report median signed delta on full 28 common pairs (~0pp), not just the >0.5% subset's mean (~0.3pp).
5. **Verdict LIRA-STAY survives** all corrections — coverage-matched LIRA still ExpR +0.103 ≤ A2 +0.333. So the *outcome* of the experiment doesn't change, but the *mechanism story* in SYNTHESIS is misleading.

The cleaner story:

> LIRA's prompt produces marginally more setups under coverage-matched conditions (+5%, not +63%). Its SL is marginally tighter (median ~0pp; mean ~0.09pp) — direction statistically significant via Wilcoxon (p=0.007) but magnitude tiny. The fleet expectancy gap (+0.094R vs A2 +0.333R) comes mostly from **the same setups, with slightly different parameters, performing slightly worse** — particularly on USDJPY LONG in the London KZ. The "extra" CANDs unique to LIRA are net flat (0R), not net negative — they dilute rather than bleed. Confidence_tier discrimination is statistically nil. **LIRA is no better than V3 for trading, costs 13% less in API, but 13% savings doesn't justify a 0.24R/trade ExpR penalty.** STAY with V3.

---

## Files
- `BETA_REPORT.md` — this file
- `beta_analysis.py` — Beta's analysis script (independent of analyze.py)
- `beta_analysis.json` — machine-readable findings
- `beta_analysis.log` — full stdout
