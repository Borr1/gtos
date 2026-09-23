# Batch 05 — QuantLabs (Bryan Downing) Competitor Intel

**Scope:** 6 transcripts, ~20,201 words. Channel: QuantLabs / Bryan Downing. Focus = his AI-agentic news-to-bot pipeline, IBKR TWS + Rhythmic futures, HFT critique, and price-prediction content.
**Agent instructions:** extract any idea upgradeable to GTOS (Python + MT5 + Claude + OB retest) — tools, strategy ideas, numerical claims, prompt snippets, architecture, risk/execution, novelty.
**Output:** per-video schema with Relevance, quotes, Novel-to-GTOS flag.

---

## TOP FINDINGS (batch-level synthesis, read first)

1. **News → PDF → bot codegen pipeline (Rhythmic/IBKR/Python).** Bryan's "agentic" workflow: news-aggregator agent writes a ~1,200-line raw file + 30-page PDF per run, a codegen phase turns each news theme into a standalone Python trading bot, and a test-mode loop of 15-30 min decides which bots get "promoted" to live. Models cited: **Codex 5.2/5.3** for bot codegen, **Claude 4.6** for the orchestrator itself (after GLM/Codex "failed"), **MiniMax M2.1** as a cheap substitute (~"90% of Claude" quality at ~5% cost). MCP servers explored via **Cline**. This is an "instrument-discovery" pipeline we don't have — GTOS is locked to 5 instruments and one OB framework. (MAYBE worth stealing the news-driven signal-generation concept as a separate KAP agent.)
2. **Signal-validation via news "layering".** Strong conceptual argument (echoed twice across the batch): HFT creates noise at the millisecond level; retail's only edge is **context**. Bryan's deep-dive video argues that raw C-features buy/sell signals flip every 3 seconds on ES (MACD example) and retail is providing exit liquidity. Proposed solution: confirm candidate trades with a news-feed filter (AI-scanned, not human-read) before commitment. **Directly applicable to GTOS** as an optional news-confirmation shadow logger on top of T7 CANDIDATEs.
3. **Specific per-asset claim to track:** AI-suggested "lowrisk bull call spread on Canadian dollar with 70% projected win ratio and only 8% max draw down; walk-forward 9.5% return vs. backtest 9.65% — close alignment." This is numeric-specific self-reported content (not audited); useful as a peer-comparison data point for our batch-WR reporting.
4. **Live bot performance he admits to** (RVK transcript): *"19 trades, 42% win ratio"* on CAD futures + ZS soybean, *"still making money."* And overnight: *"47% win ratio, 364 trades,"* only Bitcoin profitable. Order of magnitude lower WR than our 65% batch / 71.4% live — confirms our OB-retest edge is structurally stronger than his news-codegen approach.
5. **MCP security warnings + expense-control tips.** Two concrete items: (a) malicious Python package `LMLite` (his spelling) reportedly exfiltrates credentials; (b) a third-party MCP server did the same. Operational advice: stick to official MCP servers (Google Analytics example), prefer **Haiku over Sonnet** for cost, use **prepaid cards** to cap Anthropic subscription bleed. Relevant to our MCP exposure if we extend.
6. **Kilo Code / Cline / Claude Code extension** as codegen IDEs — "type English, get Python bot" workflow. Not novel, but timely: he describes a **2-minute bot-clone pattern** (IBM bot from Apple bot, change logic to Bollinger Bands) which is a reasonable template for rapid strategy-variant backtests.

**Overall relevance:** 2 MEDIUM (concept-level applicable), 3 LOW (retail/salesy content), 1 SKIP (futures-options advertorial). **Nothing directly threatens our OB-retest edge.** His whole stack is news-sentiment + rapid codegen → mostly orthogonal to our structural ICT approach.

---

### [1] AI Agents for AUTOMATED Trading: News to Bot in Minutes (Python & Rithmic)
- **Video ID / URL:** DD_uwHAgofs / https://youtube.com/watch?v=DD_uwHAgofs
- **Duration:** 2541s  **Words:** ~6469
- **Relevance:** MEDIUM — agentic news-to-bot pipeline architecture; MCP + multi-model orchestration patterns we could study; macro news-feed coverage our system ignores.
- **Core thesis:** Multi-phase AI agent pipeline: news ingestion (blockchain+crypto, commodities, forex, treasury+bonds, investing+markets) -> 30-page PDF report -> automatic Python bot generation per news-driven strategy -> 15-30min test-mode promotion loop -> promotable to live on Rhythmic futures. He uses this to argue quant coding jobs are effectively obsolete; only "systematic portfolio managers" survive.
- **Tools/tech:**
  - **Rhythmic** (futures + options low-latency data, cannot show source per ToS).
  - **Python 100%** (orchestrator + bot codegen).
  - **Kilo Code** / **Cline** (VS Code extensions), moved to Cline for better MCP server selection.
  - **Codex 5.3** for bot generation; originally GLM + Codex failed ("really hard to get through") so upgraded to **Claude 4.6** for the orchestrator ("the big guns, the expensive guns").
  - Multi-model/multi-agent via **MCP servers** ("orchestrator terminology I didn't know... set of instructions... multi-agents in parallel and/or multi-model").
  - **OpenRouter** mentioned as model aggregator option.
  - File structure: `news_feed/`, `trading_report/`, per-run timestamped bot folders.
- **Strategy / signal ideas:**
  - AI auto-selects instruments by volume priority — confirmed across multiple models.
  - Example instruments generated this run: Bitcoin momentum, Ethereum sentiment, crude oil breakout, gold safe haven, EUR/USD carry, treasury yield curve, ES macro momentum, natural gas volatility.
  - No agriculture bots generated "because volume was fairly low vs other instruments."
  - VWAP + "retest phenomenon in futures" mentioned (zone-based idea): *"price will break your magic level, look like it's gone, then trade back, grab liquidity, stop out, break out, break down."* This is his version of OB/liquidity sweep language — **same edge mechanism GTOS exploits**.
  - Cross-correlations (oil vs gold breakdown, inflation-linked derivatives).
  - Options positioning: "long EUR/USD straddle ahead of April ECB meeting"; "BoJ intervention USD/JPY Japanese call butterfly: buy 145 call, sell two 150 calls."
  - Macro driver cues he calls "drivers + targets": CME CFTC positioning, open interest deltas, IV skew, VIX/OVX spikes to 40 as regime flag.
- **Numerical claims:**
  - "30% of all trades by hedge funds" use AI agents (unverified, "a week ago").
  - "~10 minutes of running this I can create trading bots to test out and have them deployed."
  - Test mode: "15 minutes, half an hour" run before live promotion.
  - PDF is "about 30 pages," raw data file "about 1,200 lines."
  - Gold target 5000, open interest decline 8%, fell 4% as example "data signal."
  - Example CFTC: "$5 million in 110+% biotech stock put spreads to lock in gains."
  - No per-bot WR, PnL, or Sharpe reported.
- **Prompt snippets / AI usage:** None verbatim. Describes **orchestrator** with "general set of instructions" → parallel multi-agent execution. Asserts multi-modal (Codex + Claude + other) used concurrently. No API schema shown.
- **Architecture / code patterns:**
  - Phase 1: news agent (pulls from feeds) → raw file.
  - Phase 2: PDF generator (markdown/table rendering).
  - Phase 3: bot generator (per news theme -> Python script).
  - Phase 4 (optional): auto-launch bots in test mode.
  - Per-batch timestamped directory for traceability.
  - He uses Redis as message bus between Python bots and TWS server (from the IBKR video, same stack).
- **Risk / execution:**
  - Notional: 1 contract per bot in simulation; scale later.
  - "Long person, don't like shorting" bias noted — institutional strategies generate both directions but he defaults long.
  - Target-driven trading: AI-supplied entry, target, driver per strategy.
  - No specific SL sizing logic described.
- **Novel-to-GTOS:** MAYBE — the news-agent → codegen pipeline is orthogonal to our locked OB framework, but **the news-feed confirmation layer** could be repurposed as an optional CANDIDATE filter. Not a priority; our edge is structural, not event-driven.
- **Verbatim quotes:**
  > "I brought in as usual the big guns, the expensive guns, uh the Claude 4.6, which kind of coded it up pretty nicely."
  > "In within 10 minutes of running this I can create trading bots to test out and then have them deployed into a real live trading environment for Rhythmic."
  > "30% of all hedge funds are now using not just AI to do this, but they're using what you're seeing here, agents to do this. 30% of all trades by hedge funds. That was a week ago."
  > "Price will break your magic level, look like it's gone, then trade back, grab liquidity, stop out, break out, break down." *(his phrasing of OB/sweep mechanics)*

---

### [2] STOP Paying for Trading Platforms! Build AI Python Bots for FREE (0 Coding Skills)
- **Video ID / URL:** 7SInPIMWntk / https://youtube.com/watch?v=7SInPIMWntk
- **Duration:** 1746s  **Words:** ~4378
- **Relevance:** LOW — tutorial/promo for his IBKR+Kilo Code product; a few useful ops notes.
- **Core thesis:** With VS Code + Kilo Code + Interactive Brokers TWS + Python, anyone with zero coding skill can codegen working bots in minutes. Chinese LLMs (MiniMax M2.1, DeepSeek) are "90% of Claude at 5% of cost, subsidized by CCP."
- **Tools/tech:** VS Code, IBKR TWS (Trader Workstation), Python, Kilo Code extension, MiniMax M2.1, Codex 5.2/5.3, Claude (4.5/4.6 / Opus for debugging), Redis as IPC between bots and TWS server.
- **Strategy / signal ideas:** Demo bots: RSI+ATR on GBP/USD, SMA+ATR on Apple, Bollinger Bands+ATR on IBM, Alligator (SMMA on weighted price, fractal filter, Martingale grid entries, trailing exits) bot translated from a Russian-commented MQL5. Nothing novel — all retail-standard.
- **Numerical claims:**
  - IBKR cost: ~$30/month in commissions for free market data + 30 trades/month minimum.
  - MiniMax = "5% of Claude/OpenAI cost."
  - Codegen on IBM bot clone: ~2 minutes via Codex 5.2.
- **Prompt snippets / AI usage:**
  - "Create a new Python script called IBM bot from AAPL bot Python."
  - "Replace all trading logic to use Bollinger Bands."
  - Advice: simpler prompts = faster & cheaper; use "enhance prompt" feature only when needed.
  - "Give me a coding breakdown on IBM bot" for reverse-engineering / docs.
- **Architecture / code patterns:**
  - **Multi-bot w/ Redis message bus** + one TWS-server Python process. "You can run multiple of these against the Python TWS server code and it will use Redis as the message bus."
  - Each bot is a standalone Python file; server dispatches orders.
  - Cannot multi-bot natively on TWS — his Redis-proxy pattern fixes that.
- **Risk / execution:** Demo level. He mentions ATR-based stop sizing, no real risk logic described.
- **Novel-to-GTOS:** NO — we already have a per-symbol PID-locked process model; nothing to borrow.
- **Verbatim quotes:**
  > "Miniax is good enough where it's I'd say 90% the quality of output that you would get with the expensive quad uh 4.5 4.6 um and that's Opus."
  > "Chinese models because they're so cheap where they're 5% of the cost against Claude or or uh Open AI... a lot of that's subsidized by the CCP by the way."
  > "You can run multiple of these against the Python TWS server code and it will use Redis as the message bus."

---

### [3] Stop trying to trade like a hedge fund. You are becoming their liquidity.
- **Video ID / URL:** khMd97ZJ8eA / https://youtube.com/watch?v=khMd97ZJ8eA
- **Duration:** 1059s  **Words:** ~3502
- **Relevance:** MEDIUM — strong conceptual argument with two specific, testable claims; this is an AI-generated "deep dive podcast" style recap of a QuantLabs stream from Jan 24.
- **Core thesis:** Raw market data at millisecond granularity is a trap for retail; HFT firms churn the water to look like momentum. Only defense: **layer macro context (news, carry trade, BoJ) on top of raw data**; "compete on context, not speed."
- **Tools/tech:**
  - **Rhythmic "C features"** (low-latency data logs / occurrences stream).
  - AI news-feed scanners as **confirmation filters**.
  - Reference to UBS pushing crypto to institutional clients.
- **Strategy / signal ideas:**
  - **Occurrences-per-second as an "RPM" regime indicator** — not trades, but every tick analysis/bid update/query. "Every time the system analyzes a price tick, updates a bid, sends a query, or checks a logic gate. It is the digital exhaust of the trading engine."
  - Comparison of NQ vs ES occurrence volume to identify where institutional activity lives (ES ~93k vs NQ ~48k in same window).
  - Buy/sell signal flip on ES in 3s as proof of HFT churn, not value change.
  - BoJ carry-trade unwind as macro risk ("plates moving").
  - News-confirmation filter: "If chart shows a move but AI news scan finds nothing → fake out."
- **Numerical claims:**
  - "NASDAQ about 48,000 occurrences... S&P 500 ESH6 contract nearly double... over 93,000."
  - MACD buy signal on ES followed by sell signal "literally 3 seconds later."
  - Applies specifically to accounts "under $10 million."
- **Prompt snippets / AI usage:** Not verbatim, but explicit framework: *"Imagine the S&P 500 jumps 10 points in a minute. Your emotions say FOMO... But if your AI scans the news feeds and finds nothing, no earnings report, no Federal Reserve announcement, no geopolitical event, no Bank of Japan statement, then the move is suspect."* — a usable template for a **news-confirmation shadow logger** in GTOS.
- **Architecture / code patterns:**
  - Conceptual: "layering" raw market data + news + macro = signal confirmation.
  - No implementation shown; the podcast is derived from Bryan's stream.
- **Risk / execution:**
  - Macro awareness as risk filter (BoJ intervention → US asset liquidation risk).
  - "Don't trade in a vacuum. Context beats speed."
- **Novel-to-GTOS:** MAYBE — we don't currently have a **news-confirmation shadow logger** on CANDIDATE signals; borderline idea worth logging. Our entry timing is candle-close M15, so HFT-millisecond noise isn't our primary risk, but macro tape (BoJ, Fed, ECB) directly hits XAUUSD and USDJPY.
- **Verbatim quotes:**
  > "He sees a buy signal on the S&P 500 futures based on a MAC CD indicator... but then literally 3 seconds later, 3 seconds, there's a sell signal... And that is the kill zone."
  > "The source is very blunt about this. He says, 'For the retail investor, this high-speed data isn't information. It is garbage. It is noise.'"
  > "They have speed. We have context."
  > "You are buying their trash. You are providing the liquidity for them to exit their trade. You are the bag holder instantly."

---

### [4] My AI Trading Bots Are Making Money While Markets Crash (Full Setup Revealed)
- **Video ID / URL:** RVKvYOoDQ7Q / https://youtube.com/watch?v=RVKvYOoDQ7Q
- **Duration:** 1119s  **Words:** ~2889
- **Relevance:** MEDIUM — self-reported live performance numbers + security ops advice + MCP integration example.
- **Core thesis:** His Rhythmic-fed, agent-generated futures bots (BTC breakout, Ethereum geopolitical, RBO/natural-gas/copper, CAD futures, soybean ZS) are netting positive across a crashing equity tape. MCP + Claude desktop + Claude Code VS Code extension is now his preferred stack over Kilo / Cline.
- **Tools/tech:**
  - **Claude Desktop** + **Claude Code VS Code extension** (preferred now).
  - **MCP servers** for Discord posting, website integration, Google Analytics (official).
  - Cline and Kilo AI tried and rejected: "Quad modeling is more advanced."
  - Wolfram Alpha, MATLAB, Perplexity research mentioned as MCP extension targets.
  - **Haiku** as cost-control default model.
- **Strategy / signal ideas:**
  - Bots live right now: BTC futures breakout momentum, Ethereum geopolitical, RBOB/natural-gas/copper, CAD futures, ZS soybean.
  - Core argument: on "red" days for equities (S&P -1%, VIX up), commodity/currency futures bots still find PnL; single-asset retail stock traders don't.
- **Numerical claims:**
  - Live CAD + ZS combo: **19 trades, 42% WR, "still making money"** (claimed positive expectancy despite sub-50% hit rate).
  - Overnight batch: **47% WR across 364 trades, only Bitcoin profitable.**
  - Claude subscription Pro: $20-25/month; "no cap," horror stories of "$10,000 in one month."
  - Target product pricing: HFT C++ eBook at $30 → moving to $60; Quant Analytics tier from ~$50 → $97/month.
- **Prompt snippets / AI usage:** None verbatim. References "tell Claude Code which MCP servers to use, only use official ones, not third party."
- **Architecture / code patterns:**
  - **MCP server orchestration** for ops-automation: auto-post results to Discord, send files to his paid/free website, tap into GA traffic data.
  - Agents run bots in background across multiple PowerShell sessions while running new batches concurrently.
  - Real-time bot PnL + loss alerts posted to Discord — confirms our idea of Telegram push as operator dashboard.
- **Risk / execution:**
  - Bot-level notification on loss transitions (profitable → negative) via Discord webhook.
  - Account-level protection advice: **prepaid credit card capped to monthly subscription budget** to prevent runaway Anthropic API billing.
  - Package/MCP **supply-chain security**: named malicious Python package `LMLite` (his spelling, credential exfiltration) and one unnamed third-party MCP server with identical behavior. Advice: "stick with Claude/Gemini/OpenAI official MCPs; never third-party for trading."
- **Novel-to-GTOS:** NO for strategy (42-47% WR is well below our 65-71%). MAYBE for operational pattern: (a) MCP supply-chain auditing as a checklist item, (b) prepaid-card cap as expense defense, (c) Discord/Telegram webhook for per-bot PnL-transition alerts (we have some of this already).
- **Verbatim quotes:**
  > "Performance. 19 trades, 42% win ratio. So technically we're we're probably still making some money here."
  > "364 trades... 47% win ratio... Only ones that made money was Bitcoin."
  > "One of the Python packages that came parasite package delight if you loaded it called LM light... that package when you run it from your Python scripting it would basically swipe all your credentials off your computer."
  > "Use the lowest cost one, which is haiku. If you can go back a few versions like current one would be 4.6."
  > "If you have access or get a prepaid credit card... you're going to be only able to use quad models."

---

### [5] Price Predictions: Gold $5,000, Silver $130 & Natural Gas Explosion? (Q1 2026 Forecast)
- **Video ID / URL:** ZncFQX5iBbg / https://youtube.com/watch?v=ZncFQX5iBbg
- **Duration:** 713s  **Words:** ~1802
- **Relevance:** LOW — price-prediction promo, very thin on methodology; noted for numerical targets only.
- **Core thesis:** News-aggregator agent + prompt = AI-generated trade menu with entries/targets/timelines per asset for Q1 2026. Claims only **5 of his original 16 custom news feeds are actually valuable**; the rest are noise.
- **Tools/tech:** Custom news feeds (unnamed, "shall remain nameless"), unnamed Claude-class LLM consuming the feed output, Quant Analytics back-end for subscriber delivery.
- **Strategy / signal ideas:** AI-ranked trade list based purely on last 24hr news drivers — no price data supplied in this demo (theoretical pricing only). He claims supplying real prices would tighten the entry/exit.
  - Drivers enumerated: USD weakness (DXY 2026 lows), precious-metal super-cycle, energy crisis (deep-freeze storm in Texas), capital rotation crypto → BTC/ETH, Venezuela geopolitics.
  - Popular strategy types his system generates: options bull call spread, futures long momentum, options bear put spread.
- **Numerical claims (price targets, his LLM's output):**
  - **Gold**: long, target 5150-5250, timeline "over the next quarter" (note: claim that gold had already broken 5000 at recording is suspect).
  - **Silver**: long entry 115-116, target 125-130, current-quarter.
  - **Natural gas**: long 5.45-5.60, target 7.20-8.50, Feb-Mar 2026.
  - **EUR/USD**: long 1.18, target 1.19-1.205, this quarter.
  - **USD/JPY**: short, same target timeline.
  - **Bitcoin**: target 80k, then 94.5k / 105k, between Q2 and Q4.
  - Built from "about 2,000 lines of data from the last 24 hours."
- **Prompt snippets / AI usage:** *"I'm playing around with the prompting to just only show me now, most recently as of the last 10 minutes is to only focus on the pricing of the actual strategy and the pricing of whatever it's interested in trading with the forecast of an entry and exit and the reason behind it."* — describes a prompt for **signal extraction from news corpus**.
- **Architecture / code patterns:** None beyond the news-aggregator → LLM-digest flow already covered in Video 1.
- **Risk / execution:** "Ask the AI for probability on a forecast and how sustainable it is" — he uses probabilistic forecast score as a confidence proxy. No sample size or validation.
- **Novel-to-GTOS:** NO — retail-grade speculative trade calls, no edge validation. Numerical targets are useful only as external benchmarks to compare against our XAUUSD live.
- **Verbatim quotes:**
  > "Originally from yesterday had built out 16 custom feeds. What I started realizing is, uh only five are kind of valuable."
  > "We're dealing with about 2,000 lines of data. That's just from the last 24 hours."
  > "You can ask and I can ask this the AI is the next step is to say based upon what you're supplying as data projection, which one should I go with that has the highest potential?"

---

### [6] AI-Driven Options and Futures Strategies for Volatile Markets
- **Video ID / URL:** yFq6ajgC4qU / https://youtube.com/watch?v=yFq6ajgC4qU
- **Duration:** 380s  **Words:** ~1161
- **Relevance:** LOW — an AI-generated promo ("podcast-style") for Bryan's platform, dated Feb 2, 2026. Short and fluffy but contains one concrete numerical claim.
- **Core thesis:** Post-"gold/silver crash" event, traditional trading is "next to impossible." Only survival path: pivot to futures + options (trade volatility itself, not direction) **and** let AI run the entire pipeline — news scan → strategy generation → custom Python app → backtest → walk-forward — in minutes. Human becomes supervisor only.
- **Tools/tech:** AI (unnamed), Python codegen for per-trade test apps, walk-forward analysis.
- **Strategy / signal ideas:**
  - Example daily "strategic landscape" report: high-risk silver volatility play; Japanese yen risk reversal; **low-risk bull call spread on Canadian dollar**.
  - CAD spread specifically: "70% projected win ratio and only an 8% max drawdown."
  - Backtest: 9.65% return, 8% max DD → walk-forward 9.5% return "almost identical."
- **Numerical claims:**
  - **70% projected win ratio, 8% max DD** (CAD bull call spread).
  - **9.65% backtest return / 9.5% walk-forward return** — "close alignment."
  - Full cycle (idea → backtest → WF test) "in the time it takes to drink a cup of coffee" (not a validated performance claim, is a sales claim).
- **Prompt snippets / AI usage:** None.
- **Architecture / code patterns:**
  - Four-step workflow: (1) AI identifies opportunity, (2) AI writes a **dedicated one-off Python app** for that specific trade, (3) backtest, (4) walk-forward. Implicit: each trade gets its own codebase — questionable for maintainability but interesting pattern for research-only throwaway tests.
- **Risk / execution:** WF test is the "gate" for promotion (no specific PF/Sharpe threshold disclosed).
- **Novel-to-GTOS:** NO — his pipeline is news+options heavy, very different from our structural OB/ICT approach. The "one-off Python app per candidate" pattern is not something we'd adopt (maintenance nightmare).
- **Verbatim quotes:**
  > "A lowrisk bull call spread on the Canadian dollar. That last one is basically a strategy that profits if the currency goes up just a bit. And it came with a 70% projected win ratio and only an 8% max draw down."
  > "The test on historical data showed a solid 9.65% return with just an 8% max draw down. But here's the magic. The forward-looking test, the walk forward test, projected an almost identical return of 9.5%."
  > "A process of developing and validating a complex trading strategy that would traditionally take a team of quantitative analysts weeks of coding and testing can now be done in the time it takes you to drink a cup of coffee."

---

## Cross-batch patterns

1. **Bryan's stack is news-sentiment + auto-codegen**, completely orthogonal to GTOS's structural OB/ICT edge. He and we are playing different games — his bots are event/regime reactors, ours are liquidity-sweep-after-BOS reactors. He **does not mention** order blocks, FVG, BOS/CHoCH, swing highs/lows, liquidity sweeps, ICT language, or SMC. One single tangent (Video 1: "price will break your magic level... grab liquidity, stop out, break out, break down") uses OB-adjacent phrasing but he never names it.
2. **Self-reported live numbers are weak**: 42% and 47% WR on his current bots, which is below coin-flip territory on a heavy-tailed PnL distribution. Our 65% batch / 71.4% live is a structurally different regime. Not something that threatens our edge.
3. **Recurring operational lessons worth logging**:
   - MCP supply-chain risk (malicious Python + MCP packages).
   - Prepaid card to cap Claude/API runaway spend.
   - Haiku-as-default for cost control; Sonnet/Opus only when necessary.
   - Redis message bus for multi-bot on single broker connection (already known pattern; not novel to us).
4. **One usable conceptual borrow**: **news-confirmation layer** on trade candidates (Video 3 framework + Video 1 news-agent pipeline) — fits naturally as a shadow logger on T7 CANDIDATEs. Not a priority given our current focus (OB continuation monitor, between-KZ limit fix, sl_too_tight exception).
