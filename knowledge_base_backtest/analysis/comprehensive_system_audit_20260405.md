# Comprehensive System Audit
Date: 2026-04-05

## Summary
- **CRITICAL findings: 7**
- **HIGH findings: 13**
- **MEDIUM findings: 16**
- **LOW findings: 14**

**Root cause of most critical issues:** The system was built for single-instrument (XAUUSD) operation. Multi-instrument support exists in config but is never activated — instrument overrides are dead config, and core components (permissions, execution, data ingestion) have hardcoded XAUUSD references. The batch backtest pipeline has also diverged from the live pipeline, creating an optimism bias in backtest results.

---

## CRITICAL Findings (must fix before live trading)

### C1: Instrument overrides never applied — all per-instrument config is dead
- **Investigation:** 1 (Config)
- **File:** `src/components/orchestrator.py:945`
- **What:** `_load_config()` does `yaml.safe_load()` but never calls `apply_instrument_overrides()` from `src/utils/config.py`. `run_agent.py` has no `--symbol` argument.
- **Why it matters:** Gold NY KZ runs 13:00-15:30 instead of 13:00-17:00 (missing 1.5 hours). GBPUSD would use gold's $5 SL floor, 30-cent spread limit, and gold KZ times. Cross-instrument context for GBPUSD never activates. FX price formatting uses .2f instead of .5f.
- **Fix:** Wire `apply_instrument_overrides(config, symbol)` into orchestrator startup. Add `--symbol` to `run_agent.py`.

### C2: SL absolute minimum hardcoded to $5.00 — blocks all FX trades
- **Investigation:** 1, 3 (Config, Safety)
- **File:** `src/components/permissions.py:131`
- **What:** `if sl_distance < 5.0` is hardcoded. Config has per-instrument overrides (GBPUSD: 0.0003) but they're never read.
- **Why it matters:** FX SL distances are 0.0010-0.0050. Every FX trade would pass this check trivially (wrong direction — $5 floor vs 0.001 SL). For NAS100 the config says 30.0 but code enforces 5.0.
- **Fix:** Read `config["risk"]["sl_absolute_min"]` with instrument override.

### C3: Spread check hardcoded to XAUUSD symbol
- **Investigation:** 1, 3 (Config, Safety)
- **File:** `src/components/permissions.py:63`
- **What:** `mt5.get_tick("XAUUSD")` always queries gold spread. Threshold `30` (cents) is hardcoded.
- **Why it matters:** When trading GBPUSD, the system checks gold's spread instead. GBPUSD spread of 0.02 (2 pips) always passes `> 30` — spread protection completely disabled for FX.
- **Fix:** Pass symbol to Gate 3. Read `max_spread_cents` from config with instrument override.

### C4: XAUUSD hardcoded throughout execution.py — blocks multi-instrument
- **Investigation:** 4 (Dead Code)
- **File:** `src/components/execution.py` — 16+ occurrences (lines 70, 89, 154, 193, 208, 245, 274, 285, 326, 337, 378, 414, 422, 433, 441, 477)
- **What:** Every MT5 call uses hardcoded `"XAUUSD"` instead of reading from config.
- **Why it matters:** Multi-instrument execution impossible. All orders placed on XAUUSD regardless of what the AI analyzed.
- **Fix:** Parameterize symbol from config.

### C5: XAUUSD hardcoded throughout data_ingestion.py
- **Investigation:** 4 (Dead Code)
- **File:** `src/components/data_ingestion.py` — lines 64, 81, 254
- **What:** Data ingestion always pulls XAUUSD candles from MT5.
- **Why it matters:** Even if everything else were fixed, the system would analyze gold candles while thinking it's trading GBPUSD.
- **Fix:** Parameterize symbol from config.

### C6: Trade monitoring dead zone between NY end and NY end + 2 hours
- **Investigation:** 2 (Pipeline)
- **File:** `src/components/orchestrator.py:225-241, 793-796`
- **What:** After NY KZ ends (15:30 UTC), the main loop falls through to the "before London" else branch. `_is_after_all_kz()` returns False until `ny_end + 120 minutes`. During this gap, no trade monitoring occurs — no MFE/MAE tracking, no TP hit detection, no broker close detection.
- **Why it matters:** A trade open at NY close is completely unmonitored for up to 2 hours. Price could hit TP or SL with no system response.
- **Fix:** The else branch should check for active trades and call `_check_trade_and_capture()`, or `_is_after_all_kz` should not add the 120-minute delay.

### C7: INDEX.md is 126 files behind — 80% of analysis work unindexed
- **Investigation:** 5 (File Integrity)
- **File:** `knowledge_base_backtest/analysis/INDEX.md`
- **What:** Lists only 33 entries (March 31 - April 2). 126 files from April 3-4 are not indexed.
- **Why it matters:** The KB retrieval system uses INDEX.md to find relevant analysis. All displacement databases, pressure tests, phase 1 replays, multi-instrument validation, GBPUSD batch analysis, L2 verification work, and regression testing are invisible to the retrieval system.
- **Fix:** Rebuild INDEX.md with all 159 files.

---

## HIGH Findings (should fix before live trading)

### H1: enabled_frameworks config ignored — breaker_retest trades can pass
- **Investigation:** 1 (Config)
- **File:** `src/prompts/primary_analyzer_prompt.py:139-141`
- **What:** Config says `enabled_frameworks: ["ob_retest"]` but the prompt always instructs the AI to evaluate BOTH ob_retest and breaker_retest. Verification.py also processes breaker_retest candidates.
- **Fix:** Filter prompt sections by enabled_frameworks config.

### H2: R:R floor (1.3) hardcoded, disconnected from config min_rr (1.5)
- **Investigation:** 1 (Config)
- **File:** `src/components/permissions.py:101, 121`
- **What:** Gate 1 rejects trades below 1.3 R:R. Config says `min_rr: 1.5`. These are different values with different purposes (floor vs target) but the naming creates confusion.
- **Fix:** Add explicit `min_rr_floor` config key, or document the distinction.

### H3: Cross-instrument context for GBPUSD never activates
- **Investigation:** 1 (Config)
- **File:** `src/components/orchestrator.py:523`
- **What:** Reads `self.config.get("cross_instrument_context", {}).get("enabled")` but the setting only exists in the GBPUSD instrument override section, which is never applied (see C1).
- **Fix:** Depends on C1 fix.

### H4: Spread threshold hardcoded to 30 (gold cents), wrong for FX
- **Investigation:** 1, 3 (Config, Safety)
- **File:** `src/components/permissions.py:64`
- **What:** Even if symbol were fixed (C3), the threshold `30` is hardcoded. GBPUSD needs `0.03`, EURUSD needs `0.02`.
- **Fix:** Read from config with instrument override.

### H5: Daily loss limit hardcoded to -2.0%, not from config
- **Investigation:** 1, 3 (Config, Safety)
- **File:** `src/components/permissions.py:40`
- **What:** Config has `max_daily_loss_pct: 2.0` but permissions.py hardcodes `-2.0`.
- **Fix:** Read from config.

### H6: Gate 1 entirely non-instrument-aware
- **Investigation:** 3 (Safety)
- **File:** `src/components/permissions.py:72-152`
- **What:** Gate 1 receives no config and no symbol. All thresholds (SL floor $5, SL-vs-ATR 1.5x, max SL 2.5% of price) are calibrated for gold only. For forex, the 2.5% max SL check triggers at ~310 pips — no real protection.
- **Fix:** Pass config to Gate 1. Apply per-instrument thresholds.

### H7: Entire debate subsystem is dead code in live pipeline
- **Investigation:** 4 (Dead Code)
- **Files:** `src/components/debate.py`, `src/prompts/bull_agent_prompt.py`, `src/prompts/bear_agent_prompt.py`, `src/prompts/judge_prompt.py`, `src/models/debate_models.py`
- **What:** 5 modules, never imported by orchestrator. Config keys `debate_model`, `debate_round2_enabled` are dead.
- **Fix:** Remove or explicitly mark as backtest-only.

### H8: adaptive_review.py not wired into live pipeline
- **Investigation:** 4 (Dead Code)
- **File:** `src/components/adaptive_review.py`
- **What:** The Tier 2/3/4 parameter adaptation system is not imported by orchestrator. Config section `adaptation:` is dead.
- **Fix:** Wire in or remove.

### H9: _modify_tp and _modify_sl bypass safe_place_order pattern
- **Investigation:** 7 (Error Handling)
- **File:** `src/components/execution.py:413-445`
- **What:** These methods call `mt5.order_send()` directly, bypassing the checkpoint/timeout safety pattern. `_modify_tp` has NO retry. Return value of `_modify_tp` is silently ignored at lines 299, 349.
- **Why it matters:** Per the module's own rule: "After every SL/TP modification failure, close the position immediately." Failed TP modification means trade stays open with wrong TP.
- **Fix:** Check `_modify_tp` return value. On failure, close position per the module's documented rule.

### H10: max_daily_trades set but never enforced
- **Investigation:** 7 (Error Handling)
- **File:** `src/components/orchestrator.py:91`
- **What:** `session_state["max_daily_trades"] = 2` is set but no code checks `trades_today >= max_daily_trades`. Enforcement is only implicit via per-KZ limit of 1 (London + NY = 2 max).
- **Fix:** Add explicit daily trade limit check.

### H11: Batch mode skips Level 2 verification entirely
- **Investigation:** 8 (Interfaces)
- **File:** `scripts/batch_backtest.py:637-638`
- **What:** Batch never calls `verify_candidate()`. Trades that would fail L2 (hallucinated OBs, wrong zones, entries outside OB) pass in batch but would fail in live.
- **Why it matters:** Creates systematic optimism bias in backtest results.
- **Fix:** Add L2 verification to batch pipeline.

### H12: Batch safety_check() missing 3 checks from live Gate 1
- **Investigation:** 8 (Interfaces)
- **File:** `scripts/batch_backtest.py:760-796` vs `src/components/permissions.py:72-152`
- **What:** Batch is missing: (1) TP1 side check, (2) TP1 range 1.3-2.0R check, (3) max SL 2.5% check.
- **Fix:** Import and use the same `_gate1_safety_checks` function, or sync the checks.

### H13: Gold Phase 1 headline numbers are simulated, not actual
- **Investigation:** 6 (Data)
- **File:** `knowledge_base_backtest/analysis/system_improvements_20260403.md`
- **What:** Reports 61.1% WR, +0.503R avg for Gold Phase 1. Actual backtest: 50.0% WR (9W/9L), +0.403R avg. The 61.1% is from "Strategy A: 100% at TP1" simulation that flips 2 losses to wins.
- **Why it matters:** Decision-making based on inflated numbers.
- **Fix:** Clearly label simulated vs actual results in all reports.

---

## MEDIUM Findings (fix when convenient)

### M1: GBPUSD sl_absolute_min config value is 0.0003 (3 pips), not 0.00145 (14.5 pips) as expected
- **Investigation:** 1 (Config)
- **File:** `config/agent_config.yaml:171`
- **What:** 14.5 pip value is in `m5_refinement.sl_floor`, not `sl_absolute_min`.

### M2: max_daily_trades hardcoded in session_state, never reads from config
- **Investigation:** 1 (Config)
- **File:** `src/components/orchestrator.py:90, 835`

### M3: Config min_rr naming confusion (1.5 target vs 1.3 floor)
- **Investigation:** 1 (Config)
- **File:** `config/agent_config.yaml:24`

### M4: Stale module-level KZ defaults contradict config
- **Investigation:** 1 (Config)
- **File:** `src/components/orchestrator.py:48-52, 75`
- **What:** `LONDON_END = (10, 30)` is dead code; `.get()` fallback "10:30" contradicts config "09:30".

### M5: No trade monitoring during 15-minute inter-candle sleep within KZ
- **Investigation:** 2 (Pipeline)
- **File:** `src/components/orchestrator.py:200-212`
- **What:** During the sleep waiting for next M15 close, active trades are not monitored.

### M6: Gate 1 falsely recorded as "passed" when Gate 3 fails
- **Investigation:** 2 (Pipeline)
- **File:** `src/components/orchestrator.py:383-389`
- **What:** When Gate 3 denies, Gate 1 was never run but trade record shows it as "passed".

### M7: Confidence scoring is shadow-only by default — no blocking effect
- **Investigation:** 2 (Pipeline)
- **File:** `src/components/orchestrator.py:332-349`

### M8: L2 verification runs on pre-M5-refinement parameters
- **Investigation:** 2 (Pipeline)
- **File:** `src/components/orchestrator.py:311 vs 351-380`
- **What:** M5 refinement can change entry price after L2 verified it. Modified entry not re-verified against OB zone.

### M9: session_sweep/equal_sweep/fvg_fill in Literal type and validation
- **Investigation:** 4 (Dead Code)
- **File:** `src/models/analysis_models.py:100`, `src/components/primary_analyzer.py:433-444`
- **What:** AI can output these disabled frameworks and they'll be accepted.

### M10: postmortem_prompt.py never imported from src/
- **Investigation:** 4 (Dead Code)

### M11: chart_renderer.py never imported from live pipeline
- **Investigation:** 4 (Dead Code)

### M12: 10 dead config keys never read by any src/ code
- **Investigation:** 4 (Dead Code)
- **What:** monitoring.*, budget.*, postmortem_model, retrieval.embedding_model, retrieval.lancedb_path

### M13: trade_records/ directory does not exist
- **Investigation:** 5 (File Integrity)
- **File:** `knowledge_base/trade_records/` — missing
- **What:** trade_capture.py tries to save here but the directory was never created.

### M14: Regression report claims 22W/17L but data shows 23W/16L
- **Investigation:** 6 (Data)
- **File:** `knowledge_base_backtest/analysis/regression_batch_test_20260404.md`

### M15: Batch mode does not pass session_memory to prompt builder
- **Investigation:** 8 (Interfaces)
- **File:** `scripts/batch_backtest.py:248-252`

### M16: Batch mode RR threshold differs from live mode (1.4 vs 1.3)
- **Investigation:** 8 (Interfaces)
- **File:** `scripts/batch_backtest.py:781` vs `src/components/permissions.py:101`

---

## LOW Findings (code quality)

### L1: Grade filter hardcoded to ("A+", "A") — not config-driven
- **Investigation:** 1 — `permissions.py:84`

### L2: "20-period average" window hardcoded in prompt text
- **Investigation:** 1 — `primary_analyzer_prompt.py:128`

### L3: "1:1.5" R:R requirement hardcoded in prompt text
- **Investigation:** 1 — `primary_analyzer_prompt.py:130`

### L4: score_confidence called without config parameter
- **Investigation:** 2 — `orchestrator.py:331`

### L5: Gate order documented correctly (Gate 3 before Gate 1)
- **Investigation:** 2 — confirmed correct

### L6: monitoring.py never imported from live pipeline
- **Investigation:** 4 — standalone module

### L7: dashboard.py never imported from live pipeline
- **Investigation:** 4 — standalone via uvicorn

### L8: Session files lack instrument identifiers — directory-only scoping
- **Investigation:** 5

### L9: 22 undated files in analysis directory
- **Investigation:** 5

### L10: No config backup file (git-only backup)
- **Investigation:** 5

### L11: Cross-instrument trade_details array truncated (10 of 42 entries)
- **Investigation:** 6

### L12: GBPUSD sessions have 20 trades, not 42 — incomplete session pipeline
- **Investigation:** 6

### L13: Crash recovery adopts only last orphan position
- **Investigation:** 7 — `execution.py:478-498`

### L14: Exception between trade execution and state update could allow duplicate KZ trade
- **Investigation:** 7 — `orchestrator.py:401-416`

---

## Per-Investigation Details

### Investigation 1: Configuration Consistency
**Root cause:** Orchestrator loads raw YAML without applying instrument overrides. Permissions.py was written for gold-only with hardcoded values.
- 4 CRITICAL, 4 HIGH, 4 MEDIUM, 3 LOW findings
- Most impactful: C1 (overrides never applied) cascades to C2, C3, H3, H4, H6

### Investigation 2: Pipeline Flow
**Root cause:** Trade monitoring has a gap in the main loop state machine between NY end and the timeout zone.
- 1 CRITICAL, 0 HIGH, 4 MEDIUM, 2 LOW findings
- Most impactful: C6 (monitoring dead zone) — active trade unmonitored for up to 2 hours

### Investigation 3: Safety Gate Integrity
**Root cause:** Gates are gold-centric with no config parameterization.
- 2 CRITICAL (overlap with Inv 1), 3 HIGH (overlap with Inv 1), 1 MEDIUM, 1 LOW findings
- Positive: Pre-screen is solid, L2 handles edge cases correctly, no bypass paths found

### Investigation 4: Dead Code & Stale References
**Root cause:** Rapid feature addition without cleanup. Multiple subsystems (debate, adaptive review, vision) were built but never wired into the live pipeline.
- 2 CRITICAL, 3 HIGH, 4 MEDIUM, 2 LOW findings
- XAUUSD hardcoding in execution.py and data_ingestion.py is the most urgent

### Investigation 5: File Integrity & Paths
**Root cause:** INDEX.md maintenance was not automated or enforced.
- 1 CRITICAL, 1 HIGH, 2 MEDIUM, 3 LOW findings
- April 3 overwrite recovery verified clean. Git state is clean. All data CSVs present.

### Investigation 6: Data Consistency
**Root cause:** Simulated results presented as headline figures without qualification.
- 0 CRITICAL, 1 HIGH, 3 MEDIUM, 2 LOW findings
- Gold actual WR is 50%, not 61.1%. GBPUSD numbers are consistent across files.

### Investigation 7: Error Handling & Edge Cases
**Root cause:** TP modification path doesn't follow the module's own safety rules.
- 0 CRITICAL, 3 HIGH, 3 MEDIUM, 0 LOW findings (plus 20 confirmed-correct checks)
- Primary analyzer error handling is excellent. Trade capture is non-blocking by design.

### Investigation 8: Cross-Component Interfaces
**Root cause:** Batch pipeline diverged from live pipeline over multiple modification sessions.
- 0 CRITICAL, 2 HIGH, 3 MEDIUM, 4 LOW findings
- Batch skips L2 verification and 3 Gate 1 checks, creating optimism bias in results.
- Model config is consistent. Prompt caching is instrument-safe. No cache poisoning risk.

---

## Confirmed Working Correctly
- Pre-screen logic (solid, no bypass)
- L2 verification (correct for LONG/SHORT, both frameworks, handles missing data)
- Cross-instrument context (correctly soft, not a hard gate)
- D1 direction (close-over-close as designed)
- Primary analyzer error handling (timeout, 500, rate limit, malformed JSON — all handled)
- Trade capture (non-blocking, defensive serialization)
- Crash recovery (checkpoint files, position reconciliation, trade record reconnection)
- Prompt caching (content-hash based, instrument-safe)
- Model configuration (consistent between config, live, and batch)
- Git state (clean, all changes committed)
- Session file integrity (242 XAUUSD, 149 GBPUSD, no contamination)
- Data file completeness (all 25 instrument/timeframe CSVs present, non-empty)
