# Session 21 Handoff — Test Isolation Done, 5 Contamination Bugs Exposed, Punch List Carried Over

**Date:** 2026-04-17 (evening, continued from session 20 compaction)
**Owner/CEO:** Borhen
**Session status:** Current context exhausted — full handoff to fresh session
**Live system status:** All 5 instruments running. Apr 17 15:50 LOCAL heartbeat confirmed. redacted_account 1% risk profile active.

---

## 30-SECOND STATE OF THE WORLD

1. **Apr 16 XAUUSD silent crash ROOT CAUSE = pytest contamination**, not a production bug. Pytest was overwriting `knowledge_base/meta/execution_checkpoint.json`, `pending_intent_*.pkl`, and `.orchestrator_*.lock` files on live PIDs. Evidence: lock files mtimes matched `pytest` runs, not watchdog restarts.
2. **Fixed in commit `fa93c35`** — "test: isolate test suite from production paths + conftest write guard". 5 test files monkeypatched (test_execution, test_deployment_prep, test_exit_wiring, test_trade_capture, test_kb_seeding) + comprehensive write-guard in `tests/conftest.py` that raises `ProductionWriteError` if any test touches `knowledge_base/`, `shadow_logs/`, `pipeline_state/`, `logs/`.
3. **The guard exposed 5 more contamination bugs** on the way — these are real tests that were silently corrupting production. They now loudly fail with `ProductionWriteError` (exactly what we want). Full list below.
4. **Two shadow logs scrubbed of synthetic data**: `drawdown_state_changes.jsonl` (all 319 entries synthetic, truncated to 0; forensic backup at `.contaminated_backup/`) and `malformed_responses.jsonl` (3 of 41 entries synthetic on 2026-04-15T09:22:15, removed, 38 real Apr-13 entries preserved).
5. **Live processes untouched** — `pending_intent_GBPUSD.pkl` heartbeat at 17:45 AFTER pytest window confirms the live system survived. All 5 .lock files intact.

---

## WHAT WAS COMPLETED IN SESSION 21

### Commit `fa93c35` — 13 files, 888 insertions, 343 deletions

**Test files monkeypatched to use `tmp_path`:**
- `tests/test_execution.py` — `monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH", ...)`
- `tests/test_deployment_prep.py` — `_orch_mod.LOCK_DIR` + `monkeypatch.chdir`
- `tests/test_exit_wiring.py` — `_orch_mod.LOCK_DIR` + chdir
- `tests/test_trade_capture.py` — `monkeypatch.chdir`
- `tests/test_kb_seeding.py` — `monkeypatch.chdir`

**New `tests/conftest.py` write guard** (36 → 470+ lines):
- `ProductionWriteError` exception class
- `_PROTECTED_DIRS = ("knowledge_base", "shadow_logs", "pipeline_state", "logs")`
- Session-scoped autouse `_production_path_guard` fixture
- Monkeypatches `builtins.open`, `pathlib.Path.open/write_text/write_bytes/unlink/rmdir/rename/replace`, `os.remove/unlink/rmdir/rename/replace/open`, `shutil.copy/copy2/copyfile/copytree/move/rmtree`
- Snapshot-diff belt-and-suspenders: `_snapshot_dir()` + `_diff_snapshots()` (size, mtime_ns; LanceDB excluded; logs/*.log append-tolerant)
- Whitelist for pytest's own tmp dirs

**Shadow-log scrub:**
- `shadow_logs/drawdown_state_changes.jsonl`: 319 → 0 lines. ALL entries synthetic ($90k/$91k/$92k/$95k/$96k/$100,001/$105k test values). Forensic backup at `shadow_logs/.contaminated_backup/drawdown_state_changes_pre_2026-04-17.jsonl`.
- `shadow_logs/malformed_responses.jsonl`: 41 → 38 lines. Removed 3 synthetic at 2026-04-15T09:22:15 ("Sorry, I can't produce JSON right now." ×2, "not json" ×1).

**Test suite final state after commit:** 1164 pass / 13 fail. Zero production contamination in normal runs.

---

## THE 13 TEST FAILURES — CATEGORIZED

### Newly-exposed contamination (5 failures — must fix, they're writing to prod)

| File | Test class / method | What it writes | Fix pattern |
|------|---------------------|----------------|-------------|
| `tests/test_integration_live.py` | `TestFullPipelineCandidateExecuted::test_candidate_passes_all_gates_and_executes` | `knowledge_base/meta/execution_checkpoint.{pid}.tmp` via `ExecutionEngine.safe_place_order` → `_write_checkpoint` → `atomic_write(CHECKPOINT_PATH, ...)` | Add `monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH", str(tmp_path / "checkpoint.json"))` autouse fixture |
| `tests/test_integration_live.py` | 2 other tests in same file | Same — any test that calls `engine.open_trade` hits the checkpoint | Same fix, module-scoped autouse fixture |
| `tests/test_walk_forward.py` | `TestCreateLock` | `knowledge_base/meta/.orchestrator_XAUUSD.lock` | `monkeypatch.setattr(_orch_mod, "LOCK_DIR", str(tmp_path))` + chdir |
| `tests/test_infrastructure_framework.py` | 2 tests (under investigation) | Unknown — start by running `pytest tests/test_infrastructure_framework.py -v` to see the `ProductionWriteError` paths | TBD |

**Exact error example (test_integration_live.py):**
```
ProductionWriteError: Test attempted to write (open) a production path:
  C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\meta\execution_checkpoint.18724.tmp
  operation: write (open)
  Fix: redirect the write to the pytest tmp_path fixture...
```
The guard message itself tells the fresh session exactly what to do.

### Pre-existing failures — separate work

| File | Tests | Why | Priority |
|------|-------|-----|----------|
| `tests/test_deployment_prep.py::TestReseedFromSessions` | 5 tests | Need synthetic trade data seeded in tmp_path before test runs | LOW (test-quality) |
| `tests/test_security_framework.py` | 2 tests with `WF1 DID NOT RAISE` | Code bug in `src/components/wf1_protection.py`, not test isolation | MEDIUM (separate investigation) |
| `tests/test_orchestrator.py` | 1 test (pre-existing from session 20) | Review last session's notes | LOW |

---

## ACTIVE PUNCH LIST — WHAT NEEDS DOING NEXT

Ordered by priority. Fresh session should work top-down.

### P0 — Safety / live trading impact

1. **[P0-NEW] Fix the 5 newly-exposed contamination bugs** (listed above). Bundle into one commit. Use same `monkeypatch` pattern already established. Cross-test: run `pytest tests/ --tb=short` — expected outcome is 1164+5 = 1169 pass / 8 fail (the 8 pre-existing).
2. **[P0 DIAGNOSED ✓]** Apr 16 XAUUSD silent crash — root-caused to pytest contamination. Fixed by `fa93c35`. No more action unless CEO sees a new crash.

### P1 — Known pre-existing bugs (from earlier sessions)

3. **[P1-3] `_active_trade_record` never set on limit-fill path** — In `src/components/execution.py`, limit fills don't set `_active_trade_record`, so `_finalize_exit()` never fires and exit data is lost. Referenced in CLAUDE.md. Higher risk outside KZ (wider spreads).
4. **[P1-4] MT5 `fromtimestamp()` without `tz=timezone.utc`** — In `src/mt5/mt5_real.py`. Latent on UTC machines; causes timestamp drift on non-UTC boxes.
5. **[P1-5] Logger asctime in local time, should be UTC** — All `shadow_logs/` and `logs/` timestamps should be UTC for cross-session correlation.

### P2 — Infrastructure / monitoring

6. **[P2-6] Wire `scripts/api_refusal_monitor.py` into scheduler** — Script exists and tested (`tests/test_api_refusal_monitor.py`), but not auto-run. Goal: detect API refusal events like the 34 on Apr 13.
7. **[P2-7] Refresh canary fixtures for T7 calibration** — All 10 fixtures in `scripts/canary_fixtures/` are stale; with T7's higher CR, need borderline canaries.
8. **[P2-8] Build OB continuation rolling-50 monitor** — Primary decay metric per CLAUDE.md. Alarm at <60%. No script exists yet.

### P3 — Research / sims (CEO decision required)

9. **[P3-1] GBPJPY-only T7 batch simulation** (~$25) — pending CEO approval.
10. **[P3-2] NAS100 batch simulation** (~$25) — pending CEO approval.

### P4 — Low-priority cleanup

11. **[P4-12] CLAUDE.md count drift** — "47 test files" line is now wrong after session 21 commits. Check and update.
12. **[P4-13] Stale 0.3 ATR comments** in OB exception tests (SL margin was raised to 0.5 ATR).
13. **[P4-14] Verify XAUUSD-only Session ATR block doesn't leak** to other instruments.

### Also outstanding (from session 20 handoff 20, not addressed in session 21)

- **Liquidity cluster gate is DISABLED** (ships off). Shadow-logging running. Need 30+ observations before any promotion decision.
- **R2 candidate features logger** — shipping data. No action needed yet.
- **PendingLimitIntent schema_version** is deployed. Handles backwards compat for old pickle files.

---

## KEY PATTERNS / CONVENTIONS (for fresh session)

### Monkeypatch pattern for production-path tests

**Wrong (breaks after a `from X import Y` shadow):**
```python
from src.components.execution import CHECKPOINT_PATH  # local binding
# monkeypatch.setattr(execution, "CHECKPOINT_PATH", ...) won't touch this local
```

**Right:**
```python
from src.components import execution as _exec_mod
# then reference _exec_mod.CHECKPOINT_PATH everywhere
monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH", str(tmp_path / "checkpoint.json"))
```

Autouse fixture at module or class scope:
```python
@pytest.fixture(autouse=True)
def _isolate_checkpoint(tmp_path, monkeypatch):
    checkpoint_file = tmp_path / "execution_checkpoint.json"
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH", str(checkpoint_file))
    yield
```

For function-local relative paths (e.g., `Path("knowledge_base/...")` inside a function):
```python
monkeypatch.chdir(tmp_path)  # applied before test runs; auto-reverted on teardown
```

### Write guard — how it works

`tests/conftest.py` installs session-scoped interceptors on filesystem APIs. Any test that writes to `knowledge_base/`, `shadow_logs/`, `pipeline_state/`, or `logs/` raises `ProductionWriteError` with a fix hint. Belt-and-suspenders: session-scoped snapshot-diff at teardown catches anything that slipped through (e.g., subprocess writes).

### What the guard does NOT block

- Reads (all read ops are fine)
- Writes to `tmp_path` (pytest's temp dir is whitelisted)
- Writes to `research/`, `tests/`, `data/historical_2026/`, `prompts/`, `config/`, `.context/` (not protected)

---

## KEY FILES / PATHS THE FRESH SESSION NEEDS

| File | Why |
|------|-----|
| `CLAUDE.md` | Project instructions — MUST READ FIRST |
| `.context/02_session_handoffs/21_apr17_test_isolation_exposed_bugs_handoff.md` | THIS FILE — state transfer |
| `.context/02_session_handoffs/20_apr17_liquidity_gate_R2_logger_handoff.md` | Previous handoff — liquidity gate + R2 logger |
| `.context/00_core/quick_reference_card.md` | Live ops numbers |
| `tests/conftest.py` | The write-guard — read it top-to-bottom, it's 470+ lines of infrastructure |
| `tests/test_execution.py` | Canonical example of the new monkeypatch pattern |
| `src/components/execution.py` line 31 | `CHECKPOINT_PATH = "knowledge_base/meta/execution_checkpoint.json"` (hardcoded module const) |
| `src/components/orchestrator.py` line 78 | `LOCK_DIR = "knowledge_base/meta"` (hardcoded module const) |
| `shadow_logs/.contaminated_backup/` | Forensic record of pre-2026-04-17 synthetic data |

---

## LIVE SYSTEM VERIFICATION COMMANDS

Before touching any test code, confirm live processes are healthy:

```bash
# 1. Watchdog log should show all 5 "OK" on recent run
tail -20 logs/watchdog.log

# 2. PID lock files should have recent mtimes (within last ~15 min in trading hours)
ls -la knowledge_base/meta/.orchestrator_*.lock

# 3. Pending intent files should exist for pending-limit symbols
ls -la knowledge_base/meta/pending_intent_*.pkl 2>/dev/null

# 4. Displacement logger
ls -la knowledge_base/meta/.displacement_logger.lock
```

---

## CEO'S RECENT DECISIONS / PREFERENCES (FOR FRESH SESSION)

1. **Active monitoring + immediate logging fixes** (stored memory). When a bug is found live, add logging + restart immediately rather than wait. Do not let data be lost.
2. **Solid system over simplicity** — verbatim: "we need a solid system and proceed with whatever approach your judgment thinks it's best for the system's overall accuracy, frequency and be prone to issues and gaps, especially the gaps in data since it's the most important for our model". Drove decision to implement the maximum-coverage write guard (both per-test monkeypatch AND session-scoped snapshot) rather than a minimal version.
3. **WF-1 lock is cancelled** (per handoff 09). Verified changes deploy directly with CEO approval. Testing discipline still applies.
4. **Commit + follow up** — verbatim: "commit now and follow up for exposed bugs". The commit is done. Fresh session should fix the 5 exposed bugs first.
5. **redacted_account Stellar 2-Step profile @ 1% risk** (from handoff 19).

---

## FIRST ACTIONS FOR FRESH SESSION

1. Read `CLAUDE.md` (mandatory)
2. Read this file (session 21 handoff)
3. Read `20_apr17_liquidity_gate_R2_logger_handoff.md` (previous state)
4. Run `git log --oneline --since="2026-04-16"` to see recent commits
5. Run `pytest tests/test_integration_live.py tests/test_walk_forward.py::TestCreateLock tests/test_infrastructure_framework.py --tb=short` to see the 5 exposed contamination bugs with exact error paths
6. Apply the monkeypatch pattern from `tests/test_execution.py` to fix each (bundle into ONE commit with cross-testing — run full `pytest tests/ --tb=line` after each file fix)
7. Report back to CEO before moving on to P1 punch list

---

## AGENTS / WORKFLOW CONVENTIONS USED THIS SESSION

- **Code-reviewer agent** was used to independently verify my test-isolation fix. It caught a 4th issue (test_execution.py CHECKPOINT_PATH import shadowing) that I had missed. Pattern: spawn reviewer with COLD briefing (no conversation context) for independent second opinion.
- **Parallel agents A+B** executed simultaneously for the conftest guard + 4 remaining test files. A worked on test files, B worked on conftest.py. Both verified via `git diff` before staging.

Recommended pattern: for each file in the 5 contamination bug list, either (a) fix directly if simple, or (b) spawn an agent with a cold briefing if complex. Always verify agent diffs manually before commit.

---

## STATISTICAL FOOTNOTE

With the scrub of `drawdown_state_changes.jsonl`, any past analysis that cited "319 drawdown state changes" is invalid. All 319 were synthetic test data. The true count of real drawdown state changes since Apr 7 is **0** (we haven't hit 8% DD in live trading). This is consistent with live WR of 71.4% (handoff 15) — the system is well above drawdown territory.

---

*End of session 21 handoff. Commit fa93c35 is the canonical artifact for this session's work.*
