# Domain 14 — Trend, Momentum, Breakout

**Slug:** `14_trend_momentum_breakout`
**Owner:** Phase 1 Worker Agent #14
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns the empirical and theoretical literature on **trend-following and momentum** as trading anomalies: cross-sectional momentum (Jegadeesh-Titman), time-series momentum (Moskowitz-Ooi-Pedersen), trend-following CTA returns, breakout / channel / Donchian / Turtle strategies, momentum crashes, momentum-vs-reversal regime, sector / industry / factor momentum, intraday momentum, fast vs slow momentum, residual momentum, post-earnings drift (where momentum-shaped), Sharpe-decay of academic momentum after publication, behavioral and risk-based explanations of momentum.

**IN scope:** Jegadeesh-Titman 1993, Moskowitz-Ooi-Pedersen 2012, Hurst-Ooi-Pedersen century-of-evidence, Daniel-Moskowitz momentum crashes, Asness factor-momentum, Garleanu-Pedersen dynamic-trading optimal trend signals, breakout literature (Brock-Lakonishok-LeBaron 1992 moving averages), Lehmann short-term reversal exclusion at long-horizon momentum.

**OUT of scope:** **Mean reversion** at short horizon → 15; **cointegration / pairs trading** → 15; **trend as adaptive market response** → 17; **trend in single factor / cross-asset** without momentum focus → 13; **technical-pattern recognition** beyond simple breakout → 07.

---

## 2. Search strategy

### Keywords
- "momentum returns" Jegadeesh Titman
- "time series momentum" Moskowitz Ooi Pedersen
- "trend following" CTA managed futures
- "Donchian channel" breakout
- "moving average" trading rule Brock Lakonishok LeBaron
- "momentum crash" Daniel Moskowitz
- "factor momentum" Ehsani Linnainmaa
- "intraday momentum" S&P FOMC Heston
- "industry momentum" Moskowitz Grinblatt
- "residual momentum" Blitz Huij
- "post earnings announcement drift" PEAD Bernard Thomas
- "trend speed" fast slow momentum Hurst
- "momentum decay" published anomaly McLean Pontiff
- "century evidence trend following"
- "turtle trading" Eckhardt

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Financial Analysts Journal*
- *Journal of Portfolio Management*
- *Quantitative Finance*
- *Journal of Banking and Finance*

### Repositories
- arXiv `q-fin.PM`, `q-fin.ST`
- SSRN Capital Markets eJournal
- AQR research
- Robeco Quantitative Investments research
- AlphaArchitect blog
- Hudson and Thames

### Key authors
- Narasimhan Jegadeesh, Sheridan Titman (cross-sectional)
- Tobias Moskowitz, Yao Hua Ooi, Lasse Pedersen (time-series)
- Cliff Asness (factor momentum)
- Brian Hurst, Yao Hua Ooi (century evidence)
- Kent Daniel, Tobias Moskowitz (momentum crashes)
- William Brock, Josef Lakonishok, Blake LeBaron (TA rules)
- Nicolae Garleanu, Lasse Pedersen (dynamic trading)
- David Blitz, Joop Huij (residual momentum)
- Mark Carhart (4-factor)
- Bryan Kelly (factor structure)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Returns to Buying Winners and Selling Losers | Jegadeesh, Titman | 1993 | https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf |
| 2 | Time Series Momentum | Moskowitz, Ooi, Pedersen | 2012 | https://fairmodel.econ.yale.edu/ec439/jpde.pdf |
| 3 | A Century of Evidence on Trend-Following Investing | Hurst, Ooi, Pedersen | 2012-2017 | https://www.trendfollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf |
| 4 | Simple Technical Trading Rules and the Stochastic Properties of Stock Returns | Brock, Lakonishok, LeBaron | 1992 | search Journal of Finance — verify |
| 5 | Momentum Crashes | Daniel, Moskowitz | 2016 | search Journal of Financial Economics — verify |
| 6 | Dynamic Trading with Predictable Returns and Transaction Costs | Garleanu, Pedersen | 2013 | http://docs.lhpedersen.com/DynamicTrading.pdf |
| 7 | Profitability of Momentum Strategies (review) | Jegadeesh, Titman | 2001 | search Journal of Finance — verify |
| 8 | Momentum: Evidence and Insights 30 Years Later | review | 2023 | https://www.sciencedirect.com/science/article/abs/pii/S0927538X23002731 |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Factor Momentum and the Momentum Factor | Ehsani, Linnainmaa | 2022 | search Journal of Finance — verify |
| 10 | Momentum 30 years later (Springer review) | Heidari et al | 2022 | https://link.springer.com/article/10.1007/s11408-022-00417-8 |
| 11 | Trend-following alpha decay 2020-2024 | various | 2022-25 | search SSRN |
| 12 | Intraday momentum FOMC days post-2020 | various | 2022-25 | search SSRN |
| 13 | Time-series momentum on crypto | various | 2021-24 | search arXiv q-fin.GN crypto momentum |

---

## 5. GTOS subsystem connections

- **GTOS edge mechanism** (`.context/01_knowledge_base/edge_mechanism.md`) — OB-retest is a *reversion* play within an *impulse-trend*. Momentum literature contextualizes the impulse leg.
- **A4 trending_bull replay** — cohort definition relies on trending regime; trend-following literature on regime persistence applies.
- **F2 LONG decay concentrated in trending_bull** — momentum-crash literature (Daniel-Moskowitz) directly relevant to LONG-side selectivity collapse.
- **K54 v2 features** — momentum / trend-strength features (rolling mean, fast vs slow MA, ADX, Donchian-position) for regime-conditional model.
- **Time-series-momentum on XAU / NAS / US30** — asset-level trend literature for hyper-parameterizing instrument profiles.
- **Risk gate during trend acceleration** — dynamic-trading literature (Garleanu-Pedersen) on optimal sizing in presence of mean-reversion-after-acceleration.

---

## 6. Cross-domain handoff rules

- **Mean reversion / cointegration / pairs** → 15.
- **Behavioral underreaction / overreaction explaining momentum** → 17.
- **Volatility-targeted trend-following** → 16 / 21.
- **Momentum as cross-asset factor** → 13 (we keep the asset-class-specific trend studies; 13 keeps factor structure).
- **Cross-asset trend in commodities / FX** → 10 / 11 cross-link.
- **RL/ML trend agents** → 19 / 20.

---

## 7. Output spec

Files:
- `research/ml_program/literature/14_trend_momentum_breakout/papers.md`
- `research/ml_program/literature/14_trend_momentum_breakout/papers.csv`

Same schema. Special field: `horizon` (intraday / daily / weekly / monthly / multi-horizon).

---

## 8. Quality bar / target

35-50 papers. Worker should ensure: ~10 cross-sectional momentum, ~8 time-series momentum / trend-following, ~6 momentum crashes / decay, ~5 factor momentum, ~5 intraday / short-horizon, ~5 commodity / FX trend, ~3 behavioral explanations. Aim for at least 6 post-2020 to track decay/regime-shifts.
