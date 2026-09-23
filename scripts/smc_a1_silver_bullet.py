#!/usr/bin/env python3
"""
SMC A1 Silver Bullet Analysis
Analyze XAUUSD displacement data for Silver Bullet time windows.
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from scipy.stats import chi2_contingency
import numpy as np

BASE = "/Users/borr/Documents/trading/gold-agent"
DISP_PATH = f"{BASE}/knowledge_base_backtest/analysis/displacement_database_20260403_0030.json"
D1_PATH = f"{BASE}/knowledge_base_backtest/analysis/edge_discovery_d1unclear_20260405.json"
OUT_PATH = f"{BASE}/knowledge_base_backtest/analysis/smc_silver_bullet_20260405.json"

# ---------- load data ----------
with open(DISP_PATH) as f:
    disps = json.load(f)
print(f"Loaded {len(disps)} displacement records")

with open(D1_PATH) as f:
    d1_data = json.load(f)
day_cls = d1_data["day_classifications"]
# Build lookup: date -> d1_clear (XAUUSD only)
d1_lookup = {}
for dc in day_cls:
    if dc["symbol"] == "XAUUSD":
        d1_lookup[dc["date"]] = dc["d1_clear"]
print(f"Loaded {len(d1_lookup)} XAUUSD day classifications")

# ---------- extract hour, attach d1_clear ----------
for rec in disps:
    rec["hour"] = int(rec["timestamp"].split()[1].split(":")[0])
    rec["d1_clear"] = d1_lookup.get(rec["date"])

# ---------- helpers ----------
def stats_for(recs):
    n = len(recs)
    if n == 0:
        return {"n": 0, "cont_3h_rate": None, "avg_mfe_3h": None, "avg_mae_3h": None, "flag": "n=0"}
    cont = sum(1 for r in recs if r.get("cont_3h"))
    mfe_vals = [r["mfe_3h"] for r in recs if r.get("mfe_3h") is not None]
    mae_vals = [r["mae_3h"] for r in recs if r.get("mae_3h") is not None]
    result = {
        "n": n,
        "cont_3h_rate": round(cont / n, 4),
        "cont_3h_count": cont,
        "avg_mfe_3h": round(sum(mfe_vals) / len(mfe_vals), 2) if mfe_vals else None,
        "avg_mae_3h": round(sum(mae_vals) / len(mae_vals), 2) if mae_vals else None,
    }
    if n < 30:
        result["flag"] = "LOW_N"
    return result

def split_by_set(recs):
    disc = [r for r in recs if r["set"] == "disc"]
    val = [r for r in recs if r["set"] == "val"]
    return disc, val

# ---------- 1. Hourly heatmap ----------
by_hour = defaultdict(list)
for rec in disps:
    by_hour[rec["hour"]].append(rec)

hourly_heatmap = []
for h in range(24):
    recs = by_hour[h]
    disc, val = split_by_set(recs)
    s_disc = stats_for(disc)
    s_val = stats_for(val)
    s_total = stats_for(recs)
    hourly_heatmap.append({
        "hour": h,
        "n_disc": s_disc["n"],
        "rate_disc": s_disc["cont_3h_rate"],
        "mfe_disc": s_disc["avg_mfe_3h"],
        "mae_disc": s_disc["avg_mae_3h"],
        "n_val": s_val["n"],
        "rate_val": s_val["cont_3h_rate"],
        "mfe_val": s_val["avg_mfe_3h"],
        "mae_val": s_val["avg_mae_3h"],
        "n_total": s_total["n"],
        "rate_total": s_total["cont_3h_rate"],
        "avg_mfe": s_total["avg_mfe_3h"],
        "avg_mae": s_total["avg_mae_3h"],
        "flag": s_total.get("flag"),
    })

# ---------- 2. Silver Bullet windows ----------
london_sb_recs = by_hour[15]
ny_sb_recs = by_hour[19]

def window_stats(recs, label):
    disc, val = split_by_set(recs)
    return {
        "label": label,
        "total": stats_for(recs),
        "discovery": stats_for(disc),
        "validation": stats_for(val),
    }

silver_bullet_windows = {
    "london_sb": window_stats(london_sb_recs, "London SB (15:00-16:00 UTC / 10-11 AM EST)"),
    "ny_sb": window_stats(ny_sb_recs, "NY SB (19:00-20:00 UTC / 2-3 PM EST)"),
}

# ---------- 3. Control windows ----------
control_windows = {
    "london_before_h14": window_stats(by_hour[14], "London control before (14:00 UTC)"),
    "london_after_h16": window_stats(by_hour[16], "London control after (16:00 UTC)"),
    "ny_before_h18": window_stats(by_hour[18], "NY control before (18:00 UTC)"),
    "ny_after_h20": window_stats(by_hour[20], "NY control after (20:00 UTC)"),
}

# ---------- 4. Chi-squared tests ----------
def chi2_sb_vs_controls(sb_recs, ctrl_before_recs, ctrl_after_recs, name):
    """Compare SB hour continuation rate vs pooled adjacent control hours."""
    sb_s = stats_for(sb_recs)
    # Pool controls
    ctrl_all = ctrl_before_recs + ctrl_after_recs
    ctrl_s = stats_for(ctrl_all)

    if sb_s["n"] == 0 or ctrl_s["n"] == 0:
        return {"test": name, "error": "insufficient data"}

    sb_cont = sb_s["cont_3h_count"]
    sb_no = sb_s["n"] - sb_cont
    ctrl_cont = ctrl_s["cont_3h_count"]
    ctrl_no = ctrl_s["n"] - ctrl_cont

    table = np.array([[sb_cont, sb_no], [ctrl_cont, ctrl_no]])

    # Check expected counts
    if table.min() < 5:
        flag = "LOW_EXPECTED_COUNTS"
    else:
        flag = None

    try:
        chi2, p, dof, expected = chi2_contingency(table)
    except Exception as e:
        return {"test": name, "error": str(e)}

    result = {
        "test": name,
        "sb_n": sb_s["n"],
        "sb_rate": sb_s["cont_3h_rate"],
        "ctrl_n": ctrl_s["n"],
        "ctrl_rate": ctrl_s["cont_3h_rate"],
        "chi2": round(float(chi2), 4),
        "p_value": round(float(p), 6),
        "dof": int(dof),
        "significant_005": p < 0.05,
        "significant_001": p < 0.01,
    }
    if flag:
        result["flag"] = flag
    return result

chi_squared_tests = {
    "london_sb_vs_controls": chi2_sb_vs_controls(
        london_sb_recs, by_hour[14], by_hour[16], "London SB h15 vs controls h14+h16"
    ),
    "ny_sb_vs_controls": chi2_sb_vs_controls(
        ny_sb_recs, by_hour[18], by_hour[20], "NY SB h19 vs controls h18+h20"
    ),
}

# ---------- 5. D1 split for SB hours ----------
def d1_split(recs, label):
    clear = [r for r in recs if r.get("d1_clear") is True]
    unclear = [r for r in recs if r.get("d1_clear") is False]
    unknown = [r for r in recs if r.get("d1_clear") is None]
    return {
        f"{label}_d1_clear": stats_for(clear),
        f"{label}_d1_unclear": stats_for(unclear),
        f"{label}_d1_unknown": stats_for(unknown),
    }

d1_split_results = {}
d1_split_results.update(d1_split(london_sb_recs, "london_sb"))
d1_split_results.update(d1_split(ny_sb_recs, "ny_sb"))

# Also split by set within d1 groups
d1_split_by_set = {}
for sb_name, sb_recs in [("london_sb", london_sb_recs), ("ny_sb", ny_sb_recs)]:
    for d1_val, d1_label in [(True, "d1_clear"), (False, "d1_unclear")]:
        subset = [r for r in sb_recs if r.get("d1_clear") is d1_val]
        disc, val = split_by_set(subset)
        key = f"{sb_name}_{d1_label}"
        d1_split_by_set[key] = {
            "total": stats_for(subset),
            "discovery": stats_for(disc),
            "validation": stats_for(val),
        }

# ---------- 6. Build verdict ----------
lon_s = silver_bullet_windows["london_sb"]["total"]
ny_s = silver_bullet_windows["ny_sb"]["total"]
lon_chi = chi_squared_tests["london_sb_vs_controls"]
ny_chi = chi_squared_tests["ny_sb_vs_controls"]

verdict_parts = []
verdict_parts.append(f"London SB (h15): n={lon_s['n']}, cont_3h={lon_s['cont_3h_rate']:.1%}")
verdict_parts.append(f"NY SB (h19): n={ny_s['n']}, cont_3h={ny_s['cont_3h_rate']:.1%}")

if lon_chi.get("p_value") is not None:
    verdict_parts.append(
        f"London SB vs controls: chi2={lon_chi['chi2']}, p={lon_chi['p_value']:.4f} "
        f"({'SIGNIFICANT' if lon_chi['significant_005'] else 'NOT significant'} at 0.05)"
    )
if ny_chi.get("p_value") is not None:
    verdict_parts.append(
        f"NY SB vs controls: chi2={ny_chi['chi2']}, p={ny_chi['p_value']:.4f} "
        f"({'SIGNIFICANT' if ny_chi['significant_005'] else 'NOT significant'} at 0.05)"
    )

# D1 clear vs unclear for each SB
for sb_name in ["london_sb", "ny_sb"]:
    clear_r = d1_split_results[f"{sb_name}_d1_clear"]["cont_3h_rate"]
    unclear_r = d1_split_results[f"{sb_name}_d1_unclear"]["cont_3h_rate"]
    clear_n = d1_split_results[f"{sb_name}_d1_clear"]["n"]
    unclear_n = d1_split_results[f"{sb_name}_d1_unclear"]["n"]
    if clear_r is not None and unclear_r is not None:
        delta = clear_r - unclear_r
        verdict_parts.append(
            f"{sb_name} d1_clear({clear_n})={clear_r:.1%} vs d1_unclear({unclear_n})={unclear_r:.1%}, "
            f"delta={delta:+.1%}"
        )

verdict = " | ".join(verdict_parts)

# ---------- 7. Assemble and save ----------
output = {
    "generated_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "description": "Silver Bullet time window analysis for XAUUSD M15 displacements",
    "data_source": os.path.basename(DISP_PATH),
    "total_records": len(disps),
    "hourly_heatmap": hourly_heatmap,
    "silver_bullet_windows": silver_bullet_windows,
    "control_windows": control_windows,
    "chi_squared_tests": chi_squared_tests,
    "d1_split": d1_split_results,
    "d1_split_by_set": d1_split_by_set,
    "verdict": verdict,
}

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)

with open(OUT_PATH, "w") as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder)
print(f"\nSaved to {OUT_PATH}")

# ---------- Console summary ----------
print("\n===== HOURLY HEATMAP =====")
print(f"{'Hour':>4} | {'N_disc':>6} {'Rate_d':>7} | {'N_val':>6} {'Rate_v':>7} | {'N_tot':>6} {'Rate_t':>7} {'MFE':>7} {'MAE':>7}")
print("-" * 78)
for row in hourly_heatmap:
    flag = " *" if row.get("flag") else ""
    rd = f"{row['rate_disc']:.1%}" if row['rate_disc'] is not None else "  n/a"
    rv = f"{row['rate_val']:.1%}" if row['rate_val'] is not None else "  n/a"
    rt = f"{row['rate_total']:.1%}" if row['rate_total'] is not None else "  n/a"
    mfe = f"{row['avg_mfe']:.1f}" if row['avg_mfe'] is not None else "n/a"
    mae = f"{row['avg_mae']:.1f}" if row['avg_mae'] is not None else "n/a"
    print(f"{row['hour']:>4} | {row['n_disc']:>6} {rd:>7} | {row['n_val']:>6} {rv:>7} | {row['n_total']:>6} {rt:>7} {mfe:>7} {mae:>7}{flag}")

print("\n===== SILVER BULLET WINDOWS =====")
for name, data in silver_bullet_windows.items():
    t = data["total"]
    d = data["discovery"]
    v = data["validation"]
    print(f"\n{data['label']}:")
    print(f"  Total:     n={t['n']}, rate={t['cont_3h_rate']:.1%}, MFE={t['avg_mfe_3h']}, MAE={t['avg_mae_3h']}")
    print(f"  Discovery: n={d['n']}, rate={d['cont_3h_rate']:.1%}" if d['n'] > 0 else f"  Discovery: n=0")
    print(f"  Validation:n={v['n']}, rate={v['cont_3h_rate']:.1%}" if v['n'] > 0 else f"  Validation: n=0")

print("\n===== CONTROL WINDOWS =====")
for name, data in control_windows.items():
    t = data["total"]
    print(f"  {data['label']}: n={t['n']}, rate={t['cont_3h_rate']:.1%}, MFE={t['avg_mfe_3h']}, MAE={t['avg_mae_3h']}" if t['n'] > 0 else f"  {data['label']}: n=0")

print("\n===== CHI-SQUARED TESTS =====")
for name, res in chi_squared_tests.items():
    if "error" in res:
        print(f"  {res['test']}: ERROR - {res['error']}")
    else:
        sig = "***" if res["significant_001"] else ("*" if res["significant_005"] else "ns")
        print(f"  {res['test']}: SB rate={res['sb_rate']:.1%} (n={res['sb_n']}) vs ctrl rate={res['ctrl_rate']:.1%} (n={res['ctrl_n']})")
        print(f"    chi2={res['chi2']:.4f}, p={res['p_value']:.6f} {sig}")
        if res.get("flag"):
            print(f"    FLAG: {res['flag']}")

print("\n===== D1 SPLIT (SB hours) =====")
for key, val in d1_split_results.items():
    r = f"{val['cont_3h_rate']:.1%}" if val['cont_3h_rate'] is not None else "n/a"
    flag = f" [{val.get('flag', '')}]" if val.get('flag') else ""
    print(f"  {key}: n={val['n']}, rate={r}{flag}")

print("\n===== D1 SPLIT BY SET =====")
for key, val in d1_split_by_set.items():
    t = val["total"]
    d = val["discovery"]
    v = val["validation"]
    print(f"  {key}: total n={t['n']}, rate={t['cont_3h_rate']:.1%}" if t['n'] > 0 else f"  {key}: n=0")
    if d['n'] > 0:
        dflag = f" [{d.get('flag', '')}]" if d.get('flag') else ""
        print(f"    disc: n={d['n']}, rate={d['cont_3h_rate']:.1%}{dflag}")
    if v['n'] > 0:
        vflag = f" [{v.get('flag', '')}]" if v.get('flag') else ""
        print(f"    val:  n={v['n']}, rate={v['cont_3h_rate']:.1%}{vflag}")

print(f"\n===== VERDICT =====\n{verdict}")
