# Session AW — scoped A/B against the parent commit

`CLAUDE.md` §6: no "no regressions" claim without an A/B. Copy-back, never `git checkout`
(wave-11 §2), and every restored file sha256-verified.

## Base

`bec961504` — *"AV's A/B receipt made self-contained at the train — the guard's remedy, same as
AO's"*, the tip of `phase12/separability-mine` when this session started.

**Not `main`.** `main` moved two commits ahead during the session (`2def2bdf1` fx_jpy pulled from
both live books; `30f031e64` de-arm source claims found structurally rather than by line number).
Scoping against `main` pulls in `tests/ultimate_book/test_book_sleeve_telemetry.py`, which fails
at this branch's tip on a line-number assertion — a **pre-existing** failure that `30f031e64`
already fixes on `main` and that this session neither caused nor touches (`book_owner.py` is
unmodified here). Basing the A/B on the branch's own parent is what makes the comparison mean
anything; the merge train picks up `30f031e64` on its own.

## Scope

`python3 scripts/pytest_failset.py scope --base HEAD --include-worktree` — 21 paths changed,
**4 test files** reached by import closure or path literal:

```
tests/research_infra/test_ak_receipt_drivers.py
tests/research_infra/test_b7_5_diagnostic_pool.py        <- new this session
tests/research_infra/test_vig_trial_ledger_prospective.py
tests/test_implementation_state_block_citations.py
```

The new file does not exist on the before side, so the A/B is over the **3 shared files** and the
new one is counted separately — the same treatment AQ's and AV's receipts gave the same
situation, and the reason `pytest_failset diff` refuses a mismatched scope.

## What changed

**No production file was modified.** Every source change is an addition, plus three append-only
or guard-mechanism edits:

| path | status |
|---|---|
| `src/research_infra/b7_5_diagnostic_pool.py` | new |
| `tests/research_infra/test_b7_5_diagnostic_pool.py` | new (16 tests) |
| `docs/.../phase12/receipts/aw_separability_mine.py`, `aw_archive_gate.py` | new |
| `docs/.../phase12/receipts/AW_*.json`, `CANDIDATE_FAMILY_V{7,8,9}.json` | new |
| `docs/.../phase12/SESSION_AW_SEPARABILITY_MINE_RESULT.md`, `receipts/SESSION_AW_AB.md` | new |
| `docs/.../IMPLEMENTATION_STATE.md` | **appended** — B1750–B1785 |
| `docs/.../phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` | **appended** — 220 → 224 rows |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | **appended** — 36 rows (AW-3 gate) |
| `tests/test_implementation_state_block_citations.py` | **guard repair** — see below |

`research/operations/broker_truth_layer_2026_07_29/` was added to this worktree's **sparse
checkout** so `BROKER_TRUE_COSTS_V1_1.json` resolves. That is a working-tree materialisation of
an already-tracked, unmodified blob — no content change, and `git status` shows none.

### The guard repair, because it is the one edit to a shipped test

Writing B1750–B1785 raised the block ceiling past B1670 and two shipped assertions fired
immediately — which is the mechanism working, not breaking. `WAVE_11_WORKING_AGREEMENT.md` §4
says whoever raises the ceiling past a sibling owns `IN_FLIGHT_WAVE_RANGES`, so both were AW's
to fix:

1. **`B1670` became a dangling citation.** AV wrote `**B1668–B1670 — receipts.**` — one paragraph
   covering a run of three ids — and the parser recognised only `B1668`. Repaired by teaching
   `_defined_blocks` the run form, which is the **third** instance of the class this file already
   documents twice ("the blocks ARE written, so teach the parser the shape rather than rewrite
   the prose" — the bold form for Session P, the `B274/B275` form for Session R). Two restrictions
   are load-bearing and both are pinned by a new test: **bold form only** (`## B1750–B1799` is a
   section heading announcing an allocation; expanding the sixteen such headings would define
   ~700 ids nobody wrote) and **the dash must be set close** (`**B215 — B200's conclusion…**` is
   prose about an earlier block and descends). Verified against the file: the tight bold form
   matches exactly five runs, all genuine.
2. **AW's own `(1750, 1799)` entry became DEAD** — at or below the ceiling while exempting
   nothing the ceiling does not already exempt. Retired by its own author, the same retirement
   AL's and AO's entries received, with the reason recorded inline. Its unwritten tail
   B1786–B1799 is cited nowhere as an individual token and `B1750–B1799` is a range declaration
   whose upper bound `_RANGE` already excuses.

### Copy-back

| file | sha256 @ `bec961504` | sha256 @ AW |
|---|---|---|
| `test_implementation_state_block_citations.py` | `5fa21a13e44312eb…` | `75a80b1f30effae44c667f75415f3eff66f25d04c188cb86a5b7dc78848cc0e6` |
| `IMPLEMENTATION_STATE.md` | (base) | `8840c4bf647f3e599a7a3efdf0b49760a51040a57fdeec5409b3183a6bb0f8e0` |
| `REPAIR_QUEUE_APPEND.jsonl` | (base) | `2b145a02dd2da883242ba9287a21fdd57c1f00888d876e258f2d131a8b16c039` |
| `TRIAL_LEDGER.jsonl` | `a54f86c0f7be5ce306300bd74f34c521377a8b33d3ee67e1cbc308b7e3247111` | `01977118214d0ff53fc760114cfe1e24e10cb6513ffcea5f40d05e4605bf1b58` |

Base bytes copied in, suite run, my bytes copied back, all four re-hashed and confirmed identical
to the pre-A/B values.

## The comparison

```
before bec961504: 0 bad
after  bec961504: 0 bad
unchanged: 0   fixed: 0   REGRESSED: 0

No regressions.
```

Shared scope: **25 passing before → 26 after** (the +1 is the new test pinning the run-form
expansion). Full scope including the new file: **42 passed, 0 failed, 0 errored.**

## H1 — decision-contract drift

Checked at session start and at session end with CLAUDE.md §3's own snippet:

```
UNHYDRATED-LFS: …/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl
UNHYDRATED-LFS: …/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl
total flagged: 2
```

**2 at start, 2 at end, both UNHYDRATED-LFS, zero DRIFTED.** No R2-bound path was written. The
January and April ledgers this session reads are evidence OUTPUTS, not bound inputs, and they
were opened read-only through the route's own cold reader in the worktree that produced them
(H4). Neither of the two LFS-bound ledger paths in the main repo was touched (B905). No sealed
window was run; March was not read.

---

## Addendum — embedded captures, regenerated at the train merge (orchestrator, 2026-07-30)

Per the self-containment guard, same remedy as AO and AV.

# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `30f031e64` | `afb67587e` |
| captured (UTC) | 2026-07-30T15:37:52Z | 2026-07-30T16:17:08Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11843 | 70 |
| skipped | 121 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ak_receipt_drivers.py', 'tests/research_infra/test_b7_5_diagnostic_pool.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/test_implementation_state_block_citations.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py']`

**Why this is still a comparison:** Before is the committed FULL-SUITE zero baseline; after is Session AW's five-file scope re-captured at the merged tree by the orchestrator (the session's receipt predates the tool fence; a first capture attempt returned pytest rc=4 with zero tests and the tool refused it — correctly — so this is the verified second capture, 70 passed). A scoped zero against a full zero cannot hide an in-scope regression; the train-level A/B is WAVE12B_TRAIN_AB.md.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "30f031e640443feefa2233ff0a5fa75813976bc2",
  "commit_subject": "De-arm source claims found structurally, not by line number \u2014 the train collision CLAUDE.md \u00a76 warns about",
  "captured_utc": "2026-07-30T15:37:52Z",
  "dirty": true,
  "totals": {
   "passed": 11843,
   "skipped": 121,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "afb67587ece2964e6b44118bab016eb60d011900",
  "commit_subject": "AW's receipt made self-contained (third of the class) \u2014 and the agreement now mandates the tool fence",
  "captured_utc": "2026-07-30T16:17:08Z",
  "dirty": true,
  "totals": {
   "passed": 70
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/"
  ],
  "after": [
   "tests/research_infra/test_ak_receipt_drivers.py",
   "tests/research_infra/test_b7_5_diagnostic_pool.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py"
  ],
  "justification": "Before is the committed FULL-SUITE zero baseline; after is Session AW's five-file scope re-captured at the merged tree by the orchestrator (the session's receipt predates the tool fence; a first capture attempt returned pytest rc=4 with zero tests and the tool refused it \u2014 correctly \u2014 so this is the verified second capture, 70 passed). A scoped zero against a full zero cannot hide an in-scope regression; the train-level A/B is WAVE12B_TRAIN_AB.md."
 }
}
```
