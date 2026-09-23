# WAVE2 — F2-SWEEP Dead-Zone Divisor Report

Offline zero-cost sensitivity sweep over ``dead_zone_divisor`` in ``identify_structure_v2``. See the task brief and ADR-004 for motivation.

## 1. Methodology

- **Instruments:** XAUUSD, USDJPY, GBPJPY, US30_cash, GBPUSD
- **Timeframe:** H1 candles from ``data/historical_2026/{SYMBOL}_H1.csv``
- **Date range filter:** ``2026-01-02 → 2026-04-13`` (inclusive)
- **Rolling window:** 168 bars (~1 week) with step 24 (~1 day)
- **Divisors probed:** [2, 4, 6, 8, 12]
- **No API calls.** Pure offline detect_swings + identify_structure_v2 + detect_structure_breaks + identify_order_blocks replay.

Per window: compute v1 baseline once, then v2 at each divisor. v1 and v2 share the same swings (so ``detect_swings`` output is identical); OB supply differs only because ``detect_structure_breaks`` branches on ``structure.direction``. Windows labeled ``transitional`` by v2 (with ``protected_swing=None``, the only form v2 emits for transitional) produce zero BOS and zero CHoCH — the CHoCH block in ``detect_structure_breaks`` requires a protected swing and the BOS block branches only on ``bullish``/``bearish``. Zero structure events in turn yield zero OBs from ``identify_order_blocks``. This is the dominant mechanism behind the OB-supply drop the sweep quantifies.

### Data provenance

| Symbol | Bars loaded | Windows evaluated |
|--------|-------------|-------------------|
| XAUUSD | 1,629 | 61 |
| USDJPY | 1,728 | 66 |
| GBPJPY | 1,728 | 66 |
| US30_cash | 1,641 | 62 |
| GBPUSD | 1,728 | 66 |

## 2. Label distribution per (instrument, divisor)

Rows are (instrument, divisor). v1 baseline shown once per symbol. Percentages computed over all evaluated windows including ``insufficient_data``.

| Instrument | Divisor | Windows | Bullish | Bearish | Transitional | Insufficient |
|------------|---------|---------|---------|---------|--------------|--------------|
| XAUUSD | v1 (baseline) | 61 | 100.0% | 0.0% | 0.0% | 0.0% |
| XAUUSD | 2 | 61 | 16.4% | 6.6% | 77.0% | 0.0% |
| XAUUSD | 4 | 61 | 36.1% | 18.0% | 45.9% | 0.0% |
| XAUUSD | 6 | 61 | 50.8% | 24.6% | 24.6% | 0.0% |
| XAUUSD | 8 | 61 | 55.7% | 24.6% | 19.7% | 0.0% |
| XAUUSD | 12 | 61 | 55.7% | 24.6% | 19.7% | 0.0% |
| USDJPY | v1 (baseline) | 66 | 100.0% | 0.0% | 0.0% | 0.0% |
| USDJPY | 2 | 66 | 15.2% | 0.0% | 84.8% | 0.0% |
| USDJPY | 4 | 66 | 42.4% | 3.0% | 54.5% | 0.0% |
| USDJPY | 6 | 66 | 53.0% | 15.2% | 31.8% | 0.0% |
| USDJPY | 8 | 66 | 56.1% | 18.2% | 25.8% | 0.0% |
| USDJPY | 12 | 66 | 57.6% | 19.7% | 22.7% | 0.0% |
| GBPJPY | v1 (baseline) | 66 | 100.0% | 0.0% | 0.0% | 0.0% |
| GBPJPY | 2 | 66 | 19.7% | 6.1% | 74.2% | 0.0% |
| GBPJPY | 4 | 66 | 37.9% | 12.1% | 50.0% | 0.0% |
| GBPJPY | 6 | 66 | 47.0% | 18.2% | 34.8% | 0.0% |
| GBPJPY | 8 | 66 | 50.0% | 21.2% | 28.8% | 0.0% |
| GBPJPY | 12 | 66 | 50.0% | 21.2% | 28.8% | 0.0% |
| US30_cash | v1 (baseline) | 62 | 100.0% | 0.0% | 0.0% | 0.0% |
| US30_cash | 2 | 62 | 0.0% | 22.6% | 77.4% | 0.0% |
| US30_cash | 4 | 62 | 9.7% | 35.5% | 54.8% | 0.0% |
| US30_cash | 6 | 62 | 12.9% | 43.5% | 43.5% | 0.0% |
| US30_cash | 8 | 62 | 14.5% | 56.5% | 29.0% | 0.0% |
| US30_cash | 12 | 62 | 14.5% | 56.5% | 29.0% | 0.0% |
| GBPUSD | v1 (baseline) | 66 | 100.0% | 0.0% | 0.0% | 0.0% |
| GBPUSD | 2 | 66 | 4.5% | 22.7% | 72.7% | 0.0% |
| GBPUSD | 4 | 66 | 15.2% | 48.5% | 36.4% | 0.0% |
| GBPUSD | 6 | 66 | 18.2% | 54.5% | 27.3% | 0.0% |
| GBPUSD | 8 | 66 | 19.7% | 62.1% | 18.2% | 0.0% |
| GBPUSD | 12 | 66 | 19.7% | 62.1% | 18.2% | 0.0% |

## 3. OB supply per (instrument, divisor)

Total OBs, split by bullish/bearish type. ``v2 / v1`` column is the preservation ratio the F2.2 cold review flagged at 47% on USDJPY. Target: > 70%.

| Instrument | Divisor | Total OBs | Bullish OBs | Bearish OBs | v2/v1 |
|------------|---------|-----------|-------------|-------------|-------|
| XAUUSD | v1 (baseline) | 447 | 441 | 6 | 1.00 |
| XAUUSD | 2 | 139 | 94 | 45 | 0.31 |
| XAUUSD | 4 | 298 | 191 | 107 | 0.67 |
| XAUUSD | 6 | 404 | 263 | 141 | 0.90 |
| XAUUSD | 8 | 427 | 286 | 141 | 0.96 |
| XAUUSD | 12 | 427 | 286 | 141 | 0.96 |
| USDJPY | v1 (baseline) | 637 | 631 | 6 | 1.00 |
| USDJPY | 2 | 116 | 116 | 0 | 0.18 |
| USDJPY | 4 | 314 | 297 | 17 | 0.49 |
| USDJPY | 6 | 451 | 373 | 78 | 0.71 |
| USDJPY | 8 | 483 | 390 | 93 | 0.76 |
| USDJPY | 12 | 501 | 400 | 101 | 0.79 |
| GBPJPY | v1 (baseline) | 516 | 513 | 3 | 1.00 |
| GBPJPY | 2 | 167 | 129 | 38 | 0.32 |
| GBPJPY | 4 | 306 | 232 | 74 | 0.59 |
| GBPJPY | 6 | 380 | 281 | 99 | 0.74 |
| GBPJPY | 8 | 411 | 298 | 113 | 0.80 |
| GBPJPY | 12 | 411 | 298 | 113 | 0.80 |
| US30_cash | v1 (baseline) | 413 | 397 | 16 | 1.00 |
| US30_cash | 2 | 132 | 2 | 130 | 0.32 |
| US30_cash | 4 | 263 | 55 | 208 | 0.64 |
| US30_cash | 6 | 321 | 74 | 247 | 0.78 |
| US30_cash | 8 | 400 | 82 | 318 | 0.97 |
| US30_cash | 12 | 400 | 82 | 318 | 0.97 |
| GBPUSD | v1 (baseline) | 439 | 430 | 9 | 1.00 |
| GBPUSD | 2 | 177 | 33 | 144 | 0.40 |
| GBPUSD | 4 | 394 | 101 | 293 | 0.90 |
| GBPUSD | 6 | 448 | 119 | 329 | 1.02 |
| GBPUSD | 8 | 496 | 128 | 368 | 1.13 |
| GBPUSD | 12 | 496 | 128 | 368 | 1.13 |

## 4. Acceptance scoreboard

Per-divisor pass/fail on the 4 acceptance criteria:

1. **Symmetry** — aggregate ``|bullish% - bearish%| < 10pp``.
2. **Transitional rate** — aggregate AND per-instrument in [10, 30]%.
3. **OB preservation** — ``v2_total_OBs / v1_total_OBs > 70%`` per instrument.
4. **Directional balance** — ``max(bullish%, bearish%) < 60%`` per instrument.

| Divisor | Bull% | Bear% | Trans% | Symm (1) | Trans (2) | OB (3) | Dir (4) | Pass count |
|---------|-------|-------|--------|----------|-----------|--------|---------|------------|
| 2 | 11.2% | 11.5% | 77.3% | PASS (0.3%) | FAIL | FAIL | PASS | 2/4 |
| 4 | 28.3% | 23.4% | 48.3% | PASS (5.0%) | FAIL | FAIL | PASS | 2/4 |
| 6 | 36.4% | 31.2% | 32.4% | PASS (5.3%) | FAIL | PASS | PASS | 3/4 |
| 8 | 39.3% | 36.4% | 24.3% | PASS (2.8%) | PASS | PASS | FAIL | 3/4 |
| 12 | 39.6% | 36.8% | 23.7% | PASS (2.8%) | PASS | PASS | FAIL | 3/4 |

### 4.1 Per-instrument failure-mode breakdown

For each divisor, shows the instruments that individually fail each non-aggregate criterion. Empty cells = all instruments pass.

| Divisor | Trans fails (sym: %) | OB ratio fails (sym: ratio) | Dir fails (sym: max%) |
|---------|----------------------|-----------------------------|-----------------------|
| 2 | XAUUSD: 77.0%, USDJPY: 84.8%, GBPJPY: 74.2%, US30_cash: 77.4%, GBPUSD: 72.7% | XAUUSD: 0.31, USDJPY: 0.18, GBPJPY: 0.32, US30_cash: 0.32, GBPUSD: 0.40 | (none) |
| 4 | XAUUSD: 45.9%, USDJPY: 54.5%, GBPJPY: 50.0%, US30_cash: 54.8%, GBPUSD: 36.4% | XAUUSD: 0.67, USDJPY: 0.49, GBPJPY: 0.59, US30_cash: 0.64 | (none) |
| 6 | USDJPY: 31.8%, GBPJPY: 34.8%, US30_cash: 43.5% | (none) | (none) |
| 8 | (none) | (none) | GBPUSD: 62.1% |
| 12 | (none) | (none) | GBPUSD: 62.1% |

## 5. Recommendation

**No divisor clears all 4 criteria cleanly. Closest-to-passing: 8** — 3/4 criteria, transitional rate 24.3%. Selection minimises total miss magnitude across failed criteria (per-instrument severity, not just binary pass/fail). See §4.1 for details.

Per-divisor miss severity ranking (lower = closer to passing):

| Divisor | Pass count | Miss severity |
|---------|------------|---------------|
| 8 | 3/4 | 2.12 |
| 12 | 3/4 | 2.12 |
| 6 | 3/4 | 21.41 |
| 4 | 2/4 | 141.85 |
| 2 | 2/4 | 455.96 |

### 5.1 Winning-divisor metrics

- **Aggregate bullish / bearish / transitional:** 39.3% / 36.4% / 24.3% (symmetry gap 2.8%)
- **Per-instrument OB preservation ratio:**
  - XAUUSD: 0.96
  - USDJPY: 0.76
  - GBPJPY: 0.80
  - US30_cash: 0.97
  - GBPUSD: 1.13
- **Per-instrument transitional rate:**
  - XAUUSD: 19.7%
  - USDJPY: 25.8%
  - GBPJPY: 28.8%
  - US30_cash: 29.0%
  - GBPUSD: 18.2%
- **Per-instrument max(bullish%, bearish%):**
  - XAUUSD: 55.7%
  - USDJPY: 56.1%
  - GBPJPY: 50.0%
  - US30_cash: 56.5%
  - GBPUSD: 62.1% **(>= 60%)**

### 5.2 Per-instrument pathologies and caveats

- **XAUUSD**: v1: bull 100.0% / bear 0.0% (v1 known 100%-bullish bug surface). v2 across divisors [2, 4, 6, 8, 12]: trans ['77%', '46%', '25%', '20%', '20%']; bull ['16%', '36%', '51%', '56%', '56%']; bear ['7%', '18%', '25%', '25%', '25%']; OB ratio ['0.31', '0.67', '0.90', '0.96', '0.96']. **OB supply preservation worst case 0.31 at divisor 2 — below 70% target.**
- **USDJPY**: v1: bull 100.0% / bear 0.0% (v1 known 100%-bullish bug surface). v2 across divisors [2, 4, 6, 8, 12]: trans ['85%', '55%', '32%', '26%', '23%']; bull ['15%', '42%', '53%', '56%', '58%']; bear ['0%', '3%', '15%', '18%', '20%']; OB ratio ['0.18', '0.49', '0.71', '0.76', '0.79']. **OB supply preservation worst case 0.18 at divisor 2 — below 70% target.**
- **GBPJPY**: v1: bull 100.0% / bear 0.0% (v1 known 100%-bullish bug surface). v2 across divisors [2, 4, 6, 8, 12]: trans ['74%', '50%', '35%', '29%', '29%']; bull ['20%', '38%', '47%', '50%', '50%']; bear ['6%', '12%', '18%', '21%', '21%']; OB ratio ['0.32', '0.59', '0.74', '0.80', '0.80']. **OB supply preservation worst case 0.32 at divisor 2 — below 70% target.**
- **US30_cash**: v1: bull 100.0% / bear 0.0% (v1 known 100%-bullish bug surface). v2 across divisors [2, 4, 6, 8, 12]: trans ['77%', '55%', '44%', '29%', '29%']; bull ['0%', '10%', '13%', '15%', '15%']; bear ['23%', '35%', '44%', '56%', '56%']; OB ratio ['0.32', '0.64', '0.78', '0.97', '0.97']. **OB supply preservation worst case 0.32 at divisor 2 — below 70% target.**
- **GBPUSD**: v1: bull 100.0% / bear 0.0% (v1 known 100%-bullish bug surface). v2 across divisors [2, 4, 6, 8, 12]: trans ['73%', '36%', '27%', '18%', '18%']; bull ['5%', '15%', '18%', '20%', '20%']; bear ['23%', '48%', '55%', '62%', '62%']; OB ratio ['0.40', '0.90', '1.02', '1.13', '1.13']. **OB supply preservation worst case 0.40 at divisor 2 — below 70% target.**

## 6. Proposed code change

If CEO approves promotion of divisor ``8``, the one-line change in ``src/components/market_state.py`` is:

```python
def identify_structure_v2(
    swings: list[Swing],
    dead_zone_divisor: int = 8,   # <-- change default from 4 to 8
) -> StructureAnalysis:
```

All existing callers (unit tests, F2.3 shadow logger, F3 backtest) remain unchanged — they pass no divisor argument so the new default (``8``) takes effect at the function boundary. The F2.3 shadow logger then starts accumulating evidence under the tighter dead zone before any production cutover.

**Caveat:** recommended divisor 8 does NOT clear all 4 criteria. See §4.1 for which instruments fail which criterion. Before committing the default-change, consider whether a per-instrument ``dead_zone_divisor`` map is warranted.
