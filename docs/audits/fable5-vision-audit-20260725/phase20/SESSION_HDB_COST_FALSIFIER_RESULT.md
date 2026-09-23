# Session HDB — independent cost-completeness falsifier

## Verdict

**HB is not safe as submitted. It is safe to integrate only with reviewer commit
`54b608691f6aa5e842cd8369c169387163daed15`.** The builder bytes admit
authoritative costs from untrusted scalar types, stale labels, contradictory
packet/row evidence, incomplete geometry-rebase declarations, and an
over-broad 0.12 fallback exception. The reviewer commit closes every reproduced
path, preserves FD's accepted economics exactly, and leaves incomplete evidence
unusable downstream.

The change is not small by raw line count. Relative to builder head it changes
five files by 1,799 insertions and 375 deletions; 826 inserted lines are the new
124-case falsification matrix. The two production modules have a net increase
of 537 lines. It is nevertheless bounded enough to integrate by authority and
blast radius: one train-only cost normalizer, one train-only commission packet
repair, one README contract, and tests. No cost producer, runtime, config,
broker, activation, VPS, token, or live-trading surface changed. The runtime
logic now has one strict numeric parser, one packet-capture extractor, one
component classifier, and one telemetry publisher; the duplicated packet/row
classifier and duplicated state publication were removed.

`activation_authority: false`

## Findings, ordered by severity

### HDB-1 — High: Python coercion and mere field presence created cost authority

HB called `float(...)` on components and measured commission. Python booleans,
numeric-looking strings, padded strings, and some non-scalar/coercible objects
could therefore become finite cost evidence. Spread, slippage, and swap needed
only a key; commission could be authorized by a stale row-level
`commission_r_repair_status: applied` label. A captured zero and an invented
zero were not distinguishable at the authority boundary.

Reviewer repair: cost evidence must be a non-boolean `numbers.Real`, finite,
and non-negative. Every component must agree with an independent numeric/source
witness extracted from the producer packet. Legitimate captured zero remains
valid only when the witness is also numeric zero with an allowed captured
source.

### HDB-2 — High: contradictory finite evidence was selected instead of refused

HB selected top-level components ahead of nested packet components, selected
one recorded-total alias, and selected one measured-commission location. It did
not reconcile duplicate packet aliases, packet scalar versus component-map
values, flattened capture evidence versus a retained packet, or top-level
versus nested measured commission. A favorable finite value could win by
location.

Reviewer repair: all duplicate finite claims must agree within the existing
`1e-8 R` absolute tolerance. Conflicting `cost_r`/`expected_cost_r`, packet
aliases, component maps/scalars, capture witnesses, sources, or measured
commission locations produce `refused_inconsistent_component_cost`; neither
claim becomes authoritative. Malformed nested containers fail closed without
falling back to a convenient flattened value.

### HDB-3 — High: geometry and 0.12 exceptions waived contradictions too broadly

HB accepted a truthy geometry marker, any non-empty effective-cost field, or a
non-unit multiplier as sufficient evidence for a rebase. It also treated 0.12
plus loose broker/refusal/zero-commission signals as the named legacy fallback.
The packet repair could accept a stale `authority_fallback_total_cost_r: 0.12`
even when the original four components were already complete and contradicted
that total.

Reviewer repair: a geometry rebase requires the marker to be exactly `True`,
the original cost to equal the component sum, the effective cost to equal the
recorded total, and any supplied multiplier to be a positive numeric value that
reproduces the effective cost. The 0.12 replacement requires the exact current
repair binding, trusted source, complete re-decode, replacement flag, and—in
packet repair—the actual legacy shape of an unresolved original commission
capture. A stale fallback field cannot waive a complete-component conflict.

### HDB-4 — High: commission packet repair could publish invalid or inconsistent totals

HB accepted boolean, string, negative, or merely non-empty-source commission
inputs. It did not require measured and charged commission to agree, did not
require the known broker-truth repair source, and could replace an existing
total without first proving that total was either the original component sum or
the exact named fallback. Reapplying the repair changed
`commission_r_repair_total_before_r`, so repair was not idempotent.

Reviewer repair: measured and charged commission must be strict, non-negative,
finite numeric values that agree within tolerance and carry the exact trusted
source. Existing contradictory totals refuse and remain unchanged. The total is
rewritten only after the shared four-component classifier returns `complete`.
The first observed total is preserved with `setdefault`; a second repair is
byte-for-byte idempotent for the tested packet.

### HDB-5 — Medium: HB changed FD's historical floating-point addition order

HB documented preservation of the FD order but used Python `sum(...)`.
For the representative FD operands, direct historical evaluation yields
`0.358675126` (`0x1.6f4888403c167p-2`), while built-in `sum` yields
`0.35867512599999996`. The economic delta is tiny, but the claimed exact
identity was false.

Reviewer repair: both normalization and packet repair explicitly evaluate
`spread + expected_slippage + swap + commission` left to right.

### HDB-6 — Medium: stale derived state survived structural changes

HB's nested/flattened contract did not carry an independent witness for every
component and did not reconcile a retained packet with flattened fields.
Historical `complete`/authorization fields could be mistaken for current
authority after projection, normalization, or loss of a nested map.

Reviewer repair: all derived authorization state is discarded and recomputed
on every normalization. Nested packet evidence is authoritative only after
internal reconciliation; its raw witnesses are projected into
`cost_component_capture_evidence` so the flattened form can be normalized
again. Nested, flattened, and twice-normalized complete rows are deterministic;
loss of a witness changes the row to incomplete and clears authoritative cost.

## Reconstructed FD/FG cost authority

| Component | Numeric evidence | Required independent authority |
|---|---|---|
| Spread | `total_cost_components.spread_r` or its reconciled flattened value; strict finite non-negative number | Matching `tick_cost.spread_r`, `source_status: captured`, and an allowed quote source: historical predecision tick, historical spread-floor template, or the two broker-profile template sources. The conservative no-source default is not authority. |
| Expected slippage | Component value; strict finite non-negative number | Matching packet `expected_slippage_r` with source `trade_params` or `config.selected_cell_default_expected_slippage_r`. |
| Swap | Component value; strict finite non-negative number | Matching `swap_cost.cost_r`, `source_status: captured`, model `points_mode_time_stop_swap_cost_r_v1`. The producer represents favorable swap as zero, so negative values are outside this contract. |
| Commission | Component value; strict finite non-negative number | Matching `commission_cost.cost_r`, `source_status: captured`, `included_in_total_cost_r is True`, source `broker_true_commission_cash_to_r_v1` or the exact trusted FD repair source, plus a matching strict broker-truth measured commission. |

The four complete components are added in the historical order. A recorded
total must equal that result unless the exact geometry-rebase contract applies
or the exact current 0.12 replacement binding authorizes re-decoding. Any
contradictory finite claim refuses rather than selecting the lower or otherwise
favorable value.

## Compatibility decisions

- V1 numeric fields, packets, totals, and diagnostic provenance remain evidence;
  the normalizer does not rewrite historical source values.
- A historical or stale V2 `complete` label is not authority. Current component
  values, witnesses, and consistency are recomputed.
- Historical flattened rows without `cost_component_capture_evidence` remain
  diagnostic/incomplete. This is intentional: missing authority cannot be
  reconstructed from a stale source label.
- Nested packets remain supported. Flattened rows produced from a valid packet
  retain the raw witness map and remain idempotent on a second normalization.
- Explicit captured zeroes remain complete; absent, null, blank, boolean,
  string, non-finite, non-scalar, negative, or unauthoritative values do not.
- Unrelated train-engine behavior is unchanged over the selected closure: 355
  passed, zero failed, zero errored after the reviewer commit.

## Exact proof

### Builder-head adversarial A/B

The final adversarial test source has SHA-256
`25ee08993613496f7108e976a17fc3d6676e6accd15bf135f886bcf1440967e6`.
For the before side, exact builder modules were injected before pytest
collection without changing the worktree:

- `decision_semantics.py` SHA-256
  `5c0271259505785f1988b06b5d1fb8c3f6ad8437f19ed1358809993f3bc16d4e`
- `repairs.py` SHA-256
  `f1e836596326bf9c6ff5be32562b635eeb8efe6a63cd5302f357de99bd4be7c0`

Final same-test result:

| Side | Passed | Failed | Errored | Failure-set result |
|---|---:|---:|---:|---|
| Builder `db447a217` | 42 | 82 | 0 | 82 exact node IDs reproduced |
| Reviewer `54b608691` | 124 | 0 | 0 | 82 fixed, **0 regressed** |

`phase20/receipts/SESSION_HDB_ADVERSARIAL_AB_RECEIPT.md` embeds every exact
failed node ID and the tool-emitted `gtos-ab-receipt-v1` fence. The earlier
`SESSION_HDB_BUILDER_ADVERSARIAL.json` capture (78 failures) is retained only as
chronology; `SESSION_HDB_BUILDER_ADVERSARIAL_FINAL.json` is the authoritative
same-test baseline after the final four attacks were added.

### Train-engine and broker-cost closure

The builder closure is a disjoint union of HB's exact nine-file builder capture
and the exact-builder-module adversarial capture. Its scope is identical to the
reviewer closure.

| Scope | Builder | Reviewer | Failure-set result |
|---|---:|---:|---|
| Seven `test_train_engine_*` files, Wave 19 semantics, HDB falsifier, broker net-cost engine | 273 passed, 82 failed, 0 errors | 355 passed, 0 failed, 0 errors | 82 fixed, **0 regressed** |
| Broker-truth/cost carry, terminal aliases, costs layer, slippage/exit coverage, exact geometry-rebase node | — | 46 passed, 0 failed, 0 errors | PASS |
| Wave 19 semantics + HDB falsifier direct focused run | — | 166 passed, 0 failed, 0 errors | PASS |

The exact closure receipt is
`phase20/receipts/SESSION_HDB_CLOSURE_AB_RECEIPT.md`; captures are beside it.

The first extended broker-cost run correctly exposed absent sparse committed
fixtures at these exact nodes:

- `tests/research_infra/test_cn_live_cost_carry.py::test_carry_builder_reproduces_every_committed_payload_and_diff`
- `tests/test_repair_broad_replay_terminal_cost_aliases.py::test_staged_repair_changes_only_mismatched_alias_fields`
- `tests/test_repair_broad_replay_terminal_cost_aliases.py::test_main_fails_closed_before_commit_on_unexpected_change_count`

Only the exact committed fixtures were hydrated—never regenerated:

- `B7_5_POST_ACCELERATION_EXECUTION_SEAL.json`, SHA-256
  `ff15505034e738e8b4e4cb09ab3e0e3f9d399c955974caa2e8fdffd893def340`
- `repair_broad_replay_terminal_cost_aliases.py`, SHA-256
  `1a541b0a1f551b66369d345dc3866342a4d171887f7fe8b3447c80d2a6b7a05f`

The exact rerun is the 46-pass capture above. One discarded command referenced
the nonexistent path
`tests/test_v4_timewarp_broker_cost_replay.py::test_post_packet_marketability_rebase_updates_costs_and_audit_fields`
and exited 4 before collection; it is not a test failure. The intended committed
node
`tests/test_v4_timewarp_simulated_live_research_loop.py::test_marketable_limit_rebased_cost_authority_overrides_original_geometry_cost`
is included in the passing 46-test receipt.

### FD exact identity

The accepted artifact
`research/operations/wave19_sol_repair_2026_08_01/defects/REPRODUCTION_AND_BIAS.json`
is byte-identical: 30,707 bytes, SHA-256
`c9c8516ffbf084f386c8db9e7a13a00bf13155fa45198284d5722a3a88453f30`.
It contains 17,716 physical rows and 3,555 scoreable rows.

| Symbol | Complete rows | Mean cost R | Scoreable net R sum | Sign flips |
|---|---:|---:|---:|---:|
| GER40 | 13,196 | 0.333507473 | -712.117011599 | 18 |
| UKOIL_cash | 2,532 | 0.067010369 | -198.249660512 | 36 |
| USOIL_cash | 1,988 | 0.077987289 | -140.810044130 | 13 |

This is exact artifact and accepted aggregate identity, plus exact numeric
identity for the representative arithmetic. It does not regenerate the raw FD
ledger or make a new economic claim.

### Static and contract checks

- `python3 -m py_compile` on both changed modules and both semantic test files:
  PASS.
- `git diff --check`: PASS.
- All JSON receipts parsed: PASS.
- R2 contract membership over all five implementation paths: zero bound
  overlap. No decision-contract-bound byte changed.
- Initial branch/head/status: exact branch
  `phase20/cost-completeness-falsifier`, exact clean builder head `db447a217`,
  sparse checkout active, 30 GiB free.

## Reviewed and created commits

Reviewed:

- `ba3c18ddf268294813545501f84b635ccc0f25bb` — Wave 19 FG integration base.
- `bab74dc7f43bdf3e21fa34f5bad982011050b83f` — HB implementation.
- `db447a217a939898edb3d7122058737f63d78828` — HB closing result/receipt and
  commissioned builder head.

Created:

- `54b608691f6aa5e842cd8369c169387163daed15` — reviewer implementation and
  adversarial tests.
- The containing commit for this result and the machine receipt is the scoped
  HDB evidence closeout. A file cannot contain the hash of the commit that first
  contains itself; the containing hash is reported by git history and the final
  handoff.

## Residual risks and boundaries

1. `cost_component_capture_evidence` is a structural witness carried by the
   train evidence chain, not a cryptographic signature. A future producer must
   add a deliberate allowed source contract; unknown sources fail closed.
2. Historical components or witnesses already discarded cannot be recovered.
   Those rows remain incomplete even when their old numeric total is present.
3. The decision-contract-bound broker packet producer still contains legacy
   convenience-zero construction. This commission did not authorize editing
   that runtime surface; the reviewed train consumers now reject the gap.
4. The exact FD artifact was verified, not regenerated from its large raw
   ledger. No broad replay ran.
5. The existing `1e-8 R` absolute consistency tolerance remains. The matrix
   pins inside/outside edges.
6. Verification is the relevant train-engine and broker-cost closure, not a
   repository-wide green-suite claim.
7. No March or live-forward outcome was read; no runtime/config/broker/VPS/token
   surface was touched; no merge, push, deletion, arming, or activation occurred.
