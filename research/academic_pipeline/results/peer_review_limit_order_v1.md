# Peer Review: OB Limit Order Production Implementation
**Reviewer:** Independent Claude Code agent (Sonnet 4.6)
**Date:** 2026-04-13
**Files reviewed:** primary_analyzer_prompt.py, verification.py (L401–L619), execution.py (L54–L270), orchestrator.py (L363–L430, L750–L830), config/agent_config.yaml, tests/test_limit_order_flow.py
**Status of reading:** All 5 changed files read in full via bash line reads. Evidence cited by line number throughout.

---

## Section 1: Backtest-to-Production Fidelity

### Q1.1 — Entry fill condition match
**PASS.**

`execution.py:217–218`:
```python
triggered = (
    (intent.direction == "LONG" and candle["low"] <= intent.limit_price)
    or (intent.direction == "SHORT" and candle["high"] >= intent.limit_price)
)
```
Matches the backtest Scenario A fill logic exactly: LONG fills when `candle.low <= zone_entry (ob_high)`, SHORT fills when `candle.high >= zone_entry (ob_low)`.

---

### Q1.2 — 192-candle expiry: off-by-one
**FAIL — 1 candle short.**

`execution.py:206–218` (order of operations):
```python
intent.candles_elapsed += 1                          # increments FIRST
if intent.candles_elapsed >= intent.expiry_candles:  # then checks expiry
    self.pending_intent = None
    return None
triggered = (...)                                     # fill check NEVER reached on call 192
```

Trace: call 191 → `candles_elapsed = 191`, `191 >= 192` → False → fill check runs. Call 192 → `candles_elapsed = 192`, `192 >= 192` → True → expires without attempting fill. Effective check window: **191 candles**, not 192. The backtest used 192.

The test at `test_limit_order_flow.py:151–154` confirms this behavior (loops 192 times, last call expires) but validates the current implementation, not the backtest spec. The test is internally consistent but off-by-one vs the research basis.

**However, this off-by-one is the least of the expiry problems. See Q1.5 and Q2.6 for a far larger issue.**

---

### Q1.3 — Zone risk calculation: confirmed design difference
**ACKNOWLEDGED — not a bug, expected behavior.**

Production uses AI-generated SL (swing-low based). Backtest Scenario A used mechanical `ob_low * 0.999` for SL. These are different risk measurements. Impact:
- If AI SL is wider than `ob_low * 0.999` → fewer lots placed per trade, smaller R per winner.
- If AI SL is tighter → higher probability of SL being hit before TP.

No data exists to quantify this gap. It is a known difference, and the peer review cannot resolve it without a paired comparison run. Flag for monitoring: track live SL distance vs ob_low*0.999 on first 20 fills to measure the divergence.

---

### Q1.4 — Gap filter definition match
**PASS.**

Backtest: `gap_pct = (market_price_at_rejection - ob_high) / ob_high * 100`
Production (`verification.py:470`): `gap_pct = (current_price - entry_price) / entry_price * 100`

With the prompt fix (`entry_price = ob_high`), `entry_price` in production equals `ob_high` in the backtest. `current_price = m15_tf.candles[-1].close` equals the last M15 close at evaluation time — the same quantity as `market_price_at_rejection` (the candle close that was being evaluated). Formulas are numerically equivalent. Both use `ob_high` as denominator.

---

### Q1.5 — Kill-zone-only fill check vs backtest all-candle fill check
**FAIL — severe structural mismatch.**

Production: `check_limit_fill` is called only from `_process_candle` (`orchestrator.py:409`), which is only called when `_get_active_kill_zone(now)` returns non-None (main loop `orchestrator.py:317`).

Between kill zones (`orchestrator.py:323`): only `_check_trade_and_capture()` runs. No fill check.  
After kill zones (`orchestrator.py:336`): same.

**Kill zone candles per day (XAUUSD):**
- London 07:00–10:30: 14 M15 candles
- NY 13:00–17:00, first candle skipped: 15 M15 candles
- Total: **29 kill zone candles/day**

Total M15 candles per day: 96. Kill zone coverage: 29/96 = 30%.

The backtest checked all 192 forward candles (48h × 2 = 192). Production checks **29 per day ≈ 60 per 48-hour period** — 31% of what the backtest checked.

**Fill rate impact:** The backtest's 59.6% fill rate was computed against all 192 forward candles. Fills that occurred outside kill zones (roughly 70% of candles) will never trigger in production. Production fill rate will be materially below 59.6%. The +82R total R projection from the backtest cannot be assumed to apply in production.

---

## Section 2: State Machine Correctness

### Q2.1 — Double-intent prevention
**PASS — protected via control flow, not explicit guard.**

`set_limit_intent` (`execution.py:170–198`) has NO guard checking whether `pending_intent` is already set. However, the orchestrator makes it structurally impossible to call `set_limit_intent` while `pending_intent` is active:

`_process_candle` (`orchestrator.py:406–413`):
```python
if self.execution.pending_intent:
    ...
    return  # whether filled or still pending — no new setup this candle
```

The function returns early before reaching `set_limit_intent` at line 775. Protection is via control flow. This is correct but fragile — any future code path that bypasses `_process_candle` could double-set intents silently. A defensive guard in `set_limit_intent` would be safer.

---

### Q2.2 — `kz_trades` guard interaction
**PARTIAL FAIL — `skip_first_ny_candle` fires before pending check.**

`orchestrator.py` guard order:
1. `portfolio_drawdown >= max` → return (line 374)
2. `consecutive_losses >= max` → return (line 381)
3. `canary_blocked` → return (line 386)
4. `kz_trades >= 1` → return (line 389)
5. `_should_skip_first_ny_candle` → return (line 394–397)  ← **BEFORE pending check**
6. `ingest_live_data()`
7. **pending fill check** (line 406)

For XAUUSD: `skip_first_ny_candle: true` (`agent_config.yaml:216`). The NY 13:00 UTC candle is skipped **before the pending check fires**. A pending limit intent is NOT checked on the 13:00 candle. This means:
- One fill opportunity per day is missed for XAUUSD.
- The NY open candle may be the highest-liquidity candle in the kill zone — the most likely time to see a swift OB retest.

Minor in impact (1 candle/day), but it is a logic bug: the skip rule was designed to prevent **new setups** from being entered at 13:00, not to prevent limit fill checks. Fill checks should be candle-type-agnostic.

For `kz_trades >= 1` interaction: if a limit fills (kz_trades becomes 1), subsequent candles hit the kz_trades guard and return before the pending check. This is **correct** — once filled, no further fill check is needed.

---

### Q2.3 — Active trade + pending intent conflict
**PASS — cannot occur simultaneously in normal flow.**

`check_limit_fill` (`execution.py:230`) sets `self.pending_intent = None` BEFORE calling `open_trade`. So at the moment `active_trade` is set, `pending_intent` is already None. The two cannot be simultaneously active.

If `open_trade` fails (returns None), `pending_intent` is already cleared. The intent is permanently lost — no retry, no restore. This is arguably acceptable (fail-safe), but means a failed MT5 execution silently drops the intent with no recovery path.

`_check_trade_and_capture` (`orchestrator.py:1156`): only checks `active_trade`. Never touches `pending_intent`. No conflict possible.

---

### Q2.4 — Canary block interaction
**CRITICAL BUG — zombie intent.**

`orchestrator.py:384–387`:
```python
if self.session_state.get("canary_blocked"):
    self._log_candle("CANARY_BLOCKED", "model drift detected — skipping", kill_zone)
    return
```

This fires **before** the pending fill check at line 406. When canary is blocked:
1. `check_limit_fill` is never called
2. `intent.candles_elapsed` is never incremented
3. The intent **never expires** — it is frozen at its current `candles_elapsed` value
4. On the next candle, canary check fires again → same result

If the canary remains blocked (it requires manual intervention to clear per CLAUDE.md operational behavior), the pending intent becomes **immortal**. It cannot fill, cannot expire, and **blocks all new setup evaluation** (the pending check at line 406 returns early before any MSO evaluation). The system enters a stuck state where no trades can be placed — not the original intent, not a new one.

**Fix required:** Call `self.execution.cancel_limit_intent("canary_blocked")` at line 386, before returning.

---

### Q2.5 — Emergency stop interaction
**CRITICAL BUG — zombie intent + stale fill risk.**

Both emergency stop blocks (`orchestrator.py:371–382`) fire before the pending fill check. Identical problem to Q2.4:
- `candles_elapsed` never increments while stop is active
- Intent never expires
- System is stuck: no fills, no new setups

**Additional risk:** When the emergency stop clears (e.g., drawdown recovers), the frozen intent resumes from its stale `candles_elapsed`. If the stop persisted for 2+ days, the intent now points to an OB zone identified several days ago under different market conditions. On the first candle after stop clears, `check_limit_fill` runs again — and if price happens to touch the old zone, it fills at market. This is a **stale structure trade** placed immediately after an emergency stop event.

**Fix required:** Call `self.execution.cancel_limit_intent("emergency_stop")` in both emergency stop blocks (lines 374 and 381).

---

### Q2.6 — 192-candle window is NOT 48 hours in production
**CRITICAL BUG — stale zone fills up to 6+ trading days after placement.**

`check_limit_fill` is only called during kill zone candles (~29/day for XAUUSD). The `candles_elapsed` counter only increments inside `check_limit_fill`. Therefore:

```
192 kill zone candles ÷ 29 KZ candles/day = 6.6 trading days ≈ 1.3 calendar weeks
```

`_new_day()` (`orchestrator.py:1794–1815`) resets `self.session_state` including `trades_{kill_zone}` and `trades_today`. It does NOT touch `self.execution.pending_intent`. Intents persist across day boundaries.

**Scenario:** OB retest setup identified Monday 07:15 UTC. Limit placed at ob_high. Price never touches zone all week. The intent is still active the following Tuesday (6+ trading days later). By then:
- New BOS events may have invalidated the original H1 OB
- Market regime may have reversed
- The original CHoCH/BOS that triggered the setup may be structurally obsolete

If price then wicks to the old `ob_high`, the intent fires — executing at market with a structurally stale setup. This is the opposite of the precision the OB-retest edge relies on.

**The backtest assumed a 48-hour calendar window.** The implementation delivers a ~1.3 calendar week window.

**Fix required:** Replace candle-count expiry with clock-time expiry. `PendingLimitIntent.placed_time` already exists as a string field. Change `check_limit_fill` to also check:
```python
from datetime import datetime, timezone, timedelta
placed = datetime.fromisoformat(intent.placed_time)
if datetime.now(timezone.utc) > placed + timedelta(hours=48):
    # expire
```
Keep `candles_elapsed` for logging but not for expiry gate.

---

## Section 3: Execution Safety

### Q3.1 — Actual fill price vs limit price
**ACKNOWLEDGED — known slippage risk, not a code bug.**

When `check_limit_fill` triggers, `open_trade` uses `tick.ask` (current market price) as actual execution price (`execution.py:87–88`):
```python
entry_price = tick.ask if direction == "LONG" else tick.bid
sl_distance = abs(entry_price - sl)
```

The M15 candle close and the `tick.ask` at the moment of execution may differ. Worst case for XAUUSD: candle wicks to ob_high (triggering fill) but closes near candle open — at candle close, `tick.ask` = candle.close >> ob_high.

**Quantification:** Avg zone risk = 25.24 pts (from backtest data). At 10 pt slippage, effective SL distance = 35.24 pts — 40% wider than intended. This shifts R downward. Not a crash-causing bug, but a P&L degradation that should be tracked.

**Monitoring metric to add:** Log `slippage = abs(tick.ask - intent.limit_price)` at every fill.

---

### Q3.2 — SL distance used for position sizing
**ACKNOWLEDGED — position undersizing on slippage fills.**

`sl_distance = abs(entry_price - sl)` where `entry_price = tick.ask` (line 88). If `tick.ask` > `intent.limit_price`, SL distance is larger than intended, resulting in fewer lots. At 5 pt slippage on a 25 pt zone: SL distance = 30 pts → 20% fewer lots than intended. Conservative bias (not incorrect direction), but deviates from backtest sizing assumptions.

---

### Q3.3 — `"entry_price": intent.limit_price` in open_trade call is dead code
**CONFIRMED.**

`check_limit_fill` (`execution.py:235`) passes `"entry_price": intent.limit_price` to `open_trade`. Inside `open_trade` (`execution.py:87`): `entry_price = tick.ask if direction == "LONG" else tick.bid`. The passed `trade_params["entry_price"]` is never read — execution always uses `tick.ask/bid`. The parameter exists in the dict but affects nothing. It is dead code that creates misleading impression that limit_price drives execution. `TradeState.entry_price` is set to `result.price` (actual MT5 fill price, not limit_price).

---

### Q3.4 — No slippage guard on spike fill
**FAIL — gap that should be addressed before live with real capital.**

The system currently has no max-slippage guard before executing on a limit trigger. A spike candle that wicks to ob_high and fully reverses to close 20+ pts above will:
1. Trigger `check_limit_fill` (candle.low <= intent.limit_price → True)
2. Call `open_trade` with `tick.ask` = candle.close ≈ spike close

At candle.close after a full spike reversal, `tick.ask` may be 15–30 pts above `intent.limit_price`. For XAUUSD with avg zone risk 25 pts, this means entry slippage could equal the entire initial SL buffer. The trade would need to reverse back to ob_high just to break even on the SL side.

**Not a crash, but a systematic R erosion on spike candles.** Should be added: `if abs(tick.ask - intent.limit_price) > max_slippage_pts: cancel and log`.

---

## Section 4: Gap Filter Correctness

### Q4.1 — Filter ordering
**PASS — ordering is correct.**

c5 (`entry_in_ob`): checks `zone_low - tol <= entry <= zone_high + tol`. With `entry = ob_high = zone_high`, this evaluates to `zone_high <= zone_high + tol` → always True. c5 always passes for valid prompt-fixed setups. c7 (`gap_ceiling`) catches the orthogonal condition: price has run far above the zone since the zone was formed.

There is no scenario where c5 fails but c7 should have caught it first — they measure different things. Ordering is logically sound.

---

### Q4.2 — Negative gap edge case
**PASS.**

`verification.py:470`: `gap_pct = (current_price - entry_price) / entry_price * 100` (LONG).  
If `current_price < entry_price`: gap_pct is negative.  
Check: `gap_pct <= max_gap_pct` → `negative <= 1.5` → True → PASS.

Correct behavior. Price below zone entry means limit would have filled on this or a prior candle. The filter correctly passes this case.

---

### Q4.3 — `max_gap_pct: null` config crash
**FAIL — latent crash.**

`config.get("filters", {}).get("max_gap_pct", 1.5)` returns `None` if `filters.max_gap_pct` is explicitly set to `null` in YAML (the Python default only applies when the key is absent, not when it's present with a null value).

Then `gap_pct <= None` raises `TypeError: '<=' not supported between instances of 'float' and 'NoneType'`.

Current `agent_config.yaml:41` sets `max_gap_pct: 1.5` — not null — so this is latent, not active. But one YAML edit away from crashing verification. Fix: `max_gap_pct = config.get("filters", {}).get("max_gap_pct") or 1.5`.

---

## Section 5: Tests

### Q5.1 — test_gap_ceiling_pass_long: arithmetic verification
**PASS.**

`(4465.60 - 4421.39) / 4421.39 * 100 = 44.21 / 4421.39 * 100 = 0.9997% ≈ 1.00%`.  
Formatted: `f"{0.9997:.2f}"` = `"1.00"`. Assertion: `"1.0" in "Gap 1.00% <= 1.5% ceiling ..."` → True. Correct.

---

### Q5.2 — test_check_limit_fill_expires: boundary correctness
**IMPLEMENTATION-CONSISTENT but off-by-one vs backtest.**

Test calls `check_limit_fill` 192 times. Call 192: `candles_elapsed` increments to 192, `192 >= 192` → expires without fill check. Test correctly validates the current implementation.

However: the fill check is attempted on calls 1–191 (191 candles), not 192 as the backtest specified. The test passes but confirms the off-by-one from Q1.2. If the intent is to match the backtest exactly, the expiry condition should be `> expiry_candles` (strict greater-than), allowing the fill check to run on call 192 before expiring. The test would then need to call 193 times to confirm expiry.

---

### Q5.3 — Missing test: `check_limit_fill` with `pending_intent = None`
**MISSING.**

No test verifies that `check_limit_fill(candle)` returns `None` immediately when `pending_intent is None`. This is the guard at `execution.py:202–203`. While this is the simplest path, it is called by the orchestrator on every kill zone candle if `pending_intent` is active (meaning None is the success path when no intent exists). Should be tested.

---

### Q5.4 — Missing test: `max_gap_pct = null` raises TypeError
**MISSING.**

No test for `config = {"filters": {"max_gap_pct": None}}`. The bug from Q4.3 is untested. Add test asserting this raises `TypeError` (or add the config fix and test the fixed behavior).

---

### Q5.5 — Missing test: c5 passes when `entry_price = ob_high` (MOST CRITICAL)
**MISSING — highest priority.**

Change 1 (prompt fix) is the root change that makes everything else meaningful. Without `entry_price = ob_high`, the gap filter is meaningless, and limit orders would use the wrong level.

There is no test verifying that with `entry_price = ob_high`, `_check_entry_in_ob` (c5) returns PASS. Previously, this check FAILED when entry = ob_high (the original bug). After the fix, it must PASS.

This is the single most important test to add. If the prompt change is ever reverted or drifts, this test would catch it. Its absence means the most critical backtest precondition has no automated verification.

**Suggested test:**
```python
def test_entry_in_ob_passes_when_entry_equals_ob_high():
    """Prompt fix: entry_price = ob_high must pass c5 (not fail as it did before)."""
    from src.components.verification import _check_entry_in_ob
    from unittest.mock import MagicMock
    ob_high, ob_low = 4421.39, 4408.25
    ob = MagicMock(); ob.high = ob_high; ob.low = ob_low
    analysis = MagicMock()
    analysis.trade_parameters.entry_price = ob_high  # THE PROMPT FIX
    analysis.trade_parameters.direction = "LONG"
    result = _check_entry_in_ob(analysis, ob, None, config={})
    assert result.status == "PASS", f"entry=ob_high must PASS c5, got {result.status}: {result.detail}"
```

---

## Section 6: What the Research Does NOT Guarantee

### Q6.1 — February dominance and realistic base case
Feb 2026 contributed +64.5R of +82.0R total = **79% of all R in 3 months**.

Monthly breakdown:
- January: +3.2R (approx, from remaining R after Feb/Mar)
- February: +64.5R (bull trend month — gold rally)
- March: negative (39.1% WR even after gap filter)
- April 1–10: small residual

Excluding February outlier: (+82R – +64.5R) / 2.3 months = **+7.6R/month average**, which includes a losing month. This is the realistic base case. The +82R headline is not representative of a typical operating month. Do not budget or evaluate performance against +82R/quarter as an expectation.

---

### Q6.2 — AI SL vs mechanical SL (known data gap)
Explicitly documented as a design difference. No quantification available without a live-vs-mechanical SL comparison study. Monitor: log `ob_low * 0.999` alongside AI-quoted SL for every CANDIDATE evaluation. After 30 fills, compute average SL-distance ratio (AI/mechanical).

---

### Q6.3 — Gap filter is in-sample validated only
The 61.4% WR at ≤1.5% gap was **discovered and validated on the same Jan–Apr 2026 XAUUSD dataset**. No out-of-sample period exists. The filter could be capturing regularities specific to the 2026 XAUUSD bull market (clean trend, consistent OB retests) that don't generalize to ranging or bear conditions.

Implication: treat +61.4% WR as a hypothesis, not a confirmed live-trading edge, until 50+ production fills are accumulated. SPRT monitoring applies.

---

### Q6.4 — March-like drawdown: limited circuit breaker
March 2026 WR = 39.1% after gap filter — below the 40% breakeven. Current protection mechanisms:
- H29: reduces risk to 0.5% at 8% DD (slow response)
- SPRT: kills instrument at statistical threshold (slow by design)
- max_consecutive_losses = 5 (fires at 5 consecutive losses — possibly too late in a March regime)

There is **no fast-response regime filter**. If the system enters a March-like environment (ranging/declining gold in bear trend), it will accumulate small losses before any circuit breaker fires. The gap filter does not protect against this — it only filters setups by entry gap, not by market regime quality.

---

## Final Verdict

```
PRODUCTION READINESS VERDICT
=============================
Overall: NOT READY

Critical issues (block deployment — must fix before go-live):

CRITICAL-1: Zombie intent on emergency stops and canary block [Q2.4, Q2.5]
  Files: orchestrator.py:374, :381, :386
  Bug: _process_candle returns early at emergency stops and canary block BEFORE
       the pending fill check. candles_elapsed never increments. Intent never
       expires. System enters a stuck state: no fills, no new setups, no expiry.
       When stop clears, stale intent can fill immediately on a different day.
  Fix: add self.execution.cancel_limit_intent("drawdown_stop") at line 374,
       self.execution.cancel_limit_intent("consec_loss_stop") at line 381,
       self.execution.cancel_limit_intent("canary_blocked") at line 386.

CRITICAL-2: 192 kill-zone-candles ≠ 48 hours → stale zone fills after 6+ trading days [Q2.6]
  Files: execution.py:54–80, orchestrator.py:406–413, :1794–1815
  Bug: candles_elapsed increments only during kill zone candles (~29/day XAUUSD).
       192 kill zone candles ≈ 6.6 trading days ≈ 1.3 calendar weeks. Intents
       persist across _new_day() resets. A limit placed Monday can fill the
       following Wednesday against a structurally obsolete H1 OB.
       Backtest assumed 48-hour calendar window.
  Fix: add clock-time expiry in check_limit_fill using intent.placed_time:
       if datetime.now(UTC) > datetime.fromisoformat(intent.placed_time) + timedelta(hours=48): expire
       Keep candles_elapsed for logging only.

Non-critical issues (deploy and monitor — acceptable for demo phase):
- CRITICAL-2a: Off-by-one on candle expiry (191 candles checked, not 192) [Q1.2]
  Fix: change >= to > in check_limit_fill expiry check (expiry_candles → >)
- Q3.1/Q3.2: Slippage on spike fill; position undersized by 20–40% at 5–10 pt slippage
  Monitor: log slippage = abs(tick.ask - intent.limit_price) on every fill
- Q3.3: "entry_price": intent.limit_price in check_limit_fill → open_trade call is dead code
  (cosmetic, does not affect behavior)
- Q3.4: No max-slippage guard — spike candle fills at market after full wick recovery
  Add before go-live with real capital: cancel intent if tick.ask > limit + max_slippage
- Q4.3: max_gap_pct: null in config crashes with TypeError
  Fix: use `or 1.5` instead of default argument
- Q2.2: skip_first_ny_candle fires before pending check — NY 13:00 candle not checked for fills
  Minor (1 candle/day for XAUUSD), but incorrect logic — skip should not block fill checks

Tests missing (flag for follow-up):
- Q5.3: test check_limit_fill(candle) when pending_intent is None → returns None
- Q5.4: test max_gap_pct: null raises TypeError (or fix and test the fix)
- Q5.5: *** HIGHEST PRIORITY *** test that c5 (entry_in_ob) PASSES when entry_price = ob_high
         (validates the prompt fix — the root change; currently has zero test coverage)

Research gaps acknowledged (known, not bugs):
- Q6.1: Feb 2026 = 79% of all R (+64.5R of +82R). Realistic typical month ≈ +7.6R (ex-Feb).
- Q6.2: AI SL vs mechanical ob_low*0.999 — impact unknown, no comparison data.
- Q6.3: Gap filter in-sample only on Jan–Apr 2026 XAUUSD bull market — not validated OOS.
- Q6.4: No fast-response circuit breaker for March-like bear/ranging regimes.

Recommended monitoring after deployment (post critical-fix):
1. Log slippage (abs(tick.ask - intent.limit_price)) on every fill. Alert if avg > 10 pts.
2. Log intent lifetime (candles_elapsed and clock hours) on every fill or expiry.
3. Log AI SL distance vs ob_low*0.999 on every CANDIDATE evaluation (parallel fields).
4. Track fill rate in production vs backtest 59.6% (expected lower — kill-zone-only).
5. After 30 fills: run SPRT on 61.4% WR hypothesis (p0=0.40, p1=0.55, α=β=0.05).
```

---

*Review complete. Two critical bugs identified, both requiring code fixes before production deployment. Neither is a prompt issue — both are in the orchestrator/execution layer.*
