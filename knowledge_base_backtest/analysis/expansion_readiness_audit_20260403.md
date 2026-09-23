# Expansion Readiness Audit

**Date:** 2026-04-03
**Purpose:** Extract every data point needed for GBPUSD batch test design and scaling decisions

---

## Section 1: Data Inventory

### Per-Instrument Files

| Instrument | D1 | H4 | H1 | M15 | M5 | M15 Range | Trading Days | M15 Gaps |
|-----------|-----|-----|-----|------|-----|-----------|-------------|----------|
| XAUUSD | 582 | 3,489 | 13,319 | 53,202 | 90,000 | 2024-01-02 to 2026-04-02 | 582 | 2 (holidays) |
| EURUSD | 586 | 3,502 | 13,976 | 55,864 | 90,000 | 2024-01-02 to 2026-04-03 | 586 | 0 |
| GBPUSD | 586 | 3,502 | 13,975 | 55,861 | 90,000 | 2024-01-02 to 2026-04-03 | 586 | 0 |
| NAS100 | 545 | 3,239 | 12,348 | 49,215 | 90,000 | 2024-01-02 to 2026-04-02 | 545 | **4 (incl. 55-day gap Jul-Sep 2025)** |
| XAGUSD | 583 | 3,495 | 13,471 | 53,789 | 90,000 | 2024-01-02 to 2026-04-02 | 583 | 2 (holidays) |

**M5 date ranges (shorter):** XAUUSD: 2024-12-20+, EURUSD: 2025-01-16+, GBPUSD: 2025-01-16+, NAS100: 2024-10-24+, XAGUSD: 2024-12-31+

**Economic calendar:** NOT FOUND in `data/`.

**NAS100 WARNING:** 55-day data gap from 2025-07-16 to 2025-09-09. Any batch test on NAS100 must exclude this range.

---

## Section 2: Batch Test Infrastructure

### 2.1 Script: `scripts/batch_backtest.py` (1,132 lines)

**CLI Arguments:**
```
--start          Start date YYYY-MM-DD (required unless --resume-batch)
--end            End date YYYY-MM-DD (required unless --resume-batch)
--dry-run        Build prompts + estimate cost, don't submit
--resume-batch   Resume a previously submitted batch ID
--no-prescreen   Disable D1/H4 pre-screening
--vision         Include M15 chart images (PNG) in API calls
--config         Config file path (default: config/agent_config.yaml)
--output-dir     Output directory (default: knowledge_base_backtest)
```

### 2.2 Instrument Hardcoding — CRITICAL

**Line 962-964 — HARDCODED to XAUUSD:**
```python
for tf in ("D1", "H4", "H1", "M15"):
    csv_path = HISTORICAL_DIR / f"XAUUSD_{tf}.csv"
```

This is the **only** place where the instrument is hardcoded in the data loading path. The rest of the pipeline (pre-screen, prompt building, outcome evaluation) uses the loaded candle data without referencing instrument names. The symbol from config (`market.symbol`) is not used for file loading.

**Fix required:** Change to `csv_path = HISTORICAL_DIR / f"{config['market']['symbol']}_{tf}.csv"` or add a `--symbol` CLI argument.

### 2.3 Data Split

No automatic discovery/validation split. The batch processes ALL dates in the range. Split must be done manually by choosing --start/--end ranges.

### 2.4 Output

- Per-session manifests: `knowledge_base_backtest/sessions/{date}_session.json`
- Raw PA responses: `knowledge_base_backtest/batch_api/responses/{date}_responses.json`
- Batch results: `knowledge_base_backtest/batch_api/{batch_id}_results.json`
- Report: `knowledge_base_backtest/batch_api/{batch_id}_report.txt`
- Prompt cache: `knowledge_base_backtest/batch_api/{batch_id}_full_prompts.json`

### 2.5 API Configuration

- Model: `claude-sonnet-4-20250514` (from config `ai.primary_model`)
- Max tokens: 2,000 per response
- Temperature: from config (default 0 for PA)
- Batch API: Anthropic Message Batches API (50% discount)
- Prompt caching: enabled (system prompt cached across same-session calls)
- Pricing: $1.50/MTok input, $7.50/MTok output, $0.15/MTok cache read, $1.875/MTok cache write

### 2.6 Pre-screening

Uses `compute_market_state()` on the first London candle of each day. Checks:
1. Layer 1: D1 structure must be "bullish" or "bearish" (not transitional/insufficient)
2. Layer 2: H4 structure must agree with D1

Reads from `config['data']` for lookback periods, swing detection min_bars, etc. **Instrument-agnostic** — works on any OHLCV data.

### 2.7 Token Counts (from actual batch data)

- System prompt: ~2,809 tokens (11,237 chars)
- User message (MSO): ~689 tokens (2,759 chars) — varies by date
- Total input per call: ~3,500 tokens
- Output per call: ~800 tokens (calibrated estimate)

### 2.8 M5 Refinement

NOT in the batch script. M5 refinement is only in the live pipeline (`src/components/m5_refinement.py`). The batch evaluates M15-level trades only. M5 refinement calls would need to be added as a post-processing step.

### 2.9 Date Range

Accepts `--start` and `--end`. Processes ALL weekdays in range. No instrument-specific filtering.

---

## Section 3: AI Prompt Instrument Specificity

### 3.1 Primary Analyzer Prompt (`src/prompts/primary_analyzer_prompt.py`)

**Gold-specific references (MUST CHANGE for GBPUSD):**

| Line | Content | Issue |
|------|---------|-------|
| 28 | "institutional gold trader with 15+ years of experience trading XAUUSD" | Hardcoded instrument identity |
| 28 | "using Smart Money Concepts (SMC) and ICT methodology" | OK — methodology is universal |
| 43 | "U6. SL REQUIREMENTS: Stop loss must be >= 1.5x M15 ATR(14) AND >= $5.00 absolute minimum" | **$5.00 is gold-specific** — GBPUSD min SL should be ~5 pips (0.0005) |
| 100 | "BR5. Zones wider than $15 give poor RR" | **$15 is gold-specific** — GBPUSD equivalent: ~15 pips (0.0015) |
| 136 | "OB zone wider than $15" | Same — gold-specific dollar amount |

**Dollar signs in price context:** The prompt uses `$` for gold prices extensively in the schema examples and thresholds. For GBPUSD, prices are in pip-denominated format (1.2XXX).

**Instrument name injection:** The prompt text is HARDCODED as a string constant `SYSTEM_PROMPT`. It does NOT use string interpolation or f-strings. No `{symbol}` placeholder exists.

**"Pips" mentions:** NONE. The prompt only uses dollar amounts.

### 3.2 M5 Refinement Prompt (`src/components/m5_refinement.py`)

**Gold-specific references:**

| Line | Content | Issue |
|------|---------|-------|
| 28 | "expert gold scalper" | Hardcoded |
| 38-39 | "M15 SL: ${sl_price:.2f} (${sl_distance:.2f} distance)" | Dollar formatting — works but misleading for GBPUSD |
| 48 | "$1.50 buffer" | **Gold-specific** — GBPUSD buffer should be ~1-2 pips (0.0001-0.0002) |

### 3.3 Other Prompts

| File | Gold-specific? |
|------|---------------|
| `bull_agent_prompt.py` | Line 17: "senior gold trader" — hardcoded |
| `bear_agent_prompt.py` | Lines reference "capital" generally — mostly OK |
| `judge_prompt.py` | Line 15: "gold trade" — hardcoded |
| `postmortem_prompt.py` | Not read, likely has gold references |

### 3.4 Summary: Prompt Changes Needed for GBPUSD

1. Replace "gold trader" / "XAUUSD" → parameterized `{instrument}` identity
2. Replace "$5.00 minimum SL" → instrument-specific SL floor from config
3. Replace "$15 zone width" → instrument-specific threshold from config
4. Replace "$1.50 buffer" → instrument-specific buffer from config
5. Change price format from `$X.XX` to pip-based format for forex pairs

**Estimated effort:** 30-60 minutes of prompt engineering. Could be done with string interpolation: inject instrument name, min SL, buffer amounts, and zone width thresholds as variables.

---

## Section 4: Config Audit

### 4.1 Full Config (verbatim)

```yaml
market:
  symbol: "XAUUSD"
  kill_zones:
    london:
      start_utc: "07:00"
      end_utc: "09:30"
      core_end_utc: "09:30"
    ny:
      start_utc: "13:00"
      end_utc: "15:30"
  session_start_utc: "07:00"
  session_end_utc: "09:30"
  session_timeout_utc: "12:00"
  asian_session_start_utc: "00:00"
  asian_session_end_utc: "07:00"

risk:
  risk_per_trade_pct: 1.0
  max_daily_loss_pct: 2.0
  max_weekly_loss_pct: 4.0
  max_monthly_loss_pct: 8.0
  max_trades_per_day: 2
  min_rr: 1.5
  tp1_close_pct: 100
  max_spread_cents: 30          # <-- GOLD-SPECIFIC ($0.30)
  sl_buffer_dollars: 1.20       # <-- GOLD-SPECIFIC ($1.20)

model_a:
  bias_timeframes: ["D1", "H4"]
  setup_timeframe: "H1"
  entry_timeframe: "M15"
  enabled_frameworks: ["ob_retest"]
  ote_zone_fib_top: 0.618
  ote_zone_fib_bottom: 0.786
  displacement_min_ratio: 1.5
  equal_level_tolerance: 2.50   # <-- GOLD-SPECIFIC ($2.50)

ai:
  billing_mode: "api"
  primary_model: "claude-sonnet-4-20250514"
  debate_model: "claude-sonnet-4-20250514"
  postmortem_model: "claude-sonnet-4-20250514"
  review_model: "claude-sonnet-4-20250514"
  debate_round2_enabled: true
  max_api_retries: 1
  api_timeout_seconds: 30

confidence_filter_mode: "shadow"

retrieval:
  embedding_model: "all-MiniLM-L6-v2"
  lancedb_path: "knowledge_base/vectordb"
  similar_setups_top_k: 5
  min_similarity_threshold: 0.50

data:
  lookback:
    D1: 30
    H4: 80
    H1: 168
    M15: 672
  swing_detection_min_bars:
    D1: 2
    H4: 2
    H1: 2
    M15: 2
  fvg_min_gap:
    D1: 5.0                     # <-- GOLD-SPECIFIC ($5.00)
    H4: 3.0                     # <-- GOLD-SPECIFIC ($3.00)
    H1: 2.0                     # <-- GOLD-SPECIFIC ($2.00)
    M15: 1.0                    # <-- GOLD-SPECIFIC ($1.00)

m5_refinement:
  enabled: true
  sl_floor: 10.0                # <-- GOLD-SPECIFIC ($10.00)
  quality_gate:
    - HIGH
    - MEDIUM
  candle_lookback: 36
  model: "claude-sonnet-4-20250514"
  max_tokens: 500
```

### 4.2 Gold-Specific Values That Need Changing

| Parameter | Gold Value | GBPUSD Equivalent | Source |
|-----------|-----------|-------------------|--------|
| `market.symbol` | XAUUSD | GBPUSD | — |
| `risk.max_spread_cents` | 30 ($0.30) | ~2 (0.2 pips) | Typical GBPUSD spread ~0.1-0.3 pips |
| `risk.sl_buffer_dollars` | 1.20 ($1.20) | ~0.00015 (1.5 pips) | ~1.5 pips buffer |
| `model_a.equal_level_tolerance` | 2.50 ($2.50) | 0.000201 (2.0 pips) | From displacement scan |
| `data.fvg_min_gap.D1` | 5.0 | 0.00050 (5 pips) | Scale by price ratio |
| `data.fvg_min_gap.H4` | 3.0 | 0.00030 (3 pips) | Scale by price ratio |
| `data.fvg_min_gap.H1` | 2.0 | 0.00020 (2 pips) | Scale by price ratio |
| `data.fvg_min_gap.M15` | 1.0 | 0.00010 (1 pip) | Scale by price ratio |
| `m5_refinement.sl_floor` | 10.0 ($10) | 0.00100 (10 pips) | Scale by price ratio |

### 4.3 Multi-Instrument Config Structure

**Currently: FLAT.** Single-instrument config with no per-instrument sections. No mechanism for instrument-specific overrides.

### 4.4 GBPUSD Config Section (proposed)

```yaml
# Option A: Override block
instruments:
  GBPUSD:
    risk:
      max_spread_cents: 2        # 0.2 pips
      sl_buffer_dollars: 0.00015 # 1.5 pips
    model_a:
      equal_level_tolerance: 0.000201  # 2.0 pips
    data:
      fvg_min_gap:
        D1: 0.00050
        H4: 0.00030
        H1: 0.00020
        M15: 0.00010
    m5_refinement:
      sl_floor: 0.00100  # 10 pips
```

---

## Section 5: Historical AI Trade Datasets

### 5.1 Phase 1 Fresh Trades (18 trades)

| # | Date | KZ | Dir | Grade | Framework | Entry | M15 SL Dist | M5 SL Dist | M5 Quality | MFE_R | MAE_R |
|---|------|----|-----|-------|-----------|-------|------------|-----------|------------|-------|-------|
| 1 | 2024-04-08 | NY | LONG | A | ob_retest | 2338.19 | 18.0 | — | — | 0.288 | 1.087 |
| 2 | 2024-04-18 | NY | LONG | A+ | ob_retest | 2379.32 | 6.3 | — | — | 2.144 | 1.553 |
| 3 | 2024-05-31 | NY | LONG | A+ | ob_retest | 2343.80 | 9.3 | — | — | 1.722 | 1.032 |
| 4 | 2024-10-03 | NY | LONG | A | ob_retest | 2647.99 | 22.2 | — | — | 0.631 | 0.499 |
| 5 | 2025-02-18 | NY | LONG | A+ | ob_retest | 2912.02 | 28.9 | 3.0 | HIGH | 0.867 | 0.000 |
| 6 | 2025-03-25 | Lon | LONG | A+ | ob_retest | 3020.04 | 16.0 | 8.1 | HIGH | 0.992 | 0.592 |
| 7 | 2025-03-25 | NY | LONG | A | ob_retest | 2995.32 | 9.9 | 3.0 | HIGH | 4.125 | 0.000 |
| 8 | 2025-05-07 | NY | LONG | A | ob_retest | 3378.50 | 81.2 | 5.7 | HIGH | 0.241 | 0.183 |
| 9 | 2025-05-08 | Lon | LONG | A | breaker | 3369.12 | 24.9 | — | LOW | 0.378 | 1.048 |
| 10 | 2025-06-25 | Lon | LONG | A | ob_retest | 3330.72 | 14.5 | 3.0 | MED | 0.437 | 1.165 |
| 11 | 2025-09-23 | NY | LONG | A+ | ob_retest | 3787.78 | 53.9 | 3.2 | MED | 0.020 | 0.668 |
| 12 | 2025-10-13 | Lon | LONG | A+ | ob_retest | 4063.02 | 51.7 | 5.0 | MED | 1.044 | 0.061 |
| 13 | 2025-11-04 | NY | SHORT | A | ob_retest | 3987.53 | 13.9 | 3.0 | HIGH | 4.227 | 0.608 |
| 14 | 2025-12-22 | Lon | LONG | A+ | ob_retest | 4402.58 | 21.4 | 3.0 | HIGH | 2.166 | 0.000 |
| 15 | 2025-12-22 | NY | LONG | A+ | ob_retest | 4408.08 | 25.7 | 3.0 | MED | 1.592 | 0.000 |
| 16 | 2026-01-12 | NY | LONG | A+ | ob_retest | 4588.36 | 33.1 | 4.5 | HIGH | 1.263 | 0.104 |
| 17 | 2026-01-14 | Lon | LONG | A+ | ob_retest | 4633.53 | 40.7 | 17.5 | HIGH | 0.231 | 0.839 |
| 18 | 2026-01-27 | Lon | LONG | A+ | ob_retest | 5082.99 | 70.9 | 8.0 | HIGH | 1.516 | 0.513 |

### 5.2 Unified Trade Dataset (111 trades from 3 batches)

- **Date range:** 2024-04-01 to 2026-03-13
- **Total trades:** 111
- **Frameworks:** ob_retest=101, session_sweep=10
- **Directions:** LONG=103, SHORT=7, unknown=1
- **KZ:** London=58, NY=53
- **Grades:** A+=80, A=31
- **Outcomes:** WIN=72, LOSS=36, BREAKEVEN=3
- **Win rate:** 65.8%
- **Total R:** +22.17, **Avg R:** +0.200
- **Batch IDs:** 8 batches ran (largest: 174 sessions/88 trades)

---

## Section 6: Granular Analysis Status

**Monte Carlo / Kelly / MFE distribution / 25-section analysis:** NOT FOUND. No prompt file, no output files. This analysis was never run.

**What exists:** displacement_scan, phase0_corrected, phase1_tp_calibration, m5_feasibility, m5_validation, date_selection_model, multi_instrument_validation, verification_audit.

---

## Section 7: Corrected Multi-Instrument Displacement Data

Using `*_20260403_1003.csv` databases (all 3 bug fixes applied: identify_structure, MFE rounding, H1 lookback).

### Sweep+FVG+Align>=3 Combo Analysis

| Metric | XAUUSD | GBPUSD | NAS100 |
|--------|--------|--------|--------|
| Total disps | 7,496 | 7,828 | 6,953 |
| Combo (all) n | 909 | 727 | 909 |
| Combo cont_3h | 58.6% | 56.0% | 57.8% |
| Combo MFE/MAE | 1.32 | 1.27 | 1.19 |
| Combo (val) n | 576 | 433 | 551 |
| Val cont_3h | 59.2% | 56.6% | 58.1% |
| Val MFE/MAE | 1.31 | 1.31 | 1.22 |
| Direction split | 100/0 bull/bear | **97/3 bull/bear** | **99/1 bull/bear** |

**CRITICAL FINDING:** GBPUSD combo is 97% bullish. Despite GBPUSD having balanced overall direction (23% bull / 22% bear / 55% other on D1), the Sweep+FVG+Align>=3 combo almost exclusively fires on bullish days. This means the combo has NOT been tested on bearish GBPUSD. Short setups would need separate validation.

---

## Section 8: Structure Detection Deep Audit

### 8.1 identify_structure() Logic (from market_state.py)

**Exact rules (post-fix):**
```python
hh_count = sum(ALL consecutive HH pairs across full swing list)
hl_count = sum(ALL consecutive HL pairs)
lh_count = sum(ALL consecutive LH pairs)
ll_count = sum(ALL consecutive LL pairs)
recent_pairs = min(3, len(highs)-1, len(lows)-1)

if hh_count >= recent_pairs AND hl_count >= recent_pairs: "bullish"
elif ll_count >= recent_pairs AND lh_count >= recent_pairs: "bearish"
else: "transitional"
```

**Swing detection:** Simple fractals — a candle's high must be higher than `min_bars` candles on each side. `min_bars=2` for all timeframes. NOT ATR-based or zigzag.

### 8.2 GBPUSD D1 Monthly Structure Breakdown

| Month | Bullish | Bearish | Other | Total |
|-------|---------|---------|-------|-------|
| 2024-01 | 5 | 0 | 8 | 13 |
| 2024-04 | 0 | 15 | 7 | 22 |
| 2024-07 | 3 | 11 | 9 | 23 |
| 2024-09 | 6 | 10 | 5 | 21 |
| 2024-10 | 8 | 11 | 4 | 23 |
| 2024-12 | 0 | 0 | 22 | 22 |
| 2025-01 | 0 | 12 | 10 | 22 |
| 2025-03 | 20 | 0 | 1 | 21 |
| 2025-09 | 0 | 0 | 22 | 22 |
| 2025-12 | 18 | 0 | 4 | 22 |
| 2026-03 | 0 | 19 | 3 | 22 |
| **TOTAL** | **135** | **124** | **318** | **577** |
| **Pct** | **23.4%** | **21.5%** | **55.1%** | |

**Longest bearish streak:** 17 days (2024-03-26 to 2024-04-17)

**Overall:** 23.4% bullish, 21.5% bearish, 55.1% unclear/transitional. **Well balanced** between bull and bear when structure IS clear. The 55% "other" reflects the ranging nature of GBPUSD vs gold's sustained trend.

### 8.3 Specific GBPUSD Weakness Periods

| Period | Price Move | Bear Days Detected |
|--------|-----------|-------------------|
| Jun-Jul 2024 | +48 pips (choppy) | 11 |
| Sep-Oct 2024 | -255 pips (clear drop) | 21 |
| Jan 2025 | +25 pips (choppy) | 12 |
| Sep-Oct 2025 | -396 pips (sharp drop) | 7 (mostly "other") |

The Sep-Oct 2025 drop (-396 pips) was detected as bearish on only 7 days — the rest were classified "other." This suggests the structure detection may under-classify sharp bearish moves on GBPUSD when they happen quickly without forming textbook LH/LL sequences. **Worth monitoring but not a blocking issue** — the pre-screen would simply skip these days (conservative, not harmful).

---

## Section 9: Cost Estimation for GBPUSD Batch

### 9.1 Token Costs (from gold batch actuals)

| Component | Tokens |
|-----------|--------|
| System prompt | ~2,809 |
| User message (MSO) | ~689 (varies) |
| Total input per call | ~3,500 |
| Output per call | ~800 |

### 9.2 GBPUSD Batch Size

- Total weekdays: 586
- Pre-screen pass rate: 25% (147/586)
- Candles per passing day: ~20 (10 London + 10 NY)
- **Total API calls: ~147 × 20 = 2,940 candle evaluations**

### 9.3 Cost Calculation

```
Input tokens:  2,940 × 3,500 = 10,290,000
Output tokens: 2,940 × 800   =  2,352,000
Cache reads:   ~50% of input  =  5,145,000

Batch pricing:
  Non-cached input: 5,145,000 × $1.50/MTok = $7.72
  Cached input:     5,145,000 × $0.15/MTok = $0.77
  Output:           2,352,000 × $7.50/MTok = $17.64
  Cache writes:     ~147 × 2,809 × $1.875/MTok = $0.77

TOTAL BATCH COST: ~$26.90
```

### 9.4 Gold Comparison

The largest gold batch (msgbatch_01WUZbzFQniomk49SoLRAsPg) processed 174 sessions with 88 trades. Actual cost data not stored in result files, but at similar scale the Phase 1 18-trade batch cost $25.76.

**GBPUSD estimate: ~$25-30 for full 2-year backtest.** Comparable to gold.

### 9.5 M5 Refinement Calls

If ~6% of candle evaluations become CANDIDATE → ~176 candidates → M5 calls at ~500 tokens each → ~$0.50 additional. Negligible.

---

## Section 10: Pre-Screen Function Portability

### 10.1 Gold-Specific Thresholds

The pre-screen function (`prescreen_date` in batch_backtest.py) contains **NO gold-specific thresholds**. It:
1. Builds MSO via `compute_market_state(raw_data, config)`
2. Checks `d1.structure.direction` is "bullish" or "bearish"
3. Checks `h4.structure.direction` agrees with D1

### 10.2 Instrument-Agnostic Components

- `compute_market_state()` — processes any OHLCV data
- `detect_swings()` — works on any price series
- `identify_structure()` — works on any swings
- FVG detection — uses `fvg_min_gap` from config (would need GBPUSD values)

### 10.3 What Would Break Without Changes

If you pointed `batch_backtest.py` at GBPUSD data with the current XAUUSD config:
1. **File loading would fail** — hardcoded `XAUUSD_{tf}.csv` paths
2. **FVG min gaps** — $1-5 thresholds would filter out ALL GBPUSD FVGs (GBPUSD FVGs are 0.0001-0.0010 range)
3. **SL floor** — $10 would be ~10,000 pips for GBPUSD (absurd)
4. **Spread check** — $0.30 max spread is fine for gold but would need to be ~0.0002 for GBPUSD
5. **Equal level tolerance** — $2.50 would miss all GBPUSD equal levels

### 10.4 Required Changes for GBPUSD

1. Parameterize file loading with `config['market']['symbol']`
2. Create GBPUSD config section with correct pip-scale values
3. Adapt prompt text with instrument-specific thresholds
4. **Everything else works as-is** — the structure detection, pre-screening, batch mechanics, outcome evaluation, and reporting are all instrument-agnostic

---

---

## Addendum: Pressure Test Corrections

### Errors Found in Original Audit

**1. RR Safety Check — BLOCKING BUG DISCOVERED**

Both `batch_backtest.py:752` and `backtest_runner.py:681` have:
```python
if tp.risk_reward_ratio < 2.5:
    return f"rr_too_low: {tp.risk_reward_ratio:.1f}"
```

The prompt now instructs TP1 = 1.5× SL distance. If the AI outputs RR=1.5 (as instructed), the safety check would **reject every trade**. This was not a bug in past batches (which used the old 2.5R prompt), but is a **BLOCKING BUG for any future batch** using the 1.5R prompt.

Past batch results (March 2026 trades) confirm: the AI was still outputting RR=2.5 because those batches ran the OLD prompt. The 1.5R TP was validated via post-hoc simulation on r_path data, not by running the AI with a 1.5R prompt.

**Fix:** Change both lines to `if tp.risk_reward_ratio < 1.4:` (allows 1.5R with tolerance). **Must be fixed before any batch test.**

**2. SL Floor Safety Check — ALSO BLOCKING**

Both scripts have `if sl_distance < 5.0` which is `$5.00` for gold. For GBPUSD, a valid SL of 8 pips (0.0008) would be rejected as "below $5 minimum." This check needs to use the config's M15 ATR or a per-instrument floor.

**3. Spread Config Value — WRONG IN ORIGINAL REPORT**

I wrote `max_spread_cents: 2` for GBPUSD. The formula is `spread_cents = (ask - bid) * 100`. For GBPUSD with typical 1.5 pip spread: `0.00015 * 100 = 0.015`. Correct value is `max_spread_cents: 0.03` (not 2). My original was off by 100x.

**4. FVG Min Gap Values — UNDERESTIMATED**

I scaled linearly by arbitrary pip equivalents. Correct approach: scale by ADR ratio.
- Gold ADR: $60.6, GBPUSD ADR: 0.00877
- Scaling factor: 0.00877 / 60.6 = 0.0001447

Corrected FVG gaps:

| TF | Gold | GBPUSD (correct) | GBPUSD (my original) |
|----|------|-------------------|---------------------|
| D1 | 5.0 | 0.000724 (7.2 pips) | 0.0005 (5 pips) |
| H4 | 3.0 | 0.000434 (4.3 pips) | 0.0003 (3 pips) |
| H1 | 2.0 | 0.000290 (2.9 pips) | 0.0002 (2 pips) |
| M15 | 1.0 | 0.000145 (1.5 pips) | 0.0001 (1 pip) |

**5. M5 SL Floor — NEEDS EMPIRICAL OPTIMIZATION**

I wrote 0.001 (10 pips). By ADR scaling it should be ~0.00145 (14.5 pips). But the gold $10 floor was empirically optimized (tested at $3, $5, $8, $10, $12, $15). GBPUSD needs the same grid search — don't just guess from scaling.

**6. Confidence Scorer — WOULD SILENTLY FAIL**

`confidence_scorer.py` uses regex `\b(\d{4}\.\d{1,2})\b` filtered to range 1500-6000 to count gold price levels. GBPUSD prices (1.2XXX) would match ZERO levels, making the confidence scorer useless. Every trade would get LOW confidence. Not blocking for batch (confidence is logged only), but would break in production with `confidence_filter_mode: "active"`.

**7. Additional Hardcoded XAUUSD References — 22 locations total**

My original report said "one hardcoded line." The full grep found **22 locations** across 11 files:
- 6 BLOCKING for batch test (data loading + safety checks in both scripts)
- 8 FUNCTIONAL (prompt text across 5 files)
- 8 PRODUCTION-ONLY (execution, data ingestion, chart renderer, etc.)

### Corrected Summary

| Item | Status | Effort |
|------|--------|--------|
| GBPUSD data files | READY | 0 |
| **RR safety check (2.5 → 1.4)** | **BLOCKING BUG** | 5 min |
| **SL floor safety check ($5 → configurable)** | **BLOCKING BUG** | 10 min |
| Data loading hardcoded paths (2 files) | **NEEDS FIX** | 10 min |
| Config values (FVG gaps, spread, tolerance) | **NEEDS NEW CONFIG** (corrected values above) | 15 min |
| PA prompt (gold identity + dollar thresholds) | **NEEDS PARAMETERIZATION** | 30-60 min |
| M5 prompt ($1.50 buffer) | **NEEDS PARAMETERIZATION** | 15 min |
| Bull/Bear/Judge/Postmortem prompts | **NEEDS PARAMETERIZATION** | 15 min |
| Confidence scorer gold regex | **NEEDS FIX** (not blocking batch) | 15 min |
| Pre-screen logic | READY | 0 |
| Structure detection | READY | 0 |
| Outcome evaluation | READY | 0 |

**Total implementation effort: 3-4 hours (not 2-3 as originally stated).** The RR safety check is the most critical fix — without it, a 1.5R batch would produce zero trades.
