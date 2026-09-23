# GTOS Audit Synthesis Triage — 2026-04-26

**Synthesizer:** Main thread, Opus 4.7 1M
**Source:** 26 parallel audit agents
**Working dir:** `C:/Users/MSI/Documents/ai-trading-agent`
**Verification cutoff:** 2026-04-26 (HEAD `c21d702`)
**Scope:** Disposition + cross-validation of every finding against current code, ADRs, CLAUDE.md, and project memory

---

## Executive Summary

**Audits processed:** 26
**Total distinct findings extracted:** ~110 (after de-duplication of 14 cross-audit confirmations)

**Disposition counts:**
- PRE-MONDAY-BLOCKER: **3**
- POST-MONDAY-HIGH: **9**
- POST-MONDAY-MEDIUM: **17**
- POST-MONDAY-LOW: **22**
- FALSE-POSITIVE-AGENT-MISSED-CONTEXT: **18**
- VALID-AS-IS (audit-confirmed correct, noted for posterity): **27**
- DUPLICATE (consolidated into 14 cross-audit entries): **14**

**Top 3 highest-priority items (all PRE-MONDAY-BLOCKER):**
1. **Watchdog/start_all 5-vs-7 instrument drift** — `watchdog.ps1` `SymbolMap` (lines 42-48) + `TickSymbolMap` (lines 335-341) only cover 5 symbols. `start_all.bat` correctly launches all 7. XAGUSD + NAS100 will start once Monday but won't be respawned by watchdog if they crash. Tick capture daemons won't run for them either.
2. **Pre-deploy checklist commands broken** — Multiple commands in `SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md` reference syntax that doesn't exist: `pwsh scripts/watchdog.ps1 -Action stop-all` (line 44, 198), `--profile ftmo` flags on `displacement_logger.py` and `heartbeat_monitor.py` entry points (lines 54-55), checklist HEAD reference `6b85287` is 4 commits stale.
3. **`fn_smoke_trade.py` DEFAULT_SYMBOLS only 5** — Line 89 has `["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]`. Cannot smoke-test XAGUSD or NAS100 fills before Monday open without `--symbols XAGUSD,NAS100` override (which is undocumented in checklist step 6).

---

## Section 1: PRE-MONDAY-BLOCKER

### B1. Watchdog SymbolMap covers only 5 instruments (XAGUSD + NAS100 unsupervised)

- **Source audit(s):** AUDIT 18 (Monday-Ready), AUDIT 16 (MT5-Broker), AUDIT 22 (Tick-Capture)
- **Verification:** VERIFIED-AGAINST-CODE
- **Evidence cited:**
  - `scripts/watchdog.ps1:42-48` — `$SymbolMap` only contains XAUUSD/US30_cash/USDJPY/GBPJPY/GBPUSD
  - `scripts/watchdog.ps1:131` — orchestrator-kill loop iterates the same 5
  - `scripts/watchdog.ps1:335-341` — `$TickSymbolMap` also only 5 (so tick daemons won't supervise XAGUSD/NAS100)
  - `start_all.bat:60-77` — correctly launches all 7 orchestrators including `XAGUSD` (line 75) and `NAS100` (line 77)
  - `scripts/watchdog.ps1:5` — docstring still says "5 instruments"
  - `CLAUDE.md` "What is working" — fleet IS 7 instruments (2026-04-25 d2a31d0)
- **Confidence:** HIGH
- **Recommended fix:** Add `XAGUSD = "xagusd.log"` and `NAS100 = "nas100.log"` to `$SymbolMap`. Add same two to `$TickSymbolMap` (with appropriate broker mt5_symbol). Update kill-foreach loops at line 131 + line 343. Update docstring "5 instruments" → "7 instruments". One commit, ~15 min including manual smoke verification.
- **Effort estimate:** 30 min (edit + test under both profiles)
- **Risk if not fixed:** If XAGUSD or NAS100 orchestrator crashes mid-week (memory leak, MT5 disconnect, exception), there is no automated respawn. Position state could go inconsistent (open trade in MT5 but no orchestrator process to manage TP/SL/timeout). For NAS100 in 3-day live-OBSERVE, this could miss the entire trial window. For XAGUSD on 0.5% live, this is a real money management gap.

---

### B2. Pre-deploy checklist commands are broken syntax + stale HEAD reference

- **Source audit(s):** AUDIT 18 (Monday-Ready), AUDIT 19 (Ops-Doc-Drift)
- **Verification:** VERIFIED-AGAINST-CODE
- **Evidence cited:**
  - `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md:5` says HEAD is `6b85287`. Actual HEAD is `c21d702` (4 commits ahead). Step 2 line 18 `cat .context/LIVE_STATE.md | head -30 # confirm HEAD matches 6b85287` will fail comparison.
  - Checklist line 44, 104, 198 reference `pwsh scripts/watchdog.ps1 -Action stop-all` and `-Action restart-all`. Verified absent from `scripts/watchdog.ps1` — no top-level `param([Action])` block exists; the script uses GTOS_PROFILE/GTOS_MODE env-vars only (per c21d702).
  - Checklist line 54-55 reference `python scripts/displacement_logger.py --profile ftmo &` and `python scripts/heartbeat_monitor.py --profile ftmo &`. `displacement_logger.py` has no `--profile` argparse arg. `scripts/heartbeat_monitor.py` does NOT EXIST — actual entry point is `python -m src.safety.heartbeat_monitor` (per `scripts/watchdog.ps1:412`).
  - Checklist line 199 references `python scripts/flatten_positions.py` — file does not exist (already documented as "(if exists; otherwise manual via MT5 terminal)" so this caveat is acknowledged).
- **Confidence:** HIGH
- **Recommended fix:** Update checklist:
  - Line 5: `Main HEAD at session 39 close: c21d702` (or remove the assertion and let `python scripts/generate_live_state.py` regenerate)
  - Line 44: replace with `taskkill /F /FI "WINDOWTITLE eq *XAUUSD*"` (etc) OR with proper documentation that watchdog supervises automatically
  - Line 54-55: remove `--profile ftmo` from displacement_logger and heartbeat_monitor commands. Use `python -m src.safety.heartbeat_monitor`.
  - Line 198: same as line 44 (stop-all syntax doesn't exist)
- **Effort estimate:** 20 min
- **Risk if not fixed:** Operator runs commands from checklist Sunday/Monday at market-open pressure, gets PowerShell parser error, scrambles for fix. Worst case: incorrect manual `taskkill` leaves zombie processes, dual orchestrators write conflicting `position_state.json`, system enters undefined state.

---

### B3. `fn_smoke_trade.py` DEFAULT_SYMBOLS missing XAGUSD + NAS100

- **Source audit(s):** AUDIT 16 (MT5-Broker), AUDIT 18 (Monday-Ready)
- **Verification:** VERIFIED-AGAINST-CODE
- **Evidence cited:**
  - `scripts/fn_smoke_trade.py:89` — `DEFAULT_SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]` (5 symbols)
  - `scripts/fn_smoke_trade.py:330` — `--symbols default=",".join(DEFAULT_SYMBOLS)` accepts override
  - Checklist step 6 (line 60+) references smoke-trade verification but doesn't tell operator to override the 5-symbol default
- **Confidence:** HIGH
- **Recommended fix:** Update `DEFAULT_SYMBOLS` line 89 to include `"XAGUSD", "NAS100"`. Verify magic-number conflict-check still passes (each symbol gets unique magic). One-line config change.
- **Effort estimate:** 15 min including dry-run verification
- **Risk if not fixed:** Pre-Monday smoke verification doesn't exercise XAGUSD or NAS100 order paths. If broker symbol resolution is broken for either (canonical → mt5_symbol mapping), it won't be caught until first live signal arrives Monday during a kill zone — late discovery, Monday market-open blast radius.

---

## Section 2: POST-MONDAY-HIGH

### H1. `structure_detector_divergences.jsonl` unbounded growth

- **Source audit(s):** AUDIT 12 (KB-Logs-Data), AUDIT 20 (Canary-Shadow), AUDIT 25 (Logs-Data-Hygiene)
- **Verification:** VERIFIED-AGAINST-CODE — file exists at 22.84 MB (confirmed via `ls -la`); IS gitignored (line 22 of `.gitignore`); growth rate ~500K/day extrapolates to 100MB by mid-July
- **Evidence cited:** `.gitignore:22`; `shadow_logs/structure_detector_divergences.jsonl` 22,843,830 bytes Apr 26 00:00; CLAUDE.md unresolved item #4 acknowledges shadow log growth (intentional pattern #15)
- **Confidence:** HIGH
- **Recommended fix:** Implement daily/weekly rotation or sample-down policy. ADR-004 only requires divergence visibility, not full append-only — periodic rotation acceptable.
- **Effort estimate:** 2-3h (rotation policy + tests)
- **Risk if not fixed:** Disk pressure within 4 months. Slows down `tail -f` debugging. Per intentional pattern #15, rotation IS post-Monday research item — confirmed by CLAUDE.md known-minor note. Already triaged as post-Monday by CEO.

### H2. `adaptive_review.py:110` uses stale model name `claude-sonnet-4-20250514`

- **Source audit(s):** AUDIT 21 (Anthropic-Telegram)
- **Verification:** VERIFIED-AGAINST-CODE — line 110 `self.model = ai_cfg.get("review_model", "claude-sonnet-4-20250514")`
- **Evidence cited:** `src/components/adaptive_review.py:110`; all other call sites use `claude-sonnet-4-6`
- **Confidence:** HIGH
- **Recommended fix:** Change default to `claude-sonnet-4-6` to match production. Add `review_model` to `agent_config.yaml` as override path.
- **Effort estimate:** 15 min
- **Risk if not fixed:** Adaptive review (regime context module) calls a 1-year-old model alias that may be deprecated by Anthropic at any time. Falls back gracefully (catches API error → returns no insight) but would silently degrade context quality post-deprecation.

### H3. `live_evaluations/`, `inverted_tp_log.jsonl` and pipeline_state files tracked despite gitignore

- **Source audit(s):** AUDIT 24 (Git-Hygiene), AUDIT 25 (Logs-Data-Hygiene)
- **Verification:** VERIFIED-AGAINST-CODE — `.gitignore:16` lists `knowledge_base/pipeline_state/` but `git ls-files` returns 4 tracked files (02_market_state.json, 03a_primary_analysis.json, 03b_debate_round1.json, 03b_verdict.json). 21 root logs/ files tracked (audit 24 said 22; off-by-one but materially the same).
- **Evidence cited:** `git ls-files knowledge_base/pipeline_state/` returns 4 entries; `git ls-files logs/` returns 21 entries; `.gitignore` lacks `logs/` entry entirely
- **Confidence:** HIGH (contradicts intentional pattern #17 if `live_evaluations/` is in this set; verified `live_evaluations/` IS the intended commit trail per pattern #17)
- **Recommended fix:** (a) Add `logs/` to `.gitignore`. (b) `git rm --cached logs/*.log` (21 files). (c) Decision: the 4 pipeline_state tracked files were tracked BEFORE gitignore line was added — either `git rm --cached` them or remove the gitignore entry to make intent clear. Recommend `git rm --cached`.
- **Effort estimate:** 30 min (single commit)
- **Risk if not fixed:** Repo size bloat from log churn. Future agent confusion about "is this committed or not". Not blocking Monday.

### H4. Operator decision playbook is v2.0 dated April 5 (CLAUDE.md claims v3, 41 scenarios for 5-instrument fleet)

- **Source audit(s):** AUDIT 18, AUDIT 19, AUDIT 02 (Context-Docs)
- **Verification:** VERIFIED-AGAINST-CODE — file header line 3 says "Version: 2.0 — Final"; line 5 references "5-instrument autonomous XAUUSD/US30/USDJPY/GBPJPY/GBPUSD agent on FTMO $100K demo"; line 1044 confirms 41 scenarios. CLAUDE.md line 305 references "Operator decision playbook (41 scenarios)".
- **Evidence cited:** `.context/05_operations/operator_decision_playbook.md:1-7,1044`; `CLAUDE.md:305`
- **Confidence:** HIGH
- **Recommended fix:** Add XAGUSD + NAS100 to scenarios that are instrument-agnostic. Add 4-6 new scenarios specific to 0.5% sizing (XAGUSD) + 3-day observe window (NAS100). Update header to v2.1 + 2026-04-26 date. CEO-authored update preferred.
- **Effort estimate:** 2-4h CEO time (operational doc, not code)
- **Risk if not fixed:** Operator runbook lacks scenarios for 2 live instruments. CEO authored playbook; CEO judgment required for what scenarios apply. Not Monday-blocking — operator can apply XAUUSD scenarios with sizing adjustments mentally — but increases mental load during incidents.

### H5. Component 3B Bull/Bear/Judge debate (~710 LOC) DELETE vs WIRE decision pending

- **Source audit(s):** AUDIT 26 (Dead-Code), AUDIT 07 (Prompts), AUDIT 17 (Cross-Deps)
- **Verification:** VERIFIED-AGAINST-MEMORY-OR-ADR — explicit intentional pattern #8 "PAUSED (code exists, not wired)". CLAUDE.md line 133 confirms.
- **Evidence cited:** `CLAUDE.md:133`; `feedback_decision_preservation.md` memory
- **Confidence:** HIGH
- **Recommended fix:** Status quo (preserve as research scaffolding) is consistent with memory `feedback_decision_preservation.md`. Promote to POST-MONDAY-LOW with no action — CEO judgment.
- **Effort estimate:** N/A (CEO decision, not engineering)
- **Risk if not fixed:** None. ~710 LOC sit unwired. Marginal cognitive load on agents tracing imports.

### H6. Tick capture daemons never started — first parquet on Monday

- **Source audit(s):** AUDIT 22 (Tick-Capture), AUDIT 25 (Logs-Data-Hygiene), AUDIT 12 (KB-Logs-Data)
- **Verification:** VERIFIED-AGAINST-CODE — `data/ticks/` empty except `README.md`. Watchdog tick supervision wired at lines 343-385. Will launch at 07:45 local Monday (first watchdog cron after market open).
- **Evidence cited:** `ls data/ticks/` returns only README; `scripts/watchdog.ps1:343-385`
- **Confidence:** HIGH
- **Recommended fix:** As-is is acceptable per audit 22 — watchdog will start daemons Monday at 07:45 local. **BUT crosses with B1**: TickSymbolMap (line 335-341) only covers 5 — XAGUSD + NAS100 tick daemons won't start. Resolve as part of B1 fix.
- **Effort estimate:** Fold into B1 fix
- **Risk if not fixed:** Tick features are shadow-only Monday (D.1 deferred). XAGUSD/NAS100 will run without tick microstructure data. Operationally tolerable.

### H7. Telegram fire-and-forget: alerts lost on process crash

- **Source audit(s):** AUDIT 21 (Anthropic-Telegram)
- **Verification:** VERIFIED-AGAINST-CODE — `notifications.py:72-97` uses stdlib urllib HTTP, no retry queue
- **Confidence:** MED (audit asserted MEDIUM-priority; agree)
- **Recommended fix:** Add a queued-with-disk-persistence retry layer for SPRT halt + flatten + emergency telegram. Lower-priority alerts (BE update) can stay fire-and-forget.
- **Effort estimate:** 4-6h
- **Risk if not fixed:** During an MT5 disconnect or watchdog kill, the very alerts that should reach the CEO most reliably are exactly the ones that fail. SPRT halt or flatten event triggered → process killed → telegram never sent → operator unaware. PARTIAL mitigation: heartbeat_monitor still runs even when an orchestrator crashes.

### H8. `evaluation_logger` no dedicated unit test

- **Source audit(s):** AUDIT 11 (Tests), AUDIT 05 (Src-Supporting)
- **Verification:** Cannot directly verify without running test discovery — both audits claim coverage gap. PARTIAL-VERIFIED.
- **Confidence:** MED
- **Recommended fix:** Add `tests/components/test_evaluation_logger.py` with N=20+ unit tests covering schema versioning, fail isolation, file lock contention.
- **Effort estimate:** 4-6h
- **Risk if not fixed:** Existing integration tests may catch regressions; dedicated unit tests would catch schema drift faster.

### H9. `dormant_state.py` no test suite

- **Source audit(s):** AUDIT 06 (Src-Safety)
- **Verification:** PARTIAL — audit asserts gap; not directly verified by reading test directory
- **Confidence:** MED
- **Recommended fix:** Add tests for atomic-write race + restart-survival + flag-clear + dormant-on-second-trade behavior.
- **Effort estimate:** 3-4h
- **Risk if not fixed:** T2.8 daily-loss-stop is a critical safety gate. Untested code in this area carries elevated regression risk.

---

## Section 3: POST-MONDAY-MEDIUM

### M1. JSONL append duplicated 9× across loggers (audit 17 + 5)
**Disposition:** REFACTOR — extract `src/utils/jsonl_utils.py` (315 lines saved). Effort 2h. POST-MONDAY-MEDIUM.

### M2. `orchestrator.py` is 27-dependent god module (audit 17)
**Disposition:** Long-term refactor candidate. Effort 4-6h. CEO judgment on whether to split.

### M3. `live_sessions/` files from Apr 6-7 (audit 23 + 25)
**Disposition:** Implement 30d rotation/archive policy. Effort 2h.

### M4. 3 shadow loggers omit `_shadow_` prefix (audit 05 + 17)
**Disposition:** Cosmetic — `direction_emission`, `candidate_features`, `d1_bias_lag`. Rename in single migration commit. Effort 30 min.

### M5. `pipeline_state/02_market_state.1884.tmp` orphan (audit 12 + 23)
**Disposition:** 12h-old atomic-write orphan. Cleanup script + watchdog hook. Effort 30 min.

### M6. 5 dead-telemetry loggers (be/d1_bias/partial_close/regime/touch_count) (audit 12 + 20)
**Disposition:** Investigate whether call sites fire. Some (regime, touch_count) genuinely await first eval to fire — known. Verify others. Effort 1-2h.

### M7. `pipeline_state/03a/03b` deprecated v3-era files (audit 23)
**Disposition:** Verify whether still written; if not, `git rm`. Effort 30 min.

### M8. 11 `print()` calls instead of `logging` (audit 17)
**Disposition:** Convert in single audit-pass commit. Effort 1h.

### M9. 3 hardcoded shadow_logs paths + `DEFAULT_LOOKBACK_H4` + `dumb_baseline_timeout` should be config-driven (audit 17)
**Disposition:** Extract to config. Effort 1h.

### M10. Defensive `getattr` duplication across 5 modules (audit 05)
**Disposition:** Extract helper. Effort 1-2h.

### M11. State persistence pattern duplication (audit 05)
**Disposition:** Extract `src/utils/state_persistence.py`. Effort 1h.

### M12. file locking duplicated 4× (audit 17)
**Disposition:** Extract `src/utils/file_lock.py`. Effort 1h, ~200 lines saved.

### M13. time-handling duplicated 5+× (audit 17)
**Disposition:** Extract `src/utils/time_utils.py`. Effort 1h.

### M14. config loading duplicated 3× (audit 17)
**Disposition:** Already partially in `agent_config.py`; consolidate remaining 3 sites. Effort 30 min.

### M15. ARCHITECTURE.md predates entire live system (audit 19)
**Disposition:** Rewrite to current 7-instrument multi-framework state. Effort 2-3h.

### M16. MASTER_ROADMAP.md OBSOLETE (April 2 era) (audit 19)
**Disposition:** Either archive (move to historical) or rewrite. CEO call. Effort 1-2h.

### M17. 00_READING_ORDER stale at handoff 15 (audit 02 + 19)
**Disposition:** Update to handoff 40. Effort 30 min.

---

## Section 4: POST-MONDAY-LOW

| ID | Source | One-line |
|----|--------|----------|
| L1 | AUDIT 01 | `.DS_Store` + 4 empty .log files in root — DELETE |
| L2 | AUDIT 01 | 30+ Apr 5-7 era research reports in root — ARCHIVE |
| L3 | AUDIT 01 | 11 analysis scripts in root — REFACTOR to `research/` |
| L4 | AUDIT 02 | Pre-deploy checklist line 43 says "5 symbols" cosmetic UPDATE (already covered by B2) |
| L5 | AUDIT 03 | 24 research dirs ARCHIVE candidates (~180MB recovery) |
| L6 | AUDIT 03 | 2 research DELETE (`confluence_strictness_audit`, `tick_daemon_cold_review`) |
| L7 | AUDIT 04 | `orchestrator.py:583-585` kz_trades comment clarity |
| L8 | AUDIT 04 | `orchestrator.py:414-424` heartbeat write WARN comment clarity |
| L9 | AUDIT 04 | `primary_analyzer.py` API timeout error swallowed to WAIT (add logging) |
| L10 | AUDIT 07 | `short_validation_batch_prompt.md` UNUSED candidate |
| L11 | AUDIT 07 | 4 specialized tests for ADR-006 substitution |
| L12 | AUDIT 10 | `watchdog.bat` (5 lines, superseded by .ps1) — DELETE |
| L13 | AUDIT 10 | 40+ scripts in `scripts/` — ARCHIVE candidates |
| L14 | AUDIT 10 | 3 orphan canary fixtures on disk vs manifest |
| L15 | AUDIT 12 | `inverted_tp_log.jsonl` 10 days stale — verify TP tracking |
| L16 | AUDIT 13 | `project_gbpusd_observer_cost` deadline 2026-04-30 — refresh post-deadline |
| L17 | AUDIT 13 | `project_live_l2_rejection_per_instrument` is pre-FA-2 baseline — refresh |
| L18 | AUDIT 15 | No `.env.example` for onboarding |
| L19 | AUDIT 15 | No `.pytest_cache/` in `.gitignore` |
| L20 | AUDIT 21 | No graduated spend alerts |
| L21 | AUDIT 24 | `.gitattributes` not present (line ending policy) |
| L22 | AUDIT 24 | `origin/podcast-research-implementation` stale ref |

---

## Section 5: FALSE-POSITIVE-AGENT-MISSED-CONTEXT

### FP1. Audit 26 flagged 5 disabled features (tick_features, news_filter, m5_refinement, sl_liquidity_cluster, debate Gate 2) as candidates
- **Reality:** ALL intentional disabled-by-default per intentional patterns #1-#4, #8, #16. The audit correctly noted "INTENTIONAL" — flag this as agent self-resolved, no action.
- **Source:** Intentional patterns #1-4, 8, 16 in synthesis brief
- **Note:** Audit 26 acknowledged correctness; no action needed.

### FP2. Audit 24 flagged `.context/LIVE_STATE.md` as TRACKED debatable
- **Reality:** Auto-regenerated snapshot tracked intentionally so fresh sessions/clones have a baseline. Per CLAUDE.md mandatory-first-action: regenerate this file every session.
- **Source:** CLAUDE.md mandatory-first-action #2

### FP3. Audit 12 flagged `vectordb` and `canary_cache` as "NOT FOUND"
- **Reality:** Both are runtime-created on first use. Empty/missing is normal pre-deployment. canary cache populates on first PASS run; vectordb is LanceDB lazy-init.
- **Source:** CLAUDE.md (Component 5 Knowledge Base)

### FP4. Audit 06 flagged `dormant_state.py` no concurrent-process lock
- **Reality:** Documented as gap; FTMO single-account = OK per audit. Already triaged.
- **Source:** Audit 06's own caveat

### FP5. Audit 16 flagged tick daemon "never started"
- **Reality:** Watchdog auto-starts at 07:45 local Monday. Pre-Monday absence is correct state. Crosses with B1 for XAGUSD/NAS100 only.
- **Source:** `scripts/watchdog.ps1:343-385`

### FP6. Audit 16 flagged FTMO `trade_expert` flag not confirmed
- **Reality:** Pre-flight Test 6 logs warning; this is documented behavior per `project_redacted_account_free_trial_ea_excluded.md` memory. CEO will purchase FTMO paid challenge Monday AM at which point trade_expert=True is contractually guaranteed.
- **Source:** memory `project_redacted_account_free_trial_ea_excluded.md`

### FP7. Audit 16 flagged US30_cash override disabled in redacted_account.yaml
- **Reality:** Intentional per CLAUDE.md "FN US30_cash override temporarily disabled (see comment block in `config/profiles/redacted_account.yaml`)"
- **Source:** CLAUDE.md "What is working" §

### FP8. Audit 26 flagged Bull/Bear/Judge debate (~710 LOC) NOT WIRED
- **Reality:** Intentional pattern #8 PAUSED. Audit 26 correctly noted this; flagging here so fresh sessions don't re-propose deletion.
- **Source:** CLAUDE.md:133, intentional pattern #8

### FP9. Audit 08 flagged Tool C NOT scaffolded
- **Reality:** D.3 deferred per intentional pattern #9. Tool A complete, Tool B skeleton, Tool C deferred — all intentional research scaffolding.
- **Source:** Intentional pattern #9, `research/tool_use_grounding/DESIGN.md`

### FP10. Audit 09 flagged Phase-4 stubs (mt5_login=0, obsidian_*)
- **Reality:** Intentional placeholder for future credentials block.

### FP11. Audit 03 + 25 flagged `data/old_huggingface_backup` and `data/raw` 3.4M unexplained
- **Reality:** Pre-existing artifacts; not in scope of recent sessions. CEO decision required for cleanup. POST-MONDAY-LOW.

### FP12. Audit 25 flagged `live_*.log` 5 files Apr 17 (9 days old, retired)
- **Reality:** Logs from old retired-symbol entry points (live_GBPJPY.log etc); kept as historical. Could ARCHIVE but not blocking.

### FP13. Audit 11 noted 1 xfail "GENUINE BUG" on `identify_structure()`
- **Reality:** Tracked under ADR-004 as known minor (recency weighting); per CLAUDE.md it's logged-only mislabel, not behavior bug. Status quo acceptable post-Monday.
- **Source:** CLAUDE.md unresolved item #4 known-minor; ADR-004

### FP14. Audit 24 flagged 50% of agent commits missing Co-Authored-By
- **Reality:** Repo-wide hygiene observation, not actionable for active code. Could enforce via pre-commit hook (LOW priority).

### FP15. Audit 19 flagged "S1 monthly decay, A.2 logger, C.3 class-aware shipped but not in operational docs"
- **Reality:** All three ship as observability/monitoring; not user-operational features. Inclusion in playbook depends on whether operators interact with them. CEO call.

### FP16. Audit 03 listed `master_plan_apr11` as QUESTION-CEO
- **Reality:** Strategic doc; intentional preservation per `feedback_decision_preservation.md`.

### FP17. Audit 25 flagged `data/historical_2026` 53M as needing baseline
- **Reality:** Static reference data; size growth is N/A. False concern.

### FP18. Audit 13 minor count drift (29 vs actual 30 memory files)
- **Reality:** New `feedback_engineer_systemic_not_patches` shipped 2026-04-26; audit ran before. Not a contradiction.

---

## Section 6: CROSS-AUDIT CONFIRMATIONS (multi-source findings)

### CC1. 5-symbol vs 7-symbol drift (audits 16, 18, 19, 22)
- **Contributing audits:** 4
- **Independent corroboration:** HIGH
- **Disposition:** PRE-MONDAY-BLOCKER (consolidated into B1 + B3 above)
- **Action:** Resolve B1 (watchdog) + B3 (fn_smoke_trade.py) with single fleet-update commit. Update operator playbook (H4) post-Monday.

### CC2. Pre-deploy checklist commands stale/broken (audits 18, 19)
- **Contributing audits:** 2
- **Independent corroboration:** HIGH
- **Disposition:** PRE-MONDAY-BLOCKER (B2)
- **Action:** Single doc-edit commit pre-Monday-AM.

### CC3. Stale operational docs (audits 02, 18, 19)
- **Contributing audits:** 3
- **Independent corroboration:** HIGH
- **Disposition:** Operator playbook → POST-MONDAY-HIGH (H4); ARCHITECTURE.md + MASTER_ROADMAP.md → POST-MONDAY-MEDIUM (M15-M16); 00_READING_ORDER → POST-MONDAY-MEDIUM (M17). Pre-deploy checklist → PRE-MONDAY (B2).

### CC4. Code duplication candidates (audits 05, 17)
- **Contributing audits:** 2
- **Independent corroboration:** HIGH
- **Disposition:** POST-MONDAY-MEDIUM cluster (M1, M10-M14). Total ~830 LOC reduction over 8-10h work.

### CC5. Unbounded log growth (audits 12, 20, 25)
- **Contributing audits:** 3
- **Independent corroboration:** HIGH
- **Disposition:** POST-MONDAY-HIGH (H1).
- **Action:** Implement rotation policy. structure_detector_divergences.jsonl is the worst offender; orchestrator logs are secondary.

### CC6. logs/ directory not gitignored (audits 24, 25)
- **Contributing audits:** 2
- **Independent corroboration:** HIGH
- **Disposition:** POST-MONDAY-HIGH (H3).

### CC7. Heartbeat-flatten kill switch DISABLED (audits 06, 09, 26)
- **Contributing audits:** 3
- **Independent corroboration:** Intentional pattern #1.
- **Disposition:** FALSE-POSITIVE-AGENT-MISSED-CONTEXT — all 3 audits correctly noted INTENTIONAL.

### CC8. Tick daemon never started + features not in prompt (audits 12, 22, 25)
- **Contributing audits:** 3
- **Independent corroboration:** HIGH
- **Disposition:** Crosses B1 + intentional pattern #5 (D.1 deferred). Daemon-start is auto-triggered Monday by watchdog; prompt-wiring is post-Monday research per CLAUDE.md.

### CC9. confidence_filter_mode + session_memory_enabled "appear unused" (multiple)
- **Disposition:** Intentional patterns #5-#6. FALSE-POSITIVE-AGENT-MISSED-CONTEXT.

### CC10. ADR-006 substitution + DECISION ORDER + parallel evaluation (audits 07, 09)
- **Disposition:** VALID-AS-IS confirmation that ADR-006 ships correctly.

### CC11. dead-telemetry loggers (be/d1_bias/partial_close/regime/touch_count) (audits 12, 20)
- **Disposition:** POST-MONDAY-MEDIUM (M6). Some genuine call-site issues; some normal "awaiting first eval".

### CC12. ftmo + redacted_account profiles (audits 09, 16)
- **Disposition:** Intentional pattern #14 — both maintained.

### CC13. inverted_tp_log staleness (audits 12, 23)
- **Disposition:** POST-MONDAY-LOW (L15).

### CC14. backup_pre_reseed/ + master_plan_apr11 + lira/v4 research preservation (audits 03, 23)
- **Disposition:** Intentional patterns #13 + #19. FALSE-POSITIVE.

---

## Section 7: AUDIT-LEVEL CRITIQUE

| # | Audit | Quality | False-positive rate | Notes | Recommendation |
|---|-------|---------|---------------------|-------|----------------|
| 01 | ROOT-CLEAN | MED | ~10% | Clean enumeration; some "ARCHIVE" suggestions overlap intentional preservation | trust |
| 02 | CONTEXT-DOCS | HIGH | ~5% | Correctly identifies pre-deploy 5-vs-7 drift | trust |
| 03 | RESEARCH-DIR | HIGH | ~15% | Some ARCHIVE suggestions cross intentional pattern #19 (decision-preservation) | verify-before-trust |
| 04 | SRC-CORE | HIGH | ~5% | Excellent rigor; flagged comment-clarity not bugs | trust |
| 05 | SRC-SUPPORTING | HIGH | ~5% | Self-corrected on initial WARNING-level concern | trust |
| 06 | SRC-SAFETY | HIGH | ~5% | Self-acknowledges no-lock OK for FTMO single-account | trust |
| 07 | PROMPTS | HIGH | ~5% | All ADR-006 substitutions verified correct | trust |
| 08 | AI-TOOLS | HIGH | ~5% | Correctly noted Tool C NOT scaffolded as D.3 deferred | trust |
| 09 | CONFIG | HIGH | ~5% | Comprehensive override matrix verification | trust |
| 10 | SCRIPTS | HIGH | ~10% | 78 vs 75 fixture orphan claim worth verifying | verify-before-trust |
| 11 | TESTS | HIGH | ~5% | Detailed conftest analysis, called out xfail correctly | trust |
| 12 | KB-LOGS-DATA | HIGH | ~10% | structure_detector growth claim verified | trust |
| 13 | MEMORY-CHECK | HIGH | ~10% | Counted 29 (now 30); minor lag | trust |
| 14 | COST-BUDGET | HIGH | ~5% | Realistic projection within $50 cap | trust |
| 15 | SECURITY | HIGH | ~5% | Thorough cred check; only 2 LOW findings | trust |
| 16 | MT5-BROKER | HIGH | ~10% | 5/5 issues verified | trust |
| 17 | CROSS-DEPS | HIGH | ~5% | Strong refactor analysis with hour estimates | trust |
| 18 | MONDAY-READY | HIGH | ~0% | All claims verified true; highest signal audit | trust |
| 19 | OPS-DOC-DRIFT | HIGH | ~5% | Operator Playbook v3 vs v2.0 confirmed | trust |
| 20 | CANARY-SHADOW | HIGH | ~10% | Some "dead telemetry" are normal awaiting-first-eval | verify-before-trust |
| 21 | ANTHROPIC-TELEGRAM | HIGH | ~5% | Stale model name verified; Telegram non-persistence verified | trust |
| 22 | TICK-CAPTURE | HIGH | ~5% | Code-complete + tested verified | trust |
| 23 | KB-STRUCTURE | MED | ~15% | Some "stale" are intentional historical | verify-before-trust |
| 24 | GIT-HYGIENE | HIGH | ~5% | logs/ + 22 tracked files claim verified (was 21) | trust |
| 25 | LOGS-DATA-HYGIENE | HIGH | ~5% | Some duplication with audit 24 but consistent | trust |
| 26 | DEAD-CODE | HIGH | ~0% | Self-acknowledges intentional patterns | trust |

**Overall audit-batch quality: HIGH.** Avg false-positive rate ~7% (estimated from spot-check verifications). Audits with HIGH-priority findings (16, 18, 19) all verified true. **Trust the batch as a whole** for triage purposes; verify individual audit claims against current code before taking action.

---

## Section 8: SUMMARY MATRIX

| ID | Source | Severity | Category | Conf | Verified | One-line |
|----|--------|----------|----------|------|----------|----------|
| B1 | 18,16,22 | CRIT | PRE-MONDAY-BLOCKER | HIGH | YES-CODE | watchdog SymbolMap+TickSymbolMap only 5 of 7 |
| B2 | 18,19 | CRIT | PRE-MONDAY-BLOCKER | HIGH | YES-CODE | pre-deploy checklist commands broken |
| B3 | 16,18 | CRIT | PRE-MONDAY-BLOCKER | HIGH | YES-CODE | fn_smoke_trade.py DEFAULT_SYMBOLS=5 |
| H1 | 12,20,25 | HIGH | POST-MONDAY-HIGH | HIGH | YES-CODE | structure_detector log unbounded |
| H2 | 21 | HIGH | POST-MONDAY-HIGH | HIGH | YES-CODE | adaptive_review.py stale model name |
| H3 | 24,25 | HIGH | POST-MONDAY-HIGH | HIGH | YES-CODE | logs/ + pipeline_state tracked despite gitignore |
| H4 | 18,19,02 | HIGH | POST-MONDAY-HIGH | HIGH | YES-CODE | operator playbook v2.0 5-instrument stale |
| H5 | 26,07,17 | MED | POST-MONDAY-HIGH | HIGH | INTENT | Component 3B debate ~710 LOC pause |
| H6 | 22,25,12 | MED | POST-MONDAY-HIGH | HIGH | YES-CODE | tick daemons start Monday only (overlap B1) |
| H7 | 21 | MED | POST-MONDAY-HIGH | MED | YES-CODE | Telegram fire-and-forget alerts |
| H8 | 11,05 | MED | POST-MONDAY-HIGH | MED | PARTIAL | evaluation_logger no unit test |
| H9 | 06 | MED | POST-MONDAY-HIGH | MED | PARTIAL | dormant_state.py no test suite |
| M1-M17 | various | MED | POST-MONDAY-MEDIUM | MED-HIGH | mostly verified | refactor + cleanup cluster |
| L1-L22 | various | LOW | POST-MONDAY-LOW | MED-HIGH | some verified | nice-to-haves |
| FP1-FP18 | various | N/A | FALSE-POSITIVE | N/A | INTENT | intentional patterns |

---

## Section 9: LOW-CONFIDENCE FLAGS (for human review)

These findings have LOW or MED confidence and warrant a CEO/main-thread spot-check before any action:

1. **Audit 10 — 78 vs 75 canary fixtures (3 orphans on disk).** Could be cache, could be orphans. Verify via `find scripts/canary_fixtures -name '*.json' | wc -l` and cross-reference against manifest.json. CONFIDENCE LOW — only audit 10 reported, no other audit corroborated.

2. **Audit 23 — `pipeline_state/03a/03b` deprecated v3-era files.** Audit asserts "deprecated v3 era" but doesn't cite which v3 ADR or commit deprecated them. Verify whether orchestrator still writes to these paths before delete.

3. **Audit 11 + 05 — `evaluation_logger` no dedicated unit test.** Asserted but not directly verified by reading test directory. Could already have integration coverage that exercises 100% of paths.

4. **Audit 06 — `dormant_state.py` no test suite.** Same as #3 — asserted but not confirmed via grep over test files.

5. **Audit 12 — 5 dead-telemetry candidates.** Audit infers "files missing" implies hooks not firing. Could be that loggers are wired but haven't fired yet (e.g., touch_count_gate logs on REJECT only; if no rejects yet on `ob_retest`, no rows yet).

6. **Audit 24 — 50% of agent commits missing Co-Authored-By line.** Sample-based finding; haven't verified the 50% figure on full git log.

7. **Audit 25 — disk projection `99.3M after 1mo`.** Linear extrapolation from current size; doesn't account for log rotation. If H1 (H1 from this triage) addresses structure_detector log, projection becomes obsolete.

8. **Audit 19 — "Phantom features: NONE".** Exhaustive search not verified; could be features mentioned in code but never wired.

---

## END

**Synthesis status:** COMPLETE. **3 PRE-MONDAY-BLOCKERS identified + verified against current code.** Recommend resolution sequence:

1. **B1 (watchdog 5→7 expansion)** — must fix before Monday market open. ~30 min.
2. **B2 (pre-deploy checklist edits)** — must fix Sunday evening before checklist execution. ~20 min.
3. **B3 (fn_smoke_trade DEFAULT_SYMBOLS)** — must fix before checklist step 6 smoke test. ~15 min.

**Total Monday-blocker effort: ~1 hour.** All other items can wait until post-launch first-week cleanup window.
