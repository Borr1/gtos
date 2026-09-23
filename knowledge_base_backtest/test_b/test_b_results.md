# Test B Results — Prompt-Neutral Experiment

Date: 2026-04-05 08:18
Model: claude-sonnet-4-20250514
Trades: 30 (15W + 15L)


## Production vs Neutral Prompt Differences

REMOVED in neutral:
1. Identity framing: "institutional gold trader with 15+ years of experience trading XAUUSD"
   → Replaced with: "market analysis system"
2. Quality signal: "Displacement creating an FVG: ~11% higher continuation rates"
3. Quality signal: "Displacement at a pre-existing OB zone: ~5% lower probability"
4. Quality signal: "Impulse compactness: 7 or fewer candles ~85% vs 8+ candles ~55%"
5. Self-check step: "Am I forcing this because no trade has been found?"
   "Is displacement genuinely strong or am I rationalizing?"
   "Would a skeptical, experienced institutional trader agree?"
6. Reasoning Quality Signals: "Reference 8+ distinct price levels (+17pp)"
   "Avoid hedging phrases (+13pp)"
7. Confidence scoring anchoring language removed
8. BOS/CHoCH strength commentary ("BOS provides stronger confirmation")

KEPT identical:
- U1-U7 mechanical requirements
- OB1-OB7 criteria
- BR1-BR7 criteria
- Output JSON schema
- Anti-hallucination guardrails
- Internal consistency rules
- Conciseness rules
- Setup grading thresholds (A+, A, B+)
- TP1 = 1.5x SL rule
- SL >= 1.5x ATR + $5 minimum


## Decision Comparison

| Date | KZ | Outcome | Arm A Decision | Arm B Decision | Flipped? |
|------|-----|---------|---------------|---------------|----------|
| 2024-01-25 | london |   WIN | CANDIDATE     | CANDIDATE     |  |
| 2024-03-01 |  ny |  LOSS | NO_TRADE      | CANDIDATE     | YES |
| 2024-03-15 |  ny |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2024-04-01 | london |  LOSS | CANDIDATE     | NO_TRADE      | YES |
| 2024-04-02 | london |   WIN | CANDIDATE     | NO_TRADE      | YES |
| 2024-05-31 |  ny |   WIN | NO_TRADE      | CANDIDATE     | YES |
| 2024-06-05 |  ny |  LOSS | CANDIDATE     | CANDIDATE     |  |
| 2024-07-31 |  ny |   WIN | NO_TRADE      | NO_TRADE      |  |
| 2024-09-27 |  ny |  LOSS | CANDIDATE     | CANDIDATE     |  |
| 2025-01-30 | london |   WIN | CANDIDATE     | NO_TRADE      | YES |
| 2025-02-10 | london |   WIN | CANDIDATE     | NO_TRADE      | YES |
| 2025-02-12 | london |  LOSS | CANDIDATE     | CANDIDATE     |  |
| 2025-03-04 | london |   WIN | NO_TRADE      | NO_TRADE      |  |
| 2025-03-06 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2025-03-11 | london |   WIN | CANDIDATE     | CANDIDATE     |  |
| 2025-04-04 |  ny |   WIN | CANDIDATE     | CANDIDATE     |  |
| 2025-04-29 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2025-05-06 |  ny |   WIN | NO_TRADE      | NO_TRADE      |  |
| 2025-06-12 |  ny |   WIN | CANDIDATE     | CANDIDATE     |  |
| 2025-09-22 |  ny |  LOSS | CANDIDATE     | NO_TRADE      | YES |
| 2025-09-23 |  ny |   WIN | CANDIDATE     | CANDIDATE     |  |
| 2025-10-09 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2025-10-20 |  ny |   WIN | NO_TRADE      | NO_TRADE      |  |
| 2025-12-03 | london |   WIN | NO_TRADE      | NO_TRADE      |  |
| 2025-12-12 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2025-12-17 | london |   WIN | NO_TRADE      | NO_TRADE      |  |
| 2025-12-19 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2026-01-07 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2026-01-21 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |
| 2026-03-12 | london |  LOSS | NO_TRADE      | NO_TRADE      |  |

## Summary Statistics

- Total valid comparisons: 30
- Arm A CANDIDATE count: 13
- Arm B CANDIDATE count: 10
- Total decision flips: 7
- Flip rate: 23.3%

## Flipped Trades Detail

- Winner flips: 4
- Loser flips:  3

  BAD: 2024-03-01 — Production avoided LOSS, neutral took it
  GOOD: 2024-04-01 — Production took LOSS, neutral avoided it
  BAD: 2024-04-02 — Production caught WIN, neutral missed it
  GOOD: 2024-05-31 — Production missed WIN, neutral caught it
  BAD: 2025-01-30 — Production caught WIN, neutral missed it
  BAD: 2025-02-10 — Production caught WIN, neutral missed it
  GOOD: 2025-09-22 — Production took LOSS, neutral avoided it

- Good flips (neutral better): 3
- Bad flips (production better): 4

## Non-Determinism Check (Arm A)

Arm A uses the production prompt — same prompt that generated the original
batch decisions. Any Arm A decision that differs from the original batch
result represents LLM non-determinism (expected with temperature=0).

  Non-determinism: 2024-03-01 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2024-03-15 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2024-05-31 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2024-07-31 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-03-04 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-03-06 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-04-29 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-05-06 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-10-09 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-10-20 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-12-03 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-12-12 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-12-17 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2025-12-19 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2026-01-07 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2026-01-21 — Original=CANDIDATE, Arm A re-run=NO_TRADE
  Non-determinism: 2026-03-12 — Original=CANDIDATE, Arm A re-run=NO_TRADE

- Arm A non-determinism rate: 17/30 (56.7%)

## Interpretation Guide

- If Arm B flip rate ~ Arm A non-determinism rate: Prompt framing has NO effect
- If Arm B flip rate >> non-determinism rate: Prompt framing matters
- If flips disproportionately affect losers: Neutral prompt may be more selective
- If flips disproportionately affect winners: Production prompt has better signal