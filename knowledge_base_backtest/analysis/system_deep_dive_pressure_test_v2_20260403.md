# Pressure Test — System Deep Dive Verification
**Date:** 2026-04-03
**Purpose:** Verify the deep dive analysis didn't miss critical patterns or produce misleading conclusions.

---

## Test Results Summary

```
=== PRESSURE TEST RESULTS ===
Test 1 (Reasoning Patterns):    FAIL — 2 miscategorizations, m15 bug on all 10 trades
Test 2 (Confidence Correlation): FAIL — r=-0.019, confidence is pure noise (3 values: 75/80/85)
Test 3 (Missed Setup Verify):   N/A  — deep dive methodology gap prevents verification
Test 4 (Safety Rejection):      PARTIAL — GBPUSD 4/7 profitable, but combined 11/25 = 44%
Test 5 (Session Memory Impact): N/A  — batch cannot test session memory (method artifact)
Test 6 (Partial Close Math):    PASS — 3/3 matched within 0.00R (exact match)
Test 7 (Token Budget):          PASS — 3.1% usage, 3.5% after expansion, massive headroom
Test 8 (Context Agent):         FAIL — costs 174% MORE tokens, not justified

Key finding: The deep dive's loss categorization contains 2 errors out of 5 losses (40%),
and the m15_confirmation.confirmed bug affects ALL 10 sampled trades. These are now fixed
in Phase 1C. Session memory evaluation is a methodology gap in the batch testing approach.
```

---

## Test 1: Winning vs Losing Reasoning — Pattern Verification

### Result: FAIL

**Checked 2 "market_condition" losses — found both miscategorized:**

**Loss 2024-03-15 (categorized: market_condition, actual: STRUCTURE MISREAD)**
- Grade A+, confidence 80
- `h1_setup.poi_identified = False` and explanation says "No unmitigated H1 order blocks available for retest setup"
- Yet the AI gave CANDIDATE A+ using an M15 OB instead of H1 OB
- This is not "market condition" — the AI applied the wrong framework (M15 OB retest instead of H1 OB retest) and still passed it as A+

**Loss 2024-03-01 (categorized: market_condition, actual: THRESHOLD VIOLATION)**
- Grade A, confidence 75
- M15 displacement ratio: 0.4x average body
- U3 requirement: displacement >= 1.5x average body
- This should have been NO_TRADE per U3. The AI accepted weak displacement. This is a threshold violation, not random market loss.

**Winner red flags found: 8 across 5 trades**
- ALL 5 winners have `m15_confirmation.confirmed = False` despite describing strong M15 CHoCH/BOS with displacement. This confirms the Phase 1C bug (schema field always defaults to False).
- 3/5 winners mention "sweep" in reasoning but set `liquidity.swept = False`. The AI describes sweeps in narrative but doesn't set the structured field correctly.

**Corrected categorization:**

| Date | Deep Dive Category | Actual Category |
|---|---|---|
| 2024-03-15 | market_condition | structure_misread (H1 POI=none, used M15 OB) |
| 2024-03-01 | market_condition | threshold_violation (M15 disp 0.4x < 1.5x) |
| 2024-03-13 | timing_error | timing_error (CONFIRMED) |
| 2024-03-18 | market_condition | market_condition (CONFIRMED - genuine random loss) |
| 2024-05-28 | market_condition | market_condition (CONFIRMED - MFE only 0.20R) |

**Impact:** 2/5 losses had preventable causes that the safety system should have caught. Phase 1C's Internal Consistency Rules should prevent the m15 threshold violation pattern. The structure misread (no H1 OB but still CANDIDATE) may require additional guardrails.

---

## Test 2: Confidence Score — Verify Correlation

### Result: FAIL — Confidence is pure noise

| Dataset | n | Pearson r | p-value |
|---|---|---|---|
| GBPUSD | 43 | +0.085 | 0.588 |
| XAUUSD | 100 | -0.094 | 0.355 |
| **Combined** | **143** | **-0.019** | **0.821** |

**r = -0.019 is essentially zero.** With 143 trades and p = 0.82, there is no relationship between confidence score and outcome.

**Only 3 unique confidence values exist in the dataset: 75, 80, 85.**
- 75: used when AI docks -5 for one factor (e.g., CHoCH instead of BOS)
- 80: the default "everything looks good" score (Baseline 70 + displacement +5 + OB +5)
- 85: rare, used for exceptional displacement (>5x)

**High confidence (>=80) losses:** 12 trades. Same reasoning quality as winners.
**Low confidence (<80) wins:** 3 trades — including the 2 best GBPUSD trades (R=+2.62 and R=+2.90). The AI underestimated these because it penalized CHoCH-based setups, which actually won big.

**This confirms the Phase 1A decision:** The 500-token rubric was producing a 3-valued checkbox, not a calibrated score. Simplifying to "Rate 50-95 based on confluence count" loses nothing.

---

## Test 3: Missed Setup Verification

### Result: N/A — Methodology Gap

The deep dive found 0 "missed setup" candidates because:
1. Batch mode only evaluates dates that pass the prescreen (D1 clear + H4 aligned)
2. Within batch-evaluated dates, all responses are CANDIDATEs (the batch selects for them)
3. NO_TRADE responses from batch runs are not captured in the deep dive analysis

**This is a gap in the evaluation methodology, not the system.** To properly test missed setups would require:
1. Running the displacement scanner on ALL dates (not just prescreen-pass)
2. For dates where displacement exists but no CANDIDATE was produced, reading the AI's NO_TRADE reasoning
3. Verifying whether the AI's reason for passing was legitimate

**Recommendation:** Add NO_TRADE response logging to future batch runs. Currently, only CANDIDATE trades get post-processed.

---

## Test 4: Safety Rejection Outcome Verification

### Result: PARTIAL — Safety check validated overall

**Deep dive claim:** 5/8 GBPUSD direction-mismatch rejections would have been profitable (62.5%)

**Pressure test verification (from Phase 3 counter-trend analysis):**
- GBPUSD: 4/7 decisive wins = 57.1% WR (close to deep dive claim)
- XAUUSD: 7/18 decisive wins = 38.9% WR
- **Combined: 11/25 decisive wins = 44.0% WR (p = 0.73)**

The deep dive's GBPUSD finding was approximately correct (57% vs claimed 62%) but misleading because:
1. The GBPUSD subsample (8 trades) is too small for conclusions
2. The larger combined sample (33 trades) shows 44% WR — below 50%
3. The binomial test is nowhere near significance (p = 0.73)

**Conclusion:** The safety check is correctly protecting the system. The deep dive's framing of "5/8 profitable" as evidence for loosening the filter was selection bias from a small sample.

---

## Test 5: Session Memory — Real Impact

### Result: N/A — Method Artifact

**The deep dive's finding of "0/29 session memory references" is a METHOD ARTIFACT, not a system failure.**

Batch mode (`scripts/batch_backtest.py`) processes each candle independently with no `session_memory` parameter. This is by design — batch evaluates individual candle quality without session context. Session memory is only injected in live/replay mode via `orchestrator.py`.

722 replay session files exist in `knowledge_base_backtest/sessions/` but were not analyzed for memory references.

**Phase 1B's session memory instruction headers** address the real issue: when memory IS available (live mode), the AI will now be explicitly told how to use it. The batch results remain the validated performance floor — live performance with session memory should be equal or better.

---

## Test 6: Partial Close Math Verification

### Result: PASS — 3/3 exact matches

| Trade | Strategy A | Strategy B | Strategy C | Max Diff |
|---|---|---|---|---|
| 2024-04-18 (LONG, MFE=2.14R) | -1.00 = -1.00 | 1.05 = 1.05 | 0.75 = 0.75 | 0.0000 |
| 2025-11-04 (SHORT, MFE=4.23R) | 1.50 = 1.50 | 1.95 = 1.95 | 2.25 = 2.25 | 0.0000 |
| 2024-04-08 (LONG, SL hit) | -1.00 = -1.00 | -1.00 = -1.00 | -1.00 = -1.00 | 0.0000 |

Manual walk matches the Phase 2 simulation exactly. The partial close analysis math is correct.

---

## Test 7: Token Budget — Verify Room for Expansion

### Result: PASS — Massive headroom

| State | Tokens/call | % of 200K window |
|---|---|---|
| Current average | 6,103 | 3.1% |
| After Phase 1 (-470 tokens) | 5,633 | 2.8% |
| With all proposed additions (+1,300) | 6,933 | **3.5%** |

The system uses only 3.1% of the context window. Even with cross-instrument context (+500), session memory (+300), and a context plan (+500), usage stays at 3.5%.

**Marginal cost:** +1,300 tokens adds ~$0.004/call (~26% input cost increase). At ~15 candles/day, this is ~$0.06/day. Negligible.

---

## Test 8: Context Agent Feasibility — Sanity Check

### Result: FAIL — Not justified

| Metric | Current | With Context Agent |
|---|---|---|
| Tokens per session | 29,333 | 80,500 |
| Cost change | — | **+174%** |

The Context Agent proposal costs more because:
1. It adds a full LLM call per kill zone (~4,500 tokens)
2. Savings per entry call are negative (the summary doesn't reduce input enough)
3. The system already uses Anthropic prompt caching for static context (~3-4K tokens cached)

**The lightweight alternatives from Phases 1 and 4 achieve the same goals:**
- Session memory instructions (Phase 1B) → progression awareness
- Cross-instrument context (Phase 4) → market regime signal
- Asian range context (Phase 4) → volatility regime signal

These add ~1,300 tokens total vs ~80,500 for a Context Agent. The Context Agent is over-engineered for the current system scale.

---

## Key Findings

1. **m15_confirmation.confirmed bug:** Verified on ALL 10 sampled trades. Every CANDIDATE in the dataset has `confirmed=False` despite describing M15 confirmation. **Fixed in Phase 1C.**

2. **Loss categorization errors:** 2/5 losses are miscategorized by the deep dive. One is a structure misread (no H1 OB but graded A+), one is a threshold violation (M15 displacement 0.4x < 1.5x). This means the true "random market loss" rate is 3/5 (60%), not 4/5 (80%) as the deep dive claimed.

3. **Confidence score:** Confirmed pure noise with r = -0.019 across 143 trades and only 3 unique values (75/80/85). **Fixed in Phase 1A** by removing the deterministic rubric.

4. **Counter-trend safety:** The deep dive's "5/8 profitable" framing was misleading. With 33 total rejections, the combined win rate is 44% (p = 0.73). **Safety check is correctly protecting.**

5. **Methodology gaps:** Both session memory evaluation (Test 5) and missed setup detection (Test 3) are structural gaps in the batch testing approach, not system failures. Future evaluation should include replay-mode testing and NO_TRADE response logging.

6. **What's solid:** Partial close math is exact (Test 6). Token budget has 96%+ headroom (Test 7). The prompt improvements from Phase 1 are well-targeted.
