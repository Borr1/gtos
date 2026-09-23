# Domain 01 — Mathematical Foundations & Stochastic Processes

**Slug:** `01_math_foundations`
**Owner:** Phase 1 Worker Agent #1
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain covers the mathematical scaffolding underneath any quantitative trading system: probability theory on filtered spaces, stochastic processes (Brownian motion, Poisson, Levy, semimartingales, jump-diffusions), Ito calculus, stochastic differential equations, martingale theory, ergodic theorems, change-of-measure, large-deviation theory, Markov processes, and the measure-theoretic prerequisites for arbitrage pricing (NFLVR, equivalent martingale measures).

**IN scope:** SDEs and their solutions; Markov-process structure; semimartingale decompositions; stochastic integration theory; rough-path / signature methods (Lyons-Hambly); fractional Brownian motion construction (NOT applications); convergence theorems used in time-series asymptotics.

**OUT of scope:** ARIMA / state-space empirical estimation (→ domain 02), GARCH families as estimated empirical objects (→ domain 03 for distributional properties / 16 for derivative pricing), wavelet decomposition as feature engineering (→ domain 04), regime-switching as estimated model (→ domain 05). This domain owns *theory*; downstream domains own *application*.

---

## 2. Search strategy

### Keywords (Google Scholar-ready)
- "stochastic differential equation" "financial mathematics"
- "Ito calculus" "asset pricing"
- "semimartingale" "no arbitrage"
- "fractional Brownian motion" finance
- "rough path theory" finance OR "signature method" trading
- "Levy process" "financial modeling"
- "jump diffusion" Merton OR Kou
- "fundamental theorem of asset pricing" Delbaen Schachermayer
- "first hitting time" stochastic process
- "Markov chain" financial mathematics
- "ergodic theorem" "time series"
- "Girsanov theorem" risk-neutral
- "stochastic calculus" textbook foundational
- "Brownian motion" "occupation time"
- "subordinated process" finance trading time

### Key journals
- *Mathematical Finance*
- *Finance and Stochastics*
- *Annals of Applied Probability*
- *Stochastic Processes and their Applications*
- *Electronic Journal of Probability*
- *Probability Theory and Related Fields*
- *SIAM Journal on Financial Mathematics*
- *Quantitative Finance* (theoretical issues)

### Repositories
- arXiv: `q-fin.MF` (mathematical finance), `math.PR` (probability), `q-fin.PR` (pricing)
- SSRN Mathematical Finance eJournal
- Project Euclid
- HAL (French-school stochastic calculus)
- SFB 649 / Humboldt-Berlin technical report series
- ETH RiskLab archives

### Key authors
- Marc Yor, Hans Follmer, Ioannis Karatzas, Steven Shreve, Freddy Delbaen, Walter Schachermayer (foundations)
- Terry Lyons, Peter Friz, Harald Hambly (rough paths / signatures)
- Bruno Dupire, Yuri Kabanov, Mathias Beiglbock (martingale optimal transport)
- Robert Jarrow, Phillip Protter (semimartingales applied)
- David Aldous, Persi Diaconis, Jim Pitman (probability theory)
- Rama Cont (theory side; lap with domain 03)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Theorie de la Speculation (PhD thesis) | Louis Bachelier | 1900 | https://mathshistory.st-andrews.ac.uk/Biographies/Bachelier/ |
| 2 | The Pricing of Options and Corporate Liabilities | Black, Scholes | 1973 | https://www.cs.princeton.edu/courses/archive/fall09/cos323/papers/black_scholes73.pdf |
| 3 | A General Version of the Fundamental Theorem of Asset Pricing | Delbaen, Schachermayer | 1994 | search SSRN / Mathematische Annalen — verify before use |
| 4 | Continuous Auctions and Insider Trading | Albert S. Kyle | 1985 | https://personal.utdallas.edu/~nina.baranchuk/Fin7310/papers/Kyle1985.pdf |
| 5 | Brownian Motion and Stochastic Calculus (textbook) | Karatzas, Shreve | 1991 | Springer GTM 113 (book — reference, not paper) |
| 6 | Methods of Mathematical Finance | Karatzas, Shreve | 1998 | Springer (textbook) |
| 7 | Stochastic Calculus for Finance II | Steven Shreve | 2004 | Springer (textbook) |
| 8 | Continuous Martingales and Brownian Motion | Revuz, Yor | 1999 | Springer GTM 293 (textbook) |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | A Course on Rough Paths (2nd ed) | Friz, Hairer | 2020 | Springer |
| 10 | Signature methods in machine learning | Lyons et al | 2022-2024 | search arXiv math.PR + applications to time series |
| 11 | Deep learning for stochastic differential equations | Han, Jentzen, E | 2018-2022 | search arXiv |
| 12 | Path-dependent PDEs and rough volatility | Bayer, Friz, Gatheral | 2016-2023 | seed candidate — verify before use |

**Worker note:** seed candidates flagged "verify before use" must have the WebSearch result URL confirmed; drop if not located.

---

## 5. GTOS subsystem connections

- **Component 2 (`market_state.py`)** — swing detection, BOS/CHoCH event timing benefits from rigorous treatment of first-passage times and excursion theory of Brownian motion.
- **Risk gate / SL placement** — fat-tail-aware buffer multipliers (`risk.sl_buffer_atr_multiplier`) need theoretical anchors from Levy/jump-diffusion exit-time distributions.
- **Tick microstructure features (`tick_features.py`)** — subordinated processes / time-changed Brownian motion connect physical-time vs trading-time intuition behind the daemon.
- **Decay velocity research (F11, OB-zone advantage decay)** — time-varying drift models, local-martingale decompositions for non-stationarity.
- **K54 v2 ML feature engineering** — signature-method features as principled price-path representation (especially for ICT BOS/sweep patterns).

---

## 6. Cross-domain handoff rules

- Pure **distribution of returns** (heavy tails, scaling laws, GARCH residuals) → domain 03.
- Statistical **estimation / inference / multiple testing in finance** → domain 02.
- Wavelet / fractal **time-series decomposition for forecasting** → domain 04.
- Regime-switching as **estimated model with empirical fit** → domain 05.
- Stochastic-control / **optimal execution / market-making** → domain 06 (microstructure) or 21 (risk).
- Stochastic-volatility option **pricing models** with empirical calibration → domain 16.
- A paper is "ours" when its core contribution is theorem proving, process construction, or measure-theoretic foundations. Empirical applied papers go to the application domain even if they invoke our theory.

---

## 7. Output spec

Worker writes to:
- `research/ml_program/literature/01_math_foundations/papers.md`
- `research/ml_program/literature/01_math_foundations/papers.csv`

Per-paper schema (CSV columns + MD entries):
1. `id` (e.g., `01-001`)
2. `title`
3. `authors`
4. `year`
5. `source` (journal/book/arXiv ID)
6. `url`
7. `abstract` (1-3 sentences, original where possible)
8. `key_findings` (3-5 bullet points)
9. `relevance_to_gtos` (which subsystem; explicit linkage)
10. `potential_hypothesis` (a concrete testable hypothesis the program could pre-register; one sentence)
11. `cross_domain_links` (other domain slugs if relevant)

---

## 8. Quality bar / target

35-50 papers. Lower bound because foundational mathematical-finance papers are well-defined and small in number; recent rough-paths / signature-method work in finance is the growth area. Don't fluff with peripheral pure-math papers — every paper must carry a non-empty `relevance_to_gtos`.
