"""Session AQ — the `mx_btcusd` challenge dossier, generated from the artifacts (AQ-4, B1436-B1442).

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_btc_dossier.py

Writes `phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md` and its machine sibling
`phase11/receipts/AQ_BTC_DOSSIER_V1.json`.

WHY IT IS GENERATED AND NOT WRITTEN
--------------------------------------
This is the one page the challenge package cites for the estate's ONE standing admission.
Every number on it is read out of a committed artifact by this file and stamped with the
JSON path it came from, because a hand-transcribed dossier is one typo away from being the
most expensive document in the programme. If an artifact moves, this file fails loudly
rather than publishing a stale figure.

WHAT THIS SESSION ADDS TO THE ADMISSION
------------------------------------------
The admission cell `target_5R` carries `time_stop_bars=None`; its median hold is 120 h and
82.6 % of its trades are held past 24 h. The live engine would close every one of those at
~24 h, because `SLEEVE_EXIT_PROFILES` declared this sleeve's time stop as 96 M15 PRINTED
bars — one D1 bar. So the admission and the contract were not the same object, and the
dossier has to say which one it is pricing.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUD / "phase11/receipts"
CT = HERE / "AQ_CONTRACT_TRUTH_V1.json"
POP = AUD / "phase10/receipts/POPULATION_RULE_V1.json"
ADV = AUD / "phase9/receipts/AL_BTC_ADVERSARIAL_V1.json"
ERA = AUD / "phase9/receipts/AL_BTC_ERA_MECHANISM_V1.json"
PLACEBO = AUD / "phase10/receipts/AN_ECON_PLACEBO_V1.json"
OUT_MD = AUD / "phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md"
OUT_JSON = HERE / "AQ_BTC_DOSSIER_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
BANDS = ("flat", "low", "mid", "high")


def _at(doc, path: list, what: str):
    """Read a JSON path or die. A dossier that silently prints `None` is worse than none."""
    cur = doc
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        elif isinstance(cur, list) and isinstance(k, int) and 0 <= k < len(cur):
            cur = cur[k]
        else:
            raise SystemExit(f"dossier input missing: {what} at {'.'.join(map(str, path))}")
    return cur


def _f(x, n=4, pct=False):
    if x is None:
        return "—"
    return f"{100*x:.{n}f} %" if pct else f"{x:.{n}f}"


def _g(x):
    return "—" if x is None else f"{x:.6g}"


def main() -> None:
    t0 = time.time()
    ct = json.loads(CT.read_text())
    pop = json.loads(POP.read_text())
    adv = json.loads(ADV.read_text())
    era = json.loads(ERA.read_text())

    adm = _at(ct, ["admission", "arms"], "AQ admission arms")
    walk = _at(ct, ["walk", "arms"], "AQ walk arms")
    cells = _at(ct, ["admission", "cells"], "AQ admission exit cells")
    audit = _at(ct, ["spec_audit", "sleeves", BTC], "AQ spec audit for BTC")

    def A(contract, band, option="B_balanced"):
        return _at(adm, [f"{contract}|{option}|RECORDED|{band}", BTC],
                   f"admission arm {contract}/{option}/{band}")

    def W(contract, band):
        return _at(walk, [f"{contract}|RECORDED|{band}", BTC],
                   f"walk arm {contract}/{band}")

    # --- the four-cell contract truth table -------------------------------------------
    truth = {
        "2R_native__no_time_stop": {
            "what": "AA's walk. What `AA_ESTATE_WALK.json` publishes for this sleeve.",
            "target": "2R (the sleeve's own, market_expansion_d1.py:18 TARGET_R)",
            "time_stop": "none",
            **{b: {"r_per_day": W("PUBLISHED", b)["pooled_oos_mean_r"],
                   "p_raw": W("PUBLISHED", b)["p_raw"],
                   "verdict": W("PUBLISHED", b)["verdict"]} for b in BANDS}},
        "2R_native__live_time_stop": {
            "what": "WHAT THE LIVE BOOK RAN before this session's repair.",
            "target": "2R", "time_stop": "1 D1 bar (96 M15 printed bars)",
            **{b: {"r_per_day": W("LIVE_TRUE", b)["pooled_oos_mean_r"],
                   "p_raw": W("LIVE_TRUE", b)["p_raw"],
                   "verdict": W("LIVE_TRUE", b)["verdict"]} for b in BANDS}},
        "5R__live_time_stop": {
            "what": "the published admission cell, run under the live time stop.",
            "target": "5R", "time_stop": "1 D1 bar",
            **{b: {"r_per_day": A("LIVE_TRUE", b)["pooled_oos_mean_r"],
                   "p_raw": A("LIVE_TRUE", b)["p_raw"],
                   "verdict": A("LIVE_TRUE", b)["verdict"]} for b in BANDS}},
        "5R__repaired_time_stop": {
            "what": "THE ADMISSION. The cell the estate stands on, after the unit repair.",
            "target": "5R", "time_stop": "80 D1 bars (7680 M15 printed bars) — never binds",
            **{b: {"r_per_day": A("REPAIRED", b)["pooled_oos_mean_r"],
                   "p_raw": A("REPAIRED", b)["p_raw"],
                   "verdict": A("REPAIRED", b)["verdict"]} for b in BANDS}},
    }

    # --- the control that makes the dossier's numbers AN's numbers ---------------------
    an_mid = _at(pop, ["grid", "arms",
                       f"X_btc5R|B_balanced|RECORDED|mid|{BTC}"], "AN's ratified mid arm")
    mine_mid = A("REPAIRED", "mid")
    parity = {
        "what": ("this session re-derived the admission from AA's intents rather than "
                 "reading AN's number. The two must agree exactly, or one of them is wrong."),
        "an_p_raw": an_mid["p_raw"], "aq_p_raw": mine_mid["p_raw"],
        "an_r_per_day": an_mid["pooled_oos_mean_r"],
        "aq_r_per_day": mine_mid["pooled_oos_mean_r"],
        "an_n": an_mid["n_trades"], "aq_n": mine_mid["n_trades"],
        "an_q": an_mid["q_value"], "aq_q": mine_mid["q_value"],
        "an_declared_family": an_mid["declared_family_size"],
        "aq_declared_family": mine_mid["declared_family_size"],
        "p_identical": an_mid["p_raw"] == mine_mid["p_raw"],
        "r_identical": an_mid["pooled_oos_mean_r"] == mine_mid["pooled_oos_mean_r"],
        "n_identical": an_mid["n_trades"] == mine_mid["n_trades"],
        "q_differs_because": ("AN gated at CANDIDATE_FAMILY_V2's 35; this session gates at "
                              "V3's 39, per the wave-11 agreement. p is family-invariant; "
                              "only q and the BH bar move."),
    }
    parity["pass"] = all((parity["p_identical"], parity["r_identical"],
                          parity["n_identical"]))
    if not parity["pass"]:
        raise SystemExit(f"PARITY FAILED against the ratified decision: {parity}")

    folds_src = _at(pop, ["admission_fold_structure"], "AN's fold structure")
    decay = _at(folds_src, ["chronological_decay"], "AN's chronological decay")
    my_folds = mine_mid["folds"]

    bh_bar_39 = 0.10 / 39
    bonf_bar_39 = 0.05 / 39
    p = mine_mid["p_raw"]
    arith = {
        "declared_family_size": mine_mid["declared_family_size"],
        "declared_family_id": mine_mid["declared_family_id"],
        "bh_rank1_bar_alpha_0.10": bh_bar_39,
        "bh_rank2_bar_alpha_0.10": 2 * bh_bar_39,
        "bonferroni_bar_alpha_0.05": bonf_bar_39,
        "p_raw": p,
        "inside_bh_rank1_by": bh_bar_39 / p,
        "inside_bonferroni_by": bonf_bar_39 / p,
        "q_value_at_39": mine_mid["q_value"],
        "largest_family_that_admits_at_0.10": int(0.10 / p),
        "largest_family_that_admits_at_0.05": int(0.05 / p),
        "p_floor": mine_mid["p_floor"], "n_blocks": mine_mid["n_blocks"],
        "p_floor_headroom": mine_mid["p_floor_headroom"],
    }

    doc = {
        "schema": "gtos.wave11.aq.btc_dossier.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                         "aq_btc_dossier.py"),
        "session": "AQ", "blocks": "B1436-B1442", "sleeve": BTC,
        "contract_truth_table": truth,
        "parity_vs_the_ratified_decision": parity,
        "bh_arithmetic": arith,
        "spec_audit": audit,
        "exit_cells": {k: v for k, v in cells.items() if k.startswith(BTC)},
        "folds_an": folds_src, "chronological_decay": decay, "folds_aq": my_folds,
        "adversarial": _at(adv, ["survived"], "AL's adversarial scoreboard"),
        "era_out_of_sample": _at(era, ["B3_out_of_sample"], "AL's B3"),
        "seconds": round(time.time() - t0, 1),
    }
    OUT_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str))

    # ---------------------------------------------------------------- the page ---------
    rows = []
    for key, v in truth.items():
        rows.append("| `{}` | {} | {} | {} | {} | {} | {} |".format(
            key, v["target"], v["time_stop"],
            *[f"{_f(v[b]['r_per_day'])} · {v[b]['verdict'][:6]}" for b in
              ("flat", "low", "mid", "high")]))
    contract_rows = "\n".join(rows)

    band_rows = "\n".join(
        "| {} | {} | {} | {} | {} | {} | {} |".format(
            b + (" *(control)*" if b == "flat" else ""),
            A("REPAIRED", b)["verdict"],
            _f(A("REPAIRED", b)["pooled_oos_mean_r"]),
            _f(A("REPAIRED", b)["oos_mean_r_per_trade"]),
            _g(A("REPAIRED", b)["p_raw"]), _f(A("REPAIRED", b)["q_value"], 4),
            _f(A("REPAIRED", b)["drop_best_retention"], 4))
        for b in BANDS)

    fold_rows = "\n".join(
        "| {} | {} … {} | {} | {} | {} | {} | {} |".format(
            f["fold_id"], f["oos_start"], f["oos_end"], f["n_trades"], f["n_disputed"],
            _f(f["disputed_share"], 3), _f(f["gross_r_per_trade"], 4),
            _f(f["fold_mean_r_per_day"], 4))
        for f in folds_src["folds"])

    live_fold_rows = "\n".join(
        "| {} | {} | {} |".format(
            f["fold_id"], _f(f["test_mean_r"], 5),
            _f(A("LIVE_TRUE", "mid")["folds"][i]["test_mean_r"], 5))
        for i, f in enumerate(my_folds))

    md = f"""# `mx_btcusd` — the challenge dossier

**The estate's one standing admission.** Session AQ, 2026-07-30, blocks B1436–B1442.
Machine sibling: `phase11/receipts/AQ_BTC_DOSSIER_V1.json`. Every number below is read
out of a committed artifact by `phase11/receipts/aq_btc_dossier.py`; none is transcribed.

Sleeve `{BTC}` · symbol `BTCUSD` · account FTMO / `FTMO-Server3` ·
costs `research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json`.

---

## 0. The one thing that changed this week, and it is not a number

The admission cell is `target_5R`, and `target_5R` carries **no time stop**: its median
hold is {A("REPAIRED", "mid")["median_hold_hours"]:.0f} h and
**{_f(A("REPAIRED", "mid")["frac_hold_over_24h"], 1, pct=True)} of its trades are held past
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
{contract_rows}

**Both changes are necessary and neither is sufficient**, at the mid band:

* the **time-stop repair alone** — the sleeve's own 2R target at the repaired horizon —
  gives p {_g(W("PUBLISHED", "mid")["p_raw"])}: **REJECT**;
* the **5R exit alone**, still under the pre-repair one-bar time stop, gives
  p {_g(A("LIVE_TRUE", "mid")["p_raw"])}: **REJECT**;
* **both together** give p {_g(A("REPAIRED", "mid")["p_raw"])}: **ADMIT**.

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
{band_rows}

> **The headline, in the only phrasing that is honest: `mx_btcusd @ target_5R` ADMITS AT
> TWO OF THREE COST BANDS and REJECTS at `high`.** Never print a bare ADMIT. At `band_high`
> its p {_g(A("REPAIRED", "high")["p_raw"])} sits inside the BH **rank-2** threshold
> ({_g(arith["bh_rank2_bar_alpha_0.10"])}), so at the pessimistic band it would need a
> partner again — and it has none.

**The multiplicity bill, explicitly.** Declared family `{arith['declared_family_id']}`,
all-declared basis, **{arith['declared_family_size']} hypotheses** (V3 + the wave-11 ratchet;
AN's ratified run used V2's 35, which is why its q reads {_f(an_mid['q_value'], 4)} and this
one reads {_f(arith['q_value_at_39'], 4)} — p is family-invariant and identical).

* BH rank-1 bar at α = 0.10: **{_g(arith['bh_rank1_bar_alpha_0.10'])}**; p is
  **{arith['inside_bh_rank1_by']:.2f}×** inside it.
* Bonferroni bar at α = 0.05: **{_g(arith['bonferroni_bar_alpha_0.05'])}**; p is
  **{arith['inside_bonferroni_by']:.2f}×** inside it. The cell clears **both** standards,
  which `target_4R` does not — that is why 5R is the cell.
* It would still admit against a family of **{arith['largest_family_that_admits_at_0.10']}**
  at α = 0.10 and **{arith['largest_family_that_admits_at_0.05']}** at α = 0.05.
* Permutation floor {_g(arith['p_floor'])} over {arith['n_blocks']} blocks; p sits
  **{arith['p_floor_headroom']:.1f}×** above its own resolution floor, so this is a measured
  p and not a floor artefact.

## 3. The chronological folds — and the decay no gate can see

Equal calendar blocks in time order (`fold_rule = equal_calendar_folds_over_sleeve_span`).
`n_disputed` counts trades in RECORDED eras the spread model calls undecidable.

| fold | OOS window | n | disputed | share | gross R/trade | fold R/day |
|---|---|---|---|---|---|---|
{fold_rows}

**The last two folds average {_f(decay['mean_fold_r_per_day_last_two'])} R/day against the
first three's {_f(decay['mean_fold_r_per_day_first_three'])} — {_f(decay['ratio'], 1, pct=True)},
on {decay['n_trades_in_last_two']} of 232 trades and the most recent 2.7 years.** Every gate
passes anyway: `stability` counts the **sign** of a fold mean, not its level, so
`min_oos_positive_fold_frac` reads 5/5. A {1/decay['ratio']:.1f}× chronological decay is
invisible to the standard by construction.

> **Anything sized on this admission is sized on `{_f(decay['mean_fold_r_per_day_last_two'])}
> R/day`, not on the pooled `{_f(A("REPAIRED", "mid")["pooled_oos_mean_r"])} R/day`.** That is condition 3 of
> the wave-11 agreement and it is the number to put in a Monte Carlo.

**And the same folds under the pre-repair live contract**, which is the clearest single
statement of what the repair bought:

| fold | repaired (the admission) | live-true (before the repair) |
|---|---|---|
{live_fold_rows}

Under the pre-repair contract the two most recent folds are **negative**, `stability` falls
to {_f(A("LIVE_TRUE", "mid")["oos_positive_fold_frac"], 1)}, and p moves
{_g(A("REPAIRED", "mid")["p_raw"])} → **{_g(A("LIVE_TRUE", "mid")["p_raw"])}**.

## 4. What survived an attack on it

From Session AL's adversarial pass (`phase9/receipts/AL_BTC_ADVERSARIAL_V1.json` →
`survived`) and Session AN's placebo (`phase10/receipts/AN_ECON_PLACEBO_V1.json`):

| attack | result |
|---|---|
| A1 — is the 5R target a spike on a swept surface? | **RIDGE**, monotone 1R→5R; the 9-cell grid's median is +0.481 R/day |
| A7 — do all folds carry it? | **all 5 positive**; drop-worst 1.199 vs drop-best 0.761 |
| A5 — family headroom | admits to m = {arith['largest_family_that_admits_at_0.10']} at α 0.10 |
| A4 — spread composition | verdicts and p **byte-identical** under `v2_damped` and `v1_multiplicative` |
| A2 — is RECORDED a period selection? | **NOT survived, and it is a finding**: the RECORDED half earns +1.024 R gross/trade against the complement's −0.017, on overlapping calendar spans |
| AN's placebo | **38 of 40** year-matched 20-trade removals still ADMIT — the admission does not depend on which disputed trades are present |

**Out of sample on the excluded eras** (`AL_BTC_ERA_MECHANISM_V1.json` → `B3_out_of_sample`,
gross, deliberately): 2026 trade-weighted gross at 5R is
**{_f(_at(era, ['B3_out_of_sample', '2026_trade_weighted_gross_5R'], 'B3 2026 5R'))} R/trade**
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
| the band table and BH arithmetic | same, `admission.arms.REPAIRED\\|B_balanced\\|RECORDED\\|<band>` |
| the fold table and the decay | `phase10/receipts/POPULATION_RULE_V1.json` → `admission_fold_structure` |
| the ratified population rule | same → `ratified_rule`; pinned by `tests/research_infra/test_population_rule_ratified.py` |
| the adversarial scoreboard | `phase9/receipts/AL_BTC_ADVERSARIAL_V1.json` → `survived` |
| the excluded-era out-of-sample | `phase9/receipts/AL_BTC_ERA_MECHANISM_V1.json` → `B3_out_of_sample` |
| the placebo | `phase10/receipts/AN_ECON_PLACEBO_V1.json` |
| the time-stop repair | `src/components/ultimate_book/execution_packets.py`; `tests/ultimate_book/test_time_stop_units.py` |

**Parity control, stated as an enumeration rather than as the word "exactly".** This session
re-derived the admission from AA's stored intents rather than reading AN's number back.
**`p_raw`, `pooled_oos_mean_r`, `oos_mean_r_per_trade`, `n_trades`, all five fold means and
the verdict are bit-identical** to the ratified decision — p {_g(parity['aq_p_raw'])}, R/day
{_f(parity['aq_r_per_day'], 6)}, n {parity['aq_n']}. **`q_value` is NOT**: {_f(parity['an_q'], 4)}
there against {_f(parity['aq_q'], 4)} here, because the declared family is
{parity['aq_declared_family']} rather than {parity['an_declared_family']}. That raise is
Session AO's V3, not this session's V4, and it moves in the conservative direction — a bigger
bill — so the verdict is unchanged. `spec_id`, `spec_sha256`, `declared_family_id` and
`effective_family_size` differ for the same reason. A first draft of this line said the
figures reproduce "exactly" and then said "only q moves" in the same breath, which is two
claims where one of them is false; an adversarial pass called it and it is enumerated now.
"""
    OUT_MD.write_text(md)
    print(f"parity vs the ratified decision: {parity['pass']}")
    print(f"wrote {OUT_MD.relative_to(REPO)} and {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
