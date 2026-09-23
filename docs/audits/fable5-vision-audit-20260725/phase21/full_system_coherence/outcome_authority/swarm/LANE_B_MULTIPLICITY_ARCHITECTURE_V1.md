# LANE B — Is the multiplicity accounting the binding constraint on the programme?

**Verdict: YES, and the mechanism is narrower and more repairable than the thesis assumed.**

The estate's admission standard is **documented as Benjamini-Hochberg FDR at 10 %** and
**delivered as Bonferroni FWER at α = 0.10**. The two are the same test whenever one
candidate is gated against a declared family whose other members are carried at a fictional
`p = 1.0`, which is every single-candidate gate the estate has ever run. `options.py:46-52`
argues, in the estate's own words, that Bonferroni on a family this size "approaches 'admit
nothing' — and a standard that structurally cannot admit is not a standard, it is a decision
already taken." That is the standard in force.

**Four findings were destroyed by it, and four is a floor.** One of them — the inverted breaker
— should not be armed anyway, for six reasons the gate never asked about and that this lane
found in the gate's own published diagnostics. Both halves matter, and §7 is the half that
keeps this report honest.

*Lane A reached the same core degeneracy independently; priority on that point is its. §6.3
reconciles the two and sets out what each adds.*

Receipts, all reproducible from a clean checkout:

| receipt | what it establishes |
|---|---|
| `lane_b_receipts/LANE_B_FAMILY_TAXONOMY_V1.json` | the 59 are 25 mechanisms; 3 rows are the same trade series as 3 rows already counted |
| `lane_b_receipts/LANE_B_THRESHOLD_CURVE_V1.json` | BH ≡ Bonferroni here, reproduced to 1e-15; the bar-vs-size curve; the ratchet's history; seven competing bills spanning 543× |
| `lane_b_receipts/LANE_B_READJUDICATION_V1.json` | 2,895 verdict rows scanned; 310 significance-only failures; 4 destroyed findings; **0 of 7 negative controls change verdict** |
| `lane_b_receipts/LANE_B_BREAKER_REALISM_V1.json` | the qualifier: 20:1 R:R, 68 % hit rate, **one-minute median hold**, spread = 73 % of the stop distance, 82,300 R total |

---

## 1. The defect, stated exactly

`gate.py:1104-1109`:

```python
effective_family = max(n_judged, spec.declared_family_size or 0)
n_padded = effective_family - len(fam_names)
padded_p = list(fam_p) + [1.0] * n_padded
corr = S.benjamini_hochberg(padded_p, spec.alpha)
```

Benjamini-Hochberg rejects the smallest *k* p-values where *k* is the largest rank with
`p_(k) ≤ α·k/m`. Its entire power advantage over Bonferroni comes from the *other* p-values
in the family being small — that is what lets rank 2, 3, 4 fire at progressively looser
thresholds. Pad every sibling at 1.0 and no rank above 1 can ever fire, so the only operative
threshold is `α/m` and the reported q is `p·m`. That is Bonferroni, exactly.

Not an inference — three independent confirmations:

1. **The estate says so.** `candidate_family.sensitivity()`'s docstring: *"for
   Benjamini-Hochberg the smallest p in a family whose other members are all 1.0 is rejected
   exactly when `p_raw ≤ alpha / m` too … They coincide HERE and only here — with real sibling
   p-values BH is the weaker bill."* Nobody connected that sentence to the fact that every
   real gate run is the degenerate case.
2. **The CS receipt publishes the degeneracy.** `family.multiplicity` carries
   `family_members_with_null: 1`, `family_members_padded_at_p1: 58`, **`k: 0`**,
   **`threshold: 0.0`**. A step-up procedure that rejected nothing at any rank and whose
   operative threshold is zero is not doing step-up work.
3. **It reproduces.** Feeding `[0.0025997400, 1.0 × 58]` to `stats.benjamini_hochberg` and to
   `stats.bonferroni` returns the identical q = 0.1533846615, matching the published value to
   1e-15, and equal to `p × 59` exactly.

**Is the current accounting statistically *valid*?** Yes — padding at 1.0 is conservative, so
FDR is still controlled. It is valid and it is the wrong instrument: it discards the
information BH exists to use, delivers FWER control while its own documentation promises and
justifies FDR control, and does so at a family size chosen for a *different* procedure.

---

## 2. Q1 — What is actually in the 59?

**They are not 59 comparable hypotheses. They are 25 mechanisms, and 34 of the 59 rows repeat
a mechanism already declared.** Classification is bound to production source and to the
estate's own artifacts, never to prose: rows 1–32 by the `SleeveSpec.generator` function each
registry entry actually holds; rows 40–48 by `AF_FAMILY_TRADES.mechanisms.*.parent_sleeve`
and its `parity` block; rows 54–57 by `CH_MEASUREMENT_PROTOCOL_V1.looks[].sleeve`.

| derivation | rows | what it is |
|---|---:|---|
| `BASE` (not derived from another row) | 34 | includes 9 instrument-siblings inside the registry itself |
| `INSTRUMENT_SIBLING` | 6 | same entry rule, different symbol |
| `OVERLAY` | 5 | `fx_jpy` + a meta-label filter at 5 cuts |
| `RETEST` | 4 | CH's P1-HIST milestones — the same registry sleeve at another account/exit |
| `THRESHOLD_VARIANT` | 3 | `sub_xvol_pullback` with the discretizer constants moved |
| `REGIME_CELL` | 3 | a parent rule plus a conditioning filter |
| **`DUPLICATE_SERIES`** | **3** | **the same trades as a row already counted** |
| `POOLED_AGGREGATE` | 1 | nine already-declared rows judged as one series |

The seven mechanisms carrying more than one row:

| mechanism | rows |
|---|---:|
| `mx_d1_volume_surge_reversal` | 12 |
| `mx_d1_donchian_20_breakout` | 9 |
| `fx_jpy.generate_fx_jpy` | 6 |
| `substrate.generate_sub_xvol_pullback` | 6 |
| `energy_agri.generate` | 4 |
| `asia_pdl_fade.generate` | 2 |
| `mx_d1_atr_mean_reversion` | 2 |

### 2.1 Three rows are literally the same series, proved by the estate's own parity artifact

`AF_FAMILY_TRADES.json.gz` → `parity.W_MX_PILOT` maps registry sleeve names to AF member
names and publishes `n_compared: 10, n_exact: 10`:

| declared row | identical row | trades |
|---|---|---:|
| `mxf_volume_surge_reversal_ger40_d1` | `mx_ger40_cash_d1_volume_surge_reversal` | 110 = 110 |
| `mxf_volume_surge_reversal_jp225_d1` | `mx_jp225_cash_d1_volume_surge_reversal` | 110 = 110 |
| `mxf_volume_surge_reversal_us30_cash_d1` | `mx_us30_cash_d1_volume_surge_reversal` | 121 = 121 |

**A multiplicity bill is a bill on independent opportunities to find a false positive. Two
rows that are the same trade series are one opportunity, not two.** Charging two is not
conservative-but-safe; it is arithmetically wrong in the direction that destroys findings.

### 2.2 Two rows tested nothing and are charged anyway

`mx_eu50_cash_*` and `mx_fra40_cash_*` carry `look_taken: false` — `n_trades = 0`, no null,
no p-value, no possibility of a false positive. The `LOOKS_TAKEN` basis excludes them; the
**ratified basis is `all_declared`, which does not.**

### 2.3 The breaker is not in the same family as the other 57 in any meaningful sense

57 of 59 rows are generated from the `ultimate_book` M15/H4/D1 archive. **Two** — CP's
NY-metals-LONG and CQ's inverted breaker — come from the broad-V4 true-UTC replay exhaust: a
different generator, a different substrate, a different symbol surface, a different path-truth
pipeline. BH assumes a family of comparable hypotheses tested for the same question. Charging
a broad-V4 path-pool candidate for 57 looks at `ultimate_book` sleeves is a category error,
and it is conservative in exactly the direction that costs real findings.

**Verdict on Q1: the 59 are structurally a small number of mechanisms with a long tail of
variants, duplicates and re-tests. Pooling them as one BH family is statistically wrong.**

---

## 3. Q2 — The bar as a function of family size

At α = 0.10 the rank-1 threshold is `α/m`. The breaker's raw p is **0.0025997400**.

| family size *m* | rank-1 bar (raw p) | odds | breaker |
|---:|---:|---:|---|
| 1 | 0.100000 | 1 in 10 | ADMIT |
| 5 | 0.020000 | 1 in 50 | ADMIT |
| 10 | 0.010000 | 1 in 100 | ADMIT |
| 25 (distinct mechanisms) | 0.004000 | 1 in 250 | ADMIT |
| 32 (V1, owner's first ratification) | 0.003125 | 1 in 320 | ADMIT |
| **35 (V2, the last ratified declaration)** | **0.002857** | 1 in 350 | **ADMIT** |
| **38 — the last size at which it admits** | 0.002632 | 1 in 380 | ADMIT |
| **39** | 0.002564 | 1 in 390 | **reject** |
| 54 (minus no-looks and duplicates) | 0.001852 | 1 in 540 | reject |
| **59 (V27, as charged)** | **0.001695** | 1 in 590 | reject |
| 69 (AA historical) | 0.001449 | 1 in 690 | reject |
| 321 (`MECHANISM_CROSS_V1`) | 0.000312 | 1 in 3,210 | reject |
| 522 (`B7_5_SEPARABILITY_MINE_V1`) | 0.000192 | 1 in 5,220 | reject |
| 30,925 (measured trial ledger) | 0.0000032 | 1 in 308,000 | reject |

### 3.1 The number is unidentified, and it decides everything

The estate holds **seven simultaneous bills for the same estate**, spanning **543×** (59 to
30,925). Every one is defensible on its own logic. None is derivable from the others. Every
verdict is a pure function of which is chosen.

`gate.py:1100-1103` already knows about the ledger and declines to use it *because it is read
after the outcomes are* — correct, and it leaves the actual number unjustified rather than
justified. **An unidentified parameter that decides every verdict is not a standard.**

---

## 4. Q3 — The ratchet's incentive

**Yes. Every exploratory look permanently raises the bar for every future finding, by
design.** `candidate_family.py:32-34`: adding a member raises the bill, withdrawing does not
lower it, size is monotone non-decreasing. The rationale is sound — it removes the incentive
to curate, and under a shrinking family "withdraw the unsuccessful siblings" would be the
cheapest route to an admission.

What it costs, measured:

- **The family went 32 → 59 in three days** (V1 2026-07-30 → V27 2026-08-01), through 27
  versions.
- **The owner ratified the rule at V2, when the family was 35.** V3 through V27 carry
  `ratified_by: null` — **24 members and 25 versions of unratified growth.** The owner
  ratified a *rule*, and the rule says the number grows; but nobody has since put the number
  in front of him.
- **The bar tightened 1.686×**, from 0.002857 to 0.001695. **The breaker's p of 0.0026 fell
  into exactly that gap.**
- **Of the 24 rows added after ratification, zero produced an admission.** CP's #58 is
  `NOT_EVALUABLE`; CQ/CS's #59 is `REJECT`; none of the rest returned an ADMIT at the ratified
  rule. Twenty-four looks that found nothing, each of which made the next finding harder.
- **The measured trial ledger holds 30,925 look events, of which 304 (0.98 %) recorded an
  `admitted` outcome and 23,985 recorded `rejected`.** That is the estate's own record of how
  much searching it has done relative to what it has kept.

**The incentive is real: the estate is penalised for researching.** But — and this matters —
the ratchet is *correct in principle and mis-instrumented in practice*. It counts **rows
declared**, not **independent opportunities**. Three of the 59 rows are the same series; two
tested nothing; 34 repeat a mechanism. Fixing the instrument does not weaken the ratchet.

**One thing this report will not do.** "It would have admitted at the family size the owner
ratified" is a measurement of how far the bar moved. It is **not** an argument for re-using
35. Choosing the family size after seeing the outcome is precisely the defect
`candidate_family.py` exists to close, and this lane declines to reintroduce it.

---

## 5. Q4 — Architectures, with their honest false-discovery cost

### Option 0 — Status quo: BH-with-padding at `all_declared`, α = 0.10

- **What it actually is:** Bonferroni FWER at 0.10. Bar today: p ≤ 0.001695.
- **False-discovery cost:** the lowest available — P(any false admission) ≤ 0.10 across the
  whole family.
- **Cost the other way:** it delivers a standard `options.py` itself argues is "a decision
  already taken", and it is charged at a family size assembled for a different procedure.
- **Breaker:** REJECT.

### Option 1 — **RECOMMENDED (a): stop padding. Run BH as BH.**

Compute BH over the family's **real** p-values. This is not a relaxation; it is the procedure
the estate documents, actually executed.

**The arithmetic is decisive.** At m = 59 and α = 0.10 the rank-2 bar is 0.0033898. The
breaker at 0.0026 clears it. So BH admits the breaker **at the unchanged family of 59 and the
unchanged α of 0.10 as soon as ONE other declared member carries a real p at or below that
bar.** Such members demonstrably exist inside this family — `mx_btcusd_d1_donchian_20_breakout`
(declared row 15) carries **p = 0.00070** at its zero-carry ceiling (`EXIT_FRONTIER_V1`) and
**p = 0.00110** at `target_5R | RECORDED | mid` (`AL_CANDIDATE_DOSSIER_V1`). Substituting one
of them: BH returns `k = 2`, breaker `q = 0.0767`, **rejected = True**.

> **The REJECT is produced by the padding, not by the family size.**

- **False-discovery cost:** unchanged FDR ≤ 0.10 — this *is* the FDR procedure. BH's guarantee
  requires independence or PRDS; the family is positively dependent (three rows are the same
  series), for which PRDS is the standard assumption and BH is known to hold. The strictly
  conservative fallback is Benjamini-Yekutieli, whose rank-1 bar at m = 59 is
  `α/(m·H₅₉)` = 0.000363 — **BY does not rescue the breaker even with real p-values** (it would need
  8 siblings below it: rank 8 at `8α/(m·H₅₉)`). Stating that is the test that this recommendation is not
  reverse-engineered.
- **What it costs to adopt:** the estate has **never assembled the 59 members' p-values at one
  comparable standard** (population, band, cost artifact, exit contract). That assembly is the
  concrete engineering task, and it must be done **prospectively** — the standard fixed before
  the p-values are read — or it becomes the retrospective family choice all over again.
- **Breaker:** ADMIT, conditional on that assembly.

### Option 2 — **RECOMMENDED (b): per-mechanism families, declared prospectively**

Correct a candidate against the hypotheses that are *exchangeable with it and tested for the
same question*. The breaker's family is the broad-V4 true-UTC candidate factory — **2 declared
members**, not 59.

- **Statistical justification:** BH's family is defined by the inferential question, not by the
  filesystem. Charging an FX-D1 exit sweep against a crypto-donchian threshold variant is not
  conservatism, it is a mis-specified family.
- **False-discovery cost, honestly:** per-family FDR control does **not** guarantee pooled FDR
  control across families. The right way to price it is an absolute budget: with per-family
  FDR 0.10 and total admissions *R*, expected false admissions ≈ 0.10·R. At the estate's
  realistic *R* (1–5), that is **0.1–0.5 expected false admissions** — small in absolute
  terms, which is what a book owner cares about.
- **The gaming risk, and its guard:** "declare a new mechanism, get fresh α". Guards: (i) the
  partition must be structural — a distinct generator and substrate, verifiable from source,
  which is exactly how `LANE_B_FAMILY_TAXONOMY_V1.json` builds it; (ii) it must be declared
  before the outcome; (iii) the ratchet applies **within** each family unchanged; (iv) opening
  a new mechanism family draws from a standing α budget rather than getting free α.
- **Breaker:** ADMIT (q = 0.0052 at m = 2).

### Option 3 — **RECOMMENDED (c): two-tier — match the bill to the capital at risk**

This is the one that dissolves the problem rather than re-tuning it.

- **Discovery tier.** Per-mechanism honest BH at α = 0.10 (Options 1 + 2). Output is
  **incubation only, never arming** — the same firewall `options.py` already puts around
  Option C.
- **Deployment tier.** Graduation to size requires a **forward out-of-sample record** at
  economically inert weight. Multiplicity is not binding there, because a forward record is
  **one pre-committed test**: you cannot search a future that has not happened.

**This is not new machinery — the estate already runs it and the owner already approved it.**
`mx_btcusd` has been live on FTMO since 2026-07-31 at registry confidence **0.025**
(≈ 0.32 % of a 7.77 total-weight book), explicitly because "the forward record is the point".
`FORWARD_INCUBATION_SPEC_V1.md` specifies the incubation lane at **0.10 % risk per trade,
max 2 concurrent, 4 new positions/day**, owner-approved for data collection. What is missing
is not the mechanism — it is that this is a one-off rather than **the standing rule**.

- **False-discovery cost:** a false admission at the discovery tier costs an incubation slot
  and ~0.3 % of book risk. A false admission at the deployment tier is unchanged, because the
  deployment test is the forward record.
- **The category error it fixes:** admitting at 0.025 confidence weight and admitting at full
  size are charged the **same α** today. They are not the same decision.
- **Breaker:** enters **incubation**, not arming.

### Option 4 — The "book-level diversifier door" the gate's repair queue names: **REJECT**

`walkforward/diversifier.py` exists, and its own docstring records that an adversarial pass
**reached `CERTIFIED_DIVERSIFIER` with all seven checks passing on six independent attacks**;
the largest certified loser lost **8,583.8 R**. Two used real registry sleeves: `idxrev` at
−6,515.6 R (93.7 % of the sleeve invisible to every statistic the certification computes) and
`metals_softband` at −8,583.8 R at 100 % cost coverage. The gate's repair queue names this
door; it is the **weakest** option on the table and must not be a route to arming.

### Option 5 — α = 0.20 (Option C): **REJECT as p-hacking by architecture**

It lowers the bar without changing what the bar measures. `options.py:110` already
disqualifies it for arming in its own text. Rejected.

### Option 6 — Retroactively using the ratified size 35: **REJECT**

Selecting the family size after seeing the outcome. Rejected — see §4.

### Option 7 — Family hygiene (drop the 2 no-looks and 3 duplicates): **DO IT, but it is not a lever**

Removing them takes m from 59 to 54 and the breaker's q from 0.1534 to 0.1404 — **still a
REJECT**. It is a correctness fix, not a rescue, and saying so is how you can tell the rest of
this section is not reverse-engineered to admit.

---

## 6. Q5 — Retrospective re-adjudication

**Census.** 2,895 gate-verdict rows across every JSON in the audit tree; 2,361 enter the
census after excluding post-hoc constructions by name (`POST_HOC_COMPOSITE`,
`zero_carry_ceiling`, `best_cell_at_spread_bands`) and de-duplicating cells that appear once
per declared-family stamp. **310 rows fail on significance alone** — every other core gate
(expectancy, lifetime, stability, robustness) passes.

**Re-adjudication.** Not by dropping the multiplicity charge — by *moving it to the family the
look was actually taken in* and computing BH with real sibling p-values. An exit sweep of 61
cells is still charged 61. Post-selection short lists (a four-finalist dossier whose own
receipt publishes `trial_ledger_measured: 5734`) are excluded entirely.

**Result: 122 cells flip — 118 across 9 headline grids plus 4 inside the excluded short-list
groups. 188 of the 310 do not flip. It is not a blanket pass.**

**Collapsed to the object a decision is actually taken on** — 42 exit cells of one sleeve are
one finding restated 42 times, because they are the same trades under different exit rules —
**5 distinct candidates surface. One (`mx_btcusd`) the estate later admitted by another route.**

# **4 findings were destroyed.**

| candidate | raw p | pooled OOS | status |
|---|---:|---:|---|
| `cq_current_breaker_re_entry_inverted_5d_stop_0p25d` | 0.002600 | +7.519 R | never admitted — the trigger for this lane |
| `sub_xvol_pullback` (exit frontier / population dossier) | 0.005799 | +1.044 R | **an ARMED sleeve**; its exit improvement has never cleared |
| `mx_ethusd_d1_donchian_20_breakout` | 0.006399 | +0.196 R | never admitted |
| `thr_sub_xvol_pullback_vr14_s150_ac015` | 0.029497 | +0.501 R | never admitted |

The second row is the one with money on it today: `sub_xvol_pullback` is one of the three
armed sleeves, and the exit repair that would improve it has been blocked on significance —
consistent with Session AU's independent finding that AK's `target_4R` cell rejects at all
four bands, p = 0.0080 against a 0.002083 rank-1 bar.

### 6.1 The false-discovery check, and it comes out clean

`phase5/receipts/W_NEGATIVE_CONTROLS.json` carries six constructed adversaries and one
positive control. Re-adjudicated under a per-mechanism family — the most permissive
architecture recommended here — **0 of 7 verdicts change.**

| adversary construction | raw p | caught by |
|---|---:|---|
| shuffled labels, zero expectancy (the honest null) | 0.2689 | expectancy / lifetime |
| random entry, matched vol, zero edge | 0.9650 | expectancy |
| cost-eaten: gross-positive, net-negative | 1.0000 | expectancy |
| day-clustered noise, zero edge | 0.3830 | robustness |
| one-regime: all edge in a single year | 0.0001 | **stability** |
| shuffled labels, positive expectancy by construction | 0.0015 | admitted, correctly — it *is* a positive-expectancy series |

Two things follow, and they are the empirical backbone of this report:

1. **On the four genuinely zero-expectancy nulls, the raw block-permutation p is 0.269, 0.383,
   0.965 and 1.000. None is below 0.26.** The separation between the honest nulls and the
   breaker's 0.0026 is a factor of ~103. The instrument is far better separated than a bar of
   1-in-590 assumes.
2. **The significance gate has never been the gate that stopped a known-null series in this
   estate.** Every adversary that rejected was caught by expectancy, lifetime, stability or
   robustness. Significance is the gate that stopped the breaker, which passed all seven
   others.

*Caveat, stated because it is real:* four honest nulls is a small control set, and constructed
nulls are easier than market data, which carries structure the constructor did not include.
This is evidence, not proof.

### 6.2 The census is a LOWER BOUND, and two sibling lanes corroborate it

The scanner can only see verdict rows that publish a `gates` block. **Session AH's receipts do
not** (`AH_TICK_HOUR_CELLS.json`, `AH_COMPOSITION_TESTS.json` and the rest carry no `gates`
key), so anything AH surfaced is structurally invisible to this census. Lane D found exactly
such a case and calls it *"the largest un-pursued positive in the corpus"*:

> **F19** — AH's `volume_surge_reversal × index × D1` gated on `VOL_REGIME == hi`:
> **+0.2248 R/day, raw p 0.0127, 5 of 5 OOS folds positive**, n = 203, against an ungated
> comparator of +0.0999 (p 0.1204, folds 0.4). Routed to Borhen as *"the strongest new
> candidate this wave produced"* — and **the string appears in no document of any later
> phase.** Its family is also one of only 2 of 30 to pass AF's two-clause coherence test.

At its own 9-cell bill, F19's q is 0.114; at the estate family of 59 it is 0.75. It is a fifth
destroyed finding that this lane's instrument could not reach. **Treat 4 as the floor.**

### 6.3 Reconciliation with Lane A

Lane A reached the same core degeneracy independently and by a different route — *"BH here is
identical to Bonferroni"*, *"58 of 59 members were never tested … BH bought exactly zero power
over Bonferroni; the family is pure denominator"*, and the same **38** as the largest family at
which the breaker admits. Two independent lanes converging on the arithmetic is the strongest
verification available here, and priority is Lane A's on those points.

What each lane adds is disjoint, and the pieces compose:

| | Lane A | Lane B (this) |
|---|---|---|
| BH ≡ Bonferroni | found it | reproduced it to 1e-15 and traced it to `gate.py:1104-1109` |
| duplicates | "4 literal duplicates" (the CH re-tests) + "19 nested near-duplicates" | proves **3 rows are the same trade series to the trade** via AF's `parity` block (10/10 exact) — a stronger claim than near-duplicate — and classifies all 59 by production generator |
| the fix | not proposed | **BH admits at the unchanged m = 59 and α = 0.10 given one real sibling p-value**; three architecture options with priced false-discovery costs |
| scope | the breaker | **2,895 verdict rows across the whole estate → 4 destroyed findings** |
| false-discovery check | — | **0 of 7 negative controls change verdict** |
| the bill | notes the estate's own "FLOOR, not a measurement" | **seven simultaneous bills spanning 543×**; 30,925 measured looks vs 304 admissions |
| 5D/0.25D plausibility | argued from a driftless-walk bound | measured from the receipt: **one-minute median hold**, 68 % target rate, spread = 73 % of the stop, **zero** same-bar ambiguity on 96.2 % M1 paths |

Where Lane A and this lane could be read as disagreeing, they do not: Lane A's *"the judged
candidate is not a member by [the family's own] rule"* and this lane's §2.3 (*"57 of 59 sit on a
substrate the breaker does not share"*) are the same finding stated as membership and as
substrate.


---

## 7. The half that keeps this honest: the breaker should still not be armed

Everything above says the REJECT was statistically wrong. It was. **The candidate should
nonetheless not reach capital on this evidence, and the reasons are visible in the gate's own
published diagnostics — none of which the gate asked about.**

The transform (`current_breaker_re_entry_repair.py:26-31`) sets target = 5 D, stop = 0.25 D,
"where D is the candidate's original absolute entry-to-stop distance". So **R = 0.25 D and the
target is 20 R — a 20:1 reward-to-risk.**

| measured | value | source |
|---|---:|---|
| **median hold** | **1.00 minute** (p10 1.00 min, mean 26.3 min, cap 120 min) | `diagnostics.holding` |
| mean modelled spread cost | **0.7302 R** — spread alone consumes **73 % of the stop distance** | `cost_decomposition.terms.spread_r` |
| April outcomes | 2,506 TARGET / 738 STOP / 427 HORIZON → **68.3 % target rate** | `CS_APRIL_CURRENT_BREAKER_REPAIR_V1` |
| May outcomes | 1,832 / 865 / 674 → 54.3 % target rate | `CS_MAY_CURRENT_BREAKER_REPAIR_V1` |
| same-bar ambiguity | **0** in TRAIN, OOS and full capture, **both** captures | `repair_trade_bindings` |
| path truth (April + May) | 265 ordered-tick rows; **6,777 of 7,042 conservative M1 (96.2 %)** | CS result §3, §4 |
| total economics | +12.59 R/trade × 6,536 = **82,300 R** | `cost_decomposition` |
| OOS null | **31 observations, 11 blocks**, p_floor 0.000588 | `telemetry.p_floor` |
| fidelity | **transferred class rate**, "not direct measured recall for the repaired identity" | `fidelity_stamp`, CS §5 |
| fold means | 11.25 → 7.45 → 3.85 (chronological, monotone) | `diagnostics.by_fold` |

**Read the first three rows together.** The median trade claims price traversed five times the
original entry-to-stop distance, in one minute, without first traversing a quarter of it
against — through a stop whose entire width is only 1.37× the modelled spread cost. Spread
alone consumes 73 % of the risk unit, and yet the stop is hit on only 20 % of trades while a
20 R target is hit on 68 %.

And the ambiguity count is **exactly zero**, across both captures, with 96.2 % of April and
May paths resolved from M1 OHLC bars rather than ordered ticks. A stop whose whole width is
1.37 spread-costs sits well *inside* a typical M1 bar's range. Zero same-bar ambiguity across
that population is the least plausible figure in the receipt, and it is the first thing to
re-measure.

**None of this proves an artifact.** It establishes that six cheap questions stand between the
receipt and a capital decision, that all six are answerable without a new sealed replay, and
that **not one of them is the question the gate asked.** A gate that fires on breadth spent
the estate's attention on a q-value while a 20:1 win rate at one-minute resolution went
unremarked.

That is the strongest possible argument for the architecture in §5: **the multiplicity gate is
simultaneously too strict to admit real findings and pointed at the wrong failure mode.**

---

## 8. Answers, in one line each

1. **The 59:** 25 mechanisms, not 59 hypotheses. 34 rows repeat a declared mechanism, 3 are
   the same trade series as rows already counted (proved by the estate's own 10/10 parity
   artifact), 2 tested nothing and are charged anyway, and 57 of 59 sit on a substrate the
   breaker does not share. **Pooling them as one BH family is statistically wrong, in the
   conservative direction that destroys findings.**
2. **The curve:** the rank-1 bar is α/m. It has moved 0.003125 → 0.002857 → 0.001695 as the
   family went 32 → 35 → 59 in three days. **38 is the last family size at which the breaker
   admits.** Seven competing bills exist for the same estate, spanning 543×.
3. **The ratchet:** yes, every look permanently raises the bar. 24 members were added after
   the owner's only ratification, **all unratified, none produced an admission**, and they
   tightened the bar 1.686× — through the exact window the breaker's p sits in. The measured
   ledger holds 30,925 looks against 304 admissions (0.98 %).
4. **Recommended architecture:** **(a) stop padding — run BH with real sibling p-values;
   (b) per-mechanism families declared prospectively from structural source evidence;
   (c) two-tier — discovery admits to *incubation* at ≤0.10 % risk, deployment requires a
   forward record.** Expected false-admission cost: **0.1–0.5 admissions** in absolute terms,
   and ~0.3 % of book risk per false discovery-tier admission. **0 of 7 negative controls
   change verdict.** Rejected: α = 0.20, the diversifier door, and retroactive family sizing.
5. **Destroyed findings: 4, and that is a FLOOR.** (122 cells, 9 grids, collapsed to 5
   distinct candidates of which 1 was later recovered.) One of them —
   `sub_xvol_pullback`'s exit repair — is on an **armed sleeve today**. Lane D's F19 is a
   fifth that this lane's instrument structurally could not see (§6.2).
6. **The breaker under the recommended architecture:** **ADMITTED to incubation, not to
   capital** — and §7 lists six reasons, all from the gate's own diagnostics, that must be
   answered before even that.

---

## 9. What to do next, in order

1. **Family hygiene** (cheap, correctness-only, does not move a verdict): flip the 3 duplicate
   rows to `withdrawn` with the parity citation, and record why `all_declared` charges the
   2 zero-trade rows. m 59 → 54; the breaker still rejects. Do it anyway.
2. **Put the number in front of the owner.** He ratified a rule at m = 35. It is 59, through
   25 unratified versions. That is his call, not a session's.
3. **Assemble the family's p-values at one prospectively-fixed standard** so BH can be run as
   BH. This is the single highest-value engineering item in this report and it needs no new
   data — the p-values exist across the receipts; what is missing is one comparable standard,
   declared before they are read.
4. **Declare the mechanism partition** from `LANE_B_FAMILY_TAXONOMY_V1.json`, prospectively,
   with the ratchet intact inside each family.
5. **Promote forward incubation from a one-off to the standing deployment tier**, per
   `FORWARD_INCUBATION_SPEC_V1.md`.
6. **Re-measure the breaker's path truth before anything else about the breaker.** Same-bar
   ambiguity of exactly zero on a stop whose whole width is 1.37 spread-costs, with 96.2 % M1
   path resolution, is the question. Not the q-value.
