# Session 16 Handoff — OB Limit Order Architecture
**Date:** April 13, 2026 (evening session)
**Branch:** main (all changes pushed)
**Key commits:**
- `0f2dbd7` — research: T7 remainder + L2 rejection + entry scenario + filter validation
- `536c529` — feat: OB limit order architecture (entry_price fix, gap ceiling, 48h clock expiry, cancel on stops)
- `d18daf2` — data: live state updates Apr 13
- Final canary fix committed after this handoff (see below)

---

## What We Did and Why

### The Root Problem

The system was executing ~10 trades in 70 live days despite ~17/month expected frequency. Investigation revealed the cause: L2 check 5 (`entry_in_ob`) was rejecting nearly 100% of CANDIDATE setups.

**Root cause:** `primary_analyzer_prompt.py` line 150 told the AI to quote `entry_price: current M15 candle close price`. Since price was already above the OB zone by the time the AI evaluated, `entry_price > ob_high`, and the `entry_in_ob` check failed every time.

**Proof:** 557 `entry_in_ob` rejections in the simulation log (Jan–Apr 2026 XAUUSD).

---

## The Research (before any code change)

Three analyses were run on the 557 rejected setups using `scripts/simulate_t7_live_period.py` in replay mode:

**Entry Scenario Analysis** (`research/academic_pipeline/results/entry_scenario_analysis_v1.md`):
- Scenario A: limit at ob_high, fill when candle.low ≤ ob_high → 59.6% fill rate, 45.5% WR, +45R
- Scenario B: market order at rejection candle close → 45.5% WR (same — no benefit, worse slippage)
- Scenario C: market order immediately → 44.3% WR, more drawdown
- Scenario D: limit at midpoint (ob_mid) → 52.8% fill rate only, marginally worse WR
- **Conclusion: Scenario A (limit at ob_high) is the only architecture with positive expectancy**

**Filter Validation** (`research/academic_pipeline/results/filter_validation_v1.md`):
- Gap filter ≤1.5%: keeps 264/557 setups → **61.4% WR, +82R** (best)
- Gap filter ≤2.0%: 361 setups → 48.1% WR, +42.5R (worse than baseline)
- Gap filter ≤2.5%: 478 setups → 43.7% WR, +26R (worse than baseline)
- No filter (baseline): 557 setups → 45.5% WR, +45R
- Touch-1 filter: **untestable** — all 557 records have prior_touch_count ≥ 11 (scanning from dataset start Jan 2, not zone creation time)
- **Conclusion: Gap ≤1.5% is the only filter that improves both WR and total R**

**Monthly breakdown (gap ≤1.5%):**
- Jan 2026: 41 setups, 64.3% WR, +8.5R
- Feb 2026: 88 setups, **84.5% WR, +64.5R** (79% of total R — unusually clean trend month)
- Mar 2026: 79 setups, 39.1% WR, -1.5R (below 40% breakeven — structural weakness)
- Apr 2026 (partial): 56 setups, 75.0% WR, +10.5R

**Known risks:**
- Feb dominance: +64.5R of +82R came from Feb alone. Typical month outside bull trend may be much weaker.
- March WR 39.1% is below 40% breakeven even with gap filter — the filter does not protect against trend reversals.
- Gap filter validated in-sample only (same data used to discover it). Not validated out-of-sample.
- All 557 setups are LONG. Zero SHORT data in Jan–Apr 2026 (gold was in uptrend). SHORT architecture is mirrored but unvalidated.

---

## What Was Implemented (5 components)

### 1. Prompt fix — `src/prompts/primary_analyzer_prompt.py` line 150
**Before:** `- entry_price: current M15 candle close price`
**After:** `- entry_price: OB zone entry — ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT. Do NOT use the current candle close price.`

This is the change that unblocks 97%+ of previously rejected setups. L2 check 5 (`entry_in_ob`) now passes when AI quotes `entry_price = ob_high`.

### 2. Gap ceiling filter — `src/components/verification.py`
New function `_check_gap_ceiling` added as CHECK 7 (after check 6, before execution):
- Computes `gap_pct = (current_price - entry_price) / entry_price * 100` for LONG
- Fails if `gap_pct > 1.5%` (price too far above zone — stale setup, worse fills)
- `max_gap_pct` reads from `config["filters"]["max_gap_pct"]` with `or 1.5` fallback (handles `null` in YAML without crashing)

### 3. Limit order engine — `src/components/execution.py`
New `PendingLimitIntent` dataclass:
```python
@dataclass
class PendingLimitIntent:
    direction: str
    limit_price: float       # = ob_high (LONG) / ob_low (SHORT)
    stop_loss: float
    take_profit_1: float
    risk_pct: float
    expiry_candles: int = 192   # for logging only
    candles_elapsed: int = 0    # KZ candles seen since placement (logging only)
    placed_time: str = ""       # ISO UTC timestamp — used for clock-time expiry
    trade_id: str = ""
```

Three new methods on `ExecutionEngine`:
- `set_limit_intent(params, account_balance)` — stores intent, logs LIMIT_INTENT_SET
- `check_limit_fill(candle)` — called each KZ candle; triggers `open_trade()` if price touches limit; expires after 48 clock-hours
- `cancel_limit_intent(reason)` — clears intent, logs LIMIT_INTENT_CANCELLED

**Critical design detail — clock-time expiry:**
The expiry uses wall-clock time, NOT candle count. The original implementation had `candles_elapsed >= 192` which counted only kill zone candles (~29/day for XAUUSD = 6.6 trading days, not 48 hours). Fixed to:
```python
placed_dt = datetime.fromisoformat(intent.placed_time)
if datetime.now(timezone.utc) - placed_dt >= timedelta(hours=48):
    # expire
```
`candles_elapsed` is kept incrementing but only for log context — it no longer drives expiry.

### 4. Orchestrator wiring — `src/components/orchestrator.py`
Two insertions:
- **Pending fill check** inserted in `_process_candle` inside the `try:` block after `raw_data = ingest_live_data()`, before `mso = compute_market_state()`. Runs every kill zone candle.
- **`open_trade()` replaced with `set_limit_intent()`** at line ~754 — system no longer market-executes; places limit intent instead.

**Emergency stop cancel policy:**
- Portfolio drawdown stop (`drawdown_pct >= 4%`): calls `cancel_limit_intent("portfolio_drawdown_stop")` before returning
- Consecutive losses stop (`consec_losses >= 5`): calls `cancel_limit_intent("consecutive_losses_stop")` before returning
- **Canary block: does NOT cancel** — see below

### 5. Config — `config/agent_config.yaml`
```yaml
filters:
  max_gap_pct: 1.5
```

---

## The Canary Cancel Decision (peer-reviewed)

The implementation agent initially added `cancel_limit_intent("canary_blocked")` to the canary block. A peer review was commissioned on this specific question. **Verdict: REMOVE.**

**Reasoning:**
- The canary tests whether the AI's *current* evaluations are consistent with baseline — it says nothing about past evaluations
- The pending limit intent was placed when the AI was functioning correctly
- The fill check is purely mechanical: `candle.low <= intent.limit_price` — no AI involved
- The canary fires once per kill zone transition (twice/day for XAUUSD — London open and NY open)
- Worst case with cancel: a London-placed intent gets cancelled at the first NY candle if NY canary fails — losing up to 0.75R expected value for no safety benefit
- Clock-time expiry (48h) is the correct and sufficient expiry mechanism

**Final state:** canary block does NOT call `cancel_limit_intent`. The test `test_canary_block_does_not_cancel_limit_intent` in `test_orchestrator.py` asserts this explicitly.

---

## Bug Fixes Applied (peer review found 6)

A peer review identified 6 bugs in the initial implementation. All 6 were fixed:

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 1 | Critical | Clock expiry: 192 KZ candles = 6.6 days not 48h | Replaced with `timedelta(hours=48)` clock check |
| 2 | Minor | Off-by-one: fill check skipped on expiry candle | Clock-time expiry eliminates the off-by-one |
| 3 | Critical | Emergency stops leave zombie intent | `cancel_limit_intent()` on drawdown + consec_loss stops |
| 4 | Minor | `max_gap_pct: null` in YAML crashes with TypeError | Changed to `or 1.5` fallback |
| 5 | Minor | `_should_skip_first_ny_candle` blocks pending fills | Added `and not self.execution.pending_intent` guard |
| 6 | Minor | No test for `entry_price = ob_high` → PASS | Added `test_entry_in_ob_passes_when_entry_is_ob_high` |

---

## Test Suite State

- **1017 tests passing** (pre-flight: 1015, post-implementation: +2 net)
- 13 new tests in `tests/test_limit_order_flow.py`
- 3 updated/new tests in `tests/test_orchestrator.py`
- 1 updated test in `tests/test_verification.py` (expected check count 6→7)
- 25 pre-existing failures (unrelated to limit order work)

Key tests:
- `test_entry_in_ob_passes_when_entry_is_ob_high` — the most critical: verifies the prompt fix actually unblocks c5
- `test_check_limit_fill_expires` — verifies clock-time expiry (uses `placed_time` in the past)
- `test_canary_block_does_not_cancel_limit_intent` — verifies canary policy decision
- `test_portfolio_drawdown_blocks_trading` — verifies emergency stop + cancel
- `test_consecutive_losses_blocks_trading` — verifies consecutive loss stop + cancel

---

## Known Gaps / What Was NOT Done

1. **Touch-1 filter (zone freshness):** The Q-2.2 research hypothesis (72.7% WR on first-touch zones) cannot be validated with current data. All 557 records have `prior_touch_count ≥ 11` because the dataset scans from Jan 2, not from zone creation time. To enable: add `ob_zone_formed_candle_time` field to `scripts/simulate_t7_live_period.py`. This is a future research task.

2. **SHORT validation:** Zero SHORT setups in Jan–Apr 2026 data (gold was in uptrend). The gap filter and limit architecture mirror correctly for SHORT, but WR/R numbers are LONG-only. Validate separately when bear market data is available.

3. **Remaining instrument simulations:** US30, USDJPY, GBPJPY, GBPUSD full-period simulation (~$120 budget) was not run this session. Script is ready (`scripts/simulate_t7_live_period.py`). CEO decision pending.

4. **Spike slippage (deploy-and-monitor):** When price wicks to ob_high and reverses, `tick.ask` at fill moment may be above `intent.limit_price`. `open_trade()` executes at `tick.ask`, not at the limit price. The peer review estimated 5–20 pt slippage on a ~25 pt avg zone risk (~0.2–0.8R impact). No guard was added — this is accepted for now and should be monitored on first 10 fills.

5. **Position sizing (deploy-and-monitor):** `sl_distance` is computed from `tick.ask` at fill time, not from `intent.limit_price`. If `tick.ask` is 5–10 pts above `intent.limit_price`, the lot size will be slightly smaller than intended. Quantified as <5% position size error at typical slippage levels — accepted.

---

## Files Changed (complete list)

| File | Change |
|------|--------|
| `src/prompts/primary_analyzer_prompt.py` | Line 150: entry_price = ob_high not candle close |
| `src/components/verification.py` | `_check_gap_ceiling` function + wired as check 7 |
| `src/components/execution.py` | `PendingLimitIntent` dataclass + 3 limit order methods |
| `src/components/orchestrator.py` | Pending fill check + limit placement + cancel on stops |
| `config/agent_config.yaml` | `filters.max_gap_pct: 1.5` |
| `tests/test_limit_order_flow.py` | 13 new tests |
| `tests/test_orchestrator.py` | 3 new/updated tests |
| `tests/test_verification.py` | Check count 6→7 |
| `research/academic_pipeline/results/entry_scenario_analysis_v1.md` | Scenario A/B/C/D results |
| `research/academic_pipeline/results/filter_validation_v1.md` | Gap + touch-1 results |
| `research/academic_pipeline/results/peer_review_limit_order_v1.md` | Full peer review output |
| `research/academic_pipeline/data/entry_scenario_summary.json` | Machine-readable scenario results |
| `research/academic_pipeline/data/filter_validation_summary.json` | Machine-readable filter results |
| `research/academic_pipeline/prompts/EXEC_limit_order_production.md` | Implementation prompt used |
| `research/academic_pipeline/prompts/EXEC_peer_review_limit_order.md` | Peer review prompt used |
| `research/academic_pipeline/prompts/EXEC_limit_order_fixes.md` | 6-fix prompt used |

---

## How This Changes Live Behavior

**Before this session:** AI evaluates setup → L2 `entry_in_ob` fails → `NO_TRADE` → nothing executed. ~10 trades in 70 days.

**After this session:** AI evaluates setup → L2 `entry_in_ob` passes (entry_price = ob_high) → gap check ≤1.5% → `LIMIT_INTENT_SET` → system polls each KZ candle → fills when candle.low ≤ ob_high → `open_trade()` at `tick.ask`.

Expected frequency increase: from ~10 trades/70 days to approximately the gap ≤1.5% fill rate (264 setups × 60.2% fill = ~159 fills over Jan–Apr = ~40/month). This assumes current CANDIDATE rate and market conditions hold.

**The system is now trading limit orders, not market orders.** Execution price will be approximately at ob_high + ask spread rather than candle-close + ask spread. This is tighter entries with better risk geometry.

---

*Handoff written April 13, 2026. Next session should check live fills and verify slippage is within acceptable range on first 5–10 fills.*
