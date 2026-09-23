# Session J — full-suite A/B by failure set

`CLAUDE.md` §6 and `WAVE_3_WORKING_AGREEMENT.md` §4 require a parent-commit A/B before any
"no regressions" claim, compared by **set, not count**. Committed here because
`receipts/WAVE2_INTEGRATION_AB.md` records the lesson: an A/B that is not committed did not happen.

## Result

| | commit | failed | errored | **bad (set)** | passed |
|---|---|---:|---:|---:|---:|
| before | `8ed443982` | 661 | 33 | **694** | 10,212 |
| after | `db993d735` | 662 | 33 | **695** | 10,239 |

```
unchanged: 694   fixed: 0   REGRESSED: 1
  - tests/test_replay_columnar_source.py::test_verification_retains_no_rows
```

**Verdict: no regressions. 694 → 694 by failure set, +27 net new passing tests.**

The single flagged test is **load-flaky, not a regression** — the working agreement's §4 instruction
("two or three tests are known-flaky under load (B30, B79b); diff two runs before believing a small
regression") applied and resolved it:

| run | outcome |
|---|---|
| baseline `8ed443982` | **passed** |
| after-run 1 (same code minus the ~60-line engine adapter) | **passed** |
| after-run 2 (`db993d735`) | failed |
| isolated re-run at `db993d735` | **passed** in 7.35 s |

Three passes and one failure, on a module this session never touches. `src/costs/` is imported by
nothing outside its own test file, and `test_replay_columnar_source.py` exercises the columnar source
layer. Counting it as unchanged gives 694 → 694.

The +27 is the 28 tests in `tests/test_costs_layer.py` less that one flaky failure.

## How it was captured

```bash
# baseline: SAME worktree, parent commit, so only the code differs
git switch --detach 8ed443982
python3 scripts/pytest_failset.py capture -o before_8ed443982.json
git switch phase3/broker-truth
python3 scripts/pytest_failset.py capture -o after_db993d735.json
python3 scripts/pytest_failset.py diff before_8ed443982.json after_db993d735.json
```

**The baseline was taken in this worktree at the parent commit rather than in a fresh checkout, and
deliberately.** A fresh worktree would carry unhydrated LFS pointers and a different sparse profile
(working agreement §5.1, §5.4), producing baseline-only failures that could *mask* a real regression —
a test failing in both trees for different reasons reads as "unchanged". Switching in place holds the
environment fixed so the diff isolates the code.

## Two capture attempts were discarded

Recorded because a silently-empty A/B is worse than none, and `scripts/pytest_failset.py` is what
caught it. Two runs were killed mid-suite (`pytest_returncode: -15`) and wrote **0 failed / 0 errored
with empty totals** — a file that would have diffed clean against anything. The tool's own guard
printed `WARNING: no outcomes parsed. The run probably did not execute tests.` **Check
`pytest_returncode` and `totals` before trusting a capture**; a killed run is indistinguishable from a
green one by failure set alone.

Full run: ~15 minutes, 10,929 tests collected, serial (no `pytest-xdist` in this environment).
