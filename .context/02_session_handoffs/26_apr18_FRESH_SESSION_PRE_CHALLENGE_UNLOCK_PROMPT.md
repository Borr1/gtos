# Fresh Session 26 — Pre-Challenge Capability Unlock Sprint

**Issued:** 2026-04-18 (Sat) by main thread Claude after CEO flagged context drift in session 25.
**Target window:** Sat 2026-04-18 → Mon 2026-04-20 (~48h working time).
**Challenge start:** Tue 2026-04-21 — redacted_account Stellar 2-Step $100K @ 1% risk (settled, do NOT re-discuss).
**Your role:** You are Claude Code, fresh context. The outgoing session started recycling already-settled decisions and the CEO correctly called the drift out. Don't trust outgoing-session conclusions without re-verifying against source/git.

---

## MISSION (one sentence)

**Ship as many VALIDATED capability unlocks as possible to the live system before the funded challenge starts Tuesday, using parallel agent dispatch, without breaking WF-1 discipline or statistical rigor.**

"Validated" = either (a) already validated by a completed study/batch test, or (b) deployable as observation-only with no decision impact, or (c) a known bug fix where the broken behavior is confirmed from logs/trade records.

This is NOT a research sprint and NOT "defer everything to post-challenge." It's the middle path: max throughput on things that are actually ready.

---

## MANDATORY READING (do all of these before dispatching anything)

1. `CLAUDE.md` — project instructions, live state, validated numbers
2. **This file** — you're reading it
3. `.context/02_session_handoffs/25_apr18_retest_tier1_verified_tier2_dispatched_handoff.md` — **read the "Tier 2 fresh-session re-verification" section at the bottom carefully**; Tier 2 verdict is NULL/DEFER, do not re-litigate
4. `.context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md` — OB monitor shipped, needs cron-wire
5. `.context/02_session_handoffs/20_apr17_liquidity_gate_R2_logger_handoff.md` — liquidity gate shipped DISABLED, what's in shadow
6. `.context/02_session_handoffs/19_apr17_priority1_deployment_handoff.md` — touch-count + pending persistence SHIPPED; between-KZ fix was committed on Apr 14 per this handoff's retrospective
7. `.context/00_core/quick_reference_card.md` — kill zones, SPRT tables, emergency stops
8. `.context/03_analysis/research_execution_plan_113q.md` — 113 untested questions; many are pure-data replays deployable this weekend
9. `.context/06_decisions/` — ADRs 001, 002, 003 (Task A approach, Tier 2 scope, corrected methodology + Lesson 4)

Then `git log --oneline --since="2026-04-07" -- src/ prompts/ config/ scripts/` to see what's actually landed.

---

## STATE VERIFICATION CHECKLIST (do FIRST, before any agent dispatch)

The outgoing session had stale state on some items. **Verify each of these before deciding whether it's must-fix or already-done:**

| # | Claim to verify | How to check | If TRUE → | If FALSE → |
|---|---|---|---|---|
| 1 | Between-KZ pending-limit fix is committed (handoff 19 says `2a0506f` Apr 14) | `git show 2a0506f --stat` then grep orchestrator.py for `_check_pending_limit_outside_kz` | Skip from must-fix; confirm live processes restarted post-commit via log mtime | Add to must-fix; this is the single biggest leak (+1.5R/month) |
| 2 | `pending_intent` disk persistence shipped (handoff 19 `1a22d92`) | grep `_load_pending_intent` in execution.py; confirm `.pkl` files exist in `knowledge_base/meta/` | Already done; skip | Unexpected; investigate |
| 3 | `execution.py:233` pending_intent destruction race — still open? | Read `execution.py` ~line 230-250; check if `pending_intent = None` happens before or after MT5 order confirmation | Open → must-fix | Fixed → skip |
| 4 | `_active_trade_record` never set on limit fill path — still open? | Read `execution.py` limit-fill code path + search for `_active_trade_record` assignments; check if `_finalize_exit` is reachable from limit fills | Open → must-fix (silent exit data loss every limit fill) | Fixed → skip |
| 5 | OB continuation monitor cron-wired? | Check Task Scheduler / `scripts/watchdog*` for ob_continuation_monitor references | Wired → skip | Not wired → 5-min task, add to must-fix |
| 6 | Canary fixtures: how many return CANDIDATE under T7? | `python scripts/canary_test.py` dry-run or read `scripts/canary_fixtures/` + known CR | All NO_TRADE → refresh needed | Mixed → possibly skip |
| 7 | Liquidity gate shadow log — how many rows accumulated since Apr 17? | `wc -l shadow_logs/liquidity_distance_log.jsonl`; count `"decision":"would_reject"` | ≥100 would_reject → calibrate margin_atr, consider enable decision | <100 → leave disabled, continue logging |
| 8 | Variant C shadow log — any triggers since deploy? | `wc -l shadow_logs/partial_close_shadow_log.jsonl` | Exists + n≥30 → promotion decision ready | Empty → run `scripts/variant_c_replay.py` on batch data (handoff 20 P1) |

**Do this verification FIRST.** Every item on the Tier A list below depends on it.

---

## SETTLED DECISIONS — DO NOT RE-OPEN

The outgoing session started surfacing these as "open" — they are not.

- **1% risk per trade for the funded challenge.** redacted_account Stellar 2-Step $100K. Decided handoff 19/20. The live FTMO demo may be at 2%; challenge config is 1%.
- **redacted_account Stellar 2-Step $100K** is the challenge vehicle. Not FTMO, not 1-Step, not a different prop firm.
- **Tue 2026-04-21 challenge start.** Sun = deploy, Mon = demo verification, Tue = go-live.
- **T7 C-gate prompt is frozen during the challenge window.** Do not propose prompt changes.
- **Sonnet 4.6 + effort=max** for live primary analyzer. Opus 4.6 is empirically worse (P2C: CR 19% vs 38%, rejects-WR 65.3%). Don't propose Opus for the live gate.
- **Session memory = disabled live** (T2b: p=0.007 suppression). Don't re-enable.
- **Tier 2 intra-candle entry study = NULL / DEFER.** Two independent mismatches (market baseline + OB-anchored TP). Do not re-run, do not shadow-deploy, do not do M5/M1 re-run. See handoff 25 bottom section.
- **Wick/close categorical = REJECTED** (ADR 003 Lesson 4, artifact of existing SL margin). No wick/close gate.
- **SL margin = 0.5 ATR** (raised from 0.3 in `1a22d92`). Empirically near optimal cliff. No change recommended.
- **Touch-count gate: reject ≥2 touches.** Live since `1a22d92`. Do not relax.
- **Liquidity cluster gate: ships disabled + shadow-logging.** Enable decision needs 100+ `would_reject` rows first.
- **OB continuation monitor = #1 primary decay metric.** Test A rerun p=0.003 + Tier 1 100% WR confirm the edge.
- **Multi-TF M15 expansion = KILLED** (M15 OB continuation 49.9%).
- **Macro overlay = CLOSED** (COT p=0.495, DXY R²=0.136, real rates p=0.74). No macro filter layer.
- **GBPUSD = observer mode through 2026-04-30.** Don't propose shutting down.
- **5-symbol set locked:** XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD (observer). No additions pre-challenge.
- **WF-1 lock cancelled Apr 11** (handoff 09) — validated changes can deploy directly with CEO approval. Still requires validation + approval + testing.
- **H29 drawdown reduction** (8% DD → 0.5% risk) live since Apr 11.

If something in this list surprises you, verify via handoff/git BEFORE acting on the surprise.

---

## TIER A — VALIDATED + DEPLOY-READY (Sunday ship targets)

These are the things that CAN go live before Tuesday IF verification confirms they're still open. Dispatch as parallel agents once verified.

| # | Item | Why it's pre-challenge | Validation evidence | Agent brief scope |
|---|------|------------------------|---------------------|-------------------|
| A1 | `execution.py:233` pending_intent destruction race | Silent intent loss on MT5 fail; higher risk outside KZ | Handoff 17 diagnosis; `pending_intent = None` before order confirm | Move clearing to AFTER confirmed fill; add test for failed-order path |
| A2 | `_active_trade_record` never set on limit fill path | Exit data lost for EVERY limit-filled trade → post-trade analysis corrupted | Handoff 17 diagnosis; `_finalize_exit()` never reaches limit fills | Wire `_active_trade_record` on limit fill path; test that exit data lands in KB |
| A3 | Cron-wire OB continuation monitor (6h cadence) | Primary decay metric currently not being run | Shipped session 24 (`11dee1d`), 69 tests pass, CLI proven | Add Windows Task Scheduler entry; verify first run writes to `shadow_logs/ob_continuation_daily.csv` |
| A4 | Canary fixture refresh with borderline CANDIDATEs | T7's higher CR made all 10 NO_TRADE fixtures useless for drift detection | Handoff 15, confirmed again handoff 20 | Generate 3-5 borderline CANDIDATE fixtures from recent MSOs; keep 5-7 NO_TRADE for balance |
| A5 | Between-KZ pending limit fix deployed? | Confirmed +1.5R US30 miss (handoff 17) | Handoff 19 says committed `2a0506f` Apr 14; verify live processes restarted post-commit | If not deployed: restart 5 processes; if deployed: no action |

Each is an independent single-file (or near-enough) change. Parallel dispatch is fine. Use the session-20 pattern (Opus 4.7 agents + one cold reviewer).

---

## TIER B — CHEAP RESEARCH READY TO RUN (Saturday–Sunday test targets)

These are untested research plan items (wave 1–2) that are low-cost and fast enough to get a ship/kill decision before Tuesday. **Every one produces a shadow-only or observation-only artifact**; none requires a live trading-logic change without CEO approval.

| # | Question ID | What to run | Cost | Runtime | Expected payoff |
|---|---|---|---|---|---|
| B1 | Q-3.6 | AI ensemble 3× + vote on 50-MSO subset | $50-80 | 2-4h | +2-4pp WR if positive; config-only deployment |
| B2 | Variant C | `scripts/variant_c_replay.py` on 367-trade batch (handoff 20 P1, script queued) | $0 | 1-2h | Promote/kill decision for adaptive partial close |
| B3 | GBPJPY T7 batch sim | `scripts/simulate_t7_live_period.py` GBPJPY-only | ~$25 | 3-6h | Validates T7 on weakest instrument; protects vs broken deployment |
| B4 | Q-6.2 | Partial close optimization (50/25/25 vs alternatives) on batch | $0 | 1-2h | Optimal split ratios for future Variant D |
| B5 | Q-6.5 | Speed to MFE vs TP probability on batch | $0 | 30-60min | If positive, new mid-trade management signal (shadow log first) |
| B6 | Q-5.2 | MAE distribution per symbol on batch | $0 | 30-60min | Refined SL calibration numbers; inform future SL work |
| B7 | Q-2.4 | FVG gap fill rates on batch (cross-instrument) | $0 | 30-60min | Confirms/refines FVG-in-impulse signal; possible quality filter |
| B8 | Q-2.7 | Premium/discount zone evidence on batch | $0 | 30-60min | Zone-precision add-on to existing OB signal |

**All B-series agents run AGAINST batch data in `data/historical_2026/` or `data/historical/`. No live trading impact. Results go to `research/<topic>/` as markdown + CSV.**

Deploy-gate for each: pre-register hypothesis (effect size, sample threshold, Bonferroni threshold) BEFORE reading the data. If result passes AND is a shadow-loggable signal, ship a logger; if it's a gating signal, CEO-approve first.

Realistic: of the 8 B-items, expect 2-3 to produce actionable findings (11% × 8 = <1, but these are cherry-picked for deployability, so 25-40% is more realistic).

---

## TIER C — CEO DECISIONS ACTUALLY PENDING

Surface these to CEO once Tier A verification is complete. Don't propose solutions in your first message — just surface the decision with its evidence and options.

1. **`sl_too_tight` OB exception enable** (handoff 16) — blocking 4-5 trades/week. With touch-count gate now live (handoff 19), estimated impact may be lower. Options: (a) enable as-is, (b) enable with stricter predicate, (c) leave disabled, (d) re-measure post-challenge.
2. **GBPUSD/XAUUSD macro override for T7** (handoff 16) — T7 C-gate non-compliance. Options: (a) accept non-compliance for these symbols only, (b) enforce C-gate uniformly, (c) carve out exception with explicit rule.
3. **Liquidity gate enable** — requires ≥100 `would_reject` shadow rows. If verification step 7 shows <100, this is post-challenge.
4. **Variant C promotion** — requires B2 replay result or n≥30 live triggers. Likely post-challenge unless B2 result is decisive.
5. **Cron cadence for OB continuation monitor** — 6h default; confirm.

---

## THE RESEARCH EXECUTION PLAN — WHAT'S LEFT

Read `.context/03_analysis/research_execution_plan_113q.md` in full. Summary of what remains (as of 2026-04-11 when the plan was authored, minus what's been answered since):

- **Wave 1 (19 Q):** multipliers — entry engineering (4), feature engineering (7), AI evaluation (7), model risk (1). **Highest leverage per question.** L1+L2 literature sessions are the bottleneck. Q-3.6 ensemble (B1 above) is the most deployable Wave 1 item this weekend.
- **Wave 2 (26 Q):** existing edge optimization — pre-screen loosening (4), structure detection (8), SL refinement (4), exit optimization (5), decay/model risk (5). **Many are pure data replays** (B4-B8 above are all Wave 2). Weekend-parallelizable.
- **Wave 3 (42 Q):** edge discovery — zone types (8), non-zone mechanisms (11), math/stat anomalies (7), adversarial (6). **Highest variance, lowest hit rate, longest runway.** Post-challenge work.
- **Wave 4 (14 Q):** risk/portfolio — sizing (5), cross-instrument (4), macro (4), decay (1). Most macro already killed (null results documented in KB). Sizing and portfolio correlation are post-challenge.
- **Wave 5 (12 Q):** strategic/informational. Post-challenge.

**Already answered (19 questions, 11% actionable hit rate):** Q-6.1 trailing stop (NO CHANGE), Q-5.1 GARCH-EVT (NULL), Q-7.1 Kelly (deployed), Q-2.2 OB touch-1 (codified as touch-count gate), Q-8.1 Shiryaev-Roberts (deployed as EdgeMonitor), plus others in handoff 09.

**Expected forward yield:** the plan projects ~12 more actionable findings out of the 113 remaining (11% hit rate). Of those, weekend-reachable = 2-3 at best (the B-series above). **The research plan cannot be "finished" before Tuesday and nobody expects it to be** — the ask is to capture the actionable subset that's cheap and ready NOW.

---

## PARALLEL AGENT DISPATCH PATTERN (use this)

From session 20's validated pattern:

- **Main thread** = strategy + review. Do NOT implement code yourself.
- **N Opus 4.7 implementation agents in parallel**, each with one discrete task + self-contained brief (file paths, line numbers, change intent, what NOT to touch, expected tests). Background mode OK.
- **1 read-only audit agent** (Explore) for anything sensitive (e.g., confirming between-KZ fix is actually deployed).
- **1 reviewer agent** (Opus 4.7, general-purpose) AFTER all implementation agents report. Verify diffs match claims, run full suite, escalate bugs back.
- **Main thread independent verification** — read key files, run tests locally, spot-check, don't blindly trust sub-agents.

Recommended dispatch sequence:

**Wave 0 (do immediately, ~15 min):** Verification agent(s) against state-verification checklist above. Don't dispatch anything else until Wave 0 returns — save yourself from doing work that's already done.

**Wave 1 (parallel, ~30-60 min):** All verified-open Tier A items (A1-A5) as parallel agents.

**Wave 2 (parallel, 1-4h):** Tier B items B2/B4-B8 ($0 batch replays) in parallel. B1 (ensemble) and B3 (GBPJPY sim) run alone due to API cost and runtime.

**Wave 3 (after Wave 1+2 return):** Reviewer agent on all code changes from Wave 1. Synthesis of Wave 2 results → ship/kill decisions → CEO surface.

**Wave 4 (Sunday evening):** Commit Tier A changes + any validated Tier B additions as shadow loggers. Restart live processes. Prepare Monday demo verification plan.

---

## SUCCESS CRITERIA FOR THIS SESSION

Minimum (acceptable):
- Verification checklist done; stale claims rooted out
- Genuinely-open Tier A items shipped + committed + live processes restarted
- OB continuation monitor cron-wired
- Canary fixtures refreshed
- Sunday handoff written with Monday demo verification plan

Stretch (strong):
- All of the above
- B1 (AI ensemble) result produced → ship/kill decision
- B2 (Variant C replay) result → promote/kill decision
- B3 (GBPJPY T7 sim) result → T7 sanity check
- 2-4 of B4-B8 results landed as research artifacts (not deployed, but documented for post-challenge action)
- Pending-decision list (Tier C) surfaced to CEO with evidence

Out-of-scope (DO NOT attempt pre-challenge):
- Any src/components/ change beyond Tier A bug fixes
- Any prompts/ change
- New framework activation (breaker, FVG grade, H4)
- EURUSD enablement
- Re-running Tier 2 study
- Any Wave 3 edge-discovery work
- Configuration changes that affect sizing or risk outside what's settled

---

## WHAT CAN GO WRONG (pre-mortem)

1. **Verification finds Tier A items are already done.** Good — trust the evidence, skip, move to Tier B. Don't re-ship.
2. **Agent fabricates a test pass.** Always run the suite yourself after each agent reports. Read their diffs.
3. **B-series agent produces positive result on an in-sample test.** Demand out-of-sample replication before any deployment claim. Handoff 03 and the agent-reliability section of CLAUDE.md are non-negotiable.
4. **Shipping too much 48h before challenge → weekend regression no one has time to root-cause.** Prioritize: A > B > C. If Wave 1 reveals a subtle issue, stop and stabilize — don't pile on B-series while A is unresolved.
5. **Main thread exhaustion (session 25 failure mode).** If you notice you're recycling settled decisions or making claims without source, STOP and write the next handoff. Don't push through.

---

## FINAL NOTE

The outgoing session did the full strategic read (CLAUDE.md, reading-order, master roadmap, SWOT, WF-2 candidates, operator playbook, KB files, ADRs 001-003, handoffs 09/12/13/17/18/19/20/24/25, memory files, Tier 1+2 study outputs) but then started drifting on specifics (1% risk, redacted_account decision, etc.) because context was long and fatigue set in.

**You have the advantage of short context + this handoff.** Use it. Verify before acting. Dispatch in parallel. Commit small. Don't over-reach.

CEO's goal, verbatim: *"to have as much validated changes as possible for the funded account challenge."*

Good luck.

---

*Written by outgoing session 25 main thread after CEO flagged drift. Session 26 starts here.*
