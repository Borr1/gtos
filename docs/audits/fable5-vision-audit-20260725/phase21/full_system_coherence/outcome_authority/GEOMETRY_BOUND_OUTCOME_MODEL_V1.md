# GEOMETRY_BOUND_OUTCOME_MODEL_V1 — the geometry-bound outcome probability model

**Status: RESULT-BEARING, fitted on the opened estate, accepted end-to-end by
`geometry_bound_outcome_calibration_disposition()`. Default-off everywhere; live path
untouched.** Built 2026-08-11 on branch `w21-geometry-bound-outcome-model`.

## 1. What this is and what it replaces

Wave 21's probability truth read (`probability_truth/PROBABILITY_EV_TRUTH_V1.json`)
falsified the legacy action-support score as an outcome probability: strict
target-vs-stop AUC **0.496**, Brier **0.4769** against a base-rate Brier of 0.1877,
with every probability/EV surface stripped fail-closed under truth mode and the
runtime disposition pinned to `NOT_EVALUABLE_NO_GEOMETRY_BOUND_OUTCOME_MODEL`.

This model fills the acceptance slot that refusal reserved. It is exactly the
estimator preregistered in `OUTCOME_AUTHORITY_PREREGISTRATION_V1.json`
(payload `2db7e5c9…`), promoted from the synthetic-only evaluator
(`fit_wave21_development`, `UNBOUND_SYNTHETIC_ONLY_NOT_RESULT_BEARING`) to a
result-bearing fit:

- **Stage 1 — fill**: Beta(1/2,1/2) Jeffreys over resolved LIMIT attempts;
  MARKET fill is exactly 1 by contract (missing successor source is censoring,
  never no-fill).
- **Stage 2 — terminal given fill**: Dirichlet(1/2,1/2,1/2) Jeffreys over
  {TARGET, STOP, TIME_STOP}.
- **Hierarchy**: `proposed_order_type` → `× origin_family` → `× utc_session`,
  deepest cell meeting the fixed support rule (100 resolved attempts for LIMIT
  fill, 30 resolved fills for terminal); the level is chosen from
  prediction-time keys only, never by realized performance.
- **Licensed endpoint**: `P(target_before_stop | filled, terminal resolved as
  target-or-stop)` — the Dirichlet posterior restricted to {TARGET, STOP},
  i.e. Beta(n_target+1/2, n_stop+1/2) = (2·n_target+1)/(2·(n_target+n_stop)+2).
- Every probability is stored as **Jeffreys numerator/denominator integers**;
  decimals are derived aliases. NO_FILL is a separate execution mass,
  TIME_STOP a separate terminal mass, censored rows are coverage masses —
  none is ever folded into a loss.

Implementation: `src/research_infra/geometry_bound_outcome_model.py` (pure,
stdlib-only: fitter, packet builder, loader, atom validator). Fitter runner:
`w21_fit_geometry_bound_outcome_model_v1.py` (this directory). Artifact:
`GEOMETRY_BOUND_OUTCOME_MODEL_V1.json` — payload
`f2b74215031d4e714a06a9080adc15246f8f7831561674ca76c97d7968a1911a`, file sha256
`f27946e5d9c191ca09590147d356e03ff145922ddc3c213ad7f63e8a49eb002d` (the file
sha changes if the JSON is ever re-serialized; the payload hash is the
canonical identity and is verified on load).

## 2. Training corpus — the opened estate only

44 days, 292,987 occurrences, labeled by the committed
`candidate_funnel_analysis._lifecycle_row` (the same M1 modelled-lifecycle
labeler every prior Wave 21 read used), each day opened through its sealed
compact-event authority hash and each M1 source verified against its pinned
manifest root:

| window | days | source |
|---|---|---|
| October/November 2025 | 8 (10-27, 10-28, 10-29, **10-30**, 11-03, 11-04, **11-06**, 11-07) | raw-campaign registry (lane hold) |
| January 2026 | 16 | `w21-expanded-development-jan` roots + `LANE_INPUTS_TRUE_UTC_V1` january manifest (`8b7d3b26…`) |
| February 2026 | 20 | `w21-market-top-feb-r2` roots + february manifest (`955937e4…`) |

2025-10-30 and 2025-11-06 were the untouched days; the frozen decision read
opened them and the preregistration's `untouched_repair_rule` moved them into
development permanently. February is used-once VAL, already outcome-read by
`FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2` — training on it forfeits
nothing that was not already spent.

**Excluded by rule**: April/May 2026 (frozen read in progress —
`/private/tmp/w21-market-top-aprmay-r3` was never touched), held reserves
2025-10-31 and 2025-11-05, anything READ_RESTRICTED.

Totals: 241,684 lifecycle-resolved attempts; 64,389 resolved fills
(13,552 TARGET / 34,730 STOP / 16,107 TIME_STOP); 177,295 NO_FILL;
51,303 censored, retained as masses by reason (37,833 source-interval gap,
4,728 ordering ambiguity, 4,658 submission-bar limit touch, 2,748 geometry,
1,336 invalid gap through SL/TP).

Final fit: 254 cells (2 order-type roots, 10 order×family, 242
order×family×session); 198 cells terminal-evaluated at the 30-fill gate.

## 3. Bindings — the hash chain that makes it an authority

1. **Artifact seal**: canonical-JSON `payload_sha256` inside the artifact;
   `load_geometry_bound_outcome_model(path, expected_artifact_sha256=…)`
   verifies the file bytes against the caller's expected sha256 AND the
   internal payload seal, fail-closed.
2. **Preregistration binding**: the fitter refuses any preregistration whose
   payload hash is not the frozen `2db7e5c9…`.
3. **Corpus binding**: per-day compact root, sealed authority root sha256,
   source-manifest root sha256, and full per-day coverage counts inside the
   artifact.
4. **Geometry binding**: every training label was resolved at that candidate's
   own immutable approved entry/stop/target geometry. At consumption, the
   per-candidate packet stamps `geometry_contract_hash_sha256` equal to the
   candidate's **final post-router** target/stop geometry contract
   `packet_hash_sha256`; the disposition revalidates it and any later geometry
   change makes the packet stale (`…_stale_after_geometry_change`).
5. **Packet seal**: every per-candidate packet carries its own canonical
   `packet_hash_sha256` plus `model_version`, `model_artifact_sha256`,
   `model_payload_sha256`, decision-time action + horizon, the cell keys, the
   Jeffreys support counts, and the endpoint rationals. The validator
   recomputes every rational from the counts and every identity; one flipped
   integer breaks the seal.
6. **Caller attestation**: acceptance additionally requires the caller-passed
   `expected_model_artifact_sha256` (the timewarp wiring passes the sha it
   verified at load). Without it a structurally perfect packet is still
   refused (`…_model_artifact_unverified`) — nothing can self-declare
   economic authority.

## 4. Acceptance slot

`geometry_bound_outcome_calibration_disposition(packet, geometry_contract,
expected_model_artifact_sha256=…)` now has exactly one accepting path:
supported schema+version, packet self-hash valid, artifact sha attested and
matching, geometry hashes present and equal, decision action ∈ {LONG, SHORT}
with horizon strictly after decision time, endpoint and evidence-class strings
exact, `probability_status = EVALUATED_OUTCOME_BASELINE`, all counts/rationals
recomputed clean, and both preregistered support gates met. Result:

```
status  EVALUATED_GEOMETRY_BOUND_OUTCOME_CALIBRATION
reason  geometry_bound_outcome_calibration_all_atoms_validated
economic_authority_allowed  true
```

Everything else refuses with the original status
(`NOT_EVALUABLE_NO_GEOMETRY_BOUND_OUTCOME_MODEL`) and a specific reason —
out-of-support cells carry the exact preregistered shortfall and are **never
defaulted**. Legacy callers (two-argument form) keep today's refusal behavior
byte-for-byte; the three pre-existing reasons (`source_required`, `stale
after geometry change`, `model_version_unsupported`) are unchanged.

## 5. Honest evaluation — prequential, day-ordered, on the opened estate

Protocol: predict day *k* from days < *k* only; training labels admitted only
when `label_available_utc` is strictly before test-day UTC midnight minus the
3 h broker-calendar skew; independent leakage audit
(`trainer_folds.audit_fold_leakage`) clean over all 44 folds, 0 violations.
Day 1 has no prior data and is scored out-of-support by construction.

**Strict endpoint** (the licensed number), 47,388 scored rows of 48,282
potential (894 out-of-support), observed target rate 0.2815:

| metric | model | running base rate |
|---|---|---|
| pooled Brier | **0.20517** | **0.20247** |
| Oct 2025 (3,375 rows) | 0.22206 | 0.21290 |
| Nov 2025 (4,922) | 0.21073 | 0.20774 |
| Jan 2026 (17,530) | 0.20040 | 0.19801 |
| Feb 2026 (21,561) | 0.20514 | 0.20326 |

**Read this plainly: the cell-conditioned frequencies do NOT beat the pooled
running base rate on the strict endpoint** (pooled Brier +0.0027 worse, same
sign in all four windows). The hierarchy adds no discrimination skill at this
granularity. What the model delivers — and all it claims — is *honest,
support-gated, calibrated-by-construction frequencies with honest
uncertainty*, against a predecessor whose Brier was 0.4769 (2.5× worse than
base rate) and whose mean claimed probability was 0.78 against a 0.25 reality.

Reliability by predicted decile (pooled, support in each bin):

| bin | n | mean predicted | observed |
|---|---|---|---|
| 0.0–0.1 | 338 | 0.060 | 0.222 |
| 0.1–0.2 | 3,323 | 0.167 | 0.269 |
| 0.2–0.3 | 27,153 | 0.263 | 0.279 |
| 0.3–0.4 | 15,386 | 0.333 | 0.292 |
| 0.4–0.5 | 1,001 | 0.427 | 0.250 |
| 0.5–0.6 | 173 | 0.527 | 0.312 |
| 0.6–0.7 | 9 | 0.626 | 0.111 |
| 0.8–0.9 | 5 | 0.887 | 0.400 |

The mass (89.8 %) sits in the two central bins within 1.6–4.1 pp of the
diagonal; the extreme bins are thin, early-corpus cells whose extremity is
noise — the posterior counts travel in every packet precisely so a consumer
can see that support.

**LIMIT fill stage** (secondary, reported for completeness): 204,544 scored
rows, observed fill rate 0.1514, Brier **0.12332** vs base-rate **0.12856** —
here cell conditioning does carry signal beyond the base rate.

Backoff provenance (pooled): terminal resolved at the deepest
family×session level for 43,349 of 47,388 scored rows (91.5 %), at
order×family for 3,987, at the order-type root for 52. Per-cell coverage for
every scored cell is in the artifact
(`prequential_evaluation.per_cell_coverage`); the largest cells sit within
~1–3 pp of their predicted rates.

## 6. Default-off consumption wiring

`evaluate_candidate_v4` (timewarp loop), truth mode only, behind the explicit
runtime key `gtos_vnext_runtime.wave21_geometry_bound_outcome_model =
{path, artifact_sha256}` — **absent from every committed config**, pinned by
`test_runtime_key_is_absent_from_every_committed_config`:

- Key absent → behavior is today's, byte-identical: candidate-supplied packets
  (which can never be accepted — no attestation) or the blanket
  `source_required` refusal. A test proves no model load is even attempted.
- Key present → the artifact is loaded once and sha-verified (a wrong sha or
  malformed supply **raises** — an operator who supplied a model never gets a
  silently model-less run), the per-candidate packet is built after the final
  post-router geometry contract, dispositioned with attestation, and on
  acceptance attached under `geometry_bound_outcome_calibration` as
  `{packet, disposition}` with the four `probability_truth_*` stamps carrying
  the accepted status and `economic_authority_allowed: true` onto the
  candidate, the hash-bound live decision packet, and the result row.
- The truth-mode strip (`strip_probability_economic_authority`) preserves
  exactly one thing: an accepted wrapper that **revalidates in place** (seal +
  every atom). Tampered, refused, or unvalidated wrappers are stripped with
  everything else. The hash-bound live-packet verifier
  (`_hash_bound_probability_truth_disposition`) recognizes the consistent
  accepted group; any tamper without re-hashing still reads
  `hash_bound_probability_truth_disposition_invalid`.
- **Anti-replay**: only the wiring's own disposition may place the
  calibration key. A candidate-supplied wrapper — even a self-consistent
  replay of a previously accepted one — is popped after each strip, so it can
  never ride the output surfaces while the stamps disagree
  (`test_candidate_supplied_accepted_wrapper_cannot_ride_through`).
- **Live path byte-identical**: `book_owner.py`, `run_book.py`,
  `execution.py`, `admission.py`, `selector_v4.py` are untouched; no live
  config gained a key.

## 7. What this licenses — and what it does not

**Licensed**: honest per-cell outcome frequencies — the strict
target-before-stop endpoint with its posterior counts, the fill/no-fill
execution split, and the three-state terminal masses — as probability inputs
on the research truth path, for a candidate whose final geometry contract hash
matches the packet, from cells meeting the preregistered support gates.

**Not licensed**: EV-based admission, selection, sizing, scheduling, or any
live/broker authority. No consumer converts these probabilities into an
expected value or a decision — that requires a separate preregistered read
(the preregistration's own untouched two-arm comparison, or a successor),
which this model deliberately does not perform. The Selector still receives no
probability from this packet; attaching it changes which *disposition* rides
the row, not which trades happen. Also not licensed: any claim of
discrimination skill on the strict endpoint — §5 measures there is none over
the pooled base rate at this hierarchy.

## 8. R2 decision-contract note (CN precedent)

`src/research_infra/v4_timewarp_simulated_live_research_loop.py` is one of
R2's 43 bound `common_behavior_inputs`. This session edits it (the wiring in
§6). Per the standing CN-precedent rule recorded at wave 17 (owner word):
**any future sealed replay regenerates its decision contract first** — no
reseal attempt is made here, and none is needed while the B7.5 campaign stays
parked. The parked campaign's resume option was already dead by CJ's seal
break, as priced. `wave21_full_flow_truth.py` and the new
`geometry_bound_outcome_model.py` are bound by neither contract generation.

## 9. Tests

- `tests/research_infra/test_geometry_bound_outcome_model.py` — 11 tests:
  hand-count fixture pinning the exact Jeffreys integers (161/242 fill,
  61/163–81/163–21/163 terminal, 61/142 strict endpoint on 120 attempts /
  80 fills), prereg refusal, prequential shape + leakage, loader seal both
  directions, packet atoms, root backoff, out-of-support refusal with exact
  shortfall, disposition acceptance and five refusal modes (stale geometry,
  unattested, sha mismatch, tampered counts, low support, bad decision
  atoms), legacy behavior pins, strip carve-out in both directions.
- `tests/test_wave21_geometry_bound_outcome_wiring.py` — 6 tests: valid model
  accepted end-to-end through `evaluate_candidate_v4` (packet attached, live
  packet hash-valid, quality fields truthful, strip survival, tamper caught),
  missing cell refused out-of-support, absent key = refusal path with zero
  model loads, wrong/incomplete supply raises, candidate-supplied wrapper
  replay dropped, runtime key absent from all committed configs.
- Full existing surface: `tests/test_wave21_full_flow_truth_mode.py` (5),
  `tests/test_v4_timewarp_simulated_live_research_loop.py` (888) all pass
  with the changes.

## 10. A/B fence (full suite, failure-set identity)

`scripts/pytest_failset.py` capture at both sides in the identical context
(same sparse worktree, LFS-hydrated, `--continue-on-collection-errors`):

- **before** `2edefd48a` (origin/main): 33 bad
  (33 failed / 13,791 passed / 134 skipped / 32 xfailed)
- **after** `4acaea684` (this branch): 34 bad
  (34 failed / 13,807 passed / 134 skipped / 32 xfailed)
- diff: **unchanged 33, fixed 0, regressed 0** — the one count delta is
  `tests/test_replay_columnar_source.py::test_verification_retains_no_rows`,
  a KNOWN_LOAD_FLAKES-registered load flake (Session Y evidence; re-verified
  here: passes in isolation on this branch). Diff exit 0: **no regressions.**
- Net **+16 passing tests** (the 17 new tests minus the flake's one-run miss).
