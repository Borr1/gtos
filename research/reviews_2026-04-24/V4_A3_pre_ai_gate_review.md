# V4_A3 — Independent Review: pre-AI gate formalization + watchdog drift check

**Reviewer:** Opus 4.7, max effort, max-depth reasoning
**Date:** 2026-04-24
**Branch:** `worktree-agent-a97f76b5`
**Worktree:** `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a97f76b5`
**Commits under review:**
1. `a84abde` — feat(pre-ai-gate): formalize direction-aware H1 POI availability upgrade
2. `3da685b` — chore(watchdog): warn on uncommitted working-tree changes at startup
**Base commit:** `8a9bcfe`

---

## Verdict

**APPROVE both commits with one advisory.**

- `a84abde` is bit-exact with the code running live since the 2026-04-22 watchdog restart. 19/19 tests pass. The upgrade IS strictly narrower than L2 `h1_poi_exists` under current orchestrator wiring (proof below), so it cannot suppress a trade that L2 would have passed. No code change is required.
- `3da685b` is a non-fatal, additive warning. PowerShell parse is clean; the git-status filter behaves as intended in a simulated run against the dirty main worktree (11 code paths flagged, runtime-state paths correctly excluded).
- **Advisory (not a blocker):** the direction-agnostic fallback in `h1_poi_availability` is dead code under the current orchestrator, and the bearish branch has never fired in production. Both are theoretical gaps that become newly relevant if (a) the A7 market_state structural-bias finding is fixed so bearish D1 bias starts emitting, or (b) an upstream change allows the AI to produce a trade direction that differs from `daily_bias`. No immediate change needed; flagged for the file.

---

## 1. Commit `a84abde` — pre-AI gate formalization

### 1.1 Live-drift check (the critical claim)

The commit message claims: *"Commits the direction-aware upgrade that has been running live since watchdog restart on 2026-04-22."*

Verified by byte-diffing the committed blob against the live working-tree file in the main worktree:

```
$ diff <(git show a84abde:src/components/pre_ai_gates.py) src/components/pre_ai_gates.py
(no diff)
$ diff <(git show a84abde:src/components/orchestrator.py | sed -n '585,600p') <(sed -n '585,600p' src/components/orchestrator.py)
(no diff)
```

**Zero drift.** The formalized code is identical to what MT5 has been running since the 2026-04-22 watchdog respawn. The "formalization only, no behavior change" claim holds.

### 1.2 Code inspection

`src/components/pre_ai_gates.py:49-65` (new direction-aware branch):

```python
directional = bias in ("bullish", "bearish")

if directional:
    has_unmitigated_ob = any(
        (not ob.mitigated) and ob.type == bias for ob in h1_tf.order_blocks
    )
    if has_unmitigated_ob:
        return False, ""

    has_unretested_breaker = any(
        (not bb.is_retested) and bb.direction == bias
        for bb in h1_tf.breaker_blocks
    )
    if has_unretested_breaker:
        return False, ""

    return True, f"no_unmitigated_{bias}_h1_pois"
```

The three reason strings emitted in log_candle are:
- `no_unmitigated_bullish_h1_pois` (line 65 when `bias == "bullish"`)
- `no_unmitigated_bearish_h1_pois` (line 65 when `bias == "bearish"`)
- `no_unmitigated_h1_pois` (line 76, direction-agnostic fallback)

All three match the brief's expected strings exactly. Live-log evidence (see section 1.5) confirms the first and third are observed in production; the second is absent because bearish bias has not emitted.

`src/components/orchestrator.py:591-593` passes `bias` from `bias_result`:

```python
should_skip, skip_reason = h1_poi_availability(
    mso, self.config, bias=bias_result.get("bias", "")
)
```

Claim verified.

### 1.3 "Strictly narrower than L2" analysis

The commit message claims the gate is stricter than L2 `h1_poi_exists` and *"cannot false-block"*. I worked through the logic carefully.

**L2 `_check_h1_poi_exists` under `ob_retest` framework** (`src/components/verification.py:213-334`):
- OB match via `_find_matching_ob` (line 60-71): **direction-agnostic** — only checks `not ob.mitigated` + zone overlap.
- If no OB match, fallback to breaker via `_find_matching_breaker` (line 74-88): **direction-matched** via `bb.direction == required_dir` (derived from `trade_parameters.direction`).

**Gate (direction-aware branch, `pre_ai_gates.py:52-63`):**
- OB check: `not ob.mitigated AND ob.type == bias`
- Breaker check: `not bb.is_retested AND bb.direction == bias`

So L2's OB check is direction-agnostic while the gate's OB check is direction-aware. There IS a theoretical asymmetry: a scenario where L2's `_find_matching_ob` passes on an unmitigated bearish OB but the gate's `ob.type == "bullish"` filter rejects that same OB (and no unmitigated bullish OB exists), so the gate would skip where L2 would have passed on OB alone.

**Is this false-block possible in production?** Only if all three hold simultaneously:
1. `bias = "bullish"` (or mirror)
2. AI produces a `trade_direction = "LONG"` CANDIDATE
3. AI cites a bearish OB as its H1 POI

Condition 3 is semantically broken under `ob_retest` — a LONG trade on a bearish (supply) OB contradicts the framework definition. The AI is also explicitly prompted (see `orchestrator.py:1148-1151`) to trade LONG only under bullish bias. A counter-direction OB citation would be a prompt-compliance failure, not a legitimate pattern the system wants to capture.

Under the CURRENT orchestrator wiring, this scenario is rendered effectively impossible because:
- `bias_result["bias"] == "no_bias"` short-circuits the pipeline at `orchestrator.py:576-585` BEFORE the gate is reached.
- When the gate IS reached, `bias ∈ {"bullish", "bearish"}` always holds — meaning the direction-aware branch is always taken.
- The deterministic bias is injected into the prompt as a binding fact forbidding counter-direction trades (`orchestrator.py:1148-1151`).

**Conclusion:** the gate is STRICTLY NARROWER than L2 (adds `ob.type == bias` and `bb.direction == bias` filters L2 doesn't have on OB), BUT the only cases L2 would accept and the gate would reject are semantically contradictory AI outputs that the prompt explicitly forbids. "Cannot false-block in practice" is a correct characterization. "Mirrors L2" (from the 8a9bcfe message) is SLIGHTLY imprecise — they are not bit-equivalent — but the intent is preserved.

### 1.4 Counter-bias edge case (brief's specific concern)

The brief notes that under A7's structural-bias finding, if the market_state bug is fixed and bearish D1 bias starts emitting, the behavior of the gate on SHORT setups becomes newly relevant. It also flags that the bias passed to the gate is `daily_bias`, not `trade_direction` — so a counter-bias AI output is a theoretical failure mode.

**Current state (verified live):**
- `knowledge_base/live_evaluations/*/*.jsonl` contains **zero** records with `direction: "SHORT"`.
- Production logs show **91** `no_unmitigated_bullish_h1_pois` skips and **zero** `no_unmitigated_bearish_h1_pois` skips since the upgrade went live. Bearish branch has NEVER executed.
- `_compute_deterministic_bias` has only ever returned `bullish` or `no_bias` in production.

**Severity:** purely theoretical today. Two failure modes would need to activate simultaneously:
1. Market state starts emitting bearish bias (requires A7 fix).
2. The AI ignores the prompt's "LONG only" instruction under bullish bias (no precedent in logs).

**If #1 is fixed and the AI begins obeying the prompt faithfully** (LONG when bullish, SHORT when bearish), the direction-aware gate continues to be correct because `bias == ob.type == ai.trade_direction` will align.

**If #1 is fixed but the AI sometimes counter-biases** (produces SHORT under bullish bias or vice versa), the gate could mis-skip — BUT the AI's counter-bias CANDIDATE would later fail L2's direction check on the breaker fallback path anyway (L2 requires `bb.direction == required_dir`), so the downstream behavior is L2 rejection either way. A gate that skips the API call saves money at worst; the "lost CANDIDATE" case requires the AI to cite an unmitigated BEARISH OB for a SHORT trade under BULLISH bias — a sequence with no evidence of ever occurring and that L2 would pass only on OB alone (due to direction-agnostic matcher).

**Recommendation:** document this edge case in the module docstring when the next substantive edit happens. Not worth a change today. Add a test for "bias=bullish, AI trade_direction=SHORT, unmitigated bearish OB present" if/when the A7 fix lands.

### 1.5 Live evidence (corroborating the commit message)

- GBPJPY daily evaluation row counts match exactly: `wc -l` against `knowledge_base/live_evaluations/GBPJPY/2026-04-{20,21,22,23}.jsonl` returns 29 / 15 / 5 / 1. Matches commit message verbatim.
- Log reason strings over `logs/{xauusd,us30,usdjpy,gbpjpy,gbpusd}.log`:
  - `no_unmitigated_h1_pois` (legacy, pre-Apr-22): 48 events
  - `no_unmitigated_bullish_h1_pois` (post-Apr-22 upgrade): 91 events
  - `no_unmitigated_bearish_h1_pois`: 0 events
- Since Apr 22 (watchdog restart): 91 bullish-direction skips + 22 agnostic skips. The 22 agnostic are either from very early post-restart minutes or from a race where `bias_result` returned an unexpected value — worth a brief grep-forensic in a future session, but outside this review's scope.

### 1.6 Test quality review

`tests/test_pre_ai_gates.py` — 19 tests, all pass (0.24s). Coverage by category:

| Category | Tests | Notes |
|---|---|---|
| Direction-agnostic skip | 3 | all-mitigated, empty-lists, breakers-retested |
| Direction-agnostic do-not-skip | 4 | unmitigated OB (bullish + bearish), unretested breaker (bullish + bearish) |
| Framework scope bypass | 3 | breaker_retest-only, multiple, missing model_a |
| H1 missing bypass | 1 | — |
| Direction-aware bullish skip | 1 | only bearish POIs, bullish bias → skip |
| Direction-aware bullish no-skip | 2 | bullish OB, bullish breaker |
| Direction-aware bearish mirror | 1 | two cases in one test (skip + no-skip) |
| Bias="no_bias" agnostic fallback | 1 | with bearish unmitigated OB |
| Bias="" agnostic fallback | 1 | mixed bullish + bearish unmitigated |
| Scope + bias=bullish | 1 | non-ob_retest bypasses |
| H1 missing + bias=bullish/bearish | 1 | bypasses correctly |

**Gaps:**
- **No counter-bias test.** Example of a missing case: `bias="bullish"`, MSO has only unmitigated bearish OBs, `ob.type == "bullish"` filter rejects — gate skips. BUT: no test reflects the AI-side concern (gate skips, AI-that-would-have-cited-bearish-OB never runs). This is implicitly covered by `test_bullish_bias_with_only_bearish_pois_skips` (line 172-180), but the test framing is about MSO state, not AI counter-bias behavior — so the semantic is correct though the failure-mode framing is absent.
- **No test of BreakerBlock.direction string semantics.** The model field at `src/models/market_state_models.py:69` is `direction: str  # "bullish" or "bearish"` — no `Literal` constraint. Tests use the correct strings, and construction site at `market_state.py:586-596` also always uses those, so there is NO runtime risk — but a defensive assertion or Literal upgrade would be ideal. Not a blocker.
- **No test for mixed OB state: mitigated bullish + unmitigated bearish + bias=bullish.** Should skip (no unmitigated bullish AND no unretested bullish breaker). Currently coverage is via `test_bullish_bias_with_only_bearish_pois_skips` where there's no mitigated bullish OB at all; the "some but all mitigated" case has no direct test but is logically equivalent.

Test rigor is GOOD. Gaps are minor.

### 1.7 Regression risk

`pytest tests/ --timeout=30 --deselect tests/test_infrastructure_framework.py -q`:
- **1797 passed, 2 skipped, 43 deselected, 22 warnings** in 143s
- **1 failure**: `test_orchestrator.py::TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded`

The single failure is a time-dependent flaky test that I verified also fails on the parent commit `8a9bcfe`. **Not a regression.** The test assumes `placed_dt = now - timedelta(hours=20)` will always fall "before today's 07:00 UTC", but when run between 03:00 and 07:00 UTC on a given day (current run time ~14:04 UTC local conversion), the cached boundary doesn't discard the intent as expected. Pre-existing issue, not touched by the commits under review.

`test_infrastructure_framework.py::test_request_counting` was deselected because it calls `limiter.wait_for_rate_limit()` which executes `time.sleep(60)` — a 60s block that triggers pytest's 30s timeout. Also unrelated to the reviewed commits.

Targeted `pytest tests/test_pre_ai_gates.py -v`: **19 passed** in 0.24s.

---

## 2. Commit `3da685b` — watchdog git-status check

### 2.1 Code inspection (`scripts/watchdog.ps1:157-187`)

The new block runs AFTER `Test-TradingHours` (line 148) and AFTER `Write-Log "=== Watchdog check started ==="` (line 155), but BEFORE env loading and BEFORE the per-symbol orchestrator restart loop (line 207). Positioning is correct — a dirty working tree would be flagged BEFORE a potential respawn.

Key elements:
- `git -C $ProjectDir status --porcelain 2>$null` targets the main worktree via `$ProjectDir = "C:\Users\MSI\Documents\ai-trading-agent"` (line 20). **Correct** — not the worktree where the watchdog script lives. Same directory whether run from main or a sibling worktree.
- Silent-on-error via outer `try/catch` and `2>$null`. If git is missing or fails, no log spam. Acceptable.
- Porcelain v1 parsing: `line.Substring(3).Trim('"')`. Correct — columns 1-2 are status, col 3 is space, rest is path. The `.Trim('"')` handles the quoted-path case (porcelain quotes paths with special characters).
- Rename handling: `if ($path -match " -> ") { $path = ($path -split " -> ", 2)[1] }`. Correctly extracts destination.
- Filter prefix: `^(src/|scripts/|prompts/|config/|tests/|run_agent\.py)`. Covers all code-bearing paths. Excludes `logs/`, `knowledge_base/`, `pipeline_state/`, `shadow_logs/`. Matches the documented intent.

### 2.2 Functional verification

Simulated the PowerShell regex filter in Python against the current dirty main worktree:

```
drift code paths: 11
   M scripts/canary_fixtures/last_run.json
   M src/components/orchestrator.py
   M src/components/permissions.py
   M src/components/pre_ai_gates.py
   M src/components/primary_analyzer.py
   M src/components/verification.py
   M tests/test_bugfixes_0.py
   M tests/test_permissions.py
   M tests/test_pre_ai_gates.py
   M tests/test_primary_analyzer.py
   M tests/test_verification.py
```

Matches the 10 code-path count claim in the commit message (the mismatch is 1 because the main worktree has 11 vs the commit's recorded 10 — canary runs produce churn on `last_run.json`). The filter is working as designed.

### 2.3 One spurious-warning concern (not a blocker)

`scripts/canary_fixtures/last_run.json` is runtime canary output that is **tracked in git** (see `git log -- scripts/canary_fixtures/last_run.json`) and will show as dirty after every canary heartbeat. The filter prefix `scripts/` is too broad to exclude this — so every watchdog heartbeat in production will emit a spurious `drift: scripts/canary_fixtures/last_run.json` warning unless the canary result is recommitted or ignored.

**Severity:** cosmetic. The warning is non-fatal and not blocking. But it will desensitize operators to the actual drift signal.

**Suggested future refinement:** narrow the filter to exclude `scripts/canary_fixtures/` or add an exclusion for that specific file. E.g.:

```powershell
if ($path -match "^(src/|scripts/|prompts/|config/|tests/|run_agent\.py)" -and
    $path -notmatch "^scripts/canary_fixtures/") {
    $driftPaths += $path
}
```

Not required for this commit; worth a quick follow-up commit.

### 2.4 PowerShell parse verification

I was unable to run PowerShell in this review session (permission denied by the Claude harness sandbox). However the agent's reported verification method (`ParseFile` returning 0 errors + manual run) is standard for PowerShell scripts without a test harness, and the logic is straightforward enough to inspect.

The em-dash fix (ASCII `--` instead of `—`) referenced in the brief is verified — line 181 reads `"WARNING: uncommitted changes in working tree -- live code may differ from git HEAD..."`. No Unicode characters in Write-Log calls. Good.

### 2.5 Edge cases

- **Git not in PATH:** `$gitExe = "git"` + `2>$null` + outer `try/catch` handles this silently. Non-fatal. 
- **Non-git directory:** `git status --porcelain` returns exit code 128, `$LASTEXITCODE -ne 0` ⇒ skip. 
- **Watchdog running from a different directory:** `-C $ProjectDir` forces git to the main worktree regardless of cwd. 
- **Concurrent canary write:** a canary run updating `last_run.json` mid-check won't corrupt the watchdog state — status output is a point-in-time snapshot.

### 2.6 Regression risk

Additive code block wrapped in outer try/catch with `$ErrorActionPreference = "Continue"`. Zero risk of regression on existing watchdog behavior.

---

## 3. Hallucinations / factual accuracy

- `a84abde` message: claim *"direction-aware branches at pre_ai_gates.py:49-65"* — **verified** (line 49 is `directional = bias in ("bullish", "bearish")`; line 65 is `return True, f"no_unmitigated_{bias}_h1_pois"`).
- `a84abde` message: claim *"orchestrator step 3d passes bias=bias_result.get('bias', '') at orchestrator.py:591-593"* — **verified** (exact).
- `a84abde` message: claim *"19 tests passing"* — **verified** (all 19 pass in 0.24s).
- `a84abde` message: claim *"GBPJPY weekly eval rows dropped 29 → 15 → 5 → 1"* — **verified** via wc -l on `knowledge_base/live_evaluations/GBPJPY/2026-04-{20,21,22,23}.jsonl`.
- `a84abde` message: claim *"Live code was running uncommitted for ~2 days"* — **verified** via byte-diff (zero difference between committed blob and working-tree live file, and `no_unmitigated_bullish_h1_pois` strings present in logs from Apr 22 onward).
- `a84abde` message: *"Zero false-positive skips across 15+ sampled gate events"* — not independently reproducible in this review; relies on the referenced but uncommitted `research/thursday_2026-04-23_analysis/system_forensics.md`. See section 4 below.
- `3da685b` message: claim *"10 code-path drift lines"* — simulated run shows 11 in current main worktree; the difference is a transient canary write. Within noise.

### Non-hallucination but missing artifact

Both commits reference `research/thursday_2026-04-23_analysis/system_forensics.md` (and related) as Evidence. That directory is **UNTRACKED** in the main worktree and does NOT exist on the reviewed branch (`worktrees/agent-a97f76b5`). A reviewer on the feature branch cannot consult the referenced evidence.

**Severity:** the commit messages truthfully reflect evidence the committing agent saw — but the evidence is ephemeral. Recommend committing the forensic analysis in a separate `research(audit): ...` commit before the feature commits, or adding the path to `.gitignore` and rewording the Evidence references. Not a blocker for approving the code change.

---

## 4. Test gaps (summary)

Minor. Current coverage is good. Worth adding in a follow-up:

1. **AI counter-bias test.** `bias="bullish"` + MSO has a mitigated bullish OB + an unmitigated bearish OB → gate skips (semantically correct but worth pinning with a comment about WHY this is right even though an AI-side counter-bias citation would have found a match).
2. **BreakerBlock.direction Literal.** Upgrade `src/models/market_state_models.py:69` from `direction: str` to `direction: Literal["bullish", "bearish"]` for defense-in-depth. Low priority.
3. **Mixed-OB state test.** `bias="bullish"`, OBs = [mitigated-bullish, unmitigated-bearish] → gate skips (currently inferred from existing tests; explicit coverage would be nice).

None of these are blockers.

---

## 5. Recommendations

### Must-do (none)
Both commits are mergeable as-is.

### Should-do (low-priority follow-ups)
1. Narrow the watchdog filter to exclude `scripts/canary_fixtures/` — avoids every-heartbeat spurious warnings from canary runtime writes. One-line change.
2. Commit the `research/thursday_2026-04-23_analysis/` forensic evidence in a `research(audit): ...` commit so the Evidence references in `a84abde` + `3da685b` are reproducible.
3. Add a module-docstring note in `pre_ai_gates.py` flagging the counter-bias edge case (dormant under current orchestrator short-circuit at line 576).
4. Promote `BreakerBlock.direction` from `str` to `Literal["bullish", "bearish"]` — defensive typing.

### Should-do when A7 market-state-bias fix lands
1. Add test: `bias="bearish"`, MSO has unmitigated bearish OB → gate passive (already covered by existing tests, but explicit live validation needed once bearish bias emits).
2. Add test: `bias="bullish"`, AI cites bearish OB (counter-direction AI output) → gate behavior.
3. Verify the direction-agnostic fallback is actually reachable. As of now it's dead code due to the orchestrator's `no_bias` early return.

---

## 6. Summary table

| Claim | Verified | Evidence |
|---|---|---|
| Committed code matches live working tree | YES | Byte-diff is empty |
| Direction-aware branches at lines 49-65 | YES | Lines match exactly |
| orchestrator 591-593 passes bias | YES | Exact string match |
| Gate is strictly narrower than L2 | YES | Adds `ob.type==bias` + `bb.direction==bias` filters L2 lacks on OB |
| Gate cannot false-block in practice | YES (conditional) | Requires semantically broken AI counter-direction OB citation that the prompt forbids |
| 19 tests pass | YES | 19/19 in 0.24s |
| GBPJPY 29→15→5→1 | YES | wc -l matches exactly |
| Bearish branch has ever fired | NO | Zero `no_unmitigated_bearish_h1_pois` events in live logs |
| Watchdog runs git -C ProjectDir | YES | scripts/watchdog.ps1:166 |
| Watchdog filter excludes runtime paths | YES | Regex matches only 6 code prefixes |
| Watchdog non-fatal on errors | YES | Outer try/catch + `2>$null` |
| No regression on existing tests | YES | 1797 passed; 1 pre-existing flaky time-dependent failure on base commit too |
| Forensic evidence committed alongside | NO | `research/thursday_2026-04-23_analysis/` is untracked |

**Bottom line: APPROVE.** Ship both commits. Treat the four follow-up items as a small house-keeping task for the next session.
