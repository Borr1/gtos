# Session FE — Sol conditions and separability repair result

## Decision

**No existing condition earns a gate.** On 27,658 January true-UTC S0R0 scoreable opportunities,
the declared conditions preserve relative outcome rank but do not isolate positive cost-true edge.
There are zero TRAIN net-positive cells, zero TRAIN/HOLDOUT persistent net-positive cells, and zero
cells that survive TRAIN, HOLDOUT, the frozen February transfer, and multiplicity together.

The useful result is narrower and actionable:

- family and its family×session/hour interactions carry real information about *how negative* an
  opportunity is;
- seven January TRAIN cells are gross-positive and four remain gross-positive in HOLDOUT, but all
  four are net-negative;
- the frozen February transfer has nine gross-positive cells, zero net-positive cells, and zero
  strict survivors;
- simple timing marginals do not repair the book: gross variance for direction, session, UTC hour,
  symbol class, kill zone, and route session is indistinguishable from the declared within-day null;
- the existing compact pools omit the already as-of-safe `predecision_features` block, so FE shipped
  its exact bounded propagation as a research-only, default-off instrument rather than inventing a
  gate from negative evidence.

Every cell, split, window, and transfer in this result is `FORENSIC_DIAGNOSTIC`, `billed=false`,
with no promotion or activation authority.

## Evidence and discipline

`CONDITIONS_PROTOCOL.json` was committed in `4405ecf2c` before any new outcome aggregate. It fixed:

- January's first 13 observed dates as TRAIN (16,248 rows) and last eight as HOLDOUT (11,410 rows);
- 884 finite declared cells across family×direction×session, family, direction, session, UTC hour,
  symbol class, family×hour, kill zone, route session, and day of week;
- a 200-row TRAIN floor and 100-row HOLDOUT/February floor for a repair candidate;
- gross as `opportunity_net_proxy_r + cost_r`, net as `opportunity_net_proxy_r`;
- 999 seeded within-day paired-label permutations, with max-T family-wise adjustment across 87
  canonical eligible cells and both gross/net targets;
- max-adjusted axis η² and TRAIN-to-HOLDOUT Spearman tests;
- January-only gross/net top-5, top-10, and top-20 lists, frozen and committed before February;
- an unchanged February transfer with no selection or retuning;
- the 0.15R cost-width calculation as arithmetic only, never a path-outcome claim.

Feature-only enumeration found 119 eligible cells before collapsing 32 exact TRAIN-membership aliases,
leaving 87 canonical inferential identities. All 27,658 January and 24,239 February composite row
identities are unique. `LOOK_MANIFEST.json` is the complete unbilled look ledger.

The sources are compact true-UTC S0R0 pools from CJ (January, SHA-256 `ee920fb0…fc8f`) and CP
(February, SHA-256 `d89202…6b12`). FE did not read March 2026 or live-forward outcomes.

## January: rank persists, profitability does not

TRAIN-to-HOLDOUT rank persistence is real after the declared maximum adjustment:

| target | Spearman ρ | max-adjusted one-sided p | interpretation |
|---|---:|---:|---|
| gross | 0.443847 | 0.002 | moderate preservation of gross ranking |
| net | 0.894602 | 0.001 | strong preservation of cost-true ranking |

That is not an edge claim. The stable ordering sorts less-bad from worse opportunities: **7**
TRAIN cells have positive gross mean, **0** have positive net mean; **4** stay gross-positive in
HOLDOUT, **0** stay net-positive. The January freeze therefore said
`NO_JANUARY_NET_POSITIVE_CELL`, while still carrying the unchanged frozen lists to February.

Axis-level maximum-adjusted results sharpen the repair map:

| axis | gross η² / adjusted p | net η² / adjusted p | result |
|---|---:|---:|---|
| family | 0.06034 / 0.001 | 0.08684 / 0.001 | informative |
| family×direction×session | 0.01558 / 0.001 | 0.04930 / 0.001 | informative |
| family×hour | 0.01242 / 0.002 | 0.11754 / 0.001 | informative |
| session | 0.00698 / 0.148 | 0.05501 / 0.001 | gross-noise; cost creates net separation |
| kill zone | 0.00711 / 0.136 | 0.05183 / 0.001 | gross-noise; cost creates net separation |
| UTC hour | 0.00596 / 0.290 | 0.02471 / 0.001 | gross-noise; cost creates net separation |
| route session | 0.00402 / 1.000 | 0.04085 / 0.001 | gross-noise; cost creates net separation |
| symbol class | 0.00321 / 1.000 | 0.11359 / 0.001 | gross-noise; cost creates net separation |
| direction | 0.00003 / 1.000 | ~0 / 1.000 | indistinguishable on both |
| day of week | 0.00185 / 1.000 | 0.00408 / 0.796 | not resolved by this null |

The day-of-week result has an important limit: within-day permutations cannot move a day-level label
between weekdays. Its p=1 is permutation invariance, not evidence that weekday effects are absent.
Resolving that axis requires more weeks and a day-level resampling design.

## Gross-positive frontier and the cost burden

Four canonical cells have at least 200 TRAIN rows, 100 HOLDOUT rows, and positive gross mean in both
splits. None has positive net mean. Width figures below scale the observed cost arithmetic only;
changing a stop changes path geometry and gross outcomes, which FE did not recompute.

| frozen cell | Jan TRAIN gross / net | Jan HOLDOUT gross / net | Jan mean cost | share cost ≤0.15R | p90 width, fixed slippage | Feb gross / net |
|---|---:|---:|---:|---:|---:|---:|
| current FVG fill · SHORT · London | +0.2440 / -0.2161 | +0.0247 / -0.2410 | 0.3887 | 48.84% | 8.596× | +0.0403 / -0.2044 |
| liquidity sweep reclaim · LONG · London | +0.0074 / -0.3456 | +0.1762 / -0.0788 | 0.3184 | 27.60% | 4.794× | +0.1099 / -0.2282 |
| liquidity sweep reclaim · SHORT · London | +0.0398 / -0.3059 | +0.1068 / -0.1678 | 0.3217 | 23.47% | 4.765× | -0.1278 / -0.4763 |
| displacement continuation · 14:00–15:00 UTC | +0.0355 / -0.2515 | +0.1271 / -0.0793 | 0.2569 | 51.56% | 4.766× | +0.1858 / -0.0242 |

Only the current-FVG cell has positive January mean gross minus a hypothetical flat 0.15R cost
(+0.01349R). Even that cell transfers at -0.20444R net in February and -0.32458R under the declared
cost-integrity sensitivity. The closest February frontier cell is displacement at 14:00–15:00 UTC,
but it remains -0.02417R net and -0.03854R under sensitivity. Stop widening is therefore a priced
hypothesis requiring path recomputation, not an FE repair.

## Frozen February transfer

Commit `5034b73d3` froze selection digest
`48152ec75a36dc8591d5156d3da44a065f02111a9a7d69caec154027e6457099` before February. The union of
the January top lists contains 26 unique cells. February was attribution only: no rule, threshold,
rank, top-k membership, or cell was selected or retuned on it.

| frozen union | n | February gross mean | February net mean | sensitivity net mean |
|---|---:|---:|---:|---:|
| gross top 5 | 2,018 | -0.01366 | -0.27901 | -0.31354 |
| gross top 10 | 3,119 | -0.01761 | -0.38810 | -0.46275 |
| gross top 20 | 10,884 | -0.09072 | -0.51844 | -0.57969 |
| net top 5 | 5,604 | -0.07843 | -0.22096 | -0.22869 |
| net top 10 | 7,670 | -0.03798 | -0.19868 | -0.19604 |
| net top 20 | 13,046 | -0.05913 | -0.31390 | -0.33721 |

At cell level, nine frozen cells are gross-positive, zero are net-positive, zero are both, and zero
meet the strict survivor conjunction. This is transfer failure, not permission to search February.

The first transfer invocation failed closed before any cell aggregate because recomputing gross from
an eight-decimal stored net exposed differences just over the predeclared 1e-9 tolerance. The
arithmetic-only reconciliation counted all 24,239 rows: 16,560 exceed 1e-9, none exceed 5e-9, and
the maximum is 4.99998265e-9. `FEB_GROSS_IDENTITY_RECONCILIATION.json` was committed before grouping
or sign analysis and authorizes exactly 5e-9 without changing any metric, cell, threshold, or rank.

## Safe higher-information implementation

Because no declared condition survives, FE did not implement a candidate gate. Commit `a86976b14`
adds `condition_feature_propagation` to the unbound train-engine patch registry:

- it copies exactly the 15 existing `PREDECISION_FEATURE_KEYS` fields into missed-pool telemetry;
- it accepts only scalar, finite values (plus `None`), drops unknown/nested/nonfinite values, and
  records completeness/error counts;
- missing or malformed telemetry cannot suppress candidate generation;
- the candidate input, composite identity, geometry, costs, and outcomes are unchanged;
- it wraps the R2-bound timewarp helper at runtime and restores the exact original function on revert;
- it is absent from `TRAIN_DEFAULT_PATCHES` and `TRAIN_SAFE_SET_PATCHES`;
- only explicit `--patches safe+conditions` enables it, and the manifest marks the output
  sealed-incompatible.

This instrumentation changes one decision: the next bounded TRAIN capture can test volatility,
geometry, trend transition, structural distance, compression, session age, and sweep depth without
another schema blind spot. It grants no present outcome or gate claim. The capture requirement is
now exact: after CS releases the shared heavy slot, run the same authorized TRAIN prefix with `safe`
and `safe+conditions`, demand identical composite identities/economics, record projection-status
counts, then predeclare bins or a learner family before reading its outcomes.

No full replay was launched. The frozen timewarp bytes were not edited; none of FE's edited source
or test paths is R2-bound. The checker still reports the inherited CN engine break and two known
ledger-materialization rows, and `git diff f8c05d0ac --` those paths is empty.

## Verification and artifact map

- Focused condition/analyzer behavior: **17 passed**.
- Train-lane projection blast radius: **102 passed** after materializing the committed broker-cost
  fixture; no broker capture was run.
- Tool-derived final FE scope: **129 passed, 0 failed, 0 errored**; this includes the
  implementation-state citation guard.
- `SESSION_FE_AB_RECEIPT.md`: committed 12,705-pass suite baseline with its one registered
  order-sensitive load flake → scoped zero bad, **0 regressed**. The flake's non-recurrence is not
  attributed to FE.
- `py_compile` and `git diff --check`: pass. Black is not installed in this environment.

Primary artifacts live under
`research/operations/wave19_sol_repair_2026_08_01/conditions/`:

- `CONDITIONS_PROTOCOL.json` — pre-analysis contract;
- `CELL_MAP_JAN.json` — all January cell×split metrics;
- `RANK_PERSISTENCE.json` — max-adjusted cell/rank/axis inference;
- `FROZEN_JAN_SELECTIONS.json` — immutable January top-k surface;
- `FEB_TRANSFER.json` — unchanged February transfer and survivor conjunction;
- `GROSS_POSITIVE_FRONTIER.json` — four-cell arithmetic cost frontier;
- `NEGATIVE_SPACE.json` — axis repair map and predeclared instrumentation boundary;
- `LOOK_MANIFEST.json` — complete unbilled look accounting;
- `CONDITION_FEATURE_INSTRUMENTATION_RECEIPT.json` — implementation and next-capture contract.

## Residual unknowns

1. The 15 propagated predecision fields have not yet been captured on a bounded training run, so
   their separability is unknown—not negative.
2. Day-of-week needs additional weeks and a between-day null; this study cannot resolve it.
3. The arithmetic width frontier does not say what wider stops do to fills, excursions, exits, or
   gross outcome geometry.
4. February is consumed for fixed attribution and cannot be reused to select any of those repairs.
5. March 2026 and live-forward outcomes remain unread and sealed from FE.

## What I got wrong

1. The original 1e-9 gross identity tolerance assumed the producer retained enough precision for an
   exact double recomputation. It stores net at eight decimals. The first February run correctly
   failed before grouping; I measured the rounding lattice and committed the narrow 5e-9
   reconciliation instead of silently loosening it.
2. A day-of-week p-value of 1 initially looks like strong negative evidence. Under within-day label
   permutations it is mechanically invariant. I carried it as unresolved and specified the
   higher-information day-level design.
3. Strong net-rank persistence looked superficially promising. The sign audit shows it is stable
   ordering inside a wholly negative surface, not ex-ante profitable selection. The repair is more
   informative features, not a threshold on the present ranks.
4. The general test-data hydrator did not include the committed 2026-07-27 broker-cost directory.
   I followed the repository's exact sparse-checkout remedy and reran the identical test scope,
   rather than treating three missing-fixture errors as code failures or recapturing broker truth.
