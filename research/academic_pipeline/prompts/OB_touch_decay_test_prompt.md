# Agent Prompt: OB Touch Decay Analysis

## Your Mission

Test whether Order Blocks show **measurable decay** across successive touches, and whether we can use this decay signal to avoid stale OBs that are likely to fail.

---

## The Context You Need

### What is GTOS?

GTOS trades H1 Order Block retests. An Order Block (OB) is the last opposing candle before a structural break (BOS/CHoCH). When price returns to this zone, there's a ~70% probability of continuation in the impulse direction.

### The Edge Mechanism

The system's edge is **OB zone precision**:
- OB zone = last opposing candle before displacement
- Represents pre-cascade equilibrium
- First touch: institutional orders still resting at that level
- Later touches: orders may be absorbed, zone loses power

**Key validated numbers:**
- OB continuation rate: ~70% mechanically
- OB zone adds +17pp over generic pullback (p=0.003)
- System WR: 62% (AI-filtered)

### The "TACO" Framework (from ex-bank trader)

An institutional trader described pattern decay:
> "Bit like throwing a pebble in a pond — the first ripples the biggest then the subsequent ripples are a lot less."

He called repeated Trump policy reversals "TACO" (Trump Always Chickens Out) and noted:
- First TACO: Huge move
- Second TACO: Smaller move
- Third TACO: Market barely reacts

**The hypothesis:** OBs work the same way. First touch is strongest. Each subsequent touch is weaker as orders get absorbed.

---

## What We Already Suspect

From `test_a_implications_analysis.md`:
> "Mitigation tracking — JUSTIFIED. Whether an OB has been previously visited matters because it indicates whether the institutional orders at that level have already been absorbed. First-touch vs second-touch OBs likely have different continuation rates. Worth investigating with live data."

From `kb_edge_mechanisms_and_risks.md`:
> The zone before displacement represents "fair value" pre-disruption. When price returns, several forces create the reaction: (a) orders resting from participants who wanted to buy/sell at that level before the cascade disrupted them...

If orders are absorbed on touch 1, touch 2 has fewer resting orders, touch 3 even fewer.

---

## The Test Design

### Phase 1: Historical Analysis

**Question:** Do we have touch count data in existing batch trades?

Check these locations:
- `knowledge_base/trade_index.json`
- `research/academic_pipeline/data/` — any processed trade files
- `pipeline_state/` — per-candle state files
- Raw MSO outputs from Component 2

**What you're looking for:**
- OB identification timestamp (when was this OB created?)
- Touch events (each time price entered the OB zone)
- Touch number at trade entry (was this 1st, 2nd, 3rd touch?)

### Phase 2: Reconstruction (if touch data doesn't exist)

If we don't have explicit touch counts, we may be able to reconstruct:

```python
def count_ob_touches(ob_zone, price_data, entry_time):
    """
    Count how many times price entered this OB zone before our entry.
    
    ob_zone: (high, low) of the OB
    price_data: H1 candles from OB creation to entry
    entry_time: when the trade was taken
    
    Returns: touch_number (1 = first touch, 2 = second, etc.)
    """
    touches = 0
    for candle in price_data:
        # Check if candle entered the zone
        if candle.low <= ob_zone.high and candle.high >= ob_zone.low:
            touches += 1
    return touches
```

**Data needed:**
- OB zone boundaries (high/low)
- OB creation time
- H1 price data between OB creation and trade entry
- Trade entry time

### Phase 3: Analysis

**If we can determine touch number for each trade:**

```
Group trades by touch number:
- Touch 1: n=?, WR=?
- Touch 2: n=?, WR=?  
- Touch 3+: n=?, WR=?

Statistical tests:
- Chi-square for WR difference across groups
- Trend test (is WR monotonically decreasing with touch number?)
- Effect size: how many pp does each additional touch cost?
```

**Additional analysis:**
- Does the SIZE of the move decay? (Touch 1 MFE vs Touch 2 MFE)
- Does MAE increase with touch number? (later touches = more adverse movement)
- Is there a "death zone"? (e.g., after 3 touches, WR drops below breakeven)

### Phase 4: Decay Rate Measurement

Beyond just "touch 1 > touch 2", can we measure the RATE of decay?

```python
def measure_touch_decay(ob_id, touches):
    """
    For an OB with multiple touches, measure the move size per touch.
    
    Returns: decay_rate (e.g., 0.7 means each touch produces 70% of previous touch's move)
    """
    move_sizes = []
    for touch in touches:
        # Move size = how far price went after touching OB before reversing
        move_size = calculate_continuation_move(touch)
        move_sizes.append(move_size)
    
    if len(move_sizes) >= 2:
        # Calculate average decay ratio
        ratios = [move_sizes[i+1] / move_sizes[i] for i in range(len(move_sizes)-1)]
        decay_rate = mean(ratios)
        return decay_rate
    return None
```

**If decay_rate < 0.6:** The OB is dying fast — skip subsequent touches
**If decay_rate > 0.8:** The OB is holding well — continue trading it

---

## Decision Criteria

### CONFIRM Touch Decay Effect:
- Touch 1 WR significantly > Touch 2 WR (p < 0.05)
- Effect size >= 10pp difference
- Pattern holds across instruments

**Implementation:** Add touch_number filter to Component 3A evaluation. Skip OBs with touch_number >= 3 (or whatever threshold data suggests).

### REJECT Touch Decay Effect:
- No significant WR difference by touch number OR
- Touch 2 WR is actually higher (absorption = confirmation?)

**Implementation:** None. Continue trading all touches equally.

### INCONCLUSIVE:
- Insufficient data to determine touch number for most trades
- Trend exists but not statistically significant

**Next step:** Add touch_number to shadow logging for live data collection.

---

## Output Requirements

Create a report at `research/academic_pipeline/results/OB_touch_decay_analysis_v1.md` with:

1. **Data Availability Assessment**
   - Can we determine touch number from existing data?
   - If not, what's missing and how hard to reconstruct?

2. **Touch Distribution** (if data available)
   - How many trades were Touch 1, Touch 2, Touch 3+?
   - Is our sample biased toward first touches?

3. **WR by Touch Number**
   | Touch # | n | Wins | WR | 95% CI |

4. **Move Size by Touch Number**
   | Touch # | Mean MFE | Median MFE | Mean MAE |

5. **Decay Rate Analysis**
   - For OBs with multiple touches, what's the average decay rate?
   - Distribution of decay rates

6. **Statistical Tests**
   - Chi-square for WR independence
   - Trend test for monotonic decay
   - Effect sizes

7. **Recommendation**
   - CONFIRM / REJECT / INCONCLUSIVE
   - If CONFIRM: proposed filter rule (e.g., "skip touch >= 3")
   - Expected impact on frequency and WR

---

## Critical Reminders

1. **Do NOT modify any src/, prompts/, or config/ files.** Analysis only.

2. **If touch data doesn't exist, that's a valid finding.** Document what would be needed to collect it.

3. **Be careful about sample size per touch bucket.** If Touch 3+ has n=5, we can't draw conclusions.

4. **Consider: maybe Touch 2 is actually BETTER.** The first touch "confirms" the zone works, second touch is the real entry. Test this counter-hypothesis.

5. **Check for instrument differences.** Does touch decay happen on gold but not on US30?

---

## Files to Read First

1. `CLAUDE.md` — System overview
2. `.context/03_analysis/test_a_implications_analysis.md` — Why we think touch number matters
3. `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md` — The absorption mechanism
4. `research/kap_outputs/exbank_trader_patrick_transcript_analysis.md` — TACO framework origin
5. Look in `src/components/market_state.py` — how OBs are currently tracked

---

## Why This Matters

If touch decay is real and measurable:
- We can AVOID trades with low probability (stale OBs)
- This directly improves WR without changing anything else
- It's a $0 filter — just skip bad setups

If touch decay is NOT real:
- We stop worrying about it
- We can trade any touch equally

Either answer is valuable. Find out which is true.

---

*Prompt written by Strategic Research Advisor, April 13, 2026*
