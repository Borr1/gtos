# `mx_btcusd` — the challenge dossier

**The estate's one standing admission.** Session AQ, 2026-07-30, blocks B1436–B1442.
Machine sibling: `phase11/receipts/AQ_BTC_DOSSIER_V1.json`. Every number below is read
out of a committed artifact by `phase11/receipts/aq_btc_dossier.py`; none is transcribed.

Sleeve `mx_btcusd_d1_donchian_20_breakout` · symbol `BTCUSD` · account FTMO / `FTMO-Server3` ·
costs `research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json`.

---

## 0. The one thing that changed this week, and it is not a number

The admission cell is `target_5R`, and `target_5R` carries **no time stop**: its median
hold is 120 h and
**82.3 % of its trades are held past
24 hours**.

Until 2026-07-30 the live engine would have closed every one of those at about 24 hours.
`SLEEVE_EXIT_PROFILES` declared this sleeve's time stop as **96 M15 printed bars** — and 96
is the M15-bars-per-D1-bar conversion *ratio*, not a horizon. So the live contract was one
D1 bar against the 80-D1-bar horizon the evidence is measured under.

**The admission was therefore not a property of the estate; it was a property of a repair
that had not landed.** It has now (`execution_packets.py`, B1404: 96 → 7680, pinned by
`tests/ultimate_book/test_time_stop_units.py`, nothing armed moved). This page prices the
repaired contract and shows what the other three cells look like, because a challenge
package that cites the admission without citing the repair is citing a contract nobody runs.

## 1. The contract truth table — RECORDED population, all four cost bands

`R/day` is `pooled_oos_mean_r`, net of broker-true cost, out-of-sample folds only.

| contract | target | time stop | flat *(control)* | low | mid | high |
|---|---|---|---|---|---|---|
| `2R_native__no_time_stop` | 2R (the sleeve's own, market_expansion_d1.py:18 TARGET_R) | none | 0.3967 · REJECT | 0.3910 · REJECT | 0.3894 · REJECT | 0.2857 · REJECT |
| `2R_native__live_time_stop` | 2R | 1 D1 bar (96 M15 printed bars) | 0.1246 · REJECT | 0.1188 · REJECT | 0.1172 · REJECT | 0.0136 · REJECT |
| `5R__live_time_stop` | 5R | 1 D1 bar | 0.1809 · REJECT | 0.1752 · REJECT | 0.1735 · REJECT | 0.0699 · REJECT |
| `5R__repaired_time_stop` | 5R | 80 D1 bars (7680 M15 printed bars) — never binds | 0.9891 · ADMIT | 0.9833 · ADMIT | 0.9817 · ADMIT | 0.8781 · REJECT |

**Both changes are necessary and neither is sufficient**, at the mid band:

* the **time-stop repair alone** — the sleeve's own 2R target at the repaired horizon —
  gives p 0.00639936: **REJECT**;
* the **5R exit alone**, still under the pre-repair one-bar time stop, gives
  p 0.0563944: **REJECT**;
* **both together** give p 0.00109989: **ADMIT**.

The admission is an interaction, not a sum. Session AL measured the same shape on the
population axis and called it superadditive; this is the exit-contract version of it.

## 2. The admission — `target_5R` on the repaired contract, band by band

The population rule is **RECORDED**, ratified by Borhen 2026-07-30
(`phase10/receipts/POPULATION_RULE_V1.json` → `ratified_rule`, test-pinned). `flat` is the
37-day snapshot charged to every era and is carried as a **control**, not as a band — Session
AG measured that its era bias has no single sign, so a cell that only wins at flat has not
been shown to win.

| band | verdict | R/day | R/trade | p_raw | q | drop-best retention |
|---|---|---|---|---|---|---|
| flat *(control)* | ADMIT | 0.9891 | 0.9147 | 0.0009999 | 0.0390 | 0.7759 |
| low | ADMIT | 0.9833 | 0.9093 | 0.00109989 | 0.0429 | 0.7754 |
| mid | ADMIT | 0.9817 | 0.9075 | 0.00109989 | 0.0429 | 0.7747 |
| high | REJECT | 0.8781 | 0.8058 | 0.00509949 | 0.1560 | 0.7188 |

> **The headline, in the only phrasing that is honest: `mx_btcusd @ target_5R` ADMITS AT
> TWO OF THREE COST BANDS and REJECTS at `high`.** Never print a bare ADMIT. At `band_high`
> its p 0.00509949 sits inside the BH **rank-2** threshold
> (0.00512821), so at the pessimistic band it would need a
> partner again — and it has none.

**The multiplicity bill, explicitly.** Declared family `bbd08a58c160:CANDIDATE_BOOK_V1`,
all-declared basis, **39 hypotheses** (V3 + the wave-11 ratchet;
AN's ratified run used V2's 35, which is why its q reads 0.0385 and this
one reads 0.0429 — p is family-invariant and identical).

* BH rank-1 bar at α = 0.10: **0.0025641**; p is
  **2.33×** inside it.
* Bonferroni bar at α = 0.05: **0.00128205**; p is
  **1.17×** inside it. The cell clears **both** standards,
  which `target_4R` does not — that is why 5R is the cell.
* It would still admit against a family of **90**
  at α = 0.10 and **45** at α = 0.05.
* Permutation floor 9.99905e-05 over 31 blocks; p sits
  **11.0×** above its own resolution floor, so this is a measured
  p and not a floor artefact.

## 3. The chronological folds — and the decay no gate can see

Equal calendar blocks in time order (`fold_rule = equal_calendar_folds_over_sleeve_span`).
`n_disputed` counts trades in RECORDED eras the spread model calls undecidable.

| fold | OOS window | n | disputed | share | gross R/trade | fold R/day |
|---|---|---|---|---|---|---|
| 1 | 2019-01-03 … 2020-05-07 | 36 | 15 | 0.417 | 1.3333 | 1.1341 |
| 2 | 2020-05-08 … 2021-09-11 | 42 | 38 | 0.905 | 1.8046 | 1.5118 |
| 3 | 2021-09-12 … 2023-01-16 | 26 | 0 | 0.000 | 2.1458 | 1.8663 |
| 4 | 2023-01-17 … 2024-05-21 | 30 | 0 | 0.000 | 0.6000 | 0.2838 |
| 5 | 2024-05-22 … 2025-09-25 | 50 | 12 | 0.240 | 0.4400 | 0.1124 |

**The last two folds average 0.1981 R/day against the
first three's 1.5041 — 13.2 %,
on 80 of 232 trades and the most recent 2.7 years.** Every gate
passes anyway: `stability` counts the **sign** of a fold mean, not its level, so
`min_oos_positive_fold_frac` reads 5/5. A 7.6× chronological decay is
invisible to the standard by construction.

> **Anything sized on this admission is sized on `0.1981
> R/day`, not on the pooled `0.9817 R/day`.** That is condition 3 of
> the wave-11 agreement and it is the number to put in a Monte Carlo.

**And the same folds under the pre-repair live contract**, which is the clearest single
statement of what the repair bought:

| fold | repaired (the admission) | live-true (before the repair) |
|---|---|---|
| 1 | 1.13409 | 0.38300 |
| 2 | 1.51183 | 0.15659 |
| 3 | 1.86633 | 0.46789 |
| 4 | 0.28384 | -0.07806 |
| 5 | 0.11237 | -0.06176 |

Under the pre-repair contract the two most recent folds are **negative**, `stability` falls
to 0.6, and p moves
0.00109989 → **0.0563944**.

## 4. What survived an attack on it

From Session AL's adversarial pass (`phase9/receipts/AL_BTC_ADVERSARIAL_V1.json` →
`survived`) and Session AN's placebo (`phase10/receipts/AN_ECON_PLACEBO_V1.json`):

| attack | result |
|---|---|
| A1 — is the 5R target a spike on a swept surface? | **RIDGE**, monotone 1R→5R; the 9-cell grid's median is +0.481 R/day |
| A7 — do all folds carry it? | **all 5 positive**; drop-worst 1.199 vs drop-best 0.761 |
| A5 — family headroom | admits to m = 90 at α 0.10 |
| A4 — spread composition | verdicts and p **byte-identical** under `v2_damped` and `v1_multiplicative` |
| A2 — is RECORDED a period selection? | **NOT survived, and it is a finding**: the RECORDED half earns +1.024 R gross/trade against the complement's −0.017, on overlapping calendar spans |
| AN's placebo | **38 of 40** year-matched 20-trade removals still ADMIT — the admission does not depend on which disputed trades are present |

**Out of sample on the excluded eras** (`AL_BTC_ERA_MECHANISM_V1.json` → `B3_out_of_sample`,
gross, deliberately): 2026 trade-weighted gross at 5R is
**0.1434 R/trade**
on quarters the population rule *excludes* — the edge is still positive where the rule does
not look.

## 5. The band's own caveat, and the 78 trades it lives in

RECORDED keeps 78 trades in quarters the spread model itself calls undecidable, one with a
band spanning 204,058×. Charged at the pessimistic end those 78 go from +0.776 to
**+0.527 R net per trade** on a gross of +1.020 — they still pay. The other 154 move 0.6 %
from low to high, so **the whole band sensitivity lives in those 78**. Honest footnote:
**13 of the 78 are charged more than a full risk unit of cost at `band_high`** (max 2.35 R),
which are not trades anyone would take; the mean is the right statistic for an expectancy
claim and it averages over some cells the pessimistic band prices out of existence.

Closure condition for the band caveat: **tick data for the nine undecidable BTCUSD quarters,
2018Q2–2025Q3** (`REPAIR_QUEUE_APPEND.jsonl`, `ADMISSION_IS_BAND_CONDITIONAL_STAMP_IT`).

## 6. What this admission is, and what it is not

- It is **eligibility, not allocation**. Registry confidence is **0.025**
  (`candidate_registry.py:330-334`), against `sub_xvol_pullback`'s 0.45 and `crypto`'s 0.85.
  OD-AI-5 left it there deliberately. At the allocator's own convention, admitting this
  sleeve into the funded book is **economically inert** — 0.136 %/month.
- Its lever is a **separate challenge account** (OD-AI-6), where a forward record accrues on
  real broker truth with downside bounded by the challenge fee.
- It has **zero live fills**, like every armed sleeve.
- AF **refuted** the diversification story: the same rule across the nine-symbol crypto class
  scores −0.185, dispersion ratio 4.74.
- **The exit contract must be named in any package that cites this page.** It is
  `target_5R` on the repaired time stop. The sleeve's own generator emits a 2R target
  (`market_expansion_d1.py:18`), and 2R does not admit at any band.

## 7. Provenance

| claim | artifact |
|---|---|
| the contract truth table, all four cells | `phase11/receipts/AQ_CONTRACT_TRUTH_V1.json` → `admission.arms`, `walk.arms` |
| the band table and BH arithmetic | same, `admission.arms.REPAIRED\|B_balanced\|RECORDED\|<band>` |
| the fold table and the decay | `phase10/receipts/POPULATION_RULE_V1.json` → `admission_fold_structure` |
| the ratified population rule | same → `ratified_rule`; pinned by `tests/research_infra/test_population_rule_ratified.py` |
| the adversarial scoreboard | `phase9/receipts/AL_BTC_ADVERSARIAL_V1.json` → `survived` |
| the excluded-era out-of-sample | `phase9/receipts/AL_BTC_ERA_MECHANISM_V1.json` → `B3_out_of_sample` |
| the placebo | `phase10/receipts/AN_ECON_PLACEBO_V1.json` |
| the time-stop repair | `src/components/ultimate_book/execution_packets.py`; `tests/ultimate_book/test_time_stop_units.py` |

**Parity control, stated as an enumeration rather than as the word "exactly".** This session
re-derived the admission from AA's stored intents rather than reading AN's number back.
**`p_raw`, `pooled_oos_mean_r`, `oos_mean_r_per_trade`, `n_trades`, all five fold means and
the verdict are bit-identical** to the ratified decision — p 0.00109989, R/day
0.981691, n 232. **`q_value` is NOT**: 0.0385
there against 0.0429 here, because the declared family is
39 rather than 35. That raise is
Session AO's V3, not this session's V4, and it moves in the conservative direction — a bigger
bill — so the verdict is unchanged. `spec_id`, `spec_sha256`, `declared_family_id` and
`effective_family_size` differ for the same reason. A first draft of this line said the
figures reproduce "exactly" and then said "only q moves" in the same breath, which is two
claims where one of them is false; an adversarial pass called it and it is enumerated now.
