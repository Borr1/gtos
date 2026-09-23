# Wave 11 working agreement — contract truth and conditioning-to-sizing

Deltas from `WAVE_10_WORKING_AGREEMENT.md`; everything not restated is unchanged.

## 1. Authority and the live accounts

**BOTH accounts are armed and trading real money** (FTMO 2026-07-29, redacted_account 2026-07-30,
same three sleeves — CLAUDE.md §4). Never run a broker-capable script; never edit
`config/agent_config.yaml` OR `config/profiles/redacted_account.yaml` (both now carry live authority;
the FN token binds its profile's bytes); the VPS is the orchestrator's only. H1 membership check
before editing under `src/`. Standing owner directives: sessions use their own judgment;
build/improve/fix, never refute-and-stop; Workflow tool opt-in is standing.

**The population rule is RATIFIED — `RECORDED`, with conditions** (Borhen 2026-07-30,
`phase10/receipts/POPULATION_RULE_V1.json` → `ratified_rule`, test-pinned). Binding on every
admission-grade claim this wave:

- Gate on `RECORDED`; publish the **band column alongside** (flat/low/mid/high) and phrase
  admissions as "admits at N of 3 bands" — never bare.
- The family is **V3 (39 declared)** plus the ratchet; declare new looks BEFORE gating, and
  declare the **cut rule, not just the axis** — AO's pair admission died on an undeclared
  median cut; a Bonferroni over the cut rules you tried is the minimum honest bill.
- **Publish the chronological fold table on every admission-grade claim.** `stability` counts
  fold signs only; AN measured a 7.6× decay that every gate passes. Anything that will be
  sized quotes the RECENT folds as its expectancy basis.

## 2. New binding verification lessons (from AN/AO, now standard)

- **Permutation resolution floor:** before quoting a permutation p at small n, compute the
  achievable assignment count (2^blocks for sign tests). If your rank's BH bar sits at or
  below `1/achievable`, the test cannot admit there — report `NOT_EVALUABLE_AT_RANK`, not a p.
  Seed-sweep any p within 3 sd of its floor.
- **Identity-filter check:** before conditioning on a variable, prove the sleeve does not
  already pin it (max |Δ| and bucket-disagreement count over all trades). A gate on a pinned
  coordinate is a no-op that reads as a result.
- **Silent nulls fall loudly** (wave-10 §2 rule, re-affirmed — AN found a verdict-inverting
  one in its own adversarial file).
- A/B by copy-back, never `git checkout`; scoped `pytest_failset.py scope` at HEAD; the
  committed baseline is ZERO — the full-suite A/B is the orchestrator's, once per train.

## 3. Ledger and artifacts

Trial ledger and `REPAIR_QUEUE_APPEND.jsonl` are append-only, union-merged at the train.
Stamp the cost band on every arm. Seals split by population now (AN's wiring) — two runs on
two populations can never share a `spec_sha256`.

## 4. Block allocation

Wave 10: AN `B1250–B1266` · AO `B1300–B1349` — landed. AP `B1350–B1399` — in flight.
**Wave 11: AQ `B1400–B1449` (contract truth) · AR `B1450–B1499` (conditioning to sizing) ·
AS `B1500–B1549` (challenge books — commissioned on Borhen's 2026-07-30 explicit approval
of the two challenge-account levers and the full edge program).**
**Wave 12 (commissioned at the wave-11 train, 2026-07-30): AU `B1550–B1599` (contract
wiring + estate restamp) · AV `B1600–B1649` (the sample engine).** Wave-12 deltas, binding:
every exit sweep reports its `maxbars` share; the identity-filter check runs BOTH layers
(bucket count and level count) for continuous consumers; compounded book return is NOT a
valid instrument for a sizing change (use risk-weighted efficiency with blind-constant
controls); any small-n permutation p is seed-swept near its resolution floor.
AW `B1750–B1799` (separability mine — commissioned 2026-07-30 on the owner's challenge to
the campaign park; JANUARY_BANK §3's open question, measured for the first time.
RENUMBERED from B1650–B1699 at the wave-12 train: AV overran its range to B1670 before AW
started, and a pre-declaration is cheaper to move than written blocks are).
AX `B1700–B1749` (the fast sealed engine — new files beside the frozen one, R2 untouched;
acceptance = sealed January reproduced R-identically at a fraction of the wall-clock).
**Wave 13 (commissioned at the wave-12b train, 2026-07-30): AY `B1800–B1849` (the
spread-geometry repair — AW's dividend; per-sleeve, generation-side, armed-four activation
package) · AZ `B1850–B1899` (the mx_btcusd activation carry, built to the transfer step —
the orchestrator executes the ceremony) · BA `B1900–B1949` (weekend solution) · BB
`B1950–B1999` (fill truth + sleeve supply) · BC `B2000–B2049` (command center) · BD
`B2050–B2099` (live-path debt sweep) — the run-all wave, owner-ordered 2026-07-30.**

**AY has LANDED — B1800–B1841 written, its range retired by its own author**, which emptied
`IN_FLIGHT_WAVE_RANGES`; the guard refuses an empty table, so AY pointed it at **AZ's
`B1850–B1899`** as a pre-declaration (above the ceiling, exempting nothing today, working the
moment AZ writes its first block). AZ inherits that entry and owns retiring it.
**Wave 14 — the training-lane wave (RATIFIED by Borhen 2026-07-31,
`phase14/TRAINING_LANE_RATIFICATION.md` is the constitution and binds every session below):
CA `B2100–B2149` (the revival gates — the three carry-conditional sleeves re-gated on the
fetched data at the ratified rule, plus BB's fill-truth restatement of the armed book's
published cadence) · CB `B2150–B2199` (the train-grade engine — TRADE-OUTCOME identity, not
provenance; R2 and the frozen engine untouched) · CC `B2200–B2249` (the protocol machinery —
surfaces, one-bill graduation, incubation registry; owns `trainer_partitions.py` this wave,
CB imports it) · CD `B2250–B2299` RESERVED (broad-family regeneration under the repaired
stack — commissioned when CB's engine passes acceptance).**
**Wave 15 (commissioned 2026-07-31 on OD-HISTORICAL-FIRST, `phase15/OD_HISTORICAL_FIRST_SCALING.md`):
CE `B2300–B2349` (the sleeping-improvements activation package — AY floor carry, ratified
entry-hour implementation, weekend recommendation, promotion rules restated
historical-primary) · CF `B2350–B2399` (commissioned on the orchestrator's symbol-rename
event receipt).
**CF LANDED, and the event is REFUTED: there was no rename** — the probe compared GTOS canonical
names against FTMO's tree, the live profile has always mapped those to the `.cash` names, and
every target was already present six days earlier; 0 unresolvable across 137 slots on both
accounts, so no member was ever mute and the armed book was never degraded. The watchdog was
built anyway, because a real rename would have been SILENT
(`bar_provider.py:120-125` + `book_engine.py:563`). See
`phase15/SESSION_CF_SYMBOL_RENAME_RESULT.md`.**
**CG `B2400–B2449` (the lane's footprint and floor — sidecar projection, CD's projections
absorbed, the sink fork, the dirty-memo re-keys behind per-call verify; the estate's FIRST
CODEX session, per Borhen's 2026-07-31 direction that engine-lever sessions run on Codex/sol
at max effort).**
**CH `B2450–B2499` (the two measurements that arm levers — P1-HIST milestones M1/M2 on CE's
declared looks; the JPY hour-00 gate on the orchestrator's fresh 2022+ M15; per-account
silence thresholds) · CI `B2500–B2549` (the third-party M1 ingest with declared provenance —
vp_euidx_pocgrav decidable now instead of September; OD-HISTORICAL-FIRST §2 + the owner's
"data is data"). Both Codex/sol, full access.**
**CH has LANDED — B2450–B2467 written, its in-flight range retired by its own author.** P1-HIST
does not promote (`M1 FAIL`, strict `M2 UNREACHABLE`, `M3 PASS`, `M4 FAIL`); the JPY hour-01
lever is DO-NOT-ARM because every ratified gate is NOT_EVALUABLE and random s1 beats h01;
current-set FTMO/redacted_account silence thresholds are 14/21 and 15/22 weekday sessions.

**Wave 16 (commissioned 2026-07-31 on the owner's SEAL-BREAK authorization — "yes you can
break the seal and proceed as proposed"): CJ `B2550–B2599` (the re-materialization — true-UTC
sources and day packs for Jan/Feb/Apr/May 2026 as LANE inputs; the parked B7.5 campaign's
resume option dies with it, by owner word, recorded in the decision queue) · CK `B2600–B2649`
(the mechanism autopsy — H-CD-8 on the committed repaired pools, zero replay, plus the
`--days` hang fix). Both Codex/sol, full access.**
**CG, CK, CH and CI have ALL LANDED — one train, 2026-08-01, zero→zero at 12,600 (+78), every
in-flight range retired by its own author** (`receipts/WAVE16A_TRAIN_AB.md`). CG: lane floor
480 s / 2.9 GB, full-January arm 1.918 GB allocated — disk no longer binds. CK: the mechanism
is heterogeneous and cost-vetoed — `current_breaker_re_entry` carries 21.55 % of all negative
gross (repair target); `liquidity_sweep_reclaim × LONG` is persistently gross-positive and
cost-killed; the 99-cell grid awaits path-complete pools; CB-3.3 proven at 2/12/20 days.
CH: both levers DO-NOT-ARM (P1-HIST fails, h01 loses to a random control); quiet-book
thresholds live (FTMO 14/21, FN 15/22). CI: GER40/UK100 M1 2024+ landed with provenance;
vp stays NOT_EVALUABLE on UK100 volume semantics — the unblock is named.

**Wave 17 (commissioned 2026-08-01 under OD-ALL-IN — `phase17/OD_ALL_IN_20260801.md`, the
owner's direct-to-live directive, verbatim inside): CL `B2650–B2699` (pass-surface widening —
every armed-set extension priced at firm-true rules, incubation proposals, ceremony package) ·
CM `B2700–B2749` (armed-money exit fidelity — every measured-better exit on armed sleeves,
`energy_agri` scale-out answered, `--frontier-exits` packages) · CN `B2750–B2799` (H-CD-2 —
the live path charges zero commission; wire CD's prepared adapter, R2-bound edit authorized
by the standing seal break) · CO `B2800–B2849` (learning-lane live activation — bounded
weights, fail-closed to ×1.00, decision-day boundaries only). All Codex/sol, full access.
CP (new-family generation on true-UTC data) and CQ (path-complete pools + frozen 99-cell grid
+ `current_breaker_re_entry` repair) launch the moment CJ lands. The orchestrator executes
every ceremony; token re-mint done 2026-08-01 (both accounts valid to 2026-08-14, digests
unchanged, minted flat 0/0).**

**CJ, CL, CM, CN and CO have ALL LANDED — one train, 2026-08-01, every in-flight range retired**
(`receipts/WAVE17_TRAIN_AB.md`). CJ: the clock correction is real (old label = true UTC + 2 h,
54/54 weekly opens) and the January invariance hypothesis is FALSE — re-clocked S0R0 moves
−8.941 → −5.506 R (+3.435) with trades 63→57; February is the first never-read window and the
lane's true-UTC estate exists for Jan/Feb/Apr/May. CL: **the direct pass-surface addition set is
EMPTY on both accounts** — both JPY −0.1121 ΔP2 FTMO, `metals_core` ×0.50 −0.1198, softband
positive-but-carry-conditional, FN MX fails CH's gate, VP unpriceable; two incubation proposals
filed at 0.025 (ETH target-5R, Asia PDL stop-2.5) with pre-registered stops; its ceremony is a
sealed no-op host verification. CM: ONE armed-money exit repair selected — FTMO
`crypto@stop_1p5x_target_scale` (+0.25267 R/day pooled, +0.03552 latest fold = the planning
basis, 4/5 folds, all bands); redacted_account explicitly NOT selected (latest fold −0.18613); energy
scale-out honestly open (lane cannot beat n=67). CN: H-CD-2 fixed — commission is the default
fourth cost term, fail-closed on missing truth; 174 same-input decisions, 7 flips ALL
conservative (redacted_account oil); packets move to v3 with v2 readable; the one R2-bound edit is the
authorized forward seal break. CO: the lane's first live vector — FTMO `crypto` ×1.15 and
`mx@target_5R` ×1.15, everything else ×1.00, FN all-neutral; signed all-or-neutral HMAC envelope,
band [0.50, 1.15], boundary-latched, governor senior; activation window 2026-08-02
00:00:00–00:05:00 UTC, declarations expire 2026-08-08. **Three host ceremonies (CM + CN + CO)
compose at the 2026-08-02 boundary — the orchestrator executes; `book_owner.py` is carried by
BOTH CN and CO, so CN's two anchored additions are rebuilt on CO's after-bytes per CN's own
ceremony §1, never last-copy-wins.**

**Wave 18 (commissioned 2026-08-01 under OD-ALL-IN, launched on CJ's landing as promised):
CP `B2850–B2899` (`phase18/SESSION_CP_TRUE_UTC_FACTORY.md` — February's first economic read
with a pre-declared question; AW's B_TIME map regenerated on true UTC, 83 cells; new-family
generation on the corrected hour axis; candidates go to the sealed gate) · CQ `B2900–B2949`
(`phase18/SESSION_CQ_PATH_POOLS.md` — path-complete pools under CK_POOL_PATH_CONTRACT_V1 on
true-UTC packs; the frozen 99-cell grid answered exactly; `current_breaker_re_entry` repair
gated at the ratified rule; first-touch ambiguity retired by measurement). Both Codex/sol,
full access. CP owns February's outcome read; CQ builds pools without decoding outcomes.**

**CP and CQ have BOTH LANDED — one train, 2026-08-01, both ranges retired.** CP: **virgin
February REJECTS broad V4 at true UTC** (−0.151 gross / −0.640 net per scoreable row, 0/20
positive days, precision 0.309 vs 0.606 breakeven; the committed pre-outcome rule returned
`REJECT_S1R1_AS_NOT_JUSTIFIED` — the continuation probe is CLOSED). AW's B_TIME regenerated:
all 83 cells negative at the optimistic edge; **stop citing the wrong-clock map** — the
authority is `CP_TRUE_UTC_B_TIME_MAP_V1.json`. The 1,092-look factory produced ONE TRAIN
survivor: `cp_true_utc_ny_metals_long_v1` (+0.089..+0.127 R/row, precision 0.63–0.72), billed
once; the frozen gate refuses honestly (`NOT_EVALUABLE` — no fill classification, no measured
fidelity) with the four-part capture contract filed. CQ: path-complete January (27,658 rows,
3.23 M path observations); all 198 grid cells answered — suppression insufficient, as-declared
breaker dead in every cell, **INVERSION at target 5D / stop 0.25D is +11.88/+11.93 net R/trade
on TRAIN/HOLDOUT** (survivor-selected VAL, not expectancy; the full-pool control stays
negative, so this is a mechanism repair, not a book reversal); liquidity reclaim re-priced
through CN's exact chain — still cost-vetoed; **CK's first-touch bound retired: 0/27,658
ambiguous at recorded geometry**; default-off transform wired behind an absent-false key; gate
`NOT_EVALUABLE` at one fold of three. **Chain fork resolved at integration: both sessions
graduated against V25 in parallel; V26 = CP's, V27 = union tip at 59 declared / 57 looks**
(`phase18/receipts/CANDIDATE_FAMILY_V27.json`; CQ's fork receipt preserved).

**Wave 19 (commissioned 2026-08-01, the two gate-completing captures): CR `B2950–B2999`
(`phase19/SESSION_CR_NY_METALS_CAPTURE.md` — CP's four-part capture contract: executable
NY-metals-LONG over untouched OOS RECORDED eras with fill classification, measured generator
fidelity at the 0.50 floor, then the SAME frozen spec at the V27 tip, no new bill) · CS
`B3000–B3049` (`phase19/SESSION_CS_BREAKER_FOLDS.md` — CQ's prescription: two more
path-complete chronological folds from CJ's economics-unread April+May true-UTC packs,
declared before reading, then the UNCHANGED ratified gate at ≥3 folds). Both Codex/sol, full
access. If either ADMITS, the dossier goes to the orchestrator's ceremony queue under
OD-ALL-IN — CL-class firm-true pricing first, then the arming ceremony.**

**FA `B3050–B3099` (`phase19/SESSION_FA_BROAD_FORENSIC.md` — OD-BROAD-FORENSIC, the owner's
2026-08-01 mandate, verbatim inside the commission): the broad-V4 full forensic, run on
FABLE with Fable subagents through the Workflow tool — not Codex, not Opus, by owner word.
Walk the decision cycle in the replays from the top level to the last trade/reject with the
context of each decision; attribute every lost R in re-clocked January and virgin February to
a named stage/mechanism; name the gate that declined each class of the pool's positive
candidates; deliver the ranked repair list to the sealed gate. Kill/park authority over the
family is Borhen's alone — the prior "closed for good" framing was the orchestrator's
overreach and is withdrawn; the measured record (February REJECT of the S1R1 continuation
under CP's protocol) stands as measurement, not as a kill.**
**CE has LANDED — B2300–B2340 written, its own range retired by its author.** Session CE wrote
to **B2340**, which raises the ceiling past its still-in-flight sibling CD and therefore makes
CE the owner of `IN_FLIGHT_WAVE_RANGES` under the rule below. **CD's `B2250–B2299` changes
CLASS rather than going away**: it entered as a pre-declaration above the ceiling and is now
**ACTIVE**, because `B2250` is cited as an individual token in six files that the ceiling no
longer covers. It stays until CD's blocks land and **CD owns retiring it**. (CE's first reading
was that the entry had gone dead and dropped it; the guard's next assertion named `B2250` and
the six files, which is the guard doing exactly its job.)

**Wave-19 LANDING record (written 2026-08-03 by FA-continuation — the record was missing; this
closes it).** CR `B2950–B2999` and CS `B3000–B3049` landed on their branches with receipts (CR:
capture infrastructure + the four-part contract, class REPRICED after February's own funnel went
gross-negative on NY-metals; CS: the two folds + the ratified gate → REJECT at q=0.1534, six
`billed:false` ledger rows — verdict later superseded by the A1 corrected-null adjudication,
see the method-defect row). **FA's Phase-2 workflow died 100 % on the weekly API limit having
written ZERO blocks; five Codex sessions FB–FF executed FA's five dead lanes instead**
(sol-grid/exit/defects/conditions/composition), FG cherry-picked all 66 CR/CS/FB–FF commits
onto `phase19/sol-integration` (rewritten SHAs — the source branches must NEVER be separately
merged) and ghost-wrote FA's result doc. Every FB–FF headline was spot-recomputed from raw
pools by FA-continuation's A2 lanes (`phase19/receipts/forensic/a2_verify/`): FB bit-identical
over all 198 grid cells; two circulating claims REFUTED (the "V17 sign-flip registration"
naming; FE's persistent-gross count 4→5); the loss-class rule contradiction resolved and
ratified (counterfactual-exit partition). Disposition of all 28 branches:
`phase19/receipts/forensic/SOL_DISPOSITION.md`.

**Wave-20 commission/disposition record (same author, same closure).** Wave 20 = HG's
preregistration (`phase20/WAVE20_SCIENCE_PREREGISTRATION.md`, 412 lines, authorized no
execution) + the falsifier-paired chain HA/HDA → HB/HDB/HDE → HC/HDC/HDF → HI/HIA → HK →
HL/HM → p1-offline-result → HN → p1-upstream-falsifier → HP (tip `502d90616`) + HV
(uncommitted). No block range was ever taken by any wave-20 session and no WA record existed —
this entry is the disposition of record: the chain landed via FA-continuation's integration
branch `phase19/fa2-integration` (tip fast-forward + five doc-only close leaves HK/HL/HM/HN/HIA
+ HV adoption + the HM-falsifier reconciliation + the docs→src relocation), fenced by
failure-set A/B against the sealed 12,809/2/0 baseline (zero regressions;
`phase19/receipts/SESSION_FA_AB_RECEIPT.md`) and by a 2-day lane-arm outcome-identity diff.
`phase20/p1-m1-sparse-repair` DISCARDED (HP repudiation). Node dispositions:
`phase19/receipts/forensic/WAVE20_SUPERSESSION_REGISTER.md`. The breaker-flip contest (CS
REJECT vs HDC/HDF ADMIT) was adjudicated BLIND by FA-continuation's A1 clean-room: the
common-circular-phase permutation rule is not rotation-invariant (verdict flips at 14/31
rotations; support capped at 2¹¹), and at the corrected null the candidate ADMITS
(p 0.00130, q@59 0.0769, α 0.10) — with the fragility disclosures in
`phase19/receipts/forensic/a1_cleanroom/A1_CLEANROOM_NULL_DERIVATION.md`.

**FA-continuation block take (2026-08-03): FA continues `B3050–B3099` (unwritten by Phase 1)
and takes `B3100–B3199`** — rg-swept unclaimed before the take (only the continuation
commission and its resume state mention the range). Blocks land in IMPLEMENTATION_STATE.md at
the continuation's synthesis; the ranges retire in its closing commit.

Need more? Next free range is `B3200–B3249`. Whoever raises the ceiling past a sibling owns
`IN_FLIGHT_WAVE_RANGES`.

## 5. Done means / reporting

Unchanged from wave 9 §6–§7: result doc findings-first, receipts committed, an honest
"what I got wrong" section, and a handoff list for the orchestrator.

**A/B receipts MUST be the tool-emitted `gtos-ab-receipt-v1` fence**
(`scripts/pytest_failset.py receipt`), never prose — three prose receipts have failed the
guard at merge trains (AO, AV, AW) and each cost a re-capture at the merged tree.

## 6. Training lane (ratified 2026-07-31, machinery landed wave 14)

`phase14/TRAINING_LANE_RATIFICATION.md` is the constitution; this section is what binds a
session. Operating manual: `phase14/TRAINER_SESSION_TEMPLATE.md`. Code:
`src/research_infra/training_lane/` and `trainer_partitions.SurfaceMap`.

**Two axes, two verbs. Do not read one for the other.** `Disposition.trainable` says whether a
model may be **FITTED** on a day; `SurfaceMap.surface_for_day` says whether the lane may
**ITERATE** against it. They disagree on purpose — January 2026 is `SEALED` on the first and
`VAL` on the second. `lane_disposition_for_day(day)` returns both together; use it whenever the
answer will be written down.

### The three surfaces

| surface | span | rule |
|---|---|---|
| **TRAIN** | 1992-02-18 … 2024-12-31 | iterate freely, **unbilled**. Every look still logged. |
| **VAL** | 2025-01-01 … 2026-05-31 | ranking and gradient checks only, unbilled, logged. **Used-once by survivor selection** (`d.year >= 2025`, `build_survivor_book.py:74` / `KB7_growth_kelly_sizing.py:130`) — the disclosure travels on every stamped row; headline expectancy is never quoted from VAL alone. |
| **TEST** | March 2026 + every blackout; the live forward stream from **2026-07-29** | **never trained on, never iterated against.** Sealed gate and live monitoring only. |
| *(uncovered)* | 2026-06-01 … 2026-07-28 | **refused.** A declared gap, not an oversight: already consumed by every full-history gate walk (`GateSpec.global_span` ends 2026-07-27), so it is neither virgin nor open. Opening it is an owner/orchestrator decision and the honest label would be TRAIN. |

Session CC tightened the ratified frame in five places and loosened it in none; the record is
`phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json` → `tightenings_vs_the_ratified_frame`. The
load-bearing one: **the frame's "April's 15 sealed days" read as "April" would have opened
2026-04-16 … 04-30, fifteen days whose outcomes have never been read.** They are VAL.

### Logging — every look, immediately

`IterationLedger(session="XX").record(...)`, append-only, shared path
`phase14/receipts/TRAINING_LANE_ITERATION_LEDGER.jsonl`. You pass **dates**; the map computes
the surface stamp. Three things you cannot forge: the surface (computed, not accepted), the
verdict (`admitted`/`rejected` are the gate's words and raise), and `billed` (written `false`,
not a parameter).

A full-history walk declares `engine_reserved_blackout=[["2026-03-01","2026-03-31"]]` — spanning
March is not consuming it — and names the gap it crosses via `acknowledge_uncovered=`. Both
declarations land in the row. **TEST has no such escape hatch and never will.**

Log as you go, not at the end. An unlogged look cannot be graduated on.

### Billing — the one-bill rule

- **Iteration on TRAIN/VAL bills nothing.** The iteration ledger is a **sibling** of the DSR
  trial ledger, never a field on it: `measured_n_trials()` feeds DSR deflation, so lane looks
  written there would raise the estate's bill with every exploration. The two are reported side
  by side and never summed.
- **The family ratchet moves ONLY through `training_lane.graduation.graduate()`**, which bills
  **exactly one look**, atomically, with the candidate's provenance chain attached. It refuses:
  `provenance_missing`, `provenance_touches_test`, `provenance_spec_mismatch`,
  `declaration_lost_the_rule`, `unknown_family`. It is idempotent — a retry completes the
  receipt, it does not re-bill.
- **Every successor declaration goes into `candidate_family.DECLARATION_CHAIN` in the same
  commit.** `test_no_declaration_on_disk_supersedes_the_chain_head` goes red until it does.
  This is not bookkeeping: the chain was nine versions stale and the default resolved a **51 %
  under-bill** (35/32 against a true 53/50), in the permissive direction (B2204).
- **The sealed gate is FROZEN.** `CANDIDATE_BOOK_V1` basis, sealed `B_balanced` α = 0.10,
  RECORDED population with AN's conditions. Nothing in the lane changes what it takes to admit —
  it changes how cheaply we can search.

### Incubation

≤ **5 concurrent armed** incubants, each ≤ **0.05-class** confidence weight, each carrying a
pre-registered **stop** rule AND a pre-registered **promotion** rule with a `basis` naming the
artifact its threshold came from. Registering a dossier does not consume capacity; **arming**
does. Every transition needs an `OwnerCeremony` with who decided, when, and the receipt — rules
dated after the arming are refused as not-pre-registered.

`admission_basis` is `GRADUATED` (cite the graduation record) or `OWNER_RISK_ACCEPTED` (cite
the owner's decision). Both are legitimate and they are **not the same claim** — the estate has
one of each, and blurring them is how a risk-accepted sleeve gets quoted later as an admitted
one. Arming, pulling and promoting stay Borhen's ceremony every time.

**Promotion rules are HISTORICAL-PRIMARY (OD-HISTORICAL-FIRST §1; Session CE, B2338).** Before
an incubant is armed its promotion rule must pass three tests:

1. **Can it fire without waiting for the live stream?** If no, it is mis-derived and gets
   restated before arming. A rule whose binding clock is a live fill count measured in months
   is the named failure — `mx_btcusd`'s was 60 fills ≈ 51 calendar months, and CA's own dossier
   said it was "an argument for a cheaper instrument rather than a schedule".
2. **Is every milestone reachable with data that exists?** A milestone needing a capture is
   legitimate only if the capture is priced and scheduled (§2: *missing data is an action item,
   never a verdict*). One needing data nobody can get is a 51-month rule with better prose.
3. **Is the false-promotion probability stated?** CA stated its own; that is the standard. When
   it is an analytic bound rather than a bootstrap, say so and name the assumptions — and if
   the restated rule is WEAKER per decision than the one it replaces, say that too. It usually
   is; the trade is speed.

The **live stream is a veto**: it blocks a promotion and can stop a sleeve, and it never
accumulates toward one. **Stop rules are unchanged by any restatement** — they are the veto,
they are `RISK_BOUND_not_inference`, and they stay fast. The **look budget for the whole
promotion ladder is declared before any of it runs** and billed through `graduate()`; "re-gate
as the archive grows" is an undeclared group-sequential design and is refused.

Rules are amended through `IncubationRegistry.amend_rules()`, never by editing a sealed
dossier. An amendment needs an owner ceremony, a stated reason, the superseded rule ids, **both
directions together**, and the **live record at the moment of amendment** — the field that tells
the next reader whether the rule could have been fitted to the stream. Zero-fill amendments are
marked `amended_on_a_virgin_record`; later ones are not refused, only made impossible to miss.
Worked example and template: `phase15/CE_PROMOTION_HISTORICAL_FIRST.md`.

### OD-HISTORICAL-FIRST (2026-07-31), binding on every session

`phase15/OD_HISTORICAL_FIRST_SCALING.md`. The live stream is a **veto, never the clock** —
no rule may use live sample accumulation as its binding timer; "missing data" is an action
item for the orchestrator, never a verdict; a measured, controls-clean improvement to an
armed sleeve sleeping behind a default-off flag is a **defect state**. Unchanged and load-
bearing: the sealed gate, TEST inviolability, token/seal/ceremony discipline, the owner's
dial — they are what make "confirmed historically → live with no fear" a rational sentence.

### Language rules, binding

- **"dead" / "corpse" are BANNED** for any family whose repair paths have never run through the
  lane. The honest label is **`UNTESTED_UNDER_REPAIRS`**. January's four sealed arms ran the OLD
  engine — commission ≡ 0 (F38, confirmed by AW on all 28,519 rows), no spread-geometry floor,
  the pre-repair clocks and stops — and nobody has re-generated the broad family under the
  repaired stack. "Negative under a stack we have since repaired" is what the evidence supports;
  "dead" is not.
- **Never print a bare ADMIT** — "admits at N of 3 bands".
- **A VAL figure carries its used-once disclosure** into the prose, not only into the row.
- **A stop rule is a price, not a prediction**: `RISK_BOUND_not_inference`.
