# Session 22 Handoff — Task C: Canary Subprocess Deduplication

**Session:** 22 (Apr 17, 2026 — CEO Borhen, GTOS)
**Status at close:** 2 commits shipped this session; Task C teed up for fresh session.

---

## What shipped in session 22 (verify via `git log -3`)

| Commit | What | Files |
|---|---|---|
| `823dc49` | `fix(orchestrator): drop placed_date filter in pending-record recovery — midnight UTC edge` | `orchestrator.py` + `tests/test_integration_live.py` (+137 test lines) |
| `8a42afb` | `infra(canary): read model/effort from config + regenerate 12 fixtures under T7 C-gate + tests` | `canary_test.py`, `generate_canary_fixtures.py`, 13 deleted + 12 new fixtures, `baseline.json`, `last_run.json`, `manifest.json`, new `tests/test_canary.py` (249 lines, 11 tests) |

Test suite after both commits: **1187 pass / 8 fail / 1 skip**. The 8 failures are pre-existing, outside the scope of this session.

Both commits went through cold Opus 4.7 reviewer with GO verdicts.

---

## Strategic pivot during session 22 (worth remembering)

CEO asked whether to upgrade live primary-analyzer from Sonnet 4.6 → Opus 4.7 + max effort, with subscription mode for cost. I researched `research/academic_pipeline/results/P2C_opus_max_results_v1.md` (Apr 12 head-to-head on 121 MSOs, same prompt, effort=max). Result: Sonnet wins on all dimensions for this specific task.

- Opus: CR=19%, WR=60.9%, CR×WR=0.116, $0.154/call. Rejects-WR=65.3% (over-rejects winners).
- Sonnet: CR=38%, WR=69.6%, CR×WR=0.265, $0.035/call.

**Decision (CEO-approved):** keep Sonnet 4.6 + API billing for live gate. Opus 4.7 + subscription mode is reserved for research/KAP pipeline where reasoning depth matters. This is now saved in memory (`project_opus_vs_sonnet_p2c.md`).

If a future session proposes an Opus upgrade for the live gate, **cite this finding and re-run P2C before deciding**.

---

## Task C scope — canary subprocess deduplication

### The problem

`orchestrator.py:1914-1937` runs `subprocess.run(["python", "scripts/canary_test.py"], timeout=120)` every time a kill zone is entered. Invocation site: `_enter_kill_zone` at line 1943.

Cost scaling factors:
- 5 live orchestrators (one per symbol)
- Each has 2-3 kill zones per day
- Watchdog restarts every ~15 min → if restart happens inside a KZ, `session_state["current_kill_zone"]` resets to None → next tick re-enters the KZ → canary re-fires
- 12 fixtures × $0.035 ≈ $0.42 per canary run

Upper bound: 5 symbols × 3 KZ × ~12 restarts/KZ = 180 canary runs/day × $0.42 = **$75/day worst case**. Typical (no restart storms): ~$6-15/day. Either way, it's wasted spend — canary output is deterministic in `(date_utc, model, effort, fixtures_hash, prompt_hash)`.

### The design

Cache canary results keyed by the 5-component hash. On `_enter_kill_zone`, check cache before spawning subprocess. Skip if cached valid result exists for today under same config.

**Cache file:** `knowledge_base/meta/canary_cache.json`

**Schema:**
```json
{
  "date_utc": "2026-04-17",
  "model": "claude-sonnet-4-6",
  "effort": "max",
  "fixtures_hash": "sha256:abc123...",
  "prompt_hash": "sha256:def456...",
  "passed": true,
  "decision_matches": 12,
  "fixtures_count": 12,
  "completed_at_utc": "2026-04-17T07:03:14Z",
  "schema_version": 1
}
```

**Invalidation triggers (any one → miss → rerun):**
1. `date_utc` — new UTC day
2. `model` — agent_config.yaml `ai.primary_model` change
3. `effort` — agent_config.yaml `ai.primary_effort` change
4. `fixtures_hash` — any content change in `scripts/canary_fixtures/*.json` (excluding baseline/last_run/manifest)
5. `prompt_hash` — rendered output of `build_system_prompt(config)` changes

**Write semantics:** atomic via `tempfile` + `os.replace`. Concurrent writes from 5 orchestrators are benign under same hash (last-writer-wins, result identical).

**Fail-safe:** any cache read exception → fall through to full subprocess; rewrite cache with fresh result. Never block a canary run because the cache file is corrupt.

### Expected cost impact

- Before: $6-75/day (restart-sensitive)
- After: ~1 canary per UTC day = $0.42/day = **$12/mo flat**
- Savings: 60-95% depending on restart frequency

### Orchestrator changes

File: `src/components/orchestrator.py`
Function: `_run_canary_check()` (line 1914-1937)

Before `subprocess.run`:
```python
cache = _load_canary_cache()
fixtures_hash = _compute_fixtures_hash()
prompt_hash = _compute_prompt_hash(self.config)
today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

if _canary_cache_valid(cache, self.model, self.effort, fixtures_hash, prompt_hash, today_utc):
    logger.info(f"[canary] cache HIT for {today_utc} — skipping subprocess")
    return cache["passed"]
```

After successful subprocess (inside the `returncode == 0` branch):
```python
_write_canary_cache({
    "date_utc": today_utc,
    "model": self.model,
    "effort": self.effort,
    "fixtures_hash": fixtures_hash,
    "prompt_hash": prompt_hash,
    "passed": True,
    "decision_matches": 12,  # parse from stdout if needed
    "fixtures_count": 12,
    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    "schema_version": 1,
})
```

Helpers (new, in orchestrator.py or a new `src/components/canary_cache.py`):
- `_load_canary_cache() -> dict | None`
- `_canary_cache_valid(cache, model, effort, fh, ph, today) -> bool`
- `_write_canary_cache(data: dict) -> None` — atomic
- `_compute_fixtures_hash() -> str`
- `_compute_prompt_hash(config) -> str`

### NOT in scope

- `scripts/canary_test.py` — keep pure. All caching in orchestrator.
- `config/agent_config.yaml` — unchanged.
- `prompts/` — unchanged.
- Any trading logic, risk, execution — explicitly out of scope.
- OB continuation rolling-50 monitor (P2-8 separate).
- P1-4 MT5 UTC, P1-5 logger UTC, P2-6 refusal monitor scheduler — separate sessions.

---

## Test plan

New file: `tests/test_canary_cache.py` (~200 lines, ~10 tests):

1. `test_fixtures_hash_changes_on_content_change`
2. `test_fixtures_hash_ignores_baseline_last_run_manifest`
3. `test_prompt_hash_changes_on_config_change`
4. `test_cache_valid_all_fields_match`
5. `test_cache_invalid_on_date_change`
6. `test_cache_invalid_on_model_change`
7. `test_cache_invalid_on_effort_change`
8. `test_cache_invalid_on_fixtures_change`
9. `test_cache_invalid_on_prompt_change`
10. `test_cache_read_corrupt_file_returns_none` (fail-safe)
11. `test_cache_write_atomic_under_concurrent_calls` (threading.Thread ×5)
12. Integration test: monkeypatch `subprocess.run`, call `_run_canary_check` twice, assert second call does NOT spawn subprocess.

All tests must honor the Layer 1 + 2 write guards in `tests/conftest.py`. Use `tmp_path` + module-ref monkeypatch. **Never write to `knowledge_base/meta/canary_cache.json` directly in tests.**

Expected suite result after Task C: **1187 → ~1199 pass**.

---

## Subagent dispatch plan (only after CEO approval)

Because Task C touches `src/components/orchestrator.py`, it is **trading-adjacent**. The orchestrator is the coordinating state machine for live trading. Canary is a safety gate — a bug that returns stale PASS when actual state FAILS would defeat drift detection.

Per WF-1 discipline (CLAUDE.md): **CEO must approve before any code change to `src/components/`.**

Brief the CEO with:
1. The design summary above.
2. The cost number (~$12/mo vs $6-75/day).
3. The risk: **if cache invalidation has a bug, stale PASS is possible.** All 5 hash components are designed to invalidate on any change; fail-safe fallthrough reruns on error. Explicit mitigations in test plan.
4. Scope: ~200 lines new code + ~200 lines tests.

### Agent C1 — implementation (Opus 4.7, max effort)

Brief:
- Implement the 5 helpers + modify `_run_canary_check()` per above
- Add `tests/test_canary_cache.py` with all 12 tests
- Run full pytest suite; expected 1187 → ~1199
- DO NOT touch `scripts/canary_test.py`
- DO NOT touch `config/`, `prompts/`, or any other `src/components/` file
- Report: diff stat, test result, any invariants found

### Agent C2 — cold review (Opus 4.7, max effort, NO prior context)

Brief the reviewer blank-slate. Verify:
- All 5 invalidation components work (stash-and-retest if needed)
- No race conditions under concurrent writes from 5 orchestrators
- Fail-safe fallthrough proven (corrupt JSON test)
- No regressions in `_run_canary_check()` call semantics (return value, side effects)
- Full pytest suite 1187 → ~1199, no regressions
- Scope boundary (no leaks into trading logic, prompts, config)
- Respect 3 pre-existing stashes — do not disturb

### Main thread — stage, commit, handoff

- Stage only in-scope files (orchestrator.py + tests/test_canary_cache.py + optional src/components/canary_cache.py)
- Commit with detailed message (pattern from `8a42afb`)
- Update `.context/02_session_handoffs/23_*` with close-out state
- Optional: update `CLAUDE.md` `### What changed` section

---

## Open questions for CEO (resolve before Agent C1 dispatches)

1. **Cache TTL** — UTC-day only, or shorter (e.g., 6h)? *Recommended: UTC-day — matches natural "canary once per trading day" semantics. Simpler. If a mid-day model regression happens we'd still want drift detection; proposal: keep UTC-day but allow manual invalidation via `rm knowledge_base/meta/canary_cache.json`.*
2. **Fail-safe strategy** — on cache error, fall through to full subprocess (never block trading) vs. raise alarm? *Recommended: fall through + log WARN. Never block on cache infrastructure.*
3. **Cache write on canary FAIL** — cache the FAIL result too, so repeat calls don't re-run the failed canary? *Recommended: yes — the whole point is determinism; if canary fails at KZ-1, canary should fail at KZ-2 under same hash. Orchestrator behavior on cached FAIL: identical to fresh FAIL (block evaluations).*
4. **Helpers location** — inline in orchestrator.py, or new `src/components/canary_cache.py` module? *Recommended: new module. Keeps orchestrator focused on coordination. Easier to test in isolation.*
5. **Prompt hash source** — hash the `primary_analyzer_prompt.py` file bytes, or the rendered `build_system_prompt(config)` output? *Recommended: rendered output. Robust to refactors that split the prompt across files without changing meaning.*

---

## State at session 22 close (verify before acting)

- Last commit: `8a42afb`
- Test suite: 1187 pass / 8 fail / 1 skip — no regressions
- Live system: 5 orchestrators running under PID lock, watchdog healthy
- No uncommitted changes in `src/`, `prompts/`, or `config/`
- 3 pre-existing stashes (`23c083f`, `86a23fb`, `d0bbefa`) intact
- MEMORY.md updated with Opus vs Sonnet P2C pointer

---

## Mandatory reading for the fresh session (in order)

1. `CLAUDE.md`
2. `.context/02_session_handoffs/21_apr17_test_isolation_exposed_bugs_handoff.md` — prior state
3. This file
4. `git show 8a42afb` — understand the canary-refresh commit fully
5. `src/components/orchestrator.py:1914-1947` — canary call site
6. `scripts/canary_test.py` — what the subprocess does
7. `tests/conftest.py` — Layer 1+2 write guards (respect these)
8. `.context/00_core/quick_reference_card.md` — live numbers

Fresh session: run the Phase 2 verification from `.context/02_session_handoffs/21_apr17_FRESH_SESSION_PROMPT.md`. Confirm test baseline is `1187/8/1` (not 1164/13 — that was pre-session-21 baseline).

---

**End of session 22 handoff. Next session picks up Task C; Tasks A+B complete.**
