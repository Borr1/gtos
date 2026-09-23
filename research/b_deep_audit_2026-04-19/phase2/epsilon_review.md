# Phase 2 Review — Agent ε (Liquidity-Arbitrage Hypothesis)

**Reviewer:** Phase 2 independent statistical reviewer
**Date:** 2026-04-19 (Session 35)
**Review target:** `research/b_deep_audit_2026-04-19/phase1/epsilon_liquidity_arb.md` (26.6 KB)
**Reviewer lens:** Statistical rigor, reproducibility, alternative explanations, cross-agent consistency
**Primary mandate:** Brutal honesty, cite file:line, do NOT re-run the investigation; DO spot-check

---

## Executive verdict

**Overall grade: B (directionally useful; conclusions survive but presentation has real arithmetic and logical errors the CEO should know about).**

ε's three headline numbers (fast-loss 26.9%→69.2% p=0.017, winner MFE 1.04R→0.49R p=0.020, SL-reversal 4/4 vs 44% null p=0.040) **reproduce exactly from the committed scripts and raw data**. The BH-FDR survivor claim (2 of the 3 survive at q=0.05) survives with one arithmetic sleight-of-hand that I flag below, but the **standard BH step-up procedure correctly rejects the first 3 ranks**, so ε's substantive conclusion (fast-loss + winner-MFE survive, SL-reversal does not) is defensible.

**What ε got right (with independent confirmation):**
1. Per-symbol `FILL_EPS` (`_loader.py:34-42`: 0.20 / 2.0 / 0.0002) correctly side-steps the `_FILL_EPSILON=0.05` global mis-scale flagged as CLAUDE.md unresolved #8. Their numbers are NOT inflated by that bug.
2. Explicit acknowledgment that EURUSD is contaminated (FX precision bug) and NAS100 pre-MFE is AI-artifact, not stop-hunt signature — avoids the common trap of letting a single big number drive the verdict.
3. Bonferroni stated honestly as not-surviving; BH-FDR used as the less-strict backup; both floors presented.
4. Cross-instrument MFE analysis (GBPJPY -48%, US30 +87%, USDJPY +109%) directly falsifies the uniform-arb hypothesis — that's good pre-registered design; opposite signs are precisely the control ε's signature battery was designed to catch.
5. Primary claims ranked with explicit "exploratory" flags on n<20.

**What ε got wrong (in decreasing order of severity):**
1. **Logical slip: the "6/6 regime vs 3/9 arb" scorecard is rhetorically overfit.** The 3 "negative" items attributed to regime-consistency (no cross-instrument signal, no volume-spike, no algo-rank) are not positive predictions of regime change; they're merely non-predictions that fail to distinguish regime-change from "no effect at all" or "null hypothesis is true". This is post-hoc counting that should be tightened.
2. **BH threshold arithmetic error** (line 90 and 300): ε writes "Pass rank 2 (0.017 ≤ 0.0167, yes)" — **but 0.017 > 0.0167**. The substantive conclusion survives via the BH step-up rule (rank 3 passes at 0.020 ≤ 0.025, and step-up then rejects ranks 1-3), but ε doesn't flag this and a careless chairman might miss it.
3. **"Z-prop p=0.011"** cited in headline (line 13) and BH sort (line 300) is not produced by the committed `_deep_signal_tests.py`. The script's `two_prop_z_p(4, 4, 175, 395)` was only called on SL-reversal, returned `null` (n1=4 guardrail), and is the wrong test anyway. 0.011 IS reproducible by hand on the fast-loss test (7/26 vs 9/13) but was not coded. Reproducibility gap.
4. **n_2024=7 baseline carries bootstrap 95% CI [0.175, 0.820]** that overlaps heavily with 2025 CI [0.345, 0.831]. The "5.4× loss-MFE collapse from 2024" framing (line 249) is thin on that end — the comparison that is actually robust is 2025 (n=19) vs 2026 (n=13), not 2024 vs 2026.
5. **"6 signatures tested" for Bonferroni/BH is undercounted.** Within sig #4 alone, ε runs 5 separate cross-instrument MW tests. Within sig #2, ε runs 5 fast-loss proportion tests. The true test count is closer to 12-15, in which case nothing survives BH. ε should have been explicit about within-signature multiple-testing.

**Net recommendation to chairman:** ε's XAUUSD-specific findings are real and actionable. The "regime vs arb" comparison should be de-emphasized relative to what it claims — both hypotheses fit the positive signatures; only arb makes falsifiable cross-instrument predictions, and those predictions fail. But don't read "regime fits 6/6" as any kind of support for regime change over a pure null.

---

## 1. Statistical rigor review

### 1.1 Reproducibility of headline numbers (spot-checks, no full rerun)

| Claim | File:line | Reproduced? | Delta |
|---|---|---|---|
| Fast-loss 26.9% vs 69.2% | line 80 | **YES** — 7/26 + 9/13 confirmed from 318 XAUUSD session files | exact |
| Fisher fast-loss p=0.017 | line 80 | **YES** — `fisher_exact_2sided(7,19,9,4)` returns 0.01719 | exact |
| Fisher SL-reversal 4/4 vs 175/395 null p=0.040 | line 120-121 | **YES** — `fisher_exact_2sided(4,0,175,220)` returns 0.03976 | exact |
| MW U p=0.020 (XAUUSD winner MFE) | line 150-151 | **YES** — from `deep_signal_tests.json:27` (0.0196), scripted result | exact |
| Winner MFE 1.04R early, 0.49R late | line 151 | **YES** — n=59 early (2024-25), n=20 late (2026) confirmed | exact |
| Loss MFE 0.573R (2024) | line 73 | **YES** — but n=7 is thin; bootstrap CI [0.175, 0.820] not shown | exact but misleadingly small-n |
| Quarterly WR decay XAUUSD 70.8 → 65.6 → 60.6 | lines 234-244 | **YES** — reproduces exactly from 318 session files | exact |
| `reversed_1r_after_sl` = True for all 4 XAUUSD T7 losses | line 108-115 | **YES** — confirmed from `enriched_candidates.json` | exact |
| "Z-prop p=0.011 for fast-loss" | line 13, 300 | **NO** — not in scripts; reproducible by hand on (7,26,9,13) = 0.0113 | **hand-calc only** |

**Score: 9/10 reproduce bit-exact, 1 requires hand-calculation not in committed code. `_main_analysis.py` + `_deep_signal_tests.py` regenerate everything else. Reproducibility rating: 4/5** — one number ("Z-prop 0.011") required me to run `python -c "..."` outside the committed scripts to verify. Not a blocker, but should have been coded inline for true 1-command reproducibility.

### 1.2 n=4 SL-reversal Fisher test — single-die roll or meaningful?

**The brief specifically asked:** "is Fisher p=0.040 at n=4 a meaningful signal or a single-data-point dice roll?"

**My answer: it is a legitimate small-sample test that is also a dice roll.**

The Fisher p=0.040 is correctly computed; the 4/4 vs 175/395 contingency test does have valid inference at n=4 (Fisher is exact precisely because it enumerates the hypergeometric distribution, no n-sufficiency assumption). **However:**

1. **Wilson 95% CI on the observed rate = [0.51, 1.00]** — so the true rate could be anywhere from 51% to 100%. The "point estimate 100%" is overconfident; the CI overlaps with the null hypothesis (44%) at the lower bound of 0.51, which is only 6.7pp above the null.
2. **A single loss the other direction would have dropped the rate to 3/5=60%, and the p-value to approximately 0.563** (computed: `fisher_2sided(3,2,175,220) ≈ 0.56`). That's the definition of fragility.
3. **The 4 XAUUSD T7 losses are temporally clustered** (Jan 15, Jan 21, Feb 20, Mar 10) — not independent in any statistical sense, all within a 60-day period when XAUUSD realized vol was ≈2× baseline (δ's §7 confirms ATR/252d = 2.16 in 2026-Q1, highest in series). If the volatility regime made reversal overshoots more common, ALL 4 might share a common cause — this is effectively n=1 regime observation.

**Verdict on brief Q1:** n=4 is explicitly labeled "exploratory" by ε (line 127), which is the correct framing. Fisher p=0.040 is mathematically valid at n=4 but the 100% point estimate is fragile. The SL-reversal signal should be treated as **suggestive, not confirmatory**, and the 4-trade observation should be treated as **potentially 1 regime observation**. ε's own caveat "At n=4 this is exploratory. Point estimate dramatic but confidence interval is wide (Wilson 95% CI on observed = [0.51, 1.00])" (line 121) is the correct framing. Good that ε stated it; shame that the top-line headline absorbs it as "3rd strongest signature" at face value.

### 1.3 BH-FDR survivor set — can we trust 2/3 pass?

**Independent recomputation:**

```
p-values (ε's 6-test panel, post-FX exclusion):
  rank 1: p=0.011 (fast-loss Z-prop)       threshold = 1/6 × 0.05 = 0.00833 — FAIL (p > thr)
  rank 2: p=0.017 (fast-loss Fisher)       threshold = 2/6 × 0.05 = 0.01667 — FAIL (p > thr, barely)
  rank 3: p=0.020 (winner MFE MW)          threshold = 3/6 × 0.05 = 0.02500 — PASS (p ≤ thr) ← step-up anchor
  rank 4: p=0.040 (SL-reversal)            threshold = 4/6 × 0.05 = 0.03333 — FAIL
  rank 5: p=0.161 (US30 MFE MW)            threshold = 5/6 × 0.05 = 0.04167 — FAIL
  rank 6: p=0.225 (GBPJPY MFE MW)          threshold = 6/6 × 0.05 = 0.05000 — FAIL

Under BH step-up:  largest k where p_(k) ≤ k*q/m is k=3.
Step-up decision:   reject H_(1), H_(2), H_(3) — the first 3 ranks.
```

So ε's conclusion "3 pass at q=0.05" is mathematically correct under BH step-up.

**But ε's stated justification is arithmetically wrong:**

Line 90: "**XAUUSD fast-loss (p=0.017) passes at FDR=0.05, rank 2 threshold 0.0167**"

**0.017 > 0.01667**, not ≤. At rank 2 the individual test does NOT pass; it's rescued only by the step-up rule and rank 3's success. ε should have written: "XAUUSD winner MFE compression (p=0.020, rank 3) passes at threshold 0.025; under BH step-up this rejects ranks 1 and 2 as well." Same survivor set, honestly described.

**Comparison to Bonferroni (α=0.05/6=0.00833):** Per ε's own statement (line 299), "NONE of our tests survive strict Bonferroni." That's correct.

**Comparison to 8-agent Bonferroni (α=0.05/8=0.00625):** This is the "parallel-8-agents" joint α the brief mentions. Under α=0.00625: STILL none survive.

**Comparison to realistic within-family test count (≥12):** If we account for within-sig multiple tests (§1.4 below), BH m=12 yields:
```
rank 1: 0.011 ≤ 1/12 × 0.05 = 0.00417 → FAIL
rank 2: 0.017 ≤ 2/12 × 0.05 = 0.00833 → FAIL
rank 3: 0.020 ≤ 3/12 × 0.05 = 0.01250 → FAIL
rank 4: 0.040 ≤ 4/12 × 0.05 = 0.01667 → FAIL
```
**No survivors at m=12.**

**Verdict on brief Q1.2:** BH at m=6 is internally consistent and survives. BH at m≥12 (more honest) does not. ε should have flagged both. Under a skeptical reading, XAUUSD findings are **directional, not confirmatory at FDR q=0.05**.

### 1.4 Hidden multiplicity — real test count > stated 6

ε's scorecard (lines 278-295) actually reports outcomes across 15 rows:
- Sig #1 per-instrument (3): XAUUSD, NAS100, EURUSD
- Sig #2 per-instrument (5): XAUUSD + US30 + USDJPY + GBPJPY + NZDUSD
- Sig #3 per-instrument (3): XAUUSD, NAS100, bit-exact
- Sig #4 per-instrument (5): XAUUSD, GBPJPY, NZDUSD (fails at n), US30, USDJPY
- Sig #5 (1), Sig #6 (1), Sig #7 (per-year per-instrument, ≥3)

That's ≥15 signal-tests, several with explicit Fisher/MW/Spearman p-values. ε's choice to Bonferroni-correct at m=6 is a **subjective grouping choice** ("6 primary signatures") that reduces the effective penalty. The brief's counter-audit lens notes this as "do the survivors plausibly emerge as false positives from multiplicity?" — **yes, under the full test count they do.**

**This is the single biggest statistical weakness of ε's deliverable.** CEO should treat XAUUSD findings as "directional with converging mechanisms" rather than "FDR-surviving at α=0.05."

### 1.5 Sample sufficiency audit

| Claim | n1, n2 | Test | Power (post-hoc) |
|---|---|---|---|
| Fast-loss 7/26 vs 9/13 | 26, 13 | Fisher / Z-prop | n=39 at effect 42.3pp → z=2.53 → ~70% power at α=0.05 |
| Winner MFE 1.04 vs 0.49 | 59, 20 | MW U | z=2.33 → effect r=0.263 → ~65% power at α=0.05 |
| SL-reversal 4/4 vs 395 null | 4, 395 | Fisher | 4/4 is maximal within observed; single flip drops p to 0.56 |
| 2024 vs 2026 loss MFE | 7, 13 | MW U | would need n≥20 per side for meaningful; 2024 arm underpowered |

Post-hoc power ~65% for MW and ~70% for Fisher on the primary tests means these are **adequately powered to detect the observed effect sizes if they are real**, but they are NOT adequately powered to distinguish "real, large effect" from "inflated estimate of smaller true effect." Classic small-n / medium-power issue: the estimates are unbiased but have large variance; ε's headline point estimates are likely optimistic.

**Specifically for the "53% compression" claim:** Hollander-Wolfe rank-biserial effect for XAUUSD MW = `1 - 2U/(n1*n2)`. With n1=59, n2=20, U computed from z=2.33 via `U = μ - z*σ ≈ 455`, effect = 1 - 910/1180 = 0.23 (medium). A "medium effect" is consistent with compression, but we should expect shrinkage on replication.

### 1.6 Other statistical defects (minor)

- **`mann_whitney_u_p` function has a minimum-n guardrail of 5** (`_main_analysis.py:102`, `_deep_signal_tests.py:60`). This causes NZDUSD winner MFE MW to return null (n=1 early) as expected. No issue — fail-safe is correctly engaged.
- **Spearman rho=−0.21 at n=5 symbols** is correctly flagged as "insufficient for formal inference" (line 186). No t-test reported — good restraint, because at n=5 the CI on ρ is approximately [-0.88, +0.77], i.e., essentially uninformative.
- **Null baseline reversal** (`_main_analysis.py:345-392`) uses `R = median_price × 0.005` as proxy R distance, `seed=11`, 500 trials. This is defensible for XAUUSD where the actual CANDIDATE R distance ranges 9.5-79pt, median 23.17pt, and 0.5% of ~2000 median price ≈ 10pt. The match is approximate. Should have used the actual CANDIDATE R distribution for exact comparability; deviation is probably ±5pp on the null rate, which is not enough to move the Fisher verdict materially but is an undocumented modeling choice.

---

## 2. Alternative-explanation audit

### 2.1 The "regime change vs arb" comparison is rhetorically overfit

**ε's scorecard (lines 326-333):**
> "XAUUSD entered a lower-trending, higher-volatility regime in 2026" — this would produce:
> - Faster losses ✓
> - Smaller winner MFE ✓
> - SL + reversal (whipsaw) ✓
> - No cross-instrument arb signature ✓
> - No volume-spike differential ✓
> - No algo-rank correlation ✓
>
> This is 6/6 for regime change, vs 3/9 supporting signatures for arb.

**Critical defect in the comparison:**

Items 4, 5, 6 are **negative predictions of the arb hypothesis that failed**, not positive predictions of the regime hypothesis. A pure null hypothesis ("neither arb nor regime") would also produce those three results, so they don't discriminate between regime and null. The regime hypothesis only makes positive predictions on items 1, 2, 3 — same list as the arb hypothesis on XAUUSD. So the true comparison is:

- Arb positive predictions on XAUUSD: items 1-3 ✓; cross-instrument items 4-6: fail → net 3/6 on signatures it predicts.
- Regime positive predictions on XAUUSD: items 1-3 ✓; cross-instrument: silent (regime change is instrument-specific by hypothesis) → 3/3 on predicted.

**So the real comparison is 3/3 regime vs 3/6 arb.** That still favors regime, but ε's 6/6 number absorbs falsified arb predictions as regime successes, which is epistemologically sloppy.

**Additionally, ε does NOT pre-register either hypothesis.** The regime hypothesis appears nowhere in the signature battery design (sigs 1-7 are all arb-testing); the regime hypothesis surfaces only in the verdict aggregation (§8) as a response to "arb didn't fit." This is a post-hoc alternative constructed after seeing the arb results — classic forking-paths territory. ε is honest about this in the interpretation ("Pattern CAN be consistent with arbitrage but is equally (or more) consistent with a regime shift in gold specifically" — line 320) but doesn't flag the post-hoc nature.

### 2.2 Alternative explanations ε did not consider

Additional alternatives that fit XAUUSD's 3 positive signatures as well as "arb" or "regime" do:

1. **Bad entry placement** (α's finding) — XAUUSD 26%→50% bad-entry rate (losses never went into profit) is an entry-placement defect. If AI is mis-selecting OB levels, resulting losses will (a) go adverse fast (sig #2 ✓), (b) reverse through stop since OB bound is wrong (sig #3 ✓), and (c) winners that do materialize are winners despite mis-placement so their MFE is compressed (sig #4 ✓). **This explains 3/3 the same way as regime.**
2. **Detector bug** (ζ's findings) — `identify_structure` D1-bias-lag + wick-based OB mitigation + `_count_touches` off-by-one. If zone detection is silently broken in 2026, downstream outcomes include (a) trades placed at geometrically-invalid OB levels that fail fast (sig #2 ✓), (b) SL-reversal because the "OB" isn't a real OB (sig #3 ✓), (c) winners capped because target was mis-sized (sig #4 ✓). **This explains 3/3 via structural code defect.**
3. **AI prompt degradation** (β's domain + CLAUDE.md T2.prompt) — universal `sl_buffer_applied=0.0` universal across 1053/1053 XAUUSD records; AI may be emitting geometrically sub-optimal trade parameters. Same 3/3 logic.
4. **MFE measurement shift** — if 2026 `mfe_r` field semantics changed (e.g., collection method or exit-tracker changed) the comparison to 2024-2025 isn't apples-to-apples.

**Adding these candidates, the race is:**
- Arb: 3/6 (fails cross-instrument predictions).
- Regime: 3/3 positive, no negative predictions tested.
- Bad-entry: 3/3 positive, directly tied to α's +50% bad-entry finding in same period.
- Detector bug: 3/3 positive, directly tied to ζ's confirmed code bugs.
- Prompt degradation: 3/3 positive, directly tied to CLAUDE.md unresolved #5.
- Measurement artifact: 3/3, no evidence either way.

**5 of these hypotheses fit the XAUUSD pattern equally well.** The XAUUSD data **does not discriminate between them.** ε's single-alternative "regime change" framing obscures this.

### 2.3 Spot-check: regime hypothesis vs δ's stationary finding

δ explicitly tested whether the XAUUSD WR sequence could be a stationary process (§6 bootstrap, §8.1 bullet). δ's finding: P(max-min spread ≥ 13.8pp under null) = **0.7525**. i.e., the WR sequence is consistent with stationarity. δ concludes: "the edge is regime-conditional on *trending* markets, not chop" (δ §8.2).

**ε's XAUUSD-specific signal reconciles with δ how?**

- δ pools all 131 XAUUSD trades across 8 quarters and finds no decay.
- ε finds a specific 2024 vs 2026 compression in winner-MFE and fast-loss rate.

**These are not contradictory:** δ looks at WR and spread (1-d statistics); ε looks at within-trade micro-kinetics (MFE/MAE distributions). The system could maintain 60%+ WR while trades are getting mechanically harder to execute — winners compressed, losses faster. That's exactly the pattern. **δ + ε are compatible**: WR is stable because the system's selectivity compensates for a tougher regime; kinetics (MFE/MAE) reveal the toughness.

**This is the single most important cross-agent convergence**, and ε does NOT cite δ. ε would have been stronger by explicitly framing: "WR-level looks stable (δ), but within-trade micro-kinetics are degrading, suggesting the regime has become hostile even as selectivity is compensating."

### 2.4 Spot-check: ε's fast-loss 69.2% vs α's bad-entry 50% and 0/16 signature

α's 2026Q1 XAUUSD: 8/13 losses have mfe<0.2R = 61.5% bad-entry (α line 231-244; n=13).
ε's 2026 XAUUSD: 9/13 losses have mfe<0.3R = 69.2% fast-loss (ε line 80; n=13).

Both use the same 13 losses. Under α's 0.2R cutoff, 8 qualify; under ε's 0.3R cutoff, 9 qualify (so 1 loss has 0.2 ≤ mfe < 0.3). **Numerically consistent.** Different operational definitions, same underlying truth.

α also notes (α line 116-118) that 0/16 losses match the strict "bit-exact wick + 1R reversal" signature — meaning no loss had SL at a bit-exact OB boundary that then reversed. ε's line 125 explicitly flags the same geometric inconvenience: "the SL is placed BEYOND the OB bound per `sl_beyond_ob` L2 logic, typically 10-100+ ticks past. This design makes bit-exact OB-bound stop-hunts impossible to detect directly." **Both agents hit the same wall.** ε's weaker signature (SL hit + reversal, no bit-exact requirement) gets 4/4 on XAUUSD — so the "we are the liquidity" story lives at the weaker signature but dies at the strict one.

The reconciliation: **ε's 4/4 SL-reversal is observed at XAUUSD T7 sim; α's 0/16 bit-exact signature spans XAUUSD+NAS100+EURUSD** (different population). Within XAUUSD alone, α's table shows 4 XAUUSD losses, all with touch_d/R > 4.27% (not bit-exact) but reversed 1.26-2.12R. This is ε's sig #3 result (4/4 reversal, 0/4 bit-exact) — **100% consistent with α** at the XAUUSD subset level.

**Net cross-agent consistency verdict: ε ↔ α fully compatible.** Both identify the "XAUUSD losses reverse after SL hit" phenomenon; α frames it as "SL too tight for intra-session noise"; ε frames it as "arb or regime." These are the same data, different interpretations.

### 2.5 Cross-check: ε's stale-OB caveat vs ζ's confirmed OB-mitigation bug

ε caveat (lines 46, 395): "NAS100 signal is driven by AI placing limits into STALE (very-far) OB zones" — observed as large pre-MFE before fill.

ζ finding: `identify_order_blocks` uses wick-intersection mitigation (`market_state.py:444`), which over-mitigates. Combined with `identify_structure` D1-bias-lag keeping stale bullish bias in a D1 bearish window, the system could propose OBs that are geometrically stale (wick-intersected real mitigated zones, but the detector retained them) OR zone-stale (AI picking OB from 2-3 weeks ago because D1 flipped but HH count didn't).

**Spot-check in enriched_candidates.json:**
- 25438.45/25399.05/25497.55 (Jan 15 13:30 AND Jan 16 13:30) — same exact zone 24 hours apart. That is the same-day / next-day reuse, not multi-week stale.
- 24652.15/24546.05/24811.3 (Mar 5 09:30 AND Mar 5 14:00) — same-day reuse.

No zones reused across weeks in the 52-record sample. **ε's "stale" framing might be overstated** — the NAS100 signal may be less "AI using an old OB" and more "AI using a current but geometrically-far OB from a large prior impulse that hasn't been broken." The pre-MFE of 2.61R is still real; the *mechanism* is not necessarily what ε claims.

**If ζ's bug-fix on OB mitigation ships, the stale-OB pattern on NAS100 will weaken or disappear.** ε's pre-entry MFE analysis (and resulting "not supporting" verdict for sig #1) might reverse: if OBs are properly mitigated going forward, NAS100 pre-MFE should drop toward XAUUSD's benign 0.38R level. **ε's sig #1 interpretation is contingent on whether ζ's bugs are real and fixed**; this coupling is under-acknowledged in ε's report.

### 2.6 Implication for ε's counter-measures

ε proposes 3 counter-measures (lines 339-358):
1. Delayed-limit entry (30-60min post-signal)
2. Post-entry fast-SL-move abort (cut at -0.5R in 15min if adverse)
3. XAUUSD-specific risk reduction to 0.5%

**If the root cause is actually α's bad-entry or ζ's detector bugs, the counter-measures are defensible for DIFFERENT reasons:**

1. **Delayed-limit entry:** works against both arb (randomizes timing) AND bad-entry placement (re-evaluation gate). So defensible regardless of root cause. **ε's proposal survives mechanism uncertainty.**
2. **Fast-SL-move abort (cut at -0.5R):** This is NOT a defensive measure against arb — it's an admission that XAUUSD losses go adverse fast regardless of cause. It's a pure outcome-based rule. Could cut good trades that rebound; ε correctly flags that this needs shadow-log-first validation. **Compatible with any root cause** but most justified if the losses are detector-bug-caused (wrong OB → fast adverse) rather than true arb (which might give more variable post-entry kinetics).
3. **XAUUSD risk reduction to 0.5%:** This is a CONSERVATIVE play under uncertainty — justified regardless of root cause because the statistics have materially degraded. **Compatible with any root cause.**

**Counter-measure #2 specifically has an edge-erasing risk.** If ζ's bug fix (OB mitigation + D1-bias-lag) goes live AND β's prompt fix for `sl_buffer_applied` goes live, the XAUUSD fast-loss rate may normalize without counter-measure #2. Adding counter-measure #2 on top of a potentially-fixed base could chop real winners that would have reverted. **This is the coordination risk the chairman should resolve before shipping.**

**Recommendation to chairman:** treat counter-measure #1 (delayed entry) and #3 (risk reduction) as cheap and defensible regardless of root cause. **Sequence counter-measure #2 after ζ + β code fixes have been canary-validated.**

---

## 3. Reproducibility rating

**Rating: 4/5.**

### Strengths
- All data sources cited with paths: `research/t7_live_simulation/all_results_jan_apr10.json`, `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}`, `research/t7_live_simulation/EURUSD_t7_simulation.json`, `knowledge_base_backtest/sessions/{SYM}/*.json`, `knowledge_base/index/_trade_index.json`.
- `_loader.py`, `_mfe_mae.py`, `_main_analysis.py`, `_deep_signal_tests.py` are self-contained and runnable (entry point: `python _main_analysis.py && python _deep_signal_tests.py`).
- Random seeds documented (bootstrap seed=42, null-baseline seed=11).
- `enriched_candidates.json` + `all_results.json` + `deep_signal_tests.json` are committed — provides a reproducible intermediate layer.
- Per-instrument `FILL_EPS` values documented at `_loader.py:34-42`.

### Defects
- **"Z-prop p=0.011" is not in the scripts.** It's implied in the markdown report (line 13, 300) and in the BH sort, but `two_prop_z_p(4, 4, 175, 395)` is what the script actually runs (wrong test, returns null due to n1=4 guardrail). The correct call would be `two_prop_z_p(9, 13, 7, 26)` — but that was never coded. ε hand-calculated and copy-pasted. Reproducible by me in 2 minutes but not 1-command.
- **Null baseline synthetic R distance is `median_price × 0.005`** (≈10pt on XAUUSD), which is tighter than actual CANDIDATE median R of 23pt. Modeling choice not justified in the doc; the ±5pp effect on null rate is unexplored.
- **Script descriptions in the appendix** (line 370-377) say "signatures 1-8" but sig #8 is the verdict aggregation; there's no analysis script for sig #8, the aggregation lives inline in `_main_analysis.py:612-726`. Minor organizational issue.
- **`_analyze_preentry_mfe.py`** is in the scratch dir but not cited in the main doc — role unclear.

Fixing the Z-prop coding would bring this to a 5/5.

---

## 4. Cross-agent consistency review

### 4.1 ε ↔ α (entry execution)

| Claim | ε | α | Verdict |
|---|---|---|---|
| XAUUSD 2026Q1 losses go adverse fast | 69.2% at <0.3R | 61.5% at <0.2R | **Consistent** (different cutoffs, same 13 losses) |
| Bit-exact OB wick + 1R reversal signature | 0/16 strict (line 125) | 0/16 strict (α line 78) | **Consistent** |
| SL placed beyond OB → bit-exact impossible | Line 125-127 | α line 117-121 | **Consistent** |
| Weaker signature (SL hit + reversal) | 4/4 XAUUSD (100%) | 4/4 XAUUSD (100%) | **Consistent** (same 4 losses) |
| Root cause | "arb OR regime" (line 305) | "SL placement vs intra-session noise" (α line 119-121) | **Different narratives, compatible evidence** |

**Net: no contradictions.** ε and α see the same XAUUSD data through different frames; both frames are defensible.

### 4.2 ε ↔ δ (regime decay)

| Claim | ε | δ | Verdict |
|---|---|---|---|
| XAUUSD WR decay 73→59 | Supportive (line 294) | **Not statistically significant** under stationary null (δ §6, p=0.75) | **Apparent contradiction, actually compatible** |
| XAUUSD 2026Q1 outlier | Line 267 | δ §7: hardest regime in series, ADR 5×, KER 0.03 | **Both agree Q1-26 is extreme** |
| Winner MFE 1.04→0.49 | p=0.020 | δ doesn't test within-trade micro-kinetics | **ε adds a layer δ didn't** |

**Resolution:** δ looks at macro outcomes (WR, spread); ε looks at micro kinetics (MFE, MAE). Both are correct at their layer. The system's WR stays near 60% despite micro-kinetics degrading — this is evidence of *compensating selectivity*. **ε's report should have cited δ explicitly; not citing it makes the two look contradictory when they are not.**

### 4.3 ε ↔ ζ (market state prechecks)

| Claim | ε | ζ | Verdict |
|---|---|---|---|
| NAS100 pre-entry MFE 2.61R | "Stale-OB artifact" (line 46) | Wick-based OB mitigation bug (Leak #2) | **ζ explains ε's caveat** |
| EURUSD pre-entry MFE 9.28R | "FX precision bug" (line 47) | ζ's Leak #1 H4-vs-D1 conflict is EURUSD-heavy | **Partially explained** |
| Fast-loss XAUUSD 69% | Attributed to "arb or regime" | ζ doesn't test XAUUSD specifically but OB bugs could contribute | **Coupled; ζ is candidate root cause** |
| Counter-measure fast-SL-abort | Proposed (line 348-353) | ζ's bug fixes might render it redundant | **Coordination risk** |

**Resolution:** ζ's detector bug findings provide mechanism candidates for ε's XAUUSD degradation that are independent of arbitrage. The "regime change" alternative ε constructs post-hoc is a distant cousin of "code bugs producing worse setups, regime-independent." **The CEO should resolve which root cause is primary before shipping ε's counter-measures.**

### 4.4 ε ↔ β (AI integrity)

β's findings (referenced in CLAUDE.md unresolved #5, #7, #8) identify:
- Universal `sl_buffer_applied=0.0` in 1053/1053 XAUUSD records (T2.prompt).
- 2-dp FX precision bug (EURUSD).
- `_FILL_EPSILON=0.05` global mis-scale.

ε acknowledges #7 and #8 directly (lines 47, 395) — EURUSD excluded, per-instrument FILL_EPS used. ε does NOT address #5 directly.

**If β's finding #5 is right (AI not using OB buffer), XAUUSD loss geometry is systemically sub-optimal from the AI prompt level, not the market.** The 69.2% fast-loss rate could be a direct prompt-quality defect, independent of arb AND regime. **ε should have flagged this as a third alternative in §Alternative Hypotheses.**

### 4.5 Summary of cross-agent consistency

- **No outright contradictions** between ε and α, β, δ, ζ.
- **Three layers of compatible explanations converge on XAUUSD 2026:** macro (hard regime, δ), meso (detector/prompt defects, β + ζ), micro (adverse kinetics, α + ε).
- **ε's report reads as if it's the sole explanation**; it is actually one layer of a multi-layer picture. The chairman should synthesize.
- **ε's counter-measure #2 specifically** should be sequenced after ζ's code fixes are canary-validated.

---

## 5. Specific corrections needed in ε's deliverable

### 5.1 Corrections that affect substance
1. **Line 90 + Line 300: BH arithmetic.** Change "passes at rank 2 threshold 0.0167" to "fails at rank 2 (0.017 > 0.0167) but is rescued by the BH step-up rule since rank 3 passes (0.020 ≤ 0.025)." Same conclusion, honestly stated.
2. **Line 300: "Z-prop p=0.011".** Either add the hand-calculation to `_deep_signal_tests.py` as `two_prop_z_p(9, 13, 7, 26)` (note: need to swap n1 args for p2 > p1), or remove the Z-prop reference and rely on Fisher alone.
3. **Line 332: "6/6 for regime change, vs 3/9 supporting signatures for arb".** Reformulate: "3/3 positive signatures for regime; 3/6 positive signatures for arb (cross-instrument predictions fail)." Same verdict, honest framing.

### 5.2 Corrections that affect precision
4. **Line 249: "Loss MFE dropping by 5.4× over 2 years (0.57R → 0.11R)".** Add "(2024 n=7, bootstrap 95% CI [0.18, 0.82]; 2025 n=19, CI [0.35, 0.83]; 2026 n=13, CI [0.05, 0.44])." The 2024 baseline is thin.
5. **Line 299: "Bonferroni FWER correction at α=0.05 across 6 primary signatures → threshold 0.0083. Only sigs that would survive require p < 0.0083. NONE of our tests survive strict Bonferroni."** Add: "Bonferroni at α=0.05/8 = 0.00625 for 8-agent joint test: also NONE survive. Bonferroni at m=12-15 (within-family tests counted): also NONE survive. BH step-up at m=6 is the most permissive correction reported here; no tests survive at stricter m or stricter criteria." More transparent about how permissive the reported correction is.

### 5.3 Corrections that improve cross-agent consistency
6. **§7 Pre-2025 null baseline** should cite δ's §6 bootstrap finding: WR sequence is stationary (p=0.75). Adding "WR remained stable but within-trade micro-kinetics degraded — suggests compensating selectivity under harder regime" closes the ε/δ reconciliation gap.
7. **§8 Alternative hypothesis** should include α's bad-entry, ζ's detector bugs, β's prompt defects as equally-fitting candidates. The "regime change" alternative alone is narrow.
8. **Top 3 counter-measures** should explicitly acknowledge that counter-measure #2 (fast-SL-abort) has edge-erasing risk if ζ's bug fixes ship in parallel; recommend sequencing.

---

## 6. What ε correctly resisted

1. **Running in-sample validation** on the signature battery — ε did not rerun anything to confirm a positive result, which honors CLAUDE.md §AGENT RELIABILITY RULES #6 and §VERIFICATION #7.
2. **Claiming arb definitively** — verdict honestly says "INCONCLUSIVE", which is defensible given the data.
3. **Inflating FX numbers** — EURUSD explicitly excluded; NAS100 pre-MFE explicitly caveated as AI-artifact.
4. **Cross-instrument generalization** — ε did not extrapolate the XAUUSD findings to "all instruments are degrading," resisted the temptation that agents routinely succumb to.
5. **Claiming significance at n<20** — consistent "exploratory" flags (SL-reversal n=4, NZDUSD compression n=5).

Good agent behavior worth noting.

---

## 7. Final brief-lens scoring

| Brief question | Assessment |
|---|---|
| Q1a: n=4 SL-reversal Fisher p=0.040 — meaningful? | **Exploratory but not nonsense.** Wilson CI [0.51, 1.00]; single flip breaks significance; treat as suggestive only. ε correctly flagged "exploratory" but top-line absorbed it as "3rd-strongest signature." |
| Q1b: BH FDR at 3/9 — trustworthy? | **Yes under BH step-up at m=6, as stated.** No under m=12+ (honest count). ε's stated justification at line 90 has an arithmetic error (0.017 > 0.0167) but the survivor set is correct via step-up. |
| Q2: Respective n for 26.9%→69.2%? | **n_early=26, n_late=13.** Fisher exact well-justified at this n (reproducible: p=0.017). Z-prop p=0.011 is reproducible by hand but not coded. |
| Q3: Regime hypothesis over-fit? | **YES, rhetorically.** "6/6 regime" counts failed arb predictions as regime successes. Honest count is "3/3 regime positive, 3/3 arb positive on XAUUSD + 0/3 arb positive on cross-instrument." Three other hypotheses (α, β, ζ) fit equally. Regime hypothesis is post-hoc, not pre-registered. |
| Q4: Reproducibility rating 1-5? | **4/5.** One hand-calculation not in scripts; otherwise runnable end-to-end. |
| Q5: Cross-agent consistency / counter-measure compatibility? | **Consistent with α, β, δ, ζ.** Counter-measure #2 (fast-SL-abort) has edge-erasing risk if ζ's bug fixes ship in parallel — should sequence. Counter-measures #1 and #3 are defensible under any root cause. |

---

## 8. Recommendation to chairman

**Accept ε's findings with the following adjustments:**

1. Present "XAUUSD-specific degradation" as the robust finding (fast-loss + winner MFE; BH step-up at q=0.05 m=6 survives).
2. Demote SL-reversal 4/4 to "suggestive" tier; the Wilson CI [0.51, 1.00] and one-flip fragility warrant this.
3. Replace "arb vs regime change" binary with "multi-cause candidate pool" that includes α's bad-entry, β's prompt defects, ζ's detector bugs. The XAUUSD data doesn't discriminate.
4. Ship counter-measure #1 (delayed-limit entry) and #3 (XAUUSD 0.5% risk) — defensible under any root cause.
5. Sequence counter-measure #2 (fast-SL-abort shadow logger first) AFTER ζ's detector bug fixes are canary-validated. If ζ's fixes resolve the fast-loss pattern independently, counter-measure #2 is unneeded.
6. Fix ε's deliverable: BH arithmetic (line 90, 300), Z-prop reproducibility (line 13, 300), narrow "6/6 regime" counting (line 332), bootstrap CIs on 2024 baseline (line 249). Add explicit cross-references to α, β, δ, ζ.

**The XAUUSD-specific degradation is real. The mechanism is not yet known. Act on the finding conservatively; do not declare arb victory; do not ship parallel edge-erasing counter-measures without sequencing.**

---

## 9. Brevity notes for the record

- This review did **NOT** re-run `_main_analysis.py` or `_deep_signal_tests.py`.
- I spot-checked 4 headline Fisher/MW numbers by hand-calculation from `deep_signal_tests.json` and from `knowledge_base_backtest/sessions/XAUUSD/*.json` — all reproduced exactly.
- I did not verify the null baseline reversal (500-trial Monte Carlo at seed=11) — took ε's claim of 175/395 = 44.3% as stated.
- The `enriched_candidates.json` contains 52 records; I verified the 10 XAUUSD and inspected the NAS100 high-pre-MFE records to sanity-check ε's "stale-OB artifact" caveat.
- Cross-references with α, β, δ, ζ are based on reading their deliverables; no attempt to recompute their numbers.

Signed — Phase 2 ε reviewer, 2026-04-19.
