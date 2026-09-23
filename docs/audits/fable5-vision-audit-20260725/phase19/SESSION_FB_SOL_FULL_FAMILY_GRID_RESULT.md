# Session FB — full-family geometry finds two repairs, not a family kill

Session FB · Wave 19 · Blocks B3100–B3149 · branch `phase19/sol-grid`

## 1. Result

The full January family grid closes the missing Session-FA mechanism surface. The broad family is
not uniformly wrong and is not abandoned. Two unique repairs survive TRAIN-only geometry
selection, untouched HOLDOUT persistence, conservative path scoring, broker-true cost, both
directions, and the seeded 999-draw within-day fixed-leader max-T control:

1. reuse CQ's existing `current_breaker_re_entry` inversion at fixed entry, target 5D, stop 0.25D;
2. add `current_ob_retest` **without** inversion at fixed entry, target 1.5D, stop 0.25D.

Both have family-wise max-T `p=0.001`, the 999-draw resolution floor. The six positive population
rows are hierarchical evidence—family plus LONG plus SHORT—and deduplicate to these two transform
identities (`FAMILY_CLASSIFICATION.json:3801-3836`). The breaker implementation already exists and
was not duplicated. The OB-retest transform is now implemented in the research lane only,
explicit-argument enabled, default-off, outcome-field fail-closed, and has no runtime or config
wiring (`src/research_infra/current_ob_retest_geometry_candidate.py:21-32,86-134,145-212`).

This is a repair result, not an admission. No candidate was promoted, billed, queued, armed, or
activated. March and live-forward outcomes remain unread. February was opened only after the
January identities were committed and is attribution-only under `owner_mandate_20260801`; it did
not select either geometry.

## 2. Protocol and evidence integrity

`GRID_PROTOCOL.json` was committed before Session FB computed a new outcome. It fixed the 11
targets, nine stops, two orientations, first-13/last-8 split, count-only eligibility, conservative
M1 rule, bid/ask tick semantics, geometry-correct cost repricing, classifications, 999-draw seed,
February boundary, and file-only look accounting.

The analyzer independently closes the join defect Session FA identified. It requires
`candidate_id + decision_time_utc + symbol + side/direction`, verifies both key sets and row order,
and refuses candidate ID alone (`session_fb_sol_grid.py:195-245`). All 27,658 pool rows and all
27,658 sidecar rows have unique aligned composites. Candidate ID alone has **5,778 duplicate excess
rows**, so the stronger key is material, not decorative (`GRID_FULL_RESULTS.json:256091-256102`).

Path and cost truth also close:

- 4,978 rows use ordered bid/ask ticks and 22,680 use conservative M1
  (`GRID_FULL_RESULTS.json:256107-256120`);
- all 27,658 commission rows independently reproduce CN broker truth, with zero unpriced and zero
  non-identical rows (`GRID_FULL_RESULTS.json:116-130`); and
- every selected repair cell has zero same-bar ambiguity under the conservative primary.

## 3. Complete January family census

Recorded gross is `opportunity_net_proxy_r + cost_r`; recorded net is the pool's cost-true proxy.
The ten family rows below sum to all 27,658 candidates. Detailed LONG/SHORT rows and both residual
surfaces are in `GRID_FULL_RESULTS.json`.

| origin family | n | share | gross mean | gross sum | cost mean | net mean | net sum | residual-A n | residual-A net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cross_asset_lead_lag | 2,083 | 7.53% | -0.130735 | -272.321 | 0.805706 | -0.936441 | -1,950.607 | 152 | -29.508 |
| current_breaker_re_entry | 4,263 | 15.41% | -0.825435 | -3,518.829 | 0.642566 | -1.468001 | -6,258.087 | 254 | -161.831 |
| current_fvg_fill | 7,146 | 25.84% | -0.141622 | -1,012.028 | 0.974975 | -1.116597 | -7,979.201 | 1,167 | -229.390 |
| current_ob_retest | 1,340 | 4.84% | -0.104598 | -140.161 | 0.303914 | -0.408512 | -547.407 | 126 | -43.834 |
| displacement_continuation | 4,469 | 16.16% | -0.088467 | -395.357 | 0.275746 | -0.364212 | -1,627.665 | 1,646 | -306.510 |
| liquidity_sweep_reclaim | 4,475 | 16.18% | -0.041520 | -185.803 | 0.566812 | -0.608332 | -2,722.286 | 738 | -68.230 |
| regime_transition_break | 297 | 1.07% | -0.006703 | -1.991 | 0.114533 | -0.121236 | -36.007 | 38 | +5.389 |
| session_open_range_break | 987 | 3.57% | -0.074738 | -73.767 | 0.193339 | -0.268077 | -264.592 | 156 | -17.404 |
| structural_distance_extreme | 1,993 | 7.21% | -0.182008 | -362.741 | 1.230761 | -1.412769 | -2,815.648 | 78 | -19.199 |
| volatility_compression_expansion | 605 | 2.19% | -0.086786 | -52.505 | 0.170568 | -0.257354 | -155.699 | 154 | -24.919 |

The identity is exact at the retained precision: **-6,015.503029 gross - 18,341.695885 cost =
-24,357.198914 net R** over 27,658 rows (`GROSS_DECOMP.json:629-636`).

## 4. Full 198-cell classification

Count-only thresholds admit every family with `n>=500` and every family×direction cell with
`n>=300`: **26 of 30 population strata**. Every eligible population receives all 11×9×2 cells;
there is no favorable top-N truncation. The four preregistered ineligible strata are the 297-row
`regime_transition_break` family, its 151 LONG and 146 SHORT cells, and the 274-row
`volatility_compression_expansion × SHORT` cell.

| scope | anti-predictive / invertible | persistent as-declared repair | gross-positive, cost-killed | noise | dead under both | below denominator |
|---|---:|---:|---:|---:|---:|---:|
| family | 1 | 1 | 7 | 0 | 0 | 1 |
| family × direction | 2 | 2 | 13 | 0 | 0 | 3 |

The absence of eligible noise/dead labels is not a claim that the remaining mechanisms are good.
Their TRAIN-selected geometry leaders retain gross structure on both splits but remain net-negative
after geometry-correct cost; they are **repair inputs**, not kill evidence. The exact classifications
are rooted in `FAMILY_CLASSIFICATION.json:16-36`.

### Breaker inversion re-derived at true UTC

| population | split | n | mean gross R | mean net R |
|---|---|---:|---:|---:|
| breaker, all | TRAIN | 2,257 | +15.169398 | +11.877105 |
| breaker, all | HOLDOUT | 2,006 | +13.686005 | +11.928115 |
| breaker, all | FULL | 4,263 | +14.471371 | +11.901108 |
| breaker LONG | FULL | 1,969 | +15.260129 | +12.147616 |
| breaker SHORT | FULL | 2,294 | +13.794361 | +11.689524 |

The frozen TRAIN leader independently returns CQ's exact inverted 5D/0.25D cell. Both direction
cells persist and the fixed-leader max-T p is 0.001 for family, LONG, and SHORT. As-declared breaker
leaders remain negative. `BREAKER_REDERIVATION.json` contains the full source-mode and comparator
receipt; CQ's existing default-off transform is therefore reused, not forked.

### OB-retest geometry is the new repair

| population | split | n | mean gross R | mean net R | target / stop / horizon |
|---|---|---:|---:|---:|---:|
| OB-retest, all | TRAIN | 799 | +2.961366 | +1.630823 | 430 / 312 / 57 |
| OB-retest, all | HOLDOUT | 541 | +2.716180 | +1.670197 | 277 / 237 / 27 |
| OB-retest, all | FULL | 1,340 | +2.862377 | +1.646719 | 707 / 549 / 84 |
| OB-retest LONG | FULL | 746 | +2.891150 | +1.698900 | 398 / 310 / 38 |
| OB-retest SHORT | FULL | 594 | +2.826240 | +1.581186 | 309 / 239 / 46 |

The TRAIN-only winner is as-declared target 1.5D / stop 0.25D. It survives untouched HOLDOUT,
both directions, conservative ambiguity, cost, and max-T p=0.001. February's recorded/original OB
geometry remains gross-negative in both directions; that corroborates the original-family defect
but is **not** a February test of the new geometry.

## 5. Breaker pocket and max-T control

The null procedure uses seed `20260801`, 999 draws, and only TRAIN dates. Within each UTC day it
permutes the joint family×direction labels while keeping geometry outcomes fixed. Each statistic is
the selected population's TRAIN mean-net lift over the full TRAIN mean under the identical cell;
the draw statistic is the maximum one-sided lift across all 11 fixed leading cells. The null max
has mean 1.091540, q95 1.495400 and maximum 1.949611 R.

This max-T controls simultaneous inference across the fixed TRAIN leaders. It deliberately does
not reselect 99 geometries inside each draw; the untouched eight-day HOLDOUT is the geometry-
selection control. That boundary is recorded, not hidden, in `FAMILY_CLASSIFICATION.json`.

## 6. Complete gross-deficit attribution

Every signed family×direction gross sum closes to its full-pool total. Positive families remain
negative deficit contributions (offsets), so the table cannot make the deficit disappear by
dropping inconvenient rows.

| family | January gross sum | January deficit share | February gross sum | February deficit share |
|---|---:|---:|---:|---:|
| current_breaker_re_entry | -3,518.829 | 58.50% | -1,756.481 | 48.13% |
| current_fvg_fill | -1,012.028 | 16.82% | -759.616 | 20.82% |
| displacement_continuation | -395.357 | 6.57% | -2.782 | 0.08% |
| structural_distance_extreme | -362.741 | 6.03% | -421.884 | 11.56% |
| cross_asset_lead_lag | -272.321 | 4.53% | -275.127 | 7.54% |
| liquidity_sweep_reclaim | -185.803 | 3.09% | -458.511 | 12.56% |
| current_ob_retest | -140.161 | 2.33% | -53.128 | 1.46% |
| session_open_range_break | -73.767 | 1.23% | +94.727 | -2.60% |
| volatility_compression_expansion | -52.505 | 0.87% | -26.109 | 0.72% |
| regime_transition_break | -1.991 | 0.03% | +9.699 | -0.27% |
| **total** | **-6,015.503** | **100%** | **-3,649.212** | **100%** |

January is dominated by breaker plus FVG-fill (**75.32%** of gross deficit). February still assigns
68.95% to those two. The mix is not static: displacement almost disappears in February while
liquidity and structural-distance expand. That is mechanism/state information for repairs, not
permission to delete the family.

## 7. Which families make the residual choice surface negative

Residual A—broker pretrade executable and selector action in trade/open-reduced/reduce-risk—is
still negative before and after cost: **4,509 rows, -499.655805 gross, 395.779241 cost,
-895.435046 net R** (`GROSS_DECOMP.json:640-918`). Its negative family drivers are:

| family | residual-A n | residual-A net sum R |
|---|---:|---:|
| displacement_continuation | 1,646 | -306.510 |
| current_fvg_fill | 1,167 | -229.390 |
| current_breaker_re_entry | 254 | -161.831 |
| liquidity_sweep_reclaim | 738 | -68.230 |
| current_ob_retest | 126 | -43.834 |
| cross_asset_lead_lag | 152 | -29.508 |
| volatility_compression_expansion | 154 | -24.919 |
| structural_distance_extreme | 78 | -19.199 |
| session_open_range_break | 156 | -17.404 |
| regime_transition_break | 38 | **+5.389 offset** |

The top three drivers contribute 77.92% of residual-A net loss. The literal scheduler-ranked
residual B is also negative: **4,095 rows, -514.427888 gross and -870.916030 net R**
(`GROSS_DECOMP.json:921-1196`). Thus the residual surface is not negative because the scheduler
alone picked a bad row from an otherwise positive executable set; the set entering it is already
negative, led by displacement, breaker, and FVG-fill. The geometry grid then identifies how two of
those named mechanism defects can be repaired rather than suppressed.

## 8. February corroboration only

The January output hashes were committed before the separate February command could run.
February then assigns all 24,239 rows to family×direction cells and reports **-3,649.212443 gross,
11,864.260384 cost and -15,513.472827 contextual net R** (`FEB_CORROBORATION.json:404-409`). Gross
sign matches January in 14 of 20 comparable cells and differs in six
(`FEB_CORROBORATION.json:398-401`).

`opportunity_gross_r` is primary. Its independent `net + cost` cross-check differs by at most
4.999983×10⁻⁹ R per row—serialization rounding, reported over all 16,560 rows above a strict 1e-9
threshold (`FEB_CORROBORATION.json:390-395`). The signed family decomposition still closes to the
primary gross total. Net/cost remains contextual because every February row dropped
`pretrade_cost_packet_status` and 3,555 rows belong to the known flat-default symbols GER40,
UKOIL_cash, or USOIL_cash (`FEB_CORROBORATION.json:414-423`). No January rule, eligibility,
classification, cell, candidate, or p-value was changed from February.

## 9. Default-off repair implementation

`fb_current_ob_retest_as_declared_target_1p5d_stop_0p25d_v1` is a narrow research-infrastructure
candidate, not production wiring. Disabled calls deep-copy pass through. Enabled calls apply only
to `current_ob_retest`, require the full candidate/time/symbol/side identity, preserve side and
entry, set 1.5D/0.25D geometry, canonicalize nested trade parameters, and fail closed if any named
realized/path outcome field enters (`current_ob_retest_geometry_candidate.py:86-134,145-212`).

`REPAIR_CANDIDATES.json:35-87` verifies it across all **1,340** January OB rows: 746 LONG, 594 SHORT,
1,340 unique input composites, 1,340 unique transformed IDs, zero stop error, maximum target float
error 4.3656×10⁻¹¹, no outcome fields, no runtime source reference, and no config change. The
existing breaker candidate's constants/default are separately verified and its implementation hash
is retained in the same receipt. Neither candidate is promoted or activated.

## 10. Look accounting, tests, and safety

There are exactly **198 logical geometry looks** and **5,148 population-cell evaluations**
(198×26). Every population cell is `FORENSIC_DIAGNOSTIC`, `billed:false`; the 999 permutations are
one control procedure. The master iteration ledger was intentionally not appended because the
protocol is file-only forensic accounting (`LOOK_MANIFEST.json:1-8,49312-49315`). Candidate-book
multiplicity remains unchanged.

Focused behavioral verification closes at **48 passed, 0 failed, 0 errored** across the inherited
CQ semantics, composite-safe analyzer, new OB candidate, and existing broader-origin/breaker tests.
The mechanical equal-scope failure-set A/B is **0 bad → 0 bad, 0 regressed**, with 10/10 inherited
CQ tests on both the preregistered pre-code commit and final implementation commit. The widened
48-test capture is retained separately and is not misrepresented as the A/B baseline.

No full replay ran. No VPS, broker-capable script, activation token, live service, config activation,
March outcome, or live-forward outcome was touched. The R2 checker reports the same pre-existing
drift in `broker_net_cost_engine.py` plus two package ledgers; neither new source path is R2-bound,
and Session FB did not rewrite the contract or relabel that estate clean.

## 11. Residual unknowns and next decisive measurements

1. The breaker transform still needs the two additional path-complete chronological folds already
   required by CQ's unchanged ratified gate. Session FB adds no shortcut around that sample rule.
2. The new OB-retest candidate has one path-complete January TRAIN/HOLDOUT month, not admission
   evidence. Its next lawful step is independent path-complete RECORDED folds under the unchanged
   candidate-book multiplicity and gate; February's original-geometry gross is not a substitute.
3. Twenty eligible strata are gross-positive/cost-killed. Their negative result is now higher-
   information: future repairs should change cost-normalized geometry/execution or condition the
   mechanism, not declare the broad family dead.
4. February cost provenance remains incomplete. Fetch/repair broker-comparable packets before using
   its contextual net values for anything stronger than the gross attribution reported here.
5. The max-T is exact for fixed TRAIN leaders; a future gate may add a geometry-reselecting null,
   but it must not reuse this HOLDOUT or change the current p-values after seeing them.

## 12. Artifact map

| artifact | authority |
|---|---|
| `grid/GRID_PROTOCOL.json` | pre-outcome rules, evidence boundaries, hashes and multiplicity |
| `grid/GRID_FULL_RESULTS.json` | census, composite join, path/cost truth and all 198 cells |
| `grid/FAMILY_CLASSIFICATION.json` | TRAIN leaders, HOLDOUT classifications, max-T and two unique repairs |
| `grid/GROSS_DECOMP.json` | complete January/February signed deficit and residual choice surfaces |
| `grid/BREAKER_REDERIVATION.json` | true-UTC breaker family/direction comparator and null control |
| `grid/FEB_CORROBORATION.json` | frozen `owner_mandate_20260801` attribution-only read |
| `grid/LOOK_MANIFEST.json` | 198 logical looks / 5,148 unbilled forensic strata |
| `grid/REPAIR_CANDIDATES.json` | existing breaker reuse and new OB candidate materialization proof |
| `phase19/receipts/SESSION_FB_SCOPED_AB.md` | embedded equal-scope failure-set A/B |

## What I got wrong

1. My first sparse-checkout `git add` accepted the commission but omitted the out-of-cone protocol.
   I immediately used `git add --sparse` and committed `GRID_PROTOCOL.json` separately **before any
   Session-FB outcome computation**; the protocol commit is `d194d9f1f`.
2. The first classification summary said “six null-clean repairs.” Those were six population rows:
   family, LONG and SHORT for two mechanisms. Before implementing anything I added a deterministic
   transform-level deduplication and reran January. The final answer is two unique candidates.
3. My first A/B comparison widened AFTER from one inherited file to four files. The tool refused it,
   correctly. I retained that run only as the 48-test focused capture and generated the final A/B on
   the exact same inherited CQ scope.
4. The February primary gross field and rounded `net + cost` differ on many rows at a strict 1e-9
   threshold. I did not force an identity: the receipt reports the 4.999983e-9 maximum, uses primary
   gross for complete attribution, and keeps February net contextual.
