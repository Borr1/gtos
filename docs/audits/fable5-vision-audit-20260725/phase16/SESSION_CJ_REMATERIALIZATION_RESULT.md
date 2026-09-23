# Session CJ — true-UTC re-materialization

**Wave 16, blocks B2550–B2599. Branch `phase16/rematerialization`.**
Commission: `phase16/SESSION_CJ_REMATERIALIZATION.md`. Owner authority: Borhen's
2026-07-31 instruction, “yes you can break the seal and proceed as proposed.”
Receipts: `phase16/receipts/`.

**Surface disclosure:** January, February, April and May 2026 are `VAL` on the
lane surface. Every look in this session is unbilled and logged. February remains
economics-unread. No result here is admission evidence and no headline expectancy
is quoted from VAL alone.

---

## 0. Findings first

**1. The authorized seal break is real, narrow and irreversible.** The lane now
has a physically separate, provenance-stamped true-UTC source estate and immutable
prepared packs beneath
`.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/`.
`campaign_sealed` is false at every boundary; the historical R2 contract, frozen
January bundle and sealed packs were read but never rewritten. The parked B7.5
campaign's approximately 36-machine-hour sealed-window resume option is therefore
dead, exactly as priced and accepted in `phase8/OWNER_DECISION_QUEUE.md`. This is a
LANE input surface, not a successor sealed campaign.

**2. The January clock correction passes both gates over the full available bar
estate.** The weekly-open check is **54/54**: winter opens at Sunday 22:00 UTC,
daylight-time opens at Sunday 21:00 UTC, and both are Sunday 17:00
`America/New_York`. Across **96/96** frozen/fresh bar pairs and **778,162**
January-overlap rows, the old label is uniformly **+2.0 hours** ahead of true UTC
and there are **zero** non-time residual rows. The correction is therefore
`true UTC = old sealed label - 2 hours`; the source payload itself did not change.

**3. The offline estate is complete for bars, not ticks.** All four windows have
D1/H4/M15/M1 for all 24 symbols. January, February and April have captured ordered
ticks for EURUSD, USDJPY, XAGUSD and XAUUSD only (**4/24**); April's four tick
captures stop on April 29, so April 30 has none. May has **0/24** ordered-tick
coverage. The registry records every absent component as a gap and never promotes
a bar substitute into a tick claim.

**4. Correct UTC exposed a source-authority defect before it could become an
economic result.** January 1's UTC fragments for USDCAD, USDJPY and USOIL_cash
failed the unchanged M1/M15 floor because true UTC puts the first two hours of the
complete broker day on the prior UTC date. `LaneBroadSourceResolver` now rebinds
only that first populated fragment to exactly one measured broker day, and only
when the complete broker day passes the unchanged floor. It adds or synthesizes
**zero rows**. The canonical 31-day × 24-symbol source plan is bound at
`b44b433039bf7f5372fc067f62477cdb5c8b0d2caf4202755a922a7c198be954`.

**5. The hour correction is one table, but not one blanket rewrite.** Old January
labels 00/01 become prior-day true-UTC 22/23; old 02..23 become true-UTC 00..21.
AW's B_TIME results must be regenerated because hour, session and day membership
move. AW's prose says 81 cells while the committed map contains **83**. AH and CE
explicitly use broker-server hour, and CH commissioned the same broker-hour axis,
so their named 00→04 / 00→01 mechanisms do not receive a UTC-label correction.

**6. Three immutable January generations were required; only the third is active.**
The first root was byte-valid but became source-stale after the broker-day
authority repair. `authority_v2` fixed that identity, then exact replay preflight
proved its packs were built under a bare-profile factor-neutral config rather than
the runtime's factorial shell. I did not waive that authority mismatch.
`runtime_v3` binds both the corrected source identity and the runtime-neutral config;
all **31/31** pack roots authenticate, one record from each deserializes, and only
this third root is registered active. The V3 feature pass then reproduced V2's 711
changed records exactly, proving the config defect was real but was not their cause.
Six retained pre-economics arm receipts document the fail-closed chain without
reading policy economics.

**7. The commissioned January economics invariance hypothesis is false.** The
full true-UTC S0R0 arm completed cleanly, but candidates fall 154,390→153,486,
scoreable missed rows 28,544→27,658 (**−3.10 %**), orders 134→122 and trades
63→57. Realized physical net moves −8.94126133→−5.50620829 R
(**+3.43505304 R**). Missed-pool mean moves only +0.00157757 R/scoreable row,
below the declared 0.01 threshold, but denominator movement exceeds 1 % and
trade count changes. The receipt therefore correctly says
`JANUARY_RECLOCKED_ECONOMICS_MOVED_MATERIALLY`: correcting the clock changes
session-conditioned decisions, not merely their labels.

**8. February remains the first never-read economic window.** Its 28 packs load
under the true-UTC lane, but this session ran no February candidate, trade, ledger
or expectancy computation. The trainer loop owns the first economic read and its
pre-declared question.

---

## 1. Authority and guard boundary

`src/research_infra/lane_rematerialization.py` is an offline materializer and
resolver. It imports no MT5 module, exposes no broker call, converts captured
broker epochs through `broker_clock.broker_epoch_to_utc`, retains raw tick
`time_msc`, hashes every output, and stores only repo-relative logical paths.

`LaneInputRegistry.resolve` authorizes dates through the training-lane surface
guard. The train runner accepts `--lane-input-registry` only with
`--purpose LANE_ITERATION`; it rejects use under `TRAINING`, clears the historical
shared-contract claim, and stamps the unsealed lane authority into its report.
The R2 arm economics are used as historical parameter authority, never as a claim
that the new sources satisfy R2's sealed source plan.

The source-plan adapter had to satisfy four independent engine checks rather than
paper over them:

1. the engine recomputes the complete source-plan digest;
2. ordered-tick paths resolve from an explicit logical repository root;
3. chunk M1 authority must equal the projection of the full canonical authority;
4. prepared packs must bind the same factor-neutral config and source identity as
   the runtime resolver.

The first four failures established that chain. V5 then rejected the source-fixed
packs generically, and V6 named the exact config-root mismatch. All six happened
before economic output and are preserved in `CJ_RECLOCKED_ARM_S0R0_V1.json`
through `V6.json`.

## 2. Source and pack inventory

`CJ_SOURCE_MATERIALIZATION_V1.json` records **168 bar files / 3,928,647 rows**
and **12 tick files / 40,847,966 rows** across the four commissioned windows. The
initial lane root occupied 7.7 GiB. Every source is content-addressed and every
receipt states `broker_live_authority: false`, `broker_mutation_enabled: false`,
`march_outcomes_read: false`.

| window | bars | ordered ticks | packs | prepared records | compressed bytes | economics |
|---|---:|---:|---:|---:|---:|---|
| January 2026 | 24/24 × 4 TF | 4/24 | 31 | 2,908 | 1,286,029,847 | one S0R0 VAL arm |
| February 2026 | 24/24 × 4 TF | 4/24 | 28 | 2,597 | 1,220,650,722 | **unread**; smoke only |
| April 2026 | 24/24 × 4 TF | 4/24 through Apr 29 | 30 | 2,794 | 1,239,133,101 | unread |
| May 2026 | 24/24 × 4 TF | 0/24 | 31 | 2,846 | 1,124,847,006 | unread |

April's static source lookback mechanically contains rows dated in March. No
March pack, candidate result, trade result, economic ledger or outcome was read
or emitted. March was otherwise skipped entirely.

## 3. Pack-time feature measurement

The expected outer-label mapping is exact over **2,904** physically aligned
prepared windows: frozen decision label minus two hours equals the fresh true-UTC
decision time. The only outer-window differences are the measured month edges:
eight frozen-only records at January 1 00:15–02:00 old-label time and four
fresh-only records at January 31 23:15–February 1 00:00 true-UTC time.

The prepared population is nevertheless **not** a pure relabel. In **711** aligned
windows the candidate count changes, and the same 711 windows fail whole-record
nested timestamp and `utc_hour_bucket` multiset equality. Configured membership
changes on 83,830 `session`, 83,829 `session_bucket` and 22,982 `kill_zone`
occurrences. V3 reproduces every V1 comparison metric despite carrying the correct
runtime config root, so the config mismatch was not the cause: true-UTC clock and
session-conditioned pack generation changes the population. The receipt's honest
status is `JANUARY_PHYSICAL_FEATURE_SHIFT_DIVERGED`, and it is why AW's map must be
regenerated rather than relabelled.

## 4. January economics invariance test

January is `VAL`, used once by survivor selection, and all figures below are
unbilled ranking/gradient evidence only.

| measure | CD repaired sealed-clock S0R0 | true-UTC S0R0 | delta |
|---|---:|---:|---:|
| candidates | 154,390 | 153,486 | −904 |
| physical missed rows | 154,323 | 153,425 | −898 |
| diagnostic-scoreable rows | 28,544 | 27,658 | −886 (−3.10 %) |
| trades | 63 | 57 | −6 |
| orders | 134 | 122 | −12 |
| realized physical net R | −8.94126133 | −5.50620829 | +3.43505304 |
| missed-pool mean R/scoreable row | −0.88223412 | −0.88065655 | +0.00157757 |
| gross mean R/scoreable row | −0.21975482 | −0.21749595 | +0.00225887 |
| mean cost R/scoreable row | 0.66247930 | 0.66316060 | +0.00068130 |
| negative active days | 21/21 | 21/21 | 0 |

The run took 9,096.403 seconds and peaked at 4,333,895,680 bytes RSS. It
completed all 31 days with no error or engineering stop. CD's realized-net
summary had remained machine-local; `CJ_CD_BASELINE_S0R0_ECONOMICS_V1.json`
now preserves it by cross-checking the committed CD report and hashing both the
12,560-byte lane receipt and 186,773,906-byte full economics export. The new
arm's 178 MiB duplicate full export is intentionally not committed: its small
lane receipt, 57-row trade table, runner report, aggregate pool receipt and
5.4 MiB scoreable compact pool preserve the decision-changing evidence.

The materiality rule was declared in code before the candidate arm was read:
strict equality at `1e-8 R`; material movement at 0.01 R per scoreable row, 1 %
of the scoreable denominator, or any trade-count change.

## 5. Receipts

| receipt | question answered |
|---|---|
| `CJ_SOURCE_MATERIALIZATION_V1.json` | what offline captured source exists, at what true clock and hash |
| `CJ_JANUARY_CLOCK_VALIDATION_V1.json` | 54/54 weekly opens and full bar-overlap correction |
| `CJ_HOUR_AXIS_CORRECTION_V1.json` | old-label → true-UTC table and standing-axis impact |
| `CJ_SOURCE_PLAN_JANUARY_V1.json` | canonical engine source-plan authority and three broker-day rebinds |
| `CJ_PACKS_JANUARY_V1.json` | first-generation January pack build, retained as superseded history |
| `CJ_PACKS_JANUARY_V2.json` | source-compatible but runtime-config-incompatible immutable successor |
| `CJ_JANUARY_FEATURE_SHIFT_V1.json` | initial V2 feature diagnostic; causal attribution corrected by V2 below |
| `CJ_PACKS_JANUARY_V3.json` | active source- and runtime-config-compatible January packs |
| `CJ_JANUARY_PACK_SMOKE_V3.json` | authenticated 31/31 active packs and deserialized one record each |
| `CJ_PACKS_FEBRUARY_V1.json` | superseded bare-config February generation with tick gaps disclosed |
| `CJ_FEBRUARY_PACK_SMOKE_V1.json` | initial first-record-only February smoke |
| `CJ_PACKS_FEBRUARY_V2.json` | active runtime-config-compatible February generation |
| `CJ_FEBRUARY_RUNTIME_BINDING_SMOKE_V2.json` | authenticated 28/28 February roots with no economics |
| `CJ_PACKS_APRIL_V1.json` | superseded bare-config April generation and April 30 tick boundary |
| `CJ_PACKS_APRIL_V2.json` | active runtime-config-compatible April generation |
| `CJ_APRIL_RUNTIME_BINDING_SMOKE_V2.json` | authenticated 30/30 April roots with no economics |
| `CJ_PACKS_MAY_V1.json` | May pack build with zero tick coverage |
| `CJ_MAY_PACK_SMOKE_V1.json` | authenticated 31/31 May roots without an economic read |
| `CJ_JANUARY_FEATURE_SHIFT_V2.json` | final physical record alignment and pack-time feature changes |
| `CJ_RECLOCKED_ARM_S0R0_V1..V6.json` | six pre-economics fail-closed discoveries |
| `CJ_RECLOCKED_ARM_S0R0_V7.json` | complete true-UTC January S0R0 arm |
| `CJ_CD_BASELINE_S0R0_ECONOMICS_V1.json` | preserved CD physical-net authority and source hashes |
| `CJ_RECLOCKED_S0R0_V7_LANE/` | compact arm receipt and 57-trade identity table |
| `CJ_RECLOCKED_POOL_S0R0_V1.json` | compact candidate missed-pool authority |
| `pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` | 27,658 projected scoreable rows for downstream mining |
| `CJ_JANUARY_ARM_INVARIANCE_V1.json` | pre-declared economics comparison vs CD |
| `SESSION_CJ_AB.md` | tool-emitted scoped ZERO→HEAD test fence |

All registered materialization, smoke, feature and arm looks are represented in
the central iteration ledger as `VAL`, `billed:false`. The final scoped fence is
tool-emitted `gtos-ab-receipt-v1`: **0 bad → 0 bad, 0 regressed**, with
**1,914 passed / 7 skipped → 1,933 passed / 7 skipped** over
`tests/research_infra`.

## 6. What I got wrong

1. I repeated AW's “81-cell” prose before counting the committed map. It contains
   83 B_TIME cells. The correction receipt now publishes both numbers.
2. I assumed an unsealed prefix could simply omit `_B7_5_`. The historical
   builder requires that identity inside its unchanged argument shell; the lane
   report must clear the claim after the shell has done its work.
3. I initially let the runner execute its namespace prelude twice while deriving
   the unsealed fingerprint. That one-shot prelude is now excluded from the
   fingerprint replay.
4. I treated the source-manifest root as sufficient authority. The engine also
   recomputes a canonical source-plan digest, which exposed the January boundary
   defect rather than accepting the manifest by assertion.
5. I missed the runtime logical repository root for ordered tick paths, then the
   difference between chunk-local and full-plan M1 authority. Both are now
   explicit, repo-relative inputs.
6. I assumed the first January packs remained compatible after the broker-day
   authority repair because their prepared payload rows were unchanged. Their
   source identity correctly became stale; I built a successor root rather than
   weakening the binding.
7. I then assumed source compatibility made that successor runtime-compatible.
   It did not: I had built it from a bare profile rather than the runtime's
   factorial config shell. I correctly built a third root rather than dismissing
   the mismatch, but incorrectly attributed the 711 feature/candidate changes to
   that config defect. V3 reproduces those metrics exactly; the surviving cause is
   corrected-clock/session-conditioned pack generation.
8. My config-only helper initially created an output namespace as a side effect,
   and the first V3 launch failed before building packs. The helper now derives
   config without creating a route.
9. I started a May build concurrently before noticing that pack builders shared
   one registry writer. I stopped it before registration, moved its 24 MiB partial
   root to the macOS Trash, and added an advisory writer lock before resuming.
10. I expected April's four captured tick symbols to cover April 30. The archive
   stops on April 29, and the receipt now states that boundary exactly.
11. I invoked the pool compactor before creating its `receipts/pools/` output
    directory. It failed before reading a row; I created the directory and reran
    the unchanged stream successfully.
12. My first economics comparison preserved trade counts and pool R but omitted
    the arm's realized physical net R. CD's small lane receipt and full economics
    export had survived machine-locally, so I cross-checked them against the
    committed CD report, preserved their hashes and summary, and strengthened
    the final comparator. The measured realized delta is +3.43505304 R.

## 7. Handoff

1. The trainer loop owns February's first economic read. It should predeclare the
   mechanism question and preserve February's `VAL`/used-once disclosure.
2. Regenerate AW's B_TIME map on true-UTC packs; do not relabel the old cells in
   place because session/day membership changes at the 00/01 boundary.
3. Treat January/February/April tick evidence as four-symbol only and May as
   zero-symbol until a separately captured, hashed ordered-tick estate exists.
4. The lane root is intentionally machine-local under `.hermes/`. Any move to
   another machine must copy the content-addressed estate and re-run registry,
   pack and source compatibility checks; it must not substitute absolute paths.
5. Keep March outcomes unread. April source lookback rows are not permission to
   open a March result, pool or ledger.
6. Treat `CJ_JANUARY_ARM_INVARIANCE_V1.json`, not the original invariance
   expectation, as the governing January result. Any clock-sensitive downstream
   claim must be regenerated from the true-UTC packs.
7. After integration accepts the committed compact authorities, the untracked
   full arm route and duplicate 178 MiB economics export are disposable
   machine-local working state; neither is required to reproduce this result's
   counts, trade table, pool metrics or authority hashes.
