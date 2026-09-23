# Session G — Single-materialisation columnar source layer

**Phase 2, final work item — pulled forward deliberately.** Worktree
`worktrees/phase2-columnar-source-20260726`, branch `phase2/columnar-source`, from `main`.
**Your block range is B80–B89.**

**Read `../WAVE_2_WORKING_AGREEMENT.md` first** — authority, orchestration grant, hard constraints, and
four environment traps found and fixed the night before this wave.

---

## Why this is first in the wave rather than last

The plan lists this at the end of Phase 2. It is running first because **it is the constraint on
everything else's wall-clock time**, and it depends on none of the policy work.

`CLAUDE.md` H3: memory is the binding constraint, not CPU. **One replay arm peaks at 8.61 GB maxrss on a
16 GiB machine.** That is why parallel replays are forbidden today, why one month-window of four arms is
~16.5 h, and why every gate in Phases 2–5 that carries replay cost carries it serially.

The first audit's finding is the target: the source layer materialises the same bars **5×** and ticks
**4×**. Kill the copies and the arm fits. The audit's target is **≤3 GB/arm**.

This is the highest-leverage infrastructure item in the plan, and it is pure engineering — no owner
decision, no economic judgement. **Optimise hard.**

---

## Read this before you plan your measurements

**Three other Claude sessions are running on this machine right now**, each with subagents. Your session
is the one whose deliverable is a memory number, and they are contending with you for the thing you are
measuring.

Handle it explicitly rather than being surprised by it:

- Record what else was running for every measurement you report, and prefer a method that is robust to
  it (peak RSS of your own process tree, not free-system-memory).
- If you need a quiet machine for the headline before/after and the four-arm demonstration, **ask Borhen
  for a quiet window** — he is at the terminal and the other three sessions can idle. This is a
  legitimate request, not an imposition.
- A number measured under contention is still worth reporting as long as it is *labelled* as such.

---

## The hazard that shapes the whole session

**H1.** The obvious files to edit are decision-contract-bound. `replay_acceleration_source_batch.py`,
`replay_acceleration_integrated_source.py`, and the attempt5 runner are all in R2's 43 bound paths **and**
in `code_authority_paths` (`replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`), which binds
them a second time from inside an executing file — so OD-2's verification split cannot free them.

Editing any of them means: regenerate the contract, re-seal, and **re-run every affected window at
~16.5 h each**. That is not a reason to refuse the work. It *is* a reason to know, before writing a line,
exactly which side of the boundary each file sits on. **Run the membership check first and write the
answer into your first block.**

Two viable shapes. **This is the session's first real decision and it is genuinely open — decide it on
your own measurements, not on precedent:**

- **Additive** — a new source layer beside the bound one, selected by the new core, leaving the sealed
  path byte-identical. Preserves comparability across every arm already run; costs a parallel
  implementation and leaves two layers to maintain.
- **In-place** — edit the bound files, re-seal, re-run. Cleaner end state, single implementation;
  expensive, and every prior arm is incomparable until re-run.

The plan's prose leans additive (*"the old engine stays sealed for comparability"*), and prior sessions
have defaulted that way — treat that as context, not as a recommendation. If your measurements say
in-place is right, say so, quantify the re-run bill, and put the choice to Borhen with both costs; it is
his call to authorise a re-seal. Deliver the additive path as the working default meanwhile so the
session lands either way.

---

## Measure before optimising

Do not trust the 5×/4× figure or the 8.61 GB figure because a document says so. Both are in
`docs/audits/opus5-architecture-20260725/` with receipts; **reproduce them** and put your own number in
your first block. `docs/audits/opus5-architecture-20260725/receipts/profile_day_harness.py` is a working,
annotated invocation.

Note the unit trap already recorded: the oft-quoted "15.3 GB footprint" is a **GiB/GB echo of the same
8.61 GB measurement**, not a second observation. If you find a third number, check it is not a fourth
restatement of the first.

## What "done" means

- A source layer that materialises each bar and tick series **once**.
- **Measured** peak RSS per arm ≤3 GB, by the same method as the baseline — not estimated from
  allocation counts.
- A demonstration that **four concurrent arms fit in 16 GiB**, run when the machine is quiet.
- Row-level identical output to the current layer on at least one sealed day. **Session D's differential
  harness exists for exactly this** — `src/research_infra/replay_differential_harness.py`, with
  `compare_arms(...)`, `alignment="identity"`, and a self-comparison null control. Use it rather than
  writing a new comparator; it is unbound by either contract.

**On the wall-clock claim: derive it, do not assume it.** Four arms fitting in memory does not by itself
turn 16.5 h into ~4 h — that assumes perfect scaling. H3 measured contention only at *two* concurrent
arms (~1.1–1.3× net), and that curve should not be extrapolated to four. Measure the four-arm wall clock
and report what you actually get.

## Two things that will bite

1. **`zstd`-backed cold evidence is now the norm.** 284 ledgers under the denominator-to-deployment route
   were cold-demoted on 2026-07-26 (B53) and are read in place by
   `research/operations/…_2026_07_16/b7_5_cold_evidence.py` — seekable, streamed, unbound by any
   contract. Your layer must read the cold format, not assume flat `.jsonl`. Day boundaries are
   recoverable by decompressing one line per shard (~1 s for 16 shards), which Session D found and which
   is directly useful here.
2. **Do not `git clean` or `git checkout` inside that route.** Two `REPLAY_EXTENSION_*` paths are
   load-bearing **by their absence**, and `.gitattributes` there is the only LFS rule — without it a
   checkout writes pointer text instead of content.

**H4 applies to replays.** Sealed authority binds absolute paths, and replays only run from the producing
worktree — copying evidence elsewhere gets it rejected with
`fresh_source_authority_path_binding_mismatch`. If a step genuinely requires running a sealed arm from a
worktree that cannot host it, say so, finish everything that does not depend on it, and put the blocked
step to Borhen with what it would take.

## Deliverables — the floor

1. The source layer, with tests.
2. A receipt with **measured** before/after peak RSS and wall-clock, the four-arm demonstration, and the
   contention conditions each number was taken under.
3. Harness output proving row-level identity on at least one sealed day.
4. An explicit statement of which contract-bound files were touched — ideally none — and what a re-seal
   would cost if any were.
5. `IMPLEMENTATION_STATE.md` blocks **B80–B89**.

Commit scoped work as you go, and push your branch. Do not merge to `main`.
