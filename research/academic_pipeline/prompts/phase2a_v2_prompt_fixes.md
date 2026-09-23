# Phase 2A-v2: Evidence-Based Prompt Fixes
## Date: 2026-04-12
## Basis: Deep-dive analysis of P2A-3 (S4.6 max) results — 121 trades, all Q-scores, grade/confidence distributions
## Budget: ~$4 (1 test × 121 trades × ~$0.035/call)

---

## OVERVIEW

Phase 2A (P2A-3) achieved CR=38.0%, WR=69.6%, CR*WR=0.265 with Sonnet 4.6 max. Deep analysis of the 46 CANDIDATE trades and 46 lost winning trades revealed 4 specific issues in the prompt scoring that can be fixed with clear statistical evidence. This test applies those fixes and measures the impact.

**Hypothesis (stated BEFORE seeing results):** The 4 fixes will maintain WR >= 65% and may increase CR slightly (from the Q4 and London calibration effects). Primary goal is to remove counter-productive scoring signals, not to dramatically shift CR.

---

## CHANGES (4 total, all evidence-backed)

### Fix A — Q4 Scoring (Counter-Predictive)
**Evidence:** Among P2A-3 CANDIDATEs, Q4=10 (discount zone) had 57.1% WR while Q4=5 (equilibrium) had 75.0% WR (+18pp). The premium/discount reward actively penalizes better-performing trades.
**Before:** Correct side = 10 points, equilibrium = 5 points, wrong side = 0
**After:** Correct side OR equilibrium = 5 points, wrong side = 0
**Max score:** 100 → 95
**Threshold:** Stays at 65 (bimodal distribution means no trades scored 60-69, so a 5-point shift has no boundary effect)

### Fix B — Confidence Mapping (Signal Destruction)
**Evidence:** Raw scores range 65-95 but collapse to only 3 confidence values: 73(14), 78(31), 81(1). The 73→78 jump carries +6.7pp WR signal that is being wasted.
**Before:** Banded mapping (65-74→65-72, 75-84→73-80, 85+→81-90)
**After:** `confidence = score` (direct mapping)
**Risk:** Zero — confidence does not gate trade decisions in the current system

### Fix C — Grade Determinism (Post-Hoc Overrides)
**Evidence:** Two B-grade CANDIDATEs had raw scores of 90 (identical to most A-grades) but were subjectively downgraded. Both won — one returned +3.31R (second-best trade in dataset). Raw score 95 was also downgraded to B+ on one trade.
**Before:** "Map score to grade for backward compatibility" (model overrides freely)
**After:** "Grade is determined solely by score. Do not override the grade based on qualitative reasoning."
**Risk:** Low — grading doesn't gate decisions, but noisy grades confuse downstream analysis

### Fix D — London Session Calibration
**Evidence:** London discrimination is only +3.5pp (CAND WR 76.5% vs rejected WR 73.0%). London NO_TRADE lost-win rate is 74.3% — nearly 3 of 4 rejections are actual winners. NY discrimination is +14.1pp (model adds real value there). London CAND rate is 31.5% vs NY 45.3%.
**Before:** No session-specific calibration
**After:** One line added to CALIBRATION section acknowledging London's higher base rate
**Risk:** Low — calibration note, not a structural change

---

## WHAT DID NOT CHANGE
- All critical requirements (C1, C2, C3) — identical
- Q1-Q3, Q5-Q7 scoring — identical
- Bonus factors — identical
- Zone freshness rule — identical
- Breaker block framework — identical
- Decision thresholds (65/45) — identical
- Output schema — identical
- Data grounding / anti-hallucination rules — identical
- Token limits — identical
- Internal consistency rules — identical
- Session memory in user messages — present (Phase 2C will test removal separately)

---

## PRE-COMMITTED DECISION GATES

| CR*WR vs P2A-3 (0.265) | WR | Action |
|-------------------------|-----|--------|
| Higher + WR >= 65% | Pass | Use v2 prompt as base for Phase 2C |
| Similar (±0.02) + WR >= 65% | Pass | Use v2 prompt (fixes are structurally correct even if no metric shift) |
| Lower + WR >= 65% | Investigate | Check which fix caused regression |
| Any + WR < 60% | Fail | Revert to P2A-3 prompt, investigate what broke |

---

## TEST CONFIGURATION

| Parameter | Value |
|-----------|-------|
| Model | claude-sonnet-4-6 |
| Effort | max |
| max_tokens | 2000 |
| Temperature | 0 |
| System prompt | Phase 2A-v2 (fixes A-D applied) |
| User messages | Same 121 MSOs, unchanged (including session memory) |
| Test name | P2A_v2_s46_max |
