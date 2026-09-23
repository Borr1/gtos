# Session CS — two more path-complete folds decide the inverted breaker

**Verdict: REJECT.** The fixed, default-off
`cq_current_breaker_inverted_target_5d_stop_0p25d_v1` repair remains economically positive in
January, April and May, but it does not clear the unchanged V27 all-declared significance gate.
The three-fold RECORDED / FTMO-mid run returns raw `p = 0.0025997400` and Benjamini-Hochberg
`q = 0.1533846615` against `alpha = 0.10` across 59 declared family members. Every other frozen
gate passes. The repair is therefore neither admitted nor queued, and Session CS produced no
activation dossier, ceremony authority or arming action.

Authority:
`phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json` (`self_sha256`
`60c0f50fbab2272851adcbbce12a006b8a9772c1b541c8361c9bf047ec3dd8f1`).

## 1. The decision

The additional folds answer CQ's exact stopping condition. All three chronological capture-local
folds are evaluable:

| Capture-local OOS fold | Priced OOS trades | Mean net R/trade |
|---|---:|---:|
| 2026-01-16..2026-01-30 | 1,664 | +11.252342 |
| 2026-04-16..2026-04-30 | 768 | +7.453554 |
| 2026-05-16..2026-05-30 | 487 | +3.852045 |

The equal-by-fold pooled OOS mean is **+7.519313 R**, the scored-trade mean is **+10.926325 R**
over 2,919 OOS trades, all three folds are positive, and removing the strongest fold leaves
**+5.652799 R** with 75.18% retention. Full-lifetime mean is **+12.591781 R/trade** over 6,536
priced RECORDED trades. These numbers are diagnostics under the frozen gate, not permission to
trade.

The only failed predicate is significance. The raw block-permutation evidence clears alpha, but
the V27 family bill does not: `q = 0.153385 > 0.10`. The exact terminal reason is:

> REJECT significance: q=0.1534 (raw p=0.0026) fails benjamini_hochberg at alpha=0.1 across a
> family of 59

The gate's repair queue names **BREADTH**: pool the mechanism across a genuinely declared family,
or evaluate it through the book-level diversifier door. That is a new decision path, not a reason
to relax this gate or spend another undeclared look. Session CS leaves that repair path explicit
and stops this candidate before activation.

## 2. Declaration preceded every economic read

`CS_BREAKER_FOLD_PLAN_V1.json` froze the unchanged transform, fixed entry, inverted orientation,
5D target, 0.25D stop, 120-minute horizon, RECORDED population, FTMO mid-band cost truth,
`B_balanced`, alpha 0.10, V27 all-declared multiplicity and capture-local equal-calendar folds.
It was committed at `7d2f2d4f3` before April or May economics were decoded. Its self digest is
`31b2ab756bf9be6ae19ca7f5e40447c2de7ea905839a78a921919ca3b5bb3b85`.

`CS_BREAKER_LOOK_ADDENDUM_V1.json` then declared exactly four unbilled VAL looks before either
capture ran: April S0R0 substrate, April fixed-transform fold, May S0R0 substrate and May
fixed-transform fold. It introduced no candidate hypothesis and no graduation bill. The May
source-boundary amendment was also committed before May economics: May 1–30 is the capture, while
the registry's May 31 daily pack is explicitly excluded.

The unchanged gate uses three independently captured windows—January 1–30, April 1–30 and May
1–30. The same equal-calendar builder runs inside each window; only the resulting scored slices
are concatenated. Gaps are not manufactured into empty folds, and no GateSpec threshold changes.

## 3. April capture

The authenticated April S0R0 `LANE_ITERATION` run completed in 7,043.245 seconds at
4,719,067,136 bytes max RSS. It emitted 134,489 candidates, 134,443 missed-opportunity rows,
1,914 scorecard rows, 92 orders and 40 trades. The compact reader retained 25,056 unique,
diagnostic-scoreable April rows. Eighty non-scoreable May 1 broker-day tail rows present in the raw
route did not enter the compact pool or any outcome calculation.

The frozen production transform selected 3,671 `current_breaker_re_entry` rows without rerunning
CQ's grid. Path truth was ordered ticks for 265 rows and conservative M1 for 3,406 rows, including
13 explicit tick-symbol fallbacks. Same-bar ambiguity is zero in TRAIN, OOS and full capture.
Outcomes are 2,506 TARGET, 738 STOP and 427 HORIZON. The local materialization diagnostic is
+11.476105 R/trade on TRAIN and +12.539079 on OOS before the gate's RECORDED population and
FTMO-mid repricing.

All 3,671 rows reprice through CN's FTMO broker-true commission call chain with zero unpriced rows,
zero nonidentity rows and zero maximum commission delta from CJ's repaired packets.

Authority: `CS_APRIL_S0R0_ARM_V1.json`, `CS_APRIL_S0R0_POOL_V1.json`,
`CS_APRIL_PATH_POOL_V1.json` and `CS_APRIL_CURRENT_BREAKER_REPAIR_V1.json`.

## 4. May capture

The registry's May authority spans May 1–31, but the declared evidence window ends May 30. Session
CS added a fail-closed prefix binding: it authenticates the exact 30 retained daily pack roots,
recomputes the effective source identity, permits only that one measured identity-root difference,
and excludes the May 31 pack. An empty authoritative tick manifest now means zero ticks rather
than permission to scan retired repository estates.

The successful May S0R0 `LANE_ITERATION` run completed in 5,728.976 seconds at 4,844,339,200 bytes
max RSS. It emitted 132,500 candidates, 132,445 missed-opportunity rows, 1,720 scorecard rows,
110 orders and 51 trades. The compact reader retained 21,285 unique scoreable rows, all dated in
May 2026.

The frozen production transform selected 3,371 breaker rows. May has no declared tick source, so
all 3,371 paths use conservative M1. Same-bar ambiguity is zero in TRAIN, OOS and full capture.
Outcomes are 1,832 TARGET, 865 STOP and 674 HORIZON. The local materialization diagnostic is
+12.117485 R/trade on TRAIN and +7.320861 on OOS before the gate's RECORDED population and
FTMO-mid repricing. All 3,371 rows reprice through CN's FTMO cost call chain with zero unpriced or
nonidentity rows.

Two May attempts failed before economic extraction. The first exposed a prefix source-plan binding
order defect; the second exposed the full-window prepared-pack identity bound against a shorter
prefix. Both are preserved as same-spec, unbilled error attempts. Session CS repaired forward:

- bind the source-plan digest only after the effective prefix exists;
- treat an empty tick authority as exhaustive;
- prove the registered-to-prefix prepared-pack rebind from exact daily roots and authenticated
  pack contents; and
- require that runtime proof in the May consumer before any compact or path outcome can be read.

Authority: `CS_MAY_S0R0_ARM_V1.json`, `CS_MAY_S0R0_POOL_V1.json`,
`CS_MAY_PATH_POOL_V1.json`, `CS_MAY_CURRENT_BREAKER_REPAIR_V1.json` and
`CS_MAY_S0R0_PRE_ECON_PREFIX_PACK_BINDING_ERROR_V1.json`.

## 5. Frozen gate and cost truth

The gate keeps every ratified field:

- population `RECORDED`;
- account FTMO / server `FTMO-Server3`;
- mid spread band using measured `v2_damped` era-hour composition;
- CN/CJ broker-true cost artifact SHA-256
  `bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd`;
- option `B_balanced`, alpha 0.10;
- V27 prospective all-declared family, 59 declared / 57 looks; and
- unchanged fidelity, sample, expectancy, lifetime, stability, robustness, cost-coverage and
  significance thresholds.

The RECORDED filter keeps 6,536 of 11,305 transformed rows, drops 4,769 and leaves zero
unpriceable. Coverage is 100%; 19.69% is MEASURED and the weakest surviving class is MODELLED.
The transferred per-bar fidelity ceiling is 160/167 = 95.81%; it is still not direct measured
recall for the repaired identity. No claim in this result upgrades that evidence class.

The cost decomposition across the 6,536 priced rows is 13.587786 R gross, 0.996005 R total cost
and 12.591781 R net per trade. Spread is the largest mean term at 0.730175 R, then commission at
0.240622 R, slippage at 0.016850 R and swap at 0.008357 R. The model's historical-era caveat
remains: bands narrow look-ahead but do not turn transferred historical spread regimes into
forward tick measurements.

## 6. Look accounting and safety boundary

The final receipt accounts for six CS iteration-ledger rows: four completed declared VAL looks and
two same-spec runner errors with no extracted economics. All are unbilled. The candidate family
remains 59 declared / 57 looks; the repair retains its one existing graduation bill and adds zero
new hypotheses and zero new bills.

February economics were not read. April source packs do contain March lookback substrate, as
declared, but no March decision or outcome entered a compact pool, path score, trade record or
gate. Every scored April timestamp and exit is inside April; every scored May timestamp and exit
is inside May. The receipts stamp `february_2026_economics_read=false` and
`march_2026_outcomes_read=false`.

Session CS did not access a VPS, run a broker-capable script, import a broker module, read
activation-token material, read token-bound config/profile bytes, edit config, grant live broker
authority or arm the default-off transform. The final ceremony status is `NOT_QUEUED` and
`arming_authority=false`.

## 7. Engineering delivered

This was not only an evidence run. Session CS leaves reusable, behavioral infrastructure:

- authenticated prefix views over a registered LANE window, with exact prepared-pack rebind proof;
- exhaustive empty-tick-manifest semantics, preventing undeclared retired-estate discovery;
- broker-day completeness repair for internal true-UTC fragments, guarded by both M1 and M15;
- non-contiguous, predeclared capture support in the walk-forward gate while preserving the
  unchanged equal-calendar fold builder and every GateSpec threshold;
- source-bound compact/path materialization that invokes the production transform for each
  candidate, retains composite `(candidate_id, entry_utc)` identity, and refuses February, March
  or cross-capture timestamps; and
- append-only accounting for failed same-spec pre-economics attempts.

The large raw April/May replay routes and arm economics sidecars remain machine-local. The compact
scoreable pools, path sidecars, transformed trade records, arm receipts and decision receipt are
committed and content-bound.

## 8. Verification

The focused Session-CS, LANE, train-engine, walk-forward, CK-compatibility and implementation-state
suites finish **160 passed, 0 failed, 0 errored**; pytest emits only the repository's existing
unknown-`asyncio_mode` warning. `pytest_failset.py scope` reaches 26 test files from the complete
Session-CS change set and explicitly unions the one standing failure node. Its after capture is
**583 passed, 1 skipped, 1 failed, 0 errored**. The sole bad identity is unchanged from the
committed main baseline:
`tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict`.

The tool-emitted `phase19/receipts/SESSION_CS_AB_RECEIPT.md` records **1 bad -> 1 bad, 0 fixed,
0 regressed**. The commission's “ZERO baseline” wording had drifted: the actual committed,
parse-complete baseline at `bca8c4466` is 12,705 passed / one failed, so this result reports current
disk truth rather than relabeling it zero.

## What I got wrong

I initially treated May 1–30 as if the registry's already-authenticated May 1–31 prepared packs
could be consumed under a shorter source identity without an explicit proof. They cannot: daily
pack bytes were unchanged, but the window-wide source identity was correctly different. I also
bound the CLI source-plan digest before constructing the prefix, which discarded that binding,
and allowed an empty tick manifest to fall through to a retired-estate scan. Those were real
authority bugs, not reasons to abandon the fold. I preserved both pre-economics failures, fixed the
binding order and empty-authority semantics, added an exact-subset prepared-pack proof, made the
consumer require it, and reran May successfully without spending a new look or reading a forbidden
outcome.
