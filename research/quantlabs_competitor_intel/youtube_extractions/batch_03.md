# QuantLabs Batch 03 — YouTube Extraction

**Source:** Bryan Downing / quantlabsnet.com — YouTube channel
**Batch:** 03 of N (7 transcripts, ~22,987 words)
**Extraction date:** 2026-04-18
**Extractor:** GTOS competitor-intel agent
**Purpose:** Pull every actionable idea that could upgrade GTOS (live AI trading on MT5 for XAUUSD, US30, USDJPY, GBPJPY, GBPUSD).

---

## TOP FINDINGS — what this batch contributes that GTOS doesn't currently do

1. **News-driven, AI-generated daily strategy dashboards** — Brian's entire workflow: feed 24h news into Claude/GLM/MiniMax, receive a ranked menu of trade setups across futures & options with projected Sharpe/WR/DD. GTOS has no news-ingestion or cross-asset strategy-selection layer; worth flagging as a R&D direction if we ever move beyond OB-retest.
2. **"Systematic portfolio manager" = new job** — continuously re-generate bots per news regime, pick top-2 performers, retire dogs within hours. GTOS is a single-strategy system; this is a concept for a multi-strategy orchestration layer.
3. **LLM cost/quality benchmarks (qualitative)** — Codex 5.3 ~3x cheaper than Claude with comparable Python/JS output quality for "simple" trading logic; GLM-4.5 cheapest but slow; MiniMax M2.1 ~5% of Claude 4.6 Opus cost for equivalent dashboard output. Useful data point when budgeting Claude Sonnet 4.6 spend on GTOS.
4. **MT5/Pine -> Python conversion via LLM** — claims 200-line MQ5 scripts and PineScript converted to working Python in 5-10 minutes with MiniMax + Kilo Code extension. If true (unverified), could accelerate ingestion of retail strategies for GTOS research.
5. **Quantified volatility/tail-risk warnings** — repeated "gold-silver ratio elevated relative to 2008 peak", "US Treasury volatility = game over", "inflation 2.0" (energy + food) thesis. Not directly actionable for GTOS but useful macro context for interpreting live WR decay.
6. **Rhythmic (not MT5) is Brian's broker stack** — uses Protobuf + custom C certs for futures/options via CME. Not GTOS-relevant (we're FTMO MT5 forex/indices/metals), but explains his platform silos.

**One sentence verdict:** Batch is heavy on news-driven futures/options dashboards and LLM-for-vibe-coding marketing; thin on concrete statistical edge that maps to GTOS's OB-retest mechanics. One maybe-useful idea: the news-regime-aware strategy rotation pattern (Novel-to-GTOS MAYBE).

---

## Per-video extractions

### [1] New Trading Algo Revealed: 82% Win Rate Strategy for Volatile Markets
- **Video ID / URL:** esW4G9TQTcQ / https://youtube.com/watch?v=esW4G9TQTcQ
- **Duration:** 2834s  **Words:** ~6918
- **Relevance:** LOW — futures/options news-dashboard marketing; nothing extractable as a testable signal for GTOS OB-retest pipeline.
- **Core thesis:** Retail traders miss because they're in the spot market watching charts. Real money is made in futures + options using AI to translate the last 24h of news into a ranked dashboard of cross-asset straddles, risk reversals, call-back-spreads, curve flatteners etc. The 82% WR claim is for a SOFR/Treasury curve trade, not for a repeatable spot-FX/gold strategy.
- **Tools/tech:** Rhythmic API (CME futures), C#/.NET server, Electron GUI app, Python client, HTML-based daily dashboards (self-contained for distribution). AI model not explicitly named in this video but implied Claude-tier for the analysis.
- **Strategy / signal ideas:**
  - "Volatility breakout, dynamic hedge, delta hedging" across Euro, silver, Bitcoin, crude.
  - Gold call back-spread: sell 1 ATM call, buy 2 OTM calls — finances a trade in high-IV environments.
  - ATM straddle + short futures for gamma harvesting — "for each 1% move, add 2 futures in the direction of the move."
  - Short 10y ZN + long gold + long put RTY for stagflation hedge.
  - CVD + IV-compression + gamma-squeeze as Bitcoin setup filter.
  - Brian repeatedly warns: "If you're in the spot market, you're going to get crushed... you're just guessing where the price goes based on charts" — philosophically hostile to GTOS's core approach.
- **Numerical claims (verbatim):**
  - "Win ratio of 82%... you're still getting a 12 to 18% return" (SOFR futures trade).
  - "Sharp ratio 1.65... win ratio potential of 68%... riskreward which is really high one to four and a half" (oil straddle).
  - "Gold call back spread: expected return 25%... sharp ratio 1.55, max draw down negative 35%."
  - "Bitcoin post-expiry momentum: 20 to 35% return, sharp ratio 1.45, max DD -22%, win ratio 64%."
  - "Australian risk reversal: 18 to 35% return, sharp 1.2, WR 64%."
  - "Copper leaps: win rate 70%... time horizon 6 to 12 months."
  - "Brent straddle: expected return 35-80%."
  - No sample sizes cited for any of these. All are AI-projected, not backtested.
- **Prompt snippets / AI usage:** Describes feeding "the last 24 hours of news" into AI to produce a dashboard of strategy ideas. No verbatim prompt shown.
- **Architecture / code patterns:** Electron front-end -> C#/.NET server -> Rhythmic API for orders. Dashboard output as standalone HTML for distribution. Not comparable to GTOS pipeline.
- **Risk / execution:** Emphasizes synthetic options structures (back-spreads, risk reversals, straddles) for asymmetric risk. Warns about correlation: "you don't want to be in Bitcoin that's correlated, you don't want to be in gold that's correlated, you want to be in uncorrelated trades."
- **Novel-to-GTOS:** NO — futures/options stack is orthogonal to our MT5 forex/indices/gold spot CFD focus. The macro/cross-asset correlation concept is already covered at Tier-3 in GTOS (portfolio_risk.py correlation groups).
- **Verbatim quotes:**
  > "I'm starting to probably lean towards saying I want to save money because I'll be doing this quite a bit with the agents out there... class is going to be a big factor."
  > "The only way to trade this out is using the automation."
  > "If you're in the spot market, you're going to get crushed. You're not trading. You're just guessing where the price goes based upon bunch of charts."

---

### [2] A Deep Dive into the Market Ripples Caused by Mid East Tension
- **Video ID / URL:** mL38NCciddk / https://youtube.com/watch?v=mL38NCciddk
- **Duration:** 1981s  **Words:** ~4813
- **Relevance:** SKIP — pure discretionary TradingView chart-tour commentary, no system, no signal, no code.
- **Core thesis:** Post-attack Oct 9 2023(?) market reactions — USDMXN still rallying, WTI range-bound, EURTRY as a "cleaner" safe-haven proxy, gold manipulated in USD but +63% in TRY terms. DXY/USDJPY/USDCHF as safe havens pending central-bank intervention.
- **Tools/tech:** TradingView only. Oanda CFDs referenced. No code.
- **Strategy / signal ideas:**
  - "Watch gold in Turkish lira to see the true move" — XAUTRY as a de-manipulated reference for gold.
  - Gold/Silver ratio as crisis indicator (weekly chart, spiked in 2008 and 2020, currently elevated vs 2008 under "normal" conditions = hidden crisis signal).
  - USDJPY drops = BoJ intervention incoming; wait it out and re-enter once BoJ steps in.
  - USDCHF SNB peg-break memory ("dropped 20% in one day").
  - "When things get risky, so does the dollar. It rallies. When the liquidity comes in, it drops back."
- **Numerical claims:** None statistically grounded. Price ranges mentioned narratively (e.g., WTI "$94, drops to 95 on last rally, then 4-5% rally"). No backtest or WR numbers.
- **Prompt snippets / AI usage:** None.
- **Architecture / code patterns:** None.
- **Risk / execution:** Warns about high spread on exotic FX (TRY, ZAR, CZK, SEK, DKK).
- **Novel-to-GTOS:** NO — discretionary commentary.
- **Verbatim quotes:**
  > "You want to get true moves of what you would expect from gold, go with gold and Turkish lira. So this is the one to watch to see what happens in the M East."
  > "When things get risky, so does the dollar. It rallies. When the liquidity comes in, it drops back."

---

### [3] I Tested AI Models to Code Trading Bots (The Results Will Shock You)
- **Video ID / URL:** zuZBI_ul5wM / https://youtube.com/watch?v=zuZBI_ul5wM
- **Duration:** 1496s  **Words:** ~3633
- **Relevance:** MEDIUM — LLM model comparison for trading-bot code generation is directly relevant to how GTOS budgets its Claude spend.
- **Core thesis:** Same prompt across Claude 4.6, Codex 5.3, GLM-5, MiniMax; Codex ~3x cheaper than Claude with comparable quality for "simple" Python trading bots; MiniMax breaks on 1500-line prompts; GLM-5 works but is slow. Declares "systematic portfolio manager" (picking top-2 live-performing bots and retiring losers hourly) as the new job.
- **Tools/tech mentioned:**
  - Claude 4.6 ("Enthropic"), Codex 5.3 (OpenAI), GLM-5 (ZAI), MiniMax, Qwen 3, "Deep Seek 4" (coming soon).
  - Rhythmic API (CME); keeps returning to his point that rhythmic's ToS blocks him sharing code.
  - OpenRouter (implied) — "I'm going through the equivalent of an open router."
  - Runs 8 bots live in a paper-trading simulation harness.
- **Strategy / signal ideas:**
  - Daily portfolio of bots: "Treasury regarding flag a federal stagflation type of trade... Bitcoin M6 May having call for momentum... Ethereum staking support with a put sell combination... COMEX gold geopolitical tail hedging... Horror moves breakout on oil... Natural gas EU gas cap reversion."
  - NGK "gas cap mean reverting strategy" — claims Sharpe 4.3 but with $36K drawdown (starting capital unstated, so ratio unverifiable).
  - Rotation protocol: run bots for 1-2 hours, pick top-2 by live P&L, drop the rest. Regenerate new batch per news cycle.
- **Numerical claims:**
  - "NX was driving a 4.3 sharp ratio... maximum drawdown of 36K" (NGK natural gas mean-rev).
  - "Bitcoin having momentum drew the most profit" (no number).
  - "Win ratios pretty good" — no specific %.
  - Cost: 1500-line prompt breaks MiniMax/Qwen 3. GLM-5 works but slow.
  - Cost context: "Codex is pretty well as good as Claude... generally three times on average more than Codex."
  - Pricing of his products: trial $67/mo going to $127/mo; hftcode.com $23/24 EUR going to ~$100 USD.
- **Prompt snippets / AI usage:** Says prompt is ~1500 lines with full news analysis PDF (41 pages) inlined. No verbatim text shown. Generates one Python bot per trade thesis.
- **Architecture / code patterns:** Workflow = daily news PDF -> LLM -> N Python bots -> paper-trading harness -> HTML report with per-bot Sharpe/DD/WR -> operator picks top-2 live. No code shown due to Rhythmic ToS.
- **Risk / execution:** "You want to always whatever you use, you want to make sure you have a cap, a hard cap. So when you stream or use AI that there's a limit and you cannot access and run the AI anymore because if you don't, you will easily, if you're doing it with Claude, you can easily run into the thousands per month."
- **Novel-to-GTOS:** MAYBE — two ideas worth flagging:
  1. **Hard cap on LLM spend** — we should confirm GTOS has a daily budget cap for Anthropic API. (Not explicitly documented in CLAUDE.md, though `api_refusal_monitor.py` exists.)
  2. **Multi-strategy paper-trading harness with live rotation** — conceptually interesting but probably overkill for single-edge GTOS; only relevant if we ever enable a second framework beyond ob_retest.
- **Verbatim quotes:**
  > "The only jobs that'll be left over are going to be systematic portfolio managers. This is what we're doing right now. So these systematic portfolio managers go 'what should be the only strategy I should be running for today?'"
  > "You can easily run into the thousands per month. Okay, that's something I would probably put down as a critical requirement running all these AIs, especially if it's parallelization or running it with agents."
  > "Codeex is pretty well as good as Claude... which is generally three times on average more than Codex. So, they're kind of neck and neck for this simpler type of trading."

---

### [4] How to Build an AI Algorithmic Trading Bot in 2026 (Python & Codex)
- **Video ID / URL:** uTvrqUWmvco / https://youtube.com/watch?v=uTvrqUWmvco
- **Duration:** 1055s  **Words:** ~3024
- **Relevance:** LOW — infrastructure demo (Rhythmic + Python + 8 bots + HTML reports). No concrete signal or strategy we can lift. Same themes as video [3].
- **Core thesis:** Demonstrates 8 live paper-trading bots against Rhythmic data, ranked by live WR. Declares Codex 5.3 his new favorite model ("blow me away"). Argues altcoins are dead due to stablecoin demand absorbing Bitcoin/ETH liquidity.
- **Tools/tech:** Rhythmic (Protobuf + customized C cert per account; requires per-user recompile), Python, Codex 5.3, MiniMax (breaking), Qwen 3 (errors), GLM (ok), Deep Seek 4 (awaited), Interactive Brokers (small acct). Runs on Linux.
- **Strategy / signal ideas:**
  - 6 live bots this session: GC/CL/ZB/ZN/NG/HG + silver. Best performers this run: GC "real rate fade" + ES "stagflation curve" (mean-reverting).
  - Claims "I don't think you really need any more backtesting because you could test like this, run it for an hour, run it for 2 hours, you know almost instantly which ones will be the most profitable."
  - Streaming market data -> "they will kill your system. They will conflict with each other because of the streaming. So, you're forced to only use snapshot data historical."
- **Numerical claims:**
  - "Silver one... most profitable... one hundred bucks a pop over the last couple hours" — n=2 fills for ES.
  - "ES has a 100% win ratio... 2 fills" (so WR meaningless at n=2).
  - Personal IBKR account: "+22% last week, then lost almost 10% in last few days on O [Osisko] and Philip Morris."
  - "2022-2023 I just sat in US dollar for the whole year and I got about 17% return."
- **Prompt snippets / AI usage:** Again says uses Codex via OpenRouter-equivalent. Emphasizes hard cap on spend. No verbatim prompts.
- **Architecture / code patterns:** 8-bot harness reports HTML (self-contained, embedded JS). Reddit-pattern (pub/sub) via Redis for client-server-strategy split — see video [6]. Bot trigger policy: "I purposely did further tests to see what would happen on the cost and the output quality of the code."
- **Risk / execution:** "Level 2 data" = bid/ask + OHLC. "Options right now only complicates the trading logic is what you don't want. You want to go step by step and as primitive as easy as possible."
- **Novel-to-GTOS:** NO — nothing that maps to OB-retest or GTOS architecture.
- **Verbatim quotes:**
  > "I don't think you really need any more backtesting because you could test like this. Run it for an hour. Run it for 2 hours. You know almost instantly which ones will be the most profitable."
  > "Altcoins are dead. Okay, there's no volume in altcoins anymore."

---

### [5] RIP TradingView? The New Chinese AI "Destroying" US Models (Miniax M2.1)
- **Video ID / URL:** VadK_ya6kh8 / https://youtube.com/watch?v=VadK_ya6kh8
- **Duration:** 1009s  **Words:** ~2394
- **Relevance:** MEDIUM — most concrete cost/quality comparison in the batch; also the PineScript/MQ5 -> Python conversion claim is directly relevant to GTOS research workflow.
- **Core thesis:** Same prompt run through Claude 4.6 Opus vs MiniMax M2.1 produces equivalent trading dashboards; MiniMax costs ~5% of Claude. Claims TradingView/MetaTrader are doomed because LLMs can convert PineScript and MQ5 into working Python in 5-10 minutes. CLI agentic tools (Claude Code, Gemini CLI, OpenAI Codex CLI) are "for beginners and vibe coders and they're getting slaughtered on cost."
- **Tools/tech mentioned:**
  - Claude 4.6 Opus vs MiniMax M2.1 (explicit A/B).
  - **Kilo Code** VS Code extension — generates code inline, changes files, supports multiple providers.
  - PineScript (TradingView) and MQ5 (MetaTrader) as conversion sources.
  - Python + JavaScript/HTML as outputs (HTML chosen over Streamlit because end-users can open HTML in a browser, self-contained — no env setup).
  - Rhythmic Trader Pro API; Redis pub/sub as message bus; .NET C# server acts as gateway.
  - Mentions "C++ compiler built by Claude across 11 agents cost $20,000" as a cautionary tale.
- **Strategy / signal ideas:**
  - Brent call/put straddle (20 contracts each, ATM +/- 5%) + short 40 Brent futures for market-neutral gamma harvesting. "For each 1% move in Brent we execute two additional future contracts in the direction of the move to capture gamma profit... yielding $8-12K in gamma profit per 1% move on a half a million dollar notional options position."
- **Numerical claims:**
  - "Sharpe ratio 1.87, max drawdown -11% (15% is good), win ratio 74%, profit factor 3.12, hold 18 days, capture high volatility at 67%" — for AI-generated Brent straddle.
  - "Claude dashboard: $1 cost, 29,000 points."
  - "MiniMax equivalent: 5% of that cost" for same dashboard.
  - "PineScript -> Python conversion in 5 minutes with two-line prompt, one error to fix, 5-10 minutes total."
  - "MQ5 200-line conversion to Python: 5-10 minutes."
- **Prompt snippets / AI usage:** "Two-line prompt" to convert PineScript. Also: "I ask for any quote unquote secretive unknown algorithms in Python" — interesting lazy prompt-injection pattern.
- **Architecture / code patterns:**
  - Pub/sub via Redis between Python strategies and a C#/.NET gateway that wraps Rhythmic API.
  - Claims Kilo avoids "agentic auto-run" costs by keeping the loop in-editor.
- **Risk / execution:** Emphasis on options for "virtually unlimited profit potential + downside protection" — same thesis as [1].
- **Novel-to-GTOS:** MAYBE — one practical action:
  - **Test MiniMax / GLM as research-only helpers.** For offline, non-production tasks (e.g., converting external PineScript indicators we want to benchmark), a cheap Chinese model may be adequate. This is research-workflow only, not a change to the production Sonnet 4.6 gate (per our memory: Sonnet beats Opus on MSO gate empirically).
  - **Risk:** his "5% cost" claim is unverified and may not hold for our max-effort prompts. Would need our own head-to-head test.
- **Verbatim quotes:**
  > "Here's the difference in cost. So here when you factor in the cost of this dashboard in Claude... it's 29,000 points. Meanwhile, to generate the equivalent of what I just showed you in Miniax it's about 5% of this."
  > "These CLI tools are meant for like beginners vibe coders and they're getting slaughtered on cost. They don't even know it. All because they don't go out and input and learn the basics of programming."
  > "I spent five days kind of wasted my time generating different types of dashboards... So I kept it very prim and proper, very simple to a point where I'm very comfortable call them trading bots because that's kind of what they are."

---

### [6] Building an HFT System with AI: Claude 4.5 vs Gemini 3 Workflow (2026 Demo)
- **Video ID / URL:** HOcMdzbJhfU / https://youtube.com/watch?v=HOcMdzbJhfU
- **Duration:** 540s  **Words:** ~1347
- **Relevance:** LOW — demo of his four-process Rhythmic harness (VWAP + MACD-mean-rev + OU clients + .NET server). Useful only as a data point that Claude 4.5 beat Gemini 3 Pro on his C# debugging task.
- **Core thesis:** Demos multi-client-server architecture (.NET C# server + 3 Python strategy clients via Redis pub/sub). Says Claude 4.5 is "way better quality in terms of debugging and to actually build more complicated projects" but context-window truncation hurts on multi-file projects. Gemini 3 Pro only good for simple scaffolding.
- **Tools/tech:**
  - Claude 4.5 and Gemini 3 Pro as code generators.
  - Google Anti-Gravity IDE (wants to try).
  - Con EMU (terminal multiplexer) for displaying multiple PowerShell sessions.
  - .NET C# for the server; Python for strategy clients.
  - Redis pub/sub; Rhythmic Pro (test env) with a "block all orders" safety flag.
- **Strategy / signal ideas (named, no detail):**
  - **OU strategy** (Ornstein-Uhlenbeck mean reversion) — client 1, focused on ES/NQ.
  - **MACD mean reversion** — client 2.
  - **VWAP** — client 3, on oil.
  - No parameters, no performance, no code shown.
- **Numerical claims:** None.
- **Prompt snippets / AI usage:** None verbatim. Pattern: Gemini 3 Pro for scaffolding, Claude 4.5 for multi-file debugging.
- **Architecture / code patterns:**
  - **Safety flag in server: block all orders regardless of signal** — Brian says this is critical because test env (Rhythmic Test) and prod env (Rhythmic 01, Chicago) share the same code path. If the flag isn't set and you accidentally point at prod, you lose real money fast. Design pattern worth noting for GTOS: a top-level `deployment.phase` flag similar to ours (we have `deployment.phase: 2` paper trading).
  - Context window management: "With a larger project with five C# files... the context loses the history of the original file context. So as you debug, new code will be generated and will replace the older code. So you have to retain that code in place."
- **Risk / execution:** The block-orders flag is the takeaway. Otherwise just marketing.
- **Novel-to-GTOS:** NO — GTOS already has `deployment.phase` for paper vs live. OU and MACD-MR are named but not developed into testable signals.
- **Verbatim quotes:**
  > "Claude 4.5 is just way better quality in terms of debugging and to actually build more complicated projects. Gemini 3 Pro is more to lay down a simple project, get it working."
  > "I put in the Rhythmic server edition a parameter where it will block orders. So if there's any orders triggered, it'll block them... because this is important to know is that when you have against a a live environment like the rhythmic 01 production... you could lose a lot of money very quickly."

---

### [7] Quant Analytics: 2026 Future and Option Market Forecasts
- **Video ID / URL:** A1B2R-mfmYg / https://youtube.com/watch?v=A1B2R-mfmYg
- **Duration:** 270s  **Words:** ~858
- **Relevance:** LOW — 4.5-minute AI-narrated promo video with a sci-fi-trailer tone. Describes the same news-filter concept without any implementation detail.
- **Core thesis:** A news-filtering "machine" ingests 16 feeds, culls to 5 high-signal sources, extracts drivers, spits price forecasts. The splashy number: **gold to $5,100/oz**.
- **Tools/tech:** Unspecified AI system. References Bloomberg, CNBC, FT as sources.
- **Strategy / signal ideas:**
  - **Four-step method:** scan -> isolate 5 key signal sources -> extract drivers -> forecast prices.
  - Current-regime drivers claimed: USD weakening, deep-freeze energy crisis, crypto inflows, Venezuelan oil geopolitics.
- **Numerical claims:**
  - Gold target $5,100/oz.
  - Silver target $130.
  - Natural gas up to $850.
  - Bitcoin "past $100,000 later in the year."
  - No sample size, no methodology, no backtest. Pure forecast marketing.
- **Prompt snippets / AI usage:** None.
- **Architecture / code patterns:** "Started with 16 feeds, kept 5" — the only concrete pattern, but without knowing which 5, unusable.
- **Risk / execution:** None mentioned.
- **Novel-to-GTOS:** NO — this is promotional narration over the dashboard content covered in [1], [3], [4], [5].
- **Verbatim quotes:**
  > "First, it scans pretty much everything. Then step two, it isolates those five key signal sources. After that, it digs into the news from those sources to figure out what's really driving the market."
  > "$5,000... that's the price this AI-driven system is forecasting for a single ounce of gold."

---

## Cross-batch pattern notes (for the synthesis agent)

1. **Recurring "news -> AI -> dashboard -> bots" pipeline.** Every substantive video in this batch is a variant of: (a) collect 24h news, (b) summarize to PDF, (c) inline PDF into ~1500-line prompt, (d) LLM emits ranked trade ideas with projected Sharpe/WR/DD, (e) LLM emits one Python bot per idea, (f) all bots run paper-trade against Rhythmic snapshot data, (g) operator picks top-2 by live P&L. GTOS has none of this; it is architecturally orthogonal (single-edge, OB-retest, M15 candle close, deterministic gate).
2. **No statistical rigor.** Every Sharpe/WR/DD number cited is AI-projected (prompt-level), not backtested. Sample sizes are never given. The "82% WR" headline is AI-generated from news, not from any historical test. Treat all figures in this batch as marketing.
3. **Cost-of-LLM anxiety.** Brian's top fear across videos is blowing API budget. His advice — hard caps, prefer Codex/MiniMax for research — aligns with our own memory note about Sonnet being cheaper than Opus on the live gate. Worth confirming GTOS has an Anthropic spend cap.
4. **No MT5/forex content.** He's almost entirely CME futures + crypto perps + options. He actively dismisses MT5/TradingView as "doomed." Nothing in the batch is a direct signal for GTOS instruments (XAUUSD, US30, USDJPY, GBPJPY, GBPUSD).
5. **One stealth-useful concept:** the "block all orders" flag as a hard guardrail separate from environment config (video [6]). GTOS has `deployment.phase` but it may be worth auditing that prod vs paper really is a hard circuit-breaker, not just a config switch.
