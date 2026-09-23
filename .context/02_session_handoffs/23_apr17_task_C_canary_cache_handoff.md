# Session 23 Handoff — Task C Shipped: Canary Cache (Per-UTC-Day Subprocess Dedup)

**Session:** 23 (Apr 17, 2026 — CEO Borhen, GTOS)
**Status at close:** Task C implemented, cold-reviewed, committed. Punch list from handoff 21 partially cleared by intervening commits.

---

## What shipped in session 23 (verify via `git log -1`)

| Commit | What | Files |
|---|---|---|
| `0c26d25` | `infra(canary): cache canary results per UTC day — subprocess dedup` | `src/components/canary_cache.py` (new, 272 lines), `src/components/orchestrator.py` (M, +65 −2), `tests/test_canary_cache.py` (new, 558 lines, 36 tests) |

Test suite after the commit: **1187 → 1223 pass / 8 fail / 1 skip**. The 8 failures are pre-existing and unrelated to Task C: 5× `test_deployment_prep.py::TestReseedFromSessions`, 1× `test_orchestrator.py::TestNewDay::test_resets_state`, 2× `test_security_framework.py::TestWF1Protection`.

Cold-reviewed by independent Opus 4.7 reviewer (no prior context) with **GO verdict**.

---

## Design summary — what the cache actually is

Content-addressed cache at `knowledge_base/meta/canary_cache.json`, keyed by **6 components** (expanded from handoff 22's original 5):

| # | Component | Source |
|---|---|---|
| 1 | `date_utc` | `datetime.now(timezone.utc).strftime("%Y-%m-%d")` |
| 2 | `model` | `config["ai"]["primary_model"]` |
| 3 | `effort` | `config["ai"]["primary_effort"]` (None ↔ string transitions handled) |
| 4 | `fixtures_hash` | sha256 of `manifest.json` bytes **+** sorted per-file sha256 of files listed in manifest |
| 5 | `prompt_hash` | sha256 of rendered `build_system_prompt(config)` output |
| 6 | `baseline_hash` | sha256 of `scripts/canary_fixtures/baseline.json` bytes |

**Why 6 and not 5 (handoff 22's spec)?**
- Component 4 was *expanded* — handoff 22 excluded `manifest.json` from the hash. That's wrong: manifest controls *which* fixtures are loaded (threshold, fixtures list). A manifest edit that drops a fixture would silently keep using a stale cache.
- Component 6 was *added* — `baseline.json` holds the reference decisions. A baseline regen (as done in commit `8a42afb`) is the whole reason stale cache would give wrong PASS verdict. 5-component hash missed it.

### Cache file schema

```json
{
  "date_utc": "2026-04-17",
  "model": "claude-sonnet-4-6",
  "effort": "max",
  "fixtures_hash": "sha256:abc123...",
  "prompt_hash": "sha256:def456...",
  "baseline_hash": "sha256:789abc...",
  "passed": true,
  "decision_matches": 12,
  "fixtures_count": 12,
  "completed_at_utc": "2026-04-17T07:03:14Z",
  "schema_version": 1
}
```

**Invalidation triggers** (any one → miss → full subprocess run):
1. New UTC day
2. `ai.primary_model` changes in config
3. `ai.primary_effort` changes in config
4. Any fixture content or manifest content changes
5. Rendered prompt output changes (refactor-robust — not the file bytes)
6. `baseline.json` bytes change

---

## Key policy decisions — REVISED from handoff 22

Two of handoff 22's recommendations got reversed at session 23 start. Document these clearly so a future session doesn't re-open them.

### 1. Cache PASS only, never FAIL

Handoff 22 recommended caching FAIL too ("repeat calls shouldn't re-run a failed canary"). **Reversed.**

Reasoning: caching a false FAIL locks out an instrument's evaluations for 24 hours. At ~0.5–1 trades/day per instrument (post-T7), that's a direct trade-frequency hit. Re-running canary at next KZ costs ~$0.42. The asymmetry favors trade frequency on FAIL days — the extra cost is trivially small compared to a missed trade.

Behavior: on `returncode != 0` → **no cache write**. Next KZ will re-run the canary subprocess.

### 2. Fail-open preserved verbatim

`_run_canary_check()` still returns `True` on subprocess timeout (`TimeoutExpired`) or uncaught exception. The cache layer does not change fail-safe semantics.

Cache-specific error paths (corrupt JSON, hash compute failure, write failure) all **fall through to normal subprocess run** and never block trading. The cache can never block a canary from running.

### 3. Atomic writes with PID suffix

Write path uses `canary_cache.json.tmp.{pid}` + `os.replace` so the 5 live orchestrators cannot collide on the temp file. Inside a single process, `_run_canary_check` is invoked from the single-threaded main loop — no intra-process race possible.

Concurrent writes from different processes under the same hash are benign (last-writer-wins, result identical).

---

## Cost impact

| Regime | Before | After |
|---|---|---|
| No restart storms | ~$6–15/day | ~$0.42/day |
| Worst case (watchdog churn) | ~$75/day | ~$0.42/day |
| Steady state | Variable | **~$12/mo flat** |

Savings: **60–95%** depending on restart frequency. The canary now runs **at most once per UTC day per unique `(model, effort, fixtures, prompt, baseline)` tuple**.

---

## Scope boundary respected

| Path | Touched? |
|---|---|
| `scripts/canary_test.py` | NO — kept pure; all caching lives in orchestrator + new module |
| `config/agent_config.yaml` | NO |
| `prompts/` | NO |
| Other `src/components/*.py` files | NO |
| `src/components/orchestrator.py` | YES — `_run_canary_check()` at lines 1914–2000 only |
| `src/components/canary_cache.py` | NEW (272 lines) |
| `tests/test_canary_cache.py` | NEW (558 lines, 36 tests) |

---

## Verification evidence (C2 cold reviewer)

All 6 hash components independently probed via live file mutations:

| Probe | Expected | Result |
|---|---|---|
| Modify a fixture file content | `fixtures_hash` changes → cache miss | PASS |
| Modify `manifest.json` only | `fixtures_hash` changes → cache miss | PASS |
| Modify `baseline.json` only | `baseline_hash` changes → cache miss | PASS |
| Config change model | `model` mismatch → cache miss | PASS |
| Config change effort | `effort` mismatch → cache miss | PASS |
| Tick UTC day forward | `date_utc` mismatch → cache miss | PASS |

**FAIL-not-cached path:**
- `test_preexisting_pass_cache_not_overwritten_by_fail` — PASS
- `test_fail_result_is_not_cached` — PASS

**Fail-safe fallthrough:**
- `test_hash_computation_failure_falls_through` — PASS
- `test_cache_write_never_raises_on_failure` — PASS
- `test_cache_read_corrupt_file_returns_none` — PASS

**Concurrency:**
- 5-thread stress test passes. Write failures under Windows same-PID concurrency are swallowed (no data corruption, just cache not updated that iteration — harmless). `os.replace` is atomic on Windows for file-rename within same volume.

**Test isolation:**
- No `ProductionWriteError` triggered during `test_canary_cache.py` run
- `knowledge_base/meta/canary_cache.json` does **NOT** exist on main working tree (confirmed via `ls`) — will be created only on first live canary PASS after next watchdog restart cycle

---

## Punch list — status after cross-referencing commits since handoff 21

Ran `git log --oneline --since="2026-04-15"`. Mapping of recent commits against handoff 21's punch list:

| ID | Item | Status | Evidence |
|---|---|---|---|
| P0-NEW | 5 exposed contamination bugs (`test_integration_live.py`, `test_walk_forward.py::TestCreateLock`, `test_infrastructure_framework.py`) | **LIKELY RESOLVED — baseline shifted from 13 → 8 failures since handoff 21** | Commit `7777837` "test: fix 5 contamination-exposed failures + relax Layer 2 for live-process writes". Next session should re-run targeted tests to confirm no regressions remain. |
| P1-3 | `_active_trade_record` never set on limit-fill path | **LIKELY FIXED** | Commit `fb86280` "fix(orchestrator): capture exit data on limit-filled trades (P1-3)" — note the literal P1-3 tag. Verify via `git show fb86280`. |
| P1-4 | MT5 `fromtimestamp()` without `tz=timezone.utc` | **Possibly covered** | Commit `b0c2ece` "fix(observability): UTC timestamps everywhere + wire api_refusal_monitor into watchdog". Verify scope includes mt5_real.py. |
| P1-5 | Logger asctime in local time, should be UTC | **LIKELY FIXED** | Commit `b0c2ece` title explicitly says "UTC timestamps everywhere". Verify scope includes logging configuration. |
| P2-6 | Wire `api_refusal_monitor.py` into scheduler | **LIKELY DONE** | Commit `b0c2ece` mentions "wire api_refusal_monitor into watchdog". Verify via `git show b0c2ece`. |
| P2-7 | Canary fixtures refresh for T7 | **DONE** | Commit `8a42afb` (session 22) — 12 fresh fixtures, T7 C-gate, Sonnet 4.6 + effort=max, baseline regenerated. |
| P2-8 | OB continuation rolling-50 monitor | **OPEN** | No commit. No script yet. |
| P3-1 | GBPJPY-only T7 batch simulation (~$25) | **OPEN — CEO approval pending** | No commit. |
| P3-2 | NAS100 batch simulation (~$25) | **OPEN — CEO approval pending** | No commit. |
| P4-12 | `CLAUDE.md` test-file count drift ("47 test files") | **OPEN** | Count is now stale after session 21, 22, 23 commits. |
| P4-13 | Stale 0.3 ATR comments in OB exception tests | **OPEN** | No commit. |
| P4-14 | Verify XAUUSD-only Session ATR block doesn't leak | **OPEN** | No commit. |

### Also carried from session 20 (status unchanged at session 23 close)

- Liquidity cluster gate: DISABLED, shadow-logging. Need 30+ observations before promotion decision. OPEN.
- R2 candidate features logger: shipping data, no action needed.
- `PendingLimitIntent` schema_version: deployed, handles backwards compat.

### Newly confirmed resolved (since handoff 21)

Commits worth re-reading to be sure the above "LIKELY" entries are truly closed:

```bash
git show 7777837   # test contamination fixes
git show fb86280   # P1-3 exit data on limit fills
git show b0c2ece   # UTC timestamps + refusal monitor scheduler
git show 823dc49   # placed_date midnight UTC edge fix (orthogonal)
```

---

## Next session priorities (top-down)

1. **Verify the "LIKELY RESOLVED" items above** — run targeted tests and re-read commits:
   ```bash
   pytest tests/test_integration_live.py tests/test_walk_forward.py::TestCreateLock tests/test_infrastructure_framework.py --tb=short
   git show b0c2ece -- src/mt5/mt5_real.py    # does it actually touch fromtimestamp?
   git show b0c2ece -- src/components/        # does it reconfigure logging to UTC?
   git show fb86280 -- src/components/execution.py   # does _active_trade_record now set on limit path?
   ```
2. **Tackle P2-8 — OB continuation rolling-50 monitor.** Primary decay metric per CLAUDE.md. Alarm at <60%. Needs a script that scans `knowledge_base/trade_journal/` or similar, builds rolling window, alerts when below threshold.
3. **Update `CLAUDE.md`** — both `### What changed April 14` block (add session 23 canary cache work) and the "47 test files" count (now higher after session 21/22/23). Optional but reduces drift.
4. **Low-priority cleanup** — P4-13 ATR comments, P4-14 XAUUSD Session ATR scope check.
5. **Defer** — P3-1/P3-2 simulations are CEO-approval-gated; do not dispatch without explicit ask.

---

## State at session 23 close (verify before acting)

- **HEAD:** `0c26d25` ("infra(canary): cache canary results per UTC day — subprocess dedup")
- **Test suite:** 1223 pass / 8 fail / 1 skip — no regressions from session 22 baseline
- **Live system:** 5 orchestrators running (per session 22 notes — no changes this session). Watchdog will pick up new orchestrator code on next restart cycle; first canary PASS after that will create `knowledge_base/meta/canary_cache.json`.
- **Uncommitted:** ZERO in `src/`, `tests/`, `prompts/`, `config/`. Only runtime data writes (logs, evaluations, sessions, no_trades, pipeline state) — normal live-system churn.
- **Pre-existing git stashes:** 3 intact — `23c083f`, `86a23fb`, `d0bbefa` (do not disturb).
- **Profile:** redacted_account Stellar 2-Step @ 1% risk active.
- **Cache file:** `knowledge_base/meta/canary_cache.json` does NOT exist yet — created on first canary PASS after next watchdog restart.

---

## Mandatory reading for session 24 (in order)

1. `CLAUDE.md`
2. `.context/02_session_handoffs/21_apr17_test_isolation_exposed_bugs_handoff.md` — punch list origin, write-guard architecture
3. `.context/02_session_handoffs/22_apr17_task_C_canary_dedup_handoff.md` — Task C design intent (historical — session 23 revised two decisions; see above)
4. **This file** (handoff 23)
5. `git show 0c26d25` — the canary cache commit
6. `src/components/canary_cache.py` — the new module (6 pure helpers + 3 cache-ops + module constants)
7. `src/components/orchestrator.py:1914-2000` — the modified call site
8. `tests/test_canary_cache.py` — 36 tests covering all 6 invalidation components, fail-safe paths, concurrency
9. `tests/conftest.py` — Layer 1+2 write guards (respect these; Task C tests honor them)
10. `.context/00_core/quick_reference_card.md` — live ops numbers

---

## Agents / workflow convention notes

- **Subagent dispatch:** Agent C1 (implementation, Opus 4.7 max effort) and Agent C2 (cold review, Opus 4.7 max effort, no prior context) as briefed in handoff 22. Both returned clean.
- **Main-thread discipline maintained:** main thread handled design revisions (PASS-only decision, baseline_hash addition), briefing, and this handoff. Implementation delegated.
- **Guard compliance:** Task C tests use `tmp_path` + module-ref monkeypatch for the cache constants in `canary_cache.py`. No test touches `knowledge_base/meta/canary_cache.json` directly. Cross-verified by running with the session-scoped `_production_path_guard` fixture active — zero `ProductionWriteError`s raised.

---

## Statistical / ops footnote

- Apr 17 continues the no-drawdown streak — no real drawdown state changes since the Apr 17 scrub of synthetic data (handoff 21). Current live WR still tracking 71.4% per handoff 15 baseline; no SPRT / CUSUM alarms reported in most recent watchdog heartbeats.
- Canary cost model revised: the $6–75/day worst-case scenario (handoff 22) was the **pre-cache** cost assumption. With `0c26d25` live, steady-state cost is a flat $12/mo regardless of watchdog restart storms. Budget line item can be closed out.

---

*End of session 23 handoff. Task C is DONE. Commit `0c26d25` is the canonical artifact.*
