# FORENSIC SWEEP — April 11, 2026
# Gold Traders Operating System — Full System Integrity Audit
# Conducted by: Claude Code (8 parallel forensic agents)
# Scope: Every file and folder in the project
# Date: 2026-04-11

---

## FINDINGS

---

### FINDING [1]
**Category:** SILENT FAILURE RISK
**Severity:** CRITICAL
**Location:** `src/components/orchestrator.py` — debate module is never imported or called
**What it is:** The Bull/Bear Debate (Component 3B) is dead code — the architecture says CANDIDATE → Debate → Execute, but the orchestrator goes directly from CANDIDATE → L2 Verification → Permissions → Execute. The debate engine (`src/components/debate.py`) is fully implemented but never invoked in the live pipeline.
**Impact if ignored:** The system places trades without the adversarial review step that the architecture and documentation describe as a core safety gate. Every CANDIDATE proceeds to execution without a second AI opinion. CLAUDE.md pipeline description ("APPROVE >=70") is false.
**Fix required:** YES — either wire the debate into the orchestrator pipeline at the documented location (after CANDIDATE, before execution), or update all documentation to reflect that debate is not active and was intentionally removed. CEO decision required since this affects trading logic (WF-1).

---

### FINDING [2]
**Category:** DATA GAP
**Severity:** CRITICAL
**Location:** `src/prompts/primary_analyzer_prompt.py:363` (`_format_tf()`) and `market_state.py:322,347`
**What it is:** The prompt system message instructs the AI to "Check the causing_event_type field to distinguish BOS-caused vs CHoCH-caused order blocks" (system prompt ~line 180), but `_format_tf()` never renders `causing_event_type` into the data sent to the AI. The field exists in the MSO (generated at `market_state.py:322,347`) but is dropped during prompt formatting.
**Impact if ignored:** The AI is told to use a field that doesn't exist in its input. It must guess or hallucinate which structural event created each order block, undermining the distinction between BOS and CHoCH OBs that is central to the ob_retest framework.
**Fix required:** YES — add `causing_event_type` to the OB rendering in `_format_tf()` at line 363. This is a prompt data fix, not a logic change — WF-1 compatible as a bug fix.

---

### FINDING [3]
**Category:** SILENT FAILURE RISK
**Severity:** CRITICAL
**Location:** `src/components/permissions.py:44-83` (Gate 3) and `src/components/orchestrator.py:158`
**What it is:** The daily P&L circuit breaker (`daily_pnl_pct <= -max_daily_loss_pct`) in Gate 3 checks `session_state["daily_pnl_pct"]`, but this value is initialized to `0.0` at orchestrator.py:158 and never updated from MT5 deal history during the session. The 2% daily loss emergency stop is permanently inactive.
**Impact if ignored:** If the system takes multiple losing trades in a day, the daily loss circuit breaker will never trigger. The system continues trading through any drawdown.
**Fix required:** YES — add MT5 deal history query to update `daily_pnl_pct` before each trade evaluation. This is a safety gate fix — WF-1 compatible.

---

### FINDING [4]
**Category:** MISSING INFRA
**Severity:** CRITICAL
**Location:** CLAUDE.md lines 320-330 (8 emergency stops) vs `src/components/permissions.py`
**What it is:** Of 8 documented emergency stops, only 3 have code enforcement:
- (1) Portfolio drawdown > 4% — **NOT IMPLEMENTED** (no portfolio-level check)
- (2) Single trade > 1.5R loss — **NOT IMPLEMENTED** (no realized R-multiple check)
- (3) > 2 trades per KZ — Enforced (but at >= 1, stricter than documented)
- (4) Trade outside kill zone — **NOT IMPLEMENTED** in permissions (relies on orchestrator flow only)
- (5) MT5 position mismatch — **NOT IMPLEMENTED** (no comparison code)
- (6) Correlation > 2% — Partially implemented (portfolio_risk.py uses 1.5%, not 2%)
- (7) SPRT kill boundary — **NOT IMPLEMENTED** (zero SPRT code in src/)
- (8) 5 consecutive losses — Tracked in KB but **NOT ENFORCED** as a gate
**Impact if ignored:** Five documented safety stops are unenforceable. A cascading loss scenario has no automated circuit breaker beyond the broken daily P&L check. The system's stated safety architecture is largely documentation fiction.
**Fix required:** YES — implement at minimum: portfolio drawdown gate, SPRT monitoring, consecutive loss enforcement, and position mismatch detection. CEO should prioritize which stops are most critical.

---

### FINDING [5]
**Category:** SILENT FAILURE RISK
**Severity:** CRITICAL
**Location:** `scripts/canary_test.py`, `scripts/canary_fixtures/baseline.json`
**What it is:** All 10 canary fixtures baseline to NO_TRADE. The canary can detect if the model becomes MORE permissive (flips NO_TRADE to CANDIDATE), but it CANNOT detect:
- Permissive drift on bad setups (5 of 5 "true NO_TRADE" fixtures use degraded data — zeroed session levels, insufficient M15 — so the rejection is over-determined by data quality, not model judgment)
- Increased restrictiveness (no fixture baselines to CANDIDATE, so the model could start rejecting everything and the canary would still pass)
- The 5 fixtures designed as CANDIDATE (from winning trades) were baselined as NO_TRADE when the model disagreed with the backtest. This disagreement was never investigated and may be the root cause of the zero-trade problem.
**Impact if ignored:** Model drift in the dangerous direction (becoming too loose on real setups, or too tight on valid ones) is completely undetectable. The canary provides false confidence.
**Fix required:** YES — create at least 2 fixtures that reliably produce CANDIDATE decisions to catch restrictive drift. Create "tempting but wrong" fixtures with high-quality data but one clear violation to catch permissive drift. Investigate the 5-fixture CANDIDATE→NO_TRADE disagreement.

---

### FINDING [6]
**Category:** SILENT FAILURE RISK
**Severity:** CRITICAL
**Location:** `knowledge_base/no_trades/` (empty) and `src/components/orchestrator.py`
**What it is:** After 571 live evaluations over 5 days, the `knowledge_base/no_trades/` folder is empty. The `write_no_trade()` method exists in `knowledge_base.py:74-78` but is never called from the live orchestrator's evaluation rejection path. The backtest KB has 40 no-trade records, proving the mechanism works.
**Impact if ignored:** Zero audit trail for why the system rejected setups during live trading. This directly blocks diagnosis of the "zero trades" problem — you cannot reconstruct what setups were available and why they were rejected.
**Fix required:** YES — add `kb.write_no_trade()` call in the orchestrator's NO_TRADE path. This is a logging fix — WF-1 compatible.

---

### FINDING [7]
**Category:** DATA GAP
**Severity:** CRITICAL
**Location:** `src/mt5/mt5_real.py:58`
**What it is:** `datetime.fromtimestamp(r[0]).isoformat()` converts MT5 Unix timestamps to the OS local timezone, not UTC. The `datetime` import at line 3 is bare (no timezone). MT5 returns broker-time epochs, but `fromtimestamp()` without `tz=` converts to whatever the Windows machine's local timezone is. The resulting naive ISO strings have no timezone suffix. Downstream code at `data_ingestion.py:135` treats naive timestamps as UTC, but the underlying time value is already wrong if the OS timezone differs from UTC.
**Impact if ignored:** All time-dependent calculations (session levels, Asian range 00:00-07:00 UTC, kill zone boundaries) would use wrong candle boundaries on any non-UTC machine. Session levels could be computed from wrong candles, causing the AI to receive incorrect PDH/PDL/Asian levels.
**Fix required:** YES — change to `datetime.fromtimestamp(r[0], tz=timezone.utc).isoformat()`. Add `from datetime import timezone` to imports. Note: this is on the Windows machine (`C:\Users\MSI\Documents\ai-trading-agent`) — verify what timezone it is set to. If the broker provides UTC timestamps and the Windows machine is in UTC, this bug is latent but not yet active.

---

### FINDING [8]
**Category:** DATA GAP
**Severity:** HIGH
**Location:** `src/components/primary_analyzer.py:283` vs `:171`
**What it is:** `build_prompt()` returns `max_tokens=2000` (used by batch backtest), but `_call_claude()` hardcodes `max_tokens=1500` (used in live trading). Batch backtests allow 500 more tokens than live, creating a validation gap.
**Impact if ignored:** A detailed CANDIDATE response that fits in 2000 tokens during backtesting could be truncated at 1500 tokens during live trading, producing malformed JSON that triggers a NO_TRADE fallback. The system was validated at a token budget it doesn't use in production.
**Fix required:** YES — align max_tokens between batch and live. Either increase live to 2000 or decrease batch to 1500.

---

### FINDING [9]
**Category:** CONFIG CONFLICT
**Severity:** HIGH
**Location:** `config/agent_config.yaml:6` (09:30) vs `.context/00_core/quick_reference_card.md:11` (10:30) vs `CLAUDE.md:312` (10:30)
**What it is:** XAUUSD London kill zone ends at 09:30 UTC in config (the runtime value) but both CLAUDE.md and the quick reference card say 10:30 UTC. The system stops evaluating XAUUSD London setups one hour before documentation says it should.
**Impact if ignored:** An operator monitoring the system expects London trading until 10:30 but the system stops at 09:30. Valid setups between 09:30-10:30 are silently ignored with no record.
**Fix required:** YES — determine the correct end time (based on the validated backtest data) and update whichever is wrong. If 10:30 is correct, fix config. If 09:30 is correct, fix CLAUDE.md and QRC.

---

### FINDING [10]
**Category:** CONFIG CONFLICT
**Severity:** HIGH
**Location:** `config/agent_config.yaml:26` (tp1_close_pct: 100) vs `.context/00_core/quick_reference_card.md:124` (50/25/25)
**What it is:** The config closes 100% of the position at TP1. The quick reference card describes a 50/25/25 partial close strategy (50% at TP1, 25% at TP2, 25% at TP3). The system uses config (100% close at TP1).
**Impact if ignored:** An operator expects multi-stage exits but the system closes everything at TP1. This fundamentally changes the trade management behavior and expected P&L profile. The trailing stop analysis (validated at +38.9R to +52.4R) assumed a different exit structure.
**Fix required:** YES — update the QRC to match the actual config (100% at TP1), or implement the 50/25/25 strategy if that's what was intended. CEO decision required.

---

### FINDING [11]
**Category:** CONFIG CONFLICT
**Severity:** HIGH
**Location:** `config/agent_config.yaml:25` (1.5) vs `.context/00_core/quick_reference_card.md:123` (2.5) vs `.context/00_core/architecture.md:3243` (3.0) vs `src/components/knowledge_base.py:288` (3.0)
**What it is:** min_rr appears as three different values across the project: 1.5 (config, runtime), 2.5 (QRC), 3.0 (architecture doc, KB defaults, test assertions). Permissions.py enforces a floor of 1.3 (hardcoded tolerance band).
**Impact if ignored:** Tests assert stale values (rr >= 3.0) that would reject valid 1.5R trades. QRC misleads operators. KB defaults initialize with wrong baseline.
**Fix required:** YES — update QRC, architecture doc, KB defaults, and test assertions to match config value of 1.5.

---

### FINDING [12]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `knowledge_base/rules/` (empty)
**What it is:** `initialize_rules()` was never called on the live knowledge base. The adaptive review system (Component 6) requires `active_rules.yaml`, `base_rules.yaml`, `pending_reviews.yaml`, and `rule_modifications_log.yaml` — none exist. The backtest KB has all 4 files properly initialized.
**Impact if ignored:** The entire rule-adaptation feedback loop is dead. The system cannot learn from its trading outcomes because the baseline rules don't exist.
**Fix required:** YES — run `initialize_rules()` on the live KB during system startup. This is infrastructure — WF-1 compatible.

---

### FINDING [13]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `knowledge_base/vectordb/` (empty) and `src/components/knowledge_base.py:310-470`
**What it is:** LanceDB vector store is empty. Layer 3 of the three-layer KB retrieval system (semantic similarity search for similar historical setups) is non-functional. The code is fully implemented but the store has never been populated.
**Impact if ignored:** The AI never receives "similar past trades" context. Session memory and rolling stats work, but historical pattern matching is dead.
**Fix required:** YES (deferred) — populate vectordb from the backtest trade index (367 trades). This is data seeding — WF-1 compatible.

---

### FINDING [14]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `run_kap.sh` (repo root) and cron log at `research/kap_outputs/cron.log`
**What it is:** The KAP research pipeline cron job is configured correctly (every 6 hours on weekdays) but every invocation fails with "Operation not permitted." The cron log shows 12 consecutive failures.
**Impact if ignored:** The research pipeline that's supposed to discover new trading insights is completely broken. No new KAP outputs are being generated.
**Fix required:** YES — `chmod +x run_kap.sh` or fix macOS permission/sandbox restriction. Verify with a manual test run.

---

### FINDING [15]
**Category:** DATA GAP
**Severity:** HIGH
**Location:** `knowledge_base/inverted_tp_log.jsonl`
**What it is:** The 8 inverted TP entries consist of only 2 distinct patterns repeated 4 times each: Pattern A (LONG, entry=3031.59, SL=3000.68, TP=3031.0) and Pattern B (SHORT, entry=3000.0, SL=3040.0, TP=3010.0). All 8 were logged April 9, 2026 within 76 minutes. This looks like repeated processing of the same data or a test scenario, not 8 independent events.
**Impact if ignored:** The "7% inverted TP rate" statistic may be inflated or mischaracterized. The actual number of unique inverted TP events is 2, not 8.
**Fix required:** YES — investigate the April 9 processing logs to determine if these were genuine independent evaluations or reprocessed data. Update the inverted TP rate calculation.

---

### FINDING [16]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `src/components/permissions.py:110-115` (Gate 1 direction check)
**What it is:** The direction mismatch safety check in Gate 1 uses `reasoning.daily_bias.direction` (the AI's own output), not the deterministic bias computed at `orchestrator.py:815-862`. If the AI reports a different bias than the deterministic computation, the gate checks against the AI's version.
**Impact if ignored:** A trade could pass the direction gate even when the deterministic bias computation says the opposite direction. The AI's self-reported bias becomes a self-validating loop.
**Fix required:** YES — Gate 1 should check the deterministic bias (passed from orchestrator), not the AI's reported bias.

---

### FINDING [17]
**Category:** DATA GAP
**Severity:** HIGH
**Location:** `src/components/data_ingestion.py:146-150` and `src/components/market_state.py:638-641,577`
**What it is:** When session levels (Asian high/low, PDH/PDL) default to 0.0 (e.g., Monday with no Saturday data, or mid-session start), LiquidityPool entries are created at price 0.0. The sweep detection at line 577 checks `c["close"] > pool.price` — since any candle close > 0.0, every candle triggers a spurious "run" sweep on the 0.0 pool. This generates hundreds of false sweep events.
**Impact if ignored:** The MSO is flooded with spurious sweep events on days with incomplete session data. The AI receives noise in its sweep data, potentially affecting trade decisions. The prompt shows max 5 sweeps, but the wrong 5 might be shown.
**Fix required:** YES — filter out pools where `price <= 0.0` in `_build_liquidity_pools()`.

---

### FINDING [18]
**Category:** DATA GAP
**Severity:** HIGH
**Location:** `src/prompts/primary_analyzer_prompt.py:359-364` (`_format_tf()` OB rendering)
**What it is:** OrderBlock `open` and `close` fields are generated by `market_state.py:315-316,339-340` but never rendered in the prompt. The AI only sees OB `type`, `high`, `low`, and `formation_time`. It cannot compute OB body ratio (a validated +17pp predictor per Test A rerun).
**Impact if ignored:** The AI cannot use OB body characteristics, which are statistically the strongest validated predictor. It sees the zone range but not the candle body within it.
**Fix required:** YES — add `open` and `close` to OB rendering in `_format_tf()`. This is a data completeness fix — WF-1 compatible as a bug fix.

---

### FINDING [19]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `config/agent_config.yaml:185` (`deployment.phase: 2`) — not referenced by any src/ code
**What it is:** The config has `deployment.phase: 2` (paper trading) but no code anywhere checks this value. The mock/real MT5 distinction is the only barrier — once RealMT5 is instantiated (via `--mode live` or `--mode demo`), all orders are real on the FTMO demo account.
**Impact if ignored:** `deployment.phase` provides zero code-level protection. If someone accidentally connects to a real-money account, there's no software gate preventing live orders.
**Fix required:** YES (LOW URGENCY) — either implement a phase check or remove the misleading config value. Currently the system is on FTMO demo which is the correct environment, so risk is contained.

---

### FINDING [20]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `src/components/devils_advocate.py:71`
**What it is:** The Devil's Advocate API call has three issues: (1) no `timeout=` parameter (could hang indefinitely), (2) no retry logic (all other production components have retry), (3) `temperature` is not set (defaults to server default, likely 1.0, unlike every other component which uses 0).
**Impact if ignored:** A hung DA API call could delay the pipeline. Non-deterministic temperature means DA outputs vary between runs on the same data, unlike the rest of the deterministic system.
**Fix required:** YES — add timeout (from config), add temperature=0, consider adding retry logic.

---

### FINDING [21]
**Category:** SILENT FAILURE RISK
**Severity:** HIGH
**Location:** `src/components/debate.py:196` — uses `SYSTEM_PROMPT` directly, never calls `build_system_prompt_for_instrument()`
**What it is:** The debate prompt functions `bull_agent_prompt.build_system_prompt_for_instrument()` and `judge_prompt.build_system_prompt_for_instrument()` exist but are dead code. If the debate were ever wired in, all 5 instruments (US30, USDJPY, GBPJPY, GBPUSD) would receive gold-specific debate prompts ("senior gold trader," gold-specific market references).
**Impact if ignored:** If debate is activated for multi-instrument trading without fixing this, the debate agents will role-play as gold traders when evaluating US30 or USDJPY setups.
**Fix required:** YES (when debate is wired in) — debate.py should call `build_system_prompt_for_instrument(config)` instead of using raw `SYSTEM_PROMPT`.

---

### FINDING [22]
**Category:** MISSING INFRA
**Severity:** HIGH
**Location:** `src/components/orchestrator.py` — grep for "postmortem" returns zero matches
**What it is:** The postmortem generation pipeline is not wired into the orchestrator. `src/prompts/postmortem_prompt.py` exists with a full prompt template, `adaptive_review.py` references `PostmortemRecord`, but no orchestrator method calls postmortem generation after trade closure. The `knowledge_base/postmortems/` directory is empty.
**Impact if ignored:** No AI-generated post-trade analysis occurs. The system cannot learn from individual trade outcomes. The adaptive review system that depends on postmortems is broken.
**Fix required:** YES (deferred) — wire postmortem generation into trade closure path. This adds learning capability but doesn't affect current trading logic.

---

### FINDING [23]
**Category:** MISSING INFRA
**Severity:** MEDIUM
**Location:** No SPRT code exists in `src/`
**What it is:** SPRT (Sequential Probability Ratio Test) monitoring is described in CLAUDE.md (emergency stop #7), the quick reference card (SPRT tables), and `.context/01_knowledge_base/kb_validation_and_monitoring_framework.md` — but zero SPRT code exists anywhere in src/. The framework for statistically deciding whether an instrument should be killed is entirely documentation.
**Impact if ignored:** No statistical stopping rule exists for instrument performance. A degrading instrument continues trading indefinitely until manual intervention.
**Fix required:** YES — implement SPRT monitoring as described in the validation framework doc.

---

### FINDING [24]
**Category:** MISSING INFRA
**Severity:** MEDIUM
**Location:** No CUSUM code exists in `src/`
**What it is:** CUSUM (Cumulative Sum) change-point detection is described in the validation framework but not implemented.
**Impact if ignored:** No statistical change-point detection for regime shifts or edge decay.
**Fix required:** YES — implement as part of monitoring infrastructure.

---

### FINDING [25]
**Category:** MISSING INFRA
**Severity:** MEDIUM
**Location:** No position mismatch detection code in `src/`
**What it is:** Emergency stop #5 ("MT5 position mismatch with system logs") has no implementation. No code compares MT5 open positions against system state.
**Impact if ignored:** If the system and MT5 diverge (e.g., manual intervention, partial fill, network error), nobody notices.
**Fix required:** YES — add position reconciliation check on each evaluation cycle.

---

### FINDING [26]
**Category:** UNIMPLEMENTED CLAIM
**Severity:** MEDIUM
**Location:** CLAUDE.md line 39: "Telegram bot operational (@gold_trader_os_bot)"
**What it is:** Zero telegram imports exist in `src/`. No `python-telegram-bot` in `requirements.txt`. No telegram code exists in the codebase. Either the bot runs outside this codebase (e.g., in the Claw Empire office) or the claim is false.
**Impact if ignored:** If the system encounters a critical issue, the documented alerting channel doesn't exist in this codebase.
**Fix required:** INVESTIGATE — determine if telegram runs externally or if the claim is false. Update documentation accordingly.

---

### FINDING [27]
**Category:** DATA GAP
**Severity:** MEDIUM
**Location:** `src/components/market_state.py:432`
**What it is:** `identify_breaker_blocks()` hardcodes `timeframe="H1"` on all breaker blocks regardless of the actual timeframe being analyzed. D1 or H4 breaker blocks are mislabeled as "H1".
**Impact if ignored:** If breaker_retest framework is ever enabled, the AI would see D1 breaker blocks labeled as H1, causing confusion about timeframe significance.
**Fix required:** YES — accept timeframe as a parameter. Low urgency since breaker_retest is disabled.

---

### FINDING [28]
**Category:** SILENT FAILURE RISK
**Severity:** MEDIUM
**Location:** `src/components/orchestrator.py:662-680` (correlation check)
**What it is:** Five parallel orchestrator processes (one per instrument) each query MT5 positions independently with no inter-process locking. Two processes could both check correlation at the same instant before either has opened a trade, and both pass.
**Impact if ignored:** Simultaneous trade entry could violate correlation limits. With max 1 trade per KZ and 2 per day, the window is small but real.
**Fix required:** YES (LOW URGENCY) — add file-based locking or use MT5 position query as a mutex check after order placement.

---

### FINDING [29]
**Category:** SILENT FAILURE RISK
**Severity:** MEDIUM
**Location:** `src/components/orchestrator.py:359-362`
**What it is:** When a kill zone already has a trade, subsequent candles are silently skipped with no `_log_candle()` call and no evaluation logger entry. These candles are completely invisible to monitoring and session summaries.
**Impact if ignored:** You cannot know what setups were available during an active trade's kill zone. Post-session analysis has blind spots.
**Fix required:** YES — add a minimal log entry for silently skipped candles.

---

### FINDING [30]
**Category:** DATA GAP
**Severity:** MEDIUM
**Location:** `src/components/primary_analyzer.py:139-158` (static context caching)
**What it is:** D1 and H4 data are rendered into the system prompt's static context on the first API call per session and cached via `_cached_system_blocks`. If D1 or H4 structure changes intra-session (e.g., new H4 BOS during NY), the prompt shows stale D1/H4 data. The deterministic bias IS recomputed per candle from the fresh MSO.
**Impact if ignored:** The AI makes decisions based on outdated higher-timeframe structure while the deterministic bias may have changed. Inconsistency between the bias injection and the raw data view.
**Fix required:** YES (MEDIUM URGENCY) — invalidate cache when D1/H4 structure direction changes between candles.

---

### FINDING [31]
**Category:** CONFIG CONFLICT
**Severity:** MEDIUM
**Location:** `config/agent_config.yaml:27` (max_spread_cents: 100) vs `src/components/data_ingestion.py:107` (hardcoded 30)
**What it is:** The config allows spreads up to 100 cents ($1.00) for XAUUSD, but `data_ingestion.py` hardcodes `spread_normal` flag at `spread_cents <= 30`. Spreads of 31-99 cents are tradeable (pass Gate 3) but flagged as abnormal in data quality.
**Impact if ignored:** The AI sees `spread_normal=False` for spreads that are actually within the acceptable range, potentially influencing its decision.
**Fix required:** YES — `data_ingestion.py` should reference config's `max_spread_cents` instead of hardcoding 30.

---

### FINDING [32]
**Category:** SILENT FAILURE RISK
**Severity:** MEDIUM
**Location:** `src/components/adaptive_review.py:114`
**What it is:** Adaptive review always creates `Anthropic()` directly, bypassing the `LLMBackend` billing mode routing. All other production components use `LLMBackend`. If billing mode is set to "subscription," adaptive review still charges the API.
**Impact if ignored:** Unexpected API charges for weekly insights generation that should route through subscription.
**Fix required:** YES (LOW URGENCY) — use LLMBackend for billing mode consistency.

---

### FINDING [33]
**Category:** CONFIG CONFLICT
**Severity:** MEDIUM
**Location:** `src/components/permissions.py:126-127` (hardcoded 1.5) and `src/components/m5_refinement.py:346,349` (hardcoded 1.5)
**What it is:** The inverted TP auto-correction and M5 refinement both hardcode `1.5 * raw_sl_dist` for TP calculation. This should reference `config["risk"]["min_rr"]`. If min_rr changes, these wouldn't update.
**Impact if ignored:** Config changes to min_rr would create silent inconsistency with the inverted TP correction and M5 refinement TP targets.
**Fix required:** YES — read from config instead of hardcoding.

---

### FINDING [34]
**Category:** DATA GAP
**Severity:** MEDIUM
**Location:** `src/prompts/primary_analyzer_prompt.py:412` (`static_pools[:10]`)
**What it is:** Liquidity pools are truncated to the first 10 in the prompt. On instruments with many equal levels, pools beyond position 10 are invisible to the AI. One canary fixture had 113 liquidity pools.
**Impact if ignored:** The AI may miss critical liquidity targets that appear after the 10th pool. Sweep detection and level identification are incomplete.
**Fix required:** YES — sort pools by proximity to current price before truncating, rather than taking the first 10 by insertion order.

---

### FINDING [35]
**Category:** DATA GAP
**Severity:** MEDIUM
**Location:** `src/prompts/primary_analyzer_prompt.py:451-455` (only M15 swings rendered)
**What it is:** D1, H4, and H1 swing points are computed in the MSO but never rendered in the prompt. Only M15 swings (last 10) are shown. The AI sees direction labels and protected swing prices but not the full swing sequence for higher timeframes.
**Impact if ignored:** The AI cannot independently verify structure direction for D1/H4/H1 — it must trust the computed direction label. Reduces the AI's ability to catch structure computation errors.
**Fix required:** NO (LOW PRIORITY) — the direction labels are sufficient for the current framework. Adding swing sequences would increase token usage significantly.

---

### FINDING [36]
**Category:** CONFIG CONFLICT
**Severity:** MEDIUM
**Location:** Multiple hardcoded trading parameters across `src/components/permissions.py`
**What it is:** 10 hardcoded values in permissions.py that should be configurable:
- Line 147: `rr < 1.3` (min RR floor)
- Line 167/172: `tp1_r < 1.3` / `tp1_r > 2.0` (TP1 band)
- Line 193: `max_sl_pct = 2.5` (max SL as % of entry)
- Line 187: `m15_atr * 1.5` (SL vs ATR multiplier)
**Impact if ignored:** These trading-critical parameters cannot be tuned without code changes. Different instruments may need different thresholds.
**Fix required:** YES (LOW URGENCY) — move to config. Not urgent since values are currently correct for the system.

---

### FINDING [37]
**Category:** MISSING INFRA
**Severity:** MEDIUM
**Location:** `.context/00_core/architecture.md` (v1.0, dated 2026-03-28)
**What it is:** The architecture document describes a XAUUSD-only system. The actual system has expanded to 5 instruments with per-instrument config, multi-kill-zone scheduling, cross-instrument correlation, and instrument-specific tuning — none of which the architecture doc covers.
**Impact if ignored:** The architecture doc is misleading for anyone trying to understand the system. New sessions reference it as authoritative but it describes a different system.
**Fix required:** YES — update architecture doc to reflect multi-instrument reality.

---

### FINDING [38]
**Category:** UNIMPLEMENTED CLAIM
**Severity:** MEDIUM
**Location:** Handoff 07 line 96: "Session memory doubles expectancy (+0.66R vs +0.33R)"
**What it is:** Session memory IS implemented and active (`orchestrator.py:164-165,765-804,419-439`). However, the specific numbers "+0.66R vs +0.33R" are imprecisely cited. The source data (`knowledge_base_backtest/analysis/deep_trade_analysis_0.md:216-225`) shows: low patience = +0.03R avg (+0.33R total from 12 trades), high patience = +0.61R avg (+8.58R total from 14 trades). The "doubles expectancy" claim is directionally correct but the numbers are not precisely traceable.
**Impact if ignored:** Low — the mechanism works. The statistical claim is approximately correct but not rigorous.
**Fix required:** NO — update documentation if time permits.

---

### FINDING [39]
**Category:** OTHER
**Severity:** LOW
**Location:** `src/prompts/postmortem_prompt.py` and `prompts/short_validation_batch_prompt.md`
**What it is:** Two orphaned prompt files: `postmortem_prompt.py` has no production caller (only test coverage), and `short_validation_batch_prompt.md` is not loaded by any code.
**Impact if ignored:** Dead code clutter. No functional impact.
**Fix required:** NO — can be cleaned up during refactoring.

---

### FINDING [40]
**Category:** OTHER
**Severity:** LOW
**Location:** `src/components/debate.py:196` — `bull_agent_prompt.build_system_prompt_for_instrument()` and `judge_prompt.build_system_prompt_for_instrument()`
**What it is:** Instrument-specific prompt builder functions exist but are never called. Dead code.
**Impact if ignored:** No functional impact while debate is not wired in.
**Fix required:** NO — clean up when debate is activated.

---

### FINDING [41]
**Category:** OTHER
**Severity:** LOW
**Location:** `knowledge_base/logs/` (empty)
**What it is:** Vestigial directory. The monitoring system writes to `knowledge_base/meta/logs/` instead.
**Impact if ignored:** No functional impact. Confusing directory structure.
**Fix required:** NO — remove during cleanup.

---

### FINDING [42]
**Category:** OTHER
**Severity:** LOW
**Location:** Project root — no `.env.example` file
**What it is:** The `.env` file contains a real Anthropic API key. No `.env.example` documents required environment variables. The security module checks for `ENVIRONMENT`, `DEBUG`, `LOG_LEVEL`, and `SECRET_KEY` but none are documented as requirements.
**Impact if ignored:** New deployments have no reference for required env vars.
**Fix required:** YES (LOW PRIORITY) — create `.env.example` with placeholder values. Verify `.env` is in `.gitignore`.

---

### FINDING [43]
**Category:** OTHER
**Severity:** LOW
**Location:** `tests/` directory — 44 test files, not 43
**What it is:** CLAUDE.md says "43 test files" but 44 exist. Trivial off-by-one.
**Impact if ignored:** None.
**Fix required:** NO.

---

### FINDING [44]
**Category:** MISSING INFRA
**Severity:** LOW
**Location:** 16 components in `src/` with no architecture documentation
**What it is:** The following active production components exist but are not documented in the architecture doc: `devils_advocate.py`, `trade_capture.py`, `evaluation_logger.py`, `news_calendar.py`, `m5_refinement.py`, `walk_forward.py`, `portfolio_risk.py`, `llm_backend.py`, `security/environment.py`, `security/validation.py`, `security/wf1_protection.py`, `utils/cross_instrument.py`, `utils/monitoring_init.py`, `utils/file_versioning.py`, `utils/chart_renderer.py` (dead), `utils/youtube_extractor.py`.
**Impact if ignored:** New sessions working from the architecture doc will not know these components exist.
**Fix required:** YES (LOW PRIORITY) — update architecture doc to cover all active components.

---

## SWEEP SUMMARY
=============

| Metric | Count |
|--------|-------|
| Critical findings | 7 |
| High findings | 15 |
| Medium findings | 15 |
| Low findings | 6 |
| **Total findings** | **43** |
| Empty folders with no impact | 8 (postmortems/, trades/, vectordb/, logs/, journals/daily, journals/weekly, data/sessions/, live_alerts/) |
| Empty folders that will cause silent failures | 2 (rules/, no_trades/) |
| Config conflicts found | 9 |
| Unimplemented claims found | 2 (Telegram bot, session memory numbers) |
| Hardcoded values that should be in config | 10 |
| Emergency stops documented but not enforced | 5 of 8 |
| MSO fields missing from prompt | 11 |
| Dead code components | 3 (debate in pipeline, postmortem pipeline, instrument-specific debate prompts) |
| **Overall system integrity** | **SIGNIFICANT RISKS** |

---

## TOP 3 THINGS TO FIX FIRST

### 1. Daily P&L circuit breaker + emergency stop enforcement (Findings [3], [4])
The system has no working circuit breaker for daily losses. `daily_pnl_pct` starts at 0.0 and never updates. Five of eight documented emergency stops have no code enforcement. A cascading loss scenario has no automated protection. **Fix `daily_pnl_pct` update from MT5 immediately. Then implement portfolio drawdown, consecutive loss, and position mismatch checks.**

### 2. Add `causing_event_type` to prompt and `write_no_trade()` to orchestrator (Findings [2], [6])
The AI is instructed to check a field that isn't in its data, forcing hallucination on every evaluation. Meanwhile, 571 evaluations have produced zero audit trail for rejections. **Add `causing_event_type` to `_format_tf()` OB rendering. Add `kb.write_no_trade()` call in the NO_TRADE path. Both are one-line fixes that are WF-1 compatible.**

### 3. Fix canary system to detect bidirectional drift (Finding [5])
The canary only detects one direction of drift and has enshrined the model's over-restrictiveness as the baseline. The 5-fixture CANDIDATE→NO_TRADE disagreement may explain the zero-trade problem. **Create CANDIDATE-baseline fixtures. Create "tempting but wrong" fixtures. Investigate why the model rejects 5 historically winning setups.**

---

## ADDITIONAL PRIORITY ITEMS (fixes 4-7)

### 4. Align max_tokens between batch and live (Finding [8])
Live uses 1500 tokens, batch uses 2000. The system was validated at a budget it doesn't use in production.

### 5. Resolve London KZ end time discrepancy (Finding [9])
Config says 09:30, docs say 10:30. One hour of potential setups is silently ignored or the documentation is wrong.

### 6. Wire Bull/Bear Debate or update architecture (Finding [1])
The documented adversarial review step doesn't run. Either activate it or officially document its removal.

### 7. Fix timezone handling in MT5 timestamps (Finding [7])
`fromtimestamp()` without UTC is a latent bug. If the Windows machine is in UTC this is dormant, but it will corrupt data the moment the timezone changes.

---

*Generated: April 11, 2026*
*Method: 8 parallel forensic agents covering empty folders, API calls, canary fixtures, configuration, data pipeline, execution logic, claim verification, and missing infrastructure*
*Files read: 50+ source files, 10 canary fixtures, 7 handoff documents, all config files*
*Total findings: 43 (7 critical, 15 high, 15 medium, 6 low)*
