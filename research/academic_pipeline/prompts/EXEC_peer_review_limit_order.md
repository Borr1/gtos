# EXEC — Peer Review: OB Limit Order Production Implementation
# Adversarial code review — challenge everything

**For:** Fresh Claude Code agent (Sonnet or Opus)
**Role:** Independent reviewer. You did NOT write this code. Your job is to break it.
**Output:** `research/academic_pipeline/results/peer_review_limit_order_v1.md`

---

## What Was Implemented

Five changes to wire OB limit orders into the live trading system:

1. `src/prompts/primary_analyzer_prompt.py:150` — AI now quotes `entry_price = ob_high` (was: current candle close)
2. `src/components/verification.py` — New L2 check 7: `_check_gap_ceiling` rejects setups where current price > zone entry by >1.5%
3. `src/components/execution.py` — `PendingLimitIntent` dataclass + `set_limit_intent()`, `check_limit_fill()`, `cancel_limit_intent()` methods
4. `src/components/orchestrator.py` — Two insertions: (a) pending fill check in `_process_candle` after `raw_data` fetch, (b) `open_trade()` replaced with `set_limit_intent()`
5. `config/agent_config.yaml` — `filters.max_gap_pct: 1.5`

The research basis: limit orders at OB zone on 557 rejected XAUUSD setups (Jan–Apr 2026) → 61.4% WR (+82R) at gap ≤ 1.5% filter vs 45.5% WR (+45R) unfiltered.

---

## Your Review Mandate

Read every changed file in full. Then answer every question below with evidence from the code. "Looks fine" is not an answer. Cite file paths and line numbers.

---

## Section 1: Backtest-to-Production Fidelity

These questions verify that the implementation matches EXACTLY how the backtest was computed. Mismatches here mean live results will diverge from the research.

**Q1.1 — Entry fill condition match**
The backtest Scenario A logic: `fill when candle.low <= zone_entry (ob_high)` for LONG.
Does `check_limit_fill()` in execution.py use `candle["low"] <= intent.limit_price` for LONG?
Read the implementation. Quote the exact condition. PASS or FAIL.

**Q1.2 — 192-candle expiry match**
The backtest used a 192-candle (48-hour) forward window for each setup.
Does `PendingLimitIntent.expiry_candles` default to 192?
Does `check_limit_fill()` increment `candles_elapsed` on EVERY call including non-fill candles?
Quote the counter increment. PASS or FAIL.

**Q1.3 — Zone risk calculation match**
The backtest computed: `zone_sl = ob_low * 0.999`, `zone_tp = ob_high + (ob_high - zone_sl) * 1.5`.
The AI now quotes `entry_price = ob_high`, `stop_loss` below swing low (not `ob_low * 0.999`), `take_profit_1 = entry + 1.5 * |entry - sl|`.
**This is a known difference.** Confirm: in the live system, SL and TP come from the AI (swing-low based), NOT from mechanical ob_low * 0.999. State clearly whether this is the intended behavior or a gap. If it's a gap, what is the expected impact?

**Q1.4 — Gap filter definition match**
The backtest computed: `gap_pct = (entry_price - ob_high) / ob_high * 100` where `entry_price` was the REJECTED record's AI-quoted current candle close, and `ob_high` was parsed from `l2_reason`.
In production, the gap filter in `_check_gap_ceiling` computes: `(current_price - entry_price) / entry_price * 100` where `current_price` = M15 last candle close and `entry_price` = AI's new ob_high quote.
Are these computing the same thing? Is `current_price` (MSO M15 last candle) equal to what was `entry_price` in the rejected records? Confirm or flag discrepancy.

**Q1.5 — Candle-only fill check**
The backtest checked ALL 192 forward candles (including outside kill zones). The production implementation only checks candles during kill zone `_process_candle()` calls.
How many M15 candles occur outside kill zones in a 48-hour window? (London 07:00–10:30 = 14 candles, NY 13:00–17:00 = 16 candles = ~30 candles/day = ~60 candles/48h). That leaves ~132 candles per 48h window that are NOT checked.
**Verdict:** Is the fill rate in production expected to be lower than the backtest 59.6%? By how much approximately? State the implication for the +82R total R projection.

---

## Section 2: State Machine Correctness

**Q2.1 — Double-intent prevention**
Can `set_limit_intent()` be called while `self.pending_intent` is already set? Read `set_limit_intent()` — does it check for an existing intent before overwriting?
If yes: what happens to the first intent? Is that acceptable?
If no: is there a guard in `_process_candle` that prevents calling `set_limit_intent()` twice?

**Q2.2 — kz_trades guard interaction**
In `_process_candle`, the line `if kz_trades >= 1: return` fires BEFORE the `try:` block and the pending check.
Scenario: limit intent is set, kz_trades = 0. Next candle: kz_trades is still 0 (limit not filled). Is the pending check reached? Walk through the exact code path.
Scenario: limit intent fills, kz_trades becomes 1. Next candle: does `kz_trades >= 1` fire before the pending check? Is this correct (yes — no more limit checks needed)?

**Q2.3 — Active trade + pending intent conflict**
What happens if `self.execution.active_trade` is set AND `self.execution.pending_intent` is set simultaneously?
Read `_check_trade_and_capture()` (line 1166) — does it check `pending_intent`? Read `_process_candle` — which check comes first, `active_trade` or `pending_intent`? Is the ordering safe?

**Q2.4 — Canary block interaction**
The canary block check in `_process_candle` fires at line ~384: `if self.session_state.get("canary_blocked"): return`.
This is BEFORE the `try:` block. So if the canary is blocked, a pending limit is never checked and never fills.
Is this the correct behavior? State your verdict with reasoning.

**Q2.5 — Emergency stop interaction**
Portfolio drawdown stop (line ~375) and consecutive loss stop (line ~380) both fire before the pending check.
If portfolio drawdown triggers, `pending_intent` is NOT cancelled — it stays active and will try to fill on the next candle when the emergency stop condition may still be active (or worse, when the stop is resolved).
**Is this a bug?** Should `cancel_limit_intent()` be called when an emergency stop fires? What is the risk?

**Q2.6 — check_limit_fill vs check_and_manage_trade ordering**
In the main orchestrator loop, is `check_limit_fill` called on EVERY candle (including between kill zones) or only during kill zones? Read the main loop structure. State where the pending fill check fires vs where it doesn't.

---

## Section 3: Execution Safety

**Q3.1 — Actual fill price vs limit price**
When `check_limit_fill` triggers, it calls `open_trade()` which uses `tick.ask` (LONG) as the actual MT5 execution price — NOT `intent.limit_price`. 
In the backtest, fill was assumed at `zone_entry` (ob_high). If the current ask is 10 pts above ob_high at the moment of trigger, the trade executes at +10 pts slippage from the backtest assumption.
Quantify: with avg zone risk 25.24 pts and potential slippage of 5–20 pts, what is the R impact? Is this acceptable?

**Q3.2 — SL distance used for position sizing**
`open_trade()` at execution.py line 88 computes: `sl_distance = abs(entry_price - sl)` where `entry_price` is now `tick.ask` (market price), NOT `intent.limit_price`.
If `tick.ask` = 4428 and `intent.limit_price` = 4421, `sl_distance` is 6 pts LARGER than the intended zone risk. This means the lot size is SMALLER than intended (smaller risk per lot → fewer lots for same % risk).
Is this a material position sizing error? Quantify for a typical setup (avg zone risk 25.24 pts, potential 5–10 pt slippage at fill).

**Q3.3 — `open_trade` already uses `tick.ask`**
Verify: does the current `open_trade()` implementation at execution.py line 87 override `trade_params["entry_price"]` with `tick.ask`? Read the exact line. If yes, then `entry_price` in `check_limit_fill`'s `open_trade` call is irrelevant for MT5 execution — the SL distance calculation uses `tick.ask` regardless.
State whether the `"entry_price": intent.limit_price` passed to `open_trade` actually affects anything, or if it's dead code.

**Q3.4 — Limit triggered on spike candle**
Scenario: price briefly wicks to ob_high (candle.low = ob_high) but closes back above. The limit triggers. `open_trade()` is called. At the moment of execution, `tick.ask` may be significantly above `intent.limit_price` because the wick already reversed.
Is there a guard for this? Should there be a max-slippage check before executing?

---

## Section 4: Gap Filter Correctness

**Q4.1 — Filter runs after entry_in_ob, not before**
The gap filter (c7) is appended after c5 (`_check_entry_in_ob`) and c6 (`_check_sl_beyond_ob`).
With the new prompt (entry_price = ob_high), c5 will PASS for valid setups (entry = ob_high is within zone). Is there any scenario where c5 fails but c7 should have caught it first? Does the ordering matter?

**Q4.2 — Negative gap edge case**
If `current_price < entry_price` for LONG (price is BELOW the OB zone — unusual but possible after a sharp selloff), `gap_pct` is negative. Does the filter correctly PASS this? (A negative gap means price is already BELOW the OB zone entry — the limit would fill immediately.) Check the `<= max_gap_pct` condition.

**Q4.3 — Default threshold fallback**
`config.get("filters", {}).get("max_gap_pct", 1.5)` — if `filters` key is missing from config, default is 1.5. If `filters.max_gap_pct` is explicitly set to `null`, what happens? Test the fallback behavior.

---

## Section 5: Tests — Are They Actually Validating the Backtest Logic?

Read `tests/test_limit_order_flow.py` in full. For each test, state whether it correctly validates the corresponding backtest assumption.

**Q5.1** — `test_gap_ceiling_pass_long`: Does the 1.0% gap value (4465.60 given 4421.39 base) actually compute to ≈1.0%? Verify: `(4465.60 - 4421.39) / 4421.39 * 100 = ?`

**Q5.2** — `test_check_limit_fill_expires`: Does the test call `check_limit_fill` exactly 192 times? Does the 192nd call expire the intent or does expiry require a 193rd call? Read `if intent.candles_elapsed >= intent.expiry_candles` — when `expiry_candles=192` and `candles_elapsed` increments to 192 on the 192nd call, does `192 >= 192` trigger? Confirm the test boundary is correct.

**Q5.3** — Missing test: There is no test verifying that `check_limit_fill` does NOT trigger when called with `pending_intent = None`. Add it or flag it.

**Q5.4** — Missing test: There is no test for the gap filter's `max_gap_pct` default fallback (no `filters` key in config). Flag it.

**Q5.5** — Missing test: There is no integration test verifying that c5 (`entry_in_ob`) PASSES when `entry_price = ob_high` (the prompt fix). Flag it — this is the most critical change and has no direct test.

---

## Section 6: What the Research Does NOT Guarantee

State clearly (do not soften):

**Q6.1** — The 61.4% WR and +82R are from Jan–Apr 2026 XAUUSD, all LONG, bull market. February alone contributed +64.5R of +82.0R total (79%). If February 2026 was an unusually clean trend month, what is the realistic base case for a typical month?

**Q6.2** — The backtest used AI-generated SL/TP for Scenario B (market order baseline) but mechanical ob_low*0.999 SL for Scenario A (limit order). In production, limit orders will use AI-generated SL (swing-low based). If the AI's SL is wider than ob_low*0.999, R is smaller. If tighter, SL is more likely to be hit. Flag this as a known data gap.

**Q6.3** — The gap filter was validated on the same dataset used to discover it (in-sample). It has NOT been validated on out-of-sample data. State the implication.

**Q6.4** — March 2026 WR was 39.1% even after gap filter — below the 40% breakeven. The system will lose money in similar regimes. Is there any additional filter or circuit breaker to protect against a March-like drawdown period?

---

## Final Verdict

After completing all sections:

```
PRODUCTION READINESS VERDICT
=============================
Overall: READY / READY WITH CONDITIONS / NOT READY

Critical issues (block deployment):
- [list any FAIL from Q1.1, Q1.2, Q2.1–Q2.6, Q3.1–Q3.4 that are bugs]

Non-critical issues (deploy and monitor):
- [known gaps that are acceptable for initial deployment]

Tests missing (flag for follow-up):
- [from Q5.3–Q5.5 and any others found]

Research gaps acknowledged:
- [from Section 6 — these are known, not bugs]

Recommended monitoring after deployment:
- [what metrics to watch in the first 30 fills]
```

Do not soften the verdict. If there is a bug that would cause incorrect fills, wrong position sizes, or orphaned state, mark NOT READY and explain specifically.
