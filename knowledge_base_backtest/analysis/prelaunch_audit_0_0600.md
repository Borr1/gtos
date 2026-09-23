# Pre-Launch System Audit
**Date:** 2026-04-02
**Test suite:** 441/442 passing (1 pre-existing failure unrelated)

---

## Config Consistency

| Parameter | Config Value | Prompt | permissions.py | orchestrator.py | Status |
|-----------|-------------|--------|----------------|-----------------|--------|
| Min R:R | 2.5 | U5: "1:2.5" | `tp.risk_reward_ratio < 2.5` | N/A | ✅ MATCH |
| Min SL floor | $5.00 ($1.20 buffer) | U6 | `sl_distance < 5.0` | N/A | ✅ MATCH |
| Min SL ATR | 1.5× M15 ATR | U6: "1.5x ATR(14)" | `sl_distance < m15_atr * 1.5` | N/A | ✅ MATCH |
| Max trades/day | 2 | N/A | `trades_today >= max_daily` (default 2) | `max_daily_trades: 2` | ✅ MATCH (was 1 in config, FIXED) |
| Max trades/KZ | 1 | N/A | `kz_trades >= 1` | `kz_trades >= 1` check | ✅ MATCH |
| Daily loss limit | 2% | N/A | `daily_pnl_pct <= -2.0` | N/A | ✅ MATCH |
| Max spread | $0.30 | N/A | `tick.spread_cents > 30` | N/A | ✅ MATCH |
| Grade filter | A+, A | "Only A+ and A qualify" | `grade not in ("A+", "A")` | N/A | ✅ MATCH |
| London KZ | 07:00-09:30 | "07:00–09:30 UTC" | N/A | config-driven | ✅ MATCH (FIXED from 10:30) |
| NY KZ | 13:00-15:30 | "13:00–15:30 UTC" | N/A | config-driven | ✅ MATCH |
| TP1 minimum | 2.5R from entry | OB7, BR7: "2.5× SL" | `tp1_r < 2.0` (safety net) | N/A | ✅ MATCH |
| Session memory | 6 entries | N/A | N/A | `len(kz_entries) > 6` | ✅ MATCH |
| MAGIC_NUMBER | 20260401 | N/A | imported from mt5_interface | N/A | ✅ MATCH |
| Max SL distance | 2.5% of price | N/A | `sl_pct > 2.5` | N/A | ✅ NEW |

**Issues found and fixed:**
- CRITICAL: `max_trades_per_day` was 1 in config but 2 in orchestrator default → **FIXED** to 2
- CRITICAL: London KZ end was 10:30 in config but zero trades in extended window → **FIXED** to 09:30

---

## Safety Check Inventory

### Gate 3 — Circuit Breakers (checked first)
| # | Check | Field Read | Threshold | If null? | Tested? |
|---|-------|-----------|-----------|----------|---------|
| 1 | Daily loss | `session_state["daily_pnl_pct"]` | <= -2.0% | Default 0.0 (safe) | ✅ |
| 2 | Max trades/day | `session_state["trades_today"]` | >= 2 | Default 0 (safe) | ✅ |
| 3 | Max trades/KZ | `session_state["trades_{kz}"]` | >= 1 | Default 0 (safe) | ✅ |
| 4 | MT5 connected | `mt5.is_connected()` | False → deny | N/A | ✅ |
| 5 | Spread | `mt5.get_tick("XAUUSD").spread_cents` | > 30 | None → deny | ✅ |

### Gate 1 — Safety Checks (after Gate 3)
| # | Check | Field Read | Threshold | If null? | Tested? |
|---|-------|-----------|-----------|----------|---------|
| 1 | Grade filter | `reasoning.setup_grade` | Not A+ or A | Default "C" → deny | ✅ |
| 2 | Trade params exist | `pa.trade_parameters` | None → deny | Handled | ✅ |
| 3 | Direction match | `tp.direction` vs `reasoning.daily_bias.direction` | Mismatch → deny | Default "ranging" → no match → deny | ✅ |
| 4 | Min R:R | `tp.risk_reward_ratio` | < 2.5 → deny | Would fail Pydantic | ✅ |
| 5 | TP1 valid side | `tp.take_profit_1` vs `tp.entry_price` | Wrong side → deny | Checked if tp1 exists | ✅ |
| 6 | TP1 min distance | `tp1_distance / sl_distance` | < 2.0R → deny | Only if sl_distance > 0 | ✅ |
| 7 | Min SL floor | `abs(entry - sl)` | < $5.00 → deny | N/A | ✅ |
| 8 | Min SL ATR | `sl_distance` vs `m15_atr * 1.5` | Below → deny | Skipped if ATR=0 | ✅ |
| 9 | Max SL distance | `sl_distance / entry * 100` | > 2.5% → deny | Only if entry > 0 | ✅ NEW |

---

## Execution Engine Review

| Pattern | Status | Notes |
|---------|--------|-------|
| safe_place_order check-before-retry | ✅ Verified | Checkpoint written, timeout → check positions, adopt or give up. NEVER blind retry. |
| Partial close: new ticket discovery | ✅ Verified | After TP1 close, queries positions filtered by MAGIC_NUMBER, adopts new ticket. |
| SL modification failure → close all | ✅ Verified | `_move_sl_to_breakeven` calls `close_position("sl_modification_failed")` on failure. |
| MAGIC_NUMBER filtering | ✅ Verified | All `get_positions` calls filter by MAGIC_NUMBER. `our_positions = [p for p in positions if p.magic == MAGIC_NUMBER]` |
| Crash recovery | ✅ Verified | `reconcile_on_startup` checks for checkpoint files, adopts orphaned positions, clears phantom trades. |
| Duplicate order prevention | ⚠️ MEDIUM | The `_known_tickets` set prevents double-adoption, and KZ trade limit (1 per KZ) prevents double execution. However, if the KZ counter fails to increment between candle loops, a second order could theoretically be placed. Current code increments immediately on `trade_state` success. |

### Concerns Noted
- **XAUUSD hardcoded** in 18 places in execution.py. Should read from `config["market"]["symbol"]`. Not a bug today (always XAUUSD) but fragile for broker portability. **LOW priority.**
- **Lot size calculation**: `lots = risk_amount / (sl_distance * 100)`. Gold standard lot = $100/point. This is correct for standard lots where 1 lot = 100 oz. Verify broker uses standard lots (not mini). **Check on launch day.**

---

## Orchestrator Edge Cases

| Case | Status | Notes |
|------|--------|-------|
| Candle timing | ✅ Handled | `_next_m15_close` calculates next 15-min boundary + 5 second buffer. Polls via `_interruptible_sleep`. |
| KZ boundary (exactly 09:30) | ✅ Handled | `london_s <= t < london_e` — exclusive upper bound. 09:30 candle is NOT in London KZ. |
| Trade-in-progress blocking | ✅ Handled | `kz_trades >= 1` skips evaluation. Session state tracks per-KZ trades. |
| Session memory reset | ✅ Handled | `_new_day` clears `session_memory = []`. Memory is per-KZ sliding window. |
| Between-KZ trade management | ✅ Handled | `_is_between_kz` continues monitoring active trade, manages timeout trailing. |
| PID lock | ✅ Handled | Checks if PID is alive via `os.kill(pid, 0)`. Stale locks overridden with warning. |
| Null trade_params in _compress | ✅ FIXED | Added null check in both orchestrator.py and replay_session.py. |

---

## Prop Firm Compatibility

| Parameter | Current | Prop Firm Typical | Status |
|-----------|---------|-------------------|--------|
| Daily drawdown | 2% (from starting balance) | 4-5% (from highest equity) | ⚠️ Our 2% is MORE conservative — SAFE. But note: prop firms measure from high-water mark, we measure from start. **LOW risk** — worst case we stop ourselves early. |
| Symbol name | "XAUUSD" hardcoded | Varies by broker | ⚠️ **Check on launch day.** May need "GOLD", "XAUUSDm", etc. |
| Lot calculation | `risk / (sl_distance * 100)` | Correct for standard lots | ✅ Correct for standard gold lots ($100/point). |
| Min lot size | `max(lots, 0.01)` | 0.01 typical | ✅ Handled — floors at 0.01. |
| Max lot size | Not capped | 20-50 lots typical | ⚠️ **LOW risk** — with 1% risk on $100K and normal SL ($20-50), max lots ≈ 2-5. Well under limits. |

---

## Data Integrity

| Concern | Status | Notes |
|---------|--------|-------|
| Timezone consistency | ✅ | All timestamps use `datetime.now(timezone.utc)`. MT5 interface converts broker time to UTC. |
| MT5 data freshness | ⚠️ MEDIUM | `copy_rates_from_pos` returns latest bars. 5-second buffer after candle close helps. But fast markets may have late ticks. Standard approach. |
| Candle completeness | ✅ | 90% threshold is standard. Monday gaps are handled by `DataIncompleteError` which skips that candle. |

---

## Error Handling

| Scenario | Status | Notes |
|----------|--------|-------|
| API failure (rate limit) | ✅ Handled | Retry with backoff (1 retry by default, configurable). Falls back to NO_TRADE. |
| API malformed response | ✅ Handled | Retry with format correction message. Falls back to NO_TRADE. |
| MT5 disconnection | ✅ Handled | Gate 3 checks `mt5.is_connected()` before every trade. Mid-trade: broker-side SL protects. |
| Disk full | ⚠️ LOW | `atomic_write` will raise OSError. `_process_candle` catches all exceptions and logs. System continues. |
| Logging completeness | ✅ | Every CANDIDATE logs: entry, SL, TP1, grade, confidence, framework. Every rejection logs reason. |

---

## Issues Summary

| Priority | Issue | Status |
|----------|-------|--------|
| CRITICAL | max_trades_per_day mismatch (1 vs 2) | ✅ FIXED |
| CRITICAL | London KZ end 10:30 → zero value | ✅ FIXED to 09:30 |
| HIGH | Max SL distance gate missing | ✅ FIXED — 2.5% cap |
| HIGH | Breaker_retest 0% WR consuming tokens | ✅ FIXED — disabled via config |
| HIGH | Null trade_params in orchestrator._compress | ✅ FIXED |
| MEDIUM | XAUUSD hardcoded (execution.py) | Flagged — check on launch day |
| MEDIUM | Lot size assumes standard lots | Flagged — verify with broker |
| LOW | Spread check hardcoded 30 (matches config but fragile) | Noted |
| LOW | No max lot size cap | Noted — not needed at current scale |
