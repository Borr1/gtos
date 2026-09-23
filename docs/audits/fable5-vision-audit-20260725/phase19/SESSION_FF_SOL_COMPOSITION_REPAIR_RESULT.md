# Session FF — Sol eligibility and composition repair result

## Verdict

**COMPLETE_ATTRIBUTION_NO_PROMOTION.** The January and February funnel, family-tension,
probe-conversion, capacity, and February authority puzzles are reconciled to their physical
denominators. The evidence does **not** license an FVG family gate, family cap, rank change,
late-market conversion, or authority relaxation.

The demonstrated defect was narrower: both train-lane scorecard projections discarded the exact
hard-eligible set and its per-window rank rows after the finalizer computed them. Session FF added
an explicit `hard_eligibility_observability` patch that validates and preserves those producer
fields. It is default-off, absent from both default and safe patch sets, training-lane-only, and
sealed-incompatible. It does not backfill the two existing arms and does not alter selection,
sizing, execution, costs, or outcomes.

No March 2026 or live-forward outcome was read. February was used once for attribution only under
`owner_mandate_20260801`. No replay, VPS, broker, token, live service, promotion, or activation
surface was touched.

## Evidence control and denominators

Every join used `candidate_id + decision_time_utc + symbol + side_or_direction`. Candidate ID alone
was rejected because it is not unique on the commissioned surfaces. Large JSONL inputs were
streamed; the final analysis took 13.12 seconds, 610,435,072 bytes maximum RSS, and 600,097,608
bytes peak memory footprint.

| population | January | February |
|---|---:|---:|
| source/pool rows | 153,486 | 129,231 |
| scorecard candidate sum | 153,486 | 129,231 |
| cost-executable rows | 25,193 | 13,762 |
| selector-pass rows | 13,503 | 8,341 |
| scheduler-materialized rows | 8,642 | 5,054 |
| scorecard all-options-preserved sum | 10,925 | 7,303 |
| scorecard order-executable probe sum | 5,145 | 2,462 |
| compact scoreable pool rows | 27,658 | 24,239 |
| selected probes | 61 | 66 |
| filled trades | 57 | 58 |

Pool rows equal the scorecard candidate sums in both months. Selected probes equal accepted ORDER
rows, and `selected - terminal unconverted = physical TRADE rows` in both months. The source paths,
byte hashes, row counts, evidence roles, look declarations, and output hashes are frozen in
`composition/LOOK_MANIFEST.json`.

## 1. FVG and XAUUSD enrichment

### `current_fvg_fill`

| observable stage | January n / total (share) | February n / total (share) |
|---|---:|---:|
| pool | 89,936 / 153,486 (58.596%) | 74,561 / 129,231 (57.696%) |
| cost executable | 9,158 / 25,193 (36.351%) | 6,123 / 13,762 (44.492%) |
| selector pass | 6,287 / 13,503 (46.560%) | 4,309 / 8,341 (51.660%) |
| scheduler materialized | 954 / 8,642 (11.039%) | 971 / 5,054 (19.213%) |
| hard eligible | **unobserved; bounded only** | **unobserved; bounded only** |
| neutral ranked | **unobserved** | **unobserved** |
| selected | 24 / 61 (39.344%) | 49 / 66 (74.242%) |
| filled | 21 / 57 (36.842%) | 42 / 58 (72.414%) |

The observable enrichment products are 0.628752 in January and 1.255094 in February and reproduce
the filled shares exactly. Cost execution de-enriches FVG in both months; scheduler materialization
de-enriches it again; fill conversion also de-enriches it. The large positive jump is between
scheduler materialization and S0 selection (3.564x January, 3.864x February), precisely where the
discarded hard-pool and neutral-rank evidence prevents a causal partition.

The filled FVG slice is economically poor: January has 21 physical rows, 20 scoreable, and
-12.263583 net R; February has 42/42 scoreable rows and -5.783454 net R. The corresponding non-FVG
slices are +6.757375 and +1.822056 net R. That describes executed composition; it does not identify
an outcome-safe family gate because S0 is an outcome-blind neutral hash and the missing hard/rank
partition cannot be reconstructed honestly.

### February XAUUSD

| observable stage | n / total | share |
|---|---:|---:|
| pool | 6,515 / 129,231 | 5.041% |
| cost executable | 5,435 / 13,762 | 39.493% |
| selector pass | 3,748 / 8,341 | 44.935% |
| scheduler materialized | 1,347 / 5,054 | 26.652% |
| selected | 44 / 66 | 66.667% |
| filled | 40 / 58 | 68.966% |

The 13.679943x pool-to-fill product reproduces the final share. Cost authority creates the largest
concentration, and scheduler-to-selection creates another 2.501x jump. Yet February XAUUSD is
gross-positive (+0.950208 R) and net -1.594567 R, while all other symbols are gross-negative
(-0.746289 R) and net -2.366832 R. XAUUSD concentration is therefore measured but is not evidence
of a uniquely toxic symbol gate.

**Repair decision:** no FVG or XAUUSD economic gate was implemented.

## 2. Breaker and structural family tension

Uncertainty uses 20,000 day-cluster bootstrap draws with seed `20260801`; win shares use Wilson 95%
intervals. Pool comparators are scoreable, non-selected rows of the same family and exact decision
window as the executed row for the paired test. All 115 physical trade rows have execution entry
equal to the executable fill, so the sign tension is not an entry-price-convention artifact.

| month/family | non-selected pool n, mean R [95% CI] | executed physical/scoreable n, mean R [95% CI] | matched choice-set n, executed-minus-peer mean [95% CI] |
|---|---|---|---|
| Jan breaker | 4,263, -1.4680 [-1.6705, -1.3179] | 9/8, +0.5445 [-0.3748, +1.4469] | 8, +1.9200 [+0.8624, +2.9135] |
| Jan structural | 1,993, -1.4128 [-1.6485, -1.1934] | 7/7, +0.4998 [-0.6276, +1.9542] | 7, +0.6636 [-0.2449, +2.5253] |
| Feb breaker | 2,375, -1.0628 [-1.1632, -0.9228] | 3/3, +0.4060 [+0.0249, +0.6741] | 2, +0.9471 [+0.6627, +1.2315] |
| Feb structural | 1,806, -1.2393 [-1.3758, -1.1000] | 1/1, +1.1697 [single row] | 0, not estimable |

The broad pool signs are dominated by marketability-unknown and high-cost rows. Conditioning on
cost, fillability, and the exact contemporaneous family choice set removes much of that population
mismatch. January breaker selection did land on better same-window peers in seven of eight paired
rows, but eight January pairs and two February pairs cannot establish a forward family-ranking
rule—especially under an outcome-blind S0 selector. Structural evidence is still less determinate.
The complete cost, fillability, path, paired-row, bootstrap, and binomial tables are in
`composition/FAMILY_TENSION.json`.

**Repair decision:** no breaker preference, structural preference, or family cap was implemented.

## 3. Probe conversion

| month | selected | filled | unconverted | exact classification |
|---|---:|---:|---:|---|
| January | 61 | 57 | 4 | 4 true no-touch expiries |
| February | 66 | 58 | 8 | 7 true no-touch expiries; 1 same-symbol lifecycle replacement |

All eleven true no-touch expiries had zero limit touches before expiry. Their guarded late-market
fallbacks were correctly refused: nine exceeded thesis adverse-drift geometry, one fell below the
expected-net-R floor, and one fell below the effective-target-R floor. Assigning them zero outcome
or entering later at market would change the ordered policy, so their economic counterfactual is
not identified.

The twelfth row was a February XAUUSD short FVG order cancelled for a same-symbol replacement. Its
guarded-fallback ordered-path counterfactual was -0.064425 net R; the replacing XAUUSD long FVG order
filled and returned +0.695137 net R. No missing trade was invented.

FVG fill conversion de-enriches the family in both months: 21/24 (87.5%) versus 36/37 (97.3%) for
other families in January, and 42/49 (85.7%) versus 16/17 (94.1%) in February. Predecision execution
fill probability also separates filled from unfilled rows (0.8629 vs 0.5838 January; 0.8037 vs
0.6303 February). That is a fillability signal, not a realized-outcome estimate for never-filled
orders. The claimed “fill-selection adverse bias” is therefore **not identifiable** for true
no-touch limits under the existing policy.

**Repair decision:** no late-market fallback or fill-conversion rule was implemented.

## 4. Capacity and one-position-per-window

January's selected-probe distribution is 1,956 zero, 59 one, and one two-probe window. February is
1,854 zero and 66 one-probe windows. A strict one-position/window cap is falsified by the January
16:15 UTC window: the finalizer explicitly admitted an XAGUSD short FVG as package extra slot two
with prior count 1, maximum count 2, next risk 0.20% under a 0.25% ceiling, and transfer score
0.05345 above the 0.02 floor. The evidence boundary says the decision was predecision and used no
outcome fields.

The exact hard pool is not present, so only honest bounds are available:

| bound | January | February |
|---|---:|---:|
| hard-eligible candidates | [61, 8,642] | [66, 5,054] |
| hard-eligible windows | [60, 1,439] | [66, 1,297] |
| eligible windows with no selected probe | [0, 1,379] | [0, 1,231] |

The similarly named `risk_finalizer_reason` surrogate is invalid: it marks 142 January and 73
February no-selection windows as passing. Direct observed competition supplies only a lower bound
of 10 candidates across nine January windows and three candidates across three February windows.

Observed selected-row capacity never exhausted the daily budget (maximum accepted daily risk 0.30%
January, 0.20% February). Selected rows carried prior pending risk in 1/61 January and 5/66 February
cases; selected windows coexisted with open positions in 9 January and 8 February cases. Exact
zero-probe stand-down counts were:

| status | January | February |
|---|---:|---:|
| no risk-admitted candidate | 162 | 49 |
| quality blocked | 53 | 24 |
| zero-trade, no risk-admitted candidate | 1,601 | 1,684 |
| zero-trade quality blocked | 140 | 97 |

These counts explain observed stand-downs but cannot say how often the lost hard-pool headroom made
target count binding.

**Repair decision:** no capacity increase or position-count change was implemented.

## 5. February authority and authoritative executed-family table

February `cost_missing` has 5,876 rows, all
`scheduler_materialization_skipped_selector_not_risk_bearing_cost_missing`: UKOIL_cash 2,532,
USOIL_cash 1,988, and GER40 1,356. Of these, 2,259 have a diagnostic opportunity R and 3,617 are
path-auditable but R-unscoreable. Family and session decompositions are preserved in
`composition/CAPACITY_CENSUS.json`; the absence of broker-comparable cost authority remains an
upstream input fact, not permission to price at zero.

`session_authority` has exactly two rows. Both are XAUUSD long FVG candidates in
`moonshot_h10_11`, and both are `same_symbol_lifecycle_veto` cases. There is no generic February
session-authority hole to relax.

| month/family | physical n | scoreable n | gross R | cost R | net R |
|---|---:|---:|---:|---:|---:|
| Jan breaker | 9 | 8 | +4.806310 | 0.497559 | +4.355751 |
| Jan FVG | 21 | 20 | -10.242868 | 2.138023 | -12.263583 |
| Jan session open range | 20 | 20 | +0.233506 | 1.330602 | -1.097097 |
| Jan structural | 7 | 7 | +3.982123 | 0.483402 | +3.498721 |
| **Jan total** | **57** | **55** | **-1.220930** | **4.449587** | **-5.506208** |
| Feb breaker | 3 | 3 | +1.493056 | 0.275126 | +1.217930 |
| Feb FVG | 42 | 42 | -2.631910 | 3.151544 | -5.783454 |
| Feb session open range | 12 | 12 | +0.100940 | 0.666532 | -0.565592 |
| Feb structural | 1 | 1 | +1.241833 | 0.072115 | +1.169718 |
| **Feb total** | **58** | **58** | **+0.203919** | **4.165318** | **-3.961399** |

Cost R covers every physical row; gross and net R cover scoreable rows, so the January columns with
unscoreable trades are not an arithmetic identity.

This is the authoritative physical-TRADE table. In particular, January FVG is 21 physical rows,
not the 20-row scoreable projection.

## 6. Narrow repair

`src/research_infra/train_engine/cuts.py` now registers the explicit
`hard_eligibility_observability` patch. When selected, it lifts these already-computed finalizer
fields before scalar scorecard projection drops the nested container:

- exact hard-eligible count;
- producer digest;
- sorted canonical instance keys; and
- compact hard-eligible option rows, including neutral rank and finalizer rank fields.

The projector fails closed on partial fields, invalid counts, blank/duplicate/unsorted identities,
option-key disagreement, or digest disagreement. Non-factorial and missing-source rows remain
explicitly distinguishable. It deep-copies producer containers, composes with scalar projection in
either wrapper order, and preserves the prior scalar shape when absent.

The patch is not in `TRAIN_DEFAULT_PATCHES` or `TRAIN_SAFE_SET_PATCHES`. It can only be selected
explicitly (including the `safe+hard-eligibility-observability` alias), reports
`sealed_compatible=False`, and never touches the sealed replay path. Existing January/February
artifacts remain honestly marked `NOT_IDENTIFIABLE`; the repair affects only future explicitly
commissioned train-lane emissions.

## Verification

- Focused tests: 51 passed in `test_train_engine_cuts.py` (43 parent tests plus 8 new outcomes).
- Scoped clean A/B over four train-engine test files: **102 passed / 0 bad → 110 passed / 0 bad;
  zero regressed node IDs**. See `phase19/receipts/SESSION_FF_SCOPED_AB.md`.
- A/B receipt contract: 4 passed.
- Analyzer compile, repair compile, JSON parse/hash reconciliation, and `git diff --check`: passed.
- R2 binding check: both changed implementation paths are unbound. R2 already reports three drifted
  inputs at the session start (`broker_net_cost_engine.py` and two sleeve ledgers); all three are
  unchanged from starting HEAD `f8c05d0ac`. Session FF therefore makes no new decision-contract
  drift claim and does not represent the pre-existing R2 state as clean.
- No full replay was run or needed for this observability-only, default-off repair.

## Residual unknowns and exact next evidence

1. The exact historical hard-eligible and neutral-rank partitions cannot be recovered from the two
   scalar-projected arms. A future explicitly commissioned train-lane run with
   `hard_eligibility_observability` selected is the exact evidence needed.
2. True no-touch orders have no policy-consistent terminal trade R. Measuring a late-market entry
   requires a preregistered policy arm, not retrospective imputation.
3. Same-window family-pair samples are tiny (Jan breaker 8, Jan structural 7, Feb breaker 2, Feb
   structural 0); no family rank rule is supported.
4. The 5,876 February cost-missing rows need broker-comparable cost inputs before executable
   eligibility can be evaluated. Zero-cost substitution is forbidden.
5. March remains sealed and unread. Nothing here authorizes promotion, activation, or a live claim.

## Artifacts and commits

- Analysis controls and manifest: `96701822a`
- Attribution outputs and analyzer: `96659451b`
- Default-off observability repair: `d52e48b2d`
- Clean scoped A/B receipt: `aeec8e4d7`
- Required machine-readable outputs: `research/operations/wave19_sol_repair_2026_08_01/composition/`
- Run receipt: `phase19/receipts/SESSION_FF_ANALYSIS_RUN.json`
- A/B receipt: `phase19/receipts/SESSION_FF_SCOPED_AB.md`
