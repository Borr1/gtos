# GTOS Implementation Mission — Opus session handoff

You are the implementation owner for GTOS. Two independent audits are complete and reconciled; every
strategic decision needed to start is made and recorded. Your job is to execute
`docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md`, phase by phase, gate by gate.

**Work on branch `main`** in this worktree
(`/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725`) — it tracks
`origin/main`, whose tip is the foundation snapshot. Push with `GIT_LFS_SKIP_PUSH=1 git push`; read
`docs/STORAGE_AND_REMOTES.md` before any storage/push decision. The granular audit history is the
local branch `audit/claude-opus5-architecture-20260725` (archival; not pushable — the doctrine doc
explains why).

## 1. Read order (do this first, ~30–45 min)

1. `CLAUDE.md` — the root briefing. Note: H1–H3 were amended by the second audit (contract binds
   **44** paths; the 10 red selector tests are a **real defect** (F13), not LFS damage; the memory
   ceiling is 8.61 GB maxrss). Preflight step 11 points at the second audit.
2. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` — verdicts on the first audit,
   findings F1–F28, and the owner-decision update inside F1.
3. `docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md` — **your mission document**,
   including the OD-1 addendum (combined book) and the standing owner directive.
4. `docs/audits/fable5-vision-audit-20260725/AUDIT_STATE.md` — compressed digests of the nine
   investigation-agent reports (halt-surface table, learning-lane gap list, data coverage, etc.).
5. `docs/audits/opus5-architecture-20260725/` — the first audit, as reference
   (`TARGET_ARCHITECTURE.md` §2 is still the core design; the plan amends, not replaces, it).
6. `docs/audits/opus5-architecture-20260725/OWNER_SESSION_CONTEXT.md` — the owner's direction
   verbatim.

## 2. Decision state (settled — do not relitigate)

- **OD-1 (owner, 2026-07-25):** the broad system is the primary build focus and activation
  candidate. W7 went live 06-18→07-02, drew down, was deactivated; it is retained as a
  benchmark/challenger policy and a forensics/calibration source, not revived as-is. The combined
  book (both families behind one trade-intent contract under one portfolio risk budget) is the
  target *configuration space*; each family earns its slot individually through the walk-forward
  gate; the activation candidate is whatever composition clears the gates.
- **OD-2 (owner-approved):** re-seal the decision contract with `executing_closure` (SHA-bound)
  split from `verification_tooling` (versioned, unbound); **forward-only** — January stays accepted
  under its original contract; the re-seal must keep every executing file **byte-identical** so
  windows remain poolable. Then land the queued P1/P2 fixes.
- **Standing owner directive:** precedent is not authority. Anything you judge wrong or valueless —
  policy, contract, gate, verifier, structure — replace with the better alternative, documented
  (what changed, why, what replaces it). Owner boundaries that remain: risk dial, allocation
  profile, broker-real activation.

## 3. Starting queue (Phase 0 of the plan, in order)

1. Fork reconciliation — two-way merge of the live package (host-local), vendor the book's evidence route from `origin/deploy-live`, note the composition
   drift in `live_system_of_record.md`.
2. Fix F13 (the ten genuinely-red selector tests) with a decided contract, not a workaround.
3. Invert the halt mechanism into presence-of-authorization tokens (fail-closed by construction).
4. Execute OD-2 (contract split + forward-only re-seal), land P1/P2, add halt checks to the
   follower, delete or gate `fn_smoke_trade.py`.
5. Record the history graft (F28) with a pointer doc; decide graft-vs-reference for the legacy repo.
6. Gate G0 as written in the plan. Then Phase 1's four workstreams — parallelizable across sessions.

## 4. Working rules — the anti-scaffolding contract

These are the failure modes that built the mess. They are process rules, not suggestions.

- **Never assert what you did not check.** Tag claims [MEASURED]/[VERIFIED]/[INFERRED]/[HYP] in
  durable docs. If you didn't check, write "unverified". Every deliverable carries a declared-gaps
  section — saying "I did not get to X" is a required output, not a failure.
- **When something is unclear, stop and resolve it** — from disk, git, or a measurement. If only the
  owner can resolve it, ask one crisp question. **Never wrap uncertainty in another layer**; no new
  default-off flags as deferred decisions. Any gate you add must name the decision it changes.
- **Build, don't patch** (owner's central mandate). Replace mechanisms; don't fence them.
- **A/B against the parent commit before claiming "no regressions."** Know the red baseline first.
- **H1:** the decision contract binds **44 paths** — run the `CLAUDE.md` §3 check before editing
  anything under `src/`. After OD-2's re-seal, verifier edits become free; engine/config edits
  still are not.
- **Machine limits:** ≤1 replay arm at a time until the memory fix lands (8.61 GB maxrss on
  16 GiB). Never execute broker-capable scripts (`fn_smoke_trade.py`, `mt5_preflight.py`,
  `dual_broker_execution_follower.py`, `run_agent.py`, `run_book.py`, `start_all.bat`) — several are
  default-live; on this Mac they die at MT5 import, but treat them as loaded. The owner's other
  checkouts (`/Users/borr/GTOSActive/repo`, `worktrees/replay-accel-engine-20260719`) are read-only.
- **Tooling traps already hit:** 12 files carry UTF-8 BOMs (`utf-8-sig` when parsing); `zsh` eats
  `$B:refs` (use `${B}`); the LFS sleeve registry is hydrated in this worktree — fresh clones must
  re-hydrate or the F13 diagnosis gets misattributed again.
- **Verification discipline:** before declaring any phase gate passed, run an adversarial subagent
  briefed to *refute with file:line*, then fix what survives. The first audit's two shipped
  regressions and this method's corrections are the precedent.
- **Report faithfully:** failed tests are reported with output; skipped steps are named; "done"
  means verified.

## 5. Session structure and your judgment

**The plan is judgment-input, not law** — the owner's standing directive applies to it (plan design
rule 7). Gates are evidence definitions, never waiting periods; where a gate names a quantity,
sufficiency is your judgment, stated with rationale in the gate receipt. You may resequence, merge,
or restructure phases with documented reasoning. Pace yourself by your own judgment too — the one
engineering reality to respect is context quality: end a session at a gate or a clean checkpoint
rather than degrading through compactions, and Phase-1 workstreams parallelize well across sessions
(disjoint files; merge per `parallel_goal_merge_playbook.md`). Maintain
`docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` as a resumable checkpoint
(current phase, gate status, next action, open questions) updated after every work block; commit in
scoped tranches. Compute is not the constraint — replay wall-clock, market-observation time, and
owner decision points are. Conservatism means unearned smallness and waiting; it does not mean the
honesty layer in §4, which is what makes speed safe.

## 6. Escalate to the owner only for

Risk dial / allocation profile / broker-real activation; genuinely external dependencies (host-local); or a falsification-gate
failure that changes the plan (G2 failing is the named example). Everything else is yours.
