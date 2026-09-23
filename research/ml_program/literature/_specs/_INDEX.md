# Literature Program — Phase 1 Spec Index

**Last updated:** 2026-04-29 (meta-designer Phase 0 close)
**Phase:** 0 (meta-designer) → 1 (22 parallel literature workers)
**Spec count:** 22 domain specs + this index = 23 files

This index is the orchestrator's master reference for dispatching the 22 Phase 1 literature workers. Each domain spec lives at `research/ml_program/literature/_specs/{NN}_{slug}.md`.

---

## 1. Master taxonomy (22 domains)

| # | Domain | Slug | Target papers |
|---|--------|------|---------------|
| 1 | Mathematical Foundations & Stochastic Processes | `01_math_foundations` | 35-50 |
| 2 | Statistical Methodology & Validation in Finance | `02_statistical_methodology` | 40-60 |
| 3 | Distributional Characteristics & Tails | `03_distributional_characteristics` | 40-55 |
| 4 | Multi-Timeframe, Fractal, Wavelets & Hurst | `04_multitimeframe_fractal_wavelets` | 30-45 |
| 5 | Change-Point Detection & Regime Switching | `05_change_point_regime_switching` | 35-50 |
| 6 | Market Microstructure & Order Book | `06_market_microstructure_orderbook` | 45-60 |
| 7 | Order Flow, Footprint, ICT/SMC Academic | `07_order_flow_footprint_ict_smc` | 25-40 |
| 8 | Volume, Auction Theory, VWAP, OPEX | `08_volume_auction_vwap_opex` | 30-45 |
| 9 | Round-Number Effects & Level Magnetism | `09_round_numbers_level_magnetism` | 20-30 |
| 10 | Gold & Commodities Specific | `10_gold_commodities` | 35-50 |
| 11 | FX, Interest Rates, Carry, Central Banks | `11_fx_rates_carry_central_banks` | 40-55 |
| 12 | Equity Indices, Options, Gamma Flow | `12_equity_indices_options_gamma` | 35-50 |
| 13 | Cross-Asset Correlation & Factor Exposures | `13_cross_asset_correlation_factors` | 35-50 |
| 14 | Trend, Momentum, Breakout | `14_trend_momentum_breakout` | 35-50 |
| 15 | Mean Reversion, Cointegration, Statistical Arbitrage | `15_mean_reversion_cointegration_statarb` | 30-45 |
| 16 | Volatility Trading, Derivatives, Vol Regime | `16_volatility_derivatives_vol_regime` | 35-50 |
| 17 | Behavioral Finance & Adaptive Markets | `17_behavioral_adaptive_markets` | 35-50 |
| 18 | Trader Psychology & Decision Under Uncertainty | `18_trader_psychology_decision` | 25-40 |
| 19 | AI/ML for Finance — Classical, Deep, Sequence | `19_ai_ml_for_finance_classical_deep_sequence` | 50-65 |
| 20 | RL & LLMs in Trading | `20_rl_llms_in_trading` | 35-50 |
| 21 | Risk Management, Kelly, Position Sizing under Fat Tails | `21_risk_management_kelly_sizing` | 30-45 |
| 22 | Hedge Fund Alpha, Wall Street, Quantum Finance | `22_hedge_fund_alpha_wallstreet_quantum` | 25-40 |

**Aggregate target:** ~750-1100 papers across 22 domains. Phase 1 budget assumption: ~8-10h wallclock for parallel dispatch (one Opus 4.7 max-effort agent per domain × ~30-60 papers each, web-only research).

---

## 2. Cross-domain overlap map (active disambiguation needed)

The following pairs need explicit handoff rules to avoid duplication / scope-drift in Phase 1. Each spec contains its own §6 with the canonical handoffs; below is the master table.

| Topic | Owner | Adjacent domain | Handoff rule |
|-------|-------|-----------------|--------------|
| GARCH families | 03 (theory + descriptive fit) | 16 (option-pricing-vol implication) | 03 owns the empirical-fit-of-volatility paper; 16 owns it when calibrated for option pricing |
| Multifractal moments | 03 (stylized fact) | 04 (decomposition / forecasting) | 03 keeps moment-scaling-as-fact; 04 keeps wavelet / multifractal forecasting |
| OFI / LOB long memory | 06 (microstructure) | 03 (Hurst-of-order-flow as stylized fact) | 06 keeps OFI for impact / market-making; 03 cross-link only |
| Round-number / level effects | 09 (price-data evidence) | 07 (ICT/SMC trading rule) | 09 keeps the empirical price-clustering; 07 keeps the trading-rule application |
| Round-number / OPEX strikes | 09 vs 12 vs 08 | OPEX-strike pinning is dealer-flow magnetism | 12 owns dealer-gamma-pinning specifically; 09 owns generic round-number psychology; 08 owns OPEX-day VWAP / volume |
| FX bid/ask clustering | 09 (round-number side) | 06 (microstructure side) | 09 owns the clustering papers per se; 06 owns microstructure pricing / spread decomposition |
| Order flow → exchange rate | 06 (microstructure) | 11 (FX content) | 06 owns Lyons hot-potato / order-book theory; 11 owns Evans-Lyons portfolio-of-investors macro |
| Variance / vol risk premium | 16 (vol trading) | 03 (descriptive vol) | 16 owns trading-implication; 03 owns realized-vol stylized fact |
| Trend / momentum | 14 | 13 (factor) | 14 owns asset-class trend; 13 owns cross-section value-momentum-everywhere |
| Mean reversion | 15 | 14 (regime opposite of trend) | 15 owns pairs / cointegration / OU; 14 owns time-series momentum post-reversal |
| Drawdown / Kelly | 21 | 03 (tail estimation method) | 21 owns sizing application; 03 owns tail-fitting methodology |
| ML asset pricing | 19 (Gu-Kelly-Xiu) | 13 (factor models) | 19 owns ML methodology paper; 13 owns the empirical-finding-as-factor-evidence |
| RL execution | 20 (RL trader) | 06 (Almgren-Chriss + RL) | 06 owns RL-for-VWAP / minimum-impact; 20 owns RL-as-trader / portfolio agent |
| LLM extracted sentiment | 19 (as ML feature) vs 20 (as agent) vs 17 (as data source) | tri-junction | 17: LLM sentiment as research data → 17. LLM features feeding ML → 19. LLM as agent making trades → 20 |
| Behavioral momentum | 17 | 14 (TS momentum + crashes) | 17 owns the BSV / Hong-Stein / behavioral-mechanism papers; 14 owns the empirical momentum-strategy literature |
| Disposition effect | 18 (individual) | 17 (aggregate market manifestation) | 18 owns Odean / Shefrin-Statman; 17 owns market-aggregate effects |
| Hedge-fund alpha | 22 | 13 (factor evidence) | 22 owns single-fund / hedge-fund-aggregate papers; 13 owns factor-decomposition |
| Adaptive markets | 17 (Lo) | 22 (decay of published anomalies) | 17 owns AML conceptually + Lo papers; 22 owns McLean-Pontiff alpha-decay quantification |
| Risk-of-ruin / fat-tail Kelly | 21 | 03 (Hill estimator / tail index) | 21 owns sizing; 03 owns the tail-index estimation technique |
| Vol regime change-point | 05 (CP detection) | 16 (vol regime trading) | 05 owns the detection method; 16 owns the trading-rule using detection output |
| Cross-asset correlation gate | 13 (DCC, factor) | 21 (correlation-aware sizing) | 13 owns correlation-modeling; 21 owns sizing-application |
| FX safe-haven | 11 | 10 (gold-as-safe-haven) | 11 owns USD / JPY / CHF safe-haven; 10 owns gold; cross-link in both |
| Round-number ICT levels | 09 + 07 + 12 | tri-junction | 09 keeps the empirical price evidence; 07 keeps ICT-style level-trading rules; 12 keeps OPEX-strike-magnetism |

**Worker rule:** if uncertain about ownership, read the §6 of *both* candidate specs; the more specific domain wins. When both are equally specific, default to ownership of *primary contribution type*: theory → 01, statistical method → 02, distribution → 03, decomposition → 04, detection → 05, microstructure → 06, ICT → 07, volume → 08, level-effect → 09, gold → 10, FX → 11, equity-index → 12, factor → 13, trend → 14, mean-reversion → 15, vol → 16, behavioral → 17, psychology → 18, ML → 19, RL/LLM → 20, sizing → 21, hedge-fund → 22.

---

## 3. Suggested dispatch order

**RECOMMENDATION: full parallel (all 22 simultaneous).**

Reasoning:
1. **No hard dependencies.** Each domain is independently scoped and uses only public web sources. No domain consumes the output of another in Phase 1.
2. **Subscription-bounded.** All workers run on Opus 4.7 + max effort via subscription (memory `feedback_subagent_dispatch_opus47_max_effort`). No Anthropic API spend.
3. **Convergence efficiency.** Phase 2 synthesis assumes ~simultaneous completion; staging would just push synthesis later.
4. **Cross-domain handoff via §6** — if a worker finds a paper in the wrong domain, they note the cross-link in `cross_domain_links`, and synthesis agents will pick up the routing.

**Soft order if rate-limit considerations force staging** (e.g., subscription concurrent-message limits):
- **Wave A (foundational, large literature):** 1, 2, 3, 6, 16, 19 — these have the largest, most-established literatures; workers can hit ground running.
- **Wave B (asset-class & strategy):** 10, 11, 12, 13, 14, 15, 21 — depend on no other domain but benefit from foundational literature being available for cross-link lookup.
- **Wave C (specialized & emerging):** 4, 5, 7, 8, 9, 17, 18, 20, 22 — smaller / more niche / faster-moving frontier. Some (7, 9, 18, 22) have lower upper bounds and can finish faster.

Recommended: dispatch all 22 in parallel in one batch. Treat any domain that returns < 20 papers as a flag for synthesis review (may indicate fallback strategy or genuine literature scarcity).

---

## 4. Phase 1 worker quality discipline

(Identical reminders for every domain — orchestrator should compose into the shared prompt template.)

1. **Cite URLs, no fabrication.** Every paper must have a working URL or be marked `seed candidate — verify before use`. If a worker cannot verify a seed paper, drop it; do NOT invent.
2. **UTF-8 encoding** for all output `.md` and `.csv` files.
3. **Subscription-bounded.** Pure WebSearch + WebFetch. No Anthropic API calls beyond the worker's own dispatch.
4. **Output exactly two files** per domain: `papers.md` (human-readable) + `papers.csv` (machine-readable, schema in §7 of each spec).
5. **Per-paper schema** must include: `id`, `title`, `authors`, `year`, `source`, `url`, `abstract` (1-3 sentences), `key_findings` (3-5 bullets), `relevance_to_gtos`, `potential_hypothesis`, `cross_domain_links`. Domain-specific extra fields per spec §7.
6. **Reject papers without GTOS relevance.** Every entry must have a non-empty `relevance_to_gtos`. If a paper is foundational but has no GTOS hook, that's fine — say so and demonstrate the bridge.
7. **No reading-list bloat.** Better 30 strong papers than 60 weak ones. Domain spec target ranges are guides; quality bar dominates.
8. **Cross-link, don't duplicate.** If a paper belongs more naturally to another domain per §6 of this index or the spec, mark `cross_domain_links` and let synthesis route it.
9. **Recent-decade emphasis.** Each spec's "Recent advances 2020-2025" section is critical — the system is decaying empirically (item #4 / F11 / F15) and post-2020 regime literature is highest-leverage.
10. **Document gaps.** If a domain has a known limitation (e.g., domain 07 ICT/SMC academic gap), explicitly flag in the worker's `gaps_and_caveats` synthesis section.

---

## 5. Output structure (Phase 1 worker writes)

```
research/ml_program/literature/
  _specs/                              # this directory (PHASE 0 — meta-designer; READ-ONLY in Phase 1)
    _INDEX.md                          # this file
    01_math_foundations.md
    02_statistical_methodology.md
    ...
    22_hedge_fund_alpha_wallstreet_quantum.md
  01_math_foundations/                 # PHASE 1 worker writes here
    papers.md
    papers.csv
  02_statistical_methodology/
    papers.md
    papers.csv
  ...
  22_hedge_fund_alpha_wallstreet_quantum/
    papers.md
    papers.csv
  synthesis/                           # PHASE 2 (later)
```

---

## 6. Phase 2 / Phase 3 forward look (informational only)

After Phase 1 completes:
- **Phase 2** dispatches 5-7 synthesis agents, each covering 3-5 domains, ranking by relevance to GTOS subsystems and producing `literature/synthesis/{group}.md`.
- **Phase 3** dispatches 1-3 hypothesis agents that consume all syntheses + Q1.3 data findings; output is `literature/HYPOTHESIS_BACKLOG.md`.
- **Phase 4** is CEO triage + experimentation against MT5 data, subscription-bounded.

Phase 1 workers should NOT attempt synthesis in their domain output. Their job is high-quality, well-annotated paper extraction. Synthesis happens later with cross-domain perspective.

---

*This index is maintained by the meta-designer. Phase 1 workers may consult it but do not edit. Phase 2+ updates go in the parent program docs.*
