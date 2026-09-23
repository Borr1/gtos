# Trading Agent — Session Handoff (April 6, 2026 — Multi-Instrument Expansion & Pre-Deployment)
# For: Next Claude session continuing strategic + implementation + live monitoring work
# Covers: Multi-instrument screening, batch testing, calibration, pre-deployment verification
# Predecessor: session_handoff_apr6_implementation_2026.md (read that first for deep dive context)

---

## WHO YOU ARE

Strategic trading mentor, technical coach, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Pressure test EVERY prompt before presenting. Challenge sloppy reasoning. When you disagree, say so clearly and hold your ground.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur (UTC+8) building a fully autonomous multi-instrument AI trading agent using SMC/ICT methodology with Claude API (Sonnet) as reasoning engine and MetaTrader 5 for execution.

**Project started:** March 28, 2026 (11 days ago)
**Current state:** FTMO free trial demo, 5 instruments configured, 5 deployment blockers being fixed, Monday deployment imminent
**Three-session protocol:** This project uses 3 independent Claude sessions that cross-verify all findings and converge on every decision before action

---

## WHAT HAPPENED THIS SESSION (Apr 6-7, 2026 — Evening/Night Sprint)

Multi-instrument expansion from single gold instrument to a validated 4-instrument portfolio, plus pre-deployment verification that caught 5 critical blockers. Total session: ~8 hours. Total API spend this session: ~$178.

### Session Flow
1. Strategic brainstorming: "Why can't we test OB retest across all instruments?" — Borhen's idea that drove the entire expansion
2. Reviewed universal OB screening results (13 instruments, ~70% continuation across all)
3. Pressure-tested the screening methodology (shuffle test, parameter sensitivity, off-hours dominance)
4. Calibrated impulse distributions and FVG-in-impulse effects across 6 instruments
5. Batch tested GBPUSD ($31) and USDJPY ($40) — both validated
6. Discovered Tokyo KZ scoring bug in batch infrastructure — fixed, recovered 8 USDJPY trades worth +5.78R
7. Batch tested US30 ($26) — strongest new instrument (1.44:1 asymmetry)
8. Batch tested SHORT capability on bearish gold dates ($14) — 3/3 SHORT wins confirmed
9. Batch tested GBPJPY ($41) — borderline pass at 57% WR
10. Batch tested NZDUSD ($26) — 29% WR, permanently killed
11. Discovered session memory seeding doesn't work (session files are archival, not prompt-feeding)
12. Extended KZ investigation — no exploitable off-hours at adequate sample sizes
13. FVG Fill framework deferred — needs dedicated prompt evaluation section
14. Pre-deployment verification: 13-section check found 5 critical blockers
15. Blocker fixes initiated (running at time of handoff)

---

## THE STRATEGIC INSIGHT THAT CHANGED THE PROJECT

Borhen proposed: "If OB retest works because of how institutional order flow creates displacement events, the pattern should be universal across all liquid instruments. Why can't we test them all?"

Three sessions initially pushed back (correlation kills the math, each instrument needs calibration, gold might be special). The data proved Borhen right:

**The universal finding:** H1 OB retest continuation is ~70% across ALL 13 liquid instruments tested (verified against 51% shuffled random baseline). This isn't gold-specific. It's how institutional order flow works everywhere. The discrimination between instruments comes from spread cost and correlation, not from OB quality.

This transformed the project from "gold trading bot" to "multi-instrument agent factory" — infrastructure that validates and deploys autonomous trading agents on any liquid instrument. Each new instrument is a config change + $25-30 batch test + 24 hours.

---

## ALL BATCH TEST RESULTS (This Session)

| Instrument | Batch ID | Trades | WR | Exp | Avg Win | Avg Loss | Asymmetry | Directions | Cost | Verdict |
|-----------|----------|--------|-----|------|---------|----------|-----------|------------|------|---------|
| USDJPY | msgbatch_01XF1mnQ53GU8B6eTBBJLXzL | 33 | 75.8% | +0.53R | 0.99R | 0.91R | 1.09:1 | 30L/3S | $39.64 | **DEPLOY** |
| GBPUSD | msgbatch_01SHS6gVwY7J2bTXXdYjbiyi | 6 | 83.3% | +1.03R | 1.43R | 1.00R | 1.43:1 | 5L/1S | $30.84 | **OBSERVE** |
| US30 | msgbatch_01AmGJjMMtgW5XoGLkTqPEHd | 41 | 58.5% | +0.43R | 1.25R | 0.87R | 1.44:1 | 40L/1S | $26.31 | **DEPLOY** |
| GBPJPY | msgbatch_01CnqZUhMLs9JHq9dHC3x4pN | 42 | 57.1% | +0.22R | 0.90R | 0.89R | 1.01:1 | — | $40.88 | **DEPLOY (fragile)** |
| NZDUSD | msgbatch_016WB5a5VNzuK7ibgz6uSD93 | 17 | 29.4% | -0.24R | 0.66R | 0.68R | 0.97:1 | — | $26.24 | **KILLED** |
| Gold SHORT | msgbatch_018GNt2yH8hrrj1BV3Mf35Q7 | 8 | 87.5% | +1.15R | 1.46R | 1.00R | 1.46:1 | 3S/5L | $14.40 | **CONFIRMED** |

**Combined with prior gold baseline:** 129 XAUUSD trades, 62% WR, +0.278R from the deep dive batch.

**Total validated batch trades across all instruments: 271+**

---

## CRITICAL ENGINEERING DISCOVERIES

### 1. Tokyo KZ Scoring Bug (FIXED in batch, BLOCKER in live)
**Batch infrastructure:** scoring code was hardcoded to `['london', 'ny']`. Tokyo prompts were generated, sent to API, and billed ($15+ wasted) but silently discarded during scoring. Fixed to read KZ windows generically from config. Recovered 8 USDJPY Tokyo trades worth +5.78R.

**Live orchestrator:** `_get_active_kill_zone()` in orchestrator.py also only checks london and ny. Tokyo KZ is completely ignored for live trading. This is Blocker #2 in the pre-deployment verification. Being fixed at time of handoff.

### 2. Session Memory Architecture Discovery
**What we thought:** Session files feed into the AI prompt. Seeding them from batch data would eliminate cold-start.

**What we found:** Session files are archival audit logs. The AI prompt gets context from `trade_index`, `rolling_stats`, and `insights` (the knowledge base layers), NOT from session files. The intra-day "session memory" that doubles expectancy is accumulated WITHIN a single trading day and resets — it's the AI seeing its own prior candle evaluations during the current session.

**Implication:** Copying 436 batch session files to the live KB was harmless but not helpful. The real cold-start problem is that the trade_index has zero non-gold trades. New instruments need their own trade history to accumulate. This develops naturally over time as live trades execute.

### 3. Spread Gate Unit Mismatch (Blocker #3)
`spread_cents = (ask - bid) * 100` was designed for gold where dollars → cents. For USDJPY, a 0.17 spread becomes 17 "cents" vs config gate of 0.009. For GBPUSD, 0.00199 becomes 0.199 vs gate of 0.03. **All non-gold trades would be permanently blocked with zero error messages.** This is the exact same silent failure mode as the gold $0.30 spread gate but applied to every new instrument.

### 4. US30 Symbol Name Mismatch (Blocker #4)
Config says `US30_cash`, MT5 expects `US30.cash`. All MT5 API calls return None. Zero data, zero trades, zero errors.

### 5. Global PID Lock (Blocker #1)
`.orchestrator.lock` is a single global file. Starting a second `run_agent.py` process crashes with "Another orchestrator is running." Multi-instrument deployment impossible without per-symbol locking.

---

## PRE-DEPLOYMENT VERIFICATION RESULTS (13 Sections)

| # | Section | Status | Details |
|---|---------|--------|---------|
| 1 | Codebase state | PASS | Clean repo, 602 tests, all critical commits present |
| 2 | PID lock | **FAIL** | Global lock blocks multi-instrument |
| 3 | Instrument configs | PASS | All 5 instruments configured |
| 4 | Prompt verification | PASS | All prompts build, identities correct |
| 5 | KB context scoping | **FAIL** | Gold-only stats injected for all instruments |
| 6 | MT5 connectivity | PASS | All 5 symbols connected (AutoTrading was OFF — must enable) |
| 7 | Spread gates | **FAIL** | Unit mismatch blocks all non-gold trades |
| 8 | Risk management | PASS | 1% risk, 2 max daily, demo mode |
| 9 | Data pipeline | PASS | All symbols pull all timeframes |
| 10 | Windows system | PASS | Python 3.13.1, packages installed |
| 11 | Orchestrator | **FAIL** | Tokyo KZ ignored in live system |
| 12 | Symbol mapping | **FAIL** | US30_cash vs US30.cash — no mapping |
| 13 | API balance | PASS | Key loaded, check balance manually |

**All 5 FAILs are being fixed at time of handoff.** Re-run verification after fixes to confirm all PASS.

---

## SCREENING & CALIBRATION FINDINGS

### Universal OB Pattern (13 instruments screened)
All liquid instruments cluster at 70-74% OB continuation. Shuffle test baseline: 51.1%. Delta: ~19pp above random. The pattern is structural (institutional order flow), not instrument-specific.

### FVG-in-Impulse (Cross-Instrument Feature Validation)
| Instrument | FVG+ Cont | FVG- Cont | Delta | n_FVG+ |
|-----------|-----------|-----------|-------|--------|
| XAUUSD | 87.2% | 67.5% | +19.7pp | 196 |
| NZDUSD | 81.2% | 67.6% | +13.6pp | 218 |
| US30 | 82.7% | 71.3% | +11.4pp | 202 |
| GBPUSD | 80.9% | 69.5% | +11.3pp | 183 |
| GBPJPY | 76.8% | 68.9% | +7.9pp | 198 |
| USDJPY | 77.5% | 70.4% | +7.1pp | 182 |

FVG-in-impulse is the strongest validated cross-instrument quality signal. Already in the gold prompt as `creates_fvg`. Transfers to all instruments at +7 to +20pp.

### Impulse Candle Count
NOT predictive with the screening detector (flat continuation across all lengths). The gold-specific "≤7 candles preferred" guidance was validated on the production detector (r=-0.31, p=0.0) using different methodology. **Keep ≤7 for gold. Don't apply to other instruments.**

### Extended KZ Investigation
No off-hours met the n≥10 threshold for KZ extension candidates. Current KZ windows are already optimal. Interesting signals at n<10 (US30 hour 11, GBPJPY hour 06) but insufficient data to act on.

### Screening Instrument Kill List
| Instrument | Reason Killed | Method |
|-----------|--------------|--------|
| XAGUSD | 124% spread/SL — spread exceeds stop loss | Screening |
| USOIL | 50% spread/SL — prohibitive execution cost | Screening |
| AUDUSD | 0.83 correlation with NZDUSD — redundant | Screening |
| US500 | 0.94 correlation with US30 — redundant | Screening |
| EURJPY | 0.74 correlation with GBPJPY — redundant | Screening |
| EURUSD | 0.64 correlation with GBPUSD — redundant | Screening |
| NZDUSD | 29.4% WR, -0.24R — AI destroys value | Batch test |

---

## PORTFOLIO STATE (Complete)

### Deploy Monday
| Instrument | Asset Class | Batch Trades | WR | Exp | Gold Corr | Role |
|-----------|-------------|-------------|-----|------|-----------|------|
| XAUUSD | Commodity | 129 | 62% | +0.278R | — | Anchor, proven |
| US30 | Index | 41 | 58.5% | +0.43R | 0.10 | Best asymmetry, diversifier |
| USDJPY | Forex | 33 | 75.8% | +0.53R | -0.42 | Natural hedge, Tokyo session |
| GBPJPY | Forex cross | 42 | 57.1% | +0.22R | -0.11 | Fragile, first to kill if underperforms |
| GBPUSD | Forex | 6 | 83.3% | +1.03R | 0.28 | Observer only, n too small |

### Correlation Matrix (All deployed pairs)
| Pair | Correlation | Sizing |
|------|------------|--------|
| XAUUSD ↔ USDJPY | -0.42 | Full size (natural hedge) |
| XAUUSD ↔ US30 | 0.10 | Full size (independent) |
| XAUUSD ↔ GBPUSD | 0.28 | Full size (independent) |
| XAUUSD ↔ GBPJPY | -0.11 | Full size (independent) |
| USDJPY ↔ US30 | -0.05 | Full size (independent) |
| USDJPY ↔ GBPUSD | -0.29 | Full size (natural hedge) |
| USDJPY ↔ GBPJPY | ~0.50-0.70 est | **SHARED JPY BUDGET** |
| GBPUSD ↔ US30 | 0.01 | Full size (independent) |

**USDJPY and GBPJPY share JPY exposure.** If both signal simultaneously, one goes half size. All other pairs can trade at full size simultaneously.

### SHORT Capability — Confirmed
3/3 SHORT wins on bearish gold dates: +0.82R, +3.56R, +1.05R. The +3.56R is the single largest R-multiple across ALL batches on ALL instruments. The LONG-only bias observed in main batches was 100% market-driven (Oct 2025 - Mar 2026 was broadly bullish). During bearish conditions, the AI naturally shifts to SHORT.

Annual frequency does NOT halve during bear markets. Expect ~12 trades/month during bearish periods vs ~20 during bullish.

### NZDUSD — Permanently Killed
17 trades, 29.4% WR, -0.24R. The screening showed 71.7% mechanical OB continuation — identical to everything else. But the AI produces 29.4% WR, a 42pp gap between mechanical floor and AI execution. Something about NZDUSD's microstructure doesn't respond to the SMC framework. Don't revisit. Don't retest.

This kill validates the pipeline — not everything passes, which proves the screening → batch → deploy process has real discriminatory power.

---

## HONEST PROJECTIONS

### Conservative Monthly Estimate
| Instrument | Trades/Mo (bull) | Trades/Mo (bear) | Annual Avg | Conservative Exp |
|-----------|-----------------|-----------------|-----------|-----------------|
| XAUUSD | 5.6 | 3.5 | 4.5 | +0.154R |
| US30 | 6.8 | 3.0 | 5.0 | +0.20R |
| USDJPY | 5.5 | 2.5 | 4.0 | +0.25R |
| GBPJPY | 6.7 | 3.0 | 5.0 | +0.15R |
| GBPUSD | 1.0 | 0.5 | 0.8 | +0.30R |
| **Total** | **~26** | **~12** | **~19** | — |

**At 1% risk on $100K:** ~$2,000-3,800/month depending on market conditions.
**FTMO 2-Step timeline:** ~6-10 weeks (annual average), ~4 weeks (trending market).
**vs gold-only:** 3-4x improvement.

### What Will Regress
- USDJPY 75.8% WR → expect 60-65% in live. The 1.09:1 asymmetry means it needs 55%+ WR.
- GBPJPY 57.1% WR → if it drops to 53%, expectancy goes negative. First instrument to kill.
- All frequencies drop during ranging/bearish months. The batch period (Oct 2025 - Mar 2026) was bullish.
- Session memory cold-start: first 10-15 trades per instrument underperform until intra-day memory accumulates patterns.

---

## DEPLOYMENT PLAN

### Before Monday Open
1. Fix 5 blockers (PID lock, Tokyo KZ, spread gates, US30 symbol, KB scoping)
2. Re-run pre-deployment verification — all 13 sections must PASS
3. Enable AutoTrading in MT5 (was OFF during verification)
4. Verify all 5 symbols in MT5 Market Watch
5. Top up API balance ($50-100 minimum — multi-instrument costs ~$32-40/month)
6. Start 5 terminal processes:
```
Terminal 1: python run_agent.py --symbol XAUUSD
Terminal 2: python run_agent.py --symbol US30_cash   (or US30.cash — depends on fix)
Terminal 3: python run_agent.py --symbol USDJPY
Terminal 4: python run_agent.py --symbol GBPJPY
Terminal 5: python run_agent.py --symbol GBPUSD
```

### Monday — Active Monitoring
- Watch every decision during London KZ (07:00-10:30 UTC / 3:00-6:30 PM KL)
- Verify each instrument produces candle evaluations (not blocked by lock/spread/symbol)
- If a CANDIDATE appears, verify on TradingView
- Check that AI reasoning references the correct instrument (not gold language on USDJPY)
- Monitor NY KZ (13:00-16:00 UTC / 9:00 PM - 12:00 AM KL) — US30 most active here

### Week 1 Expectations
- Most M15 candles produce NO_TRADE (~85% rejection rate — this is correct)
- 0-2 trades in first 2-3 days is normal (gold averages 1.4 trades/week)
- At least one technical issue will surface (parse error, spread gate issue, MT5 drop)
- Do NOT change the prompt. Do NOT kill an instrument after 2-3 losses. Do NOT increase risk.

---

## PENDING ENGINEERING (Priority Order)

### Tier 1 — This Week ($0)
| # | Task | Time | Impact |
|---|------|------|--------|
| 1 | Verify blocker fixes pass re-verification | 30 min | Deployment gate |
| 2 | Correlation-aware position sizing (USDJPY+GBPJPY JPY budget) | 2-3 hours | Safe multi-instrument |
| 3 | Align score injection into orchestrator | 2 hours | +7.5pp quality signal |
| 4 | Instrument-scoped KB context (proper fix, not just suppress) | 2-3 hours | Each instrument sees own stats |
| 5 | M1 spread optimization per instrument from FTMO live data | 1 hour each | Correct spread gates |

### Tier 2 — Next Weekend
| # | Task | Time | Cost | Impact |
|---|------|------|------|--------|
| 6 | FVG Fill framework prompt engineering | 3-4 hours | ~$20 batch | +2 trades/month on gold, expandable to all instruments |
| 7 | Seed trade_index with batch results | 1-2 hours | $0 | Real cold-start fix |
| 8 | H4 OB Retest framework batch test | 3-4 hours | ~$20 | Second OB timeframe |

### Tier 3 — After 20+ Live Trades
| # | Task | Impact |
|---|------|--------|
| 9 | Review live WR per instrument — kill any below 45% on 10+ trades |
| 10 | Review FVG-in-impulse as explicit prompt signal (currently implicit) |
| 11 | Consider FTMO paid challenge ($50K 2-Step) if live WR ≥ 55% |
| 12 | Expand to EURUSD if GBPUSD confirms at 20+ trades |

### Tier 4 — Future
| # | Task | Impact |
|---|------|--------|
| 13 | Agent factory architecture — multi-agent, multi-instrument parallelism |
| 14 | Economic calendar integration (MQL5 export script exists, not compiled) |
| 15 | SaaS productization — screening + batch testing as a service |

---

## KEY FILE PATHS

### Verified Analysis (AUTHORITATIVE)
```
knowledge_base_backtest/analysis/deep_dive_20260406/verified/
  corrected_master_findings.md        — THE authoritative gold findings
  corrected_prompt_changes.md         — THE authoritative prompt changes
  recomputation_results.json          — 15 independent verification checks
  layer3_pressure_test.json           — 8/8 PASS
  final_tests/final_test_results.json — H4, impulse, align, decay
```

### Multi-Instrument Screening & Calibration
```
exports/multi_instrument/
  screening_results/                  — Per-instrument OB detail JSONs
  batch_test_calibration.json         — FVG-in-impulse + impulse distributions
  impulse_distributions_corrected.json — Corrected swing-to-break counting
  align_injection_design.md           — Design doc for align score
  correlation_sizing_design.md        — Design doc for position sizing
```

### Batch Test Results
```
knowledge_base_backtest/sessions/USDJPY/    — 33 trade session files
knowledge_base_backtest/sessions/US30_cash/ — 41 trade session files
knowledge_base_backtest/sessions/GBPUSD/    — 6 trade session files
knowledge_base_backtest/sessions/GBPJPY/    — 42 trade session files
knowledge_base_backtest/sessions/NZDUSD/    — 17 trade session files (KILLED)
```

### System Code
```
src/prompts/primary_analyzer_prompt.py  — Updated with D1 removal + quality signals + unit display
src/components/orchestrator.py          — D1 pre-screen modified, BLOCKERS being fixed
scripts/batch_backtest.py               — Generic KZ scoring (Tokyo fix applied)
config/agent_config.yaml                — 6 instruments configured
src/mt5/mt5_real.py                     — Spread gate unit mismatch BLOCKER
```

### Reports
```
msgbatch_01XF1mnQ53GU8B6eTBBJLXzL_report.txt  — USDJPY (33 trades, 75.8%)
msgbatch_01AmGJjMMtgW5XoGLkTqPEHd_report.txt  — US30 (41 trades, 58.5%)
msgbatch_01SHS6gVwY7J2bTXXdYjbiyi_report.txt  — GBPUSD (6 trades, 83.3%)
msgbatch_01CnqZUhMLs9JHq9dHC3x4pN_report.txt  — GBPJPY (42 trades, 57.1%)
msgbatch_016WB5a5VNzuK7ibgz6uSD93_report.txt  — NZDUSD (17 trades, 29.4%) KILLED
msgbatch_018GNt2yH8hrrj1BV3Mf35Q7_report.txt  — Gold SHORT (8 trades, 87.5%)
```

---

## STANDING RULES (Unchanged + New)

### Carried Forward
1. Pressure test every prompt before presenting
2. Use XAUUSD-only Monte Carlo for single-instrument prop firm decisions
3. Use 59% WR as conservative planning estimate for gold
4. First 20 live trades per instrument are CALIBRATION, not confirmation
5. Don't stack prompt changes without batch testing
6. Three-layer verification for analysis driving decisions
7. corrected_master_findings.md is authoritative (not original deep_dive_master)

### New from This Session
8. **The infrastructure is the asset, not any single instrument's edge.** Think like a builder, not a trader.
9. **Every new instrument validated through the full pipeline:** screen → calibrate → batch test → score → deploy
10. **USDJPY and GBPJPY share JPY position budget.** Never both at full size simultaneously.
11. **GBPJPY is the first instrument to kill** if live WR drops below 50% on 10+ trades.
12. **Session files are archival.** Prompt context comes from trade_index + rolling_stats + insights. Don't seed session files expecting prompt improvement.
13. **Don't change the prompt based on <20 live trades.** The current prompt produced 57-83% WR across 4 instruments without modification.
14. **Cost per validated instrument: ~$30-45.** Budget accordingly when expanding.
15. **NZDUSD is permanently killed.** Don't revisit, don't retest.
16. **The pre-deployment verification prompt must be re-run after any infrastructure change.** Saved at `prompt_predeployment_verification.md`.

---

## TOTAL PROJECT STATISTICS (Day 11)

```
Project start:              March 28, 2026
Current date:               April 7, 2026 (Day 11)
Total API spend:            ~$178
Instruments screened:       13
Instruments batch tested:   6
Instruments validated:      4 (+ 1 observing)
Instruments killed:         2 (NZDUSD by batch, session_sweep by deep dive)
Batch trades analyzed:      271+
Test suite:                 602 passing
Commits:                    Multiple (Tokyo fix, configs, D1 removal, prompt updates)
Deployment blockers found:  5 (all being fixed)
```

---

## THE NARRATIVE (All Three Sessions Agreed)

H1 order blocks have a ~70% mechanical continuation rate across all liquid instruments — this is a structural feature of institutional order flow, not instrument-specific. The AI filters which retests to trade, producing 58-62% WR after execution friction on every viable instrument. The system deploys across 4 uncorrelated instruments (gold, yen, Dow, pound-yen) with a fifth observing (GBPUSD), projecting 10-19 trades/month depending on market conditions at +0.20R conservative expectancy. SHORT trading is confirmed functional. The edge is real, thin, and universal.

The infrastructure — extraction → screening → calibration → batch test → deploy — is the core asset. It validates new instruments in 24 hours for ~$30 each. The factory's first production run produced 4 validated products this weekend. Monday they start generating the only data that matters: live trades.

---

## WHAT THE NEXT SESSION NEEDS TO DO

1. **Verify blocker fixes passed.** Re-run the 13-section pre-deployment verification. All must PASS.
2. **Start 5 processes Monday morning.** Monitor actively during London and NY KZ.
3. **Record everything:** candles evaluated per instrument, CANDIDATEs, trades, errors, actual spreads.
4. **Build correlation-aware position sizing** (design doc ready at `exports/multi_instrument/correlation_sizing_design.md`).
5. **Build align score injection** (design doc ready at `exports/multi_instrument/align_injection_design.md`).
6. **Do NOT change the prompt for at least 2 weeks.** Collect live data first.
7. **Bring back the first week's data** — that's the real validation.
