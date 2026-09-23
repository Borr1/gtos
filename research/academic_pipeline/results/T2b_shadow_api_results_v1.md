# T2b Shadow API Experiment Results

**Date:** 2026-04-11
**Model:** claude-sonnet-4-20250514
**N MSOs (all experiments):** 121
**N MSOs (memory experiments 1-2):** 66
**Total API cost:** $31.44
**Bonferroni threshold:** p < 0.01 (5 tests)

---

## Overview

**Context from T2a:** Outcomes within the CANDIDATE pool are unpredictable (AUC≈0.5).
The CANDIDATE gate is a deterministic rules check (setup_grade explains 97%).
**Primary optimization target = CANDIDATE rate.** WR differences < 5pp are noise.

---

## Experiment 1: Session Memory Label Scrambling (H-3.3a)

**Hypothesis:** Scrambled labels preserve >80% of memory benefit (distributional priming).

**Sample:** n=66 MSOs with ≥3 prior candles

| Condition | CANDIDATE Rate | WR (matched) | Mean Conf |
|-----------|---------------|-------------|-----------|
| A — real memory | 27.3% (n=18) | 50.0% | 22.1 |
| B — scrambled labels | 27.3% (n=18) | 55.6% | 22.1 |
| C — no memory | 50.0% (n=33) | 63.6% | 39.9 |

**A vs B chi²:** p=1.0000 (p=1.0000)
**A vs C chi²:** p=0.0073 ✓ (p<0.01)

**Frequency multiplier (B/A):** 1.000
**Monthly trade delta:** +0.0 trades/month
**Net R/month impact:** +0.00R

**Decision gate outcome:**
B within 20% of A (diff=0%): **DISTRIBUTIONAL PRIMING CONFIRMED.** Session memory works via format/regime inference, not label content.

---

## Experiment 2: Majority Label Bias (H-3.5a)

**Hypothesis:** Mixed priors (2 CANDIDATE + 3 NO_TRADE) produce >5pp higher CANDIDATE rate than all-NO_TRADE.

**Sample:** n=66

| Condition | CANDIDATE Rate | WR (matched) |
|-----------|---------------|-------------|
| A — all NO_TRADE priors | 30.3% (n=20) | 50.0% |
| B — mixed priors (2 CAND + 3 NT) | 34.8% (n=23) | 60.9% |

**Chi² A vs B:** p=0.5774 (p=0.5774)
**McNemar A vs B:** b=4, c=7, p=0.5488

**Frequency multiplier (B/A):** 1.150
**Monthly trade delta:** +2.6 trades/month
**Net R/month impact:** +1.59R

**Decision gate outcome:**
**INCONCLUSIVE.** Diff=+4.5pp but not significant at Bonferroni threshold.

---

## Experiment 3: CoT Overthinking (H-9.1a)

**Hypothesis:** Simplified binary prompt achieves ≥60% WR, comparable to full CoT prompt.

**Sample:** n=121
**Agreement rate (A=B):** 53.7%

| Condition | CANDIDATE Rate | WR (matched) |
|-----------|---------------|-------------|
| A — full CoT prompt | 46.3% (n=56) | 66.1% |
| B — simplified binary prompt | 0.0% (n=0) | n/a |

**Chi² A vs B:** p=n/a
**Disagreements:** 56 (46.3%)

**Decision gate outcome:**
Full CoT adds measurable value (WR diff=66.1%). Keep current prompt.

---

## Experiment 4: SMC vs Neutral Framing (H-3.2a)

**Hypothesis:** Neutral framing produces CANDIDATE decisions that align better with actual outcomes.

**Sample:** n=121
**Agreement rate (A=B):** 80.2%

| Condition | CANDIDATE Rate | WR (matched) |
|-----------|---------------|-------------|
| A — SMC framing (original) | 48.8% (n=59) | 66.1% |
| B — neutral statistical framing | 37.2% (n=45) | 66.7% |

**Chi² A vs B:** p=0.0691 (p=0.0691)
**Disagreements (A=CAND, B=NT):** 19 WR=63.2%
**Disagreements (A=NT, B=CAND):** 5 WR=60.0%

**Frequency multiplier (B/A):** 0.763
**Monthly trade delta:** -4.0 trades/month
**Net R/month impact:** -2.52R

**Decision gate outcome:**
Framing does not affect WR (diff=+0.6%). Choose based on token cost.

---

## Experiment 5: 3-Run Self-Consistency (H-3.6a)

**Hypothesis:** Unanimous 3/3 CANDIDATE has WR>70%; split 2/3 has WR<60%.

**Sample:** n=121

| Agreement Category | Count | % |
|-------------------|-------|---|
| Unanimous CANDIDATE (3/3) | 47 | 38.8% |
| Majority CANDIDATE (2/3) | 11 | 9.1% |
| Majority NO_TRADE (1/3) | 6 | 5.0% |
| Unanimous NO_TRADE (0/3) | 57 | 47.1% |

**Overall agreement rate (unanimous):** 86.0%

| Group | WR | N |
|-------|-----|---|
| Unanimous CANDIDATE | 63.8% | 47 |
| Majority CANDIDATE | 81.8% | 11 |

**Single-run CANDIDATE rate:** 49.6%
**Majority-vote CANDIDATE rate:** 47.9%

**Parameter variance (std across 3 runs):** entry=1.063550, SL=5.050884

**Decision gate outcome:**
Agreement=86.0% (80-90%). Meaningful diversity exists. Adaptive 2-3 run approach (Aggarwal 2023) is worth implementing.

---

## Phase 6: Combined Architecture Recommendation

### The Memory Story (Exp 1 + 2)

- Exp1: Scrambled labels produced 0% change in CANDIDATE rate vs real labels.
  → Memory mechanism is primarily distributional priming.
- Exp2: Mixed priors (+4.5pp vs all-NO_TRADE).
  → Majority label bias not confirmed as driver.

### The Prompt Story (Exp 3 + 4)

- CoT depth (Exp3): Simplified prompt CANDIDATE rate 0.0% vs full 46.3%.
  → Full CoT preferred.
- SMC framing (Exp4): Neutral CANDIDATE rate 37.2% vs SMC 48.8%.
  WR diff: +0.6%.
  → SMC framing neutral or better.

### The Ensemble Story (Exp 5)

- Agreement rate: 86.0%.
- Single-run sufficient (low gain from ensemble).

### Optimal Component 3A Configuration

| Dimension | Current | Recommendation | Evidence |
|-----------|---------|---------------|---------|
| Prompt | Full SMC CoT | Keep full CoT | Exp3 + Exp4 |
| Memory | None (live)/Real (batch) | Current design | Exp1 + Exp2 |
| Evaluation | Single-run temp=0 | Adaptive 2-3 run (Aggarwal 2023) | Exp5 |
| Confidence | Current 50-95 score | Remove confidence score (use agreement rate if running 2-3x) | T2a + Exp5 |

### Frequency Impact Summary

| Experiment | Condition | CR Control | CR Experimental | Freq Mult | ΔTrades/mo | ΔR/mo |
|------------|-----------|-----------|----------------|-----------|-----------|-------|
| Exp1 (memory vs none) | — | 27.3% | 50.0% | 1.833 | +14.2 | +8.85 |
| Exp2 (mixed vs all-NT) | — | 30.3% | 34.8% | 1.150 | +2.6 | +1.59 |
| Exp3 (simplified vs full) | — | 46.3% | 0.0% | 0.000 | -17.0 | -10.63 |
| Exp4 (neutral vs SMC) | — | 48.8% | 37.2% | 0.763 | -4.0 | -2.52 |

### Interaction with T2a and T3

- **T2a:** CANDIDATE gate is deterministic (rules check). LLM adds zone detection + spatial reasoning.
- **T2b:** Tests whether prompt/memory configuration affects pool SIZE (how many CANDIDATEs).
- **T3:** Tests whether feature thresholds (fib depth, structural density) can sub-segment the pool.
- Together: T3 says which trades to take; T2b says how many trades the system generates.

---

*Generated by T2b_shadow_api_experiments.py | Total cost: $31.44 of $100.0 budget*