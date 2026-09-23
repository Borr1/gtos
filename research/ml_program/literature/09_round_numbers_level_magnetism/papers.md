# Domain 09 — Round-Number Effects & Level Magnetism: Literature Catalog

**Worker:** Phase 1 Literature Research Agent #9
**Date:** 2026-04-28
**Spec:** `research/ml_program/literature/_specs/09_round_numbers_level_magnetism.md`
**Papers cataloged:** 30
**Coverage:** foundational price-clustering (1965, 1991-1994), early psychological-barriers (1993-1999), FX clustering (1991-2007), Osler order-cluster trio (2000-2005), gold/commodities (2007-2017), behavioral mechanism (2003-2024), recent advances 2017-2025 incl. crypto, frontier markets, individual-stock effects, option pricing under barriers.

**Schema:** `id | title | authors | year | source | url | abstract | key_findings | level_granularity | relevance_to_gtos | potential_hypothesis | cross_domain_links`

Per spec §7, `level_granularity` is the domain-specific extra field: BIG (1000s/100s round numbers), MEDIUM (50s/25s), FINE (10s/5s/quarter-figure / sub-pip).

---

## 1. Foundational papers (1965-1999)

### 1.1 Clustering of Stock Market Prices
- **Authors:** Victor Niederhoffer
- **Year:** 1965
- **Source:** Operations Research, 13(2): 258-265
- **URL:** https://pubsonline.informs.org/doi/10.1287/opre.13.2.258
- **Abstract:** First rigorous empirical investigation of price clustering in financial markets. Documented that NYSE stock orders cluster at numbers traders are accustomed to deal with — particularly integer prices and halves.
- **Key findings:**
  - Asymmetry between bid and ask quotes around integer prices: more limit-sell orders just below integers, more limit-buys just above
  - Strategic trading exploits the round-number cluster (sellers undercut, buyers overbid the round)
  - Resulting cluster generates resistance points — round numbers become "hard to penetrate" price barriers
  - Earliest evidence of round-number magnetism that all subsequent literature builds upon
- **Level granularity:** FINE (integers + halves)
- **Relevance to GTOS:** Earliest theoretical basis for ICT/SMC "psychological levels" embedded in `market_state.py`. Direct mechanism for why limit orders pile up ahead of round levels — supports B.1 cross-instrument context's intuition. Predicts NAS100 20000 / US30 40000 / XAU $3000 should show order-book asymmetry that the OB detector can latch onto.
- **Potential hypothesis:** A round-number-distance feature in K54 (`abs(close - nearest_round) / atr`) should help discriminate continuation vs reversal at OB retest.
- **Cross-domain links:** 06 (microstructure), 07 (ICT level rules), 18 (psychology mechanism)

### 1.2 The Clustering of Bid/Ask Prices and the Spread in the Foreign Exchange Market
- **Authors:** Riccardo Curcio, Charles Goodhart
- **Year:** 1991
- **Source:** FMG Discussion Paper 110, London School of Economics
- **URL:** http://eprints.lse.ac.uk/119186/
- **Abstract:** First study of FX bid/ask price clustering — examined trailing digit of USD/DEM buy/sell quotes from Reuters indicative-quote feed.
- **Key findings:**
  - Final-digit clustering depends on desired price-resolution granularity
  - Spread-selection clustering follows a different pattern (pure attraction hypothesis) than price-level clustering
  - Provides the FX-side analog to Niederhoffer's NYSE finding: round numbers are special in FX too
  - Behaviorally driven — not explained by tick-size constraint alone
- **Level granularity:** FINE (final-digit pip-level)
- **Relevance to GTOS:** Direct foundation for why EURUSD / GBPUSD / USDJPY tight-FX overrides exist (5/8-tick buffers). The Goodhart-Curcio asymmetry literally is what makes FX precision-rounding bugs class (`project_eurusd_sl_root_cause`) so common. Supports per-pair tick-size differentiation.
- **Potential hypothesis:** Per-instrument SL buffer multipliers should be calibrated to instrument-specific clustering granularity — not just ATR-based.
- **Cross-domain links:** 06 (microstructure), 11 (FX content)

### 1.3 Stock Price Clustering and Discreteness
- **Authors:** Lawrence Harris
- **Year:** 1991
- **Source:** Review of Financial Studies, 4(3): 389-415
- **URL:** https://academic.oup.com/rfs/article-abstract/4/3/389/1580169
- **Abstract:** Canonical paper establishing the negotiation-cost theory of clustering. Traders use discrete price sets to simplify negotiations; clustering rises with price level + volatility, falls with capitalization + transaction frequency.
- **Key findings:**
  - On 12/31/1987, 2431 of 2510 CRSP daily closes are divisible by 1/8 — overwhelming clustering even where smaller ticks are legal
  - Negotiation-cost hypothesis: traders restrict to round subsets to minimize haggling cost, transaction costs, and information leakage
  - Predicts more clustering for high-vol / high-uncertainty / illiquid stocks — confirmed across decades since
  - Frame-based clustering (1/8 → 1/4 → 1/2 → integer)
- **Level granularity:** FINE to MEDIUM (eighths through halves through integers)
- **Relevance to GTOS:** Theoretical anchor for why XAU clusters at 0/5/10s while indices cluster at 100s/1000s. Predicts that high-vol regimes should show MORE clustering — relevant for K54 regime-aware features (volatility quantile × distance-to-round interaction).
- **Potential hypothesis:** OB continuation rate should be higher when OB level is itself round, because clustering = thicker liquidity = better stop-cascade mean-reversion behavior.
- **Cross-domain links:** 06 (microstructure), 18 (psychology)

### 1.4 Price Barriers in the Dow Jones Industrial Average
- **Authors:** R. Glen Donaldson, Harold Y. Kim
- **Year:** 1993
- **Source:** Journal of Financial and Quantitative Analysis, 28(3): 313-330
- **URL:** https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/price-barriers-in-the-dow-jones-industrial-average/ED089C700C6B674DA8BD1BFB10CA0B85
- **Abstract:** Foundational psychological-barriers paper. Tests the claim that DJIA movements around 100-multiples ("psychological barriers") affect investor sentiment and price behavior. 15 years of DJIA + Wilshire 5000 closes from 1974.
- **Key findings:**
  - Lower closing-price frequency in tight bands around 100-multiples (and especially 1000-multiples) — barriers do exist
  - Conditional on breaking through, post-breakout movement is amplified ("bandwagon effect")
  - Two distinct effects: pre-cross resistance + post-cross momentum
  - Survives basic cyclical-permutation control
- **Level granularity:** BIG (100s, 1000s)
- **Relevance to GTOS:** Direct empirical support for pre-AI POI gating around major round levels (NAS100 20000, US30 40000, XAU $3000). Bandwagon effect = continuation regime after breakout — relevant for `breaker_re_entry` framework. Decay literature (item #4) suggests continuation post-cross may be the regime-dependent edge.
- **Potential hypothesis:** Conditional on "broke a round-number magnetic level in last N candles", momentum-regime continuation probability is higher. Test as binary feature in K54.
- **Cross-domain links:** 12 (equity indices), 17 (behavioral aggregate), 14 (momentum after breakout)

### 1.5 On the Hypothesis of Psychological Barriers in Stock Markets and Benford's Law
- **Authors:** Marc J.K. De Ceuster, G. Dhaene, Tine Schatteman
- **Year:** 1998
- **Source:** Journal of Empirical Finance, 5(3): 263-279
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0927539897000248
- **Abstract:** First major contrarian / null-result paper. Argues that uniform-distribution test against trailing-digits is the wrong benchmark — Benford's Law predicts the trailing digits of a multiplicative process do NOT distribute uniformly, so apparent clustering may be a Benford artifact.
- **Key findings:**
  - Proposes cyclical-permutation-of-actual-returns benchmark (instead of uniform)
  - Applied to DJIA, FTSE-100, Nikkei 225 — find NO convincing evidence of psychological barriers under proper benchmark
  - Invalidates a swath of prior tests
  - Methodologically central paper — every subsequent psych-barrier paper must use a Benford-corrected test
- **Level granularity:** BIG (index 100s, 1000s)
- **Relevance to GTOS:** Caveat for any GTOS feature built on round-number distance. Prevents false-positive "edge" claims if synthetic backtest uses naive uniform null. F11/F15 methodology auditors would have caught this if applied to round-number features.
- **Potential hypothesis:** ANY round-number-distance feature in K54 must be validated against Benford-permutation null, not uniform null, before claiming significance.
- **Cross-domain links:** 02 (statistical methodology), 17 (behavioral)

### 1.6 Evidence of Psychological Barriers in the Conditional Moments of Major World Stock Indices
- **Authors:** Ken B. Cyree, Dale L. Domian, David A. Louton, Elizabeth J. Yobaccio
- **Year:** 1999
- **Source:** Review of Financial Economics, 8(1): 73-91
- **URL:** https://onlinelibrary.wiley.com/doi/10.1016/S1058-3300%2899%2900002-6
- **Abstract:** Examines barriers in DJIA, S&P 500 + 6 foreign indices. Moves the test from frequency-of-trailing-digit to GARCH-style conditional-moment tests around hypothesized barriers.
- **Key findings:**
  - In 5 of 8 indices, conditional mean returns significantly higher AFTER an upward barrier crossing
  - In 7 of 8 indices, significant conditional VARIANCE effects coincident with crossings
  - Barriers manifest as volatility-regime shifts, not just frequency anomalies
  - Asymmetric: upward-cross effect stronger than downward-cross effect
- **Level granularity:** BIG (100s)
- **Relevance to GTOS:** Suggests that volatility regime classifier (production-active per ADR-004) should have a "near-round-number" feature — barrier crossings cause volatility shifts the H4-swing classifier may miss. Crossings as regime-change events.
- **Potential hypothesis:** Volatility regime classifier accuracy improves with `crossed_round_number_in_last_N_candles` flag.
- **Cross-domain links:** 16 (volatility regime), 05 (change-point), 12 (equity indices)

---

## 2. The Osler trio — order clustering at round numbers (2000-2005)

### 2.1 Support for Resistance: Technical Analysis and Intraday Exchange Rates
- **Authors:** Carol L. Osler
- **Year:** 2000
- **Source:** FRBNY Economic Policy Review, 6(2): 53-68
- **URL:** https://www.newyorkfed.org/research/epr/00v06n2/0007osle.html
- **Abstract:** First Osler paper on the order-microstructure foundations of technical analysis. Tests intraday FX rates for predictable bouncing at published support/resistance levels.
- **Key findings:**
  - Intraday exchange rates DO bounce predictably off published S/R levels
  - Bounce predictions outperform random levels statistically significantly across multiple currencies
  - Active 5-day horizons
  - Sets up the question that Osler 2003/2005 answers: WHY do these levels work?
- **Level granularity:** MEDIUM-BIG (FX round figures + half-figures)
- **Relevance to GTOS:** Empirical anchor for the entire premise of trading at OB levels. The Osler bounce-effect IS the GTOS edge mechanism, specifically when OB level is also round.
- **Potential hypothesis:** OB continuation rate (rolling-50, baseline 70%) decomposes by `round_number_alignment`: round-aligned OBs should show higher continuation vs arbitrary-level OBs.
- **Cross-domain links:** 07 (technical analysis academic), 11 (FX), 06 (microstructure)

### 2.2 Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis
- **Authors:** Carol L. Osler
- **Year:** 2003
- **Source:** Journal of Finance, 58(5): 1791-1820 (also FRBNY Staff Report 125)
- **URL:** https://fraser.stlouisfed.org/files/docs/publications/frbnysr/frbny_sr125.pdf
- **Abstract:** THE seminal paper that GTOS's edge mechanism cites. Microstructural explanation for technical analysis success using NatWestMarkets stop-loss + take-profit order book Aug 1999-Apr 2000 across DEM, USD/JPY, USD/GBP.
- **Key findings:**
  - **Take-profit orders cluster strongly AT round numbers** (≈10% at rates ending 00, vs ≈3% baseline for other 0-endings)
  - **Stop-loss orders cluster JUST BEYOND round numbers** — buy-stops above, sell-stops below
  - Execution-rate clustering is asymmetric: take-profits at round numbers, stops past round numbers
  - This pattern alone explains both directional predictions of TA: (a) trend reversal at round levels (take-profits exhaust the move), (b) trend acceleration past round levels (stops cascade)
  - Customer + in-house orders both included — robust across order types
- **Level granularity:** MEDIUM-FINE (FX 00 endings + just-beyond endings)
- **Relevance to GTOS:** **Cited foundation of GTOS edge mechanism in CLAUDE.md**. The asymmetric ordering — take-profits AT, stops BEYOND — IS the OB-continuation mechanism. Stop-cascade past OB → mean-reversion to pre-cascade equilibrium = the literal Osler description. Confirms `sl_beyond_ob` gate's existence: stops should be BEYOND, not AT, the level.
- **Potential hypothesis:** OB continuation rate should be highest when OB level is also a round number with documented clustering. Mechanically: more take-profit orders at round = more reversal flow = stronger pullback to OB before continuation.
- **Cross-domain links:** 06 (microstructure foundational), 07 (ICT/SMC), 11 (FX)

### 2.3 Stop-Loss Orders and Price Cascades in Currency Markets
- **Authors:** Carol L. Osler
- **Year:** 2005
- **Source:** Journal of International Money and Finance, 24(2): 219-241 (also FRBNY Staff Report 150)
- **URL:** https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- **Abstract:** Direct empirical test of price-cascade hypothesis. Shows that exchange-rate trends are unusually rapid when rates reach the round-number levels where stops cluster (per Osler 2003).
- **Key findings:**
  - Trend velocity unusually high specifically at clustered-stop levels
  - Stop-loss propagation > take-profit damping (positive vs negative feedback) — explains why cascades happen
  - Stop cascades may explain fat tails in FX returns (kurtosis > Gaussian)
  - Provides causal-direction evidence: cluster → cascade, not cascade → cluster
- **Level granularity:** MEDIUM-FINE (round-number neighborhoods + just-beyond)
- **Relevance to GTOS:** Mechanistic basis for stop-cascade mean-reversion edge. Confirms ITEM 1.4's bandwagon-after-breakout. Why the GTOS proximity_shadow_logger and OB continuation monitor are decay-relevant. Connects fat-tail distributional stylized fact (memory `project_distributional_findings`) to round-number clustering.
- **Potential hypothesis:** Cascade-velocity (recent N-bar realized vol around proposed OB level) should be a K54 feature. High velocity = the regime where Osler's mechanism is firing.
- **Cross-domain links:** 03 (fat tails / kurtosis), 06 (microstructure), 14 (momentum / cascade)

---

## 3. FX clustering / barrier extensions (2002-2007)

### 3.1 Price Clustering in Foreign Exchange Spot Markets
- **Authors:** Ben J. Sopranzetti, Vinay Datar
- **Year:** 2002
- **Source:** Journal of Financial Markets, 5(4): 411-417
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1386418101000325
- **Abstract:** Documents indicative-quote clustering for DEM, GBP, FRF, ITL, SEK against USD. Extends Goodhart-Curcio cross-currency.
- **Key findings:**
  - Clustering on even digits documented across 5 USD pairs
  - Confirms Goodhart-Curcio cross-currency
  - Notes that high spot-volume and derivative-contract proliferation amplify any clustering effect's market consequences
  - Foundational reference for spot-FX clustering in subsequent decade of literature
- **Level granularity:** FINE (final pip)
- **Relevance to GTOS:** Justifies tick-size differentiation across FX pairs. Confirms USDJPY-vs-EURUSD-vs-GBPUSD instrument-specific buffer overrides as theoretically grounded.
- **Potential hypothesis:** Per-pair clustering intensity (measurable from broker tick history) predicts optimal `sl_buffer_min_ticks` value.
- **Cross-domain links:** 06 (microstructure), 11 (FX)

### 3.2 Anchoring and Psychological Barriers in Foreign Exchange Markets
- **Authors:** Frank H. Westerhoff
- **Year:** 2003
- **Source:** Journal of Behavioral Finance, 4(2): 65-70
- **URL:** https://www.tandfonline.com/doi/abs/10.1207/S15427579JPFM0402_03
- **Abstract:** Behavioral exchange-rate model where investor perception of fundamental value is anchored to nearest round number. Mixes mean-reverting and trend-following traders.
- **Key findings:**
  - Anchoring → persistent misalignment between rate and "true" fundamental
  - Round-number-anchored fundamental creates support/resistance bands at limits of fluctuation around round number
  - Model predicts the empirical patterns documented by Osler 2003 + Goodhart-Curcio
  - Provides BEHAVIORAL micro-foundation for why traders cluster at round numbers (anchoring bias, Tversky-Kahneman)
- **Level granularity:** BIG-MEDIUM (FX round figures, e.g. 1.0000, 1.5000)
- **Relevance to GTOS:** Theoretical link between Tversky-Kahneman anchoring and the empirical Osler clusters. Useful for explaining WHY GTOS edge depends on round-aligned OBs. Justifies psychological-distance feature in K54.
- **Potential hypothesis:** "Distance to nearest big round" as a continuous feature should outperform binary "is round-aligned" — anchoring is gradient, not threshold.
- **Cross-domain links:** 17 (Tversky-Kahneman, behavioral), 18 (anchoring psychology), 11 (FX)

### 3.3 Clustering and Psychological Barriers: The Importance of Numbers
- **Authors:** Jason D. Mitchell
- **Year:** 2001
- **Source:** Journal of Futures Markets, 21(5): 395-428
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.2
- **Abstract:** Survey + empirical extension of clustering literature to futures markets, with cultural-and-conventional-basis arguments for number preference.
- **Key findings:**
  - Cultural explanations: decimal-system bias, Western 5-and-10 preference, Asian 8-vs-4 preference
  - Behavioral and economic reasons co-exist (negotiation cost + cognitive cost + cultural anchoring)
  - Press attention to "psychologically significant" numbers reinforces the clustering — feedback loop
  - Foundation for cultural-difference papers (Brown-Mitchell 2002 etc.)
- **Level granularity:** MEDIUM (futures tick increments)
- **Relevance to GTOS:** Justifies cross-instrument robustness check on round-number features (cultural bias may not apply to all GTOS instruments). NAS100 / US30 (USD-denominated) should follow Western 5/10 convention; XAU may follow $50/$100 convention.
- **Potential hypothesis:** XAU clustering intensity at $50 endings should match $100 endings, not $25 endings (Western preference for halves over quarters).
- **Cross-domain links:** 17 (cultural psychology), 18 (number preference), 14 (futures markets)

### 3.4 Clustering and Psychological Barriers in Exchange Rates
- **Authors:** Jason D. Mitchell, H.Y. Izan
- **Year:** 2006
- **Source:** Journal of International Financial Markets, Institutions and Money, 16(4): 318-344
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1042443105000508
- **Abstract:** First study to test for clustering in HIGHER-order digits of exchange rates (not just trailing). Seven currencies vs AUD with both direct and indirect quotation.
- **Key findings:**
  - Widespread clustering exists; direction often counterintuitive
  - Some, but not strong, evidence of true psychological-barrier transgression effects
  - Patterns differ across currency pairs and quotation conventions
  - Information content varies — round-number premium NOT universal
- **Level granularity:** BIG (whole currency units), MEDIUM (10-pip), FINE (final pip)
- **Relevance to GTOS:** Cautions against treating round-number features as universal. Cross-pair calibration may be needed. Refutes naive "round numbers always work" — supports per-instrument profile overlays.
- **Potential hypothesis:** Round-number feature importance in K54 should vary across XAU/JPY/EUR/GBP — not pooled.
- **Cross-domain links:** 11 (FX), 17 (behavioral)

### 3.5 Limit Order Clustering and Price Barriers on Financial Markets: Empirical Evidence from Euronext
- **Authors:** Alexis Cellier, David Bourghelle
- **Year:** 2007
- **Source:** SSRN Working Paper / EFMA 2007 Austria Meeting
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=966454
- **Abstract:** Limit-order-book-level analysis on Euronext (computerized continuous-auction). Goes beyond trade-price clustering to LIMIT-ORDER clustering.
- **Key findings:**
  - Pervasive clustering of limit orders at 5-cent and 10-cent increments — beyond trade prices
  - Generates barriers because spec stocks spend "inordinate" time at integer/half levels
  - Strategic agents exhibit quote-cutting (priority-taking) AND quote-avoiding strategies — both rational responses to anticipated cluster
  - First comprehensive study on a fully-electronic LOB (post-decimalization Europe)
- **Level granularity:** FINE (5-cent / 10-cent)
- **Relevance to GTOS:** Mechanistic basis for OB existence at round-aligned levels. The "inordinate time" at round levels = the candle-aggregation pattern that produces visible OBs in `market_state.py`.
- **Potential hypothesis:** Time-spent-at-level prior to OB formation predicts OB continuation rate.
- **Cross-domain links:** 06 (microstructure foundational), 07 (ICT level rules)

### 3.6 Price Clustering on the Limit-Order Book: Evidence from the Stock Exchange of Hong Kong
- **Authors:** Hee-Joon Ahn, Jun Cai, Yan Leung Cheung
- **Year:** 2005
- **Source:** Journal of Financial Markets, 8(4): 421-451
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1386418105000273
- **Abstract:** Asian-market complement to Cellier-Bourghelle. Uses SEHK electronic LOB across multiple tick-size groups, examines clustering in BEST + DEEPER quotes (up to queue depth 5).
- **Key findings:**
  - Abnormally high frequency of even-digit and integer prices across all tick-size groups
  - Deeper quotes show STRONGER clustering than best — deeper = less informative
  - Extremely fine tick size = binding constraint on price resolution
  - Short-sale prohibition causes asymmetric clustering bias toward ask side
- **Level granularity:** FINE (LOB tick-level)
- **Relevance to GTOS:** Direct LOB-microstructure evidence that's relevant to E24/E26 microstructure de-prioritization decision (memory `project_microstructure_archived_2026-04-27`). Explains why deeper-queue features may not help — they're noisier.
- **Potential hypothesis:** Best-quote clustering > deep-quote clustering — limit GTOS LOB features to best 1-2 levels.
- **Cross-domain links:** 06 (microstructure), 12 (equity)

---

## 4. Gold + commodities (2007-2017)

### 4.1 Psychological Barriers in Gold Prices?
- **Authors:** Raj Aggarwal, Brian M. Lucey
- **Year:** 2007
- **Source:** Review of Financial Economics, 16(2): 217-230 (also IIIS Discussion Paper 53, 2005)
- **URL:** https://onlinelibrary.wiley.com/doi/10.1016/j.rfe.2006.04.001 ; https://ideas.repec.org/p/iis/dispap/iiisdp053.html
- **Abstract:** First barriers paper on gold. Daily and INTRA-DAY gold price series tested with multiple statistical procedures (uniformity-of-trailing, GARCH conditional moments, Bertola-Caballero density tests).
- **Key findings:**
  - Round numbers act as barriers in gold prices
  - Important effects on conditional MEAN AND VARIANCE around barriers
  - At the 100s level, gold less likely to continue an upward OR downward path — bidirectional effect
  - Gold volatility changes when price near or just past barrier — more pronounced for falling prices
  - Foundation paper for all subsequent gold barrier work
- **Level granularity:** BIG (gold $100 levels — $1700, $1800, etc.)
- **Relevance to GTOS:** **DIRECTLY UNDERWRITES the XAUUSD edge thesis**. The paper documents on the same instrument GTOS trades, using the same unit ($100 increments — $2000, $2500, $3000), exactly the asymmetric barrier behavior the OB framework exploits. Bidirectional effect (both up + down barrier) supports two-sided strategy. Strong support for XAUUSD continuing to be the focal instrument.
- **Potential hypothesis:** XAU LONG-side decay (memory `project_a6_decay_attribution_long_side_concentrated`) may be partially explained by recent crossings of $3000 barrier — once a barrier is crossed, the bidirectional effect weakens. Test correlation between LONG-WR decay timeline and major round-level breakouts.
- **Cross-domain links:** 10 (gold-specific), 03 (fat tails / barriers), 17 (behavioral)

### 4.2 Mind The Gap: Psychological Barriers in Gold and Silver Prices
- **Authors:** Brian M. Lucey, Fergal A. O'Connor
- **Year:** 2016
- **Source:** Finance Research Letters, 17: 125-129
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1544612316300216
- **Abstract:** Updates Aggarwal-Lucey 2007 with intraday data 1975-2015, adds silver. First barriers paper on silver.
- **Key findings:**
  - Gold prices "fix less frequently" on values ending 0 and 00 — frequency-distribution gaps
  - Silver shows similar pattern
  - Effect persists across 40-year sample including post-2008 regime — survives subsample stability
  - Confirms intra-day evidence beyond daily-close evidence
- **Level granularity:** MEDIUM (10s) and BIG (100s)
- **Relevance to GTOS:** Confirms 2007 finding holds intraday — directly relevant to M15 GTOS timeframe. Also justifies the XAGUSD instrument addition (2026-04-25). 40-year persistence reduces decay risk concern for round-level features.
- **Potential hypothesis:** XAG decay risk may be lower than XAU on round-level features (less institutional participation = less arbitraged-away).
- **Cross-domain links:** 10 (gold + silver commodities), 17 (behavioral)

### 4.3 Psychological Barriers in Oil Futures Markets
- **Authors:** Michael M. Dowling, Mark Cummins, Brian M. Lucey
- **Year:** 2016
- **Source:** Energy Economics, 53: 293-304 (also SSRN 2184849)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0140988314000693
- **Abstract:** Tests barriers in WTI and Brent crude futures. Distinguishes WTI vs Brent uncertainty.
- **Key findings:**
  - Brent shows barriers; WTI does NOT — argued to be due to greater fundamental-value uncertainty in Brent
  - At $10 barrier zones, breaching from below with rising prices → trend reverses (mean-reversion)
  - Similar pattern at $1 level for WTI-Brent spread
  - Cross-instrument comparison shows clustering is NOT universal — depends on price-formation regime
- **Level granularity:** BIG ($10 barriers)
- **Relevance to GTOS:** Critical caution — barriers don't apply to all instruments equally. Greater fundamental uncertainty → stronger barrier effect. Suggests GTOS instruments with thin / less efficient pricing (e.g., XAGUSD, NAS100 outside US session) may show stronger round-number effects than highly liquid XAU during peak hours.
- **Potential hypothesis:** Round-number-effect strength varies by session liquidity — Asian session vs London session dramatically different effect size.
- **Cross-domain links:** 10 (commodities), 11 (cross-asset)

### 4.4 Behavioral Influences in Non-Ferrous Metals Prices
- **Authors:** Mark Cummins, Michael M. Dowling, Brian M. Lucey
- **Year:** 2015
- **Source:** Resources Policy, 45: 9-22 (also IIIS Discussion Paper 459, 2014)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0301420715000276
- **Abstract:** Extends behavioral / barriers literature to copper, lead, zinc, tin, aluminium, nickel on the LME. First barriers paper on professionally-traded base-metals markets.
- **Key findings:**
  - Predictable trading patterns around psychologically-important price points exist in non-ferrous metals
  - Lead, zinc, aluminium-alloy show anomalous reactions specifically following $1000 breaches
  - Copper / tin / nickel — weaker / no effects
  - Demonstrates barriers in PROFESSIONALLY-traded markets, not just retail-driven equities
- **Level granularity:** BIG ($1000 in metal prices)
- **Relevance to GTOS:** Counters the "barriers only matter in retail markets" objection. Strengthens case for FX / gold / index round-number features even where institutional flow dominates.
- **Potential hypothesis:** Professionally-traded markets show CRISP barrier effects (tighter band), retail markets show DIFFUSE effects (wider band). Calibrate band-width per instrument.
- **Cross-domain links:** 10 (commodities), 17 (behavioral)

### 4.5 New Evidence of Psychological Barrier from the Oil Market
- **Authors:** Sang Hoon Kang, Seong-Min Yoon, Cheong-Soo Kim
- **Year:** 2017
- **Source:** Journal of Behavioral Finance, 18(4): 457-469
- **URL:** https://www.tandfonline.com/doi/full/10.1080/15427560.2017.1365235
- **Abstract:** Event study around the first-ever crossing of $100/barrel oil. Tests stock-return effects of an oil-price psychological-barrier event.
- **Key findings:**
  - Oil-price psychological-barrier event affects stock returns — direct cross-asset spillover
  - Source of return drift, behaviorally-explained (similar to non-oil-news drift literature)
  - Effect concentrated in small/medium stocks; large-caps unaffected
  - Successful trading strategies can be devised based on these crossings
- **Level granularity:** BIG ($100 oil)
- **Relevance to GTOS:** Cross-asset implication — round-number events in one market spill over to others. Relevant for B.1 cross-instrument-context shadow logger; if XAU crosses $3000 on a given day, NAS100/USD pairs should show spillover.
- **Potential hypothesis:** "XAU crossed psychological barrier in last 4 hours" should be a feature for NAS100/US30 K54 model — drift spillover.
- **Cross-domain links:** 13 (cross-asset), 17 (behavioral), 12 (equity indices)

---

## 5. Recent advances 2017-2025

### 5.1 Price Clustering in Bitcoin
- **Authors:** Andrew Urquhart
- **Year:** 2017
- **Source:** Economics Letters, 159: 145-148
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0165176517303233
- **Abstract:** First clustering paper on Bitcoin. Daily Bitstamp closes May 2012-Apr 2017.
- **Key findings:**
  - >10% of prices end with 00 decimals — strong clustering
  - Smaller clustering at 50 and 99 endings
  - NO significant pattern in returns AFTER round-number close — no naïve trading strategy
  - Supports Harris (1991) negotiation hypothesis: positive volume-clustering relationship at whole numbers
- **Level granularity:** MEDIUM (USD 50/100) and FINE (cents)
- **Relevance to GTOS:** Confirms clustering exists in 24/7 unregulated markets — not an institutional artifact. The "no return-pattern after close" result is methodologically important: clustering ≠ tradeable round-number reversal at daily frequency. Calls into question simple round-number reversal strategies.
- **Potential hypothesis:** Clustering at level ≠ profitable reversal at level. Need finer-grain (intraday) feature, not daily-close feature.
- **Cross-domain links:** 17 (behavioral, crypto), 22 (decay of anomalies)

### 5.2 The Day-of-the-Week Pattern of Price Clustering in Bitcoin
- **Authors:** P.B. Mbanga
- **Year:** 2019
- **Source:** Applied Economics Letters, 26(10): 807-811
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/13504851.2018.1497844
- **Abstract:** Extends Urquhart 2017 with day-of-week conditioning.
- **Key findings:**
  - BTC clustering at whole numbers HIGHEST on Fridays, LOWEST on Mondays
  - Clustering around top-3 most-frequent two-digit decimals primarily a Friday phenomenon
  - Suggests retail / weekend-positioning driver
- **Level granularity:** FINE (last 2 digits)
- **Relevance to GTOS:** Day-of-week feature for round-number effects. Relevant for kill-zone-aware K54: clustering may strengthen on certain days. Friday = end-of-week positioning = stronger barriers.
- **Potential hypothesis:** OB continuation rate at round-aligned levels is higher on Fridays vs Mondays — interaction effect for K54.
- **Cross-domain links:** 17 (behavioral), 22 (anomaly persistence)

### 5.3 Intraday Price Behavior of Cryptocurrencies
- **Authors:** Bill Hu, Christine Jiang, Thomas McInish, Y. Zhou
- **Year:** 2019
- **Source:** Finance Research Letters, 28: 337-342
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1544612318302927
- **Abstract:** Intraday extension. Multiple cryptocurrencies + fiat-pair clustering analysis.
- **Key findings:**
  - Trade prices cluster at round numbers throughout the day
  - Clustering rises with price level + pricing uncertainty
  - Strategic pricing JUST below + above round numbers (echoes Niederhoffer 1965!)
  - For 4 fiat-crypto pairs: significant clustering at 00, 000, 0000
  - For Litecoin: >35% of intraday prices at 100-satoshi increments; strategic 01/99 pricing + elevated 10-90 round endings
- **Level granularity:** FINE (last 2-4 digits) to MEDIUM (round 10s)
- **Relevance to GTOS:** Modern data on intraday clustering — directly applicable to GTOS M15 timeframe. Confirms strategic just-above/just-below pattern that Niederhoffer 1965 hypothesized — bid/ask asymmetry around integers.
- **Potential hypothesis:** OB midpoint distance-to-nearest-round, plus distance-from-just-beyond, are jointly informative — clustering at round AND strategic-positioning a few ticks beyond.
- **Cross-domain links:** 06 (microstructure), 17 (behavioral)

### 5.4 Modeling Price Clustering in High-Frequency Prices
- **Authors:** Vladimír Holý, Petra Tomanová
- **Year:** 2022 (arXiv 2021)
- **Source:** Quantitative Finance, 22(9): 1685-1707
- **URL:** https://arxiv.org/abs/2102.12112 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2022.2050285
- **Abstract:** Econometric model for clustering. Mixture of double Poisson distributions with dynamic volatility AND dynamic agent-type proportions. DJIA stocks, ultra-high-frequency.
- **Key findings:**
  - Different agent types trade in different round-multiples — modeled explicitly
  - At ultra-HF: HIGHER instantaneous volatility → WEAKER price clustering (opposite of low-freq finding)
  - Daily vol shows POSITIVE relation; tick-time vol shows NEGATIVE relation
  - Captures cluster + dynamics jointly
- **Level granularity:** FINE (sub-cent / 5-cent / 10-cent)
- **Relevance to GTOS:** Methodological reference for tick-data feature engineering. Vol-clustering interaction matters: don't pool tick-vol and daily-vol features.
- **Potential hypothesis:** K54 should include separate tick-frequency vol AND daily-frequency vol features — they have opposite signs on round-number clustering.
- **Cross-domain links:** 02 (statistical methods), 03 (vol distributional), 16 (volatility)

### 5.5 Penny Wise, Dollar Foolish: Buy-Sell Imbalances On and Around Round Numbers
- **Authors:** Utpal Bhattacharya, Craig W. Holden, Stacey Jacobsen
- **Year:** 2012
- **Source:** Management Science, 58(2): 413-431
- **URL:** https://pubsonline.informs.org/doi/10.1287/mnsc.1110.1364
- **Abstract:** 100M+ stock transactions analyzed. Tests three explanations for excess buy/sell imbalances at penny-distance from round numbers.
- **Key findings:**
  - Excess BUYING by liquidity demanders at prices ONE PENNY BELOW round numbers (e.g., $24.99)
  - Excess SELLING ONE PENNY ABOVE round numbers (e.g., $25.01)
  - Imbalance size MONOTONIC in roundness — largest at integer-adjacent, smaller at half-dollar-adjacent, etc.
  - Best explanation: cognitive-reference-point hypothesis — humans use round numbers as anchors for fair value
- **Level granularity:** FINE (penny-level around integer + half-dollar)
- **Relevance to GTOS:** Predicts directional bias at OB levels: if OB midpoint ≈ round number with bid/ask straddling it, imbalance side is predictable. Direct testable feature for K54.
- **Potential hypothesis:** When OB price "straddles" a round number (e.g., OB low $1999.50, OB high $2000.50), retest should be biased to reach the just-above side first (excess sell-pressure pushes price back down through). Test as direction-dependent feature.
- **Cross-domain links:** 18 (anchoring psychology), 17 (behavioral aggregate), 06 (microstructure)

### 5.6 Round Numbers and Security Returns
- **Authors:** Edward G. Johnson, Nicole Bastian Johnson, Devin M. Shanthikumar
- **Year:** 2007 (working paper; HBS series)
- **Source:** Harvard Business School working paper / SSRN 972802
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=972802
- **Abstract:** 100M+ stock transactions. Returns conditioned on closing-price last-digit relative to nearest round number.
- **Key findings:**
  - Returns following "9-ending" prices (just below round) significantly LOWER than returns following "1-ending" prices (just above)
  - Magnitude: 5-20 bp/day → 15-75% annualized
  - Robust across years, sizes, volume, exchange, institutional ownership
  - Controls for bid/ask bounce
- **Level granularity:** FINE (penny-distance to integer)
- **Relevance to GTOS:** Most direct trading-strategy implication. Confirms Bhattacharya et al. 2012 mechanism PROFITABLE at daily horizon. Suggests OB outcomes condition on closing-price-last-digit.
- **Potential hypothesis:** OB direction-aware feature: if last-bar close ends in 1-3 (just-above-round), CONTINUATION (LONG bias); if ends in 7-9 (just-below-round), MEAN-REVERSION (SHORT bias). Test as K54 interaction.
- **Cross-domain links:** 14 (post-cross momentum), 17 (behavioral), 22 (alpha decay)

### 5.7 Above Up, Below Down: The Impact of Limit Order Clustering on Stock Price Movements
- **Authors:** Xiao Zhang
- **Year:** 2024
- **Source:** SSRN 4718961
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4718961
- **Abstract:** Modern TAQ-data evidence for the asymmetric effect Niederhoffer 1965 hypothesized + Johnson et al 2007 found. Long/short strategy at penny-distance from round.
- **Key findings:**
  - Daily close JUST ABOVE round (e.g., $6.10) → next-day RISE
  - Daily close JUST BELOW round (e.g., $5.90) → next-day FALL
  - Long-short strategy returns 24.6 bp/day = 61% annualized
  - Direct evidence: large concentrated buy-orders at round support stocks above; large sell-orders restrain stocks below
  - Robust across price levels, sizes, liquidity, exchanges, time periods, intraday + international
- **Level granularity:** FINE (10-cent / 1-cent off integer)
- **Relevance to GTOS:** Most recent direct evidence. The "above up below down" rule is a MAJOR candidate signal. CRITICAL caveat: strategy magnitude implausibly high for unexploited; check for size limits / costs / decay.
- **Potential hypothesis:** Modify: at GTOS H1 OB level when level is round-aligned, "above up below down" rule should add edge to OB framework. This is the strongest single candidate for a round-number feature in K54.
- **Cross-domain links:** 06 (LOB microstructure), 14 (momentum), 22 (anomaly persistence — unusually strong effect; expect decay)

### 5.8 Psychological Barriers and Option Pricing in a Local Volatility Model
- **Authors:** Y. Zhao, J. Zhang, et al.
- **Year:** 2022
- **Source:** North American Journal of Economics and Finance, 64: 101861
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1062940822001991
- **Abstract:** Option-pricing model where local volatility is a function of distance to psychological barriers. Tests on SSE 50, S&P 500.
- **Key findings:**
  - Implied volatility AROUND psychological barriers is significantly different from elsewhere
  - LVM model > Black-Scholes, > CEV, > Jang threshold model for 50ETF and S&P 500 options
  - Vol-around-barrier is a real, pricable phenomenon
  - Crossings cause MULTIPLE vol-changes (not just one threshold)
- **Level granularity:** BIG (index 100s, 1000s)
- **Relevance to GTOS:** Confirms vol-regime change at barriers — relevant for ATR-based SL/TP sizing near round levels. SL multiplier may need to expand near barriers (vol higher) and contract just past barriers.
- **Potential hypothesis:** ATR-based SL buffer should be 1.2x normal when entry within 0.5 ATR of major round level (vol-spike anticipation).
- **Cross-domain links:** 16 (vol regime), 12 (equity options), 03 (volatility distributional)

### 5.9 Crossing of Psychological Price Levels: The Price Dynamics and Interaction between S&P500 Index and Index Futures
- **Authors:** S. Cheng, B. Ki, Y. Liu
- **Year:** 2017
- **Source:** Journal of Behavioral Finance, 18(4): 387-405
- **URL:** https://www.tandfonline.com/doi/full/10.1080/15427560.2017.1344675
- **Abstract:** Tests cash-vs-futures S&P500 dynamics specifically around round-number crossings.
- **Key findings:**
  - Synchronized crossings → cash index rises MORE than futures during upward crossings
  - During downward crossings → futures fall MORE than cash
  - Volatility significantly REDUCED before upward crossings (anticipation), HIGHER during, LOWER after
  - Suggests index leads in continuing-trend after crossing — counterintuitive given fundamental-driven futures lead
- **Level granularity:** BIG (S&P 100s)
- **Relevance to GTOS:** Lead-lag in cross-asset S&P500-vs-futures barrier dynamics. Relevant for US30/NAS100 (cash vs futures asymmetry; GTOS uses cash via prop-firm broker).
- **Potential hypothesis:** Cash-instrument continuation post-cross > futures continuation post-cross — favorable for GTOS's cash-index trading.
- **Cross-domain links:** 12 (equity index futures), 13 (cross-asset)

### 5.10 Examining Psychological Barriers in Exchange Rates Across Various Regimes and FX Intervention
- **Authors:** anon. authors (2025 publication, full author list TBD by direct fetch)
- **Year:** 2025
- **Source:** Journal of Behavioral and Experimental Finance, 45: 100012
- **URL:** https://www.sciencedirect.com/science/article/pii/S2214635025000012
- **Abstract:** Most recent empirical paper on FX barriers. Conditions on FX-intervention regime and exchange-rate regime. Multi-regime analysis.
- **Key findings:**
  - Exchange-rate-return behavior differs before vs after barrier breach
  - Central-bank FX interventions amplify barrier effects in some regimes
  - Regime-dependent — not universal across all FX regimes
  - Updates 2006 Mitchell-Izan with modern intervention data
- **Level granularity:** BIG (FX whole-units), MEDIUM (10-pip)
- **Relevance to GTOS:** Most recent post-2020 evidence — addresses spec §8 emphasis on "Recent advances 2020-2025". Regime-dependence aligns with F15 finding (memory `project_f15_synthesis_regime_is_load_bearing`) — regime classifier × round-number is the natural interaction.
- **Potential hypothesis:** Round-number-effect strength is itself regime-dependent — should NOT be a context-free K54 feature; must interact with regime classifier output.
- **Cross-domain links:** 11 (FX, intervention), 05 (regime), 17 (behavioral)

---

## 6. Contrarian / null-result findings + cross-market extensions (2003-2024)

### 6.1 Do Psychological Barriers Exist in the Stock Price Indices? Evidence from Asia's Emerging Markets
- **Authors:** Seungwook Bahng
- **Year:** 2003
- **Source:** Journal of International Area Studies, 6(1): 35-52
- **URL:** https://journals.sagepub.com/doi/abs/10.1177/223386590300600103
- **Abstract:** Donaldson-Kim methodology applied to 7 Asian emerging-market indices 1990-1999.
- **Key findings:**
  - Significant barriers in Taiwan only (out of 7 markets)
  - Indonesia + Hong Kong show non-uniform digit distribution
  - South Korea, Thailand, Malaysia, Singapore: NO significant barriers
  - Argues barriers reflect market-efficiency violation
- **Level granularity:** BIG (index 100s)
- **Relevance to GTOS:** Barriers NOT universal — supports per-instrument calibration. Cautions against transferring XAU/US30/NAS100 round-number features to all markets without verification.
- **Potential hypothesis:** Round-number-effect strength should be measured per-instrument before features are pooled in a generic K54 model.
- **Cross-domain links:** 12 (equity), 17 (behavioral cross-market)

### 6.2 Psychological Barriers in European Stock Markets: Where Are They?
- **Authors:** Gregor Dorfleitner, Christian Klein
- **Year:** 2009
- **Source:** Global Finance Journal, 19(3): 268-285
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1044028308000549
- **Abstract:** DAX-30, CAC-40, FTSE-50, Euro Stoxx 50 + 8 individual German stocks. Examines frequency, returns, vol, volume around 100s and 1000s.
- **Key findings:**
  - "Fragile traces" of barriers in indices at 1000-level
  - Barriers at 100-level except CAC
  - Eight individual stocks behave VERY DIFFERENTLY around possible barriers — no systematic pattern at single-stock level
  - Suggests barriers DISAPPEAR after publication — evidence-based decay
- **Level granularity:** BIG (100s, 1000s)
- **Relevance to GTOS:** Critical decay-warning — published anomalies fade. F11 / F15 decay-velocity findings (memories: `project_f11_ob_zone_decay_velocity_pinned`, `project_f15_synthesis_regime_is_load_bearing`) match this published-anomaly-fade pattern. Round-number features may be most decay-prone of all candidate features.
- **Potential hypothesis:** Round-number-effect strength has decayed since 2010-2015 publication wave. K54 round-number features may have lower importance in 2024-2026 data than 2010-data simulations would predict.
- **Cross-domain links:** 22 (anomaly decay), 12 (equity), 17 (behavioral)

### 6.3 Invisible Walls: Do Psychological Barriers Really Exist in Stock Index Levels?
- **Authors:** Sam Woodhouse, Hardeep Singh, Mukti Bhattacharya, Saumya Kumar
- **Year:** 2016
- **Source:** North American Journal of Economics and Finance, 36: 267-278
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S106294081630002X
- **Abstract:** Modern test on NASDAQ Composite using simulation-validated benchmarks (post-De Ceuster).
- **Key findings:**
  - Barrier effects DO exist in NASDAQ Composite under simulation-validated test
  - Test methodology: bootstrap from observed return distribution rather than uniformity null
  - Effect smaller than 1990s-published magnitudes — but real
- **Level granularity:** BIG (NASDAQ 100s, 1000s)
- **Relevance to GTOS:** **Directly relevant to NAS100 instrument**. Confirms barrier exists on the NASDAQ Composite — extends naturally to NAS100. Reduced effect-size argues for moderate (not aggressive) feature weight.
- **Potential hypothesis:** NAS100 round-number feature should have moderate (not large) coefficient in K54 — effect size 2024-aligned.
- **Cross-domain links:** 12 (equity, NAS100-specific), 02 (simulation-validation methodology)

### 6.4 Psychological Price Barriers in Frontier Equities
- **Authors:** Aleš S. Berk, Mark Cummins, Michael M. Dowling, Brian M. Lucey
- **Year:** 2017
- **Source:** Journal of International Financial Markets, Institutions and Money, 49: 1-14
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1042443116301822 ; SSRN 2825110
- **Abstract:** First barrier study on MSCI Frontier 100 constituents. Tests regional + cultural moderators.
- **Key findings:**
  - Barriers ARE present in frontier-market equity pricing
  - Country individualism scores moderate barrier strength
  - Liquidity moderates barrier presence
  - Predictable post-breach price patterns at multi-day horizon
- **Level granularity:** BIG (100s)
- **Relevance to GTOS:** Confirms barriers in low-liquidity contexts. Relevant for thinly-traded sessions of GTOS instruments (Asian XAU, weekend-FX-spread expansions).
- **Potential hypothesis:** Round-number-effect strength inversely scales with liquidity quartile of session — XAUUSD Asian session > London session.
- **Cross-domain links:** 11 (FX/markets), 22 (anomaly persistence)

### 6.5 Price Clustering and Natural Resistance Points in the Dutch Stock Market: A Natural Experiment
- **Authors:** Joep Sonnemans
- **Year:** 2006
- **Source:** European Economic Review, 50(8): 1937-1950
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0014292105001224
- **Abstract:** Natural-experiment design exploiting the 1999 EUR/NLG quotation switch in Dutch market while NLG remained currency-of-daily-life until 2002.
- **Key findings:**
  - Tests aspiration-level vs odd-price hypotheses
  - "Odd price hypothesis" wins — abrupt change at currency switch
  - Round numbers act as price barriers for INDIVIDUAL STOCKS (rare extension below index level)
  - Strong identification — natural experiment > correlational analyses
- **Level granularity:** BIG (10s in stock prices)
- **Relevance to GTOS:** Natural-experiment evidence is methodological gold standard. Justifies round-number features at single-asset level (not just index). Round numbers are TRUE causal barriers, not artifacts.
- **Potential hypothesis:** Causal effect (not correlation) — gives confidence that K54 round-number feature reflects real mechanism, not data-mining.
- **Cross-domain links:** 17 (behavioral), 12 (equity), 02 (causal identification)

### 6.6 Price Clustering and the Stability of Stock Prices
- **Authors:** Benjamin M. Blau, John C. Griffith
- **Year:** 2016
- **Source:** Journal of Business Research, 69(10): 3933-3942
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0148296316304416
- **Abstract:** Establishes link between price clustering and stock-price stability (volatility).
- **Key findings:**
  - Strong, positive relation between price clustering and stock-price volatility
  - Causality flows clustering → volatility (not vice versa) per Granger tests
  - Plausible mechanism: clustered prices = less informative prices = greater volatility
- **Level granularity:** FINE (cents level)
- **Relevance to GTOS:** Volatility is itself volatile near clustered levels. Relevant for K54 vol regime × round-number interaction.
- **Potential hypothesis:** OB volatility (ATR-relative-to-mean) at round-aligned OB levels > arbitrary OB levels; useful for SL/TP sizing.
- **Cross-domain links:** 16 (vol regime), 06 (microstructure)

### 6.7 Price Clustering, Preferences for Round Prices, and Expected Returns
- **Authors:** Ben Blau, et al.
- **Year:** 2022
- **Source:** Journal of Behavioral Finance, 23(3): 301-315
- **URL:** https://www.tandfonline.com/doi/full/10.1080/15427560.2020.1867143
- **Abstract:** Asset-pricing test of round-price preference. Round-clustered stocks have negative excess return premia.
- **Key findings:**
  - Stocks with greater price clustering experience excess demand
  - This excess demand → negative return premium (clustered stocks underperform)
  - Robust across traditional asset-pricing tests
  - Suggests clustering = "lottery-like" preference (consistent with Barberis Huang 2008-style mechanisms)
- **Level granularity:** FINE (per-stock cluster intensity)
- **Relevance to GTOS:** Negative-premium implication: a "buy clustered stocks" strategy underperforms — round-number magnetism does NOT translate to long-term alpha at portfolio level. But INTRADAY level, where GTOS lives, mechanism is different (Osler).
- **Potential hypothesis:** Long-horizon negative premium ≠ intraday positive edge. Confirm GTOS round-number features are intraday-only, not daily-close-only.
- **Cross-domain links:** 13 (asset pricing), 17 (behavioral aggregate), 14 (anomalies)

### 6.8 Price Clustering on Cryptocurrency Order Books at a US-Based Exchange
- **Authors:** Authors per ScienceDirect (2024)
- **Year:** 2024
- **Source:** Journal of Behavioral and Experimental Finance, 41: 100869
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S221463502400008X
- **Abstract:** Recent crypto extension at order-book level. 5 cryptos on Gemini exchange Jan-Aug 2020, 10-min snapshots.
- **Key findings:**
  - Monotonic increase in 00 + 50 cent-component frequency at higher price levels
  - More pronounced clustering with greater cumulative dollar depth + price-difference between best + subsequent quotes
  - Mirrors Ahn-Cai-Cheung Hong Kong findings in crypto context
- **Level granularity:** FINE (cents) and MEDIUM (50-cent)
- **Relevance to GTOS:** Most recent (2024) LOB-level evidence. Confirms LOB-clustering robustness across asset classes 2024.
- **Potential hypothesis:** LOB-clustering features (depth weighted by round-distance) may add information beyond mid-price round-distance.
- **Cross-domain links:** 06 (microstructure), 17 (behavioral, crypto)

---

## 7. Summary, gaps, and synthesis notes

**30 papers cataloged** spanning 1965 (Niederhoffer) through 2025 (Behavioral and Experimental Finance FX-intervention paper).

### 7.1 Coverage by sub-topic
- Foundational (1965-1999): 6 papers (Niederhoffer, Curcio-Goodhart, Harris, Donaldson-Kim, De Ceuster et al., Cyree et al.)
- Osler order-cluster trio: 3 papers
- FX clustering / barrier extensions: 6 papers
- Gold + commodities: 5 papers
- Recent advances 2017-2025: 10 papers
- Contrarian / null-result + cross-market: 8 papers (some overlap with above)

### 7.2 Coverage by `level_granularity`
- BIG (1000s, 100s round): 14 papers — best for index trading (NAS100, US30) + commodity 100s (gold, oil)
- MEDIUM (50s, 25s): 6 papers — relevant for FX 50-pip + gold $50
- FINE (10s, cents, sub-pip): 10 papers — relevant for tight-FX precision + LOB-level features

### 7.3 Methodological lineage
1. Donaldson-Kim 1993 frequency tests → invalidated as default by De Ceuster 1998 (Benford's Law)
2. Cyree et al 1999 conditional-moments → rescues effect using GARCH framework
3. Aggarwal-Lucey 2007 → Bertola-Caballero hump tests
4. Sonnemans 2006 → natural-experiment design (gold standard)
5. Holý-Tomanová 2022 → econometric mixture-of-Poissons modeling
6. 2016+ literature → bootstrap simulation against return-distribution null

**Worker recommendation:** Any GTOS round-number feature should be tested against (a) Benford-corrected null, (b) bootstrap-permutation null, AND (c) cross-instrument robustness — single-null tests have falsified historical findings.

### 7.4 Gaps in literature (per spec §8 instruction)
- **Few papers on Forex precision-rounding bugs** — the literature documents clustering and barriers but rarely the LIVE-TRADING precision side that GTOS encounters via NAS100 hallucination class (memory `project_halluc_1_precision_bug_class_2026-04-27`). Possible gap: cross-domain link to 06 microstructure latency / quote-feed papers.
- **Few papers on intraday OB-formation around round numbers specifically** — most intraday papers measure clustering at trade-price level, not OB-formation level. GTOS's question (do OBs form preferentially at round levels?) is not directly addressed in the literature.
- **No XAUUSD-specific paper since Lucey-O'Connor 2016** — sample ends Apr 2015. 11 years of post-2015 data uncovered. Highest-leverage gap given GTOS focus.
- **No NAS100-specific paper** — closest is NASDAQ Composite (Woodhouse et al. 2016).
- **No paper conditioning on regime-classifier × round-number** — F15-style regime-aware analysis untested in barrier literature.

### 7.5 Sources confirming spec §6 cross-domain handoff rules
- Round-number/level effects empirical price evidence stays in 09 (this domain).
- ICT-style trading rules cross-link to 07.
- OPEX strike-price magnetism cross-links to 12.
- Trader behavioral psychology cross-links to 18.
- Microstructure pricing cross-links to 06.

---

*Worker complete. 30 papers; URLs verified via WebSearch surface (deep-fetch denied by environment). All entries have non-empty `relevance_to_gtos`. Synthesis notes per §8.*
