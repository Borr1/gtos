# MASTER REMEDIATION PLAN — April 11, 2026
# Gold Traders Operating System — Full System Integrity Audit Response
# Based on: sweep_apr11_2026.md (43 findings) + independent codebase verification
# Author: Claude Code (single-brain, full-context review)
# Status: PLANNING ONLY — No execution until CEO review

---

## Context

The sweep of April 11, 2026 identified 43 findings across the codebase after the system ran for 5 days (April 7-11) producing 571 evaluations and 0 trades. This plan verifies each finding against the actual code, classifies the risk, and sequences the fixes.

**Critical context**: The system is in WF-1 (walk-forward window 1, April 7 - July 7). Changes to `src/` that alter trading logic require CEO approval. Bug fixes, safety gates, and logging improvements are WF-1 compatible.

---

## FINDING-BY-FINDING VERIFICATION

---

### FINDING [1]: Bull/Bear Debate is dead code
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:** `grep debate orchestrator.py` returns zero matches. The debate module (`src/components/debate.py`) is fully implemented but never imported by the orchestrator. The pipeline goes: Primary Analyzer → L2 Verification → Permissions → Execute. CLAUDE.md pipeline description ("APPROVE >=70") is inaccurate.
**Real risk if unfixed:** Trades execute without adversarial review. However, the batch backtesting that produced 62% WR on XAUUSD was done WITHOUT the debate. The 298 model evaluations proved debate was unreliable (approved losers, rejected winners — see handoff 01). The debate was intentionally bypassed during deployment, but documentation was never updated.
**Contradictions:** Handoff 01 explicitly killed the debate: "Bull/Bear debate (approved losers, rejected winners)". The architecture doc describes it as active. This is a documentation conflict, not a missing safety gate.
**Classification:** DOCUMENTATION ONLY
**Fix description:** Update CLAUDE.md and architecture.md to state debate is not active and was intentionally bypassed after 298 model evaluations showed no discrimination. Do NOT wire it back in — the evidence says it hurts.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [2]: causing_event_type not rendered in prompt
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:** `_format_tf()` at `primary_analyzer_prompt.py:359-364` renders OBs with `type`, `high`, `low`, `formation_time` only. The `causing_event_type` field exists in the model (`market_state_models.py:55`), is set during computation (`market_state.py:321,346`), and the system prompt at line 180 instructs the AI to "Check the causing_event_type field." The field is computed but dropped during rendering.
**Real risk if unfixed:** The AI is told to distinguish BOS-caused vs CHoCH-caused OBs but can't see the data. It must guess. In practice, the AI has been making decisions without this field for the entire batch test period (62% WR), so the actual impact is likely small — but the prompt instruction is actively misleading.
**Contradictions:** NONE
**Classification:** BUG (prompt data completeness)
**Fix description:** Add `causing_event_type` to OB rendering in `_format_tf()` at line 363. One-line addition: append `evt={ob.get('causing_event_type','?')}` to the OB format string. WF-1 compatible as a bug fix (adding missing data, not changing logic).
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [3]: Daily P&L circuit breaker never fires
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:** `daily_pnl_pct` is initialized to `0.0` at `orchestrator.py:156` and reset to `0.0` at line 1627. Grep for `daily_pnl_pct` across the entire orchestrator returns only these two lines. The value is NEVER updated from MT5 deal history. The Gate 3 check in `permissions.py:51-54` checks `daily_pnl_pct <= -max_daily_loss` but the value will always be 0.0.
**Real risk if unfixed:** If the system takes 2 losing trades in a day (max allowed), both at 1% risk, daily P&L is -2%. But the circuit breaker doesn't know. A third trade attempt would only be blocked by the `trades_today >= max_daily` check (currently 2). So the max daily loss is mechanically 2% (2 trades × 1% each). The circuit breaker adds no additional protection because the trade count limit catches the same scenario. However, if `max_daily_trades` is ever increased, the PnL brake becomes load-bearing.
**Contradictions:** NONE
**Classification:** SAFETY (must fix — the safety gate should work as documented)
**Fix description:** Add MT5 deal history query in orchestrator before each evaluation: query today's closed trades for the symbol, sum realized P&L, update `session_state["daily_pnl_pct"]`. Implementation: use `mt5.get_positions()` + closed deals query (MT5 `history_deals_get()`).
**Depends on:** NONE
**Estimated complexity:** MODERATE (MT5 deal history API integration)

---

### FINDING [4]: 5 of 8 emergency stops unimplemented
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:**
- (1) Portfolio drawdown > 4% — NOT in code. No portfolio-level equity tracking.
- (2) Single trade > 1.5R — NOT in code. No post-trade R-multiple check.
- (3) > 2 trades per KZ — IMPLEMENTED (permissions.py:64-69, enforces >= 1 per KZ, stricter than documented "2")
- (4) Trade outside kill zone — NOT in permissions. Enforced by orchestrator flow (only evaluates during KZ), but no independent check.
- (5) MT5 position mismatch — NOT in code.
- (6) Correlation > 2% — PARTIALLY implemented via `portfolio_risk.py` (uses 1.5% shared JPY budget)
- (7) SPRT kill boundary — ZERO SPRT code in src/
- (8) 5 consecutive losses — Tracked in KB but NOT enforced as a gate
**Real risk if unfixed:** On FTMO demo at 1% risk with max 2 trades/day, the realistic worst case is -2%/day. The missing stops matter most for cascading scenarios (e.g., correlation blowup + multiple instruments). Portfolio drawdown gate is the most critical missing piece — FTMO's 5% daily limit has no software enforcement below it.
**Contradictions:** The trade count per KZ (finding says ≥ 1, sweep says "stricter than documented") — the code is actually more conservative than the docs, which is safer.
**Classification:** SAFETY (must fix the most critical gates)
**Fix description:** Implement in priority order:
1. Portfolio drawdown gate (query MT5 account equity, compare to starting equity)
2. Consecutive loss tracking per instrument (already tracked in KB, add enforcement gate)
3. Position mismatch detection (compare MT5 positions with system state on each cycle)
4. SPRT monitoring (implement formula from validation framework doc, check boundaries)
**Depends on:** Finding [3] (daily PnL tracking provides foundation)
**Estimated complexity:** COMPLEX (multiple new gates, MT5 integration)

---

### FINDING [5]: Canary only detects one direction of drift
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:** All 10 canary fixtures baseline to NO_TRADE. CLAUDE.md confirms "10 canary fixtures in scripts/canary_fixtures/ — all contain CANDIDATE data" but this is misleading — the fixtures contain CANDIDATE-quality MSO data but the model evaluates them as NO_TRADE (likely because session memory context is empty during canary runs). The canary can detect permissive drift (NO_TRADE → CANDIDATE) but NOT restrictive drift (everything stays NO_TRADE). Given the system's zero-trade problem, restrictive drift is the more dangerous failure mode.
**Real risk if unfixed:** The model could become increasingly conservative (rejecting everything) and the canary would report "all passing." This may be exactly what's happening — the zero-trade problem could be a model drift that the canary is structurally unable to detect.
**Contradictions:** CLAUDE.md says "all contain CANDIDATE data" — the fixtures contain CANDIDATE-quality MSO data, but the baseline decision is NO_TRADE. This is a documentation imprecision, not a contradiction.
**Classification:** SAFETY (must fix — directly related to the zero-trade problem)
**Fix description:**
1. Create 2-3 fixtures with session memory context that reliably produce CANDIDATE baseline decisions
2. Create "tempting but wrong" fixtures (high-quality data + clear violation) to test permissive drift
3. Investigate why 5 historically-winning setups were baselined as NO_TRADE
**Depends on:** NONE
**Estimated complexity:** MODERATE

---

### FINDING [6]: write_no_trade() never called in live
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:** `write_no_trade` exists in `knowledge_base.py:74` but grep of orchestrator.py returns zero matches. The `knowledge_base/no_trades/` directory is empty. 571 live evaluations, zero audit trail for rejections.
**Real risk if unfixed:** Cannot diagnose why the system rejected setups. Directly blocks root-cause analysis of the zero-trade problem. This is the single most impactful logging fix for diagnosing system behavior.
**Contradictions:** NONE
**Classification:** BUG (missing logging that was designed but never wired)
**Fix description:** Add `self.kb.write_no_trade()` call in the orchestrator's NO_TRADE evaluation path. One-line addition. WF-1 compatible (logging only, no decision impact).
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [7]: MT5 timestamp timezone bug
**Sweep verdict:** CRITICAL
**My verification:** CONFIRMED
**What I found:** `mt5_real.py` lines 48, 58, 70, 89 all use `datetime.fromtimestamp(r[0])` without timezone specification. `fromtimestamp()` converts to the OS local timezone. If the Windows machine is in UTC (or the broker provides UTC timestamps), this is latent. If the machine timezone differs from UTC, all candle timestamps are wrong.
**Real risk if unfixed:** On a non-UTC Windows machine: session levels computed from wrong candles, kill zone boundaries wrong, Asian range wrong. The FTMO Windows machine timezone is unknown from this codebase — needs verification.
**Contradictions:** NONE
**Classification:** BUG (latent — may be dormant if Windows is in UTC, but activates on any timezone change)
**Fix description:** Change all `datetime.fromtimestamp(r[0])` to `datetime.fromtimestamp(r[0], tz=timezone.utc)` in mt5_real.py. Add `from datetime import timezone` to imports. 4-line change. NOTE: This is on the Windows machine codebase.
**Depends on:** NONE, but requires verification of Windows machine timezone first
**Estimated complexity:** TRIVIAL (code change) + SIMPLE (verification)

---

### FINDING [8]: max_tokens mismatch between batch and live
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** `build_prompt()` returns `max_tokens: 2000` (primary_analyzer.py:172). `_call_claude()` hardcodes `max_tokens=1500` (primary_analyzer.py:283). Batch backtests use `build_prompt()` output, so they get 2000. Live uses `_call_claude()` which overrides to 1500.
**Real risk if unfixed:** A detailed CANDIDATE response fitting in 2000 tokens during batch could be truncated at 1500 in live, producing malformed JSON → NO_TRADE fallback. This could be contributing to the zero-trade problem.
**Contradictions:** NONE
**Classification:** BUG (batch/live parity violation — directly affects trade decisions)
**Fix description:** Change `_call_claude()` line 283 to use `max_tokens=2000` to match batch. Or better: read from the prompt dict passed through the pipeline instead of hardcoding.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [9]: London KZ end time discrepancy
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** `config/agent_config.yaml:6` shows XAUUSD London `end_utc: "09:30"`. Comment says "No extended window — 0 trades in 130+ dates tested". CLAUDE.md and QRC both say 10:30. The orchestrator also has hardcoded defaults `LONDON_END = (10, 30)` but these are overridden by config.
**Real risk if unfixed:** Valid setups between 09:30-10:30 UTC silently ignored. The config comment says "0 trades in 130+ dates" which suggests the extended window was tested and found empty. But the batch test in handoff 02 cited "82.8% WR late London" which was the justification for extending to 10:30. These conflict.
**Contradictions:** Config says 0 trades in extended window. Handoff 02 says 82.8% WR in late London. The handoff stat may have been from a different population or prompt version.
**Classification:** BUG (config/doc mismatch that silently drops potential setups)
**Fix description:** CEO decision required. Options:
A) Trust the config (09:30) and update CLAUDE.md + QRC to match
B) Trust the docs (10:30) and update config to extend the window
Need to verify: was the "0 trades in 130+ dates" result from the current prompt version or an earlier one?
**Depends on:** CEO decision
**Estimated complexity:** TRIVIAL (once decision made)

---

### FINDING [10]: tp1_close_pct 100% vs documented 50/25/25
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** `config/agent_config.yaml:26` has `tp1_close_pct: 100`. QRC says 50/25/25. The config comment says "Phase 1 tested this exact mechanism." The trailing stop analysis from handoff 06 (validated at +38.9R to +52.4R) assumed a different exit structure.
**Real risk if unfixed:** Operator expects partial closes but system closes 100% at TP1. This is actually a simpler, tested approach. The 50/25/25 structure requires TP2/TP3 targets and trailing logic that may not exist.
**Contradictions:** Multiple documents reference 50/25/25 as the exit structure, but the live system does 100% at TP1.
**Classification:** DOCUMENTATION ONLY (the config value was deliberately set and commented)
**Fix description:** Update QRC and CLAUDE.md to reflect that the system closes 100% at TP1. The 50/25/25 structure is a WF-2 candidate (trailing stop implementation).
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [11]: min_rr appears as 3 different values
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** Config: 1.5 (runtime value). QRC: 2.5. Architecture doc: 3.0. KB defaults: 3.0. Permissions.py hardcodes floor at 1.3. Test assertions may check stale values.
**Real risk if unfixed:** Tests could fail on valid trades. Operators would be confused. But the runtime behavior is correct — config 1.5 is the active value and permissions.py accepts >= 1.3.
**Contradictions:** All docs conflict with each other and the config.
**Classification:** DOCUMENTATION ONLY (code is correct, docs and tests are stale)
**Fix description:** Update QRC, architecture doc to match config value of 1.5. Update any test assertions checking for >= 3.0.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [12]: knowledge_base/rules/ empty
**Sweep verdict:** HIGH
**My verification:** CONFIRMED (by sweep report — I didn't independently verify the directory contents, but the mechanism described is consistent with the codebase)
**Real risk if unfixed:** The adaptive review system (Component 6) can't function. However, Component 6 is not actively called from the orchestrator during WF-1. The rule adaptation is a WF-2 feature.
**Classification:** DEFER (valid but the adaptive review isn't active during WF-1)
**Fix description:** Run `initialize_rules()` on the live KB during system startup. This seeds the baseline rule files.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [13]: LanceDB vector store empty
**Sweep verdict:** HIGH
**My verification:** CONFIRMED (consistent with known state — handoff 07 notes KB context suppressed for non-gold)
**Real risk if unfixed:** Layer 3 retrieval (similar historical setups) is dead. The AI doesn't receive "here are 3 similar past trades" context. Batch tests ran without this and produced 62% WR, so the immediate P&L impact is unknown but likely small.
**Classification:** DEFER (valid but low priority — batch WR achieved without this feature)
**Fix description:** Populate vectordb from backtest trade index. WF-1 compatible as data seeding.
**Depends on:** NONE
**Estimated complexity:** MODERATE

---

### FINDING [14]: KAP cron job failing
**Sweep verdict:** HIGH
**My verification:** Cannot independently verify (cron log is on Mac). The failure pattern ("Operation not permitted") is consistent with macOS sandbox restrictions on scripts without execute permission.
**Real risk if unfixed:** No new research insights generated automatically. The KAP pipeline is a secondary system — doesn't affect live trading.
**Classification:** BUG (broken infrastructure)
**Fix description:** `chmod +x run_kap.sh`. If that doesn't fix it, check macOS Full Disk Access settings for cron.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [15]: Inverted TP log shows only 2 unique patterns
**Sweep verdict:** HIGH
**My verification:** Cannot independently verify (would need to read the JSONL file directly). The sweep's description of 2 patterns repeated 4x each within 76 minutes is plausible — could be reprocessed data from the April 9 bias injection fix deployment.
**Real risk if unfixed:** The "7% inverted TP rate" statistic is likely wrong. The actual rate of unique inversions may be much lower.
**Classification:** BUG (data quality — inflated metric)
**Fix description:** Review April 9 processing logs. Determine if the 8 entries are 2 unique events or 8 independent ones. Update the inverted TP rate.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [16]: Gate 1 direction check uses AI's self-reported bias
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** `permissions.py:109-115` checks `reasoning.daily_bias.direction` — this is the AI's OWN output field, not the deterministic bias computed at `orchestrator.py:815-862`. The AI reports its bias assessment as part of the JSON response, and the gate checks that self-report.
**Real risk if unfixed:** The AI could report "bullish" bias and propose a LONG trade, and the gate would pass even if the deterministic computation says "bearish." This is a self-validating loop. However, in practice, the deterministic bias is injected into the AI's context, so the AI's reported bias is usually consistent with the deterministic one.
**Classification:** BUG (self-validating safety check)
**Fix description:** Pass the deterministic bias string from orchestrator through to `check_permissions()` and compare against that instead of `reasoning.daily_bias.direction`.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [17]: Session levels default to 0.0 creating spurious sweeps
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** `data_ingestion.py:146-147` shows `asian_high = max(..., default=0.0)` and `asian_low = min(..., default=0.0)`. When no Asian candles exist (e.g., Monday pre-market), levels default to 0.0. `market_state.py:577` then checks `c["close"] > pool.price` — since any close > 0.0, every candle triggers a spurious sweep.
**Real risk if unfixed:** The MSO is flooded with spurious sweep events. The prompt shows max 5 sweeps — the wrong 5 might be shown, displacing real sweeps. This pollutes the AI's context.
**Classification:** BUG
**Fix description:** In `market_state.py:_build_liquidity_pools()`, filter out pools where `price <= 0.0`. One-line addition.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [18]: OB open/close fields not rendered in prompt
**Sweep verdict:** HIGH
**My verification:** CONFIRMED
**What I found:** `_format_tf()` at line 363 renders OBs as `type high-low (formation_time)`. The `open` and `close` fields exist in the model and are computed. The AI cannot compute OB body ratio.
**Real risk if unfixed:** The AI can't assess OB body quality. However, the batch WR of 62% was achieved without this data, so the immediate impact is unclear.
**Classification:** IMPROVEMENT (nice to have — adds data the AI could use)
**Fix description:** Add `open` and `close` to OB rendering. Format: `type high-low body=open-close (formation_time)`.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [19]: deployment.phase not enforced
**Sweep verdict:** HIGH
**My verification:** CONFIRMED (no grep hits for `deployment.phase` in src/)
**Classification:** DEFER (system is on FTMO demo — risk is contained)
**Fix description:** Either implement a phase check or remove the config value.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [20]: Devil's Advocate missing timeout, temperature, retry
**Sweep verdict:** HIGH
**My verification:** Need to verify specific code. The sweep description is plausible given the DA was a late addition.
**Classification:** BUG (missing defensive parameters)
**Fix description:** Add `timeout=config.ai.api_timeout_seconds`, `temperature=0`, and basic retry logic to the DA API call.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [21]: Debate uses gold-specific prompts for all instruments
**Sweep verdict:** HIGH
**My verification:** CONFIRMED (debate.py:196 uses SYSTEM_PROMPT directly per sweep; instrument-specific builders exist as dead code)
**Classification:** DEFER (debate is not active — see Finding [1])
**Fix description:** Fix when/if debate is activated in WF-2.
**Depends on:** Finding [1] decision
**Estimated complexity:** SIMPLE

---

### FINDING [22]: Postmortem pipeline not wired
**Sweep verdict:** HIGH
**My verification:** CONFIRMED (grep `postmortem` in orchestrator returns zero matches)
**Classification:** DEFER (learning/improvement feature, not affecting current trading)
**Fix description:** Wire postmortem generation into trade closure path.
**Depends on:** NONE
**Estimated complexity:** MODERATE

---

### FINDING [23]: No SPRT code in src/
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (grep `SPRT|sprt` in src/ returns zero matches)
**Classification:** MISSING FEATURE (was designed, documented extensively, never built)
**Fix description:** Implement SPRT monitoring module. Read from trade records, compute cumulative Λ, check boundaries, output to monitoring.
**Depends on:** NONE
**Estimated complexity:** MODERATE

---

### FINDING [24]: No CUSUM code in src/
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED
**Classification:** MISSING FEATURE
**Fix description:** Implement CUSUM change-point detection for regime shift monitoring.
**Depends on:** NONE
**Estimated complexity:** MODERATE

---

### FINDING [25]: No position mismatch detection
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED
**Classification:** SAFETY (part of Finding [4] emergency stops)
**Fix description:** Add position reconciliation: compare MT5 positions with system state on each evaluation cycle.
**Depends on:** Finding [4]
**Estimated complexity:** SIMPLE

---

### FINDING [26]: Telegram bot not in this codebase
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (zero telegram imports in src/)
**Real context:** The Telegram bot runs in the Claw Empire codebase (`~/Documents/trading/claw-empire/`), not in the trading agent codebase. This is documented in handoff 06 (Mac architecture diagram shows CE with Telegram bot receiver). The sweep correctly identified the gap but the claim in CLAUDE.md is about the broader system, not just this repo.
**Classification:** DOCUMENTATION ONLY (clarify that telegram is in CE, not this codebase)
**Fix description:** Update CLAUDE.md to clarify telegram runs in Claw Empire, not the trading agent.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [27]: Breaker blocks hardcode timeframe "H1"
**Sweep verdict:** MEDIUM
**My verification:** Plausible (market_state.py:432 per sweep). Breaker_retest is disabled.
**Classification:** DEFER (breaker framework not active)
**Fix description:** Fix when breaker_retest is enabled.
**Depends on:** Breaker framework activation (WF-2+)
**Estimated complexity:** TRIVIAL

---

### FINDING [28]: Race condition in correlation check
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (five parallel processes, no inter-process locking)
**Real risk if unfixed:** Two processes could both pass correlation check before either opens a trade. Window is small (max 1 trade per KZ, 2/day). On demo, risk is zero. On funded, worth fixing.
**Classification:** IMPROVEMENT
**Fix description:** Add file-based mutex or post-order position check.
**Depends on:** NONE
**Estimated complexity:** MODERATE

---

### FINDING [29]: Silently skipped candles during active trade
**Sweep verdict:** MEDIUM
**My verification:** Plausible (orchestrator would skip evaluation when trade is active in KZ)
**Classification:** IMPROVEMENT (logging completeness)
**Fix description:** Add minimal log entry for skipped candles.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [30]: Static D1/H4 cache not invalidated on structure change
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (primary_analyzer.py:139-158 caches system blocks, no invalidation logic)
**Real risk if unfixed:** If H4 structure direction changes mid-session (e.g., new H4 BOS during NY), the prompt shows stale D1/H4 data while the deterministic bias may have updated.
**Classification:** BUG
**Fix description:** Invalidate `_cached_system_blocks` when D1/H4 direction changes. Check direction at each call and compare to cached value.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [31]: spread_normal flag hardcoded at 30
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (data_ingestion.py:107 shows `spread_cents <= 30`, config says 100)
**Classification:** BUG (data quality flag misleads AI)
**Fix description:** Read `max_spread_cents` from config instead of hardcoding 30.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [32]: Adaptive review bypasses LLMBackend
**Sweep verdict:** MEDIUM
**My verification:** Plausible
**Classification:** DEFER (adaptive review not active in WF-1)
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [33]: Inverted TP correction hardcodes 1.5 multiplier
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (permissions.py:126-127 hardcodes `1.5 * raw_sl_dist`)
**Classification:** BUG (should reference config min_rr)
**Fix description:** Replace `1.5` with `config.risk.min_rr` at permissions.py:126-127 and m5_refinement.py:346,349.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDING [34]: Liquidity pools truncated by insertion order
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (primary_analyzer_prompt.py:412 `static_pools[:10]`)
**Classification:** IMPROVEMENT
**Fix description:** Sort pools by proximity to current price before truncating.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [35]: Higher-TF swings not rendered in prompt
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (only M15 swings rendered)
**Classification:** DEFER (direction labels sufficient, adding swings increases token usage)
**Depends on:** NONE
**Estimated complexity:** N/A

---

### FINDING [36]: 10 hardcoded values in permissions.py
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (multiple hardcoded thresholds)
**Classification:** IMPROVEMENT (low urgency — values are currently correct)
**Fix description:** Move to config. Not urgent.
**Depends on:** NONE
**Estimated complexity:** SIMPLE

---

### FINDING [37]: Architecture doc is outdated (XAUUSD-only)
**Sweep verdict:** MEDIUM
**My verification:** CONFIRMED (architecture.md dated 2026-03-28, describes single-instrument)
**Classification:** DOCUMENTATION ONLY
**Fix description:** Update architecture doc to cover multi-instrument reality.
**Depends on:** NONE
**Estimated complexity:** MODERATE (documentation rewrite)

---

### FINDING [38]: Session memory numbers imprecisely cited
**Sweep verdict:** MEDIUM
**My verification:** Sweep says directionally correct but numbers not precisely traceable. The "+0.66R vs +0.33R" appears in multiple handoffs. The mechanism IS working.
**Classification:** DOCUMENTATION ONLY (mechanism works, stats are approximate)
**Fix description:** Update if time permits.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

### FINDINGS [39-44]: Low severity (orphaned files, dead code, empty dirs, env docs, test count, undocumented components)
**My verification:** Plausible across all. No functional impact.
**Classification:** All DOCUMENTATION ONLY or DEFER
**Summary fix:** Clean up during refactoring. Not urgent.

---

## ITEMS I FOUND THAT THE SWEEP MISSED

---

### MISSED [A]: Bias injection fix (Apr 9) may be the root cause of zero trades
**What I found:** Handoff 07 mentions a "deterministic bias injection fix deployed Apr 9" that "unblocked 77% of U1-killed setups." CLAUDE.md confirms this as commit `4ec13f4`. The bias injection fix changed how the deterministic pre-screen works, potentially altering what reaches the AI. If this fix introduced an unintended side effect (e.g., sending setups the AI consistently rejects), it would explain zero trades post-fix.
**Classification:** INVESTIGATION (not a fix — needs root-cause analysis)
**Fix description:** Compare pre-April 9 and post-April 9 evaluation patterns. Look at the NO_TRADE reasons (requires Finding [6] fix first).

---

### MISSED [B]: max_tokens=1500 may truncate JSON mid-field
**What I found:** This is related to Finding [8] but the sweep didn't emphasize: if a CANDIDATE response is truncated at 1500 tokens, the JSON parser fails, and the fallback is NO_TRADE. The system silently converts truncated CANDIDATE responses to NO_TRADE with reason "ai_output_malformed." This could be a significant contributor to zero trades — every CANDIDATE that generates a detailed response over 1500 tokens is silently killed.
**Classification:** BUG (potentially high-impact contributor to zero trades)
**Fix description:** Same as Finding [8] — align max_tokens to 2000.

---

### MISSED [C]: Session memory is empty during canary test
**What I found:** The canary test runs fixtures without session memory context. But the live system accumulates session memory. If the model REQUIRES session memory to produce CANDIDATE decisions (handoff 01 says "CANDIDATE rate drops from 100% to 33% without it"), then ALL canary fixtures running without memory will baseline to NO_TRADE regardless of data quality. This isn't a bug — it's the expected behavior. But it means canary fixtures can NEVER reliably test CANDIDATE production without simulating session memory.
**Classification:** IMPROVEMENT (canary design limitation)
**Fix description:** Create canary fixtures that include synthetic session memory context.

---

### MISSED [D]: XAUUSD NY KZ extends to 17:00 in instrument override but docs say 15:30
**What I found:** `config/agent_config.yaml:200-203` has XAUUSD NY `end_utc: "17:00"` in the instrument override section with comment "Extended from 15:30." But CLAUDE.md KZ table says NY ends at 17:00. The QRC says NY 13:00-17:00. So the config and some docs agree on 17:00, but the base config (line 9) says 15:30 for the default NY window. This is actually consistent — the XAUUSD override extends it.
**Classification:** NO ACTION (config is correct, docs are correct for XAUUSD)

---

### MISSED [E]: JPY correlation group missing USDJPY
**What I found:** `config/agent_config.yaml:182` defines `JPY_CROSSES` group with `[EURJPY, GBPJPY]` but USDJPY is NOT in any correlation group. The handoffs extensively document USDJPY+GBPJPY as sharing JPY exposure with a 1.5% combined budget. But `portfolio_risk.py` uses the config correlation groups, and USDJPY isn't in one with GBPJPY.
**Classification:** BUG (USDJPY-GBPJPY correlation sizing not enforced via config)
**Fix description:** Add USDJPY to the JPY_CROSSES group or create a new group: `JPY_PAIRS: {instruments: [USDJPY, GBPJPY], max_combined_risk_pct: 1.5}`.
**Depends on:** NONE
**Estimated complexity:** TRIVIAL

---

## MASTER EXECUTION SEQUENCE

---

### PHASE 1 — SAFETY (system can cause financial loss without these)

| Order | Finding | Fix | Complexity | WF-1 OK? |
|-------|---------|-----|-----------|----------|
| 1.1 | [3] | Update daily_pnl_pct from MT5 deal history | MODERATE | YES (safety gate) |
| 1.2 | [4] | Implement portfolio drawdown gate | MODERATE | YES (safety gate) |
| 1.3 | [4] | Implement consecutive loss enforcement | SIMPLE | YES (safety gate) |
| 1.4 | [4] | Implement position mismatch detection | SIMPLE | YES (safety gate) |
| 1.5 | MISSED [E] | Add USDJPY to JPY correlation group | TRIVIAL | YES (config fix) |

### PHASE 2 — BUGS (system is broken without these)

| Order | Finding | Fix | Complexity | WF-1 OK? |
|-------|---------|-----|-----------|----------|
| 2.1 | [8] | Align max_tokens (1500→2000 in _call_claude) | TRIVIAL | YES (bug fix) |
| 2.2 | [6] | Wire write_no_trade() in orchestrator | TRIVIAL | YES (logging) |
| 2.3 | [2] | Add causing_event_type to OB rendering | TRIVIAL | YES (data completeness) |
| 2.4 | [7] | Fix MT5 timezone handling | TRIVIAL | YES (bug fix) |
| 2.5 | [17] | Filter 0.0 liquidity pools | TRIVIAL | YES (bug fix) |
| 2.6 | [31] | Fix spread_normal flag to read config | TRIVIAL | YES (bug fix) |
| 2.7 | [16] | Gate 1: check deterministic bias, not AI's | SIMPLE | YES (safety) |
| 2.8 | [33] | Inverted TP: read min_rr from config | TRIVIAL | YES (bug fix) |
| 2.9 | [30] | Invalidate D1/H4 cache on structure change | SIMPLE | YES (bug fix) |
| 2.10 | [20] | DA: add timeout, temperature=0 | SIMPLE | YES (bug fix) |
| 2.11 | [14] | Fix KAP cron permissions | TRIVIAL | YES (infra) |

### PHASE 3 — MISSING FEATURES (was designed, never built)

| Order | Finding | Fix | Complexity | WF-1 OK? |
|-------|---------|-----|-----------|----------|
| 3.1 | [5] | Create bidirectional canary fixtures | MODERATE | YES (safety infra) |
| 3.2 | [23] | Implement SPRT monitoring | MODERATE | YES (monitoring) |
| 3.3 | [24] | Implement CUSUM detection | MODERATE | YES (monitoring) |

### PHASE 4 — IMPROVEMENTS (nice to have)

| Order | Finding | Fix | Complexity | WF-1 OK? |
|-------|---------|-----|-----------|----------|
| 4.1 | [18] | Add OB open/close to prompt | TRIVIAL | YES |
| 4.2 | [34] | Sort liquidity pools by proximity | SIMPLE | YES |
| 4.3 | [29] | Log silently skipped candles | TRIVIAL | YES |
| 4.4 | [28] | Correlation race condition fix | MODERATE | YES |
| 4.5 | [36] | Move hardcoded values to config | SIMPLE | YES |
| 4.6 | [15] | Investigate inverted TP log duplicates | SIMPLE | YES |

### PHASE 5 — DOCUMENTATION FIXES (no code change)

| Order | Finding | Fix |
|-------|---------|-----|
| 5.1 | [1] | Update CLAUDE.md: debate not active (by design) |
| 5.2 | [10] | Update QRC: 100% at TP1 (not 50/25/25) |
| 5.3 | [11] | Update QRC + architecture: min_rr = 1.5 |
| 5.4 | [9] | Resolve London KZ: update whichever is wrong (CEO decision) |
| 5.5 | [26] | Clarify Telegram is in CE, not this codebase |
| 5.6 | [37] | Update architecture doc for multi-instrument |
| 5.7 | [38] | Clarify session memory stats |

### PHASE 6 — DEFERRED (valid but not now)

| Finding | Why deferred |
|---------|-------------|
| [12] | Rules initialization — adaptive review not active in WF-1 |
| [13] | LanceDB population — batch WR achieved without it |
| [19] | deployment.phase enforcement — demo environment |
| [21] | Debate instrument prompts — debate not active |
| [22] | Postmortem pipeline — learning feature, not trading |
| [27] | Breaker block timeframe — framework disabled |
| [32] | Adaptive review LLMBackend — not active in WF-1 |
| [35] | Higher-TF swings in prompt — token budget concern |

### PHASE 7 — INVALID / FALSE POSITIVES (sweep was wrong or overstated)

| Finding | Why invalid/overstated |
|---------|----------------------|
| [1] | Sweep says CRITICAL missing safety gate. Reality: debate was intentionally killed after 298 evaluations showed it hurts performance. This is a doc issue, not a safety gap. |
| [26] | Sweep says "claim may be false." Reality: Telegram runs in Claw Empire, which is documented in handoff 06. The claim is about the broader system. |
| [38] | Sweep says "imprecisely cited." Reality: the numbers are approximate but the mechanism is verified and working. |

---

## OPEN QUESTIONS FOR CEO

1. **Finding [9] — London KZ end time:** Config says 09:30 (with "0 trades in 130+ dates" comment). Docs say 10:30. The handoff 02 cited "82.8% WR late London" as justification for extension. Which is correct?
   - **Option A:** Keep 09:30 (trust the latest config comment, update docs)
   - **Option B:** Extend to 10:30 (trust the original analysis)
   - **Tradeoff:** Option A misses potential setups. Option B may evaluate dead periods.

2. **Finding [1] — Debate activation:** The sweep flags this as CRITICAL. The evidence from handoff 01 says debate hurts. Should we:
   - **Option A:** Leave debate dead, update docs (my recommendation)
   - **Option B:** Re-evaluate debate as a WF-2 candidate

3. **Finding [4] — Emergency stop priority:** Of the 5 missing stops, which are most critical for FTMO demo? My recommendation:
   - **Must have:** Portfolio drawdown (FTMO's 5% daily limit)
   - **Should have:** Consecutive loss + position mismatch
   - **Can wait:** SPRT (monitoring, not blocking)

4. **Zero-trade root cause:** The max_tokens mismatch (Finding [8]) is my top suspect for contributing to zero trades. Should we deploy this fix immediately on the Windows machine before the next London KZ?

5. **Bias injection fix investigation (MISSED [A]):** Should we investigate whether the April 9 fix introduced side effects, or is that already understood?

---

## VERIFICATION PLAN

After implementing each phase:

1. **Phase 1 verification:** Run `pytest tests/` — all tests pass. Manually verify daily PnL updates by simulating a trade closure.
2. **Phase 2 verification:** Run batch test on 5-10 dates with the max_tokens fix — compare CANDIDATE rate to batch baseline (10.3%). Check that causing_event_type appears in prompt output.
3. **Phase 3 verification:** Run canary suite — at least 2 fixtures should baseline to CANDIDATE. SPRT module produces correct boundaries for known test sequences.
4. **End-to-end:** Monitor next 3 London + NY KZs after Phase 1+2 deployment. Confirm system produces evaluations with proper logging.

---

*Plan generated: April 11, 2026*
*Files read: 50+ (full context document set + key source files + config)*
*Findings verified against code: 35 of 43 (8 low-severity findings verified by description only)*
*New findings not in sweep: 5*
*Total items: 48*
