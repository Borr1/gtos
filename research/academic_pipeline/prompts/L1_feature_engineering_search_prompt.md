# L1 Feature Engineering Literature Search Prompt (Q-1.1 to Q-1.7)
## For: Claude Code execution agent (Opus, high effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor

---

## Literature Search: Feature Engineering for Intraday Trading Systems (Q-1.1 to Q-1.7)

### Context

GTOS is a live intraday trading system on XAUUSD + 4 instruments (US30, USDJPY, GBPJPY, GBPUSD) using H1 Order Block retest setups. The AI evaluator (Claude Sonnet) receives a structured Market State Object (MSO) containing:

Current features in MSO:
- OHLCV candle data across D1, H4, H1, M15 timeframes
- Swing highs/lows with HH/HL/LH/LL classification
- Structure events (BOS, CHoCH) with displacement quality
- Order blocks (unmitigated OBs with body, wick, formation time)
- Fair value gaps (unfilled FVGs)
- Premium/discount zone position
- Liquidity pools and sweep events
- ATR(14) per timeframe
- Average candle body per timeframe
- Session levels (PDH, PDL, Asian range)
- Tick volume (from retail CFD platform — NOT true exchange volume)

Key statistical properties already measured:
- Gold: random walk linearly (VR≈1.0, H≈0.5), fat tails (ξ=0.35, kurtosis=34.85), GARCH 0.99
- OB touch-1 continuation: 72.7% across 13 instruments (stop-cascade mechanism, Osler 2003/2005)
- Per-instrument ξ ranges from 0.16 (GBPUSD) to 0.35 (XAUUSD)
- 367 batch trades, overall WR 65%, ~17 trades/month expected frequency
- FVG-in-impulse: +7-20pp across 6 instruments
- Impulse compactness: ≤7 candles → 85% continuation vs ≥8 candles → 55%

The system enters after H1 structural break → pullback to OB zone → M15 CHoCH confirmation.

### Questions

Search for academic papers addressing each of the following. For each question, I provide search terms and what specifically is relevant to GTOS.

**Q-1.1: Mutual Information — Which features carry signal?**
Search terms: "mutual information" AND ("feature selection" OR "variable selection") AND ("financial returns" OR "stock returns" OR "forex" OR "time series")
Also search: "conditional mutual information" AND "trading", "transfer entropy" AND ("forex" OR "gold")
What we need: Methods to compute MI between OHLCV-derived structural features (swing positions, OB presence, FVG presence, displacement quality, premium/discount position) and subsequent 1-5 bar directional returns. NOT about indicator optimization (exclude RSI, MACD, Bollinger, Stochastic, moving average crossover papers). We want to know which current MSO features are signal vs noise, and whether there are missing features that MI analysis would surface.

**Q-1.2: Tick Volume Information Content on CFD**
Search terms: "tick volume" AND ("information content" OR "predictive" OR "signal") AND ("CFD" OR "retail forex" OR "OTC")
Also search: "volume" AND "forex" AND ("intraday" OR "microstructure"), "volume-return relation" AND "currency"
What we need: Is tick volume from a retail CFD broker (Exness via MT5) informative about anything — direction, volatility, institutional activity? The concern is that CFD tick volume reflects only that broker's flow, not the underlying market. If tick volume carries no signal, it should be removed from the MSO to reduce noise.

**Q-1.3: Spread Dynamics as Predictive Signal**
Search terms: "bid-ask spread" AND ("predictive" OR "signal" OR "forecasting") AND ("volatility" OR "direction" OR "informed trading")
Also search: "spread widening" AND "event" AND ("forex" OR "currency"), "adverse selection" AND "spread" AND "intraday"
What we need: Does spread widening predict subsequent volatility or direction? This could be a new feature for the MSO if spread data from MT5 is usable. Separate the volatility prediction case (probably yes — informed trading literature) from the directional prediction case (probably weak). Note: we can access real-time spread from MT5.

**Q-1.4: Multi-Timeframe Signal Combination Methods**
Search terms: "multi-scale" AND ("signal combination" OR "fusion") AND ("financial" OR "trading")
Also search: "hierarchical forecasting" AND ("time series" OR "financial"), "Bayesian" AND "multi-timeframe" AND "trading", "wavelet" AND "signal combination" AND ("forex" OR "intraday")
What we need: The current system uses simple majority vote across D1/H4/H1 for directional alignment (at least 2 of 3 must agree). Is there a better combination method? Options include: Bayesian fusion (weight each timeframe by its posterior probability), reliability-weighted voting (weight by historical accuracy), or hierarchical models (D1 conditions H4, H4 conditions H1). The key constraint: we have ~300 trades total, so the combination method must be parameterizable with very little data.

**Q-1.5: Optimal Feature Count for Small Samples**
Search terms: "curse of dimensionality" AND ("financial" OR "trading") AND ("feature selection" OR "sample size")
Also search: "VC dimension" AND "financial", "bias-variance" AND "trading" AND "features", "Vapnik" AND "sample complexity" AND "classification"
What we need: With ~300 historical trades and ~30-50 features in the MSO, are we in the danger zone for overfitting? Statistical learning theory (Vapnik, Hastie/Tibshirani) says n/p > 10 minimum for stable classifiers. But the AI is not fitting parameters — it's doing reasoning over structured data. Does the "curse of dimensionality" apply differently when the model is an LLM doing qualitative reasoning vs a traditional statistical model fitting coefficients? This is partly a novel question.

**Q-1.6: Gold vs FX Feature Requirements**
Search terms: "gold microstructure" AND ("intraday" OR "high frequency"), "commodity" AND "forex" AND "microstructure" AND "differences"
Also search: "XAUUSD" AND "price formation", "precious metals" AND "intraday" AND "patterns", "gold" AND "FX" AND "autocorrelation" AND "differences"
What we need: Our diagnostics show gold has unique properties (ξ=0.35 vs FX 0.16-0.22, GARCH 0.99, kurtosis 34.85, negative skew -1.53). Should the MSO have gold-specific features not needed for FX? For example: DXY correlation as a feature, COMEX delivery effects, London AM/PM fix residuals, central bank reserve reporting dates. Are there gold-specific microstructure papers documenting features that matter only for gold?

**Q-1.7: Order Flow Estimation from OHLCV**
Search terms: "VPIN" AND "OHLCV", "bulk volume classification" AND ("forex" OR "currency" OR "gold")
Also search: "trade classification" AND "OHLCV" AND ("Lee-Ready" OR "tick rule"), "order flow" AND "estimation" AND "candle" AND ("intraday"), "informed trading" AND "proxy" AND ("retail" OR "OHLCV")
What we need: Can we approximate institutional order flow from OHLCV data without Level 2 access? The VPIN paper (Easley, Lopez de Prado, O'Hara 2012 — ALREADY FOUND in Q-4.2 search, phase1_entry_engineering_papers_v1.md) shows volume-clock toxicity estimation. What OTHER methods exist? Specifically: (a) Bulk Volume Classification (Easley/LdP/O'Hara 2012 companion paper), (b) tick rule approximations on low-frequency data, (c) close-to-high / close-to-low ratios as flow proxies. If any of these work on M15 gold data, it's a genuinely new feature class for the MSO.

### Exclusion Filters

REJECT papers that:
- Focus on indicator optimization (RSI, MACD, Bollinger Bands, Stochastic oscillator, moving average crossovers)
- Use deep learning as a black box without explaining which features matter
- Are from predatory journals (MDPI special issues, Hindawi pay-to-publish)
- Have no empirical component (pure survey without new results — cite but don't promote)
- Test on simulated data only with no real-market calibration

### Quality Filter (5 dimensions)

Rate each paper on:
1. **Testability on GTOS data:** Can we apply this to our 367 trades / MT5 OHLCV data? (High/Medium/Low)
2. **Data availability:** Does this require data we don't have (Level 2, options chain, futures COT)? (Available/Partial/Unavailable)
3. **Relevance to GTOS pipeline:** Does this address a specific component or feature in the MSO? (Direct/Indirect/Tangential)
4. **Journal tier:** Tier 1 (JF, RFS, JFQA, Econometrica, QF), Tier 2 (JFM, JIMF, JBF, JEF, good working papers), Tier 3 (arXiv, decent conference), Tier 4 (MDPI, predatory, no review)
5. **OOS validation:** Does the paper test out-of-sample? (Yes/Partial/No)

Promote papers scoring High/Available or Partial/Direct or Indirect/Tier 1-3/Yes or Partial on at least 3 of 5 dimensions.

### Cross-Reference Requirement

Before documenting a paper, check if it already appears in:
- research/academic_pipeline/phase1_priority_a_papers.md (69 papers)
- research/academic_pipeline/phase1_entry_engineering_papers_v1.md (51 papers)

If already found, note "CROSS-REFERENCE: Already in [file] (Q-X.X)" and do not repeat the full entry. Only add new findings not present in the existing searches.

### Output Format

Match the structure of phase1_entry_engineering_papers_v1.md exactly:
- Per-question sections with verdict
- Per-paper entries with: Authors, Year, Source, Quality Tier, Citations, Asset class, OOS validation, Relevance to GTOS, Question addressed, Key finding, Key equation, Testable on GTOS data, Per-instrument note (if applicable)
- Cross-Question Synthesis section
- Specific GTOS Implications section (testable hypotheses with method, prediction, and required data)
- Rejected Papers table
- Full reference list

### Save Path

Save as: research/academic_pipeline/phase1_feature_engineering_papers_v1.md

### Constraints

- Do NOT modify any files in src/ or prompts/
- Do NOT apply gold-only findings universally — note per-instrument applicability
- Null results are valuable — if tick volume has no signal, document that conclusion clearly
- If a question has genuinely thin academic coverage, state "THIN COVERAGE" and explain what was searched and not found
- Quality over quantity — 8 excellent papers beat 25 mediocre ones
- Verify citation counts and journal existence before documenting

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Q-1.1 too broad ("MI + finance" = thousands) → Added "OHLCV-derived features only" filter + indicator exclusion
2. Q-1.4 too broad (spans signal processing, Bayesian, ensemble) → Narrowed to "multi-scale/hierarchical combination for directional trading"
3. Q-1.5 partially off-topic (learning theory, not finance) → Reframed as "learning theory constraints for financial feature sets" + added Vapnik/VC-dimension
4. Q-1.7 overlap with existing Priority A (VPIN already found) → Cross-reference noted, search targets ADDITIONAL methods only
5. Missing indicator exclusion filter (per kb_prompt_engineering_patterns.md) → Added explicit RSI/MACD/Bollinger/Stochastic exclusion
6. Missing 5-dimensional quality filter → Added: testability, data availability, relevance, journal tier, OOS validation
7. Missing per-instrument analysis note → Added to output format requirements
8. Missing cross-reference against existing 120 papers → Added cross-reference instruction against both existing files
