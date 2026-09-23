# Agent Prompt: FTMO Survival Optimization Test

## Your Mission

You are testing whether a **different exit philosophy** produces better outcomes for prop firm trading than our current approach. This is not a minor parameter tweak — it's a fundamental question about what we should optimize for.

---

## The Context You Need

### What is GTOS?

GTOS (Gold Traders Operating System) is an autonomous AI trading system that:
- Trades H1 Order Block (OB) retests on XAUUSD, US30, USDJPY, GBPJPY, GBPUSD
- Uses Claude AI to evaluate setups and decide CANDIDATE vs NO_TRADE
- Executes via MetaTrader 5 on an FTMO $100K demo account
- Has been live since April 7, 2026

### The Edge Mechanism

The system's edge is **OB zone precision** — the statistical tendency of price to continue in the impulse direction after revisiting the last opposing candle zone before a structural break. This runs at ~70% mechanically, and the AI adds selectivity.

**Key validated numbers:**
- Batch WR: 62% (129 trades, Oct 2025 - Mar 2026)
- Expectancy: +0.278R per trade
- OB zone adds +17pp over generic pullback (p=0.003)
- Current TP: 1.5R, SL: 1.0R (based on zone geometry)

### The FTMO Constraint

FTMO is a prop firm with strict rules:
- **10% maximum drawdown** from starting equity (hit this = fail)
- **5% daily drawdown limit** (hit this = fail)
- **10% profit target** to pass evaluation
- Once funded, same DD rules apply permanently

**This means the PATH to profit matters, not just the destination.** A strategy with higher expectancy but wilder swings might fail FTMO more often than a lower-expectancy strategy with smoother equity curve.

---

## The Hypothesis We're Testing

### Current GTOS Philosophy: Maximize Expectancy Per Trade

- Enter at OB zone
- Single exit: 100% at TP (1.5R)
- SL at 1.0R below/above entry
- Hold until TP, SL, or 2-hour timeout

This maximizes expected R per trade. But it also means:
- Every open trade is at full risk until it hits TP or SL
- A string of losses compounds at full position size
- No "free trades" — every position can lose 1R

### Alternative Philosophy: Optimize for FTMO Survival (from ex-bank trader interview)

An experienced institutional trader described his approach:
> "I would always look for a free trade... taking maybe 33% or even 50% at the first target and then you can reduce your stop loss slightly and then you can get away with a cheap or free trade and then you just move on to the next trade."

This philosophy:
- Locks in partial profit early (can't be given back)
- Removes risk quickly (move SL to entry = "free trade")
- Lets remainder run for larger wins
- Prioritizes survival over maximum expectancy

**The question:** Does this produce higher P(pass FTMO) even if expectancy per trade is lower?

---

## What Data You Have

### Trade Data Location
`research/academic_pipeline/data/` — look for batch trade results

### Key Fields You Need (per trade)
- **MFE (Maximum Favorable Excursion):** How far price moved in our favor before outcome
- **MAE (Maximum Adverse Excursion):** How far price moved against us before outcome
- **Outcome:** Win (hit TP) / Loss (hit SL) / Timeout
- **R-multiple achieved:** Actual profit/loss in R terms

### If MFE/MAE Not in Processed Data
Check `knowledge_base/trade_index.json` or raw trade logs. You may need to reconstruct from entry price, TP, SL, and actual exit.

### Foundation Analysis Results
`research/academic_pipeline/results/L4_foundation_results_v1.md` contains:
- B36: P(2R | 1R reached) = 53.2%
- B4: Winner MFE distribution (right-skewed, skewness 1.232)
- A1: Winner MAE (median 0.138R, P80 0.354R)

---

## The Test Design

### Step 1: Load Trade Data
Load all 129 batch trades with their MFE/MAE paths (or reconstruct).

### Step 2: Simulate Current Approach
For each trade, compute outcome under current rules:
- TP at 1.5R
- SL at 1.0R
- Result: +1.5R or -1.0R or timeout value

### Step 3: Simulate Patrick's Approach
For each trade, compute outcome under partial close rules:

**Variant A (Conservative):**
- If MFE reaches 0.5R: close 50% at +0.5R, move SL to entry
- Remaining 50%: TP at 2.0R or stopped at entry (0R) or timeout
- Calculate blended R-multiple

**Variant B (Moderate):**
- If MFE reaches 0.75R: close 50% at +0.75R, move SL to entry
- Remaining 50%: TP at 2.0R or stopped at entry or timeout

**Variant C (Aggressive):**
- If MFE reaches 1.0R: close 33% at +1.0R, move SL to entry
- Remaining 67%: TP at 2.5R or stopped at entry or timeout

### Step 4: Compute Per-Trade Metrics
For each variant:
- Mean R per trade
- Median R per trade
- Win rate (any positive R)
- Distribution of outcomes

### Step 5: Monte Carlo Simulation

For EACH strategy (current + 3 variants):

```python
def simulate_ftmo_path(trade_results, n_trades=100, risk_pct=1.0, starting_equity=100000):
    """
    Simulate one FTMO evaluation attempt.
    Returns: (passed, final_equity, max_drawdown, path)
    """
    equity = starting_equity
    peak_equity = starting_equity
    max_dd = 0
    
    for i in range(n_trades):
        # Sample a trade result (with replacement)
        r_multiple = random.choice(trade_results)
        
        # Calculate P&L
        risk_amount = equity * (risk_pct / 100)
        pnl = r_multiple * risk_amount
        equity += pnl
        
        # Track drawdown
        if equity > peak_equity:
            peak_equity = equity
        current_dd = (peak_equity - equity) / starting_equity  # DD from starting equity for FTMO
        max_dd = max(max_dd, current_dd)
        
        # Check FTMO fail conditions
        if current_dd >= 0.10:  # 10% max DD
            return (False, equity, max_dd, "DD_BREACH")
    
    # Check if passed (10% profit)
    profit_pct = (equity - starting_equity) / starting_equity
    passed = profit_pct >= 0.10
    
    return (passed, equity, max_dd, "COMPLETED")

# Run 10,000 simulations per strategy
for strategy in [current, variant_a, variant_b, variant_c]:
    results = [simulate_ftmo_path(strategy.trade_results) for _ in range(10000)]
    pass_rate = sum(r[0] for r in results) / 10000
    avg_max_dd = mean(r[2] for r in results)
    dd_breach_rate = sum(1 for r in results if r[3] == "DD_BREACH") / 10000
```

### Step 6: Statistical Comparison

For each variant vs current:
- P(pass FTMO): Is it significantly higher? (proportion test)
- Mean max drawdown: Is it significantly lower? (t-test)
- DD breach rate: Is it significantly lower?
- Expected terminal equity: Is it comparable?

---

## Decision Criteria

### CONFIRM Patrick's Philosophy (adopt in WF-2):
- P(pass FTMO) increases by >= 5 percentage points AND
- Statistical significance p < 0.05 AND
- Expected terminal equity within 90% of current approach

### REJECT Patrick's Philosophy (keep current):
- P(pass FTMO) decreases or stays same OR
- Expected terminal equity drops by > 20%

### INCONCLUSIVE (need more data):
- Small improvements (< 5pp) without statistical significance

---

## Output Requirements

Create a report at `research/academic_pipeline/results/FTMO_survival_optimization_results_v1.md` with:

1. **Data Summary**
   - How many trades analyzed
   - MFE/MAE distribution summary
   - Any data quality issues

2. **Per-Trade Comparison Table**
   | Strategy | Mean R | Median R | WR | Std Dev |
   
3. **Monte Carlo Results Table**
   | Strategy | P(pass) | Mean Max DD | DD Breach Rate | Mean Terminal Equity |

4. **Statistical Tests**
   - Proportion tests for P(pass) differences
   - Effect sizes

5. **Trade-by-Trade Diff (for best variant)**
   - Which trades improved under new rules?
   - Which trades degraded?
   - What's the pattern?

6. **Recommendation**
   - CONFIRM / REJECT / INCONCLUSIVE
   - Clear reasoning
   - If CONFIRM: implementation notes for WF-2

---

## Critical Reminders

1. **Do NOT modify any src/, prompts/, or config/ files.** This is analysis only.

2. **Do NOT fabricate data.** If MFE/MAE data doesn't exist, say so and propose how to get it.

3. **Show your work.** Every number should trace back to data or calculation.

4. **Think about edge cases:**
   - What if MFE never reaches the partial close threshold?
   - What about timeout trades — how do partials work there?
   - What about trades that gap through levels?

5. **Be honest about limitations.** If the test is inconclusive or data is insufficient, say so.

---

## Files to Read First

1. `CLAUDE.md` — System overview and current state
2. `.context/02_session_handoffs/12_apr12_strategic_advisor_L4_handoff.md` — Latest research status
3. `research/academic_pipeline/results/L4_foundation_results_v1.md` — Existing MFE/MAE analysis
4. `research/kap_outputs/exbank_trader_patrick_transcript_analysis.md` — Source of this hypothesis

---

## Why This Matters

If Patrick's approach produces significantly better FTMO survival rates, it changes our fundamental strategy. We would shift from:
- "Maximize R per trade" → "Maximize P(pass prop firm)"

These are different objective functions. The first optimizes for expected value. The second optimizes for path-dependent survival under drawdown constraints.

This is not a small question. Take it seriously.

---

*Prompt written by Strategic Research Advisor, April 13, 2026*
