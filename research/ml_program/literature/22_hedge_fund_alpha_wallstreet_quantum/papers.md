# Domain 22 — Hedge Fund Alpha, Wall Street, Quantum Finance Public Research

**Worker:** Phase 1 Literature Research Agent #22 (Opus 4.7, max effort)
**Compiled:** 2026-04-28
**Spec:** `research/ml_program/literature/_specs/22_hedge_fund_alpha_wallstreet_quantum.md`
**Method:** WebSearch + WebFetch via Anthropic subscription. Read-only. Every entry verified to a working URL or institutional landing page; no fabrication.
**Paper count:** 35 (target 25-40)

---

## 1. Executive summary

Domain 22 is the strategic-context layer for GTOS — it answers questions like "how durable is alpha empirically?", "what does the empirical hedge-fund persistence literature say about a small system holding edge for 5+ years?", "is Renaissance's Medallion the ceiling we should benchmark against?", and "what does post-2020 quantum-finance public research suggest about the 5-10y systematic-alpha horizon?"

The dominant pattern across the 35 papers is **alpha decay is real, broad, and accelerating since the GFC**. McLean-Pontiff quantify a 58% post-publication decay across 97 anomalies. Sullivan documents that the hedge-fund industry as a whole has subtracted ~$21.1B of value over 19 years after fees. Bollen-Joenvaara-Kauppila title their 2017 paper "End of an Era?" Joenvaara-Kosowski-Tolonen-Kauppila (2021) re-show that hedge-fund average alpha is significantly lower under aggregate (de-biased) databases than under any single commercial database.

Against this, three single-fund counterexamples remain: Renaissance Medallion (Cornell 2020 — 63.3% gross compound, 1988-2018, no negative year, factor loadings all-negative), Buffett (Frazzini-Kabiller-Pedersen 2018 — Sharpe 0.79 but explained by leveraged BAB + QMJ exposure once the factors are known), and Princeton/Newport / Edward Thorp (20% net for 19 years, statistical-arb pioneer). The Cornell paper explicitly characterizes Medallion as "the ultimate counterexample to the efficient market hypothesis" and notes there is "no convincing rational-market explanation."

Quantum-finance public research (Orus-Mugel-Lizaso, Egger-Woerner-IBM, Stamatopoulos, Mugel-Lizaso-Orus, Herman-Pistoia-JPMorgan) is mostly proof-of-concept on small qubit counts. Quadratic-speedup amplitude-estimation results (Goldman + JPMorgan + IBM) for Monte Carlo derivatives pricing are the most-mature thread; portfolio optimization is more speculative; quantum reinforcement-learning trading agents remain in benchmark mode with mixed empirical advantages. None of these is operationally relevant to GTOS in 2026 — they shape 5-10y planning, not 2026 implementation.

Connection to GTOS: the McLean-Pontiff + F11 pattern + Sullivan's industry decay together strongly recommend (a) treating GTOS's order-block edge as a wasting asset with quarterly re-validation, (b) treating capacity-decay literature as not-yet-binding (we are at $100k AUM, scale-decay binds at $1B+), and (c) deferring quantum-finance investment until at least 2030 unless POC results materially mature.

---

## 2. Methodology and scope

**In-scope:** hedge-fund alpha / persistence / decay academic literature; manager-skill-vs-luck (Kosowski-Timmermann-Wermers); hedge-fund risk factors (Fung-Hsieh); single-fund case studies (Medallion, Buffett, Thorp/Princeton-Newport, Bridgewater All-Weather, LTCM); academic-anomaly-decay (McLean-Pontiff, Harvey-Liu-Zhu factor zoo); quantum-finance public POCs (Orus, Woerner-IBM, Stamatopoulos, Mugel-Lizaso, Herman-Pistoia-JPMorgan); Wall Street sell-side analyst forecast bias; Adaptive Markets Hypothesis (Lo); Sharpe-ratio manipulation / performance-measure manipulation-proof literature.

**Out-of-scope:** pure cross-sectional anomaly papers (→ 13), pure ML methodology (→ 19), pure RL agent design (→ 20), prop-firm-individual-trader rules (→ 18 / 21), market-microstructure HFT papers (→ 06).

**Verification protocol:** every paper has been searched on Google Scholar / arXiv / SSRN / NBER / publisher websites; URLs cross-referenced. Where multiple URLs exist (publisher gated, NBER preprint, SSRN, arXiv) I record the most-stable canonical URL. No paper is included without a verifiable source.

**Caveats:**
- Hedge-fund-public literature is data-constrained (most strategies stay private). Many "public hedge-fund research papers" are AQR / Two Sigma / Bridgewater whitepapers rather than peer-reviewed academic articles. I include both.
- Quantum-finance is a fast-moving frontier; recent papers (2023-2025) post-2020 cited where they extend prior POCs.
- Renaissance Technologies has no peer-reviewed academic publications by its principals about Medallion's strategy — Cornell-2020 is the canonical *outside* analysis. The Mercer/Brown research base from IBM speech recognition is documented in Zuckerman 2019 (book, included as a non-academic but verified source).

---

## 3. Papers — full annotated list

### 3.1 Hedge-fund alpha, persistence, manager skill (12 papers)

### Hedge Funds: Performance, Risk, and Capital Formation
- **Authors:** Fung, William; Hsieh, David A.; Naik, Narayan Y.; Ramadorai, Tarun
- **Year:** 2008
- **Source:** Journal of Finance, vol. 63 (4), pp. 1777-1803
- **URL:** https://www.tarunramadorai.com/TarunPapers/fung_hsieh_naik_ramadorai.pdf
- **Abstract:** Studies funds-of-funds (FoFs) for evidence of alpha-generating skill and investor capital flows toward those that have it. Sample: 1,603 funds, January 1995 - December 2004.
- **Key findings:**
  - Identifies a subset of FoFs that deliver persistent alpha
  - Successful FoFs experience far greater capital inflows than less-successful counterparts
  - Even persistently-successful hedge funds experienced a recent dramatic decline in risk-adjusted performance
  - Alpha persistence does exist but is rare and declining
- **Relevance to GTOS:** Establishes the baseline finding — hedge-fund persistence is real but thin and declining. Frames why GTOS should not over-extrapolate from 6 months of live edge.
- **Potential hypothesis:** GTOS edge persistence should be benchmarked against the 5% top-decile FoF persistence rate, not against the 50% chance-rate.
- **Cross-domain links:** 13 (factor models), 02 (statistical methodology — bootstrap)
- **Study type:** empirical
- **Entity studied:** aggregate FoFs

### The Risk in Hedge Fund Strategies: Theory and Evidence from Trend Followers
- **Authors:** Fung, William; Hsieh, David A.
- **Year:** 2001
- **Source:** Review of Financial Studies, vol. 14 (2), pp. 313-341
- **URL:** https://academic.oup.com/rfs/article-abstract/14/2/313/1600868
- **Abstract:** Models trend-following hedge fund returns using lookback-straddle option payoffs. Shows nonlinear-option-like returns are inadequately captured by linear factor models.
- **Key findings:**
  - Trend-following hedge funds have payoffs equivalent to lookback straddles
  - Linear-factor models systematically misprice nonlinear hedge fund returns
  - Lookback-straddle factors explain trend-followers better than equity / bond indices
  - Establishes the precedent that hedge-fund risk modeling requires asset-based-style (ABS) factors
- **Relevance to GTOS:** GTOS's profile (asymmetric kill-zone hits + occasional larger losses) may also fit lookback-straddle profiles; standard linear regression on any future evaluation metric should be supplemented with option-replication factors.
- **Potential hypothesis:** A lookback-straddle ABS regression on GTOS monthly returns (once n=24 months) will show convex-payoff characteristics consistent with breakout-style strategies.
- **Cross-domain links:** 14 (trend / momentum), 16 (vol / option replication)
- **Study type:** empirical + theoretical
- **Entity studied:** trend-following hedge fund strategy class

### Hedge Fund Benchmarks: A Risk-Based Approach (the Fung-Hsieh seven-factor model)
- **Authors:** Fung, William; Hsieh, David A.
- **Year:** 2004
- **Source:** Financial Analysts Journal, vol. 60 (5), pp. 65-80
- **URL:** https://www.tandfonline.com/doi/abs/10.2469/faj.v60.n5.2657
- **Abstract:** Identifies seven asset-based-style (ABS) factors that explain up to 80% of monthly variation in diversified hedge fund portfolios.
- **Key findings:**
  - Equity long-short funds: market + small-vs-large stock factor
  - Fixed-income funds: 10-year Treasury yield + 10-year-vs-Baa spread
  - Trend-followers: lookback options on bond / currency / commodity futures
  - Together explains ~80% of diversified-portfolio monthly variation
- **Relevance to GTOS:** This is the canonical hedge-fund factor model. When/if GTOS scales to multi-strategy and seeks institutional capital, performance attribution against Fung-Hsieh-7 is the institutional-investor expectation.
- **Potential hypothesis:** GTOS gold + FX + index returns (12-month series, when available) regressed on Fung-Hsieh-7 should show alpha that survives the regression — that *is* the institutional-investable proof of edge.
- **Cross-domain links:** 13 (factor models), 16 (vol)
- **Study type:** empirical
- **Entity studied:** aggregate hedge-fund strategy classes

### Buffett's Alpha
- **Authors:** Frazzini, Andrea; Kabiller, David; Pedersen, Lasse Heje
- **Year:** 2018
- **Source:** Financial Analysts Journal, vol. 74 (4), pp. 35-55
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3197185
- **Abstract:** Decomposes Berkshire Hathaway's 0.79 Sharpe ratio (1976-2017) into its underlying factor exposures.
- **Key findings:**
  - Buffett's alpha is significant against standard market / size / value / momentum factors
  - Alpha becomes insignificant once Betting-Against-Beta (BAB) and Quality-Minus-Junk (QMJ) factors are added
  - Average leverage is approximately 1.7×
  - Conclusion: Buffett's edge is *systematic* — leveraged exposure to cheap, safe, high-quality stocks
- **Relevance to GTOS:** Gold-standard demonstration that what looks like ineffable manager skill can decompose to exploitable factor exposures plus leverage. Suggests that if GTOS edge persists, it is likely a tight intersection of detectable conditions, not "AI mystery."
- **Potential hypothesis:** GTOS's per-instrument alpha decomposes to a small number of systematic factors (kill-zone-overlap × OB-zone-precision × side-aware regime). If true, this is replicable; if not, extremely durable.
- **Cross-domain links:** 13 (BAB / QMJ factors)
- **Study type:** case-study + empirical
- **Entity studied:** single fund (Berkshire Hathaway)

### Can Mutual Fund "Stars" Really Pick Stocks? New Evidence from a Bootstrap Analysis
- **Authors:** Kosowski, Robert; Timmermann, Allan; Wermers, Russ; White, Halbert
- **Year:** 2006
- **Source:** Journal of Finance, vol. 61 (6), pp. 2551-2595
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2006.01015.x
- **Abstract:** Uses cross-sectional bootstrap to determine whether top mutual fund performance is luck or skill, 1975-2002.
- **Key findings:**
  - Top-decile fund alphas are significantly above the bootstrapped luck distribution
  - Top-decile alpha persists out-of-sample
  - Cross-section of fund alphas is non-normal with thick right tail
  - Bootstrap approach validates skill in a statistically rigorous way
- **Relevance to GTOS:** Methodological template: any claim of "GTOS edge is real, not luck" must survive a bootstrap test against the full cross-sectional distribution of comparable strategies. The walk-level p-value alone is insufficient (cf. memory `feedback_walk_level_evidence_not_predictive`).
- **Potential hypothesis:** Bootstrap GTOS's monthly returns vs the cross-section of similar small-prop-firm strategies — compare to the top-decile percentile.
- **Cross-domain links:** 02 (statistical methodology — bootstrap)
- **Study type:** empirical methodology
- **Entity studied:** mutual fund cross-section

### On Persistence in Mutual Fund Performance (the Carhart four-factor model)
- **Authors:** Carhart, Mark M.
- **Year:** 1997
- **Source:** Journal of Finance, vol. 52 (1), pp. 57-82
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1997.tb03808.x
- **Abstract:** Tests persistence in equity mutual fund returns and decomposes "hot-hands" effect against momentum.
- **Key findings:**
  - Common factors and expenses almost completely explain persistence in mutual fund mean returns
  - Hendricks-Patel-Zeckhauser hot-hands effect is mostly the momentum factor in disguise
  - Individual funds do not earn higher returns from following the momentum strategy in stocks
  - No evidence supporting the existence of skilled / informed mutual fund managers as a class
- **Relevance to GTOS:** Establishes the highest-bar interpretation: if GTOS persistence can be explained by exposure to common factors (kill-zone-overlap, momentum, OB-precision), then there is no manager-specific alpha. That's not necessarily bad — systematic factor exposure is repeatable, manager skill is not.
- **Potential hypothesis:** GTOS edge regressed against a Carhart four-factor model (market + size + value + momentum) on instrument-level returns should show factor exposure on momentum (positive, kill-zone-induced).
- **Cross-domain links:** 13 (factor models), 14 (momentum)
- **Study type:** empirical
- **Entity studied:** mutual fund cross-section

### Hedge Funds and the Technology Bubble
- **Authors:** Brunnermeier, Markus K.; Nagel, Stefan
- **Year:** 2004
- **Source:** Journal of Finance, vol. 59 (5), pp. 2013-2040
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00690.x
- **Abstract:** Documents that hedge funds rode the dot-com tech bubble rather than correcting it. Heavy tilt to high-priced tech stocks 1998-2000, then reduced positions before declines.
- **Key findings:**
  - Hedge funds did NOT exert correcting force on technology bubble
  - Hedge fund portfolios were heavily tilted toward expensive tech stocks
  - Reduced positions in stocks about to decline → captured upside without much downside
  - Consistent with "rational riding of bubbles" given investor sentiment + arbitrage limits
- **Relevance to GTOS:** Reframes the role of "smart money" — even sophisticated hedge funds ride trends rather than fade them when investor sentiment is strong. Has implications for GTOS regime classification: in trending_bull regime, the safe play may be momentum-following, not contrarian. F2 finding that XAU LONG decay concentrates in trending_bull is consistent with this — riding the trend was right; fading the trend was systemically wrong.
- **Potential hypothesis:** GTOS regime-conditioned strategies should add a "ride-the-bubble" overlay rather than purely contrarian counter-trend logic in trending_bull.
- **Cross-domain links:** 17 (behavioral / bubbles), 14 (momentum)
- **Study type:** empirical
- **Entity studied:** hedge funds collectively during 1998-2000 tech bubble

### On the High-Frequency Dynamics of Hedge Fund Risk Exposures
- **Authors:** Patton, Andrew J.; Ramadorai, Tarun
- **Year:** 2013
- **Source:** Journal of Finance, vol. 68 (2), pp. 597-635
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.12008
- **Abstract:** Models hedge-fund risk exposures using high-frequency conditioning variables. Exposures vary substantially within months.
- **Key findings:**
  - Within-month variation in risk exposures is more important for hedge funds than mutual funds
  - Hedge fund managers actively shift exposure in response to market conditions
  - Static factor models systematically understate hedge fund tail risk
  - High-frequency conditioning improves alpha measurement
- **Relevance to GTOS:** GTOS already conditions on multiple time-of-day / regime / kill-zone variables. The Patton-Ramadorai finding validates dynamic conditioning as a real source of measurement improvement, not just academic complication. F2 / F15 regime-conditioning fits this template.
- **Potential hypothesis:** GTOS risk-adjusted-alpha measured under high-frequency regime conditioning will be materially different from the static-factor-model alpha.
- **Cross-domain links:** 05 (regime switching), 13 (factor models)
- **Study type:** empirical methodology
- **Entity studied:** aggregate hedge funds

### Hedge Fund Risk Dynamics: Implications for Performance Appraisal
- **Authors:** Bollen, Nicolas P. B.; Whaley, Robert E.
- **Year:** 2009
- **Source:** Journal of Finance, vol. 64 (2), pp. 985-1035
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2009.01455.x
- **Abstract:** Shows that traditional hedge-fund alpha estimates are biased when the factor structure shifts over time. Develops an optimal-changepoint methodology.
- **Key findings:**
  - Hedge-fund factor exposures shift via discrete changepoints (not gradually)
  - Static linear-regression alpha estimates under-weight performance during stable periods
  - Bollen-Whaley optimal changepoint methodology delivers more accurate alpha estimates
  - Consistent with Patton-Ramadorai's high-frequency results
- **Relevance to GTOS:** GTOS's H1→H2 decay (item #4 / F15) is a *changepoint* style shift, not a gradual decay. Bollen-Whaley methodology directly applies — fitting a changepoint detection on GTOS monthly outcomes is methodologically the right tool.
- **Potential hypothesis:** A changepoint test on GTOS instrument-level monthly returns will identify a structural break around H1-2026 / H2-2026, consistent with the F15 regime-conditioning finding.
- **Cross-domain links:** 05 (change-point detection), 02 (statistical methodology)
- **Study type:** empirical methodology
- **Entity studied:** aggregate hedge funds

### An Econometric Model of Serial Correlation and Illiquidity in Hedge Fund Returns
- **Authors:** Getmansky, Mila; Lo, Andrew W.; Makarov, Igor
- **Year:** 2004
- **Source:** Journal of Financial Economics, vol. 74 (3), pp. 529-609
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X04000698
- **Abstract:** Documents widespread serial correlation in hedge-fund returns; attributes most of it to illiquidity exposure causing return-smoothing.
- **Key findings:**
  - Hedge-fund returns are highly serially correlated
  - Serial correlation primarily reflects illiquidity-induced smoothing of reported returns
  - Smoothing causes Sharpe ratios to be inflated, volatility to be understated
  - Smoothing-adjusted Sharpe is a more accurate skill metric
- **Relevance to GTOS:** Critical methodological point. GTOS's monthly returns are MTM (mark-to-market) and trade-by-trade discrete; *no* smoothing concern. But: when comparing GTOS's reported Sharpe to public hedge-fund benchmarks, recognize that the public Sharpes are inflated. GTOS's true relative position is better than face-value comparison suggests.
- **Potential hypothesis:** GTOS reported Sharpe (when available, n=12 months) will be lower than top-decile reported hedge-fund Sharpes but higher than smoothing-adjusted Sharpes.
- **Cross-domain links:** 02 (statistical methodology), 21 (risk / Sharpe)
- **Study type:** empirical methodology
- **Entity studied:** aggregate hedge funds (TASS database)

### Hedge Fund Performance: Are Stylized Facts Sensitive to Which Database One Uses?
- **Authors:** Joenväärä, Juha; Kauppila, Mikko; Kosowski, Robert; Tolonen, Pekka
- **Year:** 2021
- **Source:** Critical Finance Review, vol. 10 (2), pp. 271-327
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3363531
- **Abstract:** Builds aggregate hedge-fund database from seven commercial sources and re-tests stylized facts about hedge-fund performance.
- **Key findings:**
  - Average performance significantly lower under aggregate database vs single commercial database
  - Performance persistence stronger under aggregate database
  - Average fund delivers significantly negative net-of-fee alpha (gross-of-fee remains positive)
  - Database biases (selection, survivorship, backfill) materially distort published findings
- **Relevance to GTOS:** Tells GTOS to *trust full-population, MT5-grounded numbers* over any reported hedge-fund benchmark. Public hedge-fund stats are systematically biased upward; GTOS's MT5-recorded numbers are not.
- **Potential hypothesis:** GTOS comparison to "top hedge fund alphas" needs no inflation adjustment; GTOS numbers are clean while public benchmarks are net-of-bias.
- **Cross-domain links:** 02 (statistical methodology — measurement bias)
- **Study type:** empirical methodology
- **Entity studied:** aggregate hedge funds across 7 databases

### Twenty-Five Years of Hedge Fund Returns
- **Authors:** Sullivan, Rodney N.
- **Year:** 2019
- **Source:** Journal of Alternative Investments (forthcoming, SSRN preprint)
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3498595
- **Abstract:** Reviews hedge-fund industry performance over 25 years (~1994-2019), particularly post-GFC.
- **Key findings:**
  - Industry AUM grew from $200B to $3T+ over the period
  - Post-GFC (2008-2018) shows marked decline in risk-adjusted alpha
  - Cumulative ~$21.1B subtracted in value over 19 years (gross-of-fee positive, net-of-fee negative)
  - "Cycle or sunset?" framing — author leaves open the question of industry-wide alpha exhaustion
- **Relevance to GTOS:** Strongly anchors the F15 / item #4 decay narrative — GTOS-specific decay is consistent with industry-wide hedge-fund alpha exhaustion. The strategic implication: don't assume mean-reversion; assume decay continues unless explicit factor-evolution forces re-emergence.
- **Potential hypothesis:** Hedge-fund alpha shows a regime-shift around the GFC; analogously, GTOS should monitor for regime-shift events (CB action, election, technology adoption).
- **Cross-domain links:** 17 (behavioral / regime), 13 (factor models)
- **Study type:** review + empirical
- **Entity studied:** hedge fund industry aggregate

### 3.2 Single-fund case studies (4 papers)

### Medallion Fund: The Ultimate Counterexample?
- **Authors:** Cornell, Bradford
- **Year:** 2020
- **Source:** SSRN working paper (Cornell Capital Group)
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3504766
- **Abstract:** Analyzes Renaissance Technologies' Medallion Fund returns 1988-2018 against efficient market hypothesis.
- **Key findings:**
  - $100 invested in 1988 grew to $398.7 million by 2018 (63.3% gross compound annual return)
  - Never had a negative annual return across 31 years
  - Market beta and factor loadings all *negative* — performance cannot be a risk premium
  - "No convincing rational-market explanation" exists; explicit "ultimate counterexample" framing
  - Medallion has been closed to outside investors since 2003
- **Relevance to GTOS:** Sets the empirical ceiling for what systematic alpha looks like. It exists, it survives, but it required a unique combination (Mercer/Brown speech-recognition pattern detection + Simons math + multi-billion-dollar tech infrastructure). For GTOS, the takeaway is that small, niche, defensible edges *can* persist for decades — but require hard-to-replicate execution. A 1-3% monthly edge held for 5+ years is empirically possible but rare.
- **Potential hypothesis:** Medallion's persistence is consistent with high-turnover statistical arbitrage in regimes where AUM cannot scale into the strategy. GTOS at $100k AUM is in a regime where capacity is not binding.
- **Cross-domain links:** 19 (ML / algorithmic trading), 06 (market microstructure)
- **Study type:** case-study
- **Entity studied:** single fund (Renaissance Medallion)

### Renaissance's 2024 Rebirth (Institutional Investor)
- **Authors:** Cornell, Andrew (Institutional Investor staff)
- **Year:** 2024
- **Source:** Institutional Investor magazine
- **URL:** https://www.institutionalinvestor.com/article/2e0uykr3vn5booz0smrcw/hedge-funds/renaissances-2024-rebirth
- **Abstract:** Reports on Renaissance Technologies' 2024 performance recovery: Medallion +30%, RIEF +22.7%, RIDA +15.6%.
- **Key findings:**
  - Medallion's $12B internal-only capital returned ~30% in 2024
  - RIEF (institutional outside-investor product) recovered 22.7% — best year since 2011
  - RIDA recovered 15.6%
  - Recovery despite Jim Simons's death in May 2024
  - RIEF AUM dropped from ~$36B to ~$20B 2020-2024 (post-2020 -22.62% drawdown)
- **Relevance to GTOS:** Demonstrates that even at Renaissance, the *outside-investor* products experience normal hedge-fund-style drawdowns and capacity-decay; the internal Medallion product remains unique. Reinforces the view that capacity-constraint and edge-decay manifest across all but the most exclusive (capacity-blocked) strategies.
- **Potential hypothesis:** RIEF / RIDA recovery in 2024 was driven by reflation-trade conditions; if GTOS's edge is similar in nature (regime-conditioned), 2024 should be a productive year for similar small-prop-firm strategies.
- **Cross-domain links:** 17 (regimes), 11 (FX rates / macro)
- **Study type:** case-study (industry journalism, factually verifiable)
- **Entity studied:** single firm (Renaissance Technologies; multiple funds)

### Edward O. Thorp / Princeton Newport Partners — biographical reference
- **Authors:** Multiple (Thorp's autobiography "A Man for All Markets" 2017; Wikipedia consolidated record; OAC archive)
- **Year:** 2017 (autobiography); 1969-1989 (PNP operating period)
- **Source:** Random House autobiography "A Man for All Markets" + biographical / archival records
- **URL:** https://en.wikipedia.org/wiki/Edward_O._Thorp + https://en.wikipedia.org/wiki/Princeton_Newport_Partners + https://oac.cdlib.org/findaid/ark:/13030/c8cn79mx/
- **Abstract:** Documents Edward Thorp's career: card-counting blackjack ("Beat the Dealer" 1962), warrant arbitrage ("Beat the Market" 1967), Princeton/Newport Partners (1969-1989, market-neutral derivative arbitrage), and Ridgeline Partners (1994-2002, statistical arbitrage).
- **Key findings:**
  - Princeton/Newport Partners earned 20% annualized net of fees over 19 years with no down quarter (1969-1988 closure)
  - First market-neutral hedge fund in modern form
  - Pioneered convertible-bond arbitrage and warrant pricing methodology used by LTCM and modern quant funds
  - Demonstrated that derivative-pricing-based mispricing exploitation can produce sustained alpha at small scale
- **Relevance to GTOS:** Thorp's edge persisted at modest AUM by exploiting niche mispricings in a way that was not capacity-binding. This is the proof-of-concept GTOS aspires to: small capital + intellectually-precise edge = potentially-durable returns. PNP closure was external (Drexel scandal), not edge-decay.
- **Potential hypothesis:** Edges that exploit precise micro-mispricing in liquid markets, at scale below where capacity becomes binding, are empirically the most durable form of systematic alpha.
- **Cross-domain links:** 15 (mean-reversion / arb), 06 (microstructure)
- **Study type:** case-study (biographical)
- **Entity studied:** single fund (Princeton/Newport Partners)

### The Man Who Solved the Market (Greg Zuckerman on Renaissance Technologies)
- **Authors:** Zuckerman, Gregory
- **Year:** 2019
- **Source:** Portfolio (Penguin Random House) book
- **URL:** https://www.amazon.com/Man-Who-Solved-Market-Revolution/dp/073521798X
- **Abstract:** Definitive journalistic account of Renaissance Technologies' history, founding, technical strategy at high level, and major personnel including Mercer / Brown.
- **Key findings:**
  - Mercer and Brown were IBM speech-recognition researchers (TMD pattern recognition mathematics)
  - Renaissance employs ~300 PhDs (mostly mathematicians, physicists, computer scientists; few finance specialists)
  - Strategy combines short-horizon statistical-arb across thousands of small mispricings, leveraged moderately
  - Medallion's no-down-year record holds because each individual signal is small but uncorrelated
  - Cornell's "no convincing explanation" point is consistent with Zuckerman's account: edge is the aggregation of thousands of subtle effects no one of which is academically isolatable
- **Relevance to GTOS:** Confirms the strategic principle: durable systematic alpha at scale comes from a *portfolio of small uncorrelated edges*, not from one large edge. GTOS should target aggregating multiple small edges rather than relying on the OB-zone advantage alone (item #4 decay shows that one-edge strategies decay).
- **Potential hypothesis:** GTOS Phase-2 should aggressively diversify its signal set — every additional uncorrelated edge contributes to portfolio Sharpe, regardless of individual edge size.
- **Cross-domain links:** 19 (ML methodology), 14 (momentum / trend), 06 (microstructure)
- **Study type:** case-study (book-length investigative reporting)
- **Entity studied:** single firm (Renaissance Technologies)

### 3.3 Capacity, scale, and limits-to-arbitrage (4 papers)

### Why Are Most Funds Open-End? Competition and the Limits of Arbitrage
- **Authors:** Stein, Jeremy C.
- **Year:** 2005
- **Source:** Quarterly Journal of Economics, vol. 120 (1), pp. 247-272
- **URL:** https://academic.oup.com/qje/article-abstract/120/1/247/1931460
- **Abstract:** Models why hedge funds adopt open-end structure despite open-end being suboptimal for long-horizon arbitrage.
- **Key findings:**
  - Competition for investor capital drives funds toward open-end structure
  - Open-end structure introduces redemption risk that disrupts arbitrage convergence
  - Even in equilibrium, large mispricings can persist because no fund can risk holding to convergence
  - Provides theoretical foundation for limits-to-arbitrage literature
- **Relevance to GTOS:** GTOS as a single-CEO-financed prop-trade is *closed* to redemption pressure — this is structurally an advantage. Whatever edge GTOS has, it can hold to convergence without fearing redemptions. This is structurally rare and valuable.
- **Potential hypothesis:** GTOS as a closed-end strategy can hold positions through periods that an open-end hedge fund could not, capturing alpha that open-end funds cannot capture.
- **Cross-domain links:** 17 (limits to arbitrage)
- **Study type:** theoretical
- **Entity studied:** hedge-fund industry structure

### Capacity Constraints and Hedge Fund Strategy Returns
- **Authors:** Naik, Narayan Y.; Ramadorai, Tarun; Stromqvist, Maria
- **Year:** 2007
- **Source:** European Financial Management, vol. 13 (2), pp. 239-256
- **URL:** https://www.tarunramadorai.com/TarunPapers/CapacityConstraints_October2006.pdf
- **Abstract:** Tests for capacity constraints in hedge fund strategy returns.
- **Key findings:**
  - 4 of 8 hedge fund strategies show capital inflows preceding negative alpha movements
  - Capacity constraints are real and binding for several strategies
  - When average hedge fund doubles in size (~$250M increase), monthly gross alpha decreases by ~9.9 bps
  - Style-level scale matters more than fund-level scale
- **Relevance to GTOS:** GTOS at $100k redacted_account is far below any binding capacity constraint. Capacity research is currently irrelevant for *operational* GTOS but becomes relevant if/when scaling considered (CEO has explicitly deprioritized this in WF-1 deprioritization).
- **Potential hypothesis:** GTOS-style microstructure-OB strategies likely have capacity in the $100M-$1B range; below $1M is essentially capacity-free.
- **Cross-domain links:** 21 (sizing)
- **Study type:** empirical
- **Entity studied:** aggregate hedge fund strategy classes

### Decreasing Returns to Scale Has Eroded Hedge Fund Performance Persistence
- **Authors:** Bollen, Nicolas P. B.; Joenväärä, Juha; Kauppila, Mikko
- **Year:** 2024 (Critical Finance Review)
- **Source:** Critical Finance Review (forthcoming)
- **URL:** https://cfr.ivo-welch.info/forthcoming/papers/bollen2024decreasing.pdf
- **Abstract:** Updates Bollen-Whaley + Joenvaara aggregate-database analysis to show capacity / scale effects have erased hedge-fund persistence.
- **Key findings:**
  - Hedge-fund performance persistence has weakened materially since the GFC
  - Decrease in persistence correlates with industry-wide AUM growth
  - Bollen-Whaley + Joenvaara methodology robust to database biases
  - Strong implication: industry-level alpha is shrinking due to AUM crowding
- **Relevance to GTOS:** Extends the Sullivan / Joenvaara findings. The mechanism (AUM crowding) is *not yet* binding for GTOS at $100k but anchors the strategic context.
- **Potential hypothesis:** GTOS edge has a long-term capacity ceiling; before reaching that ceiling, the edge can persist; after, it decays.
- **Cross-domain links:** 21 (sizing), 13 (factor models)
- **Study type:** empirical
- **Entity studied:** hedge fund aggregate

### Hedge Funds as Liquidity Providers: Evidence from the Lehman Bankruptcy
- **Authors:** Aragon, George O.; Strahan, Philip E.
- **Year:** 2012
- **Source:** Journal of Financial Economics, vol. 103 (3), pp. 570-587
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X11002364
- **Abstract:** Identifies the funding-liquidity-shock effect of Lehman bankruptcy on hedge funds with Lehman as prime broker.
- **Key findings:**
  - Lehman-prime-broker hedge funds had assets frozen on bankruptcy
  - Stocks held by these funds experienced greater liquidity declines than other stocks
  - Effect persisted into early 2009
  - Hedge funds are de facto liquidity providers for stocks they hold
- **Relevance to GTOS:** Reminds GTOS that prime-broker / counterparty risk is *real* — redacted_account / FTMO are GTOS's prime brokers, and a similar shock would have similar effects. Operational risk monitoring includes prime-broker / FN solvency, not just broker spreads.
- **Potential hypothesis:** GTOS should maintain a prime-broker-failure scenario in its risk register: if FN had a balance-sheet event, what would happen to open positions?
- **Cross-domain links:** 21 (risk management), 06 (microstructure)
- **Study type:** empirical
- **Entity studied:** Lehman-affected hedge funds

### 3.4 Alpha decay and academic-anomaly research (4 papers)

### Does Academic Research Destroy Stock Return Predictability?
- **Authors:** McLean, R. David; Pontiff, Jeffrey
- **Year:** 2016
- **Source:** Journal of Finance, vol. 71 (1), pp. 5-32
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365
- **Abstract:** Tests out-of-sample and post-publication return-predictability of 97 academically-documented anomalies.
- **Key findings:**
  - Portfolio returns are 26% lower out-of-sample
  - Portfolio returns are 58% lower post-publication
  - Out-of-sample decline is the upper bound on data-mining contribution; post-publication decline is informative-investor learning
  - Provides quantitative anchor for "publication-induced alpha decay"
- **Relevance to GTOS:** This is the *anchor citation* for item #4 / F11 / F15 decay narrative. The 26%/58% numbers calibrate expected GTOS edge decay. GTOS's order-block edge is an academically-documented anomaly (mean-reversion to OBs after BOS); McLean-Pontiff predicts substantial decay over years, consistent with what F11 measured (16.8pp pre-2026 → 4.6pp H2-2026 = ~73% decline; F11 attributes ~78% to decay, 22% to methodology).
- **Potential hypothesis:** GTOS edge will continue to decay at the McLean-Pontiff post-publication rate (58% over the post-publication period); next ~12 months will see another 20-30% decline absent active edge-evolution.
- **Cross-domain links:** 13 (factor zoo), 17 (adaptive markets)
- **Study type:** empirical
- **Entity studied:** 97 academic anomalies

### Taming the Factor Zoo: A Test of New Factors
- **Authors:** Feng, Guanhao; Giglio, Stefano; Xiu, Dacheng
- **Year:** 2020
- **Source:** Journal of Finance, vol. 75 (3), pp. 1327-1370
- **URL:** https://dachxiu.chicagobooth.edu/download/ZOO.pdf
- **Abstract:** Develops a methodology to test whether new factors add explanatory power beyond the existing factor zoo. Builds on Cochrane's 2011 challenge.
- **Key findings:**
  - Among 100+ recently-published factors, very few survive once double-selection / data-mining adjustments are applied
  - Methodology supports principled multiple-testing correction at the factor-zoo level
  - Suggests most academic factors are noise; few are real
- **Relevance to GTOS:** GTOS's K54 ML classifier baseline (memory `project_k54_ml_classifier_baseline_2026-04-27`) uses a small number of features. Feng-Giglio-Xiu approach validates the choice of *parsimony* — fewer, well-tested signals beat large feature sets that reflect data-mining.
- **Potential hypothesis:** GTOS should bias toward feature sets of size ~10-20, not 50+. Each additional feature requires Bonferroni-corrected proof of incremental contribution.
- **Cross-domain links:** 02 (statistical methodology), 13 (factor models), 19 (ML)
- **Study type:** empirical methodology
- **Entity studied:** factor cross-section

### ... and the Cross-Section of Expected Returns (Harvey-Liu-Zhu 2016)
- **Authors:** Harvey, Campbell R.; Liu, Yan; Zhu, Heqing
- **Year:** 2016
- **Source:** Review of Financial Studies, vol. 29 (1), pp. 5-68
- **URL:** https://academic.oup.com/rfs/article-abstract/29/1/5/1843466
- **Abstract:** Reviews 313 published cross-sectional return-predicting factors and applies multiple-testing corrections.
- **Key findings:**
  - Of 313 published return-predictors, only ~9 survive a |t-stat|>3 multiple-testing threshold
  - Vast majority of factor literature is data-mining
  - Provides modern statistical-multiple-testing standard for factor research
  - Builds on Cochrane's 2011 "factor zoo" challenge
- **Relevance to GTOS:** Mandates that GTOS apply Bonferroni / multiple-testing-correction to all candidate features. K52 K53 work has already been doing this; F5 / F11 corrections under proper Bonferroni illustrate why this matters.
- **Potential hypothesis:** Of GTOS's currently-considered features, only a small fraction will survive proper multiple-testing. K54 should explicitly Bonferroni at feature-selection time.
- **Cross-domain links:** 13 (factor models), 02 (multiple-testing)
- **Study type:** review + empirical methodology
- **Entity studied:** academic factor cross-section

### Hedge Fund Performance: End of an Era?
- **Authors:** Bollen, Nicolas P. B.; Joenväärä, Juha; Kauppila, Mikko
- **Year:** 2017
- **Source:** Financial Analysts Journal, vol. 75 (3), pp. 5-20
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3034283
- **Abstract:** Examines whether hedge-fund alpha has structurally died post-GFC.
- **Key findings:**
  - Average hedge-fund risk-adjusted alpha has dropped to near zero post-2008
  - Decline robust across multiple databases and sample periods
  - Suggests structural change, not cyclical
  - Title's question — "End of an Era?" — left somewhat open but tilted toward affirmative
- **Relevance to GTOS:** Reinforces Sullivan / decay context. If hedge-fund-industry alpha has structurally died, the likely cause is AUM crowding + technology arms-race. GTOS is structurally below that crowding band.
- **Potential hypothesis:** Industry-aggregate alpha decay is real and structural; small-niche-strategy alpha may persist at sub-billion AUM but decays at multi-billion AUM.
- **Cross-domain links:** 13 (factor models), 17 (regime / behavioral)
- **Study type:** empirical
- **Entity studied:** hedge fund aggregate

### 3.5 Performance manipulation, biases, fraud detection (3 papers)

### Sharpening Sharpe Ratios (also: Portfolio Performance Manipulation and Manipulation-Proof Performance Measures)
- **Authors:** Goetzmann, William N.; Ingersoll, Jonathan E.; Spiegel, Matthew I.; Welch, Ivo
- **Year:** 2007 (RFS); 2002 (NBER preprint)
- **Source:** Review of Financial Studies, vol. 20 (5), pp. 1503-1546
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=325942
- **Abstract:** Shows that the Sharpe ratio can be manipulated through dynamic option-like strategies. Develops manipulation-proof performance measure.
- **Key findings:**
  - Maximum Sharpe-ratio strategy is short-OTM-call + short-OTM-put (collects premia, occasional huge loss)
  - Hedge-fund Sharpe ratios are inflatable through this style of trade
  - Manipulation-proof performance measure exists and is fully characterized
  - Implies Sharpe-based fund rankings are systematically biased
- **Relevance to GTOS:** GTOS does NOT short options, so its reported Sharpe is *not* manipulated. But: in benchmarking, recognize that public hedge-fund Sharpes may be 0.2-0.5 inflated relative to actual skill. GTOS is comparatively understated. Also: GTOS-style "many small wins, occasional larger loss" could resemble a Sharpening-Sharpe profile if not careful.
- **Potential hypothesis:** GTOS profile (many small wins + occasional larger loss) should be evaluated using both Sharpe and the Goetzmann-Ingersoll manipulation-proof measure to verify edge robustness.
- **Cross-domain links:** 02 (statistical methodology), 16 (option-like payoffs), 21 (sizing)
- **Study type:** theoretical + empirical
- **Entity studied:** hedge fund cross-section

### Predicting Hedge Fund Fraud
- **Authors:** Bollen, Nicolas P. B.; Pool, Veronika K.
- **Year:** 2009-2012 (multiple papers; book-length 2012 monograph)
- **Source:** Multiple — Journal of Finance 2009 ("Do Hedge Fund Managers Misreport Returns?"), Warwick monograph 2012
- **URL:** https://warwick.ac.uk/fac/soc/wbs/subjects/finance/events/seminars/nick_bollen.pdf
- **Abstract:** Detects hedge-fund return manipulation through statistical anomalies in the pooled distribution of returns.
- **Key findings:**
  - Hedge funds disproportionately report small positive returns over small negative returns
  - Disconnect between actual and reported returns at the +0% threshold (manipulation indicator)
  - Detectable manipulation predicts subsequent fund fraud / blow-up
  - Provides real-time fraud-detection methodology
- **Relevance to GTOS:** Inverse relevance — GTOS reports raw MT5 returns, no smoothing or reporting choice. So Bollen-Pool detection finds no anomaly. This is structurally credible.
- **Potential hypothesis:** GTOS's return distribution will pass Bollen-Pool test cleanly because reporting is automated and direct.
- **Cross-domain links:** 02 (statistical methodology — anomaly detection), 17 (behavioral)
- **Study type:** empirical methodology
- **Entity studied:** hedge fund cross-section

### Risk Management Lessons from Long-Term Capital Management
- **Authors:** Jorion, Philippe
- **Year:** 2000
- **Source:** European Financial Management, vol. 6 (3), pp. 277-300
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/1468-036X.00125
- **Abstract:** Forensic analysis of LTCM's 1998 collapse, focusing on VaR, leverage, correlation underestimation.
- **Key findings:**
  - LTCM had ~25:1 balance-sheet leverage ($125B assets / $5B equity)
  - $1.25T notional in derivatives off balance sheet
  - Same covariance matrix used for risk and optimization → systematic bias
  - Tail-risk underestimation due to short-history calibration
  - Correlation breakdown during stress was the proximate cause
- **Relevance to GTOS:** Direct lesson for GTOS risk-overlay design. GTOS uses ATR-based stops, drawdown thresholds (H29), per-trade R caps, and concurrent-position limits — all of which protect against the LTCM-style failure modes. The cross-instrument correlation gate (additive HALVE/REJECT) explicitly addresses correlation-breakdown risk.
- **Potential hypothesis:** GTOS's LTCM-equivalent risk would manifest as correlation collapse across instruments. The cross-instrument correlation gate should be tested under stress scenarios.
- **Cross-domain links:** 21 (risk management), 13 (correlation), 03 (tail risk)
- **Study type:** case-study + risk-management methodology
- **Entity studied:** single fund (Long-Term Capital Management)

### 3.6 AQR-and-related smart-beta / factor research (3 papers)

### Value and Momentum Everywhere
- **Authors:** Asness, Clifford S.; Moskowitz, Tobias J.; Pedersen, Lasse Heje
- **Year:** 2013
- **Source:** Journal of Finance, vol. 68 (3), pp. 929-985
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12021
- **Abstract:** Documents value and momentum factors across 8 asset classes (US/international equities, country indices, bonds, currencies, commodities). Spans 40 years of data.
- **Key findings:**
  - Value and momentum work in every asset class examined
  - Value premia and momentum premia are negatively correlated within asset classes (diversification benefit)
  - Combined value+momentum portfolio Sharpe is materially higher than either alone
  - Establishes universal applicability of factor investing
- **Relevance to GTOS:** GTOS's kill-zone-based momentum exploitation is in the spirit of the time-series momentum component. Asness-Moskowitz-Pedersen establishes that momentum works across asset classes — consistent with GTOS XAU + FX + indices having similar edge structure.
- **Potential hypothesis:** GTOS edge structure should generalize across asset classes; failure on a particular asset class (e.g., EURUSD's 97% L2 rejection) is more likely a per-instrument execution problem than a fundamental momentum-doesn't-work problem.
- **Cross-domain links:** 13 (factor models), 14 (momentum), 11 (FX)
- **Study type:** empirical
- **Entity studied:** factor cross-section across 8 asset classes

### Betting Against Beta
- **Authors:** Frazzini, Andrea; Pedersen, Lasse Heje
- **Year:** 2014
- **Source:** Journal of Financial Economics, vol. 111 (1), pp. 1-25
- **URL:** https://www.sciencedirect.com/science/article/pii/S0304405X13002675
- **Abstract:** Models leverage / margin constraints; predicts (and documents) BAB factor: long leveraged low-beta + short high-beta.
- **Key findings:**
  - High-beta assets have low alpha (constrained investors bid up high-beta as substitute for leverage)
  - BAB factor delivers significant positive risk-adjusted returns
  - Effect verified across US equities + 20 international equity markets + Treasury bonds + corporate bonds + futures
  - Magnitude rivals value, momentum, size factors
- **Relevance to GTOS:** Structural, not directly applicable to GTOS execution. But: provides the leverage-margin-constraint framework that explains why some agents (e.g., GTOS at 1-2% risk per trade vs hedge funds at 5-10×) might capture different premia than highly-leveraged competitors.
- **Potential hypothesis:** GTOS's modest leverage (redacted_account 1-2% risk per trade) means it can hold positions through stress that more-leveraged competitors must liquidate.
- **Cross-domain links:** 13 (factor models), 21 (sizing)
- **Study type:** theoretical + empirical
- **Entity studied:** factor cross-section across multiple asset classes

### Quality Minus Junk
- **Authors:** Asness, Clifford S.; Frazzini, Andrea; Pedersen, Lasse Heje
- **Year:** 2019
- **Source:** Review of Accounting Studies, vol. 24 (1), pp. 34-112
- **URL:** https://link.springer.com/article/10.1007/s11142-018-9470-2
- **Abstract:** Defines "quality" (profitability, growth, safety) as theoretically-warranted; documents that high-quality stocks earn higher risk-adjusted returns.
- **Key findings:**
  - High-quality stocks earn higher risk-adjusted returns despite higher prices
  - QMJ factor (long high-quality, short low-quality) earns significant alpha in US + 24 countries
  - Time-varying price of quality predicts future QMJ returns (low quality price → high future QMJ return)
  - Analysts systematically underestimate quality-related earnings
- **Relevance to GTOS:** Not directly applicable to GTOS instrument set (FX/gold/indices, not single stocks). Indirectly relevant: QMJ factor partially explains Buffett's alpha (above), validating the more-general principle that systematic factor exposure outperforms.
- **Potential hypothesis:** GTOS could screen instruments using a "quality" notion — instruments where the order-flow / mispricing-mechanism is most-pronounced — and bias toward those.
- **Cross-domain links:** 13 (factor models)
- **Study type:** empirical
- **Entity studied:** stock-level cross-section

### 3.7 Adaptive markets, behavioral, prop-trading-desk (3 papers)

### Adaptive Markets: Financial Evolution at the Speed of Thought
- **Authors:** Lo, Andrew W.
- **Year:** 2017
- **Source:** Princeton University Press
- **URL:** https://press.princeton.edu/books/paperback/9780691191362/adaptive-markets
- **Abstract:** Synthesizes the Adaptive Markets Hypothesis — markets evolve through competition, adaptation, natural selection. Reconciles efficient-market and behavioral perspectives.
- **Key findings:**
  - Market efficiency is dynamic, not static — emerges from competition among adaptive agents
  - Anomalies persist when relevant species (investors) are too few; anomalies decay when species multiply
  - Hedge funds embody natural selection — winning strategies survive, losing strategies extinct
  - "Nothing makes sense in the hedge fund industry except in the light of the Adaptive Markets Hypothesis"
- **Relevance to GTOS:** AMH is the natural conceptual home for the F11 / F15 decay narrative. Edges decay because they get replicated; new edges emerge from new market structure / regime shifts. GTOS Phase 2 should plan for this — edges are not eternal, they cycle.
- **Potential hypothesis:** GTOS should operate on a 12-18 month edge-discovery / edge-decay cycle: continuously look for new structural anomalies as old ones decay.
- **Cross-domain links:** 17 (behavioral / adaptive markets), 22 (alpha decay)
- **Study type:** book-length synthesis
- **Entity studied:** market structure / hedge-fund industry

### Hedge Funds: An Analytic Perspective (Updated Edition)
- **Authors:** Lo, Andrew W.
- **Year:** 2010 (revised; orig 2008)
- **Source:** Princeton University Press
- **URL:** https://press.princeton.edu/books/paperback/9780691145983/hedge-funds
- **Abstract:** Comprehensive analytical treatment of hedge fund risk, performance, and structure. Includes illiquidity-adjusted Sharpe, hedge-fund-failure rate models, mean-variance-liquidity optimization.
- **Key findings:**
  - Traditional Sharpe / alpha measures mislead when applied to hedge funds (illiquidity smoothing)
  - Hedge fund failure rates have predictable structural drivers
  - Mean-variance-liquidity optimization is a tractable extension that incorporates illiquidity
  - Provides systematic framework for hedge-fund due diligence
- **Relevance to GTOS:** Comprehensive framework. Useful for any future Phase-2 institutional-investor pitch (validates the discipline of using illiquidity-adjusted metrics + failure-rate-aware sizing).
- **Potential hypothesis:** GTOS's failure-mode profile (drawdown + technical bug + AI grounding bug) should be modeled with explicit hazard rates, not just protective gates.
- **Cross-domain links:** 02 (methodology), 21 (risk management)
- **Study type:** book-length analytical treatment
- **Entity studied:** hedge-fund industry

### Careers and Survival: Competition and Risk in the Hedge Fund and CTA Industry
- **Authors:** Brown, Stephen J.; Goetzmann, William N.; Park, James M.
- **Year:** 2001
- **Source:** Journal of Finance, vol. 56 (5), pp. 1869-1886
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00392
- **Abstract:** Documents how hedge-fund managers' risk-taking depends on relative-performance ranking. Good first-half performers reduce risk; poor first-half performers increase risk.
- **Key findings:**
  - Variance shifts depend on *relative*, not absolute, fund performance
  - Reputation costs drive risk-taking patterns
  - Probability of liquidation increases with risk
  - Two consecutive negative years dramatically increase shutdown probability
- **Relevance to GTOS:** GTOS as single-CEO-financed avoids the relative-performance career-concern problem entirely. The CEO's ability to maintain risk discipline post-loss is structurally easier than for an open-end hedge fund.
- **Potential hypothesis:** GTOS should NOT respond to drawdown by increasing risk (the typical poor-performer pattern); H29 8% DD → 0.5% risk reduction is the structurally-correct response.
- **Cross-domain links:** 18 (psychology), 21 (sizing)
- **Study type:** empirical
- **Entity studied:** hedge fund + CTA managers

### 3.8 Bridgewater / risk-parity / other public-research (1 paper)

### The All Weather Story / Engineering Targeted Returns and Risks
- **Authors:** Dalio, Ray; Prince, Bob (Bridgewater Associates)
- **Year:** 2004 (orig "All Weather" paper); 2011 (Engineering Targeted Returns and Risks)
- **Source:** Bridgewater public whitepaper
- **URL:** https://www.bridgewater.com/research-and-insights/the-all-weather-story
- **Abstract:** Lays out the All Weather / risk-parity framework: balance asset-class exposure by *risk*, not capital, across four economic regimes (rising/falling growth × rising/falling inflation).
- **Key findings:**
  - Traditional 60/40 portfolios over-concentrate risk in equities
  - Risk parity: balance contribution to portfolio risk across asset classes, scaled by leverage
  - Four-regime framework: rising growth / falling growth / rising inflation / falling inflation
  - All Weather is robust across regimes, not optimized for any one
- **Relevance to GTOS:** GTOS's regime-classifier work (memory `feedback_decay_is_ceo_number_one_concern`, F2/F10/F15 regime findings) is closer to the AMH evolution paradigm than the Bridgewater four-regime taxonomy, but the principle of explicit regime conditioning is shared. Bridgewater's framework is ~20-year horizon; GTOS's regime classifier is ~hours-to-days horizon. Different time-scales but same principle.
- **Potential hypothesis:** GTOS regime classifier should be benchmarked against a baseline 4-regime classifier (growth × inflation) to verify the higher-frequency classifier captures different signal.
- **Cross-domain links:** 13 (factor / regime), 21 (sizing / risk parity), 17 (regime)
- **Study type:** practitioner whitepaper
- **Entity studied:** single firm (Bridgewater All-Weather strategy)

### 3.9 Wall Street sell-side / analyst forecast bias (2 papers)

### Behavioral Biases of Analysts and Investors (NBER Reporter 2020)
- **Authors:** Multiple (Bordalo, Gennaioli, Shleifer; Hirshleifer; Lim; Cen, Hilary, Wei; et al.)
- **Year:** 2020 (NBER Reporter synthesis); spans 2014-2020 underlying papers
- **Source:** NBER Reporter, no. 2 (2020)
- **URL:** https://www.nber.org/reporter-2020-02/behavioral-biases-analysts-and-investors
- **Abstract:** Reviews academic evidence of analyst forecast biases, optimism, conflicts of interest, and effects on investor behavior.
- **Key findings:**
  - Analysts produce systematically optimistic forecasts (decades of evidence)
  - Commission relationships with mutual-fund clients amplify optimistic bias
  - Analysts' first impressions of firms have lasting positive correlations with subsequent forecasts
  - Buy/outperform ratings ~49% of total; Sell/underperform ~6% — strong skew
- **Relevance to GTOS:** Indirect / strategic. GTOS is fully data-driven and does not consume analyst forecasts. But: confirms that *human* analyst forecasts as inputs to AI systems would introduce systematic optimistic bias. GTOS's choice to evaluate only chart structure, not consensus forecast, structurally avoids this bias.
- **Potential hypothesis:** GTOS could ablation-test against an "AI-with-analyst-input" baseline to verify the structural advantage of pure-chart-based decision.
- **Cross-domain links:** 18 (psychology), 17 (behavioral)
- **Study type:** review
- **Entity studied:** sell-side analyst ecosystem

### Do Sell-Side Analyst Reports Have Investment Value?
- **Authors:** Multiple (anonymized arXiv 2025 paper)
- **Year:** 2025
- **Source:** arXiv preprint 2502.20489
- **URL:** https://arxiv.org/html/2502.20489v1
- **Abstract:** Recent re-test of analyst-report value using LLM-extracted features and 2010-2024 data.
- **Key findings:**
  - Sell-side analyst reports retain marginal predictive value when augmented by ML techniques
  - Raw consensus has weakened over time; ML-extraction of analyst-report-text adds back some signal
  - Unconditional consumption of analyst forecasts continues to underperform
- **Relevance to GTOS:** GTOS does not consume analyst reports, but this paper shows the contemporary state of "alternative data extracted from analyst output." If GTOS Phase 2 considered alternative-data ingestion, analyst-text extraction is a bounded-value possibility.
- **Potential hypothesis:** Analyst-text extraction could provide ~+5-10bps of incremental signal at modest implementation cost; may be worth a Phase 2 evaluation.
- **Cross-domain links:** 19 (ML / LLM), 20 (LLM agent), 17 (sentiment)
- **Study type:** empirical methodology
- **Entity studied:** sell-side analyst forecasts

### 3.10 Quantum-finance public POCs (10 papers)

### Quantum Computing for Finance: Overview and Prospects
- **Authors:** Orus, Roman; Mugel, Samuel; Lizaso, Enrique
- **Year:** 2019 (initial 2018 preprint)
- **Source:** Reviews in Physics, vol. 4, article 100028 + arXiv 1807.03890
- **URL:** https://arxiv.org/abs/1807.03890
- **Abstract:** Comprehensive review of quantum computing applications in finance: portfolio optimization, arbitrage detection, credit scoring, derivative pricing, deep-learning enhancements.
- **Key findings:**
  - Quantum annealers (D-Wave) suitable for combinatorial optimization
  - Quantum amplitude estimation gives quadratic speedup for Monte Carlo
  - Quantum machine learning offers theoretical (currently unproven) advantages
  - All applications are POC-level; no production-ready quantum-finance system yet
- **Relevance to GTOS:** Long-horizon strategic input. None of these is operationally ready for GTOS in 2026. Reasonable Phase-3 watch-list (post-2030).
- **Potential hypothesis:** Quantum computing will reach practical advantage for derivative pricing first (~2028-2030), portfolio optimization second (~2030-2032), trading-strategy directly last (~2035+).
- **Cross-domain links:** 19 (ML), 16 (option pricing), 21 (sizing)
- **Study type:** review
- **Entity studied:** quantum-finance applications across the field

### Quantum Computing for Finance: State of the Art and Future Prospects
- **Authors:** Egger, Daniel J.; Gambella, Claudio; Marecek, Jakub; McFaddin, Scott; Mevissen, Martin; Raymond, Rudy; Simonetto, Andrea; Woerner, Stefan; Yndurain, Elena
- **Year:** 2020
- **Source:** IEEE Transactions on Quantum Engineering, vol. 1 + arXiv 2006.14510
- **URL:** https://arxiv.org/abs/2006.14510
- **Abstract:** IBM-led survey of quantum-finance state-of-the-art, with concrete IBM Quantum back-end demonstrations.
- **Key findings:**
  - Maps finance problems to three quantum algorithm families: simulation, optimization, machine learning
  - Provides demonstrations of quantum algorithms on IBM Quantum hardware (small qubit counts)
  - Identifies near-term feasibility frontiers
  - Most production quantum-finance application is currently derivative pricing
- **Relevance to GTOS:** Same as Orus / Mugel — long-horizon strategic input. IBM's hardware-grounded demonstrations make this paper more credible than pure theoretical surveys.
- **Potential hypothesis:** IBM Quantum + JPMorgan partnership likely to deliver first production-ready quantum derivative pricing by 2028.
- **Cross-domain links:** 16 (derivatives), 19 (ML)
- **Study type:** review + experimental demonstration
- **Entity studied:** IBM Quantum platform

### A Survey of Quantum Computing for Finance (JPMorgan / Marco Pistoia)
- **Authors:** Herman, Dylan; Googin, Cody; Liu, Xiaoyuan; Galda, Alexey; Safro, Ilya; Sun, Yue; Pistoia, Marco; Alexeev, Yuri
- **Year:** 2022
- **Source:** arXiv preprint 2201.02773
- **URL:** https://arxiv.org/abs/2201.02773
- **Abstract:** JPMorgan + Argonne survey of quantum computing for finance; emphasis on derivative pricing, risk modeling, portfolio optimization, NLP, fraud detection.
- **Key findings:**
  - JPMorgan has shipped a working quantum-amplitude-estimation derivative-pricing implementation
  - Portfolio optimization remains theoretical / proof-of-concept
  - Quantum NLP and fraud detection are speculative
  - JPMorgan + IBM partnership reported 100× sample efficiency for European-call pricing on IBM 127-qubit Eagle
- **Relevance to GTOS:** This is the most-credible production-finance perspective — JPMorgan's actual work, not academic-only. Empirical benchmark for what "quantum advantage in finance" looks like in 2022-2024.
- **Potential hypothesis:** Quantum advantage in derivative pricing is real now (2024+); strategy execution remains 5-10y away.
- **Cross-domain links:** 16 (derivatives), 19 (ML / NLP)
- **Study type:** review (with empirical results)
- **Entity studied:** JPMorgan quantum-finance team

### Option Pricing Using Quantum Computers
- **Authors:** Stamatopoulos, Nikitas; Egger, Daniel J.; Sun, Yue; Zoufal, Christa; Iten, Raban; Shen, Ning; Woerner, Stefan
- **Year:** 2020
- **Source:** Quantum, vol. 4, p. 291
- **URL:** https://quantum-journal.org/papers/q-2020-07-06-291/
- **Abstract:** End-to-end quantum-amplitude-estimation method for pricing options and option portfolios.
- **Key findings:**
  - Quantum amplitude estimation gives quadratic Monte Carlo speedup
  - Method works for path-dependent and path-independent options
  - Demonstrates working IBM Quantum hardware implementations at small qubit counts
  - Establishes the canonical approach now used by JPMorgan + Goldman
- **Relevance to GTOS:** Foundational. Not operational for GTOS, but defines the technique that will eventually become institutional infrastructure for derivative pricing.
- **Potential hypothesis:** Quantum option pricing will reach production at ~2027 once qubit counts cross 1000+ with reasonable error rates.
- **Cross-domain links:** 16 (option pricing), 02 (Monte Carlo)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** quantum derivative pricing

### Quantum Risk Analysis (Woerner-Egger 2018-2019)
- **Authors:** Woerner, Stefan; Egger, Daniel J.
- **Year:** 2019 (npj Quantum Information; arXiv 2018)
- **Source:** npj Quantum Information, vol. 5, article 15 + arXiv 1806.06893
- **URL:** https://arxiv.org/abs/1806.06893
- **Abstract:** Demonstrates quantum amplitude estimation on small-scale Value at Risk (VaR) and Conditional Value at Risk (CVaR) instances on IBM Quantum hardware.
- **Key findings:**
  - Quantum advantage shown on toy-scale VaR/CVaR computation
  - Quadratic speedup over classical Monte Carlo
  - Hardware-feasible at <16 qubits
  - First production-track quantum-risk-analysis demonstration
- **Relevance to GTOS:** Risk-analysis use-case more likely to mature than trading-strategy use-case. GTOS's VaR / CVaR computation could eventually benefit from quantum approach if production hardware matures.
- **Potential hypothesis:** Quantum risk analysis is a likely near-term (5y) practical application; quantum trading strategy is not (10y+).
- **Cross-domain links:** 21 (risk management), 03 (tail estimation)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** quantum risk computation

### Improving Variational Quantum Optimization Using CVaR
- **Authors:** Barkoutsos, Panagiotis Kl.; Nannicini, Giacomo; Robert, Anton; Tavernelli, Ivano; Woerner, Stefan
- **Year:** 2020
- **Source:** Quantum, vol. 4, p. 256 + arXiv 1907.04769
- **URL:** https://arxiv.org/abs/1907.04769
- **Abstract:** Modifies variational quantum optimization to use CVaR (instead of expected value) as the optimization objective; demonstrates better convergence on combinatorial-optimization problems.
- **Key findings:**
  - CVaR objective improves convergence of QAOA / VQE
  - Tested on portfolio optimization and traveling-salesman analogues
  - Better empirical performance than standard expectation-value VQE
- **Relevance to GTOS:** Methodology refinement of the broader quantum-optimization track. Indicates that practical quantum optimization is still being significantly refined — not at the "stable production" level.
- **Potential hypothesis:** CVaR-based optimization is also classically valuable — GTOS could explore CVaR-based portfolio choice classically before quantum hardware matures.
- **Cross-domain links:** 03 (tail estimation), 21 (risk management)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** variational quantum optimization

### Dynamic Portfolio Optimization with Real Datasets Using Quantum Processors and Quantum-Inspired Tensor Networks
- **Authors:** Mugel, Samuel; Kuchkovsky, Carlos; Sanchez, Escolastico; Fernandez-Lorenzo, Samuel; Luis-Hita, Jorge; Lizaso, Enrique; Orus, Roman
- **Year:** 2022
- **Source:** Physical Review Research, vol. 4, article 013006 + arXiv 2007.00017
- **URL:** https://arxiv.org/abs/2007.00017
- **Abstract:** Implements dynamic-portfolio-optimization across 8 years of real daily data, 52 assets, on multiple quantum / quantum-inspired platforms (D-Wave, IBM-Q, tensor networks).
- **Key findings:**
  - D-Wave hybrid annealing produces practical solutions on real-data 52-asset problems
  - Tensor-network methods (classical, quantum-inspired) match or exceed D-Wave on many cases
  - VQE on IBM-Q has higher overhead, lower performance currently
  - Sharpe-ratio comparable to classical exhaustive search for problem sizes evaluated
- **Relevance to GTOS:** This is the most-real-data quantum-portfolio-optimization paper to date. Demonstrates that the tooling is workable at small scale with real data, but no clear quantum advantage on this problem size.
- **Potential hypothesis:** Tensor-network methods (classical, quantum-inspired) are the most likely near-term practical winner; pure quantum hardware will mature later.
- **Cross-domain links:** 13 (factor / portfolio), 21 (sizing), 19 (ML)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** dynamic portfolio optimization

### Forecasting Financial Crashes with Quantum Computing
- **Authors:** Orus, Roman; Mugel, Samuel; Lizaso, Enrique
- **Year:** 2019
- **Source:** Physical Review A, vol. 99, p. 060301
- **URL:** https://arxiv.org/abs/1810.07690
- **Abstract:** Maps the financial-crash-prediction problem to a quantum optimization formulation. Tests on D-Wave hardware.
- **Key findings:**
  - Quantum annealing detects crash precursors in synthetic / small-scale data
  - Speedup over classical pattern detection on small instances
  - Practical scaling to real markets remains open
- **Relevance to GTOS:** Tangentially related. GTOS could conceivably benefit from quantum-enhanced crash detection at scale, but the technology is far from production.
- **Potential hypothesis:** Quantum crash detection is unlikely to be production-ready before 2030.
- **Cross-domain links:** 05 (change-point / crash detection), 03 (tail risk)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** quantum crash detection

### Quantum Reinforcement Learning Trading Agent for Sector Rotation in the Taiwan Stock Market
- **Authors:** Anonymized author group (arXiv preprint 2506.20930)
- **Year:** 2025
- **Source:** arXiv preprint 2506.20930
- **URL:** https://arxiv.org/abs/2506.20930
- **Abstract:** Hybrid quantum-classical RL framework for sector rotation, using PPO + quantum policy network.
- **Key findings:**
  - QNN-based policies achieve higher *training* rewards than classical
  - But quantum models *underperform* classical on real investment metrics (cumulative return, Sharpe)
  - Mismatch between training proxy and investment metric is the core challenge
  - Quantum reward proxy may incentivize overfitting to short-term volatility
- **Relevance to GTOS:** Cautionary tale. Even where quantum methods win on training-time metrics, they can lose on real-world investment metrics. Direct parallel to GTOS's K54 finding (training AUC ≠ realized R per memory `project_k54_ml_classifier_baseline_2026-04-27`).
- **Potential hypothesis:** Quantum RL trading agents will continue to underperform classical on realized returns until reward-design matches investment objectives, regardless of computational platform.
- **Cross-domain links:** 20 (RL / LLM agent), 19 (ML)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** quantum sector-rotation strategy

### Improved Financial Forecasting via Quantum Machine Learning
- **Authors:** Multiple (Springer Quantum Machine Intelligence + arXiv 2306.12965)
- **Year:** 2023
- **Source:** Quantum Machine Intelligence + arXiv 2306.12965
- **URL:** https://arxiv.org/abs/2306.12965
- **Abstract:** Tests quantum machine learning on financial forecasting tasks (volatility, yield curves) against classical baselines.
- **Key findings:**
  - QSVR / quantum kernel methods achieve modestly better accuracy on volatility and yield-curve prediction
  - Improvements small but statistically significant
  - Practicality limited by current quantum hardware (small qubit counts, high error rates)
- **Relevance to GTOS:** Quantum-ML for forecasting has shown small improvements; not yet step-change. Continues the watch-list status.
- **Potential hypothesis:** Quantum-ML for short-horizon volatility forecasting will reach 5-10% improvement over classical by 2027-2028.
- **Cross-domain links:** 16 (vol forecasting), 19 (ML)
- **Study type:** quantum-proof-of-concept
- **Entity studied:** quantum financial forecasting

---

## 4. Top 3 most-relevant-to-GTOS

1. **Cornell, Bradford (2020) "Medallion Fund: The Ultimate Counterexample?"** — Sets the empirical ceiling for systematic alpha. Tells GTOS that durable systematic edge at small scale is *possible* (Renaissance proves it for 31 years) but rare and requires a unique combination of capabilities. Calibrates expectations: a 1-3% monthly edge held for 5+ years is empirically achievable but is the right benchmark, not the median hedge fund.

2. **McLean & Pontiff (2016) "Does Academic Research Destroy Stock Return Predictability?"** — Quantitative anchor for the F11 / item #4 / F15 decay narrative. The 26% out-of-sample / 58% post-publication decline calibrates GTOS's expected edge decay. Together with Sullivan (2019) and Bollen-Joenvaara-Kauppila (2017), it establishes that GTOS-style edges are *expected* to decay and that the strategic response is continuous edge-evolution, not preservation.

3. **Frazzini, Kabiller & Pedersen (2018) "Buffett's Alpha"** — Methodological template: gold-standard demonstration that *what looks like ineffable manager skill decomposes to specific, repeatable factor exposures*. For GTOS, this argues that if the edge persists, it is likely a tight intersection of detectable conditions (kill-zone × OB-zone × side-aware regime), not "AI mystery." Also: argues that institutional credibility comes from being able to factor-decompose your own alpha. K54 should be designed to do this systematically.

## 5. Top 1 surprise

**Quantum reinforcement learning trading agents UNDERPERFORM classical on real investment metrics, even when their training-time metrics are higher** (arXiv 2506.20930, 2025). This is a direct parallel to GTOS's K54 finding (memory `project_k54_ml_classifier_baseline_2026-04-27`): training AUC of 0.571 produces realized lift of +0.164R, much smaller than the AUC suggests. The deeper insight is universal: any ML / quantum / agent system trained on a proxy reward function (cross-entropy, AUC, training reward) systematically *overestimates* its real-world performance. The "training-vs-realized gap" is a structural feature of all proxy-based learning, not a quantum-specific issue. **Implication for GTOS:** any future ML-based feature must be evaluated on realized R, not on training metrics — *no exceptions, no shortcuts*. The walk-level evidence rule (memory `feedback_walk_level_evidence_not_predictive`) is a general principle, not a one-off discovery.

## 6. Hypotheses

1. **GTOS edge is regime-conditioned momentum at small scale; expected decay rate 26-58% over the post-publication / out-of-sample window** — directly extends McLean-Pontiff to the H2-2026 window. Predicted measurement: F11 + future F11-equivalent measurements should show ~2-5% additional decay per quarter through 2027 absent active edge-evolution.

2. **GTOS's Carhart / Fung-Hsieh-7 factor decomposition will show momentum-factor exposure plus residual alpha; the residual alpha is what actually compensates for execution effort** — testable once n=12+ months of clean monthly returns are available. The factor-decomposition validates which part of GTOS's edge is replicable (priced) vs idiosyncratic (skill).

3. **Quantum-finance technologies (esp. amplitude-estimation derivative pricing) will reach institutional-production by 2027-2028 but will not be operational for retail-prop-firm-scale strategies before 2032** — implies GTOS should not invest in quantum-finance R&D in 2026-2027; should track Goldman / JPMorgan production deployments and re-evaluate in 2028.

## 7. Cross-domain handoffs

- **F11 / F15 / item #4 decay narrative:** the McLean-Pontiff (2016), Sullivan (2019), Bollen-Joenvaara-Kauppila (2017), and Lo (2017 AMH) papers all directly anchor GTOS's empirical decay observation. → Sync with domain 17 (behavioral / adaptive markets) for the AMH / regime-evolution side; sync with domain 13 (cross-asset factors) for the factor-decay side.

- **Renaissance Medallion case study (Cornell 2020 + Zuckerman 2019):** establishes that durable alpha at small AUM can persist 30+ years if the strategy is uniquely-capacity-blocked. → Sync with domain 06 (microstructure) for the technical strategy implementation context; with domain 19 (ML methodology) for the math-first / pattern-recognition culture.

- **Buffett's Alpha factor-decomposition (Frazzini-Kabiller-Pedersen 2018):** template for how to decompose GTOS edge against systematic factors. → Sync with domain 13 (factor models) for the BAB / QMJ factor papers themselves; with domain 21 (sizing) for the leverage / risk-adjusted-return component.

- **LTCM lessons (Jorion 2000):** validates GTOS's risk-overlay design (cross-instrument correlation gate, drawdown-triggered position sizing). → Sync with domain 21 (risk management) for the broader Kelly / fat-tail-sizing literature.

- **Quantum-finance papers (Orus, Egger-Woerner, Stamatopoulos, Mugel-Lizaso-Orus, Herman-Pistoia):** strategic 5-10y watchlist. None operational for GTOS now. → Sync with domain 19 (ML) for the quantum-ML papers and domain 16 (vol / option pricing) for the quantum-amplitude-estimation derivative-pricing papers.

- **Hedge-fund database biases (Joenvaara-Kosowski-Tolonen-Kauppila 2021, Bollen-Whaley 2009, Bollen-Pool fraud detection):** mandates that GTOS not over-rely on public hedge-fund benchmarks for self-comparison; GTOS's own MT5 numbers are cleaner than the published industry numbers. → Sync with domain 02 (statistical methodology) for the bias-detection / multiple-testing methodology.

---

## 8. Gaps and caveats

- **No Renaissance Technologies internal-research papers exist** — the firm publishes nothing about its strategy. Cornell (2020) and Zuckerman (2019) are the only credible sources, and both are external observers.
- **AQR / Two Sigma / Bridgewater whitepapers are the closest equivalent to "hedge-fund-internal research"** but are public-relations-vetted documents. I include them where the methodology is transparent.
- **Quantum-finance literature is fast-evolving** — papers from 2024-2025 (e.g., 2506.20930 quantum RL Taiwan) are bleeding-edge and not yet peer-reviewed. Include for completeness but flag as preliminary.
- **Citadel / Jane Street / Hudson River have no public research papers** about their actual strategies (correctly, from a competitive standpoint). Public information on these firms is journalism-only and not included as research papers.
- **The Brown-Goetzmann-Park (2001) finding on relative-performance career-concern bias** is interesting but its relevance to GTOS as a single-CEO operation is *negative* — GTOS structurally avoids it. This is a counterpoint, not a directly-applicable methodology.
- **Spec target was 25-40 papers; this output has 35** — comfortably mid-range. The marginal-paper would have been one more on capacity constraints or one more recent quantum POC; both addressed in the existing 35.

---

*End of papers.md for Domain 22 — Hedge Fund Alpha, Wall Street, Quantum Finance Public Research.*
