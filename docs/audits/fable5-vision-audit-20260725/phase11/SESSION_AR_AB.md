# Session AR — scoped verification receipt (agreement §2)

**Branch `phase11/conditioning-sizing`, merge-base `7d4852b0f`.**

## 1. Blast radius, named mechanically

```
python3 scripts/pytest_failset.py scope --base 7d4852b0f          # at the final HEAD
  -> 25 changed paths -> 219 test files by import closure and path literal
  escapes: []   unresolved: []   deleted_tests: []
```

219 files is a large scope for a small change, and the reason is `admission.py`: it is imported
by the whole `ultimate_book` surface, the replay policy, the walkforward book replay and every
launcher test. Six `src/` files changed plus `run_book.py`:

| file | change |
|---|---|
| `src/components/ultimate_book/admission.py` | `TradeIntent.vr`, `VOL_LEVEL_TILT_*`, `vol_level_tilt_for`, the split-tilt fold in `size_correlated_units`, the `vol_level_tilt` parameter on it and on `admit_and_size`, and the flag in all three report dicts |
| `src/components/ultimate_book/bridge.py` | `DEFAULT_CONFIG["ultimate_book_vol_level_tilt"]`, the `_bool` read, the passthrough |
| `src/components/ultimate_book/book_engine.py` | `vol_level_tilt` constructor arg + the injected runtime key at the bridge call |
| `src/components/ultimate_book/book_owner.py` | `vol_level_tilt` passthrough |
| `src/components/ultimate_book/sleeves/substrate.py` | `vr=st.get("vr")` on the emitted intent |
| `src/research_infra/replay_policy/sleeve_book.py` | `REPORTED_ONLY_KEYS` + `describe()` |
| `run_book.py` | `--vol-level-tilt` and its warning line |

Plus the audit tree, the repair queue and the trial ledger.

## 2. HEAD, over the full scoped set

| side | scope | result |
|---|---|---|
| **HEAD (final)** | all 219 files | **6,207 passed / 33 skipped / 19 xfailed / 11 failed** — 554 s |

(An earlier capture at the mid-session HEAD over 217 files read 6,190 passed / 11 failed. The +17 is
AR's own new tests plus two files entering scope; the failure set is unchanged.)

**The 11 failures are environmental and are proven so by a copy-back A/B**, not asserted. All 11
sit in two files this session never touched:

| file | n | cause |
|---|---:|---|
| `tests/test_b7_5_neutral_selection_factorial.py` | 10 | `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` — a 131-byte LFS pointer parsed as JSON |
| `tests/test_permissions.py` | 1 | `IndexError: list index out of range` at `:317`, the sleeve-registry pointer H2 names |

### The A/B, done by copy-back per agreement §2

The seven changed source files were saved, the merge-base versions written in their place, the two
files run, then the saved versions restored — all in Python, and `git status` verified clean
afterwards.

```
[MERGE-BASE source] 11 failed, 96 passed, 1 skipped
[MY change]         11 failed, 96 passed, 1 skipped

identical failure sets: True
regressed (in mine, not base): NONE
fixed   (in base, not mine):   NONE
n failures: 11 -> 11
working tree after restore: CLEAN
```

**196 of 4,151 LFS-tracked files in this worktree are un-hydrated pointers** after
`scripts/gtos_hydrate_test_data.py` reported *"nothing to hydrate — all paths already in the
sparse profile"* and *"hydrated: 159 path(s) present"*. Both failing files read one of them.
Filed as a repair row, with the reason this session did **not** simply hydrate them: CLAUDE.md §3's
2026-07-30 amendment establishes that R2 expects bytes for
`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` that match **no committed object** —
only the uncommitted working copy in the main repo — so hydrating it in a worktree would put the
wrong bytes at a path the runner's `binding_roots` fallback finds first. **Fix the sparse profile
and the hydrator's exit message; do not blanket-hydrate.**

> **The first version of this A/B was invalid and I nearly published it.** `zsh` does not
> word-split unquoted parameter expansions, so `for f in $FILES` iterated once with the whole
> list as one string and neither copy-back happened — both sides measured my own code and
> reported "identical failure sets", which is the answer I was hoping for. Caught because
> `git status` came back clean when it should have been mid-restore. Redone in Python. The real
> answer is the same, and a confounded control that agrees with the truth is still confounded.

## 3. New and changed tests

| file | tests |
|---|---|
| `tests/research_infra/test_ar_vol_level_tilt.py` | **+29**, new file. The default-path identity on the *sized output* across all four (kelly × overlays) combinations; the deployed-constants-equal-declared-constants agreement; the centre's provenance read from `regime_spine.dials` rather than grepped; monotonicity, the unit point, the clamp, off-sleeve and unusable-`vr` no-ops; **the shrink-survives-the-size-up-cap regression**; the cap invariant; the reason string; the whole launcher→bridge wiring without a broker; and that no committed config carries the key |

**Two of those 29 failed on first run and both were real defects, not test bugs** — see the result
doc §0 and §3.2. One would have stood the armed book down every tick with a healthy heartbeat.

## 4. Family-ratchet tests against `CANDIDATE_FAMILY_V4`

```
tests/research_infra/test_candidate_family.py
tests/research_infra/test_candidate_family_v2_ratchet.py
tests/research_infra/test_ao_candidate_family_v3.py
  -> 45 passed, 1 skipped
```

`test_candidate_family_v2_ratchet.py` discovers declarations by
`AUD.glob("phase*/receipts/CANDIDATE_FAMILY_V*.json")`, so V4 is picked up automatically — which
is the same glob AO §8.6 recorded as invisible to `pytest_failset.py scope`. It is listed here by
hand for the same reason.

## 5. The `admission.py` line-shift, and what was and was not remapped

`admission.py` grew **1,807 → 1,933 lines (+126)**. The 76-line VOL_LEVEL_TILT comment block was
moved to the END of the file to shrink the blast radius; the residual shift, by old line number:

| old line | shift | old line | shift |
|---:|---:|---:|---:|
| ≤ 862 | **0** | 1200–1320 | +40 |
| 900–1100 | +11 … +12 | 1400 | +41 |
| 1158–1170 | +22 | 1424–1500 | +46 … +49 |

`phase11/receipts/ar_remap_admission_citations.py` rewrote **68 citations in 24 live-code files**
(`src/`, `scripts/`, `tests/`, plus AR's own measurement artifacts). Every rewrite is built from
`difflib` **equal blocks only** and verified by **exact line-text identity**; one citation
(`core.py`'s `admission.py:1187-1198`) could not be verified and was **left stale on purpose**.
A sample re-check after the fact: 10/10, 6/7, 3/3, 1/1 citations point at byte-identical code to
what they pointed at before.

**Not remapped, deliberately:** committed receipts under `phase1..phase10` (other sessions' sealed
evidence — a citation there records what was true when that session measured it), and
`VOL_LEVEL_TILT_DECLARATION_V1.json` plus its writer (time-sealed at `592b5be95` in a commit with no
economics; rewriting a citation inside them changes the declaration's sha256 and destroys the only
thing that commit was for). Use the table above to read an older receipt's citation.

The remapper carries an **idempotency guard**: it reads a citation's current value as an old line
number, so a second pass would double-shift every one of them silently. The guard asks git whether a
file's citations already differ from its merge-base version and refuses.

## 6. One incidental observation, not AR's

The scoped run leaves **untracked runtime state** behind at
`pipeline_state/ultimate_book/probe/{day_anchor,high_water}.json` — a governor day-anchor written by
some test in the set that constructs a live engine against a real repo root. It is **not** AR's:
running `tests/research_infra/test_ar_vol_level_tilt.py` alone from a clean tree produces no
`pipeline_state` at all (checked). It also cannot be committed here — the path sits outside the
sparse-checkout definition, so `git add -A` refuses it, which is how it was noticed. Removed rather
than staged, per the engineering rule against staging runtime dirt. Recorded because a test that
writes into the repo root's `pipeline_state/` will keep tripping that in every worktree.

## 7. What the full suite is not

Per agreement §2.4 the full-suite A/B is the orchestrator's, once per merge train, diffed against
`receipts/FAILSET_BASELINE_MAIN.json`. This receipt is the scoped one.
