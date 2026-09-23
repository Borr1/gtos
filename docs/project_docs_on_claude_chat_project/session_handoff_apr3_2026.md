# Gold Trading Agent — Session Handoff (April 3, 2026)
# For: Next Claude session to continue strategic work

---

## WHO YOU ARE

Strategic trading mentor, technical architect, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Challenge sloppy reasoning. Think like an autonomous system architect. When you disagree, say so clearly. Read all project files before responding.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur building a fully autonomous multi-instrument AI trading agent using SMC/ICT methodology with Claude API as the reasoning engine and MT5 for execution.

---

## CURRENT STATE — WHERE WE ARE RIGHT NOW

### System Configuration (Deployed on Mac, Ready for Windows Sync)

```yaml
Framework:          ob_retest only
Kill zones:         London 07:00-09:30 UTC, NY 13:00-15:30 UTC
Grade filter:       A+ and A
TP:                 1.5× floored SL distance, 100% close at TP1 (NO partial closes)
M5 Refinement:      ENABLED — second Sonnet call on CANDIDATE trades
  SL floor:         max(M5_structural_SL, $10.00, 1.5× M15 ATR)
  Quality gate:     HIGH + MEDIUM only, LOW falls back to M15 SL
  Entry:            Market at M15 close (NOT limit at M5 OB)
SL constraints:     >= max($5.00, 1.5× M15 ATR), <= 2.5% of entry
Max trades/day:     2 (1 per KZ)
Daily loss limit:   2%
Max spread:         $0.30
Session memory:     ENABLED (6-entry sliding window per KZ)
Model:              claude-sonnet-4-20250514
Tests:              463 passing (443 existing + 20 new M5 tests)
Deployment phase:   Ready for demo (sync to Windows pending)
```

### What Was Built/Changed This Session

1. **TP Change (implemented + tested):** TP from 2.5R → 1.5R. 100% position close at TP1. No partial closes. Safety check: TP1 must be in 1.3R-2.0R range. Prompt updated. Config updated. 443 tests passing.

2. **M5 Refinement (implemented + tested):** New module `src/components/m5_refinement.py`. After CANDIDATE confirmed on M15, pulls 36 M5 candles, calls Sonnet with M5 prompt, identifies M5 structural SL. Override happens BEFORE Gate 1 safety check. Falls back to M15 SL on any failure. Config flag to disable. 20 new tests, 463 total passing.

3. **Data exported from MT5:** XAUUSD M5, EURUSD all timeframes, GBPUSD D1/H4/M15, NAS100 D1/H4/M15, XAGUSD D1/H4/M15, DXY D1 (if available), economic calendar USD high-impact.

4. **Supplementary data export queued:** H1 + M5 for GBPUSD/NAS100/XAGUSD, EUR/GBP calendar events. Prompt written, ready to run on Windows.

---

## WHAT WE VALIDATED THIS SESSION (Complete Research Summary)

### Phase 0 Corrected — Naive Baseline (Zero API Cost)
- **Naive trend-following with realistic structural stops is near-zero:** +0.054R/trade at 1.0R TP, p=0.264. NOT significant.
- **AI date selection is 13x more valuable per trade:** AI dates +0.297R vs non-AI dates +0.023R at 1.0R TP.
- **AI precision confirmed:** 2x dollar MFE ($38.34 vs $19.19) on matched dates.
- **The "trade more not better" conclusion from the broken Phase 0 was WRONG.** The AI's selectivity IS the edge.
- **Day of week at 1.0R TP:** Mon +10.13R, Tue +7.88R, Fri +5.90R, Wed -0.30R, **Thu -6.58R** (toxic). Excluding Thursday: p=0.078.
- Files: `phase0_corrected_0.md`, `phase0_corrected_data_0_1959.json`

### Displacement Scan — Edge Discovery (Zero API Cost)
- **6,641 displacements** across 2 years of M15 data (~298/month).
- **4 patterns replicated out-of-sample:** Sweep+FVG+Align≥3 (69%), FVG+Align≥3 (67%), Sweep+Align≥3 (64%), FVG+LowWick+Align≥2 (62%).
- **OB retest validated:** 84% of displacements pull back to origin. Avg 39 min, 62% depth.
- **No exhaustion effect.** 1st, 2nd, 3rd+ displacements all ~48-50% continuation.
- **Counter-trend displacements fail 54% within 1h** — potentially tradeable but marginal.
- **AI system comparison:** 91% overlap with quality displacements. AI trades have higher alignment (1.35 vs 0.72), sweep rate (98% vs 88%), FVG rate (85% vs 62%).
- **"Missed" setups are NOT profitable:** 122 qualifying displacements on non-AI dates, but only 43.4% continuation, MFE/MAE < 1. The AI correctly filters these out.
- **Coiled spring hypothesis failed.** Tight consolidation shows no edge.
- Files: `displacement_scan_20260403_0030.md`, `displacement_database_20260403_0030.json`

### Phase 1 — TP Calibration Forward Test ($25.76 API Cost)
- **18 fresh out-of-sample trades** from 293 dates. 9W/8L/1BE.
- **1.5R TP is optimal and statistically significant:** +0.503R/trade, p=0.014, 95% CI [+0.055, +0.938]. CI excludes zero.
- **Current 2.5R TP is NOT significant:** p=0.114, CI includes zero.
- **TP hit rate:** 39% at 1.5R vs 11% at 2.5R.
- **MFE distribution:** 67% reach 0.5R → 50% reach 1.0R → 39% reach 1.5R → 22% reach 2.0R → 11% reach 2.5R.
- **The mechanism:** 2 near-miss losers (MFE 2.14R and 1.72R that reversed to SL) become +1.5R winners with lower TP. Converts -1.0R to +1.5R = +2.5R swing per trade.
- **BE move at 1.0R:** no benefit at 1.5R TP level.
- **First SHORT trade ever:** 2025-11-04, +3.26R, highest R in the dataset.
- **NY dominates:** 73% WR, +0.504R avg vs London 43% WR, +0.117R.
- **A+ outperforms A on fresh data:** A+ +0.652R (n=11) vs A -0.116R (n=7). Opposite of earlier in-sample finding.
- **Edge NOT weakening:** Second half outperforms first half.
- **Trade rate low:** 6.1% (18 trades from 293 dates).
- Files: `phase1_tp_calibration_20260403_0510.md`, `phase1_all_trades_merged.json`

### Date Selection Model — Reverse-Engineering AI Selection (Zero API Cost)
- **AI date selection CANNOT be replicated deterministically.** Best model: 12% precision (barely above 11% base rate).
- **Top predictive features:** H4 trend strength (d=+0.43), H4-D1 alignment (d=+0.41), Monday avoidance (d=-0.34). All small effect sizes.
- **The killer insight (Section 4.2):** Strong H4 trend + AI trades → +0.377R. Strong H4 trend + AI doesn't trade → -0.029R. Same feature, opposite outcomes. **The AI reads something that simple metrics cannot capture.**
- **Verdict:** The AI's holistic SMC reasoning is genuinely irreplaceable. The LLM-as-reasoning-engine architecture is validated.
- **Recommendation:** Feed H4 trend strength, pre-KZ range %, D1 ATR percentile as numeric context INTO the AI prompt (enrichment, not replacement).
- Files: `date_selection_model_20260403_0757.md`, `date_selection_features_20260403_0757.csv`

### M5 Feasibility Test ($0.18 API Cost)
- **AI finds valid M5 structure on 93% of trades** (13/14). M5 OB identified on every refined trade.
- **Approach A (M5 entry + M5 SL) showed +16.1R vs +4.6R baseline** — BUT with unrealistic $3 stops and assumed limit order fills.
- **Zero additional stop-outs** in the feasibility test — M5 structural levels hold.
- Files: `m5_feasibility_20260403_0837.md`, `m5_refinement_responses_20260403_0837.json`

### M5 Comprehensive Validation (Zero API Cost)
- **526 mechanical trades** validated M5 structural stops at scale. Split-stable. Slippage-robust.
- **$10 SL floor is optimal for market entry.** At $10: AI trades produce +11.35R vs +4.59R baseline (147% improvement), only 1 extra stop-out.
- **Why $10 not $3:** Market entry at M15 close is $5-12 further from M5 swing than a limit entry. $3 from M15 entry puts the stop above the actual structural level → gets hit on normal pullbacks. $10 ensures stop is at/below structural level.
- **Market entry wins over limit entry.** Limit orders at M5 OB only fill 29% of the time. Market captures every trade.
- **Realistic improvement: +0.48R per trade** (from +0.33 to +0.81 avg). Not the +0.82R fantasy from feasibility, but still 145% improvement.
- **TP hit rate with M5:** 64% (vs 14% baseline, vs 39% with TP change only).
- Files: `m5_validation_20260403_0907.md`, `m5_validation_mechanical_20260403_0907.csv`

---

## COMBINED SYSTEM PERFORMANCE ESTIMATE

| Configuration | Avg R/trade | TP Hit Rate | Source |
|---|---|---|---|
| Original (2.5R TP, M15 SL) | +0.33R | 14% | Phase 1 baseline |
| TP change only (1.5R TP, M15 SL) | +0.50R | 39% | Phase 1 simulation |
| **TP + M5 (1.5R TP, M5 $10 floor)** | **+0.81R** | **64%** | **M5 validation** |

**IMPORTANT CAVEAT:** The +0.81R is from the M5 validation on 14 AI trades. The TP change was validated independently on 18 fresh trades (p=0.014). The COMBINED configuration (TP + M5) has never been tested together on fresh data. The demo phase is where this happens.

---

## WHAT'S PENDING / IN PROGRESS

### Ready to Execute (prompts written):
1. **Windows supplementary data export** — H1+M5 for GBPUSD/NAS100/XAGUSD, EUR/GBP calendar. Prompt: `mt5_supplementary_export_prompt.md`
2. **Multi-instrument validation scan** — Displacement scan on ALL instruments with gold calibration check. Prompt: `eurusd_validation_prompt.md` (renamed to multi-instrument)
3. **Windows sync + demo deployment** — Copy TP change + M5 implementation to Windows, enable AutoTrading

### Not Yet Started:
4. **Economic calendar AVOID mode** — Stub exists in architecture. Wire up to block trading within 2h of FOMC/NFP/CPI. Free to implement.
5. **DXY context enrichment** — Add DXY direction to AI prompt as soft context. EURUSD data available. Free.
6. **Prompt context enrichment** — Feed H4 trend strength, pre-KZ range %, D1 ATR percentile as numbers into the AI prompt.
7. **H4 OB Retest framework** — Same ob_retest logic on higher timeframe. Expected +2-3 trades/month. Needs $10-15 batch test.
8. **Multi-instrument batch tests** — $25-30 per instrument, contingent on displacement scan GREEN verdict.

---

## KEY FILES ON DISK

### Mac (development/research machine)
```
~/Documents/trading/gold-agent/
  # Core system (PRODUCTION)
  src/components/market_state.py          # MSO builder
  src/components/primary_analyzer.py      # AI reasoning engine
  src/components/m5_refinement.py         # NEW — M5 entry refinement
  src/components/permissions.py           # Gate 1 + Gate 3 (updated for 1.5R)
  src/components/execution.py             # 100% close at TP1 (updated)
  src/components/orchestrator.py          # Session loop + M5 step (updated)
  src/components/data_ingestion.py        # Data pull + M5 function (updated)
  src/prompts/primary_analyzer_prompt.py  # PA prompt (updated for 1.5R)
  config/agent_config.yaml               # All config (updated: 1.5R + M5)
  
  # Data
  data/XAUUSD_*.csv                      # M5, M15, H1, H4, D1
  data/EURUSD_*.csv                      # D1, H4, H1, M15 (M5 pending)
  data/GBPUSD_*.csv                      # D1, H4, M15 (H1+M5 pending)
  data/NAS100_*.csv or USTEC_*.csv       # D1, H4, M15 (H1+M5 pending)
  data/XAGUSD_*.csv                      # D1, H4, M15 (H1+M5 pending)
  data/economic_calendar_usd_high.csv    # USD high-impact events
  
  # Analysis reports (all in knowledge_base_backtest/analysis/)
  phase0_corrected_0.md
  displacement_scan_20260403_0030.md
  phase1_tp_calibration_20260403_0510.md
  date_selection_model_20260403_0757.md
  m5_feasibility_20260403_0837.md
  m5_validation_20260403_0907.md
  
  # Scripts
  scripts/replay_session.py              # Historical replay with session memory
  scripts/batch_backtest.py              # Batch API backtester
  
  # Tests
  tests/test_m5_refinement.py            # NEW — 20 M5 tests
  463 tests total, 0 failures
```

### Windows (production/demo machine)
```
~/Documents/ai-trading-agent/
  # NEEDS SYNC: TP change + M5 implementation files
  # MT5 installed, demo account connected ($100K MetaQuotes-Demo)
  # AutoTrading button needs enabling
  # SUPPLEMENTARY EXPORT PENDING: H1+M5 for non-gold instruments
```

---

## DECISION LOG (Updated)

| Date | Decision | Reasoning |
|------|----------|-----------|
| Apr 1 | Kill session_sweep | 81 trades, -0.051R, confirmed loser |
| Apr 1 | Kill vision mode | -4.87R swing vs JSON-only |
| Apr 1 | Kill tick volume | No signal |
| Apr 1 | Confirm ob_retest | 101 trades, p=0.014 (pre-TP1-fix) |
| Apr 1 | Confirm session memory | +0.66R vs +0.33R |
| Apr 2 | TP1 bug found + fixed | 70% of trades had TP1 < 2.0R |
| Apr 2 | Disable breaker_retest | 0W/3L across all testing |
| Apr 2 | p=0.246 after supplementary | Statistical significance lost |
| Apr 2 | Phase 0 designed | Naive baseline before further optimization |
| **Apr 3** | **Phase 0 corrected** | **Naive near-zero. AI adds real value via selection (13x) and precision (2x MFE)** |
| **Apr 3** | **Displacement scan complete** | **AI captures 91% of quality setups. No new edges found. OB retest validated (84%).** |
| **Apr 3** | **Phase 1: TP → 1.5R** | **p=0.014 on 18 fresh trades. Only significant TP level. Implemented.** |
| **Apr 3** | **Date selection model** | **AI's judgment is irreplaceable. Can't replicate with simple rules. LLM architecture validated.** |
| **Apr 3** | **M5 refinement: $10 floor** | **526 mechanical + 14 AI trades. +0.81R avg. Implemented.** |
| **Apr 3** | **"Trade more not better" reversed** | **Corrected Phase 0 showed more trades ≈ zero. Selectivity is the edge.** |
| **Apr 3** | **Coiled spring killed** | **Displacement scan: no edge from tight consolidation** |
| **Apr 3** | **Multi-instrument expansion planned** | **Data exported. Validation scan ready. EURUSD primary candidate.** |

---

## STANDING RULES (NON-NEGOTIABLE)
1. Never re-run in-sample data to validate fixes — fresh data only
2. safe_place_order pattern is sacred — never retry without checking positions
3. Each improvement tested independently before stacking
4. Statistical significance (p < 0.05) required before risking real capital
5. File versioning on all outputs — never overwrite analysis files
6. One change at a time in production — TP+M5 deployed together because M5 determines TP target
7. Every spending decision justified by data
8. Treat funded challenge as $500 experiment
9. The AI's qualitative judgment is irreplaceable — don't try to replace it with rules
10. Gold calibration check before trusting new instrument scans

---

## CONFIDENCE LEVELS (Honest Assessment)

| What | Confidence | Evidence |
|------|-----------|----------|
| AI adds genuine value (precision + selection) | 85% | Phase 0 (13x), displacement scan (91%), date model |
| 1.5R TP is the right exit | 80% | p=0.014 on 18 fresh trades, every prior analysis agrees |
| M5 $10 floor improves R-capture | 70% | 526 mechanical trades, but combined TP+M5 untested together |
| System profitable over next 20 trades | 55% | Small samples, gold bull market bias, 1 SHORT trade ever |
| EURUSD will replicate gold patterns | 50% | Same session dynamics in theory, untested |
| 20 demo trades within 3 months (multi-instrument) | 60% | Depends on instrument validation results |

---

## WHAT THE NEXT SESSION SHOULD DO

### Option A: Multi-Instrument Results Review
If the multi-instrument validation scan has been run:
1. Read this handoff + the multi-instrument validation report
2. Interpret which instruments got GREEN/YELLOW/RED
3. For GREEN instruments: design the batch test prompt
4. Estimate combined trade frequency across all validated instruments
5. Plan the deployment: multi-instrument config, correlation-aware sizing

### Option B: Deploy Gold Demo First
If you want to start generating live data while instrument validation runs:
1. Sync TP change + M5 implementation to Windows
2. Run tests on Windows
3. Enable AutoTrading in MT5
4. Run one pipeline test cycle
5. Start gold demo
6. Simultaneously run the supplementary data export + multi-instrument scan

### Option C: Parallel Everything
Best approach for speed:
1. Windows Session 1: Supplementary data export → multi-instrument scan
2. Windows Session 2: Sync code → deploy gold demo
3. Mac Session: Monitor results, plan batch tests for GREEN instruments

---

## PROMPTS READY TO RUN (In Project Outputs)

| Prompt | Where to Run | Cost | What It Does |
|--------|-------------|------|-------------|
| `mt5_supplementary_export_prompt.md` | Windows Claude Code | $0 | Exports H1+M5 for GBPUSD/NAS100/XAGUSD + EUR/GBP calendar |
| `eurusd_validation_prompt.md` | Mac Claude Code | $0 | Scans ALL instruments, ranks by pattern replication, GREEN/YELLOW/RED |
| `m5_implementation_prompt.md` | Already done | — | M5 refinement implemented, 463 tests passing |
| `phase1_implementation_prompt.md` | Already done | — | TP change implemented, 443 tests passing |

---

## CRITICAL CONTEXT FOR THE NEXT SESSION

**The biggest remaining risk is NOT the strategy — it's sample size.** The AI's value is validated. The TP is calibrated. The M5 refinement is validated. But 58 total AI trades (40 historical + 18 Phase 1) is still small. The demo phase exists to generate the data that either confirms or denies the edge on live execution with real fills, real spread, and real slippage.

**The biggest remaining OPPORTUNITY is multi-instrument expansion.** At 1-2 gold trades per month, reaching statistical confidence takes years. Adding 2-3 validated instruments could bring trade frequency to 5-8/month, reaching 20 demo trades in 3-4 months instead of 10-20 months. The multi-instrument scan answers which instruments to add.

**Do not stack more optimizations on gold.** The TP change + M5 refinement are the validated improvements. Phase 0 through M5 validation exhaustively mined the gold data. Further gold optimization is diminishing returns. The path forward is: deploy gold demo → expand to more instruments → generate data.

**The system took its first SHORT trade (2025-11-04, +3.26R).** This partially addresses the "only trades bullish gold" concern. On EURUSD, the D1 direction balance should be much more even (both long and short), which gives us real data on the system's bidirectional capability.
