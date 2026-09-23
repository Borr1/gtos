# Session HDE — cost-authority minimality result

## Verdict

**HDB is behaviorally safe but is not the smallest coherent implementation. It is safe to integrate
only with HDE implementation commit
`cf70fd7e36eaaab8d5d04e04db8c85a7685b0a83`.** HDE preserves every HDB authority closure and the
accepted FD bytes/numbers while removing 214 physical runtime lines and two physical test lines.
The HDB runtime delta over HB falls from +537 net lines to +323; the delta over Wave 19 falls from
+1,022 to +808.

HDB's principal excess was not another cost engine. It was 18 parallel detail fields representing
the same state and refusal information, duplicated arithmetic, repeated serialization, a dead packet
alias, and a helper that existed only to concatenate those parallel lists. HDE retains one strict
numeric boundary, one four-component classifier, one witness extractor, one exact-order sum, one
conflict accumulator, and one state publisher. The train-only economic and authority contract is
unchanged.

`activation_authority: false`

## Findings, ordered by consequence

### HDE-1 — HDB's authority behavior is sound; its minimality claim is not

The unchanged HDB head passed all commissioned scopes before editing: 124 adversarial, 355
equal-scope closure, 46 extended broker-cost, and 166 focused tests. The repair correctly requires
strict non-boolean finite non-negative numbers, independent witnesses for all four components,
duplicate reconciliation, exact rebase evidence, the narrow current 0.12 binding, and fail-closed
downstream authorization.

However, HDB materialized the classifier's internal partition into 12 row fields and six packet
fields. Current-tree search found no runtime consumer for any of them. Most encoded the same fact
already present in `cost_decision_refusal_reasons`; the packet variants also duplicated
`commission_r_repair_total_redecode_missing_fields` and the packet's canonical decision fields.
HDE stops emitting them and explicitly purges stale copies on normalization or packet repair, so an
old detail field cannot masquerade as current authority.

### HDE-2 — Repeated mechanics were removable without weakening a refusal path

HDE removed:

- a second implementation of the four-term arithmetic in packet repair;
- a thirteen-entry packet-to-row rename map whose eleven identity mappings were already handled by
  `REPAIR_PROVENANCE_FIELDS`;
- repeated state/refusal publication after a complete assessment;
- repeated 0.12 parsing/comparison blocks;
- repeated conflict-list mutation at three reconciliation points;
- `_cost_missing_inputs`, which only concatenated classifier category lists; and
- the inherited `broker_net_pretrade_cost_packet` key alias, for which exact current-tree search
  found no producer, fixture, or consumer. The real
  `pretrade_broker_net_cost_packet` and `pretrade_cost_packet` paths remain.

The invalid-recorded-total branch removed from the late authorization block was unreachable: an
invalid present total is already recorded as a conflict by `_recorded_cost`, publishes `refused`, and
returns through `_refuse_cost` before that branch. Its adversarial cases remain in the matrix and pass.

### HDE-3 — One canonical reason surface is clearer and at least as fail-closed

The classifier now returns only `state`, `candidate_sum_r`, `missing_inputs`, and
`refusal_reasons`. Component type and witness failures retain their precise identities, for example
`invalid_component:spread_r`, `non_finite_authority:commission_r_capture_value`, and
`inconsistent_component:cost_r_vs_expected_cost_r`. The implementation no longer serializes the
same identities again into type-specific arrays.

The state precedence remains `refused` on contradiction, otherwise `incomplete` on any missing or
invalid input, otherwise `complete`. Both non-complete states publish
`authoritative_cost_r: null`; the downstream accessor re-normalizes and accepts only a current valid
`authoritative_cost_r`. Stale V2 state, authorization, detailed diagnostics, or derived totals are
discarded and recomputed.

### HDE-4 — The 826-line falsifier is large but not safely reducible by case deletion

The HDB falsifier remains exactly 826 physical lines and still collects 124 cases from 34 test
functions and 17 parameterization declarations. No test function or parameterization declaration
changed. Repeated non-authority assertions were moved into `_assert_not_authoritative`; the freed
space was used to pin removal of stale retired row and packet fields. The file changed by +64/-64,
not by dropping a case or weakening a failure identity.

## Minimum coherent state machine

1. **Extract and reconcile.** Accept the two evidenced packet keys. Refuse malformed packet
   containers, unequal duplicate packets, `cost_r` versus `expected_cost_r`, top-level versus nested
   components, flattened versus nested witnesses, and all duplicate measured-commission locations
   when they disagree.
2. **Classify four components.** In the historical order—spread, expected slippage, swap,
   commission—require a non-boolean `numbers.Real`, finite and non-negative value. Require a matching
   independent captured value and allowed source for each. Commission additionally requires exact
   inclusion and agreement with broker-true measured commission. Legitimate captured zero remains
   valid.
3. **Choose state.** A contradiction is `refused`; otherwise any absent, null, invalid, non-finite,
   negative, or unauthorized input is `incomplete`; otherwise the row is `complete`. Compute a
   candidate sum only when all four numeric components are valid, using exact historical
   left-to-right addition.
4. **Reconcile the recorded total.** Exact equality authorizes. A mismatch authorizes only when the
   exact geometry marker/original/effective/optional-positive-multiplier equations hold, or when the
   exact current unresolved-commission 0.12 repair binding holds. Otherwise refuse both claims.
5. **Publish once.** Publish the three-state value, one authorization status, one canonical reason
   list, the diagnostic candidate sum, the reconciled witness map, and—only for a complete row—the
   authoritative cost. Purge all stale derived state first.
6. **Repair packets idempotently.** Validate strict measured and charged commission, equality, and
   the trusted repair source; rebuild the commission witness; call the same classifier and sum; write
   a total only when complete; preserve the first pre-repair total with `setdefault`. A second repair
   produces the tested byte-identical packet.

## Helper trace

Every helper added by HB/HDB was traced; the HDE helpers that replace duplication are included for
completeness.

| Helper | Decision |
|---|---|
| `_is_blank` | Retained. Distinguishes missing/null/blank evidence without coercion across extraction paths. |
| `cost_number` | Retained public helper. Shared by row classification, totals, conflicts, rebase, downstream accessor, and packet repair; closes boolean/string/container/non-finite/negative attacks. |
| `assess_cost_components` | Retained public pure classifier. Shared by row normalization and packet repair; it is the single four-component authority decision. |
| `_canonical_spread_source` | Retained. Reconciles the one historical producer label with its corrected allowed-source identity; source conflicts otherwise refuse. |
| `cost_component_capture_evidence_from_packet` | Retained public extractor. Shared by packet repair and normalization; required for nested/flattened/twice-normalized witness identity. |
| `_cost_values_conflict` | Retained. Applies the strict parser and existing `1e-8 R` tolerance to duplicate numeric claims. |
| `_capture_evidence_conflicts` | Retained. Refuses flattened versus nested value/source/status/inclusion conflicts. |
| `_mappings_equal` | Retained. Compares duplicate packet aliases and fails closed when mapping equality is exceptional or non-boolean. |
| `_recorded_cost` | Retained. Reconciles `cost_r` and `expected_cost_r`, including invalid totals. |
| `_cost_inputs` | Retained. Centralizes packet/container/component/witness/measured-source reconciliation; each branch has an adversarial case. |
| `publish_cost_assessment` | Retained public publisher, reduced to canonical state/auth/reasons plus stale-detail purge. Shared by row and packet paths. |
| `_cost_missing_inputs` | **Removed.** It merely joined nine classifier arrays; the classifier now returns canonical `missing_inputs`. |
| `_refuse_cost` | Retained. Clears authority and preserves established capture/accounting compatibility statuses for every non-complete exit. |
| `_geometry_rebase_valid` | Retained. Pins exact `True`, original/component equality, effective/recorded equality, and optional positive multiplier arithmetic. |
| `cost_component_sum` | Added by HDE. One pure strict four-term historical-order implementation shared by classification and packet repair. |
| `_is_legacy_fallback` | Added by HDE. One exact finite non-negative 0.12 predicate replaces three repeated comparisons. |
| `_add_cost_conflicts` | Added by HDE. One canonical deduplicating transition to `refused` replaces three hand-built mutations. |

Existing public `normalize_evidence_row` remains the train projection entrypoint and
`authoritative_cost_value` remains the downstream fail-closed accessor; HDE did not add another
framework, class, registry, validator surface, or schema.

## Output-field trace

### HDB fields retained

| Field | Consumer or adversarial obligation |
|---|---|
| `cost_component_state` | Canonical `complete`/`incomplete`/`refused` state pinned throughout Wave 19/HDB tests. |
| `cost_component_candidate_sum_r` | Keeps the four-term claim visible when the recorded total conflicts, without granting it authority. |
| `cost_component_capture_evidence` | Carries independent witnesses through flattening and is required for second-normalization identity. |
| `cost_decision_authorization_status` | Explicit current authorization/refusal label; stale values are recomputed. |
| `cost_decision_refusal_reasons` | Sole precise failure-identity surface used by the adversarial and Wave 19 tests. |

### HDB fields retired and purged

| Fields | Why removal is safe |
|---|---|
| `cost_component_commission_delta_r` | No consumer; measured/component mismatch is already tolerance-checked and named in the canonical reasons. |
| `cost_component_absent_fields`, `cost_component_null_fields`, `cost_component_invalid_fields`, `cost_component_non_finite_fields`, `cost_component_negative_fields` | No runtime consumer; each identity remains in canonical reasons and the combined missing-input compatibility field. |
| `cost_component_authority_missing_fields`, `cost_component_authority_invalid_fields`, `cost_component_authority_non_finite_fields`, `cost_component_authority_negative_fields` | No runtime consumer; witness failures remain precisely named in canonical reasons/missing inputs. |
| `cost_component_inconsistent_fields` | No runtime consumer; every conflict remains `inconsistent_component:<identity>` in canonical reasons. |
| `cost_component_refusal_reasons` | Exact duplicate of `cost_decision_refusal_reasons`. |
| `commission_r_repair_total_redecode_invalid_fields`, `commission_r_repair_total_redecode_non_finite_fields`, `commission_r_repair_total_redecode_negative_fields`, `commission_r_repair_total_redecode_authority_missing_fields`, `commission_r_repair_total_redecode_inconsistent_fields`, `commission_r_repair_total_redecode_refusal_reasons` | No runtime consumer; packet state/reasons and `commission_r_repair_total_redecode_missing_fields` retain the decision and repairability information. |

The retired names remain only in `_RETIRED_COST_DETAIL_FIELDS`, whose purpose is deletion of stale
serialized values, and in two falsifier attacks that prove deletion. They are not in
`SEMANTIC_FIELDS` or `REPAIR_PROVENANCE_FIELDS` and are never republished.

### Pre-HB compatibility outputs retained

`recorded_cost_r`, `authoritative_cost_r`, `cost_r_authority_status`,
`cost_capture_contract_status`, `cost_capture_missing_inputs`, `cost_component_sum_r`,
`cost_component_rebase_delta_r`, and `cost_accounting_status` retain the established row-level
contract; the Wave 19 FD analyzer consumes `cost_accounting_status`. The narrowly bound legacy path
still uses `legacy_emitter_fallback_cost_r`, `cost_capture_redecode_formula`,
`cost_redecode_candidate_r`, and `cost_redecode_authority_status`. Packet repair provenance and
`commission_r_repair_total_redecode_missing_fields` remain because they bind the current 0.12
exception, idempotence, and repairability. No stale derived field is trusted on input.

## Exact size accounting

Runtime means the two production modules only; tests mean the Wave 19 semantics file plus HDB
falsifier.

| Comparison | Runtime physical lines | Runtime numstat | Test physical lines | Test numstat |
|---|---:|---:|---:|---:|
| Wave 19 FG `ba3c18ddf` | 1,781 | baseline | 568 | baseline; falsifier absent |
| HB implementation `bab74dc7f` | 2,266 | baseline for HDB/HDE delta | 925 | falsifier absent |
| HDB closeout `e101fa2b1` | 2,803 | vs HB +889/-352 = **+537 net**; vs Wave 19 +1,168/-146 = **+1,022 net** | 1,809 | Wave 19 test 983 + falsifier 826 |
| HDE implementation `cf70fd7e3` | **2,589** | vs HB +828/-505 = **+323 net**; vs Wave 19 +984/-176 = **+808 net** | **1,807** | Wave 19 test 981 + falsifier 826 |
| HDE change from HDB | **-214** | +148/-362 | **-2** | Wave 19 test +22/-24; falsifier +64/-64 |

The README changed +4/-1. Across all five implementation files HDE is +238/-451, or -213 net; the
difference from the runtime-plus-test reduction is the three-line README expansion.

## Exact proof

### Same-scope HDB-to-HDE A/B

Each side was captured with `scripts/pytest_failset.py`; all four receipts contain a tool-emitted
`gtos-ab-receipt-v1` fence. The `dirty` marker on captures consists of HDE's untracked receipt/result
work; the tested source bytes are the named commits.

| Scope | HDB `e101fa2b1` | HDE `cf70fd7e3` | Failure-set result |
|---|---:|---:|---|
| HDB adversarial matrix | 124 passed | 124 passed | 0 bad -> 0 bad; **0 regressed** |
| Equal-scope train-engine closure | 355 passed | 355 passed | 0 bad -> 0 bad; **0 regressed** |
| Extended broker-cost closure | 46 passed | 46 passed | 0 bad -> 0 bad; **0 regressed** |
| Wave 19 + HDB focused | 166 passed | 166 passed | 0 bad -> 0 bad; **0 regressed** |

Receipts:

- `phase20/receipts/SESSION_HDE_ADVERSARIAL_AB_RECEIPT.md`
- `phase20/receipts/SESSION_HDE_CLOSURE_AB_RECEIPT.md`
- `phase20/receipts/SESSION_HDE_BROKER_COST_AB_RECEIPT.md`
- `phase20/receipts/SESSION_HDE_FOCUSED_AB_RECEIPT.md`

### FD artifact and numeric identity

`research/operations/wave19_sol_repair_2026_08_01/defects/REPRODUCTION_AND_BIAS.json` remains exactly
30,707 bytes with SHA-256
`c9c8516ffbf084f386c8db9e7a13a00bf13155fa45198284d5722a3a88453f30`. Its accepted 17,716 physical
rows, 3,555 scoreable rows, and symbol aggregates remain:

| Symbol | Complete rows | Mean cost R | Scoreable net R sum | Sign flips |
|---|---:|---:|---:|---:|
| GER40 | 13,196 | 0.333507473 | -712.117011599 | 18 |
| UKOIL_cash | 2,532 | 0.067010369 | -198.249660512 | 36 |
| USOIL_cash | 1,988 | 0.077987289 | -140.810044130 | 13 |

Representative operands `0.335891148 + 0.02 + 0.002783978 + 0.0` still evaluate left-to-right to
`0.358675126` (`0x1.6f4888403c167p-2`); Python `sum` would produce
`0.35867512599999996`. `phase20/receipts/SESSION_HDE_FD_IDENTITY.json` binds the independent check.
No artifact or broker truth was regenerated and no raw ledger or broad replay ran.

### Static and contract checks

- `python3 -m py_compile` on both changed modules and both changed test files: PASS.
- JSON parse validation for all HDE captures, FD identity, and completion receipt: PASS.
- `git diff --check`: PASS.
- Exact R2 contract file SHA-256:
  `0667d2decc31090ea24cfc6631ef794a7d0749bbfbc6f8b5554bd74d4178de69`.
- All 45 path entries found under R2 `input_bindings` were compared with the five implementation
  paths: overlap `[]`. No decision-contract-bound byte changed.
- HDE sparse-hydrated only that exact committed R2 input; broker truth was not regenerated.

## Reviewed and created commits

Reviewed authority and implementation history:

- `a7d9260ed0c5ca13cafbd02bcefd93079361275c` — Wave 19 FD source head.
- `fcc9782e3e7af05a90174c8a367c5b5f77223195` — Wave 19 FG tested source-integration head.
- `ba3c18ddf268294813545501f84b635ccc0f25bb` — Wave 19 FG integration closeout/base.
- `bab74dc7f43bdf3e21fa34f5bad982011050b83f` — HB implementation.
- `db447a217a939898edb3d7122058737f63d78828` — HB closeout.
- `54b608691f6aa5e842cd8369c169387163daed15` — HDB implementation.
- `e101fa2b1e0b9399fba4ad1745d639176e06c3e5` — HDB closeout and exact HDE starting head.

Created:

- `cf70fd7e36eaaab8d5d04e04db8c85a7685b0a83` — HDE minimal implementation and test adjustment.
- The containing commit for this result, HDE captures, A/B receipts, FD identity, and machine receipt
  is the scoped HDE evidence closeout. A file cannot contain the hash of the commit that first
  contains itself; git history and the final handoff report that hash.

## Residual risks and boundaries

1. The removed third packet key has no current-tree field producer, fixture, or consumer. An untracked
   external historical row using only that spelling would now remain incomplete; there is no evidence
   obligation supporting the alias.
2. `cost_component_capture_evidence` remains a structural train-evidence witness, not a cryptographic
   signature. Unknown future sources fail closed until explicitly reviewed.
3. The existing `1e-8 R` absolute consistency tolerance remains and its inside/outside edges are
   pinned by the matrix.
4. FD identity binds the accepted artifact and representative arithmetic; it does not regenerate the
   large raw ledger or make a new economic claim.
5. Verification is the commissioned train-engine/broker-cost closure, not a repository-wide green-suite
   claim.
6. No cost engine redesign, live-runtime/config/broker/VPS/token/production/live-trading change,
   activation, merge, push, evidence deletion, March/live outcome read, or broad replay occurred.

## Pre-edit minimality/falsification TODO — completed

- Required behavior: three-state decision; strict numbers; four independent witnesses; duplicate
  conflicts; flattened/nested/twice-normalized identity; exact arithmetic; captured zero; rebase;
  narrow 0.12; downstream refusal; idempotent repair — **preserved and re-proved**.
- Compatibility: keep only committed consumers or exact adversarial obligations — **traced above**.
- Diagnostics: retain one precise reason surface; prevent stale detail recovery — **implemented and
  attacked**.
- Accidental complexity: repeated extraction/serialization/reasons, dead aliases, unused telemetry,
  broad compatibility, implementation-coupled assertions — **reduced without case deletion**.
- Proof: unchanged HDB failure sets, exact final scopes, FD identity, syntax, JSON, diff, contract
  membership, scoped commits, clean closeout — **complete at evidence commit**.
