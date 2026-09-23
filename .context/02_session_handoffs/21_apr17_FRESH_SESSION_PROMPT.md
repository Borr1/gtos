# Fresh Session Briefing Prompt — Paste This Into New Claude Code Session

**Instructions for CEO:** Open a new Claude Code session in this repo. Paste the entire block below (between the `---` markers) as your first message. The fresh session will self-brief, independently verify the prior session's work, and report back with a punch list + strategic recommendations before taking any action.

---

You are Claude Code, the primary engineering agent for the Gold Traders Operating System (GTOS). The previous session's context is exhausted — this is a clean handoff to you.

**DO NOT take any action or commit any code yet.** Read, verify, think, report — in that order. The CEO expects you to operate at three levels simultaneously: tactical (fix the exposed bugs), defensive (make sure no new change breaks anything), and strategic (think about how to make the system more accurate, more frequent, and less prone to misinterpretations).

---

## PHASE 1 — REQUIRED READING (in this exact order)

1. `CLAUDE.md` (project root) — the single source of truth. Architecture, prohibited behaviors, validated numbers, file map.
2. `.context/02_session_handoffs/21_apr17_test_isolation_exposed_bugs_handoff.md` — most recent state transfer. Covers commit `fa93c35`, the 5 newly-exposed contamination bugs, the 13-failure categorization, full P0-P4 punch list, key monkeypatch patterns, CEO preferences.
3. `.context/02_session_handoffs/20_apr17_liquidity_gate_R2_logger_handoff.md` — immediate prior state (liquidity gate shipped DISABLED, R2 logger shipping, PendingLimitIntent schema_version).
4. `.context/00_core/quick_reference_card.md` — live ops numbers.
5. `tests/conftest.py` — the 470-line write guard installed last session. Read top-to-bottom. Understand *why* it was built this way before touching any test.
6. `tests/test_execution.py` — canonical example of the monkeypatch import-shadow pattern.

---

## PHASE 2 — INDEPENDENT VERIFICATION (do NOT trust the handoff — confirm it)

The prior session claims certain things were fixed. Your first job is to verify those claims yourself with tools — not believe them.

### Verify commit fa93c35 actually does what the handoff claims

```bash
# 1. Confirm the commits exist and the tree is clean
git log --oneline -5
git status --short

# 2. Confirm the 5 monkeypatch patterns are actually in the 5 test files
#    (should find `monkeypatch.setattr` or `monkeypatch.chdir` in each)
grep -l "monkeypatch" tests/test_execution.py tests/test_deployment_prep.py \
    tests/test_exit_wiring.py tests/test_trade_capture.py tests/test_kb_seeding.py

# 3. Confirm the conftest guard is installed (look for ProductionWriteError)
grep -c "ProductionWriteError" tests/conftest.py
grep -c "_PROTECTED_DIRS" tests/conftest.py

# 4. Confirm the shadow log scrub
wc -l shadow_logs/drawdown_state_changes.jsonl                # should be 0
wc -l shadow_logs/malformed_responses.jsonl                    # should be 38
ls -la shadow_logs/.contaminated_backup/                       # forensic backup exists
```

### Verify live system is healthy and was NOT touched by the scrub

```bash
# Lock files — mtimes should be recent (within ~15 min during trading hours)
ls -la knowledge_base/meta/.orchestrator_*.lock
ls -la knowledge_base/meta/.displacement_logger.lock

# Pending intents — these are live process state. DO NOT DELETE.
ls -la knowledge_base/meta/pending_intent_*.pkl 2>/dev/null

# Watchdog should show all 5 OK on recent run
tail -30 logs/watchdog.log
```

### Re-run the failing tests yourself to see the exact error surface

```bash
pytest tests/test_integration_live.py tests/test_walk_forward.py::TestCreateLock \
       tests/test_infrastructure_framework.py --tb=short 2>&1 | tail -80
```

### Run the full suite to lock in the baseline before your changes

```bash
pytest tests/ --tb=no -q 2>&1 | tail -20
```

Expected baseline: **1164 pass / 13 fail**. Anything other than that — stop and report. Do NOT start fixing until the baseline matches.

---

## PHASE 3 — STRATEGIC REVIEW (think before doing)

Before touching code, spend one deep-thinking pass on each of these questions. Write your answers into your report to the CEO (do NOT commit them as docs unless asked):

### A. Verification of the prior session's thinking

1. Was the root-cause analysis of the Apr 16 crash (pytest contamination) correct, or is there residual risk? What would evidence of a DIFFERENT root cause look like?
2. Is the conftest write guard appropriately scoped — too aggressive (will it block legitimate future tests) or too permissive (can it miss a subprocess write or an os.low-level write)?
3. Does the shadow log scrub have any statistical consequence I should flag to the CEO? For example, does any downstream script read `drawdown_state_changes.jsonl` expecting ≥1 entry?

### B. "Making the system more accurate, more frequent, less prone to misinterpretation"

Think hard about these — they are the CEO's top-level goals. For each, cite at least one concrete change you'd propose (do not implement — just propose):

1. **Accuracy** — where in the pipeline (data ingestion → market state → primary analyzer → execution) is the highest likelihood of a silent misinterpretation? Where could the AI read a CANDIDATE correctly but the system mishandle it? Is there a gap between what the AI decides and what actually executes?
2. **Frequency** — the live trade count is ~17/month across 5 instruments. What's the gap between *evaluated CANDIDATEs* and *actually-filled trades*? What mechanical gates (sl_too_tight, touch-count, between-KZ limit, liquidity cluster) are highest on the "blocks real signal" list?
3. **Robustness to issues / miscalculations** — where else in the codebase might there be a silent contamination or a drift bug of the same class as the Apr 16 crash? Likely candidates: any module-level constant that points to a production path, any logger path hardcoded without UTC, any test that calls a production function with real side effects.
4. **Data gaps** — the CEO called these out explicitly as the most important. What data do we NOT have that, if we had it, would materially change how we evaluate edge (e.g., tick data vs M15 only, level-2 order book, true trade imbalance vs tick-volume proxy)?

### C. Change-safety checklist for YOUR upcoming work

Before you commit anything this session, confirm in writing:

- [ ] Every change is covered by a new or existing test
- [ ] The full suite (`pytest tests/`) passes at the same or better level (≥1169 pass expected after the 5 contamination fixes)
- [ ] `git diff` has been reviewed and understood — no accidental file additions, no production path writes
- [ ] At least one **independent reviewer agent** (general-purpose, cold briefing) was spawned to audit non-trivial changes
- [ ] Change does not touch `src/components/` trading logic, `prompts/`, or `config/agent_config.yaml` trade-behavior fields without explicit CEO approval
- [ ] Live system was not touched (lock files intact, pending_intent files intact, no running process was killed)
- [ ] Every claim in your report is traceable to a file read, a git log entry, or a tool output — no fabricated numbers

Fail any one of these → DO NOT COMMIT. Report back instead.

---

## PHASE 4 — PUNCH LIST OPTIONS (ordered, pick with CEO)

After you've completed Phases 1-3 and reported, the CEO will pick which of these to tackle. Do not pick for them — surface the tradeoff (effort, risk, value) for each.

### P0 — Safety / live trading impact

1. **Fix the 5 newly-exposed contamination bugs** (test_integration_live ×3, test_walk_forward::TestCreateLock ×1, test_infrastructure_framework ×2). Same monkeypatch pattern. Bundle into one commit with cross-testing. Expected: 1169 pass.

### P1 — Known pre-existing bugs

2. **P1-3:** `_active_trade_record` never set on limit-fill path → exit data lost for limit-filled trades
3. **P1-4:** MT5 `fromtimestamp()` missing `tz=timezone.utc` — latent timezone drift
4. **P1-5:** Logger asctime in local time, should be UTC

### P2 — Infrastructure / monitoring

5. **P2-6:** Wire `scripts/api_refusal_monitor.py` into scheduler
6. **P2-7:** Refresh canary fixtures for T7 calibration
7. **P2-8:** Build OB continuation rolling-50 monitor (primary decay metric)

### P3 — Research / sims (CEO approval required)

8. GBPJPY-only T7 batch simulation (~$25)
9. NAS100 batch simulation (~$25)

### P4 — Low-priority cleanup

10. CLAUDE.md count drift + stale numbers
11. Stale 0.3 ATR comments in OB exception tests
12. XAUUSD-only Session ATR block leak check

---

## AGENT PATTERNS

- **Independent code review:** spawn a `general-purpose` agent with a COLD briefing (no prior conversation context). Essential before non-trivial commits. Last session caught a bug I missed this way.
- **Parallel work:** dispatch multiple agents in a single message (e.g., Agent A on test files 1-2, Agent B on test files 3-4). Always verify their diffs manually before staging.
- **Codebase exploration >3 queries:** use `Explore` agent type.
- **Do NOT delegate judgment.** Prompts like "based on your findings, fix it" push synthesis to the agent. Write prompts that prove you understood the problem (exact file paths, line numbers, what to change, what NOT to change).

---

## CEO'S VERBATIM PREFERENCES

1. *"we need a solid system and proceed with whatever approach your judgment thinks it's best for the system's overall accuracy, frequency and be prone to issues and gaps, especially the gaps in data since it's the most important for our model"* — prefer robust, complete fixes over minimal ones. Complexity is OK if it serves the system.
2. *"commit now and follow up for exposed bugs"* — commit milestones often; don't hold up fixes waiting for bundling.
3. *"it will continue just where you resume and verifies what you did exactly and why we did it and think strategically too to make the system better, more frequent and more accurate and more prone to issues miscalculations and misinterpretations and makes sure that no new issues get presented from new changes and everything gets cross checked tested, reviewed verified and validated first"* — VERIFY the prior session's work independently; think strategically; every new change must be cross-checked, tested, reviewed, verified, and validated BEFORE commit.
4. **Active monitoring + immediate logging fixes** — when a bug is found live, add logging + restart immediately. Don't let data be lost.

---

## HARD RULES (must not be broken)

1. Do not change `src/components/` trading logic without CEO approval (WF-1 rules).
2. Do not change `prompts/` — frozen.
3. Do not change `config/agent_config.yaml` fields that affect trade decisions without CEO approval.
4. Do not `git push` without CEO approval.
5. Do not kill or restart live orchestrator processes without CEO approval.
6. Do not commit changes that reduce the test pass count.
7. Do not commit claims backed by fabricated numbers or in-sample validation.
8. Do not commit before running the full test suite.
9. Do not delegate synthesis to agents — you verify their work.
10. Do not skip Phase 2 verification because "the handoff says it's done."

---

## YOUR REPORT BACK FORMAT (after Phases 1-3)

Structure your first response to the CEO like this:

```
## Reading confirmation
- CLAUDE.md: [1 line]
- handoff 21: [1 line]
- handoff 20: [1 line]
- quick_reference_card: [1 line]
- conftest.py: [1 line]
- test_execution.py: [1 line]

## Verification results
- Commit fa93c35 status: [PASS/FAIL with evidence]
- 5 monkeypatch files: [PASS/FAIL]
- Conftest guard installed: [PASS/FAIL]
- Shadow log scrub: [PASS/FAIL with line counts]
- Live system untouched: [PASS/FAIL with mtimes]
- Baseline test count: [actual X pass / Y fail vs expected 1164/13]
- Contamination errors visible in the 5 targeted files: [PASS/FAIL]

## Strategic observations
- Accuracy gap [1 proposal]
- Frequency gap [1 proposal]
- Robustness gap [1 proposal]
- Data gap [1 proposal]

## Proposed first commit scope
- Files to change: [list]
- Fix pattern per file: [specific]
- Expected test outcome: [1169/8 or other, justify]
- Reviewer agent plan: [when, on what]

## Questions for CEO
- [any blockers, ambiguities, or choices you need resolved]
```

Then WAIT for CEO approval before implementing.

---

**Now begin. Start by reading `CLAUDE.md`.**
