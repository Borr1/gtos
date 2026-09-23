# GTOS Phase 1, Session C — root-cause the red suite, then build the deletion manifest

You are an implementation session for GTOS. Phase 0 is complete and Gate G0 is met. Work on branch
`phase1/red-suite-deletion` in **`/Users/borr/GTOSActive/worktrees/phase1-red-suite-20260726`** — your own worktree, already
created and sparse-configured. Push with `GIT_LFS_SKIP_PUSH=1 git push -u origin phase1/red-suite-deletion`.

**Do not work in `worktrees/claude-opus5-architecture-audit-20260725` and do not commit to `main`.**
Two sibling sessions are running concurrently in their own worktrees; sharing one would collide on the
git index and on the `shadow_logs/` and `pipeline_state/` trees the suite writes into. Merge to `main`
per `.context/00_core/parallel_goal_merge_playbook.md` when your gate is met.

Two other sessions may be running in parallel on the shadow reducer and the clock repair. Your work
touches neither.

**Your task has two halves and the order is not negotiable.** Root-cause first. You cannot decide what
to delete while a third of the red suite is unexplained, and the audits' own deletion tier — as
specified — would delete the live trading surface.

---

## 1. Read order

1. `CLAUDE.md` — root briefing, hazards H1–H7. **H2 is now stale in one respect**: the ten selector
   tests it describes were fixed in Phase 0 (F13, `44f9a02c6`). The contract of record is **R2**.
2. `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — **B1, B10, B11, B12, B16 are
   your task's entire prior art.** They record two experiments that already failed. Do not repeat them.
3. `docs/audits/fable5-vision-audit-20260725/GATE_G0_RECEIPT.md` §0 and §6 — why G0's test criterion
   had to be restated, and the gaps it left.
4. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` §5.4 (reachability, E9) and **F23** —
   the deletion hazard.
5. `docs/audits/opus5-architecture-20260725/OVERENGINEERING_AND_DELETION_MAP.md` — the tier as
   originally constructed. Treat it as **input, not authority**: the second audit found it not
   executable as specified.
6. `.context/00_core/repo_cleanup_and_staleness_policy.md` — before deleting anything.
7. Preflight per `CLAUDE.md` §2.

---

## 2. Half one — the 299

**Current state.** 650 failed / 9,747 passed / 33 errors at `212ad7e6d`
(`receipts/baseline_full_suite.json`). Concentration:

| Failures | File |
|---:|---|
| 188 | `tests/test_gtos_vnext_master_conversion_ledger.py` |
| 111 | `tests/test_gtos_vnext_runtime.py` |
| 31 | `tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py` |
| 17 | `tests/test_vnext_production_wiring.py` |
| 13 | `tests/test_master_research_queue_state.py` |

**The first two are 299 of 650 and their cause is unknown.** That is the open question G0 explicitly
did not close.

### What has already been tried, and failed — do not redo it

- **Sparse-checkout masking is NOT the explanation, and this was settled by experiment, not argument.**
  B10 materialised two directories (3,550 files, 39 MB) and the two files went 299 → **300**. B11 then
  did it properly — all `SCAN_ROOTS` materialised, 5.3 GiB, 20,985 files, and **failure sets diffed**
  rather than counts — giving **299 → 271: 29 fixed, 1 regressed**. So masking explains **29**, not
  zero and not all. The sparse config was restored byte-for-byte both times. **Do not spend a day
  materialising evidence trees; that experiment is done.**
- **B10's own conclusion was wrong** because it compared counts instead of sets. That is the mistake
  `scripts/pytest_failset.py` exists to prevent. Use the tool.
- **B12 found one real cause and fixed it:** `_long_path` prepended the Windows `\\?\` prefix on POSIX
  with no platform check, so paths ≥240 chars could not exist. It is a function of *checkout location*
  — the failing artifact resolves to 278 chars from this worktree and 232 from `/Users/borr/GTOSActive/repo`.
  22 files were patched, and a 23rd (worse: no platform guard *and* no length gate) in `a3a3cc6e2`.
- **C11:** ~23 failures are attributable to a missing `pytest-asyncio`, which **cannot be installed
  here** — Homebrew Python 3.14.4 is PEP-668 externally-managed and a venv would invalidate other
  assumptions. Classify them; do not chase them.

### The probes worth running, named by the sessions that ran out of time

1. Why does `build_rows()` still yield no `WAVE_READY8_CONTEXT_RISK_RULES` rows **with its sources
   present**? Suspects: `_is_non_material_handoff_source_name` filtering, and
   `iter_current_wave_long_path_source_files`.
2. Is `test_gtos_vnext_runtime.py`'s `assert 'LEGACY' == 'FOLLOW'` a **genuine routing regression**, or
   a downstream symptom of (1)? This one matters beyond the test count — if it is a real routing
   defect it is a live-adjacent finding, not bookkeeping.
3. B11 surfaced a finding that is invisible in a sparse checkout by construction:
   `test_non_material_resume_handoff_is_not_added_to_execution_denominator` **fails only when the files
   exist** — so `NON_MATERIAL_HANDOFF_SOURCE_PATTERNS`
   (`build_gtos_vnext_master_conversion_ledger.py:59`) does not catch what it claims to.
4. Classify the **33 collection errors**, which nobody has done.

**What "done" looks like for half one:** every one of the 299 assigned to a named cause, and each
cause labelled **genuine defect** / **environment-bound** / **stale, dies with its code**. Not
repaired — *classified*. Repairing tests that are about to be deleted is the failure mode this session
exists to avoid.

---

## 3. Half two — the deletion manifest

Only after half one. The reachability finding is real and large: **~85 % of tracked Python is
operationally unreachable** (E9, re-derived against the true 3,814-file / 2,347,200-line denominator —
the first audit's percentages were computed against a sparse working set, F24).

**But the tier as constructed is not executable, and this is the part to get right.** F23: its only
in-repo consumers of `book_owner.py`, `launcher.py`, `learning_actuator.py` and
`learned_edge_walkforward_gate.py` are tests the tier *also* deletes — so deleting tests first makes
the **live trading surface and the vision's own walk-forward gate** look unreferenced.

Preconditions the second audit added, all of which now hold or are yours to satisfy:

- **Materialise each tier as a reviewed manifest** — a list a human can read, not a computed set.
- **Exempt** the `ultimate_book` and learning families, and `emergency_close_*`.
- `run_book.py` is vendored (Phase 0, `31cf05634`), so cascade math is now valid.
- **Per-file hidden-consumer sweep** covering string, subprocess, config, receipt **and VPS-branch**
  consumers. One `moonshot_*` module is one subprocess hop from the live monitoring chain and named in
  active config (`agent_config.yaml:2716`).
- **Tests and the code they cover go as one reviewed pair.** Never tests first.

**Two files that must not be swept up, and the reason is recent.** `scripts/flatten_all_positions.py`
and `scripts/emergency_close_and_stop_redacted_account.py` are **gate-unaware by design** — zero references
to `live_broker_authority` or `ultimate_book`, driving the raw MetaTrader5 module directly. The owner
decided on 2026-07-26 (B21) that revoking broker authority also revokes the book's ability to close,
which makes these two the operator's **only gate-independent exit**. They look like unreferenced dead
scripts to any static analysis. They are load-bearing.

**Three Tier-A context files are queued for deletion behind you, and you are the reason.**
`.context/00_core/architecture.md` (3,337 lines of XAUUSD-only Model A, "Design Complete"),
`master_roadmap.md` (April edge claims the live system falsified) and `pre_lock_final_review.md` are
stamped `HISTORICAL` but **not deleted**, because all three are hardcoded by path in
`scripts/build_gtos_vnext_master_conversion_ledger.py` (`:31724`, `:31816`, `:31909`) — the builder whose
188 failures are half your task. It enumerates via `git ls-files` and skips missing paths, so removing
them would drop ledger rows mid-investigation. **Delete them as part of your manifest once the 299 are
classified**, and say what it did to the failure set.

**Disk headroom is a live constraint, not a footnote.** This Mac is at **91 % full with ~41 GiB free**,
and the server export just landed 4.6 GB of it. Phase 5 wants tick backfill measured in tens of GB and
cannot have it until this is solved. That makes the *evidence* half of your manifest worth more than the
Python half, in bytes reclaimed per unit of risk — and the server carries the same pattern, 60.0 GB of
`.git/lfs` against 845 MB of real objects (`VPS_EXPORT_FINDINGS.md` V6).

**Also note:** 97 % of the 6.3 GB tracked tree is generated evidence, of which 4.8 GB sits in 280
inline non-LFS blobs over 5 MB. That is a separate and probably larger win than the Python deletion,
and `repo_cleanup_and_staleness_policy.md` governs it — extract unique intelligence into current
summaries **before** deleting, rewriting or demoting.

---

## Method — use the orchestration

The owner has explicitly authorised multi-agent workflows. Use them. This programme's two live-risk
defects were found by a 28-agent adversarial pass, not by careful reading, and its worst wrong answers
came from one mind checking its own work.

This is the strongest workflow case of the three — do not attempt it single-threaded.

- **The four named probes are independent.** Fan them out. Each returns a named cause with `file:line`
  and the set of failures it accounts for.
- **Loop until dry.** 299 failures will not resolve to four causes. Run rounds of finders against the
  unexplained remainder until two consecutive rounds surface nothing new, deduplicating against
  everything already explained rather than against what you have confirmed — otherwise rejected
  hypotheses reappear every round and it never converges.
- **The hidden-consumer sweep is embarrassingly parallel.** ~3,800 tracked Python files, each needing a
  string/subprocess/config/receipt/VPS-branch check. One agent per batch. This is the half that makes
  the manifest trustworthy, and it is exactly the work a single agent does badly.

Before you claim your gate is met, run agents briefed to **refute with `file:line`**. Every review pass
in this programme has overturned something the session was confident about.

## Anti-drift — this task has a characteristic way of going wrong

**Repairing instead of classifying.** Half one's output is *every failure assigned to a named cause*.
Fixing a test that is about to be deleted with its code is worse than leaving it red.

**Believing the first plausible cause.** The sparse-masking story was plausible, intuitive, and wrong —
it explains 29 of 299. Two prior sessions anchored on it. Require each cause to *account for a specific
set* of failures, not to sound right.

**Deleting on momentum.** The manifest is the deliverable; execution can be a separate cheap session.
Per F23 the audits' own tier would have deleted the live trading surface, so a manifest that is right
and unexecuted beats a deletion that is fast and wrong.

## 4. Working rules

- **A/B every change** with `scripts/pytest_failset.py capture` + `diff` against
  `receipts/baseline_full_suite.json`. Compare failure **sets**, never counts. The tool now also
  reports `parse_complete` — if that is ever `false`, the ids it recovered do not account for pytest's
  own totals and the comparison is not trustworthy.
- **Run the whole suite**, not a scoped subset. Phase 0 had three regressions that passed in isolation
  *and* alongside the file that appeared to cause them.
- Always `--continue-on-collection-errors`.
- **Never execute broker-capable scripts.** C1: `create_mt5("live")` succeeds on macOS.
- **H1 before editing anything under `src/`.** R2, 43 bound paths.
- Deleting a bound file is a contract event, not a cleanup. Check membership first.
- Before declaring the manifest safe, run an adversarial subagent briefed to **refute with `file:line`**
  — specifically, to find a consumer your sweep missed.
- Report faithfully.

**Traps already paid for:** `zsh` eats `git show $V:path` (use `git cat-file -p "${V}:path"`);
`rg -r` is `--replace`, not recursive — it silently rewrites matches in output and cost one wrong
reading already; **`rg` cannot see sparse-masked files**, which is why a previous census reported
284 files where the tracked count is 337 — use `git ls-files` for any census, not `rg`;
`test_end_to_end_integration.py::…::test_high_load_integration` is non-deterministic.

---

## 5. Deliverables

- A classification of all 650 failures and 33 errors by named cause, with the 299 fully accounted for.
  This closes **Q4**, the largest open measurement question in the programme.
- The deletion manifest as a **reviewed list**, tiered, with the hidden-consumer sweep evidence per
  file, and the tests+code pairing explicit.
- **Nothing deleted in this session unless the manifest is reviewed and you are confident.** Producing
  a trustworthy manifest is the deliverable; executing it can be a separate, cheap session.
- `IMPLEMENTATION_STATE.md` updated with evidence tags and a declared-gaps section.

**The honest framing to keep in view:** the charter says *"activation movement is prior to
scaffolding"*, and 60.6 % of replay CPU is proof machinery while 8.3 % decides trades. Deletion serves
that — but only if it removes dead weight rather than the live surface. A manifest that is right and
unexecuted beats a deletion that is fast and wrong.
