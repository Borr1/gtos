# G7 Macro, Cross-Asset, Rates, FX, Gold Domain Synthesis

Generated: 2026-05-06T08:30:00Z
Lane: G7
Promotion verdict: NO_PROMOTION_VERDICT

## Scope And Controls

This artifact is a primitive-science research synthesis only. It does not change live prompts, execution, risk, order routing, permissions, MT5 behavior, selectors, canaries, paid-data access, or safety gates. All rows created from this synthesis carry `NO_PROMOTION_VERDICT`.

G0 governor artifacts were treated as controlling. Master registries remain G0-owned and should not be updated by this lane pass until a later governor merge.

## Mechanisms Worth Finding

1. Dollar and real-rate impulse context: gold and silver should be sensitive to USD and real-yield shocks, but local evidence says DXY is soft context only and not a hard filter.
2. Scheduled macro attention: FOMC and high-impact calendar windows can synchronize attention, widen ambiguity, and alter fill/path behavior before and after releases.
3. LBMA/ICE gold benchmark timing: AM/PM benchmark windows can change metals liquidity and path behavior, but timestamp-only fix context is not auction imbalance data.
4. COT slow-positioning context: official CFTC data can describe stale weekly crowding, but direct gold COT predictiveness is killed by local empirical evidence.
5. FX/rates/carry/global-liquidity context: BIS and rates sources can define slow macro states for USDJPY, GBPJPY, GBPUSD, and metals, but available sources are not decision-safe.
6. Cross-asset stress state: equity, index, rates, vol, USD, JPY, and gold correlations can change tail behavior and portfolio co-movement, but this must not replace live risk gates.
7. Gold-specific flow context: WGC, LBMA, and related official/metals sources can define slow demand and benchmark-calendar states, not intraday alpha by themselves.

## Evidence That Distinguishes Noise

Useful evidence must be frozen as-of the decision timestamp and must survive label separation. A macro row is only sharpened if it predicts a predeclared cohort before the outcome window opens.

Distinguishing evidence:

- Publication timestamp must be separated from observation date. COT Tuesday positions are not decision-safe until the CFTC release is cached after publication.
- Daily rates, DXY, and broad-dollar values cannot be used as intraday features unless the bar close or release time precedes the GTOS decision.
- FOMC/event labels must distinguish pre-event anticipation, release window, and post-release digestion.
- LBMA fix labels must use benchmark timestamps only unless legal auction imbalance data is later source-contracted.
- Slow weekly/monthly flow sources must be tested as context/regime labels, not as M15 execution triggers.
- Cross-asset stress must be tested against existing correlation/risk logic as a research comparator only, with no live gate edits.

## GTOS Components Affected

Research-only affected components:

- source-contract ledger for CFTC, BIS, Fed, FRED/rates, LBMA, WGC, and ICE/DXY
- future offline cohort labeling for macro event windows, fix windows, dollar/rate states, and cross-asset stress states
- monthly/rolling edge-decay diagnostics where macro states may explain nonstationarity
- neighbor-lane dependency notes for G5 behavioral attention, G8 options/vol, and G11 source governance

No live component is modified or recommended for promotion.

## Strongest Source Families

Official/public sources cached or reviewed in this pass:

- CFTC Commitments of Traders pages for official weekly positioning and historical compressed files.
- BIS statistics index for international banking, global liquidity, FX, derivatives, and SDMX/bulk-download discovery.
- Federal Reserve FOMC calendars and information for scheduled macro attention windows.
- Federal Reserve economic research page for later research-feed source discovery only.
- LBMA Gold Price and daily auction pages for official benchmark/timing context.
- World Gold Council Goldhub data page for gold price, return, volatility, correlation, and flow-style data discovery.
- ICE U.S. Dollar Index futures page as an official DXY-adjacent source candidate.

Local evidence and code were also reviewed, including GTOS gold knowledge base, validation framework, source readiness docs, external feed code, and lane triage reports.

## Lane Context Findings

Local cross-checks materially constrain the G7 search space:

- The GTOS gold knowledge base says COT positioning has zero predictive value for gold at 1-week and 4-week horizons in local analysis. G7 therefore treats direct gold COT as a killed route.
- The same knowledge base says DXY-gold inverse correlation is stable on daily data but low explanatory power, with DXY suitable only as soft context and not a hard filter.
- Source triage reports show CFTC gold and LBMA calendar data are feasible, but FX COT mapping, KMW fix data, BIS/H-K-M style macro sources, and retail/positioning data remain blocked or incomplete.
- External feed code and audits mention FRED daily series such as DFII10, DGS10, DGS2, DTWEXBGS, GVZCLS, T10YIE, and VIXCLS, but this lane could not see a validation-ready normalized cache in the working tree.
- Public FRED page/CSV refresh attempts failed during this pass, so FRED rows are source-contract blockers rather than validation inputs.
- `data/DXY_D1.csv` exists locally but appears stale and suspicious for official DXY scale/use; it cannot validate a DXY claim.
- The master roadmap contains older DXY/US10Y/SPX prompt-context ideas. Those are historical and stale relative to current no-live-change controls.

## Mechanism Conclusions

The best G7 contribution is not a direct macro trading rule. It is a source-governed context layer for later offline tests:

- Dollar/real-rate context may explain metals path differences, but only after daily-source as-of rules and low-R2 DXY counter-evidence are respected.
- FOMC and macro calendars are useful as event-cohort labels and ambiguity controls, not as automatic no-trade or trade rules in this pass.
- LBMA fix timing can define metals benchmark-window cohorts, but without auction imbalance or depth data it cannot claim executable flow.
- COT can remain a slow source-contract candidate for crowding/regime descriptions, while direct gold predictiveness is killed and FX mapping is blocked.
- BIS/global-liquidity/carry sources are plausible for slow FX/rates context but not decision-safe until tables, timestamps, and parsers are specified.
- Cross-asset stress context should be tested as path/tail/correlation description only; live risk gates remain untouched.

## Counter-Evidence And Decay Modes

Counter-evidence reviewed:

- Local gold research kills COT as a direct gold predictor at 1-week and 4-week horizons.
- Local gold research demotes DXY to soft context due low explanatory power despite stable inverse correlation.
- Macro relationships can invert by inflation regime, central-bank reaction function, crisis state, and USD funding stress.
- FOMC/pre-announcement effects can decay after adoption and may not transfer from equities/rates to XAUUSD M15 path labels.
- Benchmark-window behavior can be a time-of-day liquidity artifact rather than a gold-specific flow effect.
- Slow WGC/BIS/COT data can describe regimes too slowly for intraday GTOS decisions.

Known decay modes:

- Macro proxies become crowded or absorbed after public adoption.
- Daily/weekly data are too stale for M15 decisions unless used only as prior context.
- Publication lag and revised data create lookahead if observation date is treated as availability time.
- Cross-asset correlations are unstable during stress and can flip sign.
- Broker CFD symbols may not map cleanly to futures, index, or OTC reference instruments.

## Neighbor Pass

Neighbor lanes checked after the first synthesis pass:

- G5 committed behavioral artifacts exist. G5 row `HYP-G5-XG7-MACRO-ATTN-009` asks whether macro event labels interact with behavioral attention/news labels, blocked by calendar freshness and source contracts.
- G8 had only the controlling prompt at this HEAD. No committed G8 options/vol rows existed for integration.
- G11 had only the controlling prompt at this HEAD. No committed G11 source-expansion rows existed for integration.

Cross-domain hypotheses added as G7-owned candidates only:

- G7 x G5: macro/FOMC attention labels should be tested as behavioral attention cohorts before any news or event interpretation.
- G7 x G8: rates/USD/event states may condition options-vol or vol-of-vol stress, but this is blocked until G8 commits source-safe rows.
- G7 x G11: macro source freshness, publication lag, and local cache absence should be governed by G11 later, but G11 has not run.

All cross-domain rows remain blocked and carry `NO_PROMOTION_VERDICT`.

## Source And Budget Blockers

- FRED official refresh failed during this pass; local normalized FRED cache was not visible in the working tree.
- BIS data requires selecting exact tables, SDMX endpoints, publication rules, and cache tests before use.
- CFTC COT is weekly/delayed and FX contract mapping is not complete.
- LBMA benchmark timing is public, but auction imbalance/order-flow detail is not source-contracted.
- WGC data discovery is public, but precise downloadable series, as-of timestamps, and local cache governance remain incomplete.
- ICE DXY futures page is public, but no validation-safe local DXY parser/cache exists.
- New paid sources or API budget were not approved; source budget remains `$0`.

## Stop Output Map

- Domain synthesis: this file.
- Lane context ledger: `G7_CONTEXT_LEDGER_2026-05-06.md`.
- Ambiguity ledger: `G7_AMBIGUITY_LEDGER_2026-05-06.md`.
- Counter-evidence/decay review: this file, "Counter-Evidence And Decay Modes".
- Mechanism rows: `G7_MACRO_CROSS_ASSET_MECHANISM_ROWS_2026-05-06.json`.
- Hypothesis rows: `G7_MACRO_CROSS_ASSET_HYPOTHESIS_ROWS_2026-05-06.json`.
- Killed-route notes: context ledger and row-level `killed_route_check` / `promotion_blockers`.
- Experiment prereg specs: `G7_MACRO_CROSS_ASSET_EXPERIMENT_PREREG_SPECS_2026-05-06.json`.
- Source contracts and source/budget blockers: `G7_MACRO_CROSS_ASSET_SOURCE_CONTRACT_ROWS_2026-05-06.json` and `G7_SOURCE_INDEX_2026-05-06.md`.
- Neighbor-lane cross-domain hypotheses: this file and G7 hypothesis rows `HYP-G7-XG5-MACRO-ATTN-010`, `HYP-G7-XG8-VOL-MACRO-011`, and `HYP-G7-XG11-SOURCE-FRESH-012`.

Promotion verdict: NO_PROMOTION_VERDICT
