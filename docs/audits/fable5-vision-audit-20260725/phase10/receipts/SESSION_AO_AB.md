# Session AO — the §2 scoped verification receipt

**Branch `phase10/regime-pooling`, merge-base `8db17b29c`, HEAD `657490012` at capture.**

## 0. The one fact that makes this A/B cheap

**AO changed nothing under `src/`.** Measured: `git diff --name-only 8db17b29c..HEAD -- src/` is
empty. The 13 changed paths are the result doc, six phase-10 receipts and artifacts, two
append-only ledgers, and three new test files. So no production behaviour can have moved, and the
A/B's only job is to show that the artifacts and ledger appends did not break a test that reads
them.

| | |
|---|---|
| bound decision-contract paths changed (H1) | **NONE** — checked against R2's 43 |
| `config/agent_config.yaml` blob | **`eddbe49a…` at the merge-base, at HEAD and in the working tree** — byte-identical, three ways |
| broker module imported by any AO receipt script | **none** — no `mt5`, `MetaTrader5`, `order_send`, `create_mt5` or `broker_authority` reference in any `ao_*.py` |
| H1 drift check | **2 UNHYDRATED-LFS, 0 DRIFTED** — per `CLAUDE.md` §3's 2026-07-30 amendment this is a property of local LFS hydration, not of any commit |

## 1. Blast radius, and where the tool under-reports it

`python3 scripts/pytest_failset.py scope --base 8db17b29c --include-worktree`:

```
diff 8db17b29c...WORKTREE: 13 path(s) changed
scoped to 5 test file(s) reached by import closure or path literal
```

**Three more files belong in scope and the tool cannot see them, because they reach AO's changes
through a `glob` rather than a path literal.** `test_candidate_family_v2_ratchet.py:32` is
`AUD.glob("phase*/receipts/CANDIDATE_FAMILY_V*.json")` — it discovers
`phase10/receipts/CANDIDATE_FAMILY_V3.json` and parametrizes over it, so the new declaration is
inside its assertions while the tool lists neither. `test_candidate_family.py` and
`test_fidelity_threshold_variant.py` were added for the same reason (they own the loader and the
registrar AO's members flow through). Added by hand; both sides run the same set.

**This is a defect in the scope tool, not in the tests**, and it will bite any session that adds a
file a glob-based test discovers. Recorded rather than worked around silently.

| scope | files |
|---|---|
| the tool's answer (6, after the block append) | `test_ak_receipt_drivers.py`, `test_ao_candidate_family_v3.py`, `test_ao_p_floor_headroom.py`, `test_ao_regime_dials_inside_substrate_cells.py`, `test_vig_trial_ledger_prospective.py`, `test_implementation_state_block_citations.py` |
| **added by hand** | `test_candidate_family_v2_ratchet.py`, `test_candidate_family.py`, `test_fidelity_threshold_variant.py` |

## 2. The A/B

Three of the nine files do not exist at the merge-base, so the comparable scope is the **six**
that exist on both sides.

| side | scope | result |
|---|---|---|
| **merge-base `8db17b29c`** (in-worktree, see §3) | the 6 shared files | **73 passed / 1 skipped / 0 failed / 0 errored** |
| **HEAD** | the same 6 files | **74 passed / 1 skipped / 0 failed / 0 errored** |
| **HEAD** | all 9 files | **102 passed / 1 skipped / 0 failed / 0 errored** |
| `pytest_failset.py diff` | mechanical | **unchanged 0, fixed 0, REGRESSED 0 — "No regressions"**, exit 0 |

**The +1 passing test on the shared scope is `test_a_successor_is_a_superset_of_what_it_supersedes`
parametrized over `CANDIDATE_FAMILY_V3.json`** — the generic ratchet guard AL shipped, working on
the first successor after it, discovered by its own glob. That is the guard doing its job, not a
new test of AO's.

**+28 new tests**: 14 in `test_ao_regime_dials_inside_substrate_cells.py`, 8 in
`test_ao_p_floor_headroom.py`, 7 in `test_ao_candidate_family_v3.py`, less the 1 skipped-by-design.
Reconciliation: 74 + 29 = 103 = 102 passed + 1 skipped.

## 2.1 One test failed on the first run after the blocks landed, and it was a repair announcing itself

`test_the_in_flight_wave_range_is_declared_and_shrinking` failed with
*"in-flight range B1300-B1349 is DEAD: it sits at or below the block ceiling (B1343) and exempts
nothing the ceiling does not already exempt. Drop it."*

That is agreement §2.3's case exactly, and it is the second consecutive session to trip it (AL §9
was the first). Writing B1300–B1343 raised the ceiling from B1241 to B1343, above AO's own range
floor, so AO's `IN_FLIGHT_WAVE_RANGES` entry stopped exempting anything. **Dropped**, with the
history in the docstring.

**And the same append made AO the owner of that list**, which is what
`WAVE_10_WORKING_AGREEMENT.md` §5 anticipates ("whoever raises the ceiling past a sibling owns
`IN_FLIGHT_WAVE_RANGES`"): B1343 is past AN's 1250–1299, so **AN's entry changed class from
PRE-DECLARATION to ACTIVE** rather than going away. Verified by running the test's own predicate:
AN's entry now exempts exactly `B1250`, the individual-token citation
`phase10/SESSION_AN_POPULATION_RULE.md` makes of a block AN has not written yet, while AO's would
exempt nothing. AN's entry therefore stays and is the one a future session should check first.

## 3. How the base side was produced, and what the capture cannot record

Agreement §4 warns that a fresh worktree at the merge-base is not a usable A/B for tests reading
sparse-checkout-excluded artifacts, and `research/operations/trial_budget/TRIAL_LEDGER.jsonl` is
exactly that. So the base side was built **in-worktree**:

1. every file the base side would disturb was copied to a scratchpad first —
   `phase10/receipts/` (whole tree), `REPAIR_QUEUE_APPEND.jsonl`, `TRIAL_LEDGER.jsonl`, and the
   three new test files;
2. the two ledgers were rewritten from `git show 8db17b29c:<path>`, `phase10/receipts/` was
   removed, and the three new test files were removed;
3. the base capture was taken;
4. **everything was restored by COPY-BACK from the scratchpad, never by `git checkout`** — AL §9's
   process note, which lost an uncommitted edit that way. Verified: `git status --short` is empty
   and `git diff --stat HEAD` is empty after the restore.

**What the receipt cannot record, stated because a reader would otherwise be misled:** both
captures carry the same `commit` field (`657490012`), and the base one carries `dirty: true`. The
discriminator is the reverted artifacts, which the tool has no field for. The comparison is 0 bad
→ 0 bad on identical scopes; the commit label is not the discriminator.

## 3.1 An operational note that cost three failed captures

`pytest_failset.py capture` reported `totals: {}` with `pytest_returncode=4` three times before it
worked. The cause is not the tool: **zsh does not word-split unquoted parameter expansions**, so
`capture -o out.json $FILES` passes the whole space-separated list as ONE argument, pytest treats it
as a single nonexistent path and exits 4 (usage error). The fix is `${=FILES}`, or listing the paths
literally.

Recorded because the tool behaved correctly and the shell did not: `diff` **refused** both empty
captures with *"executed NO tests … An empty failure set compares as a perfect one. Re-capture
it."* That refusal is the only reason a vacuous 0-bad-vs-0-bad A/B was not published, and it is
worth knowing that it works.

## 4. Trial ledger

`research/operations/trial_budget/TRIAL_LEDGER.jsonl` grew by AO's own look events. **Quote the
count as a floor, never as a total** — it grows with every re-run of a driver, and AO's drivers
were re-run five times as the power terms, the seed sweep and the band axis were added.

## 5. Repair queue

`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`: **110 → 121 rows**, 11 appended, session `AO`,
**0 AO duplicate (session, sleeve, prescription) triples**.

`ao_repair_rows.py` is idempotent by that triple and reports — rather than fails on — the **six
pre-existing duplicate triples** from AD, AI and AM. Its first version refused the whole run on
those, which was wrong twice: it would have failed on work that is not AO's, and the triple is not
a unique key in this ledger by design (AD legitimately files one prescription for one sleeve at
two accounts).

**The queue was restored to its exact pre-AO bytes before the final append**, verified row-by-row
against `git show HEAD:<path>` (110 rows, `keep == base_rows`), because the rows had been appended
once against an earlier artifact and their `evidence` blocks are read from the artifacts.

---

## Addendum — the embedded captures, regenerated at the train merge (orchestrator, 2026-07-30)

The session's scratchpad capture files were lost when its process was killed two minutes
after its final commit (see the recovery merge `cc64f8b55`). Per this guard's own remedy,
the same nine-file scope was re-captured at the MERGED tree and reproduces the session's
numbers exactly: **102 passed / 1 skipped / 0 failed / 0 errored**. The tool-emitted,
self-contained receipt for that re-capture follows verbatim.

# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `8db17b29c` | `6ff85e1ff` |
| captured (UTC) | 2026-07-30T04:21:13Z | 2026-07-30T11:29:47Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11454 | 102 |
| skipped | 112 | 1 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ak_receipt_drivers.py', 'tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_ao_p_floor_headroom.py', 'tests/research_infra/test_ao_regime_dials_inside_substrate_cells.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/test_implementation_state_block_citations.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_fidelity_threshold_variant.py']`

**Why this is still a comparison:** Before is the committed FULL-SUITE zero baseline at 8db17b29c (0 failed / 0 errored); after is Session AO's nine-file scope re-captured at the merged tree by the orchestrator, because AO's own scratchpad captures were lost when its process was killed two minutes after its final commit. A scoped zero against a full zero cannot hide a regression inside the scope, which is the only claim this receipt makes; the train-level full-suite A/B is WAVE10_TRAIN_AB.md.

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
  "commit": "8db17b29ca6b6b458509ae713169698733756748",
  "commit_subject": "Wave 10: commission AN (population rule + decidability wiring) and AO (regime conditioning + power-pool)",
  "captured_utc": "2026-07-30T04:21:13Z",
  "dirty": true,
  "totals": {
   "passed": 11454,
   "skipped": 112,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "6ff85e1ff30ccba05a0323d2f5daaf1218004593",
  "commit_subject": "Commission AS: the challenge books to the login step (B1500-B1549), on explicit owner approval",
  "captured_utc": "2026-07-30T11:29:47Z",
  "dirty": true,
  "totals": {
   "passed": 102,
   "skipped": 1
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
   "tests/research_infra/test_ao_candidate_family_v3.py",
   "tests/research_infra/test_ao_p_floor_headroom.py",
   "tests/research_infra/test_ao_regime_dials_inside_substrate_cells.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/research_infra/test_candidate_family_v2_ratchet.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_fidelity_threshold_variant.py"
  ],
  "justification": "Before is the committed FULL-SUITE zero baseline at 8db17b29c (0 failed / 0 errored); after is Session AO's nine-file scope re-captured at the merged tree by the orchestrator, because AO's own scratchpad captures were lost when its process was killed two minutes after its final commit. A scoped zero against a full zero cannot hide a regression inside the scope, which is the only claim this receipt makes; the train-level full-suite A/B is WAVE10_TRAIN_AB.md."
 }
}
```
