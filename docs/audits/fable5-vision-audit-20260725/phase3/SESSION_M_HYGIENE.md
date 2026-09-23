# Session M — The hygiene batch and the correction sweep

**Stage 1 item 1.5 + `THIRD_REVIEW.md` §6.3.** Worktree `worktrees/wave3-hygiene-20260727`, branch
`phase3/hygiene-batch`, from `main` @ `1e95fe7fa`. **Your block range is B140–B149.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## What this session is really about

Read the backlog below and it looks like chores. It is not, and here is the thread that runs through
it: **almost every item is a place where the system reports a safety or correctness property it does
not have.**

A vacuous test passes against a wrong implementation and reports coverage. A permanently-red test
reports a defect that cannot exist. A ghost reference points at a fact that has moved. A gate asserts
commission is handled while the arithmetic omits it — that one is **F38**, the largest economic finding
in the programme's history, and it is the same defect class as the B41 vacuous tests: *a signal that
says "checked" where nothing was checked.*

That class is what has cost this programme the most. Not bugs — **false green.** Two months of "GTOS is
hard-halted" described flags that did not exist. A 1,679-day validation charged zero commission under a
comment saying it was optimistic. Ten tests were blamed on an LFS pointer for weeks while a real
package-admission defect sat underneath.

**So the real deliverable is not ten fixes. It is: how much of what this repo asserts about itself is
actually checked?** The backlog is where to start looking, not the boundary of the work. If the sweep
tells you something general about where false green accumulates here, that finding outranks every item
on the list — write it up, and if a cheap mechanism would catch the class rather than the instances,
build it.

**And take the latitude:** the working agreement's orchestration grant applies fully. Fanning parallel
agents across unrelated subsystems is exactly what this session's shape rewards — one per defect
cluster, plus a critic asking what the list is missing.

It contains **no owner decisions**. Each fix gets a behavioural test and a failure-set A/B. Any item
that turns out to be wrong, larger than described, or load-bearing in a way nobody noticed gets
promoted to a finding rather than forced — Sessions C, G and H each found the "small" item was the
interesting one.

## The defect backlog

**From Session H's register** (`phase2/SLEEVE_BOOK_DEFECT_REGISTER.md`) — **D3, D4, D5, D6, D7, D8,
D10-guard, D11.** Read the register; H recorded correct behaviour and value for each. **D0, D2 and D12
are not yours** — D0 is an owner decision (universe reconciliation, contract-bound profile edits), D2
belongs to Session L's MC pack, D12 is closed.

**From Session C** — the **four B42 defects**.

**From B41** — the **L1/L2 vacuous tests.** These are tests that pass against a wrong implementation.
Fix the test, not the symptom: a vacuous test is worse than a missing one because it reports safety.
Prefer behavioural assertions; a test that greps source for a substring is the failure mode you are
removing.

**Wave4b/4c permanently-red tests** — 8 of them, whose inputs were deleted from history and which can
therefore **never** pass again. Skip-with-reason, with the reason naming the deleted input. Do not
delete them silently and do not leave them red.

**F30/Q7** — suite-notification suppression.

**B58** — ghost references in `CLAUDE.md` and `IMPLEMENTATION_STATE.md`.

## D-1 — the one item here with a deadline

The orphaned sleeve-registry LFS payload. A hash-verified out-of-tree hold copy exists (B53), but
**nothing committed records that custody** — so a `git lfs prune` would erase the last *git-custodied*
copy of a **contract-bound input**. Commit it behind a pointer, or record the custody in-tree so the
closure condition is actually met. This is the only item on the list that gets worse with time.

## The correction sweep — §6.3

Documents that are affirmatively misleading today. **`CLAUDE.md` was already corrected** on 2026-07-27
(H3, H6, §4's three booleans, April's 15 days, the program change) — verify that work and extend it;
do not redo it.

Remaining:

- **`SECOND_AUDIT.md` §5.3 / E8** — amendment banner for the struck "15.3 GB is a GiB/GB echo" claim,
  mirroring the F7 banner already in that file. The claim is refuted twice over: arithmetically
  (15.32/8.61 = 1.779, not 1.0737) and by measurement (B81/B83, and `THIRD_REVIEW.md` §A1).
- **`FULL_VISION_PLAN.md`** — the ≤3 GB re-derivation note, and **Phase-4 item 1's stack conflation**
  (§7.8): *"B7.5 per-sleeve splits"* do not exist for W7 sleeves — B7.5's sleeve vocabulary is the broad
  stack's `fpsc_*` families, and all 82 registry rows are `fpsc_*`. As written it would point a session
  at the wrong registry, which is exactly the D12 trap. Also add the banner that §4 of the third review
  supersedes its Phase 2–3 sequencing.
- **`research_current_state.md`** — a staleness banner. Its live-state claims are affirmatively
  misleading today.
- **`THIRD_REVIEW_UNCONSTRAINED_PROMPT.md`** — the evidence-weight numbers it carries are superseded:
  `calendar_no_session_breadth_guard` is **77.5 MB** (one constant subtree × 2,304 rows, **1** distinct
  value), not 154 MB / 2 values; the 867/802 figures are **MiB**; scorecard fields average **1,248.7**
  (min 888, max 1,827), not a flat 1,211. Those were mine and they were wrong.
- **Session E's receipt** (`GATE_G1B_RECEIPT.md`) — two amendments, recorded the way E recorded its own
  §14 withdrawals rather than by editing the claims away: (1) the JPY *"survives Bonferroni"* claim
  double-counts cross-account duplicates; at the honest signal-level denominator **29 distinct signals,
  p = 0.00588, ×12 = 0.0706** — direction and magnitude stand, **"decisive" does not**; (2) §10 decision
  2 is framed on a moot mechanism, since `one_unit_per_cluster_per_day` is globally `false` at HEAD
  (`agent_config.yaml:1373`), so the real decision is whether to re-impose the certified envelope at all.

## Standing rules to make structural while you are in here

Two came out of this wave's review and are currently prose. If a cheap mechanism can enforce either,
build it; if not, say why.

1. **An A/B that is not committed did not happen** (`receipts/WAVE2_INTEGRATION_AB.md`).
2. **Any claim of improvement carries a placebo or null control in the same receipt.** The base rate is
   brutal: of every book-level improvement in the record, exactly **one** passed its own random-drop
   placebo — the small A8 gate. The large one failed at p = 0.59 and shipped anyway.

## Method

**Failure-set A/B per change, not once at the end.** You are making many small changes across
unrelated subsystems; a single A/B at the end tells you a set moved but not which change moved it.
Batch related items, A/B each batch. **Sets, not counts.** Two or three tests are known-flaky under
load (B30, B79b) — diff two runs before believing a small regression.

**H1 before anything under `src/`.** Several of these defects sit near contract-bound files.

## Deliverables — the floor

1. The defect backlog cleared, each item with a behavioural test and its A/B, or explicitly deferred
   with a reason.
2. D-1 closed — the custody condition actually met, not just described.
3. The correction sweep landed, with amendment banners rather than silent edits.
4. Anything promoted from hygiene to finding, written up properly.
5. `IMPLEMENTATION_STATE.md` blocks **B140–B149**, and a full-suite A/B by failure set, committed.

Commit scoped work as you go, push your branch, do not merge to `main`.
