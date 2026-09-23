# GTOS Phase 2, Session D — revive the differential harness

Phase 0 is complete, Gate G0 met. Work on branch `phase2/harness-revival` in
**`/Users/borr/GTOSActive/worktrees/phase2-harness-20260726`** — your own worktree. Push with
`GIT_LFS_SKIP_PUSH=1 git push -u origin phase2/harness-revival`. Do not commit to `main`. Three Phase-1
sessions are running concurrently in their own worktrees; your files are disjoint from all of them.

Use `/opt/homebrew/bin/python3` (system 3.9 cannot parse this codebase).

---

## 1. Read order

1. `CLAUDE.md` — hazards H1–H7. **H1 was rewritten**: contract of record is **R2**, 43 bound paths.
   **H3 (memory), H4 (absolute-path binding) and H5 (no sub-window replay) all bind your work.**
2. `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — B1–B26 supersede numbers both
   audits carry, especially B25 on what OD-2 actually freed.
3. `docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md` — **Phase 2**, and Phase 3 for what
   your work unblocks.
4. `docs/audits/opus5-architecture-20260725/REPLAY_TRUTH_AND_PERFORMANCE_AUDIT.md` — the profiles and
   measured baselines.
5. Preflight per `CLAUDE.md` §2.

---

## 2. The task, and why it is first

Phase 2 rebuilds the replay around one policy-plural decision core. That is where the throughput comes
from — **72.4 % of replay CPU is proof/attribution machinery and 0.2 % decides trades**, and a dense
day is 507.6 s today against a 150–250 s target.

**But you cannot prove a rebuild is equivalent without a comparator, so the harness comes first.** The
plan is explicit: *differential harness first, core second.* Build the core first and every parity
claim afterwards is an assertion.

The good news is E7's irony: **~80 % of the harness a rebuild needs is already written and tested**,
sitting dead. Three modules, in the plan's revival order:

| Module | Lines | What it gives you | Contract status |
|---|---:|---|---|
| `replay_acceleration_task2_semantic_acceptance.py` | 3,433 | row-level comparison, **fails closed on unknown differences** | **FREE — OD-2 freed it this week.** Editing it used to break the next replay closed |
| `replay_acceleration_partial_golden_verifier.py` | 2,008 | successor-acceptance framing | **FREE** — never bound |
| `replay_acceleration_streaming_archive_verifier.py` | 1,353 | day-shard granularity | **BOUND, and doubly** — in `input_bindings` *and* in `code_authority_paths` (`attempt5:1405-1431`). Editing costs a contract generation |

That third row is the operational fact to plan around. Two of the three are free to change; the third
is not, and OD-2's split cannot free it because the second binding lives inside an executing file. If
you need to change it, batch the edit and generate an R3 the way
`build_b7_5_post_acceleration_contract_r2_verification_split.py` generates R2 — read that builder, it
is short and it documents the three fields that must stay byte-identical (`schema`, `status`,
`predecessor_contract_binding`) because `attempt5:929-990` pins them to hardcoded constants.

**What "revived" means:** the harness can take two arm outputs and say *these differ at row X, field Y*
— or prove they do not. That capability is the whole deliverable. It is what makes every later
rebuild step falsifiable instead of hopeful.

---

## 3. Constraints that will shape your design

- **H3 — memory is the binding constraint, not CPU.** One arm peaks at **8.61 GB maxrss** on a 16 GiB
  machine. Two concurrent arms measured ~1.1–1.3× net. **Do not run parallel arms here.** The ≤3 GB/arm
  target is Phase 2 work, not yours.
- **H4 — sealed authority binds absolute paths.** `replay_acceleration_attempt5_typed_sparse_runner.py:186-190`
  hardcodes `/Users/borr/GTOSActive/repo`. Replays only run from the producing worktree. Your harness
  should not inherit that; a comparator that only works in one directory is half a comparator.
- **H5 — no sub-window replay exists.** Three independent assertions force a full sealed month, and
  `engineering_stop_after_day` is hardcoded `None` on the sealed path
  (`b7_5_post_acceleration_runner.py:832`). So debugging one day costs a full arm (~4.1 h). **This is
  the constraint most likely to slow you down, and making the harness work on a day-shard is the
  cheapest way around it** — which is exactly what `streaming_archive_verifier` was built for.
- **One arm-month is ~4.1 h.** Budget accordingly; prefer the sealed January arms that already exist
  (`/Users/borr/GTOSActive/repo`, read-only) over generating anything new.

---

## 4. Method — use the orchestration

The owner has explicitly authorised multi-agent workflows. Use them. This programme's two live-risk
defects were found by a 28-agent adversarial pass, not by careful reading.

Where a workflow earns its place here:

- **Reading the three modules.** ~6,800 lines across three dead files. One agent per module, in
  parallel, each returning what it does, what it needs as input, why it stopped executing, and what it
  would take to revive. That is a genuine fan-out, not a token-burn.
- **Comparator validation.** Once it runs, feed it pairs that *should* differ and pairs that should
  not, in parallel — a comparator that never reports a difference is worse than none, and the only way
  to know is to hand it known-different inputs and check it says so.
- **Adversarial verification before you claim it works.** Agents briefed to **refute with `file:line`**,
  specifically hunting the case where the harness reports equivalence it has not established.

## 5. Anti-drift — this task has a characteristic way of going wrong

**Reviving a dead verifier turns into rewriting it.** These modules stopped executing for reasons; some
of those reasons are that the world moved. Fix what blocks execution. Do **not** redesign the
comparison semantics because you would have done it differently — that is a Phase 2 core decision, not
a harness one, and it destroys the comparability that makes the harness worth having.

**Do not start the core.** The plan sequences harness-then-core deliberately. If you find yourself
extracting `BroadV4Policy`, stop; that is the next session.

**A green comparator that compares nothing is the failure mode.** These files are SHA-bound as if they
mattered while never executing — E7's point. Prove yours executes and discriminates before you believe
its output.

---

## 6. Working rules

- **A/B every change** with `scripts/pytest_failset.py capture` + `diff` against
  `docs/audits/fable5-vision-audit-20260725/receipts/baseline_full_suite.json` (650 failed / 9,747
  passed / 33 errors at `212ad7e6d`). Compare failure **sets**, never counts. Run the **whole** suite —
  Phase 0 had three regressions that passed in isolation and only appeared in a full run.
- Always `--continue-on-collection-errors`; without it the run executes **zero** tests and still exits
  like a completed run.
- **H1 check before editing anything under `src/`.**
- **Never execute broker-capable scripts.** C1: `create_mt5("live")` succeeds on macOS; the ImportError
  only surfaces on `.connect()`.
- Prefer behavioural tests over source-string assertions.
- Report faithfully: failed tests with output, skipped steps named, "done" means verified.

**Traps already paid for:** `zsh` eats `git show $V:path` (use `git cat-file -p "${V}:path"`); `rg -r`
is `--replace`; `rg` cannot see sparse-masked files, so any census uses `git ls-files`; **never delete a
module from `sys.modules` and re-import** (it creates a second module object and `multiprocessing` then
refuses to pickle functions from it — this broke three unrelated tests in Phase 0 and only showed up in
a full-suite run).

---

## 7. You are done when

The harness takes two arm outputs — start with two of the four sealed January arms, which are known to
differ — and reports **where** they differ at row and field level, fails closed on a difference it does
not understand, and proves on a known-identical pair that it does not cry wolf. Plus an
`IMPLEMENTATION_STATE.md` update with evidence tags and a declared-gaps section, and a receipt in the
shape of `GATE_G0_RECEIPT.md`.

If revival turns out to be the wrong call for one of the three — genuinely dead, not worth the repair —
say so with the evidence and move on. Two working comparators beat three half-revived ones.
