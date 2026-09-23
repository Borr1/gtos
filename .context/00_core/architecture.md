# XAUUSD Autonomous AI Trading Agent — Architecture Document

**Version:** 1.0  
**Date:** 2026-03-28  
**Status:** Design Complete — Ready for Phase 1 Implementation  
**Model:** Model A — London Open Liquidity Sweep  
**Market:** XAUUSD Only

---

## Table of Contents

1. [System Component Diagram & Data Flows](#1-system-component-diagram--data-flows)
2. [Detailed Component Specifications](#2-detailed-component-specifications)
3. [Data Model Definitions](#3-data-model-definitions)
4. [Trade Lifecycle State Machine](#4-trade-lifecycle-state-machine)
5. [AI Prompt Architecture](#5-ai-prompt-architecture)
6. [Three-Layer Retrieval System Design](#6-three-layer-retrieval-system-design)
7. [Sequence Diagrams](#7-sequence-diagrams)
8. [File-on-Disk Pipeline State Diagram](#8-file-on-disk-pipeline-state-diagram)
9. [Testing Strategy](#9-testing-strategy)
10. [Risk & Failure Mode Analysis](#10-risk--failure-mode-analysis)

---

## 1. System Component Diagram & Data Flows

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPONENT 8 — SESSION ORCHESTRATOR                      │
│                        (Main Loop / Coordinator)                            │
│   Initializes at 06:45 UTC. Drives the pipeline on every M15 candle close. │
│   Manages lifecycle transitions. Coordinates crash recovery.                │
│   PID-locked: knowledge_base/meta/.orchestrator.lock                       │
└─────┬──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┘
      │          │          │          │          │          │
      ▼          ▼          ▼          │          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐│   ┌──────────┐ ┌──────────┐
│COMPONENT │ │COMPONENT │ │COMPONENT ││   │COMPONENT │ │COMPONENT │
│    1     │ │    2     │ │   3A     ││   │    5     │ │    7     │
│  Data    │→│ Market   │→│ Primary  ││   │Knowledge │ │Monitoring│
│Ingestion │ │  State   │ │ Analyzer ││   │  Base    │ │& Alerting│
│          │ │ Analyzer │ │  (AI)    ││   │(Memory)  │ │Dashboard │
└──────────┘ └──────────┘ └────┬─────┘│   └─────┬────┘ └──────────┘
                               │      │         │
                    ┌──────────┘      │         │
                    │ CANDIDATE?      │         │
                    ▼ YES             │         │
              ┌──────────┐            │   ┌─────┴────┐
              │COMPONENT │            │   │COMPONENT │
              │   3B     │            │   │    6     │
              │Bull/Bear │            │   │Adaptive  │
              │ Debate   │            │   │ Review   │
              └────┬─────┘            │   └──────────┘
                   │                  │
                   │ APPROVE?         │
                   ▼ YES              │
              ┌──────────┐            │
              │COMPONENT │            │
              │    4     │◄───────────┘
              │Execution │   (safety checks)
              │ Engine   │
              └──────────┘
```

### 1.2 Data Flow — Per-Candle Pipeline

```
MT5 Server
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Component 1: Data Ingestion                                  │
│  Pulls: OHLCV (D1, H4, H1, M15), spread, econ calendar     │
│  Calculates: Asian H/L, PDH/PDL, session H/L                │
│  Writes: pipeline_state/01_raw_data.json                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Component 2: Market State Analyzer (NO AI — pure Python)     │
│  Computes: swings, structure sequence, BOS/CHoCH, OBs, FVGs │
│  Computes: premium/discount zones, liquidity pools, sweeps   │
│  Writes: pipeline_state/02_market_state.json                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┤ (Three-Layer Retrieval injected here)
            │              │
            ▼              ▼
┌────────────────┐  ┌─────────────────────────────────────────┐
│ Component 5    │  │ Component 3A: Primary Analyzer (AI)      │
│ Knowledge Base │  │  Receives: Market State + KB Context      │
│                │  │  Evaluates: Model A Steps 1–7             │
│ Layer 1: Index │──│  Outputs: NO_TRADE / WAIT / CANDIDATE     │
│ Layer 2: YAML  │  │  Writes: pipeline_state/03a_primary.json  │
│ Layer 3: Lance │  └──────────────────┬──────────────────────┘
└────────────────┘                     │
                                       │
                          ┌────────────┴──── decision == CANDIDATE?
                          │                        │
                          │ NO (NO_TRADE/WAIT)      │ YES
                          ▼                        ▼
                   ┌─────────────┐    ┌───────────────────────────────┐
                   │ Log to      │    │ Component 3B: Bull/Bear Debate │
                   │ no_trades/  │    │                                │
                   │ or session  │    │  ┌────────┐    ┌────────┐     │
                   │ manifest    │    │  │  BULL  │    │  BEAR  │     │
                   └─────────────┘    │  │ Agent  │    │ Agent  │     │
                                      │  └───┬────┘    └───┬────┘     │
                                      │      │  Round 1    │          │
                                      │      ▼             ▼          │
                                      │  ┌─────────────────────┐      │
                                      │  │ 03b_debate_r1.json  │      │
                                      │  └─────────┬───────────┘      │
                                      │            │                  │
                                      │     (Round 2 if enabled)      │
                                      │            │                  │
                                      │            ▼                  │
                                      │  ┌─────────────────────┐      │
                                      │  │      JUDGE          │      │
                                      │  │  Evaluates args     │      │
                                      │  │  Outputs verdict    │      │
                                      │  └─────────┬───────────┘      │
                                      │            │                  │
                                      └────────────┼──────────────────┘
                                                   │
                                      ┌────────────┴────────────┐
                                      │                         │
                                APPROVE (≥70)             REJECT
                                      │                         │
                                      ▼                         ▼
                            ┌──────────────────┐    ┌──────────────────┐
                            │ Deterministic    │    │ Log REJECTED     │
                            │ Safety Checks    │    │ + full debate    │
                            │ • spread < 30¢   │    │ transcript       │
                            │ • daily loss < 2%│    └──────────────────┘
                            │ • trade count < 1│
                            │ • RR ≥ 1:3       │
                            └────────┬─────────┘
                                     │
                              ALL PASS?
                                     │
                            YES      │      NO
                             │       │       │
                             ▼       │       ▼
                   ┌──────────────┐  │  ┌──────────────┐
                   │ Component 4  │  │  │ REJECTED     │
                   │ Execution    │  │  │ (safety fail)│
                   │ Engine       │  │  └──────────────┘
                   │ → MT5 order  │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ ACTIVE trade │
                   │ • Monitor    │
                   │ • Partials   │
                   │ • Trail SL   │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ CLOSED       │
                   │ → Postmortem │
                   │ → LanceDB   │
                   │ → Stats     │
                   └──────────────┘
```

### 1.3 Three-Layer Retrieval Data Flow

```
┌──────────────────────── BEFORE EACH PRIMARY ANALYSIS ──────────────────────┐
│                                                                             │
│  Layer 1: Structured Query                                                  │
│  ┌──────────────────────────────────┐                                       │
│  │ index/_trade_index.json          │→ Last 10 trade outcomes               │
│  │ statistics/rolling_stats.json    │→ Win rate, expectancy, drawdown       │
│  │ patterns/failure_patterns.json   │→ Active failure patterns              │
│  │ statistics/regime_analysis.json  │→ Current regime classification        │
│  │ rules/pending_reviews.yaml       │→ Pending rule reviews                 │
│  └──────────────────────────────────┘                                       │
│                                                                             │
│  Layer 2: Compressed Insights                                               │
│  ┌──────────────────────────────────┐                                       │
│  │ insights/current_insights.yaml   │→ Distilled condition performance      │
│  │                                  │  (full file, ~2KB, fits in prompt)    │
│  └──────────────────────────────────┘                                       │
│                                                                             │
│  Layer 3: Vector Similarity                                                 │
│  ┌──────────────────────────────────┐                                       │
│  │ Current market conditions        │                                       │
│  │        ↓ embed()                 │                                       │
│  │ [0.12, -0.34, 0.56, ...]        │                                       │
│  │        ↓ query LanceDB           │                                       │
│  │ Top 3-5 similar historical trades│→ Trade ID, outcome, R, postmortem    │
│  └──────────────────────────────────┘                                       │
│                                                                             │
│  All three layers assembled into a single context block                     │
│  Injected into Component 3A (Primary Analyzer) prompt                       │
│  Also available to Component 3B (Bull/Bear agents)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Component Specifications

### 2.1 Component 1 — Data Ingestion Layer

**Purpose:** Feed the agent clean, structured market data across all required timeframes.

**Model Tier:** None — pure Python, no AI.

**Dependencies:**
- `MetaTrader5` Python package (v5.0.5640+)
- MT5 terminal running and connected to broker
- System clock synchronized to UTC

**Inputs:**
- MT5 connection handle (initialized by Component 8)
- Current UTC timestamp
- Configuration: lookback periods per timeframe, equal-high/low tolerance ($2.50 default), Asian session bounds (00:00–07:00 UTC)

**Internal Logic:**

```python
# Pseudocode — Data Ingestion per M15 candle close

def ingest(mt5_handle, config):
    data = {}
    
    # 1. Pull OHLCV candles
    for tf in [TIMEFRAME_D1, TIMEFRAME_H4, TIMEFRAME_H1, TIMEFRAME_M15]:
        lookback = config.lookback[tf]  # D1:30, H4:80, H1:168, M15:672
        candles = mt5.copy_rates_from_pos("XAUUSD", tf, 0, lookback)
        if candles is None or len(candles) < lookback * 0.9:
            raise DataIncompleteError(f"Missing candles on {tf}")
        data[tf] = candles_to_list(candles)  # Convert to list of dicts
    
    # 2. Calculate session levels
    today_utc = current_utc_date()
    asian_candles = filter_candles(data[M15], start="00:00", end="07:00", date=today_utc)
    data["asian_high"] = max(c["high"] for c in asian_candles)
    data["asian_low"] = min(c["low"] for c in asian_candles)
    
    yesterday_candles = filter_candles(data[M15], date=today_utc - 1day)
    data["pdh"] = max(c["high"] for c in yesterday_candles)
    data["pdl"] = min(c["low"] for c in yesterday_candles)
    
    current_session = filter_candles(data[M15], start="07:00", end=now(), date=today_utc)
    data["session_high"] = max(c["high"] for c in current_session) if current_session else None
    data["session_low"] = min(c["low"] for c in current_session) if current_session else None
    
    # 3. Identify equal highs/lows across each timeframe
    for tf in [H4, H1]:
        swings = detect_swings(data[tf])
        data[f"equal_highs_{tf}"] = find_equal_levels(
            [s for s in swings if s["type"] == "high"],
            tolerance=config.equal_tolerance  # $2.50
        )
        data[f"equal_lows_{tf}"] = find_equal_levels(
            [s for s in swings if s["type"] == "low"],
            tolerance=config.equal_tolerance
        )
    
    # 4. Current spread
    tick = mt5.symbol_info_tick("XAUUSD")
    data["spread_cents"] = (tick.ask - tick.bid) * 100  # Convert to cents
    
    # 5. Economic calendar — high-impact USD events in next 24h
    cal_start = datetime.utcnow()
    cal_end = cal_start + timedelta(hours=24)
    events = mt5.calendar_get(cal_start, cal_end)
    data["high_impact_events"] = [
        {"name": e.name, "time": e.time.isoformat(), "importance": e.importance}
        for e in events
        if e.importance == 3 and "USD" in e.currency
    ]
    
    # 6. Data quality flags
    data["data_quality"] = {
        "all_timeframes_complete": True,  # or False with details
        "spread_normal": data["spread_cents"] <= 30,
        "mt5_connected": True,
        "timestamp_utc": datetime.utcnow().isoformat()
    }
    
    return data
```

**Output:** `pipeline_state/01_raw_data.json`

```json
{
  "timestamp_utc": "2026-03-28T07:15:00Z",
  "candles": {
    "D1": [ /* last 30 daily candles as {time, open, high, low, close, volume} */ ],
    "H4": [ /* last 80 H4 candles */ ],
    "H1": [ /* last 168 H1 candles */ ],
    "M15": [ /* last 672 M15 candles */ ]
  },
  "session_levels": {
    "asian_high": 3045.20,
    "asian_low": 3038.50,
    "pdh": 3052.80,
    "pdl": 3030.10,
    "session_high": 3046.00,
    "session_low": 3039.75
  },
  "equal_highs_H4": [ {"price": 3050.30, "count": 2, "candle_indices": [12, 28]} ],
  "equal_lows_H4": [],
  "equal_highs_H1": [ {"price": 3048.10, "count": 3, "candle_indices": [5, 22, 41]} ],
  "equal_lows_H1": [],
  "spread_cents": 18.5,
  "high_impact_events": [],
  "data_quality": {
    "all_timeframes_complete": true,
    "spread_normal": true,
    "mt5_connected": true,
    "timestamp_utc": "2026-03-28T07:15:00Z"
  }
}
```

**Error Handling:**
- MT5 connection failure: retry 3× with 5-second delay. If failed, log `{"error": "mt5_connection_failed", "retries": 3}` to `pipeline_state/01_raw_data.json` and set `data_quality.mt5_connected = false`. Orchestrator skips this candle.
- Incomplete data (fewer candles than 90% of lookback): log warning in `data_quality`, set `all_timeframes_complete = false` with details of which timeframes are short. Let Component 3A decide whether to proceed.
- Calendar API failure: non-critical. Log warning, set `high_impact_events = null` (not empty list — null means "unknown," empty means "confirmed no events"). Primary Analyzer treats null as "assume risk exists."
- Spread data unavailable: set `spread_cents = null`. Deterministic safety check in Component 4 blocks execution if spread is null.

---

### 2.2 Component 2 — Market State Analyzer

**Purpose:** Transform raw OHLCV into structured market context. All computations are deterministic — no AI.

**Model Tier:** None — pure Python.

**Dependencies:**
- Component 1 output (`01_raw_data.json`)
- `numpy` for numerical operations

**Inputs:**
- Parsed `01_raw_data.json`
- Configuration: swing detection parameters, FVG minimum gap size ($1.00 on gold M15, $3.00 on H4), OB freshness lookback

**Internal Logic — Key Algorithms:**

**Swing Detection (per timeframe):**
```python
def detect_swings(candles, min_bars=2):
    """
    A swing high: candle[i].high > candle[i-1].high AND candle[i].high > candle[i+1].high
    (minimum 2 candles on each side for higher timeframes)
    A swing low: mirror logic on lows.
    Returns list of {"index": int, "type": "high"|"low", "price": float, "time": str}
    """
    swings = []
    for i in range(min_bars, len(candles) - min_bars):
        # Check if all `min_bars` candles on both sides have lower highs
        is_swing_high = all(
            candles[i]["high"] > candles[i-j]["high"] and
            candles[i]["high"] > candles[i+j]["high"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_high:
            swings.append({"index": i, "type": "high", "price": candles[i]["high"],
                           "time": candles[i]["time"]})
        
        is_swing_low = all(
            candles[i]["low"] < candles[i-j]["low"] and
            candles[i]["low"] < candles[i+j]["low"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_low:
            swings.append({"index": i, "type": "low", "price": candles[i]["low"],
                           "time": candles[i]["time"]})
    
    return sorted(swings, key=lambda s: s["index"])
```

**Structure Sequence Identification:**
```python
def identify_structure(swings):
    """
    Walk through alternating swing highs/lows.
    Compare each high to previous high, each low to previous low.
    Returns: "bullish" (HH+HL), "bearish" (LH+LL), or "transitional"
    Also returns: protected_swing, last_bos, last_choch
    """
    highs = [s for s in swings if s["type"] == "high"]
    lows = [s for s in swings if s["type"] == "low"]
    
    if len(highs) < 2 or len(lows) < 2:
        return {"direction": "insufficient_data", "protected_swing": None}
    
    # Compare last 3-4 swing pairs
    hh_count = sum(1 for i in range(1, len(highs)) if highs[i]["price"] > highs[i-1]["price"])
    ll_count = sum(1 for i in range(1, len(lows)) if lows[i]["price"] < lows[i-1]["price"])
    hl_count = sum(1 for i in range(1, len(lows)) if lows[i]["price"] > lows[i-1]["price"])
    lh_count = sum(1 for i in range(1, len(highs)) if highs[i]["price"] < highs[i-1]["price"])
    
    recent_pairs = min(3, len(highs)-1, len(lows)-1)
    
    if hh_count >= recent_pairs and hl_count >= recent_pairs:
        direction = "bullish"
        protected_swing = lows[-1]  # Last HL
    elif ll_count >= recent_pairs and lh_count >= recent_pairs:
        direction = "bearish"
        protected_swing = highs[-1]  # Last LH
    else:
        direction = "transitional"
        protected_swing = None  # Ambiguous
    
    return {
        "direction": direction,
        "protected_swing": protected_swing,
        "swing_sequence": classify_each_swing(swings),  # List of HH/HL/LH/LL labels
        "hh_count": hh_count,
        "hl_count": hl_count,
        "lh_count": lh_count,
        "ll_count": ll_count
    }
```

**BOS / CHoCH Detection:**
```python
def detect_structure_breaks(candles, swings, structure):
    """
    BOS: candle body closes beyond the most recent swing in the trend direction
      - Bullish BOS: body close above most recent swing high
      - Bearish BOS: body close below most recent swing low
    CHoCH: candle body closes beyond the protected swing (against the trend)
      - Bullish structure CHoCH: body close below protected HL
      - Bearish structure CHoCH: body close above protected LH
    
    Returns list of events with type, price, candle_index, timestamp
    """
    events = []
    for i, candle in enumerate(candles):
        # Check for BOS
        if structure["direction"] == "bullish":
            recent_high = get_most_recent_swing_high(swings, before_index=i)
            if recent_high and candle["close"] > recent_high["price"]:
                events.append({
                    "type": "BOS",
                    "direction": "bullish",
                    "level_broken": recent_high["price"],
                    "close_price": candle["close"],
                    "candle_index": i,
                    "time": candle["time"]
                })
        
        # Check for CHoCH
        if structure["protected_swing"]:
            ps = structure["protected_swing"]
            if structure["direction"] == "bullish" and candle["close"] < ps["price"]:
                events.append({
                    "type": "CHoCH",
                    "direction": "bearish",
                    "level_broken": ps["price"],
                    "close_price": candle["close"],
                    "candle_index": i,
                    "time": candle["time"]
                })
            elif structure["direction"] == "bearish" and candle["close"] > ps["price"]:
                events.append({
                    "type": "CHoCH",
                    "direction": "bullish",
                    "level_broken": ps["price"],
                    "close_price": candle["close"],
                    "candle_index": i,
                    "time": candle["time"]
                })
    
    return events
```

**Order Block Identification:**
```python
def identify_order_blocks(candles, structure_events):
    """
    For each BOS event with displacement:
      - Bullish OB: last bearish (close < open) candle before the displacement up-move
      - Bearish OB: last bullish (close > open) candle before the displacement down-move
    OB is only valid if unmitigated (price hasn't returned to the zone since formation)
    
    Returns list of OBs with: type, high, low, formation_index, mitigated (bool)
    """
    obs = []
    for event in structure_events:
        if event["type"] != "BOS":
            continue
        bos_idx = event["candle_index"]
        
        if event["direction"] == "bullish":
            # Walk backward to find last bearish candle
            for j in range(bos_idx - 1, max(bos_idx - 10, 0), -1):
                if candles[j]["close"] < candles[j]["open"]:  # Bearish candle
                    ob = {
                        "type": "bullish",
                        "high": candles[j]["high"],
                        "low": candles[j]["low"],
                        "open": candles[j]["open"],
                        "close": candles[j]["close"],
                        "formation_index": j,
                        "formation_time": candles[j]["time"],
                        "causing_bos_index": bos_idx
                    }
                    # Check if mitigated
                    ob["mitigated"] = any(
                        candles[k]["low"] <= ob["high"]
                        for k in range(bos_idx + 1, len(candles))
                    )
                    obs.append(ob)
                    break
        # Mirror for bearish
    
    return obs
```

**Fair Value Gap Detection:**
```python
def identify_fvgs(candles, min_gap_size):
    """
    FVG: 3-candle pattern where candle[i-1].high < candle[i+1].low (bullish)
    or candle[i-1].low > candle[i+1].high (bearish).
    The gap is the space between those two wicks.
    
    Returns list of FVGs with: type, top, bottom, midpoint, candle_indices, filled (bool)
    """
    fvgs = []
    for i in range(1, len(candles) - 1):
        # Bullish FVG: gap between candle[i-1] high and candle[i+1] low
        gap = candles[i+1]["low"] - candles[i-1]["high"]
        if gap >= min_gap_size:
            fvg = {
                "type": "bullish",
                "top": candles[i+1]["low"],
                "bottom": candles[i-1]["high"],
                "midpoint": (candles[i+1]["low"] + candles[i-1]["high"]) / 2,
                "candle_indices": [i-1, i, i+1],
                "formation_time": candles[i]["time"]
            }
            # Check if filled
            fvg["filled"] = any(
                candles[k]["low"] <= fvg["bottom"]
                for k in range(i+2, len(candles))
            )
            fvgs.append(fvg)
        
        # Bearish FVG
        gap = candles[i-1]["low"] - candles[i+1]["high"]
        if gap >= min_gap_size:
            fvg = {
                "type": "bearish",
                "top": candles[i-1]["low"],
                "bottom": candles[i+1]["high"],
                "midpoint": (candles[i-1]["low"] + candles[i+1]["high"]) / 2,
                "candle_indices": [i-1, i, i+1],
                "formation_time": candles[i]["time"]
            }
            fvg["filled"] = any(
                candles[k]["high"] >= fvg["top"]
                for k in range(i+2, len(candles))
            )
            fvgs.append(fvg)
    
    return fvgs
```

**Premium/Discount Zone Calculation:**
```python
def calculate_premium_discount(swings, structure):
    """
    Find the most recent impulse leg (swing low to swing high in bullish, vice versa).
    Calculate Fibonacci retracement levels: 0%, 50% (equilibrium), 62%, 79%, 100%.
    
    Premium = above 50%. Discount = below 50%.
    OTE zone = 62%–79%.
    """
    if structure["direction"] == "bullish":
        # Most recent: low (start of impulse) to high (end of impulse)
        recent_low = get_last_swing_low(swings)
        recent_high = get_last_swing_high(swings)
        if not recent_low or not recent_high:
            return None
        impulse_range = recent_high["price"] - recent_low["price"]
        return {
            "impulse_low": recent_low["price"],
            "impulse_high": recent_high["price"],
            "equilibrium_50": recent_high["price"] - impulse_range * 0.50,
            "fib_62": recent_high["price"] - impulse_range * 0.618,
            "fib_79": recent_high["price"] - impulse_range * 0.786,
            "discount_zone": {"top": recent_high["price"] - impulse_range * 0.50,
                              "bottom": recent_low["price"]},
            "premium_zone": {"top": recent_high["price"],
                             "bottom": recent_high["price"] - impulse_range * 0.50},
            "ote_zone": {"top": recent_high["price"] - impulse_range * 0.618,
                         "bottom": recent_high["price"] - impulse_range * 0.786}
        }
    # Mirror for bearish
```

**Liquidity Sweep Detection:**
```python
def detect_sweeps(candles, liquidity_pools):
    """
    For each liquidity pool, check if any recent candle wicked beyond it
    but the body closed back inside.
    
    Sweep = wick beyond + body close inside = grab and reverse signal
    Run = body close beyond + follow-through = genuine breakout
    """
    sweeps = []
    for pool in liquidity_pools:
        for i in range(len(candles) - 10, len(candles)):  # Last 10 candles
            c = candles[i]
            if pool["side"] == "high":
                if c["high"] > pool["price"] and max(c["open"], c["close"]) < pool["price"]:
                    sweeps.append({
                        "pool": pool,
                        "type": "sweep",
                        "wick_extreme": c["high"],
                        "body_close": c["close"],
                        "candle_index": i,
                        "time": c["time"]
                    })
                elif c["close"] > pool["price"]:
                    sweeps.append({
                        "pool": pool,
                        "type": "run",
                        "close_price": c["close"],
                        "candle_index": i,
                        "time": c["time"]
                    })
            # Mirror for low-side pools
    
    return sweeps
```

**Average Candle Body Size (rolling 20-period):**
```python
def avg_candle_body(candles, period=20):
    recent = candles[-period:]
    bodies = [abs(c["close"] - c["open"]) for c in recent]
    return sum(bodies) / len(bodies)
```

**Output:** `pipeline_state/02_market_state.json` — the Market State Object. Full schema defined in Section 3.

**Error Handling:**
- If `01_raw_data.json` is missing or corrupt: raise `PipelineError`, orchestrator logs and skips candle.
- If swing detection produces fewer than 4 swings on a timeframe: mark that timeframe's structure as `"insufficient_data"`. Primary Analyzer decides whether to proceed.
- Division by zero in Fib calculation (impulse range = 0): mark premium/discount as `null`.

---

### 2.3 Component 3A — Primary Analyzer (AI Reasoning Engine)

**Purpose:** Evaluate the Market State Object against Model A criteria using contextual SMC reasoning.

**Model Tier:** `claude-opus-4-6` or `claude-sonnet-4-20250514` (test both in Phase 1; use whichever delivers higher accuracy within 5% margin, defaulting to Sonnet for cost if tie).

**Dependencies:**
- Component 2 output (`02_market_state.json`)
- Component 5 output (three-layer retrieval context)
- Anthropic API client
- Model A rules (embedded in system prompt)

**Inputs:**
- Market State Object (full JSON)
- Knowledge Base context block (assembled by retrieval system):
  - Layer 1: Last 10 trades, rolling stats, failure patterns, regime
  - Layer 2: `current_insights.yaml` contents
  - Layer 3: Top 3–5 similar historical setups from LanceDB

**Internal Logic:**
1. Assemble the prompt (see Section 5 for full prompt architecture).
2. Call Claude API with structured output enforcement (JSON mode).
3. Parse response. Validate against expected schema.
4. If response is malformed: retry once with explicit format correction appended.
5. If still malformed: log error, output `NO_TRADE` with `"reason": "ai_output_malformed"`.
6. Write output to `pipeline_state/03a_primary_analysis.json`.

**Output Schema:** Full Primary Analysis Output — defined in Section 3.

**Error Handling:**
- API timeout (>30 seconds): retry once. If failed, output `NO_TRADE` with `"reason": "api_timeout"`.
- API rate limit: wait `Retry-After` header duration, retry once.
- Malformed JSON response: retry with format correction. If still malformed, `NO_TRADE`.
- API returns 500: retry once after 5 seconds. If persistent, `NO_TRADE`.
- Every error is logged to `pipeline_state/03a_primary_analysis.json` with full error details so the session manifest captures it.

---

### 2.4 Component 3B — Bull/Bear Debate

**Purpose:** Subject CANDIDATE trades to adversarial debate. Confirmation bias prevention mechanism.

**Model Tier:** Same as Component 3A (must match reasoning quality).

**Dependencies:**
- Component 3A output (must be `CANDIDATE`)
- Component 2 output (Market State Object)
- Component 5 output (three-layer retrieval context)
- Anthropic API client

**Activation Gate:** Only fires when `03a_primary_analysis.json` contains `"decision": "CANDIDATE"`. On `NO_TRADE` or `WAIT`, this component is not invoked — saving API costs.

**Internal Logic:**

```python
async def run_debate(market_state, primary_analysis, kb_context, config):
    # Round 1 — Bull and Bear run concurrently
    bull_task = asyncio.create_task(
        call_claude(
            system_prompt=BULL_SYSTEM_PROMPT,
            user_content=format_bull_input(market_state, primary_analysis, kb_context),
            model=config.debate_model
        )
    )
    bear_task = asyncio.create_task(
        call_claude(
            system_prompt=BEAR_SYSTEM_PROMPT,
            user_content=format_bear_input(market_state, primary_analysis, kb_context),
            model=config.debate_model
        )
    )
    
    bull_r1, bear_r1 = await asyncio.gather(bull_task, bear_task)
    write_json("pipeline_state/03b_debate_round1.json", {
        "bull_argument": bull_r1, "bear_argument": bear_r1
    })
    
    # Round 2 — Rebuttals (if enabled)
    round2 = None
    if config.debate_round2_enabled:
        bull_rebuttal = await call_claude(
            system_prompt=BULL_REBUTTAL_PROMPT,
            user_content=format_rebuttal_input(bull_r1, bear_r1, "bull"),
            model=config.debate_model
        )
        bear_rebuttal = await call_claude(
            system_prompt=BEAR_REBUTTAL_PROMPT,
            user_content=format_rebuttal_input(bear_r1, bull_r1, "bear"),
            model=config.debate_model
        )
        round2 = {"bull_rebuttal": bull_rebuttal, "bear_rebuttal": bear_rebuttal}
        write_json("pipeline_state/03b_debate_round2.json", round2)
    
    # Judge — Final verdict (always sequential)
    verdict = await call_claude(
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_content=format_judge_input(primary_analysis, bull_r1, bear_r1, round2),
        model=config.debate_model
    )
    write_json("pipeline_state/03b_verdict.json", verdict)
    
    return verdict
```

**Decision Logic (deterministic, post-verdict):**
```python
def evaluate_verdict(verdict):
    if verdict["verdict"] == "REJECT":
        return "REJECTED"
    
    if verdict["verdict"] == "APPROVE":
        if verdict["confidence_score"] >= 70:
            return "APPROVED"
        elif verdict["confidence_score"] >= 50:
            return "APPROVED_MARGINAL"  # Proceeds but flagged for review
        else:
            return "REJECTED"  # Insufficient conviction
    
    return "REJECTED"  # Default: any ambiguity → reject
```

**Output:** Three files:
- `pipeline_state/03b_debate_round1.json`
- `pipeline_state/03b_debate_round2.json` (if enabled)
- `pipeline_state/03b_verdict.json`

Full schemas in Section 3.

**Error Handling:**
- If Bull API call fails: retry once. If still failed, the debate cannot proceed → `REJECTED` with reason `"bull_agent_api_failure"`.
- If Bear API call fails: retry once. If still failed → `REJECTED` with reason `"bear_agent_api_failure"`.
- If one agent returns malformed output: retry that agent once. If still malformed, use only the valid agent's argument + a note to the Judge that one perspective is missing. Judge should default to `REJECT` when one perspective is absent.
- If Judge API call fails: retry once. If failed → `REJECTED` with reason `"judge_api_failure"`. Never approve without a Judge verdict.
- If Round 2 fails: proceed to Judge with Round 1 only. Log the failure.

---

### 2.5 Component 4 — Execution Engine

**Purpose:** Translate APPROVED decisions into MT5 orders with zero deviation.

**Model Tier:** None — pure Python, deterministic.

**Dependencies:**
- Component 3B verdict (must be APPROVED)
- Component 3A trade parameters (entry, SL, TP levels)
- MT5 connection
- Account balance (live query from MT5)

**Activation Gate:** Only fires when:
1. Verdict is APPROVE with confidence ≥ 50
2. All deterministic safety checks pass

**Deterministic Safety Checks (hard-coded, non-AI):**
```python
def safety_checks(trade_params, account_state, session_state):
    checks = {}
    
    # 1. Spread check
    current_spread = get_current_spread()
    checks["spread_ok"] = current_spread <= 0.30  # 30 cents max
    
    # 2. Daily trade count
    checks["trade_count_ok"] = session_state["trades_today"] < 1
    
    # 3. Daily loss limit
    checks["daily_loss_ok"] = session_state["daily_pnl_pct"] > -2.0
    
    # 4. Weekly loss limit
    checks["weekly_loss_ok"] = session_state["weekly_pnl_pct"] > -4.0
    
    # 5. Monthly loss limit
    checks["monthly_loss_ok"] = session_state["monthly_pnl_pct"] > -8.0
    
    # 6. RR check
    entry = trade_params["entry_price"]
    sl = trade_params["stop_loss"]
    tp1 = trade_params["take_profit_1"]
    sl_distance = abs(entry - sl)
    tp_distance = abs(tp1 - entry)
    rr = tp_distance / sl_distance if sl_distance > 0 else 0
    checks["rr_ok"] = rr >= 3.0
    
    # 7. Risk percentage validation
    balance = account_state["balance"]
    risk_amount = sl_distance * 100 * trade_params["position_size_lots"]
    risk_pct = risk_amount / balance
    checks["risk_ok"] = risk_pct <= 0.012  # 1% with small buffer for rounding
    
    # 8. Session window check
    now = datetime.utcnow()
    checks["session_ok"] = (
        now.hour >= 7 and (now.hour < 9 or (now.hour == 9 and now.minute <= 30))
    )
    
    checks["all_passed"] = all(checks.values())
    return checks
```

**Position Sizing:**
```python
def calculate_position_size(balance, sl_distance_dollars):
    """
    Lots = (Balance × 0.01) / (SL distance in $ × 100)
    Standard lot on gold = $100 per $1 move
    """
    risk_amount = balance * 0.01
    lots = risk_amount / (sl_distance_dollars * 100)
    # Round down to nearest 0.01 lots (MT5 minimum increment)
    lots = math.floor(lots * 100) / 100
    return max(lots, 0.01)  # Minimum 0.01 lots
```

**Order Placement:**
```python
def place_order(trade_params):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "XAUUSD",
        "volume": trade_params["position_size_lots"],
        "type": mt5.ORDER_TYPE_BUY if trade_params["direction"] == "LONG" else mt5.ORDER_TYPE_SELL,
        "price": mt5.symbol_info_tick("XAUUSD").ask if trade_params["direction"] == "LONG" 
                 else mt5.symbol_info_tick("XAUUSD").bid,
        "sl": trade_params["stop_loss"],
        "tp": trade_params["take_profit_1"],  # Initial TP = TP1
        "deviation": 20,  # Slippage tolerance in points
        "magic": 202603,  # Unique identifier for this agent's trades
        "comment": f"ModelA_{trade_params['trade_id']}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    return result
```

**Partial Close Logic (runs in monitoring loop):**
```python
def manage_active_trade(trade_record, current_price):
    """
    Called on each M15 candle while trade is ACTIVE.
    Manages TP1 → TP2 → TP3 progression.
    """
    direction = trade_record["direction"]
    
    if not trade_record["tp1_hit"]:
        # Check TP1
        if (direction == "LONG" and current_price >= trade_record["tp1"]) or \
           (direction == "SHORT" and current_price <= trade_record["tp1"]):
            # Close 50%
            close_partial(trade_record["ticket"], 0.50)
            # Move SL to breakeven
            modify_sl(trade_record["ticket"], trade_record["entry_price"])
            trade_record["tp1_hit"] = True
            trade_record["events"].append({
                "type": "PARTIAL_TP1",
                "time": datetime.utcnow().isoformat(),
                "price": current_price,
                "remaining_pct": 0.50
            })
    
    elif not trade_record["tp2_hit"]:
        # Check TP2 — close 50% of remaining (= 25% of original)
        if (direction == "LONG" and current_price >= trade_record["tp2"]) or \
           (direction == "SHORT" and current_price <= trade_record["tp2"]):
            close_partial(trade_record["ticket"], 0.50)  # 50% of remaining
            # Trail SL behind M15 structure
            trail_price = get_m15_trail_level(direction)
            modify_sl(trade_record["ticket"], trail_price)
            trade_record["tp2_hit"] = True
            trade_record["events"].append({
                "type": "PARTIAL_TP2",
                "time": datetime.utcnow().isoformat(),
                "price": current_price,
                "remaining_pct": 0.25
            })
    
    else:
        # Runner — trail behind H1 structure, targeting TP3
        trail_price = get_h1_trail_level(direction)
        if trail_price:
            modify_sl(trade_record["ticket"], trail_price)
    
    # Session timeout check
    if datetime.utcnow().hour >= 12 and not trade_record["tp1_hit"]:
        # Evaluate: close at market or hold into NY
        # For initial implementation: close at market
        close_full(trade_record["ticket"])
        trade_record["exit_substate"] = "CLOSED_SESSION_TIMEOUT"
```

**Output:** `pipeline_state/04_execution_log.json` — includes order result, fill price, slippage, timestamps.

**Error Handling:**
- Order rejected by MT5: retry once after 2 seconds. If still failed, log as `FAILED_EXECUTION` with MT5 error code and description.
- Partial close fails: retry immediately. If failed, alert for manual intervention. Never modify SL as a workaround.
- MT5 disconnect during active trade: SL/TP are server-side — they execute regardless. On reconnection, sync state from MT5 trade history.
- Slippage exceeds 20 points: log as anomaly, proceed (SL/TP still valid). Flag in session manifest.

---

### 2.6 Component 5 — Knowledge Base

**Purpose:** Persistent memory. Three-layer retrieval system + all trade data.

**Model Tier:** Local embedding model (sentence-transformers/all-MiniLM-L6-v2) for LanceDB vectors. No Claude API calls.

**File Structure:**
```
knowledge_base/
├── pipeline_state/           # Ephemeral — overwritten each candle
├── sessions/                 # Append-only
├── trades/                   # Append-only
├── no_trades/                # Append-only
├── postmortems/              # Append-only
├── journals/daily/           # Append-only
├── journals/weekly/          # Append-only
├── insights/                 # Overwritten weekly by Component 6
│   └── current_insights.yaml
├── statistics/               # Updated after every trade
│   ├── rolling_stats.json
│   ├── regime_analysis.json
│   ├── condition_performance.json
│   └── quality_scores.json
├── patterns/                 # Updated after every trade
│   ├── failure_patterns.json
│   └── success_patterns.json
├── rules/                    # Modified only by Component 6 Tier 4
│   ├── active_rules.yaml
│   ├── base_rules.yaml
│   ├── rule_modifications_log.yaml
│   └── pending_reviews.yaml
├── index/
│   └── _trade_index.json     # Updated after every trade
├── vectordb/
│   └── trades.lance/         # LanceDB managed
└── meta/
    ├── agent_config.yaml
    └── .orchestrator.lock    # PID lock file
```

**Atomic Write Pattern:**
```python
def atomic_write(filepath, data):
    """Write to temp file, then atomic rename."""
    tmp_path = filepath + ".tmp"
    with open(tmp_path, 'w') as f:
        if filepath.endswith('.yaml'):
            yaml.dump(data, f, default_flow_style=False)
        else:
            json.dump(data, f, indent=2)
    os.replace(tmp_path, filepath)  # Atomic on POSIX and Windows (same drive)
```

**LanceDB Operations:**
```python
import lancedb
from sentence_transformers import SentenceTransformer

# Initialization (once at startup)
db = lancedb.connect("knowledge_base/vectordb")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Create table (if first run)
if "trades" not in db.table_names():
    db.create_table("trades", schema={
        "trade_id": str,
        "vector": list,  # 384-dim for MiniLM
        "text_summary": str,
        "outcome": str,
        "r_multiple": float,
        "setup_grade": str,
        "direction": str,
        "day_of_week": str,
        "liquidity_type": str,
        "displacement_quality": str,
        "regime": str,
        "date": str,
        "postmortem_summary": str
    })

# Write (after trade completion)
def embed_trade(trade_record, postmortem):
    text = format_trade_summary(trade_record)
    vector = embed_model.encode(text).tolist()
    
    table = db.open_table("trades")
    table.add([{
        "trade_id": trade_record["trade_id"],
        "vector": vector,
        "text_summary": text,
        "outcome": trade_record["outcome"],
        "r_multiple": trade_record["r_multiple"],
        "setup_grade": trade_record["setup_grade"],
        "direction": trade_record["direction"],
        "day_of_week": trade_record["day_of_week"],
        "liquidity_type": trade_record["liquidity_swept"],
        "displacement_quality": trade_record["displacement_quality"],
        "regime": trade_record["regime"],
        "date": trade_record["date"],
        "postmortem_summary": postmortem["summary"]
    }])

# Query (before each Primary Analyzer call)
def find_similar_setups(current_market_state, top_k=5):
    text = format_current_conditions_summary(current_market_state)
    query_vector = embed_model.encode(text).tolist()
    
    table = db.open_table("trades")
    results = table.search(query_vector).limit(top_k).to_list()
    
    return [{
        "trade_id": r["trade_id"],
        "similarity_score": 1 - r["_distance"],  # LanceDB returns L2 distance
        "outcome": r["outcome"],
        "r_multiple": r["r_multiple"],
        "setup_grade": r["setup_grade"],
        "text_summary": r["text_summary"],
        "postmortem_summary": r["postmortem_summary"]
    } for r in results]
```

**Three-Layer Context Assembly:**
```python
def assemble_kb_context(market_state):
    context = {}
    
    # Layer 1: Structured Query
    trade_index = load_json("knowledge_base/index/_trade_index.json")
    rolling_stats = load_json("knowledge_base/statistics/rolling_stats.json")
    failure_patterns = load_json("knowledge_base/patterns/failure_patterns.json")
    regime = load_json("knowledge_base/statistics/regime_analysis.json")
    pending = load_yaml("knowledge_base/rules/pending_reviews.yaml")
    
    context["layer1"] = {
        "last_10_trades": trade_index["trades"][-10:],
        "rolling_stats": rolling_stats,
        "active_failure_patterns": failure_patterns.get("active", []),
        "current_regime": regime.get("current_regime", "unknown"),
        "pending_reviews": pending.get("items", [])
    }
    
    # Layer 2: Compressed Insights
    insights = load_yaml("knowledge_base/insights/current_insights.yaml")
    context["layer2"] = insights  # Full file — small enough for prompt injection
    
    # Layer 3: Vector Similarity
    similar = find_similar_setups(market_state, top_k=5)
    context["layer3"] = similar
    
    return context
```

---

### 2.7 Component 6 — Adaptive Review System

**Purpose:** Statistical analysis of accumulated data. Identifies patterns, proposes modifications, generates compressed insights.

**Model Tier:** `claude-sonnet-4-20250514` — batch operation, cost efficiency matters.

**Cadence:**
- **After every trade:** Update rolling stats, quality scores, trade index, LanceDB. Pure Python — no AI call.
- **Weekly (Sunday):** Generate `current_insights.yaml`. 1 AI call (Sonnet).
- **Every 50 trades:** Deep statistical analysis. Up to 5 AI calls (Sonnet). Budget cap: 15 calls max per deep review.

**Rolling Statistics Update (post-trade, pure Python):**
```python
def update_rolling_stats(trade_record):
    stats = load_json("knowledge_base/statistics/rolling_stats.json")
    
    stats["total_trades"] += 1
    if trade_record["outcome"] == "WIN":
        stats["wins"] += 1
    elif trade_record["outcome"] == "LOSS":
        stats["losses"] += 1
    else:
        stats["breakeven"] += 1
    
    stats["win_rate"] = stats["wins"] / stats["total_trades"]
    stats["avg_winner_r"] = calculate_avg_winner_r(stats)
    stats["avg_loser_r"] = calculate_avg_loser_r(stats)
    stats["expectancy"] = (stats["win_rate"] * stats["avg_winner_r"]) - \
                          ((1 - stats["win_rate"]) * stats["avg_loser_r"])
    stats["profit_factor"] = stats["gross_profit"] / max(stats["gross_loss"], 0.01)
    stats["max_consecutive_losses"] = update_max_consec(stats, trade_record)
    stats["current_drawdown_pct"] = calculate_drawdown(stats)
    
    # Condition-level tracking
    condition_key = f"{trade_record['day_of_week']}_{trade_record['liquidity_type']}_{trade_record['displacement_quality']}"
    if condition_key not in stats["condition_breakdown"]:
        stats["condition_breakdown"][condition_key] = {"wins": 0, "losses": 0, "total": 0}
    stats["condition_breakdown"][condition_key]["total"] += 1
    if trade_record["outcome"] == "WIN":
        stats["condition_breakdown"][condition_key]["wins"] += 1
    
    atomic_write("knowledge_base/statistics/rolling_stats.json", stats)
```

**Dual-Axis Quality Scoring:**
```python
def score_trade(trade_record, market_state_at_entry):
    # Deterministic Axis (pure code)
    det_checks = {
        "risk_exactly_1pct": abs(trade_record["actual_risk_pct"] - 1.0) < 0.15,
        "within_session_window": trade_record["entry_time_utc"].hour >= 7 and 
                                  trade_record["entry_time_utc"].hour < 10,
        "sl_correct": trade_record["sl_placed_correctly"],
        "position_size_correct": trade_record["position_size_matches_formula"],
        "one_trade_limit": trade_record["trades_today_at_entry"] == 0,
        "partials_correct": trade_record["partials_executed_correctly"]
    }
    det_score = (sum(det_checks.values()) / len(det_checks)) * 100
    
    # LLM Axis (Claude evaluates post-hoc — deferred to postmortem generation)
    # This is calculated in the postmortem and stored separately
    
    return {
        "deterministic_score": det_score,
        "deterministic_checks": det_checks,
        "llm_score": None,  # Filled by postmortem
        "combined_score": None  # Calculated after postmortem: 0.4 * det + 0.6 * llm
    }
```

**Weekly Insights Generation (AI call):**
```python
def generate_weekly_insights():
    """
    Called Sunday. Reads all trade data, generates compressed insights.
    Single Claude Sonnet call with statistical summaries as input.
    """
    stats = load_json("knowledge_base/statistics/rolling_stats.json")
    condition_perf = load_json("knowledge_base/statistics/condition_performance.json")
    recent_trades = load_last_n_trades(50)
    
    prompt = f"""
    You are the analytical engine for a gold trading system.
    
    Generate compressed insights from this trading data. Output YAML format only.
    
    Overall Stats: {json.dumps(stats)}
    Condition Performance: {json.dumps(condition_perf)}
    Recent 50 Trades Summary: {json.dumps(summarize_trades(recent_trades))}
    
    For each condition combination with 10+ samples, classify as:
    - STRONG_EDGE (expectancy > overall + 0.3R)
    - PERFORMING (within 0.3R of overall)
    - UNDERPERFORMING (expectancy < overall - 0.3R AND sample >= 15)
    - SIGNIFICANTLY_UNDERPERFORMING (negative expectancy AND sample >= 20)
    
    Also assess debate calibration and regime performance.
    Output only valid YAML matching the current_insights schema.
    """
    
    response = call_claude(model="claude-sonnet-4-20250514", prompt=prompt)
    insights = yaml.safe_load(response)
    atomic_write("knowledge_base/insights/current_insights.yaml", insights)
```

**Adaptation Tier Logic:**
```python
def check_adaptation_tiers(stats, condition_perf):
    """Called after every 50-trade deep review."""
    
    flags = []
    proposals = []
    
    for condition, perf in condition_perf.items():
        if perf["sample_size"] < 20:
            continue  # Not enough data
        
        deviation = perf["win_rate"] - stats["win_rate"]
        
        # Tier 2: Flag for review
        if abs(deviation) > 0.15 and perf["sample_size"] >= 20:
            flags.append({
                "condition": condition,
                "deviation": deviation,
                "sample_size": perf["sample_size"],
                "tier": 2
            })
        
        # Tier 3: Propose modification
        if abs(deviation) > 0.15 and perf["sample_size"] >= 50:
            if perf["expectancy"] < 0:
                proposals.append({
                    "condition": condition,
                    "proposed_change": f"Treat '{condition}' as NO_TRADE filter",
                    "supporting_data": perf,
                    "projected_impact": calculate_projected_impact(stats, condition, perf),
                    "rollback_criteria": "Revert if expectancy drops by >0.1R over next 30 trades",
                    "tier": 3
                })
    
    return {"flags": flags, "proposals": proposals}
```

**Hard Guardrails:**
- NEVER modify: 1% risk limit, 1-trade/day limit, drawdown kill switches, 07:00–09:30 window, debate requirement.
- Max 1 rule change per 50-trade period.
- `base_rules.yaml` is read-only. Always restorable.

---

### 2.8 Component 7 — Monitoring & Alerting Dashboard

**Purpose:** Human operator visibility into agent operations and performance.

**Model Tier:** None — pure Python web app.

**Technical Stack:**
- FastAPI backend serving JSON endpoints
- Minimal HTML/JS frontend (or start with structured log output to console)
- Optional Phase 3+: Obsidian vault markdown export

**Dashboard Endpoints:**
```
GET /status              → Current session state, active trade info
GET /trades              → Trade history with filtering (date range, outcome, grade)
GET /trades/{trade_id}   → Full trade detail including debate transcript
GET /stats               → Rolling statistics, equity curve data
GET /debate-analytics    → Bull/bear win rates, false approval/rejection rates
GET /alerts              → Recent alerts sorted by severity
GET /health              → System health: API latency, MT5 connection, LanceDB, budget
```

**Alert Levels:**
```python
ALERTS = {
    "TRADE_EXECUTED": {"level": "INFO", "channels": ["log", "dashboard"]},
    "DEBATE_REJECTED": {"level": "INFO", "channels": ["log", "dashboard"]},
    "DRAWDOWN_WARNING": {"level": "WARNING", "channels": ["log", "dashboard", "email"]},
    "DRAWDOWN_LIMIT_HIT": {"level": "CRITICAL", "channels": ["log", "dashboard", "email", "sms"]},
    "ADAPTATION_PROPOSAL": {"level": "WARNING", "channels": ["log", "dashboard", "email"]},
    "QUALITY_DEGRADATION": {"level": "WARNING", "channels": ["log", "dashboard"]},
    "API_ERROR": {"level": "ERROR", "channels": ["log", "dashboard"]},
    "MT5_DISCONNECT": {"level": "CRITICAL", "channels": ["log", "dashboard", "email"]},
    "SYSTEM_ERROR": {"level": "CRITICAL", "channels": ["log", "dashboard", "email"]},
}
```

**Obsidian Export (Phase 3+):**
```python
def export_trade_to_obsidian(trade_record, postmortem):
    """One-way export: agent writes → human reads/annotates in Obsidian."""
    md = f"""---
trade_id: {trade_record["trade_id"]}
date: {trade_record["date"]}
direction: {trade_record["direction"]}
outcome: {trade_record["outcome"]}
r_multiple: {trade_record["r_multiple"]}
setup_grade: {trade_record["setup_grade"]}
tags: [model-a, {trade_record["day_of_week"]}, {trade_record["outcome"].lower()}]
---

# {trade_record["trade_id"]}

## Setup
{trade_record["reasoning"]["overall_reasoning"]}

## Debate Summary
**Bull Strength:** {trade_record["debate"]["bull_argument_strength"]}/100
**Bear Strength:** {trade_record["debate"]["bear_argument_strength"]}/100
**Verdict:** {trade_record["debate"]["verdict"]} ({trade_record["debate"]["confidence_score"]})
**Key Factor:** {trade_record["debate"]["key_factor"]}

## Outcome
{postmortem["summary"]}

## Lessons
{postmortem["lessons_learned"]}

---
Related: [[{prev_trade_id}]] | [[{next_trade_id}]]
"""
    write_file(f"obsidian_vault/trades/{trade_record['trade_id']}.md", md)
```

---

### 2.9 Component 8 — Session Orchestrator

**Purpose:** Main loop coordinator. Drives the entire pipeline.

**Model Tier:** None — pure Python orchestration.

**Lifecycle:**
```python
class SessionOrchestrator:
    def __init__(self):
        self.acquire_lock()  # PID-based lock with stale detection
        self.mt5 = initialize_mt5()
        self.kb = KnowledgeBase("knowledge_base/")
        self.state = SessionState()
    
    def run_session(self):
        """Main entry point. Called daily at 06:45 UTC."""
        try:
            # Pre-session (06:45 UTC)
            self.pre_session_routine()
            
            # Active window (07:00–09:30 UTC)
            while self.in_active_window():
                self.wait_for_m15_close()
                self.run_pipeline_cycle()
                
                if self.state.trade_taken:
                    self.monitor_active_trade()
                    break  # 1 trade/day limit — stop evaluating
            
            # Post-session
            if self.state.has_active_trade():
                self.monitor_until_close()  # Monitor through NY if needed
            
            self.generate_session_manifest()
            
            if self.state.trade_completed:
                self.run_postmortem()
                self.update_lancedb()
                self.update_rolling_stats()
            
        except Exception as e:
            self.handle_crash(e)
        finally:
            self.release_lock()
    
    def pre_session_routine(self):
        """06:45 UTC — 15 min before window opens."""
        # Pull D1/H4 data and compute initial state
        raw = ingest_data(self.mt5, pre_session=True)
        market_state = compute_market_state(raw)
        
        # Load KB context (pre-warm)
        self.kb_context = self.kb.assemble_context(market_state)
        
        # Log pre-session state
        self.state.set_pre_session(market_state, self.kb_context)
    
    def run_pipeline_cycle(self):
        """One iteration per M15 candle close."""
        # Step 1: Data Ingestion
        raw = ingest_data(self.mt5)
        write_pipeline("01_raw_data.json", raw)
        
        # Step 2: Market State
        market_state = compute_market_state(raw)
        write_pipeline("02_market_state.json", market_state)
        
        # Step 3: Refresh KB context
        self.kb_context = self.kb.assemble_context(market_state)
        
        # Step 4: Primary Analysis
        analysis = run_primary_analyzer(market_state, self.kb_context)
        write_pipeline("03a_primary_analysis.json", analysis)
        
        if analysis["decision"] == "CANDIDATE":
            # Step 5: Bull/Bear Debate
            self.state.transition("EVALUATING", "CANDIDATE")
            
            verdict = asyncio.run(run_debate(
                market_state, analysis, self.kb_context, self.config
            ))
            self.state.transition("CANDIDATE", "DEBATED")
            
            result = evaluate_verdict(verdict)
            
            if result in ("APPROVED", "APPROVED_MARGINAL"):
                # Step 6: Deterministic Safety Checks
                checks = safety_checks(
                    analysis["trade_parameters"],
                    get_account_state(self.mt5),
                    self.state
                )
                
                if checks["all_passed"]:
                    self.state.transition("DEBATED", "APPROVED")
                    
                    # Step 7: Execute
                    exec_result = place_order(analysis["trade_parameters"])
                    write_pipeline("04_execution_log.json", exec_result)
                    
                    if exec_result["success"]:
                        self.state.transition("APPROVED", "EXECUTING")
                        self.state.transition("EXECUTING", "ACTIVE")
                        self.state.trade_taken = True
                    else:
                        self.state.transition("APPROVED", "FAILED_EXECUTION")
                else:
                    self.state.transition("DEBATED", "REJECTED")
                    self.state.rejection_reason = f"safety_check_failed: {checks}"
            else:
                self.state.transition("DEBATED", "REJECTED")
                self.state.rejection_reason = f"debate_rejected: {verdict['summary']}"
        
        elif analysis["decision"] == "WAIT":
            self.state.log_wait(analysis)
        
        elif analysis["decision"] == "NO_TRADE":
            self.state.log_no_trade(analysis)
            self.kb.write_no_trade(analysis)
    
    def handle_crash(self, error):
        """Recovery from unexpected failure."""
        log_critical(f"Orchestrator crash: {error}")
        
        # Check for active MT5 trades
        positions = mt5.positions_get(symbol="XAUUSD")
        if positions:
            # SL/TP are server-side — trade is protected
            # Log the disconnect, sync state on next startup
            log_warning("Active trade exists during crash. SL/TP are broker-side.")
        
        # Write crash state for recovery
        atomic_write("knowledge_base/meta/last_crash.json", {
            "time": datetime.utcnow().isoformat(),
            "error": str(error),
            "session_state": self.state.to_dict(),
            "active_positions": [p._asdict() for p in (positions or [])]
        })
    
    def acquire_lock(self):
        """PID-based lock with stale detection."""
        lock_path = "knowledge_base/meta/.orchestrator.lock"
        if os.path.exists(lock_path):
            with open(lock_path) as f:
                data = json.load(f)
            # Check if PID is still alive
            if psutil.pid_exists(data["pid"]):
                raise RuntimeError("Another orchestrator is already running")
            else:
                log_warning(f"Stale lock detected (PID {data['pid']}). Overwriting.")
        
        atomic_write(lock_path, {
            "pid": os.getpid(),
            "started": datetime.utcnow().isoformat()
        })
```

---

## 3. Data Model Definitions

### 3.1 Market State Object

Written to `pipeline_state/02_market_state.json` by Component 2.

```yaml
# Schema (YAML representation of JSON structure)
MarketStateObject:
  timestamp_utc: string  # ISO 8601
  
  timeframes:
    D1:
      swings: list[Swing]
      structure:
        direction: "bullish" | "bearish" | "transitional" | "insufficient_data"
        protected_swing: Swing | null
        swing_sequence: list[string]  # ["HH", "HL", "HH", "HL"] etc.
        hh_count: int
        hl_count: int
        lh_count: int
        ll_count: int
      structure_events: list[StructureEvent]  # BOS/CHoCH detections
      order_blocks: list[OrderBlock]
      fair_value_gaps: list[FVG]
      premium_discount: PremiumDiscount | null
      avg_candle_body: float
    
    H4: # Same structure as D1
    H1: # Same structure as D1
    M15: # Same structure as D1
  
  session_levels:
    asian_high: float
    asian_low: float
    pdh: float
    pdl: float
    session_high: float | null
    session_low: float | null
  
  equal_highs: list[EqualLevel]
  equal_lows: list[EqualLevel]
  
  liquidity_pools: list[LiquidityPool]
  detected_sweeps: list[Sweep]
  
  spread_cents: float | null
  high_impact_events: list[EconEvent] | null
  
  data_quality:
    all_timeframes_complete: bool
    spread_normal: bool
    mt5_connected: bool
    timestamp_utc: string

# Sub-types:
Swing:
  index: int
  type: "high" | "low"
  price: float
  time: string

StructureEvent:
  type: "BOS" | "CHoCH"
  direction: "bullish" | "bearish"
  level_broken: float
  close_price: float
  candle_index: int
  time: string
  displacement_present: bool
  displacement_ratio: float  # Body of BOS candle / avg candle body

OrderBlock:
  type: "bullish" | "bearish"
  high: float
  low: float
  open: float
  close: float
  formation_index: int
  formation_time: string
  causing_bos_index: int
  mitigated: bool

FVG:
  type: "bullish" | "bearish"
  top: float
  bottom: float
  midpoint: float
  candle_indices: list[int]
  formation_time: string
  filled: bool

PremiumDiscount:
  impulse_low: float
  impulse_high: float
  equilibrium_50: float
  fib_62: float
  fib_79: float
  discount_zone: {top: float, bottom: float}
  premium_zone: {top: float, bottom: float}
  ote_zone: {top: float, bottom: float}

EqualLevel:
  price: float
  count: int
  candle_indices: list[int]

LiquidityPool:
  type: "asian_high" | "asian_low" | "pdh" | "pdl" | "equal_highs" | "equal_lows" | "session_high" | "session_low"
  price: float
  side: "high" | "low"

Sweep:
  pool: LiquidityPool
  type: "sweep" | "run"
  wick_extreme: float
  body_close: float
  candle_index: int
  time: string

EconEvent:
  name: string
  time: string
  importance: int
```

### 3.2 Primary Analysis Output

Written to `pipeline_state/03a_primary_analysis.json` by Component 3A.

```json
{
  "timestamp_utc": "2026-03-28T07:15:00Z",
  "model_used": "claude-sonnet-4-20250514",
  "decision": "NO_TRADE | CANDIDATE | WAIT",
  "confidence_score": 0,
  
  "reasoning": {
    "daily_bias": {
      "direction": "bullish|bearish|ranging",
      "confidence": "high|medium|low",
      "protected_swing_level": 0.0,
      "explanation": "string — max 200 words"
    },
    "h4_alignment": {
      "aligned": true,
      "h4_pois_identified": ["OB at 3042.50", "FVG 3038-3040"],
      "explanation": "string"
    },
    "h1_setup": {
      "poi_identified": true,
      "poi_type": "OB|FVG|liquidity_zone|none",
      "poi_price_level": 0.0,
      "zone": "premium|discount|neutral",
      "fib_retracement_pct": 0.0,
      "explanation": "string"
    },
    "liquidity_sweep": {
      "detected": true,
      "pool_type": "asian_high|asian_low|pdh|pdl|equal_highs|equal_lows|none",
      "sweep_quality": "clean|messy|ambiguous",
      "sweep_price": 0.0,
      "explanation": "string"
    },
    "m15_confirmation": {
      "choch_detected": true,
      "displacement_quality": "strong|medium|weak|none",
      "displacement_candle_body_vs_avg_ratio": 0.0,
      "explanation": "string"
    },
    "similar_historical_setups_considered": [
      {
        "trade_id": "tr_2026-01-15_001",
        "similarity_score": 0.87,
        "outcome": "WIN",
        "r_multiple": 3.2,
        "key_difference": "string — what's different about today vs that trade"
      }
    ],
    "setup_grade": "A+|A|B+|B|C",
    "overall_reasoning": "string — complete reasoning chain, max 500 words"
  },
  
  "trade_parameters": {
    "direction": "LONG|SHORT",
    "entry_price": 0.0,
    "stop_loss": 0.0,
    "sl_buffer_applied": 0.0,
    "take_profit_1": 0.0,
    "take_profit_2": 0.0,
    "take_profit_3": 0.0,
    "risk_reward_ratio": 0.0,
    "position_size_lots": 0.0
  },
  
  "no_trade_reason": "string | null",
  "wait_reason": "string | null"
}
```

### 3.3 Bull/Bear Debate Outputs

**Round 1** — `pipeline_state/03b_debate_round1.json`:
```json
{
  "timestamp_utc": "2026-03-28T07:16:30Z",
  
  "bull_argument": {
    "position": "TAKE_TRADE",
    "argument_strength_self_assessed": 0,
    "key_points": [
      {
        "point": "string — specific argument",
        "supporting_data": "string — specific price levels, ratios, or KB references"
      }
    ],
    "historical_parallels_cited": ["tr_2026-02-10_001"],
    "full_argument": "string — complete argument, max 400 words"
  },
  
  "bear_argument": {
    "position": "DO_NOT_TRADE",
    "argument_strength_self_assessed": 0,
    "key_points": [
      {
        "point": "string",
        "supporting_data": "string"
      }
    ],
    "risks_identified": [
      {
        "risk": "string",
        "severity": "high|medium|low",
        "evidence": "string"
      }
    ],
    "alternative_interpretations": ["string — different way to read the price action"],
    "full_argument": "string — complete argument, max 400 words"
  }
}
```

**Round 2 (if enabled)** — `pipeline_state/03b_debate_round2.json`:
```json
{
  "timestamp_utc": "2026-03-28T07:17:00Z",
  
  "bull_rebuttal": {
    "points_addressed": ["string — which bear points are being rebutted"],
    "rebuttal": "string — max 300 words",
    "concessions": ["string — any bear points the bull acknowledges as valid"]
  },
  
  "bear_rebuttal": {
    "points_addressed": ["string — which bull points are being rebutted"],
    "rebuttal": "string — max 300 words",
    "concessions": ["string — any bull points the bear acknowledges as valid"]
  }
}
```

**Verdict** — `pipeline_state/03b_verdict.json`:
```json
{
  "timestamp_utc": "2026-03-28T07:17:30Z",
  "model_used": "claude-sonnet-4-20250514",
  "verdict": "APPROVE | REJECT",
  "winning_perspective": "BULL | BEAR",
  "confidence_score": 0,
  "bull_argument_strength": 0,
  "bear_argument_strength": 0,
  "key_factor": "string — the specific argument that tipped the decision",
  "risk_concerns_acknowledged": ["string"],
  "summary": "string — max 200 words"
}
```

### 3.4 Trade Record (YAML)

Written to `knowledge_base/trades/tr_YYYY-MM-DD_NNN.yaml`:

```yaml
trade_id: "tr_2026-03-28_001"
date: "2026-03-28"
day_of_week: "Friday"

# Lifecycle
lifecycle_state: "CLOSED"  # Current state
exit_substate: "CLOSED_TP3_RUNNER"
state_transitions:
  - from: "EVALUATING"
    to: "CANDIDATE"
    time: "2026-03-28T07:15:05Z"
    event: "primary_analyzer_candidate"
  - from: "CANDIDATE"
    to: "DEBATED"
    time: "2026-03-28T07:16:35Z"
    event: "debate_completed"
  - from: "DEBATED"
    to: "APPROVED"
    time: "2026-03-28T07:16:36Z"
    event: "verdict_approve_confidence_82"
  - from: "APPROVED"
    to: "EXECUTING"
    time: "2026-03-28T07:16:38Z"
    event: "order_sent"
  - from: "EXECUTING"
    to: "ACTIVE"
    time: "2026-03-28T07:16:39Z"
    event: "order_filled"
  - from: "ACTIVE"
    to: "CLOSED"
    time: "2026-03-28T10:45:12Z"
    event: "runner_hit_tp3"

# Trade Parameters
direction: "LONG"
entry_price: 3039.85
stop_loss: 3033.50
sl_buffer_applied: 1.20
take_profit_1: 3048.10
take_profit_2: 3055.00
take_profit_3: 3068.50
risk_reward_ratio: 3.48
position_size_lots: 0.08

# Execution
fill_price: 3039.90
slippage_cents: 5
spread_at_entry: 18

# Analysis Context
setup_grade: "A+"
daily_bias: "bullish"
h4_aligned: true
liquidity_swept: "asian_low"
displacement_quality: "strong"
displacement_ratio: 2.4
regime: "trending_bullish"

# Debate
debate_verdict: "APPROVE"
debate_confidence: 82
bull_strength: 85
bear_strength: 58
debate_key_factor: "Clean Asian low sweep with 2.4x displacement ratio"
debate_round2_enabled: true

# Outcome
outcome: "WIN"
r_multiple: 4.06
actual_risk_pct: 0.98
pnl_dollars: 31.50
hold_time_minutes: 209

# Partial Close Events
events:
  - type: "PARTIAL_TP1"
    time: "2026-03-28T08:22:00Z"
    price: 3048.10
    remaining_pct: 0.50
  - type: "PARTIAL_TP2"
    time: "2026-03-28T09:15:00Z"
    price: 3055.00
    remaining_pct: 0.25
  - type: "RUNNER_TP3"
    time: "2026-03-28T10:45:12Z"
    price: 3068.50
    remaining_pct: 0.0

# Quality Scores
quality_scores:
  deterministic_score: 100
  llm_score: 88
  combined_score: 92.8

# Reasoning Snapshot
primary_analysis_file: "pipeline_state/03a_primary_analysis_2026-03-28T0715.json"
debate_files:
  round1: "pipeline_state/03b_debate_round1_2026-03-28T0715.json"
  round2: "pipeline_state/03b_debate_round2_2026-03-28T0715.json"
  verdict: "pipeline_state/03b_verdict_2026-03-28T0715.json"
```

### 3.5 Session Manifest

Written to `knowledge_base/sessions/YYYY-MM-DD_session.json`:

```json
{
  "date": "2026-03-28",
  "day_of_week": "Friday",
  "session_start_utc": "2026-03-28T06:45:00Z",
  "session_end_utc": "2026-03-28T09:30:00Z",
  
  "pre_session": {
    "daily_bias": "bullish",
    "h4_alignment": "aligned",
    "key_levels_marked": ["Asian H: 3045.20", "Asian L: 3038.50", "PDH: 3052.80"],
    "regime": "trending_bullish",
    "high_impact_events": []
  },
  
  "candle_evaluations": [
    {
      "candle_time": "2026-03-28T07:00:00Z",
      "decision": "WAIT",
      "reason": "No liquidity sweep yet. Asian low intact at 3038.50."
    },
    {
      "candle_time": "2026-03-28T07:15:00Z",
      "decision": "CANDIDATE",
      "confidence": 78,
      "setup_grade": "A+",
      "debate_triggered": true,
      "debate_verdict": "APPROVE",
      "trade_executed": true,
      "trade_id": "tr_2026-03-28_001"
    }
  ],
  
  "trade_summary": {
    "trade_taken": true,
    "trade_id": "tr_2026-03-28_001",
    "outcome": "WIN",
    "r_multiple": 4.06
  },
  
  "errors": [],
  "api_calls_count": 6,
  "api_cost_estimate_usd": 0.28
}
```

### 3.6 No-Trade Record

Written to `knowledge_base/no_trades/nt_YYYY-MM-DD_HHMM.yaml`:

```yaml
record_id: "nt_2026-03-27_0715"
date: "2026-03-27"
candle_time: "2026-03-27T07:15:00Z"
decision: "NO_TRADE"
reason: "Daily structure ranging — no clear directional bias"
reasoning:
  daily_bias: "ranging"
  h4_alignment: "n/a — daily ranging"
  stopped_at_step: 1
  full_explanation: "Daily showing HH followed by LL — transitional. No directional conviction."
data_quality_ok: true
```

### 3.7 Postmortem Record

Written to `knowledge_base/postmortems/pm_tr_YYYY-MM-DD_NNN.yaml`:

```yaml
trade_id: "tr_2026-03-28_001"
generated_at: "2026-03-28T11:00:00Z"
model_used: "claude-sonnet-4-20250514"

# Hindsight Analysis
daily_bias_accuracy: "correct"
h4_alignment_accuracy: "correct"
sweep_classification_accuracy: "correct"
displacement_assessment_accuracy: "correct — ratio was 2.4x, strong by any measure"
setup_grade_appropriate: true
missed_signals: []
alternative_readings_in_hindsight: "None — setup was clean"

# LLM Quality Score
llm_score: 88
llm_score_breakdown:
  bias_read: 95
  sweep_classification: 90
  displacement_assessment: 85
  grade_accuracy: 85
  missed_signals_penalty: 0

# Lessons
lessons_learned:
  - "Asian low sweep on Friday with strong daily trend continues to be high-quality"
  - "2.4x displacement ratio is well above threshold — high conviction warranted"
key_pattern: "Friday clean sweep + strong displacement = high R potential"

# Summary (also embedded in LanceDB)
summary: "LONG after clean Asian low sweep. 2.4x displacement CHoCH on M15. Full A+ alignment. Hit all 3 TPs for 4.06R. High-quality execution."

# Debate Evaluation
debate_verdict_correct: true
debate_notes: "Bear raised valid concern about Friday afternoon liquidity thinning. Mitigated by TP1 closing 50% before noon."
```

### 3.8 Quality Score Object

Stored in `knowledge_base/statistics/quality_scores.json`:

```json
{
  "scores": [
    {
      "trade_id": "tr_2026-03-28_001",
      "deterministic_score": 100,
      "deterministic_checks": {
        "risk_exactly_1pct": true,
        "within_session_window": true,
        "sl_correct": true,
        "position_size_correct": true,
        "one_trade_limit": true,
        "partials_correct": true
      },
      "llm_score": 88,
      "combined_score": 92.8,
      "date": "2026-03-28"
    }
  ],
  "rolling_avg_deterministic": 96.5,
  "rolling_avg_llm": 82.3,
  "rolling_avg_combined": 87.98,
  "trend": "stable"
}
```

### 3.9 Compressed Insights Object

Stored in `knowledge_base/insights/current_insights.yaml`:

```yaml
generated_at: "2026-06-29T10:00:00Z"
total_trades_analyzed: 187
overall_win_rate: 0.48
overall_expectancy: 0.86
overall_profit_factor: 1.72
max_consecutive_losses: 6

condition_insights:
  - condition: "Monday Asian low sweep"
    sample_size: 22
    win_rate: 0.35
    expectancy: 0.12
    avg_r_winner: 2.8
    avg_r_loser: 1.0
    flag: "UNDERPERFORMING"
    note: "Consider reducing confidence for Monday setups"
  
  - condition: "Displacement quality: medium"
    sample_size: 18
    win_rate: 0.28
    expectancy: -0.15
    avg_r_winner: 2.2
    avg_r_loser: 1.0
    flag: "SIGNIFICANTLY_UNDERPERFORMING"
    note: "Medium displacement has negative expectancy — should be treated as NO_TRADE"
  
  - condition: "Tuesday-Thursday, strong displacement, trending regime"
    sample_size: 68
    win_rate: 0.62
    expectancy: 1.45
    avg_r_winner: 3.4
    avg_r_loser: 0.95
    flag: "STRONG_EDGE"
    note: "Core edge conditions — highest confidence setups"

debate_calibration:
  total_debates: 89
  bull_wins: 63
  bear_wins: 26
  bull_win_rate: 0.71
  bear_win_rate: 0.29
  false_approvals_pct: 0.18
  false_rejections_pct: 0.12
  calibration_note: "Bear agent may be slightly under-aggressive — monitor"

regime_insight:
  current_regime: "trending_bullish"
  regime_started: "2026-06-15"
  model_performance_in_regime: "Above average (0.95R vs 0.86R overall)"
  
active_failure_patterns:
  - pattern: "Sweeps during high-impact news window"
    affected_trades: 5
    all_losses: true
    recommendation: "Hard filter against trading within 30 min of scheduled high-impact USD event"

rule_modification_history:
  - modification: "Added medium displacement → NO_TRADE filter"
    date: "2026-05-15"
    impact: "Expectancy improved from 0.72R to 0.86R over next 40 trades"
    status: "permanent"
```

### 3.10 LanceDB Record Schema

```python
# LanceDB table: "trades"
# Each row represents one completed trade

LANCE_SCHEMA = {
    "trade_id": str,           # "tr_2026-03-28_001"
    "vector": list[float],     # 384-dim embedding from MiniLM
    "text_summary": str,       # Natural language summary for embedding
    "outcome": str,            # "WIN" | "LOSS" | "BREAKEVEN"
    "r_multiple": float,       # e.g., 4.06
    "setup_grade": str,        # "A+" | "A" | "B+" | "B" | "C"
    "direction": str,          # "LONG" | "SHORT"
    "day_of_week": str,        # "Monday" ... "Friday"
    "liquidity_type": str,     # "asian_low" | "asian_high" | "pdh" | "pdl" | etc.
    "displacement_quality": str, # "strong" | "medium" | "weak"
    "regime": str,             # "trending_bullish" | "trending_bearish" | "ranging"
    "date": str,               # "2026-03-28"
    "daily_bias": str,         # "bullish" | "bearish"
    "h4_aligned": bool,
    "debate_confidence": int,  # 0-100
    "postmortem_summary": str  # Compact postmortem for injection into prompts
}

# Example text_summary for embedding:
# "2026-03-28 | LONG | Bullish Daily aligned H4 | Asian low sweep clean | 
#  Strong displacement 2.4x CHoCH | Friday | Trending bullish regime | 
#  A+ grade | WIN 4.06R"
```

---

## 4. Trade Lifecycle State Machine

### 4.1 State Diagram

```
                          ┌─────────────┐
                          │  EVALUATING │ (entry state — created each M15 candle)
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌───────────┐ ┌──────────┐ (WAIT — not a lifecycle state.
            │ NO_TRADE  │ │CANDIDATE │  Logged in session manifest only.
            │ (terminal)│ └─────┬────┘  Fresh EVALUATING on next candle.)
            └───────────┘       │
                                ▼
                          ┌──────────┐
                          │ DEBATED  │
                          └─────┬────┘
                                │
                       ┌────────┴────────┐
                       │                 │
                       ▼                 ▼
                ┌───────────┐     ┌───────────┐
                │ REJECTED  │     │ APPROVED  │
                │ (terminal)│     └─────┬─────┘
                └───────────┘           │
                                        ▼
                                 ┌───────────┐
                                 │ EXECUTING │
                                 └─────┬─────┘
                                       │
                              ┌────────┴────────┐
                              │                 │
                              ▼                 ▼
                       ┌───────────┐    ┌────────────────┐
                       │  ACTIVE   │    │FAILED_EXECUTION│
                       └─────┬─────┘    │  (terminal)    │
                             │          └────────────────┘
                             │
                    (partial close events logged
                     within ACTIVE — not state changes)
                             │
                             ▼
                       ┌───────────┐
                       │  CLOSED   │ (terminal — exit substate attached)
                       └───────────┘
```

### 4.2 Valid Transitions Table

| From | To | Triggering Event | Guard Condition |
|---|---|---|---|
| EVALUATING | NO_TRADE | Primary Analyzer returns NO_TRADE | None |
| EVALUATING | CANDIDATE | Primary Analyzer returns CANDIDATE | confidence_score > 0 |
| CANDIDATE | DEBATED | Bull/Bear debate completes | Verdict JSON written |
| DEBATED | REJECTED | Verdict = REJECT, or confidence < 50, or safety check fails | None |
| DEBATED | APPROVED | Verdict = APPROVE with confidence ≥ 50 AND all safety checks pass | safety_checks.all_passed == True |
| APPROVED | EXECUTING | Order sent to MT5 | MT5 order_send() called |
| EXECUTING | ACTIVE | MT5 confirms fill | order_result.retcode == TRADE_RETCODE_DONE |
| EXECUTING | FAILED_EXECUTION | MT5 rejects order, or spread spike, or retry exhausted | After 1 retry |
| ACTIVE | CLOSED | Position fully closed (all lots) | positions_get returns empty for ticket |

### 4.3 Exit Substates

Applied when the last portion of the position closes:

| Exit Substate | Condition |
|---|---|
| CLOSED_SL | Full SL hit before TP1 partial |
| CLOSED_BE | TP1 partial taken, then BE stop hit on remainder |
| CLOSED_TP2 | All remaining closed at TP2 |
| CLOSED_TP3_RUNNER | Runner hit TP3 |
| CLOSED_TRAIL | Runner stopped by trailing SL (between TP2 and TP3) |
| CLOSED_SESSION_TIMEOUT | Closed at 12:00 UTC — TP1 not hit |
| CLOSED_MANUAL | Human override |
| CLOSED_SYSTEM_ERROR | System failure forced close |

### 4.4 Transition Enforcement

```python
VALID_TRANSITIONS = {
    "EVALUATING": {"NO_TRADE", "CANDIDATE"},
    "CANDIDATE": {"DEBATED"},
    "DEBATED": {"REJECTED", "APPROVED"},
    "APPROVED": {"EXECUTING"},
    "EXECUTING": {"ACTIVE", "FAILED_EXECUTION"},
    "ACTIVE": {"CLOSED"},
}

TERMINAL_STATES = {"NO_TRADE", "REJECTED", "FAILED_EXECUTION", "CLOSED"}

def transition(record, from_state, to_state, event):
    if record["lifecycle_state"] != from_state:
        raise InvalidTransitionError(
            f"Record is in {record['lifecycle_state']}, not {from_state}"
        )
    if to_state not in VALID_TRANSITIONS.get(from_state, set()):
        raise InvalidTransitionError(
            f"Cannot transition from {from_state} to {to_state}"
        )
    if record["lifecycle_state"] in TERMINAL_STATES:
        raise InvalidTransitionError(
            f"Record is in terminal state {record['lifecycle_state']}"
        )
    
    record["lifecycle_state"] = to_state
    record["state_transitions"].append({
        "from": from_state,
        "to": to_state,
        "time": datetime.utcnow().isoformat(),
        "event": event
    })
```

---

## 5. AI Prompt Architecture

### 5.1 Primary Analyzer — System Prompt

```
SYSTEM PROMPT — PRIMARY ANALYZER

You are an institutional gold trader specializing in Smart Money Concepts (SMC) and ICT methodology. You have 10+ years of experience trading XAUUSD exclusively. Your role is to evaluate market conditions and determine whether a Model A setup exists on the current M15 candle.

## Your Trading Model: Model A — London Open Liquidity Sweep

You trade EXACTLY one model. Here are the rules:
- Market: XAUUSD only
- Session: 07:00–09:30 UTC (London Open)
- Bias: Daily + H4 (must be aligned)
- Setup: H1 pullback to POI in correct premium/discount zone
- Entry Trigger: M15 CHoCH with displacement after a liquidity sweep
- Min RR: 1:3 to first target
- Risk: 1% per trade
- Max Trades: 1 per day

## Evaluation Sequence — Follow This EXACTLY In Order

Step 1 — DAILY BIAS: Is the Daily chart making HH/HL (bullish), LH/LL (bearish), or unclear/ranging? If ranging or unclear → output NO_TRADE immediately. Identify the protected swing.

Step 2 — H4 ALIGNMENT: Does H4 structure agree with Daily? If H4 conflicts with Daily → output NO_TRADE or note as B-grade only. Identify H4 POIs.

Step 3 — H1 SETUP: Has H1 pulled back to a valid POI (unmitigated OB, active FVG, or key liquidity zone)? Is the POI in the correct zone (discount for longs at 50%+ retracement, ideally 62–79%; premium for shorts)? If no valid pullback → output NO_TRADE.

Step 4 — LIQUIDITY SWEEP: Has price swept a defined liquidity pool (Asian H/L, PDH/PDL, equal H/L, session H/L)? A sweep = wick beyond + body close inside. If no sweep → output NO_TRADE.

Step 5 — M15 CONFIRMATION: After the sweep, does M15 show a CHoCH in the trade direction with displacement? CHoCH = body close beyond the most recent protected M15 swing. Displacement = at least one candle with body significantly larger than the 20-period average body. If no CHoCH or no displacement → output NO_TRADE or WAIT.

Step 6 — TRADE PARAMETERS: If all steps pass, calculate entry, SL, TPs, RR. SL goes beyond the sweep wick + buffer. If RR < 1:3 → output NO_TRADE.

Step 7 — SELF-CHECK: Before outputting CANDIDATE, ask yourself:
- Am I forcing this because I haven't traded in several sessions?
- Is displacement genuinely strong or am I rationalizing?
- Would a skeptical, experienced trader agree with this assessment?
- Are there conflicting signals I'm downplaying?

If any self-check raises doubt, downgrade to WAIT or NO_TRADE.

## Historical Context

You have been provided with similar historical setups from the knowledge base. Reference them in your reasoning — how does today compare? What can be learned from their outcomes?

## Critical Rules

- Base ALL analysis on the price data provided in the Market State Object.
- If any data is ambiguous or missing, output NO_TRADE. Never assume or fabricate confluence.
- If structure is unclear, state "structure unclear" — do NOT force a read.
- When signals conflict, default to NO_TRADE. Express uncertainty explicitly.
- You can ONLY output CANDIDATE, WAIT, or NO_TRADE. You cannot output TRADE — that requires debate approval.

## Output Format

Respond with ONLY a valid JSON object matching the Primary Analysis Output schema. No preamble, no markdown, no explanation outside the JSON.
```

### 5.2 Primary Analyzer — User Message Template

```
## Market State Object
{market_state_json}

## Knowledge Base Context

### Layer 1 — Recent Performance
Last 10 trades: {last_10_trades}
Rolling stats: Win rate {win_rate}, Expectancy {expectancy}R, Current drawdown {drawdown}%
Active failure patterns: {failure_patterns}
Current regime: {regime}

### Layer 2 — Compressed Insights
{current_insights_yaml}

### Layer 3 — Similar Historical Setups
{similar_setups_json}

## Current Time: {utc_timestamp}
## Candle Being Evaluated: M15 close at {candle_time}

Evaluate this candle against the Model A entry sequence. Output your analysis as JSON.
```

### 5.3 Bull Agent — System Prompt

```
SYSTEM PROMPT — BULL AGENT

You are a senior gold trader who has identified what you believe is a high-quality Model A setup. The Primary Analyzer has assessed this as a CANDIDATE trade. Your task is to present the STRONGEST POSSIBLE CASE for taking this trade.

## Your Objective
Build a compelling, evidence-based argument for why this trade should be executed. You must:
1. Cite specific price levels from the Market State Object
2. Reference displacement ratios and structural alignment
3. Point to favorable historical parallels from the knowledge base
4. Address the setup grade and why it warrants execution
5. Explain why the risk/reward is favorable

## Rules
- Be SPECIFIC. Cite exact prices, ratios, and data points. "The setup looks good" is worthless.
- Vague optimism is not convincing. Build your case with evidence.
- You may acknowledge minor weaknesses but must explain why they don't invalidate the trade.
- Reference similar historical trades that succeeded if available.
- Your argument should be structured: Structure → Liquidity → Displacement → Parameters → Conclusion.

## Output Format
Respond with ONLY valid JSON matching the Bull Argument schema. No preamble.

{
  "position": "TAKE_TRADE",
  "argument_strength_self_assessed": 0-100,
  "key_points": [{"point": "...", "supporting_data": "..."}],
  "historical_parallels_cited": ["trade_id", ...],
  "full_argument": "..."
}
```

### 5.4 Bear Agent — System Prompt

```
SYSTEM PROMPT — BEAR AGENT

You are a senior risk manager whose primary job is to protect capital. The Primary Analyzer has identified a CANDIDATE trade. Your task is to present the STRONGEST POSSIBLE CASE for NOT taking this trade.

## Your Objective
Find every legitimate reason to reject this trade. You must:
1. Look for alternative structure readings that contradict the Primary Analyzer
2. Assess whether displacement is genuinely strong or borderline
3. Question the sweep classification — could it be a run, not a sweep?
4. Check for unfavorable patterns from the knowledge base (similar setups that failed)
5. Identify proximity to high-impact news events
6. Assess regime conditions — does the current regime favor this setup type?
7. Look for any signal the Primary Analyzer may have downplayed or missed

## Rules
- Be SPECIFIC. "This trade is risky" is worthless. Identify WHAT is risky and WHY with data.
- Vague pessimism is as useless as vague optimism.
- You may acknowledge genuine strengths but must explain why weaknesses outweigh them.
- Reference similar historical trades that FAILED if available.
- Your default recommendation is DO_NOT_TRADE. You only concede if you genuinely cannot find material weaknesses.

## Output Format
Respond with ONLY valid JSON matching the Bear Argument schema. No preamble.

{
  "position": "DO_NOT_TRADE",
  "argument_strength_self_assessed": 0-100,
  "key_points": [{"point": "...", "supporting_data": "..."}],
  "risks_identified": [{"risk": "...", "severity": "high|medium|low", "evidence": "..."}],
  "alternative_interpretations": ["..."],
  "full_argument": "..."
}
```

### 5.5 Judge — System Prompt

```
SYSTEM PROMPT — JUDGE

You are the fund manager making the final allocation decision on a gold trade. You have heard both the bull case (for the trade) and the bear case (against the trade). Your job is to evaluate the QUALITY of each argument and deliver a final verdict.

## Your Decision Framework
1. Which argument is better supported by the ACTUAL price data in the Market State Object?
2. Did either agent fabricate confluence or ignore contradicting data?
3. Are the bear's risks genuine and material, or speculative and unlikely?
4. Are the bull's strengths specific and verifiable, or vague and hopeful?
5. Does the knowledge base context (historical parallels, insights) support or contradict the trade?

## Your Default Bias: CAPITAL PRESERVATION
- If the arguments are roughly equal in strength: REJECT. Ties go to the bear.
- Only APPROVE if the bull case is CLEARLY and SPECIFICALLY stronger than the bear case.
- A CANDIDATE with genuine weaknesses identified by the bear should be REJECTED even if the bull makes a decent case.

## Confidence Score Guidelines
- 85-100: Overwhelming bull case, bear found no material weaknesses
- 70-84: Strong bull case, bear's concerns are minor or manageable
- 50-69: Bull case is stronger but bear raised valid concerns. Trade proceeds but flagged as marginal.
- Below 50: Insufficient conviction → treated as REJECT regardless of verdict field

## Rules
- You do NOT produce new analysis. You evaluate the arguments presented.
- If either agent's argument contains claims not supported by the Market State Object data, call it out.
- Be explicit about which specific point tipped your decision.

## Output Format
Respond with ONLY valid JSON matching the Verdict schema. No preamble.

{
  "verdict": "APPROVE | REJECT",
  "winning_perspective": "BULL | BEAR",
  "confidence_score": 0-100,
  "bull_argument_strength": 0-100,
  "bear_argument_strength": 0-100,
  "key_factor": "...",
  "risk_concerns_acknowledged": ["..."],
  "summary": "..."
}
```

### 5.6 Bull/Bear Rebuttal Prompts (Round 2)

**Bull Rebuttal:**
```
You are the Bull Agent. You have read the Bear's argument against this trade. Respond to their specific points. For each bear point: either rebut it with specific data, or concede it as valid. Be honest — conceding weak points strengthens your overall credibility.

Bear's argument: {bear_round1_json}

Output JSON only:
{"points_addressed": [...], "rebuttal": "...", "concessions": [...]}
```

**Bear Rebuttal:**
```
You are the Bear Agent. You have read the Bull's argument for this trade. Respond to their specific points. For each bull point: either challenge it with specific counter-evidence, or concede it as valid. Your job is still to protect capital — but intellectual honesty strengthens your case.

Bull's argument: {bull_round1_json}

Output JSON only:
{"points_addressed": [...], "rebuttal": "...", "concessions": [...]}
```

### 5.7 Anti-Hallucination Measures

Applied across ALL agent prompts:

1. **Data grounding:** Every prompt includes: "Base ALL analysis on the price data provided. If a price level, swing, or pattern is not present in the Market State Object, it does not exist."

2. **Explicit uncertainty:** "If you cannot determine a structure direction with high confidence from the data provided, state 'unclear' — do not force a classification."

3. **Self-check instruction** (Primary Analyzer only): Built into Step 7 — forces the model to question its own reasoning before outputting CANDIDATE.

4. **Judge verification:** The Judge is explicitly instructed to "flag any claim by Bull or Bear that is not supported by the Market State Object data."

5. **Strict JSON output enforcement:** All prompts end with "Respond with ONLY valid JSON matching the schema. No preamble, no markdown fences, no explanation outside the JSON structure."

6. **Retry with format correction:** If the response isn't valid JSON, retry once with: "Your previous response was not valid JSON. Please respond with ONLY a valid JSON object. No text before or after the JSON."

---

## 6. Three-Layer Retrieval System Design

### 6.1 Layer 1 — Structured Query (Fast, Recent, Exact)

**Source Files:**
- `knowledge_base/index/_trade_index.json`
- `knowledge_base/statistics/rolling_stats.json`
- `knowledge_base/patterns/failure_patterns.json`
- `knowledge_base/statistics/regime_analysis.json`
- `knowledge_base/rules/pending_reviews.yaml`

**Query Logic:** Direct file reads. No search needed — these are small, structured files loaded into memory.

**Update Frequency:** After every completed trade.

**What It Provides to the Prompt:**
```
RECENT PERFORMANCE:
- Last 10 trades: [WIN 3.2R, LOSS -1.0R, WIN 2.8R, ...]
- Rolling win rate: 48%
- Rolling expectancy: 0.86R per trade
- Current drawdown: 1.2%
- Max consecutive losses (historical): 6
- Active failure pattern: "Sweeps during high-impact news → all losses (n=5)"
- Current regime: trending_bullish (since 2026-06-15)
- Pending reviews: None
```

**Token Budget:** ~200-400 tokens.

### 6.2 Layer 2 — Compressed Insights (Distilled Wisdom, Weekly)

**Source File:** `knowledge_base/insights/current_insights.yaml`

**Update Frequency:** Weekly (Sunday) by Component 6.

**What It Provides:** The full YAML file is injected verbatim. It's designed to be compact (~500 tokens) and encode the most important learned patterns from the entire trade history.

**Key Sections Injected:**
- Condition-level win rates and expectancy (flagged as STRONG_EDGE, UNDERPERFORMING, etc.)
- Debate calibration stats
- Regime performance
- Active failure patterns
- Rule modification history

**Token Budget:** ~400-600 tokens.

### 6.3 Layer 3 — Vector Similarity (Historical Parallels, Real-Time)

**Source:** LanceDB `trades.lance` table.

**Query Flow:**
```python
def vector_retrieval_flow(market_state):
    # 1. Generate text summary of current conditions
    current_text = (
        f"{market_state['timeframes']['D1']['structure']['direction']} Daily | "
        f"H4 {'aligned' if is_aligned(market_state) else 'conflicting'} | "
        f"{get_sweep_description(market_state)} | "
        f"{get_displacement_description(market_state)} | "
        f"{datetime.utcnow().strftime('%A')} | "
        f"{get_regime(market_state)}"
    )
    
    # 2. Embed
    query_vector = embed_model.encode(current_text).tolist()
    
    # 3. Query LanceDB — top 5 most similar
    table = db.open_table("trades")
    results = table.search(query_vector).limit(5).to_list()
    
    # 4. Format for prompt injection
    similar_setups = []
    for r in results:
        similar_setups.append({
            "trade_id": r["trade_id"],
            "similarity": round(1 - r["_distance"], 2),
            "date": r["date"],
            "direction": r["direction"],
            "outcome": r["outcome"],
            "r_multiple": r["r_multiple"],
            "setup_grade": r["setup_grade"],
            "conditions": r["text_summary"],
            "postmortem": r["postmortem_summary"]
        })
    
    return similar_setups
```

**What It Provides to the Prompt:**
```
SIMILAR HISTORICAL SETUPS (from knowledge base):

1. tr_2026-02-10_001 (similarity: 0.92)
   Conditions: Bullish Daily aligned H4 | Asian low sweep clean | Strong displacement | Tuesday | Trending bullish
   Outcome: WIN 3.2R
   Postmortem: "Clean setup, displacement was 2.1x average..."

2. tr_2026-01-22_001 (similarity: 0.87)
   Conditions: Bullish Daily aligned H4 | Asian low sweep messy | Medium displacement | Monday | Trending bullish
   Outcome: LOSS -1.0R
   Postmortem: "Sweep was actually a run — price continued lower..."
```

**Token Budget:** ~300-500 tokens (5 setups × ~80 tokens each).

### 6.4 Total Context Assembly

```python
def build_full_context(market_state):
    layer1 = build_layer1_context()       # ~300 tokens
    layer2 = load_insights_yaml()          # ~500 tokens
    layer3 = vector_retrieval_flow(market_state)  # ~400 tokens
    
    # Total KB context: ~1,200 tokens
    # Market State Object: ~2,000–3,000 tokens
    # System prompt + rules: ~1,500 tokens
    # Total input per Primary Analyzer call: ~5,000–6,000 tokens
    
    return {
        "layer1": layer1,
        "layer2": layer2,
        "layer3": layer3
    }
```

---

## 7. Sequence Diagrams

### 7.1 (a) Normal Session — Debate → Trade Execution

```
Time    Orchestrator       Comp1      Comp2      Comp3A     Comp3B          Comp4      Comp5
─────   ────────────       ─────      ─────      ──────     ──────          ─────      ─────
06:45   Initialize()
        │
        ├─Pre-session──────►Pull D1/H4──►Compute──►                         │
        │                   data        state                                │
        │◄──────────────────────────────────────────────────────────────────Load KB
        │                                                                    context
07:00   wait_m15_close()
        │
07:15   run_pipeline()
        ├──────────────────►Ingest()
        │                   │
        │                   ├──writes──► 01_raw_data.json
        │                   │
        │  ◄────────────────┘
        │
        ├──────────────────────────────►Analyze()
        │                               │
        │                               ├──writes──► 02_market_state.json
        │                               │
        │  ◄────────────────────────────┘
        │
        ├──Load 3-layer context──────────────────────────────────────────────►assemble()
        │  ◄────────────────────────────────────────────────────────────────context
        │
        ├──────────────────────────────────────────►Evaluate()
        │                                           │
        │                                           │ decision = CANDIDATE
        │                                           ├──writes──► 03a_primary.json
        │  ◄────────────────────────────────────────┘
        │
        │  transition(EVALUATING → CANDIDATE)
        │
        ├──────────────────────────────────────────────────────►Debate()
        │                                                       │
        │                                                       ├─async──► Bull Agent ──┐
        │                                                       ├─async──► Bear Agent ──┤
        │                                                       │◄──────────────────────┘
        │                                                       ├──writes──► 03b_r1.json
        │                                                       │
        │                                                       │ (Round 2 if enabled)
        │                                                       ├──────────► Bull Rebuttal
        │                                                       ├──────────► Bear Rebuttal
        │                                                       ├──writes──► 03b_r2.json
        │                                                       │
        │                                                       ├──────────► Judge
        │                                                       ├──writes──► 03b_verdict.json
        │                                                       │
        │                                                       │ verdict = APPROVE (82)
        │  ◄────────────────────────────────────────────────────┘
        │
        │  transition(CANDIDATE → DEBATED)
        │
        │  run_safety_checks() → ALL PASS
        │
        │  transition(DEBATED → APPROVED)
        │
        ├──────────────────────────────────────────────────────────────────►Execute()
        │                                                                   │
        │                                                                   ├─MT5 order_send()
        │                                                                   │ fill confirmed
        │                                                                   ├──writes──► 04_exec.json
        │  ◄────────────────────────────────────────────────────────────────┘
        │
        │  transition(APPROVED → EXECUTING → ACTIVE)
        │
        │  ═══ MONITORING LOOP ═══
        │
08:22   │  TP1 hit → close 50%, SL → BE
        │  log PARTIAL_TP1 event
        │
09:15   │  TP2 hit → close 25%, trail SL
        │  log PARTIAL_TP2 event
        │
10:45   │  TP3 hit → runner closed
        │  transition(ACTIVE → CLOSED)
        │  exit_substate = CLOSED_TP3_RUNNER
        │
        │  ═══ POST-SESSION ═══
        │
11:00   generate_session_manifest()
        │
        ├──Postmortem (Sonnet)────────────────────────────────────────────── ►write postmortem
        ├──Update LanceDB──────────────────────────────────────────────────► embed + store
        ├──Update rolling stats────────────────────────────────────────────► update files
        │
        │  DONE
```

### 7.2 (b) Session Where Bear Wins

```
Time    Orchestrator       Comp3A          Comp3B              Result
─────   ────────────       ──────          ──────              ──────

07:15   pipeline cycle
        │
        ├──────────────────►CANDIDATE
        │                   (confidence: 65)
        │
        ├──────────────────────────────────►Debate Round 1
        │                                   │
        │                                   Bull: "Displacement is 1.8x,
        │                                          sweep was clean..."
        │                                   Bear: "Displacement is only 1.8x —
        │                                          borderline. H4 has a bearish
        │                                          FVG overhead at 3048 that
        │                                          could cap the move. Similar
        │                                          setup tr_2026-02-14 with
        │                                          1.7x displacement: LOSS."
        │                                   │
        │                                   Judge: REJECT (confidence: 42)
        │                                   Key factor: "Bear identified
        │                                   specific H4 resistance and
        │                                   historical parallel showing
        │                                   borderline displacement fails"
        │  ◄────────────────────────────────┘
        │
        │  transition(CANDIDATE → DEBATED → REJECTED)
        │
        │  Log REJECTED with full debate transcript
        │  Write to no_trades/ with rejection details
        │
07:30   │  Continue evaluating remaining candles...
        │  (May find another CANDIDATE or end session with no trade)
```

### 7.3 (c) No-Trade Session

```
Time    Orchestrator       Comp3A          Result
─────   ────────────       ──────          ──────

06:45   Pre-session
        Daily bias: ranging (HH followed by LL — transitional)

07:00   Candle evaluation
        ├──────────────────►NO_TRADE
        │                   Reason: "Daily structure ranging — Step 1 fails"
        │
07:15   Candle evaluation
        ├──────────────────►NO_TRADE
        │                   Reason: "Daily unchanged — still ranging"
        │
07:30   ├──────────────────►NO_TRADE (same reason)
07:45   ├──────────────────►NO_TRADE (same reason)
08:00   ├──────────────────►NO_TRADE (same reason)
        ...
09:15   ├──────────────────►NO_TRADE (same reason)

09:30   Session window closes.
        
        Generate session manifest:
        - 10 candles evaluated
        - 0 CANDIDATE, 0 WAIT, 10 NO_TRADE
        - All NO_TRADE due to Daily ranging
        - API calls: 10 (Primary Analyzer only, no debates)
        - Cost: ~$0.05
        
        Write nt_2026-03-27_0700.yaml (one record for the whole day since reason is identical)
```

### 7.4 (d) Adaptive Review Cycle — Weekly Insight Generation

```
Time    Component 6            Component 5 (KB)          Claude API
─────   ───────────            ────────────────          ──────────

Sunday
10:00   weekly_review_trigger()
        │
        ├──Load all trade data──►rolling_stats.json
        │                       condition_performance.json
        │                       last 50 trade records
        │  ◄────────────────────data loaded
        │
        ├──Calculate condition-level breakdown
        │  (pure Python — no AI)
        │  
        │  Monday Asian low: 22 trades, 35% WR, 0.12R expectancy
        │  Medium displacement: 18 trades, 28% WR, -0.15R
        │  Tue-Thu strong disp: 68 trades, 62% WR, 1.45R
        │
        ├──Generate insights YAML──────────────────────────►Sonnet call
        │                                                   "Compress this data
        │                                                    into insights YAML"
        │  ◄────────────────────────────────────────────────YAML response
        │
        ├──Validate YAML structure (parse check)
        │
        ├──atomic_write()──────►insights/current_insights.yaml
        │
        ├──Check adaptation tiers
        │  │
        │  ├─Tier 2: Flag "medium displacement" (deviation >15%, n=18)
        │  │
        │  ├─Tier 3: If n >= 50, propose modification
        │  │  (medium displacement not yet at 50 — stays Tier 2)
        │  │
        │  ├──Write flags to pending_reviews.yaml
        │
        ├──Generate debate calibration report
        │  Bull win rate: 71%, false approvals: 18%, false rejections: 12%
        │
        ├──Update quality score trends
        │
        │  DONE — weekly review complete
        │  API calls used: 1 (within 5-call budget)
```

### 7.5 (e) Vector Similarity Retrieval Flow

```
Orchestrator              Embedding Model           LanceDB              Prompt Builder
────────────              ───────────────           ───────              ──────────────

Before Primary Analyzer call:
│
├──Build current conditions text:
│  "Bullish Daily aligned H4 | Asian low sweep
│   clean | Pending M15 CHoCH | Tuesday |
│   Trending bullish regime"
│
├──────────────────────────►encode(text)
│  ◄────────────────────────[0.12, -0.34, 0.56, ...]  (384-dim vector)
│
├──────────────────────────────────────────────────►search(vector, limit=5)
│                                                   │
│                                                   │ Compute L2 distance
│                                                   │ against all stored
│                                                   │ trade vectors
│                                                   │
│                                                   │ Return top 5:
│                                                   │ 1. tr_2026-02-10 (dist: 0.08)
│                                                   │ 2. tr_2026-01-22 (dist: 0.13)
│                                                   │ 3. tr_2026-03-05 (dist: 0.19)
│                                                   │ 4. tr_2026-02-28 (dist: 0.22)
│                                                   │ 5. tr_2026-01-08 (dist: 0.31)
│  ◄────────────────────────────────────────────────results
│
├──Format for prompt injection─────────────────────────────────────────►inject into
│  "Similar setup 1: tr_2026-02-10, similarity 0.92,                    Layer 3 context
│   WIN 3.2R. Postmortem: clean setup, 2.1x displacement..."            block
│
│  Context assembled. Ready for Primary Analyzer call.
```

---

## 8. File-on-Disk Pipeline State Diagram

### 8.1 Files Written Per Pipeline Stage

```
STAGE                  FILES WRITTEN                           LOCATION                        PERSISTENCE
─────                  ─────────────                           ────────                        ───────────

Ingestion              01_raw_data.json                        pipeline_state/                 Ephemeral (overwritten)

Market State           02_market_state.json                    pipeline_state/                 Ephemeral (overwritten)

Primary Analysis       03a_primary_analysis.json               pipeline_state/                 Ephemeral (overwritten)

Debate Round 1         03b_debate_round1.json                  pipeline_state/                 Ephemeral (overwritten)
                       (only if CANDIDATE)

Debate Round 2         03b_debate_round2.json                  pipeline_state/                 Ephemeral (overwritten)
                       (only if enabled)

Verdict                03b_verdict.json                        pipeline_state/                 Ephemeral (overwritten)
                       (only if CANDIDATE)

Execution              04_execution_log.json                   pipeline_state/                 Ephemeral (overwritten)
                       (only if APPROVED)

── SESSION BOUNDARY ──

Session Manifest       YYYY-MM-DD_session.json                 sessions/                       Permanent (append-only)

Trade Record           tr_YYYY-MM-DD_NNN.yaml                  trades/                         Permanent (append-only)
                       (only if trade executed)

No-Trade Record        nt_YYYY-MM-DD_HHMM.yaml                 no_trades/                      Permanent (append-only)
                       (one per NO_TRADE evaluation,
                        or grouped if same reason)

Postmortem             pm_tr_YYYY-MM-DD_NNN.yaml               postmortems/                    Permanent (append-only)
                       (only after trade closes)

LanceDB Entry          row in trades.lance                      vectordb/                       Permanent (append-only)
                       (only after trade closes)

Rolling Stats          rolling_stats.json                       statistics/                     Updated in-place
Trade Index            _trade_index.json                        index/                          Updated in-place
Quality Scores         quality_scores.json                      statistics/                     Updated in-place

── WEEKLY ──

Insights               current_insights.yaml                    insights/                       Overwritten weekly
Weekly Journal         YYYY-WNN.yaml                            journals/weekly/                Permanent
```

### 8.2 Pipeline State Directory Lifecycle

```
At candle 07:00 close:
  pipeline_state/
  ├── 01_raw_data.json          ← NEW
  ├── 02_market_state.json      ← NEW
  ├── 03a_primary_analysis.json ← NEW (decision: WAIT)
  └── (no 03b or 04 files — not CANDIDATE)

At candle 07:15 close:
  pipeline_state/
  ├── 01_raw_data.json          ← OVERWRITTEN with new data
  ├── 02_market_state.json      ← OVERWRITTEN
  ├── 03a_primary_analysis.json ← OVERWRITTEN (decision: CANDIDATE)
  ├── 03b_debate_round1.json    ← NEW (debate triggered)
  ├── 03b_debate_round2.json    ← NEW (round 2 enabled)
  ├── 03b_verdict.json          ← NEW (APPROVE, confidence 82)
  └── 04_execution_log.json     ← NEW (trade placed)

At session end:
  → Session manifest captures summary of ALL candle evaluations
  → Trade record written to trades/
  → Pipeline state files remain until next session overwrites them
```

---

## 9. Testing Strategy

### 9.1 Phase 1 — Backtesting Harness

**Objective:** Validate AI reasoning quality against 200+ historical London Open sessions.

**Setup:**
- Pre-compute Market State Objects for 200+ historical sessions (Oct 2025 – Mar 2026)
- Feed each MSO through Components 3A and 3B
- Compare agent decisions against actual market outcomes
- No MT5 connection needed — historical data preloaded

**Metrics:**

| Metric | Target | How Measured |
|---|---|---|
| Primary Analyzer accuracy | >60% correct NO_TRADE/CANDIDATE classification | Compare decision to actual outcome (was there a valid setup that hit 1:3+?) |
| False positive rate | <30% of CANDIDATE decisions that would have been losers | Track CANDIDATE outcomes |
| False negative rate | <20% of actual winning setups classified as NO_TRADE | Manually review NO_TRADE days for missed setups |
| Debate false approval rate | <20% of APPROVED trades that lose | Track APPROVED outcomes |
| Debate false rejection rate | <15% of REJECTED trades that would have won | Retroactively evaluate rejected setups |
| Combined system accuracy | Positive expectancy (0.5R+) on approved trades | Calculate expectancy on all APPROVED trades |

**Debate Calibration Process:**
1. Run first 50 sessions with debate disabled → measure Primary Analyzer standalone accuracy
2. Enable debate Round 1 only → measure improvement in accuracy
3. Enable Round 2 → measure marginal improvement vs added cost
4. If Round 2 adds <3% accuracy improvement, disable for live trading to save costs

**Model Tier Comparison:**
1. Run 50 identical sessions through both Opus and Sonnet for Components 3A/3B
2. Compare:
   - Decision agreement rate (how often they make the same call)
   - Reasoning quality (blind human review of 20 random outputs)
   - Qualitative assessment accuracy (displacement quality, sweep classification)
3. Decision rule: If Sonnet accuracy is within 5% of Opus, use Sonnet everywhere

**Retrieval Quality Testing:**
1. After 50 backtested trades are in LanceDB, test similarity search quality
2. For each new setup, verify that the top 5 similar setups are genuinely similar (human review)
3. Measure: precision@5 (how many of top 5 are relevant) — target >60%
4. If retrieval quality is poor, evaluate alternative embedding models or richer text summaries

### 9.2 Phase 2 — Paper Trading

**Objective:** Validate real-time execution, latency, and data freshness.

**Metrics:**

| Metric | Target | How Measured |
|---|---|---|
| End-to-end pipeline latency | <90 seconds from M15 close to order placed | Timestamp pipeline start vs order_send() |
| Debate round latency | <30 seconds for Round 1 (parallel Bull+Bear) | Timestamp debate start vs verdict |
| Data freshness | M15 candle available within 5 seconds of close | Compare MT5 candle time vs ingestion time |
| MT5 execution success rate | >98% | Successful orders / attempted orders |
| Slippage | <$0.50 average | Abs(fill_price - intended_entry) |
| Partial close success rate | 100% | All TP1/TP2 partials execute correctly |
| Crash recovery success | 100% | Simulated crashes → verify state recovery |
| Daily cost | <$0.50 | Track API calls and costs |

**Testing Process:**
1. Run for 20 sessions in "shadow mode" — agent makes decisions but doesn't place orders. Compare its decisions to what you would have done manually.
2. Enable order placement on demo account for 80+ sessions.
3. Simulate edge cases: MT5 disconnect mid-session, API timeout, malformed response.

### 9.3 Phase 3 — Live Micro Account

**Objective:** Validate with real money, real spreads, real slippage.

**Metrics:**

| Metric | Target | How Measured |
|---|---|---|
| Win rate | 40-55% | Wins / total trades |
| Expectancy | >0.5R per trade | (WR × avg_win) - (LR × avg_loss) |
| Max drawdown | <8% | Peak-to-trough equity |
| Setup compliance | 90%+ | Deterministic quality score |
| Reasoning quality | >80 avg LLM score | Weekly postmortem review |
| Daily cost | <$0.40 | Budget tracking |
| Zero rule violations | 0 | No >1 trade/day, no >1% risk, no off-session trades |

**Human Review Protocol (first 30 days):**
- Every trade: review Primary Analyzer reasoning, debate transcript, execution log
- Every rejection: verify the Bear's reasoning was sound
- Every NO_TRADE day: spot-check that no valid setup was missed
- Weekly: review Obsidian vault, check quality score trends

### 9.4 Integration Tests (Automated)

```python
# Run before every deployment

def test_lifecycle_transitions():
    """Verify all valid transitions work and invalid ones raise."""
    assert transition("EVALUATING", "CANDIDATE") == OK
    assert transition("EVALUATING", "APPROVED") raises InvalidTransitionError
    assert transition("CLOSED", "ACTIVE") raises InvalidTransitionError

def test_safety_checks_block_on_spread():
    """Spread > 30 cents must block execution."""
    params = make_test_params(spread=35)
    checks = safety_checks(params, test_account, test_session)
    assert checks["spread_ok"] == False
    assert checks["all_passed"] == False

def test_safety_checks_block_on_daily_loss():
    """2% daily loss must block further trading."""
    session = make_test_session(daily_pnl_pct=-2.1)
    checks = safety_checks(test_params, test_account, session)
    assert checks["daily_loss_ok"] == False

def test_position_sizing():
    """Verify position size formula."""
    lots = calculate_position_size(balance=1000, sl_distance=10)
    assert lots == 0.10  # (1000 * 0.01) / (10 * 100) = 0.10

def test_atomic_write_survives_crash():
    """Verify atomic write doesn't corrupt files on simulated crash."""
    # Write to file, simulate crash mid-write of next update
    # Verify original content preserved

def test_verdict_evaluation_logic():
    """Test all verdict → decision mappings."""
    assert evaluate_verdict({"verdict": "APPROVE", "confidence_score": 80}) == "APPROVED"
    assert evaluate_verdict({"verdict": "APPROVE", "confidence_score": 55}) == "APPROVED_MARGINAL"
    assert evaluate_verdict({"verdict": "APPROVE", "confidence_score": 40}) == "REJECTED"
    assert evaluate_verdict({"verdict": "REJECT", "confidence_score": 90}) == "REJECTED"

def test_pipeline_state_overwrite():
    """Verify pipeline_state files are correctly overwritten each candle."""
    write_pipeline("01_raw_data.json", {"candle": 1})
    write_pipeline("01_raw_data.json", {"candle": 2})
    data = read_pipeline("01_raw_data.json")
    assert data["candle"] == 2

def test_lock_file_prevents_duplicate():
    """Only one orchestrator instance allowed."""
    orch1 = SessionOrchestrator()
    with pytest.raises(RuntimeError, match="already running"):
        orch2 = SessionOrchestrator()
```

---

## 10. Risk & Failure Mode Analysis

### 10.1 API Call Fails Mid-Debate

**Scenario:** Bull Agent completes, Bear Agent API call times out.

**Impact:** Debate cannot complete — only one perspective exists.

**Mitigation:**
1. Retry Bear Agent once (5-second timeout, then 10-second retry).
2. If still failed: verdict is automatically `REJECTED` with reason `"bear_agent_api_failure"`.
3. Rationale: Never approve a trade without adversarial challenge. Single-perspective approval is the exact confirmation bias the debate is designed to prevent.
4. Log the failure in session manifest for post-session review.

**Scenario:** Judge API call fails after both agents complete.

**Mitigation:** Same — retry once, then `REJECTED`. No trade without a Judge verdict.

### 10.2 MT5 Disconnects

**Scenario A: Disconnect before order placement.**
- Impact: Cannot execute trade.
- Mitigation: `FAILED_EXECUTION` with reason `"mt5_disconnect"`. Retry connection 3× with 5-second delay. If restored within the session window AND the setup is still valid (re-evaluate), attempt execution. Otherwise, log and move on.

**Scenario B: Disconnect during active trade.**
- Impact: Cannot manage partials or trail stop.
- Mitigation: SL and TP1 are server-side (attached to the order at placement). They execute regardless of client connection. The broker's server manages the hard risk. On reconnection: sync trade state from MT5 history, determine if TP1 hit, update trade record.
- Remaining risk: If TP1 hit but client didn't move SL to breakeven (because disconnected), the trade could reverse past original entry. This is acceptable — the original SL is still in place, limiting max loss to 1R.

**Scenario C: Disconnect during order placement (after order_send, before confirmation).**
- Mitigation: On reconnection, check `mt5.positions_get(symbol="XAUUSD")` and `mt5.history_orders_get()` for the magic number. If position exists → transition to ACTIVE. If no position → transition to FAILED_EXECUTION. Never send a duplicate order.

### 10.3 AI Returns Malformed Output

**Scenario:** Claude returns valid text but not valid JSON (e.g., includes preamble, markdown fences, or partial JSON).

**Mitigation:**
1. First attempt: Strip markdown fences (`\`\`\`json` ... `\`\`\``), strip leading/trailing whitespace, attempt parse.
2. If fails: Retry with explicit correction appended: "Your previous response was not valid JSON. Respond with ONLY a valid JSON object. No other text."
3. If second attempt also fails: Output `NO_TRADE` with reason `"ai_output_malformed"`. Log full raw response for debugging.
4. If this happens more than 3 times in a single session: Alert `SYSTEM_ERROR` for human review. Possible model degradation.

**Scenario:** Claude returns valid JSON but with incorrect values (e.g., `direction: "UPWARD"` instead of `"LONG"`).

**Mitigation:** Strict enum validation on all fields. Any value not in the expected set → treat as malformed, retry once, then NO_TRADE.

### 10.4 Market Gaps Through Stop Loss

**Scenario:** Gold gaps $30+ past the stop loss on a news event (e.g., flash crash, geopolitical shock). Actual loss exceeds 1%.

**Mitigation:**
1. **Prevention:** The no-trade filter blocks trading during high-impact news windows. The agent checks `high_impact_events` before every evaluation.
2. **Damage control:** The 2% daily loss limit acts as a circuit breaker. Even a gap loss of 2-3% triggers the daily kill switch.
3. **Architectural acceptance:** Gap risk is inherent in leveraged trading. The 1% position sizing ensures even a 3× gap (loss of 3%) is survivable. Account survives 10+ consecutive 3% losses before reaching 30% drawdown.
4. **Post-event:** The postmortem and adaptive review capture the event. If gap losses accumulate around specific conditions (e.g., Monday opens, pre-NFP), the Tier 2/3 adaptation system flags and potentially filters them.

### 10.5 Bear Agent Consistently Rejects Everything

**Scenario:** Bear agent develops a pattern of overly strong arguments, causing >80% rejection rate. Very few trades get through. System becomes too conservative.

**Detection:** Weekly debate calibration in `current_insights.yaml`. If `bear_win_rate > 0.80` over 30+ debates, flag as `BEAR_OVER_AGGRESSIVE`.

**Mitigation:**
1. Review the Bear's rejected trades retroactively — calculate what would have happened if those trades were taken.
2. If `false_rejection_rate > 25%` (rejected trades that would have been profitable): adjust the Bear's prompt to include: "Your rejection rate is currently {X}%. Historical analysis shows {Y}% of your rejections would have been profitable trades. Ensure your objections are based on specific, material weaknesses — not generic risk aversion."
3. Alternatively, adjust the Judge's threshold: lower APPROVE confidence threshold from 70 to 60 if Bear is persistently over-aggressive.
4. Hard guardrail: If rejection rate exceeds 90% for 2 consecutive weeks, alert for human review of Bear prompt.

### 10.6 Bull Agent Is Too Aggressive

**Scenario:** Bull agent approves setups that consistently lose. System takes too many bad trades.

**Detection:** Track `false_approval_rate` — if >30% of APPROVED trades are losses AND the Bear identified the winning concern pre-trade, the Bull is overriding legitimate objections.

**Mitigation:**
1. Increase Judge's capital preservation bias: "Recent data shows {false_approval_rate}% of approved trades lost. Weight bear arguments more heavily."
2. If `false_approval_rate > 40%` over 50+ debates: adjust Bull prompt to include self-check: "Before presenting your case, verify: Am I citing specific data or making emotional arguments?"
3. Hard guardrail: If combined system expectancy drops below 0R for 3 consecutive weeks, pause live trading and return to backtesting to recalibrate.

### 10.7 LanceDB Returns Irrelevant Historical Matches

**Scenario:** The top 5 similar setups from LanceDB are not actually similar — e.g., bullish setups compared to bearish ones, or trending regime compared to ranging.

**Detection:** Human review during Phase 1/2. Automated: if the top match has similarity < 0.60, the matches may be low quality.

**Mitigation:**
1. Improve text summary quality — include more discriminating features in the embedding text (specific liquidity type, exact structure description, displacement ratio).
2. Add metadata filtering to LanceDB queries — pre-filter by direction, regime, or daily bias before vector search: `table.search(vector).where("direction = 'LONG'").limit(5)`.
3. If top match similarity < 0.50, inject a note: "No closely similar historical setups found. The agent should rely more heavily on current market data and less on historical parallels."
4. Evaluate alternative embedding models if MiniLM consistently underperforms. `all-mpnet-base-v2` offers better quality at higher compute cost.

### 10.8 Embedding Model Quality Degrades

**Scenario:** Over time, the embedding model produces less useful similarity scores (possible if market regime shifts significantly from the distribution the model was trained on).

**Detection:** Track precision@5 monthly — manually review 20 random similarity queries and score relevance.

**Mitigation:**
1. If precision@5 drops below 40%: re-evaluate the text summary format. Possibly switch to a more descriptive format.
2. Consider fine-tuning the embedding model on trade summaries (requires 100+ examples).
3. If embedding quality is fundamentally insufficient: fall back to metadata-based filtering only (Layer 1 + Layer 2 without Layer 3) until resolved.
4. Layer 3 is additive — the system functions without it (Layers 1+2 provide the core context). Degraded embeddings should not break the system, only reduce the quality of historical parallel retrieval.

### 10.9 Knowledge Base Files Corrupt

**Scenario:** A critical file (`rolling_stats.json`, `active_rules.yaml`, `_trade_index.json`) becomes corrupted (e.g., power loss during non-atomic write, disk error).

**Mitigation:**
1. **Prevention:** All writes use the atomic write pattern (temp file + `os.replace()`). `os.replace()` is atomic on both POSIX and Windows (same filesystem).
2. **Detection:** On startup, validate all critical files against expected schemas. If any fail validation, alert.
3. **Recovery for statistics/index:** These are derived data. They can be rebuilt from the source trade records in `trades/`. A recovery script scans all `tr_*.yaml` files and regenerates `rolling_stats.json`, `_trade_index.json`, `quality_scores.json`, etc.
4. **Recovery for rules:** `base_rules.yaml` is the restore point. If `active_rules.yaml` is corrupt, copy `base_rules.yaml` over it. Any modifications are logged in `rule_modifications_log.yaml` and can be replayed.
5. **Recovery for LanceDB:** LanceDB uses the Lance columnar format with built-in versioning. It can self-recover from most corruption. If truly unrecoverable, regenerate from trade records (re-embed all text summaries).
6. **Recovery for pipeline_state:** These are ephemeral. Corruption here just means one candle evaluation is lost — the next candle overwrites everything. No permanent impact.

### 10.10 Cost Overrun

**Scenario:** API costs exceed the $25/month budget due to excessive retries, verbose prompts, or unexpected debate frequency.

**Detection:** Track API call count and estimated cost per session in session manifest. Dashboard surfaces daily/weekly/monthly cost.

**Mitigation:**
1. Budget cap enforcement: If monthly spend exceeds $20, switch Component 3A/3B from Opus to Sonnet (if not already).
2. If spend exceeds $25, disable Round 2 of debate for the remainder of the month.
3. If spend exceeds $30, alert for human review — something is anomalous.
4. Reduce prompt token count: trim knowledge base context if it grows beyond expected size. Cap Layer 3 at 3 results instead of 5.

---

## Appendix A — Configuration File (`agent_config.yaml`)

```yaml
# knowledge_base/meta/agent_config.yaml

market:
  symbol: "XAUUSD"
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
  max_trades_per_day: 1
  min_rr: 3.0
  max_spread_cents: 30
  sl_buffer_dollars: 1.20

model_a:
  bias_timeframes: ["D1", "H4"]
  setup_timeframe: "H1"
  entry_timeframe: "M15"
  ote_zone_fib_top: 0.618
  ote_zone_fib_bottom: 0.786
  displacement_min_ratio: 1.5
  equal_level_tolerance: 2.50

ai:
  primary_model: "claude-sonnet-4-20250514"
  debate_model: "claude-sonnet-4-20250514"
  postmortem_model: "claude-sonnet-4-20250514"
  review_model: "claude-sonnet-4-20250514"
  debate_round2_enabled: true
  max_api_retries: 1
  api_timeout_seconds: 30

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
    D1: 5.0
    H4: 3.0
    H1: 2.0
    M15: 1.0

adaptation:
  tier2_deviation_threshold: 0.15
  tier2_min_samples: 20
  tier3_min_samples: 50
  tier4_min_total_trades: 200
  tier4_max_affected_pct: 0.20
  tier4_min_expectancy_improvement: 0.10
  rollback_review_trades: 30
  max_modifications_per_50_trades: 1

monitoring:
  dashboard_port: 8080
  obsidian_export_enabled: false
  obsidian_vault_path: ""
  alert_email: ""

budget:
  monthly_cap_usd: 25.0
  cost_warning_threshold_usd: 20.0
  cost_critical_threshold_usd: 30.0

deployment:
  phase: 1  # 1=backtest, 2=paper, 3=live_micro, 4=scale
  mt5_account: "demo"
  mt5_server: ""
  mt5_login: 0
  mt5_password: ""
```

---

## Appendix B — Implementation Priority Order

For Phase 1 (Backtesting Harness), implement in this order:

1. **Configuration loader** — Parse `agent_config.yaml`
2. **Component 2** — Market State Analyzer (deterministic, testable independently)
3. **Historical data loader** — Pre-compute Market State Objects from TradingView export or MT5 historical data
4. **Component 5** — Knowledge Base (file I/O, LanceDB initialization)
5. **Component 3A** — Primary Analyzer (requires Claude API access)
6. **Component 3B** — Bull/Bear Debate (requires Component 3A working)
7. **Backtesting harness** — Loop over historical sessions, feed MSOs, log outcomes
8. **Component 6** — Adaptive Review (Tier 1 observation only for Phase 1)
9. **Statistics & analysis scripts** — Calculate accuracy, calibration, model comparison

Components 1, 4, 7, and 8 are added in Phase 2 when MT5 connection is needed.

---

*End of architecture document. Every component is specified to implementation-ready precision. Build Phase 1 first. Validate. Then proceed.*
