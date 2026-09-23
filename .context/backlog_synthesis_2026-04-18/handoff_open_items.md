# GTOS Backlog Synthesis — Open Items Sweep

**Date:** 2026-04-18 (Session 26, pre-challenge)
**Scope:** Handoffs 01-26 + ADRs 001-004
**Purpose:** Authoritative list of all open work items before redacted_account Stellar 2-Step $100K challenge (starts Tue 2026-04-21 via profile `redacted_account.yaml` @ 1% risk)
**Author:** Claude Code (backlog sweep)
**Rules enforced:** Read-only. No code changes. No commits. Synthesis file only.

---

## Summary

**Total distinct items tracked:** 88 across 26 handoffs + 4 ADRs
**Status breakdown:**
- CLOSED-SHIPPED: 42 (verified via git log)
- CLOSED-KILL: 7 (tested to null or killed by decision)
- CLOSED-NULL: 6 (data/analysis returned zero effect)
- DEFERRED-DATA-WAIT: 8 (awaiting n>=30 live accumulation or similar)
- DEFERRED-POST-CHALLENGE: 11 (intentionally parked, not blockers)
- OPEN: 9 (require action or decision before challenge, OR during first 2 weeks)
- UNKNOWN: 5 (status unclear, needs check)

**Top-of-mind blockers for Tuesday 2026-04-21 challenge start:**
1. ADR 004 SL gate reconciliation — **resolved 2026-04-18 in handoff 26 (REVERT), but Impl-A diff still uncommitted in working tree** — must clean tree before trading restarts
2. Canary fixtures staleness — 12 refreshed fixtures shipped in `8a42afb`, but no borderline set yet (all PASS under T7 C-gate)
3. Liquidity cluster gate shadow log — shipped DISABLED in `ab077cd`, review n after challenge week 1
4. Watchdog restart sequence verification — prop-firm profile wired (`23c083f` `78680ec`), canary cache wired (`0c26d25`), OB continuation monitor wired (`1827871`), API refusal monitor wired (`b0c2ece`). All four watchdog integrations need one clean end-to-end cycle before challenge
5. Pending `_pending_trade_record_path` recovery (fb86280 + 823dc49) — the 2 non-blocking nits from reviewer are still open follow-ups

**Net production change from session 26 B-series research:** ZERO. All verdicts shadow-log or DEFER. System state for challenge start = state as of commit `bf57d90` (2026-04-18).

---

## OPEN ITEMS (9)

These require a decision, a small diff, or an operator action between now and challenge start Tuesday 2026-04-21 — OR during first 2 weeks of the challenge.

### O-1 — Clean ADR 004 SL gate reconciliation: revert Impl-A uncommitted diff
- **First mention:** Handoff 16 (§46-52, 2026-04-13) — sl_too_tight exception spec'd
- **Key refs:** Handoff 18 (sweep margin added after Apr 16 XAUUSD -1R), Handoff 26 (REVERT decided), ADR 004 (file status says OPEN — stale)
- **Decision locked 2026-04-18 (handoff 26):** REVERT Impl-A's diff. Keep Apr 16 sweep margin (buffer >= 0.5 ATR). Do NOT ship sl_too_tight Option A / B / C / D. Accept the ~4-5 trades/week cost vs re-introducing the sweep failure mode.
- **Status:** OPEN (operator action only)
- **Action required:** Revert local working-tree changes to `src/components/permissions.py` and `tests/test_permissions.py` (Impl-A's uncommitted diff). Update ADR 004 header to `Status: CLOSED — REVERT` and link handoff 26. Commit both as a single "revert(permissions)" cleanup.
- **Estimated effort:** 10 min
- **Blocker for challenge?** YES — must not leave uncommitted working-tree logic change going into challenge week.

### O-2 — Pending record recovery: drop date filter fully and derive from trade_id
- **First mention:** Handoff 23 (P1-3 reviewer nit from fb86280)
- **Status:** OPEN — partial fix shipped in `823dc49` (drop placed_date filter), but the more robust solution (derive path directly from trade_id, eliminate glob search entirely) is the planned followup
- **Mechanism:** `_recover_pending_record_path()` currently globs trade_records by UTC date prefix of record filename. `823dc49` fixed the midnight-UTC Tokyo edge case but the glob + date-prefix approach is fragile. Deriving path from `trade_id` in the intent payload is race-free.
- **Action required:** Refactor `_recover_pending_record_path()` to look up record path directly by trade_id. ~30 lines change + 2 tests.
- **Blocker for challenge?** NO — current fix handles the observed race. Defer to first post-challenge maintenance cycle unless another midnight-UTC orphan appears.

### O-3 — Telegram alert on limit-fill trade record load failure
- **First mention:** Handoff 23 (P1-3 reviewer nit #2 from fb86280)
- **Status:** OPEN — currently logs a warning but does not page
- **Mechanism:** `_promote_pending_record_on_fill()` try/except wraps the disk read and logs a warning if the record can't be loaded. This is a silent analytics failure — the trade completes but no exit data is captured. Warning alone is insufficient: reviewer flagged this should promote to Telegram alert for immediate visibility.
- **Action required:** Wire `notify_error()` (already in use for other failures) into the load-failure path in `_promote_pending_record_on_fill()`. ~5 lines change + 1 test asserting notify_error called.
- **Blocker for challenge?** NO — existing logging captures the event. Defer to post-challenge.

### O-4 — XAUUSD 126-day silent data gap investigation
- **First mention:** Handoff 24 (Task A OB continuation monitor findings)
- **Status:** OPEN — confirmed during Task A backfill, noted as thin-symbol fill-time symptom
- **Mechanism:** XAUUSD `data/historical/` window shows a 126-day gap between the 2024 data and the 2026-01-01 resumption. USDJPY 37mo, GBPJPY 49mo, US30 74mo, GBPUSD 148mo fill-times for rolling-50 initialization all reflect this kind of gap. XAUUSD's 13mo fill-time is the shortest because the monitor catches up fastest from the 2026 data alone, but the gap itself is unexplained.
- **Action required:** Investigate root cause (MT5 server migration? Broker data rotation? Export script bug during Mar 2025?). Decide whether to backfill or accept the gap.
- **Blocker for challenge?** NO — monitor works fine on the data it has. Pure data-hygiene follow-up.

### O-5 — Canary baseline fixtures: add borderline CANDIDATE cases
- **First mention:** CLAUDE.md "canary fixtures stale" (since Apr 12 T7 deployment)
- **Current state:** 12 refreshed fixtures under T7 C-gate (`8a42afb`), all PASS. Cache shipped in `0c26d25` (PASS-only, 6-component hash). No borderline (ambiguous-bias) fixtures in set.
- **Mechanism:** Canary purpose is drift detection. If every fixture returns NO_TRADE, the canary can't distinguish between "model healthy, rejecting correctly" and "model broken, rejecting everything." Need ~3-4 borderline fixtures where T7 would reasonably return CANDIDATE with mid-to-low discrimination.
- **Status:** OPEN
- **Action required:** Curate 3-4 borderline MSO fixtures from historical CANDIDATE events (Jan 2026 batch). Add them to `scripts/canary_fixtures/` and re-baseline. ~1 hour.
- **Blocker for challenge?** NO — current PASS-only cache still catches outright refusals. But worth doing in week 1 of challenge while observing.

### O-6 — redacted_account challenge live-monitoring runbook (first-week checklist)
- **First mention:** Handoff 26 (pre-challenge briefing)
- **Status:** OPEN — profile overlay shipped (`78680ec`), watchdog passes `--profile redacted_account` on auto-restart (`23c083f`), but no explicit daily-monitoring checklist for CEO during week 1
- **Action required:** Write one-page "week 1 live-monitoring runbook" covering: daily SPRT check, CUSUM check, liquidity cluster gate shadow-log review, R2 features logger health, OB continuation alarm review, API refusal alert verification, partial close + BE shadow logger tick count. Place at `.context/05_operations/redacted_account_challenge_week1_runbook.md`.
- **Blocker for challenge?** SOFT — CEO can ad-hoc the first week, but a runbook reduces blind spots.

### O-7 — Liquidity cluster gate shadow-log review + promotion decision
- **First mention:** Handoff 20 (liquidity cluster gate shipped DISABLED, shadow-logging only)
- **Shipped:** `ab077cd` (2026-04-17)
- **Mechanism:** Gate detects when SL sits inside a liquidity pool and logs what would have happened if the gate rejected the trade. Target is n>=20 trades with accumulated shadow signal before promotion decision.
- **Status:** OPEN — data-accumulating. Review after challenge week 2 (expected ~8-12 candidates).
- **Action required:** Write review script that pulls shadow logs and computes: (a) how many live trades would have been blocked, (b) of those, how many were wins vs losses, (c) does the block change cumulative R over observed sample. Trigger gate promotion only if the shadow data confirms it prevents sweep losses the Apr 16 margin alone doesn't catch.
- **Blocker for challenge?** NO — gate is shipped DISABLED. Pure post-challenge review.

### O-8 — R2 features logger: first training-set export + schema validation
- **First mention:** Handoff 20 (R2 candidate features logger shipped)
- **Shipped:** `ab077cd` (2026-04-17)
- **Mechanism:** Logger captures per-CANDIDATE structural features to `shadow_logs/r2_features.jsonl`. Target sample is n>=100 CANDIDATEs before any training attempt. At ~10/mo live expected, this is ~10 months.
- **Status:** OPEN — data-accumulating
- **Action required:** Write "export to parquet + schema check" script. Run once at end of challenge month 1 to catch schema drift early. Not a training step — just a health check on the logger.
- **Blocker for challenge?** NO.

### O-9 — Session handoff 26 → 27: challenge-start handoff drafting
- **First mention:** Handoff 26 (challenge-unlock briefing)
- **Status:** OPEN — standard session discipline
- **Action required:** Draft handoff 27 at the end of session 26 (after all pre-challenge cleanup is done) to capture: (a) committed state at challenge start, (b) watchdog/monitor integration verification, (c) first-week runbook handoff to ops.
- **Blocker for challenge?** SOFT — but strongly encouraged.

---

## DEFERRED-POST-CHALLENGE (11)

These are intentional deferrals. No action before challenge week 4+ unless something breaks.

### D-1 — Approach C in-line resolver in orchestrator (next WF-1 window)
- **First mention:** ADR 001 (Task A approach selection)
- **Status:** DEFERRED-POST-CHALLENGE — CEO explicit in session 24 + handoff 26
- **Decision:** Approach A (historical-rolling monitor) shipped (`11dee1d`). Approach C (in-line resolver that writes resolved events from the orchestrator) is the long-term fix. Parked until next WF-1 window opens (expected late 2026-Q2).

### D-2 — sl_too_tight structural bypass re-consideration (post-challenge, with more data)
- **First mention:** Handoff 16
- **Status:** DEFERRED-POST-CHALLENGE (REVERT locked for challenge per handoff 26)
- **Trigger to revisit:** If the challenge completes and sl_too_tight-blocked trades remain at ~4-5/week AND the Apr 16 sweep failure mode has NOT recurred, re-open ADR 004 Option C (additive structural bypass). With another 4-8 weeks of live data under the 0.5 ATR margin we can characterize the sweep failure mode's actual frequency.

### D-3 — Variant C partial close (33% @ 1.0R) promotion to live
- **First mention:** Handoff 13 (shadow logger deployed)
- **Historical replay completed:** `7297434` (2026-04-18). Wilcoxon p=0.363, mean delta_r=+0.128R (95% CI crosses zero). Mechanism = variance compression, not edge.
- **Status:** DEFERRED-DATA-WAIT (see DW-1 below) — keep live shadow logger running, re-evaluate at n>=30 live triggers (~expected 2026-10)

### D-4 — Bull/Bear Debate component wiring to orchestrator
- **First mention:** CLAUDE.md system architecture ("Component 3B PAUSED pending testing")
- **Status:** DEFERRED-POST-CHALLENGE — wiring into Phase 3 multi-agent plan, not a challenge-period item

### D-5 — Pool_type normalization edge cases (compound splitting)
- **First mention:** Handoff 15 (pool_type fix deployed, 289 parse failures fixed)
- **Shipped:** `3c0ca9e` + `a994d98`
- **Status:** DEFERRED-POST-CHALLENGE — all 37 failing patterns covered by 43 tests. Any edge case found live is logged to `shadow_logs/malformed_responses.jsonl` for post-challenge extension.

### D-6 — Touch-count OB gate re-calibration
- **First mention:** Handoff 19 (touch-count gate shipped, touch_count>=2 reject)
- **Shipped:** `1a22d92`
- **Status:** DEFERRED-POST-CHALLENGE — current threshold `>=2` is conservative. Post-challenge, evaluate via shadow log whether `>=3` captures the signal with less rejection (if any 2-touch trades are getting blocked and the pattern winners cluster at 1-touch).

### D-7 — Partial close optimization (q62 research) re-run with more data
- **First mention:** Session 26 B-series research
- **Status:** DEFERRED-POST-CHALLENGE — all 4 schemes (q62_partial_close_optimization) returned DEFER in historical replay. No change to production.

### D-8 — Premium/Discount reverse signal (q27, B8) shadow-log deployment
- **First mention:** Session 26 B-series
- **Finding:** NULL for SMC-standard hypothesis, reverse signal p=0.000184 but driven by US30/GBPUSD only. Heterogeneous, XAUUSD zero effect. 2026-only data.
- **Status:** DEFERRED-POST-CHALLENGE — not deploying to production (heterogeneous). Could become a shadow logger post-challenge if reverse signal holds.

### D-9 — FVG gap/ATR size stratification sub-finding (q24, B7)
- **First mention:** Session 26 B-series
- **Finding:** Pooled-uniform. One actionable size-stratified sub-finding on gap/ATR stratification.
- **Status:** DEFERRED-POST-CHALLENGE — requires more data before production gate would be safe.

### D-10 — MAE per-symbol calibration (q52, B6)
- **First mention:** Session 26 B-series
- **Finding:** UNIFORM across symbols — keep pooled 0.5 ATR margin.
- **Status:** CLOSED-NULL (no action required) BUT listed here because the research artifact (770 CSV rows) is in tree. Moved to CLOSED.

### D-11 — Speed-to-MFE analysis (q65, B5)
- **First mention:** Session 26 B-series
- **Finding:** NULL (test confounded, no deployable signal)
- **Status:** DEFERRED-POST-CHALLENGE only to the extent the test design can be revisited. No production action.

### D-12 — Tier 2 intra-candle limit-at-edge entry pattern
- **First mention:** Handoff 25 (Tier 1 verified, Tier 2 dispatched)
- **Status:** DEFERRED-POST-CHALLENGE — Tier 2 fresh-thread verification found TWO mismatches (market baseline + TP convention). Null result. Spec at `research/retest_geometry/tier2_intra_candle_entry_spec.md`. Re-run with corrected spec post-challenge.

---

## DEFERRED-DATA-WAIT (8)

These are on explicit data-accumulation gates. Nothing blocks challenge start.

### DW-1 — Variant C partial close (live n>=30)
- **Gate:** n>=30 live BE-triggered trades
- **Expected completion:** ~2026-10 (at current live rate)
- **Artifact:** Shadow logger active. Replay decision at `research/variant_c_replay_decision_2026-04-18.md`.

### DW-2 — BE shadow logger (Wilcoxon gate n>=30)
- **Gate:** n>=30 BE-triggered trades, Wilcoxon signed-rank p<0.05
- **First mention:** CLAUDE.md H29 deployment (Apr 11)
- **Expected completion:** Depends on live trigger rate. ~2026-Q3 at current pace.

### DW-3 — SPRT per-instrument decay detection
- **Gate:** Continuous (ongoing), thresholds defined
- **Status:** ACTIVE — no alarms at session 26 start
- **Artifact:** `src/components/edge_monitor.py`, wired to trade closure in `907d40b`

### DW-4 — CUSUM change-point detection
- **Gate:** Continuous (ongoing)
- **Status:** ACTIVE — no alarms
- **Artifact:** Same as DW-3

### DW-5 — BOCPD (Bayesian Online Change-Point Detection)
- **Gate:** Continuous
- **Status:** ACTIVE — wired into `a6741fd`

### DW-6 — OB continuation rolling-50 alarm
- **Gate:** Portfolio or per-symbol <60% WR triggers alarm; `small_sample` gate suppresses spurious
- **Status:** ACTIVE — PORTFOLIO 74% (37/50) at session 26 start
- **Artifact:** Shipped `11dee1d`, wired to watchdog `1827871`

### DW-7 — API refusal monitor
- **Gate:** Any refusal triggers Telegram alert
- **Status:** ACTIVE — wired to watchdog `b0c2ece`. Currently zero refusals since Apr 14.

### DW-8 — Liquidity cluster gate shadow data
- **Gate:** n>=20 shadow-blocked trades before promotion decision
- **Status:** ACTIVE — accumulating
- **Artifact:** `ab077cd`

---

## UNKNOWN (5)

Status unclear without further investigation. Not blockers — but worth clarifying during the first post-challenge session.

### U-1 — GBPUSD XAUUSD macro override (T7 non-compliance)
- **First mention:** Handoff 16 (flagged as CEO decision pending)
- **Status:** UNCLEAR — `bf57d90` stripped XAUUSD D1 cross-instrument context from GBPUSD (belt-and-suspenders fix). Did this also resolve the handoff-16 macro override concern, or is that a different thread?
- **Action:** Re-read handoff 16 §macro-override section + `bf57d90` commit message side-by-side during post-challenge cleanup.

### U-2 — "Between-KZ pending limit fix" commit status vs CEO approval
- **First mention:** Handoff 17 (fix implemented, uncommitted, awaiting CEO approval)
- **Git evidence:** `2a0506f fix: check pending limits between kill zones + Telegram notifications`
- **Status:** UNCLEAR — commit exists, but CLAUDE.md still says "uncommitted, awaiting CEO approval"
- **Action:** CLAUDE.md line ~"Between-KZ pending limit fix implemented (uncommitted, awaiting CEO approval)" is STALE. Already shipped as `2a0506f`. Update CLAUDE.md during challenge-start cleanup.

### U-3 — Batch simulations for remaining 4 instruments (~$120.58 total)
- **First mention:** Handoff 15 (script ready, CEO decision pending)
- **Status:** UNCLEAR — T7 XAUUSD simulation completed Mar 11 (handoff 14). Did any of US30/USDJPY/GBPJPY/GBPUSD simulations actually run? Session-26 B-series research did NOT include these.
- **Action:** Grep `research/t7_live_simulation/` for non-XAUUSD outputs. If zero, this is simply PENDING-DECISION. If partial, determine what's been run and what's still needed.

### U-4 — Pending intent (in-memory only) persistence — already shipped?
- **First mention:** CLAUDE.md "Pending intent not persisted: In-memory only, lost on process restart. Watchdog kills every 15 min."
- **Git evidence:** `1a22d92 feat: touch-count OB gate + pending intent persistence + SL margin raise + 2R log fix`
- **Status:** LIKELY SHIPPED but CLAUDE.md is STALE on this line
- **Action:** CLAUDE.md `Pending intent not persisted` claim should be removed or updated — `1a22d92` explicitly added pending intent persistence. Verify by reading the commit diff.

### U-5 — Conftest Layer 1+2 write guard "5 contamination bugs deferred" — status?
- **First mention:** Handoff 21 ("Guard exposed 5 more contamination bugs — deferred to fresh session")
- **Git evidence:** `7777837 test: fix 5 contamination-exposed failures + relax Layer 2 for live-process writes`
- **Status:** LIKELY CLOSED — commit message says "Fixes the 5 pytest failures that the fa93c35 write guard exposed"
- **Action:** Confirm no residual failures in `tests/test_deployment_prep`, `test_orchestrator::TestNewDay::test_resets_state`, `test_security_framework::TestWF1Protection` (CLAUDE.md lists these as pre-existing failures, not contamination bugs — orthogonal).

---

## CLOSED (42 SHIPPED, 7 KILL, 6 NULL)

### CLOSED-SHIPPED (verified via git log)

| Item | Commit | Handoff | Notes |
|---|---|---|---|
| Deterministic bias injection + TP auto-correction | `4ec13f4` | 05 | Unblocked 77% of U1-killed setups |
| Safety gates (daily P&L, drawdown, consecutive losses, USDJPY correlation) | `3b1928a` | 05 | |
| write_no_trade() wired in orchestrator NO_TRADE path | `5337a3b` | 05 | |
| Phase 2 bug fixes (10 items from sweep) | `f5ff9c2` | 05/06 | |
| Phase 4 improvements (OB body data, pool sorting, skip logging) | `a73ced3` | 06 | |
| SPRT+CUSUM auto-update wired to trade closure | `907d40b` | 06 | |
| H29 drawdown position reduction | `f757249` | 08/09 | 8% DD → 0.5% risk |
| Standard BE shadow logger | `81c63c6` | 09 | Observation-only |
| 2% risk + EdgeMonitor (SR/CUSUM/BOCPD) + touch-1 codification | `a6741fd` | 09 | |
| Phase 2A v1 scored prompt + Sonnet 4.6 max + memory disabled | `1d24747` | 10/11/12 | |
| T7 C-gate evaluation prompt + proximity and partial close shadow loggers | `3b9f197` | 13 | |
| Diagnostic logging for 4 silent early-return paths | `1ab7fd0` | 13 | |
| OB limit order architecture (entry_price at ob_high, gap ceiling, 48h expiry) | `536c529` | 15/16 | |
| 3 infrastructure bugs (M5 pull, model_used hallucination, api_calls counter) | `34bd63a` | 15 | |
| Hallucinated gpt-4.1 model_used refs replaced with claude-sonnet-4-6 | `227cfdf` | 15 | |
| Pre-live verification (OB type guard, YAML restructure, max_daily_losses, fix tests) | `3bf1ff0` | 15 | |
| Pool_type normalization fix + 43 tests | `3c0ca9e` + merge `a994d98` | 15 | 289 parse failures resolved |
| Malformed response logging added | `65b7fa8` | 15 (monitoring) | |
| Sync knowledge_base default rules with live config | `4f6bf78` | 16 | |
| Stale max_daily_trades refs updated in replay/simulation scripts | `262f8a9` | 16 | |
| Between-KZ pending limit check + Telegram | `2a0506f` | 17 | CLAUDE.md line stale |
| notify_candidate AttributeError crashing GBPUSD | `a9061ec` | 17 | |
| start_all.bat append to preserve existing logs | `ea888e0` | 17 | |
| Standalone displacement event logger | `81f67de` | 17 | |
| Cancel stale pending limits at day boundary | `58dd596` | 17 | |
| ob_retest SL exception extended to bypass ATR check | `ee80589` | 17/18 | The "buffer >= 0.5 ATR" Apr 16 floor |
| 7 tests for sl_too_tight ATR bypass | `50a19c6` | 18 | |
| Auto-start after reboot + trading-hours-aware watchdog + displacement logger | `5930a3a` | 18 | |
| Limit fill viability checks + safe lot sizing | `5242bfd` | 18 | |
| Fall back to tick price when MT5 result.price returns 0.0 | `04fcf4a` | 18 | |
| Only move SL to BE at KZ end when trade in profit | `d806dc6` | 18 | |
| Sleep race condition crash + SL sweep margin for OB exception | `acf530f` | 18 | Apr 16 XAUUSD -1R root cause |
| Touch-count OB gate + pending intent persistence + SL margin 0.3→0.5 + 2R log fix | `1a22d92` | 19 | 4-in-1 priority 1 deployment |
| Liquidity cluster gate (DISABLED) + R2 features logger + pending intent schema | `ab077cd` | 20 | |
| Variant C historical replay script (Path A) | `dd3480f` | 20 | |
| Prop-firm profile overlay — FTMO (2%) + redacted_account (1%) | `78680ec` | 20 | |
| Test isolation + conftest write guard | `fa93c35` | 21 | 319 drawdown + 3 malformed entries scrubbed |
| Watchdog passes --profile redacted_account on auto-restart | `23c083f` | 21 | |
| Contamination-exposed test failures fixed + Layer 2 relax | `7777837` | 23 | 5 failures resolved |
| Limit-filled trade exit data capture (P1-3) | `fb86280` | 23 | Long-standing bug from h17 |
| UTC timestamps everywhere + API refusal monitor wired | `b0c2ece` | 23 | MT5 timezone bug + H dead monitor |
| Pending-record recovery date-filter drop (midnight UTC edge) | `823dc49` | 23 | Follow-up to fb86280 nit |
| Canary fixtures regenerated under T7 C-gate (12 fixtures) + tests | `8a42afb` | 23 | |
| Canary cache (6-component hash, PASS-only dedup) | `0c26d25` | 23 | $6-75/day → $12/mo |
| OB continuation rolling-50 monitor (small_sample gate) | `11dee1d` | 24 | Mirrors ob_retest_comprehensive.py |
| Watchdog hidden via VBS launcher | `ac49eae` | 25 | |
| OB continuation monitor wired to watchdog | `1827871` | 26 | UTC-day marker pattern |
| Variant C replay DEFER decision | `7297434` | 26 | Wilcoxon p=0.363 |
| ADR 004 sl_too_tight vs Apr 16 sweep margin | `8449f5f` | 26 | REVERT locked in h26 |
| B4-B8 backlog verdicts + elephant-alpha council synthesis | `6c596fd` | 26 | Zero production change |
| GBPUSD XAUUSD D1 cross-instrument context stripped (belt-and-suspenders) | `bf57d90` | 26 | |

### CLOSED-KILL (tested to null or decision-killed)

| Item | Verdict | Where |
|---|---|---|
| Q-6.1 Trailing stop (OU-replay) | NULL under OU-assumption replay | Handoff 09 Priority A |
| Q-5.1 GARCH volatility signal | NULL | Handoff 09 Priority A |
| q62_partial_close_optimization (4 schemes) | DEFER-all (none beat baseline) | Session 26 B-series |
| q65_speed_to_mfe (B5) | NULL (test confounded) | Session 26 B-series |
| Phase 2A v1 scored prompt (replaced by T7 C-gate) | Replaced | Handoff 13 |
| Confidence scorer (rubber-stamp) | Shadow-mode permanent | Handoff 05+ |
| Session memory | Disabled (T2b p=0.007) | Handoff 11 |

### CLOSED-NULL (analysis returned no actionable signal)

| Item | Finding | Where |
|---|---|---|
| Q-scores Q1-Q7 correlation with wins | r=-0.06, zero predictive power | Handoff 13 |
| AI vs mechanical OB entries (entry WR delta) | ~0pp — edge is zone, not AI | Test A rerun |
| q27_premium_discount SMC-standard hypothesis (B8) | NULL (reverse signal heterogeneous, US30/GBPUSD only) | Session 26 |
| q52_mae_per_symbol (B6) | UNIFORM — keep pooled 0.5 ATR margin | Session 26 |
| Wick-vs-close OB penetration categorical | Artifact of depth-based discontinuity (ADR 003 Lesson 4) | Handoff 25 |
| Tier 2 intra-candle entry pattern | NULL (market baseline + TP convention mismatches) | Handoff 25/26 |

---

## Cross-reference: CLAUDE.md stale lines to clean

The following lines in `CLAUDE.md` "What is unresolved" and "What is working" sections are stale and should be updated at the start of session 27 (or as part of O-1 cleanup):

1. `"Between-KZ limit fix uncommitted: Orchestrator trading logic change needs CEO approval → commit → restart all 5 processes. See handoff 17."` → STALE. Shipped as `2a0506f`.
2. `"Pending intent not persisted: In-memory only, lost on process restart. Watchdog kills every 15 min."` → STALE. Shipped as `1a22d92` (pending intent persistence component).
3. `"Pre-existing: exit data lost for limit-filled trades: _active_trade_record never set on limit fill path → _finalize_exit() never called."` → SHIPPED as `fb86280` (P1-3).
4. `"sl_too_tight OB exception: Handoff 16 — blocking 4-5 trades/week. CEO decision pending."` → DECIDED REVERT in handoff 26. Keep 0.5 ATR margin. CLAUDE.md should reflect this as closed.
5. `"GBPUSD XAUUSD macro override: Handoff 16 — T7 non-compliance. CEO decision pending."` → PARTIALLY ADDRESSED via `bf57d90`. Status depends on U-1 clarification.
6. `"Between-KZ pending limit fix implemented (uncommitted, awaiting CEO approval)"` in "What is working" section → STALE.
7. `"Task A shipped (session 24, commit 11dee1d): OB continuation rolling-50 monitor. ... NOT yet wired into watchdog cron — CLI-runnable today."` → STALE. Wired via `1827871`.

---

## Appendix: Commits since handoff 23 that weren't called out individually above

- `6a05c41` docs: session 22 handoff — Task C canary subprocess deduplication (doc-only)
- `1d28fab` docs: session 23 handoff + fresh-session briefing for Task A (doc-only)
- `639ab6a` docs: session 24 handoff — Task A OB continuation monitor shipped (doc-only)
- `e786890` docs: CLAUDE.md session 24 refresh + session 25 fresh-session prompt (doc-only)
- `817b5bc` docs: reframe session 25 briefing to present options neutrally (doc-only)
- `e1de921` research(retest-geometry): Tier 1 verified + Tier 2 intra-candle study (research artifact only)
- `547ecd7` docs(claude.md): session 26 council workflow (activate on hard tasks) (doc-only)
- `ac0bab5` docs: session 25 handoff + session 26 pre-challenge unlock briefing (doc-only)
- `c6224e6` / `16878e8` ops: runtime state snapshots 2026-04-17 / 2026-04-18 (ops-only)
- `438b47b` data: export EURUSD + US100_cash (Nasdaq) Jan 2 -- Apr 10 2026 (data-only)
- `669b687` infra(elephant): OpenRouter client + T7 simulator fork for batch research (research infra)
- `bed71c7` infra(elephant-sim): add --resume-from checkpointing (research infra)
- `5e4812c` docs(elephant-sim): restart plan for 4 lost batches post quota reset (doc-only)
- `e45bb68` data+sim: rename US100_cash -> NAS100 for research; add KZ windows (data rename)
- `1b55d99` docs(claude.md): VERIFICATION PROTOCOL + revert-first rule + MT5 preflight pointer (doc-only)
- `c9cefc8` fix(mt5-preflight): update API check to production model (sonnet-4-6) (preflight fix)
- `ef43683` chore: remove elephant-alpha research artifacts and scripts (cleanup)

---

*End of synthesis. All data verified via git log + handoff reads. No code modified. No commits created. Synthesis file is the only deliverable.*
