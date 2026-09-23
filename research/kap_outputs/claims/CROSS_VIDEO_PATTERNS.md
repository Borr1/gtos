# Cross-Video Pattern Analysis — Agent 2 Pre-Processing for Agent 3
# Date: 2026-04-06
# Claims analyzed: 226 across 24 videos
# Purpose: Identify corroborations, contradictions, and high-value clusters

---

## KEY CONTRADICTIONS (Agent 3 should prioritize these)

### 1. SWEEP RULE: Required vs Harmful
- **video_19 (IDFX)**: "Liquidity sweep of a prior session high/low is REQUIRED before FVG entry — no sweep = no trade"
- **video_20 (Trader Zan, 10yr quant)**: "The sweep rule does NOT improve performance — REMOVING it improved results by 46%"
- **video_13 (Silver Bullet)**: "NO CHoCH required — just displacement and FVG after sweep"
- **VERDICT**: Most retail traders insist on sweep; the only quant-coded test says remove it. HIGH VALUE test.

### 2. SILVER BULLET WIN RATE: Wild Variance
- **video_20 (Trader Zan, 2310 trades)**: 37.11% WR — most rigorous test
- **video_08 (100 trades)**: 43% WR at 2.5R target
- **video_13**: 75% WR mechanical (88% in-sample)
- **video_19 (8 trades)**: 87.5% WR — absurdly small sample
- **video_21**: 84% WR claim, 70% inside macros
- **VERDICT**: Quant test (2310 trades) says ~37%. Small-sample tests inflate WR dramatically. Sample size IS the variable.

### 3. FVG ENTRY POINT: Edge vs Midpoint
- **video_21 (Blue Edge)**: "Enter at EDGE of FVG (first touch), not middle"
- **video_06**: "Entering at consequent encroachment (MIDPOINT) gives better RR"
- **video_09 (XAUUSD specific)**: "On gold, enter on the WHOLE imbalance zone — gold rarely gives perfect fills"
- **VERDICT**: Depends on instrument. Gold may need wider zone; NQ/ES may allow edge entries.

### 4. DAILY BIAS: Needed vs Not Needed
- **video_16 (TTrades)**: "No daily bias needed — just trade the 9am candle sweep"
- **video_18**: "1H/4H directional filter is essential"
- **VERDICT**: Testable with and without HTF filter on same dataset.

---

## KEY CORROBORATIONS (High confidence — multiple sources agree)

### 1. FRIDAY UNDERPERFORMANCE (4 videos)
- video_01: "Monday and Friday produce more losing trades"
- video_08: "Monday 22% WR, Friday 35% WR; Tue-Thu is profitable zone"
- video_16: "Wednesday best day for Silver Bullet"
- video_24: "Removing Fridays improved gold turtle soup from 61% to 67%"
- **STRENGTH**: 4/4 sources agree. Friday filter is high-confidence improvement.

### 2. MINIMUM 2R TARGET (8+ videos)
- Consistent across video_01, 05, 06, 08, 09, 17, 18, 19, 23
- video_20 quant test: 3R outperformed 2R despite lower WR
- video_13 RR optimizer: ideal is 3.98R
- **STRENGTH**: Near-universal agreement. Our system should target 2R minimum, test 3R.

### 3. ASIAN SESSION AS BIAS DETERMINANT (5 videos)
- video_02: OBs below Asia session lows have high success
- video_04: Asia session must be swept before entry
- video_08: Session liquidity sweep (Asia low in London)
- video_17: Asian/London/9am range must be swept
- video_23: First side swept = directional bias (80% WR with BE management)
- **STRENGTH**: Consistent signal. Asian range sweep as bias filter is well-corroborated.

### 4. LTF CONFIRMATION IMPROVES WR (6 videos)
- video_01: CHoCH on 2-TF-lower within HTF OB
- video_02: 1-min CHoCH within HTF OB zone (doubles RR from 1:3 to 1:7.2)
- video_04: 1M reversal confirmation required
- video_06: MSS at IFVG zone adds confluence
- video_22: 15m CRT confirmation
- video_23: MSS or double purge required
- **STRENGTH**: Universal agreement that LTF confirmation helps. Debate is on WHICH TF (1m vs 5m vs 15m).

### 5. LONDON EARLY HOURS ARE BEST (3 videos, gold-specific)
- video_03: "Around 8AM London, gold produces significant directional move"
- video_24: "First 3 hours of London (3-6am ET) contain bulk of profits"
- video_24: "4-5am ET is optimal single hour for gold turtle soup"
- **STRENGTH**: Gold-specific timing data. Aligns with our London kill zone (07:00-10:30 UTC).

---

## CATEGORY DISTRIBUTION
| Category | Count | % |
|----------|-------|---|
| TRADING_RULES | 81 | 36% |
| STATISTICAL_CLAIMS | 67 | 30% |
| MARKET_MECHANICS | 28 | 12% |
| BACKTESTING_METHODOLOGY | 26 | 12% |
| RISK_MANAGEMENT | 14 | 6% |
| MARKET_MICROSTRUCTURE | 10 | 4% |

## CREDIBILITY DISTRIBUTION
| Source | Count | % |
|--------|-------|---|
| DATA (cites backtest/research) | 116 | 51% |
| EXPERIENCE (personal track record) | 105 | 46% |
| OPINION (no evidence) | 5 | 2% |

## RELEVANCE
| Level | Count | % |
|-------|-------|---|
| DIRECT (OB retest, SMC, kill zones) | 127 | 56% |
| RELATED (market structure, risk math) | 96 | 42% |
| TANGENTIAL | 3 | 1% |

---

## HIGHEST-VALUE VIDEOS FOR OUR SYSTEM
1. **video_20** (Trader Zan) — Only 10-year quant-coded test. Sweep rule removal, FVG decay, 3R>2R.
2. **video_24** (Gold futures turtle soup) — Gold-specific London data. Friday filter. NWOG confluence.
3. **video_08** (100-trade IFVG) — Largest manual backtest. Day-of-week data. Session comparison.
4. **video_01** (100 OB backtest) — OB quality scoring system. Midweek edge. LTF confirmation value.
5. **video_21** (Blue Edge) — Macro timing windows (70% WR inside vs 70% loss outside). NQ/ES correlation.
