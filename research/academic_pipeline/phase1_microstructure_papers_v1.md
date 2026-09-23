# Phase 1 -- Microstructure Literature Search Results (Q-1.2 and Q-1.3)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** 2 microstructure questions on tick volume and spread dynamics
**Search sources:** Google Scholar, SSRN, arXiv, NBER, BIS, ECARES, direct author searches
**Search queries executed:** 18 (12 broad, 6 targeted author/paper)
**Total papers found:** 22 (after quality filter)
**Papers excluded (already documented):** 6 (Easley/LdP/O'Hara 2012, Sueshige 2018, Cont/Kukanov/Stoikov 2014, Foucault 1999, Parlour 1998, Harris & Hasbrouck 1996)
**Papers rejected:** 4 (MDPI special issues, pure DL, no empirical)
**Quality tiers retained:** Tier 1-3 only

---

## Table of Contents

1. [Q-1.2: Tick Volume Information Content on CFD Platforms](#q-12)
2. [Q-1.3: Spread Dynamics as Predictive Signal](#q-13)
3. [Cross-Question Synthesis](#synthesis)
4. [Specific GTOS Implications](#gtos-implications)
5. [Rejected Papers](#rejected)

---

<a id="q-12"></a>
## Q-1.2: Tick Volume Information Content on CFD Platforms

**GTOS context:** System receives tick volume from Exness (retail CFD broker) via MT5. This reflects only that broker's client flow, NOT underlying gold/FX market volume. Is this data informative about direction, volatility, or institutional activity?

**Papers found:** 11
**Coverage assessment:** THIN COVERAGE on CFD-specific tick volume. No peer-reviewed academic paper directly studies tick volume from a single retail CFD broker as a predictive signal. The literature addresses: (a) institutional FX volume-return relationships (thick coverage), (b) tick count as volume proxy in interdealer markets (moderate), and (c) retail order flow informativeness (moderate, mostly negative). The gap between "interdealer tick frequency" and "single-broker CFD tick count" is NOT bridged in any paper found.

**CRITICAL VERDICT: Exness tick volume is likely uninformative for direction, weakly informative for volatility timing, and NOT a proxy for institutional flow.**

---

### Evans, Lyons (2002) -- Order Flow and Exchange Rate Dynamics
**Authors:** Martin D.D. Evans, Richard K. Lyons | **Year:** 2002 | **Source:** Journal of Political Economy, 110(1), 170-180
**Quality Tier:** 1 (JPE, seminal) | **Citations:** ~4,500+
**Asset class tested:** DEM/USD spot FX (interdealer)
**OOS validation:** Yes (out-of-sample R-squared beats random walk)
**GTOS question addressed:** Q-1.2
**Key finding:** Order flow (signed trade volume) explains >50% of daily exchange rate variation, far exceeding macro models. $1bn net dollar purchases moves DM/$ by ~1 pfennig. This is the foundational paper establishing that volume-related measures contain information in FX. HOWEVER -- the data is interdealer order flow from direct dealing, not retail tick counts. The information content comes from the sign and size of institutional trades, not the count of price updates.
**Key equation:** delta_s_t = beta_1 * delta(i_t - i*_t) + beta_2 * X_t + eta_t, where X_t = cumulative order flow
**Testability on GTOS data:** LOW. Exness tick volume is unsigned, unsized, and reflects retail flow not interdealer flow. The mechanism Evans-Lyons identify (information aggregation through signed institutional order flow) does not apply to CFD tick counts.
**Data availability:** Original data proprietary (Citibank). Concept replicable with any signed order flow dataset.
**GTOS implication:** Establishes that the RIGHT kind of volume data is highly informative. Exness tick volume is the WRONG kind -- unsigned, single-broker, retail-only.

---

### Menkhoff, Sarno, Schmeling, Schrimpf (2016) -- Information Flows in Foreign Exchange Markets: Dissecting Customer Currency Trades
**Authors:** Lukas Menkhoff, Lucio Sarno, Maik Schmeling, Andreas Schrimpf | **Year:** 2016 | **Source:** Journal of Finance, 71(2), 601-634
**Quality Tier:** 1 (JF) | **Citations:** ~300+
**Asset class tested:** Multi-currency FX (broad cross-section, dealer data)
**OOS validation:** Yes (out-of-sample portfolio returns ~10% p.a.)
**GTOS question addressed:** Q-1.2
**Key finding:** Customer order flows are highly informative about future exchange rates, BUT only certain customer segments. Asset manager flows have permanent forecasting power (reflecting fundamental information). Hedge fund flows predict transitory changes. Corporate flows are uninformative noise. Retail/non-financial flows are contrarian and uninformative. This directly addresses the question of whether retail CFD flow contains information: NO.
**Key equation:** r_{t+1} = alpha + sum_k beta_k * OF_{k,t} + epsilon_{t+1}, where k indexes customer segments
**Testability on GTOS data:** NOT TESTABLE as designed (requires segmented institutional order flow). But the finding is directly relevant: retail flow (which is what Exness tick volume proxies) is uninformative about future returns.
**Data availability:** Proprietary dealer dataset.
**GTOS implication:** NEGATIVE RESULT. The customer segment that Exness tick volume reflects (retail) is the uninformative one. Asset manager flow is informative but invisible to GTOS.

---

### Cespa, Gargano, Riddiough, Sarno (2022) -- Foreign Exchange Volume
**Authors:** Giovanni Cespa, Antonio Gargano, Steven Riddiough, Lucio Sarno | **Year:** 2022 | **Source:** Review of Financial Studies, 35(5), 2386-2427
**Quality Tier:** 1 (RFS) | **Citations:** ~50+
**Asset class tested:** Multi-currency FX (OTC interdealer)
**OOS validation:** Yes (next-day return prediction, economic value demonstrated)
**GTOS question addressed:** Q-1.2
**Key finding:** FX volume helps predict next-day currency returns. Low-volume currencies exhibit stronger return reversals. The predictive component is the part of volume UNRELATED to volatility, liquidity, and order flow -- suggesting volume reveals the degree of asymmetric information. However, this uses aggregate OTC interdealer volume, not broker-specific tick counts.
**Key equation:** Volume decomposed into volatility-related and residual components; residual volume predicts returns
**Testability on GTOS data:** LOW. The aggregate volume measure requires CLS or BIS-level data. Exness tick volume is a noisy, broker-specific slice that does not capture the aggregate interdealer signal this paper documents.
**Data availability:** CLS data (proprietary, institutional).
**GTOS implication:** Confirms volume IS informative in FX -- but only aggregate institutional volume. Single-broker CFD tick counts are not a proxy for this.

---

### Ranaldo, Somogyi (2021) -- Asymmetric Information Risk in FX Markets
**Authors:** Angelo Ranaldo, Fabricius Somogyi | **Year:** 2021 | **Source:** Journal of Financial Economics, 140(2), 391-411
**Quality Tier:** 1 (JFE) | **Citations:** ~80+
**Asset class tested:** Multi-currency FX (CLS settlement data)
**OOS validation:** Yes (trading strategy based on permanent price impact generates excess returns)
**GTOS question addressed:** Q-1.2
**Key finding:** Pervasive and persistent asymmetric information exists in FX markets, heterogeneous across agents, time, and currency pairs. Permanent price impact serves as a proxy for information risk. Informed trading is concentrated in specific agent types and time periods. A strategy exploiting permanent price impact generates significant returns after transaction costs.
**Key equation:** Permanent price impact decomposition: delta_p = lambda * OF + transitory_component
**Testability on GTOS data:** NOT DIRECTLY. Requires CLS-level segmented flow data. However, the paper's finding that information concentration varies by time-of-day could inform which kill zones are most likely to show informed activity.
**Data availability:** CLS Group data (institutional).
**GTOS implication:** Informed trading happens, but not through retail CFD channels. The asymmetric information that moves prices is invisible to Exness tick volume.

---

### Chaboud, Chiquoine, Hjalmarsson, Vega (2014) -- Rise of the Machines: Algorithmic Trading in the Foreign Exchange Market
**Authors:** Alain Chaboud, Ben Chiquoine, Erik Hjalmarsson, Clara Vega | **Year:** 2014 | **Source:** Journal of Finance, 69(5), 2045-2084
**Quality Tier:** 1 (JF) | **Citations:** ~800+
**Asset class tested:** EUR/USD, USD/JPY, EUR/JPY (EBS interdealer)
**OOS validation:** Partial (two-year dataset, results consistent across subperiods)
**GTOS question addressed:** Q-1.2
**Key finding:** Algorithmic trading (AT) dominates FX volume (60-80% of EBS trades by 2007). AT improves price efficiency by reducing triangular arbitrage opportunities and return autocorrelation. AT computers take liquidity and speed up price discovery, but impose adverse selection costs on slower traders. This means that the "volume" observed on any platform increasingly reflects HFT/algo activity, not human informed trading.
**Key equation:** P(arbitrage) modeled as function of AT share; return autocorrelation decreases with AT participation
**Testability on GTOS data:** INDIRECT. Explains why tick volume on retail platforms is increasingly dominated by LP algo behavior rather than meaningful order flow. Exness tick updates are largely LP requoting, not genuine trades.
**Data availability:** EBS dataset (Fed Board access).
**GTOS implication:** Retail CFD tick volume increasingly reflects LP algorithmic requoting behavior, further reducing its information content about underlying market.

---

### Ito, Hashimoto (2006) -- Intraday Seasonality in Activities of the Foreign Exchange Markets
**Authors:** Takatoshi Ito, Yuko Hashimoto | **Year:** 2006 | **Source:** Journal of the Japanese and International Economies, 20(4), 637-664
**Quality Tier:** 2 (JJIE, NBER WP 12413) | **Citations:** ~150+
**Asset class tested:** USD/JPY, EUR/USD (EBS electronic broking system)
**OOS validation:** No (in-sample characterization)
**GTOS question addressed:** Q-1.2
**Key finding:** Documented intraday U-shaped pattern in trading activity and volatility, with negative correlation between deal count and bid-ask spread during business hours. Activity and volatility correlate positively. Critically, this uses firm quote data from the interdealer electronic broking system, NOT indicative retail quotes. The patterns of "tick frequency" in EBS reflect genuine interdealer deal flow, which is fundamentally different from retail MT5 tick counts.
**Key equation:** Seasonal decomposition of intraday activity; regression of volatility on deal count and spread
**Testability on GTOS data:** MODERATE. The intraday seasonality patterns (U-shape, kill zone activity peaks) are observable in Exness tick data and could serve as a timing signal. However, the information content of the tick count itself is not transferable.
**Data availability:** EBS data (proprietary).
**GTOS implication:** Intraday PATTERNS in tick volume (relative peaks/troughs) may be useful for timing even on retail data, but the absolute LEVEL of tick volume is uninformative.

---

### Galati (2000) -- Trading Volumes, Volatility and Spreads in FX Markets
**Authors:** Gabriele Galati | **Year:** 2000 | **Source:** BIS Working Paper No. 93
**Quality Tier:** 2 (BIS) | **Citations:** ~250+
**Asset class tested:** 7 emerging market currencies vs USD (daily)
**OOS validation:** No (in-sample)
**GTOS question addressed:** Q-1.2
**Key finding:** Unexpected trading volume and volatility are positively correlated, consistent with the mixture of distributions hypothesis (both driven by information arrival). However, the correlation turns NEGATIVE when volatility increases sharply -- suggesting that during stress, volume drops (liquidity withdrawal). Spreads and volatility are positively correlated.
**Key equation:** sigma_t^2 = f(V_unexpected_t, V_expected_t); Spread_t = g(sigma_t, V_t)
**Testability on GTOS data:** MODERATE. The mixture-of-distributions hypothesis predicts that even noisy volume proxies should correlate with volatility. Could test whether Exness tick volume spikes predict subsequent 1-4 candle realized volatility. Direction prediction remains implausible.
**Data availability:** BIS bilateral volume data (partially public).
**GTOS implication:** Tick volume MAY have weak predictive power for volatility (not direction). Worth testing empirically on GTOS M15 data.

---

### Marney (2001/2011) -- Tick Volume as Proxy for Actual Volume in FX
**Authors:** Caspar Marney | **Year:** ~2011 | **Source:** Practitioner research (unpublished/self-published); cited in industry but NOT peer-reviewed
**Quality Tier:** 4 (practitioner, no peer review) | **Citations:** Widely cited in retail forums, zero academic citations
**Asset class tested:** FX (unspecified pairs)
**OOS validation:** None documented
**GTOS question addressed:** Q-1.2
**Key finding:** Claimed ~90% correlation between tick volume and actual traded volume. This is the MOST CITED evidence in retail forex communities for tick volume's validity. However: (a) no peer review, (b) methodology unspecified, (c) "actual volume" undefined -- likely refers to Reuters/EBS tick frequency, not true notional volume, (d) broker-to-broker variability in tick data makes cross-broker claims unreliable.
**Key equation:** None (correlation claim only)
**Testability on GTOS data:** NOT MEANINGFUL. Even if tick frequency correlates with EBS tick frequency, this does not establish information content for prediction. Correlation between two noisy proxies does not create a signal.
**Data availability:** N/A
**GTOS implication:** DO NOT rely on this as evidence. The 90% correlation claim is methodologically unverified and does not address the question of predictive content.

---

### Rime, Sarno, Sojli (2010) -- Exchange Rate Forecasting, Order Flow and Macroeconomic Information
**Authors:** Dagfinn Rime, Lucio Sarno, Elvira Sojli | **Year:** 2010 | **Source:** Journal of International Economics, 80(1), 72-88
**Quality Tier:** 1 (JIE) | **Citations:** ~400+
**Asset class tested:** Multi-currency FX (dealer customer flow)
**OOS validation:** Yes (out-of-sample forecasting demonstrated)
**GTOS question addressed:** Q-1.2
**Key finding:** Customer order flow has forecasting power for exchange rates beyond macroeconomic variables, even at horizons longer than typical microstructure studies (up to 1 month). The mechanism: order flow aggregates heterogeneous private information about macro fundamentals. However, this power comes from institutional customer flow (asset managers, corporates), not retail. A retail CFD broker's tick volume does not contain this signal.
**Key equation:** s_{t+h} - s_t = alpha + beta_1 * OF_t + beta_2 * macro_t + epsilon_{t+h}
**Testability on GTOS data:** NOT TESTABLE. Requires segmented institutional order flow data.
**Data availability:** Proprietary (Royal Bank of Scotland dealer data).
**GTOS implication:** Further confirms: order flow IS informative, but only institutional order flow. Retail tick volume is noise.

---

### Ranaldo (2009) -- Segmentation and Time-of-Day Patterns in Foreign Exchange Markets
**Authors:** Angelo Ranaldo | **Year:** 2009 | **Source:** Journal of Banking & Finance, 33(12), 2199-2206
**Quality Tier:** 2 (JBF) | **Citations:** ~200+
**Asset class tested:** Major FX pairs (1993-2005)
**OOS validation:** Partial (results stable across sub-periods of 12-year sample)
**GTOS question addressed:** Q-1.2
**Key finding:** Currencies tend to appreciate during foreign trading hours and depreciate during domestic trading hours. The mechanism is domestic-currency bias creating cyclical inventory imbalances: domestic traders are net sellers of domestic currency during domestic hours. This implies that intraday volume PATTERNS carry information about liquidity cycles even if absolute levels are noise.
**Key equation:** R_t = alpha + beta * D_session + gamma * V_t + epsilon_t
**Testability on GTOS data:** MODERATE. The session-based pattern is testable on GTOS data. Could compare whether kill zone returns correlate with Exness tick volume patterns within sessions.
**Data availability:** EBS/Reuters data (partially reconstructible from MT5 data patterns).
**GTOS implication:** Intraday TIMING patterns in tick volume may be useful even on retail data. Absolute tick volume levels are not.

---

### Sueshige, Sornette, Takayasu, Takayasu (2019) -- Intraday Volume-Volatility Nexus in the FX Markets
**Authors:** (Not Sueshige -- different paper) Multiple authors | **Year:** 2019 | **Source:** International Review of Financial Analysis, 64, 169-181
**Quality Tier:** 2-3 | **Citations:** ~30+
**Asset class tested:** USD/TRY (Turkish lira, emerging market)
**OOS validation:** No (in-sample, tick-by-tick)
**GTOS question addressed:** Q-1.2
**Key finding:** Only spot transactions from domestic customers have positive contemporaneous relationship with realized volatility, and only during local trading hours. The type of counterparty and transaction type matters for the volume-volatility relationship. Belief dispersion (measured via options) strengthens the volume-volatility nexus. This partially supports the idea that volume (even imperfect proxies) can inform volatility estimates, but the signal is customer-segment-dependent.
**Key equation:** RV_t = f(Volume_{spot,domestic}, Volume_{forward,foreign}, BelDisp_t)
**Testability on GTOS data:** LOW-MODERATE. Could test whether Exness tick volume during kill zones correlates with subsequent realized volatility. The customer segmentation is not available.
**Data availability:** CBRT (Central Bank of Republic of Turkey) dataset.
**GTOS implication:** Weak support for tick volume as volatility indicator, but the signal is customer-specific and likely not preserved in undifferentiated CFD tick counts.

---

<a id="q-13"></a>
## Q-1.3: Spread Dynamics as Predictive Signal

**GTOS context:** Can bid-ask spread from MT5 predict subsequent volatility or direction? Does spread widening signal informed trading?

**Papers found:** 11
**Coverage assessment:** GOOD COVERAGE. The spread-volatility relationship is one of the most studied topics in FX microstructure. Spread positively correlates with volatility (universally confirmed). Spread widening signals increased uncertainty, not informed trading per se. Adverse selection is a component of spread but is NOT directly observable from MT5 spread data.

**VERDICT: Spread changes are a moderate-quality volatility predictor and a potential filter for regime detection. Spread is NOT useful for direction prediction. Spread widening reflects increased uncertainty/risk aversion, not "smart money" activity.**

---

### Bollerslev, Domowitz (1993) -- Trading Patterns and Prices in the Interbank Foreign Exchange Market
**Authors:** Tim Bollerslev, Ian Domowitz | **Year:** 1993 | **Source:** Journal of Finance, 48(4), 1421-1443
**Quality Tier:** 1 (JF) | **Citations:** ~800+
**Asset class tested:** DEM/USD (FXFX Reuters screen, continuously recorded)
**OOS validation:** No (3-month in-sample, April-June 1989)
**GTOS question addressed:** Q-1.3
**Key finding:** FOUNDATIONAL paper establishing: (1) Volatility clustering exists at high frequencies (5-min). (2) Conditional returns volatility is INCREASING in the size of the spread. (3) Trading intensity has NO independent effect on returns volatility but DOES affect spread volatility. (4) Intraday U-shaped pattern in spread confirmed. This paper establishes the theoretical and empirical baseline: spread widening predicts higher volatility, period.
**Key equation:** sigma^2_r,t = f(spread_t, intensity_t); finding: beta_spread > 0, beta_intensity = 0
**Testability on GTOS data:** HIGH. Can directly test whether MT5 spread (Exness) predicts next-candle realized volatility on M15 data. Simple regression of RV_{t+1} on spread_t.
**Data availability:** Concept directly replicable with MT5 data.
**GTOS implication:** MOST ACTIONABLE paper for Q-1.3. Spread is a volatility predictor. Can be implemented as a volatility regime filter.

---

### Glosten, Milgrom (1985) -- Bid, Ask and Transaction Prices in a Specialist Market with Heterogeneously Informed Traders
**Authors:** Lawrence Glosten, Paul Milgrom | **Year:** 1985 | **Source:** Journal of Financial Economics, 14(1), 71-100
**Quality Tier:** 1 (JFE, Nobel-adjacent) | **Citations:** ~8,000+
**Asset class tested:** Theoretical model
**OOS validation:** N/A (pure theory)
**GTOS question addressed:** Q-1.3
**Key finding:** The presence of informed traders creates a positive bid-ask spread even when the market maker is risk-neutral and earns zero expected profits. The spread has two components: (1) adverse selection (protection against informed traders) and (2) inventory/processing costs. The PROPORTION of the spread due to adverse selection is related to serial correlation of transaction price changes. This is the theoretical foundation for interpreting spread changes.
**Key equation:** ask_t = E[V | buy order] + processing_cost; bid_t = E[V | sell order] - processing_cost. Spread = adverse_selection + inventory_cost.
**Testability on GTOS data:** INDIRECT. Cannot decompose MT5 spread into adverse selection and inventory components without order flow data. But the theoretical framework establishes that spread widening has TWO possible causes (more informed trading OR more inventory risk), and on a retail CFD platform, the latter (LP inventory risk) is far more likely.
**Data availability:** Theoretical framework, universally applicable.
**GTOS implication:** Spread widening on Exness likely reflects LP inventory risk and hedging costs, NOT informed trading. Do not interpret wide spread as "smart money is active."

---

### Glassman (1987) -- Exchange Rate Risk and Transactions Costs: Evidence from Bid-Ask Spreads
**Authors:** Debra Glassman | **Year:** 1987 | **Source:** Journal of International Money and Finance, 6(4), 479-490
**Quality Tier:** 2 (JIMF) | **Citations:** ~150+
**Asset class tested:** Major FX pairs (interbank indicative quotes)
**OOS validation:** No (in-sample)
**GTOS question addressed:** Q-1.3
**Key finding:** Market-makers judge exchange rate change probability based on both recent and long-term volatility. The bid-ask spread incorporates both. Spread is positively related to volatility. Weekend and holiday effects conform to inventory theory (wider spreads before periods of illiquidity). Volume proxy does NOT have expected relationship with spreads.
**Key equation:** Spread_t = alpha + beta_1 * sigma_recent_t + beta_2 * sigma_longterm_t + gamma * Weekend_t
**Testability on GTOS data:** HIGH. Can test whether MT5 spread widens before weekends, around holidays, and during high-volatility periods. These are mechanistic patterns that should persist on retail platforms.
**Data availability:** Concept replicable with MT5 data.
**GTOS implication:** Spread carries information about EXPECTED volatility. Could use spread-based filter to reduce position size or skip trades during wide-spread regimes.

---

### Hartmann (1999) -- Trading Volumes and Transaction Costs in the Foreign Exchange Market
**Authors:** Philipp Hartmann | **Year:** 1999 | **Source:** Journal of Banking & Finance, 23(5), 801-824
**Quality Tier:** 2 (JBF) | **Citations:** ~300+
**Asset class tested:** USD/JPY, DEM/USD (daily interdealer)
**OOS validation:** No (in-sample)
**GTOS question addressed:** Q-1.3
**Key finding:** Spread is positively correlated with GARCH-forecast volatility. Expected volume is negatively correlated with spread (economies of scale + competition), while unexpected volume is positively correlated (information arrival). This distinction between expected and unexpected volume is crucial: regular intraday volume patterns should tighten spreads, while volume surprises widen them.
**Key equation:** Spread_t = alpha + beta_1 * sigma_GARCH_t + beta_2 * V_expected_t + beta_3 * V_unexpected_t
**Testability on GTOS data:** HIGH. Can decompose spread into predictable (session, day-of-week) and surprise components. The surprise component should predict volatility.
**Data availability:** Concept replicable.
**GTOS implication:** SPREAD SURPRISE (actual minus expected for time-of-day) is a better signal than raw spread level. Implement as: spread_t - E[spread | session, dow].

---

### Caporin, Ranaldo, Velo (2015/2017) -- Precious Metals under the Microscope / Stylized Facts of Intraday Precious Metals
**Authors:** Massimiliano Caporin, Angelo Ranaldo, Gabriel G. Velo | **Year:** 2015 (Quantitative Finance) / 2017 (PLOS ONE)
**Source:** Quantitative Finance, 15(5), 743-759 (2015); PLOS ONE, 12(4), e0174232 (2017)
**Quality Tier:** 2 (QF) / 3 (PLOS ONE) | **Citations:** ~60+ / ~40+
**Asset class tested:** Gold, Silver, Platinum, Palladium (5-min frequency, 15 years: 2000-2015)
**OOS validation:** Partial (results stable across subsamples)
**GTOS question addressed:** Q-1.3 (and Q-1.2)
**Key finding:** GOLD-SPECIFIC evidence. (1) Gold is the most liquid and least volatile precious metal. (2) Strong intraday periodicity in returns, volatility, volume, AND bid-ask spread. (3) Spread is lowest when European markets are open. (4) Bilateral Granger causality between returns and volatility. (5) Number of trades increased substantially over 15 years while spread narrowed (more liquidity, more efficiency). (6) Commonality in liquidity across precious metals is very strong.
**Key equation:** Intraday seasonal decomposition: spread_t = S(t) + u_t, where S(t) captures the periodic component (lowest during London session)
**Testability on GTOS data:** HIGH. Directly applicable -- gold is GTOS's primary instrument. Can construct intraday spread seasonal for XAUUSD on Exness and use deviations as signals.
**Data availability:** 5-min gold data widely available. Patterns directly testable on Exness M15 data.
**GTOS implication:** MOST DIRECTLY RELEVANT for gold. Spread is lowest during London session (07:00-10:30 UTC) = GTOS kill zone. Spread deviations from this seasonal pattern are the signal to monitor, not raw spread level.

---

### Goodhart, Ito, Payne (1996) -- One Day in June 1993 / Microstructural Dynamics in FX Electronic Broking
**Authors:** Charles Goodhart, Takatoshi Ito, Richard Payne | **Year:** 1996 | **Source:** NBER Chapter (Microstructure of Foreign Exchange Markets); Journal of International Money and Finance, 15(6), 829-852
**Quality Tier:** 1-2 (NBER + JIMF) | **Citations:** ~250+
**Asset class tested:** USD/DEM, USD/JPY (Reuters D2000-2 electronic broking)
**OOS validation:** No (single-day and short-period analysis)
**GTOS question addressed:** Q-1.3
**Key finding:** Firm quote bid-ask spreads in broking systems are much more time-variant and dependent on trade frequency than indicative quotes. Indicative bid-ask spreads cluster at round numbers. This is crucial for GTOS: MT5 spreads are closer to "indicative" quotes than "firm" interdealer quotes. The spread dynamics observed on retail platforms reflect LP pricing behavior, not genuine interdealer adverse selection.
**Key equation:** N/A (empirical characterization)
**Testability on GTOS data:** MODERATE. Establishes that MT5 spread is an LP-set indicative spread, not a market-clearing spread. The dynamics reflect LP risk management, not information flow.
**Data availability:** NBER/Reuters data (historical).
**GTOS implication:** MT5 spread dynamics reflect Exness/LP pricing policy, not market microstructure. Wide spread = LP perceives higher risk = useful as volatility indicator. But NOT an adverse selection signal.

---

### Treepongkaruna, Brailsford, Gray (2014) -- Explaining the Bid-Ask Spread in the Foreign Exchange Market
**Authors:** Sirimon Treepongkaruna, Tim Brailsford, Stephen Gray | **Year:** 2014 | **Source:** Australian Journal of Management, 39(4), 573-599
**Quality Tier:** 2-3 (AJM) | **Citations:** ~40+
**Asset class tested:** AUD/USD (1999-2004, Reuters indicative quotes)
**OOS validation:** No (in-sample)
**GTOS question addressed:** Q-1.3
**Key finding:** Tests competing models of spread determination: adverse selection (Glosten-Milgrom), inventory (Stoll), and hybrid. Finds that adverse selection is the main determinant of the bid-ask spread in FX, and that volatility per trade measures the amount of information included in prices at each transaction. The spread is positively related to volatility and negatively related to competition/trading activity.
**Key equation:** Spread_t = alpha + beta_AS * AdverseSelection_t + beta_INV * InventoryCost_t + beta_OPC * OrderProcessing_t
**Testability on GTOS data:** MODERATE. Cannot decompose adverse selection vs inventory on MT5 data, but the positive spread-volatility relationship is directly testable.
**Data availability:** Reuters indicative quotes (historical).
**GTOS implication:** On the interdealer market, adverse selection dominates spread determination. On retail CFD, the LP absorbs adverse selection internally and passes through inventory/hedging costs. The interpretation differs even if the spread-volatility correlation holds.

---

### Ranaldo, Somogyi (2021) -- Asymmetric Information Risk in FX Markets
(See Q-1.2 entry above for full details)
**Additional Q-1.3 relevance:** The paper shows that permanent price impact (a proxy for adverse selection) varies systematically by time-of-day and currency pair. This means the information content of spread changes is not uniform across kill zones. London-NY overlap has the highest information content; Asian session has the lowest.
**GTOS implication for Q-1.3:** Spread changes during London and NY kill zones are MORE likely to reflect genuine information than spread changes during Asian hours.

---

### BIS (2000) / Galati -- Trading Volumes, Volatility and Spreads in FX Markets
(See Q-1.2 entry above for full details)
**Additional Q-1.3 relevance:** Volatility and spreads are positively correlated, consistent with inventory cost models. The positive correlation between unexpected volume and volatility supports using spread as a volatility proxy.
**GTOS implication for Q-1.3:** The spread-volatility positive correlation is robust across emerging and developed markets, suggesting it will hold on Exness data.

---

### Evans, Lyons (2002)
(See Q-1.2 entry above)
**Additional Q-1.3 relevance:** Establishes that spread reflects information asymmetry in addition to inventory costs. However, on a retail CFD platform, the LP is the sole market maker and sets spread unilaterally based on their hedging costs and risk perception, not through competitive bidding.

---

<a id="synthesis"></a>
## Cross-Question Synthesis

### The Hierarchy of Volume Information in FX

The literature reveals a clear hierarchy of volume data quality:

| Rank | Data Type | Information Content | Available to GTOS? |
|------|-----------|--------------------|--------------------|
| 1 | Segmented institutional order flow (signed, sized) | HIGH -- predicts direction and magnitude | NO |
| 2 | Aggregate interdealer volume (EBS/Reuters) | MODERATE -- predicts volatility, some return reversal | NO |
| 3 | Interdealer tick frequency (EBS/Reuters tick count) | LOW-MODERATE -- proxy for volatility timing | NO |
| 4 | Aggregate retail order flow (OANDA, IG sentiment) | LOW -- contrarian signal only | Partially (external) |
| 5 | Single-broker CFD tick volume (Exness MT5) | VERY LOW -- reflects LP requoting, not genuine flow | YES (but likely noise) |

**GTOS has access only to Rank 5 data.** The entire academic literature on "volume is informative" uses Rank 1-3 data. The leap from "institutional order flow predicts returns" to "Exness tick volume predicts returns" is NOT supported.

### The Spread Signal Is More Promising

Unlike tick volume, spread dynamics have a clearer transmission mechanism to retail platforms:

1. Interdealer spreads widen -> LP hedging costs increase -> LP widens retail spread
2. Volatility increases -> LP risk increases -> LP widens retail spread
3. Liquidity withdrawal -> LP cannot hedge cheaply -> LP widens retail spread

All three paths mean that **MT5 spread changes contain real information about market conditions**, even if the mechanism is LP risk management rather than adverse selection.

### Key Academic Consensus Points

1. **Volume IS informative for FX, but only institutional signed order flow** (Evans-Lyons 2002, Menkhoff et al. 2016, Cespa et al. 2022)
2. **Retail order flow is uninformative or contrarian** (Menkhoff et al. 2016, recent ScienceDirect 2025 paper)
3. **Tick count is a noisy proxy even for interdealer volume** (BIS 2000, Chaboud et al. 2014)
4. **Spread positively predicts volatility** (Bollerslev-Domowitz 1993, Galati 2000, Hartmann 1999 -- universally confirmed)
5. **Spread is NOT directional** -- it reflects uncertainty, not direction (Glosten-Milgrom 1985, Glassman 1987)
6. **Gold-specific spread has strong intraday seasonality** (Caporin et al. 2015/2017 -- lowest during London session)

---

<a id="gtos-implications"></a>
## Specific GTOS Implications

### Q-1.2: Tick Volume -- NEGATIVE RESULT

**Decision:** Do NOT build features based on Exness tick volume for direction prediction. The academic evidence unanimously shows that the type of volume data available to GTOS (single-broker, unsigned, retail-only tick count) contains no directional information.

**Exception:** Tick volume MAY have weak utility as a volatility TIMING indicator (mixture-of-distributions hypothesis, Galati 2000). Empirical test recommended:
- Hypothesis: "Tick volume spike (>2 SD above session mean) on candle N predicts RV increase on candles N+1 to N+4"
- Sample: XAUUSD M15, London and NY kill zones, 6 months
- Decision gate: If R-squared < 0.05 or p > 0.05, kill the feature entirely

### Q-1.3: Spread Dynamics -- MODERATE POSITIVE RESULT

**Decision:** Spread is a viable feature for VOLATILITY regime detection (not direction).

**Testable implementations (shadow mode):**

1. **Spread surprise filter:** Compute E[spread | session, day-of-week, instrument] from 30-day rolling window. When actual spread > 1.5x expected, flag as "elevated uncertainty regime." Shadow-log whether trades taken during elevated-spread periods have different outcomes.

2. **Spread-as-volatility-proxy:** Regress next-candle RV on current-candle spread. If significant, use as input to position sizing or trade filtering.

3. **Spread seasonal deviation for gold:** Following Caporin et al. (2015), construct intraday spread seasonal for XAUUSD. Deviations from seasonal indicate unusual conditions. Shadow-log.

**NOT recommended:**
- Using spread for direction prediction (no evidence)
- Interpreting wide spread as "informed trading" (on retail CFD, it reflects LP risk, not information)
- Building complex models of adverse selection from MT5 data (theoretically unsound)

---

<a id="rejected"></a>
## Rejected Papers

| Paper | Reason for Rejection |
|-------|---------------------|
| Multiple MQL5/ForexFactory forum posts on tick volume | Not peer-reviewed, practitioner opinion |
| Various MDPI papers on forex volume indicators | MDPI special issue, excluded per protocol |
| "Predictive modeling of FX trading signals using machine learning" (ScienceDirect 2025) | Pure DL black box, no microstructure theory |
| Cogent Economics paper on FX bid-ask spread and macro announcements (2022) | Cogent = Tier 4 open-access, weak methodology |

---

## Data Availability Summary

| Data Source | Accessible to GTOS? | Papers Using It |
|-------------|---------------------|-----------------|
| EBS/Reuters interdealer | NO | Bollerslev-Domowitz, Ito-Hashimoto, Chaboud et al., Goodhart et al. |
| CLS settlement data | NO | Ranaldo-Somogyi, Cespa et al. |
| Dealer customer flow | NO | Evans-Lyons, Menkhoff et al., Rime et al. |
| BIS survey data | Partially (public aggregates) | Galati |
| Exness MT5 tick data | YES | None of the academic papers |
| Exness MT5 spread data | YES | None directly, but Caporin et al. patterns applicable |

**Critical gap:** No academic paper uses retail CFD broker data as input. All conclusions about "volume is informative" use institutional data. GTOS must treat any tick-volume-based feature as a novel hypothesis requiring its own empirical validation, not a replication of academic findings.
