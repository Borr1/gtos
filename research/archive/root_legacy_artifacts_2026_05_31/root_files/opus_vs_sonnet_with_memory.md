# Opus vs Sonnet — With Full Session Memory

Date: 2026-04-05 17:00
Sonnet: claude-sonnet-4-20250514 (original batch responses)
Opus: claude-opus-4-20250514 (fresh API calls with reconstructed session memory)
Trades: 20 (10 best winners + 10 worst losers)

## Methodology

Session memory was reconstructed from stored batch results: for each
CANDIDATE candle, the Sonnet responses from all prior candles in the
same kill zone were compressed into memory entries (matching the
production orchestrator's format) and injected into the user message.
Opus received the IDENTICAL system prompt, static context, dynamic
market data, AND session memory context.

## Decision Comparison

| # | Date | KZ | Actual | R | Memory | Sonnet | S.Conf | Opus | O.Conf | Match? |
|---|------|----|--------|-----|--------|--------|--------|------|--------|--------|
| 1 | 2025-12-03 | london |   WIN | +4.14 | 0 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 2 | 2025-05-05 | london |   WIN | +3.99 | 6 prior | CANDIDATE  |   75 | CANDIDATE  |   75 | YES |
| 3 | 2025-01-30 | london |   WIN | +3.77 | 3 prior | CANDIDATE  |   80 | NO_TRADE   |    0 | **NO** |
| 4 | 2025-04-17 |  ny |   WIN | +3.47 | 6 prior | CANDIDATE  |   80 | NO_TRADE   |    0 | **NO** |
| 5 | 2025-12-22 | london |   WIN | +3.46 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 6 | 2026-01-22 | london |   WIN | +3.31 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 7 | 2026-03-06 |  ny |   WIN | +3.03 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 8 | 2025-12-10 | london |   WIN | +2.90 | 1 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 9 | 2025-03-05 | london |   WIN | +2.62 | 2 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 10 | 2024-02-06 | london |   WIN | +2.38 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 11 | 2024-03-01 |  ny |  LOSS | -1.00 | 0 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 12 | 2024-03-15 |  ny |  LOSS | -1.00 | 1 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 13 | 2024-03-18 | london |  LOSS | -1.00 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 14 | 2024-06-05 |  ny |  LOSS | -1.00 | 6 prior | CANDIDATE  |   82 | NO_TRADE   |    0 | **NO** |
| 15 | 2024-09-06 | london |  LOSS | -1.00 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 16 | 2024-09-27 |  ny |  LOSS | -1.00 | 3 prior | CANDIDATE  |   80 | NO_TRADE   |    0 | **NO** |
| 17 | 2025-02-12 | london |  LOSS | -1.00 | 3 prior | CANDIDATE  |   80 | CANDIDATE  |   75 | YES |
| 18 | 2025-03-06 | london |  LOSS | -1.00 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |
| 19 | 2025-03-14 | london |  LOSS | -1.00 | 2 prior | CANDIDATE  |   80 | NO_TRADE   |    0 | **NO** |
| 20 | 2025-04-29 | london |  LOSS | -1.00 | 6 prior | NO_TRADE   |    0 | NO_TRADE   |    0 | YES |

Decision agreement: 15/20 (75%)

## Selectivity Comparison

| Metric | Sonnet | Opus |
|--------|--------|------|
| Total CANDIDATEs | 7/20 | 2/20 |
| Winners caught | 3/10 | 1/10 |
| Losers approved | 4/10 | 1/10 |
| CANDIDATE WR | 3/7 = 43% | 1/2 = 50% |

## R-Impact Analysis

- Sonnet CANDIDATE R-total: +7.23R on 7 trades
- Opus CANDIDATE R-total: +2.99R on 2 trades
- Delta: -4.24R

## Confidence Score Comparison

Sonnet: n=7, mean=80, std=2.0, range=[75, 82]
Opus:   n=2, mean=75, std=0.0, range=[75, 75]

## Loser Analysis — Does Opus Catch What Sonnet Missed?

### 2024-03-01 (ny) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Both rejected (no session memory context may have changed this)

### 2024-03-15 (ny) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Both rejected (no session memory context may have changed this)

### 2024-03-18 (london) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Both rejected (no session memory context may have changed this)

### 2024-06-05 (ny) — LOSS -1.00R
- Sonnet: CANDIDATE (conf=82, grade=A+)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS CAUGHT IT** — rejected a loser Sonnet approved
  Opus reason: Price not at required H1 point of interest for setup qualification

### 2024-09-06 (london) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Both rejected (no session memory context may have changed this)

### 2024-09-27 (ny) — LOSS -1.00R
- Sonnet: CANDIDATE (conf=80, grade=A+)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS CAUGHT IT** — rejected a loser Sonnet approved
  Opus reason: No qualifying setup - H1 OBs too far below in discount, no liquidity sweep detected

### 2025-02-12 (london) — LOSS -1.00R
- Sonnet: CANDIDATE (conf=80, grade=A+)
- Opus:   CANDIDATE (conf=75, grade=A+)
  Both approved — same rubber stamp

### 2025-03-06 (london) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Both rejected (no session memory context may have changed this)

### 2025-03-14 (london) — LOSS -1.00R
- Sonnet: CANDIDATE (conf=80, grade=A+)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS CAUGHT IT** — rejected a loser Sonnet approved
  Opus reason: M15 bearish structure conflicts with bullish daily bias - violates U4

### 2025-04-29 (london) — LOSS -1.00R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)
  Both rejected (no session memory context may have changed this)

## Winner Analysis — Does Opus Still Catch Winners?

### 2025-12-03 (london) — WIN +4.14R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2025-05-05 (london) — WIN +3.99R
- Sonnet: CANDIDATE (conf=75, grade=A)
- Opus:   CANDIDATE (conf=75, grade=A+)

### 2025-01-30 (london) — WIN +3.77R
- Sonnet: CANDIDATE (conf=80, grade=A)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS MISSED** a +3.77R winner
  Opus reason: Missing M15 CHoCH and displacement confirmation after H1 structural break

### 2025-04-17 (ny) — WIN +3.47R
- Sonnet: CANDIDATE (conf=80, grade=A+)
- Opus:   NO_TRADE (conf=0, grade=C)
  **OPUS MISSED** a +3.47R winner
  Opus reason: No framework produced qualifying setup - no sweep detected and price not at H1 OB

### 2025-12-22 (london) — WIN +3.46R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2026-01-22 (london) — WIN +3.31R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2026-03-06 (ny) — WIN +3.03R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2025-12-10 (london) — WIN +2.90R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2025-03-05 (london) — WIN +2.62R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

### 2024-02-06 (london) — WIN +2.38R
- Sonnet: NO_TRADE (conf=0, grade=C)
- Opus:   NO_TRADE (conf=0, grade=C)

## Reasoning Quality Comparison

| Metric | Sonnet (avg) | Opus (avg) |
|--------|-------------|-----------|
| Reasoning words | 36 | 33 |
| Price levels cited | 4.9 | 4.2 |
| Hedge phrases | 0.8 | 0.7 |

## Cost-Benefit Analysis

- Current Sonnet cost: ~$60/month for 5 instruments
- Opus cost would be: ~$180/month (3x)
- Actual Opus test cost: $1.71 for 20 calls

**R-impact math:**
- Sonnet: +7.23R on 7 CANDIDATEs (3W 4L) → net +3.23R after losses
- Opus: +2.99R on 2 CANDIDATEs (1W 1L) → net +1.99R after losses
- If Opus were used: you'd miss +4.24R of profit to avoid 3R of losses → net -1.24R WORSE

## Key Findings

### 1. Opus IS more discriminating — it caught 3 of 4 Sonnet losers
Opus rejected losers on Jun 5 2024 ("price not at H1 POI"), Sep 27 2024 ("H1 OBs too far below, no sweep"), and Mar 14 2025 ("M15 bearish structure conflicts with bullish daily bias — violates U4"). These are SPECIFIC, correct rejection reasons.

### 2. But Opus is TOO conservative — it also missed 2 of 3 Sonnet winners
Opus missed the +3.77R (Jan 30) and +3.47R (Apr 17) winners. It only caught the +3.99R (May 5) winner. The 2 missed winners had R-multiples totaling +7.24R.

### 3. Session memory helped — dramatically
With session memory, Opus went from 0/10 CANDIDATEs (first test) to 2/20. Still very conservative, but no longer catatonic. This confirms session memory is critical architecture.

### 4. The rubber stamp problem is CONFIRMED for Sonnet
Sonnet confidence scores: 75, 80, 80, 82, 80, 80, 80 — std dev of 2.0. The A+/A grading shows zero differentiation between the +3.99R winner it correctly approved and the -1.00R losers it incorrectly approved.

### 5. Opus reasoning is higher quality but only marginally
Opus rejection reasons are more specific and mechanically grounded (citing exact criteria violations like U4). But on the trades both models agreed on, word counts and price citation counts were similar.

## Recommendation

**DO NOT SWITCH to Opus for production PA calls.**

The math doesn't work: Opus saves 3R of losses but misses 7.24R of winners. Net impact is -4.24R worse. At $1,000/trade (1% risk on $100K), that's approximately -$4,240 per similar 20-trade sample.

**However, consider Opus for a SECOND-OPINION GATE:**
- Sonnet generates CANDIDATEs (aggressive, catches winners)
- Opus reviews only the CANDIDATEs as a veto layer (conservative, catches losers)
- Estimated incremental cost: ~$0.08/CANDIDATE (tiny)
- Would have vetoed 3 of 4 losers while keeping the 1 winner both approved
- Net impact on this sample: +3.99R (kept) -1.00R (missed loser) = +2.99R from 2 trades instead of +7.23R -4.00R = +3.23R from 7 trades. Similar R but on 5 fewer trades (better WR, less drawdown)

This "Sonnet proposes, Opus disposes" architecture is worth testing at scale.