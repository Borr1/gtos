"""m3-5 — read the three m3 artifacts and emit the owner-facing tables.

    python3 .../m3/m3_analyse.py

Writes `M3_RESULT_V1.json`. No measurement happens here; every number is read from
`M3_REGATE_V1.json`, `M3_ARMED_ECON_V1.json`, `M3_EXIT_CONTRACT_V1.json` and lane r1's
`R1_ESTATE_*`, and every table names the artifact it came from.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
R1 = HERE.parent / "r1"
OUT = HERE / "M3_RESULT_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
SUBMID = "sub_mid_dn_revert"


def main() -> int:
    regate = json.load(open(HERE / "M3_REGATE_V1.json"))
    econ = json.load(open(HERE / "M3_ARMED_ECON_V1.json"))
    exitc = json.load(open(HERE / "M3_EXIT_CONTRACT_V1.json"))
    r1d = json.load(open(R1 / "R1_ESTATE_DELTA_V1.json"))
    r1n = json.load(open(R1 / "R1_ESTATE_NET_V1.json"))
    grid = regate["grid"]

    def pick(**kw):
        out = [r for r in grid if all(r.get(k) == v for k, v in kw.items())]
        return out

    doc: dict = {
        "schema": "gtos.wave20.m3.result.v1",
        "lane": "m3 — what the wave-20 repair does to the money",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "inputs": {
            "regate": "M3_REGATE_V1.json", "econ": "M3_ARMED_ECON_V1.json",
            "exit_contract": "M3_EXIT_CONTRACT_V1.json",
            "r1_estate": "../r1/R1_ESTATE_DELTA_V1.json + R1_ESTATE_NET_V1.json"},
        "armed_sets": econ["armed_sets"],
        "controls": {
            "regate_C2_parity_vs_AN": {
                k: v for k, v in regate.get("C2_parity_vs_AN", {}).items() if k != "checks"},
            "econ_control_vs_AI_archive_book": econ["control_vs_AI_archive_book"],
            "exit_contract_C1_max_rel_err": exitc["control_C1_median_d_bps_max_rel_err"],
            "exit_contract_C2_vs_d2": exitc["control_C2_vs_d2"],
        },
    }

    # =================================================================================
    # Q1 — does the standing admission survive?
    # =================================================================================
    q1: dict = {"cell": f"{BTC} @ target_5R",
                "rule": regate["ratified_rule"],
                "family_sizes": regate["family_sizes"],
                "at_the_ratified_rule": {}, "robustness_across_the_grid": {}}
    BAND_OF = {"old": "mid", "qs_low": "low", "qs_mid": "mid", "qs_high": "high"}
    for walk in ("old", "qs_low", "qs_mid", "qs_high"):
        for charged in (True, False):
            band = BAND_OF[walk]
            rows = pick(sleeve=BTC, config="X_btc5R", walk=walk, spread_charged=charged,
                        population="RECORDED", band=band, option="B_balanced")
            if not rows:
                continue
            r = rows[0]
            q1["at_the_ratified_rule"][f"{walk}|spread_{'charged' if charged else 'removed'}"] = {
                k: r[k] for k in ("verdict", "n_trades", "pooled_oos_mean_r", "p_raw",
                                  "q_value", "failing_core_gates", "fold_means",
                                  "oos_positive_fold_frac", "drop_best_retention",
                                  "oos_mean_r_per_trade", "declared_family_size")}
    # every population x band x option, corrected walk, spread removed
    for pop in ("ALL_ERAS", "RECORDED", "DECIDABLE", "RECORDED_AND_DECIDABLE"):
        for opt in ("B_balanced", "A_strict"):
            cell = {}
            for walk, band in (("old", "mid"), ("qs_low", "low"), ("qs_mid", "mid"),
                               ("qs_high", "high")):
                for charged in (True, False):
                    rows = pick(sleeve=BTC, config="X_btc5R", walk=walk, band=band,
                                spread_charged=charged, population=pop, option=opt)
                    if rows:
                        cell[f"{walk}|{'charged' if charged else 'removed'}"] = {
                            "verdict": rows[0]["verdict"], "p_raw": rows[0]["p_raw"],
                            "q_value": rows[0]["q_value"],
                            "pooled": rows[0]["pooled_oos_mean_r"],
                            "n": rows[0]["n_trades"]}
            q1["robustness_across_the_grid"][f"{pop}|{opt}"] = cell
    adm = [r for r in grid if r["verdict"] == "ADMIT"]
    q1["admissions_anywhere_in_the_grid"] = {
        "n_arms": len(grid), "n_admit": len(adm),
        "by_cell": dict(collections.Counter(f"{r['sleeve']}@{r['exit'][r['sleeve']]}"
                                            for r in adm)),
        "by_walk": dict(collections.Counter(r["walk"] for r in adm)),
        "by_spread_convention": dict(collections.Counter(
            "charged" if r["spread_charged"] else "removed" for r in adm)),
        "by_population": dict(collections.Counter(r["population"] for r in adm)),
    }
    doc["Q1_does_the_standing_admission_survive"] = q1

    # =================================================================================
    # Q1b — the two co-judged cells, one of which is ARMED
    # =================================================================================
    q1b = {}
    for sleeve, cfg, exitname in ((XVOL, "X_btc5R", "target_4R"),
                                  (SUBMID, "X_btc5R", "reclocked")):
        cell = {}
        for walk, band in (("old", "mid"), ("qs_mid", "mid")):
            for charged in (True, False):
                rows = pick(sleeve=sleeve, config=cfg, walk=walk, band=band,
                            spread_charged=charged, population="RECORDED",
                            option="B_balanced")
                if rows:
                    r = rows[0]
                    cell[f"{walk}|{'charged' if charged else 'removed'}"] = {
                        k: r[k] for k in ("verdict", "n_trades", "pooled_oos_mean_r",
                                          "p_raw", "q_value", "failing_core_gates",
                                          "fold_means", "oos_positive_fold_frac",
                                          "drop_best_retention")}
        q1b[f"{sleeve}@{exitname}"] = cell
    doc["Q1b_the_co_judged_cells"] = q1b

    # =================================================================================
    # Q2 — the exit contract
    # =================================================================================
    t = exitc["table"]
    doc["Q2_does_the_exit_contract_finding_survive"] = {
        "population": exitc["population"], "windows": exitc["windows"],
        "levels": {a: {"target_2.0R": t[a]["target_2.0R"]["mean"],
                       "stop_only_horizon": t[a]["stop_only_horizon"]["mean"]}
                   for a in t},
        "paired_delta": {a: t[a]["paired_delta"] for a in t},
        "paired_delta_dayblock": {a: t[a]["paired_delta_dayblock"] for a in t},
        "frac_rows_where_the_two_contracts_differ": {
            a: t[a]["frac_rows_delta_nonzero"] for a in t},
        "months_positive": {
            a: sum(1 for m, v in exitc["per_month"].items() if (v[a]["delta"] or 0) > 0)
            for a in t},
        "per_month": exitc["per_month"],
        "the_arithmetic": {
            "correction_to_the_LEVEL_of_target_2R_fill": round(
                t["fill"]["target_2.0R"]["mean"] - t["old"]["target_2.0R"]["mean"], 6),
            "correction_to_the_PAIRED_DELTA_fill": round(
                t["fill"]["paired_delta"]["mean"] - t["old"]["paired_delta"]["mean"], 6),
            "correction_to_the_PAIRED_DELTA_level": round(
                t["level"]["paired_delta"]["mean"] - t["old"]["paired_delta"]["mean"], 6),
            "ratio_level_move_to_delta_move": (
                round(abs(t["fill"]["target_2.0R"]["mean"] - t["old"]["target_2.0R"]["mean"])
                      / abs(t["fill"]["paired_delta"]["mean"] - t["old"]["paired_delta"]["mean"]), 2)
                if t["fill"]["paired_delta"]["mean"] != t["old"]["paired_delta"]["mean"] else None),
        },
    }

    # =================================================================================
    # Q3 — do the ARMED sleeves' economics move enough to matter?
    # =================================================================================
    q3: dict = {"population": econ["population"], "per_sleeve": {}, "book": {}}
    for sleeve, rec in econ["per_sleeve"].items():
        if rec.get("absent_from_archive"):
            q3["per_sleeve"][sleeve] = rec
            continue
        g = rec["gross"]
        n = rec["net"]
        q3["per_sleeve"][sleeve] = {
            "n_trades": rec["n_trades"],
            "exit_contract_walked": rec["exit_contract_walked"],
            "registry_confidence": econ["registry_confidence"].get(sleeve),
            "gross_r_per_trade": {"published": g["old"]["mean"],
                                  "corrected_low": g["qs_low"]["mean"],
                                  "corrected_mid": g["qs_mid"]["mean"],
                                  "corrected_high": g["qs_high"]["mean"],
                                  "delta_mid": round(g["qs_mid"]["mean"] - g["old"]["mean"], 6),
                                  "pct_of_published_mid": (
                                      round(100 * (g["qs_mid"]["mean"] - g["old"]["mean"])
                                            / abs(g["old"]["mean"]), 2)
                                      if g["old"]["mean"] else None)},
            "net_r_per_day": {
                "published_convention": n["old"]["spread_charged"],
                "corrected_walk_spread_removed": n["qs_mid"]["spread_removed"],
                "corrected_walk_spread_charged_conservative":
                    n["qs_mid"]["spread_charged"],
                "old_flat_snapshot_control": n["old_flat_snapshot_control"]["spread_charged"],
            },
        }
    for label, b in econ["book"].items():
        q3["book"][label] = {"sleeves": b["sleeves"], "arms": {}}
        for k, v in b["arms"].items():
            q3["book"][label]["arms"][k] = {
                "mean_r_per_book_day": v["mc"]["cell"]["mean_r_per_book_day"],
                "book_days": v["mc"]["cell"]["book_days"],
                "daily": v["daily"],
                "FTMO_P2_p_pass": v["mc"]["FTMO"]["P2_BOTH_PHASES"]["p_pass"],
                "FTMO_PH1_p_pass": v["mc"]["FTMO"]["L4_FIRM_TRUE_PH1"]["p_pass"],
                "FTMO_P2_monthly_pct": v["mc"]["FTMO"]["P2_BOTH_PHASES"].get(
                    "monthly_pct_calendar"),
                "redacted_account_P2_p_pass": v["mc"]["redacted_account"]["P2_BOTH_PHASES"]["p_pass"],
                "redacted_account_PH1_p_pass": v["mc"]["redacted_account"]["L4_FIRM_TRUE_PH1"]["p_pass"],
            }
    doc["Q3_armed_economics"] = q3

    # =================================================================================
    # Q4 — the corrections list, assembled from the artifacts
    # =================================================================================
    ps = r1d["per_sleeve"]
    pn = r1n["per_sleeve"]
    rows = []
    for s in sorted(ps):
        a, b = ps[s], pn.get(s, {})
        rows.append({
            "sleeve": s, "n": a["n"],
            "gross_published": a["old"]["mean"],
            "gross_corrected_mid": a["new_mid"]["mean"],
            "gross_delta": a["delta_mid"]["mean"],
            "gross_sign_flip": (a["old"]["mean"] > 0) != (a["new_mid"]["mean"] > 0),
            "net_published": (b.get("net_published") or {}).get("mean"),
            "net_corrected": (b.get("net_corrected") or {}).get("mean"),
            "exit_reason_changed": a["exit_reason_changed"],
            "exit_reason_changed_frac": a["exit_reason_changed_frac"],
            "exit_policy": a["exit_policy"],
        })
    rows.sort(key=lambda r: r["gross_delta"])
    doc["Q4_estate_restatement_every_sleeve"] = {
        "source": "lane r1's R1_ESTATE_DELTA_V1 / R1_ESTATE_NET_V1, re-tabulated",
        "pooled": {"gross_published": r1n["pooled"]["gross_old"]["mean"],
                   "gross_corrected": r1n["pooled"]["gross_new"]["mean"],
                   "net_published": r1n["pooled"]["net_published"]["mean"],
                   "net_corrected": r1n["pooled"]["net_corrected"]["mean"],
                   "n": r1n["pooled"]["gross_old"]["n"]},
        "n_sleeves_gross_sign_flip": sum(1 for r in rows if r["gross_sign_flip"]),
        "rows": rows,
    }

    doc["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print("WROTE", OUT)
    print(json.dumps(doc["Q1_does_the_standing_admission_survive"]["at_the_ratified_rule"],
                     indent=1))
    print(json.dumps(doc["Q2_does_the_exit_contract_finding_survive"]["the_arithmetic"],
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
