# GTOS Implementation — Session 2

You are the implementation owner for GTOS, continuing Phase 0. Session 1 landed 21 commits
(`4d2407c77..c5622c153`, all pushed to `origin/main`). Your job has two parts, in order: **review session
1's work adversarially**, then **finish Phase 0**.

Work on branch `main` in `/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725`.
Push with `GIT_LFS_SKIP_PUSH=1 git push`.

---

## 1. Read order

Read all of it from disk. Do not reconstruct any of this from a summary.

1. `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — **read this first.** It is the
   resumable checkpoint and it corrects numbers both audits carry. One expectation to set before you look
   at anything else: **the whole test suite is ~684 failed / ~9,638 passed, and that is the known
   baseline, not a catastrophe.** Both audits' "11 failures" was an ~885-test subset.
2. `docs/audits/fable5-vision-audit-20260725/OPUS_IMPLEMENTATION_PROMPT.md` — the mission, the settled
   decisions (OD-1, OD-2, the standing owner directive), and the anti-scaffolding working rules.
3. `CLAUDE.md` — root briefing, hazards H1–H7, engineering and cleanup rules.
4. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` — findings F1–F30.
5. `docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md` — the mission document. Phase 0 and
   Gate G0 are what you are finishing.
6. `docs/audits/fable5-vision-audit-20260725/AUDIT_STATE.md` — the nine investigation-agent digests.
7. `docs/audits/opus5-architecture-20260725/` — the first audit, as reference. `OWNER_SESSION_CONTEXT.md`
   is the owner's direction verbatim and governs how you choose work.
8. `.context/00_core/live_system_of_record.md` — authoritative for the live model; §2b was amended in
   session 1.
9. Preflight per `CLAUDE.md` §2: `python3 scripts/generate_live_state.py`, then `.context/LIVE_STATE.md`.

---

## 2. First task — review session 1 adversarially

`git log --oneline 4d2407c77..c5622c153`. Read the diffs. Your posture is **refute**, with `file:line`.
Session 1's own verification passes overturned two prior-audit conclusions, so assume the same is
possible here.

**Where session 1 is most likely wrong, in its own estimation — start here:**

| Risk | Commit | Why to look |
|---|---|---|
| **`admission.py` and `book_engine.py` taken wholesale** | `46c526bfe` | The single largest unreviewed surface. `admission.py` is the live **sizing and governor math** (+198 B vs HEAD) and `book_engine.py` is +4,810 B. Session 1 verified no HEAD-only *functions* were lost, but did **not** read these two diffs line by line. If anything in this session's work silently changes live risk behaviour, it is most likely here. |
| **7 convergence call sites wired programmatically** | `46c526bfe` | Inserted by a script after two off-by-one failures. They parse and tests pass, but **all 7 were never visually inspected**. Two of them re-evaluate a `{**base_outcome, ...}` dict literal as a second argument. Confirm each site's `event_type`/`outcome`/`unit` matches its own call, and that the `unit=unit` site is the right one. |
| **Live risk behaviour changed with no dedicated test** | `9495752c2` | `orchestrator.py` now holds `consecutive_losses` instead of recomputing it when `get_history_deals` returns `None`. That counter feeds the consec-losses **emergency brake** (`orchestrator.py:7004`). It is covered only by inspection and the suite A/B — a declared gap. Write the test or refute the change. |
| ~~A risk-semantics judgment call~~ | `46c526bfe` | **SETTLED — do not relitigate.** The owner decided 2026-07-26 that revoking broker authority also revokes the book's ability to close; `test_breach_flatten.py`'s arming of the gate is correct. See B21 in `IMPLEMENTATION_STATE.md` for the reasoning and the two supporting facts. |
| **3 assertions rewritten** | `46c526bfe` | `tests/test_notifications.py` now asserts `realized_usd is None` without broker reconciliation. Session 1 concluded VPS deliberately split projection from truth (`notifications.py:263,345`). Verify that read; if wrong, this masks a real regression. |
| **22 files edited, unmeasured** | `d2bb4448e` | The long-path platform guard. A no-op unless the research tree is materialized, so the suite never exercised it. |
| **A superseded commit** | `a2b1d7a3d` vs `46c526bfe` | Session 1's time-bomb fixture fix was **overwritten** when the VPS test file landed (host-local). Confirm nothing was lost in that overwrite. |

**Known method failures from session 1 — check whether they contaminated any conclusion you rely on:**

- `git show $V:path` in zsh applies the `:t`/`:s` history modifiers and **silently returns the wrong
  thing**. Use `git cat-file -p "${V}:path"`. This produced two confident wrong answers before it was
  caught. `git ls-tree` and `git diff` with `--` were unaffected.
- Comparing failure **counts** instead of failure **sets** produced a wrong "refuted" verdict. Always use
  `scripts/pytest_failset.py diff`.
- `rg -r` is `--replace`, not "recursive". `rg -rn 'x'` silently rewrites matches in the output.
- The suite has at least one **non-deterministic** test
  (`test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration`,
  pass/pass/fail over three identical runs), so a single-run A/B carries a false-positive rate.

Report what survives and what does not. Fix what you refute.

---

## 3. Then — finish Phase 0

Remaining items, in order:

1. **Item 4 — the activation token.** The complete handoff pack is **B20** in `IMPLEMENTATION_STATE.md`:
   the choke point (`RealMT5.order_send`, `mt5_real.py:392` — **re-locate it, the merge already moved it
   once from `:362`**), the full mutating-surface census re-verified post-merge, and every design
   constraint with its evidence. Non-negotiables from that pack: risk-reducing requests must pass
   **without** a token, or an expired token traps the account in an open position; the token must not
   live under `pipeline_state/`; **zero `config/agent_config.yaml` edits** (SHA-bound and currently
   clean — queue any key to item 5's re-seal batch).
2. **Item 5 — OD-2.** Additive re-seal (keep schema `v1` and both literal group names, add a sibling
   `verification_tooling` key the enforcement loop ignores, so no executing file changes and
   `code_authority_root_sha256` is preserved). Then land P1, add halt checks to
   `dual_broker_execution_follower.py`, and delete-or-gate `fn_smoke_trade.py` (note it has 827 lines of
   genuine behavioural tests). Constraints C7–C9 in the state file: there are **four** contract
   generations not two and `9faa7d4c` is the current one; the re-seal needs a pack-build-seal
   regeneration the plan omits; **twelve** files reference the binding group names, including `CLAUDE.md`
   and `AGENTS.md`. P2 is **not** landable — its file is doubly bound.
3. **Item 1's remainder** — record P4 and the three `convergence_*` modules onto the VPS lineage record.
   Small.
4. **Gate G0** — currently 2 of 5 criteria. `run_book.py` imports and its tests pass ✅; the A/B mechanism
   exists ✅. Still needed: book + companion suites green, the H1 check under the new split, and the
   token dry-run. **G0's "test suites green" needs restating first** — at a ~684-failure baseline it is
   not a meaningful criterion. Scope it to the live surface (B16) and state the rationale in the gate
   receipt, which the plan explicitly permits (design rule 7: gates are evidence definitions, and where a
   gate names a quantity, sufficiency is your judgment).

**The deletion manifest comes after item 5, not before** — item 5 re-seals the contract, and the manifest
must know which files are still SHA-bound afterward. When you build it, tests and the code they cover go
as **one reviewed pair**: per F23, deleting tests first makes `book_owner.py`, `launcher.py` and
`learned_edge_walkforward_gate.py` look unreferenced. Nothing has been deleted yet.

---

## 4. Working rules

The full set is in `OPUS_IMPLEMENTATION_PROMPT.md` §4. The ones session 1 learned the hard way:

- **A/B every change** with `scripts/pytest_failset.py capture` + `diff` against
  `docs/audits/fable5-vision-audit-20260725/receipts/baseline_full_suite.json`. Never claim "no
  regressions" without it. Re-anchor the receipt when you land work.
- Never run the suite without `--continue-on-collection-errors` — without it, 12 collection errors abort
  the run after executing **zero** tests while still exiting like a completed run. The tool pins this.
- **Never execute broker-capable scripts**: `fn_smoke_trade.py`, `mt5_preflight.py`,
  `dual_broker_execution_follower.py`, `run_agent.py`, `run_book.py`, `start_all.bat`,
  `.tools/monitor_books.py`. Note C1: `create_mt5("live")` **succeeds** on macOS; the ImportError only
  surfaces on `.connect()`, so construction is not a safety boundary. To test importability safely, copy
  the child-process pattern in `tests/test_run_book_importable.py`.
- **H1**: run the `CLAUDE.md` §3 contract check before editing anything under `src/`. B4 in the state
  file lists which Phase-0 targets are bound and which are free.
- Before declaring a gate passed, run an adversarial subagent briefed to refute with `file:line`.
- Report faithfully: failed tests with output, skipped steps named, "done" means verified.
- Rematerialize whatever you need from iCloud without asking — the owner has given standing approval and
  considers the permission ask unnecessary.

**Scope discipline — the failure mode of session 1.** It let "establish a baseline so I can A/B" expand
into root-causing unrelated test failures in files slated for deletion. The defects found were real, and
two were live-risk fixes worth having, but it was not plan work. ~330 research-bookkeeping failures and
~56 artifact-existence failures are **stale, in the deletion tier, and must not be repaired**. If you
find yourself fixing a test outside the live surface, stop and ask whether it is going to be deleted
instead.

**Escalate to the owner only for:** risk dial, allocation profile, broker-real activation; genuinely
external dependencies; or a falsification-gate failure that changes the plan. One question is already
open and batched for the G0 report: whether to graft the legacy June history (C12).
