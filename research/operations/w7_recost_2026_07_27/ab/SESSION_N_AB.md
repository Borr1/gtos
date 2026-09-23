# Session N — full-suite A/B by failure set

**Baseline `7e36ac9dc`** (`phase3/broker-truth` tip, this session's branch point) →
**after `4c0445004`** (`phase3/w7-recost` tip).

## Result

**673 bad → 673 bad by failure set. 0 regressed, 0 fixed, +18 net new passing tests.**

| | before `7e36ac9dc` | after `4c0445004` |
|---|---:|---:|
| failed | 640 | 640 |
| errored | 33 | 33 |
| **bad (set)** | **673** | **673** |
| passed | 10,261 | **10,279** |
| skipped / xfailed | 27 / 1 | 27 / 1 |

`unchanged: 673   fixed: 0   REGRESSED: 0`

The +18 is exactly `tests/test_w7_recost.py`. The change is additive — two new scripts
(`recost_w7_validation.py`, `build_survivor_book.py`), one new test module, one new route directory —
and touches nothing under `src/`, no config, and **no R2-bound path** (checked: zero bound paths under
`scripts/` or `src/costs/`).

Reproduce:
```
python3 scripts/pytest_failset.py capture -o ab/before_7e36ac9dc.json     # at 7e36ac9dc
python3 scripts/pytest_failset.py capture -o ab/after_4c0445004.json      # at 4c0445004
python3 scripts/pytest_failset.py diff ab/before_7e36ac9dc.json ab/after_4c0445004.json
```

## Hand-checked, because the refusal guards are not on this branch

Sessions L and M hardened `scripts/pytest_failset.py` after a full-suite capture was SIGTERMed and the
tool wrote a green baseline for a run that had executed nothing. **Those guards live on
`phase3/evidence-packs` and `phase3/hygiene-batch`, not on this branch's parent**, so both captures
were checked by hand before being trusted:

| | before | after |
|---|---|---|
| `pytest_returncode` | 1 | 1 |
| `totals` non-empty | ✓ | ✓ |
| `failed` + `errored` entries == `totals` failed+error | 640+33 = 673 ✓ | 640+33 = 673 ✓ |
| `parse_complete` | `True` | `True` |
| commit recorded | `7e36ac9dc` | `4c044500` |
| tracked-file modifications | **none** (`git diff HEAD` empty) | none |

**A capture with `totals: {}` is an absence of measurement, not an absence of failures.** Neither of
these is that. The baseline records `dirty: True`; that is the untracked
`research/operations/w7_recost_2026_07_27/` output directory only — `git diff HEAD` at the baseline
was empty.

## Why 673 and not B119's 694

Counts are not portable across worktrees, which is why the agreement asks for **sets**. B119 measured
694/695 in a different worktree; this pair was captured back-to-back in *this* worktree with identical
LFS and sparse-checkout state, run sequentially with nothing else competing. The set comparison within
that pair is what licenses the claim.

## Conditions

Both runs sequential, same machine, same worktree, ~17–18 minutes each, ~5.1 GB reclaimable memory,
nothing else competing. **This is the run that was deliberately deferred in B164** — Session K held
the machine at the time and launching into ~79 MB free is exactly the condition that produced the
killed-capture defect.
