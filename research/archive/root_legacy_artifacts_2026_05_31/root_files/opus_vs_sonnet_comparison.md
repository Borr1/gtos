# Opus vs Sonnet Model Comparison

Date: 2026-04-05 16:37
Sonnet: claude-sonnet-4-20250514
Opus: claude-opus-4-20250514
Trades: 10 (5 best winners + 5 worst losers)
Prompt: Identical production prompt, no session memory

## Decision Summary

| # | Date | KZ | Actual | R | Sonnet Dec | Opus Dec | Match? |
|---|------|-----|--------|-----|-----------|---------|--------|
| 1 | 2025-12-03 | london | WIN | +4.14 | NO_TRADE | NO_TRADE | YES |
| 2 | 2025-05-05 | london | WIN | +3.99 | CANDIDATE | NO_TRADE | **NO** |
| 3 | 2025-01-30 | london | WIN | +3.77 | CANDIDATE | NO_TRADE | **NO** |
| 4 | 2025-04-17 | ny | WIN | +3.47 | CANDIDATE | NO_TRADE | **NO** |
| 5 | 2025-12-22 | london | WIN | +3.46 | NO_TRADE | NO_TRADE | YES |
| 6 | 2024-03-01 | ny | LOSS | -1.00 | NO_TRADE | NO_TRADE | YES |
| 7 | 2024-03-15 | ny | LOSS | -1.00 | NO_TRADE | NO_TRADE | YES |
| 8 | 2024-03-18 | london | LOSS | -1.00 | NO_TRADE | NO_TRADE | YES |
| 9 | 2024-06-05 | ny | LOSS | -1.00 | CANDIDATE | NO_TRADE | **NO** |
| 10 | 2024-09-06 | london | LOSS | -1.00 | NO_TRADE | NO_TRADE | YES |

Decision agreement: 6/10 (60%)

## Detailed Metrics

| # | Date | Outcome | Model | Decision | Conf | Grade | Words | Prices | Hedges |
|---|------|---------|-------|----------|------|-------|-------|--------|--------|
| 1 | 2025-12-03 |   WIN | Sonnet | NO_TRADE   |    0 | C   |    32 |      0 |      0 |
| | | | Opus | NO_TRADE   |    0 | C   |    32 |      0 |      0 |
| 2 | 2025-05-05 |   WIN | Sonnet | CANDIDATE  |   75 | A   |    29 |     12 |      0 |
| | | | Opus | NO_TRADE   |    0 | C   |    26 |      1 |      0 |
| 3 | 2025-01-30 |   WIN | Sonnet | CANDIDATE  |   80 | A   |    28 |     11 |      1 |
| | | | Opus | NO_TRADE   |    0 | C   |    39 |     10 |      0 |
| 4 | 2025-04-17 |   WIN | Sonnet | CANDIDATE  |   80 | A+  |    27 |     13 |      0 |
| | | | Opus | NO_TRADE   |    0 | C   |    31 |      9 |      0 |
| 5 | 2025-12-22 |   WIN | Sonnet | NO_TRADE   |    0 | C   |    28 |      7 |      1 |
| | | | Opus | NO_TRADE   |    0 | C   |    34 |      8 |      0 |
| 6 | 2024-03-01 |  LOSS | Sonnet | NO_TRADE   |    0 | C   |    36 |      0 |      1 |
| | | | Opus | NO_TRADE   |    0 | C   |    32 |      0 |      1 |
| 7 | 2024-03-15 |  LOSS | Sonnet | NO_TRADE   |    0 | C   |    43 |      0 |      0 |
| | | | Opus | NO_TRADE   |    0 | C   |    30 |      0 |      0 |
| 8 | 2024-03-18 |  LOSS | Sonnet | NO_TRADE   |    0 | C   |    47 |      0 |      0 |
| | | | Opus | NO_TRADE   |    0 | C   |    38 |      0 |      0 |
| 9 | 2024-06-05 |  LOSS | Sonnet | CANDIDATE  |   82 | A+  |    37 |      0 |      1 |
| | | | Opus | NO_TRADE   |    0 | C   |    35 |      0 |      0 |
| 10 | 2024-09-06 |  LOSS | Sonnet | NO_TRADE   |    0 | C   |    55 |      0 |      0 |
| | | | Opus | NO_TRADE   |    0 | C   |    41 |      0 |      0 |

## Aggregate Statistics

**Sonnet:**
- CANDIDATEs: 4/10
- Confidence: mean=79, min=75, max=82, std=2.6
- Reasoning words: mean=36, range=[27, 55]
- Price levels cited: mean=4.3
- Hedge phrases: mean=0.4

**Opus:**
- CANDIDATEs: 0/10
- Reasoning words: mean=34, range=[26, 41]
- Price levels cited: mean=2.8
- Hedge phrases: mean=0.1

## Key Question: Does Opus Catch the Losers?

### 2024-03-01 (ny) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Same decision

### 2024-03-15 (ny) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Same decision

### 2024-03-18 (london) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Same decision

### 2024-06-05 (ny) — LOSS -1.00R
- Sonnet: CANDIDATE (conf=82, grade=A+)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS CAUGHT IT** — rejected a loser that Sonnet approved
  Opus reason: No H1 POI retest occurred; price remains above all unmitigated order blocks

### 2024-09-06 (london) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Same decision

## Does Opus Miss Winners?

### 2025-12-03 (london) — WIN +4.14R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2025-05-05 (london) — WIN +3.99R
- Sonnet: CANDIDATE (conf=75, grade=A)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS MISSED** a +3.99R winner

### 2025-01-30 (london) — WIN +3.77R
- Sonnet: CANDIDATE (conf=80, grade=A)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS MISSED** a +3.77R winner

### 2025-04-17 (ny) — WIN +3.47R
- Sonnet: CANDIDATE (conf=80, grade=A+)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS MISSED** a +3.47R winner

### 2025-12-22 (london) — WIN +3.46R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

## Interpretation

| Metric | Sonnet | Opus |
|--------|--------|------|
| Total CANDIDATEs | 4 | 0 |
| CANDIDATE WR | 3/4 = 75% | 0/0 = 0% |
| Winners caught | 3/5 | 0/5 |
| Losers approved | 1/5 | 0/5 |


Confidence variance: Sonnet std=2.6, Opus std=0.0
→ Opus produced ZERO CANDIDATEs, so no confidence scores to compare. Sonnet's confidence range (75-82) is extremely narrow — the "rubber stamp" problem is confirmed even on this small sample.

## R-Impact Analysis

Sonnet CANDIDATEs on these 10 trades:
- 2025-05-05: WIN +3.99R ✓
- 2025-01-30: WIN +3.77R ✓
- 2025-04-17: WIN +3.47R ✓
- 2024-06-05: LOSS -1.00R ✗

Sonnet net: +3.99 + 3.77 + 3.47 - 1.00 = **+10.23R** on 4 trades (75% WR)
Opus net: **0R** on 0 trades (took nothing)

If Opus had been used, we'd have missed +10.23R of pure profit to avoid 1R of loss. The trade-off is catastrophic.

## Recommendation

**DO NOT SWITCH TO OPUS.**

Opus is not "better calibrated" — it's **catatonic**. Zero CANDIDATEs out of 10 trades means it won't trade at all without session memory. This is likely because:

1. **Session memory dependence**: These are single-candle evaluations without prior candle context. Opus appears to require even MORE context than Sonnet to commit to a CANDIDATE decision.
2. **Opus is hyper-conservative**: Every single Opus response was NO_TRADE with grade C. It didn't produce nuanced grades or varied confidence — it just rejected everything.
3. **One bright spot**: Opus correctly rejected the Jun 5 2024 loser that Sonnet graded A+ at confidence 82. Opus's reason was precise: "No H1 POI retest occurred; price remains above all unmitigated order blocks." This suggests Opus IS more thorough in checking criteria — but too thorough to ever approve anything in isolation.

**The real finding**: The problem is NOT the model — it's the session memory architecture. Both models become dramatically more conservative without session memory context. Sonnet retains enough aggression to catch winners (3/5); Opus loses it completely (0/5). The value is in the session memory pipeline, not in switching models.

**Cost saved**: $0/month (no switch needed)

## Batch IDs
- Sonnet: extracted from output
- Opus: `msgbatch_011aK4Aq1Lhpd8A4krT2QbYs`