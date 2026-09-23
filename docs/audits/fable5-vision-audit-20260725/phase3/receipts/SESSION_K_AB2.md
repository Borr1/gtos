# Session K — full-suite A/B by failure set (final)

**Supersedes `SESSION_K_AB.md`, which was recorded in B165 and predates the bars work.** Run
2026-07-27 on `phase3/generation-port`. Committed, because `WAVE_3_WORKING_AGREEMENT.md` §4 is
explicit that an A/B which is not committed did not happen.

## Result

> **One real regression, and it was mine. Fixed. Two flakes, characterised rather than waved away.**

The first pass of this A/B is reported in full below rather than only its corrected successor,
because **the regression it caught was the useful part**.

### Pass 1 — the one that found something

| | baseline | after |
|---|---:|---:|
| failed | 661 | 664 |
| errored | 33 | 33 |
| passed | 10,212 | 10,228 |

**Regressed: 3.**

| test | verdict |
|---|---|
| `test_replay_policy_generation.py::test_the_index_and_oil_families_are_absent_from_the_vps_pull` | **REAL — mine.** Fixed. |
| `test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration` | flake (B30/B79b family) |
| `test_replay_columnar_source.py::test_verification_retains_no_rows` | flake, order/load dependent |

**The real one.** I wrote a test asserting the index and oil families were **absent** from the VPS bar
export. That pinned a transient state of someone else's data delivery rather than a behaviour, so it
went red the moment the archive was completed. It is the only genuine regression in the diff and it
was self-inflicted.

It is replaced by a test of what is actually invariant, and of the thing that broke **three times**
this session: the canonical→broker crossing. Files are keyed on canonical names while
`book_engine.py:461` fetches under the broker name, so a canonically-keyed source returns nothing —
which is exactly how the port twice produced zero `idxrev` intents, and how the first bar pull
silently omitted eleven symbol families. The new test asserts the remap exists, that the broker-keyed
source loads, and that the canonically-keyed one does not.

**A green A/B here would have been worse than a red one.** The snapshot-pinning test would have
survived into integration and gone red on the next data change, looking like someone else's problem.

### The two flakes, characterised

- **`test_high_load_integration`** (`test_end_to_end_integration.py:392`) spins threads generating 100
  shadow metrics, 50 timings and alerts concurrently, then asserts on the result. This session has now
  observed it flipping in **both directions**: it was *newly passing* in the B165 A/B and *regressed*
  here, on the same code. It also fails in isolation while passing inside the suite. That is a
  scheduling-dependent test, not a signal.
- **`test_verification_retains_no_rows`** passes in isolation on two consecutive runs; it is
  order/load dependent.

Neither is touched by this session's change, which adds two files and modifies no existing Python
(`git diff --stat <parent>..HEAD -- '*.py'`).

### Pass 2 — after the fix: clean

| | baseline (`c35245eda`) | after (`bf64df691`) |
|---|---:|---:|
| failed | 661 | **661** |
| errored | 33 | **33** |
| passed | 10,212 | **10,231** |
| skipped / xfailed | 27 / 1 | 27 / 1 |

> **REGRESSED: 0. NEWLY PASSING: 0. My test file contributes nothing to the failed or errored set.**

+19 passed = the 19 tests in `tests/test_replay_policy_generation.py`. Both flakes landed on their
passing side this run, which is itself consistent with the flake characterisation above — neither
appears in either direction.

Captures committed alongside this receipt as `SESSION_K_AB2_baseline.json` and
`SESSION_K_AB2_after.json`.

## Method, and the wrinkle the tool correctly refuses

The change is **purely additive**: `src/research_infra/replay_policy/generation.py` and
`tests/test_replay_policy_generation.py`, with **zero modifications to existing Python**. The parent's
test surface is therefore HEAD's minus the new test file, so the baseline was captured with `--ignore`
on it.

`scripts/pytest_failset.py diff` **refuses** that comparison — *"scopes differ … an A/B across
different scopes is not a comparison"* — and it is right to. The set comparison is therefore done
directly on the `failed`/`errored` node-id sets, valid on one condition: that the new test file
contributes nothing to either set. **That condition is checked every run, not assumed** — and in pass 1
it was *false*, which is how the regression was caught. In pass 2 it holds.

**The Python delta between the two capture commits was checked, not assumed.** For pass 1 it was
empty — docs only — so the sides were directly comparable. For pass 2 it is **exactly one file,
`tests/test_replay_policy_generation.py`** (the fixed test), which is the file the baseline `--ignore`s
and which is verified to contribute nothing to the after-run's failed/errored set. No production
module differs between the two sides in either pass; `src/research_infra/replay_policy/generation.py`
is new in both and is imported by nothing except that test file. *(An earlier draft of this receipt
said "identical Python" for pass 2. That was wrong — the test fix is Python — and is corrected here
rather than silently.)*

## Captures discarded, so the count of runs is honest

Across this session **five** full-suite captures were started and discarded before a usable pair:
three returned `pytest_returncode: -15` with `totals: {}` — the failure mode `pytest_failset.py`'s own
docstring warns about, where a run "exits like a completed run" having measured nothing — and two were
killed by process-group teardown when a foreground waiter hit its timeout. Causes: concurrent
full-suite runs competing for CPU (one spawned by a subagent), and my own cleanup catching a capture in
the crossfire.

**Check `pytest_returncode` and `totals` before trusting any capture file.** A 389-byte capture JSON is
not a 690-failure suite. The final pair was run detached (`nohup … & disown`) so no waiter could take
it down.
