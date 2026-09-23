# Confidence Decomposition Test — Real MSO Results

## Setup

- 5 trades from primary XAUUSD batch (2 winners, 2 losers, 1 marginal)
- Each MSO scored TWICE through a 2-dimension rubric (Structural × Contextual)
- Model: claude-sonnet-4-20250514
- Confidence = (Structural + Contextual) × 10

## Selected Trades

| Label | Date | KZ | Outcome | R-Multiple |
|---|---|---|---|---|
| winner1 | 2025-01-30 | london | WIN | +3.77R |
| winner2 | 2025-10-16 | ny | WIN | +3.45R |
| loser1 | 2024-09-27 | ny | LOSS | -1.00R |
| loser2 | 2025-02-12 | london | LOSS | -1.00R |
| marginal | 2024-04-03 | ny | WIN | +0.05R |

## Scoring Results

| Trade | Outcome | R | Run1 S | Run1 C | Run1 Conf | Run2 S | Run2 C | Run2 Conf | Gap | Consistent? |
|---|---|---|---|---|---|---|---|---|---|---|
| 2025-01-30 | WIN | +3.77R | 5 | 5 | 100 | 4 | 4 | 80 | 20 | **NO** |
| 2025-10-16 | WIN | +3.45R | 2 | 3 | 50 | 4 | 4 | 80 | 30 | **NO** |
| 2024-09-27 | LOSS | -1.00R | 4 | 3 | 70 | 4 | 3 | 70 | 0 | YES |
| 2025-02-12 | LOSS | -1.00R | 5 | 4 | 90 | 4 | 3 | 70 | 20 | **NO** |
| 2024-04-03 | WIN | +0.05R | 4 | 3 | 70 | 2 | 2 | 40 | 30 | **NO** |

**Max gap across runs: 30 pts**
**Avg gap: 20.0 pts**
**CONSISTENCY FAIL: Same MSO varies >20 pts. Scores are noise.**

## Discrimination Analysis

| Group | N | Mean Confidence | Mean Structural | Mean Contextual |
|---|---|---|---|---|
| Winners | 3 | 70 | 3.5 | 3.5 |
| Losers | 2 | 75 | 4.2 | 3.2 |
| **Gap** | — | **-5 pts** | -0.8 | +0.2 |

### Which Dimension Discriminates Better?

- Structural gap: -0.8 (winners 3.5 vs losers 4.2)
- Contextual gap: +0.2 (winners 3.5 vs losers 3.2)
- **Structural dimension discriminates better**

## Reasoning Quality Check

Does the AI cite specific numbers or use vague language?

### 2025-01-30 (WIN, +3.77R)

**Run 1 Structural:** 3-candle impulse from 2758.70 low to current 08:00 candle, creates FVG, minimal retracement as we're early in the move, recent BOS with 2.0 displacement ratio
**Run 1 Contextual:** Both timeframes bullish (with-trend), prime London KZ timing at 08:00Z, recent strong BOS events, no at_ob concerns, multiple session high runs showing momentum
**Run 1 Modifiers:** FVG boost: +1 to structural (capped at 5), no at_ob penalty

### 2025-10-16 (WIN, +3.45R)

**Run 1 Structural:** Impulse from 4222.36 low (12:30) to 4242.20 high (13:15) = 3 candles creating ~20 point move. No FVG created. Retracement is minimal as price just hit high. BOS event at 4234.99 from displacement move (ratio 2.6). Short impulse but lacks FVG and adequate retracement.
**Run 1 Contextual:** Structure bullish on both timeframes (with-trend). In NY kill zone timing (13:15). Recent BOS with good displacement (2.6 ratio). However, price is at session highs with multiple recent sweeps of asian_high, suggesting potential exhaustion. No clear align score provided but context appears mixed.
**Run 1 Modifiers:** No FVG boost applied (no three-candle gap identified). No at_ob penalty (not touching pre-existing OB zone).

### 2024-09-27 (LOSS, -1.00R)

**Run 1 Structural:** 4-candle impulse from 2658.23 low to 2665.48 high creating BOS, with 85% retracement (current price ~2662 vs high 2665.48). Clear bullish OB zone 2665.48-2662.55 formed from displacement move. No FVG created by the impulse.
**Run 1 Contextual:** Setup is with-trend (bullish structure on both H1/M15), timing is early NY kill zone (14:00 UTC). Multiple bullish sweeps of Asian low suggest liquidity grab. However, moderate concerns with multiple unmitigated OBs nearby and price in middle of session range.
**Run 1 Modifiers:** None - no FVG created by impulse, not at pre-existing OB

### 2025-02-12 (LOSS, -1.00R)

**Run 1 Structural:** Impulse from 2883.66 to 2890.51 in 3 candles (07:15-08:00), creates FVG, retracement to 2883.66 is ~100% (excessive but still within range), BOS event confirmed with ratio 3.3
**Run 1 Contextual:** Strong bullish structure on both timeframes, with-trend setup, early London kill zone timing (08:00), recent BOS with high displacement ratio 3.3, no immediate opposing zones nearby
**Run 1 Modifiers:** FVG boost already included in structural score (capped at 5)

### 2024-04-03 (WIN, +0.05R)

**Run 1 Structural:** Clean 3-candle impulse from 2269.60 low (12:30) to current level, creating bearish FVG 2281.06-2277.92. Retracement approximately 75% from session high 2287.04 to current level ~2273. BOS event from bullish M15 structure break.
**Run 1 Contextual:** Counter-trend setup (bearish in bullish M15/H1 structure), but NY kill zone timing is optimal. Multiple sweeps of asian_low suggest liquidity taken. No existing OB at current level (at_ob = false).
**Run 1 Modifiers:** FVG boost: +1 to structural score (bearish FVG 2281.06-2277.92 created by impulse). No at_ob penalty applied.

## Verdict

### FAIL — Inconsistent AND No Discrimination

**Two independent failures:**

1. **Inconsistency:** Same MSO varies by up to 30 pts across runs (4/5 trades inconsistent, avg gap 20 pts). Scores are noise.
2. **No discrimination:** Even averaging both runs, losers score HIGHER than winners (-5 pt gap, wrong direction). The rubric cannot separate good setups from bad.

**The reasoning quality is actually good** — the AI cites specific numbers (impulse candle counts, FVG yes/no, retracement %, displacement ratios). The problem is that the MSO text doesn't contain enough differentiation. Both the +3.77R winner and the -1.00R loser have clean BOS, bullish structure, good timing, and FVGs. The data looks the same because the pre-screen already filters to quality setups.

**Root cause:** The system pre-filters so aggressively (displacement ≥0.4 ATR, body ratio ≥40%, BOS confirmed) that by the time a candidate reaches the AI, ALL of them look structurally sound. There's not enough variance in the MSO to score.

**What would help:** Features NOT in the current MSO — time-of-day precision (LBMA Fix proximity), volume profile, concurrent order flow, or multi-instrument divergence. The current structural data can't distinguish winners from losers because both have clean structure.

**Action:** Kill the 2-dimension decomposition idea in its current form. The scoring rubric is sound in theory but the MSO doesn't provide enough differentiating signal. If confidence scoring is revisited, it needs new input features, not a better rubric.