# GTOS Master Backlog — Session 27 Synthesis (updated through session 28)

**Date:** 2026-04-18 (original) · session-28 closures applied 2026-04-19
**Author:** Claude Code (session 27 main thread, strategic/supervisor role)
**Purpose:** Comprehensive ordered backlog for implementing agents. CEO broke WF-1 lock 2026-04-18.
**Session-28 changes (2026-04-19):** T0.2, T0.3, T0.4, T0.5, T0.6, T1.1, T1.2, T1.3 all CLOSED (see inline tags). One follow-up nit added as T1.3.1 (canary PASS_THRESHOLD after fixture expansion).
**Session-29 changes (2026-04-19):** T1.3.1 CLOSED via Option C (tiered thresholds) — commits `2d500f1` + `ac9bad7`. See inline tag for rationale + tests.

**Session-30 changes (2026-04-19):** CLAUDE.md pruned 40.5k → 21.2k (commit `5b61bdc`). T1.4, T1.5, T1.7 CLOSED via parallel worktree dispatch + cherry-pick (commits `2654b65`, `525157e`, `baf09ea`). New section T1.x added for 23 pre-existing test failures + 1 error (categorized A-F for fresh-session parallel dispatch).
**Session-32 changes (2026-04-19):** T1.6 correlation-shock Telegram alert CLOSED (commit `b796785`). GBPUSD XAUUSD macro override verified CLOSED-MECHANICAL (commit `84069d3`, no API spend). MT5 timezone bug confirmed already-fixed (`b0c2ece` 2026-04-17, doc-hygiene only). T3.1 step 4 batch sims DECLINED 2026-04-19 (rationale: those 4 instruments are already live, accumulating forward data — redundant). **T1 tier now fully closed.** Session 33 plan: parallel dispatch of T2.1 + T2.6+T2.7 + T5.4 (3 sub-agents) AND EURUSD + NAS100 T7 sims uncapped (background bash, sequential to avoid 429s). See `.context/02_session_handoffs/32_apr19_session_close_handoff.md`.

**Session-33 changes (2026-04-19):** T2.1, T2.6, T2.7, T5.4 CLOSED in parallel dispatch (commits `12018fb`, `ed7117b`, `8eca5bb`, `d6775be`). **T3.1 NAS100 step 2 CLOSED** (`29700da`, 5-slice parallel sim: 37 CAND, 22W/11L/4U, 66.7% WR, +22.03R, +0.668R Exp; cost $22.97). Full 6-file analysis pipeline (4 parallel Opus-4.7 agents + cold review + chairman synthesis) in `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/`. EURUSD step 1 SIM COMPLETE, analysis DEFERRED session 34. **New items added:** T2.8 concurrent-cap + daily-loss-stop risk architecture (CEO-locked 10 decisions); T2.9 `verification.py` sl_beyond_ob strict-`<` → `<=` (pre-req T4.26); T4.26 sl_beyond_ob cross-instrument audit; T5.24 D1-bias-lag shadow logger + alert. Model migration (`b298e2a`): all live AI paths (M5 refinement, devils_advocate) now config-pinned to sonnet-4-6 + effort=max — rolling restart required to take effect. **Session 34 plan:** implement T2.8 + T4.26 audit + T5.24 logger + EURUSD analysis in parallel worktrees, plus operational rolling restart for model migration. See `.context/02_session_handoffs/34_apr19_FRESH_SESSION_POST_NAS100_PROMPT.md`.
**Complementary to:** `research/quantlabs_competitor_intel/synthesis/02_extraction_for_backlog_merge.md` (the other agent's work)
**Scope:** Everything unfinished, cross-referenced against session handoffs, research verdicts, WF-2 canon, ADR parked alternatives, SWOT, L4 academic pipeline, KAP claims, podcast hypotheses, config flags, playbook gaps.

---

## Orientation for the implementing agent

- **Challenge starts Tuesday 2026-04-21.** redacted_account Stellar 2-Step $100K @ 1% risk.
- **WF-1 lock was broken 2026-04-18 by CEO.** Validated changes can ship. CEO approval + verification rigor STILL required per agent reliability rules (see `CLAUDE.md`).
- **Every deliverable is a committed file** — not a chat message.
- **Before implementing ANY item here (MANDATORY verification gate):**
  1. `python scripts/generate_live_state.py` — regenerates `.context/LIVE_STATE.md` with current git state, config, enforcement check, gates. **This is the source of truth; trust it over this backlog.**
  2. Cross-check the target item against LIVE_STATE.md's "Git status" + "Last 20 commits" + "Config-flag enforcement check."
  3. If LIVE_STATE.md shows the item already shipped / closed / present, update this backlog inline (`→ CLOSED as of YYYY-MM-DD verification`) and skip to the next item.
  4. Only THEN proceed to implement.

- **Why this matters:** This backlog is a snapshot of doc-derived state on 2026-04-18. Handoffs are append-only historical records — handoff 17's "unresolved" list does NOT self-update when a later commit fixes the item. CLAUDE.md is session-refreshed, not commit-refreshed. When doc says "X is open" and git shows "X shipped in commit Y," **trust git, update the docs**. Items verified closed during session 27 have been tagged `→ CLOSED as of 2026-04-18 verification` inline.
- **ID prefixes:** `T` = tier items in this master backlog. Cross-refs to `Q###` (quantlabs), `O-#/D-#/DW-#/U-#` (handoff sweep), `R###` (research sweep).
- **Dedup:** every item here has been verified to NOT appear in the CLOSED-SHIPPED/CLOSED-NULL/CLOSED-KILL lists from the handoff sweep.

## Tier definitions

- **T0 — CRITICAL.** Correctness fixes, stale-tree cleanup, verified-silent safety gaps. Ship first.
- **T1 — HIGH-IMPACT INFRA.** Operational safety additions. Additive, pre-challenge safe.
- **T2 — VALIDATED DEPLOYMENTS.** Backtest evidence; ready for ship after T0 correctness.
- **T3 — EXPANSION.** New instruments, new frameworks, scope growth.
- **T4 — EDGE DISCOVERY.** Experiments to run before deploying (mostly historical replay, no live risk).
- **T5 — INFRASTRUCTURE MATURITY.** New shadow loggers, additional monitors.
- **T6 — RESEARCH-HEAVY.** Substantial new analysis required; long tail.
- **T7 — KILL / CLOSED.** Explicitly not-to-do; reference for dedup.

---

# T0 — CRITICAL (ship first, before challenge resumes)

### T0.1 — ~~Revert Impl-A uncommitted `permissions.py` diff~~ → **CLOSED as of 2026-04-18 verification**
- **Status:** DONE. `git status` clean on `permissions.py` + `test_permissions.py` (CEO already reverted).
- **Residual action (doc hygiene only, ~5 min):** Update `.context/06_decisions/004_sl_gate_reconciliation_2026-04-18.md` header `Status: OPEN` → `Status: CLOSED-OPTION-C-DE-FACTO`. Current live config (`agent_config.yaml:46-56`) already implements Option C semantics: `ob_retest_sl_exception: true` + `ob_retest_sl_min_buffer_atr: 0.5`. ADR remains as historical record.
- **Impact:** Cosmetic
- **Verification anchor:** `git status src/components/permissions.py tests/test_permissions.py` → empty

### T0.2 — ~~Enforce `deployment.phase` flag in code~~ → **CLOSED 2026-04-19 (session 28, commit `4944794`)**
- **Source:** Quantlabs Q014 (verified novel finding via grep + `research/sweep_apr11_2026.md:207-209`)
- **Closure:** Gate 0 `_reject_if_deployment_phase_blocked` in `permissions.py:52`, wired as FIRST gate in `check_permissions`. Config `phase: 2 → 3` (live_micro). 6 tests + 1 ordering test. Autouse conftest shim. Commit `4944794 feat(permissions): enforce deployment.phase gate (Gate 0, T0.2/Q014)`.
- **Residual note:** `phase=2` (log-only) currently behaves identically to `phase=1` (block) because orchestrator has no divert path. Documented in Gate 0 docstring as T1 follow-up. Production runs at `phase=3` — correct behavior preserved.

### T0.3 — ~~Clean 7 stale `CLAUDE.md` lines~~ → **CLOSED 2026-04-19 (session 28, commit `3005a83`)**
- **Closure:** `3005a83 docs(t0.3): stale-line sweep + ADR 004 CLOSED-OPTION-C closure`. CLAUDE.md "What is unresolved" pruned; ADR 004 header flipped to `CLOSED-OPTION-C-DE-FACTO`. Residual session-28 closures (T0.2/T0.6/T1.1/T1.3) applied in this commit.

### T0.4 — ~~Verify R078 structural bug actually fixed~~ → **CLOSED 2026-04-19 (session 28, verification only — no code change needed)**
- **Closure evidence:** `src/components/execution.py:584-593` — `self.pending_intent = None` fires ONLY after successful `open_trade()`. No destruction-before-order. R078 no longer a live bug.
- **R079 status:** confirmed closed by `fb86280 fix(orchestrator): capture exit data on limit-filled trades (P1-3)`.

### T0.5 — ~~Commit session 26 + session 27 loose ends~~ → **CLOSED 2026-04-18 (session 27 topic-commits)**
- **Closure:** `e089563 docs(handoff-26)` + `1288799 research(b-series)` + `ed1ab18 research(sl-gate)` + `7589f7f research(quantlabs)` + `62101ac research(backlog)` + `949a415 ops(live_state snapshot)`. All 2026-04-18 untracked tree flushed.

### T0.6 — ~~Watchdog integration end-to-end verification~~ → **CLOSED 2026-04-19 (session 28, commit `fa94b96`)**
- **Closure:** `fa94b96 tools(watchdog): end-to-end integration verifier (T0.6)`. `scripts/watchdog_e2e_verify.py` — 1031 lines, read-only offline-capable audit tool. 4 integration checks (OB continuation, API refusal, canary cache, redacted_account profile) with ABSENT/STALE/MALFORMED distinction. Weekend leniency Fri 17:15 UTC → Sun 21:00 UTC (aligned to `watchdog.ps1:7-12`). Dead-zone leniency 01:15-07:45 local. Exit codes 0=PASS/WARN, 1=FAIL, 2=script-error. 46 tests pass + 1 Windows-skip.

---

# T1 — HIGH-IMPACT INFRA (pre-challenge safe, additive)

### T1.1 — ~~Heartbeat-flatten kill switch~~ → **CLOSED 2026-04-19 (session 28, commit `05fd5ef`, SHIPS DISABLED)**
- **Closure:** `05fd5ef feat(safety): heartbeat-flatten kill switch (T1.1, ships DISABLED)`. `src/safety/heartbeat_monitor.py` (875 LOC) + `src/safety/__init__.py`. Orchestrator writes `pipeline_state/heartbeat.json` every 30s (main-loop + interruptible-sleep hooks). Monitor: 3 consecutive misses (~90s stale) = trigger candidate; 3 consecutive triggers (~180s total) = flatten sequence. Market-hours gate (any instrument's active KZ), Telegram pre-flatten alert + 30s CANCEL listener, MT5 `close_position` with magic `heartbeat_flatten` + 3× retry, events → `shadow_logs/heartbeat_flatten_events.jsonl`, 60-min throttle. Config `heartbeat.*` defaults all OFF (`flatten_enabled: false` → log-only). Watchdog launches monitor as independent child process. 60 new tests (total 1531→1591 pass).
- **Cold-review verdict:** GO-WITH-NITS. No blockers.
- **Nit (deferred):** weekend-KZ belt-and-suspenders — monitor's KZ check is UTC-day/time only; doesn't re-check weekend-suppress window. Redundant with watchdog's weekend stop, but a defense-in-depth follow-up would add it.
- **Live enablement:** awaits CEO approval + live observation window.

### T1.2 — ~~Prepaid card cap on Anthropic API account~~ → **CLOSED-OPERATIONAL 2026-04-19 (CEO disabled auto-reload; balance IS the cap)**
- **Closure:** CEO disabled Anthropic billing auto-reload 2026-04-19. The $50-60 prepaid balance IS the hard cap — stronger than any software enforcement (system fails closed when balance exhausts). No prepaid-card code needed. Memory: `project_anthropic_billing_auto_reload_disabled.md`.

### T1.3 — ~~Borderline canary fixtures~~ → **CLOSED 2026-04-19 (session 28, commit `bb4ed5a`)**
- **Closure:** `bb4ed5a feat(canary): add 4 borderline fixtures for drift detection (T1.3)`. 4 borderline XAUUSD fixtures added (2 candidate / 2 no_trade) sourced from `research/t7_live_simulation/all_results_jan_apr10.json`. Files: `borderline_xauusd_20260406T1000_candidate.json`, `borderline_xauusd_20260115T1315_candidate.json`, `borderline_xauusd_20260227T0945_no_trade.json`, `borderline_xauusd_20260122T0900_no_trade.json`. Manifest: 12 → 16 fixtures. `scripts/canary_fixtures/README_borderline.md` documents rationale per fixture. Baseline re-established; canary stable. API spend $2.74 of $15 cap.
- **Cold-review verdict:** GO-WITH-NITS. No blockers.
- **Multi-symbol deferral (defensible):** Spec preferred multi-symbol coverage, but `shadow_logs/candidate_features_log.jsonl` has only 6 non-XAUUSD CANDIDATEs and those rows contain only feature aggregates (no `system_prompt`/`user_message` for reconstruction). `pipeline_state/` has no per-symbol archives. T7 simulation is XAUUSD-only. Multi-symbol fixtures would require synthesis (spec's "last resort"). Deferred until non-XAUUSD MSO archives accumulate from live.
- **⚠ Nit flagged for follow-up (T1.3.1):** `scripts/canary_test.py:59` `PASS_THRESHOLD = 10`. With 16 fixtures (was 12), alarm floor drops from 83% (10/12) to 62.5% (10/16) — real sensitivity regression. Spec explicitly forbade runner modification (additive-only constraint). Standalone follow-up commit needed; see T1.3.1 below.

### T1.3.1 — ~~Tighten canary `PASS_THRESHOLD` after T1.3 fixture expansion~~ → **CLOSED 2026-04-19 (session 29, commits `2d500f1` + `ac9bad7`)**
- **Closure rationale:** Rejected A (hardcode 13) and B (derive from manifest) in favor of **Option C — tiered thresholds by fixture category**. A reintroduces the hardcoded-constant failure mode; B couldn't distinguish deep-zone flips (serious) from borderline wobble (expected).
- **Option C implementation:** `scripts/canary_test.py` now classifies fixtures by filename prefix (`borderline_*` = borderline tier, else baseline tier). Thresholds derived from categorized counts: `baseline_threshold = max(0, N - 1)` (at most 1 deep-zone flip); `borderline_threshold = ceil(0.75 * N)` (75% match floor). Current 12 + 4 split yields (11, 3) — 92% / 75% floors. Overall PASS requires both tiers AND the pre-existing keyword-drift budget (≤ 2).
- **Commits:**
  - `2d500f1 fix(canary): tiered PASS_THRESHOLDs restore drift sensitivity (T1.3.1)` — core refactor + 31 tests in `tests/test_canary_tiered_thresholds.py` + `BORDERLINE_PREFIX` constant declared. Cold-review verdict: GO-WITH-NITS.
  - `ac9bad7 fix(canary): rename BORDERLINE_PREFIX, drop stale pass_threshold, add CLI smoke test` — 3 cold-review follow-ups: (1) constant rename from the misleading `BASELINE_PREFIX` to `BORDERLINE_PREFIX`, (2) removed dead `"pass_threshold": 10` field from `manifest.json` + `generate_canary_fixtures.py` (runner has never consulted it post-T1.3.1; enforced by regression test), (3) 3 CLI smoke tests locking the `Baseline tier: N/M match (threshold: >= T) -> PASS|FAIL` stdout format under all-match / 1-baseline-flip-tolerated / borderline-flip-fails scenarios.
- **Tests:** 34 in `tests/test_canary_tiered_thresholds.py` (31 core + 3 CLI smoke) + 11 in `tests/test_canary.py` = 45 canary-related tests, all passing.
- **No live-behavior change:** canary is a shadow monitor (kill-zone entry check); tighter alarm only affects when "CANARY FAIL" prints + exit code. Orchestrator's `_run_canary_check()` integration unchanged.

### T1.4 — ~~Model-id pinning + drift alert~~ → **CLOSED 2026-04-19 (session 30, commit `2654b65`)**
- **Closure:** `2654b65 feat(monitor): model-id pinning + drift alert (T1.4)`. New `src/components/model_pin.py` (+198 LOC) + `primary_analyzer._call_claude` wrap (+11 LOC). Pin persisted at `knowledge_base/meta/model_pin.json`. Alert path wires into pre-existing `src.notifications.notify_alert` (Telegram, `src/notifications.py:244`). Pin-before-notify order prevents re-alert loops if Telegram fails.
- **Tests:** 22 in `tests/test_model_pin.py` (480 LOC), all green.
- **Spec deviation accepted:** captured `response.model` + `response.id` only, not raw HTTP response headers (Anthropic SDK requires `with_raw_response` for header access; resolved model id from `response.model` carries the same canonical information). CEO approved.

### T1.5 — ~~CUSUM on CANDIDATE rate (CR)~~ → **CLOSED 2026-04-19 (session 30, commit `525157e`)**
- **Closure:** `525157e feat(monitor): CUSUM on CANDIDATE rate (T1.5)`. New `scripts/cusum_candidate_rate_monitor.py` (+715 LOC) + watchdog.ps1 hook (+49 LOC, once-per-UTC-day marker `cusum_candidate_rate_last_run.utcdate`). Bernoulli two-sided CUSUM: `p0 = 0.103, h = 4.0, p1_up = 0.206, p1_down = 0.0515` (clamped). Data source `shadow_logs/candidate_features_log.jsonl`. State file `knowledge_base/meta/cusum_candidate_rate_state.json`. `MIN_OBSERVATIONS = 30` suppresses thin-window alarms.
- **Tests:** 41 in `tests/test_cusum_candidate_rate_monitor.py` (545 LOC).
- **Smoke on real 111-row log:** CR = 7.21%, s_up = 0.57, s_down = 0.84, no alarms. Expected.
- **Spec deviation accepted:** OVERALL scope only (per-symbol deferred). Per-symbol requires ≥30 CANDIDATEs per instrument; only XAUUSD is close. Matches T1.3 multi-symbol deferral pattern. CEO approved.

### T1.6 — ~~Correlation-shock Telegram alert~~ → **CLOSED 2026-04-19 (session 32, commit `b796785`)**
- **Closure:** `b796785 feat(monitor): correlation-shock Telegram alert (T1.6)`. New `scripts/correlation_shock_monitor.py` (+491 LOC) + `scripts/watchdog.ps1` once-per-UTC-day hook (+51 LOC, 60s timeout, marker `correlation_shock_last_run.utcdate`). 49 tests in `tests/test_correlation_shock_monitor.py` (+515 LOC). Iterates every `portfolio_risk.DEFAULT_CORRELATION_GROUPS` group; rolling-50 Pearson on M15 log-returns; alarm when `|z| > 2.0` vs 200-sample baseline (`MIN_BASELINE_SAMPLES=30`). 24h per-pair cooldown via `knowledge_base/meta/correlation_shock_state.json` (gitignored). Telegram via `src.notifications.notify_alert` (lazy import).
- **Spec deviation accepted:** Spec named `JPY_CROSSES / USD_BLOC` but `portfolio_risk.py` has no `USD_BLOC` group — agent iterates ALL groups instead of hard-coding two (satisfies "reuse existing correlation groups" rule, degrades gracefully on broker-unavailable symbols).
- **Smoke verified:** Live MT5 run hit 7 pairs; one real alert fired on AUDUSD/NZDUSD (z=-4.21, 24h cooldown now active). Sibling test suites (portfolio_risk, no_data_alert, model_pin, cusum_candidate_rate, api_refusal, watchdog_e2e_verify, heartbeat_monitor): 272 passed / 1 skipped / 0 failures.
- **Original spec (kept for reference):**
  - **Source:** Quantlabs Q004a (cold review split from full DCC-GARCH; alert-only half)
  - **Mechanism:** Rolling Pearson >2σ move vs 50-candle baseline across JPY_CROSSES / USD_BLOC. Telegram-only alert, NO position impact.
  - **Impact:** MEDIUM — operator visibility on correlation regime changes
  - **Cost:** LOW — reuses existing `portfolio_risk.py` correlation groups
  - **Risk:** LOW — alert only

### T1.7 — ~~Daily no-data alert per symbol (tick liveness)~~ → **CLOSED 2026-04-19 (session 30, commit `baf09ea`)**
- **Closure:** `baf09ea feat(monitor): per-symbol no-data alert (T1.7)`. New `scripts/no_data_alert_monitor.py` (+463 LOC) + watchdog.ps1 hook (+32 LOC, 30s timeout). Liveness signal: per-symbol log-file mtime. KZ-gated, 60-min per-symbol alert cooldown, clears prior alerts so each KZ starts fresh. Imports `KILL_ZONES_UTC` from `src/safety/heartbeat_monitor.py:104` (single source of truth). `KZ_SYMBOL_ALIAS` map bridges broker log names (e.g., `US30_cash`) to KZ keys (`US30`). State file `knowledge_base/meta/no_data_alert_state.json`. Exit codes 0/1/2 = OK/missing-creds/telegram-fail.
- **Tests:** 56 in `tests/test_no_data_alert_monitor.py` (685 LOC).
- **Spec deviation accepted:** threshold raised from 5 min → 20 min (1.33× M15 cadence). 5 min would fire on every normal inter-bar gap — false-positive storm. 20 min still catches real outages well before a KZ ends. CEO approved.

### ~~T1.x — Pre-existing test failures (23 + 1 error)~~ → **CLOSED 2026-04-19 (session 31, groups A–F commits `d0172a6`, `be6392c`, `1fa00f9`, `9170e73`, `e24a442`, `83f665c`)**
Full-suite now `1635 passed, 2 skipped, 0 failures, 22 warnings`. All six groups dispatched per the plan: A (debate asyncio canon), B (dead reseed bootstrap deleted), C (TestNewDay state reset restore), D (primary_analyzer session-21 canon), E (WF-1 security framework dead code deleted), F (watchdog_e2e_verify collection error). See `.context/02_session_handoffs/31_apr19_session_close_handoff.md` section A for per-group detail.

| Group | Count | File | Shape |
|-------|-------|------|-------|
| A | 8 | `tests/test_debate.py` | Component 3B paused — skip-or-delete decision. 5 min if skip. |
| B | 5 | `tests/test_deployment_prep.py` (`TestReseedFromSessions`, migration) | Likely dead fixtures; investigate + delete-if-obsolete. |
| C | 1 | `tests/test_orchestrator.py::TestNewDay::test_resets_state` | `orchestrator.py:2043` references `self.execution` (no longer an attr). ~15 min fix. |
| D | 7 | `tests/test_primary_analyzer.py` | Suite-ordering pollution. Apply session-21 canon (`tmp_path` + module-ref monkeypatch). |
| E | 2 | `tests/test_security_framework.py` (`TestWF1Protection`) | WF-1 lock cancelled — needs CEO steer on "delete relic" vs "rewrite for current gate". |
| F | 1 ERROR | `tests/test_watchdog_e2e_verify.py::test_run_all_checks_never_raises` | Collection/setup error, ~10 min isolation fix. |

**Dispatch plan:** C + F + D first in parallel (pure fixes, no scope questions). Then A + B after CEO confirms skip-vs-delete. E last (needs spec decision).
- **Impact:** MEDIUM — cleans full-suite so next feature work surfaces true regressions.
- **Cost:** LOW — most are <30 min; E pending CEO input.
- **Risk:** LOW — tests-only, zero production surface.

### ~~T1.8 — Weekly AI-reasoned summary of skipped trades~~ (DROPPED 2026-04-19)
- **Source:** Quantlabs Q016 (Bryan's template verified in batch_01/_02)
- **Decision (CEO, 2026-04-19):** Out of scope. CEO reviews `malformed_responses.jsonl` + `api_refusal_monitor.py` output manually inside Claude Code sessions on demand — no need for an automated weekly API-driven summary. Saves ~$2/mo + ~100 LOC of pipeline we don't want to maintain.
- **If revisited:** feed malformed + refusal logs to Claude for weekly "why no-order" post-mortem + Telegram send.

---

# T2 — VALIDATED DEPLOYMENTS (backtest evidence, CEO-approvable)

### T2.1 — ~~Trailing stop: full-population rerun, then decide~~ → **CLOSED 2026-04-19 (session 33, commit `12018fb`)**
- **Closure:** Re-dispatched full-population trailing stop rerun on current 367-trade KB. Research-only commit. See commit message for verdict. Ship decision deferred pending live BE-outcome accumulation.
- **Source:** WF-2 C01, handoffs 06/07/09, Q-6.1 (theoretical), Research R001
- **History:**
  - Apr 6 (`45da076`): Initial n=100 test. Trail 0.5R after 0.5R MFE → +52.4R (12 trades hurt). Trail 0.5R after 1.5R MFE → +38.9R (2 hurt). Handoff 06 called it "biggest discovery."
  - Apr 7 (`decfecb`): Partial rerun n=100 across 2024-2026, Trail 0.5R/1.5R MFE config: ~+0.40R/trade avg. More modest.
  - Apr 7-8 (handoff 07): Full-population n=367 rerun was DISPATCHED but **output lost in worktree merge issues**. Flagged as Priority 3.
  - Apr 11 (`2758e74`, Q-6.1): OU Lipton-LdP + fat-tail MC. Verdict: "Symmetric OU can't rank GTOS exits. NO CHANGE to SL/TP — SL governed by zone invalidation, not OU Sharpe." This is a theoretical null (OU framework can't decide), NOT an empirical rejection.
  - Live now (`d806dc6`): "Move SL to BE at KZ end when trade in profit." Not a true trailing stop.
- **Action:**
  1. Re-dispatch full-population trailing stop rerun on current 367-trade KB
  2. Compare: baseline vs Trail 0.5R/0.5R vs Trail 0.5R/1.5R vs conservative variants
  3. Report on WR, expectancy, drawdown, hurt-trade count
  4. If positive → CEO decision on live deployment
- **Impact:** Historical showed +20-50R. Updated rerun TBD.
- **Cost:** $0 (historical replay, no API), 2-4 hours analysis
- **Risk:** LOW for rerun; MEDIUM for deployment (would touch exit logic)

### T2.2 — ADR 004 Option C: additive sl_too_tight structural bypass
- **Source:** ADR 004 parked alternative, Research R032
- **Finding from session 26:** Current `sl_too_tight` gate blocks ~4-5 trades/week. Session 26 analyzed & revered ADR 004 (kept 0.5 ATR floor) because Option C depends on liquidity cluster gate as sweep protection — and liquidity gate has only 4 shadow rows, not calibrated yet.
- **Mechanism:** Bypass `sl_too_tight` when trade has strong structural signals that would have triggered liquidity cluster gate for sweep protection.
- **Impact:** HIGH — unblocks 4-5 trades/week currently rejected
- **Cost:** ~30 LOC + tests
- **Pre-req:** Liquidity cluster gate has ≥100 shadow rows OR CEO accepts early deployment with precision/recall check on current n
- **Risk:** MEDIUM — Apr 16 sweep failure mode could recur if liquidity gate doesn't catch the sweep case. MUST CEO-approve.

### T2.3 — Liquidity cluster gate enable
- **Source:** Handoff 20, Research R034, config `sl_liquidity_cluster_enabled: false`
- **Status:** Shipped DISABLED in `ab077cd`. Currently 4 shadow rows.
- **Action:** Review shadow data when ≥100 rows accumulated. Flip enabled flag after precision/recall check.
- **Impact:** MEDIUM — enables T2.2 (ADR 004 Option C)
- **Pre-req:** ≥100 shadow rows (estimated post-challenge Month 1-2)

### T2.4 — BE shadow logger → promotion decision
- **Source:** WF-2, Handoff 09, DW-2, Research R052, L4 A19
- **Status:** Active shadow logger. Waiting for Wilcoxon on n≥30 BE-triggered trades.
- **Action:** Once n≥30, Wilcoxon signed-rank test. If cumulative Δr > 0 with p < 0.05 → promote to live BE-at-1R. If Δr ≤ 0 → kill.
- **Impact:** HIGH (if promoted)
- **Cost:** LOW (decision gate only; logger already running)
- **Pre-req:** n≥30 BE-triggered trades (currently <30)

### T2.5 — Variant C partial close promotion
- **Source:** Handoff 13, Research R013, DW-1
- **Status:** Historical replay Wilcoxon p=0.363 (DEFER). Live shadow logger accumulating.
- **Action:** Flip to live ONLY after n≥30 live Variant-C triggers and live Δr direction holds
- **Impact:** MEDIUM — variance compression (not edge)
- **Pre-req:** n≥30 live triggers (currently <30)

### T2.6 — ~~Refactor `_recover_pending_record_path` (T0.4 follow-on)~~ → **CLOSED 2026-04-19 (session 33, commit `ed7117b`)**
- **Closure:** `ed7117b fix(execution): race-free pending record recovery via trade_id (T2.6)`. Record path now derived from `trade_id` in intent payload; race-free across midnight UTC.

### T2.7 — ~~Telegram alert on limit-fill trade record load failure~~ → **CLOSED 2026-04-19 (session 33, commit `8eca5bb`)**
- **Closure:** `8eca5bb feat(execution): Telegram alert on pending record recovery failure (T2.7)`. `notify_error()` fires on load failure.

### T2.8 — Concurrent-cap + daily-loss-stop risk architecture (CEO-locked session 33)
- **Source:** CEO ask post NAS100 T3.1 synthesis, 2026-04-19 (session 33).
- **Replaces:** Current `max_kz_trades=1` hardcode in `permissions.py:146-150` AND `max_daily_losses: 2` count cap.
- **Rationale:** NAS100 analysis showed `max_kz_trades=1` capped +16.02R/Q of real edge at 66.7% WR. CEO wants a portfolio-wide risk ceiling that tolerates concurrent trades while preserving worst-case daily-loss math.
- **Architecture (10 locked decisions from session 33):**
  1. Concurrent cap formulaic: `max_concurrent = floor(max_daily_loss_pct / risk_per_trade_pct)`. redacted_account (4%/1%) → 4. FTMO (4%/2%) → 2.
  2. Same-instrument concurrency allowed.
  3. "Concurrent" counts filled positions only (pending limits don't count).
  4. Daily loss measured MTM (realized + unrealized).
  5. On trigger: cancel all pending limits + stop AI analysis for the day + let open positions close naturally.
  6. Stop AI analysis = kill the M15 Anthropic calls (save cost).
  7. Daily reset at 00:00 UTC.
  8. Correlation caps remain, layered on top.
  9. H29 DD reduction stays on top (redacted_account: 1.0% → 0.25% at DD ≥8%).
  10. Daily loss stop at 4% (replaces current 2.0%).
- **Files:**
  - `src/components/permissions.py` — remove kz cap + add concurrent-cap + add dormant-state short-circuit.
  - `config/agent_config.yaml:20` — `max_daily_loss_pct: 2.0` → `4.0`; delete `max_daily_losses: 2`.
  - `config/profiles/redacted_account.yaml` — pin `max_daily_loss_pct: 4.0`, `max_concurrent: 4`.
  - `src/components/orchestrator.py` — MTM daily-PnL check + dormant-state writer on trigger.
  - NEW: cross-instrument open-position counter (MT5 magic-filter).
  - Tests: permissions, concurrent-cap, daily-loss-stop paths.
- **Impact:** HIGH — worst-case daily-loss math closes at 4% across all profiles; lifts `max_kz_trades` choke.
- **Cost:** ~300 LOC + tests. No API spend.
- **Risk:** MEDIUM — trading-logic change. Full pytest suite + demo smoke required before ship.
- **Target ship:** Before redacted_account kickoff 2026-04-21 if feasible; else first-week-live.
- **Approval:** CEO pre-approved design (session 33). Re-approval only if implementation uncovers structural issues.
- **Dispatch:** See `.context/02_session_handoffs/34_apr19_FRESH_SESSION_POST_NAS100_PROMPT.md` Action 1.

### T2.9 — `verification.py` sl_beyond_ob strict-`<` → `<=` (cross-instrument audit first)
- **Source:** NAS100 T3.1 analysis (session 33), agent C + cold review E.
- **Finding:** `verification.py:520-533` uses strict `sl < zone_low` for LONG (`sl > zone_high` for SHORT). 42 NAS100 LONG rejects had SL bit-exact to OB low → lost +13.5R standalone / +20.5R joint with T2.8.
- **Pre-req:** Cross-instrument audit on XAUUSD 367-trade KB (see T4.7 below). If pattern replicates → ship gate fix. If NAS100-only → consider prompt-level `sl_buffer_applied >= Npt` instead.
- **Fix:** `verification.py:522` `<` → `<=`; `verification.py:536` `>` → `>=`. Add tests covering SL=OB-bound exact case.
- **Impact:** HIGH (cross-instrument) or MEDIUM (NAS100-only) — +13.5R/Q minimum per instrument.
- **Cost:** 1-line patch + 2-4 tests.
- **Risk:** LOW (boundary precision).
- **Approval:** **CEO required — gate relaxation.**

---

# T3 — EXPANSION (scope growth)

### T3.1 — EURUSD + NAS100 live onboarding
- **Source:** SWOT O5, Handoff 26 F1, Research R040/R076, Quantlabs partial-overlap, KAP #1
- **Status:** ~~Data exported (`438b47b` / `e45bb68`)~~ → **NAS100 STEP 2 CLOSED 2026-04-19 (session 33, commit `29700da`). EURUSD STEP 1: sim COMPLETE but analysis pending (session 34 Action 4).**
- **Action:**
  1. T7 simulation on EURUSD Jan-Apr 2026 (~$25) — **SIM COMPLETE session 33** (data at `research/t7_live_simulation/EURUSD_t7_simulation.json`, 4.3 MB). Analysis DEFERRED to session 34 (Action 4 in fresh-session prompt 34).
  2. T7 simulation on NAS100 Jan-Apr 2026 — **CLOSED session 33.** 5-slice parallel run, $22.97, 37 CANDIDATEs, **66.7% WR resolved (22W/11L/4U), +22.03R, +0.668R Exp**. Full synthesis at `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/NAS100_T3_1_synthesis.md`. Two material gate leaks found (T2.9 sl_beyond_ob + T2.8 max_kz_trades in the new risk architecture).
  3. ~~If positive → canary test + add to live symbol list with conservative initial sizing~~ → **DEFERRED pending T2.8 ship + EURUSD analysis cross-check.** NAS100 66.7% WR is positive but has regime-dependent decay (W12-W16 = 14% WR during V-reversal). Don't add to live until fix bundle (T2.8 + T2.9) is shipped.
  4. ~~Batch simulations for US30/USDJPY/GBPJPY (~$75 for 3) if not yet run — handoff 15 flagged $120.58 total, handoff 14 only completed XAUUSD~~ → **DECLINED 2026-04-19 (session 32)** — those 4 instruments (US30, USDJPY, GBPJPY, GBPUSD) are already LIVE; historical batch sims would be redundant on instruments that are accumulating forward live data automatically. CEO prefers to spend simulation budget on NEW instruments (EURUSD + NAS100, steps 1-3 above) where there's no live data and edge needs validation before live add.

**Session 32 dispatch plan (CEO-approved 2026-04-19):** EURUSD + NAS100 T7 sims to run **uncapped** (`--budget 100` each, effectively no cap given $25/$30 per-sim estimates). $100 Anthropic balance available; CEO accepts risk + will top up if drained. Sims chained sequentially (EURUSD → NAS100) in background bash to avoid 429 rate-limit collisions. **Window: `--start 2026-01-02 --end 2026-04-17`** (fresh MT5 export ran in session 32, all 7 symbols × 4 TFs now current through 2026-04-17). Verdict goes to `research/t3_1_eurusd_nas100_validation_2026-04-19/`.

**Session 33 dispatch update (2026-04-19):** CEO approved parallel instead of serial. 5 NAS100 disjoint-date workers + 1 EURUSD worker dispatched concurrently via `run_in_background: true` bash; Tier-4 rate limits held with headroom. Wall-clock ~1.5h. All 6 processes crashed at report-write (cp1252 encoding) AFTER JSON data persisted — fix committed as `ee63ecd`. **Full NAS100 analysis + synthesis committed `29700da`** (29 files, 4 MB). EURUSD JSON intact at `research/t7_live_simulation/EURUSD_t7_simulation.json`, pipeline re-run pending in session 34.
- **Impact:** HIGH — 2-3× instrument count, edge validated across 13 instruments mechanically
- **Cost:** ~$150-200 total simulations + engineering
- **Risk:** MEDIUM — each new instrument is production surface expansion
- **Pre-req:** Challenge Week 1-4 stable

### T3.2 — Bull/Bear Debate (Component 3B) wiring + A/B evaluation
- **Source:** CLAUDE.md (paused), SWOT O2, Research R037, config `debate_round2_enabled: true` but unused
- **Status:** Code exists in `src/components/debate.py`, never wired to orchestrator, never evaluated.
- **Action:**
  1. Wire into orchestrator behind feature flag (default off)
  2. A/B test vs 3A-only on historical MSOs (~$10-30 API)
  3. If lift > 3pp WR at Bonferroni significance, promote
- **Impact:** MEDIUM — additional discrimination layer on CANDIDATEs
- **Cost:** MEDIUM — wiring + A/B harness
- **Risk:** LOW-MEDIUM — may hurt frequency if over-restrictive

### T3.3 — Secondary framework: liquidity sweep
- **Source:** KAP Edge #1, Research R047, Osler 2005
- **Mechanism:** New framework `liquidity_sweep` — entry on sweep-then-displace pattern, separate from OB retest. Parallel to current `ob_retest` framework.
- **Impact:** MEDIUM — additional edge source
- **Cost:** HIGH — new framework (analyzer, primary eval prompt adjustment, tests)
- **Risk:** MEDIUM — additional complexity

---

# T4 — EDGE DISCOVERY RESEARCH (experiments to run, low-risk)

### T4.1 — R:R sweet spot sweep
- **Source:** Podcast H6, Research R023
- **Mechanism:** Historical sweep of `min_rr` across {1.5, 1.8, 2.0, 2.2, 2.5, 3.0}. Report expectancy curve.
- **Current:** `min_rr: 1.5`. H6 claims 1.8-2.2 sweet spot.
- **Impact:** MEDIUM
- **Cost:** LOW — $0 historical replay

### T4.2 — ATR multiplier sweep (post-ADR-004 floor)
- **Source:** WF-2 C04, Research R004
- **Mechanism:** SL multiplier sweep {1.0, 1.2, 1.5}×ATR, respecting 0.5 ATR sweep floor
- **Cost:** LOW
- **Pre-req:** ≥30 live post-ADR-004 trades or historical replay sufficient

### T4.3 — Mitigated vs fresh OB continuation differential
- **Source:** 113q Q2.5, KAP #6, Research R016/R046
- **Mechanism:** Compute continuation rate separately for mitigated vs fresh OBs. Mitigation flag already in `market_state.py`.
- **Impact:** MEDIUM — new filter or ranking signal
- **Cost:** LOW — query existing OB continuation monitor CSV

### T4.4 — OB continuation by session × day-of-week matrix
- **Source:** 113q Q2.1, KAP #5, Research R015/R045
- **Mechanism:** 3-session × 5-DoW matrix of continuation rates. Identify low-cells for filter.
- **Impact:** MEDIUM
- **Cost:** LOW — extension of existing monitor

### T4.5 — Strip confidence scorer
- **Source:** WF-2 C03, SWOT O7, Research R003
- **Mechanism:** Remove `confidence` field from T7 prompt output. T5→T8 showed r=-0.06 with wins.
- **Impact:** LOW-MEDIUM — cleanup
- **Cost:** LOW — prompt edit + parse update
- **Risk:** LOW (confirmed useless)

### T4.6 — Test B: prompt-neutral rerun
- **Source:** kb_edge_mechanisms, Research R067
- **Mechanism:** Same MSOs through stripped-down prompt (no T7 structure). Measure WR delta.
- **Impact:** HIGH — isolates prompt contribution vs mechanical OB edge. Foundational.
- **Cost:** ~$15-30 API

### T4.7 — Test D: OB zone vs generic S/R
- **Source:** kb_edge_mechanisms, Research R069
- **Mechanism:** Comparative study — OB retest continuation vs generic S/R reversal on same MSOs
- **Impact:** MEDIUM — discriminates OB edge from S/R
- **Cost:** MEDIUM

### T4.8 — Two-stage entry (M15 trigger + M1 confirm)
- **Source:** 113q Q7.3, Research R019
- **Mechanism:** After M15 C-gate PASS, wait for M1 confirmation candle before entry.
- **Impact:** HIGH potential — better fills, less adverse excursion
- **Cost:** HIGH — new M1 confirm component, prompt update
- **Risk:** HIGH — entirely new entry mechanic

### T4.9 — Ensemble 3-prompt diverse voting
- **Source:** L4 D17/D20/D21, Research R007/R065
- **Mechanism:** 3 different prompts per MSO, majority vote. Position-reduce on split decisions.
- **Impact:** HIGH — L4 predicts +3pp WR + calibrated confidence from agreement rate
- **Cost:** HIGH — 3× API cost (~$180/mo) + prompt authoring
- **Pre-req:** CEO budget + prompt diversity design

### T4.10 — HMM regime classifier (shadow-first)
- **Source:** Quantlabs Q008, blog batch_03/_08/_09
- **Mechanism:** 5-state HMM `{high_vol, low_vol, liquidity_drought, trending, mean_reverting}` on M15 returns via `hmmlearn`. Shadow-log state per MSO.
- **Impact:** HIGH long-term — unlocks regime-aware sizing (T6.x), regime-conditioned prompts (T4.15), regime framework switch (T6.x)
- **Cost:** MEDIUM — new component + dependency
- **Risk:** LOW for shadow mode

### T4.11 — Hurst exponent as R2 candidate feature
- **Source:** Quantlabs Q007, L4
- **Mechanism:** Daily Hurst exponent of H1 returns logged to R2 candidate features logger. >0.5 = momentum, <0.5 = mean-revert.
- **Impact:** MEDIUM — regime signal for later modeling
- **Cost:** LOW — feature add to existing logger

### T4.12 — Microprice feature
- **Source:** Quantlabs Q019
- **Mechanism:** `(bid_size*ask + ask_size*bid)/(bid_size+ask_size)` at candle close. R2 candidate feature.
- **Impact:** MEDIUM — market-microstructure entry quality
- **Cost:** LOW — L1 bid/ask sizes via MT5

### T4.13 — OFI (Order Flow Imbalance) shadow logger
- **Source:** Quantlabs Q010
- **Mechanism:** Lee-Ready tick-rule approximation on M1 ticks. Shadow-log per symbol per KZ.
- **Impact:** MEDIUM — OBI ±0.3 extreme threshold as entry quality signal
- **Cost:** MEDIUM — tick pipeline (shared with VPIN Q005)
- **Pre-req:** Tick pipeline spike

### T4.14 — VPIN toxicity shadow logger
- **Source:** Quantlabs Q005, blog batch_04/_09
- **Mechanism:** Tick-bucket toxicity score via `mt5.copy_ticks_*`. Composite score `z(VPIN)*0.4 + z(OBI)*0.3 + z(AC1)*0.3`.
- **Impact:** MEDIUM — entry quality filter (VPIN>0.75 suggests skip)
- **Cost:** MEDIUM — tick pipeline + bucket calibration (1-2 days)

### T4.15 — Regime-conditioned T7 prompt variant
- **Source:** Quantlabs Q021
- **Mechanism:** Inject `{regime}` + `{volatility}` state into T7 C-gate prompt
- **Impact:** MEDIUM
- **Cost:** MEDIUM — prompt change (CEO approval) + regime classifier (T4.10 prereq)
- **Pre-req:** T4.10 HMM shadow-log ≥100 obs with state-dependent WR divergence

### T4.16 — Asia-range midpoint daily bias
- **Source:** Podcast H2, Research R022
- **Mechanism:** Compute midpoint of Asia session range; use as daily directional bias.
- **Impact:** LOW-MEDIUM
- **Cost:** MEDIUM — new bias module

### T4.17 — 66% stop reduction at 1:1 (H7 variant)
- **Source:** Podcast H7, Research R024
- **Mechanism:** Reduce SL by 66% (not full BE) at +1R. Different from standard BE shadow.
- **Impact:** MEDIUM — variance compression with less risk of BE stop-out
- **Cost:** MEDIUM — shadow logger variant

### T4.18 — Order-flow signature at entry (last 3 M1 candles)
- **Source:** 113q Q8.4, Research R020
- **Mechanism:** Log last 3 M1 candle signatures (body/wick direction, volume) as R2 feature
- **Impact:** MEDIUM
- **Cost:** LOW — R2 logger enrichment

### T4.19 — RSI divergence at OB retest
- **Source:** Podcast H11, Research R026
- **Mechanism:** Compute RSI divergence at retest candle, log as R2 feature
- **Impact:** LOW-MEDIUM
- **Cost:** LOW — standard indicator

### T4.20 — Chop-zone entry suppression
- **Source:** Podcast H1, Research R021
- **Mechanism:** Detect ranging H1 (ADX < threshold), suppress entries
- **Impact:** MEDIUM
- **Cost:** MEDIUM — regime classifier + filter

### T4.21 — Alpha decay by session
- **Source:** Podcast H10, Research R025
- **Mechanism:** Trend analysis of per-session OB continuation rate over time
- **Impact:** LOW-MEDIUM — decay signal
- **Cost:** LOW — monitor extension

### T4.22 — Kill-zone saturation filter
- **Source:** Podcast H22, Research R028
- **Mechanism:** After N trades in a KZ across all instruments, suppress further entries. Currently only per-day (`max_daily_losses: 2`).
- **Impact:** LOW
- **Cost:** LOW — `permissions.py` logic add

### T4.23 — Multi-TF confluence (H4 + H1 + M15)
- **Source:** Podcast H12, Research R027/R038
- **Mechanism:** Full 3-TF directional confluence check. T7 C-gate covers H1/M15 only.
- **Impact:** MEDIUM
- **Cost:** MEDIUM — prompt update + MSO enrichment
- **Risk:** Requires CEO approval (prompt change)

### T4.24 — Seasonal gold filter (Q1 ETF inflows, wedding demand)
- **Source:** Quantlabs Q030 (gold-only slice)
- **Mechanism:** XAUUSD-specific seasonal overlay on T7 prompt
- **Impact:** LOW-MEDIUM — XAUUSD only
- **Cost:** LOW

### T4.25 — Quote-stuffing / spoofing detection in KZs
- **Source:** Quantlabs Q029 (batch_03 Quote Fade Algorithm)
- **Mechanism:** Sub-second top-3-level order-book covariance anomaly detection
- **Impact:** LOW-MEDIUM — edge discovery / protection
- **Cost:** MEDIUM — tick-level analysis
- **Pre-req:** VPIN (T4.14) results

### T4.26 — sl_beyond_ob cross-instrument audit (T2.9 pre-req)
- **Source:** NAS100 T3.1 analysis (session 33), agent C + cold review E.
- **Question:** Does the NAS100 pattern — 42 bit-exact LONG rejects with `stop_loss == OB_low` killed by strict `<` gate — also exist on XAUUSD historical? If yes, ship T2.9 gate fix cross-instrument. If no, consider prompt-level fix instead.
- **Data:** XAUUSD 367-trade KB (`knowledge_base/trades/`), XAUUSD Test A rerun, XAUUSD T7 simulation JSON.
- **Deliverable:** `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md` — numerical answers + recommended fix path (gate relaxation vs prompt-level buffer requirement).
- **Impact:** HIGH (unblocks T2.9 decision).
- **Cost:** $0 (local replay).
- **Approval:** None (research).

---

# T5 — INFRASTRUCTURE MATURITY (shadow loggers, monitors)

### T5.1 — FVG gap/ATR shadow enrichment (R2 logger)
- **Source:** Session 27 B7 verdict, Research R008, D-9
- **Mechanism:** Add FVG gap-size-over-ATR features to R2 candidate features logger. ~30-50 LOC. Observation-only.
- **Impact:** LOW for now; enables post-challenge orthogonality test vs OB edge
- **Cost:** LOW

### T5.2 — Premium/Discount pd_zone shadow logger
- **Source:** Session 27 B8 verdict, Research R009, D-8
- **Mechanism:** Standalone script reading `pipeline_state/02_market_state.json` + trade index, writing `shadow_logs/pd_zone_log.csv`. Joins pd_zone with trade outcomes.
- **Decision session 27:** DEFER — orthogonality test should run on existing data FIRST. Only build logger if test shows independence from OB edge.
- **Impact:** LOW (per analysis — frequency-adjusted expectancy negative)
- **Cost:** MEDIUM (conditional)

### T5.3 — Per-symbol MAE shadow monitor
- **Source:** Session 27 B6 verdict, Research R010, D-10
- **Mechanism:** Monthly monitor mirroring `ob_continuation_monitor.py` pattern. Tracks per-symbol loser-MAE p10 drift.
- **Impact:** LOW — tripwire for OB-detection algo drift
- **Cost:** ~150 LOC standalone

### T5.4 — ~~Time-in-trade shadow logger~~ → **CLOSED 2026-04-19 (session 33, commit `d6775be`)**
- **Closure:** `d6775be feat(shadow): time-in-trade shadow logger (T5.4)`. Mirrors `be_shadow_logger.py` pattern. Last open quantlabs P0 fold.

### T5.5 — Portfolio bot health score 0-100
- **Source:** Quantlabs Q023
- **Mechanism:** Composite score across symbols (WR, Sharpe, no-data events, API-refusal rate). Alert <40.
- **Impact:** MEDIUM — operator visibility
- **Cost:** MEDIUM — aggregation layer

### T5.6 — Log-event density benchmark
- **Source:** Quantlabs Q028
- **Mechanism:** Baseline events/hour per symbol. Alert on ±50% deviation.
- **Impact:** LOW — data integrity check
- **Cost:** LOW

### T5.7 — ADWIN change detection
- **Source:** Research R062 / L4 D2
- **Mechanism:** `river.drift.ADWIN` on CR, confidence, token count
- **Impact:** MEDIUM — additional drift signal orthogonal to SPRT/CUSUM
- **Cost:** LOW — standalone script
- **Pre-req:** `river` dependency

### T5.8 — Hotelling T² rolling-30 WR predictor
- **Source:** Research R014 / 113q Q1.1
- **Mechanism:** Multivariate rolling-30 feature vector → Hotelling T² → early-warning signal
- **Impact:** MEDIUM
- **Cost:** MEDIUM

### T5.9 — DDM on win rate
- **Source:** Research R064 / L4 D7
- **Mechanism:** Warning at μ+2σ, drift at μ+3σ. Overlaps with SPRT/CUSUM but different framework.
- **Impact:** MEDIUM
- **Cost:** LOW

### T5.10 — FTMO daily cap vs realized vol correlation
- **Source:** Research R017 / 113q Q4.1
- **Mechanism:** Correlate daily-cap loss clustering with realized-volatility clusters
- **Impact:** LOW
- **Cost:** LOW — notebook

### T5.11 — Break-even frequency at min_rr=1.5
- **Source:** Research R018 / 113q Q5.6
- **Mechanism:** Solve E[R]=0 for trade count at current WR. Sanity-check economic viability.
- **Impact:** LOW — analytical reference
- **Cost:** TRIVIAL

### T5.12 — R2 features logger export + schema check (O-8)
- **Source:** Handoff O-8
- **Mechanism:** Export to parquet + schema drift check. Run end of challenge month 1.
- **Impact:** LOW — health check
- **Cost:** LOW

### T5.13 — Consecutive-loss cooldown (weak evidence)
- **Source:** Quantlabs Q015 (single-source, batch_03 only)
- **Mechanism:** Per-symbol halt after 3 consecutive losses with 60-min cooldown. Current `max_consecutive_losses: 5` stops for the day with no cooldown.
- **Impact:** LOW — weak citation, shadow-log first
- **Cost:** LOW

### T5.14 — SL/TP broker mismatch auto-alert (S13)
- **Source:** Playbook S13, Research R070
- **Mechanism:** Compare broker-reported SL/TP vs system log; Telegram alert on mismatch
- **Impact:** MEDIUM
- **Cost:** LOW — watchdog extension

### T5.15 — Zero-trade auto-flag (S23/S24)
- **Source:** Playbook S23/S24, Research R071
- **Mechanism:** Flag if CR below rolling floor
- **Impact:** MEDIUM
- **Cost:** LOW

### T5.16 — Correlation gate audit log (S31)
- **Source:** Playbook S31, Research R074
- **Mechanism:** Log every correlation-block decision (code exists, audit missing)
- **Impact:** LOW
- **Cost:** TRIVIAL

### T5.17 — Flash-crash auto-freeze (S26)
- **Source:** Playbook S26, Research R072
- **Mechanism:** Auto-freeze entry pipeline on >2×ATR single candle
- **Impact:** MEDIUM — capital protection
- **Cost:** MEDIUM — market_state.py + orchestrator

### T5.18 — VIX auto-reduce risk (S28)
- **Source:** Playbook S28, Research R073
- **Mechanism:** Reduce `risk_pct` when VIX > threshold
- **Impact:** LOW-MEDIUM
- **Cost:** MEDIUM — VIX feed + `drawdown_manager.py`-style logic

### T5.19 — Graceful API degradation policy (W9)
- **Source:** SWOT W9, Research R043
- **Mechanism:** Defined behaviors on refusal / rate-limit / model-change / timeout. Currently ad-hoc.
- **Impact:** MEDIUM
- **Cost:** MEDIUM — policy spec + implementation

### T5.20 — Parameter perturbation validation
- **Source:** Quantlabs Q017 / L4
- **Mechanism:** Sensitivity analysis on ±20% param moves. Add to R2 promotion battery.
- **Impact:** MEDIUM — validation rigor
- **Cost:** LOW

### T5.21 — Parallel MC with trade-order permutation
- **Source:** Quantlabs Q020
- **Mechanism:** Extend existing MC (99.4% P(FTMO-pass)) with trade-order permutation variant
- **Impact:** LOW
- **Cost:** LOW

### T5.22 — Passive Telegram alert for missed A+ setups
- **Source:** SWOT O6, Research R041
- **Mechanism:** Post-hoc scan — if a NO_TRADE evaluated setup would have been +1.5R+, alert CEO
- **Impact:** LOW — CEO visibility only
- **Cost:** MEDIUM

### T5.23 — XAUUSD 126-day silent data gap investigation (O-4)
- **Source:** Handoff O-4
- **Mechanism:** Investigate root cause of 126-day XAUUSD gap in `data/historical/`. Backfill or document.
- **Impact:** LOW — data hygiene
- **Cost:** 1-2 hours

### T5.24 — D1-bias-lag shadow logger + alert
- **Source:** NAS100 T3.1 analysis (session 33), agent D (rock-solid W14 finding: 54/54 bearish bias_source=D1 during +4.20% rally → 0 CANDIDATEs).
- **Problem:** D1 bias is slow to rotate through regime inflections; when D1 disagrees with H4+H1 for extended windows, all SHORT (or LONG) setups are silently refused regardless of price action.
- **Mechanism:** New logger `src/components/d1_bias_lag_logger.py`. After MSO build + before AI call, log when `d1_bias != h1_direction AND d1_bias != h4_bias`. Write to `shadow_logs/d1_bias_lag.jsonl` with consecutive-count tracking. Telegram alert when count crosses threshold (default N=20 candles ≈ 5h).
- **Impact:** MEDIUM — instrument-agnostic regime-inflection detector. Same mechanism will bite XAUUSD / US30 at next inflection.
- **Cost:** ~60 LOC + tests + watchdog wire.
- **Approval:** None (additive shadow logger; CLAUDE.md "Allowed without approval" — new safety gates additive + shadow data collection).
- **Dispatch:** See `.context/02_session_handoffs/34_apr19_FRESH_SESSION_POST_NAS100_PROMPT.md` Action 3.

---

# T6 — RESEARCH-HEAVY (substantial new analysis; long tail)

### T6.1 — Empirical Kelly f* from R-multiples
- **Source:** L4 A20, Research R053
- **Cost:** LOW (notebook)
- **Pre-req:** 300 R-multiples (currently ~42 live)

### T6.2 — Risk-constrained Kelly for FTMO
- **Source:** L4 A22, Research R054
- **Pre-req:** T6.1

### T6.3 — Conditional MFE distribution P(nR|mR)
- **Source:** L4 B1/B36, Research R055
- **Foundation for:** all partial-close decisions
- **Pre-req:** ~300 trades (42 live now)

### T6.4 — GPD fit to MAE tail (confirm ξ > 0.3)
- **Source:** L4 A3, Research R050
- **Cost:** LOW (notebook)

### T6.5 — GARCH-EVT conditional SL
- **Source:** L4 A14, Research R051
- **Pre-req:** T6.4

### T6.6 — MFE × realized-volatility correlation
- **Source:** L4 B28, Research R056

### T6.7 — Vol-regime classifier modulating exits
- **Source:** L4 B37, Research R057

### T6.8 — Full DCC-GARCH correlation-breakdown pipeline
- **Source:** Quantlabs Q004b
- **Pre-req:** arch/statsmodels dependency decision

### T6.9 — Hawkes process toxicity λ(t)
- **Source:** Quantlabs Q022
- **Nature:** Research-grade; not a sprint candidate

### T6.10 — Regime-aware framework switch
- **Source:** SWOT O4, Research R039
- **Pre-req:** T4.10 (HMM) mature

### T6.11 — Fed linguistic sentiment scoring
- **Source:** KAP Edge #4, Research R049
- **Cost:** HIGH (text pipeline)

### T6.12 — Composite strategy score for R2 ranking
- **Source:** Quantlabs Q012
- **Formula:** `0.30*Sharpe + 0.20*Sortino + 0.20*ExpR + 0.15*WR + 0.15*Calmar`
- **Pre-req:** Multi-framework architecture (currently single)

### T6.13 — Drawdown-to-Profit Ratio (DDtoP) gate
- **Source:** Quantlabs Q011
- **Caveat:** Cold review flagged citation unverified — recheck batch_06 before spending time

### T6.14 — Half-Kelly with HMM multipliers
- **Source:** Quantlabs Q013, blog batch_03
- **Pre-req:** T4.10 HMM mature

### T6.15 — News filter (NFP / CPI / FOMC)
- **Source:** WF-2 C05, Research R005, Quantlabs Q018 (AI scan variant)
- **Two paths:**
  - Config-driven block 30 min pre/post tier-1 releases
  - AI news-scan shadow logger
- **Pre-req:** Calendar source decision

### T6.16 — Session memory structural-only revival
- **Source:** WF-2 C06, Research R006, L4 D15
- **Mechanism:** Revive session memory but strip labels/numbers. T2b killed full-memory; stripped variant untested.
- **Cost:** ~$45 to test + prompt authoring

### T6.17 — Within-CANDIDATE discrimination (W1)
- **Source:** SWOT W1, Research R042
- **Mechanism:** Post-C-gate, no ranking among CANDIDATEs today. Either prompt redesign or ensemble (T4.9).

### T6.18 — Post-publication decay two-prop z-test
- **Source:** L4 C1, Research R058
- **Mechanism:** First-half vs second-half of 300-trade window
- **Pre-req:** 300+ trades (42 live now)

### T6.19 — Google Trends SVI crowding signal
- **Source:** L4 C11, Research R060
- **Mechanism:** Correlate SMC/ICT search volume with quarterly WR
- **Impact:** LOW

### T6.20 — COT positioning weekly filter
- **Source:** Quantlabs Q025, blog batch_09

### T6.21 — Shanghai gold premium XAUUSD sentiment
- **Source:** Quantlabs Q024, blog batch_09

### T6.22 — Central-bank calendar position sizing
- **Source:** KAP Edge #2, Research R048

### T6.23 — MCP supply-chain security audit
- **Source:** Quantlabs Q026, youtube batch_05 #4
- **Mechanism:** Enumerate installed packages, flag 3rd-party MCP servers
- **Impact:** LOW currently (limited MCP exposure: MT5 + Anthropic)

### T6.24 — Gateway-only broker connection architecture
- **Source:** Quantlabs Q009, large architectural change
- **Mechanism:** MT5 in separate process; hot-swap orchestrator without broker disconnect
- **Impact:** HIGH long-term
- **Cost:** HIGH — IPC + major refactor

### T6.25 — Task A Approach C: in-line resolver in orchestrator
- **Source:** ADR 001 parked, D-1, Research R030
- **Trigger:** Next WF-1 window

### T6.26 — Retest geometry Approach D (pre-2024 data)
- **Source:** ADR 002 parked, Research R031
- **Trigger:** Regime homogeneity test rejection

### T6.27 — Touch-count OB gate re-calibration
- **Source:** D-6
- **Trigger:** Post-challenge evaluation of shadow log

### T6.28 — Quadratic decay model
- **Source:** L4 C2, Research R059
- **Status:** Underpowered (4 quarters), wait for more data

### T6.29 — Pool_type edge-case extension
- **Source:** D-5
- **Trigger:** Edge case logged to `malformed_responses.jsonl` post-challenge

### T6.30 — Tier 2 intra-candle entry pattern re-run
- **Source:** D-12, Handoff 25/26
- **Trigger:** Corrected spec post-challenge

### T6.31 — EURUSD 100-OB baseline replication
- **Source:** KAP #1, Research R044
- **Pre-req:** T3.1 onboarding or parallel research

### T6.32 — OB age vs continuation rate
- **Source:** KAP #6, Research R046
- **Cost:** LOW — R2 logger enrichment + analysis

---

# T7 — KILL / CLOSED (do NOT re-propose)

## CLOSED-NULL (tested, zero effect)

| Item | Finding | Reference |
|------|---------|-----------|
| Speed-to-MFE (q65, B5) | NULL — test confounded | Session 26 |
| Q-scores Q1-Q7 correlation with wins | r=-0.06, zero predictive | Handoff 13 |
| AI vs mechanical OB entry WR | ~0pp delta — edge is zone, not AI | Test A rerun |
| Per-symbol MAE calibration (q52/B6 H1) | UNIFORM — keep pooled 0.5 ATR | Session 26/27 |
| Wick-vs-close OB penetration categorical | Artifact per ADR 003 | Handoff 25 |
| Tier 2 intra-candle entry (original spec) | Market baseline + TP convention mismatches | Handoff 25/26 |

## CLOSED-KILL (decision-based)

| Item | Verdict | Reference |
|------|---------|-----------|
| Q-6.1 trailing stop OU theoretical replay | OU can't rank — null (but empirical full-pop rerun still open as T2.1) | Handoff 09 |
| Q-5.1 GARCH volatility signal | NULL, 0/11 Bonferroni | Handoff 09 |
| q62 partial close 4 schemes | DEFER-all, none cleared Bonferroni | Session 26 |
| Phase 2A v1 scored prompt | Replaced by T7 C-gate | Handoff 13 |
| Confidence scorer (rubber-stamp) | Shadow permanent | Handoff 05+ |
| Session memory (full-label variant) | T2b p=0.007 CR suppression | Handoff 11 |

## REJECTED (competitor-derived, evaluated KILL)

| Item | Reason | Reference |
|------|--------|-----------|
| AI-generated bot pipeline (Q031) | KAP is higher-rigor equivalent | Quantlabs |
| One-strategy-many-instruments (Q032) | Wrong for ob_retest (symbol-specific) | Quantlabs |
| Rithmic/IBKR broker migration (Q033) | Scope mismatch — prop-firm MT5 by design | Quantlabs |
| BlackRock AlphaAgents debate (Q034) | Duplicate of paused Component 3B | Quantlabs |
| Streamlit per-strategy sandbox (Q035) | UI out of scope | Quantlabs |

## ALREADY-SHIPPED (don't duplicate)

| Item | Commit | Reference |
|------|--------|-----------|
| 8% DD risk reduction (H29) | `f757249` | Handoff 08/09 |
| BE shadow logger | `81c63c6` | Handoff 09 |
| Session volatility monitor (H25) | various | Handoff 09+ |
| US30 sweep divergence monitor (H16) | various | Handoff 09+ |
| Inverted TP auto-correction | `4ec13f4` | Handoff 05 |
| Touch-count OB gate | `1a22d92` | Handoff 19 |
| Pending intent persistence | `1a22d92` | Handoff 19 |
| SL margin 0.3→0.5 | `1a22d92` | Handoff 19 |
| Between-KZ pending limit check | `2a0506f` | Handoff 17 |
| Limit-filled exit data capture | `fb86280` | Handoff 23 |
| Prop-firm profile overlay | `78680ec` | Handoff 20 |
| Canary cache dedup | `0c26d25` | Handoff 23 |
| OB continuation rolling-50 monitor | `11dee1d` wired `1827871` | Handoff 24/26 |
| API refusal monitor | `b0c2ece` | Handoff 23 |
| Proximity shadow logger | `3b9f197` | Handoff 13 |
| Partial close shadow logger (Variant C) | `3b9f197` | Handoff 13 |
| Liquidity cluster gate (DISABLED) | `ab077cd` | Handoff 20 |
| R2 candidate features logger | `ab077cd` | Handoff 20 |
| Displacement event logger | `81f67de` | Handoff 17 |
| Test isolation conftest write guard | `fa93c35` | Handoff 21 |
| UTC timestamps everywhere | `b0c2ece` | Handoff 23 |
| MT5 preflight script | (see CLAUDE.md + `c9cefc8`) | Handoff 26 |
| Watchdog `--profile redacted_account` | `23c083f` | Handoff 21 |

## ALREADY-COVERED (different name, same function)

| Item | Covered by |
|------|-----------|
| Quantlabs Q036 "shadow-then-live" | Multiple GTOS shadow loggers |
| Quantlabs Q037 "50-100 trade minimum" | SPRT is stricter |

---

# Dependency graph (what depends on what)

```
T4.10 (HMM shadow) ────> T4.15 (regime prompt), T6.7 (vol-regime exits), T6.10 (regime framework), T6.14 (Kelly-HMM)
T6.4 (GPD fit) ────> T6.5 (GARCH-EVT SL)
T6.1 (Kelly f*) ────> T6.2 (risk-constrained Kelly)
T4.14 (VPIN) ────> T4.13 (OFI) [shared tick pipeline], T4.25 (quote-stuffing)
T2.3 (liquidity gate enable) ────> T2.2 (ADR 004 Option C)
T2.1 rerun positive ────> T2.1 deployment decision
T4.9 (ensemble) ────> T5.x (position-reduce on split decisions — L4 D20)
T3.1 (EURUSD/NAS100 onboarding) ────> T6.31 (EURUSD baseline validation)
T5.23 (XAUUSD data gap) is standalone; doesn't block other items
T0.2 (deployment.phase) ────> all future trading-logic changes become safer to test
```

---

# Recommended execution order

## Phase A — Pre-challenge (Sat-Mon, before 2026-04-21)

Ship fast, low-risk, high-value:
1. T0.5 — commit loose ends (30 min)
2. T0.1 — revert Impl-A diff (10 min)
3. T0.3 — CLAUDE.md stale lines (30 min)
4. T0.4 — verify R078/R079 bug status (30 min, possibly +1-2h fix)
5. T1.2 — prepaid card cap (1h operational)
6. T0.6 — start watchdog end-to-end verification (passive observation through weekend)

If time permits:
7. T1.3 — borderline canary fixtures (~2h)
8. T0.2 — `deployment.phase` enforcement (carefully; CEO approval; 3-4h)

## Phase B — Challenge Week 1 (ops + additive observation)

Operator focus. Runbook (O-6), handoff 27 draft (O-9).

Ship in parallel (additive, zero-collision):
- ~~T1.4 — model-id pinning + drift alert~~ (CLOSED session 30, `2654b65`)
- ~~T1.5 — CUSUM on CANDIDATE rate~~ (CLOSED session 30, `525157e`)
- ~~T1.6 — correlation-shock Telegram alert~~ (CLOSED session 32, `b796785`)
- ~~T1.7 — daily no-data tick-liveness alert~~ (CLOSED session 30, `baf09ea`)
- ~~T1.8 — weekly AI summary loop~~ (DROPPED session 31 — CEO reviews manually via Claude Code)
- ~~T1.x — fix 23 pre-existing test failures + 1 error~~ (CLOSED session 31, groups A–F)

## Phase C — Challenge Week 1-2 (shadow-only research)

- T2.1 — trailing stop full-population rerun (historical, $0)
- T4.1 — R:R sweet spot sweep (historical, $0)
- T4.2 — ATR multiplier sweep (historical, $0)
- T4.3 — mitigated vs fresh OB (historical, $0)
- T4.4 — OB session × DoW matrix (historical, $0)
- T4.6 — Test B prompt-neutral rerun ($15-30)

New shadow loggers:
- T5.1 — FVG gap/ATR enrichment (R2)
- T5.4 — time-in-trade shadow logger

## Phase D — Challenge Week 2-4 (careful promotions + expansion research)

- T2.4 — BE shadow promotion decision (if n≥30)
- T2.5 — Variant C promotion decision (if n≥30)
- T4.5 — strip confidence scorer (cleanup)
- T3.2 — Bull/Bear Debate A/B wiring
- T4.10 — HMM shadow-log (foundational for regime work)
- T4.11 — Hurst exponent feature
- T4.12 — microprice feature
- T4.9 — ensemble 3-prompt test (if budget permits, ~$50 to validate)

## Phase E — Month 1-2 (expansion, promotions)

- T3.1 — EURUSD + NAS100 onboarding
- T2.3 — liquidity gate enable (if n≥100)
- T2.2 — ADR 004 Option C (if liquidity gate precision/recall OK)
- T6.1 — empirical Kelly f*
- T6.4 — GPD MAE fit
- T4.14 — VPIN shadow (tick pipeline spike)
- T4.13 — OFI shadow (shares tick pipeline)

## Phase F — Month 2+ (architectural, research-heavy)

- T4.8 — two-stage entry research
- T3.3 — liquidity sweep framework
- T6.2/T6.5/T6.7/T6.8/T6.10 — advanced risk/regime modeling
- T6.24 — gateway architecture refactor (if needed)
- T6.15/T6.16 — news filter + session memory revival

---

# Summary statistics

- **Total items in master backlog:** 143 (T0-T6)
- **Pre-challenge shippable (T0+T1):** 17
- **Validated deployments awaiting CEO (T2):** 7
- **Expansion items (T3):** 3
- **Edge discovery research (T4):** 25
- **Infrastructure maturity (T5):** 23
- **Research-heavy long-tail (T6):** 32
- **Explicit KILL/CLOSED for dedup (T7):** 48+ items (prevents re-proposal)

---

# Files referenced

- `.context/backlog_synthesis_2026-04-18/00_MASTER_BACKLOG.md` — this file
- `.context/backlog_synthesis_2026-04-18/handoff_open_items.md` — source sweep
- `.context/backlog_synthesis_2026-04-18/research_wf2_open_items.md` — source sweep
- `research/quantlabs_competitor_intel/synthesis/02_extraction_for_backlog_merge.md` — source
- `research/quantlabs_competitor_intel/synthesis/00_gtos_upgrade_candidates.md` — quantlabs primary
- `research/quantlabs_competitor_intel/synthesis/01_cold_review.md` — quantlabs critique
- `.context/04_agents/WF2_SHADOW_GATES_V2.md` — WF-2 canon
- `.context/03_analysis/SWOT_FINAL.md` — SWOT
- `.context/03_analysis/research_execution_plan_113q.md` — 113-question plan
- `.context/01_knowledge_base/kb_podcast_intelligence_111_episodes.md` — podcast H1-H34
- `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md` — Tests B/C/D
- `.context/05_operations/operator_decision_playbook.md` — S1-S41
- `.context/06_decisions/001-004` — ADR parked alternatives
- `CLAUDE.md` — authoritative project state (has stale lines per T0.3)

---

# Handoff instructions for implementing agent

1. **Start with T0 entirely.** Do not skip correctness work. T0 must complete before anything else.
2. **Dispatch T1 items in parallel** where possible — all are additive, zero-collision.
3. **T2 items need explicit CEO approval per item** — each is a trading-logic change.
4. **T4 research batches can run in parallel** — multiple historical replays fit in one session.
5. **Before writing ANY code**, run `git log --oneline --since="2026-04-18"` and verify the item hasn't shipped since this backlog was generated.
6. **Every deliverable is a committed file** — not a chat message.
7. **If in doubt, ask CEO.** Don't assume authorization from this backlog.
8. **This backlog is READ-ONLY advisory.** Items may have been re-prioritized by CEO in session 28+. Treat as snapshot of 2026-04-18.

---

*End of master backlog. Generated 2026-04-18 by session 27 main thread. 3 parallel Opus 4.7 max-effort sub-agents surfaced source data; synthesis + prioritization done on main.*
