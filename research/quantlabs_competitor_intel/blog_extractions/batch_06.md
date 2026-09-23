# TOP FINDINGS (batch 06)

Top 5 articles with the most GTOS-relevant novel content:

1. **[16] Building Profitable AI-Generated Trading Strategies with Python, Rithmic and LLMs** — Full News→Prompt→LLM→Validate→Deploy pipeline (~60 min) with multi-model benchmarks (Claude 4.6 vs Codex 5.3 vs GLM-5), cost tables ($50–$1,350/mo), prompt template structure, and explicit drawdown-to-profit ratio gate (<1.0x). Concrete signature to consider mirroring.
2. **[2] Ultra-Low-Latency Avellaneda-Stoikov Market Making** — Full A-S formula discussion (γ, κ, σ), OFI blending with microprice, inventory-aggressive-unwind at 80% of max, quote-staleness invalidation (100µs-1ms). Mostly HFT, but the reservation-price / inventory-skew pattern is transferable.
3. **[1] Complete Guide to Python Trading Bots with IBKR API (Claude 3.5 Sonnet)** — Has a verbatim Claude trading-signal prompt ("Analyze the following market context... BUY/SELL/HOLD... confidence 0-100") — a direct competitor prompt for comparison against T7 C-gate.
4. **[22] Launching a Professional-Grade Futures Platform with Rithmic** — Blue-green deploy, 30-min "shadow mode" before live with $10K cap; four strategy types described (OB imbalance mean-reversion, lead-lag, vol regime, stat arb). Shadow-before-live matches our pattern, useful confirmation.
5. **[15] Advanced Cross-Asset Futures Strategies (2026 Macro Crisis)** — Explicit position-sizing cap 2%, margin 50% excess, correlation-breakdown warning during crises. Aligns with GTOS risk stance; worth citing in risk doc.

---

### [1] Complete Guide to Building Python Trading Bots with Interactive Brokers API in 2025
- **URL:** https://www.quantlabsnet.com/post/complete-guide-to-building-python-trading-bots-with-interactive-brokers-api-in-2025-step-by-step-ar
- **Date:** 2026-04-08
- **Tag:** PRIORITY
- **Relevance verdict:** HIGH
- **Core thesis:** Democratized broker APIs (IBKR) plus AI (Claude) enable retail traders to build professional-grade automated systems. Fleet-architecture with centralized risk, isolated bot failure.
- **Tools/tech:** Libraries: ibapi, pandas, numpy, scipy, ta-lib, requests, python-dotenv, anthropic. AI model: `claude-3-5-sonnet-20241022`. Storage: SQLite/PostgreSQL shared DB.
- **Numbers / claims:** Min capital $2,000 day / $500 swing; risk per trade 2%; max DD threshold 15%; paper-trade 4 weeks minimum before live; "70% of retail traders lose money"; IBKR API port 7497.
- **Prompt snippets:** Verbatim: "Analyze the following market context and provide a trading signal... should we BUY, SELL, or HOLD? Provide reasoning and confidence level (0-100)."
- **Architecture details:** Fleet of strategy bots in parallel; centralized Risk Manager; central Logger/Monitor; one bot crash doesn't affect others (process isolation, mirror of GTOS per-symbol PID-locked).
- **Strategy details:** MA crossover (20/50), Iron Condor options (10/20 delta), futures market-making with 2-tick spreads.
- **Novel-to-GTOS:** MAYBE — Prompt is simpler than T7 C-gate; worth comparing their "confidence 0-100" output format to our CANDIDATE/NO_TRADE. The drawdown stop at 15% is looser than our 8% H29 threshold; ours is tighter (safer). Fleet-architecture with central Risk Manager is similar to our orchestrator+portfolio_risk pattern.

### [2] Ultra-Low-Latency HFT Market Making: Avellaneda-Stoikov Framework
- **URL:** https://www.quantlabsnet.com/post/ultra-low-latency-high-frequency-market-making-a-comprehensive-analysis-of-the-avellaneda-stoikov-f
- **Date:** 2026-01-03
- **Tag:** PRIORITY
- **Relevance verdict:** MEDIUM (HFT-focused; we're swing/intraday on MT5)
- **Core thesis:** Hybrid market-maker combining A-S optimal stochastic control with Order Flow Imbalance (OFI) signals; inventory-based reservation-price adjustment, dynamic inventory-aware skewing.
- **Tools/tech:** C++20, inline assembly, CPU TSC reads, lock-free SPSC queues, 64-byte cache-line alignment, CPU pinning. No external deps.
- **Numbers / claims:** Target Sharpe >3.0; latency <1µs; throughput >1M ticks/sec; WR >50%; profit factor >1.5; inventory ±100 contracts example; max DD 5%; quote staleness threshold 100µs-1ms; aggressive unwind at 80% of max inventory.
- **Prompt snippets:** none stated
- **Architecture details:** Multi-threaded with dedicated market-data, strategy, and order threads; tick→book update→volatility recalc→OFI update→fill detection→quote generation pipeline.
- **Strategy details:** Reservation price = mid ± (inventory × γ × σ²); optimal half-spread = (1/γ) × log(1 + γ/κ); microprice (volume-weighted mid) blended with OFI; both quotes skewed by inventory proximity to limits.
- **Novel-to-GTOS:** MAYBE — A-S math itself is not applicable (we don't market-make). BUT: (a) the 80% inventory threshold → aggressive unwind maps conceptually to our DD-based risk reduction; (b) quote-staleness invalidation is an interesting pattern for MSO snapshot validity (if M15 candle >N seconds old, skip AI eval); (c) γ (risk aversion) × σ² scaling is a dynamic-sizing pattern worth considering vs our fixed-2% model.

### [3] Best Broker for Futures and Options — EdgeClear vs Interactive Brokers
- **URL:** https://www.quantlabsnet.com/post/best-broker-for-futures-and-options-edgeclear-vs-interactive-brokers-with-an-examination-of-fcm-pa
- **Date:** 2025-10-08
- **Tag:** PRIORITY
- **Relevance verdict:** LOW (futures broker comparison; GTOS uses MT5/FTMO)
- **Core thesis:** Broker cost/latency comparison for retail futures.
- **Tools/tech:** EdgeClear supports Sierra Chart, TradingView, QuantConnect. IBKR Python/Java/C++ API.
- **Numbers / claims:** EdgeClear ES: as low as $0.35/side (5000 ES/month); IBKR ES: $0.85/side; market data ~$15/mo/exchange; IronBeam known for low-latency and flexible intraday margin.
- **Prompt snippets:** none stated
- **Architecture details:** None relevant.
- **Strategy details:** None.
- **Novel-to-GTOS:** NO — prop-firm MT5 model is fundamentally different cost structure (FTMO fees vs per-contract).

### [4] ChatGPT-5 vs Claude 4.1 Opus — Building a Quant Pricing Engine
- **URL:** https://www.quantlabsnet.com/post/chat-gpt-5-vs-claude-4-1-opus-building-a-quant-pricing-engine
- **Date:** 2025-08-07
- **Tag:** PRIORITY
- **Relevance verdict:** LOW
- **Core thesis:** Tie with specialization: GPT-5 better for targeted code/scaffolding (C++, dashboards); Claude 4.1 Opus better for long-context multi-file codebases. GPT-5 hallucinated metrics (volatility, backtest numbers).
- **Tools/tech:** C++ pricing engine → JSON → HTML/Chart.js dashboard; CLI utility; IB Gateway on Linux headless.
- **Numbers / claims:** none stated
- **Prompt snippets:** none stated (narrative only — RTY, ZC, CC instruments, 4-week guidance CLI)
- **Architecture details:** Engine writes JSON; dashboard is single-file index.html with Chart.js (P&L, vol, DD).
- **Strategy details:** None.
- **Novel-to-GTOS:** NO — confirms hallucination risk (we already know this, mitigated via T=0 + structured JSON + validation). No novel Claude integration patterns.

### [5] Mastering Micro Gold Futures & Options with ES and CL
- **URL:** https://www.quantlabsnet.com/post/mastering-micro-gold-futures-options-with-es-and-cl
- **Date:** 2025-04-15
- **Tag:** PRIORITY
- **Relevance verdict:** SKIP (paid webinar promo, no content)
- **Core thesis:** Webinar on MGC, ES, CL with ARIMA/Black-Scholes/Greeks/hedging.
- **Tools/tech:** none stated
- **Numbers / claims:** none stated
- **Prompt snippets:** none stated
- **Novel-to-GTOS:** NO.

### [6] Algo in the Corner Office — Goldman Sachs and the Rise of AI in Banking
- **URL:** https://www.quantlabsnet.com/post/algo-in-the-corner-office-goldman-sachs-and-the-rise-of-ai-in-banking
- **Date:** 2025-02-03
- **Tag:** PRIORITY
- **Relevance verdict:** SKIP (editorial, no specifics)
- **Core thesis:** Goldman building AI assistant that "feels like another GS employee".
- **Tools/tech:** none stated
- **Numbers / claims:** none stated
- **Novel-to-GTOS:** NO.

### [7] What is Forex Trading with Quant and Automation
- **URL:** https://www.quantlabsnet.com/post/what-is-forex-trading-with-quant-and-automation
- **Date:** 2024-06-07
- **Tag:** PRIORITY
- **Relevance verdict:** LOW (beginner overview)
- **Core thesis:** Python + quant + automation for forex; TradingView mentioned as new automation path.
- **Tools/tech:** Python; TradingView webhook; no specific MT5/MT4 detail.
- **Numbers / claims:** none stated
- **Novel-to-GTOS:** NO.

### [8] Long USDJPY as Bank of Japan Raises Rates
- **URL:** https://www.quantlabsnet.com/post/long-usdjpy-as-bank-of-japan-raises-rates
- **Date:** 2024-03-25
- **Tag:** PRIORITY
- **Relevance verdict:** LOW (directional macro call, no system content)
- **Core thesis:** Long USDJPY because BoJ rate hike + hedge fund short-yen positioning.
- **Numbers / claims:** none stated (no specific levels).
- **Novel-to-GTOS:** NO — we don't take macro directional views; T7 is structure-based.

### [9] Auto Forex Trading with TradingView, IBKR and Python
- **URL:** https://www.quantlabsnet.com/post/i-got-auto-forex-trading-working-with-tradingview-ibkr-and-python
- **Date:** 2023-11-07
- **Tag:** PRIORITY
- **Relevance verdict:** SKIP (promo announcement, no technical content accessible)
- **Core thesis:** Automation via TradingView → IBKR → Python.
- **Tools/tech:** none stated in accessible content.
- **Numbers / claims:** none stated.
- **Novel-to-GTOS:** NO.

### [10] Forex/CFD/Stock/ETF Analysis Moved to Substack
- **URL:** https://www.quantlabsnet.com/post/forex-cfd-or-stock-etf-analysis-moved-to-substack
- **Date:** 2023-08-31
- **Tag:** PRIORITY
- **Relevance verdict:** SKIP (migration notice)
- **Core thesis:** Content moved to quantlabs.substack.com.
- **Numbers / claims:** Claims AI-generated strategies "beat 70% of retail traders" (unsupported).
- **Novel-to-GTOS:** NO.

### [11] FOMC Minutes Unveil Potential Impact on EURUSD
- **URL:** https://www.quantlabsnet.com/post/fomc-minutes-unveil-potential-impact-on-eurusd-pair
- **Date:** 2023-07-05
- **Tag:** PRIORITY
- **Relevance verdict:** LOW (macro opinion piece)
- **Core thesis:** Short EURUSD on hawkish Fed.
- **Numbers / claims:** none stated.
- **Novel-to-GTOS:** NO.

### [12] How to Determine Which Forex Pair Will Move
- **URL:** https://www.quantlabsnet.com/post/how-to-determine-which-forex-pair-will-move-does-this-work
- **Date:** 2020-12-28
- **Tag:** PRIORITY
- **Relevance verdict:** SKIP (landing page, no methodology)
- **Core thesis:** "New discovery. Does this actually work?" — no method disclosed.
- **Novel-to-GTOS:** NO.

### [13] Fast C++ Implementation for Order Book HFT
- **URL:** https://www.quantlabsnet.com/post/fast-c-implementation-for-order-book-hft
- **Date:** 2015-10-27
- **Tag:** PRIORITY
- **Relevance verdict:** SKIP (external-link-only, content on alexabosi.wordpress.com)
- **Core thesis:** Pointer to external C++ LOB blog post.
- **Tools/tech:** C++ LOB, Matlab charts (external).
- **Novel-to-GTOS:** NO.

### [14] Ultimate Guide to AI-Powered Quant Finance Interview Prep
- **URL:** https://www.quantlabsnet.com/post/the-ultimate-guide-to-ai-powered-quantitative-finance-interview-preparation
- **Date:** 2026-04-10
- **Tag:** KEEP
- **Relevance verdict:** LOW (interview prep, not implementation)
- **Core thesis:** Study guide covering probability, Bayesian reasoning, data structures, stochastic calculus, market microstructure.
- **Tools/tech:** SMA, RSI (0-100), Bollinger Bands, mean reversion. Hub-and-spoke WebSocket:8765 → IBKR TWS:7497.
- **Numbers / claims:** Comp (informational only): NY juniors $200-400K, seniors $500K-2M, PMs $2M-50M+.
- **Novel-to-GTOS:** NO — hub-and-spoke WebSocket pattern is one data point against our direct-MT5-per-symbol, but ours is simpler and fine for 5 instruments.

### [15] Advanced Cross-Asset Futures Trading Strategies (2026 Macro Crisis)
- **URL:** https://www.quantlabsnet.com/post/advanced-cross-asset-futures-trading-strategies-navigating-the-2026-macro-crisis-and-geopolitical-s
- **Date:** 2026-03-21
- **Tag:** KEEP
- **Relevance verdict:** MEDIUM (risk rules transfer; specific trades don't)
- **Core thesis:** Relative-value spread trades > directional; strict risk rules under macro stress.
- **Tools/tech:** COT analysis, calendar spreads, crack spreads, 3-2-1 crack, cross-asset pairs (BTP/Bund, ES/NQ rotation).
- **Numbers / claims:** Per-trade cap 2% equity; volatile contracts smaller notional; margin buffer 50% excess; BTP/Bund 87bp (from 61bp); oil $119 (Strait of Hormuz); Fed rate-hike probability 50% by Oct; US debt $39T+; BTC $70K→$60K (14.3%).
- **Prompt snippets:** none stated
- **Architecture details:** None system-level.
- **Strategy details:** Long gold (fiscal hedge), long copper on dips, ES/NQ rotation (long ES short NQ for industrial vs tech).
- **Novel-to-GTOS:** MAYBE — the correlation-breakdown-during-crisis warning is worth citing in our portfolio_risk docs. Our XAUUSD/US30/USDJPY/JPY-crosses exposure would also break down in a macro shock; we already cap at 2% per correlation group, matching their stance. Confirmation, not new.

### [16] Building Profitable AI-Generated Trading Strategies with Python, Rithmic and LLMs
- **URL:** https://www.quantlabsnet.com/post/building-profitable-ai-generated-trading-strategies-with-python-rithmic-and-llms
- **Date:** 2026-03-13
- **Tag:** KEEP
- **Relevance verdict:** HIGH
- **Core thesis:** News→Prompt→LLM codegen→Validate→Deploy pipeline produces live strategies in ~60 minutes. "Vibe coding" reduces development time months→hour.
- **Tools/tech:** Rithmic Python API (5 plants: MD/Order/Position/Historical/Repository). LLMs benchmarked:
    - GLM-5 (ZhiPu, 128K ctx, 1x, 3-8 min)
    - Codex 5.3 (OpenAI, 128K, ~1.8x, 1-3 min — "Goldilocks")
    - Claude 4.6 (Anthropic, 200K, ~3x, best readability, 5-10% failure on massive prompts)
- **Numbers / claims:** Portfolio aggregate +$78,600 / Sharpe 2.1 / max DD $12,300 (15.6%). Per-strat: BTC momentum +$41.2K Sharpe 2.8 WR 68% DD ~7%; Natural gas mean-reversion +$52.8K Sharpe 4.3 DD -36%; Gold tail hedge +$18.5K DD -18.6%. LLM monthly: GLM-5 $50-150, Codex $150-450, Claude $450-1350. Family-office TCO ~$198K/yr, LLM <1%. **Spread widens 3-5x in crisis; discount simulated perf 15-25%. Drawdown-to-Profit Ratio <1.0x required. Position sizing via 14-period ATR (not fixed lots).**
- **Prompt snippets:** Pseudocode: `prompt_template.render(analysis=market_analysis, instruments=["BTCM6", "GCM6", "NGK6", "ZNM6", "CLK6"], risk_params={"max_drawdown_pct": 0.15, "max_position_size": 5, "stop_loss_method": "atr_based"})` — typical prompt 1500+ lines.
- **Architecture details:** 4-stage pipeline: (1) News aggregation 30min → 41-page analysis, (2) Prompt construction 10min, (3) LLM codegen 2-8min, (4) Validation + backtest + deploy 15min.
- **Strategy details:** 5-7 strategies per run; auto-deploys only if performance exceeds threshold. Hardware/software kill switch; git-versioned prompts+LLM+timestamp for regulatory compliance.
- **Novel-to-GTOS:** MAYBE — Pipeline philosophy differs (they regenerate strategies from news; we have frozen T7 OB structure). BUT: (a) **Drawdown-to-Profit ratio <1.0x** is a clean promotion/kill gate worth considering for shadow-logger graduation decisions; (b) **discount simulated perf 15-25% for real-world spread widening** is a calibration number we could apply to T7 simulation outputs; (c) **ATR-14 dynamic sizing** is a pattern already in our WF-2 candidates (WF2_SHADOW_GATES_V2.md) — external confirmation. (d) Claude 4.6 at 3x cost vs Sonnet 4.6 matches our empirical finding (project_opus_vs_sonnet_p2c.md) that Sonnet wins the live gate. (e) git-versioned prompt+model+timestamp matches our existing prompt-freeze discipline.

### [17] Hosting Qwen in 2026 (StudioLM/Ollama/Jan.ai Freeze)
- **URL:** https://www.quantlabsnet.com/post/what-to-do-about-hosting-qwen-in-2026-when-studiolm-ollama-jan-ai-freeze
- **Date:** 2026-03-04
- **Tag:** KEEP
- **Relevance verdict:** LOW
- **Core thesis:** Desktop LLM apps freeze on memory exhaustion (VRAM, KV cache, RAM swap); production needs vLLM or managed APIs.
- **Tools/tech:** llama.cpp (GGUF, CPU+GPU hybrid), vLLM (PagedAttention, continuous batching), Jan.ai (5.2M downloads), Lambda GPU (B200 180GB, H100 80GB).
- **Numbers / claims:** none specific (no latency/pricing).
- **Novel-to-GTOS:** NO — we use Anthropic managed API, not local inference. Relevant only if we ever needed on-prem for latency; currently a non-issue.

### [18] Comprehensive Guide to Microsoft Qlib
- **URL:** https://www.quantlabsnet.com/post/comprehensive-guide-to-microsoft-qlib-the-ai-oriented-quantitative-investment-platform
- **Date:** 2026-02-20
- **Tag:** KEEP
- **Relevance verdict:** MEDIUM (research framework only)
- **Core thesis:** Qlib end-to-end AI quant platform covering data → alpha → risk → execution.
- **Tools/tech:** XGBoost, LightGBM, CatBoost; LSTM/GRU/attention; GNNs, transformers; DoubleEnsemble, TCTS, ADARNN. RL for execution: TWAP, PPO, OPDS. RD-Agent: LLM-based autonomous factor mining from financial reports.
- **Numbers / claims:** 37,000+ GitHub stars. Data loading: 360s (MySQL) → 7.4s (Qlib cache) — ~49x speedup.
- **Architecture details:** Offline + online deployment modes; data health verification script.
- **Novel-to-GTOS:** MAYBE — RD-Agent (LLM autonomous factor mining from filings) is interesting as a research tool for alpha discovery, not live trading. Could be used for weekly research on XAUUSD fundamentals. Not urgent.

### [19] Architectural Analysis of a Hybrid Rithmic Trading System
- **URL:** https://www.quantlabsnet.com/post/architectural-analysis-of-a-hybrid-rithmic-trading-system
- **Date:** 2026-02-07
- **Tag:** KEEP
- **Relevance verdict:** LOW (architecture only, not applicable)
- **Core thesis:** Three-tier: C#(.NET 8) gateway + Python strategy + Redis (localhost:6379) pub/sub.
- **Tools/tech:** .NET 8.0 LTS, Python 3.8+ (notes 3.13+ JIT/GIL removal coming), Redis pub/sub. Requires rapiplus.dll + rapi_net.dll.
- **Numbers / claims:** "Sub-millisecond on localhost" serialization; "acceptable for retail algo but unsuitable for HFT market making."
- **Novel-to-GTOS:** NO — our direct MT5-python per-process per-symbol is simpler for our latency needs. Redis-based decoupling might help if we needed cross-process coordination, but current design doesn't need it.

### [20] The Invisible War: Decoding Data Noise (2026)
- **URL:** https://www.quantlabsnet.com/post/the-invisible-war-decoding-data-noise-and-the-future-of-algo-trading-in-2026
- **Date:** 2026-01-25
- **Tag:** KEEP
- **Relevance verdict:** LOW
- **Core thesis:** Millisecond signals are noisy; retail should operate on minute+ timeframes where HFT noise decays.
- **Tools/tech:** "Python for research, C++ for execution". MACD cited as manipulation-vulnerable at low timeframes.
- **Numbers / claims:** ES ~90K data points vs NQ ~48K in sample (volume-reliability differs).
- **Filter recipe:** (1) macro filter (BoJ, crypto flows), (2) volume confirmation via order flow, (3) AI sentiment layer, (4) temporal abstraction (ms→min+).
- **Novel-to-GTOS:** NO — we already operate on M15/H1, above the noise floor. Confirms our timeframe choice.

### [21] Comparative Analysis of Narrative vs Numerical Forecasting 2026
- **URL:** https://www.quantlabsnet.com/post/comparative-analysis-of-narrative-vs-numerical-market-forecasting-for-2026
- **Date:** 2025-12-31
- **Tag:** KEEP
- **Relevance verdict:** LOW (macro essay)
- **Core thesis:** "Quantamental" synthesis of fundamental/technical and deep-quant.
- **Numbers / claims:** PDC 1.85% at 92nd %ile since 2008; G10 carry Sharpe 1.8-2.3 std above avg; AUD/NZD swap 87bp; JPY carry disadvantage 340bp vs G10; intervention probability 22% if USDJPY >8%/month; gold-TIPS correlation -0.68; real rates +2.1%; SPX fwd P/E 18.2x (earnings yield 5.8%); 95% VaR max-DD 2.8%; equity-bond correlation -0.42; Monte Carlo 10K paths.
- **Techniques:** HH/HL, inverse H&S, cup & handle, Ichimoku, Z-scores, Monte Carlo, volume profile.
- **LLM integration:** none.
- **Novel-to-GTOS:** NO — we don't trade macro. The USDJPY intervention-probability (22% if >8%/month) is a data point to possibly pause USDJPY if monthly move exceeds 8%, but this is a rare event and our current news filter is disabled by design.

### [22] Launching Professional-Grade Futures Platform with Rithmic API
- **URL:** https://www.quantlabsnet.com/post/launching-a-professional-grade-futures-trading-platform-with-rithmic-api-integration
- **Date:** 2025-12-18
- **Tag:** KEEP
- **Relevance verdict:** MEDIUM
- **Core thesis:** Multi-thread Rithmic stack with market-data, order-mgmt, and risk/compliance on separate threads; blue-green deploy with 30-min shadow mode before live.
- **Tools/tech:** Rithmic C++ libs + C# wrappers; FPGA-accelerated feed (nanosecond timestamps); CME Globex/ICE/Eurex.
- **Numbers / claims:** Shadow mode 30min; initial capital $10K per new strategy; lead-lag strategy daily loss cap $2,500; max 3 trades per FOMC period.
- **Strategies:** (1) Order-book-imbalance mean-reversion, 2-contract sizing, 2-5min hold; (2) Treasury→equity 50-200ms lead-lag, 3 trades max per FOMC; (3) VIX futures curve regime-transition, size inversely scaled to VIX; (4) crude calendar stat-arb, 10-day max hold.
- **Novel-to-GTOS:** MAYBE — (a) **Blue-green "shadow mode 30 min before live"** is interesting as a deploy gate — more rigorous than git commit-and-restart; possible WF-2 enhancement to run new prompts/config in parallel paper mode for N candles before full switch. (b) **Max 3 trades per FOMC period** is a sensible macro-event guard; we have news_filter.enabled=false, so not a direct gap, but worth noting if we re-enable. (c) Per-strategy daily loss cap ($2.5K) pattern matches our per-symbol approach conceptually.

### [23] The Non-Negotiable Skill: Reading API Documentation
- **URL:** https://www.quantlabsnet.com/post/the-non-negotiable-skill-why-reading-api-documentation-still-defines-great-engineers
- **Date:** 2025-12-01
- **Tag:** KEEP
- **Relevance verdict:** SKIP (philosophical essay)
- **Core thesis:** Read API docs before trusting AI-generated code. Examples: Stripe idempotency, PostgreSQL pooling, S3 perf cliffs (non-trading).
- **Novel-to-GTOS:** NO — already embedded in our MT5 preflight and VERIFICATION PROTOCOL rules.

### [24] Building an AI Trading Dashboard with Python for Futures Markets
- **URL:** https://www.quantlabsnet.com/post/building-an-ai-trading-dashboard-with-python-for-futures-markets
- **Date:** 2025-11-13
- **Tag:** KEEP
- **Relevance verdict:** LOW
- **Core thesis:** Streamlit + RandomForestClassifier dashboard for OHLCV data. "AI" = ML, not LLM.
- **Tools/tech:** Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, Streamlit. RandomForest (100 estimators), time-series train/test (shuffle=False). Drops `future_price` to avoid leakage.
- **Numbers / claims:** none stated (methodology only).
- **Novel-to-GTOS:** NO — we don't use ML classifiers; our gate is the LLM MSO evaluation.

### [25] Challenging an AI Skeptic — AI-Generated Trading Dashboard
- **URL:** https://www.quantlabsnet.com/post/challenging-a-ai-skeptic-a-look-inside-a-powerful-ai-generated-trading-dashboard
- **Date:** 2025-10-17
- **Tag:** KEEP
- **Relevance verdict:** LOW
- **Core thesis:** Streamlit dashboard built with AI assistance; 2-year data from MotiveWave.
- **Tools/tech:** Streamlit; volatility surface 3D; ATR/Sharpe/Sortino rolling; forward opportunity ranking by momentum+vol contraction+volume+risk.
- **Numbers / claims:** BRL -2.85% / -8% DD; SPX 17% ann / -15% DD; UB -1.2% / 0.65 rolling Sharpe; ETH -3% / -9% DD. Author spends "a couple hundred bucks a month on AI".
- **Novel-to-GTOS:** NO — dashboard is descriptive, not decisional.

### [26] Boost Your Trading with QuantLabs
- **URL:** https://www.quantlabsnet.com/post/boost-your-trading-with-quantlabs
- **Date:** 2025-09-29
- **Tag:** KEEP
- **Relevance verdict:** SKIP (marketing page)
- **Novel-to-GTOS:** NO.

### [27] The Quant Blueprint — Automated Trading Goal Discovery
- **URL:** https://www.quantlabsnet.com/post/the-quant-blueprint-mastering-your-automated-trading-goal-discovery
- **Date:** 2025-09-16
- **Tag:** KEEP
- **Relevance verdict:** SKIP (questionnaire sales funnel)
- **Novel-to-GTOS:** NO.

### [28] Unlocking Wall Street's Secrets — Low-Cost HFT for Retail
- **URL:** https://www.quantlabsnet.com/post/unlocking-wall-street-s-secrets-how-quant-ai-is-building-low-cost-hft-strategies-for-the-rest-of-us
- **Date:** 2025-09-03
- **Tag:** KEEP
- **Relevance verdict:** LOW (futures arb example)
- **Core thesis:** AI-built low-cap C++ HFT for rough rice put-call-parity arb.
- **Tools/tech:** C++ zero-copy buffers, lock-free ring buffers, STL only. Three-leg synthetic (buy call, sell put, sell future). Multi-leg combo IOC order.
- **Numbers / claims:** Strategy cap $6K (portfolio margining), "$850/contract" entry; 50-iter sim: gross ~$15-18/contract / total $245; execution cost $7.50/trade; slippage $5.20/trade; net $49 (80% reduction after costs). Target: Rough Rice futures (ZR) arbitrage.
- **Prompt approach:** Author requests "institutional-style" quant reports including "analytical formulas with math, strategy discussion" rather than simple code requests.
- **Novel-to-GTOS:** MAYBE — the **80% cost-drag from slippage + execution** on a quote-edge strategy is a cautionary datapoint: small-edge strategies get eaten by costs. Our OB-retest edge is large (+17pp) so this is confirmation our edge-over-costs ratio is healthier. The "institutional-style quant report" prompt-elicitation pattern is worth noting as a way to improve research-phase prompts (not live gate).

### [29] Building a Real-Time Options Pricing Engine
- **URL:** https://www.quantlabsnet.com/post/building-a-real-time-options-pricing-engine-from-theory-to-lightning-fast-code
- **Date:** 2025-08-22
- **Tag:** KEEP
- **Relevance verdict:** SKIP (options-only, not applicable)
- **Core thesis:** Python BSM engine + WebSocket feeds (Polygon.io, Finnhub) + Redis cache.
- **Tools/tech:** Python, NumPy, SciPy, Pandas, asyncio. BSM, Greeks (Delta/Gamma/Vega/Theta/Rho). Redis + RabbitMQ/Kafka optional.
- **Numbers / claims:** Simulation 500ms update intervals. No production latency stated.
- **Novel-to-GTOS:** NO — we don't trade options.

### [30] In-Depth Technical Briefing — LightningChart Senior Developers
- **URL:** https://www.quantlabsnet.com/post/an-in-depth-technical-briefing-for-one-on-one-with-lightningchart-senior-developers
- **Date:** 2025-08-05
- **Tag:** KEEP
- **Relevance verdict:** SKIP (charting library, not algo)
- **Core thesis:** LightningChart for "billions of data points" real-time visualization (WebGL/DirectX).
- **Architecture stacks scored:** Python+JS (9/10), C+++JS (7/10 — only if µs critical), pure Python (8/10), WASM hybrid (10/10).
- **Novel-to-GTOS:** NO — visualization not a current bottleneck.

