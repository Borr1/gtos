# G4 Source Index - 2026-05-06

**Lane:** `G4`
**Domain:** `market microstructure, order book, auction`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Scope:** source evidence for G4 research artifacts only

## Fetch Ledger

Raw public-source responses were cached under `research/science_program_2026_05/00_control/g4_source_evidence_raw/`.
Network fetches were requested because the controlling prompt requires public source evidence to be saved before claims are made. Blocked responses are retained as blocker evidence, not claim evidence.

| Source id | URL | HTTP status | Raw cache | Use in G4 |
| --- | --- | ---: | --- | --- |
| `SRC-G4-PAPER-OFI-CONT` | https://academic.oup.com/jfec/article/12/1/47/816163 | 403 | `cont_kukanov_stoikov_price_impact_order_book_events.html` | Blocked raw page; claim supported through source-indexed search/open evidence and RePEc abstract URL below. |
| `SRC-G4-PAPER-OFI-REPEC` | https://ideas.repec.org/p/arx/papers/1011.6402.html | indexed via web search | not fetched by curl | Mechanism prior for OFI/depth impact. |
| `SRC-G4-PAPER-QUEUE-CONT` | https://epubs.siam.org/doi/10.1137/110856605 | 403 | `cont_de_larrard_markovian_limit_order_market.html` | Blocked raw page; claim supported through source-indexed search/open evidence. |
| `SRC-G4-PAPER-QUEUE-SSRN` | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1735338 | 403 | `cont_de_larrard_ssrn.html` | Blocked raw page; blocker evidence only. |
| `SRC-G4-PAPER-LOB-SIGNALS` | https://kclpure.kcl.ac.uk/portal/en/publications/enhancing-trading-strategies-with-order-book-signals | 200 | `cartea_donnelly_jaimungal_order_book_signals.html` | Mechanism prior for volume imbalance/adverse selection. |
| `SRC-G4-PAPER-CASCADE-OSLER` | https://www.newyorkfed.org/research/staff_reports/sr150.html | 200 | `osler_stop_loss_price_cascades_nyfed.html` | Mechanism prior for stop-loss cascades. |
| `SRC-G4-DATABENTO-SCHEMAS` | https://databento.com/docs/schemas-and-data-formats/whats-a-schema | 200 | `databento_schemas.html` | Source capability evidence for MBO/MBP/trades/imbalance schemas. |
| `SRC-G4-DATABENTO-MBO` | https://databento.com/docs/schemas-and-data-formats/mbo | 200 | `databento_mbo.html` | Source capability evidence for L3/MBO order-id data. |
| `SRC-G4-CME-MBO` | https://www.cmegroup.com/education/market-by-order-mbo.html | 403 | `cme_market_by_order_mbo.html` | Blocked raw page; source-indexed web evidence only. |
| `SRC-G4-CME-RULE573` | https://www.cmegroup.com/rulebook/files/cme-group-Rule-573.pdf | 403 | `cme_globex_pre_open_guidance_rule_573.pdf` | Blocked. No G4 claim depends on this document. |
| `SRC-G4-NASDAQ-CROSSES` | https://www.nasdaqtrader.com/trader.aspx?id=openclose | 200 | `nasdaq_opening_closing_crosses.html` | Auction/imbalance source capability and timing evidence. |
| `SRC-G4-NASDAQ-FAQ` | https://www.nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf | 200 | `nasdaq_openclose_faqs.pdf` | Auction FAQ evidence; not parsed for feature claims. |
| `SRC-G4-LBMA-GOLD` | https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price | 200 | `lbma_gold_price_faq.html` | LBMA/Gold Price page cache; official auction detail is also indexed from ICE below. |
| `SRC-G4-LBMA-DAILY` | https://www.lbma.org.uk/prices-and-data/about-lbma-daily-auction-prices | 200 | `lbma_daily_auction_prices.html` | LBMA daily-auction context. |
| `SRC-G4-ICE-LBMA` | https://www.ice.com/iba/lbma-precious-metals | indexed via web open | not fetched by curl in this path | Official auction mechanics and timing evidence. |
| `SRC-G4-VPIN-COUNTER` | https://www.sciencedirect.com/science/article/pii/S1386418113000189 | 403 | `vpin_counterevidence_sciencedirect.html` | Blocked response retained; not used as claim evidence. |

## Local GTOS Artifacts Read

| Artifact | Key G4 use |
| --- | --- |
| `.context/LIVE_STATE.md` | Fresh live state, branch, clean-tree and shadow-log inventory. |
| `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` | Latest numbered handoff; historical but mandatory. |
| `.context/00_core/quick_reference_card.md` | Live risk/kz rules and `NO_PROMOTION_VERDICT` posture. |
| `.context/00_core/research_operating_doctrine.md` | Orderflow doctrine and strict promotion boundary. |
| `.context/00_core/research_current_state.md` | Current orderflow, V2b, LTO, K55, and label-separation state. |
| `.context/00_READING_ORDER.md` | Mandatory Tier 2-4 reading guide. |
| `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md` | Stop-cascade mechanism, momentum-baseline unresolved route, decay risks. |
| `.context/01_knowledge_base/kb_gold_market_deep_knowledge.md` | Gold microstructure and COT killed-route warnings. |
| `.context/01_knowledge_base/kb_validation_and_monitoring_framework.md` | Statistical/promotion discipline. |
| `research/science_program_2026_05/00_control/PROGRAM_GOVERNOR_2026-05-06.md` | G0 program boundary and safety counters. |
| `research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.md` | Required row schemas. |
| `research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md` | Zero-new-cash and validation-safe blockers. |
| `research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md` | G0 merge discipline and stale-route warnings. |
| `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_RESEARCH_CLOSURE_SYNTHESIS_2026-05-02.md` | Local orderflow synthesis, closed routes, NAS100 adverse-selection direction. |
| `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_VALIDATION_SYNTHESIS_2026-05-02.md` | MBO diagnostic signal and label-limited status. |
| `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md` | Cached NAS100 stability, date concentration, thin-depth fields. |
| `research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md` | NAS100 floors and Databento live license blocker. |
| `research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md` | Sierra depth feature state and guarded queue. |
| `research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md` | Proxy classes and blocked source rows. |
| `research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md` | GBPJPY two-book blocker and pre-registered design. |
| `research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.md` | 6B common-second policy and SI depth blocker. |
| `research/program_control/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.md` | Sierra `.scid` footprint/profile feature readiness and blockers. |
| `research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.md` | Existing orderflow primitive registry and role boundaries. |
| `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_AND_PRIMITIVE_DATA_SOURCE_SYNTHESIS_2026-05-02.md` | Sierra/Databento source architecture and primitive data limits. |
| `research/primitive_orderflow_sources_2026-05-02/PRIMITIVE_ORDERFLOW_SOURCE_SYNTHESIS_2026-05-02.md` | Primitive source ranking and FX/futures proxy limits. |
| `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.md` | V2b unresolved prospective-pair blocker. |
| `research/program_control/AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md` | Execution-mode and AI/orderflow research questions. |

## Source-Use Boundaries

- Public papers and official docs are mechanism priors and source capability evidence only.
- Local Databento/Sierra rows are diagnostic and shadow-only unless a future source contract, sample floor, no-leak test, and label policy pass.
- No paid data was fetched in this lane.
- No source is marked validation-safe by G4.
- Every G4 artifact remains `NO_PROMOTION_VERDICT`.
