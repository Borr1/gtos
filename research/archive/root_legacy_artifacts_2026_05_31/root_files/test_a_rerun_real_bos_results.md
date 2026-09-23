# Task 1 RERUN: Dumb Momentum Baseline — Real Batch Population

## Method

Used the primary XAUUSD batch (174 trading days, 2024-04-01 to 2026-03-13):
- Extracted **all CANDIDATE entries** from raw API responses (688 entries)
- Deduplicated to **1 per date+KZ** (219 unique BOS events)
- Matched to actual trade outcomes (139 became real trades)
- Estimated impulse range from entry price, SL, and Fibonacci retracement %
- Simulated alternatives on H1 data with **same SL and TP price levels**
- Simulation window: 16 H1 candles (matches median real hold time)

## Simulation Calibration

To validate the H1 simulation, we ran the **same AI-selected trades** through both
actual outcomes and simulation:

| Method | n | Resolved | Wins | WR (resolved) |
|---|---|---|---|---|
| Actual outcomes | 139 | 139 | 78 | **56.1%** |
| H1 simulation | 139 | 115 | 79 | 68.7% |
| Simulation gap | — | — | — | +12.6pp |

The simulation is 12.6pp too generous.
All simulated WRs should be read with this ~13pp calibration in mind.

## Results

| Method | Events | Filled | Resolved | Wins | WR (resolved) | WR (calibrated) |
|---|---|---|---|---|---|---|
| **AI-selected (real system)** | 139 | 139 | 139 | 78 | **56.1% (actual)** | **56.1%** |
| All OB entries, no AI filter | 219 | 219 | 173 | 122 | 70.5% | 57.9% |
| 80% retrace baseline | 219 | 183 | 136 | 73 | 53.7% | 41.1% |
| 85% retrace baseline | 219 | 159 | 118 | 42 | 35.6% | 23.0% |
| 90% retrace baseline | 219 | 135 | 112 | 29 | 25.9% | 13.3% |
| 95% retrace baseline | 219 | 115 | 103 | 16 | 15.5% | 3.0% |

## Q1: Does the AI add value?

- **AI-selected WR**: 56.1% (78/139 actual)
- **All OB entries (sim)**: 70.5% raw, **57.9% calibrated** (122/173)
- **AI advantage**: -1.8pp
- Fisher p (AI-sim vs All-OB-sim, apples-to-apples): 0.7937

**NO.** The AI selection does not outperform unfiltered OB entries.

## Q2: Does the OB zone add value over generic deep pullback?

| Comparison | OB sim WR | Baseline sim WR | Delta | Fisher p |
|---|---|---|---|---|
| OB vs 80% retrace | 70.5% | 53.7% | +16.8pp | 0.0029 * |
| OB vs 85% retrace | 70.5% | 35.6% | +34.9pp | 0.0000 * |
| OB vs 90% retrace | 70.5% | 25.9% | +44.6pp | 0.0000 * |
| OB vs 95% retrace | 70.5% | 15.5% | +55.0pp | 0.0000 * |

**YES.** OB zone (70.5%) outperforms best dumb baseline (80% at 53.7%)
by +16.8pp. Zone identification provides meaningful precision.

## Fill Rate Analysis

Deeper retrace = better RR but lower fill probability:

| Threshold | Fill Rate | Effective WR (filled × resolved WR) |
|---|---|---|
| 80% | 83.6% (183/219) | 44.9% |
| 85% | 72.6% (159/219) | 25.8% |
| 90% | 61.6% (135/219) | 16.0% |
| 95% | 52.5% (115/219) | 8.2% |
| OB zone | 100.0% (219/219) | 70.5% |

## Value Chain Decomposition

| Component | WR (raw sim) | WR (calibrated) | Value Added |
|---|---|---|---|
| Momentum only (BOS + 80% pullback) | 53.7% | 41.1% | baseline |
| + OB zone precision | 70.5% | 57.9% | +16.8pp |
| + AI selection | — | 56.1% | -1.8pp |
| **Full system** | — | **56.1%** | **+15.0pp total** |

## Same-Distance SL Variant (Fair Comparison)

The above test used same SL PRICE. Below uses same SL DISTANCE (same risk structure):

| Threshold | Filled | Resolved | Wins | WR (sim) | WR (calibrated) | vs OB (70.5% sim) |
|---|---|---|---|---|---|---|
| 80% retrace | 183 | 103 | 40 | 38.8% | 26.3% | -31.7pp |
| 85% retrace | 159 | 99 | 36 | 36.4% | 23.8% | -34.1pp |
| 90% retrace | 135 | 90 | 32 | 35.6% | 23.0% | -34.9pp |
| 95% retrace | 115 | 81 | 31 | 38.3% | 25.7% | -32.2pp |

**Even with same SL distance (same risk), the dumb baselines score 36-39% sim WR vs 70.5% for OB zone.**
The OB zone advantage is massive and NOT an artifact of SL distance.

The deeper entries have both lower fill rates AND lower WR — the OB zone is genuinely
better positioned than a generic deep pullback in this population.

## Critical Caveat: Why Dumb Baselines Collapse at Deeper Retraces

The dramatic WR drop (54% → 16%) at deeper retraces is **mechanical, not informational**:

- Using the **same SL price** means deeper entry = tighter SL distance
- At 95% retrace, entry is only ~5% of impulse range from the SL
- This tiny SL gets clipped by normal market noise
- Example: impulse range = 50pts, OB entry has 10pt SL, but 95% retrace entry has only 2.5pt SL

**This does NOT mean "the OB zone is better at picking entries."** It means the OB zone happens to sit at a distance from the impulse origin that provides adequate SL room. A dumb baseline with the **same SL distance** (not same price) would be the fairer test.

The 80% retrace (53.7% sim) is the fairest comparison because it has similar SL distance to the OB zone entry. At 80%, the OB zone still wins by +16.8pp — this IS meaningful.

## So What?

1. **OB zone adds significant value (+17pp)** over the best dumb baseline on this population.
   This reverses the finding from the simplified BOS analysis. The real system's BOS events are a
   curated population where OB zone precision matters.
2. **AI selection adds ~0pp.** The confidence scoring and multi-timeframe evaluation don't
   improve WR vs unfiltered OB entries. The AI's value may be in risk management (BE stops,
   position sizing) rather than entry selection.
3. **The 12.6pp simulation gap** means absolute calibrated numbers are approximate. But the
   **relative ranking** (OB >> 80% >> 85%+) is robust since all use the same simulation.
4. **The first test (simplified BOS) was misleading** because it used a different, broader
   population of BOS events. On the system's actual population, OB zones DO matter.