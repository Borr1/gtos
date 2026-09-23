# Domain 21 — Risk Management, Kelly, Position Sizing Under Fat Tails

**Slug:** `21_risk_management_kelly_sizing`
**Owner:** Phase 1 Worker Agent #21
**Target paper count:** 30-45

---

## 1. Domain scope statement

This domain owns the literature on **how much to risk** per trade and across a portfolio: Kelly criterion (and fractional / leveraged variants), volatility-targeting, vol-targeting strategies, drawdown control, portfolio insurance, CPPI, expected shortfall (ES) / VaR, tail-risk-aware allocation, risk parity, Markowitz mean-variance under tail risk, leverage cycle and de-leveraging, prop-firm rule design (FTMO / redacted_account / FundingPips), Sortino vs Sharpe, Omega ratio, Calmar, MAR, maximum drawdown control, time-stop versus volatility-stop tradeoffs, risk-of-ruin under fat tails (Mandelbrot, Taleb), Cesar Risk Parity / Vol-target.

**IN scope:** Kelly 1956 + Thorp Kelly-blackjack-stocks, MacLean-Ziemba Kelly-fractional, Markowitz 1952, Roy 1952 safety-first, Rockafellar-Uryasev CVaR, Acerbi-Tasche coherent risk measures, McNeil-Frey-Embrechts QRM, Cesar Anderson risk-parity, Asness-Frazzini-Pedersen leverage aversion, Buffett's $\alpha$ paper, kelly-fractional-under-fat-tails recent papers.

**OUT of scope:** **Tail estimation methodology** → 03; **regime-aware risk** as detection problem → 05; **execution-cost risk** → 06; **single-trade SL placement under microstructure** → 06; **prop-firm psychology** → 18.

---

## 2. Search strategy

### Keywords
- "Kelly criterion" position sizing finance
- "fractional Kelly" leverage drawdown
- "vol targeting" volatility scaling Asness
- "risk parity" Bridgewater
- "expected shortfall" CVaR Rockafellar
- "coherent risk measures" Artzner Delbaen
- "drawdown" maximum control leverage
- "portfolio insurance" CPPI
- "leverage cycle" Geanakoplos
- "Markowitz portfolio" mean variance
- "Roy safety first" 1952
- "leverage aversion" Asness Frazzini Pedersen
- "Buffett alpha" Frazzini Kabiller Pedersen
- "Sortino ratio" downside
- "Calmar" "MAR ratio" CTA
- "risk of ruin" gamblers ruin
- "Taleb antifragile" black swan trading

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Journal of Portfolio Management*
- *Quantitative Finance*
- *Journal of Banking and Finance*
- *Mathematical Finance*
- *Management Science*
- *Risk Magazine* (practitioner)

### Repositories
- arXiv `q-fin.RM`, `q-fin.PM`
- SSRN Risk Management
- AQR research library (Asness, Frazzini, Pedersen)
- Bridgewater research papers
- Edward Thorp personal page

### Key authors
- John Kelly Jr (1956 founder)
- Edward Thorp (Kelly applications)
- Leonard MacLean, William Ziemba (Kelly mathematics)
- Harry Markowitz (mean-variance, 1952)
- Andrew Roy (safety-first, 1952)
- Tyrrell Rockafellar, Stanislav Uryasev (CVaR)
- Philippe Artzner, Freddy Delbaen (coherent measures)
- Cliff Asness, Andrea Frazzini, Lasse Pedersen (leverage aversion)
- Alexander McNeil, Rüdiger Frey, Paul Embrechts (QRM)
- Nassim Taleb (fat tails)
- John Geanakoplos (leverage cycle)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | A New Interpretation of Information Rate (Kelly) | Kelly | 1956 | https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf |
| 2 | The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market | Thorp | 2006 | https://www.edwardothorp.com/wp-content/uploads/2016/11/TheKellyCriterionAndTheStockMarket.pdf |
| 3 | Portfolio Selection | Markowitz | 1952 | search Journal of Finance — verify |
| 4 | Safety First and the Holding of Assets | Roy | 1952 | search Econometrica 1952 — verify |
| 5 | Coherent Measures of Risk | Artzner, Delbaen, Eber, Heath | 1999 | search Mathematical Finance — verify |
| 6 | Optimization of Conditional Value-at-Risk (CVaR) | Rockafellar, Uryasev | 2000 | search Journal of Risk — verify |
| 7 | Quantitative Risk Management (book) | McNeil, Frey, Embrechts | 2005 | Princeton University Press |
| 8 | Leverage Aversion and Risk Parity | Asness, Frazzini, Pedersen | 2012 | search Financial Analysts Journal — verify |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Buffett's Alpha | Frazzini, Kabiller, Pedersen | 2018 | search Financial Analysts Journal — verify |
| 10 | Drawdown control / kelly post-2008 | various | 2020-23 | search SSRN |
| 11 | Risk parity 2022 stress regime | various | 2023-25 | search SSRN |
| 12 | CVaR-based portfolio under fat tails | various | 2022-25 | search arXiv q-fin.RM |
| 13 | Prop firm trading rules empirical | various | 2022-25 | search SSRN |
| 14 | Vol-targeting + drawdown control review | various | 2023-25 | search Quantitative Finance |

---

## 5. GTOS subsystem connections

- **`risk_per_trade_pct: 2.0` → 0.5 when DD ≥8%** (H29) — domain literature is the basis for the rule and motivates whether 0.5x reduction is calibrated correctly.
- **S79 risk policy uniform_fn 2.0% shipped** (`project_s79_risk_policy_shipped_2026-04-27`) — direct application; sharpe-weighted variant (Phase 2 follow-up) is in this domain.
- **GTOS distributional findings memory** (xi=0.35, GARCH 0.9906, 6.2x more 3-sigma events) — these tail metrics directly feed Kelly-under-fat-tails sizing.
- **H38 brief LOST $5,673** (`project_side_aware_sizing_findings`) — side-aware sizing is in this domain; literature on regime-aware Kelly relevant.
- **J46-J49 portfolio +0.742R/trade** — position-management literature (BE, time-stop, partial close) directly applicable.
- **Heartbeat-flatten kill switch** (item #1) — drawdown-control literature.
- **Max-concurrent-positions per kill-zone** — risk-budget allocation across simultaneous trades.
- **Cross-instrument correlation gate (HALVE / REJECT)** — risk-parity / correlation-aware-sizing literature.
- **Portfolio drawdown > 4% emergency stop** — direct application of drawdown control under fat tails.

---

## 6. Cross-domain handoff rules

- **Tail-fitting / EVT methodology** → 03 (we keep the sizing implication).
- **Statistical-validation of sizing rules** → 02.
- **Execution-cost-aware sizing** → 06.
- **Behavioral / loss-aversion roots of position sizing** → 18.
- **Cross-asset factor-based portfolio construction** → 13.
- **Regime-aware sizing** → 05 cross-link.

---

## 7. Output spec

Files:
- `research/ml_program/literature/21_risk_management_kelly_sizing/papers.md`
- `research/ml_program/literature/21_risk_management_kelly_sizing/papers.csv`

Same schema. Special field: `risk_metric` (Kelly / vol-target / VaR / CVaR / drawdown / sortino / omega / parity / multi).

---

## 8. Quality bar / target

30-45 papers. Worker should split: ~7 Kelly foundational, ~5 vol-targeting / risk-parity, ~5 CVaR / coherent measures, ~5 drawdown control / leverage cycle, ~5 fat-tail-aware sizing (Taleb-school + technical), ~5 prop-firm rule analysis, ~3 buffer-tradeoff (SL distance vs hit-rate). Aim for 7+ post-2020 to capture leverage / drawdown / risk-parity in tightening regime.
