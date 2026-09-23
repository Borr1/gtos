# EXEC — Limit Order Bug Fixes (6 targeted changes)

**For:** Fresh Claude Code agent
**Task type:** Bug fixes only — CEO-approved (Borhen)
**Scope:** 3 files, 6 changes, zero new files
**Do not touch anything else.**

---

## Context

A prior agent implemented OB limit orders across 5 files. A peer review found 6 bugs.
You are fixing those 6 bugs. Read the current state of each file before editing.

---

## Pre-flight

```bash
pytest tests/ -v --tb=short 2>&1 | tail -5   # record passing count
git diff --stat                               # confirm 5 files changed from prior work
```

Read these sections before touching anything:
- `src/components/execution.py` — the `check_limit_fill` method and the `PendingLimitIntent` dataclass
- `src/components/orchestrator.py` — lines 370–410 (emergency stops + try block)
- `src/components/verification.py` — the `_check_gap_ceiling` function
- `tests/test_limit_order_flow.py` — full file

---

## Fix 1 — Clock-time expiry in `check_limit_fill` (Critical)

**File:** `src/components/execution.py`

**Problem:** `check_limit_fill` expires the intent after 192 `candles_elapsed` increments. But it is only called during kill zone candles (~29/day for XAUUSD). 192 ÷ 29 = 6.6 trading days — not the intended 48 hours. A limit placed Monday could fill Friday against a structurally obsolete OB.

**Fix:** Replace the candle-count expiry check with clock-time expiry. Keep `candles_elapsed` incrementing for logging purposes but do not use it as the expiry trigger.

In `check_limit_fill`, replace the `candles_elapsed >= expiry_candles` block with:

```python
        intent = self.pending_intent
        intent.candles_elapsed += 1  # keep for logging only

        # Clock-time expiry — 48 hours from placement regardless of candle count
        placed_dt = datetime.fromisoformat(intent.placed_time)
        if datetime.now(timezone.utc) - placed_dt >= timedelta(hours=48):
            logger.info(
                "Limit intent expired (48h clock, %d KZ candles elapsed): %s",
                intent.candles_elapsed, intent.trade_id,
            )
            self.pending_intent = None
            return None
```

Ensure `timedelta` is imported: add `from datetime import datetime, timezone, timedelta` if `timedelta` is not already imported. Check the existing import line at the top of the file — do not add a duplicate import.

---

## Fix 2 — Move fill check before expiry check (Minor — off-by-one)

**File:** `src/components/execution.py` — same method, `check_limit_fill`

**Problem:** The current code increments `candles_elapsed`, checks expiry, then checks fill. On the 192nd candle (or at clock-expiry), the fill check is skipped. The backtest checked all 192 candles including the last one.

**Fix:** After the clock-time expiry block from Fix 1, the fill check must come next — before any remaining fallback logic. Confirm the method structure is:

```
1. return None if pending_intent is None
2. increment candles_elapsed
3. clock-time expiry check → return None if expired
4. fill condition check → execute if triggered
5. return None if not triggered
```

If the fill check is already after the expiry check in the current code, reorder it. The fill check is the `triggered = (...)` block.

---

## Fix 3 — Cancel intent on emergency stops (Critical — policy)

**File:** `src/components/orchestrator.py`

**Problem:** The portfolio drawdown stop and consecutive losses stop both `return` before the pending fill check runs. With clock-time expiry from Fix 1, the zombie-intent crash is resolved. But a policy problem remains: if a drawdown emergency fires and then recovers within 48h, the intent can still fill against a zone that existed before the crash. This is wrong — after a 4%+ drawdown event, we want to re-evaluate fresh.

**Fix:** Add `self.execution.cancel_limit_intent(reason)` BEFORE the `_log_candle` call in each of the two emergency stop blocks. Find the exact lines in the file — do not guess.

For portfolio drawdown stop:
```python
        if drawdown_pct >= max_drawdown:
            self.execution.cancel_limit_intent("portfolio_drawdown_stop")
            self._log_candle("EMERGENCY_STOP", ...)
            return
```

For consecutive losses stop:
```python
        if consec_losses >= max_consec:
            self.execution.cancel_limit_intent("consecutive_losses_stop")
            self._log_candle("EMERGENCY_STOP", ...)
            return
```

**Do NOT add cancel to the canary block.** The canary is a soft AI drift check — the fill check is mechanical (did price touch the zone?) and does not depend on AI model integrity. The canary block is temporary; clock-time expiry handles the intent naturally.

---

## Fix 4 — Null safety on `max_gap_pct` (Minor)

**File:** `src/components/verification.py` — `_check_gap_ceiling` function

**Problem:** If `agent_config.yaml` has `max_gap_pct: null`, `config.get("filters", {}).get("max_gap_pct", 1.5)` returns Python `None` (not the default 1.5 — the key exists, just with a null value). `gap_pct <= None` raises `TypeError`.

**Fix:** Change the one line that reads `max_gap_pct`:

```python
# Before:
max_gap_pct = config.get("filters", {}).get("max_gap_pct", 1.5)

# After:
max_gap_pct = config.get("filters", {}).get("max_gap_pct") or 1.5
```

---

## Fix 5 — Skip first NY candle guard must not block pending fill (Minor)

**File:** `src/components/orchestrator.py`

**Problem:** `_should_skip_first_ny_candle(kill_zone)` returns early at line ~395, before the `try:` block and the pending fill check. The 13:00 UTC NY candle is never checked for limit fills.

**Fix:** Add `and not self.execution.pending_intent` to the guard condition so the skip only applies when we're evaluating a new setup, not when a limit is pending:

```python
# Before:
        if self._should_skip_first_ny_candle(kill_zone):
            self._log_candle("SKIP_NY_OPEN_CANDLE", ...)
            return

# After:
        if self._should_skip_first_ny_candle(kill_zone) and not self.execution.pending_intent:
            self._log_candle("SKIP_NY_OPEN_CANDLE", ...)
            return
```

Find the exact lines in the file. The condition to add is `and not self.execution.pending_intent`.

---

## Fix 6 — Add missing test: entry_in_ob PASS when entry_price = ob_high

**File:** `tests/test_limit_order_flow.py`

**Problem:** The most critical change in the whole implementation — the prompt fix that sets `entry_price = ob_high` — has zero test coverage. No test verifies that L2 check c5 (`entry_in_ob`) actually PASSES when the AI quotes `entry_price = ob_high`. This is the change that unblocks 97% of previously rejected setups.

**Fix:** Add this test to `tests/test_limit_order_flow.py`:

```python
def test_entry_in_ob_passes_when_entry_is_ob_high():
    """
    Core backtest assumption: when AI quotes entry_price = ob_high,
    _check_entry_in_ob must PASS (entry is at the zone top = within zone).

    This is the prompt fix that unblocks 97% of previously rejected setups.
    Backtest validated 61.4% WR (+82R) assuming this check passes.
    If this test fails, the architecture fix is broken.
    """
    from src.components.verification import _check_entry_in_ob

    analysis = MagicMock()
    analysis.trade_parameters.entry_price = 4421.39   # ob_high
    analysis.trade_parameters.direction = "LONG"
    analysis.trade_parameters.stop_loss = 4401.99

    matched_ob = MagicMock()
    matched_ob.low = 4405.55
    matched_ob.high = 4421.39

    config = {"verification": {"ob_tolerance_pct": 0.2}}
    result = _check_entry_in_ob(analysis, matched_ob, None, config)

    assert result.status == "PASS", (
        f"entry_price=ob_high must PASS entry_in_ob. Got: {result.status} — {result.detail}"
    )
```

---

## Post-implementation verification

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
# Must show: same pass count as pre-flight + 1 new test = N+1 passing, zero regressions
```

```bash
python -c "
from src.components.execution import ExecutionEngine, PendingLimitIntent
from datetime import datetime, timezone, timedelta
# Verify timedelta import didn't break anything
e = ExecutionEngine.__new__(ExecutionEngine)
e.pending_intent = None
print('PASS: execution imports clean')
"
```

```bash
python -c "
from src.components.verification import _check_gap_ceiling
# Verify null fallback works
import unittest.mock as m
a = m.MagicMock(); a.trade_parameters.entry_price = 4421.39; a.trade_parameters.direction = 'LONG'
mso = m.MagicMock(); candle = m.MagicMock(); candle.close = 4450.0
mso.timeframes = {'M15': m.MagicMock(candles=[candle])}
result = _check_gap_ceiling(a, mso, {'filters': {'max_gap_pct': None}})
assert result.status in ('PASS', 'FAIL'), f'null config crashed: {result}'
print('PASS: null gap_pct fallback works')
"
```

---

## Report format

```
PRE-FLIGHT:
  Tests before: N passing

FIXES APPLIED:
  Fix 1 (clock-time expiry): [confirm timedelta imported, old block replaced]
  Fix 2 (fill before expiry): [confirm order is: expiry check → fill check]
  Fix 3 (cancel on emergency stops): [confirm two cancel calls added, canary untouched]
  Fix 4 (null safety): [confirm 'or 1.5' in place]
  Fix 5 (NY candle guard): [confirm 'and not self.execution.pending_intent' added]
  Fix 6 (Q5.5 test): [confirm test added and passes]

POST-FLIGHT:
  Tests after: N+1 passing
  Import check: PASS/FAIL
  Null fallback check: PASS/FAIL
  Files changed: N (expected 3: execution.py, orchestrator.py, test_limit_order_flow.py)
  verification.py changed: yes (Fix 4)

RISKS / NOTES:
  [anything that required judgment or couldn't be verified]
```

Zero tolerance for "it looks right." Quote the exact before/after diff for each fix.
