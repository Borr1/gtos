# Claude Code Source Audit → XAUUSD Trading Agent Architecture Upgrade

**Date:** 2026-03-31
**Source:** `claw-code/` (Python port of Claude Code harness)
**Target:** `gold-agent/` (XAUUSD intraday trading agent)

---

## Priority 1: Session Orchestrator (Component 8)

### Claude Code Pattern Found

**Files:** `claw-code/src/runtime.py` (193 lines), `claw-code/src/setup.py` (78 lines), `claw-code/src/bootstrap_graph.py` (28 lines)

The Claude Code harness uses a multi-phase bootstrap → turn loop → teardown pattern:

1. **Bootstrap** (`PortRuntime.bootstrap_session()`, runtime.py:109-152):
   - Builds workspace context (environment detection)
   - Runs parallel prefetches (MDM, keychain, project scan)
   - Initializes query engine with session ID (UUID)
   - Routes initial prompt, builds execution registry
   - Persists session state after bootstrap completes

2. **Turn Loop** (`PortRuntime.run_turn_loop()`, runtime.py:154-167):
   - Iterates up to `max_turns` times
   - Each turn: route prompt → check permissions → execute → check stop condition
   - Stop conditions: `max_turns_reached`, `max_budget_reached`, `completed`
   - Budget tracked via `UsageSummary` (cumulative tokens)

3. **Bootstrap Graph** (bootstrap_graph.py:16-27): Seven ordered stages:
   ```
   1. top-level prefetch side effects
   2. warning handler and environment guards
   3. CLI parser and pre-action trust gate
   4. setup() + commands/agents parallel load
   5. deferred init after trust
   6. mode routing: local / remote / ssh / teleport
   7. query engine submit loop
   ```

4. **Session Persistence** (session_store.py): JSON snapshot after each session with session_id, messages, token counts.

5. **No daemon/KAIROS pattern found.** The claw-code port has session recovery via `QueryEnginePort.from_saved_session()` but no persistent background daemon. The trading agent must build its own daemon loop.

### Adaptation for Trading Agent

The orchestrator maps directly to the trading agent's M15 candle-driven lifecycle, but with a critical difference: Claude Code is request-response (user submits prompt → agent responds). The trading agent is **event-driven** (M15 candle closes → pipeline runs).

**State Machine:**

```
                    ┌──────────────┐
                    │   DORMANT    │  (outside trading hours)
                    └──────┬───────┘
                           │ 06:45 UTC startup
                           ▼
                    ┌──────────────┐
                    │  INITIALIZING │  (prefetch, MT5 connect, KB load)
                    └──────┬───────┘
                           │ checks pass
                           ▼
                    ┌──────────────┐
          ┌────────│   WAITING    │◄─────────────────┐
          │        └──────┬───────┘                  │
          │               │ M15 candle close          │
          │               │ in kill zone              │
          │               ▼                           │
          │        ┌──────────────┐                  │
          │        │  EVALUATING  │  (pipeline run)  │
          │        └──────┬───────┘                  │
          │               │                           │
          │      ┌────────┴────────┐                 │
          │      ▼                 ▼                  │
          │  NO_TRADE         CANDIDATE               │
          │      │                 │                   │
          │      │                 ▼                   │
          │      │          ┌──────────────┐          │
          │      │          │  EXECUTING   │          │
          │      │          └──────┬───────┘          │
          │      │                 │                   │
          │      └────────┬────────┘                  │
          │               │ log result                │
          │               └───────────────────────────┘
          │
          │ kill zone ends OR daily limits hit
          ▼
   ┌──────────────┐
   │ KZ_COOLDOWN  │  (between kill zones)
   └──────┬───────┘
          │ next KZ starts OR session ends
          ▼
   ┌──────────────┐
   │  SHUTTING_DOWN│  (persist state, close MT5)
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   DORMANT    │
   └──────────────┘
```

### Implementation Sketch

```python
# src/components/orchestrator.py

import asyncio
import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

class OrchestratorState(Enum):
    DORMANT = auto()
    INITIALIZING = auto()
    WAITING = auto()        # idle between candle closes
    EVALUATING = auto()     # pipeline running
    EXECUTING = auto()      # MT5 order in flight
    KZ_COOLDOWN = auto()    # between kill zones
    SHUTTING_DOWN = auto()
    ERROR_RECOVERY = auto()

@dataclass
class SessionContext:
    """Mutable state for the current trading session."""
    date: str
    trades_today: int = 0
    daily_pnl_pct: float = 0.0
    current_kz: Optional[str] = None
    candles_evaluated: int = 0
    last_candle_time: Optional[str] = None
    open_position_ticket: Optional[int] = None

class Orchestrator:
    """Component 8 — M15 candle-driven session lifecycle manager.

    Modeled on claw-code/src/runtime.py PortRuntime pattern:
    bootstrap → turn loop → teardown, adapted for event-driven trading.
    """

    LOCK_FILE = Path("knowledge_base/meta/.orchestrator.lock")
    STATE_FILE = Path("knowledge_base/meta/orchestrator_state.json")

    def __init__(self, config: dict):
        self.config = config
        self.state = OrchestratorState.DORMANT
        self.session: Optional[SessionContext] = None
        self._shutdown_requested = False

        # From claw-code bootstrap_graph: ordered startup stages
        self._bootstrap_stages = [
            "acquire_pid_lock",
            "connect_mt5",
            "load_config_and_kb",
            "reconcile_open_positions",   # crash recovery
            "validate_account_health",
            "enter_turn_loop",
        ]

    # ── PID Locking (prevents duplicate instances) ────────────────

    def _acquire_lock(self) -> bool:
        """PID-based single-instance lock."""
        self.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.LOCK_FILE.exists():
            stored_pid = int(self.LOCK_FILE.read_text().strip())
            try:
                os.kill(stored_pid, 0)  # check if process exists
                return False  # another instance is running
            except OSError:
                pass  # stale lock, process is dead
        self.LOCK_FILE.write_text(str(os.getpid()))
        return True

    def _release_lock(self):
        if self.LOCK_FILE.exists():
            self.LOCK_FILE.unlink(missing_ok=True)

    # ── Bootstrap (modeled on PortRuntime.bootstrap_session) ──────

    async def bootstrap(self) -> bool:
        """Multi-phase startup. Returns True if ready to trade."""
        self.state = OrchestratorState.INITIALIZING

        if not self._acquire_lock():
            raise RuntimeError("Another orchestrator instance is running")

        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        # Execute bootstrap stages in order
        for stage in self._bootstrap_stages:
            handler = getattr(self, f"_stage_{stage}", None)
            if handler:
                success = await handler()
                if not success:
                    self.state = OrchestratorState.ERROR_RECOVERY
                    return False

        self.session = SessionContext(
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )
        self.state = OrchestratorState.WAITING
        return True

    # ── Turn Loop (modeled on PortRuntime.run_turn_loop) ──────────

    async def run(self):
        """Main event loop — blocks until shutdown.

        Like claw-code's turn loop but driven by M15 candle closes
        instead of user prompts.
        """
        if not await self.bootstrap():
            return

        try:
            while not self._shutdown_requested:
                now = datetime.now(timezone.utc)

                # Check if within any kill zone
                active_kz = self._get_active_kill_zone(now)

                if active_kz is None:
                    # Outside kill zones — sleep until next one
                    if self.state == OrchestratorState.WAITING:
                        self.state = OrchestratorState.KZ_COOLDOWN
                    next_event = self._next_kz_start(now)
                    sleep_secs = min(
                        (next_event - now).total_seconds(),
                        60,  # wake every 60s max to check signals
                    )
                    await asyncio.sleep(max(1, sleep_secs))
                    continue

                # Within a kill zone — wait for next M15 close
                self.session.current_kz = active_kz
                self.state = OrchestratorState.WAITING

                next_candle = self._next_m15_close(now)
                wait_secs = (next_candle - now).total_seconds()

                if wait_secs > 0:
                    # BLOCKING BUDGET: never block longer than 60s
                    # (from claw-code's max_budget_tokens concept)
                    await asyncio.sleep(min(wait_secs, 60))
                    if wait_secs > 60:
                        continue  # re-check conditions

                # ── Candle closed — run pipeline ──────────────
                if self._daily_limits_hit():
                    continue

                self.state = OrchestratorState.EVALUATING
                try:
                    result = await self._run_pipeline(next_candle)
                    if result and result.get("decision") == "CANDIDATE":
                        self.state = OrchestratorState.EXECUTING
                        await self._execute_trade(result)
                finally:
                    self.state = OrchestratorState.WAITING
                    self.session.candles_evaluated += 1

        finally:
            await self._shutdown()

    # ── Shutdown (modeled on session persistence) ─────────────────

    async def _shutdown(self):
        self.state = OrchestratorState.SHUTTING_DOWN
        # Persist session manifest (like claw-code persist_session)
        self._persist_session_manifest()
        # Disconnect MT5
        # Release PID lock
        self._release_lock()
        self.state = OrchestratorState.DORMANT

    def _handle_signal(self, signum, frame):
        self._shutdown_requested = True

    # ── Helpers ────────────────────────────────────────────────────

    def _daily_limits_hit(self) -> bool:
        """Circuit breaker: stop trading if daily loss >= 2%."""
        if self.session.trades_today >= self.config["risk"]["max_trades_per_day"]:
            return True
        if abs(self.session.daily_pnl_pct) >= self.config["risk"]["max_daily_loss_pct"]:
            return True
        return False

    def _get_active_kill_zone(self, now: datetime) -> Optional[str]:
        """Return 'london' or 'ny' if now is within a KZ, else None."""
        time_str = now.strftime("%H:%M")
        for kz_name, kz in self.config["market"]["kill_zones"].items():
            if kz["start_utc"] <= time_str <= kz["end_utc"]:
                return kz_name
        return None

    @staticmethod
    def _next_m15_close(now: datetime) -> datetime:
        """Calculate next M15 candle close time."""
        minute = now.minute
        next_close_minute = ((minute // 15) + 1) * 15
        if next_close_minute >= 60:
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return now.replace(minute=next_close_minute, second=0, microsecond=0)
```

### Effort Estimate
3-5 days. The state machine and candle timing logic are straightforward. MT5 connection handling and position reconciliation are the complex parts.

### Risk if Skipped
**Critical.** Without an orchestrator, there is no live trading agent. This is the #1 blocker for Phase 2.

---

## Priority 2: Crash Recovery & State Persistence

### Claude Code Pattern Found

**Files:** `claw-code/src/session_store.py` (36 lines), `claw-code/src/query_engine.py:140-150`

Key patterns:

1. **Session Snapshot on Every Turn**: `persist_session()` saves session_id + all messages + token counts after each bootstrap (runtime.py:134). The trading agent should snapshot after each candle evaluation.

2. **Reconstruct from Snapshot**: `QueryEnginePort.from_saved_session()` (query_engine.py:49-59) reconstructs the engine from a stored JSON file. This maps to "on restart, load last session manifest and reconstruct pipeline state."

3. **Transcript Compaction**: `compact_messages_if_needed()` (query_engine.py:129-132) drops old entries when transcript exceeds threshold. Maps to keeping only the last N candle evaluations in live session memory.

4. **Immutable StoredSession**: `StoredSession` is a frozen dataclass (session_store.py:8-13). The trading agent should similarly use immutable snapshots for crash recovery.

5. **Gap: External state reconciliation.** Claude Code's tools don't have external side effects that persist beyond the session. The trading agent's critical gap is MT5 positions that outlive a crash. This requires a pattern Claude Code doesn't need.

### Adaptation for Trading Agent

The critical scenario: agent crashes AFTER MT5 confirms fill but BEFORE writing trade record. On restart, there's an open position the agent doesn't know about.

**Recovery Protocol:**

```python
# Crash recovery phases (run during bootstrap stage "reconcile_open_positions")

class CrashRecovery:
    """Reconciles agent state with MT5 reality on startup."""

    async def reconcile(self) -> ReconciliationResult:
        """Phase 1: Discover truth (MT5 is source of truth)."""
        mt5_positions = await self.mt5.get_open_positions(symbol="XAUUSD")
        known_positions = self._load_known_positions()  # from trade records

        orphans = []      # MT5 has it, we don't
        phantoms = []     # we have it, MT5 doesn't
        matched = []      # both agree

        for mt5_pos in mt5_positions:
            local = known_positions.get(mt5_pos.ticket)
            if local is None:
                orphans.append(mt5_pos)
            else:
                matched.append((mt5_pos, local))

        for ticket, local in known_positions.items():
            if ticket not in {p.ticket for p in mt5_positions}:
                phantoms.append(local)

        # Phase 2: Resolve discrepancies
        for orphan in orphans:
            # MT5 has a position we don't know about.
            # Reconstruct a TradeRecord from MT5 data.
            # This is safe: the position has SL/TP server-side.
            record = self._reconstruct_trade_record(orphan)
            self._write_trade_record(record)
            alert("RECOVERY", f"Adopted orphan position: ticket={orphan.ticket}")

        for phantom in phantoms:
            # We think we have a position but MT5 doesn't.
            # It closed while we were down. Query MT5 history.
            history = await self.mt5.get_closed_orders(ticket=phantom.ticket)
            if history:
                self._close_trade_record(phantom, history)
                alert("RECOVERY", f"Closed phantom position: {phantom.trade_id}")

        return ReconciliationResult(
            orphans_adopted=len(orphans),
            phantoms_resolved=len(phantoms),
            positions_matched=len(matched),
        )
```

**Checkpoint System:**

```python
# Before any multi-step operation, write an intent record.
# Modeled on claw-code's persist_session() pattern.

class OperationCheckpoint:
    """Write-ahead log for multi-step operations."""

    CHECKPOINT_FILE = Path("knowledge_base/meta/checkpoint.json")

    def begin(self, operation: str, params: dict):
        """Write intent BEFORE starting the operation."""
        atomic_write(self.CHECKPOINT_FILE, {
            "operation": operation,      # "place_order", "modify_sl", "partial_close"
            "params": params,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed": False,
        })

    def complete(self):
        """Mark operation as completed. Safe to delete checkpoint."""
        self.CHECKPOINT_FILE.unlink(missing_ok=True)

    def recover(self) -> Optional[dict]:
        """On startup, check for incomplete operations."""
        if not self.CHECKPOINT_FILE.exists():
            return None
        checkpoint = load_json(self.CHECKPOINT_FILE)
        if checkpoint.get("completed"):
            self.CHECKPOINT_FILE.unlink(missing_ok=True)
            return None
        return checkpoint  # incomplete operation found
```

### Effort Estimate
2-3 days. MT5 position querying is well-documented. The checkpoint system is ~100 lines.

### Risk if Skipped
**High.** Without crash recovery, any agent restart during trading hours could result in untracked positions, missed SL/TP management, or duplicate orders on retry.

---

## Priority 3: Execution Permission System (Component 4)

### Claude Code Pattern Found

**Files:** `claw-code/src/permissions.py` (21 lines), `claw-code/src/tools.py:56-72`, `claw-code/src/runtime.py:169-174`

The permission system is elegant and minimal:

1. **ToolPermissionContext** (permissions.py): A frozen dataclass with `deny_names` (exact match) and `deny_prefixes` (prefix match). The `blocks(tool_name)` method returns True if the tool should be denied.

2. **Pre-execution filtering** (tools.py:56-72): `filter_tools_by_permission_context()` removes blocked tools BEFORE they can be invoked. The tool never reaches execution.

3. **Permission denial tracking** (runtime.py:169-174): Denials are logged as `PermissionDenial(tool_name, reason)` and passed through the turn result. They're auditable but non-blocking to the overall flow.

4. **Inference-based gating** (runtime.py:172-173): Bash tools are gated by default — the system INFERS danger from tool name patterns rather than requiring explicit configuration.

### Adaptation for Trading Agent

The trading agent needs a **three-gate** system. All three must pass for execution:

```
Gate 1: Safety Checks (deterministic, existing)
   ↓ PASS
Gate 2: Execution Permissions (new, from Claude Code pattern)
   ↓ PASS
Gate 3: Circuit Breakers (new, hard blocks)
   ↓ PASS
→ Execute on MT5
```

### Implementation Sketch

```python
# src/components/execution.py

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PermissionTier(Enum):
    AUTO_EXECUTE = auto()       # no confirmation, full audit trail
    EXECUTE_WITH_LOG = auto()   # execute + enhanced logging
    REQUIRE_CONFIRMATION = auto()  # human must approve
    HARD_BLOCK = auto()         # cannot execute regardless


@dataclass(frozen=True)
class ExecutionPermission:
    """Modeled on claw-code ToolPermissionContext."""
    tier: PermissionTier
    reason: str
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionDenial:
    """Modeled on claw-code PermissionDenial."""
    action: str
    tier: PermissionTier
    reason: str


class ExecutionPermissionSystem:
    """Three-gate permission system for live order execution.

    Gate architecture modeled on claw-code's tool permission filtering:
    - ToolPermissionContext.blocks() → our gate_permissions()
    - filter_tools_by_permission_context() → our pre-execution check
    - PermissionDenial tracking → our ExecutionDenial audit trail
    """

    def __init__(self, config: dict):
        self.risk_config = config["risk"]
        self.denials: list[ExecutionDenial] = []

    # ── Gate 1: Safety Checks (existing deterministic checks) ─────

    def gate_safety(self, trade_params: dict, market_state: dict) -> Optional[str]:
        """Returns None if safe, or rejection reason string."""
        # These exist in the primary analyzer already.
        # Moved here as explicit gate for defense-in-depth.
        checks = [
            self._check_rr_ratio(trade_params),
            self._check_sl_minimum(trade_params, market_state),
            self._check_direction_matches_bias(trade_params, market_state),
            self._check_kill_zone_active(trade_params),
        ]
        failures = [c for c in checks if c is not None]
        return "; ".join(failures) if failures else None

    # ── Gate 2: Execution Permissions ─────────────────────────────
    # Modeled on claw-code permissions.py ToolPermissionContext.blocks()

    def gate_permissions(self, action: str, params: dict,
                         account_state: dict) -> ExecutionPermission:
        """Classify action into permission tier.

        Like ToolPermissionContext.blocks() but with tiers instead of binary.
        """
        # HARD BLOCKS — cannot execute regardless
        risk_pct = params.get("risk_pct", 0)
        if risk_pct > 2.0:
            return ExecutionPermission(
                PermissionTier.HARD_BLOCK,
                f"Risk {risk_pct}% exceeds absolute maximum 2%",
            )

        spread = params.get("spread_cents", 0)
        if spread > self.risk_config["max_spread_cents"]:
            return ExecutionPermission(
                PermissionTier.HARD_BLOCK,
                f"Spread {spread}c exceeds maximum {self.risk_config['max_spread_cents']}c",
            )

        daily_loss = abs(account_state.get("daily_pnl_pct", 0))
        if daily_loss >= self.risk_config["max_daily_loss_pct"]:
            return ExecutionPermission(
                PermissionTier.HARD_BLOCK,
                f"Daily loss {daily_loss}% >= {self.risk_config['max_daily_loss_pct']}% limit",
            )

        # REQUIRE CONFIRMATION — human must approve
        if risk_pct > 1.0:
            return ExecutionPermission(
                PermissionTier.REQUIRE_CONFIRMATION,
                f"Risk {risk_pct}% exceeds standard 1% — requires confirmation",
            )

        # AUTO-EXECUTE — safe read-only operations
        if action in ("query_positions", "query_balance", "fetch_prices", "update_kb"):
            return ExecutionPermission(PermissionTier.AUTO_EXECUTE, "read-only operation")

        # EXECUTE WITH LOG — standard trade within parameters
        return ExecutionPermission(
            PermissionTier.EXECUTE_WITH_LOG,
            "Standard trade within all parameters",
        )

    # ── Gate 3: Circuit Breakers ──────────────────────────────────

    def gate_circuit_breaker(self, account_state: dict,
                             session_context: dict) -> Optional[str]:
        """Hard stop conditions. Returns None if clear, or block reason."""
        # Daily loss circuit breaker
        if abs(account_state.get("daily_pnl_pct", 0)) >= self.risk_config["max_daily_loss_pct"]:
            return f"CIRCUIT BREAKER: Daily loss limit hit"

        # Trade count limit
        if session_context.get("trades_today", 0) >= self.risk_config["max_trades_per_day"]:
            return f"CIRCUIT BREAKER: Max trades per day reached"

        # MT5 connection health
        if not account_state.get("mt5_connected", False):
            return "CIRCUIT BREAKER: MT5 connection lost"

        return None

    # ── Combined gate check ───────────────────────────────────────

    def check_all_gates(self, action: str, trade_params: dict,
                        market_state: dict, account_state: dict,
                        session_context: dict) -> tuple[bool, Optional[str]]:
        """Run all three gates. Returns (approved, denial_reason)."""

        # Gate 3 first (cheapest, most critical)
        cb = self.gate_circuit_breaker(account_state, session_context)
        if cb:
            self.denials.append(ExecutionDenial(action, PermissionTier.HARD_BLOCK, cb))
            return False, cb

        # Gate 1
        safety = self.gate_safety(trade_params, market_state)
        if safety:
            self.denials.append(ExecutionDenial(action, PermissionTier.HARD_BLOCK, safety))
            return False, safety

        # Gate 2
        perm = self.gate_permissions(action, trade_params, account_state)
        if perm.tier == PermissionTier.HARD_BLOCK:
            self.denials.append(ExecutionDenial(action, perm.tier, perm.reason))
            return False, perm.reason
        if perm.tier == PermissionTier.REQUIRE_CONFIRMATION:
            self.denials.append(ExecutionDenial(action, perm.tier, perm.reason))
            return False, f"CONFIRMATION REQUIRED: {perm.reason}"

        # All gates passed
        return True, None
```

### Effort Estimate
2-3 days. The permission logic is straightforward. Integration with MT5 execution adds complexity.

### Risk if Skipped
**Critical for live trading.** Without a permission system, a bug in the safety check code has no second line of defense. A single code path failure could place a trade with unlimited risk.

---

## Priority 4: Context Window Management & Session Memory

### Claude Code Pattern Found

**Files:** `claw-code/src/transcript.py` (24 lines), `claw-code/src/query_engine.py:129-132`, `claw-code/src/models.py:28-37`

Three-layer context management:

1. **Budget Tracking** (models.py:28-37): `UsageSummary` tracks cumulative input/output tokens. `add_turn()` returns a new immutable summary — functional pattern prevents accidental mutation.

2. **Budget Enforcement** (query_engine.py:87-90):
   ```python
   if projected_usage.total > max_budget_tokens:
       stop_reason = 'max_budget_reached'
   ```
   The check happens BEFORE the turn executes, not after. Proactive, not reactive.

3. **Transcript Compaction** (transcript.py:15-17):
   ```python
   def compact(self, keep_last: int = 10):
       if len(self.entries) > keep_last:
           self.entries[:] = self.entries[-keep_last:]
   ```
   Simple sliding window — keep the last N entries, drop the rest. No summarization, just truncation.

4. **Compact Trigger** (query_engine.py:129-132): Compaction runs after every `submit_message()` if entries exceed `compact_after_turns` (default 12).

### Adaptation for Trading Agent

The trading agent's context challenge: session memory across M15 candles in a kill zone. A London KZ is ~10 candles (07:00-09:30, M15). The agent needs to remember prior evaluations (e.g., "WAIT — sweep developing on candle 3") without blowing the 60K char MSO budget.

**Design: Sliding Summary Window**

```python
class SessionMemory:
    """Context manager for live trading sessions.

    Modeled on claw-code TranscriptStore with domain-specific compaction.
    """

    MAX_ENTRIES = 6          # Keep last 6 candle summaries (~2,400 chars)
    SUMMARY_MAX_CHARS = 400  # Per-candle summary budget

    def __init__(self):
        self.entries: list[dict] = []
        self.compacted_count: int = 0

    def add_candle_result(self, candle_time: str, decision: str,
                          reasoning_summary: str, key_levels: dict):
        """Add a candle evaluation result to session memory."""
        entry = {
            "candle_time": candle_time,
            "decision": decision,
            "summary": reasoning_summary[:self.SUMMARY_MAX_CHARS],
            "key_levels": key_levels,  # price levels still in play
        }
        self.entries.append(entry)
        self._compact_if_needed()

    def _compact_if_needed(self):
        """Sliding window compaction — keep last N entries.

        Directly from claw-code TranscriptStore.compact().
        """
        if len(self.entries) > self.MAX_ENTRIES:
            dropped = len(self.entries) - self.MAX_ENTRIES
            self.entries[:] = self.entries[-self.MAX_ENTRIES:]
            self.compacted_count += dropped

    def build_context_block(self) -> str:
        """Format session memory for inclusion in prompt."""
        if not self.entries:
            return ""

        lines = ["## Prior Candle Evaluations (This Kill Zone)"]
        for entry in self.entries:
            lines.append(
                f"- {entry['candle_time']}: {entry['decision']} — "
                f"{entry['summary']}"
            )
        return "\n".join(lines)

    def get_active_waits(self) -> list[dict]:
        """Return any WAIT decisions with developing setups."""
        return [e for e in self.entries if e["decision"] == "WAIT"]
```

**Token Budget Enforcement** (from claw-code's proactive check pattern):

```python
class TokenBudget:
    """Proactive token budget — check BEFORE calling Claude, not after.

    Modeled on claw-code QueryEngineConfig.max_budget_tokens.
    """

    def __init__(self, max_chars: int = 60_000):
        self.max_chars = max_chars
        self.static_chars: int = 0    # cached system prompt + D1/H4 context
        self.dynamic_chars: int = 0   # M15 candle data

    def will_fit(self, additional_chars: int) -> bool:
        """Check if adding content will stay under budget.

        Like claw-code's projected_usage check before execution.
        """
        projected = self.static_chars + self.dynamic_chars + additional_chars
        return projected <= self.max_chars

    def remaining(self) -> int:
        return self.max_chars - self.static_chars - self.dynamic_chars
```

### Effort Estimate
1-2 days. The SessionMemory class is simple. Integration with the prompt builder (`build_user_message()`) requires modifying `primary_analyzer_prompt.py`.

### Risk if Skipped
**Moderate.** Without session memory, the agent re-evaluates each candle independently. It can't track developing setups ("sweep started on candle 3, waiting for confirmation"). This reduces signal quality but doesn't create safety risks.

---

## Priority 5: Multi-Agent Redesign (Debate Engine Fix)

### Claude Code Pattern Found

**Files:** `claw-code/src/runtime.py:90-107` (routing), `claw-code/src/execution_registry.py` (registry pattern)

Key insights:

1. **Token-scored routing** (runtime.py:90-107): `route_prompt()` uses token overlap scoring to match prompts to the best handler. This is a **specialization** pattern — different handlers for different task types.

2. **Execution Registry** (execution_registry.py): Commands and tools are registered with responsibilities and executed via a lookup. Each handler has a defined scope.

3. **No adversarial debate pattern found.** Claude Code doesn't use bull/bear/judge. It uses a single agent with tool access. The multi-agent coordination is task dispatch, not adversarial.

4. **The ULTRAPLAN equivalent** in this port is `bootstrap_session()` which orchestrates multiple subsystems. The pattern is: **primary agent does the work → specialized subsystems provide verification**, not adversarial agents arguing.

### Adaptation for Trading Agent

Replace adversarial debate with **expert verification**. This maps to Claude Code's pattern of "primary agent + specialized tool validators" rather than "competing agents."

**New Architecture:**

```
Primary Analyzer (Sonnet, fast, every candle)
    │
    ├─ NO_TRADE → log, done
    ├─ WAIT → log to session memory, done
    │
    └─ CANDIDATE → send to Verification Agent
                   │
                   Verification Agent (Opus, slow, expensive, CANDIDATE only)
                   │
                   ├─ CONFIRM → execute
                   └─ REJECT(reason) → log, done
```

```python
class VerificationAgent:
    """Replaces Bull/Bear/Judge debate with expert structural verification.

    Modeled on claw-code's execution_registry pattern:
    specialized handler with defined scope and responsibility.
    """

    VERIFICATION_PROMPT = """You are a senior institutional risk manager reviewing
a CANDIDATE trade for structural soundness. You are NOT arguing against the trade.
You are checking if the structural evidence supports the thesis.

CHECK THESE SPECIFIC ITEMS:
1. Is the daily bias determination supported by the swing structure? (HH/HL or LH/LL)
2. Is the H1 order block truly unmitigated? (No prior price return into zone)
3. Is the M15 CHoCH genuine or just noise? (Requires displacement — body:wick > 1.5)
4. Is the entry within the OTE zone? (62-79% fib retracement)
5. Are SL/TP levels placed at structural points, not arbitrary numbers?

OUTPUT FORMAT (JSON only):
{
    "verdict": "CONFIRM" | "REJECT",
    "structural_issues": ["specific issue 1", "specific issue 2"],
    "confidence": 50-100,
    "critical_weakness": "the single biggest concern, if any"
}

RULES:
- CONFIRM if all 5 checks pass. Minor concerns go in structural_issues but don't REJECT.
- REJECT only for STRUCTURAL failures (wrong swing count, mitigated OB, no real CHoCH).
- "It could reverse" is NOT a valid rejection reason. Every trade can reverse.
- You must cite specific price levels from the data to support your assessment.
"""

    def __init__(self, config: dict, llm_backend):
        self.model = "claude-opus-4-20250514"  # higher capability for verification
        self.backend = llm_backend
        self.max_tokens = 600

    async def verify(self, candidate: dict, market_state: dict,
                     kb_context: dict) -> dict:
        """Send CANDIDATE to verification agent. Returns verdict dict."""
        user_msg = self._build_verification_request(candidate, market_state, kb_context)
        raw = await self._call(self.VERIFICATION_PROMPT, user_msg)
        return json.loads(strip_json_fences(raw))

    def _build_verification_request(self, candidate, market_state, kb_context) -> str:
        """Package the full context for verification."""
        return json.dumps({
            "candidate_trade": candidate,
            "market_state_summary": {
                "daily_bias": market_state.get("daily_structure"),
                "h4_alignment": market_state.get("h4_structure"),
                "h1_poi": market_state.get("h1_structure"),
                "m15_confirmation": market_state.get("m15_structure"),
            },
            "historical_context": kb_context.get("layer1", {}),
        }, indent=2)
```

**Cost Analysis:**

| Metric | Old (Debate) | New (Verification) |
|--------|-------------|-------------------|
| API calls per CANDIDATE | 3-5 (bull + bear + judge + rebuttals) | 1 (verification only) |
| Calls per NO_TRADE candle | 0 | 0 |
| Model tier | Sonnet (all agents) | Opus (verification only) |
| Expected CANDIDATEs per day | 0-2 | 0-2 |
| Daily cost increase | N/A | ~$0.15-0.30/day (2 Opus calls) |
| False rejection reduction | Baseline | Expected -40% (no generic Bear objections) |

### Effort Estimate
2-3 days. Prompt writing and testing the verification agent. Rip out debate.py or keep it as optional.

### Risk if Skipped
**Moderate.** The debate is currently disabled (net-negative). Without a replacement, valid CANDIDATEs have no second opinion. The primary analyzer alone produced acceptable results, but structural verification catches real errors.

---

## Priority 6: Prompt Template System

### Claude Code Pattern Found

**Files:** `claw-code/src/command_graph.py` (35 lines), `claw-code/src/system_init.py`, `claw-code/src/bootstrap_graph.py` (28 lines)

Patterns:

1. **Categorized organization** (command_graph.py): Commands split into `builtins`, `plugin_like`, `skill_like` categories. Each category loaded from separate sources.

2. **Staged composition** (bootstrap_graph.py): Startup assembled from ordered stages, each contributing its piece to the final state.

3. **Separation of static vs. dynamic** (system_init.py): System init message built from static metadata (trusted flag, command counts) combined with dynamic state.

### Adaptation for Trading Agent

Current: Single 391-line `primary_analyzer_prompt.py` with everything inline.
Target: Modular template system with independently testable/cacheable sections.

```
src/prompts/
├── _assembler.py           # Composition logic
├── sections/
│   ├── persona.py          # Institutional trader persona (static, cacheable)
│   ├── universal_requirements.py  # U1-U7 rules (static, cacheable)
│   ├── ob_retest_criteria.py     # OB1-OB7 (static, cacheable)
│   ├── grading_rubric.py         # A+/A/B+ definitions (static, cacheable)
│   ├── confidence_scoring.py     # Scoring rubric (static, cacheable)
│   ├── output_schema.py          # JSON schema (static, cacheable)
│   ├── token_efficiency.py       # Output rules (static, cacheable)
│   └── anti_hallucination.py     # Data grounding rules (static, cacheable)
├── context_builders/
│   ├── static_context.py   # D1/H4/session levels (cached per session)
│   ├── dynamic_context.py  # M15/H1 current candle (per-candle)
│   └── kb_context.py       # Knowledge base retrieval (per-candle)
├── bull_agent_prompt.py    # (existing, keep)
├── bear_agent_prompt.py    # (existing, keep)
├── judge_prompt.py         # (existing, keep or replace with verification)
└── verification_prompt.py  # (new, for Priority 5)
```

**Assembler:**

```python
# src/prompts/_assembler.py

from typing import Optional
import hashlib

class PromptAssembler:
    """Compose system prompt from modular sections.

    Modeled on claw-code's staged bootstrap_graph pattern:
    each section contributes independently, assembled in order.
    """

    def __init__(self):
        self._sections: list[tuple[str, str]] = []  # (name, content)
        self._cache: dict[str, str] = {}

    def add_section(self, name: str, content: str, cacheable: bool = False):
        """Add a prompt section. Cacheable sections use prompt caching."""
        self._sections.append((name, content))
        if cacheable:
            self._cache[name] = content

    def build_system_prompt(self) -> str:
        """Assemble all sections into final system prompt."""
        return "\n\n".join(content for _, content in self._sections)

    def get_cache_breakpoints(self) -> list[int]:
        """Return char offsets where cache boundaries should be placed.

        For Anthropic prompt caching: static sections get cache_control.
        """
        breakpoints = []
        offset = 0
        for name, content in self._sections:
            offset += len(content) + 2  # +2 for \n\n separator
            if name in self._cache:
                breakpoints.append(offset)
        return breakpoints

    def section_hash(self, name: str) -> str:
        """Hash a section for change detection / A/B testing."""
        content = dict(self._sections).get(name, "")
        return hashlib.sha256(content.encode()).hexdigest()[:12]
```

### Effort Estimate
1-2 days. Refactoring existing monolith into separate files. No logic changes needed.

### Risk if Skipped
**Low.** The monolithic prompt works. This is a maintainability improvement that enables A/B testing of individual sections.

---

## Priority 7: Error Handling for Live Execution

### Claude Code Pattern Found

**Files:** `claw-code/src/query_engine.py:161-169` (structured output retry), `claw-code/src/runtime.py:169-174` (permission denial resolution)

Patterns:

1. **Retry with fallback payload** (query_engine.py:161-169):
   ```python
   for _ in range(self.config.structured_retry_limit):
       try:
           return json.dumps(payload, indent=2)
       except (TypeError, ValueError) as exc:
           last_error = exc
           payload = {'summary': ['structured output retry'], 'session_id': self.session_id}
   ```
   Retry with degraded payload — don't give up, but simplify.

2. **Non-blocking denial tracking** (runtime.py:169-174): Permission denials are collected and reported but don't crash the system. They're logged alongside successful operations.

3. **Stop reason propagation** (query_engine.py:88): Every turn result carries a `stop_reason`. The caller knows WHY it stopped and can react accordingly.

### Adaptation for Trading Agent

**Error Handling Matrix:**

```
┌─────────────────────────┬───────────────────┬──────────────────────────────┐
│ Failure Type            │ System State      │ Recovery Action              │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ MT5 order timeout       │ No position known │ Query positions. If filled,  │
│                         │                   │ adopt. If not, skip candle.  │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ MT5 order rejected      │ No position       │ Log rejection reason.        │
│ (price moved)           │                   │ NO_TRADE this candle.        │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ Order filled, TP/SL     │ Open position,    │ Retry SL/TP with wider      │
│ modification failed     │ no TP/SL          │ tolerance. If still fails,   │
│                         │                   │ close position immediately.  │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ Partial close failed    │ Full position     │ Retry once. If fails, log    │
│                         │ open              │ and let full position run.   │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ MT5 connection lost     │ Position may be   │ CIRCUIT BREAKER. No new      │
│                         │ open              │ trades. Reconnect loop.      │
│                         │                   │ Positions have server-side   │
│                         │                   │ SL — they're protected.      │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ Claude API timeout      │ Mid-evaluation    │ NO_TRADE this candle.        │
│                         │                   │ (Already handled: existing   │
│                         │                   │ retry logic in debate.py)    │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ Claude API rate limit   │ Mid-evaluation    │ Wait retry_after seconds.    │
│                         │                   │ (Already handled)            │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ Agent crash mid-order   │ Unknown           │ Crash recovery on restart:   │
│                         │                   │ reconcile_open_positions()   │
│                         │                   │ (Priority 2)                 │
├─────────────────────────┼───────────────────┼──────────────────────────────┤
│ Double order risk       │ Network timeout + │ NEVER retry an order without │
│ (timeout + retry)       │ unknown fill      │ first querying positions.    │
│                         │                   │ The check_before_retry()     │
│                         │                   │ pattern below.               │
└─────────────────────────┴───────────────────┴──────────────────────────────┘
```

**Critical Pattern: Check-Before-Retry**

```python
async def safe_place_order(self, params: dict) -> OrderResult:
    """Place an order with idempotency protection.

    CRITICAL: Never retry without checking if the first attempt filled.
    This is the #1 risk in automated trading — duplicate positions.
    """
    # Write checkpoint BEFORE attempting (Priority 2 pattern)
    self.checkpoint.begin("place_order", params)

    try:
        result = await self.mt5.send_order(params)
        self.checkpoint.complete()
        return result

    except TimeoutError:
        # DO NOT RETRY. Check if order was filled.
        await asyncio.sleep(2)  # let MT5 process
        positions = await self.mt5.get_open_positions(symbol="XAUUSD")
        recent = [p for p in positions if p.open_time > self._order_start_time]

        if recent:
            # Order DID fill despite timeout. Adopt it.
            self.checkpoint.complete()
            return OrderResult(filled=True, ticket=recent[0].ticket, adopted=True)
        else:
            # Order did NOT fill. Safe to give up (NOT retry).
            self.checkpoint.complete()
            return OrderResult(filled=False, reason="timeout_no_fill")
```

### Effort Estimate
2-3 days. The error matrix is the design work. Implementation is try/except blocks with the check-before-retry pattern.

### Risk if Skipped
**Critical.** Without proper error handling, network timeouts during order placement could result in duplicate positions (double risk) or orphaned positions without SL management.

---

## Priority 8: Logging & Observability Upgrades

### Claude Code Pattern Found

**Files:** `claw-code/src/history.py` (23 lines), `claw-code/src/runtime.py:24-86` (RuntimeSession)

1. **Structured event log** (history.py): `HistoryLog` with `add(title, detail)` — simple, append-only, renders to markdown.

2. **Rich session report** (runtime.py:24-86): `RuntimeSession` captures everything: context, setup, matches, results, stream events, persisted path. Can render to markdown via `as_markdown()`.

3. **Stream events** (query_engine.py:106-127): SSE-like events (`message_start`, `command_match`, `tool_match`, `permission_denial`, `message_delta`, `message_stop`) provide real-time observability.

### Adaptation for Trading Agent

The trading agent already has AlertSystem + SessionLogger. The gaps are: alerting delivery (Telegram) and operational health monitoring.

```python
# src/components/alerting.py

import httpx
from dataclasses import dataclass
from typing import Optional

@dataclass
class TelegramAlert:
    """Real-time alert delivery via Telegram bot."""

    bot_token: str
    chat_id: str
    _client: httpx.AsyncClient = None

    async def send(self, level: str, message: str):
        if self._client is None:
            self._client = httpx.AsyncClient()

        emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🚨"}
        text = f"{emoji.get(level, '📌')} *{level}*\n{message}"

        await self._client.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"},
        )

# Alert triggers:
ALERT_TRIGGERS = {
    "trade_opened": "INFO",
    "trade_closed": "INFO",
    "daily_loss_50pct": "WARNING",    # 50% of daily loss limit
    "daily_loss_75pct": "WARNING",    # 75% of daily loss limit
    "daily_loss_limit": "CRITICAL",   # hit the limit
    "mt5_disconnected": "CRITICAL",
    "api_error_streak": "ERROR",      # 3+ consecutive API errors
    "agent_restart": "WARNING",
    "orphan_position": "CRITICAL",    # crash recovery found orphan
    "circuit_breaker": "CRITICAL",
}
```

**Health Check Endpoint:**

```python
# Add to monitoring.py

class HealthCheck:
    """Lightweight health check for external monitoring."""

    def status(self, orchestrator_state, session_context) -> dict:
        return {
            "status": "healthy" if orchestrator_state.name != "ERROR_RECOVERY" else "degraded",
            "state": orchestrator_state.name,
            "uptime_seconds": self._uptime(),
            "trades_today": session_context.trades_today if session_context else 0,
            "daily_pnl_pct": session_context.daily_pnl_pct if session_context else 0,
            "current_kz": session_context.current_kz if session_context else None,
            "last_candle": session_context.last_candle_time if session_context else None,
            "mt5_connected": True,  # from actual check
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        }
```

### Effort Estimate
1 day for Telegram alerts. 1 day for health check endpoint.

### Risk if Skipped
**Moderate.** Without alerting, you won't know the agent crashed, hit a circuit breaker, or has an orphan position until you manually check. In live trading, minutes matter.

---

## Master Implementation Roadmap

### Phase A: Required Before Going Live

| # | Component | Priority | Effort | Dependencies |
|---|-----------|----------|--------|-------------|
| 1 | **Orchestrator** (state machine + M15 loop) | P1 | 3-5 days | None |
| 2 | **Execution Engine** (MT5 order placement) | P3 (partially) | 3-4 days | MT5 Python API |
| 3 | **Execution Permission System** (3-gate) | P3 | 2-3 days | Execution Engine |
| 4 | **Crash Recovery** (position reconciliation) | P2 | 2-3 days | Execution Engine |
| 5 | **Error Handling Matrix** (check-before-retry) | P7 | 2-3 days | Execution Engine |
| 6 | **Telegram Alerting** | P8 | 1 day | None |

**Total Phase A: 13-19 days**

### Phase B: Should Have for Demo/Paper Trading

| # | Component | Priority | Effort | Dependencies |
|---|-----------|----------|--------|-------------|
| 7 | **Session Memory** (cross-candle context) | P4 | 1-2 days | Orchestrator |
| 8 | **Verification Agent** (debate replacement) | P5 | 2-3 days | None |
| 9 | **Health Check Endpoint** | P8 | 1 day | Orchestrator |
| 10 | **Checkpoint System** (write-ahead log) | P2 | 1 day | Execution Engine |

**Total Phase B: 5-7 days**

### Phase C: Optimization (After Live Validation)

| # | Component | Priority | Effort | Dependencies |
|---|-----------|----------|--------|-------------|
| 11 | **Prompt Template System** | P6 | 1-2 days | None |
| 12 | **Token Budget Enforcement** | P4 | 1 day | Session Memory |
| 13 | **Monitoring Dashboard** (FastAPI) | P8 | 2-3 days | Health Check |

**Total Phase C: 4-6 days**

### Critical Path

```
MT5 API setup
    │
    ├── Orchestrator (P1) ──→ Session Memory (P4)
    │       │
    │       └── Execution Engine (P3) ──→ Permission System (P3)
    │               │                          │
    │               ├── Crash Recovery (P2) ────┘
    │               │
    │               └── Error Handling (P7)
    │
    └── Telegram Alerting (P8)     ← independent, do early

Verification Agent (P5) ← independent, can do anytime
Prompt Templates (P6) ← independent, can do anytime
```

### One-Line Summary

The trading agent has strong AI reasoning (prompts, KB, grading) but no operational skeleton. Claude Code's patterns provide the blueprint for that skeleton: lifecycle management (runtime.py), permission gates (permissions.py), state persistence (session_store.py), context compaction (transcript.py), and structured error propagation (TurnResult.stop_reason). The adaptation is domain-specific (M15 candles, MT5 positions, kill zones) but the architectural patterns transfer directly.
