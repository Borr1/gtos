# Trading Agent — Session Handoff (April 4-6, 2026 — Research Marathon & Implementation)
# For: Next Claude session continuing strategic + implementation work

---

## WHO YOU ARE

Strategic trading mentor, technical coach, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Pressure test EVERY prompt before presenting. Challenge sloppy reasoning. When you disagree, say so clearly.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur (UTC+8) building a fully autonomous XAUUSD/GBPUSD AI trading agent using SMC/ICT methodology with Claude API (Sonnet) as reasoning engine and MetaTrader 5 for execution.

**Project started:** March 28, 2026 (9 days ago)
**Current state:** Deployed on FTMO free trial demo, awaiting first live trade with updated prompt

---

## WHAT HAPPENED THIS SESSION (Apr 4-6, 2026)

Marathon research, verification, and implementation session spanning the weekend (markets closed). Two independent Claude reviewer sessions cross-checked all findings and converged on every decision. Five major errors were caught and prevented before they reached live trading.

### Session Flow
1. Reviewed deep dive analysis outputs (8-phase, 23 JSONs, 13 MDs)
2. Discovered Monte Carlo table had 5/6 rows wrong in master report
3. Discovered at_ob direction was REVERSED in master report (positive → actually negative)
4. Designed and executed Layer 2 independent verification (15 recomputations from raw data)
5. Designed and executed Layer 3 pressure test (8/8 spot-checks PASS)
6. Ran 4 final resolution tests (H4 at OB level, impulse distribution, align in trades, WR decay)
7. Ran FTMO spread check and optimization (74 days M1 data)
8. Confirmed model config (Sonnet everywhere, no mismatch)
9. Implemented 4 prompt changes (creates_fvg, OTE removal, at_ob caution, impulse ≤7)
10. Switched to FTMO demo account, re-extracted all candle data
11. Researched prop firms for gold EA trading
12. Submitted D1-unclear batch test (14 trades, all 6 verification checks pass)
13. Implemented permanent D1 pre-screen removal (code + prompt + tests)
14. Comprehensive strategic assessment with honest expectancy calculations

---

## CRITICAL ERRORS CAUGHT AND PREVENTED

| # | Error | Impact if Missed | How Caught |
|---|-------|-----------------|-----------|
| 1 | Monte Carlo table: 5/6 rows wrong | Wrong risk sizing for prop firm | Cross-checking JSON vs MD report |
| 2 | at_ob direction reversed in report | Would BOOST confidence on momentum-absorbing setups | Layer 2 recomputation from raw data |
| 3 | Impulse guidance "1-2 candles" | Zero OBs exist with ≤2 candles; AI told to look for nonexistent pattern | Final test B: actual distribution min=4, median=7 |
| 4 | Spread gate $0.30 blocks 100% of FTMO | System runs for weeks producing zero trades silently | FTMO spread check on Windows |
| 5 | D1 batch test: prompt-level U1 still blocks | Batch wastes $15-20 for 100% NO_TRADE results | Other reviewer session caught dual-level D1 filter |

---

## VERIFIED SYSTEM METRICS (Computed 3x Independently)

### Trade Population
- **Total:** 129 trades (105 XAUUSD, 24 GBPUSD)
- **XAUUSD:** WR=61.0%, mean R=+0.204, PF=1.69
- **GBPUSD:** WR=66.7%, mean R=+0.600
- **Combined:** WR=62.0%, mean R=+0.278, PF=1.94
- **Kelly half:** 9.91%

### Stability / Decay
- First half: WR=67.2%, mean R=+0.372 (n=64)
- Second half: WR=58.5%, mean R=+0.185 (n=65)
- Discovery: WR=64.8% (n=54)
- Validation: WR=58.8% (n=51)
- Decay: 6-9pp, temporal not price-driven, London decayed more
- **Conservative planning estimate: 59% WR, +0.154R after FTMO spread**

### Quarterly Breakdown (XAUUSD meaningful quarters only)
- 2025-Q1: n=41, WR=73.2%, mean R=+0.388 ← PEAK
- 2025-Q2: n=14, WR=71.4%, mean R=+0.865
- 2025-Q4: n=22, WR=63.6%, mean R=+0.362
- 2026-Q1: n=32, WR=59.4%, mean R=+0.138 ← current state

### Monte Carlo (XAUUSD-only, 105 trades — USE THESE for prop firm decisions)
| Risk | P(Pass +8%/-5%) | P(DD>5%) | Median Final |
|------|----------------|----------|-------------|
| 0.50% | 72.2% | 7.9% | $110,392 |
| 0.75% | 77.5% | 34.6% | $115,799 |
| 1.00% | 71.9% | 64.1% | $121,434 |

---

## 7 CONFIRMED DISPLACEMENT FEATURES (Bonferroni-surviving, n=7,496)

| Feature | Effect | Disc/Val | Status |
|---------|--------|----------|--------|
| align (0-4 TF consensus) | +7.5pp / +9.4pp | Validates UP | In prompt as confidence modifier (not gate) |
| creates_fvg | +11.0pp | +11.8 / +10.2 | ✅ DEPLOYED in prompt |
| at_ob | -5.6pp (NEGATIVE) | -7.4 / -3.6 | ✅ DEPLOYED as CAUTION |
| ct (counter-trend) | -5.1pp | -1.8 / -8.0 (unstable) | Small penalty, lowest priority |
| direction | +8.6pp (bullish > bearish) | Present | Not actionable (system trades in displacement direction) |
| fvg_pct | +3.2pp | +3.2 / +4.4 | Likely redundant with creates_fvg |
| origin_revisited | -54.1pp | Validated | Semi-outcome, tautological — DO NOT USE |

---

## 17 CONCEPTS KILLED

Silver Bullet (p=0.31/0.81), OTE zone (p=0.61), Judas Swing (n=7), Consolidation (p=0.824), Breaker Blocks (40.2% below baseline), Rejection Blocks (31.3%), Volume Imbalance (24.7%), H4 alone (p=0.50), D1 alone (p=0.93), BE stop (net negative all triggers), NY KZ extension (p=0.52), DOW filtering (p=0.10), Body ratio threshold (no consistent threshold), FVG size (p=0.57), Chart vision (hurt performance), Session sweep (negative expectancy), Bull/Bear debate (approved losers, rejected winners).

---

## 12 CONCEPTS CONFIRMED ALIVE

OB Retest framework (72.8%), creates_fvg (+11pp), align ≥2 (+7.5/+9.4pp), Impulse ≤7 (85% vs 55%), at_ob caution (-5.6pp), ct penalty (-5.1pp), FVG 80-100% fill (71.4%), FVG additive dates (+35%), Session memory (~2x expectancy), AI TP targets (outperform fixed), Partial close 50/25/25 (validated), D1-unclear tradeable (Fisher p=0.568).

---

## ALL CHANGES DEPLOYED (Committed to Git)

### Prompt Changes (primary_analyzer_prompt.py)
1. **U1 modified:** Allows D1-unclear with H4+H1 consensus fallback
2. **U2 modified:** H4 becomes primary reference when D1 unclear
3. **U4 modified:** References "established bias" not "Daily bias"
4. **Step 1 modified:** States bias source used
5. **OB1 modified:** "Aligned with established directional bias" not "D1 bias"
6. **BR1 modified:** References U1/U2 instead of hardcoding "D1 must be clear"
7. **QUALITY SIGNALS section added** (between frameworks and grading):
   - creates_fvg as positive signal (+11%)
   - at_ob as caution signal (-5%)
   - Impulse ≤7 candles preferred (85% vs 55%)
8. **OTE zone removed** from OB4 (was "ideally in 62-79% OTE zone")

### Code Changes
- **orchestrator.py:** Pre-screen allows D1-unclear when H4 is clear
- **batch_backtest.py:** Same pre-screen logic + updated stats labels
- **agent_config.yaml:** max_spread_cents: 100 (was 30)

### Test Updates
- 4 test files updated for new D1-unclear behavior
- Trade count updated (105 → 119 after D1-unclear batch)
- 601 tests passing, 1 pre-existing failure (spread config, unrelated)

---

## FTMO ACCOUNT STATUS

- **Account:** FTMO free trial demo, Account MetriX 1513001239
- **Size:** $100,000
- **Status:** Ready, 0 trades taken
- **Data:** All candle exports re-done from FTMO feed (different LP from old broker)
- **Spreads:** M1 median $0.39 during KZ (much tighter than tick-level suggests)
- **Model:** Sonnet confirmed everywhere (claude-sonnet-4-20250514)

---

## D1-UNCLEAR BATCH TEST RESULTS

- **Dates tested:** 80 D1-unclear dates
- **Trades produced:** 14 (from 16 CANDIDATEs, 2 rejected by grade gate)
- **WR:** 71.4% (10W / 4L)
- **Total R:** +6.64
- **Mean R:** +0.47 (outlier-adjusted: +0.103)
- **Fisher exact test vs D1-clear:** p=0.568 (no significant difference)
- **Bias source:** 13/14 used H4+H1 consensus correctly
- **Date distribution:** Spread across 6 quarters, 9 months (not clustered)
- **Decision:** D1 pre-screen removed permanently

### Expected Frequency Impact
- Before: ~3.5 XAUUSD trades/month
- After: ~5.6 XAUUSD trades/month (+60%)
- If FVG Fill added: ~7.6 trades/month (2.2x original)

---

## SPREAD OPTIMIZATION RESULTS

- **Data source:** 74 days of FTMO M1 data with spread column
- **London median:** $0.39, NY median: $0.39 (at M15 candle close)
- **Optimal threshold:** $1.00 (100% pass rate, max observed $0.99)
- **Spread cost:** 26.2% of edge at SL=$8, 35% at SL=$6
- **Dual thresholds:** 0% improvement over single
- **Decision:** max_spread_cents = 100

### Tick vs M1 Discrepancy
- Windows tick data showed $0.60-$1.60 median
- M1 candle-close data shows $0.39 median
- Explanation: Ticks capture all spread spikes; M1 close captures the calm moment
- System evaluates at candle close → M1 number is the relevant one
- **Monitor actual spread at entry during first live week to validate**

---

## PROP FIRM RESEARCH

### Recommendation: FTMO 2-Step, $50K
- **Why FTMO:** Data already validated on FTMO feed, EAs allowed, proven payouts
- **Why 2-Step over 1-Step:** Static DD (not trailing), no Best Day Rule
- **Why $50K over $100K:** Lower fee risk while validating live performance
- **Why not yet:** Need 15-20 live demo trades first

### Firms Eliminated
- **Funding Pips:** EA restriction bans full automation (only trade/risk management EAs)
- **FTMO 1-Step:** Trailing EOD drawdown dangerous for gold's volatile winning profile; 50% Best Day Rule punishes low-frequency systems

### Key FTMO Rules for System Compliance
- EAs allowed (proprietary strategies)
- No time limit on evaluation
- 5% daily DD, 10% max DD (2-Step, static)
- 10% Phase 1 target, 5% Phase 2 target
- Min 4 trading days per phase
- News trading: unrestricted during challenge
- 80% profit split → 90% with scaling

---

## HONEST EXPECTANCY PICTURE

```
Conservative WR (validation period):          59%
XAUUSD mean R:                                +0.204
FTMO spread cost:                             -0.05R
Adjusted mean R:                              +0.154R

Current frequency:                            ~5.6 trades/month
Expected monthly R:                           +0.862R/month

At 1.0% risk on $100K:
  Monthly expected:                           +$862
  Annual expected:                            +$10,349

Prop firm timeline (FTMO 2-Step $50K at 1.0% risk):
  Phase 1 (+$5,000): ~33 trades = ~6 months
  Phase 2 (+$2,500): ~16 trades = ~3 months
  Total: ~9 months at current frequency
  With FVG Fill (~7.6/month): ~6 months total
```

---

## WHAT'S PENDING (Priority Order)

### Tier 1 — This Week
1. **Observe live trading Mon-Fri.** Don't touch the system. Record every decision. Manually verify 2-3 on TradingView. Log actual spread at entry.
2. **Collect first 5+ live trades** with updated prompt + D1 removal + FTMO spreads
3. **Monitor:** Is the system producing CANDIDATEs on D1-unclear days? What bias source does it cite?

### Tier 2 — Next Weekend
4. **FVG Fill framework batch test** ($15-20) — next frequency lever, adds ~2 trades/month
5. **Review first live trades** — compare to backtest expectations
6. **If WR < 55% on 10+ trades:** investigate, don't add more changes

### Tier 3 — After 15-20 Live Trades
7. **Align score injection** — compute in orchestrator, inject as context (code change, not prompt)
8. **CT counter-trend penalty** — small penalty, lowest priority
9. **Consider FTMO paid challenge** ($50K 2-Step) if live WR ≥ 55%
10. **SHORT direction validation batch** ($5-12) — currently LONG-only

### Tier 4 — Future
11. **Multi-instrument:** GBPUSD has 24 validated trades but needs more
12. **Economic calendar integration** — MQL5 export script ready, not compiled
13. **Agent factory architecture** — multi-agent, multi-instrument parallelism
14. **NAS100 expansion** — if OB Retest validates on indices

---

## KEY FILES

### Verified Analysis Outputs (AUTHORITATIVE — use these, not the original master report)
```
knowledge_base_backtest/analysis/deep_dive_20260406/verified/
  recomputation_results.json          — 15 independent checks from raw data
  comparison_results.json             — Prior JSON vs recomputed (18 match, 0 mismatch)
  corrected_master_findings.md        — THE authoritative findings document
  corrected_prompt_changes.md         — THE authoritative prompt changes
  align_investigation.md              — What align measures (0-4 TF consensus)
  layer3_pressure_test.json           — 8/8 PASS
  final_tests/final_test_results.json — H4, impulse, align, decay results
```

### Spread Optimization
```
knowledge_base_backtest/analysis/spread_optimization/
  spread_optimization_results.json    — Full optimization with pressure tests
  ftmo_spread_check.json              — Raw FTMO tick-level spreads (10 days)
```

### D1-Unclear Batch
```
knowledge_base_backtest/analysis/d1_unclear_batch/
  batch_metadata.json                 — Dates submitted, batch ID
  dates_identified.json               — 80 D1-unclear dates
```

### Original Analysis (USE WITH CAUTION — master report has errors)
```
knowledge_base_backtest/analysis/deep_dive_20260406/
  monte_carlo_20260406.json           — Correct JSON (report table was wrong)
  displacement_feature_screen_20260406.json — Correct JSON
  mfe_time_profile_20260406.json      — Correct JSON
  deep_dive_master_20260406.md        — HAS ERRORS (at_ob direction, MC table)
  prompt_changes_ready_20260406.md    — HAS ERRORS (impulse 1-2, at_ob positive)
```

### System Code
```
src/prompts/primary_analyzer_prompt.py  — Updated with all changes
src/components/orchestrator.py          — D1 pre-screen modified
scripts/batch_backtest.py               — D1 pre-screen modified
config/agent_config.yaml                — max_spread_cents: 100
```

---

## STANDING RULES

1. **Pressure test every prompt before presenting.** Switch to critic mode, try to break it, list issues, fix them, show what was found and fixed.
2. **Use XAUUSD-only Monte Carlo** for prop firm decisions if deploying single instrument.
3. **Use 59% WR as conservative planning estimate**, not 62%.
4. **First 20 live trades are CALIBRATION**, not confirmation.
5. **Don't stack prompt changes without batch testing.**
6. **Three-layer verification protocol** for any future analysis that drives decisions.
7. **The corrected_master_findings.md is the authoritative document**, not the original deep_dive_master.

---

## TWO-REVIEWER CONVERGENCE PROTOCOL

This session used two independent Claude reviewer sessions that cross-checked each other's work. Both sessions:
- Agreed on all 6 prompt changes and their priority
- Agreed on D1 removal as permanent
- Agreed on align as modifier not gate (24% of trades would be filtered)
- Agreed on XAUUSD-only Monte Carlo for prop firm decisions
- Agreed on 59% WR as conservative estimate
- Agreed on FTMO 2-Step $50K as prop firm recommendation
- Agreed on $1.00 max_spread
- Agreed that the research phase is complete — shift to live observation

The only divergences were in emphasis (urgency of WR decay investigation) and architecture (pre-filter vs prompt for align), both of which were resolved through data.

---

## THE NARRATIVE (Both Sessions Agreed)

H1 order blocks on gold have a 73% base rate of continuation when retested. The AI adds value by filtering which retests to trade based on multi-timeframe context, producing 62% WR at +0.28R per trade (59% / +0.15R after spread and decay adjustment). The prompt changes improve the filter; the D1 removal and future FVG Fill framework expand the opportunity set. The edge is real, thin, and requires disciplined execution to capture.

**The system is ready to trade. Let it prove itself.**
