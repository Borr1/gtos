# Session HIA — independent Wave 20 repair-integration falsification

## Findings, ordered by severity

1. **HIGH — integrated head `7728701d7` was unsafe as-is.** Its structured-fidelity path hashed
   a manifest or population and then reopened the pathname for parsing. A replacement between those
   operations could make unverified bytes inherit the verified digest. It also compared canonical
   path strings, so two hard-link paths to one inode could masquerade as independent populations.
   Repair `2e62847b5` reads, hashes and parses one byte snapshot from one open file description and
   binds population identity by `(st_dev, st_ino)`. The identical 29-node adversarial source moves
   from **26 passed / 3 failed** at `7728701d7` to **29 passed / 0 failed** after the repair.

2. **MEDIUM — the first green HIA full suite was not sufficient closeout evidence.** At targeted
   evidence head `e7fe31fad`, all 13,234 collected cases were green/non-bad, but exact JUnit set
   algebra found two sealed-baseline node IDs missing. HDA had replaced those historical names with
   stronger current-v2 tests. That is better behavior but violates G0's explicit requirement that
   every baseline identity remain collected. Commit `5b2fe3020` restores both exact names as
   meaningful behavioral pins without changing production code. Its narrow module is 16/16 green;
   the replacement full suite collects 13,236 unique IDs and contains every baseline and HI ID.

3. **PASS — the exact final suite failure-set comparison is 2 bad to 0 bad with zero regressions.**
   Both sealed control failures pass, the final failed/error sets are empty, all 12,974 control IDs
   remain present, and all 13,228 HI IDs remain present. The 262 nodes added relative to control are
   classified separately below; raw pass-count growth is not used as non-regression proof.

4. **PASS — the reviewed HDA/HDE/HDF composition and historical identities survive HIA.** HIA-V1's
   same-source HDF comparator remains 10 passed / 7 failed at HDC and 17 passed / 0 failed current;
   CR, CS, FC and FD identities remain exact; HDE remains the finite authority-backed four-component
   cost closure; and HG's critical path remains minimal and non-cycling.

## Verdict

**`SAFE_ONLY_WITH_HIA_COMMITS`.** `7728701d7` is not safe as the parent of result-bearing work.
The source/test chain that passed final verification is:

```text
7728701d7c5fcb9911d04ec536436bb2261b0250  HI closeout; unsafe TOCTOU behavior
  -> 8f69b3a5af30ff84e1d16a28bf7ce3dc11294075  HIA plan freeze
  -> 2e62847b57097c35f899334b0ac7ef0268eaa09c  fidelity snapshot/inode repair
  -> e7fe31fad93ec60a61fc66fb09a6187e93aaaaa5  targeted HIA evidence
  -> 5b2fe3020211eb7456dcd747de20dfcb1d85806d  baseline-node identity repair; final tested source
  -> containing scoped HIA evidence closeout commit
```

The containing commit is the HIA closeout authority and is reported by Git history and the terminal
handoff; a file cannot contain the hash of the commit that first contains itself. The exact source
parent for the next offline science commission is
`5b2fe3020211eb7456dcd747de20dfcb1d85806d`.

- `activation_authority: false`
- `execution_authority: false`
- `science_executed: false`

## Why the TOCTOU repair is required

At the unsafe head, hash verification and parsing were two pathname reads. A pathname is mutable:
another file can be renamed over it after the first read. The verified hash then says something true
about the first file while the parser consumes the second. Canonical path comparison has a related
blind spot: two hard-link names resolve to different strings but identify the same underlying file.

The repair in `src/research_infra/walkforward/fidelity.py:829-1103` does three bounded things:

- `_verified_source_bytes` opens once, captures `fstat`, reads one byte snapshot, checks that
  snapshot's SHA-256, and returns those exact bytes plus device/inode identity (`:829-851`);
- manifest JSON and population JSONL parse only the returned snapshots, never a reopened path
  (`:886-952`, `:955-980`); and
- reference/generated populations are refused when either canonical paths or opened-file identities
  match (`:1076-1103`).

No threshold, candidate, denominator, cost, capture rule, gate disposition or default-on surface
changed. The repaired source is 71,814 bytes at SHA-256
`fe50bbfa6c6b5a766aaf18ab328c6aacd678f92775ea842400c910d13012c2ba`.

### Same-test failure-set A/B

The exact test source is 23,395 bytes at SHA-256
`1efae61bac69090643cc8308a83ecae5921feb9f212782849f414735ba059f67` on both sides.

| Side | Passed | Failed | Errors |
|---|---:|---:|---:|
| unsafe `7728701d7` | 26 | 3 | 0 |
| repaired `2e62847b5` | 29 | 0 | 0 |

Fixed IDs:

- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_independent_sources_cannot_be_hard_links_to_one_population`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_manifest_path_replacement_cannot_change_the_bytes_parsed`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_population_path_replacement_cannot_change_hash_bound_counts`

Regressed IDs: `[]`.

## HDF comparator preserved

The identical HDF adversarial source remains 29,401 bytes at SHA-256
`b81803818d0bf0de823f3861d80811ac525da5066775fb1fbf429fa35913d4e3`.
Against HDC `32d045a73` it produces 10 passed and these seven failures; current produces 17 passed,
zero failed/errors:

- deep capture-authority immutability;
- two invalid/missing seal variants and exact-schema refusal;
- exact-date alias refusal;
- exact-tail tie retention; and
- terminal trigger/partial/ratchet completion.

The exact IDs and JUnit hashes are machine-bound in
`receipts/HIA_INDEPENDENT_VERIFICATION.json`. Regressed IDs: `[]`.

## Exact full suite and identity repair

Both full runs used Python 3.14.4, pytest 9.1.0, `PYTHONDONTWRITEBYTECODE=1`, and the same 388-rule
sparse profile at SHA-256
`8b19788683e6ed07682b5562260bd41478f50775ebf173e50038d8b5531f7b5b`.

### First HIA run — retained diagnostic, not final authority

```text
/usr/bin/time -l env PYTHONDONTWRITEBYTECODE=1 pytest -q tests/ --junitxml=/private/tmp/wave20_hia_full.xml
```

- source: `e7fe31fad93ec60a61fc66fb09a6187e93aaaaa5`;
- 13,234 collected; 13,071 passed; 131 skipped; 32 xfailed; 0 failed/errors;
- pytest 1,389.85 s; wall 1,392.18 s; maximum RSS 1,114,587,136 bytes;
- JUnit 2,025,054 bytes, SHA-256
  `ed1327108c13765fdd7e62b4d55025e9e43d08c15b425f952f5409ce47569bd2`;
- durable path:
  `/Users/borr/GTOSColdEvidence/wave20-preservation-20260801/wave20_hia_full_source_e7fe31fad93ec60a61fc66fb09a6187e93aaaaa5.xml`.

The run was green but failed the independent identity gate because these baseline IDs were absent:

- `tests/research_infra/test_direct_fidelity_measurement.py::test_direct_replay_measurement_clears_floor_without_claiming_live_recall`
- `tests/research_infra/test_direct_fidelity_measurement.py::test_gate_serializes_replay_reference_without_populating_live_recall`

The first restored assertion was initially too strong: it expected a legacy compatibility property
to be null. The preserved failed narrow proof is 15 passed / 1 failed. After pinning the real
boundary—the legacy ceiling stamp does not claim live recall, and current v2 refuses caller-count
authority—the affected module is 16/16 green. Commit `5b2fe3020` changes only that test file.

### Final HIA run — authoritative

```text
/usr/bin/time -l env PYTHONDONTWRITEBYTECODE=1 pytest -q tests/ --junitxml=/private/tmp/wave20_hia_full_v2.xml
```

- source: `5b2fe3020211eb7456dcd747de20dfcb1d85806d`;
- 13,236 collected; 13,073 passed; 131 skipped; 32 xfailed; 0 xpassed; 0 failed/errors;
- 72 warnings; pytest 1,388.11 s; JUnit suite time 1,383.197 s;
- wall 1,390.36 s; maximum RSS 1,054,277,632 bytes; peak memory footprint 858,179,192 bytes;
- JUnit 2,025,392 bytes, SHA-256
  `9c85cf52a663029a8ac6f21fbf9dbd3d731afd716a5ed6087485adca05b9345b`;
- durable path:
  `/Users/borr/GTOSColdEvidence/wave20-preservation-20260801/wave20_hia_full_source_5b2fe3020211eb7456dcd747de20dfcb1d85806d.xml`.

### Failure-set algebra

| Property | Sealed control | Final HIA |
|---|---:|---:|
| Unique node IDs | 12,974 | 13,236 |
| Passed | 12,809 | 13,073 |
| Failed | 2 | 0 |
| Errors | 0 | 0 |
| Skipped | 131 | 131 |
| Xfailed | 32 | 32 |

Baseline nodes missing from final: `[]`. HI nodes missing from final: `[]`.

Fixed control IDs:

- `tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries`
- `tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment`

Current failed IDs: `[]`. Current error IDs: `[]`. Regressed IDs: `[]`.

The self-contained tool output is `receipts/SESSION_HIA_AB_RECEIPT.md` and contains exactly one
`gtos-ab-receipt-v1` fenced payload.

## Added tests — separate from failure-set proof

The final JUnit adds 262 exact node identities relative to control. Their sorted compact-JSON list
hash is `103b41e8be2613bbf883f67a310835c1ff715eb58571b94599be4be07cf016f8`.
Every node is passing:

| Lane | New IDs | Exact identity-list SHA-256 | Final state |
|---|---:|---|---|
| HDA | 33 | `6ea605edb134598f0d6981a15ec9a84ed226aec370acf02b92fe965ad36370d9` | all pass |
| HDE | 150 | `25995a260f461a643dad7384c2bb5387ed60df59668931db4bb3cb20354766cb` | all pass |
| HDF | 73 | `1dbeded38c8d174679102dde3190d0f7584d0b90ac5dca7deccf9cef58d4ce14` | all pass |
| HIA | 6 | `85834ee4b610cf47422e5147a2544794b9abd2198f3e4ec3195e64baef399060` | all pass |

HIA additionally restored the two baseline identities above; their list hash is
`fb0a86c72d48786314ac3f6a0c30e4fb2b29855037e1cd73876bf684e07c01db`.
Per-file counts, exact HIA IDs and the hash method are machine-recorded in
`receipts/HIA_INDEPENDENT_VERIFICATION.json`.

## Historical identities preserved

- **CR:** `NOT_EVALUABLE`; 249/249 same-lineage agreement; generated-only and precision remain
  null; no independent evidence; gate not invoked.
- **CS:** `RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED`; family 59; raw p `0.0009765625`; BH q
  `0.0576171875`; composed gate-spec SHA-256
  `736872fe5ec2c4b83d4c808dc3720d9be18548654a5f9f43375bed24d85a62b7`.
- **FC:** all 40 cells remain rejected; 214 time-box identities remain exact (100 January, 114
  February attribution-only); 3,200 fast/reference comparisons; economics projection SHA-256
  `d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d`.
- **FD:** `REPRODUCTION_AND_BIAS.json` remains 30,707 bytes at SHA-256
  `c9c8516ffbf084f386c8db9e7a13a00bf13155fa45198284d5722a3a88453f30`, with 17,716 physical and
  3,555 scoreable rows. No raw ledger was replayed.

These are HIA-V1 targeted reproductions bound by
`receipts/HIA_TARGETED_VERIFICATION.json`; HIA-V2 did not spend or reopen science outcomes to repeat
them.

## Critical-path minimality

The preregistered route remains:

```text
fixed breaker -> K1 applicability if learned outputs are consumed -> P1
candidate-specific P1 stop only -> O1 -> N1 -> FC2
shared source/route/infrastructure stop -> halt, no candidate cycling
```

Exactly one breaker branch is selected. Calibration cannot run unless learned outputs are consumed.
No candidate, fixture, denominator or opportunity may be suppressed to obtain a verdict. HIA ran no
node in this science DAG.

## Fixture and resource truth

- exact join ledger: 5,995,223 bytes, SHA-256
  `64fd10148a1b656a31fd3687354d3e5df9cab396101ec9816b5d85d6f7a09870`;
- sleeve registry: 205,754 bytes, SHA-256
  `a5bcc0f81941a123d75f390e2cd7abca625de584033aad8e34d3e7898588b54e`;
- neither fixture was hydrated or changed by HIA-V2;
- the older R2 registry expectation `19365f60...` remains recorded drift and was not substituted;
- free disk was 24,694,252 KiB before the first full run, 25,348,312 KiB before the final run and
  25,289,212 KiB after it, always above the 8 GiB floor;
- no pytest, replay or science worker competed with either full run.

## Boundaries and residual risks

- No result-bearing replay, science node, calibration, paper shadow or canary ran. March 2026 and
  live-forward outcomes were not read; February remained attribution-only.
- No broker, VPS, MetaTrader, runtime, config, token, credential, order, trade, merge or push surface
  was contacted.
- The sleeve registry remains an exact LFS hydration dependency. A 131-byte pointer checkout can
  reproduce the permissions failure; that is missing fixture materialization, not policy evidence.
- The older R2 registry hash drift remains inherited and explicit.
- The suite retains 72 warnings, including `asyncio_mode` configuration and future-invalid escape
  debt. They are not failed/error nodes and were not suppressed.
- CS remains dossier-required and not armed. CR remains `NOT_EVALUABLE` pending genuinely independent
  or live-recorded executable evidence.
- This package opens only the already-preregistered offline next commission. It creates no promotion,
  execution or activation authority.
