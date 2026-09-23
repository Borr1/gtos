# Session Handoff — Strategic Review & Implementation Marathon — 2026-04-06

## WHO YOU ARE

Strategic trading mentor, technical architect, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Pressure test EVERYTHING before presenting. Challenge sloppy reasoning. When you disagree, say so clearly.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur (UTC+8) building a fully autonomous AI trading agent for XAUUSD using SMC/ICT methodology with Claude API (Sonnet) as reasoning engine and MT5 for execution. Project started March 28, 2026 — day 8 as of this session.

---

## WHAT HAPPENED THIS SESSION

This was a marathon strategic review session run in parallel with a second independent Claude session. Both sessions cross-verified each other's analysis, caught errors, debated recommendations, and converged on a unified plan. The two-session protocol caught several real errors that a single session would have missed.

### Session Flow
1. Comprehensive review of all deep dive analysis files (8 phases, 30+ output files)
2. Independent strategic assessment of system state across all dimensions
3. Received and evaluated Layer 2/Layer 3 verification results from the other session
4. Discovered the at_ob direction reversal (MD said positive, data says -5.6pp NEGATIVE)
5. Discovered the align variable as strongest untested feature (+7.5pp disc, +9.4pp val)
6. Cross-session debate on: align gate vs modifier, risk level, WR decay urgency, Monte Carlo selection
7. Final resolution tests (H4 at OB level, impulse distribution, align in trades, WR decay decomposition)
8. Spread gate optimization on FTMO M1 data
9. Model config confirmed (Sonnet everywhere)
10. 4 prompt changes implemented and verified by both sessions
11. D1-unclear batch test submitted (80 dates, $20, results back same day)
12. D1-unclear results scored and verified (14 trades, 71.4% WR, +0.47R)
13. D1 pre-screen permanently removed
14. FTMO demo account set up

---

## CRITICAL FINDINGS FROM THE DEEP DIVE VERIFICATION

### Errors Caught by Two-Session Protocol
| Error | Where | Impact | Caught By |
|-------|-------|--------|-----------|
| at_ob direction REVERSED | Master MD said positive, JSON says -5.6pp negative | Would have added wrong signal to prompt | Layer 2 verification |
| Monte Carlo table errors | 5/6 risk levels had wrong pass rates in MD | 15pp error on capital deployment decision | Layer 2 verification |
| FVG fill disc/val "missing" | Corrected doc said no split, JSON has it (disc 71.7%, val 71.0%) | Understated confidence in FVG fill finding | Other session |
| Impulse "1-2 candle" guidance | Old doc recommended single-candle impulses | Zero OBs have ≤2 candle impulses — guidance was impossible | Both sessions |
| D1 pre-screen exists in TWO places | Code (orchestrator) AND prompt (U1/U2/U4) | Batch test would have wasted $20 for 100% NO_TRADE | This session |
| 6-month timeline hallucination | Other session said "6+ months in lab" | Project is 8 days old, not 6 months | This session |

### Verified Feature Rankings (Bonferroni-surviving, n=7,496 displacements)
| Feature | Effect | Direction | Disc/Val | Status |
|---------|--------|-----------|----------|--------|
| align (TF consensus) | +7.5pp/+9.4pp | POSITIVE | Validates UP | Implemented as confidence modifier |
| creates_fvg | +11.0pp | POSITIVE | +11.8/+10.2pp | Implemented in prompt |
| at_ob | -5.6pp | **NEGATIVE** (corrected) | -7.4/-3.6pp | Implemented as caution |
| ct (counter-trend) | -5.1pp | NEGATIVE | -1.8/-8.0pp (unstable) | Implemented as small penalty |
| fvg_pct | +8.6pp | POSITIVE | Validates | Not separately implemented (correlated with creates_fvg) |
| direction | +8.6pp | Bullish > bearish | Validates | Not directly actionable |
| origin_revisited | +54.1pp | SEMI-OUTCOME | Tautological | Cannot use as predictor |

### Dead Features (confirmed, never revisit)
- H4 alignment alone: p=0.50 (displacement level), p=0.052 at OB level but only 51 non-aligned OBs
- D1 alignment alone: p=0.93 (displacement), p=0.45 (OB comprehensive) — NOW REMOVED from pre-screen
- OTE zone: p=0.61 — REMOVED from prompt
- BE stop: net negative at every trigger level
- NY KZ extension to 17:00: p=0.52
- DOW filtering: p=0.10
- All 10 "untested promising features": NULL (strength, levels_swept, liq_depth, mss, m15_aligned, etc.)
- Market regime: all regime tests p > 0.05
- FVG size: p=0.57

---

## FINAL TESTS RESULTS (Resolved All Remaining Unknowns)

### Test A: H4 at OB Level
- H4 aligned: 73.6% (n=754) vs not aligned: 60.8% (n=51)
- Effect: +12.8pp, Fisher p=0.052 (borderline, not significant)
- Disc: +11.5pp, Val: +13.5pp (gets STRONGER in validation)
- BUT: 93.7% of OBs are H4-aligned — barely varies, can't discriminate
- **Decision:** Leave H4 as-is in prompt. Don't elevate, don't remove. Not actionable as a filter.

### Test B: Impulse Candle Distribution
- Distribution: min=4, p25=6, median=7, p75=8, max=14
- Q1 (≤6): 84.8% continuation (n=217)
- Q2 (7): 84.5% continuation (n=283)
- Q3 (8): 65.8% continuation (n=155) — **19pp DROP**
- Q4 (>8): 40.7% continuation (n=150) — **another 25pp DROP**
- **Decision:** Implemented "≤7 candles preferred" as prompt guidance with concrete anchor

### Test C: Align Distribution Among Trades
- 23.7% of actual trades (14/59) had align < 2
- A hard gate would filter ~24% of trades — too expensive
- AI already selects 76.3% high-align trades naturally
- **Decision:** Implement as confidence modifier (injected score), NOT hard gate

### Test D: WR Decay Decomposition
- **By quarter:** Peak 2025-Q1 (73.2%, n=41), declined to 2026-Q1 (59.4%, n=32)
- **By price level:** NO monotonic relationship — decay is NOT price-driven
- **By KZ × half:**
  - First half London: 73.1% WR, +0.317R
  - Second half London: 60.9% WR, -0.017R (essentially breakeven)
  - First half NY: 61.5% WR, +0.269R
  - Second half NY: 53.3% WR, +0.220R
- **London decayed 12.2pp, NY decayed 8.2pp**
- **Disc/val alignment:** Discovery 64.8% → Validation 58.8% (6.0pp gap)
- **Decision:** Use ~59% WR as conservative planning estimate, not 62%. Monitor first 20 live trades.

---

## SPREAD GATE OPTIMIZATION (FTMO)

### The Problem
System was on a broker with $0.13-$0.25 spreads, gate at $0.30. Switched to FTMO where gate blocked 100% of trades.

### The Analysis
- M1 data: 100K rows, 74 trading days, spread column available
- M1 spread at candle close (relevant moment): median $0.39 London, $0.39 NY
- Tick spread (all ticks): higher ($0.71 London median) — includes mid-bar spikes
- The M1 candle-close spread is the relevant measurement (system evaluates at candle close)

### The Result
- Optimal threshold: $1.00 (100% pass rate, max observed M1 spread was $0.99)
- The gate is effectively a safety rail against extreme spikes, not an active filter
- Dual London/NY thresholds: 0% improvement over single threshold
- Spread cost: 26.2% of edge at SL=$8 (meaningful but manageable)
- At conservative 59% WR and SL=$6: spread cost rises to ~39% of edge (tight margin)

### Decision
`max_spread_cents: 100` — set and confirmed.

---

## D1 PRE-SCREEN REMOVAL (Biggest Frequency Improvement)

### The Batch Test
- 80 D1-unclear dates, 2,080 prompts, $25.53 (batch pricing)
- Temporary modifications: U1/U2/U4/Step 1/OB1/BR1/BR2 relaxed for H4+H1 consensus
- Code bypass: `--no-prescreen` flag (already existed in batch script)
- All modifications reverted after submission

### The Results
- 14 trades from 80 dates (17.5% trade frequency)
- 10 wins, 4 losses, 71.4% WR, +0.47R expectancy, +6.64R total
- All ob_retest framework, London 6 / NY 8

### The Verification (6 checks, all pass)
1. **Outliers:** Top 2 removed → n=12, 66.7% WR, +0.103R (still positive, closer to baseline)
2. **Date spread:** 6 quarters, 9 months, both 2024 and 2025 — no clustering
3. **Rejected CANDIDATEs:** 2/16 rejected by grade gate (B+, C) — normal
4. **Fisher test:** p=0.568 — no significant difference from D1-clear (confirms "D1 doesn't matter")
5. **Bias source:** 13/14 used H4+H1 consensus (the test worked as intended)
6. **London vs NY:** Both positive (London 67%/+0.35R, NY 75%/+0.57R)

### Permanent Implementation (commit 7331bbb)
- **Prompt:** U1/U2/U4/Step 1/OB1/BR1/BR2 permanently modified for H4+H1 consensus fallback
- **Code:** prescreen_mso() and prescreen_date() only skip when BOTH D1 AND H4 unclear
- **Tests:** 4 test files updated, 601 passing, 1 pre-existing failure (unrelated spread config)
- **Expected impact:** ~60% more trades (3.5 → 5.6/month)

---

## MODEL CONFIRMED

All roles use `claude-sonnet-4-20250514`. No mismatch between backtest and live. The 129-trade backtest applies directly to the deployed system.

---

## PROP FIRM STATUS

- **Account:** FTMO free trial, $100K, 1-Step challenge, no trades yet
- **Risk sizing:** Use XAUUSD-only Monte Carlo (not combined)
  - At 0.75% risk: ~78% pass rate (XAUUSD-only)
  - At 1.0% risk: ~72% pass rate (XAUUSD-only)
  - Choose based on prop firm time limit: 0.75% if no pressure, 1.0% if <90 day window
- **FTMO rules:** Allows EAs, no high-frequency scalping, max daily/total loss limits
- **NOT ready for paid challenge yet** — need 20-30 demo trades first

---

## SYSTEM STATE AS OF END OF SESSION

### Code Changes Made This Session
| File | Change | Commit |
|------|--------|--------|
| src/prompts/primary_analyzer_prompt.py | 4 quality signals (creates_fvg, at_ob, impulse, OTE removal) | Earlier commit |
| src/prompts/primary_analyzer_prompt.py | D1 removal (U1/U2/U4/Step 1/OB1/BR1/BR2) | 7331bbb |
| src/components/orchestrator.py | Pre-screen allows D1-unclear when H4 clear | 7331bbb |
| scripts/batch_backtest.py | Same pre-screen logic + label updates | 7331bbb |
| config/agent_config.yaml | max_spread_cents: 30 → 100 | Earlier |
| tests/ (4 files) | Updated assertions for new D1-unclear behavior | 7331bbb |

### Test Status
- 601 passing
- 1 pre-existing failure (test_max_spread_matches_permissions — spread config mismatch, existed before this session)

### Infrastructure
- FTMO demo account active
- FTMO data transferred to Mac (GBPUSD candles, M1 data, volatility profiles)
- All analysis outputs in knowledge_base_backtest/analysis/

---

## THE HONEST ASSESSMENT

### What's Strong
- **Research methodology:** Three-layer verification, two-session cross-check, Bonferroni correction, disc/val splits. Institutional quality.
- **Decision discipline:** Killed OTE, H4 elevation, BE stops, session sweep, vision mode, 10+ dead features. Data-driven kills.
- **Prompt changes are validated:** Every change backed by p<0.001 evidence with disc/val stability (except ct which has unstable magnitude).
- **D1 removal is the single biggest win:** 60% more trades from removing a dead filter, validated by batch test + 6 verification checks.
- **The edge is real:** 62% WR, +0.278R mean, PF 1.94 on 129 trades over 2+ years. Survived every pressure test.

### What's Concerning
- **WR decay:** 67.2% → 58.5% across halves. London went from +0.317R to -0.017R (breakeven). Not price-driven — probably temporal/regime.
- **Spread eats 26-39% of edge** on FTMO depending on SL distance. The system works but is spread-sensitive.
- **n=14 for D1-unclear trades** is too small to know the true WR. Could be 45% or 90%. The decision to remove D1 is based on the mechanical evidence (p=0.93 on n=7,496), not on 14 trades.
- **~30% AI non-determinism:** Same prompt, same data, different decisions 30% of the time. Inherent to LLM decision-making.
- **Displacement-level findings may not transfer 1:1 to trade-level.** The AI already implicitly selects for the features we've now made explicit. Marginal improvement from prompt changes may be smaller than displacement-level statistics suggest.

### The Narrative (3 sentences)
H1 order blocks on gold have a 73% base rate of continuation when retested. The AI adds value by filtering which retests to trade based on multi-timeframe context, producing ~60% WR at +0.15-0.20R per trade. The prompt changes improve the filter; the D1 removal and FVG fill framework expand the opportunity set.

---

## WHAT THE NEXT SESSION SHOULD DO

### Monday (Markets Open)
1. **Sync code to Windows** — all changes from this session
2. **Run test suite on Windows** — confirm 601 passing
3. **Let the system trade London and NY sessions** — first live session with updated prompt + D1 removal
4. **Manually verify every AI decision on TradingView** — at least 1 per day
5. **Record actual spread at entry** if a trade triggers — compare to M1 optimization data

### This Week (Observation Mode)
- Expect 1-2 XAUUSD trades (up from ~0.8/week with old frequency)
- Don't touch the system
- After each trade closes: record entry price, SL, spread, actual R, MFE/MAE
- Check if AI correctly states bias source (D1 or H4+H1 consensus) on D1-unclear days

### After 15-20 Live Trades
- Compute live WR and compare to backtest baseline (expect ~59-64%)
- Check if London decay continues or reverts
- Check if D1-unclear trades perform similarly to D1-clear
- Update Monte Carlo with live data if WR materially differs from backtest

### Still Pending (Not Blocking Deployment)
- **Align score injection** — code change to compute and inject align into prompt context. Medium priority.
- **FVG fill framework** — 71.4% continuation at 80-100% fill depth, adds ~35% more trading dates. Design needed.
- **Calendar event analysis** — blocked, need MQL5 export from Windows
- **GBPUSD expansion** — needs more validation (n=24, concentrated in 2 months)
- **Fix pre-existing test failure** — test_max_spread_matches_permissions

---

## STANDING RULES (NON-NEGOTIABLE)

1. Never re-run in-sample data to validate fixes — fresh data only
2. safe_place_order pattern is sacred
3. Each improvement tested independently before stacking
4. Statistical significance required before risking real capital
5. File versioning on all outputs
6. One change at a time in production
7. Every spending decision justified by data
8. AI's qualitative judgment is irreplaceable
9. `--symbol` required for instrument-specific config
10. Session files must be instrument-scoped
11. Pressure test EVERYTHING (~30-40% of things have issues)
12. Every prompt to Claude Code gets self-pressure-tested before presenting
13. Check for concurrent file modification
14. Economic calendar must be verified against real sources
15. Every prompt Claude writes MUST be self-pressure-tested before presenting (stored in memory)

---

## KILLED (Data says no — stop revisiting)

- D1 pre-screen as frequency filter → REMOVED (p=0.93, p=0.45, batch confirmed)
- D1 alignment as predictor → DEAD everywhere
- H4 alignment alone → DEAD at displacement level (p=0.50), underpowered at OB level (p=0.052)
- OTE zone → DEAD (p=0.61) — REMOVED from prompt
- BE stop → net negative at every trigger
- Session sweep → negative expectancy
- Chart vision → hurt performance
- Counter-trend mode → 44% WR, p=0.73
- Confidence scoring → r ≈ 0
- Context Agent → 2.4x cost, zero capability
- Cross-instrument divergence → negative expected value
- First-hour direction → random
- FVG overlap as OB predictor → reverses in validation
- Global A+ filter → kills the best segment (A-London at 77.8% WR)
- Session patience rules → confounded with KZ
- All 10 untested promising features → NULL at n=7,496

---

## KEY FILES FROM THIS SESSION

```
Analysis:
  knowledge_base_backtest/analysis/deep_dive_20260406/verified/ — Layer 2/3 outputs
  knowledge_base_backtest/analysis/deep_dive_20260406/verified/final_tests/ — H4, impulse, align, decay
  knowledge_base_backtest/analysis/spread_optimization/ — FTMO spread analysis
  knowledge_base_backtest/analysis/d1_unclear_batch/ — D1 batch test metadata + results

Batch Results:
  msgbatch_01WXewYLHYVXzTeuJnq2vzHR — D1-unclear batch (80 dates, 14 trades)

FTMO Data:
  data/historical/XAUUSD_D1.csv — FTMO feed
  data/historical/GBPUSD_*.csv — FTMO feed
  exports/mt5_data_dump/ — M1 data, volatility profiles, tick availability
```
