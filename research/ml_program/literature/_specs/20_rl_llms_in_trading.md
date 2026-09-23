# Domain 20 — RL & LLMs in Trading

**Slug:** `20_rl_llms_in_trading`
**Owner:** Phase 1 Worker Agent #20
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns research on **agentic** systems for trading: RL for portfolio / single-asset / execution, deep-RL specifically (DQN, PPO, SAC, A3C variants in finance), multi-agent RL for market simulation, LLM-as-trader prompts and agentic frameworks (BloombergGPT, FinGPT, FinMem, FinAgent, multi-agent LLM debate trading), LLM forecasting head-to-head with classical, prompt engineering for financial reasoning, retrieval-augmented LLMs over financial corpora, hallucination diagnostics in financial LLMs, fine-tuning for trading, RLHF in finance.

**IN scope:** Deng et al deep direct RL for trading, Schulman PPO applied to portfolio, Sutton-Barto RL foundations (one foundational reference), Mnih DQN, BloombergGPT, FinGPT, recent multi-agent LLM trading papers, LLM forecasting benchmarks (ForecastBench-finance), hallucination quantification, prompt-engineering for financial reasoning, GPT/Claude/Gemini-as-analyst studies.

**OUT of scope:** **Pure ML feature-engineering** for prediction → 19; **execution-only RL agents** that minimize impact (Almgren-style optimization) → 06 (we keep RL-as-trader, 06 keeps RL-for-VWAP); **non-financial RL theory** → drop; **financial LLM as data-extraction tool** for ML features → 19.

---

## 2. Search strategy

### Keywords
- "deep reinforcement learning" trading portfolio
- "DQN" stock trading agent
- "PPO" portfolio
- "SAC" continuous action trading
- "deep direct reinforcement learning" Deng financial
- "multi agent reinforcement learning" market simulation
- "FinRL" library benchmark
- "FinGPT" open source LLM
- "BloombergGPT" finance
- "FinMem" memory agent finance
- "FinAgent" multi agent trading
- "LLM" financial forecasting
- "GPT-4" stock prediction
- "Claude" trading agent
- "RLHF" finance fine tuning
- "prompt engineering" financial reasoning
- "tool use" LLM trading
- "retrieval augmented" finance
- "hallucination" LLM financial decision

### Key journals
- *IEEE Transactions on Neural Networks and Learning Systems*
- *Journal of Machine Learning Research*
- *Quantitative Finance*
- *Journal of Empirical Finance*
- *Journal of Banking and Finance*
- *Information Sciences*
- *Expert Systems with Applications*
- *Decision Support Systems*

### Repositories
- arXiv `q-fin.TR`, `cs.LG`, `cs.AI`, `cs.CL`
- AI4Finance Foundation github (FinGPT, FinRL)
- Anthropic, OpenAI research blogs
- SSRN AI in Finance
- ICLR / NeurIPS / ICML proceedings (finance tracks)

### Key authors
- Yue Deng et al (deep direct RL trading)
- Volodymyr Mnih (DQN)
- Richard Sutton, Andrew Barto (foundational)
- John Schulman (PPO)
- Shihao Gu, Bryan Kelly (overlap with 19)
- Xiao-Yang Liu (AI4Finance, FinGPT)
- Dogu Araci (FinBERT)
- BloombergGPT team
- Andrew Lo (recent LLM-finance pieces)
- Various OpenAI / Anthropic / Google researchers

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Reinforcement Learning: An Introduction (book, 2nd ed) | Sutton, Barto | 2018 | http://incompleteideas.net/book/the-book-2nd.html |
| 2 | Human-level Control through Deep Reinforcement Learning (DQN) | Mnih et al | 2015 | https://www.nature.com/articles/nature14236 |
| 3 | Proximal Policy Optimization Algorithms | Schulman et al | 2017 | https://arxiv.org/abs/1707.06347 |
| 4 | Deep Direct Reinforcement Learning for Financial Signal Representation and Trading | Deng et al | 2017 | https://ieeexplore.ieee.org/document/7407387/ |
| 5 | Attention Is All You Need (transformer) | Vaswani et al | 2017 | https://arxiv.org/abs/1706.03762 |
| 6 | BloombergGPT: A Large Language Model for Finance | Wu et al | 2023 | https://arxiv.org/abs/2303.17564 |
| 7 | FinGPT: Open-Source Financial Large Language Models | Yang et al | 2023 | https://arxiv.org/abs/2306.06031 |
| 8 | FinBERT: Financial Sentiment Analysis with Pre-trained Language Models | Araci | 2019 | https://arxiv.org/abs/1908.10063 |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | FinRL benchmark library | Liu et al | 2020-22 | search arXiv FinRL |
| 10 | Deep Hedging | Buehler et al | 2019 | search Quantitative Finance |
| 11 | Multi-agent reinforcement learning market simulator | various | 2021-24 | search arXiv |
| 12 | LLM agentic trading FinAgent / FinMem | various | 2024-25 | search arXiv |
| 13 | LLM-driven Stock Prediction | LLaMA-based | 2025 | https://www.researchgate.net/publication/394275138 |
| 14 | Comparative Analysis LLM-Based Market Prediction | various | 2024 | https://easychair.org/publications/preprint/mr3d/open |
| 15 | LLM equity markets review | Frontiers AI | 2025 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12421730/ |
| 16 | Financial sentiment analysis using FinBERT — application predicting stock movement | various | 2023 | https://arxiv.org/html/2306.02136v2 |
| 17 | Hallucination in financial LLMs | various | 2023-25 | search arXiv |
| 18 | RLHF for financial decision making | various | 2024-25 | search arXiv |

---

## 5. GTOS subsystem connections

- **GTOS Component 3A is an LLM-based MSO gate** (Sonnet 4.6, effort=max). Domain 20 is the LITERATURE ANCHOR for the entire AI architecture choice.
- **Sonnet vs Opus on MSO gate** (memory `project_opus_vs_sonnet_p2c`) — academic literature on model-size vs task-fit / chain-of-thought may inform.
- **HALLUC-1 NAS100 precision-bug class** (`project_halluc_1_precision_bug_class_2026-04-27`) — Domain literature on financial-LLM hallucination quantification + grounding.
- **A4 trending_bull replay finding** — AI did not change selectivity post-fix; literature on prompt-cascade revisions / regression-after-fix.
- **K55 ML-vs-AI shadow harness** (depends on K54 production deployment, item #7 follow-up) — literature on classical-ML vs LLM head-to-head in finance.
- **Component 3B Bull/Bear/Judge debate** (research-door-wired, default OFF, item #10) — multi-agent LLM debate literature directly applicable.
- **Tool use grounding** (`src/components/ai_tools/`, NOT yet wired into PrimaryAnalyzer — see DESIGN.md) — RAG / tool-use LLM literature.
- **Cascade prompt LOST-IRRECOVERABLE (V3 best, item #8)** — research on prompt versioning and recovery practices.

---

## 6. Cross-domain handoff rules

- **Pure ML / feature engineering** → 19.
- **Execution-only RL** (Almgren-Chriss-style minimum-impact) → 06.
- **LLM as data-extraction for sentiment factor** → 17 (we keep agentic-LLM-as-trader; 17 keeps sentiment-as-feature).
- **Theoretical RL / PPO / SAC** without finance application → drop.
- **AI safety / alignment in trading agents** — keep here.

---

## 7. Output spec

Files:
- `research/ml_program/literature/20_rl_llms_in_trading/papers.md`
- `research/ml_program/literature/20_rl_llms_in_trading/papers.csv`

Same schema. Special fields:
- `system_type` (RL / LLM-prompted / LLM-fine-tuned / multi-agent / hybrid)
- `data_modality` (price-only / news / multimodal)
- `evaluation_period` (in-sample / out-of-sample / live).

---

## 8. Quality bar / target

35-50 papers. Worker must split: ~10 RL trading foundational + recent (DQN/PPO/SAC), ~10 LLM-as-trader / agentic finance (very fast-moving 2023-2025), ~7 LLM benchmarks for forecasting, ~5 hallucination / grounding diagnostics, ~5 multi-agent debate, ~3 alignment / safety. Aim for 15+ post-2023 (the LLM-agent literature is brand-new and central to GTOS).
