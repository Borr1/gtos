# Session HB — cost component completeness hardening

## Findings

1. **The defect was real at both ends of the train-only semantic chain.**
   `repairs._apply_broker_true_commission_capture` checked only spread before
   recomputing the total and used `(slippage or 0.0)` and `(swap or 0.0)`.
   Its numeric parser also accepted NaN and infinity. At the capture boundary,
   `decision_semantics` could still expose a recorded total as authoritative
   when components were incomplete, and it checked that measured commission
   existed without checking that it equalled component commission.
2. **The repaired chain now fails closed under one shared three-state
   classifier.** Missing, null, invalid, non-finite, unauthorised, or
   inconsistent evidence retains its exact fields and reasons but emits no
   authoritative component total. Explicit captured `0.0` remains valid.
3. **Contradictory totals are no longer resolved opportunistically.** A
   measured/component commission mismatch or an unexplained recorded/component
   residual is `refused`. The two declared reconciliation paths remain: an
   explicit fill-geometry rebase and FD's identified 0.12 legacy-emitter
   fallback replacement with captured commission authority.
4. **Genuinely complete FD economics are unchanged.** The committed FD
   reproduction artifact remains byte-identical at SHA-256
   `c9c8516ffbf084f386c8db9e7a13a00bf13155fa45198284d5722a3a88453f30`;
   the complete-row counts, means, net sums, and sign flips are pinned by a
   behavioral test. The implementation deliberately retains FD's prior
   addition order.
5. **The scoped failure sets are empty on both sides.** Focused proof is
   16/16 at `ba3c18ddf` versus 42/42 at `bab74dc7f`; the train-engine and cost
   closure is 205/205 versus 231/231. Both A/Bs are `0 bad -> 0 bad`, with zero
   regressed node IDs.

**Verdict: COMPLETE for Session HB's training/evidence scope.** No live,
runtime, config, activation, broker, VPS, or token surface changed.
`activation_authority: false`.

## Before/after semantics

| Evidence case | Before HB | After HB |
|---|---|---|
| Missing spread | Packet repair blocked only this one missing component. | `incomplete`; `spread_r` is retained in the absent/null list and authorization is refused. |
| Missing slippage | `(slippage or 0.0)` silently charged zero and could label the re-decode complete. | `incomplete`; no component total is emitted and the prior total remains diagnostic only. |
| Missing swap | `(swap or 0.0)` silently charged zero and could label the re-decode complete. | `incomplete`; no component total is emitted and the exact field/reason is retained. |
| Missing commission | A non-fallback recorded total could remain authoritative; fallback handling did not preserve a full four-field refusal state. | `incomplete`; component commission and its measured/capture authority are both required. |
| Explicit authorised zero | Falsy zero and absence shared convenience paths. | Finite component `0.0` plus matching finite measured authority is `complete`; absence is not zero. |
| NaN or infinity | The packet parser returned non-finite floats, allowing non-finite arithmetic and a nominal complete status. | `incomplete`; each non-finite component or authority field is named and authorization is refused. |
| Component commission != measured commission | Presence of measured commission was sufficient. | `refused`; both values and their delta remain visible, with no authoritative selection. |
| Recorded total != component sum | The recorded value remained authoritative and the residual was merely `unclassified` unless a fallback branch happened to replace it. | `refused`, except for an explicit geometry rebase or FD's explicitly identified and authority-bound 0.12 fallback replacement. |
| Fully complete FD row | Exact four-component re-decode. | Same numeric re-decode and prior addition order; new state is `complete` and decision authorization is explicit. |

## State machine

| State | Entry condition | Numeric output | Downstream authorization |
|---|---|---|---|
| `complete` | Spread, commission, expected slippage, and swap are explicitly present, numeric, finite, authority-backed, and consistent. | `cost_component_candidate_sum_r` and authorised `cost_component_sum_r`; declared reconciliation is recorded separately. | `authorized_complete_component_cost` |
| `incomplete` | Any required component or authority is absent, null, invalid, or non-finite. | Original/recorded evidence is preserved; no authorised component sum. | `refused_incomplete_component_cost` with exact field-level reasons |
| `refused` | Finite evidence contradicts itself, including commission or total disagreement. | Diagnostic candidate values and deltas remain visible; neither claim wins. | `refused_inconsistent_component_cost` with exact inconsistency reasons |

Normalization is idempotent. Every derived v1 cost-authorization field is
recomputed, so an incomplete historical row cannot retain a stale `complete`
label merely because it was normalized before a projection or join. Original
cost/component fields and recorded totals are not rewritten.

## Implementation

- `src/research_infra/train_engine/decision_semantics.py`
  - bumps the evidence schema to `gtos.train_engine.decision_semantics.v2`;
  - provides the shared finite/authority/consistency classifier;
  - distinguishes absent, null, invalid, non-finite, authority-missing, and
    inconsistent fields;
  - validates component commission against measured commission within the
    existing `1e-8 R` float tolerance;
  - refuses unexplained total residuals and downstream authoritative cost;
  - clears and recomputes derived authorization fields on every normalization.
- `src/research_infra/train_engine/repairs.py`
  - rejects non-finite packet numbers;
  - replaces convenience-zero recomputation with the shared four-component
    assessment;
  - leaves the legacy/fallback total in place as diagnostic evidence when the
    component state is not complete;
  - carries field-level refusal provenance and makes re-gating refuse an
    incomplete or inconsistent repair packet.
- `src/research_infra/train_engine/README.md` records the v2 state machine and
  backward-compatibility boundary.
- `tests/research_infra/test_wave19_sol_decision_semantics.py` adds the
  adversarial matrix and FD identity proof without weakening prior assertions.

Implementation commit:
`bab74dc7f43bdf3e21fa34f5bad982011050b83f` (`fix(train): fail closed on
incomplete cost components`).

## Behavioral proof

The focused file covers:

- each of the four single absent components;
- multiple absent components;
- null component evidence;
- explicit authorised zero versus absent zero authority;
- NaN and positive infinity for each of the four components;
- packet-level missing slippage/swap/spread refusal;
- packet-level NaN/infinity refusal;
- measured/component commission mismatch;
- unexplained recorded/component total mismatch;
- an exact fully complete component sum;
- declared geometry-rebase preservation;
- projected/downstream `authoritative_cost_value` refusal;
- stale v1 `complete` label removal;
- FD artifact and complete-row economic identity.

### Exact failure-set A/B

| Scope | Parent `ba3c18ddf` | Repair `bab74dc7f` | Failure-set delta |
|---|---:|---:|---|
| `tests/research_infra/test_wave19_sol_decision_semantics.py` | 16 passed, 0 failed, 0 errors | 42 passed, 0 failed, 0 errors | 0 fixed, **0 regressed** |
| Seven existing `test_train_engine_*` files + the focused file + `tests/test_broker_net_cost_engine.py` | 205 passed, 0 failed, 0 errors | 231 passed, 0 failed, 0 errors | 0 fixed, **0 regressed** |

Receipts:

- `phase20/receipts/SESSION_HB_NARROW_AB_RECEIPT.md`
- `phase20/receipts/SESSION_HB_CLOSURE_AB_RECEIPT.md`
- the four embedded source captures beside those receipts

Both sides were captured from clean detached snapshots with the same committed
broker-truth artifact and the exact committed route bridge hydrated. The
initial worktree sparse profile manufactured 14 inherited failures (13 missing
broker-truth inputs and one missing route module); the supported exact-path
hydration removed those fixture-absence failures before the authoritative A/B.
No replay was launched.

Additional static checks:

```text
python3 -m compileall -q src/research_infra/train_engine \
  tests/research_infra/test_wave19_sol_decision_semantics.py  # PASS
git diff --check                                               # PASS
```

## Complete-row economic identity

The test reads the committed Wave 19 FD reproduction artifact, verifies its
SHA-256, and pins these previously accepted complete-row results:

| Symbol | Complete physical rows | Re-decoded mean cost R | Scoreable re-decoded net R | Sign flips |
|---|---:|---:|---:|---:|
| GER40 | 13,196 | 0.333507473 | -712.117011599 | 18 |
| UKOIL_cash | 2,532 | 0.067010369 | -198.249660512 | 36 |
| USOIL_cash | 1,988 | 0.077987289 | -140.810044130 | 13 |

Aggregate population: 17,716 physical rows and 3,555 scoreable rows. The
representative receipt-authorised GER40 row remains
`0.335891148 + 0.02 + 0.002783978 + 0.0 = 0.358675126 R`; both its component
sum and authoritative cost are unchanged.

This is a no-replay identity proof over the accepted FD artifact and exact
complete-row arithmetic. It does not reconstruct missing historical fields or
make a new profitability claim.

## Contract and scope controls

- R2 membership inspection found none of the four implementation/test/doc
  paths in `common_behavior_inputs`, `package_authority_inputs`, or unbound
  verifier membership. No decision-contract-bound byte changed.
- The materialized R2 audit still reports the inherited
  `src/components/broker_net_cost_engine.py` drift already carried by Wave 19;
  Session HB did not touch it. Other known FG drifts remain outside this sparse
  materialization. No new bound drift was introduced.
- No config, runtime, activation, broker, VPS, token, live-service, or
  broker-capable script was changed or invoked.
- No March or live-forward outcome was read.
- No broad or sealed replay ran.
- No merge, push, evidence deletion, or policy arming occurred.
- `activation_authority: false`

## Residual risks

1. Historical fields already discarded remain unrecoverable. V2 preserves the
   exact missing-input requirement; it does not infer or backfill a component.
2. The decision-contract-bound broker packet builder still contains its older
   convenience-zero construction. HB deliberately did not edit that runtime
   surface; the repaired train consumers now reject its packet whenever the raw
   component fields show the gap. Other consumers outside this commissioned
   train/evidence chain require a separately authorised runtime repair.
3. The accepted FD aggregate is pinned, not regenerated from the 1.2 GB raw
   ledger. This respects the no-broad-replay boundary; the committed artifact
   hash plus exact row arithmetic is the proof available in scope.
4. `1e-8 R` remains the existing float-consistency tolerance. Differences
   larger than it refuse; smaller representation noise is treated as equal.
5. Verification is the relevant train-engine/cost closure, not a claim that the
   repository-wide suite is green.
