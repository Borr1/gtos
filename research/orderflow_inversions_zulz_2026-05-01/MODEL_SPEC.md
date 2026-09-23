# Orderflow Inversions Model — Canonical Reconstruction

**Source:** Reconstructed from Zulz Trades' Whop product descriptions (10 products, all read verbatim) + 30 YouTube/TikTok transcripts.
**No fabrication:** Every claim below is sourced. See `KEY_QUOTES.md` for verbatim evidence with video IDs.
**What's missing:** Hard parameters (exact tick sizes, exact deviation multiplier, exact stop placement) — these are inside his Discord and SierraChart templates, not in any public content. Where I had to infer, I marked it `[INFERRED]`.

---

## 1. The setup name and core idea

He calls it **"Orderflow Inversion"** (sometimes "auto-flow inversion" in transcripts — that's auto-transcribed mangling of "orderflow inversion"). Marketing tagline: *"The simplest and most permanent trading model."*

**Core thesis (from Discord page):**
> "Every concept in this model is grounded in real market data, real auction theory, and real institutional activity. No patterns. No subjectivity. No guessing."

The setup is a **failure-of-aggression reversal** at a high-precision level. Trapped participants get flushed; the opposite-side flow that flushes them is your entry signal.

---

## 2. Where to take the trade — POI selection

### 2.1 Preferred POI: Low Volume Node (LVN) inside an FVG

The single most-repeated technical claim across his content:

> "ICT traders mark a fair value gap, but order flow traders mark a low volume node. If you mark out the fair value gap, it'll most of the times give you a huge zone, while if you mark out the low volume node inside that fair value gap, it'll give you a small zone within that fair value gap, and that's the exact zone where you will see price reacting from."
> — Video `UJ9CS5XCwm8`

> "There is a huge fair value gap right there, but the reaction came from this very specific level right here. Because inside that level, there is a low volume node, and these low volume nodes are the real imbalances in the market."
> — Video `p6hf29NIiBE`

**Implication:** The FVG is the fuzzy zone. The LVN inside the FVG (or at its edge) is the actual price-magnet. He treats the LVN as the operative POI.

### 2.2 Acceptable POIs (ranked by his repetition frequency)

1. **LVN inside an FVG** (primary)
2. **LVN at HTF VWAP standard-deviation level** ("delivery of this overnight low volume node and from the monthly VWAP standard deviation minus")
3. **HTF Volume Profile node** (5m/15m HTF VP overlay)
4. **Resting-liquidity level visible on heatmap** (used more as target than entry POI, but he does take entries off them — "buyers reclaiming that view obligation [VWAP deviation], lot of liquidity backing the double top showing up here in the heat map")

### 2.3 What he does NOT use as POI

- Order Blocks (no mention in any of the 30 transcripts — he is explicitly NOT an SMC-OB trader)
- Breakers (no mention)
- Generic FVG centerline (he explicitly says the FVG itself gives "a huge zone" → low precision)

---

## 3. Entry timing — the VWAP deviation reclaim trigger

### 3.1 The "first VWAP deviation" trigger

The single most-repeated entry-timing trigger:

> "Everything you need to read the session auction for ES, identify high probability levels, and **take Orderflow Inversions once price reclaims the first VWAP deviation**."
> — VP and Heatmap ES product description

> "I waited for buyers to get trapped over the first view of deviation [VWAP deviation] and I took my entry as soon as I saw aggressive buyers pushing price down."
> — Video `5oTghWjjc3I`

> "Trapped buyers at the bottom on the footprint, and I waited for aggressive buyers to show up on the footprint to take my trade."
> — Video `voyssVuS110`

**Mechanism:**
1. Price reaches an LVN that sits AT or NEAR the first VWAP standard deviation of the session.
2. Initial-side participants attempt to defend (e.g., aggressive sellers at a low LVN).
3. They fail / get absorbed at the level.
4. Opposite-side participants step in aggressively.
5. The moment of opposite-side aggression on the footprint = entry.

### 3.2 VWAP construction

From the Full Orderflow product descriptions:
- **Auto ETH/RTH VWAP split**, plotted independently for each session
- Standard deviations plotted separately for each
- Plus higher- and lower-timeframe VWAPs (5m + 15m left-side context charts)

### 3.3 Confirmation stack on the footprint

From the Footprint product descriptions:
- **Vol X Delta footprint** — Volume × Delta colored bars (color tells you who's in control at each price)
- **Per-candle Volume Profile** with POC marked
- **Auto-sized large-volume trade bubbles** (proxy for institutional size)
- **Stacked imbalances marked automatically**
- **Total candle delta + total candle volume** at the bottom
- **Session VWAP overlay**

The trader looks for:
- Trapped-side bubble cluster at the level (large-vol bubbles in losing direction)
- Stacked imbalances flipping direction
- CVD (cumulative delta) divergence vs price

### 3.4 Candle construction — non-time-based

> "Every candle prints after **2000 trades**, not after a fixed amount of minutes."

His footprint uses **tick-count bars (2000 trades per bar on NQ)**, not time-based candles. This is a deliberate noise-reduction choice. The entry trigger is therefore evaluated per "activity unit," not per minute.

---

## 4. Targets

> "Auto ETH/RTH VWAP with Deviations, split with each session's Volume Profile, Delta Profile at each price level, a CVD chart at the bottom, and a Liquidity Heatmap showing actual resting contracts at significant price levels in real time. **These levels become your targets.**"
> — Full ES Orderflow product description

**Targets in priority order:**
1. Next significant resting-liquidity level on the in-chart heatmap
2. Next VWAP deviation
3. HTF VP HVN/POC

**Risk-multiple targets observed in trade recaps:** 1R, 1.4R, 2.4R, 3.5R. He often takes 1R on news days. Mentions a trailing stop being used in one recap (got taken out at 2.4R when target was higher).

---

## 5. Invalidation

He never states an explicit stop rule on public content. From recap clips:

- One trade `IoBSg-rAcR8`: "We go below that view obligation [VWAP deviation] once again, I'm done." → invalidation = price re-breaks the reclaimed VWAP deviation in the wrong direction.
- One trade `nrKgZrQSD-k`: "Trapped buyers at the top low volume node over the first VWAP deviation, then aggressive sellers came in right after. It was a great setup, but it didn't work out." → he calls it a great setup but acknowledges it can fail; no stop rule disclosed.
- He references "moving my stop too aggressively" in one recap (`jw8_WalX2CU`) → he does use stop-trail discretion.

**[INFERRED]** Stop placement is almost certainly: just beyond the LVN extreme (high of the LVN for shorts, low for longs) plus a small buffer. This is the only mechanically consistent placement given his framing of "trapped over the first VWAP deviation."

---

## 6. Setup variants

### 6.1 Bullish Orderflow Inversion (long)

1. Bias: price has pushed down into a session LVN that sits at/near first VWAP deviation below
2. Footprint: aggressive sellers down here are getting absorbed (large red bubbles, no further price drop)
3. Trapped sellers identified
4. Aggressive buyers print on footprint → entry long
5. Stop: below LVN low [INFERRED]
6. Target: next heatmap liquidity / VWAP deviation up

### 6.2 Bearish Orderflow Inversion (short)

Mirror image. He mentions both directions in his trade recaps roughly equally.

### 6.3 Continuation variant (NOT inversion)

He also takes "**continuation setups**" — these are NOT orderflow inversions, they are with-trend pullbacks to the first VWAP deviation. Same footprint confirmation (trapped → aggressive flip), but in the trend direction. From `5oTghWjjc3I`:
> "It was a continuation set up short on ES. As soon as I saw that oil was pumping, I took that continuation short on ES because it was falling behind."

So his system has at least 2 named setups: **Inversion** (reversal) + **Continuation** (with-trend), both off the same footprint trigger.

---

## 7. Cross-instrument context (regime / correlation gate)

He mentions wanting **inverse correlation between CL and ES, and between DXY and ES** as a required confluence:
> "I usually want to see an inverse correlation between crude oil and ES and between the DXY and ES, and I was not getting that when I took these trades, so I risked only half of what I usually risk."
> — Video `uOvTqzZiDFk`

This means he uses cross-instrument flow as a **size filter**, not a hard gate.

---

## 8. Time-of-day / regime gates

- Trades **Asia session (overnight)** — favors CL, GC
- Trades **NY open at 9:30 EST** live on Discord
- Avoids **after 11am** ("This random volume coming after 11am is killing me" — `FzH7Tx3F0Zk`)
- Reduces size on **FOMC, CPI, Trump-tweet days** (multiple recaps reference 1R-only on those days)

So implicit session gating: prefer first 90 min after London/NY open + Asia clean window.

---

## 9. Why he believes it doesn't decay

His "permanence" claim is in the Discord description:
> "Every concept in this model is grounded in real market data, real auction theory, and real institutional activity."

And in `JP3cGtMeh00`:
> "If you understand the concept of alpha decay, you will realize that you need orderflow if you want to stay consistent in the markets."

His logic: orderflow is the underlying market data, not a derivative pattern. Patterns (HH/HL, OBs, etc.) are interpretations. Orderflow IS the auction. Therefore the inputs themselves don't decay — only specific interpretations do.

**Counter-honesty:** This argument is partially right (data doesn't decay) and partially wrong (his specific interpretation can absolutely decay if too many people pile into "trapped at first VWAP dev → reverse"). His packaging is novel; his primitives are not.

---

## 10. Tooling stack (mandatory for replication)

| Component | Tool | Why |
|---|---|---|
| Charting platform | SierraChart | Tick-by-tick volume; not aggregated like TradingView |
| Data feed | CME Group Market Depth | Required for level-2 / heatmap |
| Footprint indicator | "Vol X Delta" (his template) | Volume × Delta colored bars |
| Heatmap | Built into his SC template | Replaces Bookmap ($86/mo saved) |
| VWAP | Auto ETH/RTH split with deviations | Session-aware fair-value reference |
| Volume Profile | Per-session + HTF | Where LVNs are visible |

Anti-stack:
- ❌ TradingView (aggregated volume)
- ❌ Bookmap (redundant once heatmap is in SC)
- ❌ MT4/MT5 footprint plugins (no centralized volume; broker-local data)

---

## 11. What this means for GTOS (translation problems)

Direct lifts that work without futures data:
- **LVN-as-POI principle** — works on any volume profile that uses real volume (broker-local on MT5 is degraded but not zero)
- **VWAP first-deviation reclaim trigger** — pure price; works anywhere
- **Session split (ETH/RTH)** — pure time; works anywhere
- **Trapped → aggressive flip narrative** — captureable as event study with our existing tick-capture daemon

Lifts that need futures or new data:
- **Heatmap of resting liquidity** — requires L2 depth; MT5 brokers don't provide centralized depth → would need GC futures proxy for XAUUSD, NQ for NAS100, ES for US30
- **Vol X Delta footprint** — requires bid/ask trade classification at tick level (Lee-Ready or actual aggressor flag); our tick-capture daemon has bid/ask but not aggressor flag → derivable approximately
- **2000-trade candle construction** — needs trade count, not tick count → workable if tick stream includes trade size

This makes the model a **medium-effort translation candidate**, not plug-and-play. The entry trigger ("VWAP-dev reclaim + trapped + aggressive flip") is implementable in shadow mode against existing GTOS pipeline; the visual heatmap layer is the hard part.
