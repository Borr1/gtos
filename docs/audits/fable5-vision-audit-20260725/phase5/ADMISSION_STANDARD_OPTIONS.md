# The admission standard — three options, and what each one actually admits

**For Borhen. This is a decision, not a report.** Sleeve composition and the admission
standard are yours, the same class as the risk dial (`WAVE_5_WORKING_AGREEMENT.md` §1).
Session W's job was to make the choice concrete rather than adjectival, so every option
below is run through the real market-expansion family and the admit/reject lists are
measured, not described.

**Nothing here changes what is armed.** The gate is offline research machinery. It reads
bars and cost artifacts and writes JSON.

---

## 1. The short version

| | **A — Strict** | **B — Balanced** | **C — Exploratory** |
|---|---|---|---|
| Controls | P(*any* bad admission) ≤ 5% | Expected *fraction* of admissions that are junk ≤ 10% | Same, ≤ 20% |
| Method | Bonferroni (FWER) | Benjamini–Hochberg (FDR) | Benjamini–Hochberg (FDR) |
| Partially-priceable sleeves | refused | evaluated on the priceable subset, stamped | same |
| OOS folds needed | 4 | 3 | 3 |
| Folds that must be positive | 75% | 60% | 50% |
| Survives deleting its best fold | ≥60% of the headline retained | ≥50% | not required |
| Minimum trades | 50 | 30 | 20 |
| **Admits, of the 12 live market-expansion sleeves** | **0** | **0** | **1** |

**What each is for.** A is what you arm on. B is what you build a watched candidate book
from. C is a research queue — it tells you where the next data capture would pay, and a
C-pass must never reach a book.

---

## 2. What the three have in common, and why those are not negotiable

Relaxing any of these would stop the gate being a gate rather than making it more
permissive, so none of them is offered as a dial:

- **Out-of-sample only.** No in-sample statistic enters any verdict. IS numbers are
  reported so the IS→OOS decay is visible, and they touch nothing.
- **Broker-true cost, or refusal.** `src/costs/cost_r` prices the trade or the trade is
  unpriced. Never a substituted number — that is F38, the defect that made a 1,679-day
  positive validation worthless by charging zero commission.
- **A day-blocked null.** Treating trades as independent overstated a delivered error budget
  by 2.1×–7.7× on this programme's own data (B279).
- **A generation-fidelity floor.** A sleeve the port cannot reproduce is refused, not scored.
- **Lifetime accounting.** Every priced trade counts toward a full-sample expectancy floor,
  including the never-scored first fold. This exists because an adversarial refuter got a
  sleeve that lost **17,840 R over 23,325 trades** to ADMIT under the *strictest* option by
  parking the losses where the scored statistic did not look.

---

## 3. The measured answer, on the 12 sleeves the live config resolves

Generated over the full FTMO D1 archive (7,710 union daily closes, 2000-03-29 → 2026-07-27),
priced at broker truth, 2,086 trades after de-duplication on the live idempotency key.
Receipt: `phase5/receipts/W_MX_PILOT.json`. Spec seals: A `48cdb2edc4df`,
B `3ed0afa45894`, C `d747ff1532f1`.

| sleeve | trades | OOS R/day | q (B) | folds + | A | B | C |
|---|---:|---:|---:|---:|:-:|:-:|:-:|
| `mx_btcusd_d1_donchian_20_breakout` | 318 | **+0.2446** | 0.149 | 100% | ✗ | ✗ | **✓** |
| `mx_jp225_cash_d1_volume_surge_reversal` | 110 | +0.1985 | 0.487 | 80% | ✗ | ✗ | ✗ |
| `mx_ethusd_d1_donchian_20_breakout` | 311 | +0.1816 | 0.373 | 60% | ✗ | ✗ | ✗ |
| `mx_avausd_d1_donchian_20_breakout` | 189 | +0.1265 | 0.521 | 60% | ✗ | ✗ | ✗ |
| `mx_nzdjpy_d1_donchian_20_breakout` | 503 | +0.0800 | 0.524 | 60% | ✗ | ✗ | ✗ |
| `mx_us30_cash_d1_volume_surge_reversal` | 121 | +0.0584 | 0.652 | 40% | ✗ | ✗ | ✗ |
| `mx_ger40_cash_d1_volume_surge_reversal` | 110 | −0.0112 | 0.934 | 60% | ✗ | ✗ | ✗ |
| `mx_us500_cash_d1_atr_mean_reversion` | 67 | −0.2551 | 1.000 | 20% | ✗ | ✗ | ✗ |
| `mx_us100_cash_d1_atr_mean_reversion` | 71 | −0.3518 | 1.000 | 0% | ✗ | ✗ | ✗ |
| `mx_cadjpy_d1_volume_surge_reversal` | 286 | — | — | — | n/e | n/e | n/e |
| `mx_eu50_cash_d1_volume_surge_reversal` | 0 | — | — | — | n/e | n/e | n/e |
| `mx_fra40_cash_d1_volume_surge_reversal` | 0 | — | — | — | n/e | n/e | n/e |

**Every one of the seven gates rejected at least one real sleeve**, which is the clearest
evidence that none of them is decorative:

- **coverage** — `cadjpy`, `eu50`, `fra40`: broker truth has no measured spread.
- **expectancy (per day)** — `ger40`: −0.0112 R/day.
- **expectancy (per trade)** — `us100`, `us500`: day-mean flattered them; per-trade did not.
- **lifetime** — `nzdjpy`: +0.0800 R/day on the scored window, **−0.00296 R/trade across its
  whole history**.
- **stability** — `us30`: only 40% of OOS folds positive.
- **robustness** — `avausd`, `ethusd`: delete the single best fold and the edge goes.
- **significance** — `btcusd` (q 0.149), `jp225` (q 0.487).

### The one that is close

`mx_btcusd_d1_donchian_20_breakout` is the only sleeve with a real case: **+0.2446 R/day
net of broker-true cost, 100% of OOS folds positive, raw p = 0.0124** across 318 trades and
five purged/embargoed folds. It fails B on the family correction alone — q = 0.149 against
α = 0.10 — and passes C. It is not a marginal call about the sleeve; it is a marginal call
about how much credit to give one sleeve out of twelve.

---

## 4. What this does *not* say

**It does not say the market-expansion book is worthless.** It says that at broker-true
cost, out of sample, with the family correction charged, **none of the twelve clears a
standard you would arm on**, and one clears a standard explicitly labelled research-only.

**Three things bound the result, all of them stated because they cut in the optimistic
direction:**

1. **Cost is measured in the near-present and charged to the past.** The tick spread
   measurement covers **2026-06-18 → 2026-07-24** — 37 days — and is charged as a constant
   to a panel running 2007–2026, only 6.5% of which is in 2026. On this family cost is
   **33%–219% of gross R**. Spreads compressed over that period, so historical trades are
   systematically *under*-costed and every number in §3 is **optimistic by an unmeasured
   amount**. A sleeve that only just cleared would not really have cleared.
2. **Port fidelity for this family is transferred, on n=5.** K measured one `mx_*` sleeve
   (`mx_nzdjpy`, 5 agreed / 0 live-only). The 96% per-bar class rate is real, but 148 of its
   160 agreed intents come from three core-book sleeves.
3. **Entry is the decision bar's close, not the next open.** Measured signed bias:
   **+0.00152 R**, i.e. marginally *against* the sleeves. Not material.

**And what it does not cover at all:** the nine candidate sleeves. Seven of them are
first-of-day, where the port reproduces **19%** of live decisions, so any number would
measure the port's latch defect rather than the sleeve. They are refused, not scored.
Session Y owns that repair.

> **AMENDED 2026-07-29 — Session Y landed, and seven of the nine are now judgeable.** The 19%
> was not a latch defect: the port was replaying *mainline* against a live record produced by
> the VPS lineage, whose sleeves compare raw UTC hours to constants that are broker-server
> hours, so every session window sat 3 h apart. Matched, the port recovers **175 of 175**
> missing intents with **0** newly missed and all seven reach **100% live-recall**. See
> `SESSION_Y_FIRST_OF_DAY_RESULT.md`.
>
> **Two caveats you should carry into the decision, not one.** (a) The 100% is *recall*;
> identity **precision** across the seven is **72%**, and the gate's `scoreable()` has no
> precision term at all — a generator emitting 40% junk would pass it. (b) The measurement is
> **38 summer days at a constant +3 h offset**; it is not measured at the winter offset, on a
> DST transition day, or under mainline's own 21:00 UTC latch reset. Both are stamped on every
> raised row. Whether a precision floor joins `fidelity_floor` is a decision of the same class
> as the three in §7 — Y measured it and deliberately did not move the gate.

---

## 5. The recommendation, and the reasoning you can overrule

**Take B for the estate walk, and read C as the research queue.**

B controls the quantity a book owner actually cares about — what fraction of what I admit is
junk — rather than the quantity a statistician defaults to. On a 21-hypothesis family at the
sample depths this archive supports, Bonferroni divides α by 21 and approaches "admit
nothing"; a standard that structurally cannot admit is not a standard, it is a decision
already taken.

**The argument against, which is real:** B accepts that roughly one admitted sleeve in ten
is noise, and under B a partially-priceable sleeve is admitted on a *narrower* sleeve than
the one in the config. If the next step after admission is real money on a funded account
rather than a watched shadow book, A is the right standard and the cost of A is that it will
admit very little — and some of what it refuses, it refuses for missing tick data rather
than for anything about the sleeve.

**On the current evidence the choice between A and B does not change any outcome.** Both
admit zero. The choice matters for Session X, when the same standard is applied to the wider
estate.

---

## 6. What would change the answer

In descending order of value per unit of work:

1. **Tick capture for `CADJPY`, `EU50.cash`, `FRA40.cash`, `AUS200.cash`, `SPN35.cash`** —
   and D1 bars for `EU50.cash` and `FRA40.cash`, which are absent from the archive entirely.
   This is the difference between judging 9 sleeves and judging 14. It is a data fetch.
2. **A historical spread series** rather than a 37-day snapshot. This is the single largest
   unquantified bias in every number above, and it is knowably one-directional.
3. **An honest trial count.** No trial-budget ledger exists anywhere in the repo, so the DSR
   deflation runs against a floor of 128 and a published sweep rather than a measurement.
   `validation_integrity/trial_budget_ledger.py` exists to build one and has never been run.
4. **Session Y's first-of-day repair**, which unlocks 7 of the 9 candidate sleeves.

---

## 7. What you are being asked to decide

1. **Which standard** — A, B or C — Session X applies to the rest of the estate.
2. **Whether `mx_btcusd_d1_donchian_20_breakout`**, the one sleeve that passes only the
   research-grade standard, is worth a shadow slot or should wait for more data.
3. **Whether the tick capture in §6.1 is worth commissioning**, given it is what stands
   between the programme and an honest verdict on 5 of the 14 market-expansion sleeves.

Nothing has been armed, changed, or merged. The gate is on branch `phase5/walkforward-gate`.

---

## 8. Session X update — the standard applied to the whole estate

*Added 2026-07-29 by Session X. Sections 1–7 are Session W's and are unchanged.*

§5 said the choice between A and B does not change any outcome on W's twelve, and that "the
choice matters for Session X, when the same standard is applied to the wider estate." It has
now been applied. **It still does not change the outcome: all three standards admit zero, of
32 sleeves.**

| | **A — Strict** | **B — Balanced** | **C — Exploratory** |
|---|---|---|---|
| Admits, of W's 12 market-expansion sleeves | 0 | 0 | 1 |
| **Admits, of the 32-sleeve estate** | **0** | **0** | **0** |

`mx_btcusd_d1_donchian_20_breakout` — the one C-pass in §3 — **no longer passes C** once the
family is the whole estate rather than twelve: q rises from 0.149 to 0.264 against α = 0.20,
because the correction now charges 44 look-events (32 sleeves judged plus W's 12 prior looks)
rather than 12. That is the multiplicity correction working exactly as designed, and it is why
§7's first question has a cheaper answer than it looked: **on the current evidence the standard
does not decide anything, so choosing it can wait.**

**What the standard DOES decide is `metals_core`**, and that is the live decision hiding in this
table. At **A** and **B** it is `NOT_EVALUABLE` — broker truth prices 58.7 % of its trades
against a 60 % retention floor, **missing by 1.3 percentage points**, because `XAUEUR`,
`XAGEUR`, `XAUAUD` and `XAGAUD` have no measured spread. At **C** (retention floor 0.50) it is
evaluable and **REJECTs at −0.179 R/day with 20 % of OOS folds positive and −0.132 R/trade
across its whole 385-trade history.**

So the three standards differ, for the anchor sleeve of the funded book, between "cannot say"
and "measured negative". Neither is "admit".

**Two things update §6's ranking of what would change the answer.**

1. **§6.1's tick capture moves up, and its highest-value item is not on §6's list.** The four
   metals crosses above block **302 trades across five sleeves** and are the only thing between
   `metals_core` and an evaluable verdict at an armable standard. `CADJPY` (286 trades, the
   whole of `mx_cadjpy`), `EU50.cash`/`FRA40.cash` D1 bars, `XTZUSD` (112) and `DASHUSD` (35)
   follow.
2. **§6.3's trial count is now measured, and it is worse than a floor of 128.** Counting only
   the tests wave 5 actually ran: 132 gate look-events, 38 book compositions compared, 28
   diversifier certifications — **198 decision-bearing comparisons over 32 sleeve hypotheses
   whose effective independent count is about five**, resting on ≥74 authored sleeve designs
   with unrecorded parameter grids. Separately: **the DSR gates nothing** (`gate.py:771` lists
   five core gates and DSR is not among them), so the `n_trials` sweep §6.3 asks for would not
   flip a verdict at any value.

**§7 question 2 — is `mx_btcusd` worth a shadow slot?** Session X's answer is no, on new
evidence rather than on the standard: it correlates **+0.504** with the confidence-weighted
armed book over 51 overlapping days, against a 0.35 diversification ceiling. It is a duplicate
of what is already in the book, not breadth.

**§7 question 3 — is the tick capture worth commissioning?** Yes, and the case is stronger than
§6.1 stated: it is no longer only about judging 9 sleeves versus 14, it is about whether the
sleeve carrying the funded book's largest confidence weight can be judged at all.

Full detail: `SESSION_X_BOOK_LEVEL_RESULT.md`, `receipts/X_ESTATE_WALK.json`,
`receipts/X_COMMON_WINDOW_BOOK.json`, `receipts/X_STATE_D_SENSITIVITY.json`,
`receipts/X_ARMED_SET_MEMBERSHIP.json`.
