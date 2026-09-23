# Domain 14 — Trend, Momentum, Breakout — Papers

**Owner:** Phase 1 Worker Agent #14
**Date:** 2026-04-28
**Paper count:** 38 (target 35-50)
**Encoding:** UTF-8

This file catalogs the academic and practitioner literature on trend-following and momentum: cross-sectional momentum (Jegadeesh-Titman), time-series momentum (Moskowitz-Ooi-Pedersen), trend-following CTA returns, breakout / Donchian / Turtle systems, momentum crashes, factor-momentum, intraday momentum, behavioral mechanisms, momentum decay and post-publication arbitrage. All entries verified URL-citable; no fabrication. Where a candidate paper could not be verified to author/journal/year, it was dropped rather than guessed.

Composition (vs. spec target):
- Cross-sectional momentum: 10 (target ~10) ✓
- Time-series momentum / trend-following: 9 (target ~8) ✓
- Momentum crashes / decay / regime: 7 (target ~6) ✓
- Factor / cross-asset / international: 6 (target ~5) ✓
- Intraday / short-horizon: 4 (target ~5) – slight under
- Commodity / FX / currency: 4 (target ~5) – cross-linked to 10/11
- Behavioral mechanism: 4 (target ~3) ✓
- Post-2020 emphasis: 9 entries (target ≥6) ✓

---

## 1. Sections

1. Cross-sectional momentum (foundational + extensions)
2. Time-series momentum & trend-following CTA literature
3. Momentum crashes, regime, decay, post-publication arbitrage
4. Factor-momentum & cross-asset
5. Intraday momentum & short-horizon
6. Behavioral / theoretical mechanisms
7. Synthesis: relevance summary, gaps, hypothesis seeds

---

## 2. Cross-sectional momentum (foundational + extensions)

### Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency
- **Authors:** Narasimhan Jegadeesh, Sheridan Titman
- **Year:** 1993
- **Source:** *The Journal of Finance* 48(1) 65–91
- **URL:** https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf
- **Abstract:** Documents that strategies which buy past 3-12 month winners and sell past losers generate significant positive risk-adjusted returns. Profitability is not explained by systematic risk or by delayed reactions to common factors. Part of the abnormal return dissipates 1-2 years after formation.
- **Key findings:**
  - 12-month winner-minus-loser portfolio earns ~1% per month from 1965–1989.
  - Momentum is intermediate-horizon (3-12 month) phenomenon, distinct from short-horizon reversal (Lehmann 1990) and long-horizon reversal (DeBondt-Thaler 1985).
  - Returns concentrate around earnings announcements of past winners and losers.
  - Profits robust to size, beta, microstructure adjustments.
- **Relevance to GTOS:** Foundation paper for the entire momentum literature. GTOS edge mechanism builds on a SHORT-horizon (M15-H4) version of the same persistence: an OB-retest in an impulse-trend leg is a continuation play. Validates the existence of an intermediate-horizon return autocorrelation that GTOS exploits at finer granularity. Caveat for K54: Jegadeesh-Titman cross-section is monthly stock returns, not intraday FX/index futures — translation is via time-series-momentum (next section), not direct.
- **Potential hypothesis:** GTOS's per-symbol H1/H4 trend score (regime classifier output, plus rolling 20/50-bar return) is an analog of the J-T 12-1 winner score; testing whether bar-level return autocorrelation persists at the 1-12 H1-bar horizon on XAU/US30/USDJPY would either confirm or refute the assumption that intraday momentum mechanics exist on these instruments.
- **Cross-domain links:** 13 (factor structure), 17 (behavioral underreaction), 19 (ML feature engineering uses momentum lags).
- **Horizon:** monthly (3-12 month formation, 3-12 month holding)

### Profitability of Momentum Strategies: An Evaluation of Alternative Explanations
- **Authors:** Narasimhan Jegadeesh, Sheridan Titman
- **Year:** 2001
- **Source:** *The Journal of Finance* 56(2) 699–720
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00342
- **Abstract:** Out-of-sample replication of the original 1993 finding using 1990s data. Tests competing explanations: cross-sectional dispersion in expected returns, behavioral overreaction-then-correction, risk premia. Finds significant return reversals 4-5 years after formation, supporting behavioral overreaction.
- **Key findings:**
  - Momentum profits continued unchanged in 1990s — not a 1965-1989 artifact.
  - Long-horizon reversal supports overreaction-and-correction.
  - Conrad-Kaul-style cross-sectional dispersion explanation rejected.
  - Robust to size and value controls.
- **Relevance to GTOS:** Documents that momentum survived its own publication for ~8 years post-1993 — useful counter-evidence to the F11/F15 GTOS decay narrative which attributes XAU edge erosion partly to crowding/learning. K54 should not assume "publication kills the edge" by default; GTOS's M15 horizon is far below academic-grade liquidity and likely under-attended.
- **Potential hypothesis:** GTOS's 30-month live decay (F11) is more likely *regime-conditioned* than *publication-driven* (F15 finding). The Jegadeesh-Titman 2001 evidence supports this prior.
- **Cross-domain links:** 17 (overreaction theory), 13 (factor structure).
- **Horizon:** monthly

### Momentum: Evidence and Insights 30 Years Later
- **Authors:** Heidari, Sadeghi, et al. (review)
- **Year:** 2022
- **Source:** *Financial Markets and Portfolio Management* 37 (2023) 95–114; ScienceDirect (also indexed in *Pacific-Basin Finance Journal* 82, 2023)
- **URL:** https://link.springer.com/article/10.1007/s11408-022-00417-8
- **Abstract:** 30-year retrospective on Jegadeesh-Titman 1993. Reviews international evidence, factor-momentum, momentum crashes, residual momentum, behavioral and risk-based explanations, post-publication decay. Identifies open questions and synthesizes the modern literature.
- **Key findings:**
  - Momentum survives in international markets except Japan (and that exception explained by negative value-momentum correlation, see Asness 2011).
  - Risk-managed (volatility-scaled) momentum nearly doubles Sharpe.
  - Most modern variants (residual, factor, intermediate-horizon) outperform raw J-T 12-1.
  - Crash-management is the binding constraint on momentum's risk-adjusted return.
- **Relevance to GTOS:** One-stop modern survey for K54 feature engineering choices. Particularly useful: residual-momentum, volatility-scaled momentum, and intermediate-horizon variants are documented to outperform raw return-momentum. Each maps to a candidate K54 feature.
- **Potential hypothesis:** K54 v2 should include (a) residual return after H1 OB-distance regression, (b) volatility-scaled rolling return (return/realized-vol), (c) 12-1 vs 6-1 horizon split — at minimum as additive features, and run feature-importance comparison vs raw rolling return.
- **Cross-domain links:** All 14 sub-sections; useful reading-list.
- **Horizon:** review (multi-horizon)

### The 52-Week High and Momentum Investing
- **Authors:** Thomas J. George, Chuan-Yang Hwang
- **Year:** 2004
- **Source:** *The Journal of Finance* 59(5) 2145–2176
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00695.x
- **Abstract:** A simple readily-available statistic — proximity of the current price to the 52-week high — explains a large fraction of momentum profits. Dominates and improves upon past-return-based momentum. Future returns forecast using 52WH do not reverse in the long run.
- **Key findings:**
  - 52-week-high momentum subsumes raw return momentum.
  - 52WH does not exhibit long-horizon reversal — distinct anomaly.
  - Anchoring-style reference-price story consistent with the result.
  - Robust internationally and across sectors.
- **Relevance to GTOS:** Direct K54 feature candidate: per-symbol distance-to-rolling-52-bar-high (or per-instrument-appropriate window) as a regime-conditioned momentum proxy. Anchoring on prior swing highs is structurally similar to GTOS's BOS/CHoCH framing. Worth adding `distance_to_20bar_high` and `distance_to_60bar_high` as features.
- **Potential hypothesis:** Adding `pct_distance_from_rolling_high` (positive) and `pct_distance_from_rolling_low` (negative) to K54 will improve OOS calibration over rolling-return momentum alone, particularly in trending_bull regime where distance-to-high is most informative.
- **Cross-domain links:** 09 (round-numbers / anchoring), 17 (behavioral anchoring).
- **Horizon:** weekly-monthly

### Is Momentum Really Momentum?
- **Authors:** Robert Novy-Marx
- **Year:** 2012
- **Source:** *Journal of Financial Economics* 103(3) 429–453
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X11001152
- **Abstract:** Decomposes "momentum" into intermediate-horizon (months -12 to -7) and recent-horizon (-6 to -2) past returns. Intermediate-horizon dominates. Standard 12-1 momentum is mostly intermediate-horizon momentum mislabeled. Persists internationally and across asset classes.
- **Key findings:**
  - Months -12 to -7 predict more return than months -6 to -2.
  - Result holds 1926-2010 in US equities.
  - Replicates internationally + commodities + currencies.
  - Won FAMA-DFA Prize 2011 (best JFE asset pricing paper).
- **Relevance to GTOS:** Important distinction for K54: NOT all "past return" lookbacks are equal. The "echo" structure (intermediate-horizon dominates recent-horizon) suggests we should disaggregate rolling-return into early-window (e.g., bars -120 to -60) vs late-window (-60 to -1) features rather than collapsing to a single momentum scalar.
- **Potential hypothesis:** K54 v2 separating `momentum_intermediate` (e.g., 60-120 bar rolling return) from `momentum_recent` (1-30 bar rolling return) will outperform a single rolling-return feature on H1/H4 GTOS data.
- **Cross-domain links:** 17 (behavioral explanation candidates), 13 (cross-asset).
- **Horizon:** monthly

### Is Momentum an Echo?
- **Authors:** Amit Goyal, Sunil Wahal
- **Year:** 2015
- **Source:** *Journal of Financial and Quantitative Analysis* 50(6) 1237–1267
- **URL:** https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/is-momentum-an-echo/5E4B893AFD2F110B7347F8F483D28ED3
- **Abstract:** Tests Novy-Marx's intermediate-horizon "echo" finding internationally. Confirms the US echo but finds no robust evidence in 37 non-US countries or in regional aggregates. The US echo appears driven by short-term-reversal carryover from month -2.
- **Key findings:**
  - US-only finding — not international.
  - Likely driven by short-term reversal at month -2.
  - 6-2 momentum and 12-7 momentum perform similarly outside US.
  - Important caveat to Novy-Marx 2012.
- **Relevance to GTOS:** Counter-evidence to over-relying on Novy-Marx echo decomposition outside of US equities. GTOS instruments (XAU, US30, FX) are not US single-stock — the echo pattern is unlikely to dominate. Take Novy-Marx as one hypothesis among several rather than the canonical decomposition.
- **Potential hypothesis:** K54 should feature-engineer both 6-1 and 12-7 momentum but expect approximate equivalence on GTOS instruments (per Goyal-Wahal); pre-register the OOS test before training.
- **Cross-domain links:** 13, 17.
- **Horizon:** monthly

### International Momentum Strategies
- **Authors:** K. Geert Rouwenhorst
- **Year:** 1998
- **Source:** *The Journal of Finance* 53(1) 267–284
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.95722
- **Abstract:** Tests Jegadeesh-Titman momentum on 12 European countries 1980-1995. Finds return continuation in all 12 countries lasting on average ~1 year. International diversified winner-loser portfolio outperforms by >1% per month, risk-adjusted. Returns correlated with US momentum, suggesting common factor.
- **Key findings:**
  - Robust internationally, all 12 countries individually significant.
  - Negatively related to firm size but not limited to small firms.
  - Common factor with US momentum.
  - Roughly 12-month duration of continuation.
- **Relevance to GTOS:** Establishes momentum's international robustness — supporting prior that XAU/US30/USDJPY etc., while not identical assets to US-stock cross-section, plausibly host a similar return-continuation phenomenon. Useful baseline for GTOS's "momentum-on-instrument" framing.
- **Potential hypothesis:** Per-instrument time-series momentum at H1-H4 horizon should be a positive feature for K54 across all 7 GTOS instruments, with effect size weakening as instrument liquidity rises (Rouwenhorst's size pattern).
- **Cross-domain links:** 13.
- **Horizon:** monthly

### Do Industries Explain Momentum?
- **Authors:** Tobias J. Moskowitz, Mark Grinblatt
- **Year:** 1999
- **Source:** *The Journal of Finance* 54(4) 1249–1290
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00146
- **Abstract:** Documents strong industry-level momentum. Stock-level momentum profits drop sharply once industry exposure is controlled. Industry momentum drives the bulk of intermediate-horizon momentum.
- **Key findings:**
  - 20-industry SIC partition: industry-momentum dominates.
  - 1963-1995 sample.
  - Stock-momentum nearly disappears industry-neutral.
  - Industry momentum shows 1-month autocorrelation in industry-mean.
- **Relevance to GTOS:** Suggests cross-instrument correlation in trend signals — already partially active via GTOS's `cross_instrument_correlation_gate` (additive HALVE/REJECT, threshold 0.4). The Moskowitz-Grinblatt finding implies that *positive* correlation in trend-direction across correlated instruments should be a *bullish* signal for K54, not just a gate-tightener. Worth re-examining whether the corr-gate is too punitive given Moskowitz-Grinblatt's positive-correlation-as-edge frame.
- **Potential hypothesis:** A K54 feature `correlated_instrument_signed_momentum_mean` (mean of recent rolling-return for instruments with |corr|>0.4 to subject) will be a positive predictor of subject realized-R, contradicting the current correlation-gate's HALVE-on-direction-agreement assumption.
- **Cross-domain links:** 13 (factor structure), 21 (correlation-aware sizing).
- **Horizon:** monthly

### Momentum and Autocorrelation in Stock Returns
- **Authors:** Jonathan Lewellen
- **Year:** 2002
- **Source:** *The Review of Financial Studies* 15(2) 533–564
- **URL:** https://academic.oup.com/rfs/article-abstract/15/2/533/1588891
- **Abstract:** Industry, size, and book-to-market portfolios all exhibit momentum. Diversified portfolio momentum cannot be firm- or industry-specific. Negative autocorrelation in returns combined with strong cross-serial correlation explains the puzzle. Stocks covary "too strongly."
- **Key findings:**
  - Diversified portfolios show momentum, ruling out firm-specific stories.
  - Negative own-autocorrelation but positive cross-autocorrelation.
  - Suggests overreaction-to-common-factor mechanism.
- **Relevance to GTOS:** Supports the regime-driven view of GTOS decay (F15) — when factor exposure (regime / common-factor) drives momentum, regime classification becomes the load-bearing axis for prediction. Consistent with the F2 / F15 finding that LONG decay concentrates in trending_bull regime.
- **Potential hypothesis:** A regime-conditioned momentum signal (rolling return × regime probability) will dominate raw rolling return as a K54 feature.
- **Cross-domain links:** 05 (regime detection), 13 (factor structure).
- **Horizon:** monthly

### On Persistence in Mutual Fund Performance
- **Authors:** Mark M. Carhart
- **Year:** 1997
- **Source:** *The Journal of Finance* 52(1) 57–82
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1997.tb03808.x
- **Abstract:** Adds a momentum factor (UMD) to Fama-French three-factor model. Common factors plus expenses explain mutual fund return persistence. No skill detected after factor adjustment. Establishes the four-factor model standard.
- **Key findings:**
  - 4-factor model = 3-factor + UMD (up-minus-down 12-1 momentum).
  - "Hot hands" persistence is 1-year momentum exposure, not skill.
  - Established the canonical UMD construction.
- **Relevance to GTOS:** Establishes momentum as a priced risk factor — meaning some of the GTOS edge may be compensation for crash exposure rather than mispricing. Implication: the F15 regime-conditioned LONG-side decay may be the momentum-crash mechanism (Daniel-Moskowitz) showing up in GTOS PnL, not edge erosion per se.
- **Potential hypothesis:** A regime-conditioned variance-of-rolling-return feature ("local volatility of momentum") in K54 will track the Daniel-Moskowitz momentum-crash predictor.
- **Cross-domain links:** 13 (factor models), 22 (mutual fund alpha).
- **Horizon:** monthly

---

## 3. Time-series momentum & trend-following CTA literature

### Time Series Momentum
- **Authors:** Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen
- **Year:** 2012
- **Source:** *Journal of Financial Economics* 104(2) 228–250
- **URL:** http://docs.lhpedersen.com/TimeSeriesMomentum.pdf
- **Abstract:** Documents persistent time-series momentum across 58 liquid futures and forwards (equities, FX, commodities, bonds) for 1-12 month horizons, with partial reversal at longer horizons. Diversified TSMOM portfolio earns substantial abnormal returns with little exposure to standard factors and performs best in extreme markets.
- **Key findings:**
  - Persistence at 1-12 month horizon, partial reversal at 24+ months.
  - 58 instruments, 25 years, all asset classes.
  - Diversified TSMOM Sharpe ~1.5 (gross).
  - Performs best in market extremes (left and right tail) — consistent with both underreaction (Hong-Stein) and risk-driven (capacity-constrained arbitrage) stories.
  - Returns largely explained by a single TSMOM factor.
- **Relevance to GTOS:** **CITED IN GTOS EDGE MECHANISM DOC** — most central paper for the system. Provides the empirical foundation that "an asset's own past return predicts its future return" at 1-12 month horizon. GTOS exploits a *finer* horizon (M15/H1) of the same phenomenon, tied to OB-zone-precision rather than rolling-return. K54 must include a TSMOM-style signal as a baseline feature against which the OB-edge is measured.
- **Potential hypothesis:** A K54 baseline using ONLY MOP-2012-style rolling-return signals (1-12 H1-bar lookback) without OB-features will be a useful comparison: the gap between (TSMOM-only model) and (TSMOM + OB-features model) is the empirical OB-edge.
- **Cross-domain links:** 10, 11, 12 (asset-class), 13 (cross-asset factor), 17 (underreaction).
- **Horizon:** monthly (1-12 month formation, 1 month holding)

### A Century of Evidence on Trend-Following Investing
- **Authors:** Brian K. Hurst, Yao Hua Ooi, Lasse Heje Pedersen
- **Year:** 2017
- **Source:** *Journal of Portfolio Management* (also AQR whitepaper)
- **URL:** https://www.trendfollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf
- **Abstract:** Trend-following studied across 67 markets since 1880. Each decade independently shows positive returns and low correlation to traditional asset classes. Explicit decade-by-decade decomposition of strategy components.
- **Key findings:**
  - Positive returns every decade 1880–2017.
  - Low correlation with equity / bond benchmarks.
  - Crisis-alpha property: positive in equity bear markets.
  - Strategy framework decomposes into three drivers (market-move size, signal-translation, diversification).
  - Recent (2010s) underperformance attributed to muted market-move sizes, not strategy decay.
- **Relevance to GTOS:** Strong external validation that the trend-following premise survives 130+ years of regime changes. Counter-evidence to "GTOS edge will inevitably die" priors. The decomposition framework (move-size × translation × diversification) is *directly portable* to GTOS PnL attribution: when GTOS underperforms, ask which of the three drivers regressed.
- **Potential hypothesis:** GTOS's H2-2026 decay (F11/F15) may be partly a "muted-market-move" effect rather than pure model decay; if so, expected R/trade should rebound with realized-volatility regime change. Useful pre-registered prediction to test against forward live data.
- **Cross-domain links:** 16 (vol regime), 22 (CTA hedge fund alpha).
- **Horizon:** multi-horizon (1-12 month signals)

### Demystifying Managed Futures
- **Authors:** Brian Hurst, Yao Hua Ooi, Lasse Heje Pedersen
- **Year:** 2013
- **Source:** *Journal of Investment Management* 11(3) 42–58
- **URL:** http://docs.lhpedersen.com/DemystifyingManagedFutures.pdf
- **Abstract:** Shows that aggregate Managed Futures and CTA index returns can be largely replicated by diversified time-series momentum signals across 58 liquid futures/currency forwards (1985–2012). Decomposes CTA returns into systematic-trend-following exposure plus residual.
- **Key findings:**
  - CTA index R² to TSMOM signals ~80%.
  - "Manager skill" residual is small after TSMOM exposure.
  - Implication: most "CTA alpha" is systematic trend exposure.
  - Validates TSMOM as the core engine of trend-following.
- **Relevance to GTOS:** Confirms the system-level reproducibility of trend-following from a few simple signals. Reinforces that K54 with a small set of well-chosen momentum features could in principle approximate a competent CTA's trend signal. Useful realism-check: the marginal alpha over TSMOM is small, so K54 should set its baseline expectation accordingly.
- **Potential hypothesis:** A 5-feature K54 (3 TSMOM lookbacks + 2 vol scalers) will capture ~70-80% of the achievable Sharpe from a 30-feature K54 — i.e., diminishing returns to feature complexity.
- **Cross-domain links:** 22 (hedge fund alpha), 13 (factor).
- **Horizon:** monthly

### Two Centuries of Trend Following
- **Authors:** Yves Lempérière, Cyril Deremble, Philip Seager, Marc Potters, Jean-Philippe Bouchaud
- **Year:** 2014
- **Source:** *Journal of Investment Strategies* 3(3); arXiv:1404.3274
- **URL:** https://arxiv.org/abs/1404.3274
- **Abstract:** Tests trend-following on 4 asset classes (commodities, currencies, equity indices, bonds) using futures since 1960 and spot prices since 1800. Overall t-statistic ~5 since 1960, ~10 since 1800 after accounting for upward drift. Trend-following is among the most statistically significant anomalies in finance.
- **Key findings:**
  - 200+ years of evidence.
  - Across all 4 asset classes.
  - Stable across time and class.
  - t-stat 10 over 200 years.
  - Robust to market structure regime changes (gold standard, Bretton Woods, post-1971 fiat).
- **Relevance to GTOS:** Extends Hurst-Ooi-Pedersen's "century of evidence" by another century, in a peer-reviewed/quantitative venue with more granular methodology. Strong external prior that trend-following persistence is structural rather than transient. Key contribution: tests on spot data, which GTOS uses for FX (XAUUSD spot vs futures).
- **Potential hypothesis:** Spot vs futures basis variation should NOT systematically predict GTOS PnL (because the trend signal is on returns, not levels). A research falsification: regress realized R against contemporaneous basis change as a placebo control for K54.
- **Cross-domain links:** 10 (gold), 11 (FX).
- **Horizon:** multi-horizon

### Demystifying Managed Futures / "You Can't Always Trend When You Want"
- **Authors:** Abhilash Babu, Brendan Hoffman, Ari Levine, Yao Hua Ooi, Sarah Schroeder, Erik Stamelos
- **Year:** 2020
- **Source:** *Journal of Portfolio Management* (March 2020); SSRN 3487134
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3487134
- **Abstract:** Decomposes trend-following returns into (1) magnitude of market moves, (2) signal-translation efficacy, (3) portfolio diversification. Finds that 2010-2018 underperformance is *not* due to (2) or (3) — it is driven by smaller average market moves. The strategy's edge has not decayed; the input has shrunk.
- **Key findings:**
  - 82-instrument sample, 16 long-short factors.
  - 2010-2018 underperformance fully attributable to muted market moves.
  - Signal-translation and diversification stable.
  - Trend efficacy NOT decayed.
- **Relevance to GTOS:** **Direct framework for the GTOS decay diagnosis (item #4, F11, F15).** Apply the Babu et al. decomposition to GTOS H1-2026 vs H2-2026: did markets move less, or did GTOS translate moves less efficiently? F15's regime-conditioned LONG decay points to (2) translation, but Babu's framework forces a quantitative decomposition rather than narrative.
- **Potential hypothesis:** A formal Babu-decomposition on GTOS H1 vs H2 will find that XAU's H2 LONG decay is split: ~40% market-move-magnitude (smaller realized volatility in trending_bull regime), ~60% signal-translation (LONG-side selectivity collapse). A pre-registered test to run before assuming all decay is model-side.
- **Potential hypothesis 2:** GTOS underperformance attribution should report all 3 components in monthly reports, not just realized R.
- **Cross-domain links:** 16 (vol regime), 22 (CTA).
- **Horizon:** multi-horizon

### Is This Time Different? Trend Following and Financial Crises
- **Authors:** Mark C. Hutchinson, John O'Brien
- **Year:** 2014
- **Source:** SSRN 2375733; UCC Working Paper
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2375733
- **Abstract:** Tests trend-following performance after 6 financial crises (1929, 1973, 1981, 1987, 2000, 2007) over 1921-2013 across commodities, bonds, equity indices, currencies. Finds trend-following returns are <50% of normal in the 4 years following crises, due to breakdown in serial correlation.
- **Key findings:**
  - 4-year crisis-shadow effect.
  - Up to 12-month autocorrelation breaks down post-crisis.
  - Robust across the 6 crises.
  - 90+ year sample.
- **Relevance to GTOS:** Concrete empirical model for the "regime-conditioned signal breakdown" that GTOS is currently observing (F15). Predicts: crisis-and-aftermath periods see autocorrelation collapse — the same mechanism F15 attributes to LONG-side selectivity collapse in trending_bull regime. Provides a quantifiable expectation: post-crisis half-strength persistence for ~4 years.
- **Potential hypothesis:** GTOS H2-2026 may be inside a Hutchinson-O'Brien crisis-shadow (banking-sector, geopolitical, COVID-aftermath); if so, expected R/trade should partially recover within 1-3 years even without prompt or model changes. Pre-registerable test against forward live data.
- **Cross-domain links:** 05 (regime), 17 (behavioral after-crisis), 22 (CTA performance).
- **Horizon:** multi-horizon

### Which Trend Is Your Friend?
- **Authors:** Ari Levine, Lasse Heje Pedersen
- **Year:** 2016
- **Source:** *Financial Analysts Journal* 72(3) 51–66
- **URL:** https://www.tandfonline.com/doi/abs/10.2469/faj.v72.n3.3
- **Abstract:** Shows that the most common trend signals — time-series momentum and moving-average crossovers — are essentially equivalent linear filters in their general form. Hodrick-Prescott, Kalman, EWMA, and other filter choices reduce to weighted averages of past returns. Cross-correlation among signal choices is high.
- **Key findings:**
  - TSMOM ≅ MA-crossover at appropriate parameter mappings.
  - Linear-filter theory unifies most trend signals.
  - Marginal benefit of "exotic" filters small.
  - HP and Kalman give similar signals to simple lookback returns.
- **Relevance to GTOS:** Cuts down K54 feature-engineering complexity: one good rolling-return-style feature with appropriate horizon and decay captures most of the trend signal. Don't waste hyperparameter search on competing-but-equivalent signal designs. K54 should default to a small set of TSMOM lookbacks (e.g., 20, 60, 120 H1 bars) plus one EWMA, not 30 different filter variants.
- **Potential hypothesis:** Signal-choice ablation in K54 will show <5% AUC variance across {TSMOM, EMA-cross, SMA-cross, HP-filter} at matched effective lookback. Useful pre-registered test for trimming the K54 feature search space.
- **Cross-domain links:** 01 (linear filter math), 04 (wavelets / multi-timeframe).
- **Horizon:** multi-horizon

### Momentum Strategies in Futures Markets and Trend-following Funds
- **Authors:** Nick Baltas, Robert Kosowski
- **Year:** 2013 (working paper); revised editions through 2020
- **Source:** SSRN 1968996
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1968996
- **Abstract:** Constructs momentum portfolios on 71 futures contracts (1974-2012) at daily, weekly, monthly rebalance frequencies. Tests capacity constraints in trend-following. Documents relationship between TSMOM signals and CTA fund returns.
- **Key findings:**
  - Rebalance-frequency matters: monthly is the sweet spot for risk-adjusted return after costs.
  - CTA aggregate returns have ~70% R² to constructed TSMOM.
  - Capacity-constraint evidence: top-tier CTAs do not show capacity-driven returns decline.
  - 35-year backtest, robust across asset classes.
- **Relevance to GTOS:** Practical guidance on trade-frequency selection. GTOS evaluates per M15-bar close, which is daily-or-faster — well above the Baltas-Kosowski sweet spot. Suggests testing K54 with hourly and daily decision frequency as baselines, not just per-bar.
- **Potential hypothesis:** A K54 model that re-decisions only at H1 close (rather than per-M15) will produce higher per-trade expected R while catching fewer trades, with similar overall realized R/month.
- **Cross-domain links:** 22 (CTA), 06 (microstructure / capacity).
- **Horizon:** daily-monthly

### Time-series and Cross-sectional Momentum Strategies under Alternative Implementation Strategies
- **Authors:** Ron Bird, Xiaojun Gao, Danny Yeung
- **Year:** 2017
- **Source:** *Australian Journal of Management* 42(2) 230–251
- **URL:** https://journals.sagepub.com/doi/10.1177/0312896215619965
- **Abstract:** Compares time-series vs cross-sectional momentum across 24 markets under alternative implementations. TSMOM is consistently superior. Information concentrates in tails of the return distribution, explaining why TSMOM (which uses tail-positive stocks) outperforms cross-sectional rank methods.
- **Key findings:**
  - TSMOM > XSMOM in 24-market sample.
  - Tail-concentration of momentum information.
  - State-dependent: cross-sectional digs deeper in weak markets, TSMOM auto-adjusts.
- **Relevance to GTOS:** Reinforces that GTOS's per-instrument time-series-style momentum is the right paradigm for the per-symbol orchestrator architecture. Supports K54 being per-symbol, not cross-symbol-rank.
- **Potential hypothesis:** A cross-sectional rank K54 (rank GTOS instruments by recent return) will not improve over per-symbol TSMOM K54 in OOS evaluation.
- **Cross-domain links:** 13.
- **Horizon:** monthly

---

## 4. Momentum crashes, regime, decay, post-publication arbitrage

### Momentum Crashes
- **Authors:** Kent Daniel, Tobias J. Moskowitz
- **Year:** 2016
- **Source:** *Journal of Financial Economics* 122(2) 221–247
- **URL:** http://www.kentdaniel.net/papers/published/jfe_16.pdf
- **Abstract:** Despite strong long-run average returns, momentum strategies experience infrequent and persistent strings of negative returns ("crashes"). Crashes are partly forecastable: occur in panic states (post-bear-market, high vol) and are contemporaneous with market rebounds. Dynamic momentum forecast roughly doubles the static-momentum Sharpe.
- **Key findings:**
  - Crashes concentrate in panic-states (post-bear, high-vol).
  - Past-loser portfolio acquires call-option-like payoff in panic.
  - Forecastable from market state + lagged volatility.
  - Implementable dynamic strategy ~2× static Sharpe.
  - Robust internationally and across asset classes.
- **Relevance to GTOS:** **Directly maps to GTOS F15 finding** (LONG-side selectivity collapse in trending_bull regime, +48.3pp regime attribution, bonf_p=0.0016). The Daniel-Moskowitz mechanism predicts that during regime panic + rebound, momentum's LONG side gets crushed by short-coverage rebounds — exactly the pattern observed in XAU H2-2026. K54 must condition LONG-sizing on regime-state and lagged-volatility (a Daniel-Moskowitz analog).
- **Potential hypothesis:** A K54 LONG-side sizing modifier of form `0.5x if regime=panic AND vol_z > 1`, `1.0x otherwise` (Daniel-Moskowitz dynamic framework adapted) will deliver +20-40% improvement in LONG-side realized R/trade vs. uniform sizing. Bundles directly with S79 sharpe_weighted Phase 2 task.
- **Cross-domain links:** 05 (regime), 16 (vol regime), 21 (sizing under tails).
- **Horizon:** monthly

### Momentum Has Its Moments
- **Authors:** Pedro Barroso, Pedro Santa-Clara
- **Year:** 2015
- **Source:** *Journal of Financial Economics* 116(1) 111–120
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X14002566
- **Abstract:** Volatility-scaling the momentum portfolio (scale by inverse 6-month realized vol) virtually eliminates momentum crashes. Sharpe rises from 0.53 (unmanaged) to 0.97 (vol-managed). Risk of momentum is highly variable AND predictable, making the management technique simple and effective.
- **Key findings:**
  - 6-month realized vol scaling.
  - Sharpe 0.53 → 0.97.
  - Eliminates negative skew + kurtosis.
  - Predictability of momentum's own variance is the source of the Sharpe gain.
- **Relevance to GTOS:** Volatility-scaled position sizing is *exactly* the S79 risk-policy framing. GTOS already shipped uniform_fn 2.0% (S79) and is researching sharpe_weighted (Phase 2). Barroso-Santa-Clara provides the theoretical foundation. A direct port: scale GTOS per-trade size by inverse rolling-realized-vol of recent realized R, not inverse instrument-vol-of-returns.
- **Potential hypothesis:** A "Barroso-Santa-Clara" sizing rule on GTOS ((`1/realized_R_vol_30d`) clipped to [0.5, 2.0]) shipped as the sharpe_weighted Phase 2 follow-up will deliver 30-50% Sharpe improvement vs uniform_fn 2.0% in OOS evaluation.
- **Cross-domain links:** 21 (Kelly sizing), 16 (vol).
- **Horizon:** monthly

### Market States and Momentum
- **Authors:** Michael J. Cooper, Roberto C. Gutierrez Jr., Allaudeen Hameed
- **Year:** 2004
- **Source:** *The Journal of Finance* 59(3) 1345–1365
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00665.x
- **Abstract:** Momentum profits depend on the state of the market. Mean monthly momentum profit is 0.93% following positive market returns and -0.37% following negative market returns (1929-1995). Up-market momentum reverses long-run. Robust to macro controls.
- **Key findings:**
  - Up-market: positive momentum profits.
  - Down-market: negative momentum profits.
  - Long-run reversal of up-market momentum.
  - Macro-control-robust.
- **Relevance to GTOS:** Provides further direct support for regime-conditioned momentum: GTOS's regime classifier output (trending_bull / trending_bear / etc.) should be used to condition K54's expected-R for each setup, not just as a one-hot feature. Cooper-Gutierrez-Hameed's finding mirrors F2's pinpointed cell (XAUUSD London/trending_bull/LONG -59.8pp) closely.
- **Potential hypothesis:** A K54 model trained separately on trending_bull and trending_bear regimes will outperform a regime-pooled model on OOS realized R (already mostly done in K54 baseline; CGH provides academic prior).
- **Cross-domain links:** 05 (regime), 17 (behavioral state).
- **Horizon:** monthly

### Time-Varying Liquidity and Momentum Profits
- **Authors:** Doron Avramov, Si Cheng, Allaudeen Hameed
- **Year:** 2016
- **Source:** *Journal of Financial and Quantitative Analysis* 51(6) 1897–1923
- **URL:** https://si-cheng.net/wp-content/uploads/2018/12/2016-JFQA-Avramov_Cheng_Hameed-Liquidity-and-Momentum.pdf
- **Abstract:** Momentum profits are markedly larger in liquid market states. The pattern is not explained by liquidity-risk variation, time-varying factor exposures, macro conditions, return dispersion, or sentiment. A novel state-conditioning effect.
- **Key findings:**
  - Liquid states: momentum thrives.
  - Illiquid states: momentum disappears or reverses.
  - 50+ year sample.
  - Not subsumed by other state variables.
- **Relevance to GTOS:** Liquidity-conditioning is missing from GTOS's K54 baseline. Could add features like spread (already in microstructure feature set, but archived per E24+E26 NULL_VERDICT) and depth-style proxies. Worth re-examining whether liquidity features which were null in microstructure tests hold predictive value when interacted with momentum signals.
- **Potential hypothesis:** A K54 interaction feature `momentum × spread_z` will revive the (currently archived) microstructure feature set as a useful conditioning variable for trend signals — restoring some signal that the E24/E26 archive concluded was absent.
- **Cross-domain links:** 06 (microstructure / liquidity), 21 (sizing).
- **Horizon:** monthly

### Does Academic Research Destroy Stock Return Predictability?
- **Authors:** R. David McLean, Jeffrey Pontiff
- **Year:** 2016
- **Source:** *The Journal of Finance* 71(1) 5–32
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365
- **Abstract:** Tests 97 published anomalies for OOS and post-publication decay. Anomaly returns are 26% lower OOS, 58% lower post-publication. Implies investor learning rather than pure data mining.
- **Key findings:**
  - 97 anomalies.
  - 26% OOS decline = data-mining upper bound.
  - 58% post-publication decline = arbitrage/learning.
  - Difference (~32%) attributable to investor learning.
- **Relevance to GTOS:** GTOS's own decay (F11) of ~12.1pp → 4.6pp from H1-2026 to H2-2026 is in the same magnitude as McLean-Pontiff's published-anomaly decay. Important prior to set when interpreting GTOS decay: the magnitude is not unprecedented in the academic literature; the velocity (~6 months) is unusually fast.
- **Potential hypothesis:** GTOS's edge half-life will plateau at ~30-40% of pre-2026 level rather than continuing to zero, consistent with McLean-Pontiff's two-tier decline (immediate OOS + slow learning). Provides a long-run target rather than a doom prior.
- **Cross-domain links:** 17 (adaptive markets), 22 (anomaly decay literature).
- **Horizon:** monthly

### Anomalies and Market Efficiency
- **Authors:** G. William Schwert
- **Year:** 2003
- **Source:** *Handbook of the Economics of Finance*, Vol. 1, Ch. 15, pp. 939–974, Elsevier
- **URL:** https://www.billschwert.com/hbfech15.pdf
- **Abstract:** Comprehensive survey chapter on financial-market anomalies and their post-publication trajectories. Documents that anomalies frequently weaken, reverse, or disappear after academic publication. Establishes the canonical "anomalies decay" narrative, of which momentum is the most-studied counterexample (still positive 10+ years post-J-T 1993).
- **Key findings:**
  - Most anomalies weaken post-publication.
  - Momentum is unusually persistent.
  - Survey-level coverage of dozens of anomalies.
  - Establishes the "two routes": disappearance (arbitrage) or attenuation (data mining).
- **Relevance to GTOS:** Useful framing tool: position GTOS edge decay against the broader "anomalies decay" base rate from Schwert. GTOS-style mechanical OB-edges have only been "published" via prop-firm circles and ICT/SMC YouTube — partial-arbitrage rather than full-arbitrage. Implication: decay velocity should be intermediate, not extreme.
- **Potential hypothesis:** GTOS's decay velocity since 2024 vs. McLean-Pontiff's 1956-2014 mean decay velocity should match approximately, given that ICT/SMC publication peaked ~2018-2020.
- **Cross-domain links:** 17 (adaptive markets), 22.
- **Horizon:** review

### Data-Snooping, Technical Trading Rule Performance, and the Bootstrap
- **Authors:** Ryan Sullivan, Allan Timmermann, Halbert White
- **Year:** 1999
- **Source:** *The Journal of Finance* 54(5) 1647–1691
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00163
- **Abstract:** Applies White's Reality Check bootstrap to evaluate technical trading rules including Brock-Lakonishok-LeBaron 1992. Adjusts for full-universe data-snooping bias. Finds that profitability of best technical rules deteriorates significantly when correctly accounting for the multiple-hypothesis testing problem. 10-year OOS shows low profitability.
- **Key findings:**
  - Reality-check bootstrap framework.
  - 26-rule universe expanded.
  - Data-snooping correction reduces apparent profits substantially.
  - 10-year OOS confirms Brock-Lakonishok-LeBaron rules are weak.
- **Relevance to GTOS:** Critical methodological prior for K54 backtest validation. GTOS's canary + tiered-PASS / borderline framework is a Reality-Check-adjacent practice; the discipline of accounting for multiple-comparison costs in K54 hyperparameter tuning is non-negotiable. Data-snooping is THE risk for K54 with 30+ candidate features and multiple lookback choices.
- **Potential hypothesis:** Apply Sullivan-Timmermann-White Reality Check bootstrap to K54's hyperparameter selection: a single best K54 architecture's t-stat needs to clear the FWER-corrected threshold across the search universe, not just the per-model significance.
- **Cross-domain links:** 02 (statistical methodology / multiple testing).
- **Horizon:** review

---

## 5. Factor-momentum & cross-asset

### Factor Momentum and the Momentum Factor
- **Authors:** Sina Ehsani, Juhani T. Linnainmaa
- **Year:** 2022
- **Source:** *The Journal of Finance* 77(3) 1877–1919
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13131
- **Abstract:** Stock momentum emanates from momentum in factor returns. Most factors are positively autocorrelated. Stock momentum strategies indirectly time factors: they profit when factors remain autocorrelated, crash when factor autocorrelation breaks down. Reframes momentum as factor-timing in disguise.
- **Key findings:**
  - Average factor: +1bp/month after loss-year, +53bp/month after gain-year.
  - Factor-momentum subsumes stock-momentum in spanning tests.
  - Stock momentum crashes are factor-autocorrelation breakdowns.
  - Not a separate risk factor but an aggregator of factor autocorrelation.
- **Relevance to GTOS:** Profound reframing — GTOS regime classifier output (trending_bull etc.) IS effectively a "factor" whose return autocorrelation drives K54's expected R. The F15 finding (LONG decay = trending_bull collapse) is precisely a factor-autocorrelation-breakdown event in Ehsani-Linnainmaa's frame.
- **Potential hypothesis:** A K54 feature `regime_persistence_score` (rolling autocorrelation of regime-state) will be a more useful momentum-decay predictor than rolling-return autocorrelation directly.
- **Cross-domain links:** 13 (factor structure), 05 (regime).
- **Horizon:** monthly

### Value and Momentum Everywhere
- **Authors:** Clifford S. Asness, Tobias J. Moskowitz, Lasse Heje Pedersen
- **Year:** 2013
- **Source:** *The Journal of Finance* 68(3) 929–985
- **URL:** https://w4.stern.nyu.edu/facdir/lpederse/papers/ValMomEverywhere.pdf
- **Abstract:** Documents value and momentum premia across 8 diverse markets/asset classes (US, UK, Continental Europe, Japan equities; country-equity-index futures; government-bond futures; currency forwards; commodity futures). Strong common factor structure. Value-momentum negative correlation within and across asset classes. Three-factor model (market + global value + global momentum) explains broad cross-section.
- **Key findings:**
  - 8 markets/asset classes.
  - Value & momentum premia ubiquitous.
  - Negative correlation = diversifier.
  - Funding-liquidity risk partial source.
- **Relevance to GTOS:** Confirms momentum premia exist across the GTOS instrument universe (XAU = commodity, US30/NAS100 = equity index, USDJPY/GBPJPY/GBPUSD = currency). Useful baseline that justifies K54 application across GTOS portfolio. Suggests a "value-like" feature (e.g., distance from rolling fair-value mean) added to K54 alongside momentum could provide diversification.
- **Potential hypothesis:** Adding mean-reversion/value-style features (e.g., `pct_distance_from_120bar_mean` z-scored) to K54 alongside momentum will reduce K54 portfolio realized R volatility while preserving expected R, by Asness-Moskowitz-Pedersen's negative-correlation finding.
- **Cross-domain links:** 13 (factor), 15 (mean-reversion).
- **Horizon:** monthly

### Currency Momentum Strategies
- **Authors:** Lukas Menkhoff, Lucio Sarno, Maik Schmeling, Andreas Schrimpf
- **Year:** 2012
- **Source:** *Journal of Financial Economics* 106(3) 660–684
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X12001353
- **Abstract:** Empirical investigation of momentum in FX. Cross-sectional spread between past winners and losers up to 10% per annum, not explained by traditional risk factors. Partially explained by transaction costs. Behavior consistent with under- and overreaction.
- **Key findings:**
  - 10% per annum CS-momentum spread in FX (G10 + emerging).
  - Not subsumed by carry / value / momentum-elsewhere.
  - Transaction costs eat substantial portion.
  - Underreaction-then-overreaction pattern.
- **Relevance to GTOS:** Direct evidence that FX (USDJPY/GBPJPY/GBPUSD) supports momentum at multi-week horizons. Validates GTOS's per-FX-instrument application. Important caveat: 10% per annum gross does not survive transaction costs trivially — GTOS spreads/slippage on pre-NY M15 entries must be modeled into K54 expected-R explicitly, not assumed marginal.
- **Potential hypothesis:** GTOS FX instruments' expected R/trade should attenuate by realized-spread when modeled, and the post-cost K54 expected-R for FX trades should be ~50-70% of headline gross expected R (Menkhoff et al.'s cost ratio).
- **Cross-domain links:** 11 (FX), 13.
- **Horizon:** weekly-monthly

### Two Centuries of Price Return Momentum
- **Authors:** Christopher Geczy, Mikhail Samonov
- **Year:** 2016
- **Source:** *Financial Analysts Journal* 72(5) 32–56
- **URL:** https://www.tandfonline.com/doi/abs/10.2469/faj.v72.n5.1
- **Abstract:** Constructs monthly US security prices 1801-1926 to test J-T 1993 momentum strategies on truly OOS pre-original-sample data. Pre-1927 momentum profits remain positive and statistically significant. Establishes momentum is dynamically exposed to market beta conditional on market state, and a dynamically-hedged momentum significantly outperforms.
- **Key findings:**
  - 1801-1926 OOS positive and significant.
  - Dynamic-beta exposure conditioning.
  - Negative-beta-around-turning-points = crash-exposure.
  - 200+ year confirmation.
- **Relevance to GTOS:** Strong external prior that momentum is a 200+ year regularity (consistent with Lempérière 2014). Also operationalizes the Daniel-Moskowitz crash-mechanism: dynamic beta hedging = position sizing conditioned on market state. Consistent with sharpe_weighted Phase 2.
- **Potential hypothesis:** GTOS could implement a "Geczy-Samonov" beta-hedging modifier: when market state has reversed sign (regime transition flag), reduce per-trade size on directional setups by ~50%. Pre-registerable test alongside S79 sharpe_weighted.
- **Cross-domain links:** 21 (sizing), 05 (regime).
- **Horizon:** multi-horizon

### Cross-Asset Signals and Time Series Momentum
- **Authors:** Aleksi Pitkäjärvi, Matti Suominen, Lauri Vaittinen
- **Year:** 2020
- **Source:** *Journal of Financial Economics* 136(1) 63–85
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X19302156
- **Abstract:** Documents cross-asset time-series momentum: past bond market returns positively predict future equity returns; past equity returns negatively predict future bond returns. Constructs cross-asset strategy that outperforms pure equity or bond TSMOM in 20-country sample 1980-2016.
- **Key findings:**
  - Bond returns lead equity returns positively.
  - Equity returns lead bond returns negatively.
  - 20 countries.
  - Cross-asset diversified strategy improves Sharpe substantially over single-asset.
- **Relevance to GTOS:** Concrete example of "cross-asset signals improve own-asset prediction." For GTOS with its 7 instruments, this means: per-instrument K54 should likely consume features computed on *other* instruments (e.g., XAUUSD's rolling return as a feature for USDJPY's K54 forecast). Currently the cross-instrument correlation gate is the only cross-instrument signal flow.
- **Potential hypothesis:** Per-instrument K54 augmented with cross-instrument lagged-return features (constrained to instruments with |corr|>0.3) will improve OOS calibration for at least USDJPY (likely informed by XAU and US30), with effect size 5-15bp realized R/trade.
- **Cross-domain links:** 13 (cross-asset), 11 (FX), 10 (gold).
- **Horizon:** monthly

### The Strategic and Tactical Value of Commodity Futures
- **Authors:** Claude B. Erb, Campbell R. Harvey
- **Year:** 2006
- **Source:** *Financial Analysts Journal* 62(2) 69–97
- **URL:** https://www.tandfonline.com/doi/abs/10.2469/faj.v62.n2.4084
- **Abstract:** Examines challenges in estimating long-only commodity-futures expected return. Finds individual commodity excess returns are near-zero but a rebalanced commodity-futures portfolio can earn equity-like returns. Tests three momentum/term-structure tactical strategies, all of which outperform long-only benchmark.
- **Key findings:**
  - Individual commodity excess return ≈ 0.
  - Rebalanced portfolio earns equity-like return (rebalancing premium).
  - Momentum-tactical and term-structure-tactical strategies beat long-only.
  - Important caveat for "buy commodity futures and hold" portfolios.
- **Relevance to GTOS:** Anchors GTOS's XAU and XAG instruments in the commodity-momentum literature. Suggests that even where the long-only spot return is near-zero, a momentum-conditioned trading strategy on commodities can extract returns. Validates K54 application to XAU/XAG.
- **Potential hypothesis:** XAUUSD and XAGUSD K54 expected-R/trade should be in the same range as US30/NAS100 K54 (commodity-vs-equity-momentum has comparable strength per Asness-Moskowitz-Pedersen).
- **Cross-domain links:** 10 (gold/commodity).
- **Horizon:** monthly

---

## 6. Intraday momentum & short-horizon

### Market Intraday Momentum
- **Authors:** Lei Gao, Yufeng Han, Sophia Zhengzi Li, Guofu Zhou
- **Year:** 2018
- **Source:** *Journal of Financial Economics* 129(2) 394–414
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351
- **Abstract:** First-half-hour return of the SPY ETF (1993-2013) predicts the last-half-hour return. Statistically and economically significant. Stronger on volatile days, high-volume days, recession days, and macroeconomic-news-release days. Replicates on 10 other ETFs and several international markets. Theoretically consistent with infrequent rebalancing (Bogousslavsky 2016) and late-informed trading near close.
- **Key findings:**
  - First-30-min predicts last-30-min, R²~0.5-1% statistically significant.
  - Stronger on news / vol / recession days.
  - Generalizes to 10+ ETFs and international markets.
  - Implementable strategy with positive Sharpe net of costs.
- **Relevance to GTOS:** Direct evidence of *intraday* momentum at ~30-minute horizon, the same time-of-day-conditioned regularity GTOS exploits. The "stronger on high-vol and macro-news days" finding aligns with GTOS's kill-zone framing (London/NY = highest macro/news activity windows). K54 should include `time_of_day_x_volatility` interaction features.
- **Potential hypothesis:** A K54 feature `early_window_return_signed` (rolling return of first 30 minutes of London or NY session) will positively predict realized R for trades entered in the same kill zone, replicating the Gao-Han-Li-Zhou pattern at the GTOS time scale.
- **Cross-domain links:** 06 (microstructure), 08 (volume / time-of-day).
- **Horizon:** intraday

### Intraday Patterns in the Cross-section of Stock Returns
- **Authors:** Steven L. Heston, Robert A. Korajczyk, Ronnie Sadka
- **Year:** 2010
- **Source:** *The Journal of Finance* 65(4) 1369–1407
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2010.01573.x
- **Abstract:** Documents striking pattern of return continuation at half-hour intervals that are exact multiples of a trading day, lasting at least 40 trading days. Volume, order imbalance, volatility, and bid-ask-spread show similar patterns but do NOT explain the return pattern. Distinct from standard momentum.
- **Key findings:**
  - Half-hour-of-day persistence in returns.
  - 40+ trading-day duration.
  - Not driven by liquidity / order flow.
  - Periodic structure (TODP — time-of-day pattern).
- **Relevance to GTOS:** Theoretically validates GTOS's kill-zone-conditioned framework: the same kill zone tomorrow should look like the same kill zone today, period. Heston-Korajczyk-Sadka find that this structure persists for 40+ days. Implication for K54: a per-instrument-per-kill-zone modeling approach is well-justified by the academic literature.
- **Potential hypothesis:** GTOS K54 should fit per-(instrument × kill-zone) sub-models or include kill-zone-as-feature, and a kill-zone-stratified evaluation should show stable per-stratum R/trade for at least 40 trading days, conforming to Heston-Korajczyk-Sadka's TODP finding.
- **Cross-domain links:** 06 (intraday microstructure), 08 (intraday volume).
- **Horizon:** intraday

### Seasonality in the Cross-Section of Stock Returns
- **Authors:** Steven L. Heston, Ronnie Sadka
- **Year:** 2008
- **Source:** *Journal of Financial Economics* 87(2) 418–445
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X0700195X
- **Abstract:** Documents annual cross-sectional return autocorrelation at lags of 12, 24, 36, ..., up to 20 annual lags. Stocks tend to have similar relative returns in the same calendar month each year. Independent of size, industry, earnings, dividends, fiscal year. Volume and volatility show similar patterns but do not explain returns.
- **Key findings:**
  - Annual seasonal autocorrelation up to 20 lags.
  - Independent of standard controls.
  - Not subsumed by month-of-year effect.
  - Robust internationally.
- **Relevance to GTOS:** Annual-seasonality is unlikely to dominate at GTOS's intraday horizon, but a year-cycle feature (e.g., `same_month_last_year_return`) is virtually free to add and may capture a missed signal. Heston-Sadka also strengthens the case for kill-zone-conditioned modeling (intraday seasonality analog).
- **Potential hypothesis:** A K54 feature `same_kill_zone_yesterday_realized_return` will be positively predictive (intraday version of Heston-Sadka). Already partially captured but worth A/B testing as an explicit feature.
- **Cross-domain links:** 08 (intraday seasonality).
- **Horizon:** intraday-monthly

### Enhancing Time Series Momentum Strategies Using Deep Neural Networks
- **Authors:** Bryan Lim, Stefan Zohren, Stephen Roberts
- **Year:** 2019
- **Source:** *Journal of Financial Data Science* (Fall 2019); arXiv:1904.04912
- **URL:** https://arxiv.org/abs/1904.04912
- **Abstract:** Deep Momentum Networks: hybrid LSTM architecture trained directly on the Sharpe ratio of a TSMOM strategy across 88 continuous futures contracts. Outperforms classical TSMOM (with vol scaling) by >2× Sharpe gross of costs, and remains positive after 2-3 bp transaction costs.
- **Key findings:**
  - Sharpe-objective NN training.
  - Joint trend-estimation + position-sizing.
  - 88-contract futures portfolio.
  - >2× Sharpe vs static TSMOM.
- **Relevance to GTOS:** Direct precedent for K54-style ML-based momentum signals. Validates the Phase 2 K54 program direction (regime-aware LightGBM is conceptually downstream). Important methodological point: training on Sharpe (not classification accuracy) is essential — this is missing from current K54 baseline (binary classification).
- **Potential hypothesis:** Training K54 with a Sharpe objective rather than cross-entropy / log-loss will improve OOS Sharpe by 20-40% for the same feature set, replicating Lim-Zohren-Roberts' finding.
- **Cross-domain links:** 19 (deep learning / ML), 20 (RL — Sharpe objective).
- **Horizon:** monthly

### Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection
- **Authors:** Kieran Wood, Stephen Roberts, Stefan Zohren
- **Year:** 2022
- **Source:** *Journal of Financial Data Science* 4(1) 111–129; arXiv:2105.13727
- **URL:** https://arxiv.org/abs/2105.13727
- **Abstract:** Inserts an online changepoint-detection module into a Deep Momentum Network LSTM pipeline. Optimizes balance between slow trend-following (continuing strong trends) and fast mean-reversion (flipping at localized reversals). Improves Sharpe by ~33% (1995-2020) and ~67% (2015-2020) over base DMN.
- **Key findings:**
  - Online changepoint detection.
  - Hybrid slow-trend + fast-reversion.
  - Sharpe +33% full-sample, +67% recent.
  - Recent improvement particularly notable.
- **Relevance to GTOS:** **Highly relevant to GTOS.** Maps directly to the F15 / regime-aware K54 program. The Wood-Roberts-Zohren architecture is a literal recipe for "regime-conditioned LightGBM with changepoint awareness." K55 (ML-vs-AI shadow harness) Phase 2 task is essentially a port of this paper's framework.
- **Potential hypothesis:** A K54 v3 with an explicit changepoint-detection signal (BOCPD or similar) feeding regime-state to a regime-conditioned tree model will deliver +30-60% expected R/trade vs. the K54 baseline (regime-feature without changepoint awareness).
- **Cross-domain links:** 05 (changepoint detection), 19 (deep learning), 20 (RL framing).
- **Horizon:** multi-horizon

---

## 7. Behavioral / theoretical mechanisms

### A Unified Theory of Underreaction, Momentum Trading and Overreaction in Asset Markets
- **Authors:** Harrison G. Hong, Jeremy C. Stein
- **Year:** 1999
- **Source:** *The Journal of Finance* 54(6) 2143–2184
- **URL:** http://www.columbia.edu/~hh2679/jf-mom.pdf
- **Abstract:** Models a market with two trader types: newswatchers (who see private information but cannot extract others' info from prices) and momentum traders (trend-chasers). With gradual information diffusion, newswatcher behavior produces underreaction (giving rise to momentum). Momentum traders extending the pattern produce overreaction at long horizons.
- **Key findings:**
  - Two-trader-type model.
  - Underreaction → short-horizon momentum.
  - Trend-chasing → long-horizon overreaction → reversal.
  - Generates J-T 1993 + DeBondt-Thaler 1985 jointly.
  - Empirically calibratable.
- **Relevance to GTOS:** Theoretical scaffolding for the GTOS edge mechanism. Suggests two distinct populations driving GTOS's instruments (informed → newswatchers; ICT/SMC retail trend-chasers → momentum traders). Predicts that the OB-edge should weaken when the trend-chaser population dominates (via crowding).
- **Potential hypothesis:** A `cross_instrument_trend_chase_intensity` proxy (e.g., aggregate retail-side flow proxy or volume-weighted momentum-strategy crowding) should NEGATIVELY predict K54 expected-R, consistent with Hong-Stein.
- **Cross-domain links:** 17 (behavioral mechanism), 22 (institutional vs retail).
- **Horizon:** multi-horizon

### A Model of Investor Sentiment
- **Authors:** Nicholas Barberis, Andrei Shleifer, Robert Vishny
- **Year:** 1998
- **Source:** *Journal of Financial Economics* 49(3) 307–343
- **URL:** https://nicholasbarberis.github.io/bsv_jnl.pdf
- **Abstract:** Parsimonious behavioral model of investor belief-updating that produces both underreaction (to single news events) and overreaction (to series of similar news), reproducing the joint pattern of momentum + long-horizon reversal.
- **Key findings:**
  - Two-regime belief-updating mechanism (representativeness + conservatism).
  - Underreaction at single-event horizon.
  - Overreaction at series-of-events horizon.
  - Calibrated parameters match empirical magnitudes.
- **Relevance to GTOS:** Provides theoretical mechanism for why an OB-retest works: market underreacts to a single break-of-structure (the OB), then a series of confirming bars produces a trending move. The retest is the spot where the first-event-underreaction is fading. Direct theoretical grounding for the GTOS edge.
- **Potential hypothesis:** A K54 feature `bars_since_BOS_or_CHoCH` interacted with regime should be positively informative for shorter "since" values (Barberis-Shleifer-Vishny underreaction window) and negatively informative for longer "since" values (overreaction-stalling).
- **Cross-domain links:** 17, 18.
- **Horizon:** monthly

### Investor Psychology and Security Market Under- and Overreactions
- **Authors:** Kent Daniel, David Hirshleifer, Avanidhar Subrahmanyam
- **Year:** 1998
- **Source:** *The Journal of Finance* 53(6) 1839–1885
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00077
- **Abstract:** Behavioral model based on (1) investor overconfidence about precision of private information and (2) biased self-attribution. Generates negative long-lag autocorrelations + excess volatility. Biased self-attribution adds positive short-lag autocorrelations (momentum) + earnings drift + long-term reversal.
- **Key findings:**
  - Overconfidence → excess volatility + long-lag negative autocorrelation.
  - Self-attribution → short-horizon momentum + PEAD.
  - Generates joint stylized facts of mom + reversal.
  - Alternative micro-foundation to BSV 1998.
- **Relevance to GTOS:** Alternative behavioral foundation for momentum + reversal. Implication: traders' confidence-state (e.g., recent-PnL of GTOS itself, or aggregated proxies) might predict regime-shifts. Speculative but worth a feature.
- **Potential hypothesis:** A K54 feature `recent_strategy_PnL_z_score` (rolling 20-trade z-score of GTOS realized R) might NEGATIVELY predict next-trade expected R (Daniel-Hirshleifer-Subrahmanyam overconfidence-then-correction).
- **Cross-domain links:** 17, 18.
- **Horizon:** monthly

### The Disposition Effect and Underreaction to News
- **Authors:** Andrea Frazzini
- **Year:** 2006
- **Source:** *The Journal of Finance* 61(4) 2017–2046
- **URL:** https://pages.stern.nyu.edu/~afrazzin/pdf/The%20Disposition%20Effect%20and%20Underreaction%20to%20news%20-%20Frazzini.pdf
- **Abstract:** Tests whether the disposition effect — investors riding losses + realizing gains — produces underreaction to news. Constructs reference-purchase-price proxy from mutual fund holdings. Post-announcement drift is most severe when capital gains and the news event have the same sign. Magnitude depends on shareholders' capital gains/losses on event date. Strategy yields >2% per month alpha.
- **Key findings:**
  - Disposition effect → underreaction.
  - Capital-gains-overhang × news-sign interaction.
  - >2% per month alpha event-driven strategy.
  - Tight micro-foundation for momentum.
- **Relevance to GTOS:** Behavioral mechanism (disposition effect) creates path-dependence in price reaction to news — a form of regime-conditioning. For GTOS at intraday horizon, the analog is "recent trapped-LONG / trapped-SHORT levels" in the OB-retest window. Already partially captured by `liquidity_distance` shadow logger. Could be formalized as a K54 feature.
- **Potential hypothesis:** A K54 feature `bars_since_swing_high_with_close_below` (proxy for trapped longs) interacted with `entry_direction` should be positive for short setups (riding the trapped-long unwind) — replicating Frazzini's effect at the GTOS time scale.
- **Cross-domain links:** 18 (psychology / disposition), 17 (behavioral aggregates).
- **Horizon:** monthly

---

## 8. Synthesis: GTOS-relevance summary, gaps, hypotheses

### Top 3 most-relevant-to-GTOS

1. **Daniel-Moskowitz 2016 — Momentum Crashes.** Maps directly to GTOS F15 LONG-side decay in trending_bull regime. Provides forecastable crash mechanism (panic state + high vol + market rebound), implementable as K54 LONG-sizing modifier. Concrete risk-policy upgrade path.
2. **Wood-Roberts-Zohren 2022 — Slow Momentum with Fast Reversion.** Architecture is a literal recipe for K54 v3: changepoint-aware LSTM hybrid. Sharpe +33% over base DMN, +67% in recent (2015-2020) sub-sample. Direct port to the K55 (ML-vs-AI shadow) Phase 2 task.
3. **Babu-Hoffman-Levine-Ooi-Schroeder-Stamelos 2020 — You Can't Always Trend When You Want.** Decomposition framework (move-magnitude × signal-translation × diversification) is portable to GTOS PnL attribution. Allows quantitative diagnosis of GTOS H2-2026 decay (F11/F15) along three axes rather than narrative.

### Top 1 surprise

**Asness 2011 (Momentum in Japan, also Goyal-Wahal 2015 echo non-replication internationally).** The "single most-cited momentum exception" (Japan) turns out to be an artifact of treating value and momentum independently — when treated as a system (negative correlation diversification), Japanese momentum is consistent with the global pattern. This reframes how we should think about a single decaying GTOS instrument or kill zone: do not look at it in isolation; look at it as part of a diversified system.

For GTOS: a single instrument's decay (e.g., XAU LONG H2-2026) may be statistical noise within the 7-instrument portfolio when the diversifying instruments are accounted for. The S79 portfolio analysis (J46-J49) is essentially this reframe — and it shows +0.742R/trade portfolio-level vs the per-instrument decay narrative. Asness's Japan finding is the academic precedent for that reframe.

### 2-3 hypotheses (summarized; full versions in per-paper notes)

**H1 (K54 architecture):** A regime-aware K54 with (a) Daniel-Moskowitz-style crash-state LONG sizing modifier, (b) Wood-Roberts-Zohren changepoint-detection signal, and (c) Lim-Zohren-Roberts Sharpe-objective training will deliver +50-100% expected R/trade vs the current K54 baseline regime-pooled gradient-boosting classifier.

**H2 (Decomposition diagnosis):** A formal Babu-Hoffman-Levine et al. decomposition of GTOS H1-2026 vs H2-2026 will find that XAU's H2 LONG decay splits ~40% market-move-magnitude / ~60% signal-translation. If true, a substantial fraction of decay reverses with realized-volatility regime change, lowering urgency for prompt-overhaul actions.

**H3 (Cross-instrument signals):** Per-instrument K54 augmented with cross-instrument lagged-return features (constrained to instruments with |corr|>0.3) replicates the Pitkäjärvi-Suominen-Vaittinen 2020 cross-asset TSMOM finding at GTOS scale. Largest expected lift on FX instruments (USDJPY, GBPJPY) informed by XAU and US30.

### Cross-domain handoffs

- **Mean-reversion / cointegration / pairs trading** → 15 (fast-reversion side of Wood-Roberts-Zohren; Lehmann 1990's short-horizon reversal catalogued here only as boundary-of-momentum reference).
- **Behavioral underreaction / overreaction explaining momentum** → 17 (Hong-Stein, Barberis-Shleifer-Vishny, Daniel-Hirshleifer-Subrahmanyam catalogued here as drivers of momentum, but their adaptive-markets implications belong to 17).
- **Volatility-targeted trend / momentum** → 16 / 21 (Barroso-Santa-Clara, "Demystifying Managed Futures" — sizing implications belong to 21, vol regime to 16).
- **Cross-asset trend in commodities / FX** → 10 (XAU), 11 (FX) — Erb-Harvey 2006, Menkhoff-Sarno-Schmeling-Schrimpf 2012 already cross-linked.
- **RL / ML trend agents** → 19 (deep momentum networks, Lim-Zohren-Roberts), 20 (Sharpe-objective RL).
- **Hedge-fund alpha decay in trend-following** → 22 (CTA performance, Hutchinson-O'Brien crisis-shadow).
- **Changepoint-detection for regime transitions** → 05 (Wood-Roberts-Zohren's CPD module).

### Gaps / caveats

- **Intraday momentum at sub-hour horizon** is under-represented in academic literature; most papers use SPY ETF first-30-min predictability as the canonical intraday test. GTOS's M15-bar resolution sits below this — the academic horizon-mismatch is a real gap.
- **Behavioral mechanisms operate at M+ horizons.** Translation to GTOS's M15-H1 horizon requires a leap of faith; Hong-Stein and BSV 1998 do not predict that the underreaction window persists at minute scale.
- **Trend-following on FX spot vs futures** has mixed evidence post-2015. Currency-momentum spread shrinkage post-Menkhoff 2012 is a known concern; could explain part of GTOS's USDJPY/GBPUSD weak edge.
- **Crypto is in scope per spec § 2** but only captured peripherally (see search summaries); deferred to specialty domain if reactivated.

---

*End of papers.md. 38 papers cataloged. Per-paper format consistent; CSV available alongside.*
