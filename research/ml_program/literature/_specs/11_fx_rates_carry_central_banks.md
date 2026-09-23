# Domain 11 — FX, Interest Rates, Carry, Central Banks

**Slug:** `11_fx_rates_carry_central_banks`
**Owner:** Phase 1 Worker Agent #11
**Target paper count:** 40-55

---

## 1. Domain scope statement

This domain owns foreign-exchange and interest-rate research relevant to GTOS's USDJPY / GBPJPY / GBPUSD instruments: covered/uncovered interest parity, FX carry trade, FX volatility / vol-smile, central-bank policy & FX response, intraday FX dynamics, FX intervention, JPY / USD / EUR / GBP regime changes, term-structure of interest rates, monetary-policy surprise effects, MOF / BoJ intervention literature, dollar smile theory, commodity-currency relations (AUD / CAD / NOK).

**IN scope:** Meese-Rogoff puzzle, Fama 1984 forward bias, Lustig-Roussanov-Verdelhan dollar/carry factors, Brunnermeier-Nagel-Pedersen carry-trade fragility, Burnside FX carry / safe-haven, ECB FX intervention literature, BIS quarterly FX flow reports, Frankel exchange-rate models, Engel-Frankel UIP, JPY-funded carry trade with crash risk, Yen safe-haven literature.

**OUT of scope:** **FX market microstructure** (Lyons hot-potato dealer-flow, Evans-Lyons order flow → FX) → 06 / 07; **FX clustering at round numbers** → 09; **FX-volatility-trading derivatives** → 16; **gold-as-currency** → 10; central bank policy through behavioral lens → 17.

---

## 2. Search strategy

### Keywords
- "FX carry trade" Lustig Burnside
- "uncovered interest parity" Fama puzzle
- "forward premium puzzle" exchange rate
- "Meese Rogoff" exchange rate prediction
- "JPY safe haven" Yen carry funding
- "dollar smile" Stephen Jen
- "BoJ intervention" yen empirical
- "ECB FX intervention" exchange rate
- "FX volatility risk premium" SVR
- "Fed policy surprise" exchange rate
- "non-deliverable forward" NDF
- "covered interest parity violation" 2008
- "FX positioning" CFTC dollar
- "DXY" dollar index returns
- "yen funding currency" carry crash
- "GBP USD" Brexit exchange rate

### Key journals
- *Journal of International Economics*
- *Journal of International Money and Finance*
- *Review of Financial Studies*
- *Journal of Finance*
- *American Economic Review* (occasional FX)
- *Journal of Monetary Economics*
- *Journal of Banking and Finance*
- *Journal of Financial Economics*

### Repositories
- arXiv `q-fin.GN`, `econ.GN`
- NBER International Finance and Macroeconomics
- BIS Quarterly Review (FX positioning)
- IMF Working Papers
- ECB Occasional Papers / FX market reports
- Federal Reserve Board IF series
- SSRN International Macro

### Key authors
- Hanno Lustig, Adrien Verdelhan, Nikolai Roussanov (carry)
- Markus Brunnermeier, Stefan Nagel, Lasse Pedersen (carry crash)
- Craig Burnside (carry)
- Charles Engel, Kenneth West (FX prediction)
- Richard Lyons, Martin Evans (microstructure overlap)
- Jeffrey Frankel (exchange rate models)
- Linda Goldberg (Fed FX)
- Helen Popper (FX)
- Stephen Jen (dollar smile - practitioner)
- Maurice Obstfeld (open economy)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Forward and Spot Exchange Rates | Fama | 1984 | search Journal of Monetary Economics — verify |
| 2 | Empirical Exchange Rate Models of the Seventies | Meese, Rogoff | 1983 | search Journal of International Economics — verify |
| 3 | Common Risk Factors in Currency Markets | Lustig, Roussanov, Verdelhan | 2011 | search Review of Financial Studies — verify |
| 4 | Carry Trades and Currency Crashes | Brunnermeier, Nagel, Pedersen | 2008 | search NBER macro annual — verify |
| 5 | The Microstructure Approach to Exchange Rates (book) | Lyons | 2001 | https://mitpress.mit.edu/9780262622059/the-microstructure-approach-to-exchange-rates/ |
| 6 | Order Flow and Exchange Rate Dynamics | Evans, Lyons | 2002 | search Journal of Political Economy — verify |
| 7 | Carry Trade and Momentum in Currency Markets | Burnside, Eichenbaum, Rebelo | 2011 | search Annual Review of Financial Economics — verify |
| 8 | Country Specific Inflation and Currency Crashes | various | 2010s | seed candidate — search SSRN |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Covered interest parity deviations post-2008 | Du, Tepper, Verdelhan | 2018 | search Journal of Finance 2018 — verify |
| 10 | Dollar dominance / safe-haven during COVID and 2022 | various | 2022-24 | BIS Quarterly Review |
| 11 | FX intervention reaction functions BoJ 2022-24 | various | 2024-25 | IMF working papers |
| 12 | Yen weakness 2022-24 deep dive | various | 2024-25 | search SSRN — verify |
| 13 | GBP after Brexit / mini-budget volatility | various | 2022-24 | search Journal of International Money and Finance |
| 14 | NDF vs onshore FX in EM | recent | 2022-25 | search BIS papers |

---

## 5. GTOS subsystem connections

- **USDJPY / GBPJPY** instruments — JPY-funded carry trade literature is core context for Tokyo / London/NY kill-zone behavior.
- **GBPUSD observer** — Brexit / mini-budget literature underpins the choice to keep observer-only mode.
- **EURUSD profile** (live profile pinned with tight-FX overrides) — UIP / CIP / dollar-cycle literature.
- **JPY_CROSSES correlation group** — academic justification for grouping; do not unilaterally edit (memory `feedback_decision_preservation`).
- **Cross-instrument correlation gate** — JPY co-movement and DXY-conditional currency cluster behavior.
- **NFP / FOMC / BoJ event-aware logic** — central-bank-surprise FX-impact literature.
- **Dollar smile / risk-on / risk-off** — gold-FX co-movement (cross-link to 10).
- **K54 v2 features** — DXY, real-rate spreads, BoJ-rate-expectation features as candidates.

---

## 6. Cross-domain handoff rules

- **FX microstructure / dealer flow / order book** → 06.
- **FX directional-trading rules from order flow** → 07.
- **Round-number FX clustering** → 09.
- **Gold-DXY relationship** → 10 (we keep the FX-side academic; 10 keeps the gold-side).
- **FX volatility-of-vol / risk-reversal trading** → 16.
- **FX behavioral overshooting / Frankel-Froot expectations** → 17.
- **FX RL / LLM agents** → 20.

---

## 7. Output spec

Files:
- `research/ml_program/literature/11_fx_rates_carry_central_banks/papers.md`
- `research/ml_program/literature/11_fx_rates_carry_central_banks/papers.csv`

Same schema. Special fields: `currency_pairs_studied` (list), `event_type` (BoJ / Fed / ECB / data-release / generic).

---

## 8. Quality bar / target

40-55 papers. Worker should split: ~10 carry / forward bias, ~10 FX safe-haven / dollar / JPY / risk-off, ~8 central-bank policy & FX, ~8 FX vol / FX option-implied, ~5 commodity-currency, ~5 recent JPY weakness / GBP post-Brexit / EUR-debt-cycle. Aim for at least 8 papers post-2020 to capture the current monetary-policy regime.
