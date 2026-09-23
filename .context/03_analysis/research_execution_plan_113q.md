# Research Execution Plan — 113 Remaining Questions
## GTOS Academic Pipeline: Full Roadmap
## Date: April 11, 2026
## Basis: Phase 0 Taxonomy (137 total, 19 answered, 5 lit-searched-only, 113 untouched)

---

## ORGANIZING PRINCIPLE

Questions are grouped into 5 waves by **impact type**, not by component number. The logic:

- **Wave 1 — Multipliers:** Improvements that compound across EVERY trade (entry, features, AI). Even small gains here multiply across all instruments and any future edges.
- **Wave 2 — Existing Edge Optimization:** Make the OB retest edge sharper, more frequent, or more profitable.
- **Wave 3 — Edge Discovery:** Find entirely new setups, mechanisms, and anomalies.
- **Wave 4 — Risk & Portfolio:** Protect capital, optimize allocation, manage decay.
- **Wave 5 — Strategic / Informational:** Important for long-term understanding but not immediately deployable.

Within each wave, questions are ranked by expected value = (probability of actionable finding) × (impact if found).

---

## WAVE 1 — MULTIPLIERS (19 questions)
**Impact: Affects every trade. Deploy immediately if positive.**
**Expected timeline: 2-3 literature search sessions + testing**

### 1A: Entry Engineering (Component 4) — 4 questions

These determine HOW you enter every trade. A 0.1R improvement here is worth more than finding a new edge that produces 5 trades/month.

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-4.1 | Confirmation vs anticipation entry | Current: enter at signal. Could gain 3-5pp WR by optimizing entry point within the zone. | Literature likely shows confirmation adds WR but reduces frequency. Quantify the tradeoff. |
| Q-4.2 | Market vs limit order cost | Current: market orders. Limit orders save spread but risk not filling. At $0.50 spread and +0.2R avg, spread is ~5% of the edge. | Expect limit orders save 0.05-0.15R per trade on gold. Depends on fill rate. |
| Q-4.3 | Time-of-candle execution | Current: enter at candle close/signal. Is mid-candle or next-open better? | Probably small effect (<0.05R) but free to implement. |
| Q-4.4 | Retracement depth vs outcome | Does entering deeper in the zone (50% vs edge) improve RR? | Osler mechanism predicts deeper entry = closer to stop cluster = better. Testable on batch data. |

### 1B: Feature Engineering (Component 1) — 7 questions

These determine WHAT the AI sees. Garbage in, garbage out. Missing features = blind spots. Noise features = wasted context.

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-1.1 | Mutual information: features → returns | Which current features actually carry signal? Which are noise? | Expect 2-3 features are redundant. MI analysis could identify which to drop and what's missing. |
| Q-1.2 | Tick volume information content | Is tick volume signal or noise on CFD? | Literature is mixed. Likely weak signal at best on retail CFD. |
| Q-1.3 | Spread dynamics as predictive signal | Does spread widening predict direction or volatility? | Probably yes for volatility (informed trading), unlikely for direction. |
| Q-1.4 | Multi-timeframe combination methods | Is align score (majority vote) optimal? Bayesian or weighted better? | Expect weighted combination outperforms simple majority by 2-5pp. High-value finding. |
| Q-1.5 | Optimal feature count for ~300 data points | Are we overfitting with too many features? | Statistical learning theory says n/p > 10 minimum. With 300 trades, max ~30 features. Verify we're within bounds. |
| Q-1.6 | Gold vs FX autocorrelation differences | Does gold need different feature engineering? | Diagnostic already showed gold has unique properties (ξ=0.35 vs 0.16). Features should probably differ too. |
| Q-1.7 | Order flow from OHLCV (VPIN, tick rule) | Can we approximate institutional flow without Level 2? | If bulk volume classification works on gold, this is a genuinely new feature class. High potential. |

### 1C: AI Evaluation Optimization (Component 3) — 7 questions

The AI is the decision engine. Improving it improves everything.

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-3.1 | Optimal signal combination method | Is the AI using signals optimally, or would Bayesian combination beat it? | Literature will show whether structured classifiers beat LLM reasoning on structured inputs. Existential question. |
| Q-3.2 | Narrative fitting bias | Does SMC terminology help or hurt the AI? | If "order block" is just "pullback to prior candle," the terminology may be introducing bias. Testable. |
| Q-3.3 | Session memory as Bayesian updating | How does session memory actually help? | Formal Bayesian model would quantify the information gain per additional eval. Could optimize session length. |
| Q-3.4 | Confidence calibration | When the AI says "high confidence," is it actually more accurate? | Calibration curves from batch data will answer this. If poorly calibrated, recalibrate. |
| Q-3.5 | Sequential evaluation accuracy/bias | Does performance degrade through a session? Anchoring? Recency? | If later evals in a session are worse, there's an optimal session length. |
| Q-3.6 | Ensemble / multiple runs | Does running the AI 3x and voting improve WR? | Probably +2-4pp WR at 3× API cost. Worth testing. |
| Q-3.7 | LLM vs logistic regression on same features | Does the AI actually beat a simple statistical model? | If logistic regression on the 7 displacement features matches the LLM, the LLM is overpaying for intelligence. Critical sanity check. |

### 1D: Model Risk (Component 9) — 1 question from Priority B

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-9.1 | LLM performance on financial tasks | Is Sonnet actually good at this? What does the literature say? | Need to know if Sonnet's financial reasoning is validated or if we're cargo-culting. |

---

## WAVE 2 — EXISTING EDGE OPTIMIZATION (26 questions)
**Impact: Makes the OB retest edge more profitable or more frequent.**
**Expected timeline: 3-4 literature search sessions + testing**

### 2A: Pre-Screen / Frequency (Component 0) — 4 remaining questions

The system rejects 51% of days and 93% of candles. If we can safely trade more, frequency increases without diluting edge.

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-0.1 | Daily candle properties predict trending? | Could replace subjective "unclear" with quantitative filter. More days = more trades. | Conditional probabilities exist in the literature. Whether they transfer to gold intraday is the question. |
| Q-0.3 | Regime detection (HMM, change-point) | Replace D1 pre-screen with statistical regime detector? | HMM on daily gold is well-studied. Detection lag is the practical constraint. |
| Q-0.6 | GVZ / implied vol predicts intraday? | Free data source. If GVZ > X predicts trending day, easy filter. | Options-implied vol ratio (IV/RV) is documented as predictive in equities. Gold-specific data sparse. |
| Q-0.7 | Calendar effects beyond DOW | FOMC, OPEX, COMEX delivery, turn-of-month. | FOMC effect on gold is well-documented. Others less so. Low-hanging fruit if they exist. |

### 2B: Structure Detection (Component 2) — 8 remaining questions

Improve how the system identifies zones, levels, and structure.

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-2.1 | Optimal swing point detection | Different algorithms produce different structure. Is ours optimal? | Bry-Boschan and directional change algorithms may outperform fixed-lookback. |
| Q-2.3 | Support/resistance mechanisms | Osler covered stops. What about round numbers, PDH/PDL? | Round number clustering is well-documented. Adds a confirming signal to zone identification. |
| Q-2.4 | FVG gap fill rates | Do gaps fill above chance? FVG is a current quality signal. | Equity gap-fill literature is extensive. FX/gold-specific much less so. |
| Q-2.5 | Order book / liquidity pool dynamics | Where do liquidity pools form? Predictable? | Bouchaud et al. have models. Not directly testable without Level 2, but structural insights transfer. |
| Q-2.6 | Displacement magnitude vs continuation | Is bigger impulse = higher continuation? Threshold or continuous? | Directly testable on batch data. If threshold exists, it's a new quality filter. |
| Q-2.7 | Premium/discount zone evidence | Does buying in lower half of range actually work? | Mean reversion within ranges is documented. Whether it adds to OB retest specifically is the question. |
| Q-2.8 | Fractal structural breaks | Better breakout detection than fixed-lookback? | MFDFA could identify structural breaks with less lag. High implementation cost. |
| Q-2.9 | Liquidity sweep reversal evidence | Does the sweep-and-reverse pattern have academic backing? | This IS the GTOS entry mechanism. Academic confirmation would strengthen conviction. |

### 2C: Stop Loss Refinement (Component 5) — 4 remaining questions

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-5.2 | MAE distribution in gold | What does the adverse excursion distribution actually look like? | Characterize MAE → optimize SL buffer. If MAE is Pareto, current SL is theoretically justified. |
| Q-5.3 | SL placement vs stop clustering | Does placing SL where others have stops increase stop-hunt risk? | Osler data would answer this. If yes, buffer should be wider at round numbers. |
| Q-5.4 | ATR vs quantile-based SL | Is there a better method than ATR? | Quantile-based may reduce "stopped out on winners" rate. GARCH-EVT analysis showed ATR already works, but edge cases may differ. |
| Q-5.5 | SL/TP ratio and Kelly interaction | Formal framework for SL/TP/sizing as unified optimization. | Connects Q-7.1 Kelly results to SL/TP choices. Could reveal suboptimality in current ratio. |

### 2D: Exit Optimization (Component 6) — 5 remaining questions

Exit > entry per 6+ podcast sources. We answered the trailing stop question but 5 exit questions remain.

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-6.2 | Optimal partial close strategy | Is 50/25/25 optimal? Literature-searched but untested. | Almgren-Chriss framework would give the math. Could reveal 60/20/20 or 40/30/30 is better. |
| Q-6.5 | Speed to MFE predicts TP probability? | Fast moves to 1R might predict higher probability of 2R. | If true, this is a mid-trade management signal. Could adapt trailing stop based on arrival speed. |
| Q-6.6 | Session-close strategy / overnight risk | Hold through close or exit? Overnight risk premium in gold? | Gold has asymmetric overnight risk (negative skew). May justify tighter session-close rules. |
| Q-6.7 | Institutional exit principles | TWAP/VWAP/IS for exit optimization? | Probably not directly applicable at retail scale, but principles may inform trailing stop design. |
| Q-6.8 | Dynamic TP based on realized vol | Should TP expand in high-vol, contract in low-vol? | GARCH regime analysis showed high-vol entries have BETTER outcomes. TP expansion during high vol may be justified. |

### 2E: Remaining Component 8, 9 questions

| ID | Question | Why It Matters | Expected Finding |
|----|----------|---------------|-----------------|
| Q-8.2 | Alpha decay half-life | How fast does the OB edge decay? | If half-life is 3-5 years (per SWOT), system is safe. If <2 years, urgency increases. |
| Q-8.3 | Crowding measurement | Can we detect when SMC/ICT is becoming too crowded? | Social media volume, broker data, or OB continuation rate itself may serve as crowding proxies. |
| Q-8.4 | Edge lifetime estimation | Academic frameworks for estimating how long an edge survives. | Financial ecology / adaptive markets hypothesis literature. Sets expectations. |
| Q-9.2 | Black-box model drift detection | How to detect Sonnet degradation without weight access? | Output distribution monitoring, consistency checks across runs. |
| Q-9.3 | Prompt framing effects | Does causal vs statistical language in the prompt change outcomes? | Directly testable via A/B batch test. Could improve or degrade WR by unknown amount. |
| Q-9.4 | LLM ensemble methods | Temperature variation, multiple runs, voting? | Probably +2-4pp WR at 3× cost. Optimal ensemble size is the question. |

---

## WAVE 3 — EDGE DISCOVERY (42 questions)
**Impact: Find entirely new tradeable setups. Could increase frequency by 50-200%.**
**Expected timeline: 5-8 literature search sessions + extensive testing**

This is the biggest wave and the highest-variance one. Most of these will be dead ends. But the ones that survive could transform the system from single-edge to multi-edge.

### 3A: New Zone Types (Component 13) — 8 remaining questions

| ID | Question | Expected Value |
|----|----------|---------------|
| Q-13.1 | Survey of intraday strategies with OOS evidence | HIGH — widest net. Could surface entirely unexpected edges. Literature-searched but papers not deep-read. |
| Q-13.4 | Opening range breakout on gold/FX | MEDIUM — well-documented on equities, unknown on gold. Easy to test. |
| Q-13.5 | Cross-asset signals (DXY, yields, equities) for gold direction | MEDIUM — if DXY leads gold by 15-30 min, it's a free directional filter. |
| Q-13.6 | Liquidity void / price vacuum patterns | MEDIUM — FVG is a version of this. Academic formalization may improve detection. |
| Q-13.7 | Volatility breakout strategies | LOW — Bollinger/Keltner on gold. Probably dead after costs. Compression→expansion already killed. |
| Q-13.8 | Time-of-day anomalies beyond KZ | LOW — extended KZ investigation already found nothing at n≥10. |
| Q-13.9 | Institutional rebalancing patterns | MEDIUM — ETF creation/redemption, COMEX delivery. Different mechanism from OB. |
| Q-13.10 | Zone types beyond S/R (volume nodes, gamma) | HIGH — gamma exposure levels are a completely different paradigm. If detectable from public data, major new edge class. |

### 3B: Non-Zone Mechanisms (Component 14) — 11 remaining questions

| ID | Question | Expected Value |
|----|----------|---------------|
| Q-14.2 | Institutional algo footprints in OHLCV | HIGH — if iceberg/TWAP detection works from candles, it's a new signal. |
| Q-14.4 | Momentum ignition / cascade acceleration | MEDIUM — different from OB retest (riding the cascade, not fading it). |
| Q-14.6 | Gamma exposure / delta hedging flows | HIGH — entirely different mechanism. If GEX is estimable from public options data, this is a new edge class independent of OB. |
| Q-14.8 | Trade flow imbalance from OHLCV | HIGH — VPIN/bulk volume classification. If it works on gold CFD data, it's a genuine new feature. |
| Q-14.9 | Market maker inventory reversion | MEDIUM — inventory models predict mean reversion. Different mechanism from stop-cascade. |
| Q-14.10 | Day×time interaction effects | LOW — calendar effects already mostly dead. But interactions might survive. |
| Q-14.11 | Structural compression breakout prediction | LOW — compression→expansion already eliminated for ATR-based measure. Different structural definition might work. |
| Q-14.12 | Central bank reserve management patterns | LOW — very long timescale, unlikely to produce H1 signal. |
| Q-14.13 | Information-theoretic feature discovery (MI) | HIGH — model-free edge detection. Compute MI between everything and future returns. Whatever has MI > 0 is a candidate. This is the most systematic approach to finding new edges. |
| Q-14.14 | Microstructure noise as information | MEDIUM — bid-ask bounce patterns on CFD. Niche but potentially overlooked. |
| Q-14.15 | Herd behavior / contrarian signals | MEDIUM — if broker sentiment data is accessible, retail positioning extremes may predict reversals. |

### 3C: Mathematical / Statistical Anomalies (Component 15) — 7 remaining questions

| ID | Question | Expected Value |
|----|----------|---------------|
| Q-15.3 | Multifractal models (MMAR) | MEDIUM — multifractal spectrum may reveal time-varying predictability windows. |
| Q-15.4 | Wavelet decomposition | MEDIUM — separate signal from noise at different timescales. Could improve feature engineering. |
| Q-15.5 | Recurrence quantification analysis | LOW — exotic. Could detect regime changes but BOCPD may already do this better. |
| Q-15.6 | Copula tail dependence (gold vs other assets) | MEDIUM — non-linear dependencies invisible to correlation. Could improve cross-asset signals. |
| Q-15.8 | Spectral coherence / frequency-domain lead-lag | MEDIUM — might find lead-lag relationships at specific frequencies that time-domain analysis misses. |
| Q-15.10 | Network science / gold centrality | LOW — interesting but hard to make actionable at H1 timescale. |
| Q-15.11 | Topological data analysis (TDA) | LOW — cutting-edge but very high implementation cost for uncertain payoff. |

### 3D: Adversarial / Game-Theoretic (Component 16) — 6 questions

| ID | Question | Expected Value |
|----|----------|---------------|
| Q-16.1 | Predatory trading / forced flow | HIGH — Brunnermeier-Pedersen framework. If we can detect forced liquidation, it's a new entry signal. |
| Q-16.2 | Algo pattern detection | MEDIUM — if common algo patterns are detectable, can front-run or fade. |
| Q-16.3 | Market design exploitable features | MEDIUM — CFD/FX structure may have edges invisible to equity-focused literature. |
| Q-16.4 | Retail herding contrarian | MEDIUM — IG client sentiment data is public. If positioning extremes predict reversals, easy to implement. |
| Q-16.5 | Informed vs uninformed flow detection | HIGH — PIN/VPIN. If detectable from OHLCV, conditions entry on flow type. |
| Q-16.6 | Game theory for crowded strategies | MEDIUM — if SMC/ICT is crowded, what's the game-theoretically optimal response? Defensive question. |

---

## WAVE 4 — RISK & PORTFOLIO (14 questions)
**Impact: Protect capital, optimize allocation.**
**Expected timeline: 2 literature search sessions + testing**

### 4A: Position Sizing / Risk (Component 7) — 5 remaining questions

| ID | Question | Why It Matters |
|----|----------|---------------|
| Q-7.2 | Optimal drawdown response | Is the graduated reduction spec (3%→0.5%, 4%→0.25%) optimal? |
| Q-7.3 | Max drawdown distribution (EVT) | Is the H29 threshold (8% DD) optimal? |
| Q-7.4 | Correlated asset allocation | USDJPY+GBPJPY correlation reducer — is binary correct or should it be graded? |
| Q-7.5 | Risk of ruin with fat tails | Exact probability of ruin at 2% risk with ξ=0.35. |
| Q-7.6 | FTMO-specific optimal strategy | Formal optimization of "maximize P(pass) given constraints." |

### 4B: Cross-Instrument / Portfolio (Component 11) — 4 questions

| ID | Question | Why It Matters |
|----|----------|---------------|
| Q-11.1 | Optimal allocation with heterogeneous edges | Should gold get more risk than GBPJPY given higher batch WR? |
| Q-11.2 | Cross-currency signals | Does broad JPY weakness predict USDJPY or GBPJPY direction? |
| Q-11.3 | Dynamic instrument selection | Trade only the "hottest" instrument? |
| Q-11.4 | Intraday correlation stability | If correlations break during stress, concurrent positions are more dangerous than modeled. |

### 4C: Macro Overlay (Component 10) — 4 questions

| ID | Question | Why It Matters |
|----|----------|---------------|
| Q-10.1 | DXY-gold lead-lag intraday | If DXY leads by 15-30 min, it's a free directional input. |
| Q-10.2 | Macro announcements and gold | Beyond the 13:00 news skip — should FOMC/NFP days be traded differently? |
| Q-10.3 | Gold safe-haven intraday effect | Equity selloff → gold rally within same session? |
| Q-10.4 | Real rates and gold | TIPS yields as directional input? |

### 4D: Remaining Component 8 question

| ID | Question | Why It Matters |
|----|----------|---------------|
| (Already counted in Wave 2E) | | |

---

## WAVE 5 — STRATEGIC / INFORMATIONAL (12 questions)
**Impact: Long-term understanding, not immediately deployable.**
**Expected timeline: 1-2 literature search sessions**

### 5A: Psychological / Operational (Component 3) — 3 questions

| ID | Question | Why It Matters |
|----|----------|---------------|
| Q-12.1 | Human oversight value | Does your monitoring help or hurt? |
| Q-12.2 | Optimal monitoring frequency | How often should you check? |
| Q-12.3 | Disposition effect with AI oversight | Do you hold losers longer because the AI said CANDIDATE? |

### 5B: Remaining AI Risk (Component 9) — 3 questions (already in Wave 2E)

### 5C: Remaining miscellaneous — counted above

---

## EXECUTION PLAN

### Phase 1: Literature Search (the bottleneck)

Each search session covers 10-15 questions. Target: 15-25 papers per question (quality filtered). Use Opus for search depth.

| Session | Wave | Questions | Est. Papers | Priority |
|---------|------|-----------|-------------|----------|
| L1 | 1A+1B | Q-4.1 to Q-4.4, Q-1.1 to Q-1.7 | 80-120 | 🔴 IMMEDIATE |
| L2 | 1C+1D | Q-3.1 to Q-3.7, Q-9.1 | 60-90 | 🔴 IMMEDIATE |
| L3 | 2A+2B | Q-0.1, Q-0.3, Q-0.6, Q-0.7, Q-2.1, Q-2.3 to Q-2.9 | 80-120 | 🟡 THIS WEEK |
| L4 | 2C+2D+2E | Q-5.2 to Q-5.5, Q-6.2, Q-6.5 to Q-6.8, Q-8.2 to Q-8.4, Q-9.2 to Q-9.4 | 100-150 | 🟡 THIS WEEK |
| L5 | 3A | Q-13.1, Q-13.4 to Q-13.10 | 60-90 | 🟢 THIS MONTH |
| L6 | 3B | Q-14.2, Q-14.4, Q-14.6, Q-14.8 to Q-14.15 | 80-120 | 🟢 THIS MONTH |
| L7 | 3C+3D | Q-15.3 to Q-15.6, Q-15.8, Q-15.10, Q-15.11, Q-16.1 to Q-16.6 | 80-120 | 🟢 THIS MONTH |
| L8 | 4A+4B+4C | Q-7.2 to Q-7.6, Q-11.1 to Q-11.4, Q-10.1 to Q-10.4 | 80-120 | 🟡 THIS WEEK |
| L9 | 5 | Q-12.1 to Q-12.3 + any gaps | 20-30 | ⚪ WHEN TIME ALLOWS |

**Total: 9 literature search sessions, ~650-960 papers to evaluate**

### Phase 2: Deep Reads

For every search session, the top 10-15 papers get deep-read treatment:
- Exact equations extracted
- Assumptions listed
- Test specification written
- Codebase cross-reference (is this already implemented?)

Estimated: 90-135 papers deep-read across all sessions.

### Phase 3: Hypothesis Translation

Each actionable finding becomes a formal hypothesis:
- H-number
- Null and alternative hypothesis
- Test method
- Required sample size
- Bonferroni-adjusted threshold

### Phase 4: Testing

Same rigor as the diagnostic tests already done:
- Bonferroni correction
- Independent audit
- Versioned outputs
- Never overwrite

### Phase 5: Implementation

Positive findings → Claude Code implementation → shadow test 30+ observations → promote to live.

---

## EXPECTED YIELD

Based on the 19 questions already answered:
- 9 eliminated (47% — dead ends)
- 4 confirmed existing design (21% — no change needed)
- 4 informational (21% — useful context)
- 2 actionable (11% — produced deployable changes)

If this ratio holds across 113 questions:
- ~53 will be dead ends
- ~24 will confirm existing design
- ~24 will be informational
- **~12 will produce deployable improvements**

At +0.1R to +0.5R per improvement, 12 actionable findings could add +1.2R to +6R per trade or equivalent frequency/accuracy gains. This is speculative but grounded in the hit rate observed so far.

---

## RESOURCE ESTIMATE

| Resource | Estimate |
|----------|----------|
| Literature search sessions | 9 |
| Papers to evaluate | 650-960 |
| Deep reads | 90-135 |
| Diagnostic tests | 30-50 (many questions answered by existing data) |
| Claude Code implementation prompts | 10-15 |
| API cost (Opus for search, Sonnet for testing) | $200-400 |
| Calendar time (aggressive pace) | 2-3 weeks |
| Calendar time (steady pace) | 4-6 weeks |

---

## DECISION POINT

**Start with L1 (Entry Engineering + Features)?** These are the highest-leverage multiplier questions. Every improvement here compounds across all current and future trades.

**Or start with L5-L7 (Edge Discovery)?** Higher variance, but this is where entirely new setups hide. Could transform the system from 17 trades/month to 30-40 trades/month if new edges are found.

My recommendation: **L1 first.** Multipliers before discovery. But your call.

---

*Plan version: 1.0*
*Total questions remaining: 113*
*Estimated actionable findings: ~12 (based on 11% hit rate observed)*
*Highest-leverage cluster: Wave 1 (19 questions — entry, features, AI)*
*Largest cluster: Wave 3 (42 questions — edge discovery)*
