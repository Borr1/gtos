# Tier 2 Spec — Intra-Candle Limit-at-Edge Entry Study

**Status:** Specced, NOT yet dispatched. Awaiting CEO sign-off.
**Date:** 2026-04-18 (Session 25)
**Parent ADR:** `.context/06_decisions/003_retest_geometry_study_corrected_methodology.md`
**Builds on:** Tier 1 distributional analysis (n=121) + verification (n=726). See `research/retest_geometry/outputs/distributional_analysis/`.

---

## Background

Production currently enters retests at market on the M15 candle close where the AI fires CANDIDATE. CEO hypothesis: an intra-candle limit fill at the far OB edge would capture a better entry price (the wick low/high) than waiting for the candle to close. SL and TP are deterministic post-CANDIDATE — entry geometry is the only free variable.

Tier 1 + verification established:
- **P(WIN | retest does NOT penetrate far OB edge) = 100%** (n=452, Wilson lower 99.16%)
- **Median winner reverses at 55% of OB body depth** — most winners do NOT reach the far edge
- **Wick-vs-close categorical is a downstream artifact of SL margin** (verified, see ADR 003 Lesson 4)

The "shallow retests dominate the high-WR population" finding creates a tension for any limit-at-edge proposal: a far-edge limit would NEVER fill on shallow retests — i.e., on the highest-conviction winners. That tension is what this study has to resolve quantitatively.

---

## Question

For OB retests where the AI fires CANDIDATE, what is the per-trade R differential between:
- **Current:** market entry at retest M15 candle close
- **Proposed:** limit entry at far OB edge (intra-candle fill)
- **Hybrid:** 50% market + 50% limit at far edge

…on the population of setups that fill, accounting for setups missed by the limit?

---

## Sub-questions

1. **Fill rate.** What % of CANDIDATEs would fill on a far-edge limit within the retest M15 candle? Within the next 1, 2, 4 candles?
2. **Entry-price differential.** For setups that fill on both methods, what's the average price differential? In ATR? In R-units (relative to SL distance)?
3. **Per-symbol fill rate & differential.** Does the answer differ by symbol? Particularly: does USDJPY (low penetration rate, 30%) behave differently from US30 (high penetration, 54%)?
4. **Per-session fill rate & differential.** London / NY / Tokyo splits.
5. **Per-OB-body-size differential.** Big OBs vs small OBs — is the differential bigger when the OB has more room?
6. **Hybrid blended R.** If we deploy 50/50 hybrid: what's the blended expected R per setup, accounting for partial-fills?
7. **Missed-setup cost.** For setups the limit MISSES (shallow retests that never reach far edge): what's the foregone R?
8. **Limit-at-midpoint as alternative anchor.** Same analysis but with limit at OB body midpoint instead of far edge — does midpoint capture more setups while still giving meaningful price improvement?

---

## Hypothesis (pre-committed)

**H1 (primary):** Limit-at-far-edge entry adds at least +0.2R per filled setup vs market-on-close, on >40% of CANDIDATEs.

**H2 (alternative):** Hybrid 50/50 (market + far-edge limit) produces a blended +0.1R per setup over pure market entry.

**H2b (midpoint variant):** Limit-at-midpoint entry adds at least +0.1R per filled setup AND fills on >50% of CANDIDATEs (i.e., midpoint trades fill rate for price improvement vs far-edge).

**H3 (null):** No anchor produces a meaningful improvement (all differentials <+0.05R OR fill rates <30%) — recommend no change.

Decision tree (apply in order):
- If H1 holds → deploy hybrid 50/50 (far-edge anchor) to live shadow first.
- Else if H2b holds → deploy hybrid 50/50 (midpoint anchor) to live shadow.
- Else if H2 holds → deploy hybrid 50/50 (far-edge) directly to live (smaller upside, less risk).
- If H3 → document as null result; no change to entry logic.

---

## Methodology

### Data
- **Primary:** `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` (n=726, ADR-003-compliant)
- **Secondary:** `research/retest_geometry/outputs/historical/combined_retests.csv` (n=121, A1_v2)
- **Raw OHLC:** `data/historical/` — 2-year M15 corpus per symbol

### Per-row simulation
For each retest row:

1. Read raw M15 OHLC for the retest candle and the resolution window (48 candles for Geom A).
2. Identify the far OB edge price for the row (long: OB low; short: OB high). Derive from `ob_body_size` and `retest_entry_price` if not directly stored — or read OB metadata from `study.py` output.
3. **Market entry:** entry = retest candle close (current production behavior).
4. **Limit entry — run for BOTH anchors: (a) far OB edge price, (b) OB body midpoint price.** For each anchor: entry = anchor price IF the retest candle's wick reached past it. If wick didn't reach anchor → mark as "limit not filled in retest candle"; check next 1, 2, 4 candles for a fill within the window. Track which candle filled. Report fill rate, mean/median R, and R differential separately for each anchor.
5. **Hybrid entry — run for both anchors.** entry = 0.5 × market_entry + 0.5 × limit_entry IF limit filled, else 1.0 × market_entry. Track separately the 50% slice that fills as limit. Report blended R for far-edge hybrid AND midpoint hybrid.
6. **Re-walk forward** with new entry price. Recompute SL price (= far edge ± 0.5 × ATR — same offset, but absolute price changes), TP price (= 1 × OB body past far edge — same logic). Classify outcome (CONTINUED / REVERSED / UNRESOLVED) under new geometry.
7. Compute R = continuation_in_price / SL_distance (both in price units), using the new entry-anchored SL distance.

### Comparison metrics
- Fill rate by method (market: always 100%; limit: %; hybrid: limit fill rate determines weighting)
- Mean / median R per resolved setup, by method
- Mean / median R per CANDIDATE (treating missed limits as 0R)
- Per-symbol, per-session, per-OB-size buckets
- Wilson 95% CI on rates and bootstrap CIs on R differentials

### Statistical tests
- Paired test (Wilcoxon signed-rank) on per-row R differential, market vs limit, on the subset where both filled
- Bootstrap 95% CI on mean R differential
- Per-symbol breakdown only where n ≥ 30 fills

---

## Edge cases & decisions to pre-commit

1. **Limit fills on entry candle vs later candle.** If the retest candle's low (long) reaches OB low, fill at OB low. If not, scan forward for first candle whose low reaches OB low. Fill at OB low. If never reached within window → no fill.
2. **Limit fill at gap open.** If next candle gaps past the limit price, fill at the gap open (worse for buyer if long retest). Document.
3. **Same-candle SL+TP+entry ambiguity.** If limit fills AND SL hits AND TP hits all in same candle: order = entry first, then conservative pessimistic resolution (SL before TP for long, etc.).
4. **Setups where retest candle close is ALREADY past far edge.** These represent close-penetrated retests at entry candle. Market entry is unchanged. Limit at far edge would also fill (price has crossed it). Both fill at different prices — limit gets the better fill.
5. **MAE is recomputed.** With new entry, MAE is also new. Don't reuse the CSV's MAE field — re-derive from raw M15.

---

## Deliverable

Markdown report at `research/retest_geometry/outputs/intra_candle_entry/intra_<agent_id>_report.md` containing:

1. Schema verification + raw OHLC availability
2. Fill rate by method, overall + per-symbol + per-session
3. Mean/median R per resolved setup, by method
4. R differential (market vs limit, market vs hybrid) with bootstrap 95% CI
5. Missed-setup analysis (what would the limit miss?)
6. Per-symbol/session breakdowns (where n permits)
7. Pre-committed decision: H1 / H2 / H3 verdict
8. Limitations & methodological choices

---

## Agent architecture

**2 Opus 4.7 max-effort agents** (`intra_a`, `intra_b`), independent code paths, run in parallel. Same brief, separate output directories. Convergence check on:
- Fill rate (should match closely)
- Mean R differential (should match within bootstrap CI)
- H1/H2/H3 verdict (should agree)

Pattern matches the four prior 2-agent rounds in this study (A1+A2, A2_v2+A3_v2, distrib_a+distrib_b, verify_a+verify_b). All four converged on raw numbers; verify round caught a methodological artifact via convergence check. Continuing the pattern.

**Estimated wall clock:** 30-45 min per agent (raw OHLC re-walk is O(n × window) per row × n=726).

---

## Hard constraints (non-negotiable)

- WF-1 discipline: **zero** `src/components/`, `prompts/`, `config/` changes
- Observation only: no live-system mutation
- Agents write only to `research/retest_geometry/outputs/intra_candle_entry/` and `scratch/intra_{a,b}/`
- No commit, no push without CEO sign-off
- No coordination between intra_a and intra_b

---

## Decisions (CEO-approved 2026-04-18)

The 3 originally-open questions in this spec were resolved by CEO before dispatch:

1. **Add limit-at-midpoint as a 1st-class anchor (Q8 promoted, H2b added).** Reasoning: Tier 1 found median winner reverses at ~55% of OB body — midpoint (50%) likely fills ~50%+ of setups while far-edge fills only the deeper retests. Run full analysis (fill rate, R differential, hybrid blend) for BOTH anchors. New hypothesis H2b in scope; decision tree updated above.

2. **OB-size as stratification, NOT subset.** Q5 already asks per-OB-body-size differential. Stratify within the analysis; do NOT restrict the cohort to large-OB-only. Avoids confounding (AI conviction ≠ OB size) and preserves small-OB data.

3. **Same-price market/limit fills.** Treat as identical (differential = 0R for those rows; do NOT inflate "limit captured" success rate). Track and report the count separately in the deliverable for transparency.

---

## Success criteria for the study itself (not the hypothesis)

- Both agents produce reports
- Fill rate numbers agree within 2pp between agents
- Mean R differential agrees within bootstrap CI
- H1/H2/H3 verdicts agree

If verdicts disagree → adversarial methodology review (third agent, cold) before any decision.

---

## Why this study now

- Tier 1 + verification are done — distributional findings are battle-tested
- The wick/close gate idea was correctly killed; intra-candle entry is the surviving live thread from the CEO's intra-candle question
- Cheap to run (~1 hour wall clock, two agents in parallel)
- Result is decision-ready: deploy/don't-deploy a hybrid entry rule

---

## Why this study NOT yet

- Tier 2 list has 8 questions; this is question #1 (entry calibration). Other Tier 2 questions (continuation-R distribution, depth × magnitude correlation, partial-close optimization) are independent. Could be parallelized as separate spec → separate dispatch.
- This study assumes the AI gate stays unchanged. If a future change to the AI fundamentally shifts CANDIDATE distribution, results would need re-validation.

---

*Spec authored by main thread, Session 25. Dispatch awaits CEO sign-off.*
