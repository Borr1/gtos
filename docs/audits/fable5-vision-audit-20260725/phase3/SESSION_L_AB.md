# Session L — full-suite A/B by failure set

**Block B139.** Working agreement §4: *"A/B is mandatory before any 'no regressions' claim. Sets, not
counts. And commit your capture summary — the wave-2 A/B was run and not committed, so to the next
reader it did not exist."*

## Result

```
before 8ed443982 ('Cleanup: retire twelve merged worktrees' — session start tree): 694 bad
after  c1834b18b ('Session L: IMPLEMENTATION_STATE blocks B130-B139'):             694 bad
unchanged: 694   fixed: 0   REGRESSED: 0

No regressions.
```

| | before | after | delta |
|---|---:|---:|---:|
| failed | 661 | 661 | 0 |
| errors | 33 | 33 | 0 |
| **bad, by failure set** | **694** | **694** | **0 regressed / 0 fixed** |
| passed | 10,212 | **10,218** | **+6** |
| skipped | 27 | 27 | 0 |
| xfailed | 1 | 1 | 0 |

**+6 net new passing tests, zero regressions by set.** The six are exactly the behavioural tests
added for the `pytest_failset` fix below.

Command: `python3 -m pytest -q --tb=no -p no:cacheprovider --continue-on-collection-errors tests/`
Wall clock: **1,625 s (27 m 05 s)** per side.

## Provenance, stated because the two sides were produced differently

- **BEFORE** — a full-suite run started **before this session edited any file**, so its collection
  predates the changes. Its raw output was parsed into a failset record with the same `_parse()` the
  tool itself uses. All 694 ids were recovered against pytest's own totals (`parse_complete: true`),
  which is the check that makes the set trustworthy.
- **AFTER** — `scripts/pytest_failset.py capture` at `c1834b18b`.

Both sides ran `tests/` with identical arguments; `diff` refuses mismatched scopes, and did not.

## What this session changed, for scope

| category | files | can it move the suite? |
|---|---|---|
| new analysis harnesses | `scripts/evidence_pack_{dial_grid,shed_ab,day_key_mc}.py` | **no** — no test imports them |
| documents | `EVIDENCE_PACKS_RECEIPT.md`, `OWNER_DECISION_PACKETS_SESSION_L.md`, `JANUARY_BANK.md`, `IMPLEMENTATION_STATE.md`, `evidence_packs/*.json` | no |
| **the A/B tool** | `scripts/pytest_failset.py` + `tests/scripts/test_pytest_failset_parsing.py` | **yes** — and it accounts for the +6 |

No `src/`, no `config/`, no contract-bound file. The H1 membership check reports `drifted=1`, which is
the known false alarm the working agreement documents (the sleeve-registry ledger differing only in
`generated_utc` and its derived `row_hash_sha256`); **no second drifted path**, 43 bound paths checked.

## The defect this A/B exposed in the A/B tool itself

Producing the baseline found a real hole in `scripts/pytest_failset.py`, fixed in `ac1de9711`.

A full-suite `capture` was terminated by an outer 600-second timeout. pytest never printed its counts
line, and the tool wrote a well-formed record with `totals: {}`, an empty failure set,
`parse_complete: true`, and — the only surviving evidence — `pytest_returncode: -15` (SIGTERM).

`cmd_capture` did return 2 and print a warning, so the command was not silently green. But **the
artifact on disk was indistinguishable from a clean run**, and `cmd_diff` consumed it without
complaint. The exit code is not the artifact. And the existing loudness guard could not catch it:
`_parse` sets `parse_complete = False` only inside `if totals and recovered != expected`, so an
**empty** `totals` short-circuits the very check that exists for this case.

Both reading directions are silent and both are wrong:

- an incomplete capture read as the **baseline** makes every real regression look pre-existing;
- an incomplete capture read as the **after** makes every pre-existing failure look fixed, and `diff`
  prints **"No regressions."** and exits 0.

**The more dangerous variant, which the original code could not have caught at all:** a run killed
*after* pytest printed its summary parses "successfully" — non-empty totals, ids recovered,
`parse_complete: true`, exit 0 — and is a silent truncation of an unknown fraction of the suite. Only
the negative returncode distinguishes it, and nothing read it.

**Fix.** `capture` now derives `usable_as_baseline` / `unusable_reasons` from three independent
conditions — negative returncode, empty totals, incomplete parse — and writes them **into the
record**, so the artifact carries its own verdict. `diff` refuses any side marked unusable, and
separately refuses records that predate the field but exhibit the same symptoms, so older captures
cannot be laundered by their age.

Six behavioural tests drive `cmd_capture`/`cmd_diff` and assert on what they write and return,
including the killed-after-summary case — a record with correct totals and correctly recovered ids is
still refused. They deliberately do not grep the source for a string (working agreement §6).

Verified end to end: the original killed artifact is now refused by `diff` with
`pytest_returncode -15 (killed by signal)` and `no totals parsed` named as the reasons.

## Reproduce

```bash
python3 scripts/pytest_failset.py capture -o before.json      # at the parent tree
python3 scripts/pytest_failset.py capture -o after.json       # at HEAD
python3 scripts/pytest_failset.py diff before.json after.json # positional; exit 1 on regression
```

Two or three tests in this suite are known-flaky under load (B30, B79b); a small apparent regression
should be diffed twice before it is believed. None appeared here.
