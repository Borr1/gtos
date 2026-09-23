"""Append Session AF's rows to the shared repair queue, in AA's schema.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/af_repair_rows.py

WHAT GOES IN, AND WHAT DELIBERATELY DOES NOT
----------------------------------------------
The wave-7 agreement §6.5: *"Repair-queue updates append, never overwrite. Add your rows
beside AA's with your session id."* So these go into `phase6/receipts/REPAIR_QUEUE_V1.json`.

What goes in is one row per FAMILY (30), one per named work-list member, and one per
cross-cutting finding. What does NOT go in is a row per member cell: 246 rows carrying the
full diagnostics blob would take a 639 KB shared artifact past 8 MB and make it unusable
for the three other sessions appending to it this wave. **That is a cap and it is not
silent** — the complete 276-sleeve diagnosed queue is committed beside it as
`phase7/receipts/AF_REPAIR_QUEUE_FULL.json.gz`, and every row here points at it.

Idempotent: re-running replaces AF's rows rather than duplicating them.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
SHARED = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_V1.json"
MINE = HERE / "REPAIR_QUEUE_AF.json"
FULL = "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AF_REPAIR_QUEUE_FULL.json.gz"


def rows() -> list[dict]:
    adm = json.loads((HERE / "FAMILY_ADMISSION_V1.json").read_text())
    rep = json.loads((HERE / "AF_REPAIRS_V1.json").read_text())
    disp = rep["R8_best_cell_and_dilution"]["dilution"]["by_family"]
    era = rep["R7_era_validity"]["by_family"]
    rec = rep["R7_era_validity"]["rewalk"]
    out: list[dict] = []

    for f, v in sorted(adm["families"].items()):
        d = disp.get(f, {})
        e = era.get(f, {})
        r = rec.get(f + "_recorded_eras", {})
        ratio = d.get("ic_dispersion_ratio")
        # The prescription follows from WHY the family failed, and the dispersion ratio is
        # what tells the two apart: a mixture cannot be repaired by more pooling.
        if ratio is not None and ratio > 1.0:
            pres, comp = "MEMBER_CONDITIONING_NOT_BREADTH", "symbol surface"
            act = (f"cross-member SD of mean gross R is {d['cross_member_sd']} against a "
                   f"family mean of {d['family_mean_of_member_means']} (ratio {ratio}), so "
                   f"the members are a MIXTURE and equal-weight pooling dilutes instead of "
                   f"adding breadth. Do not ask for more symbols. Ask which member carries "
                   f"the edge and why — best {max(d['member_mean_r_gross'], key=d['member_mean_r_gross'].get)} "
                   f"at {max(d['member_mean_r_gross'].values())}, worst "
                   f"{min(d['member_mean_r_gross'].values())}.")
        elif (v.get("pooled_oos_mean_r_mid") or -1) > 0:
            pres, comp = "SAMPLE_OR_STABILITY", "entry"
            act = (f"members are coherent (IC dispersion ratio {ratio}, "
                   f"{d.get('n_members_positive')}/{d.get('n_members')} positive) and the "
                   f"pooled mean is +{v['pooled_oos_mean_r_mid']:.4f} R/day at raw "
                   f"p {v['p_raw_mid']:.4f}. Pooling is the right instrument here; what is "
                   f"missing is evidence, not breadth. {v['first_reason_mid']}")
        else:
            pres, comp = "PARK_WITH_LIST", "mechanism x class"
            act = (f"negative on the whole class at every band "
                   f"({v['pooled_oos_mean_r_by_band']}). Park with the conditioning map in "
                   f"AF_REPAIRS_V1.json R3.conditional_map[{f}].")
        out.append({
            "sleeve": f, "session": "AF", "verdict": v["verdict_at_mid"],
            "prescription": pres, "component": comp, "gate": "significance",
            "margin": None, "is_primary": True, "action": act,
            "evidence": {
                "n_members": v["n_members"], "n_trades": v["n_trades"],
                "window": v["window"],
                "pooled_oos_mean_r_by_band": v["pooled_oos_mean_r_by_band"],
                "p_raw_mid": v["p_raw_mid"], "q_mid": v["q_mid"],
                "band_unstable": v["band_unstable"],
                "best_member_q_mid": v["best_member_q_mid"],
                "family_beats_best_member": v["family_beats_best_member"],
                "ic_dispersion_ratio": ratio,
                "era_recorded_frac": e.get("recorded_frac"),
                "mean_spread_multiple_vs_modern_base": e.get(
                    "mean_total_spread_multiple_vs_modern_base"),
                "recorded_era_rewalk": {k: r.get(k) for k in
                                        ("n_trades", "pooled_oos_mean_r", "p_raw",
                                         "verdict")} if r else None,
                "full_diagnostics": FULL,
            },
        })

    lad = rep["R8_best_cell_and_dilution"]["intersection_cell"]["rows"]
    out.append({
        "sleeve": "mx_btcusd_d1_donchian_20_breakout", "session": "AF",
        "verdict": "REJECT", "prescription": "BREADTH_REFUTED_ADMIT_ON_OWN_EVIDENCE",
        "component": "symbol surface", "gate": "significance", "margin": None,
        "is_primary": True,
        "action": (
            "AA routed this here as a BREADTH row. Breadth was run and it makes the sleeve "
            "WORSE at every step: BTCUSD alone raw p 0.0064, the three authored crypto "
            "donchian tags 0.0461, the nine-symbol archive class 0.0834, and 0.4442 once "
            "the unvalidated deep-history eras are charged. Stop asking for more symbols. "
            "Its own evidence STRENGTHENED under an outcome-independent cost restriction "
            "(era_class == RECORDED): +0.3894 R/day OOS on n=232, 80 % folds positive, raw "
            "p 0.0064 against W's 0.0120. What it needs is a family bill it can pay — "
            "BH alpha=0.20 admits it against <= 31 looks, Bonferroni alpha=0.05 against "
            "<= 8 — which is an owner decision about what the candidate book's family IS, "
            "not a research question. Its exit/carry repair (AA: ADMIT at zero carry, "
            "q 0.048) remains with Session AD."),
        "evidence": {"ladder": lad,
                     "btcusd_standalone_all_eras_mid": adm["runs"][
                         "member|C_exploratory|mid"]["rows"][
                         "mxf_donchian_20_breakout_btcusd_d1"],
                     "full_diagnostics": FULL},
    })

    p = rep["R1_production_surface"]["sets"]
    out.append({
        "sleeve": "crypto", "session": "AF", "verdict": "REJECT",
        "prescription": "OUT_OF_WINDOW_POSITIVE_NEEDS_SAMPLE", "component": "symbol surface",
        "gate": "significance", "margin": None, "is_primary": True,
        "action": (
            "The armed book's largest edge, measured on its OWN production surface over the "
            "whole archive for the first time: +0.0869 R/day OOS, 60 % folds positive, raw "
            "p 0.3001, n=182 (2017-02..2026-07). POSITIVE out of the window that selected "
            "it, which is the first such number this sleeve has. The class expansion the "
            "plan asked for does NOT de-risk it — the nine-symbol crypto class scores "
            "-0.1849 with an IC dispersion ratio of 4.74 and a best-to-worst spread of "
            "1.80 R, so the cluster claim is refuted rather than unproven. Route: sample, "
            "not breadth."),
        "evidence": {"production_surface": p["prod_crypto_ac60_BTC_DASH"],
                     "class_family": adm["families"][
                         "fam_crypto_h4_donchian_ac60_crypto_h4"]["pooled_oos_mean_r_mid"],
                     "ic_dispersion_ratio": disp[
                         "fam_crypto_h4_donchian_ac60_crypto_h4"]["ic_dispersion_ratio"],
                     "member_means": disp[
                         "fam_crypto_h4_donchian_ac60_crypto_h4"]["member_mean_r_gross"],
                     "full_diagnostics": FULL},
    })
    out.append({
        "sleeve": "energy_agri", "session": "AF", "verdict": "REJECT",
        "prescription": "DATA_CAPTURE_NATGAS_AND_AGRI", "component": "symbol surface",
        "gate": "significance", "margin": None, "is_primary": True,
        "action": (
            "The armed four's weakest statistical case, and its mechanism DOES carry: "
            "+0.4571 R/day OOS on its own class at mid band, the strongest pooled mean in "
            "the whole 30-family grid, IC dispersion ratio 0.117 with 3 of 3 members "
            "positive — the most coherent family measured this session. It fails on SAMPLE, "
            "not on sign: 76 trades, one fold with zero, and NATGAS_cash unpriceable so the "
            "verdict is on 2 of 3 symbols. Breadth cannot fix it because the class is three "
            "symbols wide. What would: (1) a NATGAS.cash COMMISSION — its SPREAD is already "
            "measured (the 2026-07-29 tick export populated spread_price.by_session), and "
            "cost_r refuses on commission.kind='unknown', 'no deal rows for this symbol and "
            "no measured peer in its class'. So this is neither a cost-artifact re-run nor a "
            "tick capture: it needs a deal row on either account, or a signed energy-class "
            "peer transfer of the kind AA's B603 used for FTMO oil ($5.00/lot TRANSFERRED "
            "from redacted_account's MEASURED USOUSD/UKOUSD) — which is not available for gas "
            "because redacted_account carries no gas instrument in the artifact's 76. HEATOIL.c is "
            "in the same state; (2) CORN.c / COTTON.c bars, which the archive does not hold "
            "and which are the sleeve's own authored-but-untradeable legs (AA §3.2)."),
        "evidence": {"production_surface": p["prod_energy_fvg_USOIL_UKOIL"],
                     "class_family": adm["families"]["fam_energy_fvg_retest_energy_h4"],
                     "ic_dispersion": disp["fam_energy_fvg_retest_energy_h4"],
                     "full_diagnostics": FULL},
    })

    r5 = rep["R5_nzdjpy_break"]
    out.append({
        "sleeve": "mx_nzdjpy_d1_donchian_20_breakout", "session": "AF", "verdict": "REJECT",
        "prescription": "REGIME_GATE", "component": "regime gate", "margin": None,
        "gate": "expectancy", "is_primary": True,
        "action": (
            f"The break is dated and it beats its own null: splitting on the year axis, "
            f"{r5['best_split']['cut_year']} maximises |mean before - mean after| at "
            f"{r5['best_split']['abs_delta']} R "
            f"(+{r5['best_split']['mean_before']:.4f} on n={r5['best_split']['n_before']} "
            f"before, {r5['best_split']['mean_after']:.4f} on "
            f"n={r5['best_split']['n_after']} after), permutation p "
            f"{r5['best_split']['null_p']} over 2,000 shuffles. So this is not a 26-year "
            f"decay, it is a two-year collapse. The PRE-DECLARED conditioning variable — "
            f"a breakout wants a persistent tape, `crypto.py:25`'s own gate — does NOT "
            f"rescue it (PERSISTENCE==trend: -0.1953, p 0.9011). The post-hoc best is "
            f"VOL_REGIME==hi (+0.2684, p 0.1005, n=81), which is mechanically sensible for "
            f"a breakout and is offered as a conditioning-map entry for Session AB, NOT as "
            f"a significance claim."),
        "evidence": {"by_year": r5["by_year"], "best_split": r5["best_split"],
                     "dial_buckets": r5["dial_buckets"],
                     "gated_rewalk": r5["gated_rewalk"]},
    })

    r4 = rep["R4_session_filter_ceiling"]["families"]
    out.append({
        "sleeve": "mx_cadjpy_d1_volume_surge_reversal", "session": "AF", "verdict": "REJECT",
        "prescription": "COST_GEOMETRY_ENTRY_HOUR", "component": "session", "margin": None,
        "gate": "expectancy", "is_primary": True,
        "action": (
            "Reproduced at -0.0017 R/day flat (the prompt's 'closest in the whole map') and "
            "-0.2910 charged its own eras, independently of AG's driver, which read "
            "-0.0024 -> -0.3252. The named repair — AG's 13x-38x broker-hour-00 spread — is "
            "REAL and it is the dominant cost: a D1 bar closes at broker 00:00, this family "
            "enters at that close, and re-pricing the same trades two hours later removes "
            f"{r4['fam_volume_surge_reversal_fx_d1']['mean_spread_r_saved_by_plus2h']:.4f} R "
            f"of "
            f"{r4['fam_volume_surge_reversal_fx_d1']['mean_total_cost_r_at_entry_hour']:.4f} "
            "R of modelled cost across the FX volume-surge family. BUT most of that charge "
            "is itself an unvalidated extrapolation (see the ERA_MODEL row), so the ceiling "
            "is not the gain. The measurable next step is a real re-entry: the archive holds "
            "H4 bars for every FX symbol, so entering at the first H4 close after the D1 "
            "decision (broker 04:00) can be simulated end to end, changing entry price and "
            "R rather than only the spread charge. That is the honest test and it is one "
            "session's work."),
        "evidence": {"fx_families": {k: v for k, v in r4.items() if "fx" in k},
                     "member_snapshot_vs_mid": {
                         "snapshot": adm["runs"]["member|C_exploratory|snapshot"]["rows"][
                             "mxf_volume_surge_reversal_cadjpy_d1"],
                         "mid": adm["runs"]["member|C_exploratory|mid"]["rows"][
                             "mxf_volume_surge_reversal_cadjpy_d1"]}},
    })

    out.append({
        "sleeve": "spread_model_v1", "session": "AF", "verdict": "NOT_EVALUABLE",
        "prescription": "ERA_MODEL_PRODUCT_UNVALIDATED", "component": "cost geometry",
        "gate": "cost_coverage", "margin": None, "is_primary": True,
        "action": (
            "`spread_price` composes anchor x era_ratio x hour-of-week multiplicatively and "
            "each factor was validated ALONE. Their product reaches 198x the modern base on "
            "NZDUSD in the 2000s (era 13.7 x hour 14.4), charging spread_r 1.78 — 178 % of "
            "the risk unit — and 880x at the maximum across the FX D1 families, which carry "
            "a mean multiple of 71-79x with only 44 % of their trades in RECORDED eras. AG "
            "§10 item 1 already says the pre-2010 FX eras are SCHEDULE-class and "
            "unvalidated; what is new is that multiplying two unvalidated multipliers was "
            "never named as its own risk. Non-FX classes are unaffected (mean multiple "
            "0.44-0.75, and fourteen instruments do not quote at the rollover at all), "
            "which R4 reproduces independently as a ~0.000 R hour saving on metals, "
            "indices, energy and crypto. Interim treatment used here and available to "
            "everyone: restrict to era_class == RECORDED, which is outcome-independent for "
            "exactly the reason `coverage_policy='restrict_to_priced'` is. Route: AG's lane."),
        "evidence": {"by_family": era, "rewalk": rec},
    })
    return out


def main() -> None:
    rs = rows()
    MINE.write_text(json.dumps({
        "schema": "gtos.walkforward.repair_queue.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session": "AF", "run_label": "AF family expansion @ mid band, C_exploratory",
        "note": ("one row per family plus the named work-list members and the cross-cutting "
                 "findings. The complete 276-sleeve diagnosed queue is " + FULL),
        "rows": rs}, indent=1, default=str))
    shared = json.loads(SHARED.read_text())
    keep = [r for r in shared["rows"] if r.get("session") != "AF"]
    dropped = len(shared["rows"]) - len(keep)
    shared["rows"] = keep + rs
    shared.setdefault("also_at", {})
    shared["also_at"]["AF"] = {
        "session": "AF", "rows": len(rs), "appended_utc": dt.datetime.now(
            dt.timezone.utc).isoformat(),
        "full_member_level_queue": FULL,
        "note": ("AF appends family-level rows and its named members; the per-member cells "
                 "(246) live in the gzipped full queue because 246 diagnostics blobs would "
                 "make this shared artifact unusable for the sessions appending beside it")}
    SHARED.write_text(json.dumps(shared, indent=1, default=str))
    print(f"wrote {MINE.relative_to(REPO)} ({len(rs)} rows)")
    print(f"appended {len(rs)} AF rows to {SHARED.relative_to(REPO)} "
          f"(replaced {dropped} from a prior run); total now {len(shared['rows'])}")


if __name__ == "__main__":
    main()
