# Session CQ — path-complete pools expose a breaker repair, not an activation candidate

Session CQ · Wave 18 · Blocks B2900–B2949 · branch `phase18/path-complete-pools`

## 1. Result

The frozen January path grid found one mechanism-specific repair worth carrying forward:
invert `current_breaker_re_entry`, hold entry fixed, set target to 5D and stop to 0.25D. On the
predeclared TRAIN/HOLDOUT split it is strongly net-positive in both cells. The production transform
is built, pure, testable and default-off.

That is **not an admission**. The ratified `CANDIDATE_BOOK_V1` / `B_balanced` / alpha 0.10 gate on
RECORDED eras returns **`NOT_EVALUABLE`**: 3,082 trades survive the population rule, but January
supplies only one evaluable chronological fold and the frozen gate requires three. The repair is
therefore **not queued and not armed**. Its exact next requirement is two additional evaluable,
path-complete chronological folds under the unchanged transform, cost truth, population and gate.
February's first economic read remains CP's; March outcomes remain unread.

Two tempting simpler conclusions are closed. Suppressing `current_breaker_re_entry` improves the
book but leaves TRAIN and HOLDOUT materially negative, while `liquidity_sweep_reclaim × LONG`
remains cost-vetoed after an independent broker-true commission reprice. The repair is a direction
and geometry change, not deletion or a commission correction.

## 2. Path-complete January pool

CQ authenticated CJ's true-UTC `LANE_ITERATION` registry and used its compact January S0R0
population as the one-to-one candidate surface. S1R1 was not needed: the frozen question changes
candidate exit geometry and orientation, not sizing, so adding a sizing arm would have expanded the
work without changing a cell.

`CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json` binds:

- 27,658 candidate rows on 21 January trading dates and 27,658 unique join keys;
- one ordered-path sidecar row per candidate, with 3,229,819 observations and 3–120 observations
  per path inside the declared 120-minute horizon;
- 4,985 rows with authenticated tick pointers; 4,978 resolve to post-decision ordered bid/ask
  ticks, while seven XAGUSD rows conservatively fall back to authenticated M1;
- every observation strictly after the decision and no later than the horizon; and
- sidecar SHA-256 `ffa2a2151e79ab81202fab07706f859579e453e0b00784c1e69b381903e9ba61`.

Ordered ticks use bid for LONG exits and ask for SHORT exits. Where an ordered tick path is absent,
M1 is explicitly conservative: a bar touching both levels is reported ambiguous rather than given
an invented within-bar order. The builder is serial and uses the existing true-UTC packs; it does
not invoke the bounded replay prewarmer or leave child processes.

## 3. Frozen 99-cell grid and look accounting

The grid reports all **198 binding geometry cells**: 11 targets × 9 stops × two orientations.
Every cell reports TRAIN, HOLDOUT and FULL results for all three named populations: full S0R0,
`current_breaker_re_entry`, and `liquidity_sweep_reclaim × LONG`. The complete cell table and each
cell's ambiguity count are in `CQ_FROZEN_99_CELL_GRID_V1.json`; no cell was omitted because its
answer was inconvenient.

The iteration ledger contains exactly **201 CQ looks**: 198 geometry cells plus one suppression,
one liquidity-cost and one recorded-geometry ambiguity look. All are `VAL`, all are initially
unbilled, and a rerun writes zero duplicates. `CQ_LOOK_LEDGER_RECEIPT_V1.json` records 201 expected,
201 present, 0 non-VAL, 0 billed, 0 February and 0 March rows. Graduation later bills exactly the
single selected repair hypothesis; it does not rebill the other 200 looks.

## 4. What the grid says

### Suppression is insufficient

Removing all 4,263 breaker rows improves the full population's mean gross R from **-0.21750** to
**-0.10672** and mean net R from **-0.88066** to **-0.77363**, but the reduced population remains
negative on both partitions:

| split | n after suppression | mean gross R | mean net R |
|---|---:|---:|---:|
| TRAIN | 13,991 | -0.09860 | -0.82837 |
| HOLDOUT | 9,404 | -0.11879 | -0.69220 |
| FULL | 23,395 | -0.10672 | -0.77363 |

The declared suppression verdict is `DOES_NOT_SURVIVE_OUT_OF_CELL`.

### As-declared breaker geometry stays dead

The 4,263 breaker rows have recorded-geometry FULL means of **-0.82544 gross R** and
**-1.46800 net R**. None of the 99 as-declared geometry cells is persistently net-positive. Even
the best TRAIN-ranked cell, target 2D / stop 4D, remains negative on TRAIN, HOLDOUT and FULL.

### Inversion exposes the repair

The inverted breaker surface contains 64 cells net-positive on both TRAIN and HOLDOUT, plus 18
cells that are gross-positive on both but still cost-vetoed. Applying the frozen selection rule—
maximize TRAIN mean net R among the persistent net-positive cells—selects target 5D / stop 0.25D:

| split | n | mean gross R | grid mean cost R | mean net R | target / stop / horizon |
|---|---:|---:|---:|---:|---:|
| TRAIN | 2,257 | +15.16940 | 3.29229 | +11.87710 | 1,635 / 430 / 192 |
| HOLDOUT | 2,006 | +13.68601 | 1.75789 | +11.92812 | 1,287 / 485 / 234 |
| FULL | 4,263 | +14.47137 | 2.57026 | +11.90111 | 2,922 / 915 / 426 |

These are survivor-selected January VAL economics, not an activation expectancy. Their job was to
select one repair for the already-ratified gate, which then refused to judge it on one fold.

### The full pool does not become good by inversion

Neither orientation has a persistently net-positive full-pool cell. Its best inverted TRAIN-ranked
cell, target 5D / stop 4D, is gross-positive but cost-vetoed: FULL **+0.07350 gross R** and
**-0.09229 net R**. This control is why the breaker result is carried as a named mechanism repair,
not generalized into a whole-book reversal.

## 5. Liquidity reclaim is still a cost veto

CQ re-priced all 27,658 pool rows through CN's exact FTMO commission call chain and the cost artifact
SHA-256 `bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd`.
The recomputation is exactly identical to CJ's recorded commission on every row: 21,818 MEASURED,
5,840 TRANSFERRED, zero unpriced rows, zero non-identities and maximum absolute delta 0.

For `liquidity_sweep_reclaim × LONG`, recorded geometry is:

| split | n | mean gross R | mean cost R | broker-true mean net R |
|---|---:|---:|---:|---:|
| TRAIN | 1,263 | -0.00539 | 0.57415 | -0.57953 |
| HOLDOUT | 692 | +0.03008 | 0.37430 | -0.34421 |
| FULL | 1,955 | +0.00717 | 0.50341 | -0.49624 |

No liquidity cell is persistently net-positive in either orientation. The as-declared family has
86 persistent gross-positive/cost-vetoed cells, so the mechanism is not dismissed as no signal; it
is correctly classified as uneconomic at broker-true costs.

## 6. First-touch ambiguity is measured

At the recorded geometry that CK bounded, first-touch ambiguity is exactly **0 / 27,658 (0%)**:
0 / 4,978 on ordered tick paths and 0 / 22,680 on conservative M1 paths. This retires CK's
0–11.91% recorded-geometry bound; optimistic same-bar ordering cannot explain the remaining hole.

The claim is deliberately scoped. Other target/stop cells can create a different collision—for
example, the best as-declared full-pool cell has one ambiguous row. Every such count remains in the
198-cell receipt. CQ retires the old bound, not the need to report ambiguity for new geometry.

## 7. Default-off production transform

`src/components/current_breaker_re_entry_repair.py` implements
`cq_current_breaker_inverted_target_5d_stop_0p25d_v1` as a pure candidate transform. It:

- deep-copies and returns exact pass-through behavior unless explicitly enabled;
- applies only to `origin_family=current_breaker_re_entry`;
- preserves decision time and entry, inverts side, sets stop to 0.25D and target to 5D, and derives
  a new deterministic candidate identity;
- consumes predecision geometry only and stamps the original/repaired contract; and
- fails closed on malformed enabled breaker geometry.

`broader_origin_generators.py:343-368` applies it after normal candidate finalization only when the
runtime key `phase18_current_breaker_re_entry_repair_enabled` is true. The key is absent-false; CQ
changed no config byte. Generation audit records the key, default, transform and applied count.
The 4,263 materialized gate records were all produced by this production transform, retain exact
exit timestamps, and bind gzip SHA-256
`5c9ae468120300fd8d2c6ef0f99fc09ce175d77ea2ac5ecdc0ddc3fb25f2b131`.

The fidelity register classifies the stateless transform structurally as `PER_BAR`, but explicitly
does **not** claim direct live recall. It receives only the conservative transferred per-bar class
rate, 160 / 167 = **95.808%**, and carries that ceiling into the gate.

## 8. Ratified gate and exact next requirement

Graduation moves `CANDIDATE_BOOK_V1` from 57 to 58 declared members and from 55 to 56 looks. The
append-only graduation ledger has one CQ row and one billed look, with repo-relative declaration
paths. The other declared CQ looks remain unbilled.

The unchanged gate contract is RECORDED, FTMO mid band, `B_balanced`, alpha 0.10,
all-declared multiplicity, FTMO-Server3 clock and CN cost truth. RECORDED keeps 3,082 of 4,263
trades, drops 1,181 and leaves zero unpriceable. Coverage is 100%; the weakest accepted cost class
is MODELLED. Diagnostic—not admitting—means are +14.45595 gross R, 0.88945 cost R and +13.56651
net R. Spread is the largest cost term at 0.64774 R.

Only fold 1 is evaluable: 1,664 OOS trades over 2026-01-16..30, OOS mean +11.25234 R and preceding
train mean +12.55800 R. The scored-fold population has 2,844 trades, but the frozen sample gate
requires at least three evaluable folds. Consequently:

- verdict: **`NOT_EVALUABLE`**;
- primary prescription: `SAMPLE_EXTENSION`;
- missing evidence: **two more evaluable chronological folds**; and
- ceremony: **`NOT_QUEUED`**, arming authority false.

The next lawful capture is at least two additional path-complete, true-UTC RECORDED chronological
folds under the same transform and gate contract. It must come from eligible history without
stealing CP's February first read or reading March outcomes. If existing history cannot supply the
folds, the exact source request is authenticated true-UTC M1 plus ordered bid/ask ticks where
available, candidate decision geometry and the same CN broker-cost artifact for enough additional
dates to produce two evaluable folds.

## 9. Verification and safety boundary

The focused behavioral closure is **68 passed**. It covers strict post-decision path slicing,
conservative same-bar ambiguity, bid/ask tick semantics, exact CN commission identity, 201-look
accounting, February/March refusal, pure/default-off transform behavior, real broker-price float
reconciliation, end-to-end generator wiring, conservative fidelity transfer, receipt boundaries
and the single portable graduation bill.

The tool-derived A/B scope reaches 86 test files from all 18 paths in implementation commit
`15375e936`. After hydrating committed test dependencies, it closes at **3,327 passed, 13 skipped,
9 xfailed, 0 failed, 0 errored**. Against the committed suite-wide ZERO baseline of 12,671 passed,
`SESSION_CQ_AB_RECEIPT.md` reports **0 bad → 0 bad, 0 regressed** in an unedited
`gtos-ab-receipt-v1` fence.

CQ read no February economics and no March outcomes; contacted no VPS; ran no broker-capable
script; imported no broker module in the repair/gate path; read no token-bound config bytes; changed
no config; and granted no live or ceremony authority. None of CQ's changed source or tool paths is
an R2 decision-contract member. The raw R2 checker still reports unrelated pre-existing/authorized
drift in CN's cost engine and two package ledgers; CQ does not relabel that estate state as clean.

## 10. Artifact map and orchestrator handoff

| artifact | authority |
|---|---|
| `CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json` + `pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` | authenticated path-complete January population |
| `CQ_FROZEN_99_CELL_GRID_V1.json` | all 198 cell answers, controls, cost reprice and ambiguity |
| `CQ_LOOK_MANIFEST_V1.json` + `CQ_LOOK_LEDGER_RECEIPT_V1.json` | all 201 logical looks and idempotent ledger closure |
| `CQ_CURRENT_BREAKER_REPAIR_V1.json` + `pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz` | selected transform and exact gate trade records |
| `CQ_CANDIDATE_FAMILY_V26.json` | one-look ratchet successor |
| `CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json` | frozen gate verdict and sample prescription |
| `SESSION_CQ_AB_RECEIPT.md` | tool-emitted regression fence |

The orchestrator should merge the default-off implementation and evidence, keep the repair out of
the ceremony queue, and schedule only the two-fold historical capture. A future session must rerun
the unchanged ratified gate after that capture; January's diagnostic magnitude is not permission to
relax the sample gate or arm the transform.

## What I got wrong

1. The first scoped capture ran before this sparse worktree's test fixtures were fully hydrated and
   reported 74 environmental failures. The preferred hydrator removed 71; the remaining three were
   traced to one committed sparse receipt and one code-hash-bound `.hermes` Task-6 receipt already
   present elsewhere on the laptop. After exact-hash materialization, the unchanged 86-file scope
   closed ZERO. I kept only the final capture in the receipt.
2. My first generated graduation row preserved worktree-absolute declaration paths. Before the
   implementation commit I corrected the driver to execute from repo root, removed only CQ's
   uncommitted row and regenerated the family/ledger. The final ledger has one CQ row, one bill and
   repo-relative paths; a second run is idempotent.
3. The transform's first reconciliation check required bit-for-bit float equality. Real broker-price
   geometry can differ at the final binary digit when the canonicalizer recomputes target from RR.
   I replaced exact equality with tight `math.isclose` checks and pinned the realistic price case.
4. The gate driver's first description predicted fidelity as the stopping boundary. The existing
   register correctly permits a conservative structural class transfer for a pure per-bar transform;
   fidelity passes with an explicit no-direct-measurement ceiling, and sample coverage is the actual
   fail-closed boundary. I corrected the description and did not invent a direct recall claim.
