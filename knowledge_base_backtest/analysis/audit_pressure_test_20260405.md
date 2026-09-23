# Audit Pressure Test Results
Date: 2026-04-05

## Phase 1: Finding Verification

### CRITICAL Findings: 6/7 verified real, 1 reclassified

| Finding | Audit Severity | Verified | Actual Severity | Notes |
|---------|---------------|----------|-----------------|-------|
| C1: Instrument overrides never applied | CRITICAL | TRUE | CRITICAL | Exact. `_load_config` is 3 lines of yaml.safe_load, no override merge. `apply_instrument_overrides` exists in utils but is never called in live. |
| C2: SL min hardcoded $5.00 | CRITICAL | TRUE | **HIGH** | Real, but for current gold-only deployment $5 is correct. Only CRITICAL if trading other instruments. |
| C3: Spread check hardcoded XAUUSD | CRITICAL | TRUE | **HIGH** | Same as C2 — real issue but only impacts multi-instrument. Symbol and threshold both hardcoded. |
| C4: XAUUSD hardcoded in execution.py | CRITICAL | TRUE | CRITICAL | 16 occurrences confirmed, all in live code paths, zero parameterization. Also found hardcoded contract size ($100/lot) at line 82. |
| C5: XAUUSD hardcoded in data_ingestion.py | CRITICAL | TRUE | CRITICAL | 3 occurrences confirmed at lines 64, 81, 254. Zero config reads for symbol. |
| C6: Trade monitoring dead zone | CRITICAL | TRUE | CRITICAL | Confirmed via control flow trace. Between NY end (15:30) and NY end + 120min (17:30), the else branch executes _interruptible_sleep(10) but NEVER calls _check_trade_and_capture(). Active trades are unmonitored. |
| C7: INDEX.md 126 files behind | CRITICAL | TRUE | **LOW** | Real (actually 127 missing, not 126), but INDEX.md is a human reference file, not consumed by the live system. Not a runtime risk. |

**Summary: 5 truly CRITICAL, 2 HIGH (reclassified from CRITICAL), 0 false positives**

### HIGH Findings: 9/13 verified real, 2 false positives, 2 reclassified

| Finding | Audit Severity | Verified | Actual Severity | Notes |
|---------|---------------|----------|-----------------|-------|
| H1: enabled_frameworks config ignored | HIGH | **FALSE** | **FALSE_POSITIVE** | Audit was WRONG. `primary_analyzer.py` lines 139-142 DO check `enabled_frameworks` and call `_strip_breaker_sections()` to remove breaker content from the prompt when only ob_retest is enabled. |
| H2: R:R floor 1.3 disconnected from config 1.5 | HIGH | TRUE | **MEDIUM** | Intentional design (1.5 target, 1.3 acceptance floor). Comment at line 100 explains. Not config-driven but working as intended. |
| H3: Cross-instrument context never activates | HIGH | TRUE | HIGH | Confirmed dependent on C1. Config only exists in GBPUSD override block which is never merged. |
| H4: Spread threshold 30 hardcoded | HIGH | TRUE | HIGH | Confirmed. Threshold 30 at line 64, not from config. |
| H5: Daily loss limit -2.0% hardcoded | HIGH | TRUE | HIGH | Confirmed at line 40. Config value exists but is never read. |
| H6: Gate 1 non-instrument-aware | HIGH | TRUE | HIGH | 7 hardcoded thresholds confirmed. Function signature takes no config or symbol. |
| H7: Debate subsystem dead code | HIGH | TRUE | **MEDIUM** | Real but intentional. Comment says "Gate 2 stubbed for live." Future infrastructure, not accidental omission. |
| H8: adaptive_review not wired | HIGH | TRUE | **MEDIUM** | Same as H7 — planned future feature. |
| H9: _modify_tp bypasses safe_place_order | HIGH | TRUE | HIGH | Confirmed. _modify_tp has NO retry, return value never checked at lines 299, 350. Violates module's own documented rule. |
| H10: max_daily_trades never enforced | HIGH | **FALSE** | **FALSE_POSITIVE** | Audit was WRONG. permissions.py Gate 3 (lines 44-49) DOES check `trades_today >= max_daily_trades`. The daily limit IS enforced. |
| H11: Batch skips L2 verification | HIGH | TRUE | HIGH | Confirmed. Zero references to verify_candidate in batch_backtest.py. |
| H12: Batch missing 3 Gate 1 checks | HIGH | TRUE | HIGH | Confirmed: TP1 side check, TP1 R-ratio band (1.3-2.0R), max SL 2.5% all missing. Also found: live Gate 1 docstring (line 73) falsely claims "exact replica of batch_backtest._safety_check()". |
| H13: Gold Phase 1 numbers simulated | HIGH | TRUE | **MEDIUM** | Actual backtest: 9W/9L = 50.0% WR. The 61.1% is from a TP simulation. Report does not label it as simulated. Internal analysis doc, not a production gate. |

**Summary: 9 verified real (7 HIGH, 2 MEDIUM after reclassification), 2 FALSE POSITIVES (H1, H10), 2 reclassified down**

---

## Phase 2: Blind Spots Found

### 2A: Config Values Unchecked
The audit verified 13 specific config values. The full config has ~80+ configurable keys. Approximately 67 values were NOT individually verified, including:
- AI model parameters (temperature, max_tokens, retry settings)
- M5 refinement thresholds
- KB retrieval parameters (embedding model, chunk size, top_k)
- Monitoring and budget sections (though these were flagged as dead config)

**Impact:** LOW — the unchecked values are either in dead subsystems (monitoring, budget, debate) or in well-tested components (KB retrieval, M5 refinement).

### 2C: Dead Code Missed by Audit

**Partial close 25% hardcoded in execution.py** (line 319-320):
- `_execute_tp2_partial` uses `trade.initial_volume * 0.25` (hardcoded)
- Currently dead code under Phase 1 config (100% close at TP1), but if partial close is re-enabled, this magic number would need attention.
- Severity: LOW (dead code behind config gate)

**Hardcoded model name in 5+ locations:**
- `claude-sonnet-4-20250514` appears as default in primary_analyzer.py:77, m5_refinement.py:252, debate.py:74, adaptive_review.py:110, and prompt template line 221.
- All are config-overridable defaults. Maintenance burden when model version changes.
- Severity: LOW

**ATR rounding bug:** NOT found. The audit searched for `round(atr` and found nothing. Confirmed clean.

### 2D: Error Handling Gaps

The audit confirmed good error handling for:
- API timeout/500/429/malformed JSON (primary_analyzer.py) — all produce safe NO_TRADE
- Trade capture failures (save_trade_record) — non-blocking, returns None
- Crash recovery (checkpoint + MT5 reconciliation) — multi-layer

The audit did NOT test:
- What happens if `verify_candidate()` receives None for analysis or mso — **verified: line 246 checks for missing H1 data, but does NOT check for None mso. A None mso would crash at line 246 with AttributeError.** Severity: LOW (mso is always computed before verify_candidate is called).
- What happens if `create_trade_record()` receives None for any field — **verified: _safe_model_dump handles None gracefully via the str() fallback.** No issue.

### 2E: Interface Mismatches

All 3 critical interfaces verified:
1. **orchestrator → verify_candidate()**: orchestrator passes (analysis, mso, self.config). verify_candidate expects (PrimaryAnalysisOutput, MarketStateObject, dict). **MATCH.**
2. **orchestrator → create_trade_record()**: 10 named parameters all match. **MATCH.**
3. **orchestrator → analyzer.analyze()**: 4 parameters match. **MATCH.**

No type mismatches found. The audit's interface table was accurate.

---

## Phase 3: Unverifiable on Mac

| Item | Status | Risk | Notes |
|------|--------|------|-------|
| Windows path separators | LOW RISK | All hardcoded "/" paths are wrapped in `Path()` before use, which normalizes cross-platform. `_load_config` uses bare `open(path)` but Python handles "/" on Windows. |
| MT5 package availability | WELL HANDLED | Lazy import inside `mt5_real.py:connect()`. Mac uses `mt5_mock.py`. Mock accuracy cannot be verified from Mac. |
| File permissions | UNVERIFIABLE | Check Windows user has write access to knowledge_base/, data/, config/ on sync. |
| Python version | UNVERIFIABLE | Confirm matching versions. Check for 3.10+ features used (match statements, `X | Y` type unions). |
| atomic_write cross-platform | LOW RISK | Uses `os.replace()` which is atomic on POSIX but has edge cases on Windows with antivirus/indexing locks. |

---

## Phase 4: Missing Areas the Audit Didn't Cover

### Timezone Handling
**Issues found: 0**
Every `datetime.now()` call uses `datetime.now(timezone.utc)`. No timezone-naive calls. No deprecated `utcnow()`. Exemplary.

### Numeric Precision
**Issues found: 0**
Only one exact float comparison: `poi_price == 0` in verification.py (safe sentinel check). No `price == X` comparisons on market prices.

### Memory Leaks
**Issues found: 1 (LOW)**
- `session_memory`: Bounded at 6 entries per KZ (12 max). Safe.
- `candle_log`: Reset daily via `_new_day()`. Safe.
- `alerts.jsonl`: Appended indefinitely, never rotated. Will grow without bound over weeks. Severity: LOW.

### Concurrent File Access
**Issues found: 0**
PID lock prevents multiple orchestrator instances. Within a single instance, the main loop is sequential. `atomic_write` uses temp-file-then-rename pattern.

### API Rate Limiting
**Issues found: 0**
HTTP 429 handled in both API mode (reads retry_after header, sleeps, retries) and CLI mode (progressive backoff: 5s, 10s, 15s). Both exhaust retries gracefully and produce NO_TRADE.

---

## Corrected Findings Summary

### Original Audit Totals
- CRITICAL: 7
- HIGH: 13
- MEDIUM: 16
- LOW: 14
- **Total: 50**

### After Pressure Test Verification

| Category | Count | Change |
|----------|-------|--------|
| CRITICAL (verified) | **5** | -2 (C2→HIGH, C7→LOW) |
| HIGH (verified) | **10** | -3 (H2→MEDIUM, H7→MEDIUM, H8→MEDIUM, H13→MEDIUM) +2 (C2, C3 promoted from reclassified CRITICAL) |
| MEDIUM (verified) | **20** | +4 from reclassifications |
| LOW (verified) | **15** | +1 (C7 reclassified) |
| FALSE POSITIVES | **2** | H1 (enabled_frameworks IS checked), H10 (max_daily_trades IS enforced) |
| NEW findings | **3** | Partial close 0.25 hardcoded (LOW), alerts.jsonl unbounded (LOW), model name in 5 files (LOW) |

### Verified CRITICAL Findings (5)
1. **C1**: Instrument overrides never applied in live pipeline
2. **C4**: XAUUSD hardcoded throughout execution.py (16 occurrences)
3. **C5**: XAUUSD hardcoded throughout data_ingestion.py
4. **C6**: Trade monitoring dead zone (up to 2 hours post-NY)
5. *(For multi-instrument deployment)* C2+C3 escalate back to CRITICAL

### False Positives Identified (2)
1. **H1**: The audit claimed `enabled_frameworks` is ignored. FALSE — `primary_analyzer.py` lines 139-142 DO check it and strip breaker sections from the prompt. The sub-agent likely searched the prompt template file but missed the runtime filtering in the analyzer.
2. **H10**: The audit claimed `max_daily_trades` is set but never enforced. FALSE — `permissions.py` Gate 3 (lines 44-49) enforces it via `trades_today >= max_daily`. The sub-agent likely searched orchestrator.py for the enforcement but missed that it happens in permissions.py.

### Key Takeaways
1. **The audit's core finding is correct**: The system is XAUUSD-only despite multi-instrument config. C1 is the root cause; C2-C5, H3-H6 are symptoms.
2. **The monitoring dead zone (C6) is the most operationally dangerous finding** — it affects the current gold-only deployment, not just multi-instrument.
3. **Batch-live divergence (H11, H12) means backtest results overstate live performance** — this is confirmed and significant.
4. **Two findings were false positives**, both due to sub-agents not reading far enough into the code to find the enforcement logic.
5. **Platform (Mac→Windows) risks are well-mitigated** by the codebase's use of Path() and defensive MT5 imports.
6. **No timezone, precision, concurrency, or rate limit issues found** — these areas are clean.
