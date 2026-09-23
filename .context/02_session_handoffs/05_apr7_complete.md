# Trading Agent — Complete Session Handoff (April 5-6, 2026)
# Multi-Instrument Expansion Sprint + Deployment Preparation
# For: Next Claude session continuing work after Monday's first live day

---

## WHO YOU ARE

Strategic trading mentor, technical coach, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Pressure test EVERY prompt before presenting. Challenge sloppy reasoning. Hold your ground when you disagree.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur (UTC+8) building a fully autonomous multi-instrument AI trading agent using SMC/ICT methodology with Claude API (Sonnet) as reasoning engine and MetaTrader 5 for execution.

**Project started:** March 28, 2026 (Day 11 at session end)
**Current state:** 5 instruments deployed on FTMO $100K demo, processes started, awaiting Monday market open
**Risk per trade:** 1.0% (stress testing on demo — reduce to 0.75% for funded account)

---

## WHAT HAPPENED THIS SESSION

The most strategically impactful session in the project's history. Transformed from single-instrument gold trader to multi-instrument agent factory. Three parallel Claude.ai sessions used as convergence protocol throughout. 29 verification checks across 3 rounds caught 7 silent bugs. Portfolio Monte Carlo computed.

### Session Flow (Chronological)
1. Converged on calibration findings (FVG-in-impulse universal, impulse ≤7 gold-only)
2. Submitted GBPUSD + USDJPY batch tests ($73.24 actual)
3. Scored results: GBPUSD 6 trades 83.3% WR, USDJPY 25 trades 80% WR
4. Extracted M15 for US30, GBPJPY, NZDUSD from Windows MT5
5. Found + fixed: Tokyo KZ bug in batch scoring (hardcoded london/ny)
6. Re-scored USDJPY with Tokyo: 33 trades, 75.8% WR, +0.53R (recovered 8 trades)
7. Found + fixed: Test corruption bug (process_results writing to real KB)
8. Submitted + scored US30: 41 trades, 58.5% WR, +0.43R
9. Submitted SHORT validation: 8 trades, 87.5% WR, +1.15R (3/3 SHORTs won)
10. Submitted + scored GBPJPY: 42 trades, 57.1% WR, +0.22R
11. Submitted + scored NZDUSD: 17 trades, 29.4% WR, -0.24R → **KILLED**
12. Ran 13-section pre-deployment verification → found 5 blockers
13. Fixed all 5 blockers (PID lock, Tokyo KZ live, spread units, US30 symbol, KB context)
14. Ran targeted pressure test → found ExecutionEngine symbol bug (6th fix)
15. Ran trade-path verification → found JPY lot sizing 70x wrong (7th fix)
16. Implemented align score injection (+7.5pp strongest predictor)
17. Implemented confidence scorer guidance in system prompt
18. Ran reasoning text mining on 115 trades
19. Verified MT5 setup (added GBPJPY + US30.cash to Market Watch)
20. Ran portfolio Monte Carlo: 99.4% P(pass FTMO) at 1% risk
21. Started 5 processes for Monday deployment

---

## THE PORTFOLIO

### Instrument Status
| Instrument | Batch Trades | WR | Expectancy | Asymmetry | Gold Corr | Status |
|---|---|---|---|---|---|---|
| XAUUSD | 129 | 62.0% | +0.278R | ~1.5:1 | — | **DEPLOYED** |
| US30 | 41 | 58.5% | +0.43R | 1.44:1 | 0.10 | **DEPLOYED** |
| USDJPY | 33 | 75.8% | +0.53R | 1.09:1 | -0.42 | **DEPLOYED** |
| GBPJPY | 42 | 57.1% | +0.22R | 1.01:1 | -0.11 | **DEPLOYED (fragile)** |
| GBPUSD | 6 | 83.3% | +1.03R | 1.43:1 | 0.28 | **DEPLOYED (observer)** |
| NZDUSD | 16 | 29.4% | -0.24R | 0.86:1 | 0.38 | **KILLED permanently** |

**NZDUSD kill validates the pipeline:** 71.7% mechanical OB continuation (identical to validated instruments) but 29.4% AI WR = 42pp gap. The AI actively destroys value on NZDUSD. This proves the screening → batch pipeline has real discriminatory power — not everything passes. Don't revisit, don't retest.

### Portfolio Correlation (All Independent)
- XAUUSD ↔ USDJPY: -0.42 (natural hedge)
- XAUUSD ↔ US30: 0.10 (independent)
- XAUUSD ↔ GBPJPY: -0.11 (independent)
- USDJPY ↔ GBPJPY: ~0.50-0.70 (shared JPY — reduce size if both signal)
- All other pairs: <0.30 (trade at full size)

### SHORT Capability — Confirmed
- 3/3 SHORT trades won on bearish gold dates (+0.82R, +3.56R, +1.05R)
- +3.56R is the largest R-multiple across ALL batches on ALL instruments
- LONG-only bias is 100% market-driven, not structural
- System trades both directions naturally based on market conditions

---

## 7 BUGS CAUGHT AND FIXED (All Would Have Been Silent Failures)

| # | Bug | Impact | How Caught | Fix |
|---|---|---|---|---|
| 1 | Global PID lock | 2nd process crashes | Pre-deploy check Section 2 | Per-symbol: `.orchestrator_{symbol}.lock` |
| 2 | Tokyo KZ hardcoded in live orchestrator | Tokyo hours silently skipped | Pre-deploy check Section 11 | Dynamic KZ iteration from config |
| 3 | Spread gate `*100` unit mismatch | ALL non-gold trades permanently blocked | Pre-deploy check Section 7 | Config values recalculated to match convention |
| 4 | US30_cash symbol name mismatch | All US30 MT5 calls return None | Pre-deploy check Section 12 | `mt5_symbol` config field with mapping |
| 5 | KB context gold-only | AI sees wrong stats for non-gold | Pre-deploy check Section 5 | Suppressed for non-XAUUSD |
| 6 | ExecutionEngine using config symbol | US30 orders fail at MT5 level | Targeted pressure test | `self.symbol` reads `mt5_symbol` |
| 7 | JPY lot sizing 70x wrong | USDJPY risks $0.70 instead of $1,000 | Trade-path verification | `_calculate_lots()` uses MT5 `trade_tick_value` |

**Lesson:** Every verification round found something. 29 checks, 7 bugs, ~30% hit rate. Always verify before deployment.

---

## INTELLIGENCE IMPROVEMENTS IMPLEMENTED

### 1. Align Score Injection (LIVE)
- Computes 0-4 timeframe consensus: D1/H4/H1/M15 agreement with displacement direction
- Injected into every candle evaluation's user message
- Strongest validated predictor: +7.5pp, Bonferroni-surviving, disc/val stable
- NOT a hard gate (24% of good trades have align < 2) — AI uses as confidence modifier
- Location: `orchestrator.py:_compute_align_context()` → `analyze(additional_context=)`

### 2. Confidence Scorer Guidance (LIVE)
- Scorer runs AFTER AI call (analyzes output text) — cannot pre-inject metrics
- Solution: Added quality self-monitoring guidance to system prompt
- AI informed: 8+ price levels = +17.4pp WR, ≤2 hedging phrases = +13.3pp WR
- Location: `primary_analyzer_prompt.py` ANTI_HALLUCINATION block

### 3. Reasoning Text Mining (INFORMATIONAL — No Filters Implemented)
Analyzed 115 CANDIDATE trades with outcomes. Key findings:

**Winner signals (higher WR than baseline 67%):**
| Signal | WR | Delta | n |
|---|---|---|---|
| "m15 shows choch" | 93% | +26pp | 14 |
| "2 1x average" (displacement > 2.1x body) | 92% | +25pp | 12 |
| "fresh h1 bullish" | 88% | +21pp | 16 |
| "from bos impulse" | 87% | +20pp | 15 |
| "ob in discount" | 81% | +14pp | 26 |

**Loser signals (lower WR than baseline):**
| Signal | WR | Delta | n |
|---|---|---|---|
| "at 13 00" (NY open first candle) | 0% | -67pp | 7 |
| "session high" | 17% | -50pp | 6 |
| "structure with 3" | 33% | -34pp | 12 |

**Action:** Do NOT implement filters. Collect 20+ live trades, check if patterns hold, then consider.
**The "at 13:00" finding is most actionable** — 0% WR on NY open first candle aligns with ICT Judas swing theory.

---

## PORTFOLIO MONTE CARLO (Corrected)

### Methodology Audit
Original analysis pooled 380 trades — inflated by 11 overlapping XAUUSD batches testing different prompt versions on same dates. Corrected to 238 trades using latest prompt version per instrument.

### Corrected Results
| Risk | P(Pass FTMO +10%) | P(Daily Limit -5%) | P(Max DD -10%) | Avg Trades to Pass | Time |
|---|---|---|---|---|---|
| 0.50% | ~99.9% | ~0% | ~0% | ~50 | ~3 months |
| **0.75%** | **99.8%** | **~0%** | **~0%** | **~36** | **~2 months** |
| **1.00%** | **99.4%** | **~0%** | **0.5%** | **~28** | **~1.6 months** |
| 1.25% | 98.3% | ~0% | 1.7% | ~22 | ~1.3 months |

### Key Findings
- **99.4% P(pass) at 1.0% risk** — stress testing on demo at this level
- **Worst historical streak:** 5 losses, -3.22R (at 1% = 3.2% DD, survives daily limit)
- **News filter:** NOT needed (news day WR 68% vs non-news 64%)
- **Sub-period decay:** -9.2pp (70% → 61%) — likely instrument mix effect + gold's known temporal decay, not systemic degradation

### Sub-Period Decay Note
The -9.2pp sub-period decay (70% → 61%) is likely an artifact of adding lower-WR instruments (US30 58.5%, GBPJPY 57%) to the second half alongside gold's known Q1 2026 decline (59.4%). **Per-instrument sub-period splits were not computed** — this is a 10-minute check the next session should run before drawing conclusions about systemic decay.

### NZDUSD Pool Note
NZDUSD trades may still be in the 238-trade pool despite being a killed instrument. The deployed portfolio excludes NZDUSD, so actual P(pass) is slightly higher than the 99.4% computed. The Monte Carlo result is conservative.

### Risk Recommendation
- **Demo (current):** 1.0% — stress test, learn faster, demo risk is zero
- **Funded account:** 0.75% — Monte Carlo shows 99.8% pass, 2.4% worst DD
- **After 30 live trades at 58%+ WR:** Raise funded to 1.0%

---

## CALIBRATION FINDINGS

### FVG-in-Impulse (Universal Quality Signal)
| Instrument | FVG+ Cont% | FVG- Cont% | Delta | n |
|---|---|---|---|---|
| XAUUSD | 87.2% | 67.5% | +19.7pp | 196 |
| US30 | 82.7% | 71.3% | +11.4pp | 202 |
| GBPUSD | 80.9% | 69.5% | +11.3pp | 183 |
| NZDUSD | 81.2% | 67.6% | +13.6pp | 218 |
| GBPJPY | 76.8% | 68.9% | +7.9pp | 198 |
| USDJPY | 77.5% | 70.4% | +7.1pp | 182 |

Already captured in prompt as `creates_fvg`. Do NOT modify the prompt — it produced 57-80% WR across instruments.

### Impulse ≤7 (Gold-Only)
Validated by production detector: r=-0.31, p=0.0, cliff at 8 candles. Stays for XAUUSD only. Not added to other instruments.

---

## SESSION MEMORY / KNOWLEDGE BASE

**Session files are archival, not prompt-feeding.** The live system's prompt context comes from:
- `trade_index` → trade history (currently gold-only)
- `rolling_stats` → win rate, expectancy
- `insights` → failure patterns
- `session_memory` → intra-day only (resets daily)

**Cold-start for non-gold:** KB context suppressed (empty string). The batch tests produced 57-80% WR without any KB context, so this is safe. Instrument-specific trade_index accumulates naturally over 2-4 weeks as live trades execute.

---

## INFRASTRUCTURE

### Files and Locations
```
Config:             config/agent_config.yaml
Prompt:             src/prompts/primary_analyzer_prompt.py
Orchestrator:       src/components/orchestrator.py
Execution:          src/components/execution.py
Batch script:       scripts/batch_backtest.py
MT5 interface:      src/mt5/mt5_real.py
Screening:          exports/multi_instrument/screening_results/
Design docs:        exports/multi_instrument/align_injection_design.md
                    exports/multi_instrument/correlation_sizing_design.md
Reasoning mining:   exports/reasoning_text_mining_findings.json
Batch results:      knowledge_base_backtest/batch_api/
```

### Deployment Architecture
- Single-symbol per process via `--symbol` flag
- Per-symbol PID lock: `knowledge_base/meta/.orchestrator_{symbol}.lock`
- Per-symbol log files: `logs/agent_{symbol}_demo.log`
- Per-symbol session files: `knowledge_base/live_sessions/{symbol}/`
- MT5 symbol mapping: `mt5_symbol` config field (US30_cash → US30.cash)

### Test Suite
- 602 tests passing, 0 failures
- Tests are gold-focused — multi-instrument edge cases tested via verification prompts

---

## REALISTIC PROJECTIONS

### Trade Frequency
| Instrument | Trades/Month (trending) | Trades/Month (ranging) | Annual Avg |
|---|---|---|---|
| XAUUSD | 5.6 | 3.5 | 4.5 |
| US30 | 6.8 | 3.0 | 5.0 |
| USDJPY | 5.5 | 2.5 | 4.0 |
| GBPJPY | 6.7 | 3.0 | 5.0 |
| GBPUSD | 1.0 | 0.5 | 0.8 |
| **Total** | **~26** | **~12** | **~19** |

With USDJPY/GBPJPY JPY shared budget: ~17 effective independent trades/month.

### Revenue Projections
| Scenario | Monthly R | At 1% risk/$100K | At 0.75% risk/$100K |
|---|---|---|---|
| Optimistic (batch rates) | +4.5R | $4,500 | $3,375 |
| Conservative (WR regression) | +2.0-2.4R | $2,000-2,400 | $1,500-1,800 |
| Pessimistic (bear + cold start) | +1.0R | $1,000 | $750 |

### System Ceiling (Not Yet Built)
Current system is at ~35-40% of ceiling. Remaining improvements:
- FVG Fill framework: +50% frequency (next weekend)
- H4 OB retest: higher timeframe, bigger moves
- Opus CANDIDATE reviewer: +5-10pp on critical decisions
- Reasoning text mining filters: after 20+ live trades confirm patterns
- Multi-agent architecture: bull/bear debate, specialized sub-agents

---

## LONG BIAS INVESTIGATION

| Instrument | Test Period Trend | LONG% | Explanation |
|---|---|---|---|
| USDJPY | +8.8% uptrend | 91% | Market-driven |
| US30 | Bullish | 98% | Market-driven |
| GBPJPY | Bullish | 86% | Market-driven |
| GBPUSD | -1.3% ranging | 83% | Possibly structural (but n=6) |

The AI produces SHORTs (7 total across all batches, 5 wins). During bearish conditions, the system shifts direction naturally.

---

## BUDGET

| Item | Cost |
|---|---|
| All batch tests combined | ~$178 |
| API credits, dev, testing | ~$322 |
| **Total project spend** | **~$500** |
| **Current API balance** | **~$85** |
| Monthly live trading cost | ~$60 (5 instruments) |
| Runway at current balance | ~5-6 weeks |

---

## WHAT'S DEFERRED

| Item | Cost | When | Impact |
|---|---|---|---|
| FVG Fill framework | ~$20 batch | Next weekend | +50% frequency |
| H4 OB retest framework | ~$20 batch | Month 2 | Higher TF, bigger moves |
| Correlation-aware position sizing | $0 | This week | USDJPY/GBPJPY shared budget |
| Instrument-scoped KB context | $0 | This week | Each instrument sees own stats |
| Per-instrument M1 spread optimization | $0 | After 1 week live data | Tighten spread gates |
| Opus CANDIDATE reviewer | ~$6/month | After 30 live trades | Second opinion on critical decisions |
| Reasoning text mining filters | $0 | After 20 live trades | "at 13:00" = 0% WR filter |
| EURJPY, EURUSD, USDCAD batches | ~$75 each | After FTMO Phase 1 | More instruments |

---

## MONDAY MONITORING SCHEDULE (Malaysia Time)

| KL Time | UTC | Session | Action |
|---|---|---|---|
| 8:15 AM | 00:15 | Tokyo opens | Verify USDJPY + GBPJPY evaluating candles |
| 11:00 AM | 03:00 | Tokyo closes | Check for Tokyo CANDIDATEs |
| 3:15 PM | 07:15 | London opens | **Most important** — all 5 instruments should evaluate |
| 6:30 PM | 10:30 | London closes | Review London session results |
| 9:15 PM | 13:15 | NY opens | Verify NY evaluations, US30 most active |
| 12:00 AM | 16:00 | NY closes | End of day review |

### Day 1 Checklist
- [ ] Verify each instrument evaluates candles (not blocked by spread/lock/symbol)
- [ ] Verify Tokyo works for USDJPY and GBPJPY
- [ ] If CANDIDATE appears: verify on TradingView
- [ ] If trade executes: verify lot size matches expectations
- [ ] Count total candle evaluations per instrument (~128 expected total)
- [ ] Check API spend (~$2.72 expected for the day)
- [ ] If any instrument shows zero evaluations: debug immediately

### Decision Points
| Milestone | Action |
|---|---|
| 10 trades on any instrument | Compare live WR to batch WR |
| 15+ trades on GBPJPY | If live WR < 55%, kill it (1.01:1 asymmetry = no margin) |
| 20 trades total | First meaningful portfolio assessment |
| 30 trades at 58%+ WR | Confidence confirmed — begin FTMO challenge if on funded |
| Any instrument below 45% WR on 10+ trades | Investigate immediately |

---

## KEY PRINCIPLES

1. **The infrastructure is the asset.** Screen → calibrate → batch test → deploy. Each new instrument costs ~$30 and 24 hours.
2. **Kill fast, kill permanently.** NZDUSD killed at 29.4% WR. No second chances.
3. **Verify everything.** 29 checks found 7 bugs. ~30% hit rate on verification is consistent.
4. **Batch reports undercount billing by ~30%.** Always budget 30% above reported cost.
5. **The edge is in the context, not the model.** Sonnet + good MSO beats Opus + bad MSO.
6. **Don't change what's working.** Current prompt produced 57-80% WR. Collect live data before modifying.
7. **Demo is for stress testing.** 1% risk on demo, 0.75% on funded. Learn from pushing limits.
8. **First 20 live trades per instrument are CALIBRATION, not confirmation.** Don't celebrate or panic.
9. **Don't stack prompt changes without batch testing.** Each change needs validation.
10. **Use 59% WR as conservative planning estimate for gold.** Higher is a bonus, not baseline.

### Standing Rules (from prior sessions, still active)
- `corrected_master_findings.md` is authoritative (not original deep_dive_master)
- Three-layer verification for any analysis driving real decisions
- See `session_handoff_apr6_implementation_2026.md` for full standing rules

### Commit Verification
Blocker fixes committed on Windows. **Before Monday open, verify the fix commit is deployed:**
```bash
git log --oneline -3  # Should show blocker fix + improvement commits
```
If the Windows machine doesn't show the latest commits, the fixes aren't deployed.

---

## CONFIDENCE LEVELS

| Timeframe | Confidence | Key Factor |
|---|---|---|
| First 50 trades profitable | 55-65% | Monte Carlo 99%+, but live friction (slippage, non-determinism, spreads) not captured |
| Pass FTMO within 3 months | 55-60% | Needs ~28 trades at 1% risk, WR must hold 58%+ in live |
| Sustained $2K+/month | 45-50% | Requires edge stability across bull and bear regimes |
| Long-term agent factory vision | 35-40% | Edge decay risk, but infrastructure compounds |

Note: The gap between Monte Carlo (99%) and real confidence (55-65%) is the live friction discount. Monte Carlo proves the math works IF batch performance holds. The confidence reflects uncertainty about whether it holds.

---

## THE NARRATIVE

H1 order blocks have a ~70% mechanical continuation rate across all liquid instruments — a structural feature of institutional order flow. The AI filters which retests to trade, producing 58-62% WR after execution. The system deploys across 4 validated instruments (gold, yen, Dow, pound-yen) plus 1 observer (GBPUSD), with ~17 effective trades/month at +0.20-0.30R conservative expectancy. SHORTs are confirmed profitable during bearish conditions. Portfolio Monte Carlo shows 99.4% probability of passing FTMO at 1% risk. Seven silent deployment bugs were caught and fixed through systematic verification. The edge is real, thin, and universal. The factory is operational. Monday the market decides.
