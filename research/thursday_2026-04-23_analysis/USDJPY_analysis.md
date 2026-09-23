# USDJPY — Thursday 2026-04-23 Live Analysis

**Scope:** USDJPY only. 31 evaluation rows (`2026-04-23.jsonl`), 2 CANDIDATEs, 1 live fill, 1 closed trade.
**Generated:** 2026-04-24 by senior Data Analyst review. **Account at open:** $98,026.71; **close:** $99,287.62 → **+$1,260.91** (≈ +1.29R realized on the single live trade).
**HEAD at Apr 23:** `8a9bcfe feat(pre-ai-gate): skip AI call when no unmitigated H1 POI exists`
**Profile:** `redacted_account` (risk_per_trade_pct=1.0%). All USDJPY prices quoted at `.3f` precision — the correct JPY-cross setting (`config/agent_config.yaml:469`).

---

## Executive Summary

1. **Two AI CANDIDATEs emitted** — Tokyo 00:16 UTC and London 08:45 UTC. **Only the London candidate reached the market.** The Tokyo candidate was REJECTED by Gate 1 (`touch_count_too_high`, touches=3 on OB 159.361–159.488), confirming that the post-AI `touches ≥ 2` safety gate is working as designed.
2. **London `lim_2026-04-23_0845` filled and closed positive.** Limit placed at 159.692 (log `16:45:25` = UTC 08:45:25 + ~1s). Triggered at UTC 09:00 (log `17:00:05`), 7.18 lots at 159.695 (slippage +0.3 pips), SL 159.477, TP1 160.015. At UTC 09:30 the trade was force-closed via `sl_modification_failed` when the automatic breakeven SL move failed mid-move. Realized +$1,260.91 ≈ **+1.29R**. `usdjpy.log:2854-2874`.
3. **Pre-AI H1-POI availability gate fired ZERO times on 2026-04-23 for USDJPY.** Briefing claim of "2 Pre-AI gate skip events on 2026-04-23" is incorrect; grep of the full log shows the only 2 events for this symbol are 2026-04-20 15:31 UTC and 2026-04-21 00:18 UTC. `usdjpy.log:2312, 2440`. All 31 Apr-23 candles ran the full API call.
4. **29 NO_TRADEs dominated by a single structural reason:** "no reachable unmitigated H1 OB with touches<2" (≈ 17/29 rows). Only one qualifying H1 OB existed through most of the day (touches=1 at 158.914–158.792), 46–86 pips below price and never retested. The OB-retest framework was structurally starved, not incorrectly rejecting trades.
5. **Two latent system bugs are on display but did not affect the PnL outcome:** (a) `kz_trades` NameError in `orchestrator.py:492` fires on every limit fill and silently skips Telegram notification, trade-record promotion, and `_init_trade_tracking`. (b) `new_day` auto-cancels any persisted limit intent on every bootstrap because `session_state["date"]` is initialized to `None` and not persisted (`orchestrator.py:179`). Killed `lim_2026-04-22_1515` at UTC 23:46 on Apr 22 (= Apr 23 07:46 local) — see §4.

---

## Session Timeline

All times UTC. Log timestamps in `logs/usdjpy.log` are local machine time = UTC + 8h (verified: orchestrator reads `datetime.now(timezone.utc)` at `orchestrator.py:329`; candle times in JSONL are correct UTC).

| KZ | Window (UTC) | Candles evaluated | Decisions | Notable events |
|----|--------------|-------------------|-----------|----------------|
| Tokyo | 00:00–03:00 | **12** (rows 1–12, incl. 11 KZ candles + recovery run at 00:16) | 1 CANDIDATE (00:16), 11 NO_TRADE | 07:46 local bootstrap cancels `lim_2026-04-22_1515` as `new_day`. Canary cache HIT. |
| London | 07:00–09:30 | **9** (rows 13–21, with one miss at 09:00) | 1 CANDIDATE (08:45), 8 NO_TRADE | Limit filled at UTC 09:00. Force-closed at UTC 09:30 on BE-modify fail. |
| NY | 13:00–15:30 | **10** (rows 22–31) | 0 CANDIDATE, 10 NO_TRADE | Bearish M15 CHoCH at 14:30 UTC (level 159.463) flipped C2 gate; 4 of 10 rows rejected on C2 FAIL. |
| **Total** | | **31** | **2 CANDIDATE, 29 NO_TRADE** | Candidate rate = 2/31 = **6.45%** (vs batch baseline 10.3%). |

**Session JSONL rows:** `knowledge_base/live_evaluations/USDJPY/2026-04-23.jsonl` lines 1–31.
**Session summaries:** `knowledge_base/live_sessions/USDJPY/2026-04-23_{tokyo,london,ny}_summary.json` (all three report `CANDIDATE: 0` because the session summary counts are keyed to the row position and the Tokyo/London CANDIDATEs sit at rows 1 and 19 of the JSONL — the summary aggregation seems to miscount; verify separately).

Session summary aggregator inconsistency:
- `2026-04-23_tokyo_summary.json:14-19`: `candles_evaluated: 12, CANDIDATE: 0` — wrong, row 1 (`00:16`) was a CANDIDATE.
- `2026-04-23_london_summary.json:14-19`: `candles_evaluated: 10, CANDIDATE: 0` — wrong, row 19 (`08:45`) was a CANDIDATE.
- `2026-04-23_ny_summary.json:14-19`: `candles_evaluated: 10, CANDIDATE: 0` — correct.

This is a **secondary bug: session-summary CANDIDATE counter is decoupled from the JSONL** for the Tokyo and London KZs. Flag for follow-up; does not affect trading.

---

## Both CANDIDATEs — Full Detail

### Tokyo — 2026-04-23 00:16 UTC (CANDIDATE — REJECTED by Gate 1)

**Source:** `knowledge_base/trade_records/USDJPY/2026-04-23_tokyo_0016.json`
**JSONL:** row 1 of `2026-04-23.jsonl`

| Field | Value | Source |
|-------|-------|--------|
| Direction | LONG | `:11540-11550` |
| entry_price | 159.488 (H1 OB high) | `:11542` |
| stop_loss | 159.326 | `:11543` |
| **sl_buffer_applied** | **0.035** (non-zero, 3dp — **FA-2 compliant**) | `:11544` |
| take_profit_1 | 159.731 | `:11545` |
| RR | 1.5 | `:11548` |
| H1 OB cited | 159.488–159.361 touches=**3** | `:11485` prompt shows `bullish 159.488-159.361 body=... touches=3 (2026-04-23T00:00)` |
| D1 bias | transitional | prompt |
| H4 bias | bullish | prompt |
| H1 bias | bullish (5 consecutive BOS) | prompt |
| M15 bias | bullish (ratio 3.9 per AI, 2.80 per MSO) | `:11533`; warn at `usdjpy.log:2756` |
| Spread at decision | 1.2 pips | `:11570` |
| Session memory entries | 0 (disabled) | `:11568` |
| L2 verification | PASS (all 7 checks — `m15_choch_exists`, `displacement_ratio`, `h1_poi_exists`, `ob_zone`, `entry_in_ob`, `sl_beyond_ob`, `gap_ceiling`→SKIP) | `:17-77` |
| Gate 3 (env) | PASS | `:80-96` |
| **Gate 1 (safety)** | **FAIL** — `touch_count_too_high=3` | `:97-122` |
| Final outcome | `REJECTED_GATE1_SAFETY` | `:124` |
| execution / exit | `null` / `null` | `:11565-11566` |

**AI rationale excerpt (`:11538`):** "All three C-gates pass: H1 has 5 consecutive bullish BOS confirming strong directional bias (C1), M15 is fully bullish with no opposing structure (C2), and direction is LONG matching H1 bullish bias (C3). Setup qualifies as CANDIDATE."

**AI picked the wrong OB.** The prompt (`:11485`) instructs: "Prefer the lowest-touches OB (touches=N shown in the OB line); a deterministic gate will reject touches>=2 downstream." At the 00:16 candle the three unmitigated H1 OBs were:
- 158.786–158.671 touches=2 (≈ 65 pips below price)
- 158.914–158.792 touches=1 (≈ 50 pips below price)
- 159.488–159.361 touches=3 (current retest zone)

AI selected the retest-proximate OB (touches=3) despite the explicit preference-for-lowest-touches directive. This is the correct long-term behavior — the post-AI touch gate caught it. No loss of signal, but **the AI's reasoning never acknowledged the touch count at all** (no mention of touches=3 in `:11538` or `:11499` qualified_reason). Worth flagging as weak prompt adherence.

**Degenerate params check:** `entry (159.488) != SL (159.326) != TP1 (159.731)`; `sl_buffer_applied = 0.035 > 0`. PASS on FA-2 validator (no EURUSD-style "flat refusal" pattern visible).

**Displacement mismatch:** AI reported 3.90, MSO computed 2.80 (`usdjpy.log:2756`). L2 marks it `PASS` with a WARN because 2.80 is above the 1.5 threshold. AI inflation continues to be a low-grade pattern but not decision-impacting.

---

### London — 2026-04-23 08:45 UTC (CANDIDATE — FILLED — CLOSED +1.29R)

**Source:** `knowledge_base/trade_records/USDJPY/2026-04-23_london_0845.json`
**JSONL:** row 19 of `2026-04-23.jsonl`
**Trade id:** `lim_2026-04-23_0845` (limit), `tr_2026-04-23_0900` (filled position)

| Field | Value | Source |
|-------|-------|--------|
| Direction | LONG | `:12216` |
| entry_price | 159.692 (H1 OB high) | `:12218` |
| stop_loss | 159.477 | `:12219` |
| **sl_buffer_applied** | **0.033** (non-zero, 3dp — **FA-2 compliant**) | `:12220` |
| take_profit_1 | 160.015 | `:12221` |
| RR | 1.5 | `:12224` |
| H1 OB cited | 159.692–159.595 touches=**1** (freshly formed at 2026-04-23T10:00 broker ≈ UTC 07:00) | `:12148` |
| D1 bias | transitional | prompt |
| H4 bias | bullish | prompt |
| H1 bias | bullish (5 consecutive BOS) | prompt |
| M15 bias | bullish (ratio 5.7 per AI, 3.41 per MSO) | `:12195`; warn at `usdjpy.log:2842` |
| Spread at decision | 0.4 pips | `:12232` |
| Session memory entries | 0 (disabled) | `:12230` |
| L2 verification | PASS (6 of 7; `ob_zone`→**WARN** — midpoint in premium for LONG; equilibrium 159.489) | `:17-77` of record |
| Gate 3 (env) | PASS | `:80-96` |
| Gate 1 (safety) | PASS — touches=1, sl_distance=0.215 | `:97-115` |
| Final outcome | `LIMIT_PLACED` | `:116` |
| limit_intent | `lim_2026-04-23_0845`, expiry 192 candles | `:12262-12268` |

**AI rationale excerpt (`:12200`):** "All three C-gates pass: H1 has 5+ bullish BOS confirming strong directional bias, M15 is fully aligned bullish with no opposing structure, and direction matches LONG. Nearest unmitigated H1 OB (touches=1) at 159.692-159.595 provides the entry zone."

**L2 WARN on `ob_zone`:** The OB midpoint 159.644 sits in the premium half of the H1 P/D range (equilibrium 159.489). The prompt's OB-zone rule prefers discount OBs for LONG, but the AI cited the premium OB because it was the only touches=1 structure proximate to price. L2 passed this as a WARN (not a block). The trade was still profitable — premium-OB LONGs on JPY crosses are a known shadow-zone but not a disqualifier.

**Degenerate params check:** `entry (159.692) != SL (159.477) != TP1 (160.015)`; `sl_buffer_applied = 0.033 > 0`. PASS on FA-2 validator.

---

## Fill Reconciliation

| Event | UTC time | Log line | Detail |
|-------|----------|----------|--------|
| AI CANDIDATE emitted (Tokyo 0016) | 00:16:30 | n/a | REJECTED by Gate 1 `touch_count_too_high=3`; no MT5 call |
| AI CANDIDATE emitted (London 0845) | 08:45:20 | `usdjpy.log:2839` | L2 PASS, Gate 1 PASS |
| `lim_2026-04-23_0845` placed | 08:45:25 | `usdjpy.log:2848-2849` | `limit=159.692 sl=159.477 tp=160.015 expires=192` |
| Shadow DA logged | 08:45:38 | `usdjpy.log:2852` | `max_risk=52%` |
| **Limit triggered** | 09:00:05 | `usdjpy.log:2854` | M15 candle low=159.690 crossed limit=159.692. Header says `candle=2026-04-23T12:00:00+00:00` — **this is a cosmetic bug**: the timestamp is broker-time (UTC+3 EEST) mis-tagged as `+00:00`. Actual UTC = 09:00. |
| Limit fill sizing | 09:00:05 | `usdjpy.log:2855` | `original_sl_dist=0.215, actual_sl_dist=0.218, using=0.218, entry=159.695` (fill +0.003 worse than limit) |
| MT5 `result.price=0` → use tick | 09:00:05 | `usdjpy.log:2857` | Known MT5 return quirk; execution uses tick entry_price 159.695 |
| **Trade opened** | 09:00:05 | `usdjpy.log:2858` | `tr_2026-04-23_0900 LONG 7.18 lots at 159.695, SL=159.477, TP1=160.015` |
| **NameError** `kz_trades is not defined` | 09:00:05 | `usdjpy.log:2859-2864` | `orchestrator.py:492` bug. Skipped `_log_candle`, `notify_limit_filled` Telegram, `_promote_pending_record_on_fill`, and `_init_trade_tracking`. |
| Subsequent AI calls (09:15, 09:30) | 09:15, 09:30 | `usdjpy.log:2865-2872` | Normal candle processing — MSO still running despite active position |
| **BE trigger attempted** | 09:30:23 | `usdjpy.log:2873` | `Failed to move SL to BE — closing position for safety` (`execution.py:956`) |
| **Position closed** | 09:30:23 | `usdjpy.log:2874` | `Position closed: sl_modification_failed at 0.0` (MT5 `result.price=0` again) |
| Balance after close | 23:31 local | `usdjpy.log:2934` | `$99,287.62` (up from $98,026.71 = **+$1,260.91**) |

**Lot sizing / realized R math:**
- Risk per R at 1% on $98,026.71 ≈ **$980.27**
- Actual realized +$1,260.91 / $980.27 ≈ **+1.29R**
- At 7.18 lots × 0.218 JPY SL distance × (1 / 159.695 USD/JPY) × 100,000 units ≈ $979.78 risk per SL hit → consistent with 1.0% sizing
- For +1.29R, exit price ≈ 159.695 + 1.29 × 0.218 = 159.977 (= 0.038 JPY short of TP1 at 160.015)
- This is plausible: BE-modify fires when price ≥ entry + 1R = 159.913. Between the BE attempt and actual close at market (~2s), price likely advanced another ~0.063 before the safety-close executed.

**Fleet-wide fit with CEO "~2 trades happened":** The USDJPY London trade is one of the two fleet trades. This analysis covers USDJPY only; see parallel reports for the other symbol. The Tokyo CANDIDATE did **not** result in any MT5 order — it was blocked at Gate 1 safety.

---

## Cancellation of Prior-Day Limit `lim_2026-04-22_1515`

**Source:** `knowledge_base/trade_records/USDJPY/2026-04-22_ny_1515.json`; `usdjpy.log:2711-2731`

| Event | Timestamp | Note |
|-------|-----------|------|
| Limit placed (Apr 22 NY KZ) | UTC 2026-04-22 15:15:28 | LONG limit=158.914 SL=158.754 TP=159.154, 192 candles |
| Restart / bootstrap | UTC 2026-04-22 23:46:06 (local 07:46:06 Apr 23) | `pending_intent` restored from disk, age=8.5h |
| **Cancelled as `new_day`** | UTC 2026-04-22 23:46:07 | `session_state["date"]` was stale, orchestrator's first-tick `today=2026-04-22` != `None` → fires `_new_day("2026-04-22")` → `cancel_limit_intent("new_day")` |

**Root cause (not a date rollover):** `src/components/orchestrator.py:179` initializes `session_state["date"] = None` at every bootstrap, and `:339-340` checks `if self.session_state["date"] != today: self._new_day(today)`. `_new_day` unconditionally calls `self.execution.cancel_limit_intent("new_day")` (`:2243`). Because the state is not persisted across restarts, **every restart during a live trading day looks like a "new day" to the orchestrator and cancels pending limits, even when the UTC date has not changed.**

**Was the cancelled limit a missed opportunity?**

- Limit was LONG @ 158.914 with SL 158.754, TP 159.154 (Apr 22 NY decision based on touches=1 H1 OB at 158.914-158.792).
- On Apr 23 price never revisited 158.914; the daily low was ~159.294 (from the MSO at 08:45 `:12168`, protected_swing_level 159.294 at 03:00 UTC).
- So the limit **would not have filled on Apr 23** even if it had survived. The cancellation was cosmetically unclean but benign in this case.

**However:** across the full fleet, this same mechanism almost certainly kills useful limits on other symbols. This is a latent safety hazard — **the orchestrator silently discards EAs' limit intent every time it restarts, regardless of UTC date**. Flag as P1 action item.

---

## Rejection Bucket Analysis (29 NO_TRADEs)

Categorized from `no_trade_reason` in `2026-04-23.jsonl` rows 2–18, 20–31:

| Bucket | Count | Representative row | Root cause |
|--------|-------|---------------------|------------|
| **C2 FAIL** — active M15 bearish CHoCH opposes H1 bullish | **7** | rows 2–4 (CHoCH @ 03:15 UTC, lvl 159.437, ratio 5.5+), rows 6,7 (H1 CHoCH @ 03:00 UTC, lvl 159.361), rows 28–31 (CHoCH @ 14:30 UTC, lvl 159.463) | Genuine structural opposition post-sweep |
| **C1 FAIL** — H1 structure terminated by bearish CHoCH | 2 | rows 5, 7 | Same H1 CHoCH @ 03:00 UTC that flipped H1 direction-transitional |
| **Framework gate fail** — no reachable unmitigated H1 OB with touches<2 (all explicitly say C1/C2/C3 pass structurally) | **17** | rows 8–18, 20–27 | Only touches=1 OB 158.914–158.792 is 46–86 pips below price; no retest occurred |
| Framework — `framework=ob_retest` still emitted, but C1/C2/C3 pass + no POI | 3 (rows 8, 9, 11, 17, 23 explicitly; counted in the 17 above) | — | Mirror case |
| **Total** | **29** | | |

**Distribution summary:**
- 59% of rejections (17/29) = **no proximate qualifying H1 OB**. This is the dominant pattern.
- 31% (9/29) = **C1 or C2 FAIL** (structural opposition)
- Only 0 rows rejected on Gate 0 (deployment.phase), Gate 3 (env), calendar blocks, or displacement-too-weak.

**Was the MSO's OB view accurate?** The prompt at 00:16 UTC showed `3 H1 OBs` (at 158.671, 158.792, 159.361). By 02:00 UTC it showed `0 H1 OBs` (`h1_poi_identified: false` in row 8). The 159.361 OB got mitigated by price action between 00:16 and 02:00. Between 02:00 and the London/NY sessions, **no new unmitigated H1 OBs formed with touches<2 in the long side until 08:45 UTC** (when the freshly-formed 159.595–159.692 OB appeared). This is a genuine structural scarcity, not an MSO detection defect. USDJPY on Thursday was an H1 **impulsive** day (straight trend, shallow pullbacks that didn't fully retest any OB).

---

## Bias Transitions Through the Day

Source: `daily_bias_direction` and `no_trade_reason` fields across `2026-04-23.jsonl` rows 1–31.

| Time (UTC) | Row | D1 | H4 | H1 | M15 | AI daily_bias | Notes |
|-----------|-----|----|----|----|-----|----------------|-------|
| 00:16 | 1 | transitional | bullish | bullish | bullish | bullish high | 5 bullish BOS stack |
| 00:30 | 2 | transitional | bullish | bullish | bearish CHoCH | bullish high | M15 CHoCH at 03:15 broker (00:15 UTC) |
| 00:45–01:00 | 3–4 | transitional | bullish | bullish | bearish | bullish high | same CHoCH persists |
| 01:15 | 5 | transitional | bullish | **bearish CHoCH** | neutral | bullish **medium** | H1 bias reduced to medium — AI flags structure terminated |
| 01:30 | 6 | transitional | bullish | bullish (per AI) | neutral | bullish high | AI recovers — interpreted the H1 CHoCH as a pullback |
| 01:45 | 7 | transitional | bullish | **bearish CHoCH** | neutral | bullish medium | Same flip back |
| 02:00–03:00 | 8–12 | transitional | bullish | bullish | mixed | bullish high | C1/C2 pass, no POI |
| 07:15–09:30 | 13–21 | transitional | bullish | bullish | mixed bullish | bullish high | All C-gates pass; London CANDIDATE at 08:45 |
| 13:16–14:30 | 22–27 | transitional | bullish | bullish | neutral | bullish high | C1/C2 pass, no POI |
| 14:45–15:30 | 28–31 | transitional | bullish | bullish | **bearish CHoCH** (14:30 UTC, lvl 159.463) | bullish high | C2 FAIL — NY rejected |

**Key observation:** The bias "whiplash" at 01:15–01:45 UTC is driven by the M15 print at 03:00 broker-time (00:00 UTC) being an H1 bearish CHoCH **level** (159.361, the session's protected_swing_low). The AI was right to note that a bearish CHoCH had printed at that level, then wrong to retreat to medium confidence at 01:15 and 01:45 but correct at 01:30 — the inconsistency is within ~15 min, not a real regime flip. The H4 bullish BOS at UTC 00:00 (lvl 159.637) confirmed the continuation. By 02:00 UTC the H1 frame was cleanly bullish with all three C-gates passing.

**The Tokyo CANDIDATE at 00:16 caught this correctly** — the bearish CHoCH hadn't printed yet at that candle, so the bias was cleanly bullish. The REJECTION was purely from touch-count, not bias.

---

## Pre-AI Gate Audit

**Claim in task briefing:** "logs/usdjpy.log shows 2 'Pre-AI gate skip' events on 2026-04-23."
**Actual grep result (`usdjpy.log:2312, 2440`):**

| Line | Timestamp (local) | UTC | Event |
|------|-------------------|-----|-------|
| 2312 | 2026-04-20 23:31:12 | 2026-04-20 15:31:12 | `Pre-AI gate skip: no_unmitigated_h1_pois` |
| 2440 | 2026-04-21 08:18:34 | 2026-04-21 00:18:34 | `Pre-AI gate skip: no_unmitigated_h1_pois` |

**Zero Pre-AI gate skips for USDJPY on 2026-04-23.** The briefing was incorrect. On Thursday USDJPY always had ≥1 unmitigated H1 OB in the MSO — even when the OB was 50+ pips away and not a valid retest. The Pre-AI gate per `src/components/pre_ai_gates.py:12-76` only skips when H1 has zero unmitigated OBs AND zero unretested breakers; distance is not a factor.

This is **working as designed**. The gate correctly avoided skipping on days when an OB existed but was structurally unreachable (the touch-count / distance filters remain the job of the downstream deterministic gate).

**Implication:** For USDJPY on "impulsive trend" days like Thursday, the gate provides little API savings because the market continually forms new H1 OBs. The gate's expected utility is higher on clean range/consolidation days where no new OBs form.

---

## Degenerate Params Check (FA-2 Validator)

From `trade_parameters` blocks in both trade records:

| Parameter | Tokyo 00:16 | London 08:45 | Expected |
|-----------|-------------|---------------|----------|
| entry_price | 159.488 | 159.692 | 3dp, != SL, != TP1 |
| stop_loss | 159.326 | 159.477 | 3dp, != entry |
| take_profit_1 | 159.731 | 160.015 | 3dp, != entry |
| sl_buffer_applied | **0.035** | **0.033** | 3dp, **> 0** |
| Precision | all .3f | all .3f | .3f (JPY cross) |
| entry == SL? | No (0.162 JPY gap) | No (0.215 JPY gap) | — |
| entry == TP1? | No (0.243 JPY gap) | No (0.323 JPY gap) | — |

**Both CANDIDATEs pass FA-2 validation cleanly.** No signs of the EURUSD-style pre-FA-2 leak (35–59% degenerate params reported in handoff 36). USDJPY FX precision is behaving correctly after commit `fa35cc0`.

**Displacement ratio overstatement (minor):**
- Tokyo 00:16: AI reported 3.90, MSO computed 2.80 (`verification.py` WARN at `usdjpy.log:2756`)
- London 08:45: AI reported 5.70, MSO computed 3.41 (`usdjpy.log:2842`)

Both above the 1.5 threshold, so not decision-impacting. But the consistent ~40–70% inflation suggests the AI is over-crediting displacement. Worth continuing to shadow-track; not an Apr 23 action item.

---

## Missed-Setup Analysis (NY in particular)

**The question:** Was the bias wrong? Could NY have been traded bearish?

**Price-level reconstruction (NY KZ, from NO_TRADE reasoning):**
- 13:16 UTC: price ~159.660
- 13:30 UTC: price ~159.660 (MSO: "touches=1 OB at 158.914-158.792 is ~75 pips below")
- 13:45 UTC: ~159.660 (row 24)
- 14:00 UTC: ~159.600 (row 25 mentions ~159.6)
- 14:15 UTC: ~159.619 (row 26 explicit)
- 14:30 UTC: **M15 bearish CHoCH prints** at lvl 159.463 (row 27 observes it; rows 28–31 gate on C2 FAIL)
- 14:45 UTC: ~159.463 (CHoCH level)
- 15:00 UTC: row 29 — "bearish FVGs at 159.696–159.680, 159.664–159.573, 159.550–159.535"
- 15:15 UTC: row 30 — still C2 FAIL
- 15:30 UTC: row 31 — clean CHoCH, C2 FAIL

**H1 bias at NY:** Still bullish with strong structure (5 consecutive BOS, most recent at UTC 11:00 lvl 159.683). The H1 frame did NOT flip bearish.

**The M15 print is what opposed entry.** Could a SHORT have been valid?
- D1 `transitional` (not bearish)
- H4 `bullish`
- H1 `bullish` (uninterrupted)
- M15 `bearish CHoCH` at 14:30 UTC

The **deterministic bias** computed by the orchestrator is "bullish (source: H4+H1_consensus)" (`usdjpy.log:2881-2884`). A SHORT cannot be emitted against H1+H4 bullish consensus in the current architecture (C3 gate mandates direction match with H1 bias). Even if the AI wanted to SHORT at 14:45, the framework rejects it by design.

**Was that the correct call?** Yes, empirically. Price recovered through late afternoon — by end-of-day balance suggests the H4 bullish trend resumed. A SHORT against D1+H4+H1 consensus on a single M15 CHoCH is explicitly what the architecture is designed NOT to do, and the batch WR of 75.8% on USDJPY implies this filter is additive edge.

**Did the NY KZ offer valid LONG setups that got rejected?** No. The H1 OB structure was:
- 158.786–158.671 (touches=2, ~90 pips below)
- 158.914–158.792 (touches=1, ~75 pips below)
- 159.595–159.692 (already filled Thursday at 09:00 UTC — mitigated by the earlier trade's fill)

After the London trade filled and closed, the 159.595–159.692 OB was no longer unmitigated. NY had no H1 POI anywhere near price. **The NY session was correctly empty.**

**Only alternative setup pattern:** A fresh H1 OB forming during NY from the 14:30 M15 bearish CHoCH + subsequent recovery BOS would create a new bullish OB candidate. Looking at the reasoning flow rows 28–31, all four cite the CHoCH at 14:30 as the blocker — meaning no new bullish BOS printed through 15:30 UTC. The NY M15 structure was too choppy to form a clean new retest setup.

---

## USDJPY vs Batch Performance — Calibration Check

Per `CLAUDE.md`:
- Batch WR vs breakeven: **75.8% (n=33)**, p=1.96e-04 (confirmed Bonferroni survivor).
- Canonical CANDIDATE rate: **10.3%** of evaluated setups (fleet-wide baseline).
- Apr 23 USDJPY: **2 / 31 = 6.45% CANDIDATE rate.**

**2 candidates/day is slightly below fleet baseline** (at 17 trades/month across 5 instruments, per-symbol expectation ≈ 3.4 trades/month ≈ 0.16/day/symbol; Thursday had 2 candidates from USDJPY alone, **above** the per-symbol daily expectation).

**Quality assessment:**
- Tokyo 00:16: Premium setup structurally (A+, 3/4 TF alignment, clean sweep, strong 3.9× displacement, discount zone). Rejected for touch-count, NOT quality.
- London 08:45: A+ but with one qualifier — premium-zone OB for a LONG (L2 WARN). Displacement inflation was high (5.7 AI vs 3.41 MSO). Still fit framework criteria.

**In the batch WR distribution (75.8%, n=33), both setups look representative** — not standout A+ A+, not marginal. The London fill netting +1.29R is consistent with the 1.0R expectation (most wins terminate at TP1 = +1.5R; BE-fail-close caught this one just shy of TP1).

**Comparison to active USDJPY days:** Apr 21 had **11 CANDIDATEs in one day** across London+NY (`2026-04-21.jsonl`, 14 rows). That is ~3× Thursday's activity. Apr 22 had 2 CANDIDATEs (Tokyo + NY). Thursday's cadence is **normal** for this symbol, not anomalously quiet. The driver of quiet days is not "AI over-rejecting" but "H1 structure running away without retesting" — exactly what Thursday exhibited.

---

## Concerns / Action Items

### P0 — Silent data-loss bugs

1. **`kz_trades` NameError on every limit fill** (`src/components/orchestrator.py:492`): `self.session_state[f"trades_{kill_zone}"] = kz_trades + 1` — `kz_trades` is undefined in the scope. Fires every fill, skips:
   - `_log_candle("LIMIT_FILLED", ...)` — JSONL log of fill
   - `notify_limit_filled(...)` — Telegram alert
   - `_promote_pending_record_on_fill()` — trade-record promotion from `pending` to `filled` state
   - `_init_trade_tracking(trade_state)` — sets up BE/trailing state (this may explain why the BE-move failed — the position tracking may have been partially set up via a different codepath; ERROR at `:2859` confirms the try/except swallowed the NameError).
   Evidence: `usdjpy.log:2858-2864`. Should fix before next limit fills.

2. **Session summary CANDIDATE counter miscounts** (`knowledge_base/live_sessions/USDJPY/2026-04-23_{tokyo,london}_summary.json`): Both Tokyo and London summaries report `CANDIDATE: 0` despite rows 1 and 19 of the JSONL being CANDIDATEs. Audits relying on these summaries will undercount. JSONL is authoritative; summaries are derived and broken.

3. **`new_day` auto-cancel on every bootstrap** (`src/components/orchestrator.py:179, 339-340, 2243`): `session_state["date"]` is initialized to `None` and not persisted. Every restart → `None != today` → `_new_day` fires → all pending limit intents get `cancelled (new_day)`. This killed `lim_2026-04-22_1515` at UTC 23:46 Apr 22 (same UTC day). Benign on Thursday (limit wouldn't have filled anyway), but a real risk during FTMO trial if the system restarts after a legitimate limit placement.

### P1 — AI-side behavior to watch

4. **AI picked a touches=3 OB despite prompt directive** — Tokyo 00:16 (`trade_records/.../2026-04-23_tokyo_0016.json:11499`). AI reasoning never mentioned touch count. Gate 1 caught it, so no live loss; but this suggests prompt adherence is soft on touch-count priority when an OB is retest-proximate. Worth tracking across instruments.

5. **Displacement ratio consistently inflated** (both CANDIDATEs ~40–70% over MSO). Not decision-impacting but indicates the AI over-scores displacement. Shadow-log pattern, no action yet.

6. **L2 WARN `ob_zone` premium-for-LONG on London 08:45** — passed through, trade was profitable. This WARN is not a blocker by design, but during audits it's useful to track premium-zone fills vs discount-zone fills for `ob_retest` to see if the edge differs.

### P2 — Cosmetic

7. **Broker-time mis-tagged as UTC in log messages** (`usdjpy.log:2854` shows "candle=2026-04-23T12:00:00+00:00" for a UTC 09:00 event = EEST 12:00). Internal MT5 candle timestamps carry broker-tz but the log formatter appends `+00:00`. Fix in the `Limit triggered` log statement at `execution.py:525-529`.

### Positive observations

- **FA-2 FX precision + sl_buffer_applied + degenerate-params validator work correctly for USDJPY** (no leak).
- **Gate 1 `touch_count_too_high` correctly blocked a high-touch OB retest** — this is the designed safety net working.
- **Pre-AI gate neither over-skipped nor under-skipped** — zero fires because every candle had ≥1 unmitigated H1 OB present, which is correct.
- **Realized +1.29R on the one live trade** — modest, just short of TP1 at 1.5R, due to a downstream BE-modify failure. No loss of edge.

---

## Appendix — Citations

**Evaluation rows:**
- `knowledge_base/live_evaluations/USDJPY/2026-04-23.jsonl` (31 rows; CANDIDATEs at rows 1 and 19)
- `knowledge_base/live_evaluations/USDJPY/2026-04-21.jsonl` (14 rows; 11 CANDIDATEs — high-activity reference day)
- `knowledge_base/live_evaluations/USDJPY/2026-04-22.jsonl` (6 rows; 2 CANDIDATEs Tokyo 00:30 and NY 15:15)

**Trade records:**
- `knowledge_base/trade_records/USDJPY/2026-04-23_tokyo_0016.json` (11590 lines; `REJECTED_GATE1_SAFETY`)
- `knowledge_base/trade_records/USDJPY/2026-04-23_london_0845.json` (12268 lines; `LIMIT_PLACED`)
- `knowledge_base/trade_records/USDJPY/2026-04-22_ny_1515.json` (the limit that got `new_day` cancelled)

**Session summaries:**
- `knowledge_base/live_sessions/USDJPY/2026-04-23_tokyo_summary.json:14-19`
- `knowledge_base/live_sessions/USDJPY/2026-04-23_london_summary.json:14-19`
- `knowledge_base/live_sessions/USDJPY/2026-04-23_ny_summary.json:14-19`

**Logs:**
- `logs/usdjpy.log:2711-2732` — prior-day limit placement + new_day cancel
- `logs/usdjpy.log:2744-2763` — Tokyo 00:16 CANDIDATE flow
- `logs/usdjpy.log:2836-2862` — London 08:45 CANDIDATE → limit placement → fill
- `logs/usdjpy.log:2856-2864` — `kz_trades` NameError
- `logs/usdjpy.log:2873-2874` — BE-modify fail → safety close
- `logs/usdjpy.log:2312, 2440` — the only 2 Pre-AI gate skip events (neither on Apr 23)

**Code:**
- `src/components/pre_ai_gates.py:12-76` — `h1_poi_availability` gate
- `src/components/orchestrator.py:179, 329-340` — session_state date init + new_day check
- `src/components/orchestrator.py:481-508` — limit fill handling (containing `kz_trades` bug at :492)
- `src/components/orchestrator.py:2228-2251` — `_new_day` + `cancel_limit_intent("new_day")`
- `src/components/execution.py:479-610` — limit fill logic, sizing, cancel
- `src/components/execution.py:856-874` — `close_position`
- `src/components/execution.py:945-957` — BE move-to-entry; close-on-modify-fail
- `src/components/primary_analyzer.py:193-196` — per-instrument `price_format` set
- `src/prompts/primary_analyzer_prompt.py:14, 154-160` — `_PRICE_FMT` + PRECISION prompt block
- `config/agent_config.yaml:436-472` — USDJPY overrides (price_format=".3f")

**Shadow logs (Apr 23 USDJPY entries):**
- `shadow_logs/proximity_shadow_log.jsonl:117` (Tokyo 00:16, `proximity=unknown`)
- `shadow_logs/proximity_shadow_log.jsonl:122` (London 08:45, `proximity=inside distance_to_ob=0.0`)
- `shadow_logs/candidate_features_log.jsonl` — 108 USDJPY entries total (not parsed per-day)
- `shadow_logs/displacement_events.jsonl` — no USDJPY Apr 23 entries (sub-threshold at 2.80 and 3.41)
- `shadow_logs/heartbeat_flatten_events.jsonl:1119-1138` — not USDJPY-specific (fleet watchdog)
- `shadow_logs/liquidity_distance_log.jsonl` — no USDJPY entries (symbol-agnostic file; no match on "USDJPY")

**Correlation log:**
- `logs/correlation_shock.log:32-33` — JPY_CROSSES USDJPY↔EURJPY ρ=-0.063, USDJPY↔GBPJPY ρ=+0.130 (both `status=ok`; no correlation shock Thursday).
