# Gold Trading Agent — Session Handoff (April 2, 2026)
# For: Next Claude session to continue strategic work

---

## WHO YOU ARE

Strategic trading mentor, technical architect, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Challenge sloppy reasoning. Think like an autonomous system architect. When you disagree, say so clearly. Read all project files before responding.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur building a fully autonomous XAUUSD AI trading agent using SMC/ICT methodology with Claude API as the reasoning engine and MT5 for execution.

---

## CURRENT STATE — THE HONEST PICTURE

### What's Built (Production-Grade)
- ~16,000 lines Python, 441 tests (291 on Windows), battle-tested execution pipeline
- Components: data ingestion, market state analyzer, primary analyzer (Claude API), execution engine, orchestrator, safety checks, session memory, confidence scorer (shadow mode)
- Safety: safe_place_order (check-before-retry, never blind retry), partial closes with ticket tracking, crash recovery, PID locking, circuit breakers
- Deployment: verified on Windows MT5 demo ($100K MetaQuotes-Demo), all preflight checks passed, AutoTrading button needs enabling

### What's Validated
- **Directional skill is real:** 85% of 40 trades reach +0.25R MFE, 52% reach +1.0R MFE. Avg MFE 1.29R vs avg MAE 0.59R. The AI picks direction better than random.
- **Safety checks work:** Caught bad trades, prevented anomalies, net positive across all datasets.
- **Session memory improves quality:** High patience (6+ prior evaluations) → 64% WR, +0.61R. Low patience (0-2) → 42% WR, +0.03R.

### What's NOT Validated
- **Statistical significance is GONE.** Combined 40 trades: 19W/20L/1BE, +8.91R, +0.223R exp, **p=0.246** (95% CI includes zero). The original 36-trade p=0.048 degraded when 4 out-of-sample trades (all losses) were added.
- **Exit strategy is broken.** TP at 2.5R is hit only 12% of the time. Average winner exits via timeout at +0.85R. Post-hoc simulation suggests 1.5R TP would be optimal (+0.415R exp vs +0.232R), but this is untested forward.
- **All 40 trades are LONG.** Gold went from $2,780 to $5,569 (100% bull run) during the testing period. Zero SHORT trades, zero bearish/ranging market data. The system might just be "buy gold dips during a bull market."
- **AI value over naive trend-following is UNPROVEN.** We haven't compared the system against simply buying at the KZ open when D1 is bullish. This is the most fundamental unanswered question.

### Key Metrics (40 Combined Trades)
```
Trades: 40 (19W / 20L / 1BE)
Win Rate: 47.5%
Expectancy: +0.223R
Total R: +8.91R
Profit Factor: 1.59
p-value: 0.246 (NOT significant)
95% CI: [-0.160R, +0.605R]
Avg Win: +1.27R | Avg Loss: -0.75R
TP1 Hit Rate: 12% (5/40)
Avg MFE: 1.29R | Avg MAE: 0.59R
```

---

## WHAT HAPPENED THIS SESSION (April 2, 2026)

### 1. System Review & Roadmap Assessment
- Reviewed master_roadmap.md, complete_session_handoff.md, architecture.md
- Identified that the revenue projections were dangerous (anchoring on optimistic numbers when CI includes zero)
- Re-prioritized Phase 1 items: 1E (pre-screen loosening) → 1C (Asian range) → 1A (H4 OB) → 1B (DXY)

### 2. Pre-Screen Loosening Investigation (1E)
- Ran analysis: 331 of 510 weekdays (65%) killed by pre-screen
- 130 dates (39.3%) classified as POTENTIAL_MISS — ob_retest preconditions existed
- 107 of 130 were D1 "transitional" with clear H4 direction
- **Decision: Shelved.** Loosening requires 3 coupled changes (pre-screen + prompt Step 1 + Gate 1 safety check). Too much architectural risk for ~1.4 trades/month gain. 1A (H4 OB retest) and EURUSD expansion offer better ROI.

### 3. Replay Blitz — Initial NO-GO
- 66 dates, 7 trades, -0.48R expectancy → NO-GO
- **Root cause: TP1 placement bug.** 70% of ALL batch trades had TP1 below 2.0R from entry (median 0.63R). The AI was setting TP1 at structural resistance instead of at 2.5× SL distance.
- Average win was +0.20R because TP1 was trivially close to entry

### 4. Critical Bug Fixes
- **TP1 prompt rule:** Added "TP1 MUST be at minimum 2.5× SL distance from entry"
- **TP1/SL ratio safety check:** Gate 1 rejects TP1 < 2.0R from entry
- **Max SL distance gate:** Rejects SL > 2.5% of entry price (catches $428 SL anomaly)
- **Null trade_parameters guard:** Demotes CANDIDATE to NO_TRADE if params are None
- **Breaker_retest disabled:** Config flag `enabled_frameworks: ["ob_retest"]`
- **London KZ reverted:** 07:00-09:30 (extended window 09:30-10:30 produced zero trades in 130+ dates)
- **max_trades_per_day fix:** Was 1 in config, should be 2
- **File versioning:** All reports now timestamped, INDEX.md tracks all analysis files
- **Outcome simulation labeling:** Fixed CLOSED_SESSION_TIMEOUT vs CLOSED_TP1_THEN_TIMEOUT distinction

### 5. TP1 Fix Validation (36 trades on 64 fresh dates, Sonnet)
- **Results: 36 trades, 52.8% WR, +12.07R, +0.335R exp, p=0.048**
- TP1 fix works: 0/36 below 2.0R (vs 70% before). Avg TP1 distance: 2.54R
- 5 trades hit TP1 averaging +2.33R — the system working as designed
- Average win jumped from +0.20R to +1.27R
- Profit factor: 2.01

### 6. Supplementary Replay (4 trades on 55 random dates, Sonnet)
- **Results: 4 trades, 0% WR, -3.16R** — all losses
- All old productive dates were already used, so this was purely random dates
- P(0/4 | true WR=52.8%) = ~5% — unlucky but not impossible
- Combined 40 trades: p degraded from 0.048 to 0.246
- Trade #4 reached 1.98R MFE then reversed to -1.00R (near-miss)

### 7. Deep Trade Analysis (36-trade dataset)
Key findings ranked by evidence strength:
1. **TP at 2.0R is optimal** — post-hoc sim shows +21.46R (vs +12.07R baseline). 63% of winners reach 2.0R vs 37% reaching 2.5R. BUT: this is in-sample optimization.
2. **Patience is the strongest predictor** — 6+ prior evaluations: 64% WR, +0.61R. First-candle entries: 25% WR, -0.27R.
3. **SL distance predicts outcomes** — SL ≤ 0.75% of price: 68% WR, +0.77R. Above 0.75%: 35% WR, -0.15R.
4. **A-grade outperforms A+** — A: 60% WR, +0.52R. A+: 48% WR, +0.20R. Counterintuitive but consistent.
5. **BE move at 1.0R MFE** — Would save 5 near-miss losers. BUT: R-path simulation (20-candle only) showed it kills some winners too. Full-path simulation needed.
6. **Thursday weak, Friday strong** — Thu: 27% WR (n=11). Fri: 86% WR (n=7). Contradicted by supplementary run (all 4 Friday losses). Likely noise.
7. **NY outperforms London** — NY: 58% WR, +0.52R. London: 47% WR, +0.13R.

### 8. Pre-Launch Audit (Passed)
- Config consistency: 14/14 parameters verified matching across all files
- Safety checks: 14 total (5 Gate 3 + 9 Gate 1), all verified
- Execution engine: safe_place_order, partial close, crash recovery all verified
- 441 tests passing (1 pre-existing failure)
- Pre-flight checklist created at `docs/preflight_checklist.md`

### 9. Windows Demo Deployment (Verified)
- All fixes confirmed present on Windows codebase
- MT5 connected to demo account ($100K, MetaQuotes-Demo)
- Symbol XAUUSD confirmed, contract size 100 (standard), filling IOC
- Pipeline integration test passed (data ingestion → MSO → pre-screen → API call)
- Pre-screen returned PASS, API returned NO_TRADE (D1 transitional) — correct behavior
- **Blocker: AutoTrading button needs enabling in MT5 toolbar**

### 10. Strategic Reassessment — The Hard Truth
- Realized: gold went up 100% during our test period. ALL trades are LONG.
- The fundamental question "does the AI add value over naive trend-following?" was never asked
- DXY research shows gold-DXY inverse correlation is ~-0.45 but broke in 2023-2024 (both rose together)
- Decided on a phased approach: prove the foundation before optimizing

---

## THE PLAN — Phased Approach to a Trusted System

### Phase 0: Does the Foundation Work? ($0, 1 day) ← NEXT STEP
**Status: Prompt written, ready to run on Mac**

**0A: Naive Baseline Test**
Compare AI system against three naive strategies on the same 40 trade dates:
- Strategy 1: Enter LONG at first KZ candle when D1 bullish, SL at session low
- Strategy 2: Same but SL at 2× M15 ATR (matching AI's risk profile)
- Strategy 3: Average of entering at every KZ candle (random entry baseline)

Compare: MFE (R and $), MAE, WR at various TP levels, dollar P&L with 1% risk sizing.
Also compare selectivity: AI trades 40 of all passing dates. Naive trades ALL passing dates.

**Possible outcomes:**
- AI significantly outperforms → proceed to Phase 1
- AI similar to naive → system is just trend-following, needs fundamental rethink
- AI underperforms → OB analysis is degrading simple entries

**0B: DXY Diagnostic**
Pull EURUSD D1 data (DXY proxy, 57.6% weight). For each of the 40 trades, check if DXY direction correlated with outcome. If wins cluster on DXY-bearish days → DXY context would help.

**Prompt file:** `/mnt/user-data/outputs/phase0_diagnostic_prompt.md` (already written)

### Phase 1: Fix the Exit ($15-20, 3 days)
**Only if Phase 0A confirms AI adds value**
- Change TP from 2.5R to the level supported by MFE data (likely 1.5R)
- Update safety check minimum accordingly
- Forward-validate on 40-50 fresh dates
- Target: positive expectancy independently, combined p < 0.03

### Phase 2: Add Macro Context Layer ($5-10, 3 days)
**Only if Phase 0B shows DXY correlation**
- Add DXY daily direction, US10Y direction, VIX level to MSO
- Add gold-DXY correlation regime indicator (normal inverse vs broken)
- Don't hard-filter — give the AI context for reasoning
- A/B test: 30 dates, 15 with macro context vs 15 without
- Prompt addition: "DXY is [direction], yields [direction], VIX [level]. Does macro support the trade?"

### Phase 3: Economic Calendar Integration ($0-5, 2 days)
- Wire up MT5 calendar API (already stubbed in architecture)
- AVOID mode first: warn AI when high-impact event within 2 hours
- EXPLOIT mode later: post-event sweep + displacement pattern
- Flag event days in data for retrospective analysis

### Phase 4: M5 Entry Refinement ($10-15, 1 week)
**Highest-leverage technical improvement**
- When M15 returns CANDIDATE, pull 12 M5 candles for current bar
- Second focused prompt: "M15 setup confirmed. Where is the precise M5 entry and tightest M5 SL?"
- Tighter SL = larger position = more R per dollar move
- If median SL tightens from $33 to $15: same $20 move goes from 0.6R to 1.3R
- Test first: take 10 historical CANDIDATEs, manually add M5 data, check if AI produces tighter entries ($2-3 feasibility test)

### Phase 5: Combined System Validation ($15-25, 1 week)
- Deploy all validated changes on 50+ fresh dates
- Target: 20+ trades, positive expectancy, p < 0.05
- Final gate before funded deployment

### Phase 6: Funded Launch
- Only after Phase 5 passes
- Select prop firm ($100K, allows EAs, XAUUSD available, 8-10% target)
- Treat as $500 experiment producing real-market data

**Total estimated cost: $45-75 across all phases. Timeline: 3-4 weeks.**

---

## CURRENT SYSTEM CONFIGURATION

```yaml
Framework:          ob_retest only (breaker_retest disabled via config)
Kill zones:         London 07:00-09:30 UTC, NY 13:00-15:30 UTC
Grade filter:       A+ and A
Min R:R:            2.5 (in prompt and safety check)
TP1 minimum:        2.5× SL distance (prompt rule + 2.0R safety floor)
Max SL distance:    2.5% of entry price
SL floor:           max($5.00, 1.5× M15 ATR)
Max trades/day:     2 (1 per KZ)
Daily loss limit:   2%
Max spread:         $0.30
Input:              JSON-only (vision killed)
Session memory:     ENABLED (6-entry sliding window per KZ)
Confidence scorer:  SHADOW MODE (logs, doesn't filter)
Model (backtest):   claude-sonnet-4-20250514
Model (live):       claude-sonnet-4-20250514 (stay on Sonnet — validated on it)
MAGIC_NUMBER:       20260401
Budget cap:         $50/month API
Deployment phase:   2 (demo)
Tests:              441 passing (Mac), 291 passing (Windows)
```

---

## DATA INVENTORY — What's Valid, What's Not

| Dataset | Trades | TP1 Valid? | Memory? | Status |
|---------|--------|-----------|---------|--------|
| 101-trade batch (Apr 24–Mar 26) | 101 | NO (70% broken) | No | **INVALIDATED** |
| Sprint 1.5 replay (30 dates) | 17 | NO | Yes | **INVALIDATED** |
| Replay blitz (66 dates) | 7 | NO | Yes | **INVALIDATED** — bugs found |
| TP1 validation (64 dates, Sonnet) | 36 | YES | Yes | **CURRENT** |
| Supplementary (55 random dates) | 4 | YES | Yes | **CURRENT** |
| **Combined valid dataset** | **40** | **YES** | **Yes** | **p=0.246 (not significant)** |

All dates used across ALL replays are burned — cannot be reused. ~300 fresh dates remain.

---

## KEY FILES ON DISK

### Mac (development/research machine)
```
~/Documents/trading/gold-agent/
  src/components/market_state.py          # MSO builder
  src/components/primary_analyzer.py      # AI reasoning + null params guard
  src/components/permissions.py           # Gate 1 + Gate 3 + TP1 check + max SL
  src/components/execution.py             # safe_place_order, partial closes
  src/components/orchestrator.py          # Session loop, KZ management
  src/prompts/primary_analyzer_prompt.py  # PA prompt with TP1 rule
  src/utils/file_versioning.py            # Timestamped outputs
  config/agent_config.yaml                # All configuration
  scripts/replay_session.py              # Historical replay with session memory
  scripts/batch_backtest.py              # Batch API backtester
  scripts/analyze_prescreen_kills.py     # Pre-screen analysis
  data/XAUUSD_*.csv                      # Historical candle data (M15/H1/H4/D1)
  knowledge_base_backtest/analysis/       # All analysis reports (versioned)
  knowledge_base_backtest/analysis/INDEX.md  # Report index
  docs/preflight_checklist.md            # Launch day checklist
```

### Windows (production/demo machine)
```
~/Documents/ai-trading-agent/            # Same codebase, synced
  # All fixes from this session verified present
  # MT5 installed, demo account connected
  # Run with: python run_agent.py --mode demo
```

---

## DECISION LOG (Updated)

| Date | Decision | Reasoning |
|------|----------|-----------|
| Apr 1 | Kill session_sweep | 81 trades, -0.051R, confirmed loser |
| Apr 1 | Kill vision mode | -4.87R swing vs JSON-only |
| Apr 1 | Kill tick volume | No signal differentiating winners/losers |
| Apr 1 | Confirm ob_retest | 101 trades, p=0.014 (pre-TP1-fix, now invalidated) |
| Apr 1 | Confirm session memory | +0.66R vs +0.33R (pre-TP1-fix) |
| Apr 2 | TP1 bug discovered | 70% of trades had TP1 < 2.0R. Root cause: prompt |
| Apr 2 | TP1 fix deployed | Prompt rule + safety check + max SL gate |
| Apr 2 | Disable breaker_retest | 0W/3L across all testing, 12/13 CANDIDATEs safety-rejected |
| Apr 2 | Revert London KZ to 09:30 | Extended window: 0 trades in 130+ dates |
| Apr 2 | Fix max_trades_per_day | Was 1 in config, should be 2 |
| Apr 2 | Shelve 1E pre-screen loosening | Too much architectural risk for ~1.4 trades/month |
| Apr 2 | Shelve 1A/1B/EURUSD | Foundation must be proven first |
| Apr 2 | p=0.246 after supplementary | Statistical significance lost. Need Phase 0 diagnostic |
| Apr 2 | Phase 0 designed | Naive baseline + DXY diagnostic before any further optimization |

---

## STANDING RULES (NON-NEGOTIABLE)
1. Never re-run in-sample data to validate fixes — fresh data only
2. safe_place_order pattern is sacred — never retry without checking positions
3. Each improvement tested independently before stacking
4. Statistical significance (p < 0.05) required before risking real capital
5. File versioning on all outputs — never overwrite analysis files
6. The AI picks direction; risk management creates the edge
7. Plan on the floor (2-3 trades/month), execute toward ceiling (5-8)
8. Every spending decision justified by data
9. Treat funded challenge as $500 experiment, not as "going live"

---

## WHAT THE NEXT SESSION SHOULD DO

1. **Read this document + master_roadmap.md + architecture.md** to get full context
2. **Run Phase 0** — the naive baseline prompt is ready at the path described above, or ask Borhen for it
3. **Interpret Phase 0 results** and make the GO/HOLD/RETHINK decision
4. **If GO:** proceed to Phase 1 (TP calibration forward test)
5. **If RETHINK:** investigate where the AI's value actually lies before optimizing

The demo is running on Windows concurrently. Any demo results should be logged and analyzed separately from replay data.

---

## CRITICAL CONTEXT THE NEXT SESSION MUST UNDERSTAND

**The biggest risk is not a code bug — it's deploying a system we don't understand.** The AI shows directional skill (MFE evidence) but we haven't proven it outperforms naive trend-following. Gold went up 100% during testing. Every trade was LONG. The system might just be an expensive way to buy dips in a bull market.

Phase 0 answers this. It costs nothing. It takes one Claude Code session. Until it's done, everything else is optimization of a potentially illusory edge.

**The second biggest risk is premature optimization.** The deep analysis found many "patterns" — Thursday weakness, A+ underperformance, SL distance thresholds, patience filters. At n=36-40, most of these are noise. The Friday finding (86% WR) was directly contradicted by the supplementary run (0/4 Fridays won). Don't act on any finding until it validates on fresh, independent data.

**The system is mechanically ready for production.** The audit is clean, the safety checks work, the execution pipeline is verified. The only question is whether the STRATEGY makes money. That's what Phase 0-5 answers.
