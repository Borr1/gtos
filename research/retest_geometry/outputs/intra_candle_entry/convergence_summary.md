# Tier 2 Intra-Candle Entry — Convergence Summary (intra_a vs intra_b)

**Date:** 2026-04-18 (Session 25)
**Author:** Main thread Claude
**Inputs:** `intra_a_report.md`, `intra_b_report.md`
**Spec:** `research/retest_geometry/tier2_intra_candle_entry_spec.md`

---

## TL;DR

Numerical convergence is mostly tight — fill rates within 0.0–2.2pp, missed-setup counts byte-identical (206/193/0), hybrid-far per-CANDIDATE differential within 0.025R across both interpretations. **But the agents made different methodology choices on the spec's "market entry = retest candle close" definition, producing a consistent ~0.06R gap in differential estimates that pushes verdicts to opposite sides of the H1 (+0.2R) and H2b (+0.1R) decision thresholds.**

intra_b uniquely surfaced a **deployment-critical qualitative finding** that intra_a did not: the far-edge limit BREAKS 156 market wins (43.8% of paired wins) but RESCUES only 14 market losses (8.8%). Mean differential is positive ONLY because the limit-fill winning trades are 3.86× R-magnitude (small SL distance → bigger R per win), not because it improves win/loss discrimination. **High-variance edge, not high-WR edge.** For prop-firm context where consistency matters more than total return, this trade-off may be unattractive even if statistically positive.

**Per spec (line 156): verdicts disagree → adversarial methodology review (third agent, cold) before any decision.**

---

## Numerical convergence

| Metric | intra_a | intra_b | Gap | Status |
|---|---|---|---|---|
| Total rows processed | 726 | 726 | — | ✅ |
| Far-edge limit fill rate | 71.6% (520/726) | 71.6% (520/726) | 0.0pp | ✅ Identical |
| Midpoint limit fill rate | 87.7% (637/726) | 85.5% (621/726) | 2.2pp | ⚠️ Just outside 2pp tolerance |
| Far-edge missed setups | 206 (193 CONT, 0 REV) | 206 (193 CONT, 0 REV) | 0 | ✅ Identical |
| Far-edge limit-minus-market mean R (paired) | **+0.240** [+0.108, +0.368] | **+0.178** [+0.053, +0.299] | 0.062R | ⚠️ CIs overlap |
| Midpoint limit-minus-market mean R (paired) | **+0.150** [+0.077, +0.219] | **+0.086** [+0.015, +0.154] | 0.064R | ⚠️ CIs overlap |
| Hybrid-far spec-literal / single-pos vs market | +0.247R | +0.222R | 0.025R | ✅ |
| Hybrid-far per-leg / two-leg vs market | +0.082R | +0.062R | 0.020R | ✅ |

Fill rates and missed-setup classifications converge tightly. R differentials show a **consistent ~0.06R gap** (intra_a always higher) that is too systematic to be sampling noise.

---

## Verdict convergence

| Hypothesis | intra_a | intra_b | Agree? |
|---|---|---|---|
| **H1** (far-edge ≥+0.2R, fill >40%) | HOLDS by mean (+0.240); CI lower below threshold; flagged | **FAIL** (mean +0.178 below threshold) | ❌ Disagree on letter; both straddle the +0.2R line |
| **H2 single-pos / spec-literal** (≥+0.1R) | HOLDS (+0.247) | PASS (+0.222) | ✅ |
| **H2 per-leg / two-leg** (≥+0.1R) | Below bar (+0.082) | FAIL (+0.062) | ✅ |
| **H2b** (midpoint ≥+0.1R, fill >50%) | HOLDS (+0.150) | **FAIL** (+0.086) | ❌ Disagree on letter; both straddle the +0.1R line |
| **H3** (null) | DOES NOT HOLD | FAIL | ✅ |

**Verdict disagreement on H1 and H2b — both estimates straddle the decision thresholds.** Per spec, this triggers adversarial review.

Both agents flagged the **H2 hybrid interpretation ambiguity** independently and produced near-identical numbers under each interpretation:
- Spec literal / single-position averaged-entry: **clears H2**
- Per-leg two half-sized positions: **fails H2**

This is a deployment design question, not a data finding.

---

## Root-cause analysis: why the ~0.06R gap?

Both agents read the spec literal "market entry = retest M15 candle close" but interpreted it differently:

- **intra_a:** Used the actual M15 candle close price (literal spec text). Sometimes outside the OB zone (5.6% of rows have close past far edge in impulse direction).
- **intra_b:** Used the CSV's `retest_entry_price` field (which is M15 close IF inside zone, else next M15 candle's open — matches what the A2_v2 backtest produced for the upstream outcome classifications).

Implications:
- Market R baseline differs: intra_a market mean R = -0.006 per resolved; intra_b = +0.046.
- intra_b's market baseline is +0.052R higher → all "limit minus market" differentials look ~0.05–0.07R smaller.
- Both interpretations are defensible. intra_a is closer to the spec's literal text. intra_b is closer to the upstream A2_v2 classification used in Tier 1 verification.

This is **exactly the kind of subtle methodology fork the 2-agent verification pattern is designed to catch.** Neither agent is wrong; the spec is ambiguous on which entry rule to use.

A second smaller divergence: intra_b's midpoint fill count (621) differs from intra_a's (637), a 16-row gap (~2.2pp). Likely cause: different handling of "already past midpoint at retest" rows. Need a third agent to spot-check.

---

## Critical qualitative finding (intra_b uniquely)

intra_b's cross-tabulation of paired far-edge outcomes (n=498):

```
                  far=CONT   far=REV   far=UNRES
market=CONT          182       156         18      (356 market wins)
market=REV            14       146          0      (160 market losses)
market=UNRES           0         0          4
```

- **156 cases (43.8% of market wins) where the far-edge limit BREAKS a win** that market would have caught
- **14 cases (8.8% of market losses) where the far-edge limit RESCUES a loss**
- **182 cases (51.1% of market wins) where both win** — and on these the limit gives **3.86× the R per win** (small SL distance from limit fill → bigger R-multiple per TP hit)

**The mean +0.18R differential exists ONLY because winning limit trades are 3.86× the R magnitude of winning market trades.** This is a high-variance edge, not a high-WR edge. The strategy trades 142 net wins for higher R-per-win on the remaining ones.

**Prop-firm context implications:**
- FTMO's 5% daily loss / 10% max drawdown caps mean variance is the binding constraint, not expected return
- A strategy that decreases WR but increases R-per-win can underperform a higher-WR strategy on prop-firm metrics even with higher mean R
- The 156 broken wins are concentrated on the SAME setups Tier 1 identified as "shallow retests dominate the high-WR population" — the limit systematically forfeits the highest-conviction continuations

intra_a did not surface this cross-tab. **This finding alone may matter more than the H1 verdict.**

---

## Other qualitative findings

### Methodology pessimism → numbers are LOWER bounds (intra_b §10.1)
Same-candle SL+TP+entry ambiguity is resolved pessimistically (SL before TP). M15 data can't disambiguate; M1 or M5 data could. intra_b estimates true differential is likely **+0.20 to +0.25R** under more even-handed methodology — which would clear H1.

### Per-symbol concentration
- intra_a: GBPUSD, US30, XAUUSD all show CI excludes 0
- intra_b: ONLY XAUUSD shows CI excludes 0 (GBPUSD CI lower = 0.000, marginal)
- Both agree: GBPJPY essentially null differential

The per-symbol divergence is the same root cause as the headline divergence — different market baselines.

### Per-session concentration (both agents agree)
- NY session: strongest differential for both anchors, CI clearly excludes 0
- London: marginal positive
- Tokyo: weakest of the three named sessions
- Off-session: lowest fill rates (58% far-edge), weakest signal

### Lesson 4 stratification (intra_b §10.10)
intra_b applied the Lesson 4 rule — stratify by underlying continuous variable before recommending. Stratified by SL-distance ratio:
- q1_tightest: ~0R differential (consistent with pessimistic same-candle artifact)
- q2/q3/q4: consistent +0.21 to +0.28R

The differential is real and not a categorical proxy. The methodology pessimism is the dominant artifact.

### OB-size stratification (Q5)
- intra_a quintile data: non-monotonic, Q4 actually negative (−0.056), Q1 + Q3 + Q5 strongly positive
- intra_b quartile data: also non-monotonic (Q1 highest +0.250, Q2 weak +0.094)
- Both confirm: **"bigger OB → bigger differential" hypothesis is NOT supported**

---

## Recommendation

**Per spec line 156 (mandatory rule):** Verdicts disagree on H1 and H2b → **adversarial methodology review (third agent, cold) required before any deployment decision.**

The third agent's brief should:
1. Adjudicate the market entry definition fork (intra_a's literal close vs intra_b's CSV `retest_entry_price`). Recommend which is canonical for this study and re-derive verdicts under the chosen interpretation.
2. Investigate the 16-row midpoint fill count divergence (637 vs 621) and identify root cause.
3. Independently verify intra_b's win-broken/loss-rescued cross-tabulation. If correct, weight it heavily in the deployment recommendation.
4. Independently consider whether the same-candle pessimism is the dominant methodology artifact and whether the M5/M1 re-run intra_b suggested is a prerequisite for any deployment.

**Even if the third agent resolves the verdict in favor of "deploy hybrid 50/50 (far-edge anchor) to live shadow":**
- The win-broken/loss-rescued ratio (156/14 = 11:1) and high-variance edge profile suggest **prop-firm context may make this unattractive regardless of mean R differential.**
- A more conservative path: deploy MIDPOINT hybrid (lower price improvement but lower variance, fewer broken wins per intra_b §5 cross-tabulation showing 82 broken vs 156).
- A more aggressive path: restrict to NY-session-only, XAUUSD-only deployment — but n is thin and risks p-hacking.

**Specific recommendation to CEO:**

Two options for the weekend:

**Option A (per spec):** Dispatch adversarial third agent now (~30-45 min). Re-derive verdict. If clean H1 holds → consider shadow deploy; if confirmed null → document.

**Option B (CEO override on spec rule):** Accept the current results as **inconclusive on the H1/H2b decision tree but informative on deployment risk**. Document as null result for entry rule change. The win-broken/loss-rescued finding is robust regardless of methodology fork — that's the deployment-relevant finding.

If the funded challenge starts Tuesday, Option B is cheaper. Option A buys methodology confidence but doesn't change the qualitative deployment picture.

---

## Hard finding regardless of third-agent outcome

**The Tier 1 finding from the parent study still stands:** the existing market-entry rule is producing 100% WR on non-penetrated retests (Wilson lower 99.16%). The current entry logic is NOT broken. Tier 2 was asking whether limit-at-edge could capture additional R from the 28% of CANDIDATEs where retest goes deep. Answer:

- **The answer is YES on mean** — both agents agree the limit captures more R per resolved setup
- **The answer is MAYBE on net** — the 156 broken wins (mostly the high-conviction shallow-retest population) are a real cost
- **The answer is NO under strict per-leg hybrid interpretation on H2/H2b thresholds**
- **The answer is YES under spec-literal hybrid interpretation on H2 threshold**

No clean answer exists from this study under the strictest reading. The cleanest deployment-relevant finding is qualitative: **the existing market-on-close rule may already be on the efficient frontier for prop-firm consistency, even if not for theoretical mean R.**

---

*Joint summary author: main thread Claude. Both individual reports preserved at `intra_a_report.md` and `intra_b_report.md`. Per-row simulation data in agents' scratch directories.*
