# EXEC — Production Implementation: OB Limit Order Architecture Fix
# XAUUSD (and all active instruments)

**For:** Claude Code agent with write access to src/
**Task type:** Production code change — CEO-approved (Borhen)
**Effort:** Max — read every file in full before making any edit
**Scope:** Exactly 5 files, zero new files

---

## Research Basis

**Why:** `src/prompts/primary_analyzer_prompt.py` line 150 tells the AI to quote `entry_price = current M15 candle close`. That price is above the OB zone. L2 `entry_in_ob` check requires entry within the zone → rejects 97%+ of signals → 10 trades in 70 days.

**Validated fix (557 XAUUSD setups, Jan–Apr 2026):**
- Unfiltered limit orders at OB zone: 45.5% WR, +45.0R
- Gap ≤ 1.5% filter: **61.4% WR, +82.0R** (+37R vs unfiltered)
- The 1.5–2.0% gap band alone: 12.3% WR on 57 trades (net drag, correctly excluded)
- Breakeven for 1.5R system = 40.0%. Gap ≤ 1.5% = 21pp above breakeven.

---

## Pre-Flight Checklist — Complete Before Touching Code

```bash
pytest tests/ -v --tb=short 2>&1 | tail -5    # record pass count
git status                                      # confirm clean or note state
```

Read these file sections IN FULL before editing:
- `src/prompts/primary_analyzer_prompt.py` lines 140–160
- `src/components/verification.py` lines 401–570
- `src/components/execution.py` lines 1–150
- `src/components/orchestrator.py` lines 363–440 and 740–835
- `config/agent_config.yaml` (full file)

Do not proceed until all reads are complete.

---

## CHANGE 1 — `src/prompts/primary_analyzer_prompt.py`

**Line 150.** Replace exactly:
```
- entry_price: current M15 candle close price
```
With:
```
- entry_price: OB zone entry — ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT (bottom of nearest unmitigated H1 OB). Do NOT use the current candle close price.
```

Nothing else changes in this file.

---

## CHANGE 2 — `src/components/verification.py`

### Step A: Add `_check_gap_ceiling` function

Insert this function between line 444 (end of `_check_entry_in_ob`) and line 446 (start of `_check_sl_beyond_ob`):

```python
def _check_gap_ceiling(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    config: dict,
) -> VerificationCheck:
    """CHECK 7: Current price is within max_gap_pct% of zone entry.

    Prevents limit orders on stale zones where price has run far away.
    Evidence: gap >1.5% band produced 12.3% WR on 57 trades (Jan–Apr 2026).
    Only meaningful after Change 1 (prompt fix) sets entry_price = ob_high.
    """
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("gap_ceiling", "SKIP", "No trade_parameters")

    m15_tf = mso.timeframes.get("M15")
    if not m15_tf or not getattr(m15_tf, "candles", None):
        return VerificationCheck("gap_ceiling", "SKIP", "No M15 candles in MSO")

    current_price = m15_tf.candles[-1].close
    entry_price = tp.entry_price
    direction = tp.direction

    if direction == "LONG":
        gap_pct = (current_price - entry_price) / entry_price * 100
    else:
        gap_pct = (entry_price - current_price) / entry_price * 100

    max_gap_pct = config.get("filters", {}).get("max_gap_pct", 1.5)

    if gap_pct <= max_gap_pct:
        return VerificationCheck(
            "gap_ceiling", "PASS",
            f"Gap {gap_pct:.2f}% ≤ {max_gap_pct:.1f}% ceiling "
            f"(current={current_price:.2f}, zone_entry={entry_price:.2f})",
            mso_value=round(current_price, 2),
            ai_value=round(entry_price, 2),
        )

    return VerificationCheck(
        "gap_ceiling", "FAIL",
        f"Gap {gap_pct:.2f}% > {max_gap_pct:.1f}% ceiling — zone too far "
        f"(current={current_price:.2f}, zone_entry={entry_price:.2f})",
        mso_value=round(current_price, 2),
        ai_value=round(entry_price, 2),
    )
```

### Step B: Wire c7 in `verify_candidate`

After line 546 (`checks.append(c6)`) and before line 548 (the blank line before `log_warnings`), insert:

```python
    # CHECK 7: Gap ceiling — current price within configured % of zone entry
    c7 = _check_gap_ceiling(analysis, mso, config)
    checks.append(c7)
```

The existing `first_fail` loop at line 555 already handles any length of `checks` — no further changes needed.

---

## CHANGE 3 — `src/components/execution.py`

### Step A: Add `PendingLimitIntent` dataclass

Insert after the `TradeState` dataclass ends (before line 53 where `class ExecutionEngine` begins):

```python
@dataclass
class PendingLimitIntent:
    """Pending limit order — checked each M15 candle by the orchestrator.

    Fills when candle.low <= limit_price (LONG) or candle.high >= limit_price (SHORT).
    Expires after expiry_candles M15 candles without fill (default 192 = 48 hours).
    This is candle-level polling, not a native MT5 pending order.
    """
    direction: str
    limit_price: float
    stop_loss: float
    take_profit_1: float
    risk_pct: float
    expiry_candles: int = 192
    candles_elapsed: int = 0
    trade_id: str = ""
    placed_time: str = ""
```

### Step B: Add state to `ExecutionEngine.__init__`

After line 63 (`self.active_trade: Optional[TradeState] = None`), insert:

```python
        self.pending_intent: Optional[PendingLimitIntent] = None
        self._pending_account_balance: float = 0.0
```

Update the import at top of file if needed: `from dataclasses import dataclass, field` is already imported. `Optional` is already imported via `typing`.

### Step C: Add three methods after `open_trade` (after line 147, before line 149 `safe_place_order`)

```python
    def set_limit_intent(
        self,
        trade_params: dict,
        account_balance: float,
        risk_pct_override: float | None = None,
    ) -> PendingLimitIntent:
        """Store a limit order intent. Orchestrator checks each candle for fill."""
        risk_pct = (
            risk_pct_override
            if risk_pct_override is not None
            else self.config.get("risk", {}).get("risk_per_trade_pct", 1.0)
        )
        intent = PendingLimitIntent(
            direction=trade_params["direction"],
            limit_price=trade_params["entry_price"],
            stop_loss=trade_params["stop_loss"],
            take_profit_1=trade_params["take_profit_1"],
            risk_pct=risk_pct,
            trade_id=f"lim_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')}",
            placed_time=datetime.now(timezone.utc).isoformat(),
        )
        self.pending_intent = intent
        self._pending_account_balance = account_balance
        logger.info(
            "Limit intent set: %s %s limit=%.2f sl=%.2f tp=%.2f expires=%d candles",
            intent.direction, self.symbol, intent.limit_price,
            intent.stop_loss, intent.take_profit_1, intent.expiry_candles,
        )
        return intent

    def check_limit_fill(self, candle: dict) -> Optional[TradeState]:
        """Check if candle triggers the pending limit. Returns TradeState if filled."""
        if self.pending_intent is None:
            return None

        intent = self.pending_intent
        intent.candles_elapsed += 1

        if intent.candles_elapsed >= intent.expiry_candles:
            logger.info(
                "Limit intent expired after %d candles: %s",
                intent.candles_elapsed, intent.trade_id,
            )
            self.pending_intent = None
            return None

        triggered = (
            (intent.direction == "LONG" and candle["low"] <= intent.limit_price)
            or (intent.direction == "SHORT" and candle["high"] >= intent.limit_price)
        )

        if not triggered:
            return None

        logger.info(
            "Limit triggered: %s candle=%s low=%.2f limit=%.2f",
            intent.trade_id, candle.get("time", "?"),
            candle.get("low", 0), intent.limit_price,
        )
        saved_trade_id = intent.trade_id
        self.pending_intent = None

        trade_state = self.open_trade(
            trade_params={
                "direction": intent.direction,
                "entry_price": intent.limit_price,
                "stop_loss": intent.stop_loss,
                "take_profit_1": intent.take_profit_1,
                "take_profit_2": 0.0,
                "take_profit_3": 0.0,
                "risk_reward_ratio": 1.5,
            },
            account_balance=self._pending_account_balance,
            risk_pct_override=intent.risk_pct,
        )

        if trade_state:
            # Preserve the limit intent trade_id for record linkage
            trade_state.trade_id = saved_trade_id.replace("lim_", "lim_filled_")

        return trade_state

    def cancel_limit_intent(self, reason: str = "manual") -> None:
        """Cancel active pending limit intent without executing."""
        if self.pending_intent is not None:
            logger.info(
                "Limit intent cancelled (%s): %s", reason, self.pending_intent.trade_id,
            )
            self.pending_intent = None
```

---

## CHANGE 4 — `src/components/orchestrator.py`

Two precise insertions. Read lines 363–440 and 740–835 in full before editing.

### Insertion A: Pending check inside `_process_candle` (after line 401, before line 404)

Current code at lines 399–406:
```python
        try:
            # 1. Ingest live data
            raw_data = ingest_live_data(self.mt5, self.config)

            # 2. Compute MSO
            mso = compute_market_state(raw_data, self.config)
```

After line 401 (`raw_data = ingest_live_data(...)`), INSERT:

```python
            # 1b. Pending limit fill check — runs every candle while intent is active.
            # Emergency stops above (drawdown, consec_losses, canary) already fired.
            # No new setup evaluated while a limit intent is pending.
            if self.execution.pending_intent:
                m15_candles = raw_data.get("candles", {}).get("M15", [])
                if m15_candles:
                    trade_state = self.execution.check_limit_fill(m15_candles[-1])
                    if trade_state:
                        self.session_state["trades_today"] += 1
                        self.session_state[f"trades_{kill_zone}"] = kz_trades + 1
                        self._log_candle("LIMIT_FILLED", trade_state.trade_id, kill_zone)
                        logger.info(
                            "LIMIT FILLED: %s at %.2f",
                            trade_state.trade_id, trade_state.entry_price,
                        )
                        try:
                            self._init_trade_tracking(trade_state)
                        except Exception as e:
                            logger.error("Exit tracking init failed on limit fill: %s", e)
                return  # whether filled or still pending — no new setup this candle
```

The `return` is unconditional: while a limit is pending, no AI call, no prescreen, nothing. This is the correct behavior — we never queue multiple setups simultaneously.

**Verify `kz_trades` is in scope:** It is. Line 388 reads `kz_trades = self.session_state.get(f"trades_{kill_zone}", 0)` before the `try:` block at line 399. The insertion is inside the `try:` block, so `kz_trades` is accessible.

### Insertion B: Replace `open_trade()` call (lines 754–828)

**Step 1:** Find the line that reads `trade_state = self.execution.open_trade(` (line 754).

**Step 2:** Replace the entire block from `# 8. EXECUTE` (line 751) through the closing `else: ... self._log_candle("EXECUTION_FAILED", ...)` (line 828) with:

```python
            # 8. PLACE LIMIT ORDER
            balance = self.mt5.get_account_balance()
            tp = analysis.trade_parameters
            pending = self.execution.set_limit_intent(
                trade_params={
                    "direction": tp.direction,
                    "entry_price": tp.entry_price,
                    "stop_loss": tp.stop_loss,
                    "take_profit_1": tp.take_profit_1,
                    "take_profit_2": tp.take_profit_2,
                    "take_profit_3": tp.take_profit_3,
                    "risk_reward_ratio": tp.risk_reward_ratio,
                },
                account_balance=balance,
                risk_pct_override=effective_risk_pct if corr_adj.adjusted else None,
            )

            if pending:
                self._log_candle(
                    "LIMIT_PLACED", pending.trade_id, kill_zone,
                    extended_kz=False, kz_sub_window=kill_zone,
                )
                logger.info(
                    "LIMIT PLACED: %s %s limit=%.2f sl=%.2f tp=%.2f",
                    pending.trade_id, pending.direction,
                    pending.limit_price, pending.stop_loss, pending.take_profit_1,
                )
                if record:
                    try:
                        record["decision_pipeline"]["final_outcome"] = "LIMIT_PLACED"
                        record["limit_intent"] = {
                            "trade_id": pending.trade_id,
                            "limit_price": pending.limit_price,
                            "stop_loss": pending.stop_loss,
                            "take_profit_1": pending.take_profit_1,
                            "expiry_candles": pending.expiry_candles,
                        }
                        save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                    except Exception as e:
                        logger.error("Trade capture: failed to save limit intent record: %s", e)
            else:
                if record:
                    record["decision_pipeline"]["final_outcome"] = "LIMIT_INTENT_FAILED"
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._log_candle("LIMIT_INTENT_FAILED", "set_limit_intent returned None", kill_zone)
```

**Before replacing:** Read lines 740–760 carefully. Confirm that `effective_risk_pct`, `corr_adj`, `tc_cfg`, `record`, `kill_zone`, and `balance` are all in scope at that point. If any variable name differs from what you see in the file, use the name in the file.

**The shadow entry and `_init_trade_tracking` blocks that follow the original `open_trade` call are removed.** They will fire correctly in Insertion A when the limit fills. Do not keep them here.

---

## CHANGE 5 — `config/agent_config.yaml`

Add a new `filters:` section (or append to existing if already present):

```yaml
filters:
  max_gap_pct: 1.5        # Max % gap between current price and OB zone entry
                          # Validated: gap >1.5% produced 12.3% WR on 57 trades (Jan–Apr 2026)
                          # Set to 999.0 to disable
```

---

## Tests — Write `tests/test_limit_order_flow.py`

```python
"""
Tests for OB limit order flow.
Validates that implementation matches the backtest assumptions from
research/academic_pipeline/results/entry_scenario_analysis_v1.md
and research/academic_pipeline/results/filter_validation_v1.md.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_analysis(entry_price, direction="LONG", tp=None, sl=None):
    analysis = MagicMock()
    analysis.trade_parameters.entry_price = entry_price
    analysis.trade_parameters.direction = direction
    analysis.trade_parameters.stop_loss = sl or (entry_price - 20)
    analysis.trade_parameters.take_profit_1 = tp or (entry_price + 30)
    return analysis

def _make_mso(current_price):
    m15_candle = MagicMock()
    m15_candle.close = current_price
    m15_tf = MagicMock()
    m15_tf.candles = [m15_candle]
    mso = MagicMock()
    mso.timeframes = {"M15": m15_tf}
    return mso

def _make_engine():
    from src.components.execution import ExecutionEngine
    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0)
    config = {"market": {"symbol": "XAUUSD"}, "risk": {"risk_per_trade_pct": 1.0}}
    return ExecutionEngine(mt5, config)

# ── Gap Filter Tests ─────────────────────────────────────────────────────────

def test_gap_ceiling_pass_long():
    """Gap 1.0% below 1.5% ceiling → PASS."""
    from src.components.verification import _check_gap_ceiling
    # ob_high=4421.39, current=4465.60 → gap=(4465.60-4421.39)/4421.39*100=1.0%
    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    mso = _make_mso(current_price=4465.60)
    result = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    assert result.status == "PASS"
    assert "1.0" in result.detail or "Gap" in result.detail

def test_gap_ceiling_fail_long():
    """Gap 2.0% above 1.5% ceiling → FAIL."""
    from src.components.verification import _check_gap_ceiling
    # ob_high=4421.39, current=4509.82 → gap≈2.0%
    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    mso = _make_mso(current_price=4509.82)
    result = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    assert result.status == "FAIL"

def test_gap_ceiling_pass_short():
    """SHORT direction: gap computed as (entry - current) / entry."""
    from src.components.verification import _check_gap_ceiling
    # ob_low=4405.55, current=4384.37 → gap=(4405.55-4384.37)/4405.55=0.48% → PASS
    analysis = _make_analysis(entry_price=4405.55, direction="SHORT")
    mso = _make_mso(current_price=4384.37)
    result = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    assert result.status == "PASS"

def test_gap_ceiling_skip_no_trade_params():
    """No trade_parameters → SKIP."""
    from src.components.verification import _check_gap_ceiling
    analysis = MagicMock()
    analysis.trade_parameters = None
    result = _check_gap_ceiling(analysis, MagicMock(), {})
    assert result.status == "SKIP"

def test_gap_ceiling_skip_no_m15():
    """No M15 candles in MSO → SKIP."""
    from src.components.verification import _check_gap_ceiling
    analysis = _make_analysis(entry_price=4421.39)
    mso = MagicMock()
    mso.timeframes = {}
    result = _check_gap_ceiling(analysis, mso, {})
    assert result.status == "SKIP"

def test_gap_ceiling_configurable_threshold():
    """max_gap_pct=2.0 allows 1.9% gap that 1.5 would reject."""
    from src.components.verification import _check_gap_ceiling
    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    mso = _make_mso(current_price=4505.42)  # ~1.9% gap
    result_strict = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    result_loose  = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 2.0}})
    assert result_strict.status == "FAIL"
    assert result_loose.status == "PASS"

# ── Limit Intent Tests ───────────────────────────────────────────────────────

def test_set_limit_intent_stores_correctly():
    """set_limit_intent stores PendingLimitIntent with correct fields."""
    from src.components.execution import PendingLimitIntent
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    intent = engine.set_limit_intent(params, account_balance=100000.0)
    assert isinstance(intent, PendingLimitIntent)
    assert engine.pending_intent is intent
    assert intent.direction == "LONG"
    assert intent.limit_price == 4421.39
    assert intent.stop_loss == 4401.99
    assert intent.expiry_candles == 192

def test_check_limit_fill_triggers_on_touch():
    """LONG: candle low ≤ limit_price triggers open_trade."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        result = engine.check_limit_fill({"time": "2026-01-07 10:00:00",
                                           "open": 4430.0, "high": 4432.0,
                                           "low": 4421.00, "close": 4428.0})
    assert mock_open.called
    assert result is not None
    assert engine.pending_intent is None  # cleared after fill

def test_check_limit_fill_no_trigger_above():
    """LONG: candle low > limit_price — does not trigger."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    result = engine.check_limit_fill({"time": "t", "open": 4430.0, "high": 4432.0,
                                       "low": 4425.0, "close": 4428.0})
    assert result is None
    assert engine.pending_intent is not None  # still pending

def test_check_limit_fill_expires():
    """After 192 candles without fill, intent expires and returns None."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    non_trigger = {"time": "t", "open": 4500.0, "high": 4502.0,
                   "low": 4498.0, "close": 4500.0}
    result = None
    for _ in range(192):
        result = engine.check_limit_fill(non_trigger)
    assert result is None
    assert engine.pending_intent is None

def test_cancel_limit_intent():
    """cancel_limit_intent clears pending_intent."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)
    assert engine.pending_intent is not None
    engine.cancel_limit_intent(reason="test")
    assert engine.pending_intent is None

def test_short_limit_triggers_on_high():
    """SHORT: candle high ≥ limit_price triggers open_trade."""
    engine = _make_engine()
    params = {"direction": "SHORT", "entry_price": 4405.55,
              "stop_loss": 4426.00, "take_profit_1": 4374.91,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4395.0, "high": 4406.0,
                                           "low": 4393.0, "close": 4394.0})
    assert mock_open.called
    assert result is not None
```

---

## Post-Implementation Verification

Run all five in order. Every check must pass.

### Check 1: Tests
```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
# Expected: original N passing + 10 new tests passing. Zero regressions.
```

### Check 2: Prompt instruction removed
```bash
python -c "
from src.prompts import primary_analyzer_prompt
import yaml
with open('config/agent_config.yaml') as f:
    config = yaml.safe_load(f)
prompt = primary_analyzer_prompt.build_system_prompt(config)
assert 'current M15 candle close' not in prompt, 'FAIL: old instruction still present'
assert 'ob_high' in prompt or 'OB zone entry' in prompt, 'FAIL: new instruction not present'
print('PASS: prompt instruction updated correctly')
"
```

### Check 3: Gap filter importable
```bash
python -c "
from src.components.verification import _check_gap_ceiling, verify_candidate
print('PASS: gap filter importable')
"
```

### Check 4: Limit intent importable
```bash
python -c "
from src.components.execution import ExecutionEngine, PendingLimitIntent
e = ExecutionEngine.__new__(ExecutionEngine)
assert hasattr(ExecutionEngine, 'set_limit_intent')
assert hasattr(ExecutionEngine, 'check_limit_fill')
assert hasattr(ExecutionEngine, 'cancel_limit_intent')
print('PASS: limit intent methods present')
"
```

### Check 5: Exact file diff
```bash
git diff --stat
# Must show exactly 5 files. No extras.
```

---

## Green Light — ALL required before reporting done

- [ ] Pre-flight test count ≥ N (record exact number)
- [ ] Post-implementation: original N tests still pass (zero regressions)
- [ ] 10 new limit order tests pass
- [ ] Check 2 (prompt) PASS
- [ ] Check 3 (gap filter import) PASS
- [ ] Check 4 (limit intent import) PASS
- [ ] `git diff --stat` shows exactly 5 files
- [ ] You read every file section listed in pre-flight IN FULL before editing

---

## Rollback

```bash
git revert HEAD --no-edit
```
Single commit. Single revert. System returns to current behavior immediately.

---

## Report Format

```
PRE-FLIGHT:
  Tests before: N passing
  Git status: clean / X uncommitted files

CHANGES MADE:
  1. primary_analyzer_prompt.py:150 — [old] → [new] (exact text)
  2. verification.py — _check_gap_ceiling added at line X, c7 wired at line Y
  3. execution.py — PendingLimitIntent at line X, 3 methods at lines Y/Z/W
  4. orchestrator.py — pending check inserted after line 401, open_trade replaced at line 754
  5. agent_config.yaml — filters.max_gap_pct: 1.5 added

GREEN LIGHT:
  Tests after: N+10 passing
  Prompt check: PASS/FAIL
  Import checks: PASS/FAIL
  Files changed: N (expected 5)

KNOWN LIMITATIONS / RISKS:
  [anything that couldn't be fully verified or required judgment calls]
```

If any check fails: stop, report what failed, do not mark complete.
