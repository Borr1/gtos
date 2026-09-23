# G5 Source Index

Generated: 2026-05-06T07:00:00Z
Lane: G5
Promotion verdict: NO_PROMOTION_VERDICT

No external raw data was downloaded in this pass. This file records web/source-index evidence used to form research-only hypotheses and source contracts. All external source contracts remain `validation_safe: false` until legality, cache, parser, timestamp, and no-lookahead checks pass.

## Academic Mechanism Sources

| Source ID | Source | URL | Used For | Research State |
| --- | --- | --- | --- | --- |
| LIT-G5-AMH-001 | Lo, "The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective" | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=602222 | Adaptive-market ecology, competition, edge decay | context-only |
| LIT-G5-PRED-001 | Brunnermeier and Pedersen, "Predatory Trading" | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=590767 | Forced-flow/predatory liquidation mechanism | context-only |
| LIT-G5-CASCADE-001 | Bikhchandani, Hirshleifer, and Welch, "A Theory of Fads, Fashion, Custom, and Cultural Change as Informational Cascades" | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1286306 | Informational cascades and fragile conformity | context-only |
| LIT-G5-HERD-001 | Lakonishok, Shleifer, and Vishny, "The Impact of Institutional Trading on Stock Prices" | https://shleifer.scholars.harvard.edu/publications/impact-institutional-trading-stock-prices | Herding and positive feedback, including weak/null evidence | context-only |
| LIT-G5-HERD-002 | Christie and Huang, "Following the Pied Piper" | https://rpc.cfainstitute.org/research/financial-analysts-journal/1995/following-the-pied-piper-do-individual-returns-herd-around-the-market | Herding counter-evidence using dispersion | context-only |
| LIT-G5-ATTN-001 | Barber and Odean, "All That Glitters" | https://academic.oup.com/view-large/114041066 | Attention-driven buying and news/volume attention proxies | context-only |
| LIT-G5-NEWS-001 | Tetlock, "Giving Content to Investor Sentiment" | https://cir.nii.ac.jp/crid/1363107369584529280 | Media pessimism, trading volume, and reversion interpretation | context-only |
| LIT-G5-FOMC-001 | Lucca and Moench, "The Pre-FOMC Announcement Drift" | https://www.fedinprint.org/item/fednsr/12655 | Scheduled macro attention/drift source family | context-only |
| LIT-G5-FOMC-DECAY-001 | Kurov, Wolfe, and Gilbert, "The disappearing pre-FOMC announcement drift" | https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/ | Decay/counter-evidence for macro attention anomaly | context-only |
| LIT-G5-LLM-001 | Lopez-Lira and Tang, "Can ChatGPT Forecast Stock Price Movements?" | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788 | LLM/news interpretation and adoption-decay framing | context-only |

## Candidate Data Sources

| Source ID | Source | URL | Used For | Blocker |
| --- | --- | --- | --- | --- |
| SRC-G5-GTRENDS-SMC-001 | Google Trends FAQ and Trends API documentation | https://support.google.com/trends/answer/4365533?hl=en-CA ; https://developers.google.com/search/blog/2025/07/trends-api | Search-attention proxy for SMC/ICT/XAUUSD crowding | no lane extractor, taxonomy, cache, or no-lookahead test |
| SRC-G5-CFTC-COT-GOLD-001 | CFTC Commitments of Traders | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm ; https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm | Slow positioning/regime context for gold/futures participation | weekly release lag, contract mapping, and role limitation |
| SRC-G5-OANDA-ORDERBOOK-001 | OANDA Order Book / Position Book | https://www.oanda.com/bvi-en/cfds/tools/orderbook/ | Retail order/position attention proxy | legal/API/historical capture not established |
| SRC-G5-NEWS-CALENDAR-LOCAL-001 | Local GTOS news calendar and refresh script | `src/components/news_calendar.py`, `scripts/refresh_economic_calendar.py`, `config/agent_config.yaml` | Scheduled event label/freshness cohort | operator-maintained, stale-source risk |
| SRC-G5-AI-SHADOW-LOCAL-001 | Local dumb baseline and AI shadow readiness artifacts | `research/dumb_momentum_baseline/REPORT.md`, `research/program_control/AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.md` | AI/mechanical paired decision experiment | insufficient paired forward rows |
| SRC-G5-PROMPT-NEUTRAL-001 | Prompt-neutral rerun backlog item | `.context/backlog_synthesis_2026-04-18/00_MASTER_BACKLOG.md` | AI framing/narrative anchoring test | paid API budget not approved; live prompt untouched |

Promotion verdict: NO_PROMOTION_VERDICT
