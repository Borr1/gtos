# Session CP — virgin February rejects broad V4; the true-UTC factory yields one capture-bound candidate

Session CP · Wave 18 · Blocks B2850–B2899 · branch `phase18/true-utc-factory`

## 1. Result

The first never-read economic window in GTOS rejects another broad-family arm. February 2026 S0R0
is negative before costs, substantially worse after broker-true commission/swap repair, negative on
every scoreable trading day, below breakeven precision and negative in the 58 executed trades. The
committed pre-outcome rule therefore returns `REJECT_S1R1_AS_NOT_JUSTIFIED`; Session CP did not run
S1R1. February is now a used-once VAL surface, not a fresh holdout or admission-grade result.

Correcting the clock did not rescue AW's old B_TIME family either. All 83 cells remain economically
negative at the optimistic edge of CP's F31 interval. One cell changes label only because its
true-UTC TRAIN denominator falls below 200, not because it survives.

The new-family factory does find one genuinely different TRAIN survivor: New York-session LONG
metals. CP billed it exactly once into `CANDIDATE_BOOK_V1` V26 and invoked the frozen RECORDED gate at
the owner's all-declared `B_balanced`, alpha 0.10 rule. The gate returns `NOT_EVALUABLE`, not
`REJECT` and not `ADMIT`: the raw missed-opportunity population lacks exact fill classification and
the new generator has no measured fidelity. No activation package or ceremony dossier is warranted.

## 2. February's committed first read

The mechanism question, denominator, continuation rule and reject rule were committed in
`phase18/receipts/CP_FEBRUARY_FIRST_READ_PROTOCOL_V1.json` before any February economic row was
decoded. The source-plan sidecar authenticated 24 symbols and 28 days from CJ's foreign registry,
required zero M1 rebinds, and bound canonical digest
`3c33efe2bdfef3e97258bdef562ba42219e99ac37f6725ba2ee024880fac9fbb`
(`CP_FEBRUARY_SOURCE_PLAN_V1.json:5-29`). The registry remained read-only.

| committed first-read measure | February S0R0 |
|---|---:|
| physical missed rows | 129,165 |
| diagnostic-scoreable rows | 24,239 |
| scoreable trading days | 20 |
| unreadable proxy rows | 0 |
| executed trades | 58 |
| gross mean R / scoreable row | **-0.15055128** |
| cost-true net mean R / scoreable row | **-0.64002116** |
| positive / negative scoreable days | **0 / 20** |
| observed precision / breakeven precision | **0.309336 / 0.606359** |
| precision headroom | **-0.297023** |
| realized physical net R | **-3.96139869** |

All four minimum-denominator checks pass and all five predeclared reject predicates pass
(`CP_FEBRUARY_FIRST_READ_RESULT_V1.json:1-56`). The arm completed in 6,997.538 seconds with peak RSS
4,200,759,296 bytes. Its LANE receipt stamps all 28 calendar days VAL and
`LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade`. The raw 166 MiB aggregate
is preserved with the untracked replay route; HEAD carries the authenticated arm/LANE receipts,
44 KiB trade table, 5.1 MiB mineable compact pool and deterministic first-read result.

This answers the cheap clock-conditioned question: the broad V4 family's negative direction
persists on a virgin true-UTC month. It does not prove every future broad-family variant is negative,
but it removes the only justification in the committed protocol for paying for S1R1.

## 3. AW B_TIME regenerated, not relabelled

`CP_TRUE_UTC_B_TIME_MAP_V1.json` regenerates the same 83 declared cell identities from CJ's
true-UTC January compact pool. Membership is recalculated at the true hour/day boundary; no old
cell statistic is renamed. The F31 lower edge conservatively charges -0.038186 R to every row because
the compact projection lacks exact exit provenance.

- 82 verdicts remain `F1_TRAIN -> F1_TRAIN`.
- `authority_session==moonshot_h07_08` moves `F1_TRAIN -> F1_TRAIN_DENOMINATOR` because true-UTC
  TRAIN `n=193`, below the 200-row floor; its optimistic TRAIN mean is still -2.11150374 R/row
  (`CP_TRUE_UTC_B_TIME_MAP_V1.json:3611-3672`).
- The best optimistic TRAIN cell is `session_bucket==london` at -0.42798732 R/row; therefore all
  83 optimistic edges are negative (`CP_TRUE_UTC_B_TIME_MAP_V1.json:5-77`).
- All 83 looks are append-only and unbilled. Receipt root:
  `8e19f609911727c8aa5619c14c8080514c8f0db8ac1b430cbc75f326a80b6d96`.

Downstream work should stop citing AW's wrong-clock B_TIME economics. The one changed label is a
denominator change, not evidence for the mechanism.

## 4. The true-UTC candidate factory

The factory declared 28 time predicates crossed with 39 pretrade conditions: **1,092 looks**.
It evaluated only the first 13 January TRAIN days (16,248 scoreable rows); the eight January holdout
days were not economically evaluated by the factory. A cell survived only with at least 200 rows,
10 days, positive mean at the F31 lower edge, lower-edge precision above 0.50 and at least 60%
positive days. Protocol root:
`d65d74e1faf044b8e1486dd4595587de42e7a6c74ef51d78219f0f1368567d63`.

First-failure accounting is complete: 726 cells fail minimum rows, 362 fail positive lower-edge
mean, three fail lower-edge positive-day breadth, and one survives
(`CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json:5-32`). The survivor is:

| field | value |
|---|---|
| cell | `route_session_ny__asset_metals__direction_LONG` |
| candidate | `1493e333da89dbd6` |
| spec digest | `0f4382260c4b5ba8b1acb03d624c5ecf51d8decb46f448fa1287327263631ff7` |
| TRAIN population | 290 rows / 13 days |
| mean R interval | **+0.08929324 to +0.12747924** |
| precision interval | **0.63448276 to 0.72068966** |
| lower-edge positive-day share | **0.61538462** |

This is a TRAIN survivor, not a sealed-gate pass. The factory receipt is rooted at
`66dc811f3941c65dd1370040994fad2b1c9ae9dd1544df75fa49279a30c44f4f`; all 1,092 physical rows are
unbilled iteration looks.

## 5. One graduation bill; frozen gate honestly refuses

The survivor graduates exactly once as `cp_true_utc_ny_metals_long_v1`. V26 raises the ratcheted
`CANDIDATE_BOOK_V1` all-declared size **57 -> 58** and looks-taken size **55 -> 56** while preserving
the owner's `B_balanced`, alpha 0.10 rule (`CANDIDATE_FAMILY_V26.json:5048-5049,5885-5889`). The
graduation ledger contains one CP row and one billed look.

CP then ran the real frozen gate with the V26 declaration, RECORDED population stamp and mid cost
band. The source audit prevented a false verdict:

- the full raw holdout population has 249 matching candidates; the compact mining projection has
  only 121 scoreable rows and is not the gate population;
- all 249 raw rows lack `counterfactual_order_fill_status`, so there are zero exact filled records
  and zero explicit no-trade records;
- the ordered-path oracle has 61 executed/selected rows and joins zero of the 249 missed candidates;
  zero join coverage cannot be interpreted as zero fills;
- decision time cannot substitute for fill time, planned entry cannot substitute for actual fill,
  net proxy cannot substitute for gross R, and no holding period may be assumed;
- the new sleeve also has no registered generator-fidelity measurement at the frozen 0.50 recall
  floor.

The resulting status is
`FROZEN_GATE_NOT_EVALUABLE_SOURCE_AND_FIDELITY_CAPTURE_REQUIRED`
(`CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json:288-342`). Its receipt root is
`f0b9127a1d92271f9992ddec20bb55a4b0f5838051a5edeba4b8dc5b07500482`. Multiplicity is paid, but
there is no admission, rejection or activation claim.

The exact next capture contract is already filed at lines 5-19 of that receipt:

1. Generate the declared NY-metals-LONG policy as an executable candidate population over untouched
   OOS RECORDED eras.
2. Persist exact fill/no-fill classification and, for each fill, fill UTC/price, exit UTC, pre-cost
   gross R, terminal reason and a content-bound path source.
3. Measure and register generator fidelity at the frozen 0.50 recall floor.
4. Re-run the same V26 all-declared RECORDED `B_balanced` alpha 0.10 spec without another graduation
   bill.

## 6. Research-path repairs

The first attempt to launch February exposed a real engine hazard: a registry-backed run could
silently fall back to January. `train_engine/runner.py:220-249` now requires an explicit registry
window, rejects orphan window/source-plan arguments and reports the resolved window. The CLI contract
is pinned at `runner.py:536-589`.

CJ's registry is machine-local to another worktree. `lane_rematerialization.py:214-247` now derives
the registry's logical owning repo, resolves its relative authority there, writes outputs only in the
current worktree, and restores the logical cwd around the legacy engine path
(`lane_rematerialization.py:1463-1519`). `inspect_canonical_source_plan` measures a read-only sidecar
without mutating the foreign registry (`lane_rematerialization.py:1874-1907`). Behavioral tests cover
the explicit-window refusal, foreign-root portability, local output isolation and sidecar digest.
Neither modified research-infrastructure path appears anywhere in the R2 decision contract, so CP
did not move a bound economic input or regenerate sealed authority.

## 7. Look accounting

The append-only iteration ledger contains **1,177 CP rows, all unbilled**:

| mechanism | rows | billed |
|---|---:|---:|
| February canonical source plan | 1 | 0 |
| regenerated B_TIME | 83 | 0 |
| true-UTC factory | 1,092 | 0 |
| February S0R0 | 1 | 0 |

The separate graduation ledger carries exactly one CP row and one billed look. No row was rewritten
after a failed attempt, and no second February read exists.

## 8. Verification and safety boundary

The focused CP behavioral fence is **90 passed, 0 failed, 0 errored**; the only warning is the
repository's existing unknown pytest option `asyncio_mode`. It covers the engine/registry repair,
committed first-read evaluator, B_TIME regeneration, factory, recorded-gate refusal and family-chain
ratchet. The final failset tool derives a 30-path closure reaching 10 test files and records
**142 passed, 0 failed, 0 errored**. Against the committed suite-wide **12,671 passed / zero-bad**
baseline, `phase18/receipts/SESSION_CP_AB_RECEIPT.md` reports **0 bad -> 0 bad, 0 regressed** in its
unedited embedded `gtos-ab-receipt-v1` fence. The scope difference is declared in the receipt; the
orchestrator owns the next whole-suite train capture.

Session CP did not read a March 2026 outcome or live-forward TEST row, contact the VPS, run a
broker-capable script, touch an activation token, edit either token-bound config/profile byte, or
build an activation package. The replay routes and mandatory generated `.context/LIVE_STATE.md`
remain unstaged. The 166 MiB raw economics aggregate is preserved route-local rather than added as
another generated inline blob.

## 9. Orchestrator handoff

1. Treat February as used-once VAL evidence and the broad V4 continuation probe as closed; do not
   run S1R1 under this protocol.
2. Replace every downstream citation of AW's wrong-clock B_TIME map with
   `CP_TRUE_UTC_B_TIME_MAP_V1.json`.
3. Carry V26 forward as the multiplicity authority. Do not bill the CP candidate again when the
   four-part capture contract is satisfied.
4. The next useful build is executable NY-metals-LONG candidate capture plus measured generator
   fidelity over untouched RECORDED eras. Reinvoke the frozen spec only after both exist.
5. Do not queue ceremony work: the candidate is `NOT_EVALUABLE`, not admitted.

## 10. What I got wrong

1. My first progress grep was too broad and surfaced partial economic fields before the arm
   completed. I did not use or report those values, narrowed every subsequent checkpoint to completed
   day and row count, and let the committed evaluator make the first decision.
2. I initially treated the 121 compact scoreable holdout rows as the candidate's gate population.
   The raw-ledger audit proved 249 matching candidates. I rebuilt the receipt on the full raw
   population before committing it; the 121-row projection is now disclosed only as a mining subset.
3. I briefly considered a second February candidate re-read after defining February as used once.
   I stopped before launching or producing any artifact. The ledger has exactly one source-plan look
   and one S0R0 arm for February.
4. The first compactor invocation failed before reading a ledger row because I had not created
   `phase18/receipts/pools/`. I created the directory and reran the same command; no partial output or
   statistic existed from the failed call.
5. The runner emitted a 166 MiB plaintext economics aggregate into the receipts directory. Nothing
   bound that path and it duplicates route ledgers, so I preserved it byte-for-byte inside the
   untracked replay route and committed the compact, mineable evidence instead.
