# Wave-2 integration A/B — the full-suite failure-set comparison

**Run 2026-07-26 (UTC), reported here 2026-07-27.** This receipt exists because the third review's
adversarial pass (`THIRD_REVIEW.md` §A2 item 1) correctly found that **no full-suite A/B existed in
the repo for the integrated wave-2 tree** — the 507→507 zero-regression receipt (B51/B57) certifies
the *wave-1* merge already in `main`, not this one.

The A/B had in fact been run, concurrently with the review, by the orchestration session. It lived
in a scratchpad rather than in the tree, so to any later reader it did not exist. **That is the
finding, and this file is the fix.** Evidence outside the repository is not evidence.

---

## Result

```
before  a890a66d2  ('Third review: remove the language that would have held Fable back')   695 bad
after   8440264b5  ("Merge branch 'main' into review/wave2-integration-20260727")          695 bad

unchanged: 695    fixed: 0    REGRESSED: 0

No regressions.
```

**+145 net new passing tests** — 10,066 → 10,211.

| | baseline | integrated |
|---|---|---|
| commit | `a890a66d27f1bda3` (`main`) | `8440264b5` (four wave-2 branches merged) |
| captured (UTC) | 2026-07-26T18:56:15Z | 2026-07-26T18:43:52Z |
| failed | 662 | 662 |
| errored | 33 | 33 |
| **bad (failed + errored)** | **695** | **695** |
| passed | 10,066 | 10,211 |
| working tree | clean | clean |
| pytest args | `tests/` | `tests/` |

Compared by **failure set**, not by count — `scripts/pytest_failset.py diff <before> <after>`.

## Why a purpose-built baseline was necessary

Counts are not portable across worktrees: the wave-2 worktrees are sparse checkouts and measure a
different total than a full checkout (B39 — the ~177 delta is missing evidence fixtures, not broken
code). Sessions G and H each reported **694** in their own single-branch trees; `main` measures
**695** here. Neither number is wrong; they are not comparable, which is exactly why the rule is
sets.

So the baseline was built to match the integrated tree in every respect that could move the set:

- fresh worktree `worktrees/ab-main-baseline-20260727`, detached at `main` @ `a890a66d2`
- identical sparse configuration, including `git sparse-checkout add /shadow_logs/ /pipeline_state/`
  (132 + 104 files — absent by default in these sparse trees, and their absence moves the set)
- identical offline LFS hydration
- same machine, same Python (`/opt/homebrew/bin/python3`)

## What this does and does not certify

**Does:** the four wave-2 branches, merged together, introduce no test that fails at the integrated
tree and passed at `main`. This is the check no individual session could run — each verified its own
branch in isolation, which cannot catch an interaction between four independent changes.

**Does not:** say anything about the 695. That population is pre-existing and unrelated (H2; Session
C closed Q4 at 77.4 % environment-bound with zero genuine defects on the live decision path).

**Per-branch coverage, stated because §A2 was right to ask:** three of the four wave-2 sessions
touched `src/` and each A/B'd zero regressions in its own tree (B79b, B88, B99a). Session E changed
no `src/` file at all — 9 files: docs, two scripts, one test — and has no suite A/B of its own. It is
covered by this one.

## Reproduce

```bash
python3 scripts/pytest_failset.py capture --out /tmp/before.json     # at the baseline commit
python3 scripts/pytest_failset.py capture --out /tmp/after.json      # at the merge commit
python3 scripts/pytest_failset.py diff /tmp/before.json /tmp/after.json
```

`diff` takes **positional** arguments (`before after`), not `--before/--after`.

## Standing rule this establishes

An A/B that is not committed did not happen. Every future integration merge lands its capture pair's
summary in `docs/audits/**/receipts/` in the same commit as the merge, or the merge states the
residual in its own message.
