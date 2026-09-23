# L3 — Edge Optimization Literature Search (Q-0.1, Q-0.3, Q-0.6, Q-0.7, Q-2.1, Q-2.3 to Q-2.9)
## For: Claude Code execution agent (Opus, high effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor

---

## Literature Search: Edge Optimization — Pre-Screen Frequency + Structure Detection

### Context

GTOS is a live intraday trading system on XAUUSD + 4 instruments (US30, USDJPY, GBPJPY, GBPUSD) using H1 Order Block retest setups. The system currently:

**Pre-screen (Component 0):**
- Uses D1 directional bias as the top-level filter. If D1 structure is "unclear" or "ranging" → the AI falls back to H4+H1 consensus (at least 2 of 3 must agree)
- Rejects ~51% of trading days due to unclear D1 direction
- Evaluates ~10-20 candles per kill zone session, with only ~10.3% receiving CANDIDATE
- Expected frequency: ~17 trades/month across all instruments — significantly below the ~30-40/month that would maximize FTMO pass probability at optimal sizing

**Structure detection (Component 2 — `src/components/market_state.py`):**
- Detects swing points using a fixed-lookback algorithm (N candles before/after)
- Classifies swings as HH/HL/LH/LL based on sequential comparison
- Identifies BOS (Break of Structure) and CHoCH (Change of Character) events
- Detects Order Blocks: last opposing candle before a structural break
- Detects Fair Value Gaps: unfilled 3-candle gaps
- Detects liquidity sweeps: wicks beyond key levels (PDH/PDL, Asian range, session levels, equal highs/lows)
- Computes premium/discount zones relative to impulse legs
- Operates on H1 and M15 timeframes

**Key statistical properties:**
- OB touch-1 continuation: 72.7% across 13 instruments (the core edge)
- Gold: ξ=0.35 (fat tails), GARCH 0.99, kurtosis 34.85, negative skew -1.53
- FVG-in-impulse: +7-20pp across 6 instruments
- Impulse compactness: ≤7 candles → 85% continuation vs ≥8 → 55%
- Quarterly WR decay: 73.2% → 71.4% → 63.6% → 59.4% (trend real, cause unknown)

**The frequency problem:** The system's edge is validated but trades are too rare. If we can SAFELY increase frequency (more trading days, more setups per day, or faster zone identification) without diluting the 72.7% continuation rate, expected value increases substantially. Kelly optimal sizing at current WR gives f*=4%, but we're running at 1-2% because frequency is too low for the sample sizes needed to validate higher risk.

### Questions

**Q-0.1: Daily Candle Properties Predict Trending Days**
Search terms: "daily range" AND "trending" AND ("forecast" OR "predict") AND ("intraday" OR "gold" OR "forex")
Also search: "daily body" AND "range ratio" AND "trend", "daily candle" AND "continuation" AND "pattern", "opening range" AND "daily" AND "direction", "range expansion" AND "preceding day" AND "gold"
What we need: Can we replace the subjective "D1 unclear" rejection with a quantitative filter? Specifically: does yesterday's candle body-to-range ratio, absolute range, or body direction predict whether today will be trending (exploitable by OB retest) vs ranging (no OB opportunity)? If a simple quantitative rule recovers even 20% of the rejected days without diluting WR, frequency increases by ~10%.

**Q-0.3: Regime Detection (HMM, Change-Point)**
Search terms: "hidden Markov model" AND ("gold" OR "forex" OR "financial") AND ("regime" OR "volatility")
Also search: "change point detection" AND "intraday" AND ("forex" OR "gold"), "regime switching" AND "trading" AND "strategy", "BOCPD" AND "financial", "structural break" AND "detection" AND ("real-time" OR "online")
What we need: GTOS already has BOCPD and CUSUM monitors (deployed April 11). Question: can an HMM or change-point detector REPLACE the D1 directional pre-screen? The key constraint is detection LAG — a regime detector that identifies "trending" 4 hours after the trend started is useless for intraday OB entries. We need real-time or near-real-time detection (lag < 2 hours). The literature on HMMs for gold and FX is extensive (Hamilton 1989 is the foundation). Focus on papers that test detection speed, not just detection accuracy.

**Q-0.6: GVZ / Implied Volatility Predicts Intraday Patterns**
Search terms: "GVZ" AND ("gold" OR "XAUUSD"), "implied volatility" AND "realized volatility" AND ("gold" OR "precious metals") AND ("intraday" OR "predict")
Also search: "CBOE Gold ETF Volatility" AND "signal", "IV-RV ratio" AND "forecast" AND "gold", "option-implied" AND "intraday" AND "pattern" AND "metals", "volatility risk premium" AND "gold"
What we need: GVZ (CBOE Gold ETF Volatility Index) is freely available. If GVZ level or GVZ/RV ratio predicts whether a day will be trending vs ranging, it's a free pre-screen filter. The equity VIX literature is extensive; gold-specific VIX literature is thin. We need gold-specific evidence. Also: does the volatility risk premium (VRP = IV - RV) predict gold intraday direction or magnitude?

**Q-0.7: Calendar Effects Beyond Day-of-Week**
Search terms: "FOMC" AND "gold" AND ("intraday" OR "volatility" OR "reaction")
Also search: "options expiry" AND "gold" AND "pattern", "COMEX delivery" AND "gold" AND "price", "turn-of-month" AND "gold", "NFP" AND "gold" AND "intraday", "fix" AND "London" AND "gold" AND "price impact", "month-end rebalancing" AND "gold", "central bank" AND "gold" AND "announcement"
What we need: The system currently has a news filter (disabled) and skips 13:00-13:15 UTC. Are there specific calendar events that predict OB continuation behavior? Three categories: (a) events that increase volatility (FOMC, NFP) — these may IMPROVE OB setups (stronger displacement), (b) events that disrupt structure (COMEX delivery, month-end rebalancing) — these may DEGRADE OB setups, (c) events that create predictable patterns (London fix, options expiry) — these may create NEW entry opportunities. Most important: FOMC effect on gold intraday structure. Is OB continuation rate different on FOMC days?

**Q-2.1: Optimal Swing Point Detection**
Search terms: "turning point detection" AND ("algorithm" OR "method") AND ("financial" OR "price")
Also search: "Bry-Boschan" AND ("dating" OR "algorithm"), "directional change" AND ("intrinsic time" OR "forex"), "swing point" AND "detection" AND ("optimal" OR "comparison"), "local extrema" AND "time series" AND "noise", "zig-zag" AND "algorithm" AND "financial"
What we need: GTOS uses a fixed-lookback swing detection (N candles before/after form a higher/lower pivot). Are there better algorithms? Bry-Boschan (1971) is the gold standard for business cycle dating — does it work for intraday price structure? Directional-change algorithms (Glattfelder et al. 2011, Tsang) detect swings in intrinsic time, which may be more robust than clock time. The key question: does a different swing algorithm produce better BOS/CHoCH identification, and does that improve OB zone detection?

**Q-2.3: Support/Resistance Mechanisms Beyond OB**
Search terms: "round number" AND ("clustering" OR "barrier") AND ("forex" OR "exchange rate")
Also search: "psychological level" AND "price" AND "barrier", "previous day high" AND "support" AND "resistance", "session level" AND "intraday" AND "bounce", "order clustering" AND "price level" AND "forex", "price magnet" AND "support" AND "resistance"
What we need: GTOS uses OB zones as the primary S/R mechanism. But price also responds to round numbers (e.g., 2300, 2350 on gold), PDH/PDL, session levels, and equal highs/lows. Does adding these as confirming signals to OB zones improve WR? Specifically: does an OB zone that ALSO aligns with a round number or PDH/PDL have a higher continuation rate? Osler (2003) documented stop clustering at round numbers — this is the same mechanism as the OB edge.

**Q-2.4: FVG Gap Fill Rates**
Search terms: "price gap" AND "fill" AND ("probability" OR "rate") AND ("intraday" OR "forex")
Also search: "fair value gap" AND "fill" AND "empirical", "imbalance" AND "rebalance" AND "price" AND "time", "unfilled gap" AND "return" AND "probability", "gap" AND "momentum" AND "continuation" AND "intraday"
What we need: FVG presence is a current quality signal in the MSO (+7-20pp continuation across 6 instruments). But: (a) Do FVGs fill above chance? (b) How fast do they fill? (c) Does FVG SIZE predict continuation vs fill probability? The equity gap literature (common gaps vs breakaway gaps) is relevant but FX/gold-specific FVG literature is likely thin. SMC/ICT practitioners claim FVGs "must fill," but this is untested academically. If FVG fill rate is >80%, the gap represents a temporary inefficiency exploitable by the retest entry.

**Q-2.5: Order Book / Liquidity Pool Dynamics**
Search terms: "limit order" AND "clustering" AND ("forex" OR "exchange rate")
Also search: "order book" AND "dynamics" AND "intraday" AND ("model" OR "empirical"), "liquidity" AND "concentration" AND "price level" AND "prediction", "Bouchaud" AND "order book" AND "model", "latent order book" AND "estimation"
What we need: Where do liquidity pools form? Can we predict stop-loss and take-profit clustering from OHLCV data? GTOS identifies pools at key levels (PDH/PDL, Asian range, equal highs/lows) — but is this the right set? Bouchaud et al.'s latent order book models predict order accumulation patterns from price dynamics. If applicable to FX/gold at M15, this could improve the liquidity sweep signal. Key constraint: we cannot observe the actual order book (retail CFD has no L2 data).

**Q-2.6: Displacement Magnitude vs Continuation**
Search terms: "impulse" AND "magnitude" AND "continuation" AND ("forex" OR "price")
Also search: "momentum" AND "magnitude" AND "reversal" AND "threshold", "breakout" AND "strength" AND "follow-through", "initial move" AND "continuation" AND "probability", "displacement" AND "structural break" AND "quality"
What we need: Is bigger impulse = higher continuation rate? Or is there a threshold (e.g., >2x avg body = good, >5x = overextended)? GTOS already measures displacement_ratio (impulse body / avg body). We know ≤7 candles compact impulse → 85% vs ≥8 candles → 55%. But the MAGNITUDE threshold is not studied. This is directly testable on batch data (already have displacement_ratio for 129 trades). Literature may provide theoretical framework for why a threshold exists (momentum vs mean-reversion regimes).

**Q-2.7: Premium/Discount Zone Evidence**
Search terms: "mean reversion" AND "range" AND ("intraday" OR "forex") AND ("zone" OR "half")
Also search: "Fibonacci retracement" AND "empirical" AND ("forex" OR "gold" OR "exchange rate"), "optimal retracement" AND "entry" AND "trading", "intra-range position" AND "future return", "pullback depth" AND "continuation"
What we need: GTOS requires longs in discount (below 50% of impulse) and shorts in premium (above 50%). Is there empirical evidence for this? The T1 entry engineering tests found that entry depth (as defined) was hard to measure because entries are ABOVE the OB zone. But the AI decision JSON includes `h1_setup.fib_retracement_pct` — this IS the premium/discount position. If the literature says 62-79% retracement is the "sweet spot," it directly validates the current fib62/fib79 levels in the MSO. NOTE: Fibonacci retracement per se is debunked (Droke 2001 — already in L1 search), but RANGE POSITION (upper/lower half) as a mean-reversion signal is different from Fibonacci mysticism.

**Q-2.8: Fractal Structural Breaks**
Search terms: "multifractal" AND "breakout" AND ("detection" OR "signal") AND "financial"
Also search: "MFDFA" AND ("gold" OR "forex" OR "financial"), "fractal dimension" AND "structural break" AND "price", "scale-invariant" AND "pattern" AND "detection" AND "trading", "Hurst exponent" AND "local" AND "change"
What we need: Can multifractal analysis (MFDFA) identify structural breaks with less lag than fixed-lookback? The current swing detection uses a fixed N-candle lookback, which means there's always an N-candle LAG before a break is confirmed. If MFDFA or local Hurst exponent can detect regime transitions earlier, it could improve BOS/CHoCH detection speed. Key concern: implementation complexity vs marginal improvement. If the literature shows MFDFA adds 1-2 candles of detection speed, the implementation cost may not justify it.

**Q-2.9: Liquidity Sweep Reversal Evidence**
Search terms: "stop hunting" AND ("evidence" OR "empirical") AND ("forex" OR "exchange rate")
Also search: "stop loss" AND "clustering" AND "reversal" AND "cascade", "false breakout" AND "reversal" AND "probability", "stop cascade" AND "mean reversion", "price reversal" AND "liquidity" AND "sweep"
What we need: The GTOS entry mechanism IS the sweep-and-retest: price sweeps a liquidity pool (stops above/below a level), then reverses. Osler (2003, 2005) documented stop-loss clustering at round numbers and the cascade mechanism. But is there additional academic evidence for the sweep→reversal pattern specifically? The US30 sweep divergence monitor (H16) already tracks this: US30 68% continuation vs XAUUSD 31% after sweeps. Can the literature explain this cross-instrument difference? Is there a framework for predicting when a sweep leads to continuation vs reversal?

### Exclusion Filters

REJECT papers that:
- Focus on indicator optimization (RSI, MACD, Bollinger, Stochastic, moving average crossovers)
- Use deep learning as a black box without explaining which structural features matter
- Are from predatory journals (MDPI special issues, Hindawi)
- Focus on daily/weekly forecasting with no intraday application
- Test on simulated data only with no real-market calibration
- Claim "Fibonacci ratios have mystical significance" without statistical testing

### Quality Filter (5 dimensions)

Rate each paper on:
1. **Testability on GTOS data:** Can we test this on our 367 trades / M15 OHLCV / MT5 data? (High/Medium/Low)
2. **Data availability:** Does this need data we don't have (Level 2, options chain, COT)? (Available/Partial/Unavailable)
3. **Relevance to GTOS pipeline:** Does this address Component 0 (pre-screen) or Component 2 (structure detection) specifically? (Direct/Indirect/Tangential)
4. **Journal tier:** Tier 1 (JF, RFS, JFQA, Econometrica, QF), Tier 2 (JFM, JIMF, JBF, JEF, good working papers), Tier 3 (arXiv, decent conference), Tier 4 (MDPI, predatory, blog)
5. **OOS validation / reproducibility:** (Yes/Partial/No)

Promote papers scoring well on at least 3 of 5 dimensions.

### Cross-Reference Requirement

Check papers against ALL prior search results:
- `research/academic_pipeline/phase1_priority_a_papers.md` (69 papers)
- `research/academic_pipeline/phase1_entry_engineering_papers_v1.md` (51 papers)
- `research/academic_pipeline/phase1_feature_engineering_papers_v1.md` (57 papers)
- `research/academic_pipeline/phase1_ai_evaluation_papers_v1.md` (96 papers)

Note cross-references; do not repeat full entries for papers already covered.

### Output Format

Match the structure of phase1_feature_engineering_papers_v1.md:
- Per-question sections with verdict
- Per-paper entries with: Authors, Year, Source, Quality Tier, Citations, Asset class / task tested, OOS validation, Relevance to GTOS, Question addressed, Key finding, Key equation / method, Testable on GTOS data, Per-instrument note (if applicable)
- Cross-Question Synthesis section
- Specific GTOS Implications section (testable hypotheses with method, prediction, required data)
- Rejected Papers table
- Full reference list

### Save Path

Save as: `research/academic_pipeline/phase1_edge_optimization_papers_v1.md`

### Constraints

- Do NOT modify any files in src/ or prompts/
- The FOMC/calendar effects question (Q-0.7) should focus on GOLD-SPECIFIC evidence. Generic equity calendar anomaly papers are tangential.
- The FVG question (Q-2.4) must distinguish between equity common gaps and FX intraday FVGs — these are structurally different phenomena.
- The Fibonacci question (Q-2.7) must separate mystical claims from empirical range-position evidence. The fact that price often retraces 50-62% is a statistical regularity about mean reversion, not evidence for Fibonacci ratios.
- Null results are valuable — "there is no academic evidence that FVGs fill above chance" would be important.
- If a question has thin coverage, state "THIN COVERAGE" and explain what was searched and not found.
- Quality over quantity — 8 excellent papers beat 25 mediocre ones.
- Cross-instrument differences matter: gold microstructure differs from FX (documented in L1 Q-1.6). Note per-instrument applicability.
- ALREADY KNOWN: Osler 2003/2005 (stop clustering, cascades) — cited extensively in prior searches. Do not repeat these entries. Build on them.

---

## Prerequisites (execution agent must complete before starting)

### Required Tool Access
- **WebSearch** — CRITICAL. This is a literature search — it cannot be performed without web search access. If WebSearch is unavailable, exit immediately with "TOOL_UNAVAILABLE: WebSearch required for literature search."

### Recommended Model
- **Opus** — This prompt requires deep analytical synthesis across 12 questions with cross-referencing against 273+ prior papers. Sonnet can execute but Opus produces more thorough coverage and better synthesis.

### Required Reading (before starting searches)

Read ALL 4 prior search result files to avoid duplicates and to build on existing findings:

1. **`research/academic_pipeline/phase1_priority_a_papers.md`** (69 papers) — Original priority search covering broad topics
2. **`research/academic_pipeline/phase1_entry_engineering_papers_v1.md`** (51 papers) — L0 entry engineering literature
3. **`research/academic_pipeline/phase1_feature_engineering_papers_v1.md`** (57 papers) — L1 feature engineering: tick volume, CLV, BVC, session ATR, MI, spread
4. **`research/academic_pipeline/phase1_ai_evaluation_papers_v1.md`** (96 papers) — L2 AI evaluation: XGBoost baseline, CoT, framing, memory, confidence, self-consistency

**Total papers already covered: 273+.** If you find a paper already covered in a prior search, note it as a cross-reference — do NOT repeat the full entry.

### Search Strategy

For each of the 12 questions:
1. Run 2-3 search queries using the provided search terms
2. Scan titles and abstracts for relevance
3. For relevant papers, read enough to extract: method, key result, asset class, OOS validation status
4. Apply the quality filter (5 dimensions)
5. Check against the 4 prior files for duplicates
6. Rate testability on GTOS data specifically

### Output Discipline
- **Quality over quantity** — 8 excellent papers per question beats 25 mediocre ones
- If a question has < 3 quality results after thorough searching, mark "THIN COVERAGE" and explain what was searched
- Null results are valuable — "no academic evidence found" is a finding
- Per-instrument notes for gold vs FX differences (gold ξ=0.35 microstructure)

### Time Estimate
- 12 questions × 3 searches × 2 min/search + synthesis = ~90-120 min execution time
- Budget search time per question proportionally to expected impact:
  - HIGH (Q-0.1, Q-0.3, Q-2.1, Q-2.9): More search iterations, deeper reads
  - MEDIUM (Q-0.6, Q-0.7, Q-2.3, Q-2.4, Q-2.6): Standard 2-3 searches
  - EXPLORATORY (Q-2.5, Q-2.7, Q-2.8): 1-2 searches, accept thin coverage

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Q-0.1 too broad ("daily candle predict trend" = thousands of pattern papers) → Narrowed to body-to-range ratio, range expansion, and continuation specifically
2. Q-0.3 overlap with already-deployed BOCPD/CUSUM → Noted existing monitors, focused search on HMM REPLACING D1 pre-screen and on detection LAG as key metric
3. Q-0.6 extremely thin on gold-specific GVZ → Added broader "options-implied volatility" search terms, noted likely thin coverage
4. Q-0.7 too broad (calendar anomalies = massive literature) → Focused on gold-specific: FOMC, NFP, London fix, COMEX delivery. Excluded generic equity anomalies.
5. Q-2.1 could surface indicator-based papers → Added explicit exclusion for indicator optimization
6. Q-2.4 equity gap literature is huge but irrelevant to intraday FVGs → Added note distinguishing equity gaps from FX intraday FVGs
7. Q-2.7 Fibonacci mysticism danger → Added explicit instruction to separate mystical claims from empirical range-position evidence. Referenced Droke 2001 (already in L1) as debunking Fibonacci per se.
8. Q-2.8 MFDFA is exotic and high-implementation-cost → Added cost-benefit framing: only worth recommending if detection speed gain > 1-2 candles
9. Q-2.9 overlap with existing Osler coverage → Added note: Osler already extensively cited. Search for ADDITIONAL evidence beyond Osler.
10. Missing cross-reference against L1 and L2 papers (now 273+ papers) → Added all 4 prior search files to cross-reference list
11. 12 questions is a lot for one search session → Acceptable because many questions overlap (structure detection is one domain). The alternative (splitting into L3a/L3b) would create redundant context loading.
12. Missing prerequisites section → Added: WebSearch requirement, Opus recommendation, required reading list, search strategy guidance, time estimate.
