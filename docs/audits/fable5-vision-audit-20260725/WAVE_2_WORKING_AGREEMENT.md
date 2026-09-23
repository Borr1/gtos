# Wave 2 — working agreement

Included by reference from all four session prompts (E, F, G, H). Read it once; it is the same for
everyone.

---

## How to work

**You have full engineering authority inside your worktree.** Change production code, config, tests,
verifiers, launchers and research artifacts as needed to build the strongest result. The constraints
further down are about two specific things — *not corrupting sealed evidence* and *not touching a live
broker*. They are not a signal to work cautiously or narrowly. Inside them, be aggressive.

**Your judgment outranks this prompt.** It was written before the work started, by someone who had not
done it, and it will be wrong about something. Where the evidence contradicts a premise here, act on the
evidence and record the correction — that *is* the result, not a deviation from it. Wave 1's strongest
session withdrew its own headline twice and was better for it. Do not implement something you can see is
wrong because a prompt said so; say so and do the right thing.

**Orchestrate freely.** You are authorised to use subagents (the Agent tool) and the Workflow tool at
whatever fan-out the task warrants: parallel readers over independent evidence, adversarial verifiers
against your own findings, judge panels over competing designs, loop-until-dry sweeps where the size of
the problem is unknown. **This is standing approval from the owner — you do not need to ask, and you
should not run single-threaded out of politeness.** Independent verification of anything you are about
to assert is expected, not optional; this programme's failures have consistently been confident first
answers.

**The deliverables are a floor, not a ceiling.** If the work opens something more valuable than what is
listed, pursue it and say why. If you finish early, go deeper — do not stop at the list.

**If one branch is blocked, finish every other branch in full,** then state plainly what you left out
and why. A blocked sub-task is never a reason to deliver less overall, and it is not a reason to end the
session.

**Borhen is at the terminal.** If you reach a genuine owner decision — the risk dial, allocation
profile, re-sealing the economic contract, anything that changes what the system trades — ask him
directly and keep working on everything else meanwhile. Do not stall, and do not quietly absorb the
decision yourself. Everything that is not that is yours to decide.

---

## Environment — verified 2026-07-26, read before your first command

Four traps were found and removed the night before this wave. The first three are already fixed; you
need to know them so you do not re-diagnose them.

- **Your worktree is a sparse checkout.** `research/` is largely excluded (`knowledge_base*`, `exports/`
  entirely). `tests/` is complete. `shadow_logs/` (132 files) and `pipeline_state/` (104) were restored
  on 2026-07-26. The R2 contract and `b7_5_cold_evidence.py` are present.

- **The `507 bad` test baseline is from a FULL checkout and will NOT reproduce here.** Expect roughly
  **684**; the ~177-failure delta is missing evidence fixtures, not broken code (B39). **Capture your own
  baseline in your own worktree before changing anything**, and A/B only against that. Never compare a
  failure count across worktrees — compare failure *sets*, in one tree, with `scripts/pytest_failset.py`.

- **The H1 membership check reports `drifted=1` here. That is expected, pre-existing, and not yours.**
  `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` differs from R2's expected hash in exactly
  two fields — `generated_utc` and its derived `row_hash_sha256`. All 82 rows are otherwise identical to
  the sealed copy in `/Users/borr/GTOSActive/repo` (verified field-by-field, 2026-07-26). It is a
  regeneration-timestamp artifact, not economic drift. **A second drifted path means you caused it —
  stop and look.**

- **94 files under `research/` and `data/` are unhydrated LFS pointers** — 131-byte stubs where you
  expect data. *A pointer read as data is indistinguishable from an empty result*, which is this
  programme's signature failure mode. Check file size before trusting anything under those trees.
  Hydrate on demand with `git lfs checkout <path>`; the objects are in the local 55 GB store and need no
  network. (The two contract-bound sleeve ledgers were hydrated for you already.)

---

## Hard constraints — these are the real ones

- **Never execute broker-capable scripts**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
  `mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
  `flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. **`create_mt5("live")` succeeds
  on macOS** — the ImportError only surfaces at `.connect()`, so construction is *not* a safety boundary.
  Reading these files is encouraged; running them is not.
- **`/Users/borr/GTOSActive/repo` and `worktrees/replay-accel-*` are read-only.** Read them freely for
  comparison — the sealed registry copy lives there.
- **Run the H1 contract-membership check (`CLAUDE.md` §3) before editing anything under `src/`.**
  Editing a bound file forces a re-seal and ~16.5 h/window of re-runs; that is an owner decision, not a
  blocker you absorb.
- **H3 — memory, not CPU, is the binding constraint.** One replay arm peaks at 8.61 GB maxrss on a
  16 GiB machine, and **three other sessions are running concurrently**. Do not launch parallel replays.
- **`SECRETS_DO_NOT_COMMIT/` must never enter the repo**, and no live or replay code path may read an
  iCloud path.
- **Do not merge to `main`.** Commit on your branch, push it. Integration is done once, deliberately.
- **Stay inside your `IMPLEMENTATION_STATE.md` block range.** If you need more than ten, extend with
  letter suffixes (`B69a`, `B69b`) — never step into the next session's range. Three sessions collided on
  B27 last wave.

## Evidence discipline

- Tag every claim `[MEASURED]` / `[VERIFIED]` / `[INFERRED]` / `[HYP]`. Cite `file:line` for
  production-state claims.
- **Prefer behavioural tests.** This wave found seven test files silently validating a *different
  checkout* via a hardcoded `sys.path.insert`, and a source-string test that passed against a wrong
  implementation. A test that greps source proves nothing.
- **Before trusting any zero, prove your probe can see the thing it searched for.** An empty result from
  a broken probe is indistinguishable from a genuine empty — see the LFS-pointer trap above for a live
  example.
- When you correct yourself, record the correction, not just the corrected result.
