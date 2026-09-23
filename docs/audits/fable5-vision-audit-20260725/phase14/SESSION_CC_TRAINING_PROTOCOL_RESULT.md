# Session CC — the training-lane protocol machinery

**Blocks B2200–B2231. Branch `phase14/train-protocol`.** Implements
`phase14/TRAINING_LANE_RATIFICATION.md`, ratified by Borhen 2026-07-31 ("i give explicit
approval, please proceed as proposed with the training lane"). Receipts: `phase14/receipts/`.
A/B: `phase14/SESSION_CC_AB.md` (tool-emitted `gtos-ab-receipt-v1` fence).

---

## 0. Findings first

**The ratified protocol is code, and six honesty properties now hold by construction rather
than by anyone's discipline.** A lane session cannot label a March look "TRAIN", cannot record
a look that touches the live stream, cannot write `verdict="admitted"` on an exploration look,
cannot graduate a candidate it never logged, cannot double-bill by retrying, and cannot arm a
sixth incubant or one whose stop rule was written after the fills were visible.

Three findings matter more than the machinery.

### F1 — The family ratchet was nine versions stale, and the default under-billed by 51 %

[MEASURED, B2204.] `candidate_family.DECLARATION_CHAIN` was `(V1, V2)`. **Eleven** declarations
sat on disk in an unbroken `supersedes` chain to V11, so `DEFAULT_DECLARATION` resolved
`CANDIDATE_BOOK_V1` at **35 declared / 32 looks against a true 53 / 50**.

Small is the permissive direction — the one `CandidateFamilyError`'s own docstring says every
branch must fail closed against. It was latent while every caller passed an explicit path, and
it went live the moment this session's biller had to answer "which declaration IS the ratchet".
Session AP found and fixed the same defect once (V1→V2, eight hours, B1350–B1399). It re-opened
and ran nine versions.

### F2 — And the reason AP's fix did not hold is worse than the staleness

[MEASURED, B2205.] **Extending the chain would have gone RED.**
`test_candidate_family_chain.py` asserts the head declaration carries `ratified_rule`, and
**V3 through V11 all dropped it** (key-set diff, computed in `cc_family_v12.py`). So Borhen's
2026-07-30 ratification of the sealed admission rule — `CANDIDATE_BOOK_V1`, all-declared basis,
sealed `B_balanced` α = 0.10 — survived only in V1 and V2, two links behind the head, while the
guard written to catch exactly a dropped rule could not fire because the pointer never moved
past them.

**The stale pointer hid the dropped rule, and the dropped rule made moving the pointer
expensive. Neither end shows the other.** That is the shape worth remembering: two guards, each
individually sound, whose failure modes were each other's cover.

Repaired both ways (B2206). `CANDIDATE_FAMILY_V12.json` is V11's membership with V2's rule
carried forward — **zero new members, zero new looks**, membership hash asserted identical to
V11's. The chain now runs V1..V12 explicitly. And the *mechanism* is repaired, not the
instance: `test_no_declaration_on_disk_supersedes_the_chain_head` discovers declaration files
and fails when one supersedes the head, so "somebody forgot to append" is a red test instead of
a quiet under-bill.

### F3 — Half of April 2026 has never been read, and the ratified frame would have burned it

[MEASURED, B2203.] The ratification lists **"April's 15 sealed days"** under TRAIN — "iterate
freely". Read as *April*, that opens **2026-04-16 … 2026-04-30: fifteen days whose outcomes
have never been read.** 2026-04-16 has shards but no `COMPACT_EVENT_MANIFEST.json` and
contributes zero rows to any JSONL ledger; 04-17 onward was prepared and never run; only S1R1
was ever launched and there is no resume path (B36, `JANUARY_BANK.md` §5.1).

They are held at **VAL**. This is T1, the load-bearing one of five tightenings vs the ratified
frame — and it is the answer to the commission's "record every boundary you tighten and why".

---

## 1. The five tightenings, and the zero loosenings

`phase14/receipts/CC_CONTAMINATION_AUDIT_V1.json` → `tightenings_vs_the_ratified_frame`. The
`loosenings` list is empty and a test asserts it.

| | tightening | why |
|---|---|---|
| **T1** | April 2026-04-16…04-30 is **VAL, not TRAIN** | fifteen days with no outcome ever read. See F3. |
| **T2** | the three already-read replay windows (Jan, Apr 01–15, May 13–17) are **VAL, not TRAIN** | they fall inside the frame's own VAL span. Two declarations over one range is an ambiguity and the **narrower USE wins**. Both surfaces are unbilled and logged, so the lane loses nothing; what it gains is the used-once disclosure travelling automatically. |
| **T3** | **2026-06-01 … 2026-07-28 stays UNCOVERED, therefore refused** | the frame declares no surface for it. It is *not* virgin — `GateSpec.global_span` ends 2026-07-27, so every full-history walk has read it — so calling it TEST would be a lie that invites a "confirmation" on burned data. Recorded as an `UncoveredGap` with its measured consumption. |
| **T4** | TEST opens at the **earliest** arming across both accounts (2026-07-29) | the two books share sleeves; a per-account cutoff would leave 2026-07-29 iterable for a redacted_account claim while FTMO was trading it. |
| **T5** | `TRAINABLE_ROLES` **unchanged** | the surface axis is additive and answers a different verb. Verified by exhaustion over 2025-01-01…2026-12-31, not by sample. |

### The whole surface, in seven runs (B2219)

Scanned day by day, 1900-01-01 … 2030-12-31. Exactly one hole in the modern era, and it is
the declared gap:

| from | to | surface | iterable |
|---|---|---|---|
| 1900-01-01 | 1992-02-17 | — | no (no archive) |
| 1992-02-18 | 2024-12-31 | TRAIN | yes |
| 2025-01-01 | 2026-02-28 | VAL | yes |
| **2026-03-01** | **2026-03-31** | **TEST** | **no — blackout, checked before any band** |
| 2026-04-01 | 2026-05-31 | VAL | yes |
| 2026-06-01 | 2026-07-28 | — | no (`gap_2026H1_tail_pre_arming`) |
| **2026-07-29** | open | **TEST** | **no — live forward** |

---

## 2. The design decision the commission left open, and the arithmetic behind it

**CC-2 asked: a `surface` field on the existing trial ledger, or a sibling ledger?** Sibling,
and the reason is measurable rather than aesthetic (B2207).

`validation_integrity.trial_budget_ledger.measured_n_trials()` is
`max(prospective look events, retrospective bound, floor)` and it feeds the **DSR deflation**.
Lane iteration written into that ledger raises the estate's DSR bill with every exploration —
which is the backward leak `TRAINING_LANE_RATIFICATION.md` §1.2 names, where AW paid a 486-look
family bill for research triage. A field cannot fix it: `measured_n_trials` would have to learn
to *subtract*, and **a bill you can subtract from is not a ratchet.**

Measured as behaviour, not argued: 25 lane looks move `n_prospective_look_events` by **exactly
0** (`test_the_iteration_ledger_never_feeds_the_dsr_trial_ledger`).

**The obvious objection — a sibling is a cheap place to hide a real look — does not survive
contact with the biller.** `graduate()` reads its provenance out of the iteration ledger and
refuses `provenance_missing`. Logging is a **prerequisite for billing**, not an alternative to
it: the cheap ledger is the only road to the expensive one (B2208).

The two summaries are reported side by side, with a note saying they are never summed.

---

## 3. What each artifact refuses

### The iteration ledger — three things a caller cannot forge (B2209)

1. **The surface stamp.** `record()` takes DATES and classifies them through the map. You
   cannot assert `surface="TRAIN"` over a span that touches March.
2. **The verdict.** `admitted` / `rejected` / `graduated` raise. They are the sealed gate's
   words; a TRAIN/VAL look reporting one has either mislabelled itself or run the gate without
   billing it. Cheaper to refuse the word than to audit the prose later.
3. **`billed`**, written `false` by the module and not a parameter.

### The graduation biller — what "atomic" honestly means for two files (B2212–B2214)

Two files move: the declaration (the bill) and the graduation ledger (the receipt). No
filesystem moves two files together, so that is not claimed. What is:

- the declaration is written to a pending path, **loaded back through the estate's own
  validating loader**, checked non-decreasing, and only then `os.replace`d —
  `load_candidate_family` has no fallback by design, so a half-written declaration would stop
  the estate's billing entirely;
- the **bill is paid before the receipt**, so a crash between them leaves the estate
  over-billed, never under-billed;
- **`graduate()` is idempotent** — a second call for a candidate already in the family finds
  the paid bill and emits the missing receipt (`billed_looks=0`, no successor file written).
  A ratchet a retry could pay twice is not a ratchet, and one whose retry path needs a human
  editing JSON is a ratchet that gets edited.

Measured: 53 → 54 on the first call, 54 → 54 on the second, one receipt row.

Five refusals, each pinned behaviourally: `provenance_missing` · `provenance_touches_test` ·
`provenance_spec_mismatch` · `unknown_family` · `declaration_lost_the_rule`. The TEST check
reads the **stamp**, not the row's label — tested by forging a ledger row that claims
`surface: VAL` while carrying TEST days, which is still refused. The last refusal is F2 turned
into a guard.

### The incubation registry — three constraints, three moments (B2216–B2218)

Weight (≤ 0.05) and the rules are properties of ONE record → `register()`. Capacity (≤ 5
concurrent, where concurrent means **armed**) is a property of the SET → `arm()`, so filing
dossiers is free and arming is what the ratification bounds. The ceremony is a property of the
TRANSITION → `arm`/`pull`/`promote` each need an `OwnerCeremony` with who decided, when, and
the receipt. Pretending they are one check is how a registry becomes a form nobody fills in
honestly.

"Pre-registered" is **checked against the arming time**, not asserted: a ceremony dated before
the earliest rule's `pre_registered_utc` is refused.

**`GRADUATED` and `OWNER_RISK_ACCEPTED` are kept as distinct required fields, against the
ratification's own framing.** §4 frames incubation as "between admission and full weight", but
the estate has two intakes and only one is an admission: `mx_btcusd` graduated, while the
five-sleeve expansion was armed on explicit owner risk acceptance with neither added sleeve
passing an admission standard — and CA's revival candidates will be the same shape. A page that
reads "incubating" over both is the page that lets a risk-accepted sleeve be quoted later as an
admitted one.

---

## 4. What I got wrong

**4.1 — I predicted two siblings' in-flight ranges would go dead, and dropping them broke the
guard immediately** [B2228]. My reasoning: every wave-14 commission declares its allocation in
RANGE form and `_RANGE` excuses a range, so CA's `(2100, 2149)` and CB's `(2150, 2199)` exempt
nothing once my blocks raise the ceiling. **Wrong, for a reason the codebase already
documented** — `KNOWN_GHOSTS["B1786"]` says it in one line: *`_RANGE` exempts a range's UPPER
bound and not its lower*. So `B2100–B2149` is itself read as a citation of B2100, and dropping
the two entries made B2100 and B2150 dangle in the same test run. Both restored as **ACTIVE**.
The direction is what makes this worth recording: it would have deleted two live exemptions
covering other sessions' unwritten work.

**4.2 — my first iteration ledger refused the estate's own standard walk** [B2210]. It rejected
`GateSpec.global_span` (1992-02-18 … 2026-07-27) with "touches 31 TEST days", because that span
*contains* March. But **spanning is not consuming**: `panel.py` drops every trade whose label
span touches a blackout before pricing, and `folds.py:125` pushes fold boundaries out of one. A
ledger that refuses the walk every gate run in this estate performs would have been unusable on
day one — and I would have shipped it if I had not run the real span through it. Fixed with
`engine_reserved_blackout=`, validated in **both** directions so it can neither be narrower than
the lane's blackout nor smuggle a filter in as one.

**4.3 — `UNCOVERED` was a possible value of a row's `surface` field, and that would have killed
the field** [B2211]. First version returned it as "most restrictive present", which made the
estate's commonest walk stamp itself `UNCOVERED`. A field whose commonest value is a non-value
trains readers to ignore it, and it buried the TRAIN/VAL distinction that decides whether the
used-once disclosure applies. Uncoveredness is now loud in three other keys and `surface` stays
the question it claims to answer.

**4.4 — `trial_budget_ledger` cites the wrong POSIX guarantee, and I nearly copied it** [B2223].
It cites `PIPE_BUF`, which is the guarantee for **pipes**. For a regular file the honest
statement is `O_APPEND` plus the observation that a single `write()` may return short. My first
`append_row` inherited both the citation and a 512-byte refusal derived from it — which would
have refused most real rows. Corrected: the returned byte count is compared against the payload
and a short write **raises rather than being completed**, because retrying the tail is exactly
what tears the row after another session's line. Filed against `trial_budget_ledger` rather
than edited — its behaviour is correct even though its citation is not.

**4.5 — an adversarial pass on my own incubation registry found the one check that makes
"pre-registered" mean anything, broken in three ways** [B2230]. `arm()` compared the ceremony
against the **earliest** rule's `pre_registered_utc`. Wrong bound: "pre-registered" is a claim
about EVERY rule, so an incubant whose stop rule predates the ceremony and whose **promotion**
rule was written an hour after it passed — and a promotion rule added once the fills are visible
is precisely what the constraint exists to stop. Bound on the LATEST rule now. In the same pass:
timestamps were compared as **strings**, and ISO-8601 offsets are not lexicographically ordered
(`"…T00:00:00Z"` sorts above `"…T00:00:00+00:00"` because `'Z' > '+'` while denoting the same
instant), so the check would have silently failed for whichever session spelled it with `Z` —
both spellings are valid and both appear in this estate's receipts. And `sorted()` over
`(instant, dict)` pairs raised `TypeError` whenever two rules shared a timestamp. All three came
out of writing **one** test that combined the two offset spellings with a late promotion rule.
The lesson I will carry: the check I was most confident about was the one nobody had made
adversarial, because it reads as obviously correct in English.

**4.6 — a one-off failure I nearly wrote off as flake was a real landmine in the A/B method
this estate mandates** [B2231]. A wide sweep showed one failure —
`test_fast_engine_accel.py::test_route_cleanup_refuses_the_namespace_root_itself` — that passed
on every re-run and is in no scope of mine. The honest thing was to chase it, and the mechanism
is exact: `ATTEMPT5_NAMESPACE_ROOT` is an **empty directory**; git does not track empty
directories, so its absence leaves `git status` clean and `git checkout -- .` cannot bring it
back. Reproduced deterministically. It therefore fails **exactly once** after any working-tree
clean and heals itself when the sibling test recreates the root — the hardest shape to
attribute, and the working agreement *mandates* A/B by copy-back, which is such a clean. The
next session doing an honest A/B would have read it as "your change broke the fast engine".
Fixed at the test, with the precondition made explicit rather than inherited.

**4.7 — what I did not do.** I did not resolve whether the June route's March fit disqualifies
March as a broad-family holdout (Session Z left it as an owner/review judgment and it still is).
I did not open the 2026-06-01…07-28 gap, which is 41 already-burned trading days that a future
session may legitimately want; it is refused and the decision is named as the orchestrator's.
I did not repair the pre-existing collection error in my A/B scope (see §6).

---

## 5. Coordination with the siblings — by artifact shape, as instructed

- **CA** (revival gates) files incubation dossiers. The shape is
  `Incubant(incubant_id, sleeve, account, proposed_weight≤0.05, admission_basis, evidence,
  stop_rules=(PreRegisteredRule,...), promotion_rules=(...), expected_economics)`, and
  `incubation.rules_from_dicts()` builds the rules straight from the AS dossier JSON shape
  (`class`, not `class_`). A `REVIVAL_CANDIDATE` with no graduation record files as
  `OWNER_RISK_ACCEPTED` citing the owner's decision.
- **CB** (train engine) imports `trainer_partitions` and must not modify it (its acceptance
  gate 4). The call is `DEFAULT_SURFACE_MAP.assert_iterable(days, context=...)` for the lane
  check and `DEFAULT_REGISTRY.assert_trainable(...)` if it ever fits. Its CB-4 output contract
  (per-arm trade table + spec digest + surface stamp + engine version) maps one-to-one onto
  `IterationLedger.record(...)`: pass `spec=`, `engine_version=`, and the dates.
- **CD** (broad-family regeneration) is unblocked by design: January 2026 is lane-`VAL`, so the
  regeneration is legal, unbilled and logged, and its figures carry the used-once disclosure.
  `IN_FLIGHT_WAVE_RANGES` now carries CD's `B2250–B2299` as its pre-declaration.

**One collision risk, named:** CA may publish its own `CANDIDATE_FAMILY_V12.json`. If both
exist at the train, **renumber mine** — it adds zero members and zero looks, so re-parenting it
onto CA's declaration is a one-line `supersedes` change with no arithmetic to redo. Recorded in
`cc_family_v12.py`'s own docstring so whoever hits it does not have to find this page.

---

## 6. A/B, and the one thing in it that is not zero

`phase14/SESSION_CC_AB.md`, tool-emitted. **1 bad → 1 bad, 0 regressed, 0 fixed, 551 → 552
passed** over 32 shared files, plus **62 passed / 0 failed** in the new test file captured
separately (it does not exist at BASE — Session BD's B2073 lesson). Wider sanity outside the
receipt: `tests/research_infra/` + `tests/scripts/` at HEAD is **2096 passed, 7 skipped,
0 failed** — and that sweep is what surfaced B2231.

**The one `bad` is pre-existing, identical on both sides, and already filed.**
`test_moonshot_unified_execution_scorer.py` fails at collection on
`ImportError: cannot import name 'aggregate_reduction_rows'`. Session AT triaged it in wave 6
as **KEEP-REAL**: *223 tests that have never once collected*, an unwritten API surface rather
than a rename, deliberately not deleted. Not absorbed here — writing two unwritten API
functions blind and then discovering what 223 hidden tests assert is a session, not a footnote
in one. **So the honest headline is "0 → 0 by failure set, with one pre-existing collection
error unchanged", not "zero".**

The `+1 passed` is identified by node id rather than inferred:
`test_candidate_family_v2_ratchet.py::test_a_successor_is_a_superset_of_what_it_supersedes[CANDIDATE_FAMILY_V12.json]`
— an existing guard applying itself to the new declaration.

A/B by copy-back, sha-verified in both directions, driven from Python (BD's B2075: `zsh`
word-splitting produced a fake A/B that reported the answer its author wanted).

---

## 7. Handoff

1. **Merge the agreement section.** `phase14/WAVE_AGREEMENT_TRAINING_LANE_SECTION.md` is a
   drop-in replacement for `WAVE_11_WORKING_AGREEMENT.md` §6, which says in its own last line
   that CC's merge replaces it.
2. **`CANDIDATE_FAMILY_V12` collision.** See §5. Renumber mine if CA publishes a V12.
3. **`IN_FLIGHT_WAVE_RANGES` at the train.** CA's and CB's entries are ACTIVE and must survive
   until their blocks land; CC's is retired and CD's `(2250, 2299)` added. If either sibling's
   branch still cites an individual **unwritten** token of its own after merge, restore that
   branch's entry rather than deleting the citation (AU's B1593 is why that distinction matters).
4. **Two `KNOWN_GHOSTS` entries added** (B2086, B2094) — BD's commit-subject ranges quoted
   inside an immutable receipt fence and inside BD's own correction paragraph. Third instance
   of the B1976 class; delete the entries if those blocks are ever really allocated.
5. **`aggregate_reduction_rows` / `aggregate_execution_rows` are still unwritten** — AT's filed
   KEEP-REAL item, 223 tests dark. Worth a commissioned session; it is the largest single block
   of hidden coverage anyone has measured in this estate.
6. **`trial_budget_ledger`'s `PIPE_BUF` citation** is wrong (its behaviour is not). One-line
   docstring repair for whoever next owns that module.
7. **Nothing here changes the sealed admission rule, and one test asserts it.** No config was
   touched, no VPS access, no broker-capable script run, no R2-bound path edited —
   `trainer_partitions.py` and `candidate_family.py` are both unbound (checked before editing).
