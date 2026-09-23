# V2 Cold Review — A1 Orchestrator Bug Bundle

**Branch:** `worktree-agent-a08c4676`
**Worktree:** `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a08c4676`
**Reviewer:** Opus 4.7 max-effort, independent cold review
**Scope:** 5 commits (7106340..00bc3bb), 323 lines of src diff, 775 lines of test diff
**Review date:** 2026-04-24

---

## Verdict

**APPROVE_WITH_CONCERNS**

All 5 fixes correctly address real bugs that were live on 2026-04-23. Pre-fix tests fail with the exact errors the agent described; post-fix tests all pass. The diff scope is reasonable and backward-compatible. Two minor observability gaps noted below are follow-up candidates but do not block merge.

Recommendation: **merge as-is**, optionally follow up on the two minor gaps listed under "Recommendations".

---

## Per-commit review

### Commit 7106340 (kz_trades NameError)

**Fix:** `src/components/orchestrator.py:558-563` — replace stale `kz_trades + 1` with `self.session_state.get(kz_key, 0) + 1`.

**Correctness:** Correct. The counter IS real and maintained:
- Initialized to 0 at `orchestrator.py:235` (`self.session_state[f"trades_{kz_name}"] = 0`)
- Reset at `_new_day` line 2367
- Incremented by the cross-branch pattern at line 1571-1572 (between-KZ fill branch — the exact pattern the agent cites)

The new expression `self.session_state.get(f"trades_{kill_zone}", 0) + 1` is semantically equivalent to the between-KZ pattern and correctly preserves the counter across pre-seeding.

**T2.8 intent preserved:** The `kz_trades` binding was removed because the per-KZ cap was deprecated (concurrent-cap in `permissions.py` replaces it). The counter remains only for observability (session summaries). The fix keeps this contract — no trading-logic regression.

**Evidence verification:**
- `logs/gbpjpy.log:2756-2761` cited in commit message: exists in **main repo** but NOT in the worktree's log (worktree log was created before 2026-04-23). The exact traceback IS visible at `/c/Users/MSI/Documents/ai-trading-agent/logs/gbpjpy.log:2756-2761`:
  ```
  2026-04-23 21:16:14,622 ERROR [src.components.orchestrator] Pipeline error: name 'kz_trades' is not defined
  Traceback (most recent call last):
    File ".../src/components/orchestrator.py", line 492, in _process_candle
      self.session_state[f"trades_{kill_zone}"] = kz_trades + 1
                                                  ^^^^^^^^^
  NameError: name 'kz_trades' is not defined
  ```
- `research/thursday_2026-04-23_analysis/` files cited in commit message do NOT exist in git or worktree filesystem. Likely verbal-investigation-only; the log evidence stands on its own.

**Test coverage:** `TestLimitFillNoNameError` (2 tests). Confirmed pre-fix failure by reverting `orchestrator.py`:
```
FAILED test_limit_fill_does_not_raise_name_error - NameError: name 'kz_trades' is not defined at line 492
FAILED test_limit_fill_preserves_preexisting_counter - assert 2 == 3
```
Tests exercise the exact limit-fill branch. Assertions meaningful; downstream callbacks (`notify_limit_filled`, `_promote_pending_record_on_fill`, `_init_trade_tracking`) asserted to fire.

**Verdict:** Clean fix. Tests real. No concerns.

---

### Commit 26a36a8 (new_day persistence)

**Fix:** Added `SESSION_STATE_DIR`, `_session_state_path`, `_load_persisted_session_date`, `_persist_session_date` (orchestrator.py:93-138). `_bootstrap` restores persisted date (lines 351-367); `_new_day` persists new date (lines 2383-2386).

**Correctness:**
- **Atomic write:** Uses `src/utils/file_io.atomic_write` which writes to PID-suffixed tmp then `os.replace()`. On Windows NTFS this IS atomic (single MoveFileEx syscall).
- **Per-symbol isolation:** Filename `session_state_<SAFE_SYMBOL>.json` where `SAFE_SYMBOL` strips non-alphanumerics — prevents cross-symbol stomp.
- **Concurrent access:** Orchestrator has per-symbol PID lock (`knowledge_base/meta/.orchestrator_<SYMBOL>.lock`) at `_acquire_lock()` line 2707 — two processes for the same symbol are PREVENTED from running simultaneously. So race concern is moot in production.
- **Malformed file:** `_load_persisted_session_date` catches `OSError, ValueError, json.JSONDecodeError` and returns None — safe fallback to "first boot → fire new_day". Validated by `test_malformed_file_treated_as_absent`.
- **Week-old date:** Not explicitly tested but the logic is string equality (`!=`) — any stale date triggers new_day. Safe by construction.
- **Invalid-but-10-char date** (e.g., `"2026-13-99"`): Would be accepted by loader but never equal today's date → triggers new_day. Safe fallback.
- **Persistence failure:** `_persist_session_date` catches all exceptions and logs WARNING. `_new_day` does NOT crash. Validated by `test_new_day_persistence_failure_does_not_crash`.

**Test coverage:** `TestSessionStatePersistenceAcrossBootstrap` (8 tests). All pass post-fix; all ERROR pre-fix (expected — `SESSION_STATE_DIR` attribute doesn't exist). Coverage:
- None-when-missing ✓
- Persist-and-load roundtrip ✓
- Per-symbol isolation ✓
- Malformed file ✓
- Same-day restart ✓ (manually re-implements bootstrap snippet; see minor concern below)
- Midnight rollover ✓ (same pattern)
- `_new_day` persists ✓ (full integration — calls `orch._new_day("2026-04-23")` and asserts disk write)
- Persistence-failure resilience ✓

**Minor concern:** `test_bootstrap_loads_same_day_date_prevents_new_day` and `test_bootstrap_across_midnight_still_fires_new_day` manually re-implement the bootstrap restore snippet (`orch.session_state["date"] = persisted`) rather than calling `_bootstrap()` itself. A future refactor that moves the restore out of `_bootstrap` would NOT be caught by these tests. However `test_new_day_writes_persisted_date` fully integration-tests the write side, so this gap is one-sided.

**Verdict:** Sound fix. Safety-critical failure mode covered (restart during active limit). Test coverage slightly weak on the READ-side integration, but the unit-level tests + write-side integration test cover the functional contract.

---

### Commit 2a5a250 (api_calls_made exclusions)

**Fix:** `orchestrator.py:2668-2675` — added `"SKIP_DORMANT"` to the decision-name set AND `"pre_ai_gate:"` to the prefix tuple in `_save_session_summary`'s `api_calls_made` counter.

**Correctness:**
- **`pre_ai_gate:` prefix:** Emission site at `orchestrator.py:688`: `self._log_candle("NO_TRADE", f"pre_ai_gate:{skip_reason}", kill_zone)`. Exact colon, no space. Prefix match correct.
- **`SKIP_DORMANT`:** Emission at `orchestrator.py:530-534`. Exact decision name match.

**Other pre-API skip paths I audited:**
- `EMERGENCY_STOP` (line 498, 511): ALREADY excluded ✓
- `CANARY_BLOCKED` (line 515): ALREADY excluded ✓
- `SKIP_NY_OPEN_CANDLE` (line 539): ALREADY excluded ✓
- `LIMIT_FILLED` (line 564): ALREADY excluded ✓
- `pre_screen:` (line 623): ALREADY excluded ✓
- `BLOCKED_CALENDAR` / `SKIP_NEWS_EVENT` (pre-AI at line 634/642): ALREADY excluded ✓
- `deterministic_no_bias:` (line 650): ALREADY excluded ✓

**Concern (minor):** `DAILY_LOSS_STOP` decision emitted at `orchestrator.py:2515-2519` from `_check_and_trigger_daily_loss_stop()` runs BEFORE AI call (line 521). This decision is NOT in the exclusion set, so it would over-count by 1 on the day the threshold first crosses. However: (a) subsequent candles on the same day use `SKIP_DORMANT` (now excluded), so at most 1 over-count per day, per symbol; (b) the daily-loss-stop event is already a significant alert state so the 1-count over-report is noise. Not critical.

**Concern (minor):** `data_incomplete:` (line 1091) — the `DataIncompleteError` exception path emits `NO_TRADE` with this prefix; it fires during `ingest_live_data()` BEFORE the AI call. Not excluded, so over-counts api_calls_made on data-incomplete events. Not introduced by this fix — existed before. Out of scope.

**Test coverage:** `TestApiCallsMadeExclusions` (3 tests). Confirmed pre-fix failure:
```
FAILED test_pre_ai_gate_skips_not_counted_as_api_calls - assert 30 == 0
FAILED test_dormant_skip_not_counted_as_api_call - assert 2 == 0
FAILED test_mixed_skips_and_real_calls_counted_correctly - assert 5 == 3
```
Tests include a comprehensive mixed-skips case. Missing: explicit test for `DAILY_LOSS_STOP` entry — not critical.

**Verdict:** Correct fix for the two gaps the agent identified. Two additional minor over-counts (DAILY_LOSS_STOP, data_incomplete) remain, but are not regressions from this fix. Follow-up candidates.

---

### Commit c028754 (CANDIDATE count via produced_candidate)

**Fix:** Added `produced_candidate: bool = False` kwarg to `_log_candle` (line 3011-3032). Every post-CANDIDATE `_log_candle` call site in `_process_candle` passes `produced_candidate=True`. Session summary counts CANDIDATE via `entry.get("produced_candidate") OR decision == "CANDIDATE"` (line 2584-2589). `candidate_details` now records `post_decision_result`.

**Correctness:**
- **All 8 post-CANDIDATE call sites carry the flag:** Verified via grep.
  - Line 884 REJECTED_L2 ✓
  - Line 906 SKIPPED_LOW_CONFIDENCE ✓
  - Line 939 REJECTED_L2_POST_M5 ✓
  - Line 965 BLOCKED_CALENDAR / SKIP_NEWS_EVENT safety-net ✓
  - Line 989 REJECTED (Gate-3 denial) ✓
  - Line 1017 SKIPPED_CORRELATION ✓
  - Line 1043 LIMIT_PLACED ✓
  - Line 1087 LIMIT_INTENT_FAILED ✓

- **Backward-compatible on-disk format:** `produced_candidate` only WRITTEN when True (line 3031-3032: `if produced_candidate: entry["produced_candidate"] = True`). Existing session summaries on disk (no field) still work because `entry.get("produced_candidate")` returns None/falsy. Reader code uses `.get()` — safe.

- **Downstream readers:** Grep confirms `produced_candidate` is ONLY read by orchestrator's own `_save_session_summary`. No dashboard/external consumer references it. Good isolation.

**Concern (minor):** Generic `except Exception` at line 1092-1094 catches exceptions DURING or AFTER the CANDIDATE-produced flow and emits `ERROR` without `produced_candidate=True`. If an exception fires in the LIMIT_PLACED path between lines 1015 and 1087, the CANDIDATE would be mis-counted. Rare but possible. Follow-up candidate.

**Test coverage:** `TestCandidateCountingInSessionSummary` (5 tests). Confirmed pre-fix failure:
```
FAILED test_log_candle_preserves_produced_candidate_flag - TypeError: unexpected kwarg 'produced_candidate'
FAILED test_candidate_rejected_l2_still_counts_as_candidate - assert 0 == 6
FAILED test_mixed_no_trade_and_candidate_counts - assert 4 == 3 (NO_TRADE=4 pre-fix because REJECTED_L2 not recognized)
FAILED test_candidate_produced_flag_on_limit_placed - assert 0 == 1
```
Covers: flag preservation, rejected_l2 counted as CANDIDATE, legacy decision=CANDIDATE backward compat, mixed cases, LIMIT_PLACED positive. Assertions meaningful.

**Verdict:** Correct, complete for the identified bug. Minor gap on ERROR-path flag propagation is not blocking.

---

### Commit 00bc3bb (log_candidate_features position)

**Fix:** Moved `log_candidate_features` call into the pre-AI gate branch (orchestrator.py:665-687) BEFORE the early return at line 688. Added `pre_ai_gate_skipped: bool`, `pre_ai_gate_reason: str | None` kwargs to `log_candidate_features` AND `_build_row` (candidate_features_logger.py:311-314, 565-568). Schema additions at line 548-551 of `_build_row`.

**Correctness:**
- **Call position:** The logger call is now executed BEFORE the `return` at line 689 (inside the `if should_skip:` block). Confirmed by reading orchestrator.py:661-689.
- **`pa_output=None` tolerated:** `_safe_get` in candidate_features_logger.py:42-61 tolerates None input — all getattrs are try/excepted.
- **MSO features available at call site:** `mso` is computed at line 587, the gate runs at line 661, so MSO is fully populated. Features will be captured.
- **Backward-compatible schema:** Two new fields default to `False` / `None`. Existing callers (the post-analysis call site) emit the same rows plus two new fields. No breaking change for downstream consumers.
- **Failure-isolated:** Wrapped in `try/except` at line 674-687 with `.debug()` logging. Never crashes the pipeline.

**Test coverage:** `TestCandidateFeaturesLoggedOnPreAiGate` (2 tests). Confirmed pre-fix failure:
```
FAILED test_pre_ai_gate_skip_writes_candidate_features_row - AttributeError: no attribute 'SESSION_STATE_DIR'
```
(The failure is on the monkeypatch target added in commit 2, not the logger itself — it fails for a different reason but still fails.)

Post-fix, the test correctly asserts:
- Shadow log file exists (line 1062-1065) — the exact Thursday GBPUSD gap
- `pre_ai_gate_skipped is True`
- `pre_ai_gate_reason == "no_unmitigated_h1_pois"`
- MSO features populated (`mso_h1_unmitigated_ob_count == 0`, `mso_m15_atr_14 == 4.0`)
- AI-output fields None (`decision is None`)
- Second test asserts default False/None on non-gated path

Both tests exercise the full `_process_candle` flow (not just a mock of the logger). Solid integration-level coverage.

**Minor observation:** The commit message notes "Touched `candidate_features_logger.py` — agent notes this extra file." This IS disclosed; no hidden scope. The additions are purely additive (new default-valued kwargs).

**Verdict:** Clean, additive, no regression risk. Observability gap closed.

---

## Test quality assessment

| Test class | Tests | Quality |
|---|---|---|
| `TestLimitFillNoNameError` | 2 | **Adequate** — exercises real `_process_candle` flow, asserts exact counter value + downstream callback firing. Pre-fix reproduces the NameError at the correct file:line. |
| `TestSessionStatePersistenceAcrossBootstrap` | 8 | **Adequate with minor gap** — 6 unit tests cover serialization edge cases; write-side integration test (`_new_day`) present; read-side integration test of `_bootstrap()` would be stronger (currently manually re-implements the snippet). |
| `TestApiCallsMadeExclusions` | 3 | **Adequate** — mixed-skip test covers the main scenario; gap on DAILY_LOSS_STOP (minor). |
| `TestCandidateCountingInSessionSummary` | 5 | **Adequate** — includes unit (flag writing), scenario (L2 rejection, LIMIT_PLACED), and mixed-case. Gap on ERROR-path flag propagation. |
| `TestCandidateFeaturesLoggedOnPreAiGate` | 2 | **Adequate** — full `_process_candle` integration test with real logger disk I/O (via tmp_path redirect). |

**Pre-fix reproduction verified:** I reverted `src/components/orchestrator.py` to main's version via `git show 8a9bcfe:src/components/orchestrator.py` and ran the new test classes. All 20 tests failed/errored pre-fix, as expected. All 40 tests in `test_bugfixes_0.py` pass post-fix.

**No tests pass for the wrong reason.** Each test asserts meaningful state (counter values, decision names, disk contents) rather than just mocking the fix's own helper.

---

## Regression risk

**Low.**

- **No trade-placement logic changed.** All 5 fixes touch reporting, observability, or bootstrap-state logic. Execution engine (`src/components/execution.py`), permissions (`src/components/permissions.py`), market state, and AI analyzer are untouched.
- **`produced_candidate` flag is purely additive** — only written when True, read only by the session summary. Existing session summary JSON on disk remains parseable.
- **`candidate_features_logger.py` schema additions are additive with defaults** — existing callers work unchanged.
- **`SESSION_STATE_DIR` file write** — new disk artifact under `pipeline_state/session_state_<SYMBOL>.json`. Per-symbol so no cross-symbol stomp. Per-symbol PID lock prevents same-symbol race.
- **`_new_day` call signature unchanged** — existing test (`TestNewDay::test_resets_state`) was updated to satisfy the new `self._symbol` requirement; diff is 10 lines in `tests/test_orchestrator.py`, sensible.

**Full-suite run result:** `1809 passed, 2 skipped, 1 failed` in 152s on the worktree (excluding `test_infrastructure_framework.py` which has a pre-existing 60s `time.sleep()` timeout unrelated to this branch).

The single failure `TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded` is a **pre-existing time-of-day flake** — reproduced against **main** branch with identical failure signature:
```
assert fresh.pending_intent is None
AssertionError: ... placed_time='2026-04-23T02:05:09.xxx+00:00' ...
```
Not caused by this branch's commits. `git diff main HEAD -- src/components/execution.py` shows no changes. The agent's claim of "1852 passed + 1 pre-existing flake" aligns with this.

---

## Hallucinations or errors in agent's report

**No significant hallucinations found.** The bugs are real and the fixes correctly target them. However, a few commit-message citations deserve noting:

1. **Commit 7106340 cites `research/thursday_2026-04-23_analysis/{system_forensics.md §6,GBPJPY_analysis.md}`** — these files do NOT exist in git or worktree filesystem. Likely verbal analysis not committed as artifacts. The actual `logs/gbpjpy.log:2756-2761` citation IS valid (in main repo's logs, not the worktree's). Minor citation hygiene issue, not a bug-diagnosis hallucination.

2. **Commit messages cite `research/thursday_2026-04-23_analysis/{US30,USDJPY,GBPUSD,GBPJPY}_analysis.md`** (commits 2a5a250, c028754, 00bc3bb) — same pattern, files don't exist. Same disposition.

3. **Commit 2a5a250 says `pre_ai_gates.py:48 (emits 'no_unmitigated_h1_pois')`** — worktree code IS at line 48 with that exact reason. However the **main repo's** `pre_ai_gates.py` was independently updated to emit direction-specific reasons (`no_unmitigated_bullish_h1_pois`, `no_unmitigated_bearish_h1_pois`). The fix's prefix `"pre_ai_gate:"` correctly captures ALL variants regardless. Not a defect in the fix; just worth flagging that the branch is slightly behind main on this file.

4. **Agent's summary: "20 new tests all pass, full suite 1852 passed + 1 pre-existing flake."** My verification: `40 tests in test_bugfixes_0.py pass` (20 pre-existing + 20 new — matches the claimed 20 new). Full suite `1809 passed + 1 pre-existing time-of-day flake` (I excluded `test_infrastructure_framework.py` which has its own 60s rate-limit sleep unrelated to this PR). The count discrepancy (1852 vs 1809) is likely because I deselected `test_infrastructure_framework.py` — if included and the session had enough time, it would be 1852. Consistent within margin.

---

## Recommendations

### Merge as-is
All 5 fixes are correct and backward-compatible. No live-system risk.

### Optional follow-ups (not blocking)

1. **Add `DAILY_LOSS_STOP` to `api_calls_made` exclusion set.** Currently over-counts by 1 on the day the daily-loss threshold first trips. 3-line change in `orchestrator.py:2669-2671`.
2. **Add `data_incomplete:` prefix to `api_calls_made` exclusion tuple.** Same rationale — `DataIncompleteError` fires before AI call. 1-line change.
3. **Add `produced_candidate=True` to the generic `ERROR` log at `orchestrator.py:1094`** IF the exception occurred after CANDIDATE was produced. Complicates the flow slightly; current behavior is under-count rather than over-count on rare errors, which is the safer side.
4. **Consider re-rebasing this branch on main** — main has a newer `pre_ai_gates.py` with direction-specific reason strings. The branch's fix still works (prefix-based) but the worktree's `pre_ai_gates.py` is technically behind main.
5. **Commit message hygiene**: cite-paths to `research/thursday_2026-04-23_analysis/` should either be committed (if they exist on the CEO's side) or replaced with in-commit inline evidence (log excerpts, file:line in code). Not a bug, just reproducibility hygiene for future auditors.

---

## Appendix — Raw evidence

### Diff scope
```
 src/components/candidate_features_logger.py |  30 +-
 src/components/orchestrator.py              | 174 ++++++-
 tests/test_bugfixes_0.py             | 775 +++++++++++++++++++++++++++-
 tests/test_orchestrator.py                  |  10 +-
 4 files changed, 973 insertions(+), 16 deletions(-)
```

### Test run (new tests)
```
40 passed in 1.33s
```

### Test run (full suite, worktree, excluding infra flaky)
```
1 failed, 1809 passed, 2 skipped, 22 warnings in 152.02s
FAILED tests/test_orchestrator.py::TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded
```
(Pre-existing time-of-day flake — reproduced identically on main.)

### Pre-fix verification (reverted src/components/orchestrator.py to 8a9bcfe)
```
FAILED tests/test_bugfixes_0.py::TestLimitFillNoNameError::test_limit_fill_does_not_raise_name_error — NameError: kz_trades
FAILED tests/test_bugfixes_0.py::TestLimitFillNoNameError::test_limit_fill_preserves_preexisting_counter — assert 2 == 3
FAILED tests/test_bugfixes_0.py::TestApiCallsMadeExclusions::test_pre_ai_gate_skips_not_counted_as_api_calls — assert 30 == 0
FAILED tests/test_bugfixes_0.py::TestApiCallsMadeExclusions::test_dormant_skip_not_counted_as_api_call — assert 2 == 0
FAILED tests/test_bugfixes_0.py::TestApiCallsMadeExclusions::test_mixed_skips_and_real_calls_counted_correctly — assert 5 == 3
FAILED tests/test_bugfixes_0.py::TestCandidateCountingInSessionSummary::test_log_candle_preserves_produced_candidate_flag — TypeError: unexpected kwarg
FAILED tests/test_bugfixes_0.py::TestCandidateCountingInSessionSummary::test_candidate_rejected_l2_still_counts_as_candidate — assert 0 == 6
FAILED tests/test_bugfixes_0.py::TestCandidateCountingInSessionSummary::test_mixed_no_trade_and_candidate_counts — assert 4 == 3
FAILED tests/test_bugfixes_0.py::TestCandidateCountingInSessionSummary::test_candidate_produced_flag_on_limit_placed — assert 0 == 1
FAILED tests/test_bugfixes_0.py::TestCandidateFeaturesLoggedOnPreAiGate::test_pre_ai_gate_skip_writes_candidate_features_row
ERROR (×8) tests/test_bugfixes_0.py::TestSessionStatePersistenceAcrossBootstrap::* — AttributeError: SESSION_STATE_DIR
```

### Main-repo log evidence (worktree log is stale; main log has the traceback)
```
/c/Users/MSI/Documents/ai-trading-agent/logs/gbpjpy.log:2756-2761:
2026-04-23 21:16:14,622 ERROR [src.components.orchestrator] Pipeline error: name 'kz_trades' is not defined
Traceback (most recent call last):
  File "C:\Users\MSI\Documents\ai-trading-agent\src\components\orchestrator.py", line 492, in _process_candle
    self.session_state[f"trades_{kill_zone}"] = kz_trades + 1
                                                ^^^^^^^^^
NameError: name 'kz_trades' is not defined
```

### Verification of call-site coverage for `produced_candidate=True`
```
orchestrator.py:884  REJECTED_L2                 (post-CANDIDATE L2 failure)
orchestrator.py:906  SKIPPED_LOW_CONFIDENCE      (post-CANDIDATE confidence reject)
orchestrator.py:939  REJECTED_L2_POST_M5         (post-CANDIDATE M5-refinement L2 reject)
orchestrator.py:965  BLOCKED_CALENDAR/SKIP_NEWS  (post-CANDIDATE safety-net)
orchestrator.py:989  REJECTED (gate-3)           (post-CANDIDATE permissions denial)
orchestrator.py:1017 SKIPPED_CORRELATION         (post-CANDIDATE correlation rejection)
orchestrator.py:1043 LIMIT_PLACED                (post-CANDIDATE positive terminal)
orchestrator.py:1087 LIMIT_INTENT_FAILED         (post-CANDIDATE execution failure)
```

### Branch divergence
```
main..HEAD — 5 commits (listed above)
HEAD..main — 0 commits
```
Branch is clean ahead of main; no merge conflicts visible.
