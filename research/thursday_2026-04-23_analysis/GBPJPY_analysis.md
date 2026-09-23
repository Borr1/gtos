# GBPJPY — Thursday 2026-04-23 Analysis

**Scope:** GBPJPY only, 2026-04-23 UTC trading day
**Pre-AI gate shipped:** 2026-04-20 (commit `8a9bcfe`), direction-agnostic variant
**Pre-AI gate LIVE variant on 2026-04-23:** direction-aware (uncommitted working-tree mod to `pre_ai_gates.py` + `orchestrator.py`)
**Account at Thursday open:** $98,026.71 (verified `logs/gbpjpy.log:2597`)
**Account at Thursday close:** $99,287.62 (verified `logs/gbpjpy.log:2796`)
**Net Thursday P&L:** +$1,260.91 (+1.286 %)

---

## Executive Summary

1. **Pre-AI gate did its job — but the "47 skips" figure in the brief is wrong.** Exact count of GBPJPY pre-AI-gate skips on 2026-04-23 UTC = **21**, all with reason `no_unmitigated_bullish_h1_pois` (`logs/gbpjpy.log` grep, filtered to log-local `2026-04-23` prefix = a superset of UTC 2026-04-23 given the GMT+8 log clock). Weekly GBPJPY eval-row compression is real: **29 → 15 → 5 → 1** rows across Mon-Thu, matching the gate-plus-directional-upgrade narrative.
2. **Exactly one GBPJPY AI call on Thursday — a CANDIDATE at 07:16 UTC (London KZ, index 0).** All 10 H1 OBs in the MSO except one were already mitigated; the sole unmitigated OB (215.064-215.167, formed 2026-04-23 06:00 UTC, touch_count=1) was a fresh pristine retest in discount zone. L2 PASS on 6/6 applicable checks, `sl_buffer_applied=0.04` (FA-2 compliant).
3. **Limit fill happened ~6h later at 13:16 UTC, immediately triggering a latent `NameError: kz_trades` crash at `orchestrator.py:492`.** The position survived on the broker server (SL+TP set server-side in the `open_position` `order_send` request), but our own TP1-monitoring pipeline lost its post-fill tracking object because `_init_trade_tracking` never ran. Exit was finally observed as a passive `"Position 432844145 no longer exists - closed by broker"` at 13:54 UTC — 38 minutes after fill. We cannot independently attribute the exit to TP1 vs SL from log evidence alone; circumstantial evidence (account balance +$1,260.91 for the day, one other fleet trade) is consistent with TP1 hit but short of 80 % confidence.
4. **Sampled gate correctness: zero false-positive skips detected.** Every Tokyo skip (00:16-03:00 UTC) pre-dates the OB formation (06:00 UTC), and every NY skip (13:30-15:30 UTC) post-dates a fill that pushed price back toward SL, plausibly mitigating the OB. Confidence ≥ 90 % for Tokyo, ~70 % for NY (we cannot read MSO at each skip without persisted snapshots — Confidence <80 % flagged).
5. **Key concerns:** (a) the `NameError: kz_trades` crash is live code at `orchestrator.py:492` (no open fix); (b) gate skips are NOT written to `live_evaluations/GBPJPY/<date>.jsonl` — only to `logs/gbpjpy.log` — which blinds downstream research without log-cross-referencing; (c) the direction-aware gate upgrade is running live but UNCOMMITTED (`git status` shows `M src/components/pre_ai_gates.py`, `M src/components/orchestrator.py`) — violating the "every deliverable is a committed file" rule in CLAUDE.md.

---

## 1 — Pre-AI Gate Efficacy & Breakdown

### 1.1 Fact check: the 47-skip figure

The task brief states "47 Pre-AI gate skip events on 2026-04-23". That number is the total pre-AI-gate skips in the **entire `logs/gbpjpy.log` file** (spanning 2026-04-21 onwards), not Thursday only. Exact counts:

| Scope | Count |
| --- | --- |
| Whole `logs/gbpjpy.log` | 47 (`grep -c "Pre-AI gate skip:"`) |
| Log-local `2026-04-23` prefix (= approx UTC 2026-04-22 16:00 → 2026-04-23 15:59 given GMT+8 logger) | 21 |
| UTC 2026-04-23 proper (Tokyo KZ 11 + NY KZ 9 + first Tokyo candle 00:16 = covered) | 21 |

So **21 GBPJPY pre-AI-gate skips on Thursday**, not 47. All 21 use reason string `no_unmitigated_bullish_h1_pois` (direction-aware path). `logs/gbpjpy.log:2694-2716,2763-2780`.

### 1.2 Skip distribution (all 21, log-local → UTC)

| Log-local (GMT+8) | UTC | KZ | Reason |
| --- | --- | --- | --- |
| 08:16:11 | 00:16:11 | tokyo | `no_unmitigated_bullish_h1_pois` |
| 08:30:05 | 00:30:05 | tokyo | same |
| 08:45:05 | 00:45:05 | tokyo | same |
| 09:00:05 | 01:00:05 | tokyo | same |
| 09:15:05 | 01:15:05 | tokyo | same |
| 09:30:05 | 01:30:05 | tokyo | same |
| 09:45:05 | 01:45:05 | tokyo | same |
| 10:00:05 | 02:00:05 | tokyo | same |
| 10:15:05 | 02:15:05 | tokyo | same |
| 10:30:05 | 02:30:05 | tokyo | same |
| 10:45:05 | 02:45:05 | tokyo | same |
| 11:00:05 | 03:00:05 | tokyo | same |
| 21:30:05 | 13:30:05 | ny | same |
| 21:45:05 | 13:45:05 | ny | same |
| 22:00:05 | 14:00:05 | ny | same |
| 22:15:05 | 14:15:05 | ny | same |
| 22:30:05 | 14:30:05 | ny | same |
| 22:45:05 | 14:45:05 | ny | same |
| 23:00:05 | 15:00:05 | ny | same |
| 23:15:05 | 15:15:05 | ny | same |
| 23:30:05 | 15:30:05 | ny | same |

Tokyo: 12 skips. NY: 9 skips. Total 21.

### 1.3 Why only a single AI call on Thursday

From the live_evaluations weekly trend (verified via `wc -l knowledge_base/live_evaluations/GBPJPY/<date>.jsonl`):

| Date | Rows |
| --- | --- |
| 2026-04-20 | 29 |
| 2026-04-21 | 15 |
| 2026-04-22 | 5 |
| 2026-04-23 | **1** |

The sharp drop from Mon (29) → Thu (1) matches:
1. Gate non-directional shipped 2026-04-20 23:19 CST (commit 8a9bcfe) — eliminates candles with zero unmitigated H1 POIs in ANY direction.
2. Gate upgraded to **direction-aware** (uncommitted in git but live) between the last `no_unmitigated_h1_pois` log line on 2026-04-22 15:45 and the first `no_unmitigated_bullish_h1_pois` on 2026-04-22 21:16 — eliminates candles where there's only an opposing-side unmitigated OB.
3. GBPJPY H1 structure on Thursday was cleanly bullish but had saturated the H1 OBs via repeated testing — most bullish OBs were already mitigated before the day began. A single fresh unmitigated bullish OB was printed at H1 06:00 UTC candle close (215.064-215.167), and that's the only candle-window the gate allowed AI to evaluate.

**Verdict:** GBPJPY was **legitimately H1-POI-starved on Thursday.** Only 1 AI call is the expected result, not a gate bug. The commit message observation ("~15 guaranteed-reject GBPJPY AI calls/day") applied to the pre-directional variant; the directional variant is even more aggressive.

---

## 2 — The One CANDIDATE (07:16 UTC London)

All facts below are from `knowledge_base/trade_records/GBPJPY/2026-04-23_london_0716.json` and `knowledge_base/live_evaluations/GBPJPY/2026-04-23.jsonl:1`.

### 2.1 AI output

| Field | Value |
| --- | --- |
| decision | CANDIDATE |
| direction | LONG |
| grade | A+ |
| confidence | 82 |
| framework | ob_retest |
| entry_price | 215.167 |
| stop_loss | 215.024 |
| take_profit_1 | 215.382 |
| take_profit_2 / 3 | 0.0 (unused) |
| sl_buffer_applied | 0.04 (FA-2: non-zero, JPY-cross precision ✓) |
| RR | 1.5 |
| position_size_lots | 0.01 (pre-sizing; later grew via MT5 tick-value calc to 10.29 lots at fill) |
| session_memory_count | 0 (memory disabled system-wide) |
| align_score | 4/4 bullish (D1, H4, H1, M15 all bullish — `logs/gbpjpy.log:2722`) |
| deterministic_bias | `bullish (source=D1)` (`logs/gbpjpy.log:2723`) |
| spread_at_entry | 1.70 cents (`trade_record line 11104`) |

### 2.2 H1 OB cited

- Zone: **215.064 - 215.167** (low-high)
- Type: bullish, touch_count: 1, `mitigated: false`
- Formation time: 2026-04-23 06:00 UTC (76 min before the CANDIDATE candle)
- Causing BOS: H1 candle index 166 at 2026-04-23 09:00 UTC (within same MSO window — BOS that preceded the retest)
- AI POI level: 215.116 (midpoint of the OB)
- `trade_record lines 1404-1416` + `lines 11048-11056`

### 2.3 AI reasoning

> "All three C-gates pass: H1 has 11 bullish BOS confirming strong directional bias (C1), M15 is fully aligned bullish with no opposing structure (C2), and direction is LONG matching H1 bullish bias (C3)." (`trade_record line 11072`)

> Explanation of POI: "Nearest unmitigated H1 bullish OB at 215.167-215.064 (touches=1), formed at 2026-04-23T06:00 following bullish BOS, sitting below current price in discount zone." (`trade_record line 11055`)

### 2.4 L2 verification (all checks)

| Check | Status | Detail (`trade_record lines 20-76`) |
| --- | --- | --- |
| m15_choch_exists | PASS | M15 BOS bullish with displacement at 2026-04-14T13:45, ratio 2.29 |
| displacement_ratio | PASS | WARNING: AI claimed 3.70, MSO measured 2.29 (still ≥ 1.5 threshold) |
| h1_poi_exists | PASS | OB found 215.06-215.17 vs AI POI 215.12 |
| ob_zone | PASS | Midpoint 215.12 in discount zone (eq=215.21), correct for LONG |
| entry_in_ob | PASS | Entry 215.17 inside OB 215.06-215.17 |
| sl_beyond_ob | PASS | SL 215.02 below OB low 215.06 |
| gap_ceiling | SKIP | "No M15 candles in MSO" (cosmetic) |

**Note: the displacement_ratio mismatch (AI=3.70 vs MSO=2.29) is logged as a WARNING only.** L2 lets it through because 2.29 ≥ 1.5. AI-hallucinated displacement is a known broader concern (FA-2 touched related AI-side hygiene) but does not block this trade.

### 2.5 Gates 1 & 3

- Gate 1 (AI-output sanity): PASS — grade A+, direction LONG, RR 1.5, sl_distance 0.143. (`trade_record lines 97-115`)
- Gate 3 (account/broker): PASS — daily_pnl 0 %, trades_today 0, trades_in_kz 0, MT5 connected, spread 1.80 cents. (`trade_record lines 81-96`)

Final decision: `LIMIT_PLACED` (`trade_record line 116`).

---

## 3 — Fill Reconciliation

### 3.1 Timeline (UTC)

| UTC | Event | Source |
| --- | --- | --- |
| 07:16:33 | CANDIDATE written to live_evaluations jsonl | `GBPJPY/2026-04-23.jsonl:1` |
| 07:16:38 | Limit intent saved; LIMIT PLACED `lim_2026-04-23_0716` at 215.167, SL 215.024, TP 215.382, expiry 192 candles (~48 h) | `logs/gbpjpy.log:2732-2734` |
| 07:16:38 → 13:16:14 | 6-hour inter-KZ + London-KZ-post-intent idle; no new evals (pending_intent blocks `_process_candle`) | `orchestrator.py:484-513` |
| 13:00:00 | Entering NY KZ (21:00 local) | `logs/gbpjpy.log:2747` |
| 13:01:09 | Canary PASS | `logs/gbpjpy.log:2749` |
| 13:16:14 | First NY M15 candle processes; `check_limit_fill` triggers — M15 candle at broker-time 16:15:00 (= UTC 13:15 ±) low 215.116 ≤ limit 215.167 | `logs/gbpjpy.log:2751` |
| 13:16:14 | Fill sizing: original_sl_dist=0.143, actual_sl_dist=0.152, entry=215.176 (4 pips positive slippage against us from 215.167 limit) | `logs/gbpjpy.log:2752` |
| 13:16:14 | Risk 1.00 % (no correlation penalty) | `logs/gbpjpy.log:2753` |
| 13:16:14 | MT5 result.price=0.0 fallback → tick entry_price=215.176 | `logs/gbpjpy.log:2754` |
| 13:16:14 | **Trade opened: tr_2026-04-23_1316 LONG 10.29 lots at 215.176, SL=215.024, TP1=215.382** (ticket 432844145) | `logs/gbpjpy.log:2755` |
| 13:16:14 | **Pipeline crash: `NameError: name 'kz_trades' is not defined` at orchestrator.py:492** | `logs/gbpjpy.log:2756-2761` |
| 13:30:05 | Next NY candle — `_process_candle` — gate skip `no_unmitigated_bullish_h1_pois` (the 215.064-215.167 OB has been mitigated — body-closed below 215.064 since the 13:15 M15 low at 215.116 pierced the OB, and subsequent bars presumably closed through) | `logs/gbpjpy.log:2763` |
| 13:45:05 | Next candle — same gate skip | `logs/gbpjpy.log:2765` |
| 13:54:05 | **Position 432844145 no longer exists - closed by broker** | `logs/gbpjpy.log:2766` |
| 14:00 → 15:30 | 7 more gate skips through end of NY KZ | `logs/gbpjpy.log:2768-2780` |
| 15:30:05 | All KZs complete, no active trade. Ending session. | `logs/gbpjpy.log:2782` |
| 15:31:04 | Account balance: **$99,287.62** (from $98,026.71 → +$1,260.91) | `logs/gbpjpy.log:2796` |

### 3.2 Slippage analysis

- Limit: 215.167
- Fill: 215.176 (adverse 9-pip slippage — this pattern of "actual_sl_dist > original_sl_dist" with positive slippage is the expected behaviour of `execution._fill_limit` which preserves SL geometry by widening the effective SL distance, keeping the risk profile rational)
- `logs/gbpjpy.log:2752` explicitly records original_sl_dist=0.143 vs actual_sl_dist=0.152 — this is the per-instrument `_FILL_EPSILON` scaling from session 35 (commit `4af838f`) behaving as designed.

### 3.3 Exit (TP vs SL vs other) — unresolved

Direct evidence:
- `Position 432844145 no longer exists - closed by broker` (`logs/gbpjpy.log:2766`) at 13:54:05 UTC, 38 min after fill.
- Source code `execution.check_and_manage_trade` logs this exact string when a prior-known ticket is missing from MT5's `get_positions` output (`src/components/execution.py:683-687`). It means "position disappeared between two polls", and is written BEFORE our own `_execute_tp1_partial` would fire its "TP1 full close" log line.
- We do NOT see any "TP1 full close" log.

That leaves three possibilities for how the position exited:
| Scenario | Evidence for | Evidence against |
| --- | --- | --- |
| **Broker-side TP1 fill** (price reached 215.382 between our 13:45 and 13:54 polls; MT5's server-side TP=215.382 on the ticket auto-closed it before our 15 s polling cycle checked) | Consistent with TP set via `order_send` request["tp"]=tp1 (`execution.py:402`); account went UP $1260.91 Thursday; no opposing "TP1 full close" log needed because server beat our poll | Price would have had to travel ~20 pips UP from 215.176 in ~38 min after a pull-back to 215.116 at fill. Plausible but not verifiable from logs. |
| **Broker-side SL hit** (price closed below 215.024) | The 13:30 pre-AI gate skip at UTC 13:30 means MSO saw the 215.064-215.167 OB as mitigated by that candle — price must have body-closed below 215.064 at least once. Only 40 pips from there to SL 215.024. | Account balance UP $1260.91 — if GBPJPY were at −1R (~−$980) AND USDJPY's earlier safety-close is unclear, totals don't match a straight SL-hit picture. |
| **Manual broker-server close** (e.g. spread/stop-out/risk-manager action) | No direct evidence | FN demo does not typically auto-close open positions outside of SL/TP |

**Confidence in TP1 hit: ~65 %.** Flagged <80 %. Caveats:
- USDJPY had its own incident Thursday — trade opened 09:00 UTC, `Failed to move SL to BE - closing position for safety` + `Position closed: sl_modification_failed at 0.0` at 09:30 UTC (`logs/usdjpy.log:2873-2874`). Exit price was 0.0 (MT5 result fallback) so USDJPY P&L is ALSO indeterminate from logs alone.
- The +$1,260.91 account change is plausibly consistent with "GBPJPY ~+1R, USDJPY ~+0.3R" or "GBPJPY ~+1.3R, USDJPY ~0R" — both scenarios require GBPJPY to be a winner.

**Recommended follow-up (not done as part of this read-only report):** pull MT5 deal history (`mt5.history_deals_get`) for ticket 432844145 to reconcile exact close price and P&L. Same for USDJPY ticket.

### 3.4 The `kz_trades` NameError

- **File:line:** `src/components/orchestrator.py:492`
- **Blame:** commit `536c5296` (2026-04-13, Borhen Benltaief) introduced the bug.
- **Code:** `self.session_state[f"trades_{kill_zone}"] = kz_trades + 1` — `kz_trades` is referenced but never defined in scope.
- **Comment at line 461-462 (from T2.8 commit `dc4cec2`):** *"No `kz_trades` cap any more — the concurrent-cap in permissions.py replaces per-KZ and per-day loss gates"* — so the line is dead legacy and should be either deleted or replaced with `self.session_state.get(f"trades_{kill_zone}", 0)`.
- **Impact today:** the post-fill tracking flow is derailed:
  1. `Trade opened` logs successfully (line 444 inside `_fill_limit`)
  2. control returns to `_process_candle` at line 490
  3. line 491 increments `trades_today` successfully
  4. line 492 raises `NameError` — pipeline aborts
  5. `_log_candle("LIMIT_FILLED", ...)` on line 493 never runs → no LIMIT_FILLED row in jsonl
  6. `_promote_pending_record_on_fill` on line 503 never runs → pending-records index still contains the intent ID (`knowledge_base/trade_records/GBPJPY/_pending_records_index.json:2`, which STILL holds `lim_2026-04-23_0716 → ...2026-04-23_london_0716.json` at the time of this analysis — a stale entry that should have been promoted/removed on fill)
  7. `_init_trade_tracking(trade_state)` on line 505 never runs → no `_active_trade_record` for `_finalize_exit` to consume at exit time
  8. Net effect: broker-side position is fine (server has SL+TP), but orchestrator-side MFE/MAE tracking, exit capture, and trade-record exit finalization all silently skip.

This is a **live latent bug** that the pre-AI gate path never hit until Thursday (first LIMIT_FILLED under ob_retest-only framework since gate went live with directional variant).

### 3.5 Session summary discrepancies

`knowledge_base/live_sessions/GBPJPY/2026-04-23_london_summary.json` reports:
- `candles_evaluated: 1`, `api_calls_made: 1`, `decisions: {NO_TRADE: 1, CANDIDATE: 0, WAIT: 0}`

This is **wrong**: the 07:16 evaluation was a CANDIDATE, not a NO_TRADE (confirmed by `GBPJPY/2026-04-23.jsonl:1` `"decision": "CANDIDATE"`). The session summary's `decisions` counter seems to misclassify the post-evaluation state (LIMIT_PLACED → tracked as NO_TRADE for that candle at summary time). Cosmetic but worth flagging.

`2026-04-23_ny_summary.json` and `2026-04-23_tokyo_summary.json` both show `kz_start: "2026-04-23T13:00:00Z"` and `kz_end: "2026-04-23T15:30:00Z"` — the NY KZ boundaries — regardless of which KZ the summary is for. Another cosmetic but real session-summary bug (file-level template leakage).

---

## 4 — Pre-AI Gate Correctness Audit (sampled skips)

**Method.** Pre-AI-gate skips do NOT write rows to `live_evaluations/<symbol>/<date>.jsonl`, no_trade yamls, or any other durable MSO snapshot. The only direct record is the one-line `logs/gbpjpy.log` entry. Therefore MSO state at each skip is NOT recoverable directly — we must triangulate via the MSO captured at the adjacent CANDIDATE candle (07:16 UTC) and reason about OB lifecycle to verify correctness.

The 07:16 MSO enumerates all 10 H1 bullish OBs present at that time, with formation_time, touch_count, and `mitigated` flag (`trade_record.json:1273-1417`):

| Formation time (UTC) | OB zone | `mitigated` | touches | Notes |
| --- | --- | --- | --- | --- |
| 2026-04-15 19:00 | 215.475-215.822 | true | 29 | |
| 2026-04-16 07:00 | 215.444-215.552 | true | 28 | |
| 2026-04-17 04:00 | 215.314-215.486 | true | 32 | |
| 2026-04-17 22:00 | 214.325-214.480 | true | 9 | |
| 2026-04-20 11:00 | 214.525-214.686 | true | 7 | |
| 2026-04-20 19:00 | 214.736-214.912 | true | 15 | |
| 2026-04-21 09:00 | 214.702-214.979 | true | 7 | |
| 2026-04-21 14:00 | 214.986-215.222 | true | 33 | |
| 2026-04-21 22:00 | 215.055-215.238 | true | 26 | |
| 2026-04-22 09:00 | 215.089-215.355 | true | 20 | |
| **2026-04-23 06:00** | **215.064-215.167** | **FALSE** | **1** | ← the one the CANDIDATE traded |

All 6 H1 breaker blocks are `is_retested: true` and `direction: bearish` (would support SHORT, not LONG).

### 4.1 Sample 1 — 2026-04-23 00:16:11 UTC (first Tokyo skip)

- Bias at that moment: bullish, align=4/4 (consistent with 07:16 MSO D1/H4/H1/M15 all bullish; no structural event flipped overnight)
- The 215.064-215.167 OB had not yet been formed (formation 06:00 UTC, ~6 h later)
- ALL other bullish H1 OBs were already `mitigated: true` by 07:16 UTC (`touch_count ∈ {7, 9, 15, 20, 26, 28, 29, 32, 33}`)
- For these to have all been mitigated BY 00:16, they had to already be mitigated BEFORE 00:16 (OB mitigation is a terminal state — once body-closes-below, stays mitigated)
- Bullish breakers: zero in MSO at 07:16 — none existed at 00:16 either (breakers only form as mitigated OBs; none of the mitigated OBs have `direction: bullish` as a breaker because all breakers flipped to `bearish`)
- **Verdict: correct skip. No unmitigated bullish H1 OB and no bullish breaker to retest — AI would have had nothing valid to cite.**
- Confidence: ~95 %. (Small residual uncertainty on whether mitigation states were identical at the earlier snapshot, since MSO is recomputed each candle.)

### 4.2 Sample 2 — 2026-04-23 01:30:05 UTC (mid-Tokyo)

- Same logic as Sample 1 — the fresh OB is still 4.5 h in the future.
- Tokyo price action (from H1 swings in 07:16 MSO at `trade_record lines 1083-1093`): low swing at 215.064 formed at 06:00 UTC ( = the OB low, confirming price dropped to create the OB), prior swing high 215.350 at 03:00 UTC. So from 00:00-03:00 UTC price was consolidating 215.184 → 215.350 → somewhere. No structural change that would un-mitigate prior OBs.
- **Verdict: correct skip.**
- Confidence: ~95 %.

### 4.3 Sample 3 — 2026-04-23 03:00:05 UTC (last Tokyo skip)

- Still 3 h before fresh OB formation.
- Same reasoning.
- **Verdict: correct skip.**
- Confidence: ~95 %.

### 4.4 Sample 4 — 2026-04-23 13:30:05 UTC (first NY skip, 14 min after fill)

- The 215.064-215.167 OB **existed** at 07:16 UTC and was freshly retestable. For it to now trigger a gate skip at 13:30, it must have been marked `mitigated: true` between 07:16 and 13:30 UTC.
- Mitigation rule (`market_state.py:549-554`): bullish OB mitigated when any subsequent H1 candle's BODY closes below the OB low (215.064).
- The M15 candle that filled the limit at 13:15 UTC had low 215.116 (above 215.064 — just a touch, not a close-through). So the OB was NOT yet mitigated right at the fill.
- Between 13:15 and 13:30 UTC, price had to body-close below 215.064 on at least one H1 candle (the 13:00 UTC H1 candle would close at 14:00 UTC, so at 13:30 the 13:00 H1 candle is still forming). So the mitigation trigger must be from an earlier H1 (12:00, 11:00, etc.). Given the fresh OB's low 215.064 and swing low of the same value at H1 06:00, and all H1 OBs above are mitigated, it's plausible an H1 candle between 07:00 and 13:00 UTC closed below 215.064 (these are the bars whose activity we don't have in the trade_record).
- Alternative: the MSO at 13:30 may have re-classified the OB's mitigation during its rolling recompute.
- **Verdict: plausibly correct skip, but unverifiable without the 13:30 MSO snapshot.**
- Confidence: ~70 % (<80 % flagged).

### 4.5 Sample 5 — 2026-04-23 15:30:05 UTC (final NY skip, end of day)

- Position was already closed by broker at 13:54 UTC. The 215.064-215.167 OB is either mitigated (if exit was SL) or still unmitigated (if exit was TP1 — price went UP from OB retest rather than through it).
- If TP1 was hit, the OB should STILL be unmitigated at 15:30 (price went up, not down-through).
- But the gate skipped at 15:30 saying `no_unmitigated_bullish_h1_pois` — meaning MSO says zero unmitigated bullish OBs.
- This is the most ambiguous sample. Two scenarios:
  1. **Exit was SL** — then OB was mitigated before close. Skip is correct.
  2. **Exit was TP1** — then the OB should be unmitigated and the gate should NOT skip. If the gate skipped anyway, either (a) the OB is "old enough" it rolled out of the H1 lookback window (H1 MSO typically keeps a bounded number of historical bars), or (b) a later H1 candle (e.g. 13:00, 14:00, 15:00) closed below 215.064 after TP1 was hit and price retraced back down.
- Without the 15:30 MSO, we cannot determine which.
- **Verdict: indeterminate.**
- Confidence: ~50 %. Not enough evidence to claim gate bug; mitigation is plausible under either exit outcome, just harder to verify under TP1.

### 4.6 Aggregate

- 3 of 5 samples verified correct with ≥ 95 % confidence.
- 2 of 5 samples plausible but unverifiable due to the gate's deliberate non-logging of MSO at skip time.
- **Zero false-positive skips detected.** However, our tools cannot detect subtle false-positives without MSO snapshots at skip times. See §7 for an actionable recommendation.

---

## 5 — Pre-FA-2 vs Post-FA-2 CANDIDATE Rate & Gate Payload

### 5.1 FA-2 compliance on Thursday's CANDIDATE

- `sl_buffer_applied: 0.04` (`trade_record lines 11078,11092` + eval_jsonl `sl_buffer_applied` field implicit in trade_record) — **non-zero, satisfies FA-2's post-AI degenerate-params validator.**
- FX precision: SL=215.024, TP1=215.382 — both to 3-decimal precision (JPY cross). Matches FA-2 prompt precision mandate.
- L2 validation passed — the CANDIDATE is a valid H1 POI retest, not a ghost citation of an already-mitigated OB.

### 5.2 Is the gate doing what the commit message promised?

Commit `8a9bcfe` claimed: *"Closes observed ~15 guaranteed-reject GBPJPY AI calls/day from AI citing already-mitigated H1 OBs."* Verification:
- Pre-gate GBPJPY AI calls/day (using Mon 2026-04-20 as "before-directional-gate" baseline): 29 rows (≈ 21 during KZs after accounting for canaries etc.)
- Post-gate GBPJPY AI calls/day (Thu 2026-04-23): 1 row
- Savings: 28 rows or ~97 % reduction. That exceeds the "~15/day" estimate — the directional upgrade is more aggressive than the original variant.
- At claude-sonnet-4-6 effort=max with ~$0.24/call (approximate, per CLAUDE.md monthly cost note), this is ~$6-7/day per instrument savings, scales to ~$200/month across the fleet if similar. Budget-relevant given the $50-60 Anthropic balance cap.

### 5.3 Did the one CANDIDATE that DID pass the gate deliver a valid H1 POI retest?

Yes. The OB cited (215.064-215.167 formed 06:00 UTC, touches=1, not mitigated) is a textbook fresh bullish H1 OB in discount zone. L2 PASSED `h1_poi_exists` cleanly. No already-mitigated-OB citation, no ghost POI.

---

## 6 — Market Reality Thursday

Reconstructed from the single MSO snapshot at 07:16 UTC (`trade_record lines 122-2500+`, H1 swings at `lines 794-1094`, H1 OBs at `lines 1273-1416`):

### 6.1 D1/H4/H1 structure

- D1 bullish (align_score 4/4), protected swing at 213.995 (2026-04-17 low), most recent high 215.899 (2026-04-15), retrace to 213.995 then recovery
- H4 bullish, structure_events show 7 consecutive bullish BOS since 2026-04-07 through 2026-04-22 08:00; most recent swing low 214.914 (2026-04-22 12:00)
- H1 bullish, 11 BOS events, most recent BOS at 2026-04-23 09:00 UTC level_broken 215.350 close 215.390 ratio 2.16

### 6.2 Thursday H1 price action (inferred from H1 swings)

Overnight into Thursday:
- 2026-04-23 00:00 UTC low 215.184
- 2026-04-23 03:00 UTC high 215.350
- 2026-04-23 06:00 UTC **low 215.064** ← this is where the fresh OB formed (bullish reversal candle)
- Between 06:00 and 07:16 UTC: a bullish impulse (the BOS breaking 215.350 at 09:00 — but that's H1 candle 09:00 which is AFTER 07:16, so the MSO time-travel here is from the ongoing candle data post-eval)
- By 15:16 local (07:16 UTC): current price ~215.308 (from `trade_record line 11118`, proximity context)

Pre-London price: around 215.20-215.35 range, squeezing into the OB discount zone. Trade logic was sound.

### 6.3 Post-CANDIDATE market

- London KZ stayed above the entry 215.167 from 07:16 to 13:00 UTC (otherwise the limit would have filled during London, not NY). So price drifted/ranged above 215.167 for ~6 hours.
- At 13:15 UTC (during the first NY M15 candle) price dipped to low 215.116 — piercing the OB zone 4 pips and triggering our limit — then reversed.
- 38 min later position exited. Given the subsequent gate skips say "OB mitigated", price likely revisited 215.064 or lower at some point after fill. Whether it hit TP1=215.382 first is the exit-path ambiguity of §3.3.

### 6.4 Missed setups

**None inside London KZ itself.** The only evaluated candle (07:16 UTC) produced a CANDIDATE that was placed as a LIMIT. All subsequent London candles (07:30-09:30 UTC) are blocked by `pending_intent` check in `orchestrator.py:484-513` — this is intentional 1-setup-at-a-time discipline, not a missed opportunity.

**None outside KZ.** The between-KZ window (09:30-13:00 UTC) is non-tradeable by config. The inter-KZ sleep was functional.

**None in NY KZ.** All 9 NY skips occurred AFTER the fill (13:16 UTC). The fresh OB was used. No second setup would have been eligible under the ob_retest framework since (a) concurrent-cap limits are in force, (b) all OBs were mitigated post-fill.

**Tokyo KZ had zero eligible setups.** H1 POI starvation was legitimate.

---

## 7 — Concerns, Action Items, and Confidence Ladder

### 7.1 Concerns (ordered by priority)

1. **`NameError: name 'kz_trades' is not defined` at `orchestrator.py:492` — live latent bug triggered by first post-gate limit-fill. (Confidence: 100 %.)** Impact: LIMIT_FILLED log never written; pending-records index not promoted; `_init_trade_tracking` not called → MFE/MAE tracking + exit capture silently skipped; trade record `execution` and `exit` fields remain `null`. Post-session session_summary miscounts decisions.
2. **Direction-aware gate upgrade is uncommitted (violates CLAUDE.md: "Every deliverable is a FILE committed to main"). (Confidence: 100 %.)** `git diff` shows unstaged changes to both `src/components/pre_ai_gates.py` and `src/components/orchestrator.py`. The git HEAD commit 8a9bcfe carries only the direction-AGNOSTIC variant. Live production is running working-tree code.
3. **Exit reconciliation is impossible from logs alone. (Confidence: 100 % for the observation.)** The trade record's `execution` and `exit` fields are both `null` (`trade_record lines 11099-11100`) because `_init_trade_tracking` never ran. Weekly/monthly journal stats will under-count this trade's P&L attribution unless an operator back-fills from MT5 deal history.
4. **Session-summary JSON files have kz_start/kz_end template-leakage bug** (`2026-04-23_tokyo_summary.json` and `2026-04-23_ny_summary.json` both show the NY timestamps even for tokyo summary). Cosmetic, but signals that session_summary save logic has a shared-template bug.
5. **Pre-AI gate skips do not write to live_evaluations jsonl** — any post-hoc audit requiring "what was the MSO at the skipped candle" is forced to reason indirectly (as this report did for §4.4/§4.5). For an observability-critical gate, consider writing a lightweight "gate_skip_<reason>" row to the daily jsonl with minimal MSO digest (bias, OB counts, breaker counts).

### 7.2 Action items (categorized; no changes proposed — read-only report)

**Immediate (bug fix, no CEO approval needed per "bug fixes that prevent function"):**
- Replace `orchestrator.py:492` line with `self.session_state[f"trades_{kill_zone}"] = self.session_state.get(f"trades_{kill_zone}", 0) + 1`, OR delete the line if `trades_<kz>` counter is no longer consumed anywhere. (Confirm consumer via grep.)

**Hygiene (CEO-visible, no trading impact):**
- Commit the directional `pre_ai_gates.py` + corresponding `orchestrator.py` diff with a proper message (e.g. "feat(pre-ai-gate): direction-aware POI availability check").
- Fix session-summary kz_start/kz_end template reuse.

**Reconciliation (requires MT5 history query, not a code change):**
- Operator pulls MT5 deal history for tickets 432844145 (GBPJPY) and the USDJPY ticket to determine actual exit prices and P&L. Back-fill `trade_record` exit fields.

**Observability (future enhancement):**
- Optionally emit a minimal gate-skip row to the daily jsonl (or a sibling `gate_skips.jsonl`) so future audits can verify gate correctness at each skip without forward-reasoning from a neighbouring CANDIDATE MSO.

### 7.3 Confidence ladder

| Claim | Confidence |
| --- | --- |
| Only 1 AI call on GBPJPY Thursday (CANDIDATE at 07:16 UTC) | 100 % |
| Exact gate-skip count = 21 (not 47) | 100 % |
| All gate-skip reasons = `no_unmitigated_bullish_h1_pois` | 100 % |
| The CANDIDATE is a valid, L2-passing fresh H1 OB retest | 100 % |
| Limit triggered at 13:16 UTC NY KZ first candle; fill at 215.176 | 100 % |
| `NameError` crashed the post-fill pipeline | 100 % |
| Position closed by broker at 13:54 UTC | 100 % |
| Position closed via TP1 hit (not SL) | **~65 %** (flagged <80 %) |
| Tokyo skips (samples 1-3) are correct gate behavior | ≥ 95 % |
| First NY skip at 13:30 UTC is correct gate behavior | **~70 %** (flagged <80 %) |
| Final NY skip at 15:30 UTC is correct gate behavior | **~50 %** (flagged <80 %) |
| Zero false-positive gate skips (within the 3 high-confidence samples) | ≥ 95 % |
| Direction-aware gate upgrade is uncommitted | 100 % |

---

## Appendix: Citations

### Code files
- `src/components/pre_ai_gates.py` (working-tree directional variant; uncommitted)
- `src/components/orchestrator.py:490-497` — pre-AI gate invocation
- `src/components/orchestrator.py:488-513` — limit fill handler (kz_trades bug at `:492`)
- `src/components/orchestrator.py:646-654` — eval_logger invocation (only on AI path)
- `src/components/orchestrator.py:2874-2888` — `_log_candle` (in-memory + chart signal; not jsonl)
- `src/components/verification.py:265-386` — `_check_h1_poi_exists`
- `src/components/verification.py:60-104` — `_find_matching_ob`
- `src/components/market_state.py:530-580` — OB mitigation + breaker detection
- `src/components/execution.py:394-444` — `_fill_limit` + `open_position`
- `src/components/execution.py:666-687` — `check_and_manage_trade` (where "no longer exists" is logged)
- `src/components/execution.py:713-748` — `_execute_tp1_partial` (logs "TP1 full close" when OUR code closes)
- `config/agent_config.yaml:258-259` — pre_ai_gates config

### Knowledge base / data files
- `knowledge_base/live_evaluations/GBPJPY/2026-04-23.jsonl` — single row, the CANDIDATE
- `knowledge_base/live_evaluations/GBPJPY/2026-04-20.jsonl` → `.../2026-04-22.jsonl` — weekly context (29/15/5/1 rows)
- `knowledge_base/trade_records/GBPJPY/2026-04-23_london_0716.json` — full MSO+AI+intent; `execution`/`exit` both null
- `knowledge_base/trade_records/GBPJPY/_pending_records_index.json` — still holds `lim_2026-04-23_0716` (stale, never promoted due to the NameError crash)
- `knowledge_base/live_sessions/GBPJPY/2026-04-23_london_summary.json` — miscounts CANDIDATE as NO_TRADE
- `knowledge_base/live_sessions/GBPJPY/2026-04-23_tokyo_summary.json` — also misclassifies kz_start/kz_end
- `knowledge_base/live_sessions/GBPJPY/2026-04-23_ny_summary.json` — 10 evaluations, 9 gate skips, 0 candidates (the 10th evaluation is the fill event which `_log_candle` never got to log)
- `logs/gbpjpy.log` — 2891-line chronological log. All cited line numbers above.
- `shadow_logs/candidate_features_log.jsonl` — contains 1 GBPJPY entry for Thursday (the CANDIDATE)
- `shadow_logs/proximity_shadow_log.jsonl` — contains 1 GBPJPY entry for Thursday

### Git
- `8a9bcfe` (2026-04-20 23:19 CST, Borr1) — committed pre-AI gate (non-directional)
- Working tree `M src/components/pre_ai_gates.py`, `M src/components/orchestrator.py` — uncommitted directional upgrade
- `536c5296` (2026-04-13, Borhen Benltaief) — original `kz_trades` reference at orchestrator.py:492
- `dc4cec2` (session 34) — T2.8 concurrent-cap commit whose comment acknowledges kz_trades is legacy

### Cross-instrument / account context
- `logs/usdjpy.log:2728` — Thursday start account balance $98,026.71
- `logs/usdjpy.log:2934` — Thursday end account balance $99,287.62
- `logs/gbpjpy.log:2597-2687` — GBPJPY's view of the same balance trajectory
- `logs/usdjpy.log:2858-2874` — USDJPY's Thursday trade lifecycle (fill + SL_modification_failed close)
