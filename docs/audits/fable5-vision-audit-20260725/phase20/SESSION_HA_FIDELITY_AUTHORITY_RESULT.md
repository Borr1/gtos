# Session HA — fidelity reference authority result

**Disposition: COMPLETE. The fidelity-authority defect is repaired. Activation authority is
`false`.**

## 1. Findings

1. **The same-lineage replay privilege escalation is closed.** Fidelity references now distinguish
   `same_lineage_replay`, `independent_replay`, `live_record`, and the ambiguous historical
   `replay_reference` value. Gate-spec v2 seals one of three current policies:
   `independent_or_live`, `replay_consistency`, or `live_record_only`
   (`src/research_infra/walkforward/fidelity.py:218-252`,
   `src/research_infra/walkforward/spec.py:420-471`). A same-lineage measurement can clear only an
   explicitly sealed replay-consistency gate; it cannot clear the current default
   `independent_or_live` gate.

2. **Caller-supplied aggregate counts no longer carry current gate authority.** The historical
   registrar remains available only to reproduce v1 receipts and stamps those records
   `caller_counts`. Every v2 policy refuses them with `fidelity_evidence_unstructured`
   (`fidelity.py:362-371`, `:1042-1098`). The new registrar accepts no numerator or denominator.
   It reads a content-bound v2 manifest, verifies the manifest and both referenced JSONL source
   hashes, refuses duplicate or incomplete identities, and computes:

   - recall numerator = `|reference identities ∩ generated identities|`;
   - recall denominator = `|reference identities|`;
   - generated-only count = `|generated identities - reference identities|` only when the
     manifest explicitly attests a complete generated population.

   The implementation is at `fidelity.py:802-1040`.

3. **Recall, precision, and null semantics are explicit in the verdict.** Gate-result v2 records
   measurement schema, evidence authority, reference kind, both lineage hashes, all three derived
   counts, recall, precision, and whether precision is supported. The gate also records the sealed
   reference policy and optional precision floor (`gate.py:108`, `:518-561`). When a policy carries
   a precision floor, null precision refuses with `fidelity_precision_unmeasured`; it is never
   imputed as a pass (`fidelity.py:409-420`). `fidelity_precision_floor=None` means the gate does
   not require precision, and that choice is itself visible and sealed.

4. **The CR historical result remains honest.** The committed CR v1 receipt is unchanged. It says
   its 249/249 comparison used a replay reference from the same code lineage and reports null
   precision. Its frozen result remains `NOT_EVALUABLE` because the recorded executable population
   is absent. Under gate-spec v2, that same v1 caller-count receipt additionally refuses at the
   fidelity boundary; no historical artifact was silently rewritten.

5. **The repair is research-only and default-off.** The new registrar is process-local and runs
   only when a research caller explicitly invokes it. No runtime, config, activation, broker, VPS,
   token, risk, or live-behavior file changed. No replay was launched. No March or live outcome was
   opened.

## 2. Sealed behavioral contract

| Gate policy | References that can pass | References that cannot pass |
|---|---|---|
| `independent_or_live` | `independent_replay`, `live_record` | `same_lineage_replay`, ambiguous v1 `replay_reference` |
| `replay_consistency` | `same_lineage_replay` | independent/live references and ambiguous v1 receipts |
| `live_record_only` | `live_record` | every replay reference |
| v1 historical compatibility | historical v1 semantics only | cannot be selected by a v2 spec |

Structured replay evidence must bind both generator lineages by SHA-256. A same-lineage manifest
requires equal hashes; an independent manifest requires different hashes. A live-record manifest
requires explicit recording authority. The reference and generated populations are separate
hash-bound JSONL sources, and every configured identity field must be present and scalar on every
row. Duplicate identities refuse rather than being silently collapsed.

## 3. Compatibility and schema boundary

- `gtos.walkforward.gate_spec.v2` is the current default. Reference policy and precision floor are
  included in `spec_sha256`.
- `gtos.walkforward.gate_result.v2` publishes the new authority and measurement fields.
- `gtos.walkforward.fidelity_evidence.v2` plus
  `gtos.walkforward.fidelity_measurement.v2` identify derived-count evidence.
- `gtos.walkforward.fidelity_measurement.caller_counts.v1` identifies historical direct receipts.
- `LEGACY_DEFAULT_SPEC` reconstructs gate-spec v1 explicitly. Its serializer omits the two fields
  that did not exist in v1, and its reader restores only `legacy_any_reference`; a v1 spec cannot
  carry a v2 policy or precision floor (`spec.py:545-675`). Published v1 seals remain pinned by the
  existing compatibility tests.
- The current `DEFAULT_SPEC` and A/B/C options are v2 with `independent_or_live`. No precision
  threshold was chosen in this commission because that threshold is an admission-standard/owner
  decision; the absence is now explicit rather than conflated with a passing precision result.

## 4. Adversarial proof and failure sets

### 4.1 Focused authority tests

```text
python3 -m pytest -q tests/research_infra/test_direct_fidelity_measurement.py
14 passed; 0 failed; 0 errored
```

The behavioral cases cover:

- same-lineage replay against `independent_or_live` — refused;
- altered caller counts over the unchanged source hash — both versions refused;
- nested structured-source hash drift — refused;
- missing v2 structured schema — refused;
- null precision with a sealed precision floor — refused;
- legitimate same-lineage replay consistency — fidelity gate passes;
- legitimate independent replay — fidelity gate passes;
- legitimate live-recorded measurement — fidelity gate passes;
- existing CR v1 receipt and final `NOT_EVALUABLE` disposition — preserved.

### 4.2 Clean parent A/B

Exact scope:

```text
tests/research_infra/test_direct_fidelity_measurement.py
tests/research_infra/test_walkforward_gate.py
tests/research_infra/test_fidelity_register_matches_receipt.py
tests/research_infra/test_fidelity_threshold_variant.py
tests/research_infra/test_gate_wipeout_signal.py
tests/research_infra/test_cr_ny_metals_capture.py
tests/research_infra/test_candidate_family.py
tests/research_infra/test_published_seals_pinned_by_value.py
```

Failure-set result:

| Revision | Passed | Failed | Errored | Bad set |
|---|---:|---:|---:|---|
| parent `ba3c18ddf268294813545501f84b635ccc0f25bb` | 154 | 0 | 0 | `{}` |
| repair `3cf33386558e8ae279296069d3a72137b07794c3` | 167 | 0 | 0 | `{}` |

Diff: **0 regressed, 0 unchanged-bad, 13 added passing cases.** Both captures used clean working
trees. The tool-emitted `gtos-ab-receipt-v1` fence is in
`phase20/receipts/SESSION_HA_AB_RECEIPT.md`; the raw captures are embedded there and also stored in
`phase20/receipts/session_ha_ab/`.

### 4.3 Relevant walk-forward/fidelity closure

The closure ran these exact test files:

```text
test_cm_armed_fidelity.py
test_cp_true_utc_recorded_gate.py
test_direct_fidelity_measurement.py
test_fidelity_register_matches_receipt.py
test_fidelity_threshold_variant.py
test_gate_filter_selector_evidence.py
test_gate_partial_universe_stamp.py
test_gate_wipeout_signal.py
test_learned_edge_walkforward_gate.py
test_walkforward_book_replay.py
test_walkforward_diversifier.py
test_walkforward_family.py
test_walkforward_gate.py
test_walkforward_supply.py
test_cr_ny_metals_capture.py
test_candidate_family.py
test_published_seals_pinned_by_value.py
```

Result: **289 passed; 0 failed; 0 errored.** Machine capture:
`phase20/receipts/SESSION_HA_WALKFORWARD_CLOSURE.json`.

The first pre-change attempt produced 26 failures, all in `test_walkforward_gate.py`. They were
classified before patching as one missing committed sparse fixture, not behavior:
`research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`. The exact committed
path was hydrated without rebuilding broker truth; its SHA-256 is
`bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd`. The clean parent capture
then passed 154/154. No test or threshold was weakened.

Additional checks:

```text
python3 -m py_compile src/research_infra/walkforward/{fidelity,spec,gate,options,__init__}.py
git diff --check
```

Both passed. `ruff` was not installed in this environment, so no ruff result is claimed.

## 5. Residual risks

1. A v2 manifest content-binds its lineage hashes and source populations, but code cannot prove
   organizational independence from hashes alone. The artifact author must still justify why two
   different lineage hashes represent an independent generator rather than a cosmetically changed
   fork. The gate now makes that claim explicit and reviewable instead of accepting an ambiguous
   replay label.
2. The authored K/Y live-record register remains code-authored authority rather than a newly
   materialized v2 identity manifest. It is not caller input and remains covered by its existing
   receipt-transcription tests. Migrating that historical register would be a separate evidence
   rematerialization, not a reason to reinterpret its receipts here.
3. Current A/B/C proposals disclose precision but set no precision floor. A future precision
   requirement must choose a threshold before outcomes are read; once set, null and below-floor
   precision fail closed.

## 6. Scope and activation statement

Implementation commit: `3cf33386558e8ae279296069d3a72137b07794c3`.

Changed implementation/test surface only:

- `src/research_infra/walkforward/{fidelity,gate,spec,options,__init__}.py`;
- `tests/research_infra/{test_direct_fidelity_measurement,test_walkforward_gate,test_candidate_family}.py`.

`activation_authority: false`. No activation permission was requested or created. No runtime,
configuration, account, broker, VPS, token, or live state was changed.
