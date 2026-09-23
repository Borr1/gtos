# Gold Trading Agent — Master Roadmap
## Updated April 2, 2026

---

## Phase 0: Validate & Go Live (THIS WEEK)

**Gate: Replay blitz shows positive expectancy + demo executes 1-2 clean trades**

### Already Done
- [x] Edge validated: 101 trades, 69.3% WR, +0.235R, p=0.014, durable across 7/8 quarters
- [x] Confidence scorer built (shadow mode): price_level_count >= 8 splits WR by 17.4%
- [x] Breaker block detection built + integrated into PA prompt
- [x] Extended London KZ (07:00-10:30) deployed
- [x] causing_event_type added to PA schema
- [x] Demo deployed on Windows MT5
- [x] Batch test with breaker blocks: ob_retest 88% WR on fresh data, 2 breaker trades found (both losses, n=2 meaningless)
- [x] Tick volume killed (no signal)
- [x] 401 tests passing

### In Progress
- [ ] Replay blitz running (results pending)
- [ ] Batch with breaker blocks processing

### Remaining This Week
- [ ] Review replay blitz results — GO/NO-GO decision
- [ ] Demo runs Wed-Fri, confirm 1-2 clean MT5 executions (order, partial close, SL modify)
- [ ] Select prop firm (requirements: $100K, allows EAs, XAUUSD available, 8-10% target, no/generous time limit)
- [ ] Set up prop firm account, verify symbol name, configure agent
- [ ] Pre-flight checklist: API key on production billing, correct MAGIC_NUMBER, circuit breakers match prop firm rules (set tighter)
- [ ] Decision: breaker_retest enabled or shadow-only for funded launch

### Monday: Go Live
- `python run_agent.py --mode live`
- Monitor first 2-3 sessions closely
- Expected: 3-6 trades/month at +0.22R to +0.66R expectancy

---

## Phase 1: Deepen the Edge on XAUUSD (Weeks 2-4)

**Gate: Phase 0 producing live trades without execution bugs**

**Goal: Increase frequency from 5/month to 8-10/month on gold alone, and improve per-trade quality**

### 1A. H4 OB Retest Strategy
- Same framework as ob_retest but one timeframe higher
- H4 OB zone + H1 CHoCH confirmation (instead of H1 OB + M15 CHoCH)
- Longer holding period, bigger moves (3-5R winners vs 1-2R)
- Expected frequency: 2-3 swing trades/month
- Implementation: prompt addition (similar to breaker block integration), Component 2 already computes H4 OBs
- Cost to test: ~$10-15 batch run
- **This is the single highest-value frequency addition because it uses the same proven logic on a higher timeframe**

### 1B. DXY Correlation Layer
- Add DXY (US Dollar Index) daily data to the MSO
- DXY data available free from MT5 — just export alongside XAUUSD
- Add to PA prompt: "DXY daily bias is [bullish/bearish/ranging]. Does this support or conflict with the XAUUSD trade thesis?"
- Gold and DXY have strong inverse correlation — bullish gold + bearish DXY = higher conviction
- Implementation: data ingestion addition + one prompt section
- No separate backtest needed — add it to the MSO and let the AI use it as confluence
- **This doesn't add trades but improves confidence on existing trades — the AI has fundamental context for WHY institutional flow is happening**

### 1C. Asian Range Width Filter
- Compute Asian session range (00:00-07:00 UTC high minus low) as percentage of 20-day ADR
- Narrow Asian range (< 50% of ADR) historically predicts larger London moves
- Wide Asian range (> 80% of ADR) predicts London consolidation
- Purely deterministic — add to pre-screen or use for position sizing
- Cost to validate: free (run against historical data)
- Implementation: one function in data_ingestion, one line in pre-screen or confidence scorer
- **This could recover some of the 51% of trading days currently killed by pre-screening**

### 1D. Breaker Block Refinement
- Based on replay blitz and batch results, decide: keep, refine, or kill
- If keeping: analyze which breaker block characteristics predict wins (zone tightness, displacement quality on mitigation, time since mitigation)
- If killing: remove from prompt to reduce complexity
- Decision requires 20+ breaker block trades — may need a dedicated batch run on the full date range

### 1E. Pre-Screen Loosening Investigation
- 133 of 259 weekdays killed by "D1 ranging/unclear" in latest batch
- Run analysis: on killed dates, did H1/M15 have tradeable structure anyway?
- If yes for 20%+ of killed dates: the pre-screen is too aggressive and we're leaving money on the table
- Potential fix: allow "D1 ranging" dates but require stronger H4+H1 confluence
- Cost to investigate: free analysis on existing data, ~$15 batch run to test loosened filter

---

## Phase 2: Multi-Market Intelligence (Weeks 4-8)

**Gate: Phase 1 strategies validated, live system running stable for 2+ weeks**

**Goal: Transform from single-instrument trader to multi-market system. Target 15-20 trades/month.**

### 2A. EURUSD Expansion (First New Instrument)
- Export data from MT5 (already planned, 10 minutes)
- Run ob_retest backtest with ATR recalibration only
- EURUSD has similar London open dynamics to gold (Asian-to-European handoff)
- If validates: add to live system, separate position limits
- Expected: +3-5 trades/month
- Cost: ~$25-40 backtest

### 2B. Cross-Market Correlation Dashboard
- Ingest DXY, US10Y (10-year treasury yield), SPX (S&P 500) daily data alongside XAUUSD
- Build correlation matrix: when DXY is bearish + US10Y dropping + SPX risk-off → gold has highest probability of strong bullish setups
- Don't trade these instruments — use them as CONTEXT for gold and EURUSD trades
- Implementation: data ingestion expansion + MSO enrichment + prompt section
- **This is genuinely AI-native — no human trader monitors 4 markets simultaneously and processes correlations in real time on every candle**

### 2C. Macro Event Integration
- Economic calendar data already architected in Component 1 (MT5 provides it)
- Wire it into the PA prompt: "FOMC rate decision in 4 hours — high-impact USD event"
- Two modes: AVOID (don't enter new trades within 2 hours of high-impact events) or EXPLOIT (after the event, look for the liquidity sweep + displacement pattern that commonly follows)
- Start with AVOID mode (reduce risk), research EXPLOIT mode with backtesting
- **FOMC/NFP/CPI days produce the biggest gold moves of the month — currently we treat them the same as any other day**

### 2D. Correlation-Aware Position Sizing
- When XAUUSD and EURUSD both signal LONG simultaneously (both driven by dollar weakness), reduce position size on each to avoid concentrated USD exposure
- When signals are uncorrelated (gold safe-haven bid + EUR weakness), full size on both
- Implementation: portfolio-level position sizing in the orchestrator
- Requires: correlation data from 2B

---

## Phase 3: Multi-Agent Architecture (Months 2-3)

**Gate: 2+ instruments live, 15+ trades/month, positive expectancy confirmed over 50+ live trades**

**Goal: Move from "one AI doing everything" to specialized sub-agents. Target 20-30 trades/month.**

### 3A. Specialized Sub-Agents
Three agents evaluate the same MSO simultaneously with different mandates:

**Trend Agent (current system, refined)**
- ob_retest + H4 OB retest + breaker blocks
- Only trades WITH the established H4/D1 trend
- Conservative: high WR, moderate RR

**Reversal Agent (new)**
- Looks for setups at major H4/D1 structural levels where trend exhaustion is likely
- Requires: H4 liquidity sweep + D1 resistance/support + displacement away from the level
- Trades AGAINST the trend but only at key levels with strong confirmation
- Aggressive: lower WR, high RR (3-5R targets)

**Momentum Agent (new)**
- Evaluates pure displacement quality and session momentum
- After a strong displacement move, enters on the first clean pullback
- Doesn't need OB or breaker block — just displacement + pullback + continuation
- Higher frequency, lower conviction per trade

**Orchestrator logic:** Each agent outputs its assessment independently. The system takes a trade only when at least 2 of 3 agents agree on direction. When all 3 agree, maximum position size. When only 2 agree, reduced size.

### 3B. Discretionary Mode
- Give the AI the full MSO without framework constraints
- Prompt: "Based on all available structure, liquidity, and session data, is there ANY high-probability trade setup? Explain your reasoning and identify which framework it most closely resembles."
- Run in shadow mode alongside the framework-based system
- Track: does discretionary mode find setups the framework misses? What's the hit rate?
- **This is the most AI-native approach — leveraging the LLM's training on millions of trading discussions instead of constraining it to our predefined checklist**

### 3C. Adaptive Prompt Injection
- After 100+ live trades with confidence scorer data, inject the system's own performance stats into the prompt
- "Your historical accuracy on London ob_retest is 74%. Trades where you cited 8+ price levels won 75% of the time. Trades where you used 3+ hesitation phrases won 60%."
- The AI gets calibration data about its own track record — meta-learning
- Only safe to deploy after large sample size to avoid overfitting

### 3D. Ensemble Evaluation
- Run each CANDIDATE through the PA 3 times at temperature 0.4
- Disagreement rate becomes a mechanical confidence measure
- Only deploy if reasoning text mining proves insufficient as a confidence proxy
- Cost: negligible ($0.10-0.30/month on CANDIDATEs only)

---

## Phase 4: Scale (Months 3-6)

**Gate: 50+ live trades with positive expectancy, execution pipeline proven, multiple strategies validated**

### 4A. Additional Instruments
- XAGUSD (silver — correlated to gold, add carefully with correlation-aware sizing)
- NAS100 (if ob_retest validates — different microstructure, needs independent testing)
- GBPUSD (London session overlap, strong institutional patterns)
- Each instrument: ~$30-40 backtest + 2 weeks demo validation

### 4B. Multiple Prop Firm Accounts
- Scale to 3-5 funded accounts across different firms
- Same system, same strategies, different capital pools
- At 15-20 trades/month with +0.30R expectancy on $100K accounts: $4,500-6,000/month per account
- 3-5 accounts: $13,500-30,000/month

### 4C. Bayesian Scoring Engine
- After 200+ trades with full feature data (confidence metrics, framework, KZ, regime, DXY correlation)
- Replace heuristic confidence scoring with empirical P(WIN | conditions)
- Continuously updated as new trades flow in
- The ultimate version of the confidence proxy — trained on your own data, not general assumptions

### 4D. Telegram Alerting + Remote Monitoring
- Subscribe to orchestrator events
- Trade opened/closed alerts
- Daily P&L summary
- Circuit breaker notifications
- System health checks

---

## Architecture Vision: What This Becomes

```
                    ┌─────────────────────────────────┐
                    │     MULTI-MARKET DATA LAYER      │
                    │  XAUUSD · EURUSD · DXY · US10Y  │
                    │  SPX · Economic Calendar         │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │    ENRICHED MARKET STATE (MSO)    │
                    │  Structure · OBs · Breakers ·    │
                    │  FVGs · Liquidity · Correlations │
                    │  Asian Range · Regime · DXY Bias │
                    └──────────────┬──────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
     ┌────────▼───────┐  ┌────────▼───────┐  ┌─────────▼──────┐
     │  TREND AGENT    │  │ REVERSAL AGENT │  │ MOMENTUM AGENT │
     │  ob_retest      │  │ H4/D1 levels   │  │ displacement   │
     │  H4 OB retest   │  │ exhaustion     │  │ pullback       │
     │  breaker retest │  │ reversal       │  │ continuation   │
     └────────┬───────┘  └────────┬───────┘  └─────────┬──────┘
              │                    │                     │
              └────────────────────┼────────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      CONSENSUS ENGINE            │
                    │  2/3 agree → trade               │
                    │  3/3 agree → full size            │
                    │  Correlation-aware sizing         │
                    │  Confidence scoring (Bayesian)    │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      EXECUTION LAYER             │
                    │  MT5 · Safety gates · Circuit    │
                    │  breakers · Partial closes ·     │
                    │  Crash recovery · Audit trail    │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      LEARNING LAYER              │
                    │  Reasoning text mining ·         │
                    │  Adaptive prompt injection ·     │
                    │  Bayesian scoring · Performance  │
                    │  attribution by agent/strategy   │
                    └─────────────────────────────────┘
```

---

## Revenue Projections (Conservative → Optimistic)

| Timeline | Trades/Month | Expectancy | Monthly Revenue (per $100K account) |
|----------|-------------|------------|--------------------------------------|
| Month 1 (Phase 0) | 3-5 | +0.22R | $660-1,100 |
| Month 2 (Phase 1) | 6-10 | +0.25R | $1,500-2,500 |
| Month 3 (Phase 2) | 10-15 | +0.30R | $3,000-4,500 |
| Month 4+ (Phase 3) | 15-25 | +0.30R | $4,500-7,500 |
| Scaled (3 accounts) | 15-25 | +0.30R | $13,500-22,500 |

These use the CONSERVATIVE floor for expectancy. Replay data with session memory showed +0.66R which would roughly double these numbers. Plan on the floor, be surprised by the upside.

---

## Decision Log

| Date | Decision | Reasoning |
|------|----------|-----------|
| Apr 1 | Kill session_sweep | 81 trades, -0.051R, confirmed loser |
| Apr 1 | Kill equal_sweep | 1 trade in 2 years |
| Apr 1 | Kill fvg_fill | 0 trades in 2 years |
| Apr 1 | Kill vision mode | -4.87R swing vs JSON-only |
| Apr 1 | Kill tick volume | No signal differentiating winners/losers |
| Apr 1 | Confirm ob_retest | 101 trades, p=0.014, durable 7/8 quarters |
| Apr 1 | Confirm session memory | +0.66R vs +0.33R, doubles expectancy |
| Apr 1 | Extend London to 10:30 | Natural continuation of 82.8% WR late window |
| Apr 1 | Build breaker blocks | 10.4 KZ retests/month, promising frequency |
| Apr 1 | Confidence proxies | price_level_count >= 8 splits WR by 17.4% |
| Apr 2 | Pending: replay blitz | GO/NO-GO for funded account |
| Apr 2 | Pending: breaker blocks | Keep/refine/kill based on sample size |
