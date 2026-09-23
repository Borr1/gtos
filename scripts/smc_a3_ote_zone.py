#!/usr/bin/env python3
"""SMC A3: OTE Zone validation analysis from displacement database."""

import json
import datetime
from pathlib import Path
from scipy.stats import chi2_contingency
import numpy as np

BASE = Path("/Users/borr/Documents/trading/gold-agent/knowledge_base_backtest/analysis")
DB_PATH = BASE / "displacement_database_20260403_0030.json"
DAY_PATH = BASE / "edge_discovery_d1unclear_20260405.json"
OUT_PATH = BASE / "smc_ote_zone_20260405.json"


def load_data():
    with open(DB_PATH) as f:
        db = json.load(f)
    with open(DAY_PATH) as f:
        day_raw = json.load(f)
    day_cls = {
        r["date"]: r
        for r in day_raw["day_classifications"]
        if r["symbol"] == "XAUUSD"
    }
    return db, day_cls


def grp_stats(rows, label=""):
    n = len(rows)
    if n == 0:
        return {"n": 0, "cont_3h_rate": None, "avg_mfe_3h": None, "avg_mae_3h": None, "flag": "EMPTY"}
    cont = sum(1 for r in rows if r.get("cont_3h"))
    mfe = [r["mfe_3h"] for r in rows if r.get("mfe_3h") is not None]
    mae = [r["mae_3h"] for r in rows if r.get("mae_3h") is not None]
    result = {
        "n": n,
        "cont_3h_rate": round(cont / n, 4),
        "avg_mfe_3h": round(np.mean(mfe), 3) if mfe else None,
        "avg_mae_3h": round(np.mean(mae), 3) if mae else None,
    }
    if n < 30:
        result["flag"] = "LOW_N"
    return result


def chi2_test(group_a, group_b, label=""):
    """Chi-squared on cont_3h between two groups."""
    a_yes = sum(1 for r in group_a if r.get("cont_3h"))
    a_no = len(group_a) - a_yes
    b_yes = sum(1 for r in group_b if r.get("cont_3h"))
    b_no = len(group_b) - b_yes
    table = [[a_yes, a_no], [b_yes, b_no]]
    if min(a_yes + a_no, b_yes + b_no) == 0:
        return {"chi2": None, "p_value": None, "table": table, "flag": "EMPTY_GROUP"}
    chi2, p, dof, _ = chi2_contingency(table)
    result = {
        "chi2": round(chi2, 4),
        "p_value": round(p, 6),
        "dof": dof,
        "table": table,
        "significant_005": p < 0.05,
    }
    if min(len(group_a), len(group_b)) < 30:
        result["flag"] = "LOW_N"
    return result


def is_d1_aligned(row):
    return (row.get("d1_dir") == "bullish" and row.get("direction") == "bullish") or \
           (row.get("d1_dir") == "bearish" and row.get("direction") == "bearish")


def analyze_subset(rows, day_cls, label="all"):
    """Full analysis on a subset of rows."""
    ote = [r for r in rows if r.get("in_ote")]
    not_ote = [r for r in rows if not r.get("in_ote")]

    # --- 1. OTE vs not OTE ---
    ote_vs = {
        "in_ote": grp_stats(ote),
        "not_in_ote": grp_stats(not_ote),
    }

    # --- 2. Chi-squared ---
    chi = chi2_test(ote, not_ote, "ote_vs_not_ote")

    # --- 3. Premium/Discount interaction ---
    def pd_key(r):
        if r.get("in_disc"):
            return "discount"
        elif r.get("in_prem"):
            return "premium"
        else:
            return "neutral"

    pd_groups = {}
    for r in rows:
        ote_label = "OTE" if r.get("in_ote") else "notOTE"
        zone = pd_key(r)
        key = f"{ote_label}_{zone}"
        pd_groups.setdefault(key, []).append(r)

    pd_interaction = {k: grp_stats(v) for k, v in sorted(pd_groups.items())}

    # Sweet-spot chi-squared tests
    pd_chi = {}
    if "OTE_discount" in pd_groups and "OTE_premium" in pd_groups:
        pd_chi["OTE_discount_vs_OTE_premium"] = chi2_test(
            pd_groups["OTE_discount"], pd_groups["OTE_premium"]
        )
    if "OTE_discount" in pd_groups and "OTE_neutral" in pd_groups:
        pd_chi["OTE_discount_vs_OTE_neutral"] = chi2_test(
            pd_groups["OTE_discount"], pd_groups["OTE_neutral"]
        )

    # --- 4. D1 alignment interaction ---
    # Add d1_clear info
    for r in rows:
        date = r.get("date")
        dc = day_cls.get(date)
        r["_d1_clear"] = dc["d1_clear"] if dc else None

    d1_groups = {}
    for r in rows:
        ote_label = "OTE" if r.get("in_ote") else "notOTE"
        aligned = is_d1_aligned(r)
        d1_label = "d1_aligned" if aligned else "not_d1_aligned"
        key = f"{ote_label}_{d1_label}"
        d1_groups.setdefault(key, []).append(r)

    d1_interaction = {k: grp_stats(v) for k, v in sorted(d1_groups.items())}

    # Chi-squared: OTE+aligned vs OTE+not_aligned
    d1_chi = {}
    if "OTE_d1_aligned" in d1_groups and "OTE_not_d1_aligned" in d1_groups:
        d1_chi["OTE_aligned_vs_OTE_not_aligned"] = chi2_test(
            d1_groups["OTE_d1_aligned"], d1_groups["OTE_not_d1_aligned"]
        )
    # Best vs worst
    if "OTE_d1_aligned" in d1_groups and "notOTE_not_d1_aligned" in d1_groups:
        d1_chi["OTE_aligned_vs_notOTE_not_aligned"] = chi2_test(
            d1_groups["OTE_d1_aligned"], d1_groups["notOTE_not_d1_aligned"]
        )

    # Also: d1_clear interaction (OTE + d1_clear)
    d1c_groups = {}
    for r in rows:
        ote_label = "OTE" if r.get("in_ote") else "notOTE"
        clear = r.get("_d1_clear")
        if clear is None:
            cl = "unknown"
        elif clear:
            cl = "d1_clear"
        else:
            cl = "d1_unclear"
        key = f"{ote_label}_{cl}"
        d1c_groups.setdefault(key, []).append(r)

    d1_clear_interaction = {k: grp_stats(v) for k, v in sorted(d1c_groups.items())}

    # --- 5. KZ interaction ---
    kz_groups = {}
    for r in rows:
        ote_label = "OTE" if r.get("in_ote") else "notOTE"
        kz_label = "KZ" if r.get("kz") else "notKZ"
        key = f"{ote_label}_{kz_label}"
        kz_groups.setdefault(key, []).append(r)

    kz_interaction = {k: grp_stats(v) for k, v in sorted(kz_groups.items())}

    kz_chi = {}
    if "OTE_KZ" in kz_groups and "OTE_notKZ" in kz_groups:
        kz_chi["OTE_KZ_vs_OTE_notKZ"] = chi2_test(
            kz_groups["OTE_KZ"], kz_groups["OTE_notKZ"]
        )
    if "OTE_KZ" in kz_groups and "notOTE_notKZ" in kz_groups:
        kz_chi["OTE_KZ_vs_notOTE_notKZ"] = chi2_test(
            kz_groups["OTE_KZ"], kz_groups["notOTE_notKZ"]
        )

    # --- 6. Session split ---
    session_groups = {}
    for r in rows:
        sess = r.get("session", "unknown")
        ote_label = "OTE" if r.get("in_ote") else "notOTE"
        key = f"{sess}_{ote_label}"
        session_groups.setdefault(key, []).append(r)

    session_split = {k: grp_stats(v) for k, v in sorted(session_groups.items())}

    return {
        "n_total": len(rows),
        "ote_vs_not_ote": ote_vs,
        "chi_squared_ote_vs_not": chi,
        "premium_discount_interaction": pd_interaction,
        "premium_discount_chi": pd_chi,
        "d1_alignment_interaction": d1_interaction,
        "d1_alignment_chi": d1_chi,
        "d1_clear_interaction": d1_clear_interaction,
        "kz_interaction": kz_interaction,
        "kz_chi": kz_chi,
        "session_split": session_split,
    }


def build_verdict(all_res, disc_res, val_res):
    """Generate verdict summary."""
    points = []

    # OTE edge
    ote_rate = all_res["ote_vs_not_ote"]["in_ote"]["cont_3h_rate"]
    not_rate = all_res["ote_vs_not_ote"]["not_in_ote"]["cont_3h_rate"]
    chi_p = all_res["chi_squared_ote_vs_not"]["p_value"]
    delta = round(ote_rate - not_rate, 4) if ote_rate and not_rate else None

    points.append(f"OTE cont_3h={ote_rate:.1%} vs non-OTE={not_rate:.1%} (delta={delta}, p={chi_p})")

    if chi_p is not None and chi_p < 0.05:
        points.append("OTE effect is statistically significant (p<0.05)")
    else:
        points.append("OTE effect is NOT statistically significant")

    # Validation hold
    if val_res and val_res["ote_vs_not_ote"]["in_ote"]["n"] >= 30:
        v_ote = val_res["ote_vs_not_ote"]["in_ote"]["cont_3h_rate"]
        v_not = val_res["ote_vs_not_ote"]["not_in_ote"]["cont_3h_rate"]
        v_delta = round(v_ote - v_not, 4) if v_ote and v_not else None
        points.append(f"Validation: OTE={v_ote:.1%} vs non-OTE={v_not:.1%} (delta={v_delta})")
        if v_delta and v_delta > 0:
            points.append("OTE edge HOLDS in validation period")
        else:
            points.append("OTE edge DOES NOT hold in validation period")

    # Best combo
    pd = all_res["premium_discount_interaction"]
    best_key = max((k for k in pd if pd[k]["n"] >= 30),
                   key=lambda k: pd[k]["cont_3h_rate"] or 0, default=None)
    if best_key:
        points.append(f"Best PD combo: {best_key} cont_3h={pd[best_key]['cont_3h_rate']:.1%} (n={pd[best_key]['n']})")

    kz = all_res["kz_interaction"]
    best_kz = max((k for k in kz if kz[k]["n"] >= 30),
                  key=lambda k: kz[k]["cont_3h_rate"] or 0, default=None)
    if best_kz:
        points.append(f"Best KZ combo: {best_kz} cont_3h={kz[best_kz]['cont_3h_rate']:.1%} (n={kz[best_kz]['n']})")

    d1 = all_res["d1_alignment_interaction"]
    best_d1 = max((k for k in d1 if d1[k]["n"] >= 30),
                  key=lambda k: d1[k]["cont_3h_rate"] or 0, default=None)
    if best_d1:
        points.append(f"Best D1 combo: {best_d1} cont_3h={d1[best_d1]['cont_3h_rate']:.1%} (n={d1[best_d1]['n']})")

    return points


def main():
    db, day_cls = load_data()
    print(f"Loaded {len(db)} displacement records, {len(day_cls)} day classifications")

    disc = [r for r in db if r.get("set") == "disc"]
    val = [r for r in db if r.get("set") == "val"]
    print(f"Discovery: {len(disc)}, Validation: {len(val)}")

    all_res = analyze_subset(db, day_cls, "all")
    disc_res = analyze_subset(disc, day_cls, "discovery")
    val_res = analyze_subset(val, day_cls, "validation")

    verdict = build_verdict(all_res, disc_res, val_res)

    output = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_file": str(DB_PATH.name),
        "total_records": len(db),
        "discovery_n": len(disc),
        "validation_n": len(val),
        "all_periods": all_res,
        "discovery": disc_res,
        "validation": val_res,
        "verdict": verdict,
    }

    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2, cls=NpEncoder)
    print(f"\nSaved to {OUT_PATH}")

    # Print summary
    print("\n" + "=" * 70)
    print("OTE ZONE ANALYSIS SUMMARY")
    print("=" * 70)

    for period, res in [("ALL", all_res), ("DISCOVERY", disc_res), ("VALIDATION", val_res)]:
        print(f"\n--- {period} (n={res['n_total']}) ---")
        ote = res["ote_vs_not_ote"]["in_ote"]
        not_ote = res["ote_vs_not_ote"]["not_in_ote"]
        print(f"  OTE:     n={ote['n']:>5}  cont_3h={ote['cont_3h_rate']:.1%}  mfe={ote['avg_mfe_3h']:.2f}  mae={ote['avg_mae_3h']:.2f}")
        print(f"  not OTE: n={not_ote['n']:>5}  cont_3h={not_ote['cont_3h_rate']:.1%}  mfe={not_ote['avg_mfe_3h']:.2f}  mae={not_ote['avg_mae_3h']:.2f}")
        chi = res["chi_squared_ote_vs_not"]
        print(f"  Chi2: {chi['chi2']}, p={chi['p_value']} {'***' if chi.get('significant_005') else ''}")

    print("\n--- PREMIUM/DISCOUNT x OTE (all periods) ---")
    for k, v in sorted(all_res["premium_discount_interaction"].items()):
        flag = f" [{v.get('flag','')}]" if v.get('flag') else ""
        print(f"  {k:25s}  n={v['n']:>5}  cont_3h={v['cont_3h_rate']:.1%}  mfe={v['avg_mfe_3h']:.2f}  mae={v['avg_mae_3h']:.2f}{flag}")

    print("\n--- D1 ALIGNMENT x OTE (all periods) ---")
    for k, v in sorted(all_res["d1_alignment_interaction"].items()):
        flag = f" [{v.get('flag','')}]" if v.get('flag') else ""
        print(f"  {k:30s}  n={v['n']:>5}  cont_3h={v['cont_3h_rate']:.1%}  mfe={v['avg_mfe_3h']:.2f}  mae={v['avg_mae_3h']:.2f}{flag}")

    print("\n--- D1 CLEAR x OTE (all periods) ---")
    for k, v in sorted(all_res["d1_clear_interaction"].items()):
        flag = f" [{v.get('flag','')}]" if v.get('flag') else ""
        print(f"  {k:25s}  n={v['n']:>5}  cont_3h={v['cont_3h_rate']:.1%}  mfe={v['avg_mfe_3h']:.2f}  mae={v['avg_mae_3h']:.2f}{flag}")

    print("\n--- KZ x OTE (all periods) ---")
    for k, v in sorted(all_res["kz_interaction"].items()):
        flag = f" [{v.get('flag','')}]" if v.get('flag') else ""
        print(f"  {k:20s}  n={v['n']:>5}  cont_3h={v['cont_3h_rate']:.1%}  mfe={v['avg_mfe_3h']:.2f}  mae={v['avg_mae_3h']:.2f}{flag}")

    print("\n--- SESSION x OTE (all periods) ---")
    for k, v in sorted(all_res["session_split"].items()):
        flag = f" [{v.get('flag','')}]" if v.get('flag') else ""
        print(f"  {k:20s}  n={v['n']:>5}  cont_3h={v['cont_3h_rate']:.1%}  mfe={v['avg_mfe_3h']:.2f}  mae={v['avg_mae_3h']:.2f}{flag}")

    print("\n--- VERDICT ---")
    for v in verdict:
        print(f"  * {v}")


if __name__ == "__main__":
    main()
