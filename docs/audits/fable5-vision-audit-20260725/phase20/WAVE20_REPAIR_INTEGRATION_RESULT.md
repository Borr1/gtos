# Wave 20 repair integration — findings and exact failure-set proof

Session HI integrated the four exact reviewed authorities on branch
`phase20/repair-integration`. This is an offline research-infrastructure result. It generated no
scientific outcome and confers no promotion, runtime, broker, family-kill or activation authority.

## Findings

1. **The four exact reviewer heads are integrated with full ancestry and no repair omitted.** HDA,
   HDE, HDF and HG are second parents of four explicit merge commits. Their required builder,
   reviewer-implementation and reviewer-closeout histories remain ancestors. No unsafe builder
   predecessor was integrated in isolation.

2. **HDA fidelity authority and HDF capture authority compose as one strict current-v2 contract.**
   `gtos.walkforward.gate_spec.v2` retains source-bound fidelity provenance, anti-forgery,
   lineage/path/symlink boundaries, finite identity checks and the deeply immutable capture
   declaration. A current read requires the exact schema and a valid lowercase full seal. Historical
   `gate_spec.v1` bytes remain reconstructible only with explicit `allow_legacy=True`; v1 cannot
   carry current fidelity or capture authority, and a capture-bearing payload cannot silently
   downgrade. Genuinely absent capture fields remain absent from canonical bytes rather than moving
   unrelated pre-capability seals.

3. **HDF's seven additional repairs remain mechanically visible after composition.** The identical
   final adversarial source, SHA-256
   `b81803818d0bf0de823f3861d80811ac525da5066775fb1fbf429fa35913d4e3`, produces 10 passed and seven
   exact failures against HDC `32d045a732467e439ba1807db0ce786e8a11e53b`, then 17 passed against
   the integrated source. Those seven nodes cover deep capture immutability, current schema/seal
   enforcement, exact-date refusal, exact-tail tie retention and terminal-observation state repair.
   HDA/HDF fresh-process tests also pass 40/40 in both orders, so registrar/schema state leakage is
   not hiding the union.

4. **The scientific identities required by the commission are unchanged.** CR remains historical
   `NOT_EVALUABLE`: 249/249 same-lineage agreement, null generated-only/precision values, no
   independent evidence and no RECORDED executable population. CS remains a 59-member-family
   `ADMIT` under the independently rebuilt capture-start null, raw p `0.0009765625`, BH q
   `0.0576171875`, status `RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED`; the current composed
   authority seal is `736872fe5ec2c4b83d4c808dc3720d9be18548654a5f9f43375bed24d85a62b7`.
   FC retains all 40 historical rejections, all 214 time-box outcomes, 3,200 fast/reference
   comparisons and projection hash
   `d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d`.

5. **HDE's minimal cost authority is intact.** Finite authority-backed spread, commission, slippage
   and swap components are summed left-to-right. Missing/nonfinite authority fails closed. The
   unsupported redundant `broker_net_pretrade_cost_packet` alias remains removed and no redundant
   telemetry was resurrected. FD's accepted artifact remains 30,707 bytes at SHA-256
   `c9c8516ffbf084f386c8db9e7a13a00bf13155fa45198284d5722a3a88453f30`, with 17,716 physical and
   3,555 scoreable rows; no ledger replay or new economic decode ran.

6. **Both sealed baseline failures are repaired at their exact causes.** The FG verifier now removes
   only the exact-join ledger from its stale expected-drift list after that hydrated file matches its
   R2 seal; all hash checks and the two genuine inherited drifts remain. The streaming-archive test
   now patches a module-local clock/sleep proxy instead of shared stdlib `time.sleep`; production
   publication behavior and timing semantics are untouched. The exact nodes pass together, their
   modules pass 38/38, and monitoring/archive order checks pass 42 with 12 skips in each order.

7. **The first integrated full suite exposed two bounded issues, and both were repaired without
   weakening behavior.** HG's unnamespaced zero-branch label looked like a nonexistent implementation-state
   evidence block; the branch labels are now namespaced `HG_B0`/`HG_B1`, leaving the preregistered
   route unchanged. The sleeve-registry fixture had reverted to its 131-byte LFS pointer during
   source merging; hydrating only its exact committed 205,754-byte object at SHA-256
   `a5bcc0f81941a123d75f390e2cd7abca625de584033aad8e34d3e7898588b54e` restored the permissions
   fixture with no tracked source change. The two exact nodes then pass, their owning modules pass
   106/106, and the unchanged full-suite command is green.

8. **The exact suite-wide failure-set A/B is 2 bad to 0 bad, with zero regressions.** The sealed
   baseline has 12,974 collected, 12,809 passed and the two commissioned bad node IDs. The final
   source has 13,228 collected, 13,065 passed, 131 skipped, 32 xfailed and zero failed/error nodes.
   Collection rose by 254 because reviewer tests were added; that is classified separately from the
   failure set. Both baseline node IDs are fixed and no new node ID regressed.

## Source and merge ledger

| Lane | Exact reviewed source head | Required reviewer implementation | Explicit merge commit |
|---|---|---|---|
| HDA fidelity authority | `9894fa0c72f68af587d4a04004de44f7076b9416` | `4f5c5d4286764b622cc0f539ac40887a2bbbd8b4` | `e323cbebaf92687b42960c4baa1d6e3704b5613f` |
| HDE cost minimality | `52ede5eabcb5d09d8ceb6e12d878f7bd0442e5ad` | `cf70fd7e36eaaab8d5d04e04db8c85a7685b0a83` | `4bc9e296e112133aca58187c5ce03fa7044a541b` |
| HDF exit/capture science | `da2514dc6c9ceee16ed85f01b314ace973d50980` | `14c0e2ad1c4390ba78412832179d9b1e1dbf16f2` | `35a923241c355d5da4337a2542491d7675519076` |
| HG science preregistration | `b7e4e8a29349244ea675c492a6fdb8cffdb94563` | same single source commit | `bc288834bffb6118ef09c99a44bb49e5407bc5d7` |

The Git-derived ancestry and receipt hashes are in
`phase20/receipts/HI_SOURCE_COMMIT_LEDGER.json`. The pre-merge prediction was committed before any
source merge as `3c0a0bfef5c232beb112108f70591f2bc910128e`.

## Conflict resolutions

The only Git content conflict was `src/research_infra/walkforward/spec.py`. It was resolved manually
as the v2 fidelity/capture union described above. Three auto-merged overlaps received semantic
review rather than byte-level acceptance:

- `src/research_infra/walkforward/gate.py` retains both fidelity authority enforcement and sealed
  capture/fold/null enforcement.
- `tests/research_infra/test_candidate_family.py` retains legacy seal pins and current composed-seal
  capability checks without moving the 59-member family.
- `tests/research_infra/test_walkforward_gate.py` retains both adversarial surfaces and explicit
  legacy/current boundaries.

HDF's `folds.py`, `stats.py`, exit evaluator and FC/CS receipt implementations were non-overlapping
reviewed authority and remain intact. HDE's train-engine implementation was non-overlapping and
remains minimal. HG had no source overlap. Every path, discarded item and verification surface is
recorded in `phase20/receipts/HI_CONFLICT_RESOLUTION_LEDGER.json`.

## Scoped integration commits

- `3c0a0bfef5c232beb112108f70591f2bc910128e` — preintegration conflict map and Git-derived source
  ledger.
- `e323cbebaf92687b42960c4baa1d6e3704b5613f` — explicit HDA merge.
- `4bc9e296e112133aca58187c5ce03fa7044a541b` — explicit HDE merge.
- `35a923241c355d5da4337a2542491d7675519076` — explicit HDF merge and manual semantic composition.
- `bc288834bffb6118ef09c99a44bb49e5407bc5d7` — explicit HG merge.
- `69c092e2839e0ace8a334be7dcea78cc083907d3` — the two sealed baseline repairs.
- `4ad0dba35ff28bd1d9597f88a01d191cb967db08` — HDF comparator import isolation.
- `7c494e73a5504615ff6ca917926760cf17697cff` — composed current-v2 seal and explicit-legacy pins.
- `6b72de84d27e10563da102237be46e5a0180c7d6` — HG branch-label namespace repair exposed by the
  first full suite. This is the exact source head tested by the final full suite.
- The containing commit for this result, machine receipts, root-cause map and session-register
  update is the closeout commit authority; a file cannot contain the hash of the commit that first
  contains itself.

## Verification

### Reviewer and semantic closures

| Surface | Result |
|---|---:|
| HDA independently selected fidelity/walk-forward closure | 557 passed, 1 skipped |
| HDE adversarial matrix | 124 passed |
| HDE equal-scope train-engine closure | 355 passed |
| HDE extended broker-cost closure | 46 passed |
| HDE focused closure | 166 passed |
| HDF exit/walk-forward/FC/CS closure | 168 passed |
| CR historical identity closure | 6 passed |
| Tool-derived 38-file changed-test union | 978 passed, 1 skipped, zero bad |

All HDA, HDE and HDF adversarial nodes and their independently selected closures are represented.
Syntax compilation of every changed Python file passed. Every HI JSON receipt parsed. The
`git diff --check` guard passed.

### Exact full-suite A/B

Both sides use Python 3.14.4, pytest 9.1.0, `PYTHONDONTWRITEBYTECODE=1`, and the identical 388-rule
sparse profile SHA-256
`8b19788683e6ed07682b5562260bd41478f50775ebf173e50038d8b5531f7b5b`.

Command:

```text
/usr/bin/time -l env PYTHONDONTWRITEBYTECODE=1 pytest -q tests/ --junitxml=/private/tmp/wave20_integration_full.xml
```

| Metric | Sealed baseline | Final integrated source |
|---|---:|---:|
| Source head | `cf46792ee4823175c67eed30329cf93ba1a95a7d` | `6b72de84d27e10563da102237be46e5a0180c7d6` |
| Collected | 12,974 | 13,228 |
| Passed | 12,809 | 13,065 |
| Failed | 2 | 0 |
| Errors | 0 | 0 |
| Skipped | 131 | 131 |
| Xfailed | 32 | 32 |
| Warnings | 72 | 72 |
| Wall seconds | 1,462.17 | 1,409.50 |
| Maximum RSS bytes | 1,175,552,000 | 1,185,857,536 |
| JUnit bytes | 1,979,133 | 2,022,765 |
| JUnit SHA-256 | `65b9cddf5483be0d1e9fb90899d765a1eb9dc1da9fcffd1b888eb92b00d9b3d7` | `7b03e130c7b17c859d300943a744ffdc5da93c691155e54d68ce5ff156e30c7d` |

Baseline bad node IDs, both fixed:

- `tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries`
- `tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment`

Final bad node IDs: `[]`. Regressed node IDs: `[]`.

The final JUnit was copied without overwrite to
`/Users/borr/GTOSColdEvidence/wave20-preservation-20260801/wave20_integration_full_source_6b72de84d.xml`.
Its copied bytes and hash match `/private/tmp/wave20_integration_full.xml`. The tool-emitted,
self-contained failure-set receipt is `phase20/receipts/SESSION_HI_AB_RECEIPT.md`; the detailed
machine proof is `phase20/receipts/HI_INTEGRATED_VERIFICATION.json`.

## Boundaries and residual risks

- No result-bearing replay or preregistered science node ran. March 2026 and live-forward outcomes
  were not read; February's attribution-only role did not change.
- No runtime/config/activation byte changed. No broker, VPS, token, credential, order, trade, push or
  main-branch surface was touched.
- No family member, observation, opportunity, cost, denominator or candidate was removed or
  suppressed.
- A pointer-only sparse checkout can reproduce the sleeve-registry permissions failure. Future
  exact-suite runs must hydrate that committed LFS object and classify absence as fixture
  materialization, not policy regression.
- HG's preregistration receipt binds the root-cause map and session register at the control-head
  identity. HI deliberately updates the current copies; readers must use the commit identity named
  by each receipt rather than treating a path-only hash as timeless.
- CS remains dossier-required and not armed. CR remains `NOT_EVALUABLE` pending genuinely
  independent or live-recorded executable evidence.

`activation_authority: false`
