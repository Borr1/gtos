# Session HDA — independent fidelity-authority falsifier result

**Disposition: builder head `113b04891969213614d4635c1e609629c935f67c` is not safe as-is. The
repair is safe to integrate only with reviewer commit
`4f5c5d4286764b622cc0f539ac40887a2bbbd8b4`. `activation_authority: false`.**

## Findings

1. **HIGH — HA's replay/live provenance was label authority, not evidence authority.** The builder
   accepted two caller-chosen 64-hex strings as generator lineages. Relabelling same-lineage
   populations `independent_replay` and changing one string cleared the default
   `independent_or_live` policy. Relabelling the same rows `live_record` needed only a non-empty
   `capture_id`. This contradicts HA's claim that lineages were content-bound
   (`SESSION_HA_FIDELITY_AUTHORITY_RESULT.md:59-63`). Both attacks passed at `113b0489`.

   **Repair:** replay lineages now require path-and-SHA-256-bound `lineage_authority` artifacts;
   live references require a path-and-SHA-256-bound `recording_authority` artifact plus capture id
   (`fidelity.py:924-1042`). Code verifies the named bytes and their drift. It does not pretend that
   hashes prove organizational independence or broker-live origin.

2. **HIGH — the public authored register could mint arbitrary v2 authority.**
   `FIDELITY_REGISTER` was an exported mutable `dict`. Any caller could insert a frozen `Fidelity`
   object with `reference_kind=live_record`, `evidence_authority=authored_register`, and perfect
   counts, bypassing all registrars and the caller-count refusal. The builder's gate accepted it.

   **Repair:** the authored backing store is private and the public register is a live read-only
   mapping (`fidelity.py:739-755`). `Fidelity` itself was already frozen. No production consumer
   mutated the public mapping; the two tests that deliberately exercised the authored-overwrite
   guard now mutate the private backing only inside their fixtures.

3. **HIGH — an explicit v1 spec emitted a v2-branded gate result.** A historical caller-count
   record legitimately clears `LEGACY_DEFAULT_SPEC`, but HA's global gate-result schema was always
   `gtos.walkforward.gate_result.v2`. That let legacy semantics travel under a v2 top-level label,
   despite a nested v1 spec.

   **Repair:** result schema now follows spec schema. A v1 spec emits gate-result v1 and the exact
   historical fidelity field shape; a v2 spec emits the authority/precision fields in gate-result
   v2 (`gate.py:109-110`, `:142-190`, `:216-238`). Default and A/B/C option calls remain v2.

4. **MEDIUM — process-local registrars were order-dependent and could reveal shadow authority
   after a clear.** The direct registrars rejected collisions with temporary records, but the
   surface and threshold registrars did not reject direct-record collisions or duplicates. They
   silently wrote `_SURFACE_EXPANSIONS` while `fidelity_for` continued returning the earlier direct
   record. Clearing direct measurements then revealed the hidden transferred-class record. The
   same defect made duplicate registration last-write-wins and test-order dependent.

   **Repair:** all four public registrars share one non-shadowable slot check
   (`fidelity.py:772-790`, `:943`, `:1118`, `:1237`, `:1330`). Direct, structured, surface, and
   threshold registrations now reject authored, direct, temporary, and duplicate collisions before
   reading or writing evidence. Their separate clear functions can no longer reveal a shadow.

5. **MEDIUM — two path strings to one file counted as an independent comparison.** A reference
   path and a symlinked generated path to the same JSONL passed as separate populations when paired
   with different caller-chosen lineage strings.

   **Repair:** after both content hashes verify, their canonical resolved paths must differ
   (`fidelity.py:1043-1059`). Relative, absolute, and external evidence paths remain supported;
   repository containment is not claimed because GTOS evidence legitimately lives outside the
   repository.

6. **LOW — Python-only `NaN`/`Infinity` tokens became valid identities.** Python's JSON decoder
   accepts those non-standard constants by default. HA therefore admitted invalid JSON rows and
   canonicalized them into set identities.

   **Repair:** manifests and JSONL rows use strict constant rejection, and canonical identity
   serialization disallows non-finite values (`fidelity.py:853-860`, `:875-918`, `:945-951`).

These are integration blockers, not documentation nits. The exact builder-head failure set contains
seven node IDs because finding 1 has separate replay and live attacks. HA's 154-to-167 green A/B did
not contain these adversaries, so its empty failure sets did not establish safety.

## Reconstructed authority contract

Wave 19 CR remains the controlling historical example:

- `CR_GENERATOR_FIDELITY_V1.json` records 249 agreed, 0 reference-only, null generated-only,
  `precision_supported=false`, and `reference_kind=replay_reference`.
- Its caveat explicitly says the second artifact was emitted from the **same code lineage** and does
  not establish generator correctness (`CR_GENERATOR_FIDELITY_V1.json:10-24`).
- `CR_NY_METALS_CAPTURE_RESULT_V1.json` keeps that historical v1 measurement ready/pass at its own
  0.50 replay-consistency floor, but the frozen gate was not invoked and the overall disposition is
  `NOT_EVALUABLE` because no broad-V4 RECORDED executable population exists
  (`CR_NY_METALS_CAPTURE_RESULT_V1.json:208-217`).
- FG preserved exactly that split and still requires a source-bound broad-V4 RECORDED NY-metals
  executable population (`SESSION_FG_SOL_REPAIR_INTEGRATION_RESULT.md:93`).

The current boundary is therefore:

| Surface | What may authorize it | What cannot authorize it |
|---|---|---|
| gate-spec/result v1 | explicit historical reconstruction | no v2 authority claim |
| v2 `replay_consistency` | structured same-lineage identity comparison with hash-bound lineage artifacts | ambiguous v1 caller counts |
| v2 `independent_or_live` | structured independent replay or live-record comparison with hash-bound provenance artifacts | same-lineage evidence, ambiguous labels, caller counts |
| v2 `live_record_only` | structured live-record comparison with hash-bound recording artifact | every replay kind and caller counts |

The historical `register_direct_fidelity_measurement` API remains available because CR must reproduce
its committed v1 receipt. Its aggregate counts remain stamped `caller_counts`; every v2 GateSpec path,
including implicit `run_gate(..., spec=None)`, refuses it with
`fidelity_evidence_unstructured`. Direct calls to `Fidelity.refusal_reason()` retain their historical
legacy default only for receipt reconstruction; gate authority always supplies the sealed spec policy.

## Adversarial results

| Attack | Builder `113b0489` | Reviewer `4f5c5d4` |
|---|---|---|
| mutate public authored register with perfect live record | accepted mutation; v2-capable record | `TypeError`; unknown sleeve remains unmeasured |
| register v1 direct record, shadow with surface/threshold record, then clear | hidden record written; clear reveals it | collision refused before write |
| duplicate surface/threshold registration | last write wins | refused |
| relabel same-lineage evidence independent and alter free-form lineage hash | default policy passes | missing hash-bound lineage authority refuses |
| relabel evidence live with only a capture id | live policy passes | missing hash-bound recording authority refuses |
| drift lineage or recording authority bytes | no artifact existed to verify | hash mismatch refuses |
| use reference plus symlink alias as generated population | passes | same canonical population refuses |
| add nested caller counts to manifest | ignored; source-derived counts prevail | ignored; source-derived counts prevail |
| duplicate identity | refuses | refuses |
| scalar `1`, string `"1"`, and boolean `true` | distinct | distinct |
| missing/null/non-scalar identity field | refuses | refuses |
| blank lines and extra non-identity fields | ignored | ignored |
| malformed JSON | refuses | refuses |
| `NaN`/`Infinity` JSON constants | accepted | refuses |
| empty reference population | refuses | refuses |
| empty generated population | recall 0, never missing/pass | recall 0, never missing/pass |
| incomplete generated population | precision null | precision null |
| null precision, no sealed precision floor | disclosed, does not gate | disclosed, does not gate |
| null precision, sealed precision floor | refuses | refuses |
| manifest/population hash drift | refuses | refuses |
| relative and absolute paths | supported | supported |
| legacy spec write/read round trip | seal preserved | seal preserved |
| v1 spec gate-result wrapper | incorrectly v2 | v1 with legacy shape |
| implicit/default and A/B/C option specs | v2 `independent_or_live` | unchanged v2 `independent_or_live` |

Recall and precision denominators were recomputed independently with reference `{a,b,c}` and
generated `{a,x,y}`: agreed 1, reference-only 2, generated-only 2, recall 1/3, precision 1/3. A
second mixed-type case proved nested manifest counts cannot move the derived values.

## Compatibility and minimality decisions

- No new policy enum, evidence schema, gate-spec field, threshold, or general security framework was
  added. The builder's v2 contract was tightened before integration by reusing its existing
  `source_path`/`source_sha256` evidence primitive for lineage and recording authority.
- No committed non-test `gtos.walkforward.fidelity_evidence.v2` manifest exists, so requiring
  `lineage_authority`/hash-bound `recording_authority` does not invalidate published v2 evidence.
- The public authored register remains lookup/iteration compatible. Only mutation was removed.
- Surface and threshold structural transfers remain available. They accept no receipt path or
  caller count, and a v1 record cannot collide with, overwrite, or later reveal one.
- `gtos.walkforward.gate_spec.v1` still omits the two v2 fidelity fields when serialized and restores
  `legacy_any_reference` only when read. A v1 schema with a v2 policy or precision floor still
  refuses; a v2 schema with the legacy policy still refuses.
- Published pre-field legacy seal
  `4910f6ac46025bd676cd96860a57b699c17c60a4d4ecd5361bf228125693668e` remains pinned.
  CR's frozen v1 spec seal remains
  `5503fc704285427a3f82bcef58e5296b4bb212ac263098c80d5a98046cbee8f0`.
- CR historical files are byte-identical at source commit `47139bc3`, FG close
  `ba3c18ddf`, builder `113b0489`, and reviewer `4f5c5d4`:
  - generator receipt file SHA-256:
    `1e8451ad400b699835fd627048877094b2f1ffb4b71769806943ba0b346b2c4c`;
  - result receipt file SHA-256:
    `f5015f8c1f56058d6ab84bb8d9a69acf58b59579738002fac58255711d6a6b24`.

The production repair touches only `fidelity.py` and `gate.py`. Test changes update the builder's
new structured-manifest fixtures, prove the register is read-only, and add the HDA adversarial
module. No option or current research call was disabled merely to make the authority tests pass.

## Failure-set A/B

Tool-emitted receipt:
`phase20/receipts/session_hda_ab/SESSION_HDA_AB_RECEIPT.md`.

Exact equal path scope:

```text
tests/research_infra/test_hda_fidelity_authority_falsifier.py
tests/research_infra/test_direct_fidelity_measurement.py
tests/research_infra/test_walkforward_gate.py
tests/research_infra/test_candidate_family.py
tests/research_infra/test_fidelity_threshold_variant.py
tests/research_infra/test_walkforward_family.py
tests/research_infra/test_walkforward_supply.py
tests/research_infra/test_fidelity_register_matches_receipt.py
```

| Revision | Failed | Errored | Failure set |
|---|---:|---:|---|
| builder `113b04891969213614d4635c1e609629c935f67c` | 7 | 0 | seven HDA authority node IDs |
| repair `4f5c5d4286764b622cc0f539ac40887a2bbbd8b4` | 0 | 0 | empty |

Failure-set diff: **7 fixed, 0 unchanged bad, 0 regressed**. The raw pass totals were 216 and 227,
but they are not the regression claim. Both captures were dirty only for the HDA test/TODO/receipt
artifacts; implementation bytes correspond exactly to the named commits.

## Independent closure

Focused HDA adversaries:

```text
python3 -m pytest -q tests/research_infra/test_hda_fidelity_authority_falsifier.py -p no:cacheprovider
21 passed, 0 failed, 0 errored
```

Independently selected import/literal closure: 25 walk-forward, fidelity, gate, family, partition,
published-seal, diagnostics, and exit-parity files; **515 passed, 18 skipped, 0 failed, 0 errored**.
The exact file list is recorded in `SESSION_HDA_COMPLETE.json`.

Mutation-sensitive files ran in two opposite orders, each in a fresh Python process:

```text
direct -> family -> threshold -> HDA: 60 passed
HDA -> threshold -> family -> direct: 60 passed
```

CR compatibility ran independently:

```text
python3 -m pytest -q tests/research_infra/test_cr_ny_metals_capture.py \
  tests/research_infra/test_direct_fidelity_measurement.py::test_cr_v1_same_lineage_receipt_stays_historical_and_not_evaluable \
  -p no:cacheprovider
6 passed, 0 failed, 0 errored
```

The first broad closure attempt exposed one committed sparse bridge and later one committed partition
registry. Only those exact paths were hydrated:

- `run_selected_package_replay_bridge.py`, SHA-256
  `2ed740e9102ee35183cd7594e2cef7610a1c0767396c9cea5cf58452fdb6748a`;
- `ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl`, SHA-256
  `cbd28933f17998e0b5b61e82d8726cc7b6424cad5abcc86ec1db21e9292e1c07`.

One candidate closure file,
`tests/research_infra/test_moonshot_unified_execution_scorer.py`, was excluded after direct builder
inspection proved its collection error pre-existed this review: builder HEAD's
`moonshot_expanded_market_leakage_reduction.py` has no `aggregate_reduction_rows` export. That test is
unrelated to fidelity and no source or test was weakened to absorb it.

Required checks:

```text
python3 -m py_compile src/research_infra/walkforward/{fidelity,spec,gate,options,__init__}.py
git diff --check
```

Both pass. `ruff` is not installed; no ruff result is claimed.

## Residual risks

1. A hash-bound lineage artifact proves identity and drift of named bytes, not organizational
   independence. An independent-replay claim still requires a reviewer to inspect why the two
   artifacts represent independent generators rather than cosmetically different forks.
2. A hash-bound recording artifact proves the named capture receipt did not drift, not that the
   capture was broker-live. Source provenance remains a human/evidence-chain claim.
3. `generated.population_complete=true` is sealed in the manifest but completeness cannot be
   inferred from the JSONL alone. Precision claims require review of the generator/capture contract.
   `false` always yields null precision; a sealed precision floor then fails closed.
4. Authored K/Y and structural-class-transfer records remain code-authored historical authority.
   They are no longer publicly mutable and cannot be shadowed by caller-count records, but
   rematerializing them as v2 identity manifests would be a separate evidence programme.

## Scope, commits, and activation boundary

Reviewed commits:

- `ba3c18ddf268294813545501f84b635ccc0f25bb` — Wave 19 FG close / HA base;
- `3cf33386558e8ae279296069d3a72137b07794c3` — HA implementation;
- `113b04891969213614d4635c1e609629c935f67c` — HA builder closeout and required HDA start.

Created implementation commit:

- `4f5c5d4286764b622cc0f539ac40887a2bbbd8b4` — closes the seven authority failures.

This result and its completion receipt are committed separately as audit evidence; the containing
closeout commit is reported in the final handoff because a commit cannot include its own hash.

`activation_authority: false`. No merge or push was performed. No runtime, config, account, broker,
VPS, token, risk, production, or live-trading surface changed. No broad replay ran. March and live
outcomes were not read. No evidence was deleted.
