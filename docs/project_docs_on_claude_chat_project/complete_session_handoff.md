# Gold Trading Agent — Complete Session Handoff
# Date: April 1, 2026
# For: New Claude session to continue deployment

---

## WHO YOU'RE WORKING WITH

Borhen. 6+ years coding (TypeScript primary, Python comfortable). Developing SMC/ICT trader. Building a fully autonomous AI trading agent for XAUUSD (gold). Wants brutal honesty, no sugarcoating. Pushes back on reasoning errors. Budget-conscious. On Claude Max 5x ($100/month). Goal: disciplined, independent gold trader with AI system → prop firm funded accounts → multi-instrument scaling.

Act as his strategic trading mentor, technical architect, and research advisor. Be direct. Challenge sloppy reasoning. Don't give vague motivational fluff. Think like an autonomous system architect, not a small retail trader.

---

## PROJECT OVERVIEW

An autonomous XAUUSD trading agent that uses Claude as its AI reasoning engine. The system evaluates M15 candle closes during London (07:00-09:30 UTC) and NY (13:00-15:30 UTC) kill zones, identifies H1 order block retest setups after structural breaks, and executes trades with partial close management.

**Tech stack:** Python, ~16,000 lines across 35+ files, 367 tests passing. Anthropic Claude API (Sonnet for backtesting, Opus planned for live). MetaTrader 5 for execution. File-on-disk pipeline with Pydantic models. LanceDB for vector similarity search.

---

## WHAT WAS BUILT TODAY (March 31 → April 1, 2026)

### Session 1-2: Data Analysis + System Restructure
- Analyzed 91 backtest trades. Discovered session_sweep framework had NEGATIVE expectancy (-0.051R/trade, 81 trades) while ob_retest had +0.900R/trade (9 trades, 100% WR)
- session_sweep + London was the #1 value destroyer: -8.80R across 55 trades
- Root cause: session_sweep requires the AI to judge "sweep vs breakdown" from JSON numbers — an inherently ambiguous visual judgment. ob_retest asks "is price at the OB zone after a structural break?" — a numeric check the AI handles well
- Found 1,449 near-misses where ob_retest had CHoCH but not BOS
- **Critical fix in Component 2 (market_state.py):** Order blocks were only generated from BOS events. Modified `identify_order_blocks()` to also create OBs from CHoCH events. Added `causing_event_type` field to OrderBlock model
- Rewrote Primary Analyzer prompt: removed frameworks 3+4 (equal_sweep, fvg_fill — zero trades ever), relaxed ob_retest from BOS-only to CHoCH+BOS, added kill zone rules, confidence scoring rubric, session_sweep restricted to NY A+ only
- Added MFE/MAE tracking to outcome simulation
- Min RR aligned to 2.5 across prompt, safety checks, and config

### Session 3: Validation Batch
- Ran full date range (Apr 2024 – Mar 2026) on restructured system
- **Results: 111 trades, 64.9% WR, +22.17R total, +0.200R expectancy, p=0.046**
- ob_retest: 101 trades, p=0.014, CI [+0.056R, +0.420R] — CI excludes zero
- ob_retest London: 58 trades, 74.1% WR, +11.24R — London went from biggest loser to biggest winner
- session_sweep (NY A+ only): 10 trades, 20% WR, -1.52R — still losing
- Confidence scoring: still broken (105/111 at 80, 6 at 75)
- **First confirmed statistical edge in the project**

### Session 4: Final Pre-Demo Optimization
- Killed session_sweep entirely (10 trades, 20% WR, confirmed loser even with restrictions)
- Prompt reduced from 12,340 → 9,420 chars (-24%), single framework
- TP optimization analysis: every fixed TP1 override performs WORSE than AI-set targets with partial closes. Current TP structure preserved.
- Session timeout policy: trailing with BE stop for 2 hours adds +0.167R/trade. 57% of timeouts continue favorably. Policy defined for live implementation.
- Smoke test: 5 trades, 100% WR, +5.29R, all ob_retest, zero session_sweep leakage
- 272 tests passing after session_sweep removal

### Session 5: Chart Vision A/B Test
- Built chart renderer (Plotly, TradingView-style dark theme, OB zones, session levels annotated)
- Added --vision flag to batch pipeline
- Ran A/B test: JSON-only vs JSON+Chart on same dates
- **Vision HURTS performance:** WR dropped from 100% to 66.7%, -4.87R swing on shared trades
- Verified images were correctly rendered, encoded, and received by Claude (3,366 vs 1,490 tokens/request)
- **Decision: JSON-only is production configuration. Vision rejected.**
- 277 tests passing

### Sprint 1: Live Pipeline Build
- Built Component 1 (data ingestion): live MT5 data → MSO-compatible format
- Built Component 4 (execution engine): safe_place_order with check-before-retry, partial closes (50% TP1, 25% TP2, 25% runner), ticket tracking after partial close, SL modification with failsafe close, crash recovery (orphan/phantom detection)
- Built Component 8 (session orchestrator): M15 candle loop, dual KZ management, session memory injection, pre-screening, PID locking, signal handlers, clean shutdown
- Built MT5 abstraction (interface + mock + real): MockMT5 simulates fills, partial close ticket changes, SLTP modifications
- Built permissions module: Gate 1 (safety checks) + Gate 3 (circuit breakers)
- Session memory: sliding window of 6 candle summaries per KZ, injected into dynamic context before H1/M15 data
- Entry point: run_agent.py --mode mock/demo/live
- **367 tests passing (277 original + 90 new)**

### Sprint 1.5: Historical Replay Validation
- Built replay_session.py: runs historical dates through the live pipeline sequentially with session memory
- Replayed 30 Tier 1 dates (dates where ob_retest traded in batch)
- **Replay results: 17 trades, 70.6% WR, +11.21R, +0.66R expectancy**
- **Batch comparison: 36 trades on same dates, 72.2% WR, +11.87R, +0.33R expectancy**
- Session memory makes the system MORE SELECTIVE: half the trades, double the expectancy, 95% of the R
- Key flip: 2025-02-12 batch LOSS -1.00R → replay WIN +2.73R (session memory improved entry timing)
- **Decision: Session memory ENABLED for production**

---

## CURRENT SYSTEM CONFIGURATION (LOCKED)

```
Framework:          ob_retest only (CHoCH + BOS)
Kill zones:         London (07:00-09:30 UTC) + NY (13:00-15:30 UTC)
Grade filter:       A+ and A
Min RR:             2.5
TP structure:       AI-set structural targets, 50%/25%/25% partial closes
SL:                 >= max($5.00, 1.5x M15 ATR)
Input:              JSON-only (vision tested and rejected)
Session memory:     ENABLED (sliding window of 6 candle summaries per KZ)
Timeout policy:     Trail with BE stop for 2h after session end
Model (backtest):   Sonnet via Batch API
Model (live):       Opus (max accuracy, ~$0.80/day)
Edge:               p=0.046 (batch), +0.66R/trade (replay with session memory)
Frequency:          ~2-3 trades/month per instrument
Prompt size:        9,420 chars (~2,355 tokens)
Tests:              367 passing
```

---

## CURRENT STATUS: DEPLOYING TO WINDOWS FOR MT5 DEMO

The codebase is on the Windows machine at `~/Documents/ai-trading-agent`. MT5 is installed. Claude Code is available on Windows via the desktop app.

### What's happening RIGHT NOW

Borhen is about to run the Windows deployment prompt through Claude Code on the Windows machine. This prompt:
1. Verifies Python + MetaTrader5 package + dependencies
2. Catches and fixes a CRITICAL BUG: MT5 timeframe constants (H1=16385 not 60, H4=16388 not 240, D1=16408 not 1440)
3. Tests real MT5 connection → data ingestion → MSO computation → pre-screen → Primary Analyzer
4. Launches `python run_agent.py --mode demo` for tonight's NY session

### The MT5 Timeframe Bug (MUST BE FIXED)

In `src/components/data_ingestion.py`, the timeframe constants are likely hardcoded as:
```python
TF_H1 = 60      # WRONG — MT5 uses 16385
TF_H4 = 240     # WRONG — MT5 uses 16388
TF_D1 = 1440    # WRONG — MT5 uses 16408
TF_M15 = 15     # This one happens to be correct
```

The fix:
```python
try:
    import MetaTrader5 as _mt5
    TF_M15 = _mt5.TIMEFRAME_M15
    TF_H1 = _mt5.TIMEFRAME_H1
    TF_H4 = _mt5.TIMEFRAME_H4
    TF_D1 = _mt5.TIMEFRAME_D1
except ImportError:
    TF_M15 = 15
    TF_H1 = 16385
    TF_H4 = 16388
    TF_D1 = 16408
```

### Other Potential Integration Issues

- `compute_session_levels()` in data_ingestion.py might still be a stub (`pass`) — needs to replicate the logic from `scripts/historical_data_loader.py`
- MT5 returns Unix timestamps; the conversion to ISO strings must use UTC (not local time)
- MT5 candle field access: `copy_rates_from_pos` returns numpy structured arrays — verify field mapping in `mt5_real.py`
- XAUUSD symbol name might differ per broker: could be "GOLD", "XAUUSDm", "XAUUSD.a"
- The `equal_highs_H4`, `equal_lows_H4` etc. fields expected by `compute_market_state()` — verify data_ingestion includes them

---

## ARCHITECTURE SUMMARY

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/components/market_state.py` | 633 | Deterministic MSO builder (swings, structure, OBs from BOS+CHoCH, FVGs, sweeps) |
| `src/components/primary_analyzer.py` | 409 | AI reasoning engine, calls Claude API |
| `src/prompts/primary_analyzer_prompt.py` | ~400 | System prompt + user message builder |
| `src/components/orchestrator.py` | ~500 | Session orchestrator: candle loop, dual KZ, session memory |
| `src/components/execution.py` | ~470 | Execution engine: safe_place_order, partial closes, crash recovery |
| `src/components/data_ingestion.py` | ~220 | Live MT5 data → MSO-compatible format |
| `src/components/permissions.py` | ~120 | Gate 1 (safety checks) + Gate 3 (circuit breakers) |
| `src/mt5/mt5_interface.py` | ~100 | Abstract MT5 interface |
| `src/mt5/mt5_mock.py` | ~130 | Mock for development/testing |
| `src/mt5/mt5_real.py` | ~100 | Real MT5 connection (Windows only) |
| `scripts/batch_backtest.py` | 1038 | Batch API backtester |
| `scripts/backtest_runner.py` | 1115 | Sequential backtester + outcome simulation |
| `scripts/replay_session.py` | ~800 | Historical replay with session memory |
| `run_agent.py` | ~30 | Entry point |
| `config/agent_config.yaml` | 96 | All configuration |

### Pipeline Flow (Live)

```
M15 candle close within kill zone
  → Data Ingestion (MT5 → raw_data dict)
  → Market State Analyzer (raw_data → MSO)
  → Pre-screen (D1 bias clear? H4 aligned? If no → skip Claude call)
  → Primary Analyzer (MSO + session memory → Claude API → CANDIDATE/NO_TRADE)
  → Update session memory (sliding window of 6)
  → If CANDIDATE: Permission check (Gate 3 circuit breakers → Gate 1 safety checks)
  → If approved: Execution Engine (safe_place_order → MT5 order)
  → Trade management (TP1 partial → SL to BE → TP2 partial → trail runner)
  → Session timeout: BE stop for 2 hours
```

### Safety Checks (Gate 1)
- Grade must be A+ or A
- Direction must match D1 bias
- RR >= 2.5
- SL >= $5.00
- SL >= 1.5x M15 ATR

### Circuit Breakers (Gate 3)
- Daily loss >= 2% → block all trading
- Max trades per day: 2 (1 per KZ)
- Max trades per KZ: 1
- MT5 disconnected → block
- Spread > 30 cents → block

### safe_place_order() — Critical Safety Pattern
1. Write checkpoint to disk (intent record)
2. Send order with 10-second timeout wrapper
3. If timeout: sleep 2 seconds, query MT5 positions
4. If position found (order filled despite timeout): adopt it
5. If no position: give up, DO NOT RETRY
6. Clear checkpoint after completion
7. NEVER retry without checking positions first (prevents duplicate orders)

### Partial Close Mechanics (MT5-specific)
- Partial close CHANGES THE TICKET NUMBER on MT5
- After each partial close: query positions to discover new ticket
- Re-apply SL/TP on the new ticket (they don't carry over)
- If SL modification fails: close entire position immediately (no position without a stop)
- Use MAGIC_NUMBER (20260401) to filter positions to this agent only

---

## VALIDATED DECISIONS (WITH DATA)

| Decision | Result | Evidence |
|----------|--------|----------|
| Kill session_sweep | ✅ Confirmed loser | 81 trades -0.051R, 10 trades post-restriction -0.152R |
| ob_retest as primary | ✅ Confirmed edge | 101 trades, 65% WR, +0.22R, p=0.014 |
| CHoCH relaxation | ✅ Unlocked volume | 9 trades → 101 trades (from Component 2 OB fix) |
| Remove frameworks 3+4 | ✅ Zero trades ever | equal_sweep: 1 trade total, fvg_fill: 0 trades |
| Vision (chart images) | ❌ Hurts performance | -4.87R swing, verified images delivered correctly |
| Session memory | ✅ Doubles expectancy | +0.66R/trade vs +0.33R/trade, half the trades, 95% of R |
| TP optimization | ❌ Don't change | Every fixed TP1 override worse than AI-set + partial closes |
| Timeout trailing | ✅ +0.167R/trade | 57% continue favorably, avg post-timeout MFE > MAE |
| Min RR 2.5 (not 3.0) | ✅ More opportunities | Aligned across prompt, safety checks, config |
| Confidence scoring | ⚠️ Still broken | Constant 80, rubric doesn't work, not blocking for demo |

---

## WHAT COMES AFTER DEMO DEPLOYMENT

### Demo Phase (3-4 weeks)
- Target: 15-20 trades on MT5 demo account
- Compare results to backtest: WR should be 55%+, expectancy +0.10R+
- Session memory should improve accuracy vs backtest (conservative floor)
- Live costs: ~$25/month (Opus at $0.80/day)

### If Demo Validates
- First prop firm challenge ($100K funded, ~$500 entry fee)
- At moderate scenario (+0.40R/trade, 3 trades/month): 8% target in ~7 months
- Multi-instrument expansion: NAS100, EURUSD, XAGUSD (~$30-40 validation each)
- ob_retest framework is market-agnostic — same logic, different ATR calibration
- Scale to 3-5 funded accounts: $4,000-10,000/month at moderate-optimistic scenarios

### Future Improvements (During/After Demo)
- Verification agent in shadow mode (Opus on CANDIDATEs only, logs verdicts, doesn't block)
- Bayesian scoring engine after 200+ trades (replace broken confidence with empirical P(WIN | conditions))
- Aggressive BE move at +0.5R MFE (could flip near-miss losers)
- Multi-instrument data feeds
- Telegram alerting for remote monitoring
- Full checkpoint/WAL system for production hardening

---

## STANDING PRINCIPLES
- Never re-run in-sample data to validate fixes — use fresh data
- The backtest without session memory is a conservative floor
- Each improvement must be tested before the next starts
- Vision is dead — JSON-only is the production path
- session_sweep is dead — ob_retest only
- Session memory is enabled — confirmed +0.33R/trade improvement
- Pre-screening on D1+H4 only — never filter on framework-specific conditions
- The AI picks direction; the risk management structure creates the edge
- safe_place_order is NON-NEGOTIABLE — never retry without checking positions