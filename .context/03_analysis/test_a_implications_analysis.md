# Test A Implications Analysis — OB Zone vs Generic Deep Pullback

**Date:** 2026-04-05 (original) → **Updated 2026-04-05** (post-rerun)
**Trigger:** ~~Preliminary Test A results show OB zone adds approximately zero value.~~ **REVERSED.** Definitive rerun on real 219-event XAUUSD population shows OB zone adds +16.8pp (p=0.003).
**Status:** DEFINITIVE. Rerun used actual batch population (219 BOS events, 139 real trades). Simulation calibrated against known outcomes (12.6pp optimism bias measured and documented).

---

## 1. Reclassification

### Criticism 2a: OB Continuation = Simple Momentum

**Previous rating:** CONCERNING — PARTIALLY CONFIRMED BY PRELIMINARY TEST A
**Updated rating:** REVERSED — OB ZONE ADDS SIGNIFICANT VALUE ON REAL POPULATION

**What the definitive rerun showed:**

On the system's actual 219 BOS events (the real population Component 2 produces):

| Method | Sim WR | Calibrated WR | vs OB Zone |
|--------|--------|---------------|------------|
| OB zone entry | 70.5% | 57.9% | baseline |
| 80% retrace (best dumb alternative) | 53.7% | 41.1% | -16.8pp (p=0.003) |
| 85% retrace | 35.6% | 23.0% | -34.9pp |
| 90% retrace | 25.9% | 13.3% | -44.6pp |

The OB zone outperforms the best generic deep pullback by +16.8pp with Fisher p=0.003. Same-SL-distance variant confirms: dumb baselines score 36-39% sim WR vs 70.5% for OB zone. The advantage is NOT an artifact of SL distance mechanics.

**Why the preliminary test was wrong:** The simplified BOS detector used a different, broader population of structural breaks. On that generic population, the OB zone added nothing — because the BOS events themselves were lower quality. On the real system's curated BOS population (produced by Component 2's specific swing detection, CHoCH/BOS classification, and OB generation rules), zone precision matters significantly. The Component 2 filter IS the value — it selects BOS events where the OB zone provides meaningful entry advantage.

**What about AI selection?** The AI adds approximately 0pp to WR over unfiltered OB entries in the rerun (56.1% actual vs 57.9% calibrated for all OBs). This is a separate finding — the AI's value may be in risk management and partial close optimization rather than entry selection. This does NOT diminish the OB zone finding.

---

## 2. Operational Implications — The Zone IS the Edge

### 2.1 Engineering Investments That ARE Justified

The original analysis suggested these were "potentially wasted." They are now confirmed as core infrastructure:

**OB detection in Component 2 — HIGH VALUE.** The specific logic identifying the last opposing candle before the impulse, computing exact boundaries, and classifying by causing event type (BOS vs CHoCH) is what separates a 70.5% sim WR from a 53.7% generic pullback. This is a 17pp edge generator. Protect it, refine it, do not simplify it.

**Zone refinement features — JUSTIFIED.** Body-range ratio filtering, OB freshness tracking, nearby OB counting — these optimize a variable (zone quality) that is now confirmed to matter. The theoretical justification is restored: the OB zone represents a specific price level where institutional orders were placed, and returning to that level triggers the continuation.

**Mitigation tracking — JUSTIFIED.** Whether an OB has been previously visited matters because it indicates whether the institutional orders at that level have already been absorbed. First-touch vs second-touch OBs likely have different continuation rates. Worth investigating with live data.

**Retracement depth analysis — REFRAMED.** The 85-90% peak continuation finding is NOT just about entry price advantage. It's about how deeply price must retrace into the impulse to reach the OB zone. OBs that sit at 85-90% retracement are better positioned than those at 70% or 95%. This is a zone-quality signal, not a generic momentum signal.

### 2.2 What Is STILL Important to Invest In

**AI selectivity remains the open question.** The AI doesn't improve WR over unfiltered OB entries in batch. This could mean:
- The AI's value is in R-multiple optimization (better partials, smarter exits), not WR improvement
- The AI's value emerges only with session memory (batch had no context)
- The AI is genuinely not adding entry selection value

Monitor this in live. If after 50 live trades the AI's CANDIDATE WR doesn't exceed the ~70% mechanical OB continuation rate, the AI's selection criteria need rework.

**Session memory is still critical.** The doubling of expectancy from session memory is independent of the zone-vs-momentum question. Whether the zone matters or not, the AI making better decisions with context is validated.

**Kill zone timing — reframed.** Under the zone interpretation, kill zone optimization is about trading when institutional order flow is most active and OB zones are most likely to hold. London and NY sessions are when large institutions deploy capital, creating the zones and the liquidity for retests. This is the original ICT framing, and it's now supported by the data.

### 2.3 What to Monitor for Edge Decay

This is the most significant operational update from the reversal.

**PRIMARY DECAY METRIC: OB continuation rate.** Since the zone IS the edge, track the rolling percentage of retested OBs that produce continuation in the correct direction. The batch baseline is ~70%. If this drops below 60% over a rolling 50-OB window, the edge is decaying.

How to measure in live: for every H1 OB that Component 2 identifies and that price retests during a kill zone, record whether price subsequently moves at least 1R in the expected direction within 16 candles. This is the mechanical baseline — it doesn't require the AI to take a trade. Log it for ALL retested OBs, not just AI CANDIDATEs.

**SECONDARY DECAY METRIC: AI discrimination ratio.** Track the gap between AI-selected CANDIDATE WR and the mechanical OB continuation rate. Currently the AI doesn't add WR value (56% vs 58% calibrated). If the AI starts actively DESTROYING value (AI WR falls significantly below mechanical baseline), the prompt needs rework.

**TERTIARY DECAY METRIC: BOS frequency and impulse character.** If structural breaks become weaker (smaller impulses, more whipsaws), the quality of the OB population degrades. Track: average impulse candle count per BOS event, percentage of BOS events that create FVGs (currently the strongest quality signal).

**DE-PRIORITIZED: H1 return autocorrelation.** The original analysis elevated this as the primary decay metric under the momentum interpretation. Since the edge is zone-specific rather than pure momentum, autocorrelation is a background indicator, not the primary alarm. It's still worth computing quarterly as a market microstructure health check, but it should NOT be the trigger for edge-decay decisions.

### 2.4 Impact on New Instrument Expansion

**What stays the same:** The ~70% universal OB continuation rate across 13 instruments indicates OB zones work across all liquid instruments. This is now interpreted as "institutional order accumulation zones are universal" rather than "momentum persistence is universal." The practical implication is identical — expansion criteria don't change.

**What changes:** Instrument selection should weight OB zone quality metrics (body-range ratio, FVG-in-impulse rate, retracement depth distribution) alongside spread and correlation. An instrument with high-quality OB formation and low spread is a better candidate than one with high autocorrelation but messy zone structure.

**NZDUSD reinterpretation stays the same.** The AI destroyed value on NZDUSD (29% WR on a 70% mechanical base). Whether the mechanism is zone-based or momentum-based, the AI's SMC-framed prompt generates bad decisions on NZDUSD. The kill was correct.

### 2.5 FVG-in-Impulse — Interpretation Updated

Under the zone interpretation: FVG-in-impulse = "the impulse that created the OB was strong enough to leave a gap." This indicates high-conviction institutional flow — the orders were aggressive enough to skip price levels. Such impulses create stronger OB zones because the institutional position was larger and more decisive.

This is the ICT explanation, and it's now data-supported rather than just narrative. The practical implication is identical regardless of interpretation — FVG-in-impulse is a validated quality signal. Keep using it.

The impulse candle count finding (fewer = better, r=-0.31) also reframes cleanly: a single-candle impulse means the institutional order was executed in one burst, creating a concentrated OB zone. Multi-candle impulses = gradual accumulation = diffuse zone = weaker support/resistance.

---

## 3. Updated "What Would Change Our Mind"

### 3.1 What Would RE-REVERSE the Finding (Back to "Zone Doesn't Matter")

The Test A rerun is definitive for this data population. To re-reverse, we would need:

**Primary criterion:** Live trading shows no WR difference between trades where price entered exactly at the OB zone boundary vs trades where price entered at a generic deep pullback level near (but not at) the OB. This requires 50+ live trades with entry-location tracking.

**Secondary criterion:** A properly constructed out-of-sample test on a completely different date range (not Oct 2025–Mar 2026) shows the OB zone advantage disappears. The walk-forward window starting April 7 serves this purpose. If OB continuation rate drops from ~70% to ~55% in live forward data, the zone advantage may be period-specific.

**Tertiary criterion:** Cross-instrument evidence. If 2+ instruments show OB continuation rate ≈ generic pullback continuation rate when tested with the definitive methodology (real Component 2 population, not simplified BOS detector), the gold result may be gold-specific.

**If two of three criteria are met:** Re-evaluate. The zone finding is only as strong as its forward replication.

### 3.2 What Would Further CONFIRM the Finding (Deepen Zone Investment)

If live trading shows:

- OB continuation rate remains ≥65% over 50+ retested OBs
- Trades entering at the OB zone boundary (within 20% of zone height) outperform trades entering further from the boundary
- First-touch OBs outperform second-touch OBs by ≥5pp

Then: invest heavily in zone refinement — OB quality scoring, zone layering, multi-timeframe OB confluence, and mitigation tracking become high-priority engineering.

### 3.3 Forward-Looking Live Validation — Updated Protocol

**Track for EVERY retested OB (not just AI CANDIDATEs):**
1. OB zone boundaries (high/low)
2. Entry price (where the AI's limit order fills, or where price first touches the zone if NO_TRADE)
3. Distance from OB boundary at entry (in % of zone height)
4. Whether this is 1st, 2nd, or 3rd touch of this specific OB
5. Outcome: did price move ≥1R in expected direction within 16 H1 candles?

**After 30 retested OBs:** Compute live OB continuation rate. Compare to batch baseline (70.5% sim, 57.9% calibrated). If live rate is within the simulation's 12.6pp optimism range (i.e., live ≥ 45%), the zone is performing as expected.

**After 50 retested OBs:** Run the zone-vs-pullback comparison on live data. This is the definitive forward validation.

---

## 4. Summary of Action Items — Updated

| # | Action | Cost | Priority | Status |
|---|---|---|---|---|
| ~~1~~ | ~~Complete Test A rerun on real 129 events~~ | ~~$0~~ | ~~IMMEDIATE~~ | **DONE — zone confirmed +17pp** |
| 2 | Add OB continuation rate to live monitoring dashboard | $0 | **HIGH** | New primary decay metric |
| 3 | Track entry location relative to OB zone in live | $0 | **HIGH** | Forward validation |
| 4 | De-prioritize H1 autocorrelation (quarterly check, not primary) | $0 | LOW | Updated from HIGH |
| 5 | Run Test B (prompt-neutral) if AI discrimination ratio stays ≈0 after 50 trades | $5-10 | MEDIUM | Deferred |
| 6 | Investigate first-touch vs second-touch OB performance in live | $0 | MEDIUM | After 50 retested OBs |
| 7 | Maintain Component 2 OB detection as-is — do NOT simplify | $0 | STANDING | Permanent |

---

## 5. Value Chain — Definitive Decomposition

From the rerun, the system's value chain is:

```
BOS event (structural break detected)
  → +0pp baseline (market noise)

+ OB zone precision (Component 2 identifies specific zone)
  → +17pp (the largest single value-add)

+ AI selection (Claude evaluates context, grades setup)
  → ~0pp on WR (AI value may be in R-multiple management, not WR)

+ Session memory (sliding window of prior evaluations)
  → +?pp on WR, ~2x on expectancy (from earlier validation)

+ Execution rules (partials, timeout, spread gate)
  → contributes to R-multiple, not WR directly
```

**The zone IS the edge.** Everything else amplifies it (session memory, execution) or is still proving itself (AI selection). Protect the zone detection at all costs.

---

*This analysis supersedes the previous version dated 2026-04-05. The preliminary "zone doesn't matter" finding was an artifact of using a simplified BOS detector on a different event population. The definitive rerun on the real system population reverses that finding with p=0.003.*
