# The population rule — one decision, for Borhen

**Session AN, 2026-07-30.** Evidence: `phase10/receipts/POPULATION_RULE_V1.json` (240 gated
arms) and `phase10/receipts/AN_ECON_PLACEBO_V1.json`. Nothing here is armed, nothing touches
`config/agent_config.yaml`, nothing touched the VPS.

**You are ratifying a measurement protocol, not a verdict.** The question is which eras count as
evidence when a sleeve is judged. Wave 8 answered it in passing, inside a driver, and nobody
chose it; Session AL then measured that the answer decides whether this estate has an admitted
candidate at all.

---

## The decision, in one table

Every arm below is `mid` band, `B_balanced` (α = 0.10, BH), declared family 35, broker-true cost.
`q` is comparable only inside this table.

| population | what it keeps | `mx_btcusd @ 5R` | `mx_btcusd @ 4R` | `sub_xvol_pullback @ 4R` | `sub_mid_dn_revert` |
|---|---|---|---|---|---|
| **ALL_ERAS** (control) | everything priceable | REJECT · 318 · p 0.0106 | REJECT · p 0.0133 | REJECT · p 0.0077 | REJECT · p 0.352 |
| **RECORDED** (standing) | eras from an observed series | **ADMIT · 232 · p 0.0011 · q 0.0385** | **ADMIT · p 0.0023 · q 0.0805** | REJECT · p 0.0080 | REJECT · p 0.163 |
| **DECIDABLE** (the model's own) | eras whose band is narrow | REJECT · 240 · p 0.0581 | REJECT · p 0.0717 | NOT_EVALUABLE (n 56) | REJECT · p 0.440 |
| **BOTH** (strictest) | observed **and** narrow | REJECT · 154 · p 0.0158 | REJECT · p 0.0301 | NOT_EVALUABLE (n 53) | REJECT · p 0.117 |

**Across the whole grid — 240 arms, 4 bands, 2 options, 2 exits — exactly 9 arms ADMIT and all
nine are `mx_btcusd` on `RECORDED`.** Zero admissions exist on any other population, at any band,
under either standard. The population rule is the only thing standing between this estate and no
admitted candidate.

---

## What each rule costs you

**RECORDED — admits, and its objection is measured and bounded.**
It keeps 78 `mx_btcusd` trades in quarters the model itself calls capture requirements, one with
a band spanning **204,058×**. That sounds fatal and is not, because a band is only as important
as the quantity it is a band on: BTCUSD's spread is **0.9 % of its risk unit**, so charging the
*pessimistic* end of that band takes those 78 trades from +0.776 to **+0.527 R net per trade** on
a gross of +1.020 R. They are also not free-riders and not a different population — their gross
is +1.0196 R/trade against the clean 154's +1.0263.
**Its real cost is the band, not the eras:** RECORDED admits at flat, low and mid and **REJECTS at
high** (p 0.0051). The honest headline is *"admits across two thirds of the model's own cost
envelope"*, and the whole band sensitivity lives in those 78 trades — the other 154 move 0.6 %
from low to high. One caveat on the +0.527: **13 of the 78 are charged more than a full risk unit
of cost at `band_high`** (max 2.35 R), which are not trades anyone would take. The mean is the
right statistic for an expectancy claim and it is honest to say it averages over some cells the
pessimistic band prices out of existence.

**DECIDABLE — rejects everything, and it is the weakest of the four as a standalone rule.** Two
measurements. **36.5 %** of the eras it calls decidable are `SCHEDULE` — a single backfilled
constant, where every dispersion term is zero *by degeneracy* and the floor puts it at 0.18229,
comfortably under the 0.5 threshold. And its threshold is **not calibrated across sleeves**: the
same 0.5 in log-spread means different amounts of R depending on how big the spread is relative
to the stop. `sub_mid_dn_revert`'s *accepted* trades carry a median charged cost range of
**0.0232 R** while `mx_btcusd`'s *rejected* trades carry **0.0122 R** — so the flag tolerates
1.9× more cost uncertainty on one sleeve than it refuses on another.

> **My first draft called that an inversion and it is not** — an adversarial pass over my own
> claim refuted the word. Within *every* sleeve the flag orders cost range correctly (undecidable
> wider): `mx_btcusd` 8.83×, `sub_xvol_pullback` 5.09×, `sub_mid_dn_revert` 1.55×, pooled over
> 939 trades 3.02×, Spearman −0.2249. The 6.4× figure I first published is the largest of 50
> cross-sleeve group pairs, only 5 of which run the "wrong" way. The defect is the level, not the
> direction — which is a weaker criticism and the true one.

Do not ratify this one, but for the calibration reason and the degeneracy reason, not because the
flag is backwards.

**BOTH — defensible, rejects everything, and buys no measured honesty.** n falls 232 → 154
(−34 %). The honesty it buys is the 78 trades' cost uncertainty, and that uncertainty is already
charged and already survived: worst case +0.527 R/trade. Adopting it converts a measured
admission into a capture requirement in exchange for downside that has been priced.
(It is *nearly* the same set as `Coverage.MEASURED` on a tick-anchored symbol but not identical —
the coverage class additionally excludes gap-extrapolated eras, which is 16 of the 232 admitting
trades. A first draft of this line claimed they were the same set; an adversarial pass refuted it.)

**ALL_ERAS — rejects everything, and charges 20–50× SCHEDULE backfills** the model's own
`honest_limit` says nothing validates.

---

## Recommendation: ratify **RECORDED**, with two conditions

1. **The band travels with the admission, always.** `mx_btcusd @ target_5R` on RECORDED is
   ADMIT at flat/low/mid and REJECT at high. Publish it as *"admits at two of three bands"* — never
   as a bare ADMIT. At `band_high` its p 0.0051 sits inside the BH **rank-2** threshold, so at the
   pessimistic band it would need a partner again.
2. **`target_5R` is the cell, not `target_4R`.** Both admit under BH, but 4R's p 0.0023 fails
   Bonferroni (bar 0.00143) while 5R's 0.0011 clears both standards. If you want one admission
   that survives an option change, it is 5R.

**Why RECORDED and not the intersection:** the objection to RECORDED is a cost-uncertainty
objection, and cost uncertainty is the one thing this estate can now charge rather than argue
about. Charged at its worst, the disputed evidence still pays. The intersection answers the
objection by deleting the evidence instead of pricing it.

**What I tried that did not work, because you should know the recommendation survived an attack
on it.** I built a scale-correct replacement — keep a trade if its charged cost range across the
model's own band is ≤ τ R — and it admits at **every** τ from 0.02 to 0.50 with a plateau from
0.05, at p 0.0008 against RECORDED's 0.0011, on 221 of 232 trades. It looked like the answer. Then
the placebo killed the improvement: the 20 trades it drops average **−0.10 R** against the kept
+1.13 R and all 20 sit in 2018 and 2020, and a random 20-trade removal *matched to those same two
years* reaches p ≤ 0.0008 in **10 of 40 draws** (placebo p **0.268**). So the criterion never reads
a return, but its p gain is not distinguishable from removing any 20 trades from two bad years.
**The structural finding stands and the verdict claim does not**, so it is routed as the next
repair and not offered as the rule.

One thing that came out of that attack is worth having on its own: **38 of 40 year-matched placebo
draws still ADMIT.** The admission does not depend on which 20 of those trades are present.

---

## Before you ratify: the admission decays, and no gate can see it

This is not about the population rule and it is the number I would most want in front of me. The
folds are equal calendar blocks in **time order**:

| fold | window | n | gross R/trade | fold R/day | share of the disputed 78 |
|---|---|---:|---:|---:|---:|
| 1 | 2019-01-03 … 2020-05-07 | 36 | 1.333 | +1.134 | 41.7 % |
| 2 | 2020-05-08 … 2021-09-11 | 42 | 1.805 | +1.512 | **90.5 %** |
| 3 | 2021-09-12 … 2023-01-16 | 26 | 2.146 | **+1.866** | 0 % |
| 4 | 2023-01-17 … 2024-05-21 | 30 | 0.600 | +0.284 | 0 % |
| 5 | 2024-05-22 … 2025-09-25 | 50 | 0.440 | +0.112 | 24.0 % |

**The two most recent folds average +0.198 R/day against the first three's +1.504 — 13.2 %, on
34.5 % of the trades and the most recent 2.7 years.** Every gate passes anyway, because
`stability` counts only the **sign** of a fold mean, not its level. A 7.6× chronological decay is
invisible to the standard by construction.

And it explains the population difference mechanically: **53 of the 78 disputed trades sit in folds
1–2**, fold 2 is 90.5 % disputed and carries the second-highest fold mean, and folds 3–4 contain
none. So dropping the 78 does not shave a pooled mean — it removes most of two early folds and
takes fold positivity from 5/5 to 3/5, which is what moves p from 0.0011 to 0.0158. The pooled
statement above ("their gross is indistinguishable from the clean 154's") is true and does not
carry that.

**What it means for the decision:** the population rule is still the population rule, and RECORDED
is still the only rule under which anything admits. But *any* use of this admission should be sized
on the recent folds, not the pooled figure. Both facts came from a completeness critic run over
this session's own output; neither was in the first draft.

## Three other things this decision should be made alongside

- **`sub_mid_dn_revert` is not near admission, but AM's clock repair is not the reason — and my
  first draft of this bullet had that backwards.** Its *nearness* is flat-only: p 0.0198 at the
  flat snapshot (reproduced to the digit) is 6.93× the bar, and at the mid band the same trades
  give **p 0.352 = 123× the bar**, a 17.80× proximity loss. But the *re-clock improvement* is not
  a flat artefact at all — measured at all four bands, it weakens in p (9.98× → 2.10×) and **grows
  in R/day** (+0.099 flat → +0.122 mid → +0.130 high), and at low and mid it is a **sign flip on
  the expectancy gate** that does not exist at flat. Charging the measured era cost makes AM's
  repair matter *more*. Two different sentences; only the first is about admission.
- **Adopt AM's band-widened era table, and AM's published figures need no correction.** It moves
  **0 verdicts** across every standing candidate, leaves the mid band byte-identical, and its only
  measured effect is 4 of 54 arms on `sub_mid_dn_revert` moving in both directions. Cost of
  adoption ≈ 0, and it replaces an unvalidated level shift with an honest band. **A "correction"
  in my own first draft is withdrawn**: I read the artifact's provenance stamp instead of its
  movement and published 585 eras at +0.152 log against AM's 536 at +0.166. 49 of the 585 stamped
  eras carry a delta of exactly zero, and 536 × 0.166247 / 585 = 0.152322 — my figure was AM's
  diluted by those zeros. AM was right. One condition survives: the widest actually-widened
  half-width is 0.4048, **0.0952 log** short of the decidability threshold, so a hypothesis
  **1.235×** larger starts flipping eras to undecidable — which now degrades coverage, where
  before this session it did not.
- **The choice is now sealed, whichever way you make it.** Two runs on two different populations
  used to produce the same `spec_sha256`; they no longer can. Zero seal collisions across 240 arms.

**Not yours to decide here, and untouched:** α, arming, sleeve composition, the risk dial, the
registry weight. This is one line of measurement protocol.
