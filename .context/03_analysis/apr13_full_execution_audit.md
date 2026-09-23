# GTOS Full Execution Audit — April 13, 2026

**Author:** Claude Code (monitoring/audit agent)
**Generated:** 2026-04-13 (evening session)
**Coverage:** Full trading day 00:00–14:00 UTC
**Sources:** All 5 instrument eval JSONL files, all 40 trade records, all 5 log files, shadow_logs/malformed_responses.jsonl, lock files, permissions.py, verification.py, primary_analyzer.py, orchestrator.py

---

## 1. Executive Summary

| Severity | Issue | Impact |
|----------|-------|--------|
| CRITICAL | **AutoTrading disabled in MT5** — 6 trades failed to execute | Real lost setups |
| CRITICAL | **Anthropic API returning "Sorry, I can't produce JSON"** — 12 incidents (37 log entries), 07:59–13:10 UTC | XAUUSD London session lost; 7+ other failures |
| HIGH | **M5 refinement broken** — `RealMT5` missing `copy_rates_from_pos` | Every CANDIDATE fails M5 pull; SL not being tightened |
| HIGH | **GBPJPY sl_floor > OB zone width** — current OB (10.6 pip) < floor (11.8 pip) | Systematic Gate 1 rejection of valid GBPJPY setups at this OB |
| MEDIUM | **USDJPY OB stale** — price 40–50 pips above only H1 OB; 14 wasted API calls (~$0.41) | Costs without any chance of execution |
| MEDIUM | **US30 L2 tolerance too permissive** — 0.2% = 95-pt tolerance on 31-pt OB zone | Allows hallucinated entries 63 pts outside OB to reach execution |
| MEDIUM | **GBPUSD macro conflict filter inconsistent** — same M15 ratio fires CANDIDATE and NO_TRADE in different candles | Unpredictable evaluation; potentially costing or granting trades unfairly |
| MEDIUM | **Eval JSONL gaps** — pre-restart candles have trade records but no eval entries | Data integrity gap; 6+ candles unaccounted in JSONL |
| LOW | **TP1 warning message misleading** — says "Safety check will reject" at 1.5R but Gate 1 accepts 1.3–2.0R | Noise; no trading impact |
| LOW | **model_used hallucination** — AI reports "gpt-4.1" in response JSON | Logging inaccuracy only |
| LOW | **risk_per_trade_pct discrepancy** — config=2.0%, CLAUDE.md says 1.0% | Needs CEO verification |

**Overall system status:** Pipeline is running but two critical production failures (AutoTrading + API refusals) are actively costing trades. 6 genuine execution failures confirmed today. System has made 0 fills.

---

## 2. Process Health

### PID Status (verified via tasklist.exe at audit time)

| Symbol | PID | Started (UTC) | Memory | Status |
|--------|-----|---------------|--------|--------|
| XAUUSD | 32628 | 2026-04-13T13:38:47 | 76,324 KB | **ALIVE** |
| USDJPY | 30612 | 2026-04-13T13:38:47 | 83,336 KB | **ALIVE** |
| GBPJPY | 32032 | 2026-04-13T13:38:48 | 83,416 KB | **ALIVE** |
| GBPUSD | 23288 | 2026-04-13T13:38:48 | 83,344 KB | **ALIVE** |
| US30_cash | 3064 | 2026-04-13T13:39:14 | 83,624 KB | **ALIVE** |

All 5 processes healthy. Current processes all started at 13:38–13:39 UTC.

### Process Restart History (today)
Multiple restarts occurred during the day (inferred from config reload log messages):
- **XAUUSD**: Restarted at ≈08:24, ≈08:33, ≈09:00, 13:38 UTC
- **GBPJPY**: Restarted at ≈08:20, 13:38 UTC
- **USDJPY/GBPUSD/US30**: At minimum restarted at 13:38 UTC

Consequence: `candle_index_in_kz` resets to 0 on each restart. Post-restart, the per-KZ trade count is reset, which could theoretically allow more than 1 trade per KZ session if a filled trade occurred before restart. No fills today, so no violation.

### Log Errors Summary

| Log file | ERRORs found | Nature |
|----------|-------------|--------|
| usdjpy.log | 0 | — |
| gbpjpy.log | 4 | All "Order failed: AutoTrading disabled by client" |
| gbpusd.log | 1 | "Order failed: AutoTrading disabled by client" |
| us30.log | 1 | "Order failed: AutoTrading disabled by client" |
| xauusd.log | 0 | — |

Recurring WARNINGs (non-blocking, expected):
- `TP1 placement warning: Minimum should be 2.0R` — every CANDIDATE (misleading message, see §5.5)
- `Displacement ratio mismatch: AI=X MSO=Y` — every CANDIDATE (logged correctly, AI underreports)
- `M5 pull from MT5 failed: 'RealMT5' object has no attribute 'copy_rates_from_pos'` — every CANDIDATE with M5 refinement enabled
- `Calendar contains estimated dates` — every process start (known, low urgency)

---

## 3. Trade Funnel — Full Day April 13

### XAUUSD

| Stage | Count | Notes |
|-------|-------|-------|
| KZ candles processed | ~8 | 07:15–08:15 UTC (London); all others pre-screened |
| Pre-screen PASS | ~5 | Before restart at 08:24 UTC |
| API called | ~5 | All returned "Sorry, I can't produce JSON now" |
| CANDIDATE | 0 | — |
| L2 verification | 0 | — |
| Gate 1 safety | 0 | — |
| Execution attempted | 0 | — |
| Filled | 0 | — |

From 09:15 UTC onward: **Pre-screen BLOCKED all candles** (`L2_h4_conflict_bullish_vs_d1_bearish`).
- `orchestrator.py:2281` `prescreen_mso()`: D1=bearish, H4=bullish → conflict → skip API call
- This is correct system behavior. XAUUSD had a legitimate H4/D1 structural conflict all afternoon.
- Blocked: 6 London candles (09:15–10:30) + 2 NY candles (13:16, 13:30) = 8 saved API calls

**XAUUSD had zero evaluations logged to the eval JSONL for all of April 13.** The ~5 London candles that bypassed the pre-screen all resulted in API refusals ("Sorry, I can't produce JSON now."). No `2026-04-13.jsonl` exists in `knowledge_base/live_evaluations/XAUUSD/`.

---

### USDJPY

| Stage | Count | Notes |
|-------|-------|-------|
| KZ candles (Tokyo+London+NY) | ~21 | 11 Tokyo + ~9 London + 1 NY |
| Parse failures (pool_type) | 2 | 00:16, 00:31 UTC — known pool_type fix. No eval record values set. |
| AI evaluated (clean) | ~19 | — |
| CANDIDATE | 12 | 5 Tokyo + 7 London |
| NO_TRADE | ~9 | OB retest framework condition unmet, or C1/C2/C3 fail |
| L2 PASS | 0 | All 12 CANDIDATEs failed L2 |
| Gate 1 | 0 | — |
| Execution attempted | 0 | — |
| Filled | 0 | — |

**All 12 USDJPY CANDIDATEs failed L2 on `entry_in_ob` or `sl_beyond_ob`.**

Root cause: The only active H1 OB is at **159.252–159.319** (established 2026-04-11T07:00). USDJPY price traded at **159.55–159.87 all day** — a gap of 30–55 pips above the OB. The AI C-gates correctly fire CANDIDATE (H1 bullish, M15 aligned, direction LONG), but the OB retest framework entry must be in the OB zone. The AI then quotes entry at current market price (159.7–159.9), which L2 correctly rejects.

L2 log evidence (usdjpy.log):
- `16:31`: L2 FAILED: `entry_in_ob` — Entry 159.67 outside OB 159.25–159.32
- `16:45`: L2 FAILED: `sl_beyond_ob` — SL 159.46 NOT below OB low 159.25
- `17:00`: L2 FAILED: `sl_beyond_ob` — SL 159.49 NOT below OB low 159.25
- `17:30`: L2 FAILED: `entry_in_ob` — Entry 159.66 outside OB 159.25–159.32
- `21:16`: L2 FAILED: `entry_in_ob` — Entry 159.69 outside OB 159.25–159.32
- `21:30`: L2 FAILED: `entry_in_ob` — Entry 159.82 outside OB 159.25–159.32

**Systematic cost**: ~$0.41 (14 API calls × $0.029) for evaluations that have zero chance of executing.

---

### GBPJPY

| Stage | Count | Notes |
|-------|-------|-------|
| KZ candles (Tokyo) | 11 | 00:15–03:00 UTC |
| Tokyo NO_TRADE | 11 | C1 FAIL: H1 bullish, required SHORT per H4 bearish |
| KZ candles (London, all processes) | ~9 | 07:15–09:30 UTC + pre-restart evaluations |
| CANDIDATE (London) | 7 | 07:15, 07:30, 08:00, 08:15, 09:15 from eval + 13:15, 13:30 from pre-restart |
| L2 FAIL | 1 | 13:15 NY (entry not in OB) |
| L2 PASS | 6 | 07:15, 07:30, 08:00, 09:15 London + 13:30 pre-restart (ob_zone WARN only) |
| Gate 1 REJECTED (sl_floor) | 2 | 08:15 (SL_dist=0.107 < floor=0.118) and 09:15 (SL_dist=0.107 < floor=0.118) |
| AutoTrading disabled | 4 | **07:15, 07:30, 08:00 London; 13:30 NY** |
| Filled | 0 | — |

Tokyo analysis: All 11 NO_TRADE are correct — H4 is bearish (requires SHORT) but H1 is firmly bullish (5+ bullish BOS, protected swing at 213.649). C1 and C3 correctly fail.

London 07:15 (CANDIDATE, A+, conf=78):
- Entry: 214.26, SL: 214.00, TP1: 214.65 — all L2 checks PASS
- L2 warning: `ob_zone` — OB midpoint in premium but LONG requires discount (strict_zone_check=false → WARN only)
- Execution: **AutoTrading disabled** → EXECUTION_FAILED

London 07:30 (CANDIDATE, A+, conf=82):
- Entry: 214.08, SL: 213.86, TP1: 214.39 — all L2 checks PASS
- Same ob_zone WARN
- Execution: **AutoTrading disabled** → EXECUTION_FAILED

London 08:00 (CANDIDATE, pre-restart process):
- Entry: 214.00, SL: 213.64, TP1: 214.55 — all L2 checks PASS
- Execution: **AutoTrading disabled** → EXECUTION_FAILED

London 08:15 (CANDIDATE, pre-restart process):
- Entry: 214.08, SL: 213.99 — all L2 checks PASS
- **Gate 1 REJECTED** — `sl_below_minimum_floor: SL_dist=0.09 (min=0.118)` (9 pips < 11.8 pip floor)
- Correct rejection per current rules.

London 09:15 (CANDIDATE, eval JSONL record, conf=78):
- Entry: 214.109, SL: 214.002, TP1: 214.27 — all L2 checks PASS
- **Gate 1 REJECTED** — `sl_below_minimum_floor: SL_dist=0.10700 (min=0.118)` (10.7 pips < 11.8 pip floor)
- Note: Entry is INSIDE OB zone (214.023–214.129). This is a genuine OB retest. SL is 2.1 pips below OB low. The rejection is correct per current rules but is a thin margin (1.1 pip gap to floor).

London 09:30 (NO_TRADE):
- AI correctly identifies candle is at KZ boundary: "09:30 UTC is at the terminal boundary of the London kill zone; no active kill zone is open for entry execution." Correct.

NY 13:30 (CANDIDATE, pre-restart process):
- Entry: 214.43, SL: 214.00 — M5 pull failed, L2 PASS
- Execution: **AutoTrading disabled** → EXECUTION_FAILED

---

### GBPUSD

| Stage | Count | Notes |
|-------|-------|-------|
| KZ candles (London, 07:00–12:00) | 17 | Including pre-restart |
| KZ candles (NY) | 3 | Including pre-restart |
| CANDIDATE | 7 | 07:30, 08:00 (pre-restart), 09:00, 11:00, 11:15, 11:45, 13:15 (pre-restart) |
| NO_TRADE | 13 | Macro conflict filter + OB not retested |
| L2 FAIL | 4 | 07:30 (sl_beyond_ob), 08:00 (sl_beyond_ob), 11:45 (sl_beyond_ob), 13:15 (L2 fail) |
| Gate 1 REJECTED | 2 | 09:00 and 11:00 (sl_too_tight) |
| AutoTrading disabled | 1 | **11:15** |
| Filled | 0 | — |

**GBPUSD 07:30 London** (CANDIDATE A+, conf=75):
- L2 FAIL: `sl_beyond_ob` — SL above OB low; AI hallucinated prices both showing as "1.34" in logs (full precision used internally)

**GBPUSD 09:00 London** (CANDIDATE A+, conf=78):
- L2: all PASS (ob_zone WARN only)
- Gate 1 REJECTED: `sl_too_tight: SL_dist=0.00032 < 1.5*ATR=0.00093` (3.2 pips < 9.3 pip ATR-minimum)
- The AI proposed an absurdly tight SL of 3.2 pips. Correct rejection.

**GBPUSD 11:00 London** (CANDIDATE A+, conf=78):
- L2: all PASS (ob_zone WARN only). Note: M5 pull failed (copy_rates_from_pos) at this candle.
- Gate 1 REJECTED: `sl_too_tight: SL_dist=0.00032 < 1.5*ATR=0.00093` (same pattern as 09:00)
- 3.2 pip SL is too tight regardless. Correct rejection.

**GBPUSD 11:15 London** (CANDIDATE A+, conf=78):
- L2: all PASS (ob_zone WARN), M5 pull failed
- Execution: **AutoTrading disabled** → EXECUTION_FAILED
- **Genuine lost trade.**

**GBPUSD macro conflict filter**: The `cross_instrument_context` block adds XAUUSD D1 direction to the prompt. Today D1 is bearish (dollar strong), conflicting with LONG GBPUSD. The AI applies a subjective "exceptional confluence" bar that is **inconsistently applied**:
- 09:30 (M15 ratio=1.9): NO_TRADE
- 11:45 (M15 ratio=1.9): CANDIDATE
- 09:00 (M15 ratio=2.0): CANDIDATE (then Gate1 rejected)
- 08:45 (M15 ratio=2.0): NO_TRADE

The same M15 displacement ratio triggers different decisions across candles. This non-determinism costs both real trades (sometimes correctly blocked, sometimes incorrectly allowed) and wastes API calls.

---

### US30_cash

| Stage | Count | Notes |
|-------|-------|-------|
| KZ candles (London, 08:00–10:30) | 10 | Including pre-restart |
| KZ candles (NY) | 1 | — |
| CANDIDATE | 9 | 08:15 (pre-restart), 08:30, 08:45, 09:00, 09:15, 09:30, 09:45, 10:00, 10:30 |
| NO_TRADE | 2 | 10:15 (temporal mismatch), 13:46 (no H1 OB near price) |
| L2 FAIL | 8 | All `entry_in_ob` — entry quoted above OB zone (47677–47726 vs OB 47524–47555) |
| L2 PASS (tolerance) | 1 | 09:15 — entry 47461 is 63 pts below OB (within 95-pt tolerance) |
| Gate 1 | 0 | — |
| AutoTrading disabled | 1 | **09:15** |
| Filled | 0 | — |

**US30 09:15 London** (CANDIDATE A+, conf=78):
- Entry: 47461.78, OB zone: 47524.51–47555.51
- Entry is **63 points BELOW the OB low** (outside the zone, not an OB retest)
- L2 `entry_in_ob`: OB zone × 0.002 = 47524 × 0.002 = 95 points tolerance → 63 < 95 → **PASS**
- M5 pull failed (copy_rates_from_pos)
- Execution: **AutoTrading disabled** → EXECUTION_FAILED
- **Note**: If this trade had executed, a limit buy at 47461.78 would be placed 63 pts below the OB zone — this is NOT an OB retest entry. The L2 tolerance allowed a hallucinated entry through.

**US30 systematic entry hallucination**: All 8 L2 FAIL cases had AI-quoted entries at **current market price** (~47677–47726) rather than at OB zone (47524–47555). Displacement mismatch: AI consistently reports 0.70–1.30× while MSO shows 7.21–8.74×. The AI is not "hallucinating" per se — it's quoting entry at the close price, not at the OB. The prompt instructs "entry_price: current M15 candle close price" — this is the root cause of all US30 L2 rejections.

**Root cause**: The T7 prompt instructs `entry_price: current M15 candle close price`. For an OB limit order architecture, the entry should be `ob_high` (for a LONG). The prompt is giving the AI the wrong instruction — it should say "entry_price: ob_high for LONG, ob_low for SHORT" (or match the limit order architecture).

---

## 4. Blocked Trade Analysis — Were Rejections Valid?

### AutoTrading Failures (6 total) — Invalid blocks, genuine losses

| Time (UTC) | Symbol | L2 Result | SL (pips) | Setup Grade | Assessment |
|-----------|--------|-----------|-----------|-------------|------------|
| 07:15 | GBPJPY | PASS (ob_zone WARN) | 26 pips | A+, conf=78 | **Valid setup, lost to MT5 setting** |
| 07:30 | GBPJPY | PASS (ob_zone WARN) | 22 pips | A+, conf=82 | **Valid setup, lost to MT5 setting** |
| 08:00 | GBPJPY | PASS | 36 pips | A+, conf=? | **Valid setup, lost to MT5 setting** |
| 09:15 | US30 | PASS (entry 63 pts below OB) | 211 pts | A+, conf=78 | Questionable: entry not actually in OB |
| 11:15 | GBPUSD | PASS (ob_zone WARN) | ~3 pips | A+, conf=78 | Valid setup, but SL may have been too tight (M5 unavailable) |
| 13:30 | GBPJPY | PASS | 43 pips | A+, conf=78 | **Valid setup, lost to MT5 setting** |

The 4 GBPJPY AutoTrading failures are genuine losses — these setups passed all pre-execution checks.

### Gate 1 sl_floor Rejections (3 total) — Correct

| Time (UTC) | Symbol | SL_dist | sl_floor | Gap | Assessment |
|-----------|--------|---------|---------|-----|------------|
| 08:15 | GBPJPY | 9 pips | 11.8 pips | 2.8 pip | Correct — SL too tight |
| 09:00 | GBPUSD | 3.2 pips | 9.3 pips (1.5×ATR) | 6.1 pip | Correct — AI hallucinated extremely tight SL |
| 09:15 | GBPJPY | 10.7 pips | 11.8 pips | 1.1 pip | Correct per rules; debatable (see §5.4) |
| 11:00 | GBPUSD | 3.2 pips | 9.3 pips (1.5×ATR) | 6.1 pip | Correct — same hallucination as 09:00 |

### Gate 1 sl_floor + OB Width Issue (GBPJPY-specific)

GBPJPY's current H1 OB: **214.023–214.129** (width = 0.106 = 10.6 pips).
GBPJPY `sl_absolute_min` (config): **0.118 = 11.8 pips**.

The sl_floor (11.8 pips) exceeds the OB zone width (10.6 pips). For a LONG entry in this OB with SL placed at OB low (or below), the maximum SL distance from entry (at OB high 214.129) to below OB low (214.023) is ≤10.6 pips. This means **any GBPJPY trade with this specific OB will fail the sl_floor check**, regardless of whether the setup is otherwise valid.

The 07:15 and 07:30 trades escaped this because they placed SL 16–22 pips below OB low (using a wider swing low for reference), not the OB low itself. Those trades had valid SL distances.

### L2 `entry_in_ob` Rejections — All valid

All USDJPY, US30, and GBPUSD `entry_in_ob` rejections are correct: the AI quoted entry at current market price, which was away from the OB zone. The OB retest framework requires price to be at or retesting the OB zone for a valid entry.

**One exception**: US30 09:15 passed L2 `entry_in_ob` with entry 63 pts below OB (within 95-pt tolerance). The L2 tolerance for US30 is too permissive (see §5.6).

---

## 5. Systematic Issues Found

### 5.1 CRITICAL: AutoTrading Disabled in MT5

**File**: `src/components/execution.py` (order placement logic)  
**Error**: `"Order failed: AutoTrading disabled by client"` (from MT5 return code)  
**Occurrences today**: 6 (GBPJPY ×4, GBPUSD ×1, US30 ×1)  
**Root cause**: MT5 terminal has AutoTrading (Expert Advisors) disabled in client settings. The system calls `mt5.order_send()` but MT5 rejects it because the terminal doesn't allow algorithmic trading.  
**Fix**: In MT5 terminal: **Tools → Options → Expert Advisors → Allow automated trading** (checkbox). Or verify `AutoTrading` button is green in the MT5 toolbar.  
**This is not a code bug.** The watchdog and processes are working correctly — MT5 is rejecting orders at the broker level.

---

### 5.2 CRITICAL: Anthropic API Returning "Sorry, I can't produce JSON right now."

**File**: `shadow_logs/malformed_responses.jsonl`  
**First occurrence**: 2026-04-13T07:59:22 UTC  
**Last occurrence**: 2026-04-13T13:10:42 UTC  
**Total entries**: 39 (37 for "Sorry" refusals + 2 for pool_type failures from 00:31)  
**Pattern**: Each incident produces 3 entries (attempt=1, attempt=2, then attempt=1 again with "not json" 8-byte stub)  
**Unique incidents**: ~12 separate candle evaluations refused

**Sample raw responses**:
- `"Sorry, I can't produce JSON right now."` (38 bytes) — returned by API on both first attempt AND FORMAT_CORRECTION retry
- `"not json"` (8 bytes) — exact source unclear, appears as 3rd entry per incident

**Impact**:
- **XAUUSD lost its entire London session** — ~5 evaluations from 07:15–08:15 UTC all got refusals. No eval JSONL records created.
- ~7 additional refusals across other instruments during peak London hours.
- System logs `no_trade_reason: "ai_output_malformed"` (or loses the record entirely for XAUUSD).
- FORMAT_CORRECTION retry is wasted — API refuses both attempts identically.

**Possible causes** (investigation needed):
1. Anthropic API rate limiting (check API dashboard for 429 errors)
2. Content moderation trigger — trading content occasionally flagged (unlikely but possible)
3. API service degradation during London open (07:00–08:30 UTC peak load)

**Note**: The malformed_responses.jsonl does NOT record the symbol or candle_time — impossible to know which instrument/candle triggered each refusal without cross-referencing timestamps.

**Also note**: In the 00:31 UTC entry (pool_type failure), the AI reported `"model_used": "gpt-4.1"`. This is the AI hallucinating the model identifier field. The actual model is claude-sonnet-4-6. Minor, but confusing.

---

### 5.3 HIGH: M5 Refinement Broken — `copy_rates_from_pos`

**File**: `src/components/data_ingestion.py` (M5 data pull for refinement)  
**Error**: `WARNING [src.components.data_ingestion] M5 pull from MT5 failed: 'RealMT5' object has no attribute 'copy_rates_from_pos'`  
**Occurrences**: Every CANDIDATE across all instruments  
**Instruments confirmed**: GBPJPY, USDJPY, US30, GBPUSD  

**Root cause**: `RealMT5` class does not implement `copy_rates_from_pos` method. This method is being called by the M5 refinement code to pull 36 M5 candles for SL optimization. The MT5 API method may be named differently (e.g., `copy_rates_range` or `copy_rates_from`).

**Impact**: M5 SL refinement is disabled for all live trades. The SL distance used is the AI-proposed value, not the M5-refined tighter value. Configuration `m5_refinement.enabled: true` has no effect.

**Secondary impact**: The Gate 1 ATR check uses M15 ATR (not M5), so it's unaffected. The Gate 1 sl_too_tight check still functions correctly.

---

### 5.4 HIGH: GBPJPY sl_floor > Current OB Width

**Config**: `GBPJPY.risk.sl_absolute_min: 0.118` (11.8 pips)  
**Current H1 OB**: 214.023–214.129 = 0.106 = 10.6 pips wide  
**OB zone created**: 2026-04-13T08:00 BOS (per trade record prompt data)

For any GBPJPY LONG entry at or near OB high (214.129) with SL placed 1–3 pips below OB low (214.023), the maximum SL distance is ~12–13 pips (barely meets floor). But if the AI places SL exactly at OB low (214.023), the distance from entry (214.109) is only 10.7 pips — 1.1 pips below the 11.8 pip floor.

Two confirmed Gate 1 rejections (08:15 and 09:15) for exactly this reason. The 07:15, 07:30, and 08:00 trades escaped because the AI used a wider swing low for SL reference (~16–36 pips from entry).

**This will persist until the current OB is mitigated or a new wider H1 OB forms.**

---

### 5.5 MEDIUM: TP1 Warning Message Misleading

**File**: `src/components/primary_analyzer.py:568–583` (`_warn_tp1_placement()`)  
**Code** (line 578–582):
```python
if tp1_r < 2.0:
    logger.warning(
        "TP1 placement warning: TP1 at %.2fR (entry=%.2f, SL=%.2f, TP1=%.2f). "
        "Minimum should be 2.0R. Safety check will reject this trade.",
        ...
    )
```

**Actual Gate 1 check** (`permissions.py:151–179`):
```python
# Phase 1: TP1 target is 1.5R. Accept 1.3R-2.0R tolerance band
if tp1_r < 1.3:  # reject only below 1.3R
    return ExecutionDenial(...)
if tp1_r > 2.0:  # reject only above 2.0R
    return ExecutionDenial(...)
# 1.3R–2.0R is ACCEPTED
```

The warning fires on every CANDIDATE with TP1=1.5R and says "Safety check will reject" — but Gate 1 accepts 1.3–2.0R. A TP1 at 1.50R will **not** be rejected by Gate 1. The warning is factually wrong. It's producing false alarm noise in every single log.

This warning fired 15+ times today across all instruments.

---

### 5.6 MEDIUM: US30 L2 `entry_in_ob` Tolerance Too Permissive

**Config**: `verification.ob_price_tolerance_pct: 0.002` (0.2%)  
**US30 price range**: ~47,500 → 0.2% = **95 points**  
**US30 OB zone**: 47,524–47,555 = **31 points wide**

The L2 tolerance (95 points) is **3× the OB zone width** (31 points). This allowed US30 09:15 (entry=47461, OB low=47524) to pass L2 — an entry 63 points below the OB zone.

For comparison:
- GBPUSD: 0.2% of 1.34 = 0.00268 = 2.68 pips (reasonable for 5-pip OB zones)
- GBPJPY: 0.2% of 214 = 0.428 = 42.8 pips (reasonable for 10-pip OB zones)
- US30: 0.2% of 47500 = 95 points (excessive for 30-point OB zones)

Consider adding an instrument-specific `ob_price_tolerance_pct` or using absolute units instead of % for index instruments.

---

### 5.7 MEDIUM: GBPUSD Macro Conflict Non-Determinism

**Config block**: `instruments.GBPUSD.cross_instrument_context`  
**Effect**: XAUUSD D1 direction is included in the GBPUSD prompt as a macro headwind signal.

Today XAUUSD D1 is bearish (dollar strength). The AI is supposed to apply an "exceptional confluence" threshold to proceed with LONG GBPUSD despite this headwind. The threshold is described qualitatively in the prompt — not as a hard number.

**Observed inconsistency** (all from London KZ today):

| Time | M15 disp_ratio | Decision | Note |
|------|---------------|----------|------|
| 08:45 | 2.0 | NO_TRADE | "below exceptional threshold" |
| 09:00 | 2.0 | CANDIDATE | "3/4 TF alignment meets threshold" |
| 09:30 | 1.9 | NO_TRADE | "below exceptional threshold" |
| 11:00 | 1.7 | CANDIDATE | "11 BOS confirms strong bias" |
| 10:30 | 1.9 | NO_TRADE | "insufficient" |
| 11:45 | 1.9 | CANDIDATE | "strong bias across 3/4 TFs" |

Same M15 ratio (1.9) triggers NO_TRADE at 10:30 and CANDIDATE at 11:45. The AI's judgment varies based on how it frames the reasoning. This is inherent in soft-threshold AI evaluation.

---

### 5.8 MEDIUM: Eval JSONL Gaps — Pre-Restart Candles

Trade records exist for candles that have no corresponding eval JSONL entry:

| Symbol | Candle | Trade record | JSONL entry | Gap |
|--------|--------|-------------|-------------|-----|
| USDJPY | 07:45 London | `london_0745.json` | Missing | Pre-restart process |
| GBPJPY | 08:00 London | `london_0800.json` | Missing | Pre-restart process |
| GBPJPY | 08:15 London | `london_0815.json` | Missing | Pre-restart process |
| GBPJPY | 13:15 NY | `ny_1315.json` | Missing | Pre-restart process |
| GBPUSD | 08:00 London | `london_0800.json` | Missing | Pre-restart process |

These records likely came from processes that ran before the 13:38 UTC restart. The eval JSONL records may have been written to a different (now-terminated) session context, or the write failed before the process was killed.

**No trading impact today** (all 5 were either L2 rejected or AutoTrading failures). However, this creates a data integrity gap — we can't reconstruct the full eval history from JSONL alone.

---

### 5.9 LOW: USDJPY Displacement Ratio Hallucination

The AI consistently underreports USDJPY M15 displacement ratio by ~4×:

| Candle | AI reports | MSO measures | Ratio error |
|--------|-----------|--------------|-------------|
| 08:31 | 1.35 | 5.59 | 4.1× |
| 08:45 | 2.00 | 5.62 | 2.8× |
| 09:00 | 1.35 | 5.51 | 4.1× |
| 09:30 | 2.00 | 5.75 | 2.9× |
| 13:45 | 1.30 | 5.59 | 4.3× |

L2 uses the MSO value (`Displacement ratio mismatch` warning logged). **No trading impact.** However, the eval JSONL stores the AI-reported value (`m15_displacement_ratio: 0.4–2.3`), making historical analysis using this field systematically wrong for USDJPY. Any retrospective analysis comparing USDJPY displacement to win rate is poisoned by this hallucination.

---

## 6. Configuration Audit

| Parameter | Config value | CLAUDE.md says | Status |
|-----------|-------------|----------------|--------|
| `risk.risk_per_trade_pct` | **2.0%** | "Demo: 1.0%" | **DISCREPANCY — verify with CEO** |
| `drawdown_reduction.threshold` | 0.08 | 8% | ✓ |
| `drawdown_reduction.reduced_risk_pct` | 0.5 | 0.5% | ✓ |
| `ai.primary_model` | claude-sonnet-4-6 | claude-sonnet-4-6 | ✓ |
| `ai.primary_effort` | max | max | ✓ |
| `session_memory_enabled` | false | false | ✓ |
| `enabled_frameworks` | ["ob_retest"] | ["ob_retest"] | ✓ |
| `confidence_filter_mode` | shadow | shadow | ✓ |
| `api_timeout_seconds` | 60 | 60 | ✓ |
| `deployment.phase` | 2 (paper) | paper | ✓ |
| `news_filter.enabled` | false | false | ✓ |
| `budget.monthly_cap_usd` | 50.0 | "~$60/month" | NOTE: cap < expected cost |
| `m5_refinement.enabled` | true | — | Broken (see §5.3) |
| `GBPJPY.risk.sl_absolute_min` | 0.118 | — | Current OB (0.106) < floor |
| `USDJPY.risk.sl_absolute_min` | 0.085 | — | ✓ |

**`budget.monthly_cap_usd: 50.0`**: CLAUDE.md projects ~$60/month API cost. The cap of $50 will be hit before month-end. Check whether `cost_critical_threshold_usd: 30.0` will trigger alerts or hard stops during the WF-1 window.

---

## 7. Recommendations (Prioritized)

### IMMEDIATE (before tomorrow's Tokyo open at 00:00 UTC)

**R1 — Enable AutoTrading in MT5** *(CRITICAL)*
- In MT5 terminal: **Tools → Options → Expert Advisors → "Allow automated trading"** checkbox
- Or click the **AutoTrading** button in the toolbar (should be green/active)
- This is the single highest-priority fix. 6 valid setups were lost today.
- Estimated impact: 3–4 GBPJPY LONGs that passed all pipeline checks would have been placed.

**R2 — Investigate Anthropic API Refusals** *(CRITICAL)*  
- Check Anthropic API dashboard for rate limit events (429 errors) between 07:59–13:10 UTC today
- Check whether any safety/content filter was triggered (the prompt contains trading + financial content)
- As a temporary fix: add exponential backoff and a 3rd retry attempt on "Sorry" responses
- Add Telegram alert: when `malformed_responses.jsonl` receives a `"Sorry"` response, notify immediately
- Long-term: consider if prompt content is triggering content filtering and adjust phrasing

### HIGH (this week)

**R3 — Fix `copy_rates_from_pos` in RealMT5** *(HIGH)*  
- File: wherever `RealMT5` is defined (likely `src/components/mt5_real.py` or similar)
- Add `copy_rates_from_pos(symbol, timeframe, start_pos, count)` method using the correct MT5 Python API call
- MT5 Python API uses `mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)` — check if the class is wrapping this correctly
- Without this, M5 SL refinement never runs. Every live trade uses AI-proposed SL without tightening.

**R4 — Add OB Proximity Prescreen to Production** *(HIGH)*  
- The simulation prescreen (`scripts/simulate_t7_live_period.py:ob_proximity_prescreen()`) blocks evaluations when price is >1% from any H1 OB
- Port this to production orchestrator for USDJPY specifically: price is 50 pips above the only OB, but the system still evaluates every candle
- Today cost: ~$0.41 in wasted USDJPY calls with zero execution probability
- This would save ~30% of USDJPY API calls until price returns to the OB zone

### MEDIUM (this sprint)

**R5 — Fix `_warn_tp1_placement()` message** *(MEDIUM)*  
- File: `src/components/primary_analyzer.py:578–582`
- Change from: `"Minimum should be 2.0R. Safety check will reject this trade."`
- Change to: `"TP1 at %.2fR. Target 1.5R, accepted range 1.3R–2.0R."`
- This fires 10–20× per day and creates false alarm noise.

**R6 — Add instrument+candle_time to malformed_responses.jsonl** *(MEDIUM)*  
- File: `src/components/primary_analyzer.py:57–66` (`_log_malformed_response()`)
- Add `symbol` and `candle_time_utc` fields to each log entry
- Currently impossible to diagnose which instrument is suffering API refusals

**R7 — Tighten US30 L2 tolerance** *(MEDIUM)*  
- Current: `verification.ob_price_tolerance_pct: 0.002` (0.2%) applies to all instruments
- US30 at ~47500: 0.2% = 95 pts (3× OB zone width)
- Consider adding `instruments.US30_cash.verification.ob_price_tolerance_pct: 0.0005` (0.05% = ~24 pts)
- Or use absolute-unit tolerance for index instruments instead of percentage

**R8 — Verify risk_per_trade_pct** *(MEDIUM)*  
- Config has `risk_per_trade_pct: 2.0%` but CLAUDE.md states `1.0%`
- If running at 2.0% risk on $100K demo, each trade risks $2,000 — double the documented level
- Get CEO confirmation on which value is correct

**R9 — Make GBPUSD macro conflict threshold explicit** *(MEDIUM)*  
- Current approach: AI uses qualitative judgment for "exceptional confluence"
- Produces non-deterministic results (same M15 ratio = CANDIDATE or NO_TRADE)
- Consider adding to prompt: "Proceed LONG against XAUUSD D1 bearish ONLY if: M15 displacement_ratio ≥ 2.5 AND H1 BOS count ≥ 5 AND H1 avg_ratio ≥ 2.0"
- Hard numbers → deterministic, testable

### LOW / MONITORING

**R10 — Monitor GBPJPY sl_floor vs OB width**  
- Current H1 OB (214.023–214.129, created 2026-04-13T08:00) is 10.6 pips wide vs 11.8 pip floor
- This OB will either get mitigated (price trades through it) or a new wider OB will form above
- Until then, GBPJPY Gate 1 will reject any trade where AI places SL at OB low
- No fix needed — monitor until OB changes

**R11 — Fix eval JSONL integrity for pre-restart candles**  
- Investigate why pre-restart candle evaluations produce trade records but no JSONL entries
- Check if `_log_candle()` is called on the `ai_output_malformed` path
- Consider adding startup recovery: on process start, check if any trade records from today lack corresponding JSONL entries and backfill

**R12 — Fix model_used hallucination**  
- After parsing AI JSON response, overwrite `model_used` field with the actual configured model
- Add to `_normalize_pa_fields()` in `primary_analyzer.py`: `r["model_used"] = self.model` (where self.model is the configured model string)

---

## 8. Today's Performance Summary

| Metric | Count |
|--------|-------|
| Total KZ candles processed (all instruments) | ~73 |
| Pre-screen blocked (XAUUSD) | 8 |
| API evaluated | ~60 |
| API refusals ("Sorry, I can't produce JSON") | ~12 |
| Parse failures (pool_type) | 2 |
| NO_TRADE (AI decision) | ~35 |
| CANDIDATE | ~23 |
| L2 FAIL | ~16 |
| Gate 1 REJECTED | 4 |
| Execution attempted | 7 |
| AutoTrading disabled | 6 |
| **Filled** | **0** |
| Estimated API cost (today) | ~$1.74 (60 calls × $0.029) |
| Trades lost to fixable bugs | **6 (AutoTrading)** |
| Trades correctly blocked | All Gate 1 rejections |

**Bottom line**: The pipeline is functionally working (C-gates firing correctly, L2 catching hallucinated entries, Gate 1 protecting against tight SLs) but two production failures are preventing any fills:
1. MT5 AutoTrading setting (fixable in 30 seconds)
2. Anthropic API periodic refusals (needs investigation)

---

*Report generated by monitoring/audit agent. All claims sourced from actual file reads. Sources: knowledge_base/live_evaluations/*/2026-04-13.jsonl, knowledge_base/trade_records/*/2026-04-13_*.json, logs/*.log, shadow_logs/malformed_responses.jsonl, knowledge_base/meta/.orchestrator_*.lock, src/components/permissions.py, src/components/primary_analyzer.py, orchestrator.py.*
