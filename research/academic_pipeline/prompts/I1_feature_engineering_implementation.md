# I1 — Feature Engineering Implementation (CLV + BVC + Session ATR)
## For: Claude Code execution agent (Sonnet, max effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor
## Basis: phase1_feature_engineering_papers_v1.md (L1 findings, 57 papers)
## WF-1 Status: CANCELLED — free to modify src/, prompts/, config

---

## Overview

Implement 3 new features in the Market State Object (MSO) based on L1 literature search findings. These features replace the information gap left by tick volume (which was never in the MSO but was identified as a missing signal by the research pipeline) with empirically-backed OHLCV-derived proxies.

**Changes:**
1. **CLV** (Close Location Value) — order flow proxy from price data alone (Ha & Hu 2017)
2. **BVC** (Bulk Volume Classification) — buy/sell volume classification (Easley et al. 2016)
3. **Session-specific ATR** — separate ATR for London, NY, and overlap sessions for gold (Ibikunle 2018)

**All changes are ADDITIVE** — no existing features are removed. The AI gets more information, not less.

---

## Data Discovery (verified April 11, 2026)

### What's already there

**OHLCV data flow:**
- `src/mt5/mt5_real.py` → pulls candles from MT5 with {time, open, high, low, close, volume}
- `src/components/data_ingestion.py:277` → converts tick_volume to "volume" field
- `src/components/market_state.py` → processes OHLCV into structural features (swings, OBs, FVGs, etc.)
- Volume is available in internal OHLCV but NOT passed to the AI prompt

**MSO → AI prompt pipeline:**
- `src/prompts/primary_analyzer_prompt.py:build_dynamic_context()` (line 432) → builds the H1/M15 dynamic section
- `src/prompts/primary_analyzer_prompt.py:_format_tf()` (line 340) → formats per-timeframe data
- Currently outputs: structure, breaks, OBs, breaker blocks, FVGs, P/D, avg body, ATR(14)
- **No volume, no flow proxies, no session-specific ATR**

**`src/prompts/primary_analyzer_prompt.py:build_static_context()` (line 397)** → builds D1/H4 + session levels. Changes per session, not per candle.

### Key file paths

| File | What to modify |
|------|---------------|
| `src/components/market_state.py` | Add CLV and BVC computation to the analyzer |
| `src/components/market_state_models.py` | Add new fields to the data models (if using Pydantic) |
| `src/prompts/primary_analyzer_prompt.py` | Add CLV, BVC, session ATR to `_format_tf()` output |
| `config/agent_config.yaml` | Add feature flags if needed |
| `tests/` | Add tests for new computations |

---

## Implementation 1: CLV (Close Location Value)

### What it is

CLV = (2 × Close - High - Low) / (High - Low)

Range: [-1, +1]. Positive = close near high (buying pressure). Negative = close near low (selling pressure). Zero = close at midpoint.

**Why it matters (L1 findings):** CLV requires ZERO volume data and measures closing position within the bar. It's a directional flow proxy that works on any OHLC data. (Ha & Hu 2017, standard microstructure reference)

### Where to compute it

In `src/components/market_state.py`, wherever per-candle OHLCV data is processed. The computation should happen on M15 candles (the evaluation timeframe) and optionally on H1 candles.

```python
def compute_clv(candle: dict) -> float:
    """Close Location Value: (2*C - H - L) / (H - L). Range [-1, +1]."""
    h = candle['high']
    l = candle['low']
    c = candle['close']
    if h == l:  # Doji — no range
        return 0.0
    return (2 * c - h - l) / (h - l)
```

### What to add to the MSO

Add to each timeframe's data:
- `clv_current` — CLV of the current (most recent) candle
- `clv_avg_5` — Average CLV over the last 5 candles (smoothed directional signal)

### How to display in the AI prompt

Add to the `_format_tf()` output, after the ATR line:

```python
# In _format_tf():
clv_current = tf_data.get("clv_current", None)
clv_avg_5 = tf_data.get("clv_avg_5", None)
if clv_current is not None:
    parts.append(f"  CLV: {clv_current:+.2f} (avg5: {clv_avg_5:+.2f})")
```

Example output: `CLV: +0.73 (avg5: +0.31)` — means current candle closed near its high, recent trend is mildly bullish.

---

## Implementation 2: BVC (Bulk Volume Classification)

### What it is

BVC classifies each bar's volume as buying or selling based on where the close falls relative to the open:

```python
from scipy.stats import norm

def compute_bvc(candle: dict, atr_14: float) -> float:
    """Bulk Volume Classification. Returns buy fraction [0, 1]."""
    o = candle['open']
    c = candle['close']
    v = candle.get('volume', 0)
    
    if atr_14 <= 0 or v <= 0:
        return 0.5  # No information
    
    # Sigma scaled to bar timeframe (M15 = 15/60 of hourly)
    sigma = atr_14 * (15 / 60) ** 0.5
    
    if sigma <= 0:
        return 0.5
    
    z = (c - o) / sigma
    buy_fraction = norm.cdf(z)  # P(buy | close > open, scaled by volatility)
    return buy_fraction
```

Buy volume = V × buy_fraction. Sell volume = V × (1 - buy_fraction).
Net flow = V × (2 × buy_fraction - 1). Positive = net buying.

**Why it matters (L1 findings):** BVC achieves ~76% accuracy for buy/sell classification on M15 data (Easley et al. 2016). Combined with CLV, it provides two independent flow signals from price data alone. (Q-1.7 recommendation: "Three implementable methods — CLV, BVC, EDGE")

**NOTE:** BVC uses the tick_volume field that's already in the internal OHLCV data (from data_ingestion.py). It does NOT add tick_volume to the MSO — it transforms it into a meaningful signal.

### Where to compute it

Same location as CLV — in market_state.py where per-candle OHLCV is processed. Requires ATR(14) to be computed first (it already is).

### What to add to the MSO

- `bvc_buy_fraction` — Current candle's buy fraction (0-1)
- `net_flow_5` — Cumulative net flow over last 5 candles: sum(V_i × (2 × buy_fraction_i - 1)). Positive = net buying pressure.

### How to display in the AI prompt

```python
# In _format_tf():
bvc = tf_data.get("bvc_buy_fraction", None)
net_flow = tf_data.get("net_flow_5", None)
if bvc is not None:
    flow_dir = "buy" if bvc > 0.6 else ("sell" if bvc < 0.4 else "neutral")
    parts.append(f"  Flow: {flow_dir} (BVC={bvc:.2f}, net5={net_flow:+.0f})")
```

Example output: `Flow: buy (BVC=0.82, net5=+4350)` — current candle is net buying, cumulative 5-bar flow is bullish.

### scipy dependency

BVC uses `scipy.stats.norm.cdf()`. Check if scipy is already a dependency:
```bash
grep -r "scipy" requirements.txt setup.py pyproject.toml
```

If not present: scipy is likely already installed (it's a dependency of many ML packages). If truly missing, add it. Alternatively, use a pure-Python approximation of the normal CDF:

```python
import math

def _norm_cdf(x: float) -> float:
    """Standard normal CDF approximation (Abramowitz & Stegun)."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
```

This avoids adding scipy as a dependency for one function.

---

## Implementation 3: Session-Specific ATR for Gold

### What it is

Instead of a single ATR(14) computed over all candles, compute separate ATR values for each session window. Gold has a documented W-shaped intraday volatility pattern (Ibikunle 2018):
- London open: HIGH volatility
- Pre-NY: moderate
- NY open: HIGH volatility (highest)
- Overlap close: declining
- Asian: LOW volatility

**Why it matters (L1 findings):** Using uniform ATR for SL/TP sizing is suboptimal for gold. London ATR is different from NY ATR. Session-specific ATR improves SL calibration. (Q-1.6: "Session-specific ATR normalization is the highest-priority gold feature")

### How to compute it

```python
def compute_session_atr(candles: list, session_hours: tuple, period: int = 14) -> float:
    """Compute ATR using only candles from the specified session hours (UTC).
    
    session_hours: (start_hour, end_hour) in UTC.
    For gold: london=(7,11), ny=(13,17), asian=(22,3)
    """
    session_candles = [
        c for c in candles 
        if _in_session(c['time'], session_hours)
    ]
    
    if len(session_candles) < period:
        return None  # Insufficient data
    
    # Standard ATR computation on session-filtered candles
    trs = []
    for i in range(1, len(session_candles)):
        h = session_candles[i]['high']
        l = session_candles[i]['low']
        prev_c = session_candles[i-1]['close']
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    
    # EMA-style ATR
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    
    return atr
```

### What to add to the MSO

For GOLD ONLY (XAUUSD):
- `atr_london` — ATR(14) using only London session candles
- `atr_ny` — ATR(14) using only NY session candles
- `session_vol_ratio` — Current session ATR / overall ATR (> 1.0 = more volatile than average)

For other instruments: keep the current uniform ATR(14). The session-specific feature is gold-specific based on documented microstructure differences (gold ξ=0.35 vs FX 0.16-0.22).

### How to display in the AI prompt

```python
# In _format_tf(), for gold only:
atr_session = tf_data.get("atr_session", None)  # Current session's ATR
vol_ratio = tf_data.get("session_vol_ratio", None)
if atr_session is not None and vol_ratio is not None:
    vol_label = "HIGH" if vol_ratio > 1.2 else ("low" if vol_ratio < 0.8 else "normal")
    parts.append(f"  Session ATR: {atr_session:{_PRICE_FMT}} ({vol_label}, {vol_ratio:.1f}x avg)")
```

Example: `Session ATR: 8.52 (HIGH, 1.4x avg)` — NY session is 40% more volatile than overall average.

### Instrument check

The gold-specific behavior should be gated on the instrument:

```python
# In market_state.py or wherever session ATR is computed:
if symbol == "XAUUSD":
    compute_session_specific_atr(...)
```

---

## Testing Requirements

### Unit tests (add to `tests/`)

1. **CLV computation:**
   - Candle closing at high → CLV = +1.0
   - Candle closing at low → CLV = -1.0
   - Candle closing at midpoint → CLV = 0.0
   - Doji (high == low) → CLV = 0.0

2. **BVC computation:**
   - Large bullish candle (close >> open) → buy_fraction > 0.8
   - Large bearish candle (close << open) → buy_fraction < 0.2
   - Doji → buy_fraction ≈ 0.5
   - Zero volume → buy_fraction = 0.5

3. **Session ATR:**
   - With synthetic candles: session-filtered ATR should differ from overall ATR
   - Edge case: fewer than 14 session candles → returns None

4. **Prompt formatting:**
   - Verify CLV, BVC, and session ATR appear in _format_tf output
   - Verify they don't appear when data is missing (None)

### Integration test

Run the system on one historical XAUUSD MSO and verify:
- CLV and BVC values are reasonable (CLV in [-1, 1], BVC in [0, 1])
- Session ATR is computed for the active session
- The formatted prompt includes the new features
- No existing tests break

### Regression safety

```bash
pytest tests/ -v
```

All existing tests must pass after changes. If any test fails: fix the test or the implementation, do not skip.

---

## Shadow logging

Before these features affect live AI decisions, they should be logged to verify they carry signal:

1. Add the new features to the session log JSON (knowledge_base/sessions/)
2. After 50+ evaluations with new features: compute Spearman correlation between CLV/BVC/session_ATR and trade outcomes
3. If no feature has ρ > 0.05 after 50 trades: the features are noise. Remove from the prompt to reduce token count.

This is natural validation — the features appear in the prompt, the AI may or may not use them, and we measure whether trades taken with these features visible have different outcomes.

---

## Output Files

Modified files (expected):
- `src/components/market_state.py` — new computation functions
- `src/components/market_state_models.py` — new model fields (if Pydantic models are used)
- `src/prompts/primary_analyzer_prompt.py` — `_format_tf()` additions
- `tests/test_market_state.py` (or new file) — unit tests for CLV, BVC, session ATR

Do NOT modify:
- `config/agent_config.yaml` (no feature flags needed — features are always computed)
- Any file in `knowledge_base/` or `pipeline_state/`

---

## Constraints

- **Do NOT remove existing features** — this is purely additive
- **Do NOT change the AI prompt instructions** (U1-U7, OB1-OB7). Only add new data fields to the MSO context.
- **Do NOT add tick_volume to the AI prompt** — it was confirmed as noise by L1. Only add DERIVED features (CLV, BVC, session ATR).
- **Session ATR is GOLD-ONLY.** Other instruments keep uniform ATR(14).
- **Avoid adding scipy as a dependency** if it's not already present — use the pure-Python norm CDF approximation instead.
- **All existing tests must pass** after implementation.
- **seed=42** if any randomization is needed (there shouldn't be).

---

## Prerequisites (execution agent must complete before starting)

### Required Codebase Reading (read BEFORE writing any code)

1. **`src/components/market_state.py`** — Read in full. Understand:
   - How per-candle OHLCV data flows through the analyzer
   - Where structural features (swings, OBs, FVGs) are computed
   - How data is assembled into the MSO dict
   - Where ATR(14) is currently computed (you'll need it for BVC sigma scaling)
   - The existing code style, naming conventions, and patterns

2. **`src/components/market_state_models.py`** — Read in full. Understand:
   - Whether Pydantic models are used (add new fields there if so)
   - Existing field naming conventions (snake_case, type annotations)
   - How the model structure maps to the data flow in market_state.py

3. **`src/prompts/primary_analyzer_prompt.py`** — Read these specific sections:
   - `_format_tf()` at line 340 — this is where you ADD the CLV/BVC/session ATR output lines
   - `build_dynamic_context()` at line 432 — understand how H1/M15 data is assembled
   - `_PRICE_FMT` variable — use this for formatting session ATR values
   - Look at how existing fields (ATR, avg body) are formatted as a style template

4. **`src/components/data_ingestion.py`** — Read line ~277. Understand:
   - How tick_volume becomes the internal "volume" field
   - This is the volume value BVC will use — it's available in the candle dict as `candle['volume']`

5. **`config/agent_config.yaml`** — Read to verify no feature flags are needed (per Constraints)

6. **`tests/`** — Run `ls tests/` and read at least one existing test file to understand:
   - Test style (pytest fixtures, assertion patterns, mocking approach)
   - File naming convention for new test files

### Environment Check
```bash
# Check if scipy is already a dependency
grep -r "scipy" requirements.txt setup.py pyproject.toml 2>/dev/null

# If NOT found: use the pure-Python _norm_cdf() approximation (provided in Implementation 2)
# Do NOT add scipy as a new dependency for one function
```

### Testing
```bash
# After all implementation, run:
pytest tests/ -v

# ALL existing tests must pass. If any fail: fix the implementation or the test.
# Do not skip tests.
```

### Key Code Patterns to Match

When adding to `_format_tf()`, follow the existing pattern:
```python
# Existing pattern (from the file):
atr = tf_data.get("atr_14", None)
if atr is not None:
    parts.append(f"  ATR(14): {atr:{_PRICE_FMT}}")

# Your additions follow the same pattern: .get() with None check, then parts.append()
```

When adding computation functions to `market_state.py`, follow existing patterns:
- Functions should be pure (input → output, no side effects)
- Handle edge cases (doji, zero volume, insufficient data) with explicit returns
- Type hints if the file uses them
- No global state

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Original I1 was "kill tick volume from MSO" → Verified tick volume is NOT in the MSO. Reframed as ADD features.
2. BVC requires scipy.stats.norm → Added pure-Python fallback to avoid dependency issues.
3. Session-specific ATR applied to all instruments → Restricted to XAUUSD only (gold-specific microstructure per L1 Q-1.6).
4. Missing integration test → Added verification step on historical XAUUSD MSO.
5. No shadow logging → Added natural validation: log features, measure correlation after 50 trades.
6. Missing edge cases in CLV (doji) and BVC (zero volume) → Added explicit handling.
7. Format string in prompt didn't specify precision → Used existing _PRICE_FMT for consistency.
8. Net flow computation unclear for BVC → Added explicit formula: sum(V_i × (2 × buy_fraction_i - 1)).
9. No gate for removing useless features → Added: if ρ < 0.05 after 50 trades, remove from prompt.
10. Missing prerequisites section → Added: codebase reading list, environment check, testing instructions, code pattern guidance.
