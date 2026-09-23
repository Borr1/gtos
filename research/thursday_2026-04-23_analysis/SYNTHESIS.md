# Thursday 2026-04-23 — Fleet Analysis Synthesis

**Author:** Claude Code (Opus 4.7, max effort) — synthesis of 6 parallel deep-dive agents
**Scope:** Full forensic review of Thursday's live trading session — redacted_account $100K demo, 4 live + 1 observer instrument
**Date produced:** 2026-04-24
**Per-instrument reports:** `XAUUSD_analysis.md`, `US30_analysis.md`, `USDJPY_analysis.md`, `GBPJPY_analysis.md`, `GBPUSD_analysis.md`
**Cross-cutting report:** `system_forensics.md`

---

## Executive summary (read this first)

1. **Fleet P&L Thursday: +$1,260.91 (+1.29%)** on 2 filled trades. Account $98,026.71 → $99,287.62. Both trades are LONG (USDJPY + GBPJPY); XAUUSD/US30/GBPUSD had zero fills.
2. **Both fills hit a pre-existing P0 bug** (`kz_trades` NameError at `orchestrator.py:492`, from commit `dc4cec2` T2.8) that silently skipped Telegram notifications, trade-record promotion, and BE-tracking init. **Recovered via fallback paths**, but lifecycle state is incomplete and Telegram alerts for both fills were silently dropped. This is the #1 fix.
3. **Pre-AI gate (committed in `8a9bcfe`) is running an UNCOMMITTED upgrade** in live production. The direction-aware version (gating on bias direction, not just any POI) is in the working tree only — `git diff HEAD` shows the diff. Watchdog restart picked it up; live pipeline depends on uncommitted code. Gate is semantically correct (verified against L2 — actually STRICTER than L2, so cannot false-block), but process discipline has broken.
4. **The gate is working as intended and is NOT over-blocking.** Verified via sampled MSO reconstructions across all 5 instruments; zero false-positive skips found. GBPJPY's weekly eval count fell 29→15→5→1 Mon-Thu, exactly as the gate was designed to do.
5. **All 6 US30 CANDIDATEs were correctly rejected by L2.** 4 London CANDIDATEs were AI hallucinations (Sonnet cited an M15 OB as "the H1 POI" because all real H1 OBs had touches≥2 — the AI's own rationale explicitly admits "(M15, touches=1)"). L2 `h1_poi_exists` caught them. Counterfactual: all 4 would have SL'd out for ~4R of loss.
6. **Directional concentration risk (MEDIUM/HIGH):** 98%+ bullish bias across the 4 live instruments in April. ZERO bearish CANDIDATEs since redacted_account kickoff (Apr 20). Either genuine regime or a structural bullish bias in `market_state.compute_market_state`. Cannot distinguish within this audit's scope — deserves a dedicated deep-dive.
7. **GBPUSD "observer-only" is a label, not a gate.** Same 1% risk, same pipeline, same `mt5.order_send` capability. The only thing blocking GBPUSD trades is the pre-AI gate — a cost governor, not a safety barrier. If the gate ever opens on GBPUSD and a CANDIDATE passes L2, it WILL trade.
8. **FA-2 (FX precision fix) did NOT land on GBPUSD.** 11 CANDIDATEs from last week show 63.6% REJECTED_L2 on `sl_beyond_ob` — geometrically impossible SL>entry for LONG. Masked Thursday only because the gate suppressed all CANDIDATEs. Same EURUSD-class bug per handoff 36.
9. **Canary 16/16 pass, heartbeat-flatten stayed disabled, OB continuation 74% (healthy), CUSUM no alarm, correlation ok.** Core safety rails OK.

---

## Fleet-wide Thursday numbers

| Metric | XAUUSD | US30_cash | USDJPY | GBPJPY | GBPUSD | **Fleet** |
|---|---|---|---|---|---|---|
| M15 candles processed | 30 | 22 | 39 | 34 | 30 | **155** |
| Pre-AI gate skips | 7 | 0 | 0 | 21 | 30 | **58** |
| Pre-screen rejects (D1/H4 conflict, etc.) | 23 | 2 | 8 | 12 | 0 | **45** |
| Deterministic no-bias | 0 | 0 | 0 | 0 | 0 | **0** |
| AI evaluations (actual API calls) | 0 | 20 | 31 | 1 | 0 | **52** |
| CANDIDATEs | 0 | 6 | 2 | 1 | 0 | **9** |
| Permissions gate rejects | — | — | 1 (Tokyo touch_count=3) | — | — | **1** |
| L2 rejects (post-AI) | — | 4 (M15-as-H1 hallucination) | — | — | — | **4** |
| Post-M5 rejects | — | 1 (SL tightened inside OB) | — | — | — | **1** |
| Other rejects (AI data inconsistency) | — | 1 (NY 16:00 poi≠entry) | — | — | — | **1** |
| Limits placed | 0 | 0 | 2 | 1 | 0 | **3** |
| Limits cancelled (new_day) | 0 | 0 | 1 (prior-day) | 0 | 0 | **1** |
| **Fills** | **0** | **0** | **1** | **1** | **0** | **2** |
| Estimated R | — | — | +0.3 to +0.7R | ~+1.0R | — | **~+1.29R** |
| $ P&L | $0 | $0 | (part of +$1,260.91) | (part of +$1,260.91) | $0 | **+$1,260.91** |

Notes on counts: UTC-day basis (fixing the UTC+8 log timezone discovered by XAUUSD agent). "Pre-AI gate skips" numbers here reflect actual Thursday-UTC; initial pre-discovered counts (51/39/47) included Wednesday log tail.

---

## The 2 trades (the whole day's PnL)

### Trade 1 — USDJPY LONG (London 08:45 CANDIDATE → filled 09:00 UTC)
- **Setup:** Clean touches=1 H1 OB (159.595-159.692), entry 159.695, SL 159.477, TP1 160.015. RR 1.5. `sl_buffer_applied=0.033` (FA-2 compliant, 3dp).
- **Fill:** limit filled UTC 09:00 at 159.695, volume 7.18 lots.
- **Exit:** force-closed UTC 09:30 when automatic BE-SL-move failed (MT5 `sl_modification_failed`). Close price logged as 0.0 (MT5 `result.price=0.0` anomaly — fallback only implemented for fills, not closes).
- **Bug hit:** `kz_trades` NameError at orchestrator.py:492 fired on fill event. LIMIT_FILLED jsonl row not written; no Telegram fill alert; BE-tracker never init.
- **Outcome:** Estimated +0.3R to +0.7R per forensic agent (depending on actual exit price). Trailing-BE mechanism recovered the trade.

### Trade 2 — GBPJPY LONG (London 07:16 CANDIDATE → filled 13:16 UTC)
- **Setup:** A+ grade. Fresh bullish H1 OB formed at 06:00 UTC (215.064-215.167). Entry 215.167, SL 215.024, TP1 215.382, RR 1.5. `sl_buffer_applied=0.04` (FA-2 compliant). L2 passed 6/6 checks.
- **Fill:** limit filled UTC 13:16 at 215.176.
- **Exit:** broker-closed UTC 13:54 (38 min after fill). NO "TP1 close" log from our code — close happened broker-side.
- **Bug hit:** same `kz_trades` NameError on fill event. LIMIT_FILLED jsonl row not written. Trade record `execution` + `exit` fields remain null. `_pending_records_index.json` still holds stale `lim_2026-04-23_0716` entry (state leak).
- **Outcome:** Likely TP1 hit given 38-min duration + 20.6 pip target. Estimated ~+1.0R. Confidence ~65% (no TP1 close log, attribution unclear).

**PnL attribution**: Fleet net = +$1,260.91. USDJPY agent attributed +$1,260.91 to USDJPY alone (1.29R); forensic agent says split across both. **Math check**: USDJPY 1% = ~$1,000/R; GBPJPY 1% = ~$1,000/R. If USDJPY ≈ +0.3R ≈ $300 and GBPJPY ≈ +1.0R ≈ $1,000, sum ≈ $1,300 — matches. I go with the **forensic agent's attribution** (both contributed).

---

## The candidates that were rejected (and why)

### US30 — 6 CANDIDATEs, 0 fills, ALL correctly blocked

- **4 London (08:16/30/45/09:00)**: AI hallucination. Claude-Sonnet-4-6 cited an M15 OB (49175.21-49144.21) as "the H1 POI" because all real H1 OBs had touches≥2 (disqualified by prompt). AI's rationale at `_0816.json:14139` explicitly says "(M15, touches=1)" — **conscious substitution, not oversight**. L2's `h1_poi_exists` caught all 4. Counterfactual: entries at 49175.21 would have SL'd at 49118 during the 09:15-10:30 retracement (low 49076.81). **L2 saved ~4R of loss.**
- **NY 13:46**: L2 passed (original AI SL 49046.27 was valid, below H1 OB 49155.31). M5 refinement tightened SL to 49219.75 → inside OB zone → `REJECTED_L2_POST_M5` at `orchestrator.py:840`. Correct fail-closed behavior but represents a **lost legit setup** — recoverable with an M5 SL clamp.
- **NY 16:00**: AI data inconsistency. `poi_price_level=48531.325` points at touches=4 OB midpoint; `entry_price=48645.71` points at touches=2 OB high. Two different OBs in one output. L2 matched against touches=4 → `sl_beyond_ob` failed. **New class of AI bug beyond FA-2 scope.**

### USDJPY — 2 CANDIDATEs, 1 filled, 1 gate-rejected
- **Tokyo 00:16**: AI picked a touches=3 H1 OB at 159.361-159.488 despite prompt's "prefer lowest touches" directive. Gate 1 blocked with `touch_count_too_high=3`. **Safety gate worked as designed.**
- **London 08:45**: filled (see above).

### GBPJPY — 1 CANDIDATE, 1 filled
- **London 07:16**: clean A+ setup, filled at 13:16 (see above).

### XAUUSD — 0 CANDIDATEs
- Every London candle either pre-AI gated (7, no bullish H1 OB existed) or pre-screen blocked (23, H4 flipped bearish around 09:00 UTC while D1 stayed bullish). NY identical pattern.
- **Possible missed setup (~40% confidence):** NY 13:30 UTC day low 4684.09 formed a new unmitigated bullish H1 OB (4684.09-4701.49), H1 BOS at 15:00 with displacement 1.73, rally to 4743. Pre-screen blocked every NY candle due to H4 bearish. True retest into 4684-4701 never materialized, so "missed CANDIDATE" claim is weak; "missed AI evaluation" claim is ~70%.

### GBPUSD — 0 CANDIDATEs (observer + gate-suppressed)
- 30 candles all pre-AI gate skipped.

---

## Critical bugs found (ranked by priority)

### P0 — Must fix immediately
1. **`kz_trades` NameError at `orchestrator.py:492`** (pre-existing since `dc4cec2` T2.8 Apr 13). Fires on every limit fill. Hit by BOTH Thursday fills. Blocks: `notify_limit_filled` Telegram alert, trade-record promotion, `_init_trade_tracking`. Trades survived via fallback paths, but the pipeline's "this trade is now managed" state is incomplete. Every future fill will hit this.
2. **Uncommitted production code running live.** `src/components/pre_ai_gates.py`, `src/components/orchestrator.py`, `tests/test_pre_ai_gates.py` — direction-aware gate upgrade in working tree, not committed. Watchdog restart 2026-04-22 picked it up. The logic is correct, but (a) any subsequent watchdog restart on a freshly-cloned instance would revert to the agnostic gate; (b) `git log` doesn't reflect live reality; (c) no review happened.

### P1 — Material hazards
3. **`new_day` auto-cancels pending limits on every bootstrap** (`orchestrator.py:179, 339-340`). `session_state["date"]` initializes to `None` and is not persisted across restarts. Killed `lim_2026-04-22_1515` at UTC 23:46 Apr 22 even though UTC date had not changed. Benign Thursday, but a real FTMO-trial risk if a watchdog respawn happens mid-window.
4. **FA-2 FX precision leak on GBPUSD.** 63.6% L2-reject rate on `sl_beyond_ob` across 11 CANDIDATEs last week — Sonnet producing SL > entry for LONG. Same symptom as documented EURUSD issue at n=193 (handoff 36 §"Known gaps #4"). If pre-AI gate ever opens for GBPUSD, these will flow through as CANDIDATEs and get L2-rejected en masse. FA-2 commit `fa35cc0` did NOT fix 5dp FX.
5. **"Observer-only" for GBPUSD is a label, not a gate.** Same 1% risk, same `mt5.order_send` wiring. "Observer" lives in comments + handoffs, no code enforcement. CEO-aware risk but should be hardened.

### P2 — Architecture / correctness
6. **AI M15-as-H1 OB substitution** (US30 London, 4 CANDIDATEs). Conscious violation of prompt — AI admits it. Needs prompt hardening; possible post-AI validator for "cited POI timeframe == H1".
7. **AI data inconsistency (poi_price vs entry_price point to different OBs)** (US30 NY 16:00). New failure class. Need a post-AI validator that cross-checks POI-level ↔ entry-price ↔ same-OB bounds.
8. **Directional concentration** (98%+ bullish April, zero bearish CANDIDATEs since redacted_account kickoff). Could be regime — could be a structural bullish bias in `market_state.compute_market_state`. Needs a dedicated audit.
9. **M5 output SL clamp** missing. NY 13:46 US30 CANDIDATE lost to M5 tightening SL inside OB. A clamp `SL ∈ [swing_low − buffer, OB_low − buffer]` before re-verify recovers the legit setup.

### P3 — Observability / cosmetic
10. **`api_calls_made` reporting bug** at `orchestrator.py:2530-2541`. Pre-AI gated candles count as API calls. Missing `pre_ai_gate:` prefix in exclusion tuple. Affects all instruments using the gate.
11. **`log_candidate_features` positioned AFTER pre-AI gate.** 58 Thursday gated candles invisible to shadow loggers. Move the log call before the gate if we want to monitor what the gate is suppressing.
12. **Session summaries mis-count CANDIDATEs.** London/Tokyo JSON summaries report `CANDIDATE: 0` when raw jsonl has CANDIDATE rows. candle_log being overwritten by downstream rejection codes.
13. **MT5 close-price `0.0` anomaly** (USDJPY close at 09:30). Fallback only implemented for fill events, not close events.
14. **L2 displacement check binds to stale events** (first-in-list = potentially week-old). Low priority; didn't affect Thursday.
15. **Pre-AI-gate skips don't write MSO snapshots**, so post-hoc verification of gate correctness on skipped candles is limited.

---

## What worked (do-not-break list)

- **Pre-AI gate is semantically correct and strictly narrower than L2.** Verified by all 5 per-instrument agents + forensic agent. Zero false-positive skips found across sampled evidence. Weekly eval decline on GBPJPY (29→15→5→1) matches the rollout exactly.
- **L2 `h1_poi_exists` saved us from 4R of AI-hallucination loss on US30 London.**
- **Gate 1 touch-count rejection saved us from a touches=3 OB pick on USDJPY Tokyo.** AI violated "prefer lowest touches" — gate caught it.
- **FA-2 XAUUSD + JPY-cross compliance is clean.** `sl_buffer_applied > 0`, no degenerate params, prices at correct precision on both Thursday fills.
- **Canary 16/16 pass, OB continuation 74%, CUSUM no alarm, correlation checks ok, heartbeat-flatten stayed disabled.** Safety rails healthy.
- **Pre-screen correctly blocked XAUUSD NY** when H4 flipped bearish while D1 stayed bullish. Intentional design, working.

---

## Answer to CEO's core questions

**Q: "Is everything good?"**
A: Core trading logic and safety gates are good — L2 caught 4 AI hallucinations, Gate 1 caught 1 touch-count violation, pre-AI gate saved money without over-blocking. **But pipeline lifecycle has a P0 bug (`kz_trades` NameError) hit by both Thursday fills**, plus we're running uncommitted code in production. Pnl was positive; process hygiene is not.

**Q: "Did we miss opportunities that looked good on paper?"**
A: One candidate at ~40% confidence — XAUUSD NY after 13:30 UTC formed a fresh bullish H1 OB + H1 BOS that could have generated a LONG CANDIDATE, but pre-screen blocked on H4=bearish. By design. Not a bug. All other instrument silences were legitimate market-state conditions.

**Q: "Is the system blocking the right opportunities, or blocking good ones too?"**
A: Blocking the right ones. Every US30 CANDIDATE that got rejected was correctly rejected — 4 were AI hallucinations, 1 was an M5 SL-into-OB refinement, 1 was an AI data inconsistency. The pre-AI gate blocks only where L2 would have rejected anyway. The only "optimistic" block is NY 13:46 US30 (M5 tightened the SL inside the OB — recoverable by an M5 clamp).

**Q: "Or is the market not offering setups?"**
A: Thursday had **9 CANDIDATEs fleet-wide** vs. the typical ~17 trades/month average (~0.6/day per instrument). Nine raw CANDIDATEs in a day is above average — the filter funnel converted 9 → 3 limits → 2 fills, which is on-distribution. The issue isn't "market didn't offer" — it's that the AI produced 4 flawed CANDIDATEs that safety gates correctly killed.

---

## Prioritized recommendations

**This week (before next live day):**
1. **Fix `kz_trades` NameError** — 10-min fix, critical. Every limit fill currently loses Telegram alerts + trade-record promotion.
2. **Commit the pre-AI gate uncommitted code.** Review the diff, CEO-approve, commit. Add `git status` check to watchdog or fleet health monitor.
3. **Persist `session_state["date"]` across restarts** (or rekey on UTC rollover, not bootstrap). Prevents accidental limit cancellations.

**Next week (FA-2 follow-up):**
4. **T2.prompt.v2 for FX 5dp precision** — Unblocks GBPUSD (currently 63.6% L2-reject). Same work would unblock EURUSD eventually. Per handoff 36 this was already on the post-kickoff list.
5. **Post-AI validator: POI-level, entry-price, and SL must all lie in the same OB bounds.** Catches the US30 NY 16:00 class.
6. **Prompt hardening against M15-as-H1 substitution** — when all H1 OBs have touches≥2, the AI should return NO_TRADE not invent an H1 POI from M15.

**Session-worthy investigations:**
7. **Directional concentration audit.** 98%+ bullish April with zero bearish CANDIDATEs since Apr 20 needs a dedicated look at `market_state.compute_market_state` — is this a regime or a structural bias?
8. **Formalize GBPUSD "observer" mode.** Either commit a trading-disabled flag (cleanest), or decide to promote GBPUSD to live (blocker: FA-2 FX fix) per the end-of-April decision the CEO already flagged.
9. **M5 SL clamp design.** Keeps SL inside `[swing_low − buffer, OB_low − buffer]` before re-verify. Recovers setups like US30 NY 13:46.

**Observability/cosmetic:**
10. Fix `api_calls_made` exclusion, move `log_candidate_features` before pre-AI gate, fix session-summary CANDIDATE mis-count, add MT5 close-price=0.0 fallback, fix L2 displacement stale-event binding.

---

## Per-instrument verdicts

| Instrument | Verdict | Key finding |
|---|---|---|
| **XAUUSD** | Correct silence | No bullish H1 POI London, H4-flip blocked NY. ~40% confidence on one missed setup. Uncommitted live gate code confirmed. |
| **US30** | Safety gates working as designed | 4 AI hallucinations caught by L2, 1 M5 tighten lost legit setup, 1 AI data inconsistency new bug class. |
| **USDJPY** | +1 trade, partial P&L recovered | Touch-count gate worked on Tokyo, `kz_trades` NameError hit on London fill, BE-move failure forced early close. |
| **GBPJPY** | +1 trade, clean setup | A+ grade CANDIDATE, `kz_trades` NameError hit on fill, exit ambiguous but likely +TP1. |
| **GBPUSD** | Observer silence, but FA-2 FX leak | Gate suppressed everything; 63.6% L2-reject rate on recent CANDIDATEs confirms FX precision bug not fixed by `fa35cc0`. |

---

## Confidence flags
- Attribution of PnL between USDJPY and GBPJPY: ~65% (no TP1 close logs for either; reconciling via account math + duration/target heuristics).
- XAUUSD missed setup claim: ~40% missed CANDIDATE, ~70% missed AI evaluation.
- Directional concentration root cause (regime vs bug): cannot distinguish within audit scope — genuinely ~50/50 based on available evidence.
- Gate correctness on 2 NY GBPJPY skips: ~50-70% (pre-AI gate skips don't write MSO snapshots; inference-only).
- Everything else: ≥85% confidence.

---

## Files produced by this audit

```
research/thursday_2026-04-23_analysis/
├── SYNTHESIS.md                 ← this file
├── XAUUSD_analysis.md           28 KB
├── US30_analysis.md             33 KB
├── USDJPY_analysis.md           32 KB
├── GBPJPY_analysis.md           35 KB
├── GBPUSD_analysis.md           31 KB
└── system_forensics.md          50 KB
```

Each per-instrument report includes session timeline tables, candidate detail rows, rejection buckets, gate audits, missed-setup analysis, concerns with confidence %, and file:line citations. The forensic report has 45+ cross-cutting file:line citations on gates, lifecycle, reconciliation, and the shadow-log review.
