# G8 Options, Gamma, Volatility Risk Premium Domain Synthesis - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

## Scope

G8 translates options/gamma/volatility-risk-premium ideas into source-contracted GTOS shadow hypotheses only. It does not promote a filter, selector, prompt change, execution change, risk change, or safety change.

Primary objects studied:

- Dealer gamma exposure and gamma-flip/wall regimes.
- VIX1D/VIX9D/VIX/VIX3M/GVZ/VVIX implied-volatility regimes.
- Variance risk premium construction from implied variance minus realized variance.
- OPEX/expiry calendar regimes, especially for index symbols.
- ETF options proxies for CFD instruments: `QQQ -> NAS100`, `DIA/SPY -> US30`, `GLD -> XAUUSD`, `SLV -> XAGUSD`.

## Source Refresh Result

Earlier LTO-032 docs correctly blocked official historical aggregate GEX and VRP validation. G8 confirmed that the public-source state is more nuanced:

- Official/historical aggregate GEX remains blocked. No paid data was purchased, and no Cboe delayed option-chain scraping was performed.
- FlashAlpha Basic remains a vendor proxy and forward-context source only in local GTOS. Its public API page describes GEX, gamma flip, call/put walls, 0DTE, and free-tier limits, but that does not make it official or validation-safe.
- Cboe public CSV histories were found and cached for VIX, VIX1D, VIX9D, VIX3M, GVZ, and VVIX through 2026-05-05. These unlock source-design work, not promotion. They still need parser, publication timestamp, license, and no-lookahead join tests.
- Cboe SPX/VIX product specs and methodology PDFs are useful for calendar and index-construction context, not position or gamma data.

## Mechanism Translation

1. **Dealer gamma feedback.** Literature evidence supports a mechanism where aggregate dealer gamma sign can affect intraday momentum/reversal, especially when liquidity is thin. The GTOS version must use point-in-time gamma state, gamma-flip distance, and wall proximity only as context until an official or legally replayable historical source exists.

2. **Short-horizon implied-vol stress.** VIX1D and VIX9D can express near-term equity-index volatility pressure. A GTOS hypothesis can test whether the VIX1D-VIX9D spread or level changes lifecycle ambiguity, no-fill behavior, or path-R distribution for NAS100/US30 candidates. The source is public but not yet validation-safe.

3. **Metals implied volatility.** GVZ can proxy gold ETF implied-volatility state. This may matter for XAUUSD/XAGUSD candidate lifecycle, but the ETF-to-CFD transfer must be treated as a proxy risk, not a direct gold spot truth.

4. **VRP construction.** Variance risk premium should be treated as a formula contract: implied variance source minus realized variance computed strictly with bars ending before decision time. Academic VRP results in quarterly equity returns do not directly validate intraday GTOS behavior.

5. **OPEX calendar pressure.** GTOS already has OPEX calendar features in `research/ml_program/scripts/features/time_session.py`. G8 should not duplicate "add OPEX feature" work. Any stronger pinning/unwind hypothesis requires gamma/open-interest context, not calendar alone.

6. **Proxy transfer risk.** Options data usually lives on ETFs or indices while GTOS trades CFDs or broker symbols. Every proxy row needs explicit mapping, as-of timestamps, basis/correlation checks, and a blocker if the proxy cannot be reconciled to the traded symbol.

## Counter-Evidence And Decay Modes

- Dealer gamma is not universally stabilizing or destabilizing. The sign of the mechanism depends on whether dealers are net positive or negative gamma, liquidity state, maturity bucket, and proximity to walls/flip levels.
- Vendor GEX values can differ by model, option chain coverage, stale open interest, contract filtering, and spot reference. FlashAlpha is useful for forward context but cannot validate a historical signal without replayability and legal timestamping.
- VIX1D/VIX9D are equity-index implied-volatility indices. They may be irrelevant for metals and only indirectly relevant for US30/NAS100 broker CFDs.
- GVZ is a gold ETF volatility index, not spot XAUUSD implied volatility.
- VRP can easily become a lookahead feature if realized variance includes bars after the decision timestamp.
- OPEX calendar effects decay if most pressure is already reflected in price or if the actual gamma/open-interest distribution is absent.
- Same dataset discovery cannot validate these hypotheses. Every experiment row keeps outcome review closed.

## Killed Routes

- Do not scrape Cboe delayed option-chain tables for historical gamma.
- Do not treat FlashAlpha vendor text as official exchange gamma data.
- Do not treat public Cboe CSV discovery as validation-safe.
- Do not add live GEX/OPEX/VRP filters to `src/`, `prompts/`, `config/`, `permissions`, `execution`, or selectors.
- Do not mix broker actual-R, synthetic path-R, lifecycle no-fill, observation-only, and context-only labels in one metric.
- Do not validate VRP with realized variance that reaches past the decision timestamp.
- Do not claim OPEX calendar alpha without a generic calendar baseline and, for pinning claims, point-in-time gamma/open-interest context.

## Neighbor-Lane Pass

G2 stochastic tails was available and read. It treats options/gamma/VRP as partial/blocked sources and cautions against direct volatility-clustering promotion. G8 aligns with that: vol-index and VRP rows are context or lifecycle hypotheses until source contracts are proven.

G7 and G10 were not present in `research/science_program_2026_05` at run time, so no neighbor outputs were available. The cross-domain hooks are therefore preregistered as pending:

- With G2: VIX/VVIX/GVZ/VRP features should be tested against stochastic-tail and volatility-family baselines rather than replacing them.
- With G7: if macro/liquidity outputs later exist, test whether implied-vol stress only matters during liquidity/news regimes.
- With G10: if market-state or portfolio-context outputs later exist, test whether gamma/OPEX states are portfolio exposure context rather than entry filters.

## Source/Budget Blockers

- Budget: `$0` new external cash; paid historical GEX remains blocked.
- Official historical aggregate GEX: blocked pending legal source and replayable timestamps.
- FlashAlpha Basic: free-tier, vendor proxy, forward-context only; validation_safe=false.
- Cboe volatility CSVs: public and cached, but source registry/parser/publication-time/no-lookahead tests missing.
- VRP: formula preregistration required before any outcome review.
- OPEX: local calendar overlap exists; actual pressure hypotheses require point-in-time options data.

## Output Summary

G8 produced seven mechanism rows, seven hypothesis rows, seven preregistered experiment specs, eight source-contract rows, a source index, context ledger, ambiguity ledger, and completion audit. Every row/report carries `NO_PROMOTION_VERDICT`.

