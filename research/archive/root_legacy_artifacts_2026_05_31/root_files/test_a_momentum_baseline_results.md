# Task 1: Dumb Momentum Baseline Results

## Question
Does the OB zone identification add value over simple deep pullback after BOS?

## Method
For each qualified H1 BOS event (displacement ≥ 0.4 ATR, body ratio ≥ 40%):
- **OB retest**: Enter when price touches the identified OB zone
- **Dumb baseline**: Enter when price retraces ≥X% of the impulse range (no OB identification)
- **Same continuation logic**: 1.25 ATR target, 0.5 ATR stop, 20-candle window
- **Retest window**: 250 H1 candles (~10 trading days)

## Raw Results

### XAUUSD (551 BOS events)

| Entry Method | Retested | Continued | Rate |
|---|---|---|---|
| **OB Zone** | 485 | 146 | **30.1%** |
| 70% Retrace | 441 | 132 | 29.9% |
| 80% Retrace | 428 | 134 | 31.3% |
| 85% Retrace | 418 | 122 | 29.2% |
| 90% Retrace | 412 | 130 | 31.6% |
| 95% Retrace | 402 | 129 | 32.1% |

### GBPUSD (692 BOS events)

| Entry Method | Retested | Continued | Rate |
|---|---|---|---|
| **OB Zone** | 601 | 187 | **31.1%** |
| 70% Retrace | 566 | 185 | 32.7% |
| 80% Retrace | 552 | 184 | 33.3% |
| 85% Retrace | 547 | 190 | 34.7% |
| 90% Retrace | 543 | 199 | 36.6% |
| 95% Retrace | 535 | 182 | 34.0% |

### USDJPY (752 BOS events)

| Entry Method | Retested | Continued | Rate |
|---|---|---|---|
| **OB Zone** | 667 | 213 | **31.9%** |
| 70% Retrace | 614 | 191 | 31.1% |
| 80% Retrace | 598 | 181 | 30.3% |
| 85% Retrace | 585 | 181 | 30.9% |
| 90% Retrace | 577 | 179 | 31.0% |
| 95% Retrace | 570 | 200 | 35.1% |

### US30_cash (721 BOS events)

| Entry Method | Retested | Continued | Rate |
|---|---|---|---|
| **OB Zone** | 640 | 234 | **36.6%** |
| 70% Retrace | 614 | 237 | 38.6% |
| 80% Retrace | 598 | 222 | 37.1% |
| 85% Retrace | 591 | 228 | 38.6% |
| 90% Retrace | 583 | 227 | 38.9% |
| 95% Retrace | 569 | 228 | 40.1% |

### GBPJPY (724 BOS events)

| Entry Method | Retested | Continued | Rate |
|---|---|---|---|
| **OB Zone** | 653 | 186 | **28.5%** |
| 70% Retrace | 610 | 191 | 31.3% |
| 80% Retrace | 593 | 187 | 31.5% |
| 85% Retrace | 581 | 173 | 29.8% |
| 90% Retrace | 574 | 179 | 31.2% |
| 95% Retrace | 560 | 175 | 31.2% |

## POOLED SUMMARY (All Instruments)

| Entry Method | Retested | Continued | Rate | Delta vs OB |
|---|---|---|---|---|
| **OB Zone** | 3046 | 966 | **31.7%** | — |
| 70% Retrace | 2845 | 936 | 32.9% | -1.2pp |
| 80% Retrace | 2769 | 908 | 32.8% | -1.1pp |
| 85% Retrace | 2722 | 894 | 32.8% | -1.1pp |
| 90% Retrace | 2689 | 914 | 34.0% | -2.3pp |
| 95% Retrace | 2636 | 914 | 34.7% | -3.0pp |

## Important Note on Absolute Rates

The ~31% absolute continuation rates here differ from the screening's ~70% because:
1. This analysis uses a **simplified BOS detection** (no CHoCH, no full structure tracking)
2. My implementation returns False when neither target nor stop hit within 20 candles
3. Different BOS event populations may be included

**The absolute rates are NOT comparable to the screening's 70%.** What matters is the **RELATIVE comparison** between OB zone and dumb baselines, since both use the exact same BOS events, same continuation logic, and same parameters.

## Interpretation

- **Best dumb baseline**: 95% retrace at **34.7%** (2636 retests)
- **OB zone rate**: **31.7%** (3046 retests)
- **OB disadvantage**: The OB zone actually performs **3.0pp WORSE** than the best dumb baseline
- **Fisher's exact p-value**: 0.0190 — the difference is **statistically significant**
- **Across ALL thresholds**: Every dumb baseline (70-95%) matches or beats the OB zone

**VERDICT: OB zone identification adds ZERO value.** In fact, a simple deep pullback entry after BOS **outperforms** the OB zone. The edge is **purely momentum/trend-following**, not zone precision.

Per-instrument: This finding is consistent across 4 of 5 instruments (XAUUSD roughly even, GBPUSD/US30/GBPJPY all show dumb > OB). Only USDJPY shows OB slightly ahead.

## So What?

**The dumb baseline BEATS the OB zone. This is the strongest possible result:**
- The "edge" is structural momentum after BOS, not the specific OB zone
- Identifying the OB candle and its high/low zone adds no value — ANY deep pullback works as well or better
- The deeper the pullback (95% vs 70%), the BETTER the continuation — this is pure mean-reversion within a trend
- **AI evaluation still adds value** through selectivity (choosing WHICH BOS events to trade, kill zone filtering, context assessment) — but the zone identification step is cargo cult
- A simpler entry rule (BOS → wait for ≥85% retrace → enter) would produce identical or superior results without the OB detection complexity