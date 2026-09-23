# Fresh Session Briefing — Session 24 (GTOS)

**Project:** Gold Traders Operating System (GTOS)
**Date context:** Going into session 24, after session 23 close (2026-04-17)
**Live system status:** 5 orchestrators running on FTMO $100K demo, redacted_account 1% risk profile active

---

## Mandatory reading (in order)

1. `CLAUDE.md` — project instructions
2. `.context/02_session_handoffs/21_apr17_test_isolation_exposed_bugs_handoff.md` — punch list origin
3. `.context/02_session_handoffs/22_apr17_task_C_canary_dedup_handoff.md` — canary work context
4. `.context/02_session_handoffs/23_apr17_task_C_canary_cache_handoff.md` — **latest close-out, read carefully**
5. `.context/00_core/quick_reference_card.md` — live numbers
6. This file

---

## Where we are — sessions 21→23 arc

Infrastructure safety hardening before touching the core edge signal:

- **Session 21** — Root-caused Apr 16 XAUUSD silent crash = pytest contamination, not production bug. Added conftest Layer 1+2 write guards (`fa93c35`, 470+ lines). Scrubbed 319 synthetic drawdown entries + 3 synthetic malformed responses from shadow logs.
- **Session 22** — Regenerated canary fixtures under T7 C-gate (`8a42afb`, 12 fresh fixtures + 249-line test file).
- **Session 23 (just completed)** — Shipped canary subprocess dedup cache (`0c26d25`):
  - Cost: $6–75/day restart-sensitive → ~$12/mo flat
  - 6-component hash: date / model / effort / fixtures+manifest / rendered prompt / baseline
  - PASS-only caching (FAIL never cached — avoids 24h lockout on false FAIL)
  - Fail-open preserved verbatim; cache infra cannot block trading
  - 36 new tests all pass; full suite 1187 → 1223 / 8 fail / 1 skip
  - Cold-reviewed by independent Opus 4.7 with GO verdict

---

## State at session 23 close

- **HEAD:** `0c26d25` (canary cache) + docs commit on top
- **Test suite:** 1223 pass / 8 fail / 1 skip — 8 failures pre-existing and unrelated
- **Live system:** 5 orchestrators running; watchdog healthy
- **Pre-existing stashes:** 3 intact (`23c083f`, `86a23fb`, `d0bbefa`) — DO NOT DISTURB
- **Clean trees:** `src/`, `tests/`, `prompts/`, `config/` all clean
- **Canary cache:** `knowledge_base/meta/canary_cache.json` will be created on first canary PASS after next watchdog restart — verify this happens during session 24 health check

---

## Your mission — Task A: OB Continuation Rolling-50 Monitor

### Why this is the next priority

Per CLAUDE.md, **OB continuation rate is the #1 primary decay metric for the system's edge.** Baseline ~70% mechanically across 13 instruments. Alarm threshold: <60%. Rolling 50-OB window.

SPRT, CUSUM, and the canary each cover different failure modes. None of them directly detect a slow decay in OB continuation rate. If our core edge breaks, THIS monitor catches it first — before a losing streak triggers SPRT-kill or an emergency stop.

**No monitor currently exists.** This is the biggest unfilled gap in edge-health observability.

### Scope

Build `scripts/ob_continuation_monitor.py` that:

1. Reads OB retest events from `knowledge_base/meta/ob_retest_events_*.json` (logged per-instrument — **verify the actual schema first**, don't assume)
2. Computes rolling 50-OB continuation rate per-instrument AND portfolio-wide
3. Alarms (log `CRITICAL` + Telegram if available) when rate drops below 60% over the rolling window
4. Writes daily snapshot to `shadow_logs/ob_continuation_daily.csv`
5. Runnable standalone (target: cron every 6h)
6. Unit-testable in CI with synthetic data injection

### NOT in scope

- Changes to `src/components/` (observation-only monitor, NOT a gate)
- Changes to trading logic, prompts, config
- Changes to existing scripts (`scripts/canary_test.py`, etc.)
- Any modification to trade decisions, risk, execution

---

## BEFORE starting Task A — Verification pass (MANDATORY)

Handoff 23 flagged 3 punch-list items as "LIKELY RESOLVED" by inference from commit subject lines. Verify before layering new work:

1. **P0-NEW contamination bugs** — run:
   ```bash
   pytest tests/test_integration_live.py tests/test_walk_forward.py::TestCreateLock tests/test_infrastructure_framework.py -v
   ```
   Expected: all pass. If any fail with `ProductionWriteError`, those contamination bugs are still open — fix them FIRST, bundle into one commit, then start Task A.

2. **P1-3 `_active_trade_record` on limit-fill path** — read `git show fb86280`. Verify limit-fill path now sets `_active_trade_record` so `_finalize_exit()` fires. If not, flag.

3. **P1-5 / P2-6 UTC timestamps + refusal monitor scheduler** — read `git show b0c2ece`. Verify UTC timestamps everywhere + `api_refusal_monitor` actually scheduled/wired into watchdog.

4. **Live health check:**
   ```bash
   tail -20 logs/watchdog.log
   ls -la knowledge_base/meta/.orchestrator_*.lock
   ls -la knowledge_base/meta/canary_cache.json  # should appear post-restart
   ```

Report findings to CEO. If anything is still broken, fix it FIRST. No Task A work until the verification pass is clean.

---

## Agent delegation pattern (CEO directive — CRITICAL)

Main thread stays strategic: briefing, reviewing, committing. Delegate all implementation / verification / review work to subagents.

| Role | Agent type | Model | Isolation | Brief style |
|---|---|---|---|---|
| A1 — implementation | `general-purpose` | `opus` | `worktree` | Full spec, guardrails, test plan, file paths, line numbers |
| A2 — cold reviewer | `general-purpose` | `opus` | none (or `worktree`) | Blank-slate adversarial review, pytest evidence required |
| A3 — runtime verifier (optional) | `general-purpose` | `opus` | `worktree` | Synthetic <60% injection, verify alarm fires |

### Effort setting — known limitation

The `Agent` tool schema exposes `model` but NOT `effort`. You cannot force `effort: max` on subagents via tool params. Compensate by:

- Long, specific briefs with explicit `"think hard about X, Y, Z"` directives
- All required context provided upfront (no back-and-forth)
- Explicit success criteria and guardrails in the brief
- File paths and line numbers, not vague descriptions

This pattern was used successfully in session 23 for C1 (implementation) and C2 (cold review) — both produced thorough, verifiable output.

---

## Guardrails — flawless execution, zero new system issues

1. **Observation-only.** Monitor must NOT affect trading decisions or gate logic. It's a passive canary for edge decay.
2. **Conftest write guards.** Tests MUST use `tmp_path` + module-ref monkeypatch pattern. Never write to `knowledge_base/`, `shadow_logs/`, `pipeline_state/`, or `logs/` from tests. Canonical examples: `tests/test_canary_cache.py` (session 23) and `tests/test_execution.py`.
3. **No `src/components/` changes.** Monitor is a standalone script in `scripts/`.
4. **No changes to `scripts/canary_test.py`, `scripts/canary_fixtures/`, `config/`, or `prompts/`.**
5. **No commits without explicit CEO approval.** Main thread stages + commits ONLY after A1 + A2 both green.
6. **No push to remote.** Local commits only, per CLAUDE.md.
7. **Preserve the 3 pre-existing stashes** (`23c083f`, `86a23fb`, `d0bbefa`). Never run `git stash drop/clear/pop` without explicit approval.
8. **WF-1 discipline.** No prompt changes, no config changes that affect trade decisions.
9. **Schema-aware.** If the `ob_retest_events_*.json` schema differs from expectations, STOP and report. Don't silently adapt — this is production data.

---

## Success criteria — Task A

- [ ] Monitor computes correct rolling-50 continuation rate (hand-verified against a sample case)
- [ ] Alarm fires reliably at <60% (verified via synthetic data test)
- [ ] Daily CSV appends correctly
- [ ] Unit tests pass in isolation AND full suite regression-free (expected ~1223+N pass / 8 fail / 1 skip)
- [ ] Cold reviewer A2 verdict: GO
- [ ] CEO sign-off before commit
- [ ] Handoff 24 written and committed alongside the code

---

## Post-Task-A roadmap

Once Task A ships, CEO decides on Task B (pending approval):

- **P3-1** GBPJPY-only T7 batch simulation (~$25) — statistical validation
- **P3-2** NAS100 T7 batch simulation (~$25) — statistical validation

Both produce evidence for future sizing decisions.

---

## Suggested opening moves (first tool calls of the fresh session)

```bash
# 1. Mandatory reading (these paths match the "Mandatory reading" section above)
# Read via Read tool, not cat

# 2. Verify current git / test state
git log --oneline -5
git stash list
git status --porcelain src/ tests/ prompts/ config/

# 3. Run the targeted verification pytest
pytest tests/test_integration_live.py tests/test_walk_forward.py::TestCreateLock tests/test_infrastructure_framework.py -v

# 4. Live-health spot-check
tail -20 logs/watchdog.log
ls -la knowledge_base/meta/.orchestrator_*.lock
ls -la knowledge_base/meta/canary_cache.json
```

Report the verification findings to the CEO. Wait for approval before starting Task A or dispatching A1.

---

*End of fresh-session briefing. Execute verification → report → dispatch Task A on CEO approval.*
