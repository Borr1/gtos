# Domain 22 — Hedge Fund Alpha, Wall Street, Quantum Finance Public Research

**Slug:** `22_hedge_fund_alpha_wallstreet_quantum`
**Owner:** Phase 1 Worker Agent #22
**Target paper count:** 25-40

---

## 1. Domain scope statement

This domain owns research on **how the alpha-generating industry actually works** at the public-research level: hedge-fund returns / persistence / fees, capacity decay, AUM-vs-alpha relationship, Renaissance Medallion-style anomaly, Buffett alpha decomposition, prop-trading-desk research, sell-side flow / proprietary-research case studies, quantum-finance public research (D-Wave-finance, IBM Quantum-Finance applications), high-frequency-trading firm public lit, FX dealer-flow studies as institution literature, agency conflicts in proprietary trading, hedge-fund-strategy-classification, manager-skill vs luck (Kosowski-Timmermann-Wermers, Fama-French managers).

**IN scope:** Renaissance Medallion analysis, Buffett's Alpha, hedge-fund persistence, Kosowski-Timmermann-Wermers, Fung-Hsieh seven factors, Carhart performance, hedge-fund-style research, smart-beta literature, quantum-finance public proof-of-concepts (NEC-Quantum trading 2022-25, IBM, Goldman, JPMorgan public quantum experiments), fintech disruption research.

**OUT of scope:** **Pure ML strategies** → 19; **RL agents** → 20; **factor-momentum-cross-sectional anomaly** → 13 / 14 split; **AI / LLM agentic trading** → 20; **prop-firm individual-trader rules** → 21 / 18.

---

## 2. Search strategy

### Keywords
- "hedge fund returns" persistence Kosowski Timmermann
- "Fung Hsieh" hedge fund seven factors
- "smart beta" alternative beta
- "Renaissance Medallion" returns analysis
- "Buffett's alpha" Frazzini Kabiller
- "Capacity constraints" hedge fund AUM
- "manager skill" luck mutual fund
- "alpha decay" published anomaly McLean Pontiff
- "prop trading desk" sell-side research
- "agency conflict" proprietary trading
- "high-frequency trading firm" public research
- "quantum computing" finance portfolio optimization
- "QAOA" portfolio optimization quantum
- "D-Wave finance" application
- "JPMorgan quantum" Goldman finance
- "fintech disruption" hedge fund automation

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Journal of Portfolio Management*
- *Financial Analysts Journal*
- *Journal of Empirical Finance*
- *Quantitative Finance*
- *npj Quantum Information* (quantum)
- *arXiv quant-ph*

### Repositories
- arXiv `q-fin.PM`, `q-fin.GN`, `quant-ph` (quantum)
- SSRN Hedge Funds eJournal
- NBER Asset Pricing
- AQR Capital Management research
- Bridgewater research papers
- IBM Quantum (research blog)
- Andrew Lo MIT lab (hedge fund research)
- Nassim Taleb personal page

### Key authors
- William Fung, David Hsieh (hedge-fund factors)
- Robert Kosowski, Allan Timmermann, Russ Wermers (manager skill)
- Cliff Asness (smart beta / Buffett alpha — overlap)
- Andrea Frazzini, David Kabiller, Lasse Pedersen (Buffett)
- Brad Cornell (Medallion analysis)
- Andrew Lo (hedge fund research)
- Nassim Taleb (fat-tail trading philosophy)
- Stefan Woerner et al (IBM Quantum finance)
- Roman Orus (quantum finance review)
- Ed Thorp (hedge fund pioneer overlap)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Buffett's Alpha | Frazzini, Kabiller, Pedersen | 2018 | search Financial Analysts Journal — verify |
| 2 | Hedge Funds: Performance, Risk, and Capital Formation | Fung, Hsieh | 2007 | search Journal of Finance — verify |
| 3 | Hedge Fund Risk Factors and the Value at Risk of Fixed Income Trading Strategies | Fung, Hsieh | 2002 | search Journal of Fixed Income — verify |
| 4 | Are Mutual Fund Manager Returns Statistically Distinguishable from Luck? | Kosowski, Timmermann, Wermers, White | 2006 | search Journal of Finance — verify |
| 5 | Medallion Fund: The Ultimate Counterexample | Cornell | 2020 | https://www.cornell-capital.com/blog/2020/02/medallion-fund-the-ultimate-counterexample.html |
| 6 | Hedge Funds and the Technology Bubble | Brunnermeier, Nagel | 2004 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00690.x |
| 7 | Does Academic Research Destroy Stock Return Predictability? | McLean, Pontiff | 2016 | search Journal of Finance — verify |
| 8 | The Evolution of Technical Analysis (book) | Lo, Hasanhodzic | 2010 | book — Bloomberg Press |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Optimal Trading Strategies (book) | Kissell, Glantz | 2003 | https://www.amazon.com/Optimal-Trading-Strategies-Quantitative-Approaches/dp/0814407242 |
| 10 | Renaissance 2024 rebirth | Institutional Investor | 2024 | https://www.institutionalinvestor.com/article/2e0uykr3vn5booz0smrcw/hedge-funds/renaissances-2024-rebirth |
| 11 | Quantum portfolio optimization | Stefan Woerner et al / IBM | 2020-24 | search arXiv quant-ph + portfolio |
| 12 | Quantum Monte Carlo for option pricing | various | 2021-24 | search arXiv quant-ph 2105 |
| 13 | Hedge-fund style classification with ML | various | 2022-25 | search SSRN |
| 14 | Roman Orus quantum finance review | Orus | 2019-22 | search arXiv quant-ph 1902 |
| 15 | NEC quantum trading systems | various | 2022-25 | search press / arXiv |

---

## 5. GTOS subsystem connections

- **GTOS is a private prop-firm trading system** — domain 22 is the strategic context (where does GTOS fit in the public-research-on-quant-trading landscape? what's the empirical rate of edge decay? what's the realistic ceiling for systematic alpha?).
- **Edge decay (item #4 / F11)** — McLean-Pontiff academic-publication-decay literature anchors the *expectation* that an order-block edge would decay over years.
- **Validated Numbers maintenance** — hedge-fund alpha decay literature underpins how to interpret the K52 re-test results.
- **Capacity / scaling** — GTOS is operating at $100k redacted_account; capacity-constraint literature isn't immediately binding but informs future scaling considerations.
- **Quantum-finance literature** — long-horizon strategic input. Public quantum-portfolio-optimization research is mostly proof-of-concept but the directional roadmap matters for 5-10y planning.
- **AI as edge** — the question whether Claude API at $50/mo can produce alpha competitive with Renaissance-style HFT firms is grounded in this domain's literature.

---

## 6. Cross-domain handoff rules

- **Cross-section equity factor** → 13.
- **AI / LLM agent trading** → 20.
- **Hedge-fund risk-management strategies** → 21.
- **Behavioral / sentiment effect on hedge-fund returns** → 17.
- **High-frequency / market-making firm research** → 06.
- **Prop-firm psychology** → 18.

---

## 7. Output spec

Files:
- `research/ml_program/literature/22_hedge_fund_alpha_wallstreet_quantum/papers.md`
- `research/ml_program/literature/22_hedge_fund_alpha_wallstreet_quantum/papers.csv`

Same schema. Special fields: `study_type` (empirical / case-study / review / quantum-proof-of-concept), `entity_studied` (single fund / aggregate / strategy-class / firm-type).

---

## 8. Quality bar / target

25-40 papers. **Justified lower bound:** hedge-fund-public research is data-constrained (most strategies stay private). Aim for ~10 hedge-fund alpha / persistence, ~5 capacity / decay, ~5 specific hedge-fund case-studies (Medallion, Buffett, others), ~5 quantum-finance public POCs, ~5 sell-side / prop-trading-desk research. Reject pure marketing / non-research blog posts.
