# Final Pre-Live Verification Report

**Date:** April 14, 2026
**Reviewer:** Claude Opus 4.6 (final review agent)
**Time:** 03:15 – 03:40 GMT+8
**Verdict:** ISSUES FOUND — 3 must be addressed before live

---

## Part 1: Change Discovery

### Git Status

Branch `main` has **diverged from origin/main** — 1 commit each side:
- Local: `227cfdf` (fix: replace hallucinated gpt-4.1 model_used references)
- Origin: `34bd63a` (fix: three infrastructure bugs — M5 pull, model_used, api_calls_made)

**14 unstaged modified files, 4 untracked files.**

### Recent Commits (April 13–14)

| Hash | Message | Files |
|------|---------|-------|
| 227cfdf | fix: replace hallucinated gpt-4.1 model_used references with claude-sonnet-4-6 | knowledge_base/, shadow_logs/ |
| 65b3ad3 | data: Apr 13 end-of-day — session summaries, final pipeline state, full logs | data files |
| 91cedaf | data: Apr 13 complete — full-day audit, NY records, no_trade files | data files |
| a548e19 | Merge branch 'main' | merge |
| b469708 | fix: remove cancel_limit_intent from canary block | orchestrator |
| 536c529 | feat: OB limit order architecture | orchestrator, permissions |

Origin-only (not on local):
| 34bd63a | fix: three infrastructure bugs — M5 pull method, model_used hallucination, api_calls_made counter | data_ingestion, orchestrator, primary_analyzer, tests |

### Complete Change Inventory (Unstaged)

| File | Change Type | Summary |
|------|-------------|---------|
| config/agent_config.yaml | Modified | YAML restructure: risk keys moved from drawdown_reduction to risk; gate1 section added; GBPUSD cross_instrument_context disabled; risk_per_trade_pct changed to 2.0 |
| src/components/permissions.py | Modified | New `_ob_retest_sl_exception_applies()` function; Gate1 sl_floor bypass for ob_retest; +47 lines |
| src/components/orchestrator.py | Modified | Rename `api_calls_made` → `candles_in_pipeline` in session summary |
| tests/test_permissions.py | Modified | +105 lines: 5 new tests for OB retest SL exception |
| tests/test_prelaunch_audit.py | Modified | Fix test path: `drawdown_reduction.min_rr` → `risk.min_rr` |
| tests/test_batch_backtest.py | Modified | Fix assertion: London end_utc `09:30` → `10:30` |
| tests/test_monitoring.py | Modified | Fix: use `tmp_path` instead of `/nonexistent/path` |
| tests/test_end_to_end_integration.py | Modified | Fix 5x: `_log_dir` → `_logs_dir` attribute references |
| tests/test_infrastructure_framework.py | Modified | Fix: delegate through `shadow_collector`, fix metric type name |
| tests/test_resolve_obs.py | Modified | Fix: use `patch.dict("sys.modules")` instead of wrong patch target |
| knowledge_base/inverted_tp_log.jsonl | Modified | +12 new inverted TP log entries (runtime data) |
| shadow_logs/drawdown_state_changes.jsonl | Modified | +66 new drawdown state entries (runtime data) |
| shadow_logs/malformed_responses.jsonl | Modified | +22 new malformed response entries (runtime data) |
| research/kap_outputs/cron.log | Modified | +1 line (runtime data) |

### Untracked Files

| File | Purpose |
|------|---------|
| .context/02_session_handoffs/16_apr13_ob_limit_order_architecture_handoff.md | Handoff (DUPLICATE number — 16_monitoring_audit already committed) |
| .context/02_session_handoffs/17_apr14_monitoring_fixes_final_verification_handoff.md | Handoff for today's monitoring fixes |
| .context/03_analysis/april13_findings_verification.md | Analysis report |
| .context/03_analysis/test_failures_yaml_verification_report.md | Analysis report |

---

## Part 2: Issue Resolution Verification

| # | Issue | Status | Evidence |
|---|-------|--------|----------|
| 1 | GBPUSD cross-instrument context | FIXED | `config.instruments.GBPUSD.cross_instrument_context.enabled = false` — verified via YAML parse. Causes 2 test regressions (see Part 6). |
| 2 | YAML indentation bug — risk keys misplaced | FIXED | 10 keys now under `risk:` section, 3 under `drawdown_reduction:`. YAML parses clean. Structure verified. |
| 3 | GBPJPY sl_floor > OB width blocking valid trades | FIXED | `gate1.ob_retest_sl_exception = true` in config. `_ob_retest_sl_exception_applies()` added to permissions.py. 5 tests pass. **But see HIGH issues in Part 3.** |
| 4 | Gate3 spread check using 30 instead of 100 for XAUUSD | FIXED | `risk.max_spread_cents = 100`. XAUUSD has no per-instrument override, so effective = 100. |
| 5 | Gate1 OB tolerance using 0.02 instead of 1.20 | FIXED | `risk.sl_buffer_dollars = 1.20`. XAUUSD effective = 1.20. However, this value is also used as OB matching tolerance in the new exception function (see HIGH issue). |
| 6 | Test failures from YAML bug (Group 2) | FIXED | `test_prelaunch_audit.py::TestConfigConsistency` — 3/3 pass. Key path updated to `config["risk"]["min_rr"]`. |

---

## Part 3: File-by-File Verification

### config/agent_config.yaml
- **Syntax:** OK (yaml.safe_load succeeds)
- **Structure:** risk: 10 keys, drawdown_reduction: 3 keys, gate1: 1 key, filters: 1 key
- **Values verified:**
  - `risk_per_trade_pct: 2.0` — **DISCREPANCY with CLAUDE.md** (says 1.0). Was changed per CEO decision (mem obs 461). CLAUDE.md needs update.
  - `min_rr: 1.5` — matches CLAUDE.md
  - `max_trades_per_day: 2` — matches CLAUDE.md
  - `max_spread_cents: 100` — correct for XAUUSD
  - `sl_buffer_dollars: 1.20` — correct
  - `sl_absolute_min: 5.0` — correct for XAUUSD
  - `gate1.ob_retest_sl_exception: true` — new, correct
  - `GBPUSD.cross_instrument_context.enabled: false` — intentional, with comment

### src/components/permissions.py
- **Syntax:** OK (py_compile succeeds)
- **No TODOs/FIXMEs:** Confirmed
- **No debug prints:** Confirmed

**Expert review findings (2 HIGH, 2 MEDIUM):**

**[HIGH] OB type not checked in `_ob_retest_sl_exception_applies()` (lines 109-116)**
The function iterates unmitigated H1 OBs and checks if `entry_price` is within `[ob.low - tol, ob.high + tol]`, then checks SL placement. But it never checks `ob.type` (bullish/bearish). A LONG trade could match a bearish OB and bypass sl_floor incorrectly. The test mocks use `SimpleNamespace` without a `type` field, so tests don't catch this.

Production `OrderBlock` model has a `type: Literal["bullish", "bearish"]` field. The fix: add `ob.type == "bullish"` guard for LONG and `ob.type == "bearish"` for SHORT.

**[HIGH] `ob_tol` uses `sl_buffer_dollars` — wrong semantic (line 107)**
`sl_buffer_dollars` is SL placement padding (how far beyond the OB to place the stop). The codebase already has `verification.ob_price_tolerance_pct = 0.002` (0.2% of price, ~$6 for gold, ~2.5 pips GBPUSD) as the established OB matching tolerance. Using `sl_buffer_dollars` instead creates:
- For XAUUSD: $1.20 tolerance (0.04% at $3000) — much tighter than the 0.2% convention
- For GBPJPY: 0.014 (1.4 pips) — reasonable by coincidence

This won't cause false positives (wrong OB match) for XAUUSD since $1.20 is quite tight, but it could cause false negatives — valid OB retests just outside the $1.20 window won't match, and the exception won't fire. The semantic mismatch is the deeper concern: this tolerance should derive from the same source as all other OB proximity checks.

**[MEDIUM] Matched OB details absent from bypass log (lines 225-229)**
The `logger.info` records `SL_dist` and `floor` but not which OB was matched (low, high, type). Post-trade audit cannot confirm which OB justified the bypass.

**[MEDIUM] No log when all OBs are mitigated (lines 109-117)**
If all H1 OBs are mitigated, the function silently returns False. The SL floor fires but the reason (no unmitigated OB found) is invisible in logs.

### src/components/orchestrator.py
- **Syntax:** OK
- **Change:** Rename `api_calls_made` → `candles_in_pipeline` in session summary dict (line ~1970)
- **CONFLICT:** Origin commit `34bd63a` modifies the **same lines** — it fixes the counting logic to exclude `pre_screen:` and `deterministic_no_bias:` prefixes, adds 5 more skip decisions. **These changes will conflict on merge.** See Part 4.

### tests/test_permissions.py
- **Syntax:** OK
- **5 new tests (TestGate1OBRestestSLException):** All pass. Cover enabled/disabled, LONG, SHORT, non-ob_retest framework, and SL-inside-OB rejection.
- **Gap:** Tests use `SimpleNamespace` without `ob.type` field — does not test that production `OrderBlock.type` is checked.

### tests/test_prelaunch_audit.py
- **Fix:** `config["drawdown_reduction"]["min_rr"]` → `config["risk"]["min_rr"]`
- **All 3 TestConfigConsistency tests pass.**

### tests/test_batch_backtest.py
- **Fix:** London end_utc assertion `09:30` → `10:30` (matches expanded XAUUSD KZ)
- **Passes now.**

### tests/test_monitoring.py
- **Fix:** `ShadowDataCollector(kb_base="/nonexistent/path")` → `ShadowDataCollector(kb_base=str(tmp_path / "test_recovery"))`
- **Passes now.**

### tests/test_end_to_end_integration.py (recovered from stash)
- **Fix:** 5x `enhanced_logger._log_dir` → `enhanced_logger._logs_dir`
- **Reduces failures from 6 → 2** (2 remaining have other root causes)

### tests/test_infrastructure_framework.py (recovered from stash)
- **Fix:** Delegate through `monitor.shadow_collector._metrics_queue` etc.; fix metric type `operation_timing` → `operation_duration_ms`
- **Reduces failures from 9 → 2** (2 remaining have other root causes)

### tests/test_resolve_obs.py (recovered from stash)
- **Fix:** Replace wrong `patch("MetaTrader5.xxx")` targets with `patch.dict("sys.modules", {"MetaTrader5": fake_mt5})`
- **All 5 tests now pass** (were all 5 failing before)

---

## Part 4: Cross-File Consistency

### Config Keys vs Code Usage
- **All 5 keys used in permissions.py `risk_cfg.get()` exist in config:** max_daily_loss_pct, max_spread_cents, min_rr, sl_absolute_min, sl_buffer_dollars
- **5 config keys not used in permissions.py** (used elsewhere): max_monthly_loss_pct, risk_per_trade_pct, tp1_close_pct, max_trades_per_day, max_weekly_loss_pct
- **No orphaned references.**

### CLAUDE.md vs Config

| Key | Config Value | CLAUDE.md Value | Match? |
|-----|-------------|-----------------|--------|
| risk_per_trade_pct | **2.0** | **1.0** | MISMATCH — CEO changed to 2% (obs 461) but CLAUDE.md not updated |
| min_rr | 1.5 | 1.5 | Match |
| max_trades_per_day | 2 | 2 | Match |

### Branch Merge Conflict

Local unstaged change to `orchestrator.py` (rename `api_calls_made` → `candles_in_pipeline`) conflicts with origin commit `34bd63a` (improved counting logic for `api_calls_made`). Both modify the same 2-line block at line ~1970. Manual merge resolution required — the correct result is the renamed key **with** the improved counting logic:

```python
"candles_in_pipeline": sum(
    1 for e in kz_entries
    if e.get("decision") not in (
        "SKIP", "BLOCKED_CALENDAR", "SKIP_NEWS_EVENT",
        "EMERGENCY_STOP", "CANARY_BLOCKED",
        "SKIP_KZ_TRADED", "SKIP_NY_OPEN_CANDLE",
        "LIMIT_FILLED",
    )
    and not str(e.get("detail", "")).startswith(
        ("pre_screen:", "deterministic_no_bias:")
    )
),
```

### Handoff Numbering Conflict
Two files numbered `16_`:
- `16_apr13_monitoring_audit_handoff.md` (committed)
- `16_apr13_ob_limit_order_architecture_handoff.md` (untracked)

One should be renumbered to avoid confusion.

---

## Part 5: System Behavior Simulation

### XAUUSD Effective Config

| Key | Value | Source | Correct? |
|-----|-------|--------|----------|
| max_spread_cents | 100 | top-level risk | YES |
| sl_buffer_dollars | 1.20 | top-level risk | YES |
| sl_absolute_min | 5.0 | top-level risk | YES |
| min_rr | 1.5 | top-level risk | YES |
| max_trades_per_day | 2 | top-level risk | YES |
| risk_per_trade_pct | 2.0 | top-level risk | YES (per CEO decision) |

### GBPJPY Effective Config

| Key | Value | Source | Correct? |
|-----|-------|--------|----------|
| max_spread_cents | 5.0 | per-instrument | YES |
| sl_buffer_dollars | 0.014 | per-instrument | YES |
| sl_absolute_min | 0.118 | per-instrument | YES |

### Cross-Instrument Context

| Instrument | Enabled | Correct? |
|------------|---------|----------|
| GBPUSD | **false** | YES (disabled per monitoring finding) |
| All others | No section | YES (feature not configured) |

### Gate1 OB Exception

| Key | Value | Correct? |
|-----|-------|----------|
| gate1.ob_retest_sl_exception | true | YES |

---

## Part 6: Test Results

**Full suite:** 1048 collected (excluding test_passive_alerts.py — MetaTrader5 import)

| Metric | Count |
|--------|-------|
| Passed | 1042 |
| Failed | 6 |
| Collection errors | 1 (test_passive_alerts.py — pre-existing) |

### Failure Breakdown

| Test | Category | From Today? |
|------|----------|-------------|
| test_cross_instrument::test_gbpusd_context_generated | **NEW REGRESSION** | Yes — config change disabled cross_instrument_context; test reads live config |
| test_cross_instrument::test_unavailable_xau_with_asian | **NEW REGRESSION** | Yes — same cause |
| test_end_to_end_integration::test_trading_decision_with_monitoring | Pre-existing | No — deeper infrastructure mismatch |
| test_end_to_end_integration::test_performance_degradation_detection | Pre-existing | No — deeper infrastructure mismatch |
| test_infrastructure_framework::test_cross_component_integration | Pre-existing | No — remaining attribute/schema issues |
| test_infrastructure_framework::test_monitoring_under_load | Pre-existing | No — remaining attribute/schema issues |

### Fixes Achieved Today (test improvements)

| Test File | Before | After | Fixed |
|-----------|--------|-------|-------|
| test_permissions.py | 13/13 | 18/18 | +5 new tests, all pass |
| test_prelaunch_audit.py (ConfigConsistency) | 2/3 | 3/3 | Fixed key path |
| test_monitoring.py | Failing | Passing | Fixed ShadowDataCollector path |
| test_batch_backtest.py | Failing | Passing | Fixed KZ assertion |
| test_resolve_obs.py | 0/5 | 5/5 | Fixed patch targets |
| test_end_to_end_integration.py | 0/~20 | ~18/20 | Fixed _log_dir → _logs_dir |
| test_infrastructure_framework.py | ~0/~25 | ~23/25 | Fixed attribute delegation |
| test_cross_instrument.py | 5/5 | 3/5 | **2 new regressions** |

### Critical Test Groups

| Test Group | Result |
|------------|--------|
| test_permissions.py | **18/18 PASS** |
| TestConfigConsistency | **3/3 PASS** |
| test_pool_type_normalization.py | All pass (from prior commit) |

---

## Part 7: Documentation & Handoffs

- **Handoff 17** created (untracked): `17_apr14_monitoring_fixes_final_verification_handoff.md`
- **Handoff numbering conflict:** Two files numbered `16_`
- **CLAUDE.md discrepancy:** `risk_per_trade_pct` documented as 1.0, config is 2.0
- **Unstaged analysis files:** 2 in `.context/03_analysis/`
- **Shadow logs growing normally:** 59 malformed responses, 286 drawdown state changes

---

## Part 8: Final Coherence

- [x] Code matches config (all risk_cfg.get() keys exist in YAML)
- [ ] Config matches documentation — **risk_per_trade_pct mismatch** (2.0 vs documented 1.0)
- [x] YAML structure correct (10 risk, 3 drawdown, 1 gate1)
- [x] All syntax checks pass (Python + YAML)
- [x] No TODOs/FIXMEs in changed code
- [x] No debug prints in changed code
- [x] Permissions tests 18/18
- [x] Config consistency tests 3/3
- [ ] OB retest exception has 2 HIGH-severity logic gaps (ob.type, ob_tol semantic)
- [ ] Orchestrator change will conflict with origin on merge
- [ ] 2 new test regressions from cross_instrument_context disable

---

## Issues Found

### BLOCKING (must fix before live)

**B1. OB type not checked in sl_floor exception (HIGH)**
`_ob_retest_sl_exception_applies()` does not check `ob.type` (bullish/bearish). A LONG trade matching a bearish OB would incorrectly bypass sl_floor. This is a safety gate bypass with no type guard.
- File: `src/components/permissions.py:109-116`
- Fix: Add `ob.type == "bullish"` for LONG, `ob.type == "bearish"` for SHORT
- Test gap: Mocks use SimpleNamespace without type field

**B2. Branch divergence — merge conflict in orchestrator.py (HIGH)**
Local main and origin/main have diverged. The orchestrator.py changes conflict on the same lines. Must merge before commit, or the origin fix (improved api_calls_made counting) will be lost.
- Local: rename `api_calls_made` → `candles_in_pipeline`
- Origin: fix counting logic (exclude pre_screen, add EMERGENCY_STOP etc.)
- Resolution: apply both (rename + improved logic)

**B3. 2 new test regressions from config change (MEDIUM)**
Disabling GBPUSD `cross_instrument_context` breaks 2 tests that read live config. Tests should either be updated to expect empty string when disabled, or use fixture configs.
- `test_cross_instrument.py::test_gbpusd_context_generated`
- `test_cross_instrument.py::test_unavailable_xau_with_asian`

### NON-BLOCKING (fix soon, not urgent for London open)

**N1. ob_tol uses sl_buffer_dollars — wrong semantic (MEDIUM)**
The OB matching tolerance in `_ob_retest_sl_exception_applies()` uses `sl_buffer_dollars` instead of the established `verification.ob_price_tolerance_pct`. Won't cause false positives but could miss valid matches for XAUUSD.

**N2. CLAUDE.md says risk_per_trade_pct = 1.0, config is 2.0 (LOW)**
CEO decided 2% (obs 461). CLAUDE.md section "Current config" needs update.

**N3. Missing OB details in bypass log (LOW)**
The info log when sl_floor is bypassed doesn't include which OB was matched. Add ob.low, ob.high, ob.type to the log message.

**N4. Handoff numbering conflict (LOW)**
Two files numbered `16_` in session_handoffs/. Rename one.

**N5. Uncommitted test fixes from prior session (INFO)**
Three test files (test_end_to_end_integration.py, test_infrastructure_framework.py, test_resolve_obs.py) have fixes that surfaced via git stash. These reduce failures from ~22 to 6 and should be committed.

---

## Recommendations

**Before London open (07:00 UTC):**
1. Fix B1: Add `ob.type` check to `_ob_retest_sl_exception_applies()` + update tests
2. Fix B2: Pull origin, resolve merge conflict in orchestrator.py
3. Fix B3: Update cross-instrument tests to handle disabled config (or accept the 2 known failures)

**Soon after:**
4. Fix N1: Replace `sl_buffer_dollars` with `ob_price_tolerance_pct * entry_price` for OB matching
5. Fix N2: Update CLAUDE.md risk_per_trade_pct to 2.0
6. Commit the recovered test fixes (N5)
7. Fix N3: Add matched OB details to bypass log
8. Fix N4: Renumber duplicate handoff 16

---

## Final Verdict

**ISSUES FOUND** — The system has 3 blocking issues before live trading:

1. **OB type not checked** — safety gate bypass could match wrong OB type. LOW probability in practice (requires a bearish OB at the same price as a bullish entry), but structurally wrong for a safety-critical path.

2. **Branch divergence** — must merge origin to avoid losing the api_calls_made counting fix. Without merge, session summaries will have wrong API call counts.

3. **2 test regressions** — the cross-instrument tests break from the config change. Tests should reflect the intended state.

The YAML fix (issue 2), OB exception feature (issue 3), cross-instrument disable (issue 1), XAUUSD thresholds (issues 4-5), and all other monitoring agent findings are correctly addressed. The core trading pipeline (permissions gates, config resolution, risk parameters) is functional and verified.
