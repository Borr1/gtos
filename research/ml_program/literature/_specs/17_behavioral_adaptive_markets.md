# Domain 17 — Behavioral Finance & Adaptive Markets

**Slug:** `17_behavioral_adaptive_markets`
**Owner:** Phase 1 Worker Agent #17
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns research on **why markets deviate from rational** at the *market level*: behavioral models of price formation, limits to arbitrage, noise traders, sentiment indices, behavioral asset pricing, adaptive markets hypothesis (AML), Andrew Lo evolutionary finance, post-earnings drift / momentum / reversal as behavioral, herding evidence, social-media effects on prices (StockTwits, Twitter, Reddit), media-sentiment trading, retail-investor biases at the aggregate level.

**IN scope:** Barberis-Shleifer-Vishny, Hong-Stein, DeLong-Shleifer-Summers-Waldmann (DSSW noise traders), Shleifer-Vishny limits-of-arbitrage, Lo adaptive-markets, Tetlock media sentiment, Da-Engelberg-Gao FEARS / search-volume, Stambaugh-Yu-Yuan sentiment-as-pricing-anomaly, Shiller excess volatility, behavioral momentum / reversal models.

**OUT of scope:** **Individual-trader cognitive biases / decision-making under uncertainty** → 18; **rational-expectations technical-trading rule analysis** → 14 / 15; **behavioral roots of round-number clustering** → 09 cross-link; **micro-behavior in execution** (overconfidence in own orders) → 06.

---

## 2. Search strategy

### Keywords
- "limits of arbitrage" Shleifer Vishny noise trader
- "adaptive markets hypothesis" Lo
- "noise trader" DeLong Shleifer Summers
- "Tetlock" media sentiment stock returns
- "FEARS" Google search volume Da Engelberg
- "investor sentiment" Baker Wurgler
- "Stambaugh Yu Yuan" sentiment anomaly
- "herding" institutional retail returns
- "social media" Twitter Reddit StockTwits returns
- "GameStop" meme stock 2021 retail
- "post earnings announcement drift" behavioral
- "underreaction overreaction" Hong Stein
- "BSV model" Barberis Shleifer Vishny
- "excess volatility" Shiller dividends
- "behavioral asset pricing" survey Barberis

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Quarterly Journal of Economics*
- *Journal of Behavioral Finance*
- *Journal of Behavioral and Experimental Finance*
- *Review of Behavioral Finance*

### Repositories
- arXiv `q-fin.GN`, `q-fin.PM`
- SSRN Behavioral Finance
- NBER Behavioral Finance
- Andrew Lo MIT Lab page
- Robert Shiller Yale page
- Nicholas Barberis Yale page

### Key authors
- Andrew Lo (adaptive markets)
- Robert Shiller (behavioral asset pricing)
- Nicholas Barberis, Andrei Shleifer, Robert Vishny (BSV)
- Hersh Shefrin (behavioral asset pricing)
- Werner DeBondt, Richard Thaler (overreaction)
- Paul Tetlock (media sentiment)
- Malcolm Baker, Jeffrey Wurgler (sentiment index)
- Robert Stambaugh, Jianfeng Yu, Yu Yuan (sentiment-anomaly)
- Hong, Stein, Lim (gradual diffusion)
- Brad Barber, Terrance Odean (retail)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | The Adaptive Markets Hypothesis | Lo | 2004 | https://web.mit.edu/Alo/www/Papers/JPM2004_Pub.pdf |
| 2 | A Model of Investor Sentiment | Barberis, Shleifer, Vishny | 1998 | https://nicholasbarberis.github.io/bsv_jnl.pdf |
| 3 | The Limits of Arbitrage | Shleifer, Vishny | 1997 | https://www.nber.org/system/files/working_papers/w5167/w5167.pdf |
| 4 | Do Stock Prices Move Too Much to be Justified by Subsequent Changes in Dividends? | Shiller | 1981 | https://ms.mcmaster.ca/~grasselli/Shiller81.pdf |
| 5 | Giving Content to Investor Sentiment | Tetlock | 2007 | https://business.columbia.edu/sites/default/files-efs/pubfiles/3097/Tetlock_Media_Sentiment_JF.pdf |
| 6 | Investor Sentiment and the Cross-Section of Stock Returns | Baker, Wurgler | 2006 | search Journal of Finance — verify |
| 7 | Hedge Funds and the Technology Bubble | Brunnermeier, Nagel | 2004 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00690.x |
| 8 | Noise Trader Risk in Financial Markets | DeLong, Shleifer, Summers, Waldmann | 1990 | search Journal of Political Economy — verify |
| 9 | A Unified Theory of Underreaction, Momentum Trading and Overreaction | Hong, Stein | 1999 | search Journal of Finance — verify |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 10 | GameStop / meme-stock retail 2021 | various | 2021-22 | search SSRN GameStop retail |
| 11 | Robinhood / WallStreetBets effect on returns | various | 2022-24 | search SSRN |
| 12 | Adaptive Markets in low-volume vs high-volume regimes | various | 2022-25 | search SSRN |
| 13 | Twitter sentiment as factor 2020-25 | various | 2022-25 | search SSRN |
| 14 | LLM-extracted sentiment vs lexicon 2023-25 | various | 2023-25 | search arXiv q-fin.GN LLM sentiment |
| 15 | Adaptive Markets Hypothesis insights into small stock market efficiency | recent | 2024 | https://www.tandfonline.com/doi/full/10.1080/00036846.2024.2326039 |

---

## 5. GTOS subsystem connections

- **Edge mechanism document** (`edge_mechanism.md`) — explicitly cites stop-cascade / mean-reversion-after-cascade. The behavioral / limits-of-arbitrage / noise-trader literature is the direct theoretical anchor.
- **Edge decay (item #4 / F11)** — adaptive markets hypothesis predicts that academic-published edges decay (McLean-Pontiff). Deep relevance to GTOS's survival question.
- **Order block precision** — BSV / Hong-Stein model the underreaction / overreaction dynamics that explain why retests have edge.
- **Component 3B Bull/Bear/Judge debate** (research-door-wired, default OFF) — behavioral bias literature underpins why an adversarial structure may help.
- **Touch-count gate decay** — A19 LOOSEN_TO_3 rejection finding may be regime-dependent; behavioral literature on participant-rotation explains.
- **K54 v2 features** — sentiment indices, FEARS, news flow, retail-vs-institutional flow as candidate features.
- **NAS100 retail-flow effect post-2020** — meme-stock literature relevant for index sub-day dynamics.

---

## 6. Cross-domain handoff rules

- **Individual-trader psychology / decision biases** → 18.
- **Behavioral momentum-and-reversal as quant strategy** → 14 / 15 cross-link.
- **LLM-extracted sentiment as data source** → 19 / 20.
- **Sentiment-driven volatility / VIX** → 16.
- **Cross-asset behavioral spillover** → 13.
- **Limits-of-arbitrage capital constraints** → 22 (hedge fund).

---

## 7. Output spec

Files:
- `research/ml_program/literature/17_behavioral_adaptive_markets/papers.md`
- `research/ml_program/literature/17_behavioral_adaptive_markets/papers.csv`

Same schema. Special field: `mechanism` (underreaction / overreaction / sentiment / herding / limits-of-arb / adaptive).

---

## 8. Quality bar / target

35-50 papers. Worker should split: ~10 BSV / Hong-Stein / behavioral foundational, ~7 limits of arbitrage, ~5 Lo adaptive markets, ~7 sentiment / media / FEARS, ~5 GameStop / retail era, ~5 sentiment-pricing-anomaly. Aim for at least 8 post-2020 (the retail-flow / social-media regime is the central recent shift).
