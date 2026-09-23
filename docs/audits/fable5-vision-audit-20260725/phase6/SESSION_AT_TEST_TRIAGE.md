# Session AT — retire the tests that protect nothing, and make the A/B cheap

**Wave 6.** Worktree `worktrees/wave6-test-triage-20260729`, branch `phase6/test-triage`, from
`main`. **Blocks B900–B949.**

**Read `../WAVE_6_WORKING_AGREEMENT.md` §0 first**, then `../FOURTH_REVIEW.md` §6.3.

---

## The instruction, in the owner's words

Borhen, 2026-07-30:

> can we just get rid of the tests that dont matter, as most of these 600 something issues arent
> real anyway, i dont want to keep doing this A/B i think it's silly and has no value

**He is substantially right and the measurement backs him.** Across 16 A/B runs on 2026-07-29, five
reported a REGRESSION and **all five were the same handful of load-sensitive tests** — zero real
regressions were caught by a full-suite A/B in that period. The two genuine catches of the day came
from *reading the failure list*, never from the count. The standing set is ~660 bad on a suite of
~11,400, and it has been that way for six waves.

**Your job is to make the number mean something again, by deleting what earns it.** This is a
deletion session. The default is retirement, and keeping a failing test requires a reason.

## What is already measured — do not re-derive it

`IMPLEMENTATION_STATE.md` **B372** partitioned the 660 [MEASURED, Session U]:

| bucket | n | share |
|---|---:|---:|
| **absent data** — a file missing from disk | **321** | 52.3 % |
| code-shaped — `AssertionError` | 197 | 32.1 % |
| code-shaped — other exception | 40 | 6.5 % |
| unclassified (mostly bare `StopIteration`) | 33 | 5.4 % |
| absent dependency — import error | 12 | 2.0 % |
| **absent data** — unparseable JSON (the LFS-pointer shape) | **11** | 1.8 % |

**Of the 321 missing-file failures, 250 name a path that IS committed in `HEAD`** — all under
`research/`, which the sparse profile excludes. Hydrating all of `research/` is **5.6 GB and 20,282
files**; that is a real option for a subset and a bad one wholesale.

And the concentration, measured by the orchestrator today from a 694-id capture:

| test file | failures | binds to |
|---|---:|---|
| `tests/test_gtos_vnext_master_conversion_ledger.py` (20,623 lines) | **188** | `research/a2_v2_active_backtest/` — the A2-V2 era, listed **historical** in `CLAUDE.md` §10 |
| `tests/test_gtos_vnext_runtime.py` (32,173 lines) | **111** | `research/full_matrix.jsonl`, `gate.jsonl`, `frozen_ready_action_runtime_rule_ledger.jsonl` — **but also tests live code**, the prop-safe selector |
| `tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py` | **31** | V4-vs-V3 frozen replay — and **V3 is `false`/default-off** (`CLAUDE.md` §4) |
| 11 further files at ≥10 each | (to 392 total) | |

**Two files carry 43 % of the noise.**

## The one thing you must not do

**Do not delete a test file wholesale because most of its failures are stale.** Both big files mix
route-bound tests with tests on code that is *live*: `gtos_vnext_runtime.py` carries the prop-safe
selector, and FTMO is trading real money right now. Deleting 111 tests to clear 111 failures would
remove live coverage silently — the exact false economy of deleting a smoke alarm because it keeps
going off.

**Triage per test, not per file.** That is the only constraint on this session.

## The decision rule

For each failing test, one of four dispositions, each recorded:

| disposition | when | what to do |
|---|---|---|
| **DELETE** | asserts against a superseded route's artifacts, and nothing current consumes that route | remove the test; name the route and the authority that supersedes it |
| **HYDRATE** | needs a `research/` path committed in `HEAD`, and the route is **current** | `git sparse-checkout add` the directory; report the disk cost |
| **SKIP-WITH-REASON** | protects real behaviour but its fixture data is gone and not reconstructible | `pytest.mark.skip(reason=...)` naming exactly what data would restore it — **never a bare skip** |
| **KEEP — REAL** | code-shaped failure on a live or reachable path | leave failing, and file it with `file:line` and what it means |

**Reachability is the test.** `OVERENGINEERING_AND_DELETION_MAP.md` measured that **21.7 % of 1.33 M
Python lines is reachable from a current entrypoint**. A test whose subject is unreachable and whose
route is superseded is protecting nothing.

## What good looks like

1. **A disposition for all ~694**, in one machine-readable artifact
   (`TEST_TRIAGE_V1.json`: id, bucket, disposition, reason, authority).
2. **The deletions applied**, with the standing failure set re-measured after. State the number
   plainly — if it goes 660 → 300, say so; if the honest total is 550, say that.
3. **The A/B made cheap**: propose and implement scoping by blast radius in
   `scripts/pytest_failset.py`. A docs-and-new-tests branch should not run 11,400 tests. A branch
   touching `src/` on a live path must. The orchestrator already added `KNOWN_LOAD_FLAKES` there
   (commit `9fe4136f0`) — extend that instrument rather than building a second one.
4. **Any further load flakes you verify** added to `KNOWN_LOAD_FLAKES` with the evidence, per its
   docstring: it only earns an entry after failing at the BASE commit too, or passing in isolation
   at the commit that "broke" it.

## Traps

- **Do not edit `config/agent_config.yaml`** — the live activation token binds its digest; one byte
  stops the armed FTMO book placing.
- **H1: check decision-contract membership before editing under `src/`.** You should not need to
  touch `src/` at all; if you do, that is a finding.
- **`git status` clean does not mean present.** Sparse-checkout carries the skip-worktree bit;
  `git ls-files -v <path>` shows it.
- **`CLAUDE.md` §8 is the authority you are acting under**: *"Delete, compress, rewrite, or demote
  stale context pollution after proof."* **After proof** is the operative phrase — every DELETE row
  needs its supersession named, not asserted.
- **Do not `git clean` or `git checkout` inside the denominator-to-deployment route** — two
  `REPLAY_EXTENSION_*` paths there are load-bearing *by their absence* (`CLAUDE.md` §4).

## Method

This is a build task and the burden of proof is inverted the same way as everywhere else in wave 6:
**the default is retirement.** Keeping a failing test requires naming what it protects. Do not
commission an adversary to argue for keeping tests; if a check would end in "therefore keep", make it
end in "therefore keep, because it covers X on a reachable path."

Your own A/B is the one that matters most in this wave: **you are changing the measuring instrument,
so measure before and after and show the failure sets, not the counts.** A deletion that also removed
a passing test would be invisible in a count and obvious in a set.

## Not yours

The VPS. Arming, tokens, gates. Broker-capable scripts. Merging to `main`. Sleeve composition.

Use your own judgment on scope and on whether anything above is wrong.
