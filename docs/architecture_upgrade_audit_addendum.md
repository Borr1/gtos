# Architecture Upgrade Audit — Addendum & Corrections

**Date:** 2026-03-31 (second pass)
**Reason:** Pressure-test of initial audit revealed missed patterns, understated complexity, and inaccuracies.

---

## What the Initial Audit Got Wrong or Understated

### Correction 1: The Trading Agent Has MORE Error Handling Than Stated

The initial audit said "error handling defaults to NO_TRADE on any failure (safe)." This is an understatement.

**Already implemented:**
- `primary_analyzer.py:220-309` — Full retry logic for API mode (SDK built-in) AND subscription mode (progressive backoff: 5s → 10s → 15s with higher retry count)
- `primary_analyzer.py:183-198` — Format correction retry: on malformed JSON, retries with correction prompt appended
- `debate.py:282-307` — Async retry per agent role with specific handling for timeout, rate limit (parses `retry_after` header), and 500 errors
- `primary_analyzer.py:333-396` — Field normalization auto-corrects 11+ variant spellings (e.g., `equal_high` → `equal_highs`, `order_block` → `OB`, `A-` → `B+`)

**Impact on P7 (Error Handling):** The AI-layer error handling is already solid. P7 should focus EXCLUSIVELY on the MT5 execution layer, not the AI layer. The error handling matrix in the initial audit is correct for execution, but the "Risk if Skipped" should note that AI-layer errors are already well-handled.

### Correction 2: Orchestrator Design Missed Dual Kill Zones

The initial audit's state machine only had `WAITING` → `EVALUATING` inside a single KZ. The actual system evaluates BOTH London (07:00-09:30 UTC) AND New York (13:00-15:30 UTC), with max 1 trade per zone per day.

**Corrected State Machine Addition:**

```
WAITING (London KZ)
    │ M15 candle close
    ▼
EVALUATING (London)
    │
    ├── Trade taken → London slot filled
    └── No trade → continue evaluating London candles
    │
    │ 09:30 UTC — London KZ ends
    ▼
KZ_COOLDOWN (09:30 → 13:00 UTC gap)
    │
    │ 13:00 UTC — NY KZ starts
    ▼
WAITING (NY KZ)
    │ M15 candle close
    ▼
EVALUATING (NY)
    │
    ├── Trade taken → NY slot filled
    └── No trade → continue evaluating NY candles
    │
    │ 15:30 UTC — NY KZ ends
    ▼
SHUTTING_DOWN
```

**Config implication:** `max_trades_per_day: 1` in current config means 1 TOTAL across both KZs. The config should clarify `max_trades_per_kz: 1` vs `max_trades_per_day: 2` (1 per KZ). The batch backtest already handles dual KZs correctly (`batch_backtest.py` processes both windows).

### Correction 3: Batch API Pathway Was Completely Omitted

The initial audit focused entirely on live execution patterns. But `batch_backtest.py` (1,104 lines) implements a complete 5-phase batch pipeline that's a mature, production-tested component:

1. **COLLECT** — Pre-screen dates using deterministic checks (zero API cost), build prompts for all M15 candles in both KZs
2. **SUBMIT** — Convert to Anthropic Messages Batches API format, submit batch
3. **WAIT** — Poll with configurable interval (default 60s)
4. **PROCESS** — Download results, parse responses, apply safety checks, evaluate outcomes
5. **REPORT** — Generate statistics, cost analysis, per-window breakdown

**Cost savings:** 70-75% vs sequential API calls (50% batch discount + prompt caching).

**Why this matters for the audit:** The batch system already solves many problems the audit flagged:
- Pre-screening filters (D1 bias + H4 alignment) are deterministic date filters that could be reused by the live orchestrator
- Safety checks in batch processing are the same checks that should be in the execution engine
- Session manifest writing is already implemented

### Correction 4: Vision Mode Not Mentioned

`batch_backtest.py` supports a `--vision` flag that renders annotated M15 charts as base64 PNGs and sends them as multimodal messages to Claude. The chart renderer (`chart_renderer.py`, 250+ lines) produces TradingView-style dark theme charts with:
- Order block zones (teal/red transparent)
- Structure breaks (yellow dotted)
- Session levels (Asian blue, PDH purple, London orange)
- Premium/discount zones
- Current price marker

**Audit implication:** If vision mode improves accuracy, the live orchestrator should support it too. This adds a dependency on chart_renderer for the orchestrator that wasn't in the initial audit.

### Correction 5: Cost Tracking Pattern in claw-code Was Missed

`claw-code/src/cost_tracker.py` implements a `CostTracker` with:
- `total_units` counter
- `events` list tracking `(label, units)` pairs
- `costHook.py` — `apply_cost_hook()` wraps operations with cost tracking

**Direct mapping to trading agent:** The trading agent already has token counting in `primary_analyzer.py:231-241` and `debate.py:325-346`, plus batch cost calculation in `batch_backtest.py:855-892`. But there's no UNIFIED cost tracker that aggregates across all components.

**New recommendation:** Add a centralized `CostTracker` (modeled on claw-code's) that aggregates:
- Primary Analyzer API costs
- Debate Engine API costs (if used)
- Verification Agent costs (new, from P5)
- Adaptive Review API costs (weekly insights + deep reviews)
- Running total checked against `budget.monthly_cap_usd: 25.0`

### Correction 6: Trust-Gated Initialization Deserves Its Own Section

`claw-code/src/deferred_init.py` implements a critical pattern: **security-sensitive subsystems only initialize if trusted=True**. The four gated subsystems are:
- `plugin_init`
- `skill_init`
- `mcp_prefetch`
- `session_hooks`

**Direct mapping:** The trading agent should have trust-gated phases in its bootstrap:

| Phase | Trusted=True (live trading) | Trusted=False (backtest/dry-run) |
|-------|---------------------------|--------------------------------|
| MT5 connection | Real connection | Mock/skip |
| Order execution | Real orders | Simulated |
| Telegram alerts | Real alerts | Log only |
| Account queries | Real balance | Fixed test balance |

This gives the orchestrator a clean way to support paper trading (Phase 2) vs live trading (Phase 3) vs backtesting (Phase 1) through a single `trusted` flag rather than mode-switching logic scattered everywhere.

### Correction 7: Protected Parameters and the Adaptation Guardrail System

The initial audit mentioned the adaptive review's 4 tiers but didn't emphasize the **protected parameters** system strongly enough.

`adaptive_review.py:44-53` defines 8 FROZEN parameters:
```python
PROTECTED_PARAMETERS = frozenset({
    "max_risk_pct",
    "max_trades_per_day",
    "max_daily_loss_pct",
    "max_weekly_loss_pct",
    "max_monthly_loss_pct",
    "session_start_utc",
    "session_end_utc",
    "debate_required",
})
```

**Why this matters for the permission system (P3):** These same parameters should be HARD_BLOCK in the execution permission system. The permission system should read from the same `PROTECTED_PARAMETERS` frozenset, ensuring the AI adaptation system and the execution system agree on what's immutable. This is defense-in-depth: even if the adaptation system has a bug that tries to modify `max_risk_pct`, the execution permission gate rejects it.

### Correction 8: Lifecycle State Machine Was Not Mentioned

`trade_models.py` implements a formal lifecycle state machine with explicit transitions:

```
EVALUATING → NO_TRADE | CANDIDATE
CANDIDATE → DEBATED
DEBATED → REJECTED | APPROVED | APPROVED_MARGINAL
APPROVED | APPROVED_MARGINAL → EXECUTING
EXECUTING → ACTIVE | FAILED_EXECUTION
ACTIVE → CLOSED
```

Terminal states: `NO_TRADE`, `REJECTED`, `FAILED_EXECUTION`, `CLOSED`

The `transition()` function enforces forward-only transitions with `StateTransition` tracking (from_state, to_state, timestamp, reason).

**Audit implication:** The orchestrator's state machine (P1) should COMPOSE with this trade lifecycle state machine, not replace it. The orchestrator manages the session lifecycle; the trade model manages individual trade lifecycle. These are orthogonal.

### Correction 9: Stream Protocol as Observability Pattern

claw-code's `query_engine.py:106-127` implements an SSE-like stream protocol:
```
message_start → command_match → tool_match → permission_denial → message_delta → message_stop
```

Each event carries structured data (session_id, commands, tools, denials, usage, stop_reason, transcript_size).

**Mapping to trading agent:** The orchestrator should emit similar structured events for real-time monitoring:

```python
# Orchestrator events (for Telegram, dashboard, or log consumption)
ORCHESTRATOR_EVENTS = [
    "session_start",          # bootstrap complete
    "kz_enter",               # entering kill zone
    "candle_close",           # M15 candle detected
    "evaluation_start",       # pipeline begins
    "evaluation_result",      # NO_TRADE / CANDIDATE / WAIT
    "verification_start",     # sending to verification agent
    "verification_result",    # CONFIRM / REJECT
    "execution_start",        # placing MT5 order
    "execution_result",       # filled / rejected / timeout
    "circuit_breaker",        # daily limit hit
    "kz_exit",                # kill zone ended
    "session_end",            # shutdown
    "error",                  # any error
    "crash_recovery",         # reconciliation on restart
]
```

This gives the Telegram alerting (P8) a clean event bus to subscribe to rather than ad-hoc alert calls scattered through the code.

---

## New Patterns Found That Weren't in Initial Audit

### Pattern A: Parity Audit as Continuous Validation

`claw-code/src/parity_audit.py` continuously validates the Python port against the archived TypeScript source. It measures:
- Root file coverage (% of TS files with Python equivalents)
- Directory coverage (% of subsystem directories present)
- Command/tool entry counts

**Trading agent application:** After implementing the orchestrator and execution engine, create a `system_health_audit.py` that continuously validates:
- All 8 components are present and initialized
- KB files are consistent (trade_index count matches trade record files)
- MT5 positions match local records (the reconciliation from P2, run on a schedule)
- API cost is within budget
- Config parameters haven't been corrupted

This turns crash recovery (P2) from a "only on startup" operation into a continuous background validation.

### Pattern B: Pre-Screen Filters Save Money

`batch_backtest.py` pre-screens dates using deterministic checks BEFORE making any API calls:
- D1 bias must be clearly bullish or bearish
- H4 must agree with D1 (no conflicts)

Dates that fail pre-screening are skipped entirely (zero API cost).

**Live trading application:** The orchestrator should run the same pre-screen BEFORE calling the Primary Analyzer:

```python
async def _should_evaluate_candle(self, market_state) -> bool:
    """Deterministic pre-screen — skip Claude call if structure is unclear."""
    d1 = market_state.timeframes.get("D1")
    h4 = market_state.timeframes.get("H4")

    # No clear daily bias → no trade possible (U1 will fail)
    if d1 and d1.structure.direction not in ("bullish", "bearish"):
        return False

    # H4 conflicts with D1 → no trade possible (U2 will fail)
    if d1 and h4:
        if d1.structure.direction != h4.structure.direction:
            return False

    return True  # Structure looks viable, worth the API call
```

**Cost impact:** In backtesting, ~30-40% of dates were pre-screened out. At $0.01-0.03 per Claude call, this saves $5-15/month in live trading.

### Pattern C: Deterministic Quality Scoring

`adaptive_review.py:227-252` implements 6 binary quality checks as pure Python (no AI):
1. Risk exactly 1% (±0.15%)
2. Entry within session window (07:00-09:59 UTC)
3. SL direction correct
4. Position size > 0
5. One trade per day limit
6. Partial closes correct (TP1 remaining ≤ 55%)

**Audit implication:** The execution engine (P3) should run these SAME checks as a final gate before placing the order. The quality scoring currently runs post-trade (in adaptive review). Moving it pre-trade adds another validation layer:

```python
# In execution engine, BEFORE placing order:
pre_trade_checks = compute_deterministic_quality(trade_params, session_context)
if pre_trade_checks.score < 100:
    failed = [c for c in pre_trade_checks.checks if not c.passed]
    logger.warning("Pre-trade quality check failed: %s", failed)
    return ExecutionDenial(reason=f"Quality check failures: {failed}")
```

### Pattern D: Debate Calibration Metrics

`adaptive_review.py:434-476` tracks debate performance metrics:
- `bull_wins` vs `bear_wins` (based on debate confidence ≥ 50)
- `false_approvals_pct` (losses among approved trades)
- Analyzed over last 200 trades

**If implementing the Verification Agent (P5):** Track the same calibration metrics:
- `verification_confirm_rate` — what % of CANDIDATEs get confirmed
- `verification_false_confirms` — confirmed trades that lost
- `verification_false_rejects` — rejected trades that would have won (requires hypothetical outcome tracking)

This enables the adaptive review system to tune the verification agent over time, just as it currently tunes the debate.

### Pattern E: API Key Safety as Critical Pattern

`llm_backend.py:189-193` implements a critical safety mechanism:
```python
env = os.environ.copy()
for key in _API_KEY_ENV_VARS:
    env.pop(key, None)
# Double-check: assert no API key survived
for key in _API_KEY_ENV_VARS:
    assert key not in env, f"CRITICAL SAFETY FAILURE: {key} still present!"
```

**Risk context:** In subscription mode, if the API key leaks through to the subprocess, each Claude call bills at API rates (~$0.01-0.03) instead of subscription rates ($0.00). Over a month of live trading, this could be $1,800+ in accidental charges.

**Audit implication:** The orchestrator should run a similar safety check on startup:
```python
# In bootstrap, verify billing mode matches intent
if config["ai"]["billing_mode"] == "subscription":
    for key in _API_KEY_ENV_VARS:
        if key in os.environ:
            raise RuntimeError(
                f"SAFETY: {key} is set but billing_mode=subscription. "
                f"Remove the API key or switch to billing_mode=api."
            )
```

---

## Revised Effort Estimates

| Priority | Initial Estimate | Revised Estimate | Reason for Change |
|----------|-----------------|------------------|-------------------|
| P1: Orchestrator | 3-5 days | 4-6 days | Dual KZ handling, trust-gated init, pre-screen filters, event emission |
| P2: Crash Recovery | 2-3 days | 2-3 days | Unchanged — MT5 reconciliation is the core work |
| P3: Permission System | 2-3 days | 3-4 days | Add protected parameters integration, pre-trade quality checks, API key safety |
| P4: Context Management | 1-2 days | 1-2 days | Unchanged |
| P5: Multi-Agent Redesign | 2-3 days | 2-3 days | Add calibration metrics tracking |
| P6: Prompt Templates | 1-2 days | 1-2 days | Unchanged |
| P7: Error Handling | 2-3 days | 1-2 days | **Reduced** — AI-layer already well-handled, focus only on MT5 execution |
| P8: Observability | 2 days | 2-3 days | Add event bus, unified cost tracker, system health audit |

**NEW: P9 (added)**
| P9: Unified Cost Tracker | N/A | 1 day | CostTracker aggregating all API costs, checked against monthly budget |
| P10: Pre-Screen Filters | N/A | 0.5 days | Deterministic pre-screen before Claude call, already proven in batch |
| P11: Trust-Gated Bootstrap | N/A | 0.5 days | Single `trusted` flag for backtest/paper/live mode switching |

---

## Revised Master Roadmap

### Phase A: Required Before Going Live (16-22 days)

| # | Component | Priority | Effort | Change from v1 |
|---|-----------|----------|--------|----------------|
| 1 | Orchestrator (dual KZ, trust-gated, events) | P1 | 4-6 days | +1 day |
| 2 | Execution Engine (MT5 orders) | P3 | 3-4 days | same |
| 3 | Permission System (3-gate + protected params) | P3 | 3-4 days | +1 day |
| 4 | Crash Recovery (position reconciliation) | P2 | 2-3 days | same |
| 5 | Execution Error Handling (MT5 only) | P7 | 1-2 days | **-1 day** |
| 6 | Telegram Alerting via Event Bus | P8 | 1-2 days | +0.5 day |
| 7 | API Key Safety Check | P3 (sub) | 0.5 days | **NEW** |
| 8 | Pre-Screen Filters (from batch code) | P10 | 0.5 days | **NEW** |

### Phase B: Should Have for Paper Trading (6-9 days)

| # | Component | Priority | Effort |
|---|-----------|----------|--------|
| 9 | Session Memory (cross-candle context) | P4 | 1-2 days |
| 10 | Verification Agent (debate replacement) | P5 | 2-3 days |
| 11 | Unified Cost Tracker | P9 | 1 day |
| 12 | Trust-Gated Bootstrap Modes | P11 | 0.5 days |
| 13 | System Health Audit (continuous validation) | P8 | 1-2 days |

### Phase C: Optimization (4-6 days)

| # | Component | Priority | Effort |
|---|-----------|----------|--------|
| 14 | Prompt Template System | P6 | 1-2 days |
| 15 | Token Budget Enforcement | P4 | 1 day |
| 16 | Monitoring Dashboard (FastAPI) | P8 | 2-3 days |
| 17 | Vision Mode for Live (chart rendering) | New | 1 day |

---

## Files That Connect Both Codebases (Reference Map)

| claw-code File | Trading Agent Equivalent | Pattern Transferred |
|---------------|------------------------|-------------------|
| `runtime.py` (PortRuntime) | `orchestrator.py` (Orchestrator) | Bootstrap → turn loop → teardown |
| `query_engine.py` (QueryEnginePort) | `primary_analyzer.py` (PrimaryAnalyzer) | Submit message, budget tracking, stop reasons |
| `permissions.py` (ToolPermissionContext) | `execution.py` (ExecutionPermissionSystem) | Pre-execution filtering, denial tracking |
| `session_store.py` (StoredSession) | `knowledge_base.py` (SessionManifest) | Session persistence and reload |
| `transcript.py` (TranscriptStore) | New: SessionMemory | Sliding window compaction |
| `setup.py` (run_setup) | Orchestrator bootstrap stages | Parallel prefetch, trust gating |
| `deferred_init.py` | New: trust-gated init | Security-aware mode switching |
| `cost_tracker.py` (CostTracker) | New: unified CostTracker | Centralized cost aggregation |
| `bootstrap_graph.py` | Orchestrator._bootstrap_stages | Ordered initialization pipeline |
| `history.py` (HistoryLog) | `monitoring.py` (SessionLogger) | Structured event logging |
| `execution_registry.py` | Orchestrator pipeline dispatch | Component lookup and execution |
| `parity_audit.py` | New: system_health_audit.py | Continuous state validation |

---

## Conclusion

The initial audit's 8 priorities and implementation sketches are architecturally sound. The main corrections are:

1. **Dual KZ handling** was missing from the orchestrator design
2. **Error handling effort was overestimated** because the AI layer already has comprehensive retry logic
3. **Three new micro-priorities** should be added: unified cost tracker, pre-screen filters (already proven in batch), and trust-gated bootstrap
4. **The batch_backtest.py is a goldmine** — it contains pre-screen logic, safety checks, and session manifest writing that can be extracted and reused by the live orchestrator
5. **Protected parameters** should be shared between the adaptive review and execution permission system for defense-in-depth
6. **The event bus pattern** from claw-code's stream protocol cleanly solves the "where do alerts come from" problem

Total revised effort: **Phase A: 16-22 days**, **Phase B: 6-9 days**, **Phase C: 4-6 days**.
