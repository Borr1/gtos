# G11 Context Ledger

Date: 2026-05-06  
Lane: G11 Data Sources And Market Expansion  
Verdict: NO_PROMOTION_VERDICT

## Mandatory Session Context

| Source | Role in G11 | Key evidence used | G11 treatment |
|---|---|---|---|
| `.context/LIVE_STATE.md` | Authoritative current state after regeneration | HEAD `42bf621c`; G11 branch active; latest handoff is session 54; `.context/00_core/research_current_state.md` is stale vs HEAD | Used as state gate, not staged |
| `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` | Weekend goal framing | Primitive-science branch discipline and goal-lane separation | Context only |
| `.context/00_core/quick_reference_card.md` | Operational guardrails | Expired-POI limitation and emergency stops remain live constraints | Reinforces no live change |
| `.context/00_core/research_operating_doctrine.md` | Research method | Strict promotion, source cache protocol, no outcome peeking, `NO_PROMOTION_VERDICT` default | Governs all rows |
| `.context/00_core/research_current_state.md` | Historical research map | Marked stale by live-state generator | Not used as current authority |
| `.context/00_READING_ORDER.md` | Deep-work reading map | Read as required, but stale relative to current science branch | Context only |

## G0 Program Context

| Source | Evidence | G11 implication |
|---|---|---|
| `G0_WAVE1_RECONCILIATION_2026-05-06.md` | Wave 1 merged G1-G6 only; G11 listed as ready-to-launch; all source contracts `validation_safe=false`; survivor backlog 0 | G11 starts from no inherited promotion-safe source |
| `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md` | 41 mechanisms, 51 hypotheses, 50 preregs, 45 source rows, no validation-safe row | G11 must not mark any source safe |
| `SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | G0-level source rows remain blocked | G11 source rows are source-contract scaffolds only |
| `GOAL_STATUS_REGISTRY_2026-05-06.json` | G11 status was `READY_TO_LAUNCH_NOT_RUN` | This lane produces first G11 artifacts |
| `PROGRAM_GOVERNOR_2026-05-06.md` and `SCHEMA_CONTRACTS_2026-05-06.*` | Required row contracts and promotion invariants | Used for JSON schema fields |

## Local Source-Unblocking Context

| Source | Evidence | G11 implication |
|---|---|---|
| `research/operations/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | 11 source contracts, all `validation_safe=false`; blockers across COT, BIS, FRED, Databento, Sierra, FlashAlpha, VIX/gamma/VRP | G11 keeps all source rows blocked |
| `research/operations/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.md` | CFTC/FRED/FlashAlpha local cache exists; BIS selected but not cached; FX mapping still required | Public data can support manifests, not validation |
| `research/operations/LTO031_LTO032_DATABENTO_CREDIT_REPLAY_MANIFESTS_2026-05-06.md` | 8 requests, 0 fetch-ready, 113 local raw Databento files, 3590.279 MB, estimate-before-fetch required | No paid Databento pull; local cache context only |
| `research/operations/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.md` | 125 converted CSV files all bid/ask-capable; 3 blocked symbol counts; VAH/VAL deferred | Sierra bid/ask volume is practical; stacked imbalance/profile definitions remain blocked |
| `research/operations/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.md` | FlashAlpha Basic forward context only; historical aggregate GEX/VIX1D/VIX9D/VRP blocked | Options/gamma remains source-blocked |
| `research/operations/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md` | 5 source bundles, 0 numeric-ready | No external numeric K55 feature is ready |
| `research/operations/NO_AI_SHADOW_OBSERVER_RELOAD_PROOF_SOURCE_REGISTRY_2026-05-06.md` | Active observers: EURUSD, GER40, UK100; controls/inactive excluded | Observer lanes are suitable for source diagnostics only |

## Local Primitive And Expansion Context

| Source | Evidence | G11 implication |
|---|---|---|
| `research/primitive_orderflow_sources_2026-05-02/PRIMITIVE_ORDERFLOW_SOURCE_SYNTHESIS_2026-05-02.md` | CME futures as primitive source; Databento best practical programmatic; Sierra best visual/forward; LMAX price/access blocked; broker-vs-proxy transfer must be measured | G11 adopts source-transfer gate |
| `research/instrument_expansion_2026-05-02/01_STRUCTURAL_SCREEN.md` | Mechanical screen found candidate instruments but warns about spread/slippage/tick-volume proxy limits | Expansion is backlog, not promotion |
| `research/instrument_expansion_2026-05-02/02_DECAY_ANALYSIS.md` | No fleet-wide mechanical OB decay; XAUUSD decay likely AI-side, GBPJPY market-side; no corrected-p survivor | Do not use decay evidence to expand symbols |
| `research/instrument_expansion_2026-05-02/03_MICROSTRUCTURE.md` | FX spread burden, index late-US density, crypto weekend/min-lot, oil gaps; suggests shadow KZ extension logging only | Friction gate required before expansion |
| `research/expanded_oos_2026-05-03/EXPANDED_OOS_FINAL_SYNTHESIS_2026-05-03.md` | True temporal OOS blocked by zero resolved pairs | No validation labels opened |
| `research/expanded_oos_2026-05-03/EXPANDED_OOS_DATA_SOURCE_MAP_2026-05-03.md` | Source/proxy transfer diagnostic only; Sierra and Databento caches present but not validation-complete | Source map is context, not proof |
| `research/expanded_oos_2026-05-03/EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_2026-05-03.md` | Candidates frozen; opened outcome slices 0 | Maintains no-peeking discipline |

## Neighbor-Lane Context

| Neighbor | Files available | G11 result |
|---|---|---|
| G4 Microstructure Auction | Synthesis, context ledger, source index, mechanisms, hypotheses, preregs, source contracts, goal status | Added one G11/G4 source-gated-orderflow cross-domain hypothesis |
| G7 | No completed G7 lane artifact found at this HEAD | No G7 cross-domain hypothesis added |
| G8 | No completed G8 lane artifact found at this HEAD | No G8 cross-domain hypothesis added |

## Public Source Captures

Raw captures are stored under `research/science_program_2026_05/01_domain_syntheses/raw/G11_data_sources_expansion_sources_2026-05-06/`.

| Capture | Evidence used | G11 treatment |
|---|---|---|
| `sierra_intraday_file_format.html` | `.scid` file format; `NumTrades`, `BidVolume`, `AskVolume` fields; bid/ask aggressor notes | Supports Sierra bid/ask-volume source contract |
| `sierra_market_depth_file_format.html` | market-depth command types and `NumOrders`, `Price`, `Quantity` fields | Supports Sierra depth source contract |
| `cftc_cot_index.html` | COT purpose, Tuesday positions, Friday release, historical/API details | Context-only public positioning source |
| `fred_api_docs.html` | vintages, release calendar, API keys, series vintage dates | Context-only release-aware macro source |
| `bis_data_portal.html` | BIS Data Portal and release-calendar data | Context-only long-cycle macro source |
| `cboe_datashop.html` | downloadable market tick/trading data for options/equity/ETFs and historical/intraday/tick modes | Source exists but paid/licensed and not validation-safe |
| `cboe_vix_overview.html` | Cboe volatility-product context | Source context only |
| `nasdaq_trader_open_close.html` | Nasdaq opening/closing crosses and subscription-only imbalance data | Auction imbalance source blocked |
| `lbma_precious_metal_prices.html` | LBMA precious-metal benchmark descriptions and licensing notes | Price benchmark source blocked for validation |
| `databento_*.html` | HTTP 200, but JavaScript-shell pages only in captured HTML | Weak source-existence evidence only; no technical claims based on these captures |

