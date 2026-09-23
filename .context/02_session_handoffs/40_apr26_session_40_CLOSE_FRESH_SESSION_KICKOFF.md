# Session 40 CLOSE — Fresh Session Kickoff Handoff

**Created:** 2026-04-26 (Sunday, weekend sprint close)
**Status:** Closes session 40. Next session opens against Monday FTMO challenge launch + deferred-changes pursuit.
**Companion document:** `.context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md` — comprehensive deferred-list (read this AFTER LIVE_STATE.md).

---

## 1. What this session accomplished (durable summary)

### Code shipped to main
| Commit | What | Impact |
|---|---|---|
| `1340f56` | `fvg_fill` framework activated | New POI source, 6 borderline canary fixtures |
| `64d05b8` | `breaker_re_entry` framework activated | New POI source, 9 borderline canary fixtures + L2 check |
| `68f7a4b` | Pre-AI gate broadened to multi-framework | Skip AI when ALL enabled frameworks have 0 POIs |
| `daabff8` | KEEP touch-count at 2 (A19 verdict) | LOOSEN_TO_3 rejected, threshold parameterized |
| `222b69f` | Canary timeout 360 → 420 (75 fixtures) | Subprocess wallclock buffer |
| `573ce3c` | Staging→main canary regression PASS | Pre-merge gate |
| `d1b863c` | Canary baseline regen post-merge | 32/32 baseline + 42/43 borderline |
| `f5c1030` / `fba3875` | ADR-005 touch-count gate logger | PASS+REJECT logged from Mon onward |
| `cd662a9` / `1b2d4e8` | Dumb-momentum-baseline live shadow logger | Empirical AI-vs-mechanical comparison |
| `f1654f3` | Tick capture daemon (vision Layer 1) | Microstructure features extracted, NOT wired |
| `9b593d5` / `beba16e` | Regime classifier V1 (shadow-only) | H4-swing 4-class observational |
| `edd5b4e` / `24139a0` | Cross-instrument correlation gate | Halve-then-reject on multi-position correlation |
| `4850fba` / `6d70e00` | Correlation matrix refresh (current 2026 6mo data) | Closes Monday-blocker |
| `45fc046` | CLAUDE.md staleness audit batch | High+medium severity fixes |
| `d614c54` | Phantom REPORT.md files committed | REVIEWER_PASS.md + dumb_baseline/REPORT.md |
| `d2a31d0` | XAGUSD live (0.5%) + NAS100 live-OBSERVE (0.25%) | 7-instrument fleet, FTMO 1% FX overrides |
| `2cac8f5` | Weekend research artifacts committed | 314 files, 11 research dirs + WEEKEND_FINAL_REVIEW |

**HEAD now at `2cac8f5`** (post-doc-cleanup). Sunday config commit pending: v2_shadow → v2 promotion per `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md`.

### Research findings (full detail in `40_apr26_DEFERRED_CHANGES_MASTER.md`)
- **Per-class adapter agent (HIGH confidence):** Class-bias confirmed. Metals +5.8pp, JPY +7.4pp, indices -2.5pp, tight-FX -30.8pp AI uplift. Smoking gun: XAU-anchored cross-instrument block at `src/prompts/primary_analyzer_prompt.py:1252-1270`.
- **Pre-AI gate optimization agent (KEEP-AS-IS):** All 14 tightening variants fail ≤0.5R/mo ceiling. Surprise: G0_MULTI is OVER-skipping (~6R/Q1 missed). Cost framing corrected — fleet $57/mo well under $50-60 cap.
- **Rejected setups mining agent (KEEP-AS-IS):** Most rejections correct. Top miss patterns: BLOCKED_LIMIT cap saturation +40R/mo BT, live `sl_beyond_ob` over-rejection +43R/mo (n=35 too thin). Confirmed-correct rejections: `no_qualifying_h1_poi` (-63.5R), BT `h1_poi_exists` L2 (-49.8R), `prescreen_no_direction` (4,528 rows blind-direction loses).
- **Doc cleanup agent:** 314 files committed in `2cac8f5`. CLAUDE.md staleness clean. 5 placeholder READMEs for non-persisted agent outputs. Cascade prompt LOST (recovered template stale → DROP-TUESDAY-PLAN).

### Decisions ratified
- Risk for Monday: 1.0% FX / 0.5% metals (XAUUSD + XAGUSD) / 0.25% NAS100 — confirmed by CEO over Risk-MC's 0.75% recommendation.
- v2 detector promotion: GO under LONG-WR-watch SPRT halt at <40% n=20 (CEO-approved Sunday afternoon).
- V4 prompt: SHELVED (60-fixture canary FAIL + DP1 -1R regression).
- LIRA prompt: SHELVED (12-slice fleet ExpR +0.094R vs V3 +0.333R).
- Cascade prompt: LOST + recovered template stale → DROP-TUESDAY-PLAN.
- Touch-count threshold: KEPT at 2 (A19 REJECTED LOOSEN_TO_3).
- 7-instrument fleet for Monday: XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD (observer), XAGUSD, NAS100 (3-day observe).
- Deferred from Monday: GER40, UK100, EURUSD (per Tier 2 backtest verdicts).

---

## 2. Honest expectancy + confidence numbers

### Edge confidence
- **HIGH** that an edge exists (5 Bonferroni-surviving findings, OB+17pp p=0.003).
- **MEDIUM-LOW** on edge magnitude post-Q2-decay (XAUUSD Mar 33%, Apr 10% n=10; H1-vs-H2 chi-square p=0.006).

### Monday FTMO Phase 1 expectations (8% target / 5% daily / 10% total DD)
| Scenario | P(pass 30d) | P(pass 90d) | P(blow up) | E(R/mo) |
|---|---|---|---|---|
| Optimistic (v2 holds, Adapter A ships) | 75-85% | 90-95% | 3-7% | +25R / +2.5% |
| Base case (v2 partial, decay continues mild) | 60-70% | 80-88% | 8-15% | +10-15R / +1-1.5% |
| Pessimistic (Apr-style decay continues) | 35-50% | 60-75% | 15-25% | +0-5R / 0-0.5% |

**My honest read:** ~70% P(Phase 1 pass in 30d), ~10% P(blow up). Closer to base than optimistic.

### What I'm NOT confident about
- v2 SHORT recovery magnitude in production (F3 backtest n=2 SHORTs WIN both, wide CI).
- Whether Apr XAUUSD WR=10% is regime-driven (will end) or AI-side (will persist until prompt fix). Dumb-momentum baseline showed Apr XAUUSD mechanical 50% WR — points AI-side.
- True fill rate of fvg_fill + breaker_re_entry frameworks live (BT had 0/2 of 217 fills; could be cosmetic OR backtest-window artifact).
- $/mo API cost staying under $50-60 cap with 7 instruments (current estimate $57/mo — close).

### What changes the math (in priority order)
1. **Adapter A** (XAU-anchor gate by |corr|): if validated and shipped → indices class-bias addressed → +2-5pp uplift. Could shift base→optimistic.
2. **v2 promotion** (Sunday-pending): if SHORT signal recovers → optimistic-case more likely.
3. **LONG-WR-watch SPRT halt** (already armed): caps tail-risk at <40% WR n=20 per instrument.
4. **7-instrument diversification:** dilutes single-instrument decay.

---

## 3. Outstanding state at session close

### Sunday-still-pending (per pre-deploy checklist)
- [ ] v2_shadow → v2 config commit on `config/agent_config.yaml` (`market_state.detector_version`)
- [ ] Smoke trade verification (task #30) — run `scripts/fn_smoke_trade.py`
- [ ] Monday morning rolling restart with v2 + new frameworks (task #31)

### Tasks still open in tracker
- #18 — Main-thread audit of label disagreements (low priority, post-Monday research)
- #30 — Sunday smoke trade verification
- #31 — Monday morning rolling restart
- #75 — This handoff (will close upon write)
- #76 — Update CLAUDE.md to surface deferred master (will close upon update)

### CLAUDE.md unresolved items still open
- Item #2 — Heartbeat kill switch live enablement (CEO call after observation window)
- Item #4 — v2 promotion (Sunday config commit pending, then closes)
- Item #6 — `skip_first_ny_candle` window-boundary bug (need 30d shadow data)
- Item #8 — Touch-count threshold flip (need 6w production data)

### Branches audit (zero unmerged work blocking Monday)
- All feature/fix branches squash-merged to main (0 commits ahead unmerged)
- `feat/tick-capture-daemon` shows 1 commit ahead — that's the pre-squash original (already in main as `f1654f3`)
- `staging-sunday-deploy-imported` + `staging/sunday-deploy` — no unique work, candidates for cleanup
- ~50 worktree-agent-* branches — completed-agent state, cleanup candidates (Group F.1 in deferred master)
- Research branches (`lira-*`, `v4-*`, `phase1-*`) — shelved, artifacts committed (Group F.2)

### Uncommitted runtime files (expected, leave alone)
- `logs/*.log` — live process append logs
- `shadow_logs/heartbeat_flatten_events.jsonl` — live shadow data
- `knowledge_base/pipeline_state/02_market_state.json` — runtime state
- `research/pre_ai_gate_optimization/analysis.json|analyze.py` — agent's working dir (touched during run)
- New `research/rejected_candidates_value_mining/{10,11,12,13}_*.py` + .jsonl/.csv — agent's outputs
- `.context/LIVE_STATE.md` — auto-regenerated each session (modified by `scripts/generate_live_state.py`)

---

## 4. Fresh session opening protocol

### Step 1: Standard session orientation
```bash
python scripts/generate_live_state.py
cat .context/LIVE_STATE.md
cat CLAUDE.md
```

### Step 2: Read this handoff and the deferred master
```bash
cat .context/02_session_handoffs/40_apr26_session_40_CLOSE_FRESH_SESSION_KICKOFF.md  # this file
cat .context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md  # the pursuit list
```

### Step 3: First decision point with CEO
Before dispatching any work, present:
1. The 20-item deferred list (Section 3 of deferred master)
2. The honest expectancy/confidence numbers (Section 2 of deferred master)
3. Recommended pursuit priority (Section 4 of deferred master)

Ask CEO:
- "Should I dispatch verification agents in parallel for all 20 items, or sequence by priority group (A first, B next, C/D/E later)?"
- "What's the budget ceiling for verification agents?" (~$15-25 if all 20 items get a verification agent at Opus-max)
- "Any item the CEO already wants killed without verification?"

### Step 4: Dispatch verification agents
Use the **Verification brief** field from each item in the deferred master. Each agent reads the cited artifacts + current code, returns: (a) is finding still valid? (b) is proposed change correct? (c) what risk? (d) expected R impact?

Run agents IN PARALLEL where possible. Council pattern (3-stage) only for B.1 (Adapter A) — that's the highest-leverage prompt change.

### Step 5: CEO triage after verification
Each item gets bucketed into SHIP / RESEARCH / REJECT. Ship items in dependency order. Update CLAUDE.md unresolved-list as items close.

---

## 5. Known traps for the fresh session

### Trap 1: Agents kill subprocesses on return
Per memory `feedback_long_running_subprocess_pattern.md` — long-running Python sims (>30 min) MUST be dispatched from main thread via `Bash run_in_background: true`, not from inside an agent. Tier 2 backtests this weekend lost 5 zombie agents because of this. The orchestrator pattern in `scripts/run_tier2_backtests.py` uses ThreadPoolExecutor inside main process — preserve that pattern.

### Trap 2: Walk-level evidence ≠ realized R
Per memory `feedback_walk_level_evidence_not_predictive.md` — Track A walk-level p=5e-16 on touch-count decay REVERSED under A1's realized-R per stratum. Don't ship gate/prompt changes on walk evidence alone — always join with `all_results.json` per-stratum outcomes.

### Trap 3: Research scripts don't auto-load .env
Per memory `project_research_scripts_missing_dotenv.md` — `simulate_t7_live_period.py` has no `load_dotenv()`. From Claude Code bash, prefix with `set -a && source .env && set +a` or add dotenv to the script.

### Trap 4: Canary timeout scales with fixture count
Per memory `feedback_canary_timeout_scales_with_fixture_count.md` — orchestrator boot canary has hardcoded `timeout=N`. Currently 420 for 75 fixtures. Re-benchmark on every fixture-count change.

### Trap 5: BT-vs-live disagreement is real
Rejected mining agent surfaced: `sl_beyond_ob` 94% non-fill in BT vs 46% non-fill in live. `m15_choch_exists` synthetic-ATR view +55R reverses to -13.3R under LIMIT-fill correction. Don't trust BT-only findings without live cross-check.

### Trap 6: Cascade prompt is LOST
`prompts/primary_analyzer_prompt_v3_cascade.py` source file does not exist anywhere in the repo, branches, stashes, or worktrees. Recovered template at `research/prompt_cascade_ab_test/RECOVERED_v3_cascade_template.py.txt` is STALE vs current 3-framework V3. If CEO asks for cascade UX → must re-draft, not restore.

### Trap 7: CLAUDE.md is at 36,940 chars (>30k target)
Per memory `feedback_claudemd_size_discipline.md` — every parallel agent dispatch inherits CLAUDE.md. Bloat tax × N parallel agents. Prune target is <30k. (Item A.4 in deferred master.)

---

## 6. Reference index

### Primary reading order for fresh session
1. `.context/LIVE_STATE.md` — current state authoritative
2. This file — what just shipped + what's deferred + how to pursue
3. `.context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md` — the pursuit list
4. `CLAUDE.md` — durable instructions
5. `research/WEEKEND_FINAL_REVIEW_2026-04-25.md` — weekend cross-validator summary
6. Cited artifacts in deferred master Section 5 (per-item)

### Pre-deploy checklist (Sunday-pending)
- `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md`

### Operator playbook
- `.context/05_operations/operator_decision_playbook_v3.md` (41 scenarios)

---

## 7. Final notes for the operator (CEO)

**Why I'm closing the session here:** context is heavy (compaction event happened mid-flow), and the deferred-list pursuit is too important to be done by an exhausted main thread. A fresh session can dispatch up to 20 verification agents in parallel without running into context constraints.

**What CEO should know going in:**
1. The 20-item deferred list is COMPREHENSIVE — every weekend agent finding that wasn't shipped is in there with effort/risk/impact + verification brief.
2. My expectancy/confidence numbers (Section 2 of deferred master) are MY numbers. Pressure-test them. Especially the "Pessimistic" scenario probability — I may be too optimistic at 35-50% P(pass 30d) given Apr XAUUSD 10% WR data.
3. The single highest-leverage Monday-shippable item is Adapter A. If cold-review tonight passes — ship it with the v2-promotion commit and you've materially improved indices class-bias for Monday.
4. The shadow loggers (A.1, A.2) are pure intel-gathering — $0 risk and they unlock decisions in 30 days. No reason not to ship.
5. The risk-policy items (C.7 cap saturation, C.6 sl_beyond_ob relax) have real R upside but live data accumulation is the bottleneck — be patient.

**Pre-Monday checklist for CEO (operator) after fresh session opens:**
- Confirm v2 config commit lands (CLAUDE.md item #4 → close)
- Confirm smoke-trade Sunday (task #30)
- Confirm rolling restart Monday morning (task #31) — `start_all.bat` now launches 7 instruments
- Watch for SPRT halts on XAUUSD LONG WR <40% in first 20 trades
- Watch for unexpected $/mo API spend ramp (cap risk)

Good luck with FTMO Phase 1.

---

*End of session 40 close handoff. Fresh session opens against this + the deferred master.*
