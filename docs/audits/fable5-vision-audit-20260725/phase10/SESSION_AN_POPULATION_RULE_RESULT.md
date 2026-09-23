# Session AN — the population rule: wired, sealed, and priced on every axis; and the estate's one admission survives only on one of them

**Wave 10. Branch `phase10/population-rule`, from `main` at `8db17b29c`. Blocks B1250–B1268. Not merged.**

**Scoped verification (agreement §2): see §9.** Receipt: `phase10/SESSION_AN_AB.md`.

---

## 0. Headline

The commission asked for four things in dependency order. All four are delivered, and the third
and fourth both came back different from what the brief expected.

> **Across 240 gated arms — 3 candidate cells × 5 populations × 4 bands × 2 options × 2 exit
> configurations — exactly 9 ADMIT, and all nine are `mx_btcusd_d1_donchian_20_breakout` on
> `RECORDED`.** Zero admissions exist on `ALL_ERAS`, on `DECIDABLE`, on
> `RECORDED_AND_DECIDABLE` or on the disputed-trade diagnostic, at any band, under either
> standard. **The population rule is the only thing standing between this estate and no admitted
> candidate**, which is what makes it a decision rather than a detail.

**1. The coverage hole is closed, and it was 182 eras rather than one quarter.** An undecidable
**RECORDED** era degraded nothing: `BTCUSD 2020Q1` priced as `coverage=MEASURED` on a band its own
artifact calls a 204,058× capture requirement. **182 of the model's 275 undecidable eras are
RECORDED** (66.2 %). `not decidable` now degrades on every path — 192 of 2,653 era cells change
class, monotonically weaker, five behavioural tests each verified RED against the pre-repair logic.

**2. `require_decidable` is a GateSpec axis and the population rule is in the seal.** AL
reimplemented the restriction three times in one session, each time *before* `run_gate`, so two
runs on two different populations produced the same `spec_sha256`. Now: `spread_require_decidable`
threaded spec → `price_trades` → `cost_r` → `spread_price`, seal-honest on `spread_composition`'s
rule (None ≡ False ≡ the pre-field seal; only True moves it), plus `era_population.py` — four named
rules, the argument for each, the rule stamped into `spec_id`. **Zero seal collisions across 240
arms.** Nobody reimplements it again.

**3. The coverage repair moves ZERO verdicts, and the commission's stated reason why it might is
not the mechanism.** Item 5 says *"it can — coverage degradation feeds `restrict_to_priced`"*.
It does not: `coverage_frac` counts **refusals**, not classes, and **no code reads a coverage class
into a verdict anywhere** — `require_measured_cost_frac` is declared and read by nothing in `src/`.
The repair is a truthfulness repair, and its value is measured where a verdict cannot see it: **1,584
trade-level coverage classes corrected, including 78 of `mx_btcusd`'s 232 RECORDED trades (33.6 %)
that were claiming a measured spread they did not have.**

**4. AM's band-widened era table should be adopted, and my own "correction" to AM's figures was the
error.** 0 verdicts moved over 54 arms; the mid band is byte-identical; BTCUSD carries 0 widened
eras so the admission cannot move. **All four of AM's published claims reproduce exactly.** My
reader counted the provenance stamp (585 eras) instead of the movement (536); 49 of the 585 carry a
delta of exactly zero and 536 × 0.166247 / 585 = 0.152322, which is precisely the "corrected" mean
I published. Withdrawn.

**And one thing the commission did not ask for, which is the session's own finding — with its
verdict claim refuted by my own placebo.**

> **`decidable` is a threshold on the spread's own LOG width and an admission is a claim in R, so
> its LEVEL is uncalibrated across sleeves.** `sub_mid_dn_revert`'s *accepted* trades carry a median
> charged cost range of **0.0232 R** while `mx_btcusd`'s *rejected* trades carry **0.0122 R** — the
> same flag tolerates 1.9× more cost uncertainty on one sleeve than it refuses on another. The
> scale-correct instrument (`|total_r(high) − total_r(low)| ≤ τ`, entry-knowable to 2.2e-16) ADMITs
> at every τ in [0.02, 0.50] with a plateau from 0.05, at p 0.0008 against RECORDED's 0.0011.
>
> **Then the placebo killed the improvement.** The 20 trades it drops average −0.10 R against the
> kept +1.13 R and all 20 sit in 2018 and 2020; a year-matched random 20-trade removal reaches
> p ≤ 0.0008 in **10 of 40 draws** (placebo p **0.268**). Outcome-independent in assignment, not
> outcome-neutral — AL §3.3's distinction, applied to a rule I was proposing. **The structural
> finding stands; the verdict claim is withdrawn**, and the rule is routed as a repair rather than
> offered as the rule. What the attack gave back is worth having: **38 of 40 year-matched draws
> still ADMIT**, so the admission does not depend on which 20 of those trades are present.

**Recommendation to Borhen: ratify `RECORDED`**, with the band stamp mandatory and `target_5R` as
the cell. One page at `phase10/POPULATION_RULE_DECISION.md`. The reasoning is in §5.

**Seven of nine refuters came back refuted and six of the seven corrected a number I was about to
publish.** §8 owns all of them; two changed a headline. Nothing was armed, `config/agent_config.yaml`
was neither read for a live decision nor written, no broker-capable script ran, the VPS was never
contacted.

---

## 1. Item 1 — the coverage hole [B1250]

`spread_model.py`'s coverage branch was an `if fb is not None and … not decidable` / `elif
era_class not in ("RECORDED", "NO_BAR_HISTORY")` pair, so the decidability arm was reachable **only
through the no-bar-history fallback**. On the ordinary era path an undecidable RECORDED era matched
neither branch and inherited the anchor's class.

Measured by calling the model, before and after:

| era | class | decidable | coverage before | coverage after |
|---|---|---|---|---|
| BTCUSD 2020Q1 (band spans 204,058×) | RECORDED | **False** | **MEASURED** | MODELLED |
| BTCUSD 2018Q3 | RECORDED | **False** | **MEASURED** | MODELLED |
| BTCUSD 2021Q3 | SCHEDULE | True | MODELLED | MODELLED |
| BTCUSD 2022Q1 | QUANTIZED | True | TRANSFERRED | TRANSFERRED |

**It is not one quarter.** Over the whole model:

| | count |
|---|---:|
| undecidable eras | **275** |
| — of which `RECORDED` | **182** (66.2 %; FTMO 134/195, redacted_account 48/80) |
| — `FLOORED` | 64 (already MODELLED via the class branch) |
| — `QUANTIZED` | 29 |
| era cells whose coverage CLASS changes | **192** (7.2 %) |
| — RECORDED, MEASURED anchor: MEASURED → MODELLED | 166 |
| — QUANTIZED, MEASURED anchor: TRANSFERRED → MODELLED | 26 |
| — already MODELLED (anchor was MODELLED) | 19 |

**192, not 211** — a first draft of the source comment counted every era the new branch fires on
rather than every era whose class moves, and 19 of them already sat at MODELLED because their anchor
did. Counting the trigger is not counting the effect; the same mistake recurs in §4 and §8.1.

Monotone by construction: `weakest()` is `max` by strength and MODELLED is weakest, so the repair
can only weaken. Pinned over every era in the model, and a refuter independently confirmed it over
21,287 paired estimate calls including the fallback path and 2,636 gap>8 cells, with **0** cells
strengthened and **0** cost values changed.

**Five behavioural tests, each verified RED against the pre-repair logic by copy-back** (never `git
checkout` — AL §9's lesson) and GREEN after. They pin the general rule and not the anecdote: no
undecidable era anywhere reports MEASURED (≥ 200 checked, ≥ 100 of them RECORDED), monotonicity over
every era, and the degradation reaching `cost_r`'s consumer.

---

## 2. Item 2 — the wiring, and the seal [B1251–B1253]

### 2.1 The axis

`SpreadModel.estimate` has taken `require_decidable=` since Session AG shipped it and **no
production path passed it** — its only call sites anywhere were `test_spread_model.py:193` and
`:374`. `GateSpec.spread_require_decidable` now threads spec → `panel.price_trades` → `cost_r` →
`spread_price`.

**The seal-honesty rule is `spread_composition`'s, not `_ABSENT_MEANS_UNCHANGED`'s, and the
difference is the point.** Dropping-at-None would be wrong here for the opposite reason it is right
there: None and False are the *same behaviour*, so a spec that says False must hash like one that
says nothing, or one methodology seals two ways. Verified:

| | `B_balanced` seal |
|---|---|
| pre-field `spec.py` loaded from `8db17b29c` | `6de55ed5e74b…` |
| HEAD, `spread_require_decidable=None` | `6de55ed5e74b…` |
| HEAD, `=False` | `6de55ed5e74b…` |
| HEAD, `=True` | `ec83fa483b4f…` |

A refuter reproduced this for all three options and `DEFAULT_SPEC`, and re-derived **all 18**
published `spec_sha256` in the restored cohort at HEAD — 18/18, zero mismatches.

### 2.2 `era_population.py` — the rule, named once

Four candidate rules plus one diagnostic, each carrying the argument for it, expressed as
`(trade predicate, spec mutation)`. Two properties the estate did not have:

- **The rule is in the seal.** `spec_for` stamps `|pop=<RULE>` into `spec_id`, which `canonical()`
  hashes. For all of wave 9 the four populations produced **one** `spec_sha256`; they now produce
  five distinct ones, and the grid records **zero collisions across 240 arms**.
- **The filter and the flag are deliberately redundant** on the decidable-family rules, so a
  divergence between a driver's predicate and the model's own field surfaces as a refusal count
  rather than as a silent difference. §3.3 states honestly where that control is armed and where it
  is a tautology.

**A design choice reversed mid-session.** The first version dropped trades the model cannot
classify. That launders a coverage shortfall into a smaller population: `coverage_frac` reads 1.0,
`restrict_to_priced` has nothing to stamp, and `A_strict`'s refusal never fires. They are kept now
and the gate owns that accounting. Inert on these cells (0 unclassifiable trades everywhere), so
the choice was made on the principle because the measurement could not make it.

### 2.3 A hole the adversarial pass found in the seal *tests* [B1253]

`test_candidate_family.py` pins the BROKEN seal cohort by exact prefix and the RESTORED cohort by
`assert len(seals) >= n` — a **count**. A refuter replaced all 18 restored seals with fabricated
hashes in a temp copy of the five artifacts and the test **still passed**. Exactly 3 of the 18 are
pinned by value. `tests/research_infra/test_published_seals_pinned_by_value.py` pins all 18 by
value (7 tests), including a control that the substitution it exists to catch would be caught.

---

## 3. Items 4–5 — the decision grid [B1254–B1259]

### 3.1 The table that is the decision

`mid` band, declared family 35 (`CANDIDATE_FAMILY_V2`, all-declared basis), broker-true cost. `q` is
comparable only inside this table.

| population | n | R/day | p_raw | q | verdict | fold means (5) | retention |
|---|---:|---:|---:|---:|---|---|---:|
| ALL_ERAS | 318 | 0.547 | 0.0106 | 0.185 | REJECT | 1 of 5 negative | 0.712 |
| **RECORDED** | 232 | **0.982** | **0.0011** | **0.0385** | **ADMIT** | **0 negative** | 0.775 |
| DECIDABLE | 240 | 0.513 | 0.0581 | 1.0 | REJECT | 3 negative | **0.194** |
| RECORDED_AND_DECIDABLE | 154 | 0.892 | 0.0158 | 0.516 | REJECT | 2 negative | 0.639 |
| RECORDED_UNDECIDABLE (diag.) | 78 | 0.914 | 0.0392 | 1.0 | REJECT | 1 of 3 negative | 0.296 |

Distance from the BH rank-1 bar (0.10/35 = 0.0028571), `target_5R` at mid: RECORDED **0.38×** (i.e.
inside it), ALL_ERAS 3.71×, RECORDED_AND_DECIDABLE 5.53×, DECIDABLE **20.33×**.

**Every ADMIT in the whole grid, all nine:**

| config | option | population | band | p_raw | q | R/day |
|---|---|---|---|---:|---:|---:|
| `target_5R` | B_balanced | RECORDED | flat | 0.001000 | 0.0350 | 0.9891 |
| `target_5R` | B_balanced | RECORDED | low | 0.001100 | 0.0385 | 0.9833 |
| `target_5R` | B_balanced | RECORDED | mid | 0.001100 | 0.0385 | 0.9817 |
| `target_5R` | **A_strict** | RECORDED | flat / low / mid | same p | 0.0350 / 0.0385 | — |
| `target_4R` | B_balanced | RECORDED | flat / low / mid | 0.0022 / 0.0023 / 0.0023 | 0.0770 / 0.0805 | 0.7694 |

`target_4R` clears BH's 0.002857 and fails Bonferroni's 0.001429, so **only `target_5R` survives an
option change.** Verdict counts by population, over all 48 arms each: ALL_ERAS 0 ADMIT / 40 REJECT /
8 NOT_EVALUABLE; RECORDED **9** / 31 / 8; DECIDABLE 0 / 32 / 16; RECORDED_AND_DECIDABLE 0 / 32 / 16.

### 3.2 The armed sleeve, and `sub_mid_dn_revert`

`sub_xvol_pullback @ target_4R` (trading real money on FTMO today): REJECT on ALL_ERAS (p 0.0077)
and RECORDED (p 0.0080, 2.80× the bar), **NOT_EVALUABLE on both decidability populations** (n 56 /
53) under `B_balanced`, and **NOT_EVALUABLE on all four populations** under `A_strict`. AL's third
measurement of AI §2.5c reproduces on every population; it is a coverage fact an arming discussion
has to carry, not an argument for disarming.

`sub_mid_dn_revert` (AM's re-clocked 533) is REJECT everywhere; §4.2 is its finding.

### 3.3 What the redundancy control actually proves [B1258]

`coverage_frac` is 1.0 and `decidability_refusals` is 0 on **all 240** arms. A refuter measured that
this is not a check passing 240 times:

| | arms | why |
|---|---:|---|
| **armed** — flag on, era path entered | **72** | DECIDABLE + RECORDED_AND_DECIDABLE at low/mid/high. All 72 pass. |
| inert — flag off | 144 | every ALL_ERAS / RECORDED / RECORDED_UNDECIDABLE arm |
| inert — flag on, flat band | 24 | `cost_r` enters the era path only when `spread_band is not None` |

**And it is armed on 0 of the 9 ADMIT arms**, because all nine are RECORDED and RECORDED does not set
the flag. The sharpest case is in the grid: the 48 RECORDED_UNDECIDABLE arms are 100 % undecidable
trades by construction and still stamp `coverage_frac` 1.0. Positive control, run: the same
population with the flag on at mid gives 9 of 9 unpriced and 9 refusals. Quote the armed
denominator, never the total.

### 3.4 The B1250 delta, and why the repair is invisible to a verdict [B1254–B1255]

48 arm-cells, A/B'd with the pre-repair rule restored **in-process** (no source reverted):
**0 verdict fields moved, 0 sleeve-level coverage stamp fields moved.** Three mechanisms:

1. `coverage_frac = n_priced / n_evaluable` and a trade is priced iff `cost_r` did not raise. A
   class change cannot move it — so the commission's *"coverage degradation feeds
   `restrict_to_priced`"* is not the mechanism.
2. **No code reads a coverage class into a verdict at all.** `require_measured_cost_frac` is
   declared at `spec.py:354` and read by nothing in `src/`. (A refuter found this; my own version
   said "it is 0.0 in all three options", which is true and beside the point.)
3. The stamps held for **three different reasons**, and calling all of them saturation was wrong for
   32 of the 48 cells — see §8.5.

Where the repair IS visible, per trade, at mid:

| cell | population | n | before | after | classes changed |
|---|---|---:|---|---|---:|
| `mx_btcusd` | RECORDED | 232 | MEASURED 216 / MODELLED 16 | MEASURED 138 / MODELLED 94 | **78 (33.6 %)** |
| `sub_xvol_pullback` | RECORDED | 85 | MEASURED 74 / MODELLED 11 | MEASURED 48 / MODELLED 37 | 26 (30.6 %) |
| `sub_mid_dn_revert` | RECORDED | 325 | MEASURED 319 / MODELLED 6 | MEASURED 292 / MODELLED 33 | 27 (8.3 %) |

**1,584 trade-level classes corrected across the census.** A third of the admitting population was
claiming a measured spread it did not have, and no field a verdict carries could see it — which is a
stronger argument for the repair than a moved verdict would have been.

### 3.5 The band, and the 78 disputed trades [B1259]

RECORDED admits at flat/low/mid and **REJECTS at `band_high`** (p 0.005099 — inside the BH rank-**2**
threshold 0.005714, so the pair structure returns there). The band sensitivity is **entirely** in the
78:

| population | net R/trade @ low | @ mid | @ high | change low→high | mean gross R/trade |
|---|---:|---:|---:|---:|---:|
| disputed 78 (RECORDED ∧ ¬decidable) | +0.7816 | +0.7756 | **+0.5272** | **−32.5 %** | +1.0196 |
| clean 154 (RECORDED ∧ decidable) | +0.7927 | +0.7907 | +0.7883 | −0.6 % | +1.0263 |

Two readings, and both belong in the decision. The 78 are **not economically a different
population** — their gross is indistinguishable from the clean 154's — and **the 204,058× band is a
band on a quantity that is 0.9 % of a crypto risk unit**: mean spread 0.0092 R at mid, 0.2576 R at
the 717× high end. Charged at its worst the disputed evidence still pays. *Caveat kept:* 13 of the
78 are charged more than a full risk unit at `band_high` (max 2.3461 R), so the +0.5272 mean averages
over cells the pessimistic band prices out of existence.

### 3.6 The admission decays chronologically, and no gate can see it [B1268]

A completeness critic found that everything above prices the admission **pooled**, and that the two
questions an owner asks about a candidate — is the edge recent, and is it concentrated where the
evidence is weakest — are answerable from the arm's own folds and were unpublished. Both are now
measured. `fold_rule="equal_calendar_folds_over_sleeve_span"`, so folds are equal calendar blocks in
time order:

| fold | OOS window | n | gross R/trade | fold R/day | disputed share |
|---|---|---:|---:|---:|---:|
| 1 | 2019-01-03 … 2020-05-07 | 36 | 1.3333 | +1.1341 | 41.7 % |
| 2 | 2020-05-08 … 2021-09-11 | 42 | 1.8046 | +1.5118 | **90.5 %** |
| 3 | 2021-09-12 … 2023-01-16 | 26 | 2.1458 | **+1.8663** | 0 % |
| 4 | 2023-01-17 … 2024-05-21 | 30 | 0.6000 | +0.2838 | 0 % |
| 5 | 2024-05-22 … 2025-09-25 | 50 | 0.4400 | +0.1124 | 24.0 % |

**The last two folds average +0.1981 R/day against the first three's +1.5041 — 13.2 %, on 80 of 232
trades (34.5 %) and the most recent 2.7 years.** Every gate passes: `stability` counts the **sign**
of a fold mean, so `min_oos_positive_fold_frac` reads 5/5 and a 7.6× decay is invisible by
construction.

And it makes the population difference mechanical rather than statistical: **53 of the 78 disputed
trades sit in folds 1–2**, fold 2 is 90.5 % disputed and carries the second-highest fold mean, and
folds 3–4 contain none. Dropping the 78 removes most of two early folds and takes fold positivity
5/5 → 3/5 — which is what moves p 0.0011 → 0.0158. §3.5's pooled statement is true and cannot carry
that. **Neither fact changes which population admits; both belong in front of Borhen**, and the
decision doc carries them above its recommendation rather than below it.

### 3.7 The three parity controls [B1257]

| | question | result |
|---|---|---|
| **C1** | does `era_population` reproduce AL's published populations? | **IDENTICAL on all 9** — 318/232/240/154/78 and 88/85/56/53 |
| **C2** | does `p_raw` reproduce AL's on every shared arm? | **Δ exactly 0.0** on all five, not merely < 1e-9 |
| **C3** | do the populations seal separately? | **0 collisions** over 240 arms, 5 distinct seals per context |

Two honest qualifications the pass added. The xvol half of C1 compares against **typed literals**
(`AL_POPULATION_INTERSECTION_V1.json` is BTC-only; those counts live in
`AL_CANDIDATE_DOSSIER_V1.json`) — verified by hand, and weaker than a control against an artifact.
And the C2 note claiming *"the same `p_raw` gets a different `q` by construction"* is **falsified by
its own five rows**: `q` is identical to AL's on all five to full precision. The R0 rule is that `q`
*need not* travel, not that it cannot.

---

## 4. Item 3 — AM's band-widened era table, and a correction to a correction

### 4.1 The recommendation: ADOPT [B1260]

54 arms, two configs × three populations × three bands, both models. **0 verdicts moved.** 4 of 54
arms moved any number, all `sub_mid_dn_revert @ ALL_ERAS`:

| arm | p of record → widened | R/day of record → widened |
|---|---|---|
| `ALL_ERAS` @ low | 0.242876 → **0.218378** | +0.07319 → **+0.08164** |
| `ALL_ERAS` @ high | 0.533447 → **0.579742** | −0.01077 → **−0.02357** |

Better at `low`, worse at `high` — which is exactly what widening a band should do. `mx_btcusd`'s
admission **cannot** move: **BTCUSD carries 0 widened eras**, six of nine cryptos leaving the
defect's scope by AM's own §4.1 (their reference window is itself a nominal constant). Only 14 FTMO
symbols are widened at all. Cost of adoption ≈ 0, and it replaces an unvalidated level shift with an
honest band.

**One condition:** the widest actually-widened half-width is **0.404800** against the 0.5
decidability threshold — **0.0952 log** of headroom, flip multiplier **1.235×**. A hypothesis that
much larger starts flipping SCHEDULE eras to undecidable, which **since B1250 degrades Coverage**
where before it would not have. That coupling is the one thing a future re-sizing of AH §6 must
check.

**AM's published figures need no correction, and mine did.** §8.1.

### 4.2 `sub_mid_dn_revert` — the level is flat-only, the repair is not [B1261]

The grid carried only the re-clocked arm, so it measured the sleeve's absolute p per band and never
the clock **delta**. On that evidence my first draft wrote *"the re-clock improvement is a
flat-snapshot artefact"* — a claim about a delta supported only by levels. Measuring the missing arm
inverts it:

| band | p authored → re-clocked | × closer | Δ R/day | expectancy gate |
|---|---|---:|---:|---|
| flat (control) | 0.197480 → 0.019798 | 9.975 | +0.0988 | both pass |
| low | 0.642836 → 0.242876 | 2.647 | +0.1182 | **FAIL → PASS** |
| mid | 0.741026 → 0.352365 | 2.103 | +0.1223 | **FAIL → PASS** |
| high | 0.856114 → 0.533447 | 1.605 | +0.1298 | both fail |

The improvement **weakens in p and grows in R/day**, and at low and mid it is a sign flip on the
expectancy gate that does not exist at flat. **Charging the measured era cost makes AM's B1200 repair
matter MORE.** The authored flat arm reproduces AM's own published `authored_utc` figures to full
precision, which is what makes the other three rows trustworthy.

What IS flat-only is the sleeve's **nearness to admission**: 6.93× the BH rank-1 bar at flat becomes
**123.33×** at mid — a **17.80×** proximity loss (not "18×"). The population axis helps the level and
does not rescue it: RECORDED 0.163, RECORDED_AND_DECIDABLE 0.117 at mid. Its prescription is
therefore **cost**, not more trades and not a population: 65.6 % of its SCHEDULE trades and 39.3 % of
its undecidable-RECORDED trades carry a charged cost range over 0.05 R, and its all-population median
cost range is 0.0256 R against `mx_btcusd`'s 0.0023 R — 11×, the widest of any candidate cell.

---

## 5. The recommendation, and the argument for it

**Ratify `RECORDED`.** Three measured reasons and one honest concession.

1. **It is the only population on which anything admits**, and the admission is not fragile to
   *which* trades are present: 38 of 40 year-matched placebo draws that delete 20 of its trades
   still ADMIT (§6.2).
2. **The objection to it is charged and survives.** "A third of its evidence sits on cost bands too
   wide to decide" is true of the band and false of the conclusion: at the pessimistic end of their
   own band those trades net +0.527 R/trade on a gross of +1.020, and their gross is
   indistinguishable from the clean population's.
3. **`DECIDABLE` is the weakest of the four as a standalone rule** — 36.5 % of the eras it calls
   decidable are `SCHEDULE`, where the narrow band is a degeneracy the model's own
   `_measure_class_hw_floor` docstring describes; and its threshold's level is uncalibrated across
   sleeves (§6.1). `RECORDED_AND_DECIDABLE` is defensible but converts a measured admission into a
   capture requirement in exchange for downside that has already been priced.
4. **The concession: RECORDED rejects at `band_high`.** The honest headline is *"admits across two
   thirds of the model's own cost envelope"*, and any publication of the admission has to carry it.
   `target_5R`, not `target_4R`, because only 5R survives the option change.

The decision doc is `phase10/POPULATION_RULE_DECISION.md`. **Ratifying is Borhen's; adopting the
widened table is the merge train's; α, arming and sleeve composition are untouched.**

---

## 6. What this session found that it was not sent to find

### 6.1 `decidable` is measured in the wrong units [B1262]

The scale-correct question is not "is the spread's log band narrow" but "is the cost uncertainty
small relative to R". The instrument: `|total_r(band_high) − total_r(band_low)|`, which is **exactly
the spread range** (max deviation 2.2e-16 over 232 trades — commission, swap and slippage are
band-independent and cancel), hence a function of `(symbol, entry_utc, sl_distance_price)` alone and
unable to read a return.

| | median charged cost range | n |
|---|---:|---:|
| `mx_btcusd` RECORDED ∧ **undecidable** — the flag REJECTS these | **0.0122 R** | 78 |
| `sub_mid_dn_revert` SCHEDULE ∧ **decidable** — the flag ACCEPTS these | **0.0782 R** | 154 |

**That 6.383× is NOT an inversion**, and my first draft said it was. A refuter showed — and my own
re-run confirms to the digit — that within *every* sleeve the flag orders cost range correctly
(undecidable wider): `mx_btcusd` 8.83×, `sub_xvol_pullback` 5.09×, `sub_mid_dn_revert` 1.55×, pooled
over 939 trades **3.02×**, Spearman(flag, cost_range) **−0.2249**. The 6.383× is rank 1 of 50
cross-sleeve group pairs, only 5 of which run the "wrong" way. **The defect is the LEVEL:**
`sub_mid_dn_revert`'s accepted trades (0.0232 R) sit above `mx_btcusd`'s rejected trades (0.0122 R),
so one fixed log threshold tolerates 1.9× more cost uncertainty on one sleeve than it refuses on
another. One threshold cannot serve a 0.9 %-of-R spread and a 6 %-of-R spread; a threshold in R can.

### 6.2 The proposal, and the placebo that refuted its p [B1263]

`RECORDED ∧ cost_range ≤ τ`, τ swept:

| τ (R) | 0.02 | 0.05 | 0.10 | 0.15 | 0.20 | 0.25 | 0.50 |
|---|---|---|---|---|---|---|---|
| n | 193 | 212 | 216 | 221 | 221 | 221 | 221 |
| p_raw | 0.0011 | **0.0008** | 0.0008 | 0.0008 | 0.0008 | 0.0008 | 0.0008 |
| verdict | ADMIT | ADMIT | ADMIT | ADMIT | ADMIT | ADMIT | ADMIT |

A plateau from 0.05 upward, so no τ is doing work — which is the opposite of a tuned threshold, and
it is why the cell looked like the answer. Then:

| | mean gross R | win rate | years |
|---|---:|---:|---|
| kept (212) | **+1.1301** | 36.3 % | all |
| dropped (20) | **−0.1000** | 15.0 % | 2018 (9), 2020 (11) |

Two seeded placebos, 40 draws each, solo gate: **P1** uniform reaches p ≤ 0.0008 in 6 of 40;
**P2** matched to that exact year histogram reaches it in **10 of 40 — placebo p 0.268**.
`H_calendar` is **not refuted**. The criterion never reads a return, but its p gain is
indistinguishable from removing any 20 trades from two bad years. So: structural finding stands,
verdict claim withdrawn, routed as a repair with the instruction that τ be fixed on a materiality
argument in R and **never on a p-value**, and re-tested on a sleeve whose spread is a larger share of
its risk unit, where the two orderings should separate the other way.

---

## 7. Artifacts

| file | what |
|---|---|
| `phase10/receipts/POPULATION_RULE_V1.json` | the commissioned deliverable: 240 grid arms, the B1250 delta with its per-trade census, the widened-table evaluation, the clock×band comparator, the econ proposal, and C1/C2/C3 |
| `phase10/POPULATION_RULE_DECISION.md` | the one-page decision for Borhen |
| `phase10/receipts/AN_ECON_PLACEBO_V1.json` | the two placebos, 80 seeded draws, and the verdict that killed my own proposal's p |
| `phase10/receipts/an_population_rule.py` | the driver; six stages (`probe`, `delta`, `grid`, `widened`, `clockband`, `econ`) |
| `phase10/receipts/an_econ_placebo.py` | the placebo, seeded so it reproduces byte-for-byte |
| `phase10/receipts/an_repair_rows.py` | the six queue rows |
| `src/costs/spread_model.py` | B1250; `src/costs/model.py`, `walkforward/panel.py`, `walkforward/spec.py` B1251 |
| `src/research_infra/walkforward/era_population.py` | **new** — the population rule, named once |
| `tests/test_spread_model.py` | +5 tests (B1250), 1 strengthened, 1 rewritten (B1264) |
| `tests/research_infra/test_era_population.py` | **new**, 14 tests |
| `tests/research_infra/test_published_seals_pinned_by_value.py` | **new**, 7 tests (B1253) |
| `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` | **110 → 116 rows**, 6 appended, session `AN` |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | every look; **10,524 → 10,808**, 284 of them AN's — including all 82 placebo draws, because a look taken cannot be un-taken and inflating the DSR trial count with random draws is the conservative direction (quote as a floor; it grows on re-run) |

---

## 8. What I got wrong

**Nine refuters plus a completeness critic, each told to default to `refuted` and to verify by
running code. Seven returned refuted, and six of the seven corrected a number I was about to
publish.** Two were caught by my own controls before the pass. Everything below is fixed in the
numbers rather than footnoted.

### 8.1 I published a wrong correction to AM, and the arithmetic of my own error proves it

The worst one, because it accused another session of two reporting errors it did not make. I counted
eras carrying the provenance stamp `band_halfwidth_log_v1` (**585**) rather than eras whose
half-width **moved** (**536**). **49 of the 585 carry a delta of exactly 0.000000** — stamped for
provenance, unmoved — and `536 × 0.166247 / 585 = 0.152322`, which is precisely the "corrected" mean
I published. AM's 536 / 0.166 was right all along.

The same error moved the load-bearing figure: I read FTMO CHFJPY 2000Q2 (half-width 0.43031,
**delta 0**) as the widest widened era, when it is FTMO AUDUSD 2000Q2 at 0.404800. So the headroom
to the decidability threshold is **0.0952 log** and the flip multiplier **1.235×**, not 0.0697 and
1.16× — I understated the margin by 37 %, in the note whose own text called it *"the one thing a
future re-sizing has to check"*.

### 8.2 "The re-clock gain is a flat-snapshot artefact" was a delta claim with no delta measured

I had the re-clocked arm at four bands and the authored arm at none, and drew a conclusion about the
difference. Measured (§4.2), the improvement survives every band and **grows in R/day**, with an
expectancy-gate sign flip at low and mid that does not exist at flat. The supportable sentence is
about the sleeve's *nearness to admission*, which is flat-only at 17.80×. I published the wrong one
of two sentences that sound alike.

### 8.3 "`Coverage.MEASURED` IS the intersection population" — false, and my test could not see it

I asserted `MEASURED ⟺ anchor MEASURED ∧ RECORDED ∧ decidable`, "0 mismatches over 2,653 era
cells", in a production docstring, a rule note and a test. The census **structurally could not
contain a counterexample**: it skipped every `era_fallback` symbol (their `eras` dict is empty) and
every cell where the nearest-era fallback moved off the requested quarter — the two families where
it breaks. Exhaustively probed it fails on **105 RECORDED + gap ≥ 1** cells (`if gap: MODELLED` is
unconditional while `decidable` only flips past `MAX_ERA_GAP_QUARTERS`), **63 REFERENCE** and
**23 NO_BAR_HISTORY**. The correct predicate needs `era_gap_quarters == 0` and the wider class set —
**0 mismatches over 8,748 probes** — and it matters on the admitting sample: 16 of 232 trades
(6.9 %). The test now runs the exhaustive cross-product and asserts each dropped clause is
individually load-bearing. **A control whose scope cannot contain a counterexample is not a
control**, and I wrote one.

### 8.4 "The orderings are close to INVERTED" — the direction was right everywhere

§6.1. I reported an extreme cross-sleeve order statistic as a property of the rule. Within every
sleeve and pooled, `decidable` orders cost range correctly. The corrected claim (a level that is not
calibrated across sleeves) is weaker, truer, and still supports the prescription.

### 8.5 "The stamps were already saturated" was true of 16 of 48 arm-cells

I gave one reason where there are three. On the 12 flat cells the repair is *inapplicable*; on the 36
banded cells `weakest_coverage` is genuinely saturated; `measured_frac` is saturated only on the 16
`mx_btcusd` cells. On the other 32 it is **live** (0.051–0.173) and held by **data** — all 39
fully-MEASURED-cost trades happen to sit in decidable, non-gapped RECORDED eras. One undecidable era
touching any of those 39 would have moved it. So "moves nothing" is a structural guarantee for the
verdict fields and only a measured fact for `measured_frac`, and I published it as if both were
structural.

### 8.6 I quoted a control's denominator as 240 when it was 72

§3.3. `decidability_refusals == 0 on all 240 arms` reads as a check that passed 240 times; on 168 of
them a nonzero value is unreachable, and it is armed on **0 of the 9 ADMIT arms**. The refuter also
supplied the positive control I should have run myself: the same population with the flag on gives 9
refusals.

### 8.7 "test_candidate_family pins the 18 published seals" — it pins 3

§2.3. All 18 do reproduce; the *suite* guards 3 of them by value and 15 by a count that survives
substitution with fabricated hashes. Fixed by adding a test rather than by softening the claim.

### 8.8 Two I caught myself, both of the same class as §8.1

- **A `nan != nan` comparator** reported "2 verdict fields moved" by the B1250 repair. Both were
  `drop_best_retention: nan → nan` on `sub_mid_dn_revert @ ALL_ERAS @ band_high`, whose drop-best
  expectancy is 0/0. Publishing that would have been a fabricated finding of exactly the kind AL
  §8.4 and AK §7.6 recorded against themselves. The comparator is NaN-aware and says why.
- **The widened-artifact reader returned all zeros** — "0 eras moved, 0 flips, 0 mid ratios" — which
  would have published *"AM's repair changes nothing"*. It read `band_halfwidth_log`; the widening
  lands on `band_halfwidth_log_floored`. A silent null in an adversarial artifact is worse than a
  failed attack (agreement §2), and this one would have been worse still because it flattered my own
  conclusion.
- **And a flipped percentage pair** in a repair-queue row, appended and then corrected by removing
  exactly my own six rows (verified: 110 pre-existing rows byte-preserved) and re-appending.

### 8.9 The completeness critic found a live verdict-inverting bug in my own adversarial file

Fifteen gaps, of which the worst is the third instance of the same class as §8.8. My placebo's
`summarise()` computed `atleast = sum(1 for p in ps if p <= (p_econ or 0))`. `_p()` returns None by
design when a sleeve is ABSENT, and `p_econ or 0` makes that `p <= 0`, which no permutation p
satisfies — so `atleast` would go **10 → 0**, `placebo_p` **0.2683 → 0.0244**, and the printed
conclusion would flip from *"H_calendar NOT REFUTED"* to *"H_calendar REFUTED at the 0.10 level"*.
Measured on the artifact's own 40 draws. **An adversarial control that fails silently in the
direction of its own thesis is worse than no control**, and I wrote one while §8.8 was on the page.
Both reference arms are now guarded loudly, and its `min(k, len(pool))` under-draw — which would
have made the "matched" placebo delete fewer trades than the rule it tests — raises instead.

Four more from the critic, all fixed:

- **A bad band token failed OPEN in `src/`.** `classify` catches `Exception → None` and
  `filter_records` keeps on None, so an unrecognised band made `estimate` raise on *every* trade,
  which read as "unclassifiable" and kept all of them — the strictest population silently becoming
  the control. Measured: `"MID"`, `"typo"`, `""` and `None` each took RECORDED_AND_DECIDABLE from
  1-of-8 to **8-of-8** with `mix == {"kept": 0, "dropped": 0, "unpriceable": 8}`. Both the band and
  the nothing-classified case now raise, with two tests.
- **My own trial ledger under-counted by 88 looks** — `run_arm` recorded only when
  `p_raw is not None`, dropping every NOT_EVALUABLE arm, 36.7 % of the grid, while the sibling
  placebo file commits in writing to the opposite standard. Every gate run is recorded now.
- **A p95 off-by-one** (`int(0.95 * len(v)) - 1`) put two published 95th percentiles *below* their
  own medians on small groups. Nearest-rank now.
- **The declared family is declared, not ratified.** `CANDIDATE_FAMILY_V2` carries
  `ratified_by: null`; CLAUDE.md's ratified record is V1 at 32. The direction is conservative
  (q 0.0385 at 35 against 0.0352 at 32, and `target_4R` fails Bonferroni at either), so it is
  disclosure rather than arithmetic — but "declared family 35" should not be read as ratified.

**And the critic caught that the published artifact was STALE against its own driver** in three
places, because I had re-run only the stages I had just edited. Fixed by re-running `--stage all`,
which is the only way the artifact and the code can be the same thing.

### 8.10 What the pass could NOT refute

- **The coverage-repair arithmetic, every integer.** A refuter A/B'd the pre-repair module against
  HEAD over all 2,653 cells: 192 changed, 166 + 26 exactly as claimed, 275 firing, 182 RECORDED,
  FTMO 195/134 and redacted_account 80/48, 9.3 % of FTMO eras. Monotonicity over 21,287 paired calls with
  0 strengthened and 0 cost values changed. It also confirmed the `fb` case is genuinely subsumed
  rather than dropped (0 changes over 7,728 fallback calls).
- **The population parity.** Counts identical on all nine including the four AL never published for
  BTC at `target_4R`; `p_raw` Δ **exactly 0.0** on all five shared arms; `pooled_oos_mean_r`
  identical to 17 decimals; five distinct seals against one in AL's lane. And the drop-vs-keep
  reversal of §2.2 A/B'd both ways: identical counts in all 25 cell × population combinations,
  because `unpriceable` is 0 everywhere.
- **The 9-of-240 ADMIT census and every count in it**, plus `coverage_frac` 1.0 and `n_unpriced` 0
  on 240/240 — it is the *inference* about the control's denominator that was wrong, not the counts.
- **The econ instrument's numbers**: 0.012248, 0.078182, 6.383, the +0.5272 / +0.7756 / +1.0196
  triple, and that `spread_require_decidable=True` refuses exactly the 78 RECORDED-undecidable
  trades element-wise. It is the word "inverted" that failed, not a figure.
- **`sub_mid_dn_revert`'s flat reproduction of AM to full precision**, and the fairness of the
  flat-vs-mid comparison on every axis (same population, exit, option, family, coverage policy;
  only the band and therefore the seal differ).

---

## 9. Verification — the §2 scoped receipt

See `phase10/SESSION_AN_AB.md` for the capture. Summary:

- **Blast radius** by `pytest_failset.py scope --base 8db17b29c --include-worktree`: 21 test files
  by import closure and path literal, no escapes, no unresolved, no deleted tests.
- **HEAD: 0 failed / 0 errored.** +26 new tests (5 in `test_spread_model.py`, 14 in
  `test_era_population.py`, 7 in `test_published_seals_pinned_by_value.py`), 1 test strengthened and
  1 rewritten.
- **The five new B1250 tests were each verified RED against the pre-repair logic** by copying the
  patched module aside, applying the old branch in place, running, and restoring by copy-back. A
  test that passes against a wrong implementation is worthless, and this is the only way to know.
- **H1**: 2 UNHYDRATED-LFS / 0 DRIFTED — a property of local LFS hydration per `CLAUDE.md` §3's
  2026-07-30 amendment, not of any commit. **None of the five edited `src/` files is bound**;
  membership checked before editing.
- `config/agent_config.yaml` neither read for a live decision nor written. No broker module imported
  by any receipt script. Nothing merged, nothing pushed.

---

## 10. Routing

**For Borhen — one ratification.** `phase10/POPULATION_RULE_DECISION.md`. Recommendation:
`RECORDED`, band stamp mandatory, `target_5R` as the cell.

**For the merge train.** Adopt `SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json` (0 verdicts moved,
mid byte-identical, AM's figures correct), carrying the 0.0952-log headroom condition.

**For the next session, in value order.**

1. **`mx_btcusd`'s sample, still.** AL's item 1 is untouched and remains the best lever: 318 trades
   on one symbol over nine years, and pooling with its donchian siblings for power (not for
   diversification, which AF refuted) has never been run. The nine undecidable BTCUSD quarters
   (2018Q2–2025Q3) are also a **named capture requirement** — tick data for them would close the
   band objection outright rather than arguing it.
2. **The scale-correct population rule, with τ fixed on materiality.** §6.2 built the instrument and
   refuted its p. What remains is a τ chosen in R, and a re-test on a sleeve whose spread is a large
   share of its risk unit — `sub_mid_dn_revert` at 0.0256 R median is the obvious candidate, and it
   is where the calibration defect should bite hardest.
3. **`sub_mid_dn_revert`'s cost, not its clock and not its population.** §4.2: its lever is a symbol
   subset with tight era bands, or capture. Its clock repair is real and larger under cost than it
   looked.
4. **`sub_xvol_pullback` is NOT_EVALUABLE on all four populations under `A_strict`** and on two of
   four under `B_balanced`, while trading real money. Not an argument for disarming — an argument
   that its evidence has a coverage shape the arming discussion should state.

**Not mine and untouched:** the VPS, arming, tokens, gates, α, sleeve composition, the risk dial,
ratifying the population rule, adopting the widened table, merging to `main`,
`config/agent_config.yaml`.
