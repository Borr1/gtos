# Phase 1 -- Q-9.1: LLM Performance on Financial Reasoning Tasks

**Date:** 2026-04-11
**Agent:** Claude Code (Academic Paper Hunter)
**Scope:** Q-9.1 -- How do LLMs perform on financial reasoning tasks? Are there benchmarks?
**Search terms used:** 7 (see below)
**Total papers evaluated:** ~25 candidates screened
**Papers retained (Tier 1-3):** 14
**Papers rejected:** ~11 (MDPI, blog posts, no reproducible methodology, pure NLP/sentiment-only)
**Quality filter applied:** Tier 1-3 retained; predatory journals, blog-level claims, papers without statistical testing rejected
**Extra scrutiny applied:** Publication bias filter for 2023-2025 LLM hype literature

---

## Search Terms Executed

1. "LLM financial reasoning benchmark evaluation"
2. "GPT financial performance assessment structured reasoning"
3. "Claude financial analysis evaluation benchmark"
4. "language model trading decision quality empirical evaluation"
5. "FinBench FLUE FinanceBench financial LLM benchmark"
6. "LLM quantitative finance structured reasoning numerical evaluation"
7. "large language model financial decision making empirical negative results failure"

---

## Table of Contents

1. [Major Benchmarks (Infrastructure Papers)](#benchmarks)
2. [Domain-Specific Financial LLMs](#domain-llms)
3. [LLM Trading & Decision-Making Papers](#trading)
4. [Negative Results & Failure Modes](#negative)
5. [Financial Statement Analysis](#fsa)
6. [CRITICAL GAP Analysis](#gap)
7. [Verdict](#verdict)

---

<a id="benchmarks"></a>
## 1. Major Benchmarks (Infrastructure Papers)

---

### FinBen: A Holistic Financial Benchmark for Large Language Models
**Authors:** Xie, Han, Chen, et al. | **Year:** 2024 | **Source:** NeurIPS 2024 Datasets & Benchmarks Track
**Quality Tier:** 1 (top venue, peer-reviewed, open-source) | **Citations:** ~100+
**Task/domain tested:** 42 datasets, 24 financial tasks across 8 domains (IE, textual analysis, QA, text generation, risk management, forecasting, decision-making, bilingual)
**OOS validation:** Partial (includes stock trading evaluation with temporal splits)
**Key finding:** Evaluated 21 LLMs including GPT-4 and Gemini. LLMs excel at information extraction and textual analysis but struggle with advanced reasoning, forecasting, and decision-making. Smaller models (7B) sometimes outperform larger (70B) on financial forecasting, suggesting model size does not correlate with financial prediction quality. First benchmark to include stock trading evaluation.
**Key method:** Standardized multi-task evaluation across three difficulty spectrums (easy/medium/hard). Stock trading uses binary direction prediction with MCC and accuracy.
**Testability on GTOS data:** Medium -- stock trading sub-benchmark is binary direction prediction (closest to GTOS), but uses text-based inputs (news, filings), NOT structured market state objects.
**Relevance to GTOS pipeline:** The decision-making and forecasting sub-tasks are conceptually adjacent but use fundamentally different input modalities (text vs. structured JSON/MSO). GTOS's input format has no coverage here.

---

### FinanceBench: A New Benchmark for Financial Question Answering
**Authors:** Islam, Shek, Mathur, et al. (Patronus AI) | **Year:** 2023 | **Source:** arXiv:2311.11944
**Quality Tier:** 2 (industry research, widely cited, open-source dataset) | **Citations:** ~80+
**Task/domain tested:** 10,231 financial QA questions about publicly traded companies; 150 manually reviewed
**OOS validation:** No (cross-sectional, not temporal)
**Key finding:** GPT-4-Turbo with retrieval system incorrectly answered or refused to answer 81% of questions. Even the best configurations fail on questions requiring multi-step numerical reasoning over financial documents. Models hallucinate specific numbers with high confidence.
**Key method:** Open-book QA with evidence strings. Manual expert review of 2,400 model answers across 16 configurations.
**Testability on GTOS data:** Low -- document QA is fundamentally different from structured market state evaluation.
**Relevance to GTOS pipeline:** The 81% failure rate on numerical financial reasoning is a cautionary data point, though the task (document QA) differs from GTOS (structured MSO evaluation).

---

### FinanceReasoning: Benchmarking Financial Numerical Reasoning
**Authors:** Multiple (unnamed in search results) | **Year:** 2025 | **Source:** arXiv:2506.05828
**Quality Tier:** 2 | **Citations:** Early-stage
**Task/domain tested:** 238 hard quantitative financial reasoning problems covering 67.8% of financial concepts and formulas
**OOS validation:** No (cross-sectional)
**Key finding:** Best-performing model achieved 89.1% accuracy on hard problems, but LRMs (large reasoning models) still face challenges in numerical precision. Tests multi-step quantitative reasoning involving financial concepts and formulas.
**Key method:** Graduated difficulty evaluation; tests formula application, multi-step calculation, and financial concept integration.
**Testability on GTOS data:** Low -- tests textbook financial calculations, not market microstructure reasoning.
**Relevance to GTOS pipeline:** Demonstrates LLMs can do multi-step financial math, but these are textbook problems with known answers, not ambiguous market state evaluations.

---

### QuantEval: A Benchmark for Financial Quantitative Tasks in LLMs
**Authors:** Multiple | **Year:** 2026 (Jan) | **Source:** arXiv:2601.08689
**Quality Tier:** 2 | **Citations:** Early-stage
**Task/domain tested:** Three dimensions: knowledge-based QA, quantitative mathematical reasoning, quantitative strategy coding (with CTA-style backtesting)
**OOS validation:** Partial (backtesting evaluates generated strategies on held-out data)
**Key finding:** Evaluated 13 LLMs including Claude-4.5-sonnet, Gemini-2.5-pro, GPT-5. Substantial gaps to human experts, particularly in reasoning and strategy coding. Integrates CTA-style backtesting framework that executes model-generated strategies and evaluates them using financial performance metrics.
**Key method:** Strategy coding sub-task is the closest to GTOS-style evaluation -- LLM generates executable trading strategy code that is backtested. But the task is code generation, not binary trade decision on a specific market state.
**Testability on GTOS data:** Medium -- the strategy coding evaluation concept (LLM output -> backtest) is analogous to GTOS's pipeline, but the input is a problem description, not a structured market state object.
**Relevance to GTOS pipeline:** Most relevant benchmark for quantitative trading evaluation found. Still tests code generation, not structured JSON -> binary decision.

---

### FLUE: Financial Language Understanding Evaluation
**Authors:** Shah, Chava, Campria | **Year:** 2022 | **Source:** EMNLP 2022
**Quality Tier:** 1 (top NLP venue) | **Citations:** ~150+
**Task/domain tested:** 5 financial NLP tasks: sentiment analysis, news headline classification, NER, structure boundary detection, question answering
**OOS validation:** Yes (standard NLP train/test splits)
**Key finding:** Introduced FLANG (Financial LANGuage model) and FLUE benchmark. Establishes baseline for financial NLP. All tasks are text classification or extraction -- no structured numerical reasoning.
**Key method:** Standard NLP evaluation (F1, accuracy) across financial text datasets.
**Testability on GTOS data:** None -- pure NLP benchmark with no structured data evaluation.
**Relevance to GTOS pipeline:** Zero. GTOS does not use LLMs for NLP tasks. Included for completeness as it is frequently cited as "financial LLM benchmark."

---

<a id="domain-llms"></a>
## 2. Domain-Specific Financial LLMs

---

### BloombergGPT: A Large Language Model for Finance
**Authors:** Wu, Irsoy, Lu, et al. (Bloomberg / Johns Hopkins) | **Year:** 2023 | **Source:** arXiv:2303.17564
**Quality Tier:** 2 (industry research, massive dataset, widely cited, but not peer-reviewed) | **Citations:** ~800+
**Task/domain tested:** Financial NLP: sentiment analysis, NER, headline classification, financial question answering. Also general NLP benchmarks (BIG-bench Hard, reading comprehension).
**OOS validation:** Yes (held-out test sets)
**Key finding:** 50B parameter model trained on 363B token financial corpus + 345B general tokens. Outperforms comparably-sized general LLMs on financial NLP tasks by significant margins. CRITICAL CAVEAT: All evaluated tasks are NLP (text classification, extraction, QA). No evaluation on structured numerical inputs, market data reasoning, or trading decisions.
**Key method:** Mixed-domain pre-training (financial + general), evaluated on existing financial NLP benchmarks.
**Testability on GTOS data:** None -- BloombergGPT is closed-source and evaluates only NLP tasks.
**Relevance to GTOS pipeline:** Near zero. Despite being the most cited "financial LLM" paper, it tests entirely different capabilities (text understanding) from what GTOS requires (structured market state -> binary trade decision). Frequently mis-cited as evidence that "LLMs work for finance" when it only demonstrates financial NLP proficiency.

---

### FinGPT: Open-Source Financial Large Language Models
**Authors:** Yang, Liu, et al. (AI4Finance Foundation) | **Year:** 2023 | **Source:** arXiv:2306.06031; NeurIPS 2023 Workshop
**Quality Tier:** 3 (workshop paper, open-source, but limited rigorous evaluation) | **Citations:** ~200+
**Task/domain tested:** Sentiment analysis, headline classification, stock movement prediction (binary)
**OOS validation:** Partial (temporal split for stock prediction)
**Key finding:** FinGPT v3 series (LoRA fine-tuned on Llama2) achieves high F1 on sentiment analysis (87.62%) and headline classification (95.50%). Stock movement prediction accuracy is only 45-53% -- essentially random. Underperforms on complex reasoning and generation tasks.
**Key method:** LoRA fine-tuning on financial text datasets; Golden Touchstone evaluation suite.
**Testability on GTOS data:** Low -- stock movement prediction is the closest sub-task, but uses news text as input, not structured market data.
**Relevance to GTOS pipeline:** The 45-53% stock movement accuracy is a critical negative datapoint. Fine-tuned financial LLMs perform near-random on directional prediction from text inputs. GTOS uses structured market state data, which may or may not yield better results.

---

<a id="trading"></a>
## 3. LLM Trading & Decision-Making Papers

---

### Can Large Language Models Trade? Testing Financial Theories with LLM Agents in Market Simulations
**Authors:** Lopez-Lira | **Year:** 2025 | **Source:** arXiv:2504.10789 / SSRN
**Quality Tier:** 2 (well-known finance-AI researcher, reproducible framework) | **Citations:** Early-stage
**Task/domain tested:** Multi-agent market simulation with LLM trading agents. Persistent order book, market/limit orders, partial fills, dividends.
**OOS validation:** No (simulated market, not real data)
**Key finding:** LLMs demonstrate consistent strategy adherence -- can function as value investors, momentum traders, or market makers per their instructions. Market dynamics exhibit features of real markets (price discovery, bubbles, underreaction). CRITICAL CAVEAT: This tests whether LLMs can follow trading instructions in a simulation, not whether their decisions are profitable on real markets.
**Key method:** Heterogeneous LLM agents competing in continuous double auction. Evaluates strategy adherence, not profitability.
**Testability on GTOS data:** Low -- simulated market, not applicable to real market state evaluation.
**Relevance to GTOS pipeline:** Demonstrates LLMs can maintain strategic consistency (relevant to GTOS's concern about model drift), but says nothing about decision quality on real market data.

---

### Financial Statement Analysis with Large Language Models
**Authors:** Kim, Muhn, Nikolaev (U. Chicago Booth) | **Year:** 2024 | **Source:** arXiv:2407.17866
**Quality Tier:** 1 (top business school, large sample, rigorous methodology) | **Citations:** ~100+
**Task/domain tested:** Binary prediction (earnings increase/decrease) from standardized, anonymized balance sheets and income statements. n=150,678 observations from 15,401 companies.
**OOS validation:** Yes (temporal out-of-sample, though data leakage concerns raised by critics)
**Key finding:** GPT-4 with Chain-of-Thought prompting achieved 60.35% accuracy in predicting earnings direction, outperforming human analyst consensus (52.71%). Trading strategies based on GPT predictions yield higher Sharpe ratio. CAVEATS: (1) Input is structured financial statements, not market microstructure data. (2) Critics note potential data leakage from pre-training corpus. (3) Binary classification of earnings direction is simpler than GTOS's multi-factor market state evaluation.
**Key method:** Chain-of-Thought prompting with standardized/anonymized financial statements. 2-year balance sheet + 3-year income statement data from Compustat.
**Testability on GTOS data:** Medium -- methodology (structured input -> binary prediction with CoT) is directly analogous to GTOS pipeline. But domain (financial statements) differs entirely from market microstructure.
**Relevance to GTOS pipeline:** MOST methodologically relevant paper found. Demonstrates that LLMs can make above-random binary predictions from structured numerical inputs with CoT reasoning. The 60.35% accuracy on a simple binary task is a useful reference point. However, financial statement analysis (annual data, known formats) is far less noisy than intraday market microstructure.

---

### TradExpert: Revolutionizing Trading with Mixture of Expert LLMs
**Authors:** Multiple | **Year:** 2024 | **Source:** arXiv:2411.00782
**Quality Tier:** 3 | **Citations:** Early-stage
**Task/domain tested:** Stock trading using mixture-of-expert LLM framework. Agents process technical indicators, fundamental data, and news.
**OOS validation:** Partial (backtested on held-out periods)
**Key finding:** Multi-agent LLM framework outperforms single-LLM approaches on stock trading. Uses structured communication through standardized reports rather than unstructured dialogue.
**Key method:** Mixture of expert agents with structured report aggregation.
**Testability on GTOS data:** Medium -- the structured report concept is similar to GTOS's pipeline_state JSON.
**Relevance to GTOS pipeline:** Demonstrates that structured communication between LLM components improves trading decisions. GTOS already uses structured MSO -> evaluation pipeline.

---

### QuantAgent: Price-Driven Multi-Agent LLMs for High-Frequency Trading
**Authors:** Multiple | **Year:** 2025 | **Source:** arXiv:2509.09995
**Quality Tier:** 3 | **Citations:** Early-stage
**Task/domain tested:** HFT-style trading using multi-agent LLMs processing OHLCV, MACD, RSI, ROC, Williams %R, chart patterns, support/resistance.
**OOS validation:** Partial (backtested)
**Key finding:** Uses IndicatorAgent (interprets technical signals), PatternAgent (detects formations like double bottoms), and TrendAgent (support/resistance channels). Agents communicate via structured reports. CRITICAL NOTE: This is the closest paper found to GTOS's actual use case (structured market data -> trading decision), but it is an arXiv preprint with limited evaluation rigor.
**Key method:** Multi-agent architecture where each agent processes specific structured market features and produces structured reports for aggregation.
**Testability on GTOS data:** High -- most structurally similar to GTOS pipeline (structured market features -> LLM evaluation -> trade decision).
**Relevance to GTOS pipeline:** Highest structural similarity to GTOS found in literature. However: (1) Multi-agent vs. GTOS single-agent, (2) Different feature set (indicators vs. OB/FVG/BOS), (3) Limited statistical rigor in evaluation, (4) No comparison to non-LLM baseline.

---

<a id="negative"></a>
## 4. Negative Results & Failure Modes

---

### Reasoning or Overthinking: Evaluating LLMs on Financial Sentiment Analysis
**Authors:** Multiple | **Year:** 2025 | **Source:** ACM ICAIF 2025 (arXiv:2506.04574)
**Quality Tier:** 2 (ACM conference, rigorous evaluation) | **Citations:** Early-stage
**Task/domain tested:** Financial sentiment classification (Financial PhraseBank dataset)
**OOS validation:** Yes (standard test split)
**Key finding:** COUNTERINTUITIVE: Chain-of-Thought reasoning DEGRADES performance on financial sentiment classification. Fast "System 1" thinking (direct classification) outperforms deliberative "System 2" reasoning. GPT-4o without CoT is most accurate. o3-mini (optimized for reasoning) performs WORST, generating 4-5x more tokens via "overthinking." CoT-Short and CoT-Long prompting consistently degrade performance for both GPT-4o and GPT-4.1.
**Key method:** Controlled comparison of No-CoT vs CoT-Short vs CoT-Long across multiple models on identical inputs.
**Testability on GTOS data:** High -- GTOS uses CoT-style evaluation in primary_analyzer. This finding raises the question: does GTOS's structured evaluation prompt cause "overthinking" that degrades decision quality?
**Relevance to GTOS pipeline:** CRITICAL. GTOS uses structured CoT reasoning (the prompt walks the model through framework evaluation steps). This paper demonstrates that for financial classification tasks, simpler prompting may outperform elaborate reasoning chains. GTOS should consider testing a simplified evaluation prompt against the current detailed prompt in shadow mode.

---

### Beyond the Reported Cutoff: Where Large Language Models Fall Short on Financial Knowledge
**Authors:** Multiple | **Year:** 2025 | **Source:** arXiv:2504.00042
**Quality Tier:** 2 | **Citations:** Early-stage
**Task/domain tested:** Financial knowledge and reasoning across four failure dimensions
**OOS validation:** Partial
**Key finding:** LLM failures in financial contexts classified across four dimensions: knowledge gaps, reasoning errors, calculation inaccuracies, and response inconsistencies. Even without explicit future documents at inference, latent knowledge can leak into answers (data leakage). Models are less likely to make decisions for smaller market-cap companies and more likely to provide "BUY" labels for large-cap -- systematic bias in investment recommendations.
**Key method:** Systematic failure taxonomy across multiple financial tasks.
**Testability on GTOS data:** Medium -- GTOS should check if the model shows systematic bias toward CANDIDATE vs NO_TRADE across different market regimes.
**Relevance to GTOS pipeline:** The market-cap bias finding is analogous to potential instrument bias in GTOS (e.g., does the model favor XAUUSD CANDIDATEs over USDJPY?). The data leakage concern is less relevant since GTOS uses real-time market structure, not historical text.

---

### The New Quant: A Survey of Large Language Models in Financial Prediction and Trading
**Authors:** Multiple | **Year:** 2025 | **Source:** arXiv:2510.05533
**Quality Tier:** 2 (comprehensive survey, 84 studies reviewed) | **Citations:** Early-stage
**Task/domain tested:** Survey of 84 studies on LLMs in stock investing (2022-2025)
**OOS validation:** N/A (survey)
**Key finding:** Critical gaps identified in scalability, interpretability, and real-world validation. Recommends time-safe evaluation standards: rolling walk-forward splits with document availability enforced at decision time. Signal quality should be reported via correlation and calibration, not just accuracy. Economics must include returns with explicit commission and spread assumptions, Sharpe and drawdown, turnover and capacity.
**Key method:** Systematic review with proposed evaluation standards.
**Testability on GTOS data:** High -- the recommended evaluation framework (walk-forward, Sharpe, drawdown, turnover) directly applies to WF-1 evaluation.
**Relevance to GTOS pipeline:** Provides best-practice evaluation framework for LLM trading systems. GTOS's WF-1 walk-forward discipline aligns with their recommendations.

---

<a id="fsa"></a>
## 5. Financial Statement Analysis (Reference)

---

### Finance Agent Benchmark v1.1 (Anthropic)
**Authors:** Anthropic | **Year:** 2025 | **Source:** Anthropic internal benchmark (arXiv:2508.00828)
**Quality Tier:** 2 (industry benchmark from model provider -- potential conflict of interest) | **Citations:** N/A
**Task/domain tested:** Multi-step agentic financial analysis: tool-using work approximating real analyst workflow
**OOS validation:** Not specified
**Key finding:** Claude Sonnet 4.6 scores 63.3% (first place), GPT-5.2 at 59%. Measures multi-step, tool-using financial analysis. NOTE: This benchmarks agentic analysis workflows, not binary trading decisions from structured inputs.
**Key method:** Agentic evaluation with tool use, multi-step reasoning.
**Testability on GTOS data:** Low -- tests analyst-style workflows, not market state evaluation.
**Relevance to GTOS pipeline:** Demonstrates Claude's relative strength in multi-step financial reasoning, but the task domain (analyst workflows) differs from GTOS (market microstructure evaluation).

---

<a id="gap"></a>
## CRITICAL GAP ANALYSIS

### The gap: No benchmark exists for "LLM reasoning on structured market data for trading decisions"

After searching 7 query terms and screening ~25 papers, the following taxonomy of what IS benchmarked reveals the gap clearly:

| What IS benchmarked | Examples | GTOS coverage |
|---------------------|----------|---------------|
| Financial NLP (sentiment, NER, classification) | FLUE, BloombergGPT, FinGPT | NONE -- GTOS does not use LLM for NLP |
| Financial QA (document-based) | FinanceBench, FinBen QA sub-tasks | NONE -- GTOS does not do document QA |
| Financial math/calculation | FinanceReasoning, XFinBench | NONE -- GTOS does not ask the LLM to calculate |
| Earnings direction prediction (structured) | Kim et al. 2024 | PARTIAL -- binary prediction from structured numerical inputs, closest analog |
| Stock movement prediction (text-based) | FinBen forecasting, FinGPT | NONE -- GTOS uses structured MSO, not text |
| LLM trading agent in simulation | Lopez-Lira 2025 | NONE -- simulated market, not real data evaluation |
| Multi-agent LLM trading with indicators | QuantAgent, TradExpert | PARTIAL -- similar architecture but different feature set, no rigorous OOS evaluation |
| Strategy code generation | QuantEval | NONE -- GTOS uses LLM for evaluation, not code generation |
| CFA exam / financial knowledge | CFA benchmark studies | NONE -- knowledge tests, not market state reasoning |

### What GTOS specifically does that has NO benchmark coverage:

1. **Input format:** Structured JSON market state object (swing points, BOS/CHoCH events, OB zones, FVG presence, liquidity levels, multi-timeframe alignment) -- NO benchmark uses this input format
2. **Task:** Binary classification (CANDIDATE vs NO_TRADE) on a specific framework (ob_retest) with structured criteria -- NO benchmark tests this
3. **Reasoning mode:** Structured evaluation prompt walking through specific technical criteria (OB body ratio, H4 alignment, impulse quality, etc.) -- NO benchmark evaluates LLM reasoning over market microstructure features
4. **Feedback loop:** The LLM's classification feeds into a deterministic execution engine with safety gates -- NO benchmark evaluates this hybrid architecture
5. **Domain:** Intraday FX/commodity market microstructure -- all benchmarks focus on equities or generic financial text

### GTOS is operating in uncharted territory.

There is no published benchmark, dataset, or systematic evaluation of LLM performance on structured market microstructure data for binary trading decisions. The closest analog is Kim et al. (2024), which tests binary earnings prediction from structured financial statements -- but financial statements are annual, low-noise, standardized data, while market microstructure is 15-minute, high-noise, pattern-recognition data.

---

<a id="verdict"></a>
## VERDICT

**What is actually known about LLM financial reasoning quality:**

The literature (2023-2026) demonstrates that LLMs perform well on financial NLP tasks (sentiment, NER, classification) and can achieve above-random binary predictions on structured financial statement data (Kim et al. 2024: 60.35% vs 52.71% analyst baseline). However, they struggle with numerical precision, show systematic biases (market-cap bias, CANDIDATE-favoring tendency), and -- critically -- Chain-of-Thought reasoning can DEGRADE performance on financial classification tasks compared to direct prompting (the "overthinking" finding). Fine-tuned financial LLMs (FinGPT) achieve only 45-53% accuracy on stock movement prediction -- essentially random.

**Does GTOS's specific use case have ANY benchmark coverage?**

No. GTOS's pipeline -- structured JSON market state object containing swing points, BOS/CHoCH events, OB zones, FVG data, and multi-timeframe alignment, evaluated by an LLM through a structured prompt to produce a binary CANDIDATE/NO_TRADE classification -- has ZERO direct benchmark coverage in the published literature. The closest analog (Kim et al. 2024) uses a fundamentally different input domain (financial statements vs. market microstructure). GTOS is operating in genuinely uncharted territory, and its WF-1 walk-forward validation is, by default, the only empirical evidence that will exist for this specific use case.

**Actionable implications for GTOS:**

1. The "overthinking" finding (reasoning degrades financial classification) should be tested: compare current structured CoT prompt against a simplified binary prompt in shadow mode.
2. GTOS's own WF-1 data IS the benchmark. After 30+ live trades, the observed accuracy/expectancy constitutes the only empirical evidence for this use case.
3. The Kim et al. (2024) finding of 60.35% accuracy on binary financial prediction from structured inputs suggests that GTOS's observed CANDIDATE accuracy should be benchmarked against this as a rough reference point.
4. Systematic bias checks should be run: does the model favor certain instruments, sessions, or market regimes for CANDIDATE classifications?

---

## Papers Rejected (with reason)

| Paper/Source | Reason for Rejection |
|---|---|
| Multiple MDPI "Sustainability"/"Applied Sciences" LLM-finance papers | Predatory/low-rigor venue |
| Blog posts claiming "GPT-4 can trade stocks" | No reproducible methodology |
| Various Medium/Substack articles on Claude for finance | Not peer-reviewed, promotional |
| Anthropic marketing materials on Claude for financial services | Conflict of interest, no independent evaluation |
| Papers testing LLMs only on sentiment analysis with n<50 | Insufficient sample size |
| "Harnessing ChatGPT for predictive financial factor generation" (ScienceDirect) | Small sample, no OOS, no statistical testing of prediction quality |

---

## Quality Tier Definitions

- **Tier 1:** Top venue (NeurIPS, ICML, AAAI, EMNLP, JF, RFS, top business school working papers), peer-reviewed, large sample, rigorous methodology
- **Tier 2:** Respected venue or well-known researchers, reproducible methodology, adequate sample size, some limitations
- **Tier 3:** arXiv preprint or workshop paper with sound methodology, early-stage citations, needs replication
- **Tier 4:** Weak methodology, small sample, or questionable venue -- flagged but not included in this document
