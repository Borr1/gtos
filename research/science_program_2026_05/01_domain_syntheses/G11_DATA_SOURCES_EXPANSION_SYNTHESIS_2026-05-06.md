# G11 Data Sources And Market Expansion Synthesis

Date: 2026-05-06  
Lane: G11 Data Sources And Market Expansion  
Branch: science-goals/g11-data-sources-expansion  
Controlling prompt: `research/science_program_2026_05/04_goal_prompts/G11_G11_DATA_SOURCES_EXPANSION_GOAL_PROMPT_2026-05-06.md`  
Verdict: NO_PROMOTION_VERDICT

## Scope Guard

This is a primitive-science research lane only. It does not authorize any live trading change, selector change, prompt edit, risk edit, execution edit, permissions edit, canary edit, MT5 behavior change, paid data pull, or order behavior change.

G11 asks a narrower question than "which instrument should be traded next": what source layer and market-expansion primitives are fit to support future validation without contaminating GTOS with stale, illegal, hindsight, proxy, or cost-blind data.

## Hypotheses Before Search

1. The first-order failure mode for external data is not predictive weakness, but provenance weakness: unknown as-of timestamps, license constraints, missing cache manifests, and delayed/revised releases.
2. Instrument expansion rankings are likely unstable when source coverage, spread burden, broker-vs-proxy transfer, and session liquidity are treated as primitives instead of afterthoughts.
3. Microstructure data should be source-gated before any feature research: Sierra local files and Databento historical futures can be useful, but not unless proxy transfer, date concentration, and label separation are explicitly measured.
4. Public macro/positioning sources can be useful as context, but their release lag and revision behavior probably make them unsafe for direct decision features at M15/H1 horizons.
5. Options/gamma/volatility sources may be relevant for index and gold stress regimes, but current GTOS source access is mostly forward-context or paid/licensed, not validation-safe.

## Search And Evidence Plan

1. Regenerate live state and read current G0 wave-1 artifacts at HEAD before relying on any stale handoff.
2. Cross-check local source-unblocking outputs, primitive orderflow source research, instrument expansion screens, expanded OOS source maps, and observer-source registries.
3. Fetch only free/public source pages required to verify access, licensing/as-of clues, and source structure. No paid source access was used.
4. Read G4 as the nearest completed neighbor lane. G7/G8 were not present at this HEAD as completed lane outputs, so no G7/G8-derived cross-domain rows were added.
5. Translate only source-valid mechanisms into `science_mechanism_v1`, `science_hypothesis_v1`, `experiment_prereg_v1`, and `source_contract_v2` rows. All rows retain `NO_PROMOTION_VERDICT`.

## Domain Synthesis

### 1. Source contracts are a primitive, not paperwork

G0 wave-1 left every source contract `validation_safe=false`. LTO031/LTO032 source-unblocking work reached the same conclusion across free public, Databento replay, Sierra footprint/profile, options/gamma/VRP, and K55 integration artifacts. G11 therefore treats source readiness itself as a market primitive:

- A source is not usable for validation until legality, cache path, as-of timestamp, publication lag, revision policy, feature role, and label separation are frozen.
- "Data exists" is weaker than "data can be used in a validation-safe feature."
- Any future G0 reconciliation should keep `validation_safe=false` for G11 rows until source-specific blockers are closed.

### 2. Market expansion needs three gates before performance

The instrument-expansion screens showed promising mechanical candidates, but the strongest recurring caveat was that ranking by mechanical OB behavior alone is insufficient. Before opening performance labels for a new symbol, G11 proposes three prerequisite gates:

- Source coverage gate: enough broker-actual history, source roots, and cache manifests exist for the candidate symbol and its proxy.
- Transfer gate: broker MT5 prints and external primitive source prints have measured alignment, lead-lag, and gap behavior.
- Friction gate: spread/ATR, tick value, min-lot, session density, weekend-gap, and kill-zone fit are measured before performance comparison.

This keeps AUDJPY, EURJPY, AUDUSD, EURUSD, SPX500, CHFJPY, NAS100, UK100, USDJPY, NZDUSD, and BTCUSD in a research backlog rather than a promotion backlog.

### 3. Sierra and Databento are complementary, not interchangeable

G4 and the primitive orderflow source research converge on a practical architecture:

- Sierra is best for local forward/recent bid/ask volume, `.scid` conversion, and footprint/profile research where local files already exist.
- Databento is best for targeted historical/API futures research, especially CME `GLBX.MDP3`, but live access and paid pulls remain blocked unless explicitly authorized.
- Direct exchange feeds are purer but operationally heavy. LMAX is a serious FX venue candidate but current price/access terms keep it out of G11 validation.

Sierra public documentation confirms `.scid` intraday records expose `NumTrades`, `BidVolume`, and `AskVolume`; Sierra market-depth files expose bid/ask add/modify/delete commands, `NumOrders`, `Price`, and `Quantity`. That is enough to justify source-contract rows, not enough to promote an orderflow feature.

### 4. Public macro/positioning sources are context-only until lag/revision behavior is frozen

CFTC COT, FRED, and BIS sources are accessible and useful for macro context and source manifests, but they have direct validation blockers:

- CFTC COT is weekly, based on Tuesday positions, normally released Friday, and classification is report-based rather than trader-intent truth. The gold KB already warns COT has not earned a direct XAUUSD filter role.
- FRED explicitly exposes vintages and release calendars, which is useful only if every feature joins by release/as-of timestamp rather than observation date.
- BIS data exposes a release-calendar driven public portal and long-cycle macro series; that is too slow for M15/H1 decision features without a separate hypothesis.

G11 therefore keeps these sources as `context_only` or `observation_only` until release-aware joins are implemented and preregistered.

### 5. Options/gamma and auction feeds are mostly blocked, but valuable to map

Cboe DataShop public pages confirm tick/intraday/daily options/equity data access exists, but source-unblocking artifacts already mark official/historical aggregate GEX, VIX1D/VIX9D, VVIX, VRP, and broader options/gamma history as blocked or incomplete. Nasdaq and LBMA auction/benchmark pages establish market-structure sources, but subscription/licensing limits and symbol-transfer ambiguity prevent validation use.

This matters because G4 identified index-auction and gold-fix style imbalance mechanisms as plausible neighbors. G11 records them as source contracts and killed or blocked routes, not as candidate production features.

### 6. Observer expansion is the safest way to learn

The no-AI observer source registry shows active observer candidates exist outside the live trading core. G11 treats observers as the correct container for market expansion:

- Collect eligibility, rejection, lifecycle, source freshness, spread, and source-transfer diagnostics.
- Keep labels unopened until preregistration and sample floors are satisfied.
- Do not convert observer evidence into trade selection without a later governed lane.

## Mechanism Inventory

G11 writes 7 mechanisms and 8 hypotheses:

- `SCI-G11-PROVENANCE-001`: source provenance and as-of integrity.
- `SCI-G11-COVERAGE-BIAS-002`: source-coverage bias in instrument expansion.
- `SCI-G11-SOURCE-TRANSFER-003`: broker/proxy transfer and lead-lag risk.
- `SCI-G11-PUBLIC-LAG-004`: public macro/positioning release lag and revisions.
- `SCI-G11-OPTIONS-VOL-005`: options/gamma/volatility source availability and licensing.
- `SCI-G11-OBSERVER-EXPANSION-006`: no-AI observer expansion as low-risk evidence collection.
- `SCI-G11-FRICTION-007`: spread/liquidity/session friction as a primitive expansion gate.

One cross-domain hypothesis is added after the G4 neighbor pass:

- `HYP-G11G4-SOURCE-GATED-ORDERFLOW-008`: source-contract readiness should reduce invalid orderflow-feature use before any G4 microstructure experiment is allowed to open outcome labels.

No G7/G8 cross-domain hypotheses were added because completed G7/G8 lane artifacts were not present at this HEAD.

## Promotion State

Every G11 mechanism, hypothesis, preregistration, source contract, and report carries `NO_PROMOTION_VERDICT`.

No source is validation-safe. No paid source was accessed. No outcome labels were opened. No live system file was edited.

