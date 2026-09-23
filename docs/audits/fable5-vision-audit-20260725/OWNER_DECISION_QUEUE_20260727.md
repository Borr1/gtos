# Owner decision queue — 2026-07-27

**For Borhen.** Everything the plan needs from you, in one place, as typed packets:
**decision / evidence / options / recommendation / explicitly not taken.**

Sessions produce measurements and recommendations. Risk dial, allocation profile, sleeve composition,
and any change to the sealed economic contract are yours. Nothing here has been taken by an agent.

**Nine are decidable now** — the five full packets below (D-A…D-E), plus **D-I, D-J, D-L, D-M** added
by wave 3 and listed at the end. **D-F is yours to execute**, not to decide, and its runbook now
exists. **D-G and D-K** their own sessions recommend deferring into OD-3. **C12** stays open and
non-blocking, **D-H is withdrawn**, and **OD-3** waits on wave 4. The whole board is at the end so
you can see it in one place.

> *Counts corrected at integration (Session O, 2026-07-27, B184): this line read "Five are decidable
> now. Four wait on wave-3 output," which was true before wave 3 and false after it. Four sessions
> added decisions and none updated the header.*

---

## D-A · The JPY cluster, and the certified envelope behind it

**Decision.** End the JPY-cross trial — and separately, decide whether to re-impose the certified
one-unit-per-cluster-per-day envelope.

**Evidence.** The JPY cluster is measured dead on live evidence: **−0.453 R gross**, **37.4 % of net
loss**, and negative *gross* as well as net — so it is not a cost artifact. Signal-level
**p = 0.00588**. GBPJPY's failure is gross-edge, not cost, which is precisely why the cost model never
saw it coming; USDJPY is killed by commission on the validation's own rows.

**The correction that reframes this, and it matters.** The G1b receipt framed the decision as "end the
JPY *exemption* from the cluster cap." That mechanism is moot: `ultimate_book_one_unit_per_cluster_per_day`
is **globally `false`** at HEAD (`config/agent_config.yaml:1373`), with `jpy` listed in
`cluster_cap_exempt_clusters` underneath a cap that is not running. **The live book is already
operating outside the envelope the 2.0 % dial was certified on.** The config comment says the trade-off
was accepted for trade frequency plus validated diversification.

So there are two decisions, and the second is larger than the first.

**Options.**
1. Kill JPY, leave the cap off. Removes a measured-dead cluster; leaves the dial running outside its
   certification.
2. Kill JPY **and** re-impose `one_unit_per_cluster_per_day: true`. Restores the certified envelope;
   reduces trade frequency at a time when frequency is already the open question (G4).
3. Kill JPY, re-impose the cap, and keep a named exemption for a cluster you deliberately choose.
4. Neither — wait for the re-cost, since the survivor book may not contain JPY at all.

**Recommendation.** **Option 1 now, option 2 revisited after G4.** Killing JPY is unambiguous — it is
negative gross, on live evidence, and no re-cost will rescue it. The cap is different: re-imposing it
cuts frequency, and Session K is about to tell us whether frequency is *already* the book's binding
problem. Deciding the cap before G4 spends the decision at the worst moment. But make the record honest
either way — the dial's certification currently does not describe the running system.

**Explicitly not taken.** No agent has touched `agent_config.yaml`. The JPY sleeves are still live in
shadow.

---

## D-B · The candidate book at the 2.0 % base

**Decision.** Candidate book on or off.

**Evidence.** It accounts for **76.4 % of the net loss** of the live fortnight (B64), and was switched
on **same-day with no cited validation**. Its validation package is not absent — this was corrected
from the third review's own first draft — but it is **proxy-grade and placebo-failed**: A8-frame MC,
Sharpe 0.277, MC pass 0.9999, and **it fails its own random-day placebo at p(random ≥ observed) =
0.59.** The activating document rests the decision on *"replay/MC + readiness/routing/package proof"*,
not on beating random timing. It has **never been jointly validated with the core book at the live
dial** — CYCLE62 contains zero occurrences of "candidate" or "expansion".

**Context worth having.** Of every book-level improvement in the record, exactly **one** passes its own
placebo: the small A8 metals-confluence gate (Sharpe 0.1446 → 0.1478). The large exciting one is this
one, and it failed.

**Options.** (1) Off now. (2) On, pending the re-cost. (3) Off, with a documented path back in through
the walk-forward gate like any other candidate.

**Recommendation.** **Option 3.** Off, and re-entry only through the gate. This is the single clearest
case in the record of a change that shipped on the wrong kind of proof, and it cost three quarters of
the loss. Turning it off is not a judgment that it has no edge — it is a judgment that nobody has
measured whether it does.

**Explicitly not taken.** Config untouched.

---

## D-C · Q8 — three tests that pass only when a live gate is OPEN

**Decision.** How to resolve three tests whose green state depends on a live activation gate being
open.

**Evidence.** B41 L3. As written, these tests encode "the gate is open" as the correct state. That is
backwards for a system whose safety posture is gates-closed: the suite should be green in the safe
configuration and red in the dangerous one, never the reverse.

**Options.** (1) Rewrite them to assert gate-closed behaviour. (2) Parameterise over both states.
(3) Skip-with-reason until activation.

**Recommendation.** **Option 2.** Both states are real and both should be pinned — the gate will be
open one day, and that is exactly when you want the assertion to exist. Option 1 loses coverage of the
state you are working toward; option 3 loses it entirely.

**Explicitly not taken.** Session M can execute whichever you pick; it is on its list only as a
decision, not as a change.

---

## D-D · Campaign disposition — B7.5

**Decision.** Finish under the frozen engine / park as a priced option / retire.

**Evidence.** Finishing costs **~36 machine-hours serial** (April 16.5 + May ~2.7 + March 16.5 — May is
~3 trading days), and the option **expires at the first bound-file edit**, after which add +16.5 MH to
re-run January for comparability. April carries **no partial credit**: 15 sealed days, and the stopped
S1R1 cannot resume — the runner refuses non-fresh output namespaces
(`b7_5_post_acceleration_runner.py:292-315`) and hardcodes sub-window away on the sealed path (`:832`).

**Two conditions that bind before any window ever runs again.** First, the **pooled
promote/reject/inconclusive evaluator does not exist anywhere** — verified: zero threshold keys in any
Python, and the only pooling artifact is `factor_or_policy_promotion_authorized: False` hardcoded in
two analyzers. Reading April's outcomes without it would improvise the terminal decision after seeing
the data. Second, **the protocol seals the thresholds but not the pooling weights** (by-window vs by
risk-cash), so even the pooling semantics would otherwise be chosen post-hoc. Under either weighting,
April would need a total effect of roughly **+0.36 to +0.45** from a family whose every measured cell
is negative — pooled must exceed +0.1 from a −0.152 start.

**Recommendation.** **Park as a priced option, banked first** — which is what approving the plan
already implies; this packet exists so the specifics are explicit rather than inherited. Session L
writes `JANUARY_BANK.md` so the park does not orphan the lessons, the most valuable of which is a
standing design rule: *no dynamic runtime sizing on any activation path without factorial-grade
evidence.* **March stays outcome-unread** — it is the only untouched month, and the scarcest resource
the programme owns.

**Explicitly not taken.** Nothing deleted. The monolith, R2, sealed January and the April partial stay
exactly where they are.

---

## D-E · The charter's item 6 says credentials are absent. They are present.

**Decision.** Accept the divergence, or remediate it.

**Evidence.** `GTOS_ULTRA_GOAL.md`'s culmination item 6 states credentials are absent as a safety
property. Today: both MT5 terminals are authenticated and connected, `trade_allowed` is **true** on
both, two funded accounts, supervisor Running — in shadow. The plan never stated this divergence for
you to accept.

**Options.** (1) Accept it and amend the charter to describe the real posture. (2) Remediate — remove
stored credentials from the VPS, accepting that the shadow stream stops. (3) Accept it *conditional on*
the activation token landing there, which converts the exposure from "credentials present, one config
layer" to "credentials present, cryptographic authorization required."

**Recommendation.** **Option 3.** The shadow packet stream is the forward-evidence lane the whole plan
ends on; stopping it costs the thing you need most. But accepting credentials-present with no
authorization layer is what the current posture actually is, and it is not defensible. Session I lands
the token carry; take option 3 the moment its runbook is executed.

**Explicitly not taken.** No credential touched. No VPS change made by any agent.

**Session I addition (2026-07-27).** A fourth option exists that this packet did not list:
keep the terminals authenticated but authenticate them with an **investor / read-only
password**, so the broker itself refuses orders while the shadow stream keeps running. It is
the only option on the board that puts a refusal *outside* GTOS's own code. UNVERIFIED —
nobody has checked whether FTMO or redacted_account offer it, or whether `run_book.py`'s
account-identity check passes on an investor login. Worth an hour before taking option 3.
See `phase3/CHARTER_ITEM6_CREDENTIALS_DIVERGENCE.md`.

**Option 3 is now unblocked.** The token carry is done, reviewable
(`phase3/TOKEN_CARRY.md`) and has an owner-executed ceremony
(`phase3/STAGE0_VPS_RUNBOOK.md`) — that is D-F.

---

## Waiting on wave-3 output — listed so you can see the whole board

| # | Decision | Blocked on |
|---|---|---|
| **OD-3** | **The activation candidate: composition and dial.** Reopens OD-1. | Wave 4 — the re-cost (1.2) and the out-of-window survivor replay (1.3b). **Session K's G4 is delivered — see below; it changes what OD-3 is choosing between.** |
| D-F | **VPS token carry execution** — you run it, on the VPS | ~~Session I's runbook~~ **UNBLOCKED** — `phase3/STAGE0_VPS_RUNBOOK.md` is in-tree as of this merge. Waiting on you, not on a session. |
| D-G | **B54 Part 2** — re-key `decision_day_of` to the runtime day? Changes risk bucketing. | ~~Session L's D2 MC pack~~ **UNBLOCKED** — `phase3/evidence_packs/DAY_KEY_MC.json` is in-tree. Session L's recommendation: **defer to OD-3**, and when taken, re-derive the Kelly bins with it so a correctness fix does not import a size increase. |
| ~~D-H~~ | ~~**D0 universe reconciliation** — 4 metals crosses + DASHUSD are absent from both live profiles, which is why `metals_core` ran 2-of-6.~~ **Premise withdrawn 2026-07-27 (Session K, D16): they are absent from redacted_account only. `operator_profile` carries all six, so on FTMO `metals_core` ran 6-of-6 and still produced nothing.** Restated as **D-I** below. | — |
| C12 | Legacy history graft (carried from G0 §7) | Nothing — still open, still non-blocking |

### Added 2026-07-27 by Session K

| # | Decision | Why it is yours | Cost of the answer |
|---|---|---|---|
| **D-I** | **Add the four metal crosses (XAUEUR/XAGEUR/XAUAUD/XAGAUD) + DASHUSD + XPDUSD/XTZUSD/AVAUSD to the redacted_account profile — or accept that the two live accounts trade different books?** redacted_account supports **76 of 95** declared sleeve-symbol slots against FTMO's 95/95. | Sleeve composition, and the profiles are decision-contract-bound (H1). | **Quantified against real bars, then corrected twice by adversarial review — read the third version.** At *generation* level the four crosses contribute **62.4 %** of `metals_core`'s intents. But the book sizes **one correlated unit per (cluster, day)** (`admission.py:1004`; `metals.py:20-26` — "the unit splits across more symbols, it does not stack more units"), and at **unit** level redacted_account runs **57 %** of FTMO's metals complex, not "a third" as I first wrote. The crosses add **42.6 %** of metals unit-days, and **60 % of cross fires land on the same instant as a USD-leg fire** — largely the same opportunity re-expressed.<br><br>**The fact that should weigh most, and which I missed until review:** `metals.py:15-17` records that the four crosses **"were not on the validated data surface -> added later with data-coverage reconcile"**. So 62.4 % of `metals_core`'s generation sits **outside the W7 validation**. That cuts *against* adding them to redacted_account, not for it — adding them would widen the unvalidated share of a book whose whole activation argument rests on its validation. Prepared as a profile diff; ~0 machine-hours. *(Two earlier versions of this row — "would not have changed the live outcome", and "a third of the book" — are both withdrawn.)* |
| **D-J** | **12 of the 29 sleeves take their risk-bucket day key from the wall clock, not from any bar** (`market_expansion_d1.py:147-161`, override at `:217-221`). Fix it to the bar-derived day, or leave it? | It changes correlated-unit bucketing and Kelly day counts on the market-expansion book — a risk-envelope change. Distinct from D-G: that one re-keys `decision_day_of` globally, this one is 12 sleeves reading a clock instead of a bar. | Register entry D13. Magnitude on live sizing is unmeasured; measuring it is ~0.5 session. |

**And one thing that is not a decision but changes how you should read OD-3** — G4's answer, in one
line: **88.5 % of core-8's confidence weight sits in sleeves that were expected to generate only a
handful of intents across the entire 38-day live window, and all five are statistically consistent
with having generated nothing.** `metals_core`, the 1.00-confidence anchor, generates
**≈ 35 intents/year**, and the five combined **≈ 126/year**
(`phase3/G4_GENERATION_VERDICT.md:97-100`, Revision 4). The window that triggered OD-1 was still too
short to test the book's core — but on Session K's own corrected wording that is *"too short, with
the observed zero at the edge of what frequency comfortably explains,"* not *"far too short."* So
the case for treating that window as evidence *against* the W7 book is weaker than it looked, and by
a **smaller** margin than the first measurement implied.

> **Corrected at integration (Session O, 2026-07-27, B183).** This paragraph carried **9–17
> intents/year**, taken from `G4_GENERATION_VERDICT.md` §5 — which that document's own `:265` marks
> `[MEASURED — SUPERSEDED by Revision 4]` and whose `:11` says to read Revision 4 first. Session K
> measured the correction (`~2x faster than published`, commit `7c763604c`) and updated the receipt
> but not this queue, so the owner-facing number was the superseded one. The correction cuts
> *against* the argument this paragraph makes, which is why it mattered.

Two honesty notes on that finding, since it argues in the W7 book's favour and should therefore be
read sceptically: it says nothing about whether those sleeves would be *profitable*, only that they
were never given the chance to be measured; and a commissioned adversarial pass refuted three of the
five claims in the receipt's first draft — including its headline p-value — before it reached you.
What survived is in `phase3/G4_GENERATION_VERDICT.md`, with everything withdrawn listed in its §7.

### Added 2026-07-27 by Session L — full packets in `phase3/OWNER_DECISION_PACKETS_SESSION_L.md`

Listed here at integration so the board is complete in one place. Each has a full
decision/evidence/options/recommendation packet in that file; these rows are the index, not the
argument.

| # | Decision | Session L's recommendation | Cost of the answer |
|---|---|---|---|
| **D-K** | **The dial** — the risk percentage per account. | **Not a decision now.** It is part of OD-3 and should be set with the survivor book in front of you. Carry three constraints into OD-3: set the dial *per account*, not per book; state it with its reset rule; the two firms' reset clocks differ, so a dial safe under one is not automatically safe under the other. | with OD-3 |
| **D-L** | **Re-impose the certified one-unit-per-cluster-per-day envelope?** The second and larger half of D-A. | **Fix the record now** (comments, config block, a startup assertion); **defer the flag** to OD-3. | record fix: now. Flag: with OD-3 |
| **D-M** | **Replace the gross-cap shed algorithm? (D1)** | **Keep first-fit-descending**, fix the docstring, and downgrade D1 to a measured latent property. | none — zero realised cost in 38 days |

> **Renumbered at integration (Session O, 2026-07-27, B184). Read this if you saw an earlier draft.**
> Sessions K and L ran in parallel and **both allocated `D-I` and `D-J`** — to four different
> decisions. Neither could see the other, and because the two sets lived in *different files* git
> reported no conflict at all; `IMPLEMENTATION_STATE.md` ended up carrying both meanings under the
> same label (`:4364` K's, `:4637` L's). The queue owns the letter space and Session L's document
> states it *extends* this one, so **L's two yielded**:
>
> | was (Session L) | is now | decision |
> |---|---|---|
> | D-I | **D-L** | re-impose the certified cluster envelope |
> | D-J | **D-M** | replace the gross-cap shed algorithm |
>
> Session K's **D-I** (metals crosses on redacted_account) and **D-J** (12 sleeves keyed to the wall clock)
> are unchanged, and K's D-I keeps the slot because this queue's withdrawn D-H row already points at
> it by name. **D-K (the dial) did not collide and was left alone.** No decision content changed —
> only two labels. The root cause was that L's decisions never reached this board; adding them above
> is the fix, so the next session can see the whole letter space in one place before allocating.

**OD-2 stands unchanged.** The forward-only verification split proved itself: every wave-2 session
worked under it and not one re-seal was owed.

---

## How to answer

Reply with the letters and your choice — `D-A: 1`, `D-B: 3`, and so on — or say "your recommendations"
and I will record them as taken and route each to the session that executes it. Anything you want to
defer, say defer; none of the five blocks wave 3 from starting.
