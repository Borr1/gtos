# Agent Prompt: Real Rates Filter for Gold OB Trades

## Your Mission

Test whether **real interest rates** (TIPS yields) provide a useful filter for gold OB trades. Specifically: does trading gold OBs only when real rates are moving in the "right" direction improve win rate?

---

## The Context You Need

### What is GTOS?

GTOS trades H1 Order Block retests on gold (XAUUSD) and other instruments. The system is purely technical — it uses price structure (D1/H4 bias, H1 OB zones) with no fundamental or macro inputs.

### The Gold-Rates Relationship

Gold has a well-documented inverse relationship with **real interest rates**:
- Real rate = Nominal Treasury yield - Inflation expectations
- Measured by: TIPS yields (Treasury Inflation-Protected Securities)
- When real rates RISE: Gold tends to FALL (opportunity cost of holding gold increases)
- When real rates FALL: Gold tends to RISE (gold becomes more attractive)

This is THE primary macro driver of gold prices. Academic sources:
- Baur & Lucey (2010): Gold as inflation hedge
- Erb & Harvey (2013): "The Golden Dilemma" — real rates explain gold moves
- Numerous Fed papers on gold-rates relationship

### What GTOS Currently Does

The system has NO macro component:
- DXY-gold correlation checked: r=-0.369, R²=0.136 (explains only 14% of moves)
- COT data checked: NULL (p=0.495)
- Decision: don't add macro filters based on these weak signals

**But we never tested real rates directly.**

### The Hypothesis

From ex-bank trader interview:
> "Rates over macro, risk over everything. Learn the short end of the curve."

**Question:** Does aligning OB trade direction with real rate direction improve WR?

- Bullish gold OB + Falling real rates = Aligned → Higher WR?
- Bullish gold OB + Rising real rates = Misaligned → Lower WR?
- (Reverse for bearish OBs)

---

## The Test Design

### Step 1: Get Real Rate Data

**Source:** FRED (Federal Reserve Economic Data) — Free, reliable, daily data

**Series to download:**
- `DGS10` — 10-Year Treasury Constant Maturity Rate
- `DFII10` — 10-Year Treasury Inflation-Indexed Security (TIPS yield)
- OR `T10YIE` — 10-Year Breakeven Inflation Rate (then calculate real rate)

**Preferred:** Use `DFII10` directly — it's the real rate.

**Download:** https://fred.stlouisfed.org/series/DFII10
- Format: CSV
- Date range: 2025-01-01 to 2026-04-01 (covers our batch period)

### Step 2: Calculate Rate Direction

For each trading day, calculate:
```python
def get_rate_direction(date, rate_data, lookback=5):
    """
    Determine if real rates are rising or falling.
    
    Returns: 'RISING', 'FALLING', or 'FLAT'
    """
    current_rate = rate_data[date]
    past_rate = rate_data[date - lookback_days]
    
    change = current_rate - past_rate
    
    if change > 0.05:  # More than 5 bps rise
        return 'RISING'
    elif change < -0.05:  # More than 5 bps fall
        return 'FALLING'
    else:
        return 'FLAT'
```

**Sensitivity analysis:** Test lookback periods of 3, 5, 10 days.

### Step 3: Join with Trade Data

Load the 129 batch trades (or gold-only subset, n=129 if all are gold).

For each trade:
- Get trade date
- Get rate direction on that date
- Get trade direction (LONG/SHORT)
- Determine alignment:
  - LONG + FALLING rates = ALIGNED
  - LONG + RISING rates = MISALIGNED
  - SHORT + FALLING rates = MISALIGNED
  - SHORT + RISING rates = ALIGNED

### Step 4: Analysis

**Primary analysis:**
```
Group trades by alignment:
- ALIGNED: n=?, WR=?
- MISALIGNED: n=?, WR=?
- FLAT/NEUTRAL: n=?, WR=?

Fisher exact test for WR difference
Effect size in percentage points
```

**Secondary analysis:**
```
By rate direction alone:
- Trades during FALLING rates: WR=?
- Trades during RISING rates: WR=?

Note: Most of our trades are LONG (gold bull market), 
so this may conflate direction with alignment.
```

**Tertiary analysis:**
```
Rate momentum strength:
- Strong move (>10 bps change): WR by alignment?
- Weak move (<5 bps change): WR by alignment?

Does stronger rate momentum = stronger alignment effect?
```

### Step 5: Practical Filter Design

If alignment matters, design the filter:

```python
def should_trade(ob_direction, real_rate_direction):
    """
    Returns True if this OB trade should be taken.
    """
    if real_rate_direction == 'FLAT':
        return True  # Trade anyway when rates are stable
    
    aligned = (
        (ob_direction == 'LONG' and real_rate_direction == 'FALLING') or
        (ob_direction == 'SHORT' and real_rate_direction == 'RISING')
    )
    
    return aligned  # Only trade when aligned
```

**Backtest this filter:**
- How many trades would be skipped?
- What's the WR of skipped trades? (confirmation that we're skipping bad ones)
- What's the WR of remaining trades?
- Net impact on frequency × WR?

---

## Decision Criteria

### CONFIRM Real Rates Filter:
- ALIGNED WR significantly > MISALIGNED WR (p < 0.05)
- Effect size >= 10pp
- Filter doesn't kill too many trades (frequency drop < 30%)
- Improvement in WR outweighs frequency reduction

**Implementation:** Add daily real rate direction check. Skip misaligned setups.

### REJECT Real Rates Filter:
- No significant WR difference by alignment OR
- Effect size < 5pp OR
- Filter kills > 50% of trades for marginal WR gain

**Implementation:** None. Continue purely technical approach.

### INCONCLUSIVE:
- Trend exists but p > 0.10
- Sample size too small in one category

**Next step:** Shadow log rate alignment on live trades for larger sample.

---

## Important Considerations

### Gold-Specific Test

This test is ONLY for gold (XAUUSD). Real rates don't have the same relationship with:
- US30 (equity index — different drivers)
- USDJPY/GBPJPY (JPY driven by BOJ policy)
- GBPUSD (UK-US rate differential matters, not just US real rates)

If this filter works, it's a gold-only enhancement.

### Timing Mismatch

- TIPS yields are daily data
- Our trades are intraday (M15/H1)
- We're testing: does the DAILY macro backdrop affect intraday OB success?
- This is a coarse filter, not a precision signal

### Bull Market Bias

Our batch period (Oct 2025 - Mar 2026) was a gold bull market. Most trades are likely LONG. This means:
- Falling rates = both good for gold AND aligned with our LONG bias
- Hard to separate "rates help" from "bull market helps"

**Mitigation:** Focus on the MISALIGNED cases. If LONG trades during RISING rates significantly underperform, that's the actionable signal.

### Data Lag

TIPS yields are published end-of-day. For a trade at 08:00 UTC, we'd use yesterday's close.
- This is fine for a daily regime filter
- Not suitable for intraday rate movements

---

## Output Requirements

Create a report at `research/academic_pipeline/results/real_rates_gold_filter_analysis_v1.md` with:

1. **Data Summary**
   - TIPS yield data range and quality
   - Number of gold trades in batch
   - Distribution of trade dates across rate regimes

2. **Rate Regime Distribution**
   | Regime | Days | Trades | % of Sample |
   | RISING | ? | ? | ? |
   | FALLING | ? | ? | ? |
   | FLAT | ? | ? | ? |

3. **Alignment Analysis**
   | Alignment | n | Wins | WR | 95% CI |
   | ALIGNED | ? | ? | ? | ? |
   | MISALIGNED | ? | ? | ? | ? |

4. **Statistical Tests**
   - Fisher exact test p-value
   - Effect size (pp difference)
   - Odds ratio

5. **Filter Backtest**
   - Trades kept if filter applied: n
   - Trades skipped: n (with their actual WR)
   - Net frequency impact
   - Net WR impact
   - Expected R change per month

6. **Sensitivity Analysis**
   - Results with 3-day lookback
   - Results with 10-day lookback
   - Results with different bps thresholds

7. **Recommendation**
   - CONFIRM / REJECT / INCONCLUSIVE
   - If CONFIRM: exact filter specification
   - Implementation complexity assessment

---

## Files to Read First

1. `CLAUDE.md` — System overview
2. `.context/01_knowledge_base/kb_gold_market_deep_knowledge.md` — Gold market mechanics
3. `research/kap_outputs/exbank_trader_patrick_transcript_analysis.md` — "Rates over macro" quote
4. Look for batch trade data with dates

---

## Why This Matters

If real rates alignment improves WR by 10+ pp:
- This is a FREE filter (public data, zero cost)
- Adds a macro layer without complexity
- Provides early warning when macro headwinds exist

If real rates don't matter:
- Confirms our purely technical approach is sufficient
- Saves us from adding unnecessary complexity
- One less thing to monitor

Either answer simplifies our decision space.

---

*Prompt written by Strategic Research Advisor, April 13, 2026*
