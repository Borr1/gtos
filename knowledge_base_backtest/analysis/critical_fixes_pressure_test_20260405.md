# Critical Fixes Pressure Test Report
Date: 2026-04-05

---

## EXECUTIVE SUMMARY

**7 of 10 tests PASS. 1 CRITICAL blocker found. 2 PARTIAL failures.**

The most important finding: **`contract_size` is MISSING from `agent_config.yaml`**. The execution engine defaults to 100 (correct for gold). For GBPUSD, the correct value is 100,000. Using the wrong default produces a **1000x position sizing error** — a 1% risk trade becomes a 1000% risk trade. **This MUST be fixed before any non-gold trading.**

---

## TEST RESULTS

### Test 1: C6 — Trade Monitoring Dead Zone — PASS

**Branch table (verified against orchestrator.py lines 188-246):**

| Branch | Calls trade check? | How often? | Sleep method |
|--------|-------------------|------------|-------------|
| During KZ (candle wait) | YES | Every 60s during wait | `_monitored_sleep` (line 208) |
| After candle process | YES | Per candle | Direct call (line 215) |
| Between KZs (inter-KZ) | YES | At entry + every ≤60s loop | Direct (line 218) + `_interruptible_sleep(min(wait,60))` (line 226) |
| After all KZs | YES | At entry + every 60s | Direct (line 229) + `_monitored_sleep(60)` (line 232) |
| Else (pre-London) | YES | If active trade, every ≤300s | Direct (line 240) + `_monitored_sleep` (lines 244/246) |

**`_check_trade_and_capture()` call sites in orchestrator.py:** 5 total (lines 215, 218, 229, 240, 897).

**`_monitored_sleep()` implementation (lines 890-897):**
- Sleeps in 60s chunks via `_interruptible_sleep`
- After each chunk, checks `self.execution.active_trade` and calls `_check_trade_and_capture()` if true
- All long sleeps in the main loop now use this method

**Verdict:** All branches covered. No dead zone possible during any sleep. The +120 min delay after NY was removed — `_is_after_all_kz()` now triggers immediately at NY end.

---

### Test 2: C1 — Instrument Overrides — PASS (with minor gap)

**`_load_config()` (line 972-988):**
- Calls `apply_instrument_overrides(raw, symbol)` at line 975
- This is called in `__init__` (line 66) BEFORE `_bootstrap()` which inits ExecutionEngine, permissions, etc.
- Order is correct: config loaded → overrides applied → components initialized

**`apply_instrument_overrides()` in `src/utils/config.py` (line 25-58):**
- Deep-merges instrument-specific overrides from `config['instruments'][symbol]`
- Sets `market.symbol` to the requested symbol
- Removes `instruments` key from output (downstream sees flat config)
- Raises `ValueError` if symbol not found in instruments dict

**`run_agent.py` (line 29):** `--symbol` argument present, passed to `SessionOrchestrator(symbol=args.symbol)`

**`replay_session.py`:** Does NOT support `--symbol`. Not in the fix scope but noted.

**Config verification (from agent_config.yaml):**
- GBPUSD override at line 151: KZ london end = "12:00", cross_instrument_context.enabled = true, sl_absolute_min = 0.0003 ✓
- XAUUSD override at line 142: NY end extended to "17:00" ✓

**Verdict:** PASS. Overrides apply correctly before any component reads config.

---

### Test 3: C4 — Execution XAUUSD Removal — CRITICAL FAIL

**grep "XAUUSD" execution.py:** 1 match — line 59 (fallback default in `config.get()`). Acceptable.

**`self.symbol` set in `__init__` (line 59):** `config.get("market", {}).get("symbol", "XAUUSD")` ✓

**Position sizing (lines 79-86):**
```python
contract_size = self.config.get("risk", {}).get("contract_size", 100)
lots = risk_amount / (sl_distance * contract_size)
```

**CRITICAL: `contract_size` is NOT defined in `agent_config.yaml`** — not in base `risk:` section, not in any instrument override. Default of 100 always applies.

**Position sizing calculations:**

| Scenario | Balance | Risk% | Risk$ | SL_dist | Contract Size | Expected Lots | Actual Lots (code) |
|----------|---------|-------|-------|---------|---------------|---------------|-------------------|
| Gold (XAUUSD) | $100K | 1% | $1,000 | $10.00 | 100 | 1.00 | 1.00 ✓ |
| GBPUSD (correct) | $100K | 1% | $1,000 | 0.0050 | 100,000 | 2.00 | — |
| GBPUSD (current bug) | $100K | 1% | $1,000 | 0.0050 | 100 (default!) | **2,000.00** | **2,000.00** ✗ |

**Impact:** For GBPUSD, the code would calculate 2,000 lots instead of 2.00 lots — a **1,000x position sizing error**. Risk would be $1,000,000 instead of $1,000. MT5 would likely reject the order (exceeds margin), but if it doesn't, this is catastrophic.

**Required fix:** Add `contract_size` to config:
- Base `risk:` section: `contract_size: 100` (gold default)
- GBPUSD instrument override: `contract_size: 100000`
- Each instrument must specify its own contract size

**Verdict:** CRITICAL FAIL. Gold trading unaffected (default 100 is correct). Any non-gold instrument has catastrophically wrong position sizing.

---

### Test 4: C5 — Data Ingestion XAUUSD Removal — PASS

**grep "XAUUSD" data_ingestion.py (excluding comments):** 2 matches:
- Line 60: `config.get("market", {}).get("symbol", "XAUUSD")` — fallback default ✓
- Line 247: `symbol: str = "XAUUSD"` — parameter default in `pull_m5_candles()` ✓

**Symbol flow verified:**
- `ingest_live_data()` reads `config["market"]["symbol"]` at line 60 ✓
- `pull_m5_candles()` accepts `symbol` parameter, used at line 257: `mt5.copy_rates_from_pos(symbol, TF_M5, ...)` ✓
- Orchestrator passes `self._symbol` at line 741 ✓

**Verdict:** PASS. All MT5 calls use the configured symbol.

---

### Test 5: Permissions Parameterized — PASS (with minor gap)

**Parameterization verified:**
- `check_permissions()` accepts `config` and `symbol` (line 20-22) ✓
- Gate 3 reads `max_daily_loss_pct` from config (line 45) ✓
- Gate 3 spread check uses passed `symbol` for tick (line 70) ✓
- Gate 3 reads `max_spread_cents` from config (line 71) ✓
- Gate 1 reads `sl_absolute_min` from config (line 144) ✓

**Caller analysis:**
- `orchestrator.py` line 396: passes `config=self.config, symbol=self._symbol` ✓
- `replay_session.py` line 393: **NO config or symbol passed** — uses defaults (XAUUSD, hardcoded 5.0 SL floor, 30 spread, 2.0 daily loss). Not a live-trading issue but replay won't correctly simulate non-gold instruments.
- Test files: use defaults — acceptable for tests targeting gold behavior.

**Spread unit check:**
- MT5: `spread_cents = (ask - bid) * 100`
- Gold: spread $0.30 → spread_cents = 30. Config: max_spread_cents = 30. ✓ Same unit.
- GBPUSD: spread 0.00015 → spread_cents = 0.015. Config: max_spread_cents = 0.03 (≈3 pips). ✓ Same unit.
- Unit is consistent. Naming is gold-centric ("cents") but values are in the same scale.

**Verdict:** PASS for live trading. replay_session.py has stale call signature (won't break — defaults are backward compatible — but won't use instrument-specific thresholds).

---

### Test 6: H9 — TP/SL Modify Return Handling — PASS

**`_modify_tp()` (lines 438-459):**
- Attempt 1 → if fail, logs warning, sleeps 1s
- Attempt 2 → if fail, logs error "Continuing with existing TP"
- Returns False but does NOT close position ✓
- TP failure = trade continues running ✓

**`_modify_sl()` (lines 419-436):**
- Attempt 1 → if fail, sleeps 1s
- Attempt 2 → returns bool
- Callers handle the bool:

**Caller behavior on SL failure:**
- `_move_sl_to_breakeven()` (line 416): calls `self.close_position("sl_modification_failed")` ✓
- `_execute_tp2_partial()` (line 351): checks `sl_ok`, if False → `self.close_position("sl_modification_failed")` ✓

**Module Rule 3 compliance:** SL modify failure → position closed ✓. TP modify failure → position NOT closed ✓.

**Verdict:** PASS.

---

### Test 7: M8 — L2 Post-M5 Re-verification — PASS

**M5 refinement code (orchestrator.py lines 356-392):**
1. If M5 `applied` = True, `apply_m5_overrides(analysis, m5_out["overrides"])` updates analysis
2. Immediately re-runs `verify_candidate(analysis, mso, self.config)` (line 376)
3. Checks specifically for `sl_beyond_ob` failure (line 377)
4. If `sl_beyond_ob` FAIL → rejects with `REJECTED_L2_POST_M5` and returns

**Does M5 change entry_price?** No — confirmed in verification report: "M5 does NOT change entry_price, so Checks 4-5 (entry_in_ob, ob_zone) remain valid."

**Re-verification uses updated analysis:** Yes — `apply_m5_overrides` modifies `analysis` in-place before `verify_candidate` is called with it.

**Verdict:** PASS.

---

### Test 8: No New Issues Introduced — FAIL (2 issues)

**Issue 1: Missing `contract_size` in config** (see Test 3)
- The code references `config.risk.contract_size` but no instrument defines it
- Default of 100 works only for gold

**Issue 2: `replay_session.py` stale `check_permissions` call**
- Line 393: `check_permissions(analysis, mso, session_state, self.mt5)` — no config/symbol
- Not a live-trading risk (backward-compatible defaults used)
- But replay won't accurately simulate non-gold permission thresholds

**Import check:** `from src.utils.config import apply_instrument_overrides` in orchestrator.py — verified, module exists ✓

**Signature compatibility:** `check_permissions()` new params have defaults — all callers compile. No crash risk.

**Default parameter safety:** If config is None, `(config or {}).get("risk", {})` returns empty dict, then `.get("sl_absolute_min", 5.0)` returns default. Safe — no crash, but uses gold defaults.

**Verdict:** FAIL due to contract_size gap.

---

### Test 9: Full Regression — PASS

```
549 passed, 0 failed, 19 warnings (pre-existing deprecation warnings)
```

No new tests were added by the fix session (the verification report confirmed all 549 pre-existing tests pass).

**Verdict:** PASS.

---

### Test 10: End-to-End Instrument Switching — PARTIAL FAIL

**GBPUSD pipeline trace:**

| Component | GBPUSD-specific? | Detail |
|-----------|-----------------|--------|
| Config load | ✓ | `apply_instrument_overrides` merges GBPUSD section |
| Orchestrator symbol | ✓ | `self._symbol = "GBPUSD"` from config |
| KZ times | ✓ | London end = "12:00" (from override), NY = "13:00"-"15:30" (base default) |
| Execution engine symbol | ✓ | `self.symbol = "GBPUSD"` from config |
| Data ingestion symbol | ✓ | Reads from config, pulls GBPUSD candles |
| Permissions symbol | ✓ | Passed via orchestrator |
| SL floor | ✓ | 0.0003 from GBPUSD override |
| Max spread | ✓ | 0.03 from GBPUSD override |
| Cross-instrument context | ✓ | enabled=true, reference=XAUUSD |
| **Position sizing** | **✗** | **contract_size defaults to 100 instead of 100,000** |

**Verdict:** PARTIAL FAIL — everything correct except the critical contract_size gap.

---

## SUMMARY TABLE

```
=== CRITICAL FIXES PRESSURE TEST ===
Test 1  (C6 Monitoring Dead Zone):    PASS   — 5 call sites, all branches covered, 60s monitoring during all sleeps
Test 2  (C1 Instrument Overrides):    PASS   — overrides apply for XAUUSD and GBPUSD before component init
Test 3  (C4 Execution XAUUSD):        FAIL** — 0 hardcoded (good), but contract_size MISSING from config (CRITICAL)
Test 4  (C5 Data Ingestion XAUUSD):   PASS   — 0 hardcoded, symbol flows from config through all MT5 calls
Test 5  (Permissions Parameterized):   PASS   — all thresholds from config; replay_session.py stale (non-blocking)
Test 6  (H9 TP/SL Modify):            PASS   — TP logs+continues, SL closes position on failure
Test 7  (M8 L2 Post-M5):              PASS   — re-verified with updated SL after M5 refinement
Test 8  (No New Issues):              FAIL   — contract_size missing, replay_session stale call
Test 9  (Regression):                 PASS   — 549 tests passing, 0 new tests added
Test 10 (End-to-End Instrument):      FAIL*  — GBPUSD traces correctly EXCEPT contract_size defaults wrong
```

`**` = CRITICAL — blocks non-gold live trading
`*` = Fails due to contract_size dependency

---

## REQUIRED FIXES BEFORE NON-GOLD TRADING

### FIX 1 (CRITICAL): Add `contract_size` to config

**In `config/agent_config.yaml`:**

Base `risk:` section:
```yaml
risk:
  contract_size: 100  # 1 lot = 100 oz for XAUUSD
```

GBPUSD instrument override:
```yaml
instruments:
  GBPUSD:
    risk:
      contract_size: 100000  # Standard forex lot
```

All other instrument overrides need their contract_size specified:
- EURUSD: 100000
- USDJPY: 100000 (note: JPY pairs have different P&L calculation)
- XAGUSD: 5000 (silver)

### FIX 2 (LOW): Update `replay_session.py` check_permissions call

```python
# Line 393: add config and symbol
denial = check_permissions(analysis, mso, session_state, self.mt5,
                           config=self.config, symbol=self._symbol)
```

---

## GOLD-ONLY ASSESSMENT

For **XAUUSD-only trading**, all 7 critical fixes are verified working:
- Trade monitoring has no dead zones
- Position sizing is correct (contract_size default 100 = gold standard)
- All permission thresholds work correctly
- TP/SL modify handling follows Module Rule 3
- L2 re-verification after M5 is functional

**The system is safe for XAUUSD live trading.** The contract_size issue only affects non-gold instruments.
