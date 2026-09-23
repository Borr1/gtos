# Session AV — scoped A/B against the parent commit

`CLAUDE.md` §6: no "no regressions" claim without an A/B. Copy-back, never `git checkout`
(wave-11 §2), and every restored file sha256-verified.

## Scope

`python3 scripts/pytest_failset.py scope --base f6b51dd07 --include-worktree` — **9 test files**
reached by import closure or path literal:

```
tests/research_infra/test_ak_receipt_drivers.py
tests/research_infra/test_ar_vol_level_tilt.py
tests/research_infra/test_av_metalabel_leakfree.py      <- new this session
tests/research_infra/test_av_timebase_per_file.py       <- new this session
tests/research_infra/test_regime_spine_conditions.py
tests/research_infra/test_vig_trial_ledger_prospective.py
tests/test_broker_clock_truth.py
tests/test_implementation_state_block_citations.py
tests/test_replay_policy_generation.py
```

The two new files do not exist on the before side, so the A/B is over the **7 shared files**
and the new ones are counted separately — the same treatment AQ's receipt gave the same
situation, and the reason `pytest_failset diff` refuses a mismatched scope.

## The comparison

Two production files were edited: `src/utils/research_timebase.py` and
`src/research_infra/replay_policy/generation.py`. Both are **unbound by the R2 decision
contract** (H1 membership checked at session start; drift 2 UNHYDRATED-LFS at start and at
end, unchanged).

| | sha256 |
|---|---|
| `research_timebase.py` @ `f6b51dd07` | `b0932c62ac53…` |
| `research_timebase.py` @ AV | `3c319b7a250a…` |
| `generation.py` @ `f6b51dd07` | `02b63031b1b7…` |
| `generation.py` @ AV | `6b1983cb2ae8…` |
| `test_implementation_state_block_citations.py` @ AV | `ded6d3d7e81e…` |
| `IMPLEMENTATION_STATE.md` @ AV | `f390b4875e6c…` |

Base bytes copied in, suite run, my bytes copied back, all re-hashed and confirmed identical
to the pre-A/B values.

Four files were restored to their base bytes for the before side —
`src/utils/research_timebase.py`, `src/research_infra/replay_policy/generation.py`,
`tests/test_implementation_state_block_citations.py` and
`docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — because the last two are
what the block-citation guard reads, and comparing my `IN_FLIGHT_WAVE_RANGES` edit against my
own block section would have been an A/B against itself.

| side | failed | errored | passed |
|---|---:|---:|---:|
| **before** (`f6b51dd07` bytes) | 0 | 0 | **140** |
| **after** (AV bytes) | 0 | 0 | **140** |

```
unchanged: 0   fixed: 0   REGRESSED: 0
No regressions.
```

## New tests

**+36 net new passing**, counted by running each file:

| file | tests |
|---|---:|
| `test_av_timebase_per_file.py` | 26 |
| `test_av_metalabel_leakfree.py` | 10 |

Full scoped run including the new files: **176 passed / 0 failed / 0 errored**.

The full-suite A/B is the orchestrator's, once per merge train (wave-11 §2).

## What the new tests pin, and why those properties

* **The clock probe recovers the clock it was given**, for all three hypotheses, on synthetic
  files whose basis is known by construction — a positive control, without which a refusal
  means nothing.
* **The probe never contradicts the control archive.** `data/historical_2026/` is FTMO
  broker-local by an independent exchange-anchor measurement; the per-file probe is allowed to
  under-claim on it and is not allowed to claim a different clock. That is the only failure
  direction F7 cannot tolerate.
* **`CsvBarSource` does not double-correct a `true_utc` sidecar** — the regression for the
  interop defect this session found.
* **No trade is scored by a meta-label model that saw its own outcome**, asserted against the
  entry/exit times of every row rather than by inspecting the fitting code.
* **A perfect feature is learned and a useless one is not** — the positive and negative
  control for the model machinery, without which its AUC of 0.523 could be a broken fitter
  rather than an absent signal.
* **The five implemented cuts are exactly the five declared family members** — a cut
  implemented but not declared is an uncharged look; a cut declared but not implemented is a
  bill nobody paid.

---

## Addendum — the embedded captures, regenerated at the train merge (orchestrator, 2026-07-30)

Per the self-containment guard's own remedy: the same nine-file scope re-captured at the
MERGED tree, tool-emitted block below, scope difference justified in-receipt.

# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `f6b51dd07` | `b706a87c2` |
| captured (UTC) | 2026-07-30T13:37:27Z | 2026-07-30T14:53:57Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11688 | 176 |
| skipped | 121 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ak_receipt_drivers.py', 'tests/research_infra/test_ar_vol_level_tilt.py', 'tests/research_infra/test_av_metalabel_leakfree.py', 'tests/research_infra/test_av_timebase_per_file.py', 'tests/research_infra/test_regime_spine_conditions.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/test_broker_clock_truth.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_policy_generation.py']`

**Why this is still a comparison:** Before is the committed FULL-SUITE zero baseline; after is Session AV's nine-file scope re-captured at the merged tree by the orchestrator, because AV's committed receipt predates the tool fence. A scoped zero against a full zero cannot hide a regression inside the scope; the train-level full-suite A/B is WAVE12_TRAIN_AB.md.

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
  "commit": "f6b51dd07cada007bb236c84e846f95c1b1fdcb0",
  "commit_subject": "Wave 12: commission AU (contract wiring + estate restamp B1550-B1599) and AV (the sample engine B1600-B1649)",
  "captured_utc": "2026-07-30T13:37:27Z",
  "dirty": true,
  "totals": {
   "passed": 11688,
   "skipped": 121,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "b706a87c2480c6dd3ef8e422be0a5c650f7f330c",
  "commit_subject": "Merge Session AV: the sample engine \u2014 fx_jpy measured negative at its own live contract, the triplication found, and width is exhausted on 29 of 30 families",
  "captured_utc": "2026-07-30T14:53:57Z",
  "dirty": true,
  "totals": {
   "passed": 176
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
   "tests/research_infra/test_ar_vol_level_tilt.py",
   "tests/research_infra/test_av_metalabel_leakfree.py",
   "tests/research_infra/test_av_timebase_per_file.py",
   "tests/research_infra/test_regime_spine_conditions.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/test_broker_clock_truth.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_policy_generation.py"
  ],
  "justification": "Before is the committed FULL-SUITE zero baseline; after is Session AV's nine-file scope re-captured at the merged tree by the orchestrator, because AV's committed receipt predates the tool fence. A scoped zero against a full zero cannot hide a regression inside the scope; the train-level full-suite A/B is WAVE12_TRAIN_AB.md."
 }
}
```
