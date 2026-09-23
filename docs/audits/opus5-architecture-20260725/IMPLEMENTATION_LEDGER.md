# Implementation Ledger

Branch `audit/claude-opus5-architecture-20260725`, from `a3badc054`.
Every change below is either a **fix** (a defect this audit closed) or a **characterisation** (a defect deliberately left alone because fixing it would change accepted sealed evidence — pinned by a test so it cannot change silently).

Test command: `python3 -m pytest tests/test_opus5_architecture_audit_hardening.py tests/test_replay_semantic_parity.py tests/test_mt5.py -q`

---

## Fixes

### P1 — Semantic-parity comparators compared `NaN` as equal
**Register:** R-P1. **Files:** new `src/research_infra/replay_canonical_bytes.py`; `replay_semantic_parity.py`, `replay_acceleration_task2_semantic_acceptance.py`, `b7_5_post_acceleration_semantic_verifier.py`.

`canonical_bytes` is defined **40 times across 6 distinct `json.dumps` signatures**. The three used by the semantic-parity comparators were the only ones with `allow_nan=True`. Under that setting a non-finite float serialises to the bare token `NaN`/`Infinity`, and because parity is decided on **bytes**, `b"NaN" == b"NaN"` — so two runs that both produced an undefined economic value compared **equal** and the comparator reported zero differences. All 28 sealing encoders use `allow_nan=False` and raise on the same input.

Demonstrated before the fix:

```
PARITY canonicalizer (allow_nan=True):
   bytes: b'{"final_r":NaN,"net_r":Infinity,"symbol":"NAS100"}'
   byte-equal -> True   => _difference_paths reports NO difference
   diff paths: []
SEALING canonicalizer (allow_nan=False):
   RAISES: ValueError Out of range float values are not JSON compliant: nan
```

**Change as landed — narrower than first attempted.** One authoritative encoder with the sealing signature, which fails closed and names the offending path. `replay_semantic_parity.compare_semantic_ledgers` catches it and re-raises `SemanticParityError("semantic_row_non_finite:<role>:<index>:…")`, preserving the caller contract.

**Applied to one of the three comparators, not all three.** `b7_5_post_acceleration_semantic_verifier.py` and `replay_acceleration_task2_semantic_acceptance.py` are SHA-256-bound in the decision contract (R37). The first attempt edited them anyway and broke `tests/test_b7_5_post_acceleration_contract.py` with the exact error R37 predicts. Both are reverted to the sealed hashes; the hole they still carry is pinned by `test_characterise_contract_bound_comparators_still_use_the_old_encoder`, which fails when the contract is re-sealed and the fix lands.

**Implementation note.** The first version pre-walked every row with `non_finite_paths` before comparing. That cost ~15 % of comparison time for a check `_difference_paths` already performs via `canonical_bytes`, and it could not see the two other comparison entry points. Replaced with exception conversion at the one place that matters.

**No-op on history.** A scan of the materialised Phase-D January S1R1 ledgers (order, trade, oracle, bucket, source) found **zero** non-finite tokens. On all existing evidence the new encoder is byte-identical to the one it replaces.

**Superseded test.** `test_compare_semantic_ledgers_preserves_nonfinite_numeric_identity` asserted the old behaviour. Replaced by `test_compare_semantic_ledgers_rejects_nonfinite_numeric_values`, which keeps the `+inf`/`-inf` sign-flip case the old test protected **and** adds the `NaN`/`NaN` case it could not catch. The invariant analysis is written into the test docstring.

### P2 — Authority hash non-determinism: **verified, NOT fixed** (contract-bound)
**Register:** R-A5-3. **File:** `src/research/moonshot_scheduler_v4_best_trade_allocator.py`.

A `set` is not a `Sequence`, so it fell through `_canonical_hash_payload` to `json.dumps(..., default=str)`, which emits the Python set repr — whose element order depends on `PYTHONHASHSEED`. Measured:

| `PYTHONHASHSEED` | `_stable_sha256({"symbols": {...5 symbols...}})` |
|---|---|
| 0 | `fd1af9b66969590d…` |
| 1 | `0bdd2db34034b61c…` |
| 2 | `57681401acadf64f…` |
| 3 | `9e57f36a4f0b1124…` |

`PYTHONHASHSEED` is unpinned repo-wide except in one test.

**Not fixed.** This file is contract-bound (R37); the first attempt to guard it broke the arm bindings. Reverted. Two further defects in the same function are also left in place and pinned by `test_characterise_authority_hash_defects_remain_unfixed`: `None`/`""` elision collides with key absence, and floats round to 12 dp. The adversarial review additionally found that a guard on *values* would have been incomplete anyway — a `frozenset` used as a **dict key** is stringified by `str(key)` and never routed through the canonicaliser, producing 6 different digests across 6 hash seeds.

### P3 — `_modify_tp` left no audit record of a broker mutation while halted
**Register:** R5 (downgraded). **File:** `src/components/execution.py`.

`_modify_tp` reached `self.mt5.order_send(request)` with zero `runtime_halt` references, while `_modify_sl` records a halt diagnostic for every mutation it performs while halted.

**First attempt was wrong and is retracted.** It refused "exposure-extending" TP moves. A TP move does not increase risk — the stop is untouched, so max loss is unchanged — and the TP1→TP2→TP3 ladder moves TP further from entry by construction. `tests/test_runtime_control_atomic_halt.py:238` asserts `_modify_tp(ticket, 2680.0) is True` on a long with TP 2670.0 **while halted**. The change broke that test; it is a codified statement of intent, not an oversight.

**Change as landed.** Take the halt snapshot so the mutation is recorded in the halt diagnostic stream with `disposition: permitted_tp_move_does_not_increase_risk`, then proceed. Behaviour is unchanged; only the audit trail improves. The predicate `_tp_modify_reduces_or_preserves_exposure` is deleted.

### P4 — `create_mt5` opened a real broker connection for any unrecognised mode
**Register:** R7. **File:** `src/mt5/__init__.py`.

`if mode == "mock": … else: return RealMT5(...)` meant `create_mt5("mok")`, `create_mt5("simulate")` and `create_mt5("")` all connected to a real terminal.

**Change.** `_REAL_MODES = frozenset({"demo", "live"})`; anything outside `{"mock", *_REAL_MODES}` raises. Every string-literal call site passes `mock`, `demo`, or `live`, and all four argparse definitions restrict to those three.

**Known rough edge (accepted).** `scripts/run_shadow_observer.py:78-82` uses `default=os.environ.get("GTOS_MODE", "live")`, and argparse does **not** validate `choices` against a default — so `GTOS_MODE=paper` now raises an unhandled `ValueError` where it previously opened a real broker connection. Failing loudly is the better of the two, but a clean message would be better still.

### P5 — `max_gap_pct: 0` silently became the loosest setting
**Register:** R33. **File:** `src/components/verification.py`.

`config.get("filters", {}).get("max_gap_pct") or 1.5` coerced the **strictest** configured value (`0`) into the **loosest** default.

**Hardened after review.** A bare `float()` introduced two new failure modes the review caught: `max_gap_pct: ""` raised an unhandled `ValueError`, and YAML `no`/`off` became `0.0` — turning the gate from permissive to rejecting everything. Now: `None` and `bool` fall back to 1.5, unparseable values fall back to 1.5, numeric strings coerce. Also fixed the sibling defect on the same line — `config.get("filters", {})` only defaults on a *missing* key, so an explicit empty `filters:` raised `AttributeError`; it is now `config.get("filters") or {}`.

---

## Characterisations (deliberately not fixed)

Each is pinned by a test that fails if the behaviour changes, so it cannot drift silently. All are in `tests/test_opus5_architecture_audit_hardening.py`.

| Test | Finding | Why not fixed |
|---|---|---|
| `test_characterise_authority_hash_elides_none_and_empty_string` | R-A5-2. `_canonical_hash_payload` drops keys whose value is `None` or `""`, so `{"risk_pct":1.0,"broker_live_authority":None}` and `{"risk_pct":1.0}` produce the **identical** authority digest. A safety flag that degrades to `None` is invisible to every `expected_*_authority_hash_sha256` check. (`False` is *not* elided — which is why the defect is subtle.) | emitting `null` changes every sealed authority digest |
| `test_characterise_authority_hash_rounds_floats_to_12dp` | R-A5-2b. Values differing by <1e-12 share a digest | same |
| `test_characterise_selected_orders_materialise_in_lexical_order` | R8. `sorted(selected_instance_key_set)` at `v4:93202`, rank already destroyed by `set()` at `:91706` | changing iteration order changes every sealed result |
| `test_characterise_duplicate_top_level_definition_in_replay_engine` | R26. Guards the whole of `src/` against **new** duplicate top-level definitions, with an allowlist of the two known cases | editing the 96k-line monolith invalidates every sealed arm binding (see R37) |
| `test_characterise_replay_and_live_use_different_risk_profiles` | R10. Asserts the divergence set is exactly `{NAS100: (0.25, 0.5), US30_cash: (2.0, 1.0)}` | the pin is a research decision, not a bug to silently flip |

**The duplicate-definition guard found a defect nobody had recorded.** `_is_sha256` is defined twice in `replay_acceleration_progressive_benchmark.py` with **different semantics**: `:480` uses `int(value, 16)` (accepts uppercase hex); `:997` requires every character in `"009abcdef"` (lowercase only). The stricter one wins, so live behaviour is the safe one — but a reader studying `:480` sees validation that never runs. Logged as R26b.

---

## Measurements

| Measurement | Result | Artifact |
|---|---|---|
| Sampled dense-day profile (4 ms, 86,945 samples, 95.5 % of wall captured) | proof/canonicalise/encode/attribute/type-check = **60.6 % of self-time**; `evaluate_candidate_v4` = **8.3 % of wall** | `receipts/profile_jan01_02_sampled.json` |
| Order-row anatomy on real sealed ledgers | 494,196 B, 1,274 top-level keys, 8,091 leaves → **765 distinct values**, **63.8 % key names** | §4 of the performance audit |
| Arm evidence volume | **15.75 GB** logical JSON for **148 orders / 72 trades** | `B7_5_POST_ACCELERATION_ARM_RECEIPT.json` |
| Fixed per-process startup | **63.03 s wall / 108.98 s CPU** before the first decision | measured directly |
| No-event economic path | **1.7 s** across all four sealed January arms — the 5 s target passes; the reported 52.5 s "miss" is startup amortised onto it | arm summaries |
| ABC `isinstance` dispatch | `isinstance(x, Mapping)` 81.4 ns vs `isinstance(x, dict)` 14.7 ns (**5.53×**); measured 65.8 s self-time ⇒ **≈0.81 billion calls** in one two-day run | §5.1 |
| **Exact-parity optimisation** | concrete-type fast path in `_canonical_hash_payload`: **2.19× on canonicalisation, 1.56× on the full hash stage**, **0 digest mismatches over 296 real authority payloads (41.6 MB canonical)** | `receipts/micro_parity.txt` |
| Reused `JSONEncoder` hypothesis | **refuted at this call site** — 1.00×. Encoder construction is amortised over large payloads; the profile's 19.7 s must come from many small dumps elsewhere, which is unproven | same |

---

## Adversarial review of this audit's own changes

An independent reviewer was tasked with refuting these fixes. It found **two real regressions I had missed and wrongly declared absent**, plus six lesser defects. All are resolved above. The failure was mine and it was methodological: I ran a *subset* of tests and reported "zero regressions" without an A/B against the parent commit.

| Finding | Outcome |
|---|---|
| **C2 CRITICAL** — `test_runtime_control_atomic_halt.py::test_halt_blocks_new_entries_but_allows_risk_reducing_management` passed at parent, failed after P3 | P3 retracted and re-landed as diagnostic-only. Test passes. |
| **C1/C3 CRITICAL** — P1/P2 edited three contract-bound files; `test_b7_5_post_acceleration_contract.py` broke with the exact `input_drift` error R37 predicts | All three reverted to the sealed hashes. Test passes. |
| **H1 HIGH** — a circular reference now *hung* instead of raising, because `non_finite_paths` had no cycle detection and ran inside the `except ValueError` handler | Cycle detection added; two tests cover it. |
| **H2 HIGH** — the P2 set guard was incomplete anyway: a `frozenset` **dict key** is stringified by `str(key)` and bypasses the canonicaliser (6 seeds → 6 digests) | Recorded; P2 not landed. |
| **H3 HIGH** — `NonFiniteCanonicalValueError` subclasses `ValueError`, not `SemanticParityError`, and the pre-check covered only one of three entry points | Pre-check replaced by exception conversion at the single relevant site; blast radius now one module. |
| **H4/M1 HIGH** — the TP predicate contradicted the declared halt boundary and failed *open* for unknown `position.type` | Predicate deleted. |
| **M2 MEDIUM** — bare `float()` broke on `""` and inverted on YAML `no` | Hardened. |
| **M3 MEDIUM** — sibling `config.get("filters", {})` defect left on the same line | Fixed. |
| **M4 MEDIUM** — four new tests were source-string matching, not behaviour; the hash-seed test used a **list**, so it never entered the new branch | Rewritten as behavioural or removed with the code they covered. |

## Regressions

**Verified by A/B against the parent commit `5e70fa3ea`, the check I should have run first:**

| | failed | passed |
|---|---:|---:|
| parent `5e70fa3ea` | 11 | 874 |
| this branch | **11** | **874** |

Identical failure sets — **zero regressions, zero new failures**. The 11 are pre-existing: 10 in `test_selector_v4.py` and 1 in `test_permissions.py`, all caused by `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` being an unhydrated 131-byte LFS pointer in this checkout. Worth noting independently: **the test suite is not green at the commit whose evidence was accepted.**

**Blocker discovered, and it is a finding (R37).** The decision contract binds 42 source files by SHA-256, and those hashes feed the arm fingerprints. Applying P1 to `b7_5_post_acceleration_semantic_verifier.py` — a file that never runs during a replay — caused the next replay to fail closed:

```
ValueError: selection_sizing_decision_contract_input_drift:
  src/research_infra/b7_5_post_acceleration_semantic_verifier.py
```

For the end-to-end benchmark the three contract-bound files were temporarily reverted (patches retained), the measurement taken, and the fixes restored. **This means P1 and P2 cannot ship into the campaign without regenerating the decision contract and all four arm fingerprints** — which is precisely why these defects survived.

---

## Unresolved decisions for the owner

| # | Decision | Why it is yours |
|---|---|---|
| D1 | Re-seal the decision contract to land P1 and P2, or carry the defects until the next planned re-seal | costs a contract regeneration and re-running the accepted windows |
| D2 | Fix R8 (materialise orders in finalizer-rank order) — changes every sealed result | a research-validity call, not an engineering one |
| D3 | Fix R-A5-2 (`None` elision) — changes every authority digest | same |
| D4 | Retire `timewarp_replay_risk_profile_path` so replay models the live profile | changes what the research measures |
| D5 | Run the four factorial arms in parallel — **3.7× campaign speedup, zero semantic change**, machinery already built and proven in Task 7 | pure scheduling; recommended unconditionally |
