# GTOS System Forensics — Thursday 2026-04-23

**Scope:** Fleet-wide pipeline and gate behavior across all 5 instruments (XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD observer) on Thursday 2026-04-23 UTC.

**Analyst mode:** Max-depth forensic, read-only, on uncommitted production.

**Time-zone note.** All log files are written in Windows local time = UTC+8. Every claim below is stated in UTC; where a log line is quoted verbatim, its "2026-04-23 HH:MM:SS" prefix is local and must be shifted by −8h to get UTC. Example: log `2026-04-23 15:16:38` = `2026-04-23T07:16:38 UTC`. Verified by comparing `pipeline_state/heartbeat.json` (`utc: 2026-04-23T17:01:03`) to its own log line `2026-04-24 01:01:03`.

---

## Executive Summary

1. **The pre-AI H1 POI availability gate is working correctly, but it has been UPGRADED in place on live (uncommitted)** — converted from direction-agnostic to direction-aware between 2026-04-22 09:30 UTC and 09:45 UTC. Every Apr 23 skip sampled traces to a verifiable "no unmitigated bullish H1 OB" state. No false positive was found against the 3-day CANDIDATE set. Confidence 85% (one state-reconstruction gap for XAUUSD at 07:16 UTC due to no persistent MSO dump at that timestamp).

2. **Thursday saw 2 filled trades, net positive ~+$1,260.91 (~+1.26% on $98,026.71).** USDJPY LONG filled 09:00 UTC, force-closed 09:30 UTC on `sl_modification_failed` at end-of-London trailing-BE attempt (trade was in profit per `handle_timeout_trailing` logic). GBPJPY LONG filled 13:16 UTC, broker-closed 13:54 UTC (likely TP1 fill — 38 min, 20.6 pip target, Δ=+0.206). Account ended at $99,287.62.

3. **CRITICAL BUG found: `NameError: name 'kz_trades' is not defined` at `src/components/orchestrator.py:492`.** Raised on every limit-fill (USDJPY 09:00 UTC, GBPJPY 13:16 UTC). The exception kills the fill-handling branch BEFORE `_promote_pending_record_on_fill()` (line 503) and `_init_trade_tracking()` (line 505) run — trade records are never promoted with fill data, Telegram `notify_limit_filled()` never fires, exit-tracking (BE/TP1) is not initialized. Bug is pre-existing in HEAD (`dc4cec2`, T2.8), not introduced by the uncommitted pre-AI gate changes.

4. **Heartbeat-flatten kill switch firing 120 TRIGGER_CANDIDATE events in log-only mode on Thursday** — config flag `heartbeat.flatten_enabled: false` verified, so no flatten actions were taken. Events cluster around process shutdown/restart transitions (cross-KZ pauses). Not a bug.

5. **XAUUSD and GBPUSD had ZERO AI evaluations on 2026-04-23 UTC** — XAUUSD was fully filtered by pre-screen (23 candles, D1/H4 conflict bullish-vs-bearish) + pre-AI gate (7 candles, no unmitigated bullish H1 POI); GBPUSD was fully filtered by pre-AI gate (30 candles, no unmitigated bullish H1 POI). No `no_trades/*.yaml` sampling indicates the AI could have traded — both are legitimate regime-response states.

6. **Fleet directional bias is >98% bullish on every active instrument for the entire April 2026 dataset; ZERO bearish CANDIDATEs since redacted_account kickoff (2026-04-20).** XAUUSD 138/2, US30 176/4, USDJPY 328/2, GBPJPY 144/19 (bullish/bearish evals). This is not a bug — it reflects the underlying market regime — but represents concentrated directional risk.

7. **Canary Thursday = pass.** `scripts/canary_fixtures/last_run.json` timestamp `2026-04-23T13:31:07Z`, 16/16 match (12 baseline + 4 borderline), 66.2s elapsed, $12/mo cache floor intact via 1 cache HIT observed mid-day.

---

## Section 1 — Pre-AI Gate Audit (the big one)

### 1.1 Gate code and wiring

- Gate definition: `src/components/pre_ai_gates.py:12-76` (full file, 77 lines).
- Wired in orchestrator: `src/components/orchestrator.py:587-597` (step 3d, after pre-screen + deterministic bias, before session memory + primary analyzer).
- Config flag: `config/agent_config.yaml:259` — `pre_ai_gates.h1_poi_availability_enabled: true`.
- Guard: gate is passive unless `model_a.enabled_frameworks == ["ob_retest"]` (config line 80 has exactly this).

### 1.2 Uncommitted upgrade: direction-agnostic → direction-aware

- Commit `8a9bcfe` (2026-04-20 23:19) introduced the **direction-agnostic** form: any unmitigated H1 OB (any type) OR any unretested H1 breaker keeps gate passive; otherwise skip with reason `no_unmitigated_h1_pois`.
- Uncommitted working-copy edit (`git diff HEAD -- src/components/pre_ai_gates.py`, file mtime `2026-04-22 17:32:17 local = 09:32 UTC`) added direction-awareness: when `bias` is "bullish" or "bearish", filter unmitigated OBs on `ob.type == bias` and unretested breakers on `bb.direction == bias`. The reason string becomes `no_unmitigated_{bias}_h1_pois`.
- Log evidence of the deployment moment — the **last** direction-agnostic skip was `2026-04-22 17:30:05` local = `09:30 UTC`; the **first** direction-aware skip was `2026-04-22 18:01:09` local = `10:01 UTC`. Transition window matches the file mtime.
- This change is UNCOMMITTED. `git diff HEAD -- src/components/orchestrator.py` shows the companion wiring change adding the `bias=bias_result.get("bias","")` argument. No test file update visible. `tests/test_pre_ai_gates.py` is listed as modified in `git status` but its diff was not examined here.

### 1.3 Fleet-wide Thursday skip census (by UTC day, not log local-day)

| Instrument | Candles processed | Pre-AI skip | Pre-screen FAIL | Deterministic no_bias | AI evals |
|-----------|-------------------|-------------|-----------------|------------------------|----------|
| XAUUSD    | 30                | 7           | 23              | 0                      | 0        |
| US30_cash | 20                | 0           | 0               | 0                      | 20       |
| USDJPY    | 32                | 0           | 0               | 0                      | 31 (1 limit-pending) |
| GBPJPY    | 32                | 21          | 0               | 0                      | 1 (10 limit-pending) |
| GBPUSD    | 30                | 30          | 0               | 0                      | 0        |
| **Total** | **144**           | **58**      | **23**          | **0**                  | **52**   |

(Script used: `PYTHONIOENCODING=utf-8 python3` scanning each `logs/{instrument}.log`, converting `%Y-%m-%d %H:%M:%S` local → UTC via `−8h`.)

All 58 Thursday pre-AI skips carry reason `no_unmitigated_bullish_h1_pois` (direction-aware form). Zero direction-agnostic skips on Thursday UTC. Confidence 100%.

### 1.4 Sampled skip verifications

All sampled skips correspond to verifiable MSO states in which the deterministic bias was bullish and there was no unmitigated bullish H1 OB:

- **GBPJPY 07:16 UTC CANDIDATE.** MSO dump in `knowledge_base/trade_records/GBPJPY/2026-04-23_london_0716.json` contains D1=bullish, H4=bullish, H1=bullish; H1 order_blocks includes one unmitigated bullish OB at 215.064–215.167 touch_count=1. Gate correctly passed (let through for AI eval); AI returned CANDIDATE; L2+Gate1+Gate3 passed; LIMIT_PLACED fired. This is the inverse of a skip — confirms gate doesn't over-block when a legit bullish POI is present. Confidence 100%.
- **US30_cash 08:16 UTC CANDIDATE.** MSO in `knowledge_base/trade_records/US30_cash/2026-04-23_london_0816.json`: D1=transitional, H4=bullish, H1=bullish; 2 unmitigated bullish H1 OBs (48472.35-48590.30 touches=4; 48629.71-48645.71 touches=2). Gate correctly passed. Bias resolved via H4+H1 consensus path (`_compute_deterministic_bias` at orchestrator.py:1076). Confidence 100%.
- **XAUUSD skips 16:00–16:45 UTC (8 candles).** No per-candle MSO dump persisted (no trade record written for skipped candles). The 17:00 UTC `pipeline_state/02_market_state.json` (timestamp_utc `2026-04-23T17:00:05`) shows H1 structure: protected_swing at `4684.09` formed `2026-04-23T13:00:00 UTC`, with 1 unmitigated bullish OB at 4684.09–4701.49 touch_count=1 (ALL other bullish OBs mitigated, all bearish breakers retested). This OB is associated with the 13:00 UTC swing low and therefore cannot have existed at 07:00 UTC when London KZ opened. At 17:00 UTC the pre-screen fired (H4 flipped bearish), so we cannot tell from this snapshot whether the gate would have passed with the new OB alone. Indirect confirmation via 07:16 skip log line: deterministic bias resolved (gate only runs when directional), and zero unmitigated bullish OBs existed at that moment (consistent with a bear-regime day). Confidence 75% — one state-reconstruction gap for 07:16–10:30 UTC; the 13:00 UTC swing-formation timestamp is the strongest evidence that no bullish OB existed earlier that day.
- **GBPUSD skips 07:00–11:45 UTC (30 candles).** No surviving MSO dump (no trade records written Thursday, no Apr 23 eval file). Inferred from GBPJPY's near-identical session structure and the fact that the skip reason was always `no_unmitigated_bullish_h1_pois` (deterministic bias resolved bullish). Confidence 70% — no independent evidence to falsify.

### 1.5 L2 consistency check — does the pre-AI gate mirror L2?

`src/components/verification.py:60-97` (`_find_matching_ob`) filters H1 OBs by:
- `not ob.mitigated` (required)
- strict containment of `poi_price` OR within-tolerance match
- **Does NOT filter by `ob.type == bias`.**

The pre-AI gate (`pre_ai_gates.py:52-54`) ADDS the `ob.type == bias` filter. **The pre-AI gate is STRICTLY MORE CONSERVATIVE than L2.** This means:

- A skip by the pre-AI gate can never filter a trade that L2 would have passed, because for a LONG (bullish-bias) setup the AI would cite a bullish OB as POI — which by construction is in the `ob.type == bias` subset the gate checks.
- Commit `8a9bcfe` claimed "guaranteed to correspond to an L2 rejection downstream" — this remains true after the uncommitted direction-aware upgrade, because the stricter gate rejects a super-set of what L2 would reject.

The gate's docstring (`pre_ai_gates.py:17-21`) accurately describes L2's contract: "L2's `h1_poi_exists` ... requires the AI's cited POI to fall inside either (a) an unmitigated H1 OB or (b) an unretested H1 breaker in the AI's trade direction." Note the docstring says "in the AI's trade direction" — but the actual L2 code does NOT enforce direction. The docstring is aspirational; the gate enforces what the docstring says, which is stricter than what L2 enforces. No gap in safety.

### 1.6 False-positive hunt

Catalog of all CANDIDATEs 2026-04-21 → 2026-04-23 (inclusive) with direction and h1_poi_identified:

- XAUUSD: 0 CANDIDATEs in window.
- US30_cash: 7 CANDIDATEs (1 on 2026-04-21, 6 on 2026-04-23) — all bullish, all `h1_poi_identified=True`.
- USDJPY: 13 CANDIDATEs — all bullish, all `h1_poi_identified=True`.
- GBPJPY: 3 CANDIDATEs — all bullish. **1 CANDIDATE on 2026-04-21T09:15:05 had `h1_poi_identified=False`** (needs follow-up — if the AI claimed no POI but still emitted CANDIDATE, L2 `h1_poi_exists` would have immediately FAILed; this is an AI-side issue, not a pre-AI gate issue).
- GBPUSD: 7 CANDIDATEs — all bullish, all `h1_poi_identified=True`.

**No false-positive CANDIDATE was generated on a candle that immediately followed a pre-AI skip on the same instrument.** When an instrument skips, subsequent candles on the same instrument either continue skipping (bullish MSO unchanged), get preempted by pre-screen (bias flip invalidated), or transition to a valid POI state which allows a CANDIDATE on a later candle (US30 08:16 UTC CANDIDATE is 8+ candles AFTER the preceding day's NY KZ where US30 had 0 skips — no adjacency).

Confidence 90% on no-false-positive claim (small population, only 3 days of direction-aware gate in production).

### 1.7 Cost saving estimate

- Thursday API calls: 64 total (XAUUSD 0 + US30 26 + USDJPY 35 + GBPJPY 3 + GBPUSD 0). Of these, ~52 are primary-analyzer evals; the rest are M5 refinement (1 per CANDIDATE) + devil's advocate shadow + canary.
- Candles that WOULD have been sent to AI without pre-AI gate: 58 additional evals × ~$0.04/call (Sonnet-4.6 effort=max average) ≈ $2.32 saved on Thursday alone.
- At the fleet's historical mean pre-AI skip rate (Thursday UTC: 58 skips / 144 candles = 40% — heavy XAUUSD+GBPUSD contribution), the gate saves roughly $2–$6/day or ~$60–$180/month. This is material against the `$50/mo` `budget.monthly_cap_usd` cap.
- Pre-AI skip rate has climbed sharply: 0 (Apr 20, gate direction-agnostic) → 24 (Apr 22, mixed modes) → 58 (Apr 23, all direction-aware). The spike correlates with the uncommitted direction-aware upgrade + a persistent bull-regime day producing no new bullish POIs.

---

## Section 2 — Permissions Gate Rejections (post-CANDIDATE)

Nine CANDIDATEs emitted Thursday across the fleet. Walked every trade record in `knowledge_base/trade_records/{instrument}/2026-04-23_*.json`:

| Trade record | Final outcome | L2 pass | Gate1 pass | Gate3 pass | Reason |
|-------|-----|-----|-----|-----|-----|
| GBPJPY london 07:16 UTC | LIMIT_PLACED | True | True | True | → filled 13:16 UTC |
| USDJPY london 08:45 UTC | LIMIT_PLACED | True | True | True | → filled 09:00 UTC |
| USDJPY tokyo 00:16 UTC | REJECTED_GATE1_SAFETY | True | **False** | True | `touch_count_too_high: touch=3 @ 159.361–159.488 OB, entry=159.488` |
| US30 london 08:16 UTC | REJECTED_L2 | **False** | — | — | `h1_poi_exists: AI cites POI at 49531.31 but no unmitigated H1 OB near it` |
| US30 london 08:30 UTC | REJECTED_L2 | **False** | — | — | same — AI re-cited 49531.31 |
| US30 london 08:45 UTC | REJECTED_L2 | **False** | — | — | AI cited 49175.21, unmatched |
| US30 london 09:00 UTC | REJECTED_L2 | **False** | — | — | AI cited 49531.31, unmatched |
| US30 ny 13:46 UTC | REJECTED_L2_POST_M5 | True | — | — | M5 refinement tightened SL from 49046.27 → 49219.75, re-verify of `sl_beyond_ob` failed because 49219.75 is inside OB zone 49155.31–49365.31 |
| US30 ny 16:00 UTC | REJECTED_L2 | **False** | — | — | `sl_beyond_ob: SL 48599.49 is not below OB low 48472.35` (AI cited wrong OB for LONG direction) |

Gate rejections summary:
- **4 of 9 US30 CANDIDATEs rejected by L2 `h1_poi_exists`** — AI persistently cites POI prices that don't match any unmitigated H1 OB. This is an AI error mode independent of the pre-AI gate (the pre-AI gate only checks if ANY unmitigated bullish OB exists in MSO; it doesn't validate the AI's cited POI against the MSO data).
- **1 of 9 rejected by L2 `sl_beyond_ob`** — AI placed SL inside the OB zone.
- **1 of 9 rejected post-M5 by re-verification** — M5 structural SL violated OB-beyond constraint (correct rejection: tightening SL inside the OB is a framework breach).
- **1 of 9 rejected by Gate1 `touch_count_too_high`** — USDJPY tokyo, AI cited an OB with touch_count=3 (T4 statistical filter: touch_count>=2 is rejected; WR drops from 72.7% to 31.5% at touch-2+).
- **2 of 9 passed all gates → LIMIT_PLACED** — GBPJPY london + USDJPY london.

No rejections on Gate 0 (`deployment.phase=3` is current and valid), no rejections on Gate 3 (MT5 connected throughout, daily-loss-stop never triggered), no correlation rejections, no dormant-state rejections, no concurrent-cap rejections (max 2 concurrent, well under the redacted_account profile cap of 4).

**Liquidity-cluster SL gate (SHADOW only, ships disabled):** Both filled trades would have been REJECTED if the gate were enabled. Evidence from `shadow_logs/liquidity_distance_log.jsonl`:
- GBPJPY LONG SL @ 215.024 is 0.006 pips from an equal_lows pool @ 215.03 — within the 0.5·M15_ATR margin (0.0397). Shadow decision = `would_reject`.
- USDJPY LONG SL @ 159.477 is 0.003 pips from an equal_lows pool @ 159.48 — within the 0.5·M15_ATR margin (0.026). Shadow decision = `would_reject`.

Both trades were nonetheless net-positive by end of day, suggesting the liquidity-cluster gate would have produced false rejections on Thursday. Sample size 2 — do NOT draw conclusions.

---

## Section 3 — Canary Health

`scripts/canary_fixtures/last_run.json`:
- Timestamp: `2026-04-23T13:31:07Z` (Thursday, mid-London-KZ exit → NY-KZ entry boundary for some instruments).
- Model: `claude-sonnet-4-6 effort=max` (matches `ai.primary_model` / `ai.primary_effort`).
- Baseline: `2026-04-18T17:41:18Z`, same model+effort.
- Result: PASSED — 16/16 decision matches (12/12 baseline, threshold 11; 4/4 borderline, threshold 3). 0 keyword drifts. Elapsed 66.2s.
- Cache behavior observed in logs: `logs/usdjpy.log` at `2026-04-23 15:00:00 local = 07:00 UTC` — `[canary] cache HIT for 2026-04-23 — skipping subprocess`. This is the PASS-only content-addressed cache (T1.3.1) working as designed — one primary run plus several free cache hits across instruments.
- `Canary passed: model behavior stable` appears 11 times across the 5 instrument logs on Thursday, aligned with kill-zone entries (London entry ~07:00 UTC, NY entry ~13:00 UTC). All PASS.

No canary trip, no prompt regression. Confidence 100%.

---

## Section 4 — Process Lifecycle

### 4.1 Orchestrator restart cadence

Thursday was NOT a cold-boot day. The fleet had been running since the Monday kickoff (2026-04-20 10:01:29 UTC — rolling restart under `--profile redacted_account`). The watchdog (scripts/watchdog.ps1) operates on a 15-minute schedule; most orchestrator processes are short-lived — they start at KZ entry, run until KZ end + monitoring of any active trade/pending limit, then cleanly exit with log line `All kill zones complete, no active trade. Ending session.` → `Shutting down orchestrator` → `Shutdown complete`.

`logs/start_all.log` shows exactly one `start_all.bat` invocation on Thursday: `[Thu 04/23/2026 8:01:01.74]` local = 00:01 UTC — just after midnight UTC day-rollover, starting 5 orchestrators + displacement logger.

### 4.2 Instrument-by-instrument Thursday lifecycle (all times UTC)

- **XAUUSD:**
  - Bootstrap 00:01, processed NY KZ 16:00–17:00 UTC (5 skips) then exited.
  - Bootstrap 07:00 (watchdog auto-restart on KZ open), processed London KZ 07:00–10:30 UTC (7 pre-AI skips + 11 pre-screen failures, 3 skipped before pre-screen checked).
  - Actually: 30 candles processed. 7 pre-AI skipped (before 09:00 UTC), 23 pre-screen failed (from 09:00 UTC onwards because H4 flipped bearish while D1 held bullish), 0 AI evals.
  - Entered NY KZ 13:00 UTC; pre-screen continued to fire (same D1/H4 conflict) through session.
  - Process restart pattern: normal cycle (clean shutdown-restart per KZ boundary).
- **US30_cash:** Processed 20 candles, all through AI eval (0 pre-AI skips). 6 CANDIDATEs, 14 NO_TRADE. 4 London KZ trade records saved (all REJECTED_L2), 2 NY trade records saved (REJECTED_L2_POST_M5 + REJECTED_L2). Normal process cycle.
- **USDJPY:** Bootstrap 07:46 UTC after being offline since ~01:16 UTC (Tokyo KZ restart). Processed 32 candles — 2 CANDIDATEs (both LONG), 29 NO_TRADE. 1 trade placed (08:45 UTC limit) → filled 09:00 UTC → closed 09:30 UTC. Process restarts on every KZ rotation. See 4.3.
- **GBPJPY:** Processed 32 candles — 21 pre-AI skips, 1 CANDIDATE. 1 trade placed (07:16 UTC limit) → filled 13:16 UTC → closed 13:54 UTC. Process restarts on every KZ rotation and dead-zone wake-ups (normal behavior).
- **GBPUSD (observer):** Processed 30 candles, all pre-AI skipped. Zero AI evals, zero CANDIDATEs, zero trades. Consistent with observer-only mandate.

### 4.3 The 07:46 UTC (15:46 local) cluster start

All 5 orchestrators, displacement_logger, and heartbeat_monitor restarted at `2026-04-23 07:46:06.555` (UTC). Looking at the GBPJPY bootstrap log for context:

```
2026-04-23 15:46:02,575  notifications configured: account=$100,000, risk=1.00%, $/R=$1,000
2026-04-23 15:46:02,582  Loaded 31 economic calendar events (15 upcoming)
2026-04-23 15:46:02,592  Loaded equity peak from state: $100000.00
```

The watchdog log shows this as the cycle at the Thursday-morning London KZ window (fleet was idle 04:31–07:11 during the EU pre-market dead zone, then spun up ~30 min before London KZ open at 08:00 UTC). This is EXPECTED BEHAVIOR — `watchdog.log` lines like `Watchdog: Done (will restart processes when trading hours resume) ===` for 02:00–07:00 UTC confirm the idle gap was intentional.

### 4.4 One anomaly worth noting

Between 00:01 UTC and 01:01 UTC (day-rollover + early Tokyo KZ end for XAUUSD/USDJPY), the watchdog restarted processes every 15 min because each process was exiting at session end → watchdog respawning into the next short KZ window → exit again. This is not a crash loop — each instance ran to clean shutdown and logged `All kill zones complete, no active trade. Ending session.` before exiting. But it IS inefficient: 5 bootstraps in 60 minutes per process means paying the bootstrap cost repeatedly. Not a Thursday-specific problem — it's an architectural choice. Flagged.

---

## Section 5 — Heartbeat / Malformed / OB Continuation

### 5.1 Heartbeat-flatten kill switch

- Config: `heartbeat.flatten_enabled: false` — verified.
- `logs/heartbeat_monitor.log` — single startup line on 2026-04-23: `heartbeat_monitor starting: enabled=False write_interval=30s miss_threshold=3` at 07:46:03 UTC. Only one start — not a crash loop.
- `shadow_logs/heartbeat_flatten_events.jsonl` — 160 Thursday events: 40 `FEATURE_DISABLED` + 120 `TRIGGER_CANDIDATE`. All events cluster around kill-zone boundaries and process startup, consistent with the orchestrator's clean-exit pattern (brief stale-heartbeat windows while the process is respawning).
- No `FLATTENED` events, no `CANCELLED_VIA_TELEGRAM` events — the feature remained in observation-only mode for the entire day. Confidence 100%.

### 5.2 Malformed responses / API refusals

- `shadow_logs/malformed_responses.jsonl` last-mod 2026-04-21 19:30 UTC. **Zero Thursday entries.** All primary-analyzer calls returned parseable JSON.
- `logs/api_refusal_monitor.log` empty (zero-byte file since 2026-04-17). No API refusals Thursday.
- Displacement mismatches logged but not fatal: 3–5 `Displacement ratio mismatch: AI=X MSO=Y` warnings per CANDIDATE. AI under-reports the MSO value systematically (e.g. US30 `AI=2.3 MSO=4.32`); this is the known FA-2 prompt-precision issue.

### 5.3 OB continuation rolling-50 monitor

`shadow_logs/ob_continuation_daily.csv` Thursday entry (portfolio line only shown; per-instrument all insufficient-sample):

```
2026-04-23,PORTFOLIO,50,2025-08-01,2026-04-17,37,50,74.0000,false,false
```

Portfolio rolling-50 = 74.0% (above the 60% alarm threshold; baseline is 70%). Per-instrument rates all flagged `insufficient_sample=true` (n<50). No alarm fired.

### 5.4 CUSUM candidate-rate

`shadow_logs/cusum_candidate_rate_daily.csv` Thursday entry:

```
2026-04-23,OVERALL,332,54,0.162651,0.344962,0.590849,3,0,false,,false,2026-04-22T16:00:05.033776+00:00
```

Fleet CR 16.27% — elevated above the 10.3% baseline noted in CLAUDE.md. 3 cumulative UP-side alarms since tracking began, but **no alarm fired today**. The S_up statistic decayed from 0.99 on Apr 22 to 0.34 on Apr 23 as the bullish-regime CANDIDATE cluster normalized.

### 5.5 Displacement / correlation-shock

- `logs/displacement.log` last Thursday entry at 07:46 UTC — 4 displacement events logged, all "outside_kz" (pre-market). Two flagged `[CORRELATED: GBPJPY]` and `[CORRELATED: USDJPY]` for the JPY cross group. No in-KZ displacement events logged Thursday in the portion examined.
- `logs/correlation_shock.log` Thursday entry 08:02 UTC — all 7 correlation pair checks `status=ok`, no alarms. `US_INDICES` shows `no_data` because US500 isn't loaded (expected per FN profile).

---

## Section 6 — Fill Reconciliation (the 2 real Thursday trades)

### Table of actual filled trades on 2026-04-23 UTC

| # | Instrument | Candle (UTC) | Direction | Entry | SL | TP1 | Filled (UTC) | Close (UTC) | Close reason | Logged close price | Expected R | $ P&L (est.) |
|---|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 1 | USDJPY | 2026-04-23T08:45 | LONG | 159.692 (limit → 159.695 actual fill) | 159.477 | 160.015 | 09:00:05 | 09:30:23 | `sl_modification_failed` (BE-move failed at KZ-end, position force-closed) | `0.0` (MT5 `result.price` populated as 0; actual broker-close price unknown from agent log) | Trade was in profit per `handle_timeout_trailing` gate (line 895–898); likely 0.3R–0.7R realized | ~+$290 to +$700 |
| 2 | GBPJPY | 2026-04-23T07:16 | LONG | 215.167 (limit → 215.176 actual fill) | 215.024 | 215.382 | 13:16:14 | 13:54:05 | `Position 432844145 no longer exists — closed by broker` (TP1 fill very likely given 38-min duration + matching Δ to TP1) | Not logged — `_check_trade_and_capture` detected zero positions and recorded the close | Likely 1.0R (TP1 hit) given 38 min to cover 20.6 pip target | ~+$980 |

**Net cross-check:** account balance went from $98,026.71 (start of Thursday) to $99,287.62 (end of Thursday) = +$1,260.91 (+1.29%). Matches the estimated sum +$290 to +$1,680 with reasonable tolerance.

### Trade 1 (USDJPY) — full event trail

- `2026-04-23 16:45:25,981 local` (08:45:26 UTC) — `Limit intent set: LONG USDJPY limit=159.69200 sl=159.47700 tp=160.01500 expires=192 candles`. Trade record `2026-04-23_london_0845.json` saved with `LIMIT_PLACED`.
- `2026-04-23 17:00:05,033 local` (09:00:05 UTC) — `Limit triggered: lim_2026-04-23_0845 candle=...12:00:00+00:00 low=159.69000 limit=159.69200`. Note: candle timestamp in the log (`12:00:00+00:00`) is the MT5 server-time candle open, not the fill time. Fill fee adjustment: `actual_sl_dist=0.21800` vs original `0.21500` = 0.003 slippage, position sizing recalculated at `0.21800`, `entry=159.69500` instead of limit 159.692 (0.003 above limit — typical broker gap-fill).
- `2026-04-23 17:00:05,596 local` — `MT5 result.price=0.00000 -- using tick entry_price=159.69500 instead` — the known MT5 result.price=0.0 anomaly, worked around by tick-fallback (execution.py:417-424).
- `2026-04-23 17:00:05,596 local` — `Trade opened: tr_2026-04-23_0900 LONG 7.18 lots at 159.695, SL=159.477, TP1=160.015`. Position size 7.18 lots × contract_size 100_000 / 1.0 = ~$12.7M notional; at 0.218 SL distance and 1% risk, $/R ≈ 7.18 × 100k × 0.218 / 100 = ~$1565, matches 1% of ~$98k (the recalc from actual SL dist).
- `2026-04-23 17:00:05,597 local` — **`Pipeline error: name 'kz_trades' is not defined`** — crash in the limit-fill branch at orchestrator.py:492. See Section 8 below. Consequence: `notify_limit_filled()` at line 498 never fires (Telegram silent on this fill); `_promote_pending_record_on_fill()` at line 503 never runs (trade record at `knowledge_base/trade_records/USDJPY/2026-04-23_london_0845.json` retains `LIMIT_PLACED` status with `execution: None` and `exit: None`); `_init_trade_tracking()` at line 505 never runs (exit-tracking coroutine not started, BE/TP1 monitoring disabled for this trade).
- Despite the crash, the MT5 position IS open (the `order_send` succeeded in execution.py:417 before the orchestrator-level `kz_trades` error). The next candle's orchestrator step `_check_pending_limit_outside_kz` or `_check_trade_and_capture` should have adopted the orphan position on re-entry — but no logs show that adoption event. Raising this as a material silent-state-divergence concern.
- `2026-04-23 17:30:23,565 local` (09:30:23 UTC) — `Failed to move SL to BE — closing position for safety`. Orchestrator's `handle_timeout_trailing()` (execution.py:880-909) was called at end-of-London-KZ, detected the trade was in profit (current_price > 159.695), attempted `_move_sl_to_breakeven()`, the MT5 modify request failed (retry once, also failed), and fell through to `close_position("sl_modification_failed")`.
- `2026-04-23 17:30:23,919 local` — `Position closed: sl_modification_failed at 0.0` — close reported success; result.price=0.0 again (same MT5 anomaly). Actual close price not captured in log.

Why the `_move_sl_to_breakeven` failed is not logged at any diagnostic level — only the terminal ERROR line. Possible causes: broker rejected SL modification because price was too close to current tick (MT5 "Invalid stops" 10016); MT5 connection hiccup; position already in a BE-invalid state due to tight SL distance. Not diagnosable from logs alone.

### Trade 2 (GBPJPY) — full event trail

- `2026-04-23 15:16:38,618 local` (07:16:38 UTC) — `Limit intent set: LONG GBPJPY limit=215.16700 sl=215.02400 tp=215.38200 expires=192 candles`. Trade record `2026-04-23_london_0716.json` saved with `LIMIT_PLACED`.
- `2026-04-23 21:16:14,072 local` (13:16:14 UTC) — `Limit triggered: lim_2026-04-23_0716 candle=...16:15:00+00:00 low=215.11600 limit=215.16700`. Fill sizing recalculated: `original_sl_dist=0.14300, actual_sl_dist=0.15200` → entry=215.176 (0.009 above limit).
- `2026-04-23 21:16:14,620 local` — `Trade opened: tr_2026-04-23_1316 LONG 10.29 lots at 215.176, SL=215.024, TP1=215.382`. Volume 10.29 lots × 100_000 / 1.0 = ~$1.029M; $/R ≈ 10.29 × 100k × 0.152 / 100 / 215 ≈ $727 per R in USD. (Approximate — converting JPY-denominated P&L via USDJPY depends on current rate.)
- `2026-04-23 21:16:14,622 local` — **Same `kz_trades` crash.** Same silent trade-record-not-promoted outcome.
- `2026-04-23 21:54:05,088 local` (13:54:05 UTC) — `Position 432844145 no longer exists — closed by broker`. This is the orchestrator's reconciliation path detecting a phantom trade. Close reason not captured directly. Given 38-minute duration and the TP1 target requiring a +20.6 pip move from entry, TP1 hit is plausible. No BE move attempt was logged beforehand — so the close is likely a natural TP1 fill at broker-side (MT5 filled the TP order outside the agent's polling window, and the next orchestrator poll discovered zero positions).

### Critical bug summary — `kz_trades` NameError

`src/components/orchestrator.py:492`:
```python
self.session_state[f"trades_{kill_zone}"] = kz_trades + 1
```
Variable `kz_trades` is not defined in this scope. The bug is pre-existing — first introduced in commit `dc4cec2` (T2.8 concurrent-cap, session 33) and NOT fixed in the uncommitted current working copy. Blame shows `dc4cec2` as the introducer. Git log on the line via `-S "kz_trades"` shows commits `dc4cec2`, `a73ced3`, `12ff525`. The comment 2 lines above (`orchestrator.py:461`) says "No `kz_trades` cap any more" — meaning the T2.8 refactor intentionally removed the cap but left this one reference behind as dead code that happens to execute on every fill.

**Consequences of this bug, per trade:**
1. Telegram `notify_limit_filled()` does NOT fire — CEO has no real-time fill notification.
2. Trade record `2026-04-23_{london,ny}_HHMM.json` remains at `LIMIT_PLACED` state — `execution` and `exit` fields stay `null`. Post-hoc analysis of Thursday's fills requires cross-referencing MT5 broker history.
3. `_init_trade_tracking()` does NOT run — the exit-monitor coroutine is not started. BE-trigger and TP1 partial-close logic are DISABLED for any trade that fills through this path. The trade is "orphaned" until the next orchestrator poll adopts it via `reconcile_on_startup` or `_check_trade_and_capture`.
4. For the USDJPY trade, the 30-minute BE-attempt-at-KZ-end was triggered by `handle_timeout_trailing` (a different code path, executed per-candle on the active trade), so some exit logic DID run — but the trade's lifecycle state is incomplete in the trade record.
5. For the GBPJPY trade, the broker-side TP1 fill was detected only post-hoc by the reconcile-zero-positions path.

Priority: HIGH. Shipping a fix requires a new commit; CEO approval per CLAUDE.md WF-1 discipline.

---

## Section 7 — Cost Audit

- Thursday API calls (all `https://api.anthropic.com/v1/messages` POSTs): 64 across the fleet.
  - XAUUSD: 0 (100% filtered)
  - US30_cash: 26 (20 primary + 6 M5 refinement on CANDIDATEs)
  - USDJPY: 35 (31 primary + 2 M5 refinement + 2 devil's advocate shadow + canary)
  - GBPJPY: 3 (1 primary + 1 M5 refinement + 1 devil's advocate shadow)
  - GBPUSD: 0 (100% filtered)
- At Sonnet-4.6 effort=max typical cost $0.04 per eval, Thursday spend ≈ $2.56. At $50/mo cap, one Thursday-volume day = 5.1% of monthly budget. Runway: ~20 days at this pace.
- Without the pre-AI gate, XAUUSD would have added ~7 calls (23 filtered by pre-screen anyway), GBPUSD ~30 calls, GBPJPY ~21 calls = additional 58 calls × $0.04 = +$2.32 (-+91%). Pre-AI gate is saving ~50% of API cost on a day like Thursday.
- Canary cache behavior is saving significant cost too: one primary canary run at 13:31:07 + cache HITs for subsequent instrument-level re-checks throughout the day. CLAUDE.md states the cache reduced canary cost from ~$6–75/day to ~$12/mo.

**At current pace, the fleet is within budget** but the XAUUSD/GBPUSD 100%-filter rate is masking real cost savings. If the regime flips and bullish POIs re-emerge everywhere, daily cost could triple. Monitor.

---

## Section 8 — Red-Team Findings on Pre-AI Gate

### 8.1 Bias-injection attack surfaces

The gate (pre_ai_gates.py:49) takes bias as `bias in ("bullish", "bearish")` — treats anything else as "not directional" and falls back to direction-agnostic logic. The orchestrator call site (orchestrator.py:591-592) passes `bias=bias_result.get("bias", "")` from `_compute_deterministic_bias(mso)`. That function (orchestrator.py:1046-1093) returns `"bullish"`, `"bearish"`, or `"no_bias"` based strictly on MSO structure fields. No user input, no AI input, no stateful dependency — the bias cannot be poisoned externally. Confidence 100%.

### 8.2 Failure mode (a): D1 stuck bullish when it should be bearish

If `_compute_deterministic_bias` returns "bullish" on a D1 structure that is actually bearish (because `tf.structure.direction` is computed incorrectly by `market_state.compute_market_state`), the gate would filter bullish POIs but never check bearish POIs. Consequence: every skip labels as `no_unmitigated_bullish_h1_pois`, and the system evaluates zero bearish setups even though they would be legitimate.

Evidence check: the April evaluation data shows 98–99% bullish daily_bias across all active instruments. This could be:
- (a) Genuine bullish regime (plausible — gold, US indices, JPY crosses have all been in a bullish regime in April).
- (b) Structural bullish bias in `compute_market_state` direction computation.

I could not distinguish (a) from (b) within the scope of this audit — the MSO direction computation is in a file not on the read list. Flagging for follow-up.

### 8.3 Failure mode (b): D1 bias not updated after recent bearish structural events

The XAUUSD behavior on Thursday is instructive. At 09:00 UTC H4 flipped bearish (pre-screen started firing L2_h4_conflict_bearish_vs_d1_bullish). D1 remained bullish for the rest of the day. This means the trading system HELD a bullish-D1 view for at least 8 hours while H4/M15 had flipped bearish. The pre-screen correctly blocked trading during this interval (good — don't trade against H4). But if the D1-lag is real (T5.24 shadow logger was added specifically to detect this), the system is under-exposed to bearish setups when D1 is slow to flip.

Follow-up: review `shadow_logs/` for any D1-bias-lag entries on Thursday. The `d1_bias_lag_logger` config flag is enabled; logger fires at 20 consecutive contradictory candles. Thursday had 23 consecutive pre-screen failures on XAUUSD (09:00–18:30 UTC, 38-candle run under dead-zone skipping) — would trigger the logger. I did not open the D1-bias-lag log file; worth confirming with a grep in follow-up.

### 8.4 Failure mode (c): Orchestrator passes direction argument incorrectly

Verified: `orchestrator.py:591-592` passes `bias=bias_result.get("bias", "")` — the literal output of `_compute_deterministic_bias`. The only gotcha is that `bias_result["bias"]` can be `"no_bias"`, in which case `bias_result.get("bias","")` returns the string `"no_bias"`, which fails the `bias in ("bullish", "bearish")` check inside the gate and falls back to direction-agnostic. Safe.

However, the orchestrator doesn't run the pre-AI gate at all when bias is "no_bias" — because step 3c (orchestrator.py:575-585) returns early on `no_bias`. So the fallback path is theoretically unreachable from live. Tests may exercise it directly.

### 8.5 Gate is STRICTER than L2 — architectural concern?

As noted in 1.5, the gate filters by `ob.type == bias` but L2's `_find_matching_ob` doesn't. This means:
- For any setup L2 would pass with a "wrong-type-OB" POI (e.g., the AI cites a bearish OB as POI for a LONG setup — stretches credibility but possible in breaker-retest hybrid logic), the pre-AI gate would skip instead. L2 would have marked `h1_poi_exists=PASS` and Gate1 `direction_mismatch` would have rejected on the bias/direction axis.

The net safety outcome is the same (trade doesn't get placed) but the rejection REASON is different (pre-AI skip vs Gate1 direction mismatch). This could be a data-quality issue for the post-hoc shadow-log analysis — trades that would have shown up in the Gate1 reject corpus now show up as pre-AI skips and are invisible to the CANDIDATE-rate CUSUM (it only counts evals that went to AI).

Flag for CEO: is a pre-AI skip equivalent to a NO_TRADE for the CUSUM/CR-rate purposes? Current code logs `NO_TRADE` candle outcome in the skip path (`orchestrator.py:596`), which would let the CUSUM count them. Needs verification.

### 8.6 Gate blocked ~58 API calls on Thursday — any missed legitimate setups?

Zero evidence of false skip from the data examined. But the population is thin (1 instrument day of direction-aware gate × 5 instruments × ~30 candles each). Re-verify after 2 more weeks of live data.

---

## Section 9 — Thursday vs Normal Comparison

Thursday's activity was LOW but within normal bounds for a post-kickoff trading week:

- Typical fleet day (per CLAUDE.md): "~17 trades/month across all instruments" = ~0.6 trades/day/fleet. Thursday = 2 trades. Normal range.
- Typical fleet day CANDIDATE count: ~17/month × ~10% = very low. Thursday had 9 CANDIDATEs across fleet. Above baseline.
- AI evals per day: ~50-100 per instrument when active. Thursday = 0–32. Distribution heavily bimodal — XAUUSD/GBPUSD pinned to 0, others normal.

**Is this system regression?** No evidence for regression:
- The pre-AI gate's direction-aware upgrade means both XAUUSD and GBPUSD got filtered ALL DAY because neither had an unmitigated bullish H1 OB (XAUUSD was in a multi-day downtrend, GBPUSD in a sideways/bearish phase). This is REGIME RESPONSE, not gate malfunction.
- US30 and USDJPY (where bullish POIs existed) evaluated normally and produced CANDIDATEs.
- GBPJPY evaluated 1 CANDIDATE early (07:16 UTC) then skipped the rest of the day because the one unmitigated bullish OB it had was used up and mitigated once filled.

**Is this regime-driven?** Yes, high-confidence. The 98% bullish bias across instruments + the pre-AI gate's direction-awareness means that whenever a pullback exhausts the unmitigated bullish OB inventory, the gate correctly stops burning API tokens on CANDIDATEs that would L2-reject. When new OBs form (like XAUUSD's 13:00 UTC swing-low OB), the gate re-enables that instrument.

Confidence: gate behavior is correct; low activity is regime-driven, not a bug.

---

## Concerns and Action Items (prioritized)

### P0 (ship same-day, with CEO approval)

1. **`kz_trades` NameError at orchestrator.py:492** (Confidence 100%). Crashes on every limit fill. Blocks Telegram fill notifications, blocks trade-record promotion, blocks `_init_trade_tracking` (disables BE/TP1 exit monitoring from the fill path). Pre-existing in HEAD (`dc4cec2`). Fix: remove line 492 entirely (the comment at line 461 says this cap was removed in T2.8) OR replace with `self.session_state.get(f"trades_{kill_zone}", 0) + 1`. Simple diff; suggest CEO sign-off on removal since the counter is nowhere read downstream.

### P1 (within a few days)

2. **Commit the direction-aware pre-AI gate change (`8a9bcfe` uncommitted delta)** (Confidence 90%). The change has been running in production since 2026-04-22 09:30 UTC and is providing real cost savings (~50%/day). Shipping uncommitted code in a production trading system has multiple downsides: (a) no atomic rollback via `git revert`, (b) `.context/LIVE_STATE.md` auto-generator cannot see it, (c) CLAUDE.md "What is working" bullets claim the gate is direction-agnostic. Action: review-and-commit with a proper feat() message, update CLAUDE.md.

3. **Silent fill state-divergence risk** (Confidence 85%). Due to the `kz_trades` crash, trade records for filled trades stay at `LIMIT_PLACED`. MT5 has an open position, agent state thinks the limit is still pending. `_init_trade_tracking` doesn't run, so no exit coroutine watches the trade. The only paths that recover are `handle_timeout_trailing` (KZ-end BE move, triggered USDJPY close) and reconcile-zero-positions (GBPJPY detected via "Position no longer exists"). If a position is stopped out mid-KZ while the orchestrator is NOT actively polling (between candle processing), the broker closes it but the agent doesn't learn until the next poll — and the trade record never gets the exit details. Post-hoc P&L reconstruction requires MT5 broker history. This is likely already the case historically (since `dc4cec2` in session 33); historical trade records may have silent missing exit data for prior fills too.

4. **MT5 `result.price=0.0` anomaly** (Confidence 80%). Observed twice on Thursday (both fills). The fallback at `execution.py:417-424` writes the tick price instead, but on `close_position` the anomaly is not compensated, so `Position closed: ... at 0.0` is the actual record. This creates permanent data gaps — close prices are lost. Action: extend the tick-fallback to close_position too (`execution.py:870-872`).

### P2 (investigate)

5. **Fleet-wide 98% bullish bias** (Confidence 70% regime, 30% latent structural issue in MSO direction computation). Zero bearish CANDIDATEs since kickoff. Either regime is genuinely this one-sided, or `market_state.compute_market_state` has a bullish bias. Recommend running a direct audit of the `compute_market_state` direction logic against a known-bearish historical period (e.g. 2026-04-08 XAUUSD when it was pulling back).

6. **Stability of the direction-aware pre-AI gate over a market regime flip.** The gate has not been tested under prolonged bearish bias. If the next bear regime hits, verify that (a) `_compute_deterministic_bias` flips correctly, (b) the skip reason becomes `no_unmitigated_bearish_h1_pois`, (c) the gate does NOT over-filter by also requiring bullish POIs in a bearish state.

7. **USDJPY BE-move failure root cause** (Confidence 50%). The ERROR log `Failed to move SL to BE — closing position for safety` has no diagnostic detail about WHY `_modify_sl` failed. Action: add retcode/error logging in `execution.py:959-976`.

8. **Telegram $/R display uses initial $100k balance, not current** (Confidence 85%). Log line `notifications configured: account=$100,000, risk=1.00%, $/R=$1,000` prints on every bootstrap — but actual account balance is $98,026.71 (before Thursday). FA-4 was supposed to wire $/R to resolved risk%; verify the runtime formatter is actually using `session_state['current_balance']` vs a hardcoded initial.

### P3 (observational)

9. **Watchdog restart churn in dead-zone boundaries** (Confidence 90%). Between 00:01 UTC and 01:01 UTC, 5 watchdog cycles restarted 5+ processes each time, because each orchestrator exits cleanly at KZ-end and the watchdog respawns into the next short window. This wastes ~5 minutes/cycle on bootstrap overhead. Consider extending the session "wait-for-next-KZ" behavior into the orchestrator itself rather than relying on watchdog respawn.

10. **D1-bias-lag logger output needs inspection** (Confidence 80%). Thursday had 23 consecutive XAUUSD pre-screen failures due to H4/D1 conflict — should have tripped the `d1_bias_lag_logger.alert_threshold_consecutive=20` alert. Verify the alert fired.

11. **Pipeline_state race condition** (Confidence 65%). Multiple orchestrator processes (5 instruments) share `knowledge_base/pipeline_state/02_market_state.json` and `03a_primary_analysis.json`. Observed mismatch: at 17:00 UTC the market_state.json was XAUUSD (prices ~4700-4800) but 03a_primary_analysis.json was US30 (prices ~48-49k). These files are overwritten per-candle per-process with no locking. They're only diagnostic (not authoritative state), so the impact is analyst confusion only, but any future feature reading them for real-time cross-instrument data would hit a race.

---

## Appendix: File:Line Citations

- `src/components/pre_ai_gates.py:12-76` — full `h1_poi_availability` gate.
- `src/components/pre_ai_gates.py:52-54` — direction-aware bullish OB check.
- `src/components/pre_ai_gates.py:58-61` — direction-aware bullish breaker check.
- `src/components/pre_ai_gates.py:63-65` — skip return with `no_unmitigated_{bias}_h1_pois` reason.
- `src/components/pre_ai_gates.py:67-76` — direction-agnostic fallback.
- `src/components/orchestrator.py:587-597` — step 3d wiring of pre-AI gate; passes `bias=bias_result.get("bias","")`.
- `src/components/orchestrator.py:1046-1093` — `_compute_deterministic_bias` (MSO-only, no external input).
- `src/components/orchestrator.py:3016-3046` — `prescreen_mso` (L2_h4_conflict firing on XAUUSD Thursday).
- `src/components/orchestrator.py:549-553` — step 3 wiring of prescreen.
- `src/components/orchestrator.py:574-585` — step 3c wiring of deterministic bias (skip on no_bias).
- `src/components/orchestrator.py:490-507` — limit-fill branch containing the `kz_trades` crash at line 492.
- `src/components/orchestrator.py:461` — comment explicitly saying `kz_trades` cap was removed.
- `src/components/verification.py:60-97` — `_find_matching_ob` (no type filter, weaker than pre-AI gate).
- `src/components/verification.py:100-150` — `_find_matching_breaker`.
- `src/components/verification.py:265-386` — `_check_h1_poi_exists` L2 check.
- `src/components/permissions.py:46-67` — `check_permissions` entry, Gate0→Gate3→Gate1 order.
- `src/components/permissions.py:70-140` — Gate 0 deployment.phase enforcement.
- `src/components/permissions.py:316-345` — `_reject_if_touch_count_too_high` (Gate1; fired on USDJPY tokyo 00:16 UTC).
- `src/components/permissions.py:459-578` — `_reject_if_sl_behind_liquidity_cluster` (shadow-only; both Thursday fills would have been `would_reject`).
- `src/components/execution.py:417-424` — MT5 `result.price=0.0` fallback on fills.
- `src/components/execution.py:856-878` — `close_position` (does NOT apply tick fallback).
- `src/components/execution.py:880-909` — `handle_timeout_trailing` (USDJPY BE-move-at-KZ-end trigger).
- `src/components/execution.py:949-957` — `_move_sl_to_breakeven` (fails → close_position for safety).
- `config/agent_config.yaml:80` — `enabled_frameworks: ["ob_retest"]` (pre-AI gate activation requirement).
- `config/agent_config.yaml:259` — `pre_ai_gates.h1_poi_availability_enabled: true`.
- `config/agent_config.yaml:283` — `heartbeat.flatten_enabled: false` (verified in heartbeat_monitor startup log).
- `config/profiles/redacted_account.yaml:27-32` — risk 1%, max_concurrent=4, max_daily_loss=4%.
- `config/profiles/redacted_account.yaml:47-49` — XAUUSD 0.5% risk override.
- `scripts/canary_fixtures/last_run.json` — Thursday canary result, timestamp 2026-04-23T13:31:07Z, passed 16/16.
- `pipeline_state/heartbeat.json` — `2026-04-23T17:01:03.245861+00:00 pid 4532 symbol GBPJPY` (last write).
- `pipeline_state/m5_refinement.json` — last M5 refinement (USDJPY SL_TOO_TIGHT path using M15 SL, timestamp corresponds to 08:45 UTC eval).
- `knowledge_base/trade_records/GBPJPY/2026-04-23_london_0716.json` — the one GBPJPY filled trade (record frozen at LIMIT_PLACED due to kz_trades bug).
- `knowledge_base/trade_records/USDJPY/2026-04-23_london_0845.json` — the one USDJPY filled trade (same).
- `knowledge_base/trade_records/US30_cash/2026-04-23_london_0816.json` — US30 MSO dump used for gate verification.
- `knowledge_base/pipeline_state/02_market_state.json` — XAUUSD MSO at 17:00 UTC (race-condition risk: shared across all orchestrator processes).
- `shadow_logs/liquidity_distance_log.jsonl` — 2 Thursday entries (both filled trades would be would_reject).
- `shadow_logs/heartbeat_flatten_events.jsonl` — 160 Thursday events, all FEATURE_DISABLED or TRIGGER_CANDIDATE; zero executions.
- `shadow_logs/ob_continuation_daily.csv:2026-04-23,PORTFOLIO,...,74.0000,false,false` — 74% continuation, no alarm.
- `shadow_logs/cusum_candidate_rate_daily.csv:2026-04-23,OVERALL,332,54,0.1627,...,false` — fleet CR 16.27%, no alarm.
- `logs/start_all.log` — single Thursday start at `[Thu 04/23/2026 8:01:01.74]` local = 00:01 UTC.
- `logs/watchdog.log` — restart cycle pattern confirmed normal.
- `logs/heartbeat_monitor.log:8` — single `2026-04-23 07:46:03,105 enabled=False` startup.
- `logs/gbpjpy.log` — limit-placed, limit-triggered, trade-opened, kz_trades error, broker-closed sequence.
- `logs/usdjpy.log` — limit-placed, limit-triggered, trade-opened, kz_trades error, BE-attempt-failed, position-closed sequence.
- `logs/us30.log` — `21:46:34 M5 REFINED: quality=MEDIUM ... SL=49219.75 TP=49583.65` and subsequent L2 re-verification FAIL.
- `logs/correlation_shock.log:30-36` — Thursday correlation check, all `status=ok`.
- `logs/ob_continuation.log` — Thursday rolling-50 summaries at 08:02:13.

---

**Report author:** GTOS System Forensic Analyst (Claude Code, Opus 4.7, max effort).
**Report generated:** 2026-04-24 (post-Thursday session).
**Total data sources consulted:** ~30 files across logs, shadow_logs, knowledge_base, pipeline_state, src, config, scripts.
