# Microstructure Analysis — Pressure Test Results
**Date:** 2026-04-05
**Testing:** microstructure_master_20260405.md + all 6 stream JSONs
**Methodology:** Manual recomputation, code review, statistical verification

---

## Overall Verdict: 4 PASS, 2 PARTIAL PASS, 1 INCONCLUSIVE

| Test | Subject | Result | Critical? |
|------|---------|--------|-----------|
| 1 | Sweep Data Accuracy | **PASS** (5/5 dates) | No |
| 2 | Displacement Feature Analysis | **PASS** (with caveats) | No |
| 3 | MSO Recomputation Validity | **INCONCLUSIVE** | Yes |
| 4 | Winning vs Losing Anatomy | **PARTIAL PASS** | Yes |
| 5 | Session Dynamics Realism | **PASS** | No |
| 6 | Cross-Instrument Methodology | **PASS** | No |
| 7 | Top 10 Actionable Patterns | **PARTIAL PASS** | Yes |

**No critical failures triggered** (none of the 5 critical failure conditions were met).

---

## TEST 1: Sweep Data Accuracy — PASS

**Method:** Picked 5 random XAUUSD dates, manually recomputed Asian H/L, PDH/PDL, and sweep detection.

| Date | Asian H | Asian L | PDH | PDL | Sweeps | Result |
|------|---------|---------|-----|-----|--------|--------|
| 2024-09-09 | Match | Match | Match | Match | 2/2 | PASS |
| 2024-05-07 | Match | Match | Match | Match | 2/2 | PASS |
| 2025-05-05 | Match | Match | Match | Match | 4/4 | PASS |
| 2025-03-20 | Match | Match | Match | Match | 2/2 | PASS |
| 2025-02-18 | Match | Match | Match | Match | 4/4 | PASS |

- **Minimum distance filter ($3):** Working correctly — verified in code and data.
- **Sweep type classification:** Rejection = body closes inside level; breakout = body closes beyond. Logic verified in `detect_sweeps()` lines 147-153 and 181-185.
- **Deduplication:** First sweep per level/KZ/day correctly implemented.

---

## TEST 2: Displacement Feature Analysis — PASS (with caveats)

### Raw ranking vs reported ranking:
The raw JSON contains ALL 94 features ranked by MI, including outcome variables:
- **Ranks 1-8 are ALL outcome/post-entry variables:** net_3h (MI=0.693), net_sess, mfe_3h_bm, cont_session, mfe_sess, mae_sess, mfe_3h, mae_3h
- **Rank 9:** `tight` (MI=0.175) — first truly predictive feature
- **Rank 10:** `revisit_mfe` (MI=0.170) — post-entry (MFE after revisit)
- **Rank 11:** `consol` (MI=0.130) — second truly predictive feature

### Master report handling:
The master report correctly filters out outcome variables and presents a "non-leaky" ranking starting with `tight` and `consol`. It also correctly flags `nc_dir` and `nc_cont_pct` as "not usable for entry decisions (they're post-entry)."

### Tautological features in top 10 of clean ranking:
- `nc_dir` (rank 3, MI=0.028): Next candle direction — POST-ENTRY, correctly flagged
- `nc_cont_pct` (rank 4, MI=0.028): Next candle continuation — POST-ENTRY, correctly flagged
- No tautological features in the top 10 that are NOT flagged

### Constant feature check:
- `mss`: NOT constant (6.7% max value — well distributed)
- `sweep_cb`: 90.8% dominant value (moderate imbalance — could reduce discriminative power)
- `creates_fvg`: 61.5% dominant (OK)
- No features with >95% same value

### Caveat:
`tight` (MI=0.175) and `consol` (MI=0.130) have chi2 p-values of 0.225 and 0.391 respectively — **NOT statistically significant**. The high MI may be a cardinality artifact. The master report notes this caveat.

### Cross-reference with previous investigation:
Top predictors (tight, consol, volume, creates_fvg) are the SAME as previously identified. New features not previously examined: nc_body_ratio, sweep_cb, liq_depth (all low MI < 0.003).

---

## TEST 3: MSO Recomputation Validity — INCONCLUSIVE

### Discrepancy found:
The master report states "Stream 4 event sequencing failed — simplified structure detection was insufficient." However, the Stream 4 JSON contains REAL events:
- Winners: avg 9.66 events per trade, 86.2% have sweeps, 90.0% have displacements
- Losers: avg 9.38 events per trade, 86.7% have sweeps, 97.8% have displacements

### Assessment:
- Events WERE detected using the simplified M15 approach
- However, there is NO ground truth (production MSO outputs) to compare against
- The master report's "failed" assessment may refer to an earlier iteration, or to the inability to match production MSO quality
- Cannot verify whether the simplified detection produces events CONSISTENT with what the AI saw during batch sessions

### Verdict:
INCONCLUSIVE — data exists and appears reasonable, but no production MSO comparison is possible. The 4-hour M15 window detects events, but their correspondence to the multi-timeframe production MSO is unverifiable.

---

## TEST 4: Winning vs Losing Anatomy — PARTIAL PASS

### Event detection: WORKING
Both winners (n=80) and losers (n=45) have real pre-entry events detected. The >50% threshold is met for all major event types in BOTH groups:
- SWEEP: W=86.2%, L=86.7%
- BOS: W=82.5%, L=77.8%
- DISPLACEMENT: W=90.0%, L=97.8%
- OB_FORMED: W=98.8%, L=100%
- CHoCH: W=71.2%, L=75.6%

### Differentiation: NONE
**Zero of 11 features show statistical significance (p<0.05):**

| Feature | Winners | Losers | p-value |
|---------|---------|--------|---------|
| total_events | 9.66 | 9.38 | 0.692 |
| n_displacements | 2.19 | 2.60 | 0.124 |
| n_sweeps | 2.14 | 1.84 | 0.285 |
| n_structure_breaks | 2.67 | 2.38 | 0.201 |
| has_sweep | 86.2% | 86.7% | 0.998 |
| displacement_strength | 3.29 | 3.66 | 0.268 |

Losers actually have MORE displacements (2.60 vs 2.19) and HIGHER displacement strength (3.66 vs 3.29), though not significantly.

### Sequence analysis:
Top sequences have max 2.5% frequency (winners) / 4.4% (losers). No dominant pattern emerges — sequences are nearly unique to each trade.

### Hindsight bias: NONE
All events are in the 4-hour pre-entry window — observable in real-time.

### Robustness:
With zero significant differences, removing 10 winners would not change the conclusion.

### Interpretation:
This is a valid NULL RESULT, not a methodology failure. Pre-entry event counts/frequencies do NOT predict trade outcome. The differentiating factors are at the ENTRY QUALITY level (OB zone, width, premium placement from Stream 3), not the preceding event sequence.

---

## TEST 5: Session Dynamics Realism — PASS

### 5A: First-hour direction persistence
- **XAUUSD London:** 49.6% (n=514) — BELOW random. NOT actionable.
- **XAUUSD NY:** 52.3% (n=516) — barely above random. NOT actionable.
- **Actionability:** Signal requires full hour to form, arriving 60 minutes into KZ window. Still within the window (4-5 hours remain), so PARTIALLY usable in theory — but the near-random rates make it moot.
- **Master report assessment:** Correctly says "Do NOT use first-hour direction as a strong signal."

### 5B: Asian session predictors
- Asian-London direction correlation: 0.003 — ZERO signal
- Already captured by existing Asian range width filter: direction adds nothing new
- First-touch analysis: ~50/50 probabilities for all combinations — random

### 5C: London-NY relationship
- Same direction: 51.8% (n=515) — perfectly random
- Sample size: ADEQUATE (515 days with both sessions represented)
- No predictive relationship between London and NY direction

### Overall:
All findings correctly assessed for actionability. Near-random results correctly identified as non-actionable. Bullish bias in London first-hour (55.2% vs 43.0%) is a subtle observation worth noting.

---

## TEST 6: Cross-Instrument Methodology — PASS

### Correlation on matched dates:
516 common trading days used — CORRECT.

### Confounding from gold bull run:
Daily RETURNS used (not price levels) — bull run confounding is mitigated. Rolling 20d correlation range [-0.35, 0.81] includes negative periods, confirming the relationship is genuinely variable and not just spurious co-trending.

### Lead-lag analysis:
Simple sweep timing comparison, NOT Granger causality. GBPUSD sweeps first 58.2% of the time, likely because London (where GBPUSD is more active) opens before NY. Adequate as a descriptive analysis; acknowledged limitation for causal claims.

### Divergence signal quality issue:
"XAU down + GBP up → XAU next day positive 58.5%" is MISLEADING:
- Average next-day return is **-0.1031%** (NEGATIVE)
- The positive hit rate hides the fact that losses are larger than gains
- No positive expected value — should be labeled "not actionable" rather than "weak"

---

## TEST 7: Top 10 Actionable Patterns — PARTIAL PASS

| # | Pattern | n | New? | Real-time? | Implement | Validated? |
|---|---------|---|------|------------|-----------|------------|
| 1 | FVG distinguishes quality | 6,641 | No | Yes | Prompt | No |
| 2 | tight/consol top predictors | 6,641 | No | Yes | Prompt | No |
| 3 | GBPUSD rejection sweeps | 377 | **Yes** | Yes | Code | No |
| 4 | 83.7% origins revisited | 6,641 | No | Yes | Core | No |
| 5 | Hour 2 UTC best displacement | 232 | **Yes** | Yes | Prompt | No |
| 6 | OB mitigation 69.7% | 818 | No | Yes | Core | No |
| 7 | Narrow OBs in premium zone | 121 | **Yes** | Yes | Prompt | No |
| 8 | GBPUSD double sweeps 5x | 176 | **Yes** | Yes | Code | No |
| 9 | First-hour direction random | 514 | **Yes** | Yes | Prompt | No |
| 10 | Cross-instrument moderate | 516 | **Yes** | Yes | Low | No |

### Summary:
- **All 10 have n >= 30:** YES
- **All 10 are real-time detectable:** YES
- **6/10 are NEW information** not previously identified
- **0/10 validated in hold-out/split periods** — ALL in-sample
- **Implementable:** 5 prompt changes, 2 code changes, 2 already core, 1 low priority

### Critical issues:
1. **No split validation:** All findings are in-sample. The master report acknowledges this ("All findings are in-sample. True validation requires hold-out or walk-forward testing") but does not document split-period results.
2. **P2 statistical weakness:** tight/consol chi2 p-values (0.225, 0.391) are NOT significant despite high MI scores.
3. **P10 misleading presentation:** 58.5% positive rate masks negative expected value.

---

## Recommendations

### Immediate actions (high confidence):
1. **P7 — Premium zone filter:** Only statistically significant finding (p=0.020). Implement premium zone preference in OB scoring.
2. **P3 — GBPUSD rejection sweeps:** New, adequately sampled, actionable. Add as high-priority signal for GBPUSD.

### Moderate confidence (implement with monitoring):
3. **P1 — FVG weight:** Low MI (0.006) but 10pp difference with large n. Small effect, low risk.
4. **P5 — Hour 2 displacement quality:** Interesting but n=232 for this specific hour.
5. **P8 — GBPUSD double sweep patience:** Descriptive guidance for GBPUSD strategy.

### Low confidence (need validation first):
6. **P2 — tight/consol weighting:** High MI but statistically non-significant. Need walk-forward test.
7. **P10 — Cross-instrument divergence:** Negative expected value — DO NOT implement as-is.

### Do not implement:
8. **P9 — First-hour direction:** Correctly identified as near-random. Use as guardrail (don't rely on it), not as signal.
9. **P4, P6 — Framework validation:** Already the core approach. No action needed beyond confirmation.
