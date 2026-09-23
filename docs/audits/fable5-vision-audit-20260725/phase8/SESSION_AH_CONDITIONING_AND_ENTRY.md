# Session AH — member conditioning and entry economics: 23 families are mixtures, and the FX cohort enters at the worst hour of the week by construction

**Wave 8.** Worktree `worktrees/wave8-conditioning-entry-20260730`, branch
`phase8/conditioning-entry`, from `main`. **Blocks B1000–B1049.**

**Read `../WAVE_8_WORKING_AGREEMENT.md` in full first**, then AF's result §5–§7 (your work list
is cut from its routing), AB's regime-spine result (your conditioning dials), and AG's spread
result §10 (the era model you will repair).

---

## The mission

AF answered the breadth question: the estate's families are mixtures, and the two levers that
remain are **which member carries the edge and why** (23 families routed
`MEMBER_CONDITIONING_NOT_BREADTH`) and **what the entry actually costs** (the FX D1 cohort fills
at broker hour 00, the measured 13×–38× hour of the week, by construction). Both levers are
yours, plus the cost-model defect that currently prevents honest pricing of anything pre-2010.

## The work list, in value order

**1. The H4 re-entry test — the largest unpriced lever wave 7 found (AF §5.4).** The `mx_*` D1
family decides at the D1 close (broker 00:00) and enters there. The archive holds H4 bars for
every FX symbol, so entering at the first H4 close after the decision (broker 04:00) can be
simulated end to end — moving the entry *price* and therefore R geometry, not merely re-pricing
the spread charge. Regenerate the FX D1 cohort (and any other class where hour-00 cost is
material — AF measured ~0.000 R elsewhere, so check, don't assume) at the shifted entry, walk
through the gate at measured carry, and publish before/after per member. `mx_cadjpy` — the
estate's closest miss at −0.0017 flat — is the named beneficiary; its whole cohort rides along.
Where the shifted entry changes gross by more than cost, say which dominates and why — a
mechanism whose edge dies four hours after the close is a real finding about the mechanism.

**2. The era×hour product repair (AF §6, routed from AG's lane).** `spread_model_v1` composes
`anchor × era_ratio × hour_of_week` multiplicatively; each factor validated alone; the product
reaches 198×–880× on pre-2010 FX and charges up to 178 % of the risk unit as spread. Repair with
a validation, not a guess: propose the composition that the H4 block-pair data can actually
support (additive-in-logs with a cap? hour profile flattened outside RECORDED eras? era ratio
applied to the all-hours median only?), validate it on AG's own held-out pairs, and re-run the
verdicts AF published at `mid` band for the affected FX families. Publish which verdicts move.
Until your fix lands, everything downstream keeps AF's interim (`era_class == RECORDED`).

**3. Member conditioning on the 23 mixture families.** The substrate is complete:
`AF_FAMILY_TRADES.json.gz` is regime-labellable per trade, and `AF_REPAIRS_V1.json` →
`R3_regime_conditioning.conditional_map` carries three dials × four buckets for all 30 families.
For each mixture family, answer: which members carry the edge, is the carrier stable across
folds, and is there a **pre-declared** conditioning variable (state it before you look — AB's
dials: PERSISTENCE, VOL_REGIME, the session axis) under which the family coheres? Two named
cases to settle: the crypto donchian per-member split (DASH/ETH/XTZ/BTC positive vs
ADA/DOT/XRP/LTC negative — is that maturity/vintage, liquidity, or noise?), and `mx_nzdjpy`'s
dated 2025 break (permutation p 0.0005; the pre-declared PERSISTENCE gate failed, VOL_REGIME==hi
is post-hoc — test it out-of-sample by era rather than promoting it).

**4. The volume-surge stability shape (AF §5.2).** 6/6 members positive, constant composition,
band-stable, fails only fold stability ([+0.394, −0.131, −0.018, −0.090, +0.346]). Condition on
AB's spine: does a pre-declared regime dial explain the middle folds? If yes, the family admits
as a conditioned family with the look counted; if no, its row says exactly which regimes came
closest.

**5. `idxrev`'s inverse test** — AA's standing row, the one sleeve with genuinely no excursion
to keep (AD re-confirmed: best cell +0.0004). Re-simulated inverse (continuation on the same
trigger), not sign-flipped, per AF's method note. Cheap from stored intents; either direction is
a result.

**6. The conditioning map, consolidated.** Whatever admits, park-with-list, or stays open: one
artifact that AI and wave 9 can query — per family, per member, the dial/bucket surface with
fold-stability and look counts. AF built the substrate; you are making it decision-grade.

## Substrate

- `phase7/receipts/AF_FAMILY_TRADES.json.gz` (134,027 trades, reachability-flagged),
  `AF_REPAIRS_V1.json`, `FAMILY_ADMISSION_V1.json`.
- AB's regime spine artifacts (its result doc names the dials and their published bands).
- AG's spread model + `BROKER_TRUE_COSTS_V1.json`; the block-pair receipts its validation used.
- Bars `/Users/borr/GTOSActive/vps-bars-20260727/`; hydrate
  `research/operations/spread_model_2026_07_29/` per agreement §4.

## Deliverables

1. `phase8/receipts/ENTRY_HOUR_FRONTIER_V1.json` — the H4 re-entry before/after per member,
   gate verdicts at measured carry.
2. `phase8/receipts/SPREAD_MODEL_V2_VALIDATION.json` — the era×hour repair with its held-out
   evidence and the list of verdicts it moves.
3. `phase8/receipts/CONDITIONING_MAP_V1.json` — item 6.
4. Repair-queue rows appended (session `AH`); result doc with the §2 scoped receipt; every look
   in the ledger.

## Not yours

The VPS. Arming, tokens, gates, sleeve composition. Merging to `main`.
`config/agent_config.yaml`. Declaring the candidate-book family size (that is Borhen's, prepared
by AI).

Use your own judgment on scope and on whether anything above is wrong — and say so in your report
when you do.
