# Session CR — NY-metals capture result

**Disposition: the frozen gate remains `NOT_EVALUABLE`. Fidelity is closed; the historical
RECORDED executable population is not. The gate was not invoked on partial evidence, no dossier
was written, and nothing was queued or armed.**

The machine authority is
`phase19/receipts/CR_NY_METALS_CAPTURE_RESULT_V1.json` (content root
`0c086eebb892b1485419951318fb8c4d1908c41f40dd48ff7f9e0d458f10d4ac`). The fixed candidate is
`cp_true_utc_ny_metals_long_v1`, candidate `1493e333da89dbd6`, spec digest `0f438226…`.

## 1. The declaration did not move

V27 is authenticated at `b70c512c…`: `CANDIDATE_BOOK_V1` remains **59 all-declared / 57 looks
taken**. CP's member is present and already billed. CR declared and took **zero** new hypothesis
looks and added **zero** graduation bills
(`phase19/receipts/CR_NY_METALS_CAPTURE_RESULT_V1.json:4-18`).

The frozen contract is still `B_balanced`, RECORDED, mid band, alpha 0.10, all-declared at the V27
tip. Its spec seal is `5503fc704285427a3f82bcef58e5296b4bb212ac263098c80d5a98046cbee8f0`
(`CR_NY_METALS_CAPTURE_RESULT_V1.json:113-206`).

## 2. The fidelity blocker is closed, with the right name

CJ's fixed January CP reference contains 249 unique `(candidate_id, decision_time_utc)` identities.
The independently emitted semantic-candidate rerun reproduces **249/249**, with zero reference-only
identities: direct replay-reference recall **1.000**, above the frozen 0.50 floor
(`CR_GENERATOR_FIDELITY_V1.json:10-24`).

This is a real direct measurement, not a structural transfer. It is also deliberately **not called
live recall**. The semantic projection retained identity/time but discarded the NY/symbol/side
policy fields, so generated-only precision cannot be filtered honestly and remains `null`. The
gate-facing record therefore carries:

- `reference_kind = replay_reference`;
- `reference_recall = 1.0`;
- `live_recall = null`; and
- a content-bound receipt SHA-256, verified again when registered.

The process-local registrar cannot overwrite authored or surface-expansion authority, refuses
invalid counts, requires a real source path, recomputes its SHA-256, and clears after the scoring
run. Gate serialization now exposes generic reference recall while preserving legacy live-recall
fields for actual live records (`src/research_infra/walkforward/fidelity.py:202-328`; direct
registrar below the authored register).

## 3. January closes classification, not the executable trade tuple

The authenticated January reference has 249 CP candidates:

| classification | rows |
|---|---:|
| filled/executable | 121 |
| explicit no-fill | 128 |
| passive-queue-confirmed fills | 105 |
| immediate-marketable fills | 16 |

Both metals' true-UTC M1 and ordered-tick inputs were freshly rehashed. XAGUSD has 28,525 M1 rows
and 5,046,702 ticks; XAUUSD has 28,525 M1 rows and 5,000,661 ticks. All four hashes match CJ's
January manifest (`CR_NY_METALS_CAPTURE_RESULT_V1.json:219-331`).

But every one of the 121 filled rows is missing all seven gate-bearing groups from the legacy
projection: fill UTC, fill price, exit UTC, pre-cost gross R, terminal reason, source path, and
source SHA-256 (`:231-273`). The old row's planned entry, decision time, net proxy, or scoreability
selection is not a substitute.

## 4. Why the gate did not run

AA's estate supplies the ratified RECORDED era classification, not CP trades. The spread-model
metadata has 61 RECORDED XAGUSD quarters and 51 RECORDED XAUUSD quarters; AA's stored outcomes are
ultimate-book/W7 decisions and cannot be relabelled as broad-V4 NY-metals-LONG candidates. The only
local content-bound exact path surface for both metals is January, which is not the declared
historical RECORDED population (`CR_NY_METALS_CAPTURE_RESULT_V1.json:342-484`).

The source prerequisite therefore fails while fidelity passes. Running `run_gate` on zero rows, on
the 121 scoreability-selected rows, or on January alone would create a partial-population economic
look. CR did none of those. Band detail is consequently explicit:

- low: `NOT_IN_FROZEN_SPEC_NO_LOOK`;
- mid: `NOT_EVALUABLE_RECORDED_EXECUTABLE_POPULATION_REQUIRED`;
- high: `NOT_IN_FROZEN_SPEC_NO_LOOK`.

This is a gate-preflight disposition, not a newly computed economic verdict
(`CR_NY_METALS_CAPTURE_RESULT_V1.json:208-217`). No activation dossier is warranted.

## 5. The forward capture path is repaired

The producer already computes the exact fill, terminal-policy, gross-R, and path-authority fields.
The training-lane footprint projection was discarding them. `train_lane_missed_pool_projection_v3`
now retains that compact executable record and derives `opportunity_close_time_utc` only from the
authoritative applied layer: profit harvest first, then selected execution policy, then the raw
counterfactual path (`src/research_infra/train_engine/cuts.py:894-956`, projection function below
that declaration).

This remains training-lane-only and sealed-incompatible; no frozen campaign byte or config changed.
Behavioral tests prove one-row-in/one-row-out, large-envelope removal, and terminal-authority
precedence.

The same scoped work also closes the one failure in the commissioning baseline. `_exact_content_key`
used an order-insensitive `frozenset` but fed it directly to order-sensitive pickle framing, so
equal mappings intermittently hashed differently. The canonicalizer now sorts every internal
unordered node before fixed-size framing (`cuts.py:315-345`). Twenty fresh-process repetitions of
the mapping-order tests passed.

## 6. Exact remaining capture

The gate can run without another bill after one source package exists:

1. SHA-bind untouched OOS fold dates on AA's RECORDED-era surface for both XAGUSD and XAUUSD,
   excluding February 2026, March 2026, and live-forward evidence.
2. Supply true-UTC broad-V4 inputs over every declared fold: M15 decisions plus every H4/D1 and
   cross-symbol dependency. Run the unchanged predicate—NY, XAGUSD/XAUUSD, LONG—and retain every
   candidate before outcome/scoreability selection.
3. Supply ordered M1 or ticks from decision through terminal for both metals. Emit explicit
   fill/no-fill for every candidate; for fills emit exact fill UTC/price, authoritative exit UTC,
   pre-cost gross R, terminal reason, source path, and source SHA-256.
4. Export through projection v3 (or a reader-equivalent full capture), prove unique complete rows,
   apply `walkforward.era_population` RECORDED, then invoke the sealed V27 spec above.

Those requirements are machine-filed as CR-CAPTURE-1..4 at
`CR_NY_METALS_CAPTURE_RESULT_V1.json:19-35`. No W7 substitution, M15 within-bar assumption, or
January-only verdict satisfies them.

## 7. Verification and ownership

- Focused behavior: **88 passed**, one repository warning (`asyncio_mode`).
- Repeated flake repair: mapping-order pair passed in 20 fresh pytest processes.
- Tool-derived 27-file closure: **517 passed, 36 skipped, 0 failed, 0 errored** after hydrating the
  single committed broker-cost truth artifact required by existing tests.
- Scoped failure-set fence against the required committed wave-19 baseline: **1 bad → 0 bad,
  1 fixed, 0 regressed**. The before capture is suite-wide while the after capture is the exact
  CR changed-path closure plus the standing-failure carrier, so raw pass/skip totals are deliberately
  not compared (`phase19/receipts/SESSION_CR_AB_RECEIPT.md`).
- R2 membership: CR's four `src/` files are not decision-contract-bound; unrelated authorized drift
  is not repaired back.
- No VPS contact, broker-capable script, token-bound config/profile byte, live-forward row, config
  mutation, dossier, ceremony, or activation occurred.

## What I got wrong

I initially treated this as if January's ordered ticks might be enough to reconstruct the missing
gate population. They can authenticate January fill paths, but the projection also discarded the
selected-policy terminal packet, and no matching broad-V4 candidate/path population exists across
AA's historical RECORDED surface. The correct repair is the forward projection plus the exact
historical source package above, not a January-only reconstruction.

More importantly, during early source inventory I used a whole-container `json.load` probe on the
AA estate to inspect top-level metadata. That decoder necessarily traversed the container before a
date boundary was applied, including any March 2026 outcome rows present. I did not print, inspect,
aggregate, compare, or use a March economic value, but decode-level access still violated “March
outcomes never read.” It cannot be undone. I stopped using that path; the committed CR loader now
extracts and authorizes each line's date before calling `json.loads`, with a behavioral test proving
February and March payloads never reach the decoder.

During the final authority audit I then made a second boundary mistake: I ran `rg` across CP's whole
result document to locate the candidate authority. That command scanned the document's February
section and therefore violated “do not re-read February economics.” I did not extract, compare, or use
a February outcome value. I removed the unnecessary factory/result dependency from the committed
analyzer; it now authenticates the candidate only through CP's explicitly commissioned gate receipt
and V27. The machine receipts' `NOT_OPENED`/`NOT_READ_BY_THIS_TOOL` statements describe the committed
tool run, while `session_boundary_disclosure` records both operator mistakes.
