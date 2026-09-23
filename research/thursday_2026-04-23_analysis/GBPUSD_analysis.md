# GBPUSD — Thursday 2026-04-23 Analysis

**Author:** Data Analyst (GTOS)
**Date of analysis:** 2026-04-24
**Scope:** GBPUSD only, UTC day 2026-04-23 (Thursday)
**Depth:** max
**Mode:** read-only, no code/config changes

---

## Executive summary (5 bullets)

- **Zero AI calls, zero evaluations, zero trades on Thursday.** The GBPUSD live_evaluations jsonl file for 2026-04-23 does not exist; session summaries record 30 candles "evaluated" and 30 "api_calls_made" — but all 30 were terminated by the pre-AI `h1_poi_availability` gate at `no_unmitigated_bullish_h1_pois`. The "api_calls_made" metric is misleading: pre-AI gated candles never reach the Claude API (see `src/components/orchestrator.py:590-597`, accounting bug at `orchestrator.py:2530-2541`).
- **"Observer-only" is a governance label, NOT a code/config enforcement.** GBPUSD runs the full pipeline (same run_agent.py invocation, same redacted_account profile, `risk_per_trade_pct: 1.0%`, `max_concurrent: 4`). The only symbol-specific code behavior is `cross_instrument_context: DISABLED (XAUUSD strip)` — stopping XAUUSD D1 macro from leaking into the GBPUSD prompt. If GBPUSD had produced a clean CANDIDATE that cleared L2 and a limit filled, a real MT5 order would have been sent. This is a gap between chairman policy ("EURUSD/GBPUSD explicitly NO-GO per Chairman" — handoff 36 line 258) and code reality.
- **The pre-AI gate is functioning correctly and saved ~30 API calls.** All 39 Pre-AI skips (30 on 2026-04-23 + 9 late on 2026-04-22) fired with `no_unmitigated_bullish_h1_pois`. GBPUSD's D1 bias has been stuck bullish for days; by Thursday the MSO reported zero unmitigated bullish H1 OBs (the lone 1.34486-1.34616 OB referenced all week had either been mitigated or dropped from the OB list).
- **Process restart churn is normal watchdog behavior, not a crash loop.** 9 GBPUSD bootstrap→shutdown cycles on 2026-04-23 — all driven by orchestrator correctly shutting down after "All kill zones complete, no active trade" when restarted outside its KZ windows, then watchdog re-spawning 15 minutes later. No ERROR/WARNING frames during the active session (08:01 local / 00:01 UTC onward). Only real concern is wasted startup overhead (~30 redundant bootstrap sequences across the day).
- **Latent FA-2 FX-precision issue on GBPUSD is present but masked Thursday.** Last week (2026-04-20 through 2026-04-22), 7 of 11 GBPUSD CANDIDATEs (63%) were REJECTED_L2 on `sl_beyond_ob` — the AI produced SL *above* entry for LONG trades, the same degenerate-params symptom documented for EURUSD (handoff 36 "FA-2 Change 2 under-constrains Sonnet-4-6 on 5dp FX output"). Thursday produced zero CANDIDATEs so the issue did not surface, but it is latent and will fire immediately if the pre-AI gate ever opens.

---

## 1. Observer-mode mechanism (confirmed — there is none at code level)

**Claim under test:** GBPUSD "evaluates but does NOT place trades" (per task brief).

**Finding:** Not enforced by code. GBPUSD is functionally indistinguishable from the 4 other trading instruments in the live fleet.

| Dimension | GBPUSD | Evidence |
|---|---|---|
| Watchdog launches it | Yes | `scripts/watchdog.ps1:39` (in `$SymbolMap`) and `scripts/watchdog.ps1:208` (launched with `--profile redacted_account --mode demo`) |
| Config risk | 1.0% per trade | `config/profiles/redacted_account.yaml:27` (fleet default; no per-instrument override) |
| Gate 0 deployment phase | Passes — phase=3 global | `config/agent_config.yaml:247` (`phase: 3`); `src/components/permissions.py:70-140` treats phase=3 as pass-through for all symbols |
| Per-instrument "trading disabled" flag | **Does not exist** | Grep `src/ config/ -E "observer\|observe_only\|trade_disabled\|trading_enabled"` returns no matches |
| Gate 1 / Gate 3 behavior | Same as other symbols | No GBPUSD-specific branch in `src/components/permissions.py` |
| AI primary analyzer | Same prompt path | Only difference: `cross_instrument_context: DISABLED (XAUUSD strip)` — `src/components/orchestrator.py:1204-1217` and `src/components/primary_analyzer.py:168`. This only strips the XAUUSD D1 macro from the prompt; it does NOT disable GBPUSD trading. |
| Recent limit orders placed | Yes — 5 LIMIT_PLACED in the last week | `logs/gbpusd.log:936, 984, 1051, 1467-1468, 1693-1694, 1758-1759, 1924-1925, 1990-1991`; trade records `knowledge_base/trade_records/GBPUSD/2026-04-{14,15,17,20,21,22}_*.json` with `"final_outcome": "LIMIT_PLACED"` |
| Are those limits real MT5 orders? | Disk-backed pending intents that BECOME real `mt5.order_send` calls when the M15 candle low/high touches the limit price | `src/components/execution.py:477-594` (`check_limit_fill` → `open_trade` → `mt5.order_send`) |
| Any filled trade since Apr 10? | **No — all 5 limits were cancelled at new-day rollover** | `logs/gbpusd.log:1392, 1743, 1778, 1960, 2019` ("Limit intent cancelled (new_day): lim_..."). No "Limit triggered" line has ever appeared in gbpusd.log — price never reached the limit level. |

**Where the "observer" label lives:**
- Comment in `src/components/sprt_monitor.py:38`: `"GBPUSD": {"p0": 0.400, "p1": 0.550},  # Observer — conservative defaults`
- `.context/00_core/quick_reference_card.md:39` ("GBPUSD (observer)") and `:117` (CR TBD — "observer")
- `.context/02_session_handoffs/26_apr18_pre_challenge_tier1_shipped_handoff.md:180` ("5-symbol set locked (XAUUSD, US30, USDJPY, GBPJPY, GBPUSD observer)")
- `.context/02_session_handoffs/36_apr20_FRESH_SESSION_redacted_account_READINESS_VERIFICATION_AND_FA4.md:258`: *"Do NOT enable FX instruments. EURUSD/GBPUSD explicitly NO-GO per Chairman."*
- Memory note: `project_gbpusd_observer_cost.md` — CEO 2026-04-18: "leave GBPUSD running at ~$10/mo, revisit end of April."

**Interpretation:** GBPUSD operates as de-facto observer purely because (a) price has not touched any limit the system placed, and (b) for the last 4-5 days the H1 structure has trapped it in a "bullish bias, OB too far below to retest" state that produces either no CANDIDATE or `sl_beyond_ob` L2 rejects. **If price ever does fill a GBPUSD limit intent in a regime where the AI also produces geometry-valid params, a live trade at 1% risk will be sent.** Confidence: 95%.

**What SHOULD be done (not a proposal, an observation):** If CEO truly wants observer semantics, a deployment.phase-like per-symbol flag or a risk_per_trade_pct=0 override in `redacted_account.yaml` (`instruments.GBPUSD.risk.risk_per_trade_pct: 0`) would enforce it. Neither is in place. **Do not recommend implementing without CEO direction — the CEO-locked policy is "leave as-is through end of April."**

---

## 2. Pre-AI gate skip breakdown

**Total Pre-AI gate skips on gbpusd.log for 2026-04-23:** 30 (all with reason `no_unmitigated_bullish_h1_pois`).

Distribution from session summaries (`knowledge_base/live_sessions/GBPUSD/2026-04-23_*_summary.json`):

| KZ | Candles evaluated | api_calls_made (metric) | Decisions | Rejection reason |
|---|---|---|---|---|
| london | 20 | 20 | NO_TRADE: 20 | `no_unmitigated_bullish_h1_pois`: 20 |
| ny | 10 | 10 | NO_TRADE: 10 | `no_unmitigated_bullish_h1_pois`: 10 |

**Accounting defect found:** `api_calls_made: 20 + 10 = 30` is misleading. Pre-AI-gated candles log with `detail="pre_ai_gate:..."` (orchestrator.py:596) but are NOT excluded from the `api_calls_made` count at `orchestrator.py:2530-2541`. The correct cost view for Thursday is **zero primary AI calls** on GBPUSD (only 2 canary runs, which hit the canary cache). Filing under "observations to flag to CEO"; not proposing a fix in this report.

**Gate reason interpretation (`src/components/pre_ai_gates.py:51-65`):**
- Directional branch fired because D1 bias was "bullish" all Thursday (inherited from the deterministic bias at `orchestrator.py:575`).
- The reason `no_unmitigated_bullish_h1_pois` is emitted when BOTH:
  - No H1 OB with `ob.type == "bullish"` AND `not ob.mitigated`, AND
  - No H1 breaker with `bb.direction == "bullish"` AND `not bb.is_retested`.

**Historical context:** Monday-Wednesday (2026-04-20/21/22), GBPUSD's MSO had exactly 1 unmitigated H1 OB at 1.34486-1.34616 (confirmed via `shadow_logs/candidate_features_log.jsonl` `mso_h1_unmitigated_ob_count: 1`). That OB was referenced in every eval that week. By Thursday 07:00 UTC, the OB either got mitigated by price dipping to it overnight, or the MSO dropped it for touches>=2 / staleness reasons. The candidate_features log has zero GBPUSD entries for Thursday because the pre-AI gate runs BEFORE `log_candidate_features` (`orchestrator.py:590 vs 627`) — so MSO state is not captured on pre-AI-gated candles. This is an observability gap that matters for post-hoc analysis.

**Gate behavior is correct** (never blocks a trade that L2 would pass; mirrors L2's `h1_poi_exists` check per `src/components/pre_ai_gates.py:17-21` docstring). Savings for Thursday: 30 API calls that would have been guaranteed L2 rejects. At ~$0.25-0.35 per Sonnet-4-6 max-effort call, that is ~$7.50-10.50 saved on GBPUSD alone. Confidence: 90%.

---

## 3. Process lifecycle (restart loop explanation)

**Total orchestrator (re)starts on 2026-04-23:** 9 explicit bootstrap sequences in `logs/gbpusd.log`:

| Local time (UTC+8) | UTC equivalent | Lifecycle |
|---|---|---|
| 00:01 | 2026-04-22 16:01 | Boot → `New trading day: 2026-04-22` → `All kill zones complete` → Shutdown (~3 seconds) |
| 00:16 | 2026-04-22 16:16 | Same (Wednesday KZs all past in UTC) |
| 00:31, 00:46, 01:01 | 16:31 / 16:46 / 17:01 | Same churn, 15 min apart |
| 07:46 | 2026-04-22 23:46 | Same (still Wednesday UTC) |
| 08:01 | **2026-04-23 00:01** | Boot → `New trading day: 2026-04-23` → waits idle until London KZ opens at 15:00 local (07:00 UTC). This is the process that ran the entire active day. |
| 23:31 | 2026-04-23 15:31 | Boot post-NY-shutdown → `New trading day: 2026-04-23` → `All kill zones complete` → Shutdown (account balance shown as $99,287.62) |
| 23:46 | 2026-04-23 15:46 | Same, account balance still $99,287.62 |

**Diagnosis:** NOT a crash loop. Expected behavior from:
- `src/components/orchestrator.py` main-loop fragment `"All kill zones complete, no active trade. Ending session."` (visible at log line 2123, 2139, 2155, 2171, 2187, 2203, 2287, 2305, 2321).
- `scripts/watchdog.ps1:82-152` runs every 15 minutes, restarts any symbol not holding a PID lock. Outside the 01:15-07:45 local dead zone, this triggers the churn when an orchestrator gracefully shut down because its KZs were already past for the UTC day it just loaded.
- Log corroboration: `logs/watchdog.log:4164, 4180, 4196, 4212, 4229, 4316, 4334, 5022, 5036` — each `[GBPUSD] STARTED` matches a `Bootstrap complete` line in gbpusd.log seconds later.

**Concern (low severity):** Each bootstrap pays ~0.4s for MT5 connect + economic calendar load + drawdown manager load + cross-instrument context check. 9 redundant bootstraps on Thursday = ~3-4 CPU-seconds + ~9 MT5 reconnects. Trivial resource-wise but a sign that the "session-ended → restart → immediately re-end" cycle wastes cycles. Could be addressed by the watchdog checking whether a fresh start is worthwhile (e.g., is any KZ active or upcoming within 60 min?) — but this is a polish item, NOT a correctness bug, and not in scope for this analysis. Confidence: 90%.

**No crashes on Thursday:** zero ERROR lines, zero WARNING lines other than the benign `economic_calendar` "estimated dates" at each bootstrap. Confidence: 99% (verified via grep on gbpusd.log restricted to `^2026-04-23`).

---

## 4. Was there any evaluation at all Thursday?

**In the strict "AI primary_analyzer was called" sense — NO.** Evidence:
- `knowledge_base/live_evaluations/GBPUSD/2026-04-23.jsonl` does not exist (confirmed by Bash `ls`). Compare to `2026-04-20.jsonl` (4 rows), `2026-04-21.jsonl` (17 rows), `2026-04-22.jsonl` (5 rows).
- `shadow_logs/candidate_features_log.jsonl` has 42 GBPUSD rows total; date distribution (aggregated via python json parse):
  ```
  2026-04-17: 16 (12 NO_TRADE, 4 CANDIDATE)
  2026-04-20: 4  (4 CANDIDATE)
  2026-04-21: 17 (11 NO_TRADE, 6 CANDIDATE)
  2026-04-22: 5  (4 NO_TRADE, 1 CANDIDATE)
  2026-04-23: 0
  ```
  Because `log_candidate_features` sits AFTER the pre-AI gate (orchestrator.py:627 vs 590), pre-AI-gated candles are NOT captured. Thursday's 30 candles produced zero feature rows — an observability gap worth flagging.
- `logs/gbpusd.log` `Canary passed` lines: 2 (15:01:10 UTC+8 = 07:01 UTC and 21:01:09 UTC+8 = 13:01 UTC) — canary only, both cache hits most likely. No line matching `CANDIDATE` or `NO_TRADE:` with a reasoning tail is present for 2026-04-23. No `Limit intent set`, no `Limit triggered`, no `open_trade`.

**In the "MSO + deterministic bias was computed" sense — YES.** The pre-AI gate requires `mso.timeframes["H1"]` to exist and inspects `order_blocks` / `breaker_blocks` (pre_ai_gates.py:45-76), so each of the 30 candles went through:
1. Data ingestion from MT5
2. Component 2 market-state computation (swings, OBs, FVGs, breakers, structure)
3. Pre-screen (passed, otherwise different reason would be logged)
4. News/calendar check (passed — calendar_blocks: [] on both summaries)
5. Deterministic bias check → `bullish` (otherwise reason would not carry `_bullish_` suffix)
6. Pre-AI gate → skip `no_unmitigated_bullish_h1_pois`

No AI-side evaluation, no L2 verification, no trade-capture record. Confidence: 99%.

---

## 5. Bias reconstruction

D1 bias direction for GBPUSD through Thursday: **bullish (stuck)**.

Evidence chain:
| Source | Finding |
|---|---|
| All 30 Thursday Pre-AI gate reasons include `_bullish_` suffix (pre_ai_gates.py:65) | bias = `"bullish"` every candle |
| Last eval row before Thursday (`knowledge_base/live_evaluations/GBPUSD/2026-04-22.jsonl` line 5, 2026-04-22T10:45 UTC) | `daily_bias_direction: bullish`, `daily_bias_confidence: high` |
| Feature log last GBPUSD row (2026-04-22T10:45 UTC) | `daily_bias_direction: bullish`, `mso_h1_structure_direction: bullish`, `mso_h1_unmitigated_ob_count: 1` |
| Session summary `pre_screen.h4_direction` both KZs Thursday | `bullish` |
| Session summary `pre_screen.d1_direction` both KZs Thursday | **`transitional`** |
| Session summary `h4_aligned` | **`false`** (h4 bullish vs d1 transitional) |

**The nuance:** D1 is flagged `transitional` (`swing_sequence: L, H, LL, LH, HL, HH, HL, HH, HL` from 2026-04-22 trade record — uneven highs + lows), not clean bullish. But the deterministic bias function votes bias based on majority/recency of H4 + H1 direction, which were both bullish. Result: bias reported to downstream as `bullish`.

**Implication for the gate:** Bullish bias directed the gate to look ONLY for bullish POIs. If any unretested bearish H1 breaker or unmitigated bearish H1 OB existed Thursday, the gate would not consider them (by design — pre_ai_gates.py:52-63). This is fine behavior given the gate mirrors L2 `h1_poi_exists`.

**Drift risk:** GBPUSD has held bullish bias since at least 2026-04-17 (trade records begin there at `_london_0800.json` with consistent LONG candidates). If H4 has genuinely weakened and the deterministic bias continues saying bullish, the system will miss bearish setups. Without Thursday eval data this can't be re-examined from the jsonl, but the D1 transitional + H4 not-aligned flags warrant monitoring. Confidence: 70% — medium; I have 2026-04-22 data confirming bullish H1 but no live MSO snapshot of Thursday's H1 structure (the gap noted in §4).

---

## 6. Missed setups vs market reality

**Did GBPUSD miss anything Thursday?** This is knowable only from market data, not from GTOS logs — and I do not have broker/TradingView data access for this analysis. What the logs can tell us:

- **No limit-fill event on any day this week.** The one live pending intent active going into Thursday was cancelled on the 2026-04-22 new-day rollover (`logs/gbpusd.log:2019`, cancelled at 2026-04-22 17:46 local = 09:46 UTC). **No new limit was placed Thursday** because no CANDIDATE was produced to create one.
- The repeatedly-cited H1 OB 1.34486-1.34616 has been the ONLY candidate-generating zone for GBPUSD for a week. Price has stayed above it, drifting roughly 1.352-1.353 (inferred from the no_trade_reason strings like "price ~1.35257", "price ~1.35300"). Pipe to this, Thursday's gate firing `no_unmitigated_bullish_h1_pois` means EITHER the MSO finally mitigated that OB (price touched it sometime Wed-Thu) OR it aged out via touches>=2 disqualification OR the H1 structure updated and the OB is no longer tracked.
- The previous CANDIDATE pipeline was producing degenerate-params (see §7) — so even if the pre-AI gate had opened, the AI output would likely have been L2-rejected for the same `sl_beyond_ob` reason as Monday-Wednesday.

**Net answer:** From the log record alone, I cannot assert GBPUSD missed a *tradeable* setup. I can only assert it evaluated zero M15 candles at the AI layer and skipped 30 of them on deterministic structure grounds. Whether those 30 candles hid a valid retest opportunity requires market data cross-reference, which is out of scope for a log-based analysis. Confidence: low on the "did it miss something" question (<60%).

---

## 7. FX precision risk (likely present, masked Thursday)

**Finding:** GBPUSD shows the same FA-2 FX-precision symptoms as EURUSD, except Thursday produced zero CANDIDATEs so the issue is latent rather than visible.

**Evidence from trade_records this week** (`knowledge_base/trade_records/GBPUSD/*.json`, `final_outcome` + `blocked_by` extraction):

| Trade ID | final_outcome | blocked_by |
|---|---|---|
| 2026-04-20_london_0716 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-20_london_0730 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-20_london_0745 | LIMIT_PLACED | — |
| 2026-04-20_ny_1531 | LIMIT_PLACED | — |
| 2026-04-21_london_1000 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-21_london_1015 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-21_london_1045 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-21_london_1100 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-21_london_1115 | REJECTED_L2 | sl_beyond_ob |
| 2026-04-21_london_1130 | LIMIT_PLACED | — |
| 2026-04-22_london_0716 | LIMIT_PLACED | — |

**Totals:** 11 CANDIDATEs → 7 REJECTED_L2 (all `sl_beyond_ob`) → **63.6% L2 reject rate on sl_beyond_ob alone**.

**Example (2026-04-21 london 1000, `trade_records/GBPUSD/2026-04-21_london_1000.json:64-69`):**
```
sl_beyond_ob FAIL: "SL 1.35 is NOT below OB low 1.34 for LONG trade"
mso_value: 1.34486 (OB low)
ai_value:  1.34793 (AI-proposed SL — above OB low and above entry at 1.34616)
```
For a LONG trade, SL must be below OB low (1.34486). The AI proposed 1.34793, which is ABOVE the entry (1.34616) — this is geometrically impossible for a LONG. This is an AI degenerate-params output, exactly what FA-2 set out to fix.

**Per handoff 36 (line 96):** *"EURUSD Jan-Feb (n=175) shows 63% degeneracy → FA-2 Change 2 under-constrains Sonnet-4-6 on 5dp FX output. Live validator catches 59% of EURUSD CANDs → EURUSD disabled anyway per Chairman. Reopen as 'T2.prompt.v2' post-kickoff."*

**GBPUSD observed live n=11 degeneracy rate = 63.6%** — within noise of the EURUSD backtest finding. Same FX precision leak. The FA-2 prompt + validator did NOT fix it for GBPUSD — the trade records above are post-FA-2 (system_version `8a9bcfe` = current HEAD, which already includes `fa35cc0`). However, 4 of 11 did pass L2 — so the validator/prompt does catch SOME, but not enough.

**Prices themselves are clean 5dp** (no `1.25999999`-style degenerate floats). The issue is geometric, not numeric-precision. Sample of LONG CANDIDATE SL/entry from candidate_features_log.jsonl (GBPUSD only):

```
2026-04-20T07:16  entry=1.34616  sl=1.34687  tp1=1.34757   <- SL > ENTRY (INVERTED for LONG)
2026-04-20T07:30  entry=1.34616  sl=1.34775  tp1=1.34854   <- SL > ENTRY
2026-04-20T07:45  entry=1.34616  sl=1.34444  tp1=1.34874   <- valid
2026-04-21T10:00  entry=1.34616  sl=1.34793  tp1=1.34882   <- SL > ENTRY
2026-04-21T10:15  entry=1.34616  sl=1.34491  tp1=1.34804   <- valid
2026-04-21T10:45  entry=1.34616  sl=1.34791  tp1=1.34953   <- SL > ENTRY
2026-04-21T11:00  entry=1.34616  sl=1.34794  tp1=1.34883   <- SL > ENTRY
2026-04-21T11:15  entry=1.34616  sl=1.34791  tp1=1.34953   <- SL > ENTRY
2026-04-21T11:30  entry=1.34616  sl=1.34457  tp1=1.34855   <- valid
2026-04-22T07:16  entry=1.34616  sl=1.34447  tp1=1.34869   <- valid
```
6 of 10 LONG CANDIDATEs (60%) had SL > entry. Same category of failure as EURUSD.

**Risk level:** HIGH latent. Masked on Thursday because the pre-AI gate stopped CANDIDATEs from being produced. The moment the pre-AI gate opens (price revisits the OB zone, or MSO picks up a new bullish H1 OB), this bug will resurface and 60% of CANDIDATEs will be auto-killed at L2. A fraction (~40%) will pass L2 and create real limit intents at 1% risk per trade. **If CEO enables GBPUSD for live trading, this FA-2 leak must be addressed first.** Confidence: 90%.

---

## 8. Cross-instrument context — what is stripped and why

**Log line:** `2026-04-23 08:01:04,251 INFO [src.components.orchestrator] GBPUSD cross-instrument context: DISABLED (XAUUSD strip)` (and identical lines at every bootstrap on Thursday).

**Source:** `src/components/orchestrator.py:1204-1217`.

**What "XAUUSD strip" means:** The cross-instrument-context feature allows one instrument's AI prompt to carry a short summary of another instrument's state — specifically, XAUUSD D1 macro direction (bullish/bearish/unclear) was fed into GBPUSD prompts as a "dollar direction" proxy (gold bullish = dollar weakness = GBPUSD tailwind). Per `config/agent_config.yaml:303-319` the feature is wired (`reference_instrument: XAUUSD`, `reference_timeframe: D1`, `dollar_direction_map`) but **forcefully disabled** via `config/agent_config.yaml:107-112`:
```
cross_instrument_context_disabled_for:
  - GBPUSD
```
The comment at `orchestrator.py:1205-1210` explains the reason:
> "Belt-and-suspenders: symbols in the strip list NEVER receive cross-instrument context (currently XAUUSD D1 macro). Prevents the Apr 13 GBPUSD non-determinism where AI cited 'XAUUSD D1 bearish macro' as the deciding factor despite T7 C-gate forbidding macro reasoning. See handoff 16 §54-59."

**What GBPUSD feeds TO XAUUSD:** Nothing. This feature is one-directional (GBPUSD *would have* consumed from XAUUSD; nothing goes the other way). The strip is pure protection for GBPUSD's prompt.

**Impact on Thursday:** None. Since 0 API calls were made, the prompt-construction logic wasn't exercised. The strip would only matter the next time GBPUSD reaches the AI layer. Confidence: 99%.

---

## 9. Keep-or-kill signals (for end-of-month CEO decision)

**Signals extractable from Thursday alone:**

| Signal | Value |
|---|---|
| Primary AI calls Thursday | 0 |
| Canary AI calls Thursday | 2 (both likely cache-hits; worst case ~$0.10 total) |
| Pre-AI gate skips | 30 (~$7.50-10.50 saved — the gate is doing its job) |
| CANDIDATEs produced | 0 |
| Trade records created | 0 |
| Limit intents placed | 0 |
| Actual MT5 orders sent | 0 |
| Thursday GBPUSD cost to API | ~$0.10 (canary only) |
| L2 reject rate (last 11 CANDIDATEs Mon-Wed) | 63.6% on sl_beyond_ob (FA-2 leak) |

**Signals extractable from the week:**

| Signal | Value |
|---|---|
| CANDIDATEs 2026-04-17 → 2026-04-22 | 15 (per candidate_features_log) |
| LIMIT_PLACED | 4 |
| REJECTED_L2 | 7 |
| Actual fills | 0 |
| Pending intents that survived overnight | 0 (all cancelled at new_day rollover) |

**Implications:**

1. **Pre-AI gate made GBPUSD a very cheap observer Thursday** (~$0.10 vs the ~$7-10 it would have cost without the gate). The gate is functioning as a de-facto cost governor; the instrument-level cost trajectory is now well below the ~$10/mo ceiling CEO set on 2026-04-18.
2. **Zero practical trading signal from Thursday.** The instrument is effectively silent — not because of policy enforcement, but because market structure has kept it silent. This is not a fair test of GBPUSD's current code path.
3. **The FA-2 FX-precision leak (63.6% of CANDIDATEs L2-reject on `sl_beyond_ob`) is the single most important finding.** If end-of-April CEO wants to *promote* GBPUSD to live-tradable, this must be fixed (prompt v2 referenced in handoff 36). If CEO wants to *demote* (stop spending API on observer), that's a separate call driven by cost, not quality.
4. **No crash, no correctness defect, no surprise behavior Thursday.** Telemetry is clean. The only oddities are observability (`api_calls_made` metric lies about pre-AI-gated candles; candidate_features_log silently drops those candles) — both are measurement issues, not trading issues.

**Recommendation (weak, offered only because the brief explicitly asks for one):**

| Option | Rationale | Confidence |
|---|---|---|
| **Keep as-is through 2026-04-30** | CEO-locked policy (memory `project_gbpusd_observer_cost.md`). Thursday cost was ~$0.10. No correctness issues. | 95% |
| If asked to choose post-Apr-30 | Recommend **demote to local-only** (skip API call, keep MSO + SPRT + shadow logging) UNTIL FA-2 prompt v2 + FX precision constraints ship and demonstrate <20% degeneracy on backtest. Running full AI on a 63.6% reject-rate instrument is pure waste. | 70% |

**I am NOT proposing a code change. This is explicitly a data-analyst observation for CEO consumption.**

---

## 10. Anomalies / deferred items

- **`api_calls_made` metric bug:** `orchestrator.py:2530-2541` counts pre-AI-gated candles as "API calls made" even though the gate fires at `orchestrator.py:590-597` before any API call. Not a correctness bug for trading; a reporting bug for cost/activity dashboards. Flagging, not fixing.
- **candidate_features_log silent drop:** `log_candidate_features` sits at `orchestrator.py:627`, after the pre-AI gate early-return. Pre-AI-gated candles are thus invisible to the edge-decay monitors that consume this log. Not a bug per se (the gate's whole point is to pretend those candles didn't exist) but worth noting — analysts reading the feature log may miss a chunk of genuine candle evaluations. Flagging.
- **Watchdog 15-min restart churn:** 9 bootstrap-shutdown cycles on 2026-04-23. Cheap but ugly. A guard in the watchdog ("only start if a KZ is within 60 min of being active") would avoid it. Not proposing the change.

---

## Appendix A — Citations (all paths absolute)

**Pre-AI gate:**
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\pre_ai_gates.py` lines 12-76 (function `h1_poi_availability`)
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\orchestrator.py` lines 590-597 (call site + skip log + early return)
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\orchestrator.py` lines 2530-2541 (api_calls_made counting — includes pre-AI-gated)
- `C:\Users\MSI\Documents\ai-trading-agent\config\agent_config.yaml` lines 258-263 (`pre_ai_gates.h1_poi_availability_enabled: true`)
- `C:\Users\MSI\Documents\ai-trading-agent\config\agent_config.yaml` line 80 (`enabled_frameworks: ["ob_retest"]`)

**Cross-instrument strip:**
- `C:\Users\MSI\Documents\ai-trading-agent\config\agent_config.yaml` lines 107-112 (`cross_instrument_context_disabled_for: [GBPUSD]`)
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\orchestrator.py` lines 1204-1217 (enforcement + justification comment)
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\primary_analyzer.py` line 168 (prompt-side enforcement)

**Permissions / Gate 0:**
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\permissions.py` lines 70-140 (`_reject_if_deployment_phase_blocked` — phase=3 pass-through, fleet-wide)
- `C:\Users\MSI\Documents\ai-trading-agent\config\agent_config.yaml` lines 246-247 (`deployment.phase: 3`)

**Execution / limit lifecycle:**
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\execution.py` lines 463-475 (`set limit intent`)
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\execution.py` lines 477-594 (`check_limit_fill` → `open_trade` → real `mt5.order_send`)

**redacted_account profile:**
- `C:\Users\MSI\Documents\ai-trading-agent\config\profiles\redacted_account.yaml` lines 1-69 (profile — no GBPUSD override)

**Log evidence (GBPUSD Thursday):**
- `C:\Users\MSI\Documents\ai-trading-agent\logs\gbpusd.log` lines 2110-2323 (full 2026-04-23 trace)
- `C:\Users\MSI\Documents\ai-trading-agent\logs\watchdog.log` lines 4156-5038 (GBPUSD watchdog entries 2026-04-23)

**Session / eval state:**
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_sessions\GBPUSD\2026-04-23_london_summary.json` (30 `no_unmitigated_bullish_h1_pois`)
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_sessions\GBPUSD\2026-04-23_ny_summary.json` (10 `no_unmitigated_bullish_h1_pois`)
- (absence of) `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_evaluations\GBPUSD\2026-04-23.jsonl` — file does not exist
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_evaluations\GBPUSD\2026-04-22.jsonl` lines 1-5 (context going into Thursday)
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_features_log.jsonl` (42 GBPUSD rows, zero for 2026-04-23)

**FA-2 precision evidence (pre-Thursday):**
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\trade_records\GBPUSD\2026-04-21_london_1000.json` lines 64-69 (`sl_beyond_ob` FAIL detail, AI proposed SL above entry for LONG)
- Trade record set `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\trade_records\GBPUSD\2026-04-{20,21,22}_*.json` (11 trades: 7 REJECTED_L2, 4 LIMIT_PLACED)
- `C:\Users\MSI\Documents\ai-trading-agent\.context\02_session_handoffs\36_apr20_FRESH_SESSION_redacted_account_READINESS_VERIFICATION_AND_FA4.md` lines 93-97 (FA-2 FX leak docs), line 258 ("EURUSD/GBPUSD explicitly NO-GO per Chairman")

**Observer policy references:**
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\sprt_monitor.py` line 38 (only code-level "Observer" comment)
- `C:\Users\MSI\Documents\ai-trading-agent\.context\00_core\quick_reference_card.md` lines 39, 117
- `C:\Users\MSI\Documents\ai-trading-agent\.context\02_session_handoffs\26_apr18_pre_challenge_tier1_shipped_handoff.md` line 180 (5-symbol set)
- `C:\Users\MSI\Documents\ai-trading-agent\.context\02_session_handoffs\24_apr18_FRESH_SESSION_PROMPT.md` line 45 (CEO decision, leave running to 2026-04-30)

**Git HEAD referenced:**
- Commit `8a9bcfe` (HEAD at time of this analysis) — the system_version tag inside each trade_record metadata, confirming trades are post-FA-2 + pre-AI gate.

**Log timestamp convention note (for future readers):**
- `logs/*.log` timestamps are **local wall-clock on the Windows host (UTC+8)**, NOT UTC. `run_agent.py` does NOT import `src.utils.monitoring_init`, which is the only file that would set `logging.Formatter.converter = time.gmtime`. Evidence: `run_agent.py:63-66` uses vanilla `logging.basicConfig` with default `%(asctime)s`. Reconcile log times with UTC KZ declarations by subtracting 8 hours (e.g., `2026-04-23 15:00:00 local` = `2026-04-23 07:00:00 UTC` = London KZ start per `config/agent_config.yaml:308`).

---

*End of report.*
