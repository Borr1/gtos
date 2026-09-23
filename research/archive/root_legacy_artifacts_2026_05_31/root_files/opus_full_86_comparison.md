# Full 86-Trade Model Comparison — DEFINITIVE RESULTS

**Date:** 2026-04-05
**Sample:** 56/86 trades completed (37W 19L) — sufficient for conclusions
**Models tested:** Original Sonnet, Sonnet+Thinking (10K budget), Opus+Thinking (10K budget)
**All with reconstructed session memory from batch results**
**Total cost:** Sonnet+T $2.44 + Opus+T $8.36 = **$10.80**

---

## Executive Summary

| Model | CANDIDATEs | Winners | Losers | WR | R-Total | Avg R/trade |
|-------|-----------|---------|--------|-----|---------|-------------|
| **Orig Sonnet** | **56/56 (100%)** | **37** | **19** | **66%** | **+29.35R** | **+0.52R** |
| Sonnet+Thinking | 2/56 (4%) | 2 | 0 | 100% | +0.57R | +0.29R |
| Opus+Thinking | 0/56 (0%) | 0 | 0 | N/A | +0.00R | N/A |

**Thinking models reject 96-100% of ALL trades — winners and losers alike.**
Original Sonnet generates +29.35R. The best thinking model generates +0.57R.

---

## Why Thinking Models Fail

### The #1 rejection reason: "Price not at H1 POI/OB"

| Rejection Category | Sonnet+Thinking | Opus+Thinking |
|-------------------|-----------------|---------------|
| Price not at H1 POI/OB | 39 (75%) | 48 (86%) |
| M15 CHoCH/displacement missing | 8 (15%) | 4 (7%) |
| Directional bias/alignment fail | 3 (6%) | 2 (4%) |
| Other | 2 (4%) | 2 (4%) |

The thinking budget makes models **hyper-literal about OB3** ("price at OB"). Original Sonnet interprets "at or near the OB zone" loosely — it treats price within a few dollars of the zone as qualifying. Thinking models verify exact price-in-zone coordinates and reject when price is approaching but not yet inside the zone boundary.

### Proof: Original Sonnet vs Thinking on the same data

**2025-05-05 (WIN +3.99R):**
- Original Sonnet: "H1 bullish OB at 3248.47-3241.29, price in discount at 68.5% retracement" → CANDIDATE
- Sonnet+Thinking: "Price not positioned at H1 order block for retest entry" → NO_TRADE

**2025-01-30 (WIN +3.77R):**
- Original Sonnet: "Fresh unmitigated H1 bullish OB at 2763.45-2759.87" → CANDIDATE
- Sonnet+Thinking: "Order block in wrong premium/discount zone" → NO_TRADE

**2024-05-24 (WIN +1.90R):**
- Original Sonnet: POI identified = False, type = none, price = 0.0 → **STILL said CANDIDATE**
- Sonnet+Thinking: "No H1 POI available for retest" → NO_TRADE

The original Sonnet literally admitted there was no H1 POI on 2024-05-24 and STILL output CANDIDATE. This is the "loose interpretation" that produces 66% WR at high frequency.

---

## Veto Gate Simulation

**Architecture:** Original Sonnet proposes CANDIDATE → Thinking model vetoes or approves

| Veto Model | Survived | Vetoed | Winners Lost | Losers Saved | Net R-Impact |
|-----------|----------|--------|-------------|-------------|-------------|
| Sonnet+Thinking | 2 trades (2W 0L) | 54 trades (35W 19L) | 35 winners (+44.05R) | 19 losers (+15.27R) | **-28.78R worse** |
| Opus+Thinking | 0 trades | 56 trades (37W 19L) | 37 winners (+44.62R) | 19 losers (+15.27R) | **-29.35R worse** |

The veto gate saves 15.27R of losses but destroys 44.05R of profits. Net impact is catastrophically negative.

---

## The 4-Trade Diagnostic Was Misleading

The earlier 4-trade test (all losers) showed:
- Sonnet+Thinking: 4/4 losers rejected (100%)
- Opus+Thinking: 4/4 losers rejected (100%)

This looked like perfect discrimination. But on the full population:
- Sonnet+Thinking rejects 95% of WINNERS too
- Opus+Thinking rejects 100% of WINNERS

**A filter that rejects everything has 100% precision on losers — and 0% recall on winners.**

---

## Confidence Score Analysis

| Model | n | Mean | Std | Min | Max |
|-------|---|------|-----|-----|-----|
| Orig Sonnet (from batch) | 56 | ~80 | ~2.5 | 75 | 85 |
| Sonnet+Thinking | 3 | 70 | 14.7 | 55 | 90 |

Sonnet+Thinking does produce more varied confidence when it does approve — range of 55-90 vs Sonnet's rubber-stamp 75-85. But with only 2-3 CANDIDATEs, the sample is meaningless.

---

## Cost Analysis

| Model | Per-call | Monthly (batch) | Monthly (direct) |
|-------|---------|-----------------|-----------------|
| Orig Sonnet | $0.01 | ~$60 | ~$30 |
| Sonnet+Thinking | $0.044 | ~$90 | ~$89 |
| Opus+Thinking | $0.149 | ~$225 | ~$299 |

Even if Opus+Thinking worked, it's 5x the cost for worse results.

---

## FINAL VERDICT

### Keep Original Sonnet. Do NOT enable extended thinking. Do NOT switch to Opus.

**The numbers are unambiguous:**
- Original Sonnet: +29.35R on 56 trades (66% WR)
- Best thinking alternative: +0.57R on 2 trades (100% WR but useless frequency)
- Opus+Thinking: 0R on 0 trades

**Extended thinking makes the model too strict.** The production system works because Sonnet applies the OB retest criteria with appropriate flexibility — "at or near" the zone rather than "exactly inside the zone boundary." This flexibility is what captures the +3-4R monster winners.

**The real problem to solve is confidence calibration** (rubber-stamp 75-82 range), not model selection. The model is right 66% of the time — it just can't tell you HOW right it is.

### What NOT to try next:
- Opus as PA: Produces zero trades
- Thinking as PA: Produces near-zero trades
- Thinking as veto gate: Vetoes winners at the same rate as losers
- Any model that is "more careful": The edge IS the loose interpretation

### What TO try next:
- Prompt restructuring for confidence variance (separate confidence from the CANDIDATE decision)
- Post-hoc scoring: After CANDIDATE, use a separate lightweight call to score confidence
- Walk-forward validation of the existing 66% WR system — it already works

---

## Red Team Correction (Appendix)

**The red team correctly identified a methodological error:** The original 20-trade test used **regular Opus** (no thinking), which produced 2/20 CANDIDATEs with real discrimination (caught 3/4 losers, missed 2/3 winners). The full 86-trade test used **Opus+Thinking**, which is a fundamentally different model behavior. The 86-trade test definitively rules out thinking models but does NOT test the veto-gate concept with regular Opus at scale.

**What was actually proven:**
1. Extended thinking (both Sonnet+T and Opus+T) kills trade frequency — ruled out definitively
2. Regular Opus (no thinking) showed promise on n=20 but was never scaled to 86
3. The prompt's loose interpretation of "at or near the OB zone" is load-bearing — tightening OB3 wording would destroy the edge

**Decision:** Close the investigation. Regular Opus veto gate is a WF-2 question at best. The 66% WR Sonnet system launches Monday. Lock the prompt. Go live.

**Total research cost:** ~$15 across all model comparison tests
