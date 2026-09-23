# Session CK — mechanism autopsy result

**Disposition: FILED. Nothing graduated, no family declaration changed, no March 2026 outcome was
read, and every outcome look was January `VAL` / unbilled.** The mechanism analysis below is zero-
replay: it reads only CD's four committed repaired pools. The bounded engine work in §6 is the
commission's separate H-CD-7 engineering proof and is not evidence for the mechanism verdict.

## Findings first

1. **“The broad family is wrong about direction” is true for a large, concentrated pocket, not as a
   uniform description of every generator.** `current_breaker_re_entry` is −0.82755 gross R/row over
   15.19 % of S0R0 and carries 21.55 % of all negative gross R. Its LONG cell is −0.89839 TRAIN /
   −0.83317 HOLDOUT and survives CK's declared within-day family-wise max-T null (`p = 0.000999`).
   This is persistent anti-direction, not one bad month aggregate.

2. **One different subfamily has reproducible pre-cost information and still is not economic.**
   `liquidity_sweep_reclaim × LONG` is +0.03013 TRAIN / +0.03483 HOLDOUT gross R/row, with 69.2 % /
   62.5 % gross-positive days and family-wise `p = 0.001998`; FULL gross is +0.03177. FULL net is
   **−0.48234 R/row**. CK files that signal; CK does not graduate it.

3. **The committed pools do not identify the commissioned 99-cell geometry surface.** They contain
   terminal economics at the incumbent 2D target / 1D stop, but no ordered path, touch times,
   same-bar flag or content-bound path pointer. Exactly one direct cell is identified; it is
   −0.8819 to −0.8822 net R/row. Another 18 cells are definitively negative and 80 are unknown per
   arm. The inverted surface has 18 definitively negative and 81 unknown cells. “Zero exact positive
   cells” is true; “every alternative geometry is negative” is not established.

4. **On the 14.34 % binary endpoint slice, direction is adverse and inversion is still net-negative.**
   Mirroring 2D/1D target/stop endpoints changes gross from about −0.490 to +0.2455 R/row, but leaves
   **−0.1114 net R/row** even under zero same-bar ambiguity. Break-even would require 108.9 % of the
   source stops to be ordinary. This diagnoses direction plus a cost/geometry veto on that slice; the
   other 85.65 % remains path-unidentified.

5. **Same-bar first-touch is a live suspect, not a cleared explanation.** Its exact frequency is
   bounded only at 0–11.91 %. The maximally optimistic reassignment is worth +0.3649 gross R/row,
   enough to cover the observed −0.2196/−0.2198 gross deficit. The projection erased the evidence
   needed to narrow that bound.

6. **H-CD-7 was a real pool-lifecycle hazard, but its reported lock did not reproduce.** CK's
   `--days 12` reproduction was active at ~100 % CPU after 174.76 s, not blocked at 0 %. Separately,
   three old CD `ProcessPoolExecutor` groups were still orphaned as 15 PPID-1 processes. Bounded
   fixtures now prewarm serially; sealed/full-month runs retain the runner default. The exact 2-day
   comparator is `OUTCOME_IDENTICAL` at zero tolerance.

The answer is therefore **mixed but actionable**: one generator is strongly anti-directional, one
generator/side cell carries small gross information that current costs destroy, and the full
direction/geometry question cannot be closed until the missing ordered-path evidence is restored.

## 1. Evidence and claim boundary

The four inputs are CD's committed repaired pools, 114,195 rows total:

| arm | rows | mean gross R/row | mean net R/row | gross-positive days |
|---|---:|---:|---:|---:|
| S0R0 | 28,544 | −0.219755 | −0.882234 | 0 / 21 |
| S0R1 | 28,546 | −0.219677 | −0.882112 | 0 / 21 |
| S1R0 | 28,552 | −0.219744 | −0.882060 | 0 / 21 |
| S1R1 | 28,553 | −0.219638 | −0.881931 | 0 / 21 |

`ck_mechanism_autopsy.py:160-208` verifies each committed file hash, row count, stable schema,
January-only dates and required numerics before scoring. It fails closed on any March row
(`:193-196`). The protocol hash is pinned in code (`:52`, `:128-134`), so an outcome-bearing grid
cannot be widened after the fact.

Every geometry/cut/null rule was committed before pool outcomes were read in
`CK_MECHANISM_PROTOCOL_V1.json` (commits `4af452072`, `8dbc7cbcc`, `b9e3fa111`). All 99 target/stop
cells, both orientations, first-13/last-8 chronological split, eligibility floors, five interaction
families and the within-day max-T null were fixed there.

## 2. CK-1 — stop/target geometry

Every row's price geometry is the incumbent target distance 2.0 × original risk and stop distance
1.0 × original risk. The pool has no observations between entry and terminal accounting. Strict
row-wise logical bounds therefore give:

| orientation | exact cells | definitively net-negative | unidentified vs zero | exact net-positive |
|---|---:|---:|---:|---:|
| original | 1 | 18 | 80 | 0 |
| inverted | 0 | 18 | 81 | 0 |

The same counts hold on every arm. The direct 2D/1D cell is the only exact cell and has the net means
in §1. Upper surfaces in `CK_MECHANISM_MAP_V1.json` are **possibility bounds**, not repriced outcomes;
they cannot identify the best cell or its true distance from break-even.

The schema finding is not cosmetic. CD's projector originally retained the mine's feature fields plus
a short economics list, then the ~8 GB raw ledgers were deleted. It did not preserve even scalar
terminal/path provenance. The forward fix at `phase14/receipts/cd_pool.py:45-95,160-179` retains 23
oracle/source-pointer fields in future compact pools. `CK_POOL_PATH_CONTRACT_V1.json` defines the
content-bound ordered-path sidecar needed to make arbitrary target/stop repricing exact. Historical
pools were not rewritten.

## 3. CK-2 and CK-3 — direction and first-touch ambiguity

Recorded terminal classification identifies about 694/695 targets and 3,400/3,401 stops per arm;
roughly 24,450 rows are neither endpoint. The predeclared binary slice is therefore only
4,094–4,096 rows, 14.34–14.35 % of each pool.

| binary-slice diagnostic | original 2D/1D | mirrored 1D/2D, zero ambiguity |
|---|---:|---:|
| gross R/row | about −0.490 | +0.2455 to +0.2457 |
| net R/row | about −1.204 | **−0.11136 to −0.11144** |
| evidence coverage | 14.34–14.35 % | same rows only |

The gross sign flip is direct evidence that entries on this slice tend to resolve against their
declared side. Costs plus worse reward/risk erase even the perfect mirror. It is not permission to
call the entire 114,195-row pool inverted, because 85.65 % lacks an identified endpoint path.

Likewise, the pool cannot distinguish an ordinary stop from a conservative same-bar target-and-stop
case. Treating every recorded stop as potentially ambiguous gives frequency 0–11.91 % and optimistic
gross contribution 0 to +0.3649 R/row. Since +0.3649 exceeds the observed gross hole, first-touch
ordering remains capable of explaining it in the logical extreme. A path sidecar is the exact next
capture required; a verbal dismissal is not.

## 4. CK-4 — entry taxonomy

Of 178 rank-eligible declared taxonomy cells, four are gross-positive on TRAIN and one is positive on
both chronological splits:

| cell | TRAIN n / gross | HOLDOUT n / gross | FULL gross | FULL net | family-wise control |
|---|---:|---:|---:|---:|---:|
| `liquidity_sweep_reclaim × LONG` | 1,306 / +0.03013 | 701 / +0.03483 | **+0.03177** | **−0.48234** | max-T p=0.001998 |
| `GER40` | 940 / +0.02697 | 550 / −0.03795 | +0.00300 | −0.3197 | fails holdout |

The other TRAIN-positive interactions fail HOLDOUT. In contrast, the leading persistent loss pockets
are:

| cell | share of rows | gross R/row | persistence / control |
|---|---:|---:|---|
| `current_breaker_re_entry` | 15.19 % | **−0.82755** | 21.55 % of all negative gross R |
| `current_breaker_re_entry × LONG` | — | −0.89839 TRAIN / −0.83317 HOLDOUT | max-T p=0.000999 |
| `GBPUSD` | — | −0.53202 FULL | persistent symbol pocket |

`origin_family`, `risk_finalizer_reason` and `symbol` meet the declared concentrated-and-persistent
rule. Interactions involving origin remain persistent because `current_breaker_re_entry` dominates
them. The S/R arm switches barely move this shape: the winning gross cell and the leading loss cell
are identical across all four arms.

## 5. What was built and repaired

* `ck_mechanism_autopsy.py` is a deterministic, hash-pinned, January-only analyzer that emits exact
  results separately from partial-identification bounds and logs its manifest idempotently.
* `CK_POOL_PATH_CONTRACT_V1.json` specifies the missing ordered-path sidecar and strict join/refusal
  behavior.
* `cd_pool.py` now preserves scalar terminal/oracle fields and a content-bound source pointer for
  future pool projections (`phase14/receipts/cd_pool.py:70-95`).
* `sealed_inputs.build_january_args` now uses one source-prewarm worker only for bounded fixtures and
  stamps the previous/current policy (`src/research_infra/fast_engine/sealed_inputs.py:170-193`). Full
  arms remain on the frozen runner's default topology.
* 60 focused tests cover the analyzer, projection preservation, bounded topology, train-lane gate and
  outcome comparator.

## 6. CK-5 — H-CD-7 and the CB-3.3 boundary

The initial causal story did not survive reproduction. At the commissioned 90-second point the
`--days 12` process was doing active Python work. CK extended observation to 174.76 s, sampled ~100 %
CPU and ~1.5 GB RSS in package-entry normalization, found no prewarm children, and interrupted the
run. That means prepared-root narrowing did not produce the claimed lock on this launch.

The live process census did reveal the failure class: three two-hour-old CD pool groups, each one
resource tracker plus four spawn workers, all PPID 1 / 0 % CPU in the wave-14 worktree. CK terminated
those 15 explicit PIDs cleanly and changed bounded prewarming to serial. No broad process kill and no
file deletion were used. `CK_HANG_DIAGNOSIS_V1.json` carries the evidence and claim boundary.

On the published two-day S1R1 repaired-stack fixture, the comparator computed:

* `accepted: true`, `OUTCOME_IDENTICAL`, zero refusals;
* exact 5 trades / 10 orders / 96 scorecards / 8,807 missed rows;
* identical trade and order multisets plus missed-pool aggregate at float tolerance 0;
* wall 503.642 → 512.318 s, while economic hot path 439.755 → 386.321 s.

This is lifecycle hardening, not a speed claim.

The first medium-size completion is now measured:

| prefix | active days (>10 s hot path) | wall | max RSS | progress rows | terminal result |
|---|---:|---:|---:|---:|---|
| `--days 2` | 1 | 512.318 s | 2.103 GB | 2 / 2 | exit 0, `error: null`, identity accepted |
| `--days 12` | 7 | **3,007.090 s** | **3.983 GB** | **12 / 12** | exit 0, `error: null` |
| `--days 20` | 13 | **5,274.293 s** | **4.387 GB** | **20 / 20** | exit 0, `error: null` |

The 12-day run materialized 57,799 candidates / 57,779 missed rows / 40 orders / 19 trades / 672
scorecards. Its seven active-day hot paths total 2,774.147 s with median 403.877 s. The harness then
removed both exact temporary output routes after extracting the report/economics, and no child process
survived. That proves completion and roughly working-day-proportional cost at 12 calendar days; it does
not promise equal cost per calendar day.

The independent 20-day prefix then crossed the day-12 boundary and completed all 20 rows: 97,850
candidates / 97,819 missed rows / 62 orders / 30 trades / 1,248 scorecards, with 13 active days and
4,777.379 s of economic hot path. Aggregate wall per requested calendar day is 256.159 / 250.591 /
263.715 s at N=2/12/20; total wall scales 1× / 5.8696× / 10.2949× against prefix length 1× / 6× /
10×. **CB-3.3 is therefore proven at 2, 12 and 20 calendar days as a prefix-only cost gate.** It is
not a constant-cost-per-day claim and does not license arbitrary start-day slicing.

## 7. Look accounting and proof fence

The mechanism analyzer emitted 1,899 distinct looks. CK-5 adds four engineering rows: one interrupted
diagnostic, plus the completed 2/12/20-day runs. `CK_FINAL_LOOK_LEDGER_RECEIPT_V1.json` binds the final
canonical ledger and verifies **1,903/1,903 CK rows**, all `VAL`, all `billed: false`, zero March rows;
verdicts are 887 evaluated / 1,015 not-evaluable / one honestly logged error.

The mandated copy-back A/B is committed in `phase16/SESSION_CK_AB.md` with the tool-emitted
`gtos-ab-receipt-v1` fence: ZERO and HEAD each pass **169/169** shared-scope tests, **0 bad → 0 bad,
0 regressed**. The two HEAD-only files, absent at ZERO and therefore tested separately rather than
smuggled into the baseline, pass **7/7**. `CK_AB_SCOPE_V1.json` records the 32 changed paths and import/
literal closure. The driver never moved HEAD or invoked checkout; it restored and SHA-verified every
HEAD byte before the AFTER capture.

No family was graduated. The result doc and map are filings, not admission or deployment authority.

## 8. What I got wrong

1. **I initially trusted the commission's statement that the pool rows carry path data.** A schema-
   only census before outcome reading showed they do not. Had I substituted terminal endpoints for an
   ordered path, the 99-cell surface would have been invented. I froze partial-identification rules and
   built the missing-path contract instead.

2. **My first H-CD-7 theory repeated the prepared-root × pool suspicion.** Direct process evidence
   falsified it: the current run was compute-active and had already passed prewarm. The evidence that
   survived was narrower—old pool processes can be orphaned after their parents die—not that root
   narrowing itself deadlocks.

3. **My first taxonomy look manifest omitted the five interaction-family nulls even though the
   protocol declared controls for them.** I caught that before writing the result, added those looks,
   and reran the idempotent ledger reconciler. The final mechanism count is 1,899, not the earlier
   1,894.

4. **I expected “globally wrong direction” to be a cleaner answer than the data support.** The
   concentrated `current_breaker_re_entry` loss is real, but `liquidity_sweep_reclaim × LONG` is
   persistently gross-positive. The accurate model is heterogeneous and cost-vetoed, not uniformly
   anti-predictive.

5. **My first final A/B was red because I left CK's in-flight block exemption alive after CK had
   landed blocks.** The governance test correctly identified B2600-B2649 as a dead exemption below
   the new B2613 ceiling. I retired it, reran the whole copy-back comparison from a regenerated scope,
   and committed only the green fence.

## 9. Handoff — exact next work, no graduation

1. **Restore ordered path evidence.** Materialize `CK_POOL_PATH_CONTRACT_V1.json` from the exact source
   paths and hashes if those sources still exist; otherwise regenerate a projection with the repaired
   `cd_pool.py`. Carry target/stop touch order and same-bar resolution. Do not infer path from terminal
   R.
2. **Re-run the predeclared 99-cell/orientation grid unchanged** once the sidecar joins exactly. The
   existing protocol is the frozen specification; any widened grid is a new family of looks.
3. **File `current_breaker_re_entry` for generator-level causal repair.** The natural candidate is a
   direction/entry-timing redesign or an owner-visible off-switch experiment, not a CK removal. Preserve
   its chronological and within-day controls.
4. **File `liquidity_sweep_reclaim × LONG` for cost/geometry examination.** It has pre-cost information,
   not net economics. Do not graduate it from this result.
5. **Keep bounded fixtures serial-prewarm unless a supervised executor-shutdown repair is separately
   built and identity-gated.** Full sealed arms were deliberately left untouched.

## 10. Primary receipts and commits

* Protocol: `phase16/receipts/CK_MECHANISM_PROTOCOL_V1.json`
* Mechanism map: `phase16/receipts/CK_MECHANISM_MAP_V1.json`
* Path contract: `phase16/receipts/CK_POOL_PATH_CONTRACT_V1.json`
* Look manifest / first receipt: `CK_LOOK_MANIFEST_V1.json`, `CK_LOOK_LEDGER_RECEIPT_V1.json`
* H-CD-7 diagnosis / identity: `CK_HANG_DIAGNOSIS_V1.json`,
  `CK_BOUNDED_PREWARM_ACCEPTANCE_V1.json`
* Bounded completion / final looks: `CK_BOUNDED_PREFIX_PROOF_V1.json`,
  `CK_FINAL_LOOK_LEDGER_RECEIPT_V1.json`
* Regression fence: `phase16/SESSION_CK_AB.md`, `phase16/receipts/CK_AB_SCOPE_V1.json`,
  `CK_AB_AFTER_V1.newtests.txt`
* Commits through the 2-day gate: `4af452072`, `8dbc7cbcc`, `b9e3fa111`, `25e7d5eb5`, `091a40a1d`,
  `acd6d46da`, `011c09941`, `cf98e306b`, `a592d3277`; later proof commits `f29b59964`,
  `16b953435`, `cb3854c08`, `a16f7d635`
