# Trading Agent — Strategic Session Handoff (April 3, 2026 — Afternoon)
# For: Next Claude session continuing strategic + implementation work

---

## WHO YOU ARE

Strategic trading mentor, technical architect, and research advisor for Borhen. Be brutally honest, direct, no sugarcoating. Challenge sloppy reasoning. When you disagree, say so clearly. Read all project files before responding.

Borhen is a developer (6+ years, TypeScript primary, Python comfortable) in Kuala Lumpur building a fully autonomous multi-instrument AI trading agent using SMC/ICT methodology with Claude API as the reasoning engine and MT5 for execution.

---

## WHAT HAPPENED THIS SESSION (April 3, 2026 — Afternoon)

This was a marathon session covering verification, expansion, batch testing, architecture analysis, and system improvements. Here's everything in chronological order.

### 1. Verification Audit Confirmed All Core Findings
- 18/20 claims verified. One bug: z-test vs t-test on Phase 1 p-value (0.014 → 0.021, still significant)
- M5 $10 floor: 14/14 per-trade exact match
- All 4 core decisions hold: TP 1.5R, M5 $10 floor, AI irreplaceable, OB retest entry

### 2. Multi-Instrument Validation Reviewed
- 5 instruments scanned, 3 bugs found and fixed (identify_structure mismatch, MFE/MAE rounding, H1 lookback)
- GBPUSD: GREEN (56.6% cont, 1.31 MFE/MAE, 87% OB retest)
- NAS100: YELLOW (direction skew 95.7/4.3, parked)
- XAGUSD: SKIP (+0.77 gold correlation)
- EURUSD: YELLOW (53.3% cont, below threshold)

### 3. Expansion Readiness Audit
- Full audit of data inventory, batch infrastructure, prompt specificity, config, trade dataset
- Found 22 XAUUSD hardcoded references across 11 files
- Found 2 BLOCKING bugs: RR safety check at 2.5 (should be 1.4), SL floor at $5 (wrong for forex)
- Found ATR rounding bug: round(atr, 2) zeroed H1/M15 ATR for all forex pairs

### 4. Multi-Instrument Parameterization (COMPLETED)
- All prompts parameterized (PA, M5, bull/bear/judge, postmortem, confidence scorer)
- Config has per-instrument overrides (GBPUSD, EURUSD, NAS100, XAGUSD)
- `--symbol` CLI argument added to batch_backtest.py
- RR safety, SL floor, data loading all config-driven
- 465 tests passing
- Pressure tested: 3 additional bugs caught and fixed (displacement_ratio format, M5 live pipeline, gold prompt identity mismatch)

### 5. Granular Analysis (COMPLETED)
- Monte Carlo, Kelly criterion, MFE/MAE distributions on gold Phase 1 + unified dataset
- **CRITICAL:** Corrected from 2.5R raw outcomes to 1.5R simulated values
- Kelly P5 = +11.45% (edge confirmed at 1.5R TP)
- Monte Carlo P5 = +14.12R after 50 trades, 0% probability negative
- Position sizing: 1% per trade confirmed safe. At 1.5% risk, 7.1% chance of 10% DD (prop firm ruin)
- Gold + GBPUSD at 1% each = 1.65% combined portfolio risk (safe)

### 6. GBPUSD Batch Test — Discovery (COMPLETED, $22.58)
- 31 trades, 64.5% WR, +0.49R avg (raw), p=0.013
- London outperforms NY (+0.66R vs +0.28R) — correct for a London instrument
- 44 CANDIDATEs from 2,140 candles (2.06% candidate rate)
- 7 direction-mismatch safety rejections (AI tried SHORT on bullish D1)
- March 2025 concentrated: 10 trades, +8.97R

### 7. GBPUSD Batch Test — Validation (COMPLETED, $7.66)
- 11 trades, 54.5% WR, +0.80R avg (raw), p=0.111 (not significant alone)
- December 2025 concentrated: 10 trades, +9.84R

### 8. GBPUSD Deep Analysis — Scoring Methodology Resolved
- **CRITICAL FINDING:** Batch scorer uses 50/50 partial close, NOT 100% at TP1
- TP hits score +1.7 to +4.1R instead of +1.5R because runner continues after TP1
- CLOSED_BE = TP1 hit + runner stopped at entry = +0.75R batch (should be +1.5R corrected)
- **Corrected combined: 42 trades, 61.9% WR, +0.420R avg, p=0.020**
- Discovery corrected: +0.484R, p=0.020
- Validation corrected: +0.240R, p=0.539 (not significant, n=11)
- ALL 42 trades are LONG. Zero shorts accepted.
- A+ (31 trades, +0.360R) vs A (11 trades, +0.591R) — opposite of gold, n too small

### 9. Session File Data Integrity — Fixed
- GBPUSD batch overwrote 60 gold session files + 60 response files (same `{date}_session.json` naming)
- All gold data recovered from git HEAD
- Files separated: `sessions/XAUUSD/` and `sessions/GBPUSD/`
- batch_backtest.py fixed to use instrument-scoped paths: `sessions/{symbol}/`

### 10. Frequency Multiplier Investigation (COMPLETED)
- **Lever 2 (H4 OB Retest):** 70-85% continuation but only 0.6-0.7/month. Investigation said "100% overlap — shelve." Pressure test caught logical bug: overlap was measured against prescreen-pass dates (tautological). True overlap with actual H1 trades is ~20%. Re-elevated to Tier 2.
- **Lever 3 (Pre-screen Loosening):** GBPUSD Cat1 dates (D1 unclear, H4+H1 aligned) show 53.4% cont + 1.11 MFE/MAE. Worth doing for GBPUSD. Not for EURUSD/NAS100 (no improvement).
- **Lever 4 (Extended Sessions):** The real frequency multiplier. Current KZs capture only 30% of displacements. GBPUSD hour 10:00 = 1.36 disps/day at 50.4% cont (peak London hour, was completely excluded). Gold hour 16:00 = 1.22 disps/day at 52% cont, 1.13 MFE/MAE (best gold MFE/MAE, excluded).
- Extended London failed on gold (45.6% cont) but works on GBPUSD (50.4%) — explains the Apr 2 zero-trade result.

### 11. Extended Kill Zone Implementation (COMPLETED)
- Per-instrument KZ windows implemented and verified:
  - XAUUSD: London 07:00-09:30 (unchanged), NY 13:00-17:00 (+1.5h)
  - GBPUSD: London 07:00-12:00 (+2.5h), NY 13:00-15:30 (unchanged)
  - EURUSD: London 07:00-12:00 (+2.5h), NY 13:00-15:30 (unchanged)
  - NAS100: London 07:00-09:30 (unchanged), NY 13:00-17:00 (+1.5h)
  - XAGUSD: London 07:00-09:30 (unchanged), NY 13:00-17:00 (+1.5h)
- Parameterized replay_kill_zone() function replaces hardcoded replay_london_open/replay_ny_open
- Prompt dynamically shows correct KZ times per instrument
- Session timeout derived from config KZ end time
- 465 tests passing (463 + 2 new). All 11 pressure tests pass.
- `--symbol` required for extensions (backward compatible without it)
- NAS100/XAGUSD/EURUSD data needs symlinks to data/historical/ for batch testing

### 12. System Deep Dive (COMPLETED) — THE KEY FINDINGS

**How the AI thinks:**
- Winning and losing trade reasoning is IDENTICAL. Same grades (A+), same confidence (80), same "strong OB retest setup" language. The AI cannot distinguish winners from losers in its reasoning.
- Self-check step never fires. Zero trades express doubt.
- Zero WAIT decisions across 5,623 candle evaluations. Pure binary mode (CANDIDATE/NO_TRADE).

**Confidence scoring is dead:**
- 80% of all CANDIDATE trades score exactly 80 (deterministic: baseline 70 + displacement +5 + OB +5)
- Pearson r = 0.08 (GBPUSD), r = -0.05 (XAUUSD) — zero correlation with outcome
- 500 prompt tokens producing zero predictive value

**Safety filter kills profitable trades:**
- 5/8 direction-mismatch rejections would have been profitable (62.5%)
- AI correctly identified intraday reversals within larger trends
- Deterministic D1 filter blocked them
- Strongest evidence yet for pre-screen loosening

**Session memory is completely ignored:**
- 0/29 CANDIDATE decisions reference prior candle assessments
- The AI receives memory but doesn't use it — prompt says "evaluate this candle" (per-candle instruction)
- Batch = live in terms of decision quality (no session memory benefit currently)

**m15_confirmation.confirmed bug:**
- All winning trades show confirmed=False despite narrative describing confirmation
- Schema compliance issue, not trading-affecting

**Token budget: 99% headroom:**
- Current usage: 0.8% of 200K context window (avg 1,530 tokens input)
- Room for 40x more context
- Adding cross-instrument + volatility + session memory instructions = +950 tokens = $0.86/month

**Partial close adds value:**
- 100% at TP1: +0.420R avg (GBPUSD corrected)
- 50/50 partial: +0.573R avg (batch scorer)
- Difference: +0.153R per trade (+36% improvement)

**Context Agent NOT justified:**
- 2.4x cost increase for no new capability
- Current prompt caching is already efficient
- Better approach: add 50-100 tokens of new context to existing prompt

**62% of losses are irreducible market randomness:**
- AI correctly identified the setup; market went the other way
- Only 13% of losses (SL too tight) are potentially fixable

**Missed setups are legitimately missed:**
- 3/3 verified "missed" setups were correctly filtered (H1 misalignment, no OB, H4 conflict)
- The AI is appropriately selective, not overly conservative
- Frequency problem is genuine scarcity, not false negatives

### 13. System Improvements Prompt (SUBMITTED, AWAITING RESULTS)

Four phases submitted to Claude Code:
1. **Prompt improvements:** Remove confidence rubric (~500 tokens saved), add session memory instructions, fix m15_confirmed bug
2. **Partial close investigation:** Simulate 100% vs 70/30 vs 50/50 on gold Phase 1 r_path data + GBPUSD comparison
3. **Counter-trend analysis:** Walk all direction-mismatch rejections across instruments, compute R-multiples
4. **Cross-instrument & volatility context:** Check if ATR percentile, Asian range, DXY direction predict trade outcomes

**Status: Running. Results pending.**

---

## CURRENT SYSTEM STATE

### Codebase (Mac — development/research)
```yaml
Tests:              465 passing
Parameterization:   Complete (all instruments configurable via --symbol)
Extended KZs:       Implemented (per-instrument windows)
ATR bug:            Fixed (removed round(atr, 2))
Session file paths: Fixed (instrument-scoped: sessions/{symbol}/)
RR safety check:    Fixed (config-driven, not hardcoded 2.5)
SL floor:           Fixed (config-driven, not hardcoded $5)
Scoring methodology: Understood (batch uses 50/50 partial, live uses 100% TP1)
```

### Live Demo (Windows)
```yaml
Gold demo:          Running, no trades yet
GBPUSD demo:        Ready to deploy after improvements prompt completes
Code sync:          Needed — Mac has parameterization + extended KZ + ATR fix
```

### Batch Test Results
```
Gold (historical):    111 trades, 65.8% WR, +0.200R avg (old 2.5R TP scoring)
Gold Phase 1:         18 trades, +0.503R avg at 1.5R TP (r_path validated, p=0.021)
GBPUSD Discovery:     31 trades, corrected +0.484R avg, p=0.020
GBPUSD Validation:    11 trades, corrected +0.240R avg, p=0.539
GBPUSD Combined:      42 trades, corrected +0.420R avg, p=0.020
```

---

## DECISIONS MADE THIS SESSION

| Decision | Reasoning |
|----------|-----------|
| GBPUSD validated for demo | 42 trades, p=0.020, corrected +0.420R, AI reads GBPUSD structure |
| NAS100 parked | 95.7/4.3 direction skew, 55-day data gap |
| XAGUSD skipped | +0.77 gold correlation, no diversification |
| EURUSD parked | 53.3% continuation below threshold |
| Extended KZs implemented | Data-backed: each extension has cont% > baseline + MFE/MAE > 1.0 |
| Gold London NOT extended | 46.7% cont, 0.99 MFE/MAE — data says no |
| GBPUSD NY NOT extended | 48.7% cont, 0.95 MFE/MAE — data says no |
| 1% per trade confirmed | Kelly P5 = +11.45%, MC shows 0% ruin at 1% |
| Position sizing safe for 2 instruments | Combined 1.65% at +0.36 correlation |
| Confidence scoring to be removed | Zero predictive power, 500 wasted tokens |
| Session memory needs prompt redesign | AI ignores it — needs explicit "reference prior assessments" instruction |
| Counter-trend trades worth investigating | 62.5% of safety rejections were profitable |
| H4 OB Retest re-elevated | Pressure test caught overlap metric bug, true overlap ~20% not 100% |
| Context Agent rejected | 2.4x cost, no new capability vs adding context lines |
| Partial close worth investigating | +0.153R per trade improvement on GBPUSD |
| M5 SL floor for GBPUSD not yet calibrated | ADR-scaled to 14.5 pips — needs empirical grid search like gold's $3-$15 sweep |

---

## KNOWN RISKS AND OPEN CONCERNS

1. **GBPUSD monthly concentration:** 48% of trades come from 2 months (Mar 2025 + Dec 2025). Without those months, combined p=0.270 (not significant). The edge is positive across 8/14 months but magnitude is concentrated.
2. **ALL 42 GBPUSD trades are LONG.** Zero directional diversity. SHORT capability is completely unvalidated. 8 SHORT candidates were proposed by AI but rejected by D1 safety filter.
3. **GBPUSD trade frequency is 4-5x higher than gold** (29% vs 6% of sessions produce trades). Unclear whether this is legitimate (GBPUSD has more structural breaks) or the AI being less selective with the "forex trader" prompt.
4. **Combined TP+M5 never tested together on fresh data.** Gold Phase 1 validated TP 1.5R. M5 validated separately. Combined +0.81R is an extrapolation.
5. **Extended KZ windows untested with AI.** Displacement data is positive but the AI might not find qualifying setups in extended hours. Batch test needed.
6. **M5 SL floor for GBPUSD** was ADR-scaled (14.5 pips), not empirically optimized. Gold's $10 floor was found via grid search across $3-$15. GBPUSD needs the same treatment.

---

## WHAT'S PENDING

### Awaiting Results (submitted to Claude Code):
1. **System improvements prompt** — prompt changes, partial close simulation, counter-trend analysis, volatility/cross-instrument context investigation
2. **System improvements pressure test** — verification of above

### Not Yet Started:
3. **Sync Mac code to Windows** — parameterization + extended KZ + ATR fix + prompt improvements
4. **Deploy GBPUSD to live demo** — after code sync + improvements
5. **Extended KZ batch tests** — test whether AI finds setups in extended hours
6. **Pre-screen loosening for GBPUSD** — 2-4h implementation, Cat1 dates show 53.4% cont
7. **H4 OB Retest batch test** — $15-25, exceptional edge quality (70-85% cont)
8. **NAS100/EURUSD batch tests** — $25-30 each, after GBPUSD proves multi-instrument works
9. **Economic calendar export** — Windows MT5, blocks AVOID mode
10. **Performance monitoring system** — rolling metrics, regime detection, weekly reports (future)

---

## KEY FILES CREATED/MODIFIED THIS SESSION

### Analysis Reports (knowledge_base_backtest/analysis/)
```
expansion_readiness_audit_20260403.md + .json
pre_batch_verification_20260403.md
atr_bug_fix_20260403.md
gbpusd_sample_prompt_corrected_20260403.txt
gbpusd_batch_deep_analysis_20260403.md + .json
gbpusd_pressure_test_20260403.md
frequency_multiplier_investigation_20260403.md + .json
frequency_multiplier_pressure_test_20260403.md
extended_kz_pressure_test_20260403.md
system_deep_dive_20260403.md + .json
system_deep_dive_pressure_test_20260403.md
granular_analysis_20260403.md + .json (CORRECTED — now uses 1.5R simulated values)
```

### Code Modified
```
config/agent_config.yaml                    — instrument overrides, KZ extensions, sl_absolute_min
src/utils/config.py                         — deep_merge, apply_instrument_overrides (fixed for base symbol)
src/prompts/primary_analyzer_prompt.py      — parameterized identity, thresholds, KZ display, price format
src/components/primary_analyzer.py          — uses build_system_prompt(config)
src/components/m5_refinement.py             — parameterized identity, buffer, price format
src/components/market_state.py              — removed round(atr, 2) (ATR bug fix)
src/components/permissions.py               — config-driven SL floor, .5f format for forex
src/components/orchestrator.py              — config-driven KZ times, extended NY support, _full_config injection
src/components/confidence_scorer.py         — parameterized regex and price range
src/prompts/bull_agent_prompt.py            — build_system_prompt_for_instrument()
src/prompts/bear_agent_prompt.py            — same
src/prompts/judge_prompt.py                 — same
src/prompts/postmortem_prompt.py            — removed "gold" reference
scripts/batch_backtest.py                   — --symbol flag, replay_kill_zone(), instrument-scoped paths, config-driven safety
scripts/backtest_runner.py                  — config-driven RR check, SL floor, symbol
scripts/historical_data_loader.py           — replay_kill_zone() generic function
tests/test_batch_backtest.py               — updated mocks for replay_kill_zone, new KZ tests
tests/test_prelaunch_audit.py              — updated for dynamic KZ display
```

### Batch Results (knowledge_base_backtest/batch_api/)
```
msgbatch_01NoUmtxUEP81v71PuNf7s7V_*  — GBPUSD discovery (Jan 2024 - Jun 2025)
msgbatch_01GFcnn3BoVnxZs3TseQt4hD_*  — GBPUSD validation (Jul 2025 - Apr 2026)
sessions/XAUUSD/                      — restored gold sessions (242 files)
sessions/GBPUSD/                      — separated GBPUSD sessions (149 files)
responses/XAUUSD/                     — restored gold responses
responses/GBPUSD/                     — separated GBPUSD responses
```

---

## CONFIDENCE LEVELS (Updated)

| What | Confidence | Evidence |
|------|-----------|----------|
| AI adds genuine value (gold) | 90% | Phase 0 (13x), Phase 1 (p=0.021), displacement scan, verification audit |
| AI transfers to GBPUSD | 80% | 42 trades, p=0.020 corrected, London outperforms NY as expected |
| 1.5R TP is optimal for full close | 85% | Phase 1 simulation, MFE cliff at 1.75R |
| Partial close improves on 1.5R | 65% | +0.153R on GBPUSD, needs gold r_path verification (pending) |
| M5 $10 floor works on gold | 75% | 526 mechanical + 14 AI trades, combined TP+M5 untested live |
| Extended KZs add trade frequency | 60% | Displacement data positive, AI performance in extended hours untested |
| Counter-trend trades have edge | 45% | 5/8 profitable but n=8 is too small for confidence |
| GBPUSD profitable over next 20 trades | 55% | Corrected +0.42R but all LONG, weak validation |
| Pre-screen loosening helps GBPUSD | 55% | Cat1 53.4% cont + 1.11 MFE/MAE, untested with AI |
| System profitable over next 50 trades (multi-instrument) | 60% | Combined evidence across gold + GBPUSD |

---

## STANDING RULES (NON-NEGOTIABLE)
1. Never re-run in-sample data to validate fixes — fresh data only
2. safe_place_order pattern is sacred — never retry without checking positions
3. Each improvement tested independently before stacking
4. Statistical significance (p < 0.05) required before risking real capital
5. File versioning on all outputs — never overwrite analysis files
6. One change at a time in production
7. Every spending decision justified by data
8. The AI's qualitative judgment is irreplaceable — don't try to replace it with rules
9. Gold calibration check before trusting new instrument scans
10. `--symbol` required for instrument-specific config (backward compatible)
11. Session files must be instrument-scoped (`sessions/{symbol}/`)
12. Batch scorer uses 50/50 partial close — corrected R-multiples needed for 100% TP1 comparison

---

## WHAT THE NEXT SESSION SHOULD DO

### If System Improvements Results Are Available:
1. Read this handoff FIRST
2. Read the system improvements output + pressure test output
3. Assess: did partial close add consistent value across gold AND GBPUSD?
4. Assess: how many counter-trend trades total across instruments? Is win rate significant?
5. Assess: did any volatility/cross-instrument metric predict outcomes?
6. Based on findings: prioritize what to implement next
7. If partial close validated: implement in live config
8. If counter-trend significant: design focused batch test
9. Plan code sync to Windows + GBPUSD demo deployment
10. Design extended KZ batch test (the implementation is done, needs batch validation)

### Priority Order for Builds:
1. **Implement validated improvements** from the improvements prompt
2. **Sync code to Windows** (parameterization + extended KZ + ATR fix + improvements)
3. **Deploy GBPUSD demo** alongside gold
4. **Run extended KZ batch** on GBPUSD (test if AI finds setups in 09:30-12:00)
5. **Run extended KZ batch** on gold (test if AI finds setups in 15:30-17:00)
6. **Pre-screen loosening** for GBPUSD (Lever 3, 2-4h implementation)
7. **H4 OB Retest batch** ($15-25, Tier 2 priority)
