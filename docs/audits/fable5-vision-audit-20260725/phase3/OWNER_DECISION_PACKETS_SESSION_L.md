# Owner decision packets — Session L

**For Borhen, 2026-07-27.** Four packets, typed: **decision / evidence / options / recommendation /
explicitly not taken.** These extend `OWNER_DECISION_QUEUE_20260727.md`; **D-G was listed there as
blocked on this session's D2 MC pack and is now unblocked.** D-L, D-M and D-K are new.

Evidence for all four is `phase3/EVIDENCE_PACKS_RECEIPT.md` and the three JSON receipts under
`phase3/evidence_packs/`. **No config, no production code, and no contract-bound file was touched by
this session.**

**One thing to carry into all four, because it decides how to read them.** Every P&L number below
comes from a **single 17-day trading window on a book that lost money and whose composition D0 showed
is not the validated one** — zero placements from any train-validated sleeve. On a losing book, *any*
rule that removes trades looks good. That is why each packet reports its null control, and why in two
of them the null control is the answer.

**And a second thing, because it changed two of these packets.** After the measurements were first
written up, two adversarial refuters were run against them. They voided two headline findings and
moved several numbers by up to 22×. The full ledger is `EVIDENCE_PACKS_RECEIPT.md` §4; the packets
below are the corrected versions, and where a recommendation used to rest on something withdrawn,
that is said in the packet.

---

## D-G · Re-key `decision_day_of` to the runtime day? (B54 Part 2)

**Decision.** Change the correlated-unit grouping key from the signal bar's UTC date to the cycle
runtime date — or leave it.

**Evidence.** `bar_provider.py:86-88` returns the signal bar's UTC date. It drives four consumers:
the Kelly-lite per-day count (`admission.py:1101-1106,1144-1148`), the `(decision_day, cluster)`
correlated-risk-unit bucket (`:1107-1113`), and both placement caps (`book_owner.py:1601-1617`).

D2 measured that a cycle whose intents' last-closed bars straddle UTC midnight gets **two Kelly
multipliers on units decided from one `size_correlated_units` call** — worst observed ×1.241 against
×0.748, a **1.66× ratio** — and that only a runtime key unifies all four measured cycles, because no
bar-derived key can unify the `idxrev`-vs-`idxrev` case. **This session reproduced D2's census
exactly** (12 states with two Kelly counts, 4 with two multipliers) from an independent grouping.

The MC pack now says what the re-key does to the envelope:

| | effect |
|---|---|
| **Envelope tightening (safe direction)** | the runtime key removes **43 `(day, cluster)` correlated-unit buckets** (268 → 225) — 71 cycles currently split across more than one bar-day, and one cycle can produce only one runtime key by construction |
| **Size increasing (not safe)** | merging raises the per-day active-sleeve count, hence the Kelly multiplier — never downward. Mean size ratio **1.001856**, p05–p95 [1.000510, 1.003570]; **0.57 %** of buckets change |
| **Sensitivity to the missing running-conviction store** | real but small. `kelly_running_count: true` means live used `na = max(per_cycle, running)` and the store is absent from the export; drawing `running` to the recorded maximum (na = 11) gives the distribution above |

**So the re-key is genuinely two-signed, and it is now quantified rather than argued.** It tightens
correlation bucketing and loosens size in the same move. On this window both are small: 43 buckets,
+0.19 % mean size.

**Corrected after adversarial review.** The first version of this packet said 129 buckets and
+2.9 % size, and claimed the answer was *invariant* to the missing running-conviction store. All
three were wrong: 129 counted (cycle, bar-day) partitions rather than (day, cluster) buckets; the
+2.9 % ignored the running store; and the invariance was an artifact of a sampler that drew
`running` only up to the per-cycle count, which forces the result. **The direction of the finding is
unchanged and the magnitudes are smaller** — which strengthens the recommendation to defer rather
than weakening it.

**Options.**
1. **Leave it.** The UTC key stays; the 0.45–0.67 % consequential-sizing rate stays; the Kelly tilt
   remains partly a function of which symbols closed a bar before midnight.
2. **Re-key to runtime**, matching the convention the 14 `mx_*` sleeves already use. Tightens the
   envelope by 43 buckets; raises size on 0.57 % of buckets, +0.19 % on the mean.
3. **Re-key to runtime *and* re-derive the Kelly bins** so the merged counts do not import a size
   increase the dial was not certified with.
4. **Defer to OD-3** and decide the day key with the surviving book's composition in front of you.

**Recommendation. Option 4 now, option 3 when you take it.** Two reasons. First, the measured effect
is **smaller than first reported** — 43 buckets and +0.19 % mean size — and the book is
placement-deactivated, so there is no urgency and no cost to waiting. Second, and this is the real
argument: **the re-key is a sizing change, and Session K is about to tell us whether the book's
binding problem is that it does not fire often enough (G4).** If G4 says frequency is the
constraint, a change that tightens correlation bucketing lands differently than if it says the
opposite. When you do take it, take option 3 rather than 2: option 2 imports a size increase as a
side effect of a correctness fix, and side-effect size increases on a funded account are exactly
what this programme has been burned by.

**Explicitly not taken.** `bar_provider.decision_day_of` is unchanged.
`tests/ultimate_book/test_sleeve_server_clock.py:123-131` — the deliberate tripwire that fails the
instant anyone re-keys it — still passes.

---

## D-L · Re-impose the certified one-unit-per-cluster-per-day envelope?

**Decision.** Set `ultimate_book_one_unit_per_cluster_per_day` back to `true`, or leave it `false`.
This is the second and larger half of D-A.

**Evidence — the config truth first.** The cap is **globally `false` at HEAD**
(`config/agent_config.yaml:1373`), with `jpy` in `cluster_cap_exempt_clusters` (`:1374`). The exempt
list is **unreachable**: `book_owner.py:1612` evaluates the global boolean first in a short-circuiting
`and`, so with the cap off *every* cluster is effectively exempt and exempting `jpy` buys nothing.
The code default is `True` (`book_owner.py:170`), every comment in the file describes an active cap,
and **nothing in code or tests pins the shipped config value** — which is why this went unnoticed.
**The live book has been running outside the envelope the 2.0 % dial was certified on.**

**Evidence — what re-imposing it would have done.** Re-running
`placement_ledger.cluster_placed_today_other_bar` over the 145 recorded `unit_placed` packets, priced
by joining to the broker trade rows (100 % join rate in every configuration):

| configuration | placed | blocked | saved | **random-blocking null** | **ECDF percentile** |
|---|---:|---:|---:|---:|---:|
| cap off (HEAD) | 145 | 0 | — | — | — |
| cap on, UTC key, `jpy` exempt (config as written) | 116 | 29 | **−0.1685 pp** | +0.8590 pp | **0.172** |
| cap on, UTC key, no exemption | 108 | 37 | **+0.9583 pp** | +1.0483 pp | **0.471** |
| cap on, runtime key, `jpy` exempt | 112 | 33 | −0.3472 pp | +0.9550 pp | 0.119 |
| cap on, runtime key, no exemption | 104 | 41 | +0.7796 pp | +1.2606 pp | 0.332 |

**The null control is the finding. Every cap configuration underperforms blocking the same number of
placements uniformly at random** (2,000 draws). The best one saves +0.958 pp against a random mean of
+1.048 pp — *below the median random draw*. On a book with negative realised expectancy any rule that
removes trades improves P&L in expectation; **the cap does not select which trades to remove better
than chance.**

So "re-imposing the cap would have saved about a point on the fortnight" is a true sentence that
means nothing, and it is exactly the shape of claim that got the candidate book activated on a
placebo it had already failed. It is reported here so you never see it without its null.

**One thing this does *not* support, and the first version of this packet claimed it did.** The gap
between the exempt and non-exempt configurations (percentile 0.172 vs 0.471) sits inside a null band
**3.8 pp wide**. Calling it "a second, independent line of evidence for ending the JPY trial" while
refusing to read a same-sized runtime-vs-UTC ordering was inconsistent, and an adversarial pass said
so. **Withdrawn.** D-A's case for ending the JPY trial rests on its own live evidence — −0.453 R
gross, negative *gross*, 37.4 % of net loss — and is strong without this.

**Options.**
1. **Leave the cap off**, and correct the record: amend the `book_owner.py` comments and the config
   block so nothing claims the dial is running inside an envelope it is not, and add a startup
   assertion that logs loudly when the shipped config disagrees with the certified envelope.
2. **Re-impose the cap with no exemption** (`true`, exempt list empty). Restores the certified
   envelope; costs 37 of 145 placements on this window; **contract-bound config edit.**
3. **Re-impose with a deliberately chosen exemption** that is not `jpy`.
4. **Defer to OD-3** and set the envelope with the surviving book's composition.

**Recommendation. Option 1's *record fix* immediately and unconditionally, then option 4 for the cap
itself.** The record fix is not a risk decision and should not wait: right now the code says the
book runs inside a certified envelope and it does not, and there is no test that would catch the
disagreement. That is a correctness defect regardless of which way you eventually set the flag, and
Session M can land it.

The cap itself should wait, for the same reason as D-G plus one more: **this window cannot justify
the cap in either direction.** Re-imposing it cuts trade frequency at exactly the moment Session K is
measuring whether frequency is the book's binding constraint, and the P&L argument for doing so has
just failed its placebo. Decide it with G4 and the survivor book in hand. If you want it re-imposed
before then on pure risk-envelope grounds — "the dial's certification should describe the running
system" — that is a defensible reason and option 2 is the right shape, but note it is a
contract-bound edit (`agent_config.yaml` is one of R2's 43 bound paths) and carries the re-seal cost.

**Explicitly not taken.** `agent_config.yaml` untouched. Both flags are exactly as shipped.

---

## D-M · Replace the gross-cap shed algorithm? (D1)

**Decision.** Keep first-fit-descending, or replace it with proportional scaling.

**Evidence — how much it has cost so far: exactly nothing.** Across the 1,754 recorded governor
states and 469 distinct (headroom, unit-set) cases, **the cap never bound once**: all **6,355**
recorded `would_units` carry `reason: "sized"`, **zero** carry `gross_risk_cap_would_exceed`, and the
maximum utilisation reached was **0.465375**. Whatever the shed's flaws, they have cost the live book
nothing over 38 days, and no replay can reach the shed. The discriminating measurement is therefore
**synthetic by necessity** — 20,000 cases from the live 13-cluster confidence map against the recorded
headroom distribution, of which 5,705 (28.52 %) bind. (The harness reproduces D1's published
four-cluster table and its 28.6 % shortfall case exactly before reporting anything new.)

**Evidence — on binding cases**, in the **conservative arena**: an adversarial pass found that three
clusters in the live map (`metals` 1.00, `energy` 0.80, `fxcross_vol_state_squeeze` 0.12) never
appear in any recorded unit while driving ~94 % of binding cases, so the table below restricts to the
10 clusters that actually fired. That drops the binding rate from 28.5 % to 9.9 %.

| arm | deployed risk | conviction-weighted | headroom used | **top unit starved** |
|---|---:|---:|---:|---:|
| **first-fit-descending (incumbent)** | 0.03220104 | **0.02029418** | 95.20 % | **0.20 %** |
| proportional scaling | **0.03378375** | 0.01926009 | 100.00 % | 0 % |
| largest-first | 0.03233780 | 0.02030722 | 95.60 % | 0.20 % |
| worst-expectancy-drop | 0.03075155 | 0.02006864 | 90.73 % | 0.20 % |
| smallest-first | 0.02004237 | 0.00628737 | 59.41 % | 98.84 % |
| ascending-conviction | 0.02005538 | 0.00629257 | 59.46 % | 98.58 % |
| best achievable *subset* (deployed) | 0.03245212 | 0.02017673 | 95.95 % | 0.66 % |
| best achievable *subset* (conviction) | 0.03235115 | 0.02034912 | 95.64 % | 0.20 % |
| **random order, single draw (NULL)** | 0.02753424 | 0.01513085 | 81.32 % | 32.78 % |

Four things follow, and three of them defend the incumbent:

1. **The incumbent beats a fair null.** It wins **69.65 %** of binding cases and loses 6.17 % against
   a *single* random draw. (The first version of this packet compared against the **mean of 64**
   random draws, which shrinks the null's variance 8× and inflates significance by √64; corrected.)
2. **The incumbent is near-optimal**: **99.23 %** of the best achievable subset on deployed risk,
   **99.73 %** on conviction-weighted risk.
3. **Its starvation rate is the theoretical floor, not a merit — and that is the stronger claim.**
   The top-conviction unit's own risk exceeds the *entire* headroom on exactly **0.20 %** of binding
   cases, meaning **no algorithm whatsoever could seat it** — and the incumbent's starvation rate is
   exactly that 0.20 %. It starves **only when starvation is forced**. (The first version said it
   "beats both exact optima"; that compared against arms optimising a different objective and is
   withdrawn.)
4. **Proportional scaling does *not* dominate — the first version's headline is withdrawn.** In the
   conservative arena it deploys +4.9 % more risk but carries **less** conviction-weighted risk *on
   the mean* (0.01926 vs 0.02029) and loses to the incumbent on **83.16 %** of binding cases. In the
   unrestricted arena its mean edge is a bare +0.0001 and is carried entirely by the top 1 % of wins
   while it still loses 64 % of cases.

**And the brief's three named alternatives are no better**; `smallest_first` and
`ascending_conviction` starve the top unit 98–99 % of the time, worse than random.

**Options.**
1. **Keep first-fit-descending.** Fix the misleading docstring — it claims a property the algorithm
   does not have — and stop.
2. **Replace with proportional scaling.** +4.9 % deployed risk when the cap binds, zero starvation,
   at the cost of a conviction-weighted shape that is worse both on the mean and in 83 % of cases.
   **This is a sizing-semantics change on a funded book under its certified structure.**
3. Keep the incumbent and add proportional scaling as a flagged, default-off variant, so it is
   measurable if the cap ever starts binding.

**Recommendation. Option 1 now, with the docstring fix, and revisit only if the cap starts binding.**
The measurement says the incumbent's cost is (a) **exactly zero realised** over the whole window, and
(b) bounded at **~0.8 %** of deployable risk against the best achievable subset even when it does
bind — while starving the top unit only in the cases where starvation is mathematically forced.
Proportional scaling deploys more risk in a conviction shape that is worse on the mean and in 83 % of
cases. That is not a trade worth making blind, on a funded account, for a regime that has never
occurred. **D1 should be downgraded from a defect awaiting a fix to a documented, measured, latent
property.** The adversarial pass made this recommendation *stronger*, not weaker: it removed the one
argument that pointed the other way.

If you disagree and want the deployed-risk gain, option 3 is the safe path to it: land it default-off
and let Stage 3's hardened packet stream (which will emit raw governor equity and open risk, making
the shed validatable for the first time) decide it on live evidence.

**Explicitly not taken.** `admission.py` is unchanged — including the docstring, which is a Session M
hygiene item, not a Session L change.

---

## D-K · The dial — an input to OD-3, not a decision of its own

**Not a decision to take now.** The dial is part of OD-3 (activation candidate + composition + dial)
and should be set with the survivor book in front of you. This packet exists so that when OD-3
arrives, the dial question is already measured.

**Evidence — three things the grid settles.**

**(1) The ranking is arithmetic, not evidence.** The observed surface is perfectly monotone: smaller
dial, smaller loss, at every step. Under 400 permutations of the realised-R sequence the live dial
holds its observed rank in **84 %** (FTMO) and **65.5 %** (redacted_account) of draws, with null mean rank
8.002 and 8.315 against an observed 8. *"A lower dial would have lost less" is true of any losing
book and carries no information from these 38 days.* Do not let it be an argument.

**(2) What the dial genuinely buys is order-dependence, and that is not in-sample.** Σ R is identical
in every permutation; only the arrival order varies. The width of the outcome band is therefore the
share of the result decided by *when* the wins came:

| dial | FTMO band width | redacted_account band width |
|---:|---:|---:|
| 0.75 % | 1.78 pp | 2.20 pp |
| 1.25 % | 2.72 pp | 3.42 pp |
| **2.00 % (live)** | **3.77 pp** | **4.86 pp** |
| 4.00 % | 4.91 pp | 7.34 pp |
| 20.00 % | 7.67 pp | 16.50 pp |

At every dial ≤ 4 % the upper tail of that band is **positive** — the same 175 trades produce a
profitable fortnight under a luckier ordering. **The dial converts a fixed edge into an increasingly
sequencing-dependent outcome**, and that argument for a lower dial does not depend on knowing this
window's result.

**(3) Three specifics for the dossier.**
- **B65's linear counterfactual is right in direction and ~3 points optimistic.** At 1.25 % the
  governor-aware loss is −1.651 % (FTMO) / −2.470 % (FN) against B65's linear −1.5947 % / −2.3350 %.
  The dial step 2.00 % → 1.25 % saves **34.5 %** of the loss, not 37.5 %.
- **No dial you would plausibly run engages any of the book's discrete brakes.** All trades are taken
  at every dial up to **6.00 %**, three times the ceiling. The first block appears at 8.00 %; the
  first firm-rule breach at **10 %** and only on FTMO.
- **FTMO is the binding account, and not because it traded worse.** At the live dial it sits at
  **53.8 %** of its total-loss wall against redacted_account's 40.9 %, despite losing less in book terms —
  because it entered the window already 2.95 % down. **A dial set per-book rather than per-account
  mis-prices the constraint.**

**Also settled, and it is a safety result rather than a dial result:** B56's daily-reset defect
(FTMO reset on server time instead of 00:00 CE(S)T) had **zero measured effect** on this window — the
grid is identical under both clocks at every dial. But the hazard class is large: moving redacted_account's
reset by one hour changes its worst day by **2.66×** (−1.256 % → −3.336 %) and costs 13 of 78 trades
at the live dial, 56 of 78 at a 4 % dial. **A dial that is safe under one reset rule is not
automatically safe under the other**, so OD-3's dial must be stated per account *with its reset rule
named*.

**Options.** None to take now. When OD-3 arrives the dial choice should be made on: the survivor
book's cost-true expectancy (Stage 1.2), its firing frequency (Stage 1.3 / G4), the order-dependence
table above, and each account's entry drawdown.

**Recommendation.** Carry three constraints into OD-3: **(a)** set the dial per account, not per
book, and name the reset rule with it; **(b)** treat order-dependence, not expected loss, as the
dial's real cost, because it is the only part of this surface that is not in-sample; **(c)** discount
any "dial X would have done better on the fortnight" argument to zero — it failed its null.

**Explicitly not taken.** No dial, profile, or risk setting has been changed or recommended for
change. `ultimate_book_profile` is still `clean3_w7_ceiling_nom2p00`.

---

## Summary — what to answer

| # | decision | recommendation | urgency |
|---|---|---|---|
| **D-G** | re-key `decision_day_of` to runtime? | **defer to OD-3**; when taken, re-derive the Kelly bins with it so a correctness fix does not import a size increase | none — book is placement-deactivated |
| **D-L** | re-impose the certified cluster envelope? | **fix the record now** (comments, config block, a startup assertion); **defer the flag** to OD-3 | record fix: now. Flag: with OD-3 |
| **D-M** | replace the gross-cap shed? | **keep first-fit-descending**, fix the docstring, downgrade D1 to a measured latent property | none — zero realised cost in 38 days |
| **D-K** | the dial | not a decision now; three constraints to carry into OD-3 | with OD-3 |

Reply with the letters and your choice — `D-G: 4`, `D-L: 1`, and so on — or say "your
recommendations" and they will be recorded as taken and routed. **None of the four blocks any wave-3
session.**
