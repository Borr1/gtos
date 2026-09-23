# Session AF — the breadth prescription, executed: it does not work, and the measurement says what to do instead

**Branch `phase7/family-expansion`. Blocks B800–B818. Not merged.**
**246 members · 30 families · 134,027 trades · 26 gate runs · 778 ledger rows.**
Scoped verification per `WAVE_7_WORKING_AGREEMENT.md` §2 — receipt in §9.

---

## 0. Headline

The estate's most common honest failure is significance, and the Fundamental Law's answer is
breadth. `AA_ESTATE_WALK` filed 22 `BREADTH` rows on that logic, each carrying the required
multiple `(z_α / z_observed)²`. This session ran it — five production mechanisms across
every symbol in the archive, both timeframes where it was asked for, judged as families with
every look counted.

**Breadth does not deliver, and the reason is measurable rather than statistical.** Pooling
made the estate's best new-edge candidate monotonically worse:

| set | n | pooled OOS R/day | raw p |
|---|---:|---:|---:|
| `BTCUSD` alone, on the eras the spread model actually measured | 232 | **+0.3894** | **0.0064** |
| `BTCUSD` alone, all eras, mid band | 318 | +0.2383 | 0.0145 |
| the 3 crypto donchian tags the estate authored, RECORDED eras | 483 | +0.2023 | 0.0461 |
| the 3 authored tags, all eras | 818 | +0.1260 | 0.0744 |
| the 9-symbol archive crypto class, RECORDED eras | 594 | +0.1602 | 0.0834 |
| the 9-symbol class, all eras, mid band | 1,207 | +0.0111 | 0.4442 |

Every symbol added costs it. The √k gain assumes members of **equal** information
coefficient; the crypto donchian class runs **+0.349 (BTCUSD) to −0.225 (LTCUSD)** per trade
gross, a cross-member SD of 0.192 against a family mean of 0.061. That ratio — 3.12 — is
the diagnosis, and it generalises as a **two-part** test:

| family | k | dispersion ratio | members + | raw p |
|---|---:|---:|---:|---:|
| `volume_surge_reversal` × index × D1 | 6 | **0.736** | **6/6** | **0.1204** |
| `energy_fvg_retest` × energy × H4 | 3 | **0.117** | **3/3** | **0.1740** |
| `atr_mean_reversion` × metal × D1 | 9 | 0.610 | 0/9 | 1.0000 |
| `atr_mean_reversion` × energy × D1 | 3 | 0.682 | 0/3 | 0.6621 |
| `donchian_20_breakout` × crypto × D1 | 9 | 3.119 | 5/9 | 0.4442 |
| `crypto_h4_donchian_ac60` × crypto × H4 | 9 | 4.735 | 5/9 | 0.9413 |
| `donchian_20_breakout` × fx × D1 | 14 | 80.132 | 5/14 | 1.0000 |

**Both halves are needed and the first draft of this section got it wrong.** Seven of the
thirty families have a dispersion ratio below 1, not two — because the ratio is `sd/|mean|`
and is therefore sign-blind: a family whose members agree on being *uniformly bad* scores
just as tight as one whose members agree on being good. `atr_mean_reversion` × metal is 0.610
with 0 of 9 members positive.

The test that actually separates them is **ratio < 1 AND every member positive**, and
exactly two of thirty pass it — the same two that hold the two best p-values in the grid.
The rule this session leaves behind is therefore one query with two clauses: **before
spending a session on breadth, check that the members agree AND that what they agree on is
positive.** It costs nothing on trades that already exist.

**Four things Borhen can decide on, none of which existed this morning.**

1. **The armed `crypto` sleeve has a positive out-of-window number for the first time.** Its
   own rule on its own two symbols over the whole archive: **+0.0869 R/day OOS, 60 % of
   folds positive, raw p 0.3001, n=182, 2017-02..2026-07.** Against `CLAUDE.md` §4's
   +0.100 %/month for the armed four as a block, this is the sleeve-level version and it is
   the right sign.
2. **The de-risk the plan hoped for is refuted, not unproven.** The same rule across the
   nine-symbol crypto class scores **−0.1849** with a dispersion ratio of 4.74 and a
   best-to-worst spread of 1.80 R per trade. The book's largest edge does **not** become a
   diversified cluster on this evidence. Composition is yours; this session recommends
   against pricing it as diversification.
3. **`energy_agri`'s mechanism carries — its class is three symbols wide.** +0.4571 R/day,
   the strongest pooled mean in the grid, the tightest coherence measured anywhere here
   (3/3 positive, ratio 0.117). It fails on sample, and the two things that would fix it are
   a `NATGAS.cash` **commission** (its spread is already measured; `cost_r` refuses on an
   unknown commission with no peer to transfer from — §3.3) and CORN/COTTON bars.
4. **The cost model everything downstream is charged with has a defect, found by suspecting
   my own probe.** `spread_model_v1` multiplies an era ratio by an hour-of-week multiplier
   and each was validated alone; their product reaches **198× the modern base** on NZDUSD in
   the 2000s, charging 178 % of the risk unit as spread. Details, size and interim treatment
   in §6 — it is routed to AG's lane, not repaired here.

**Nothing admitted.** 0 of 30 families and 0 of 246 members, at three standards × four cost
bands. The best pooled raw p is 0.1204. That is not the headline and §7 is the reason: every
one of the 30 leaves with a prescription, and 23 of them leave with the *same* one, which is
itself the finding.

---

## 1. What was measured, and how it is known to be the same instrument

**246 (mechanism, symbol, timeframe) cells over the whole archive, 134,027 trades in 406 s.**
Five production rules: the three `market_expansion_d1` D1 mechanisms, the armed `crypto`
sleeve's ac60-gated H4 donchian (`crypto.py:31-66`), and `energy_agri`'s FVG retest
(`energy_agri.py:47-63`). The grid is a complete cross — every cell taken, in a fixed order,
with every drop recorded — so nothing in it was chosen after an outcome was seen.

Generation walks bars directly rather than driving `GenerationPort`, because 246 members
that are deliberately in no registry would have meant editing `sleeves/registry.py` for
research symbols on a repo whose FTMO book is armed. That is an equivalence claim, so it is
measured:

**`W_MX_PILOT.json` parity: 10 of 10 exact, on two independent statistics.** Trade counts —
189/189, 318/318, 286/286, 311/311, 110/110, 110/110, 503/503, 71/71, 121/121, 67/67 — for
every one of W's twelve live `mx_*` sleeves that has bars, *and* median hold in D1 bars,
which W publishes separately and which matches 10/10 (nine at 3, `mx_nzdjpy` at 4). Counts
alone could in principle coincide over a different trade set; a second statistic computed
from the exit index makes that a great deal less likely. `energy_agri` is exact against
`AA_ESTATE_TRADES.json.gz` at 67/67. The two sleeves not compared, `mx_eu50_cash` and
`mx_fra40_cash`, have no bars in either archive, which is AA's standing `GENERATION` row.

Getting to 10/10 cost two findings.

### 1.1 The pre-gap bar, at D1, where it is four times larger than AB measured it

The first run was a strict superset of W's — +11 % on `mx_nzdjpy`, +10 % on `mx_cadjpy` —
and `only W` was **empty**. All 56 extra NZDJPY bars are the last closed bar before a
≥ 2-interval gap: 53 Thursday-dated with three days to the next bar, one Wednesday with
four, two Sundays with two.

That is `bar_provider.py:60-80`'s own docstring: the engine drops that bar as *forming* at
its own close (`:92`) and refuses it as stale afterwards (`book_engine.py:512`). Session AB
measured it at H4 — 29 of 29 fires immediately before a gap, 1.3 %–6.8 % of trades on five
sleeves. **At D1 it is much larger, because every Friday is a pre-gap bar**: 5,705 of
134,027 trades (**4.26 %**), −440.0 R gross, mean **−0.0771 R** against **+0.0117 R** for
reachable trades.

`engine_reachable` reproduces the rule exactly and the primary population excludes those
bars, which is what makes the parity exact. Note the sign: the unreachable population is
*worse*, so this plumbing defect is not currently costing money on this family — but the
number is now known rather than assumed.

### 1.2 Which bars a sleeve can trade depends on which OTHER symbols share its launcher

The one remaining difference — AA 181 `crypto` trades against 182 — is BTCUSD's
2021-12-04 02:00 bar, and the cause is structural. AA's H4 union grid is its nine sleeves'
symbol surfaces (44,681 closes); this run's is all 41 archive symbols (45,179). The instant
that rescues that bar, 14:00, is contributed by **AVAUSD and XTZUSD**. Restricting this
driver's grid to AA's symbol set reproduces AA's 44,681 closes and its 18,007 reachable
BTCUSD bars exactly.

Live the coupling is narrower and different: the launcher triggers on **reference symbols
only** — `DEFAULT_REF_SYMBOL = {16388: ["XAUUSD","BTCUSD"], 16408: ["XAUUSD","BTCUSD"]}`,
`launcher.py:49`. In the era where both exist the research grid over-counts by **3.34 % of
D1 and 0.09 % of H4** reachable bars; before BTCUSD existed it reaches 15–17 % on
long-history FX, which is an archive artifact and not a live property.

### 1.3 A correction to the plan's own arithmetic

**The archive is 41 instruments, not 43.** `FOURTH_REVIEW.md` §5.4 says 43 and this
session's prompt repeats it. `GER40_cash` and `JP225_cash` are re-exports of `GER40` and
`JP225` under the dotted broker name — identical `broker_symbol` in `BARS_MANIFEST.json`,
byte-identical at D1 and H4 for JP225, one field of one row apart for GER40 (the forming
bar, re-pulled seconds later in the dotted-name top-up). Counted once; keeping both would
have put one instrument in a family twice and bought free breadth.

---

## 2. The family test, and the bill it pays

Two runs over the same trades:

* **member** — every cell judged as its own sleeve, which is what W did to twelve `mx_*`
  sleeves generalised to 246;
* **family** — each mechanism × asset class × timeframe pooled into ONE sleeve, so the
  gate's own day panel takes the equal-weight cross-section. The √k is produced by sealed
  panel code, not by anything this session wrote.

**Both are corrected against the same 276-look bill** (246 member cells + 30 families), so
the family-vs-standalone comparison changes the hypothesis and nothing else. That is the
conservative reading and it is affordable: pooling k members multiplies the t-statistic by
√k while doubling the look count moves the Bonferroni z by about 0.2. The optimistic reading
(correct across the 30 families only) is published beside it and moves nothing — every q is
1.0 either way.

Three disciplines are enforced by code rather than intention, and each closes a way this
could have been a laundering exercise:

1. **The family is the SYMBOL CLASS, never a result.** `family_members` builds the complete
   cross; a member leaves only for data, with the reason recorded in `FamilyGrid.dropped`.
2. **`pool_family` refuses mixed fidelity classes and mixed timeframes.** A pooled series
   wearing its best-attested member's stamp would be laundering; a day panel mixing one
   observation per day with six would be arithmetic nonsense.
3. **A surface-expanded member inherits its parent's structural CLASS rate, never the
   parent's own measurement.** `mx_nzdjpy_d1_donchian_20_breakout` is MEASURED_DIRECT at
   5/5 = 100 %; expanding its rule onto XAUUSD must not hand XAUUSD that number, because
   there is no live XAUUSD-donchian record for it to have agreed with. Every expanded row
   carries "THIS MEMBER HAS NO LIVE RECORD OF ITS OWN" in its stamp.

**Cost configuration, declared before the results were seen:** `mid` is the verdict band —
AG measured that the flat snapshot's bias has no consistent sign (EURUSD 2002 at 50×,
XAUUSD 2022 at 0.18×), so "charge the snapshot and note the caveat" is not available.
`snapshot` is reported beside it for comparability with every prior estate number;
`low`/`high` are the robustness envelope. §6 is what that decision then ran into.

---

## 3. The armed book: one number up, one hypothesis dead

### 3.1 `crypto` — the first positive out-of-window figure this sleeve has

`crypto.ON_SURFACE` is `("BTCUSD","DASHUSD")` (`crypto.py:24`). Its own rule, its own two
symbols, the whole archive, at mid band:

**+0.0869 R/day OOS · 60 % of folds positive · raw p 0.3001 · n=182 · 2017-02..2026-07.**

`CLAUDE.md` §4 records the armed four out of window at +0.100 %/month over ten years and
−0.220 % before 2020, and V's finding that the 5.46 %/month headline is measured on the
window that selected the sleeves. This is the sleeve-level version of that question for the
book's largest single edge, and the sign is right. It is not significant and it is not being
presented as such — n=182 over nine years is a thin sleeve, which is the whole reason
`FOURTH_REVIEW.md` §3.1 called it the book's real concentration.

### 3.2 The cluster claim is refuted, not unproven — and that is the more useful outcome

§3.1 of the plan asks for the crypto donchian family across the archive so that "the armed
book's largest single risk becomes a diversified cluster claim." Run:

| | pooled OOS R/day (mid) | raw p | dispersion ratio | members positive |
|---|---:|---:|---:|---:|
| production surface (BTC+DASH) | **+0.0869** | 0.3001 | — | — |
| the 9-symbol crypto class, same rule | **−0.1849** | 0.9413 | 4.735 | 5/9 |

Per-member gross R on the class: DASHUSD +0.883, ETHUSD +0.794, XTZUSD +0.555, BTCUSD
+0.481, AVAUSD +0.278, ADAUSD −0.106, DOTUSD −0.239, XRPUSD −0.604, LTCUSD −0.916. A
1.80 R spread between best and worst is not one mechanism read nine times.

Five of the nine members begin in late 2024 or 2025 — the archive's crypto-minor history is
short — so the family's early folds are 2–4 members wide and its last fold is 9. Per-fold
composition is published (`FAMILY_ADMISSION_V1.json` → `families.*.composition_by_fold`)
rather than averaged away, because a family whose composition changes is a different
portfolio in each fold and a reader is entitled to see it.

**Recommendation, and it is a recommendation not a decision:** do not price a crypto cluster
cap as diversification on this evidence. If the intent is to de-risk the concentration, the
lever this sweep supports is sample and conditioning on the two symbols that are already
armed, not more symbols.

### 3.3 `energy_agri` — the mechanism carries, the class is three symbols wide

The armed four's weakest statistical case (AA: q 0.33 at minimal carry). Its FVG-retest rule
on the energy class:

**+0.4571 R/day at mid band — the strongest pooled mean in the entire 30-family grid** —
with the tightest coherence measured anywhere here: dispersion ratio **0.117**, 3 of 3
members positive (NATGAS 0.941 / UKOIL 0.852 / USOIL 0.704 R/trade gross), band-stable
across all four cost configurations (0.417 / 0.468 / 0.457 / 0.440).

It fails on **sample**: 76 trades, one of five folds with zero trades, and `NATGAS_cash` has
no measured spread so the verdict runs on 2 of 3 symbols (85.5 % of trades). Breadth cannot
fix a three-symbol class. Two things would, both data and both named:

1. **a `NATGAS.cash` COMMISSION** — and this session's first draft got the blocker wrong,
   so it is worth being exact. Its **spread is already measured**: the 2026-07-29 tick
   export populated `spread_price.by_session` with real percentiles. `cost_r` refuses it on
   `commission.kind = "unknown"` — *"no deal rows for this symbol and no measured peer in
   its class; commission is UNKNOWN, not zero"* — which is F38 behaving correctly, not a
   gap. The fix is the same **cross-account transfer** AA's B603 used for FTMO oil, whose
   $5.00/lot is TRANSFERRED from redacted_account's MEASURED `USOUSD`/`UKOUSD`. redacted_account carries
   no gas instrument in the artifact's 76, so that particular transfer is not available
   today, and the honest options are one redacted_account gas deal row, one FTMO gas deal row, or
   a stated energy-class peer transfer that someone is willing to sign. **This is not a
   re-run of the cost artifact and it is not a tick capture** — both would leave the
   commission unknown. `HEATOIL.c`, the sleeve's other dropped energy leg, is in exactly the
   same state.
2. **`CORN.c` / `COTTON.c` bars** — this sleeve's own authored-but-untradeable legs (AA
   §3.2's naming finding), absent from the archive.

---

## 4. `mx_btcusd`: the prescription changes owner

AA routed it here as a `BREADTH` row and it was the right call to test. The test says
breadth is unavailable to it, and in the same run its own evidence got **stronger**:

**+0.3894 R/day OOS, 80 % of folds positive, raw p 0.0064 on n=232**, restricted to the eras
the spread model actually measured (`era_class == RECORDED` — an outcome-independent
restriction, §6). W's snapshot figure was +0.2446 at p 0.0120.

Its q is 1.0, and the reason is this session: 276 looks. **The sweep made the bill bigger.**
That is the ledger working exactly as designed and it is worth stating plainly, because the
consequence is that `mx_btcusd`'s admission is now a question about what the candidate
book's family IS rather than about the sleeve. At raw p 0.0064 it admits under BH α=0.20
against a family of ≤ 31 looks, or Bonferroni α=0.05 against ≤ 8.

`GateSpec.declared_family_size` is on the caller's honour and the package has no principled
stopping rule for it — the docstring says so. **That is an owner-decision item, not a
research one**, and it is the single thing standing between the estate's best new-edge
candidate and a verdict. Its exit/carry repair (AA: ADMIT at zero carry, q 0.048, swap 77 %
of cost over a 72 h median hold) remains with Session AD and is unaffected.

---

## 5. The three named mechanisms, answered

### 5.1 ATR mean reversion — all three questions the plan asks, all negative

`FOURTH_REVIEW.md` §3.3 refuses a verdict on the mechanism until three things are done. All
three are done.

**Over the other 40 symbols** (the plan's own words: "the mechanism was only ever tried on
the two worst plausible hosts"): crypto −0.335, energy −0.057, fx −0.469, index −0.084,
metal −0.299 R/day at mid. It does not live anywhere in the archive.

**The inverse** — continuation on the same trigger, **re-simulated** rather than sign-flipped,
because the contract is a 1R stop against a 2R target and negating stored R would answer a
question about a symmetric instrument that does not exist: crypto **+0.0436** (p 0.254),
metal −0.032, index −0.129, energy −0.271, fx −0.373. That is the only positive ATR-MR cell
in either direction across all ten, and at p 0.254 after ten looks it is a conditioning-map
entry.

**Vol-regime conditioning** using Session AB's published `PERSISTENCE` dial at AB's own
`revert` band (< −0.10) — the pre-declared home of mean reversion, not a fitted threshold:
crypto −0.204, fx −0.450, index −0.025, metal −0.151.

**Disposition: park with the list.** The list is
`AF_REPAIRS_V1.json` → `R3_regime_conditioning.conditional_map`: three dials × four buckets
for all 30 families, which is work-list item 7's deliverable and is the substrate for
anyone who wants to condition any of these mechanisms later.

### 5.2 The volume-surge family — the failure is stability, and it routes to AB

`volume_surge_reversal` × index × D1 is the best-behaved family in the grid on every
structural measure: 6 of 6 members positive, dispersion ratio 0.736, **all six firing in
every one of its five folds** (constant composition, unlike the crypto families), 85 % of
trades in RECORDED eras, and band-stable — 0.0968 / 0.1013 / 0.0999 / 0.0978.

It fails on **stability**: 40 % of OOS folds positive against a 50 % floor, fold means
[+0.394, −0.131, −0.018, −0.090, +0.346]. Two good folds at the ends is a regime shape, and
it routes to Session AB's spine rather than to more symbols. `mx_jp225` standalone is
+0.2071 R/day at mid, p 0.1126, 80 % of folds positive, band-stable — the second strongest
single member in the sweep.

**`mx_ger40`'s three-way split comes out differently from the plan's reading.** On the
regenerated stream it is **gross-POSITIVE**: +0.0909 R/trade over n=110, mean MFE 1.389 R,
55 % of trades reaching 1 R, capture ratio 0.072. So §3.3's `−0.0112/day` is a net number
and the sleeve's problem is cost geometry — not entry, and not the exit. Its whole cohort
shares the shape: JP225 +0.282 (capture 0.211), US30 +0.141, SPX500 +0.096, GER40 +0.091,
UK100 +0.037, NAS100 +0.034, every one keeping 4–21 % of its excursion. That is the same
picture AA measured on `metals_core` (reaches 1.76 R, keeps 0.114) on a different mechanism,
and it is Session AD's lane.

### 5.3 `mx_nzdjpy` — the break is dated, and it beats its own null

Splitting the trade series on the year axis, **2025** maximises |mean before − mean after| at
**0.785 R**: +0.1137 R/trade gross on n=466 before, **−0.6713** on n=37 after. Permutation
null over 2,000 shuffles of the same returns against the same year labels: **p 0.0005**.
2026 (−0.615) continues it. So this is not a 26-year decay — it is a two-year collapse, and
the conditioning variable the plan asks for has to explain 2025, not the 2000s.

The **pre-declared** variable does not: a breakout should want a persistent tape, which is
the gate the armed `crypto` sleeve already applies to its own donchian (`crypto.py:25`,
`AC_THR = 0.15` on `autocorr(B, i, 60)`), and `PERSISTENCE == trend` gives −0.1953, p 0.9011.
The post-hoc best bucket is `VOL_REGIME == hi` (+0.2684, p 0.1005, n=81) — mechanically
sensible for a breakout, offered to AB as a conditioning-map entry and **not** as a
significance claim.

### 5.4 `mx_cadjpy` — the named repair is real and its size is not yet known

Reproduced at **−0.0017 R/day** flat (the prompt's "closest in the whole map") and **−0.2910**
charged its own eras, independently of AG's driver, which read −0.0024 → −0.3252. Two
instruments, different code paths, same answer.

AG's named repair — the FX family paying 13×–38× at broker hour 00 — is real and it is the
dominant term. A D1 bar closes at broker 00:00 and this whole family enters at that close,
so every fill lands on the worst hour of the week **by construction**. Re-pricing the same
trades two hours later removes **80–81 %** of modelled cost on the three FX D1 families and
**~0.000 R** on every other class — exactly the signature AG predicted, since fourteen
instruments do not quote at the rollover at all.

**But that ceiling is not the gain**, because §6. What is measurable next, with data already
on this machine: the archive holds H4 bars for every FX symbol, so entering at the first H4
close after the D1 decision (broker 04:00) can be simulated end to end — moving the entry
*price* and therefore R, not only the spread charge. One session's work, and it is the
largest single unpriced lever this sweep found.

---

## 6. The defect I found by suspecting my own probe

R4 came back with the FX D1 families paying **0.46–0.50 R of total cost per trade**, 80 % of
it spread, and a **+0.40 R** saving from a two-hour entry shift. A spread charge of half the
risk unit is not a market. The working agreement's rule is to suspect the probe, and it does
not survive.

`spread_model_v1` composes `anchor × era_ratio × hour_of_week` multiplicatively. Measured:

| | era_ratio | hour_mult | product | `spread_r` charged |
|---|---:|---:|---:|---:|
| NZDUSD, 2000s | 13.7 | 14.4 | **198×** | **1.78** (178 % of the stop) |
| EURUSD, 2000s | 32.6 | 14.7 | 479× | 0.46 |
| EURUSD, 2020s | 4.5 | 12.7 | 57× | 0.085 |

Across the three FX D1 families the mean multiple is **71–79×** and the maximum **880×**,
with only **44 %** of their trades in `RECORDED` eras.

Each factor was validated **alone** — AG on H4 block pairs, which are all-hours medians
(skill 0.33–0.58), and on the 37-day tick window, where `era_ratio` is 1 by construction.
AG's own §10 item 1 already says the pre-2010 FX eras are `SCHEDULE`-class and
unvalidatable. What is new is that nobody had named **the product of two unvalidated
multipliers** as its own risk, and it is larger than either.

Non-FX classes are unaffected: mean multiple 0.44–0.75, which R4 reproduces independently as
a ~0.000 R hour saving on metals, indices, energy and crypto.

**Interim treatment, used here and available to everyone**: restrict to `era_class ==
RECORDED`. That is outcome-independent for exactly the reason
`GateSpec.coverage_policy="restrict_to_priced"` is — it is a property of the broker's bar
data, not of returns. Under it the FX families stay deeply negative (−0.28 to −0.36), so the
defect **inflated the magnitude and did not create the sign**; the crypto donchian family
improves from p 0.444 to p 0.083; `mx_btcusd` improves from p 0.0145 to p 0.0064.

**Routed to Session AG's lane. Not repaired here** — the fix is a validation question about
the model's composition, and inventing one under time pressure inside a session that needs
the answer is how a model gets fitted to its customer.

---

## 7. Every family leaves with a prescription, and 23 leave with the same one

36 rows appended to the shared queue (`phase6/receipts/REPAIR_QUEUE_V1.json`, session `AF`,
now 123 rows total), plus the complete 276-sleeve diagnosed queue at
`phase7/receipts/AF_REPAIR_QUEUE_FULL.json.gz`.

| prescription | n | what it means |
|---|---:|---|
| `MEMBER_CONDITIONING_NOT_BREADTH` | 23 | dispersion ratio > 1 — the members are a mixture. **Do not ask for more symbols.** Ask which member carries the edge and why. |
| `PARK_WITH_LIST` | 5 | negative on the whole class at every band; the list is the conditional map |
| `SAMPLE_OR_STABILITY` | 2 | members coherent, pooling is the right instrument, what is missing is evidence |
| `BREADTH_REFUTED_ADMIT_ON_OWN_EVIDENCE` | 1 | `mx_btcusd` — §4 |
| `OUT_OF_WINDOW_POSITIVE_NEEDS_SAMPLE` | 1 | `crypto` — §3.1 |
| `DATA_CAPTURE_NATGAS_AND_AGRI` | 1 | `energy_agri` — §3.3 |
| `REGIME_GATE` | 1 | `mx_nzdjpy` — §5.3 |
| `COST_GEOMETRY_ENTRY_HOUR` | 1 | `mx_cadjpy` and the FX cohort — §5.4 |
| `ERA_MODEL_PRODUCT_UNVALIDATED` | 1 | §6, to AG |

**A scope cap, stated because the agreement forbids silent ones.** The 23-row majority is
the session's own answer to itself: the breadth question was asked 30 times and 23 of the
answers are "this was the wrong question for this family." Cheaper next time — one query.

**What was skipped, and why.** `volume_surge_reversal` and `atr_mean_reversion` were swept at
their authored D1 timeframe only, not also at H4; `donchian_20_breakout` was swept at both
because the armed `crypto` sleeve is the same mechanism on H4 and the prompt asks the crypto
family at both. Those 86 unrun cells would have been 86 fresh hypotheses on every symbol at
once, bought nothing on the work list, and would have raised the bill every other row pays.
Recorded in `AF_FAMILY_TRADES.json.gz` → `sweep`.
`mx_aus200_volume_surge` and `mx_spn35_volume_surge` remain unjudged: their spreads are now
measured but **their bars are still absent** (§9 ceremony pending), so they are exactly where
the prompt predicted — a data row, not a verdict. Same for `mx_eu50` and `mx_fra40`.

---

## 8. What I got wrong, and what in the plan I am correcting

**Mine, three.**

1. **The first driver was a strict superset of the estate's own.** +11 % on `mx_nzdjpy`, and
   I could have shipped it as "more coverage." It was the pre-gap bar (§1.1), the engine
   cannot reach those bars, and every downstream number would have been about a program the
   live book is not.
2. **My own regime-gate selection rule excluded the mechanistically right bucket by six
   trades.** R5's first revision picked the best dial bucket under an `n >= 100` floor,
   which dropped `PERSISTENCE == trend` at n=94 in favour of one six trades larger and 0.08 R
   worse — and `trend` is the bucket a breakout should want and the one `crypto.py:25`
   already gates on. Both gates are now published side by side with their selection basis
   stamped `pre_declared` / `post_hoc_best`.
3. **I nearly reported a +0.40 R repair.** §6. It was 80 % of a cost that is itself an
   unvalidated extrapolation.
4. **The first draft of this document's own headline rule was false**, and an adversarial
   pass over my own claims caught it after the first commit. I wrote that "the two families
   whose dispersion ratio is below 1 are exactly the two with the best p-values." **Seven**
   are below 1. The ratio is `sd/|mean|` and is sign-blind, so a family agreeing on being
   uniformly bad scores as tight as one agreeing on being good —
   `atr_mean_reversion` × metal is 0.610 with 0 of 9 members positive. The corrected rule is
   two-part (§0) and only then does it pick out exactly two of thirty. The repair-queue
   logic was never wrong — it already routed on the mean's sign as well — so no row moved;
   what was wrong was the sentence a reader would have carried away, which is the part that
   would have cost the next session a session.

5. **I got `energy_agri`'s data prescription wrong on the first pass** and caught it by
   checking the refusal instead of quoting it. I wrote "a measured NATGAS.cash spread — a
   re-run, not a capture." Its spread IS measured; `cost_r` refuses on an unknown
   **commission**, which no re-run and no tick capture would supply. Corrected in §3.3 —
   and the corrected version is a smaller, sharper ask.

**In the plan and the prompt, three.**

1. **"43 archive symbols"** (`FOURTH_REVIEW.md` §5.4, and this session's prompt) is **41
   instruments.** §1.3.
2. **`mx_ger40`'s `−0.0112/day` is a net number and the sleeve is gross-positive.** §5.2.
   §3.3's three-way question resolves to cost geometry, not to the exit and not to the
   inverse.
3. **The prompt's framing — "mx_btcusd fails only a 69-look family bill" — is right about
   the diagnosis and wrong about the cure.** The bill is not what breadth fixes here,
   because the class is a mixture. §4.

---

## 9. Scoped verification

**Blast radius.** Two production files changed, both in the walkforward package and both
verified unbound by the R2 decision contract before editing (H1 check re-run at session
start; the only two "drifted" paths are the known un-hydrated LFS pointers):

* `src/research_infra/walkforward/family.py` — new
* `src/research_infra/walkforward/fidelity.py` — additive: `register_surface_expansion`,
  `clear_surface_expansions`, `surface_expansions`, `EXPANSION_PREFIXES`, and one line in
  `fidelity_for` that consults the expansion table after the authored register

**Scope run at HEAD** — the new tests, plus every test importing the modules touched:

```
$ python3 -m pytest tests/research_infra/test_walkforward_family.py \
    tests/research_infra/test_fidelity_register_matches_receipt.py \
    tests/research_infra/test_walkforward_gate.py \
    tests/research_infra/test_wf_diagnostics.py \
    tests/research_infra/test_wf_exits_parity.py \
    tests/research_infra/test_walkforward_diversifier.py \
    tests/research_infra/test_wf_registry_surface_reconciliation.py \
    tests/research_infra/test_walkforward_book_replay.py \
    tests/research_infra/test_learned_edge_walkforward_gate.py -q
```

Receipt in §9.1. No production rule was modified: `market_expansion_d1.TAG_TO_RULE`,
`crypto.ON_SURFACE` and `energy_agri.ON_SURFACE` are widened inside a context manager and
restored on exit including on exception, and two tests assert they come back byte-identical.
A third asserts the widened generator reproduces the production tag bar for bar on the
authored cell — the property that makes the whole sweep about the same program.

**Not run:** the full suite. `WAVE_7_WORKING_AGREEMENT.md` §2 retires it, and Session AT is
re-shaping the suite under this branch.

### 9.1 Receipt

```
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [100%]
171 passed, 1 warning in 6.93s
```

Green, so no base comparison was needed — §2 item 2 asks for a base run only to explain a
failure, and there is none. Nine files, 171 tests, 14 of them new.

**Two invariants re-checked after every driver had run, because both would be silent:**

```
$ python3 -c "from src.components.ultimate_book.sleeves import crypto, energy_agri, \
    market_expansion_d1 as mx; print(crypto.ON_SURFACE, energy_agri.ON_SURFACE, \
    len(mx.TAG_TO_RULE))"
('BTCUSD', 'DASHUSD') ('USOIL_cash', 'UKOIL_cash') 14
```

and the H1 contract check, which reports the same **2 un-hydrated LFS pointers** it reported
at session start and nothing else — `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`
and `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`, the pair `CLAUDE.md` §3 names. No bound path
drifted.

Diff against the merge-base under `src/` and `tests/`: **3 files, +937/−1**, one of which is
the new test file.

**One environment note that cost an hour and will cost the next session one too.**
`research/operations/spread_model_2026_07_29/` is outside this worktree's sparse-checkout
cone, so `load_spread_model()` raises `SpreadModelError` and every `spread_band=` verdict
silently becomes unavailable. `git sparse-checkout add research/operations/spread_model_2026_07_29`
hydrates it. This is §4's "sparse-checkout lies" in its exact predicted shape.

---

## 10. Artifacts

| path | what |
|---|---|
| `src/research_infra/walkforward/family.py` | mechanisms detached from symbols; the grid; pooling; the two context managers |
| `src/research_infra/walkforward/fidelity.py` | `register_surface_expansion` and its three guards |
| `tests/research_infra/test_walkforward_family.py` | 14 behavioural tests |
| `phase7/receipts/af_family_generate.py` | the sweep, `engine_reachable`, the parity check |
| `phase7/receipts/af_family_gate.py` | 26 gate runs, member and family, banded |
| `phase7/receipts/af_repairs.py` | R1–R8, the named repairs |
| `phase7/receipts/af_repair_rows.py` | queue rows, idempotent append |
| `phase7/receipts/AF_FAMILY_TRADES.json.gz` | 134,027 trades with path, regime-labellable, reachability-flagged |
| `phase7/receipts/FAMILY_ADMISSION_V1.json` | **deliverable 1** — per family: members, verdict, banded sensitivity, standalone-vs-family, fold composition |
| `phase7/receipts/AF_REPAIRS_V1.json` | R1–R8 with the conditional map for all 30 families |
| `phase7/receipts/AF_REPAIR_QUEUE_FULL.json.gz` | all 276 diagnosed sleeves |
| `phase7/receipts/REPAIR_QUEUE_AF.json` | the 36 rows also appended to the shared queue |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | +778 rows (359 distinct variants); 2,421 total |

---

## 11. Routing

**Borhen — one decision, and it is the only thing standing between the estate's best new-edge
candidate and a verdict.** `mx_btcusd` posts raw p 0.0064 and q 1.0. The q is a function of
`declared_family_size`, which the gate leaves on the caller's honour with no principled
stopping rule. **What is the family a candidate-book admission is corrected against?** Every
hypothesis the campaign ever evaluated (2,421 ledger rows), this session's grid (276), the
candidate book you would actually choose from (~12–30), or the sleeve alone? At ≤ 31 looks it
admits under BH α=0.20; at ≤ 8 under Bonferroni α=0.05. This is the same class of decision as
the risk dial and it is not a session's to make.

**Also Borhen — one small item, and it is not the one I first wrote.** `NATGAS.cash`'s
spread is already measured; what blocks it is an UNKNOWN commission with no peer to transfer
from (redacted_account carries no gas instrument). Closing it needs a deal row on either account
or a signed energy-class peer transfer — a decision, not a capture. It would close
`energy_agri`'s partial universe on the sleeve whose mechanism is the strongest thing in
this grid.

**Session AG** — §6. The era × hour product, and whether the composition is separable.

**Session AB** — three regime rows: the index volume-surge family's two-good-folds shape
(§5.2), `mx_nzdjpy`'s dated 2025 break with its permutation null (§5.3), and the full
conditional map (three dials × four buckets × 30 families) as substrate.

**Session AD** — the index volume-surge cohort keeps 4–21 % of a 1.2–1.5 R excursion across
all six members (§5.2), which is the `metals_core` shape on a different mechanism. And
`mx_btcusd`'s carry repair is unchanged and unaffected by anything here.

**Wave 8** — the H4 re-entry test (§5.4) is the largest unpriced lever this sweep found, and
it needs no new data. The diversifier door has one fewer customer than the plan expected:
per-symbol allocation inside an admitted family presumes an admitted family, and there is
none.
