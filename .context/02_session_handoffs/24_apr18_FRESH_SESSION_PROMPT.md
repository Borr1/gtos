# Fresh Session Briefing — Session 25 (GTOS)

**Project:** Gold Traders Operating System (GTOS)
**Date context:** Going into session 25, after session 24 close (2026-04-18)
**Live system status:** 5 orchestrators running on FTMO $100K demo, redacted_account 1% risk profile active

---

## Mandatory reading (in order)

1. `CLAUDE.md` — project instructions (refreshed 2026-04-18 by session 24)
2. `.context/02_session_handoffs/23_apr17_task_C_canary_cache_handoff.md` — Task C context
3. `.context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md` — **latest close-out, read carefully**
4. `.context/06_decisions/001_task_a_ob_continuation_monitor_approach.md` — first ADR; models the structure for future ADRs
5. `.context/00_core/quick_reference_card.md` — live numbers
6. This file

---

## Where we are — sessions 22→24 arc

Sessions 21–24 followed a discipline: harden the observability and safety infrastructure *before* touching the core edge signal.

- **Session 21** — Root-caused Apr 16 XAUUSD silent crash = pytest contamination. Added conftest Layer 1+2 write guards (`fa93c35`, 470+ lines). Scrubbed 319 synthetic drawdown entries + 3 synthetic malformed responses.
- **Session 22** — Regenerated canary fixtures under T7 C-gate (`8a42afb`, 12 fresh fixtures + 249-line test file).
- **Session 23** — Shipped canary subprocess dedup cache (`0c26d25`). Cost: $6–75/day restart-sensitive → ~$12/mo flat. 6-component hash, PASS-only, fail-open preserved.
- **Session 24** — Shipped OB continuation rolling-50 monitor (`11dee1d`). Historical-rolling methodology per ADR 001. 69 new tests, full suite 1223→1292 pass. `small_sample` gate suppresses spurious alarms on thin windows (GBPUSD takes 148mo to fill rolling-50).

---

## State at session 24 close

- **HEAD:** `11dee1d` (OB continuation monitor) → most recent docs commit on top
- **Test suite:** 1292 pass / 8 fail / 1 skip — 8 failures pre-existing (`test_deployment_prep`, `test_orchestrator::TestNewDay::test_resets_state`, `test_security_framework::TestWF1Protection`)
- **Live system:** 5 orchestrators running; watchdog healthy
- **Pre-existing stashes:** 3 intact (`23c083f`, `86a23fb`, `d0bbefa`) — **DO NOT DISTURB**
- **Clean trees:** `src/`, `tests/`, `prompts/`, `config/` all clean
- **Monitor deliverable:** CLI-ready; NOT yet wired into watchdog/Task Scheduler — parked follow-up

### Session 24 post-script (2026-04-18 late)

After handoff 24 was written, two small items closed:

- **Watchdog window-flash fix:** Task Scheduler task `GTOS_Watchdog` (fires every 15 min) was showing a brief cmd/PowerShell console window each fire. Fixed via new `scripts/watchdog_launcher.vbs` wrapper (hidden-window). Task action changed from `watchdog.bat` → `wscript.exe watchdog_launcher.vbs`. `watchdog.bat` and `watchdog.ps1` untouched. Uncommitted — `scripts/watchdog_launcher.vbs` is new. Rollback: `schtasks //Change //TN "GTOS_Watchdog" //TR "C:\Users\MSI\Documents\ai-trading-agent\scripts\watchdog.bat"`.
- **GBPUSD observer-mode decision:** CEO decision 2026-04-18: **leave GBPUSD running full pipeline at ~$8–12/mo through end of April, revisit 2026-04-30.** Do NOT propose shutdown, local-only conversion, or other scope reduction before then unless the live system misbehaves. Saved to project memory (`project_gbpusd_observer_cost.md`).

---

## Your mission — present task options to CEO, then execute the one chosen

After the mandatory reading and verification pass, your first job is **NOT** to pick a task. It is to report verification findings and then lay out the viable next-step options for the CEO with honest trade-offs. The CEO selects; you then open an ADR (if approach forks exist), dispatch sub-agents, and supervise.

### Task options (order below is NOT a recommendation — all are viable)

#### Option 1 — Retest Geometry Study (deep research, observation-only)

**Question:** For every OB retest that CONTINUED — **how** did it continue? Where did price wick to before the bounce? Stayed inside OB or stabbed below? How deep in pips / H1 ATR? Is behavior drifting over time?

**Why it matters:** distinguishes two patterns with opposite P&L:
1. Liquidity-grab continuation (shallow wick, strong bounce) → hold the trade
2. Breakdown disguised as continuation (deep wick, weak bounce, eventual reversal) → tighter SL

SL buffer is currently 0.5 ATR past OB edge (handoff 19). If p95 MAE past edge is 0.3 ATR, we're leaving room on the table. If 0.8 ATR, we're getting wicked out prematurely. This study tells us which.

**Deliverable:** `scripts/ob_retest_geometry_study.py` (or under `research/`) emitting per-retest CSV with MAE pips / MAE ATR / penetration past OB edge / time-to-MAE / recovery speed / OB body size / symbol / session / date. Computes p50/p75/p90/p95 per symbol, rolling-median drift quarter-over-quarter, London/NY/Tokyo breakdown, and whether deeper wick predicts stronger continuation.

**Approach forks (pre-ADR 002 material):** retest definition (first-only vs all-in-48h), outcome filter (CONTINUED-only vs both), time horizon (12 M15 mirror-live vs longer), MAE normalization (pips vs ATR vs OB-body-size), session labeling (hardcoded UTC vs production `session_detector`).

**Cost:** ~1 session, no API. **Payoff:** feeds a future WF-1 SL-calibration decision (separate session).

**Out of scope:** any `src/components/` change, trading-logic change, live system touch, changes to `scripts/ob_continuation_monitor.py` / `scripts/ob_retest_comprehensive.py` / canary scripts.

---

#### Option 2 — XAUUSD 126-day silent-gap investigation (read-only data archaeology)

**Question:** Why did XAUUSD produce zero resolved OB retests from 2025-11-24 → 2026-03-30 (handoff 24 "Unresolved findings")?

**Hypotheses to test:** regime shift, over-aggressive mitigation logic in `market_state.py`, structural OB-frequency drop, or raw-data anomaly in `data/historical/XAUUSD`.

**Why it matters:** if the cause implicates live mitigation logic, this has direct WF-1 implications (we may be throwing out legitimate OBs). If it's regime, it informs monitoring cadence. If it's data, it affects Option 1's validity.

**Deliverable:** one write-up in `.context/03_analysis/` with root cause + recommended follow-up. Pure investigation.

**Cost:** ~half-session. **Payoff:** potentially unblocks edge-decay monitoring validity for gold specifically.

---

#### Option 3 — Watchdog cron wiring for OB continuation monitor (infra)

**What:** Add `scripts/ob_continuation_monitor.py --daily` to scheduled fire (Windows Task Scheduler, daily at 01:00 UTC or similar). Confirm daily CSV rows accrete in `shadow_logs/ob_continuation_daily.csv` in production. Add Telegram alarm on <60% (respecting `insufficient_sample` gate).

**Why it matters:** without this, the session 24 monitor is CLI-runnable but nobody runs it. Observability without automation rots quickly.

**Cost:** ~1–2 hours. **Payoff:** closes the session 24 follow-up; the #1 edge-decay sentinel starts actually firing.

---

#### Option 4 — P3 instrument batch simulations (statistical validation)

**What:** Run T7 batch simulation on GBPJPY (~$25) and/or NAS100 (~$25) using `scripts/simulate_t7_live_period.py`. Handoff 15 says the script is ready; CEO decision has been pending.

**Why it matters:** our confidence in T7 per-instrument comes mostly from XAUUSD (7 trades, n too small for conclusions). Broader instrument validation informs whether the prompt transfers or needs per-instrument tuning.

**Cost:** ~$25–50 API + 30–60 min/instrument runtime. **Payoff:** cross-instrument generalizability evidence.

---

#### Option 5 — P5 Approach C in-line OB resolver (WF-1 live-system change)

**What:** Implement the in-line OB retest resolver on `_log_ob_retest_event` in `src/components/orchestrator.py` (ADR 001 Approach C). Fixes the live event log's PENDING-never-resolved gap.

**Why this is different:** touches `src/components/orchestrator.py` → requires a WF-1 window + explicit CEO approval. Larger blast radius; more ceremony (ADR, sub-agent review, canary regen possibly, staged deploy).

**Cost:** ~2–3 sessions. **Payoff:** the live event log self-heals; removes need for session-24 historical-rolling workaround eventually.

---

#### Option 6 — Smaller parked items

- **Between-KZ pending-limit fix commit** (uncommitted from session 17; touches `src/components/orchestrator.py` → WF-1 approval needed)
- **sl_too_tight OB exception** (handoff 16 — blocking 4–5 trades/week, CEO decision pending)
- **GBPUSD XAUUSD macro override** (handoff 16 — T7 non-compliance, CEO decision pending)
- **Canary fixture refresh** (all 10 baseline NO_TRADE; need borderline canaries to catch prompt regressions)
- **CLAUDE.md "What is unresolved" prune** — some items resolved by sessions 19–24 but list not re-audited end-to-end

---

## BEFORE starting any task — Verification pass (MANDATORY)

1. **Test suite health:**
   ```bash
   python -m pytest tests/test_ob_continuation_monitor.py --tb=no -q   # expect 69 pass
   python -m pytest tests/ --tb=no -q                                  # expect 1292 pass / 8 fail / 1 skip
   ```

2. **Live-system spot check:**
   ```bash
   tail -20 logs/watchdog.log
   ls -la knowledge_base/meta/.orchestrator_*.lock
   ls -la knowledge_base/meta/canary_cache.json
   ```

3. **Verify Session 24 commits and stashes:**
   ```bash
   git log --oneline -5              # expect 11dee1d at or near HEAD
   git stash list                    # expect 3 stashes preserved
   git status --porcelain src/ tests/ prompts/ config/   # expect clean
   ```

Report findings to CEO. If anything is broken, fix it FIRST. No task execution until the verification pass is clean.

---

## Decision record requirement — ADR 002+

Per `.context/06_decisions/` convention (established session 24 — see ADR 001): before dispatching implementation, if the chosen task has **more than one viable approach**, create the next sequential ADR (`002_<slug>.md`) documenting:

- **Context & blocker** (if any)
- **Chosen approach** (with justification)
- **Rejected alternatives** (each with "why rejected for now" + "when to revisit" + revisit triggers)
- **Consequences** (accepted trade-offs + what's still covered)

This ADR commitment is **durable guidance from the CEO — applies to all approach-level forks going forward**, not just one task. It is NOT a status report; it is a design artifact that future sessions read when they ask "why did we go this way?"

If the chosen task has only one obvious approach (e.g., Option 3 watchdog wiring is mechanical), an ADR is not required — just note that in the handoff.

---

## Agent delegation pattern (CEO directive — CRITICAL)

Main thread stays strategic: briefing, reviewing, committing, writing ADRs. Delegate implementation / verification / review to Opus 4.7 subagents.

| Role | Agent type | Model | Isolation | Brief style |
|---|---|---|---|---|
| A1 — implementation | `general-purpose` | `opus` | `worktree` (recommended) | Full spec, guardrails, ADR reference, test plan, file paths, line numbers |
| A2 — cold reviewer | `general-purpose` | `opus` | none or `worktree` | Blank-slate adversarial; pytest evidence required; re-derive all numbers |
| A3 — statistical validation (optional) | `general-purpose` | `opus` | `worktree` | Sanity-check distributions against published Test A (n=219, p=0.003) where overlapping |

### Effort setting — known limitation

The `Agent` tool schema exposes `model` but NOT `effort`. Compensate:
- Long, specific briefs with `"think hard about X, Y, Z"` directives
- All required context provided upfront (no back-and-forth)
- Explicit success criteria and guardrails
- File paths AND line numbers, not vague descriptions

This pattern worked in sessions 23 (canary cache) and 24 (OB continuation monitor) — both produced high-quality, verifiable output.

---

## Guardrails (apply to every option)

1. **Observation-only is the default.** Options 1–4 are read-only research / infra. Only Option 5 (Approach C) and some items in Option 6 touch live trading logic — treat those as WF-1 changes requiring explicit CEO approval + sub-agent review before committing.
2. **Conftest write guards.** Tests MUST use `tmp_path` + module-ref monkeypatch. Never write to `knowledge_base/`, `shadow_logs/` (except the study's own dedicated output path), `pipeline_state/`, or `logs/` from tests. Canonical examples: `tests/test_ob_continuation_monitor.py`, `tests/test_canary_cache.py`, `tests/test_execution.py`.
3. **No `src/components/` changes without CEO approval** — scoped to Option 5 / 6 only.
4. **No changes** to `scripts/ob_continuation_monitor.py`, `scripts/ob_retest_comprehensive.py`, `scripts/canary_test.py`, `scripts/canary_fixtures/`, `config/`, `prompts/` — unless explicitly scoped.
5. **No commits without explicit CEO approval.** Main thread stages + commits only after A1 + A2 both green.
6. **No push to remote.** Local commits only, per CLAUDE.md.
7. **Preserve the 3 pre-existing stashes** (`23c083f`, `86a23fb`, `d0bbefa`). Never run `git stash drop/clear/pop` without explicit approval.
8. **WF-1 discipline.** Research/infra is fine. Any prompt / config / trading-logic change requires CEO approval and is typically a separate session.
9. **Do NOT propose GBPUSD changes** before 2026-04-30 per CEO decision (see project memory + "Session 24 post-script" above).

---

## Success criteria (generic — adapt per chosen task)

- [ ] Deliverable committed (script / CSV / write-up / infra change)
- [ ] Unit tests pass in isolation AND full suite regression-free (expected ~1292+N pass / 8 fail / 1 skip)
- [ ] Cold reviewer A2 verdict: GO
- [ ] ADR written and committed (if approach-level forks existed)
- [ ] CEO sign-off before commit
- [ ] Handoff 25 written and committed

---

## Parked (do NOT touch unless CEO elevates)

- **Approach B side-file resolver** — only relevant if Approach A historical-window misses short-term decay.
- **CLAUDE.md "What is unresolved" list** — may need pruning; some items resolved by sessions 19–24, list not re-audited end-to-end. Candidate for a small cleanup task if CEO redirects there.
- **GBPUSD month-end revisit** — CEO decision 2026-04-18: leave running at ~$8–12/mo through end of April. Revisit 2026-04-30. See `project_gbpusd_observer_cost.md` memory.

---

## Suggested opening moves (first tool calls of the fresh session)

```bash
# 1. Mandatory reading via Read tool, not cat

# 2. Verify current git / test state
git log --oneline -5
git stash list
git status --porcelain src/ tests/ prompts/ config/

# 3. Verification pytest
python -m pytest tests/test_ob_continuation_monitor.py --tb=no -q
python -m pytest tests/ --tb=no -q

# 4. Live-health spot-check
tail -20 logs/watchdog.log
ls -la knowledge_base/meta/.orchestrator_*.lock
ls -la knowledge_base/meta/canary_cache.json
```

Report verification findings to CEO. If everything is clean, present the Options 1–6 summary in your own words (2–3 lines per option: what, why, cost, payoff) and ask CEO to pick. Do NOT pre-select or strongly recommend — the CEO picks, you execute. After the pick, open the next ADR (if applicable), then dispatch A1 per the delegation pattern above.

---

*End of fresh-session briefing. Execute: verification → report → present options → CEO selects → ADR (if forks) → dispatch A1 → cold review (A2) → CEO sign-off → commit → handoff 25.*
